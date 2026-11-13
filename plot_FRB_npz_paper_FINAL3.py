import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import sys
import os
import argparse

def plot_frb_waterfall(npz_file, down_freq=1, down_time=1, plot_time=20.0,
                       no_ylabel=False, no_xlabel=False, no_ytick_values=False,
                       subburst_offsets=[0.0], onpulse_widths=[10.0],
                       title=None, freq_max=None, freq_label_max=None):
    """
    Load an FRB .npz file and plot the frequency vs. time waterfall plot with intensity profile on top.
    Optionally draw vertical lines marking the on-pulse width regions for each sub-burst.
    Plot is centered on the main burst peak (t=0 at detected peak), with offsets relative to it.
    """
    if len(subburst_offsets) != len(onpulse_widths):
        print(f"Error: Number of subburst_offsets ({len(subburst_offsets)}) must match onpulse_widths ({len(onpulse_widths)})")
        sys.exit(1)

    # Get base name for burst identifier (strip multiple extensions)
    full_base = os.path.basename(npz_file)
    base_name = os.path.splitext(os.path.splitext(os.path.splitext(full_base)[0])[0])[0]
    
    # Load data
    data = np.load(npz_file)
    wfall = data['wfall']
    burstmetadata = {k: data[k] for k in data if k != 'wfall'}
    
    # Frequency and time resolutions
    df = abs(burstmetadata['bandwidth']) / wfall.shape[0]
    dt = burstmetadata['duration'] * 1000 / wfall.shape[1]  # ms
    
    # Downsampling
    if down_freq > 1:
        orig_nfreq = wfall.shape[0]
        nfreq = orig_nfreq // down_freq
        if nfreq * down_freq != orig_nfreq:
            print(f"Warning: Truncating frequency channels to {nfreq * down_freq}")
        wfall = np.mean(wfall[:nfreq*down_freq].reshape(nfreq, down_freq, wfall.shape[1]), axis=1)
        df *= down_freq
        if 'dfs' in burstmetadata:
            orig_dfs = burstmetadata['dfs']
            burstmetadata['dfs'] = np.mean(orig_dfs[:nfreq*down_freq].reshape(nfreq, down_freq), axis=1)

    if down_time > 1:
        orig_ntime = wfall.shape[1]
        ntime = orig_ntime // down_time
        if ntime * down_time != orig_ntime:
            print(f"Warning: Truncating time bins to {ntime * down_time}")
        wfall = np.mean(wfall[:, :ntime*down_time].reshape(wfall.shape[0], ntime, down_time), axis=2)
        dt *= down_time

    lowest_freq = min(burstmetadata['dfs'])
    time_array = np.arange(wfall.shape[1]) * dt

    # Intensity profile to find peak
    intensity = np.sum(wfall, axis=0)
    burst_idx = np.argmax(intensity)
    t_burst = time_array[burst_idx]

    # Center plot on main burst peak (t=0 at t_burst)
    plot_center = t_burst

    # Compute span for cropping to ensure all sub-bursts visible (offsets rel to t_burst)
    max_offset_abs = max(abs(o) for o in subburst_offsets)
    max_half = max(w / 2 for w in onpulse_widths)
    crop_half = max(50.0, plot_time + max_offset_abs + max_half + 20.0)  # Margin for visibility

    # Desired window around plot center
    start_desired = plot_center - crop_half
    end_desired = plot_center + crop_half
    start_idx = np.searchsorted(time_array, max(0, start_desired))
    end_idx = np.searchsorted(time_array, min(time_array[-1], end_desired))

    wfall_crop = wfall[:, start_idx:end_idx]
    rel_times_crop = time_array[start_idx:end_idx] - plot_center

    # Pad to full range if needed
    left_extra = rel_times_crop[0] + crop_half
    right_extra = crop_half - rel_times_crop[-1]
    pad_left = int(np.ceil(left_extra / dt)) if left_extra > 0 else 0
    pad_right = int(np.ceil(right_extra / dt)) if right_extra > 0 else 0

    wfall_padded = np.pad(wfall_crop, ((0, 0), (pad_left, pad_right)),
                          mode='constant', constant_values=0)

    if pad_left > 0:
        left_times = np.arange(-pad_left, 0) * dt + rel_times_crop[0]
    else:
        left_times = np.array([])
    if pad_right > 0:
        right_times = np.arange(1, pad_right + 1) * dt + rel_times_crop[-1]
    else:
        right_times = np.array([])

    rel_times_padded = np.concatenate((left_times, rel_times_crop, right_times))
    time_min = rel_times_padded[0]
    time_max = rel_times_padded[-1]
    extent = [time_min, time_max, lowest_freq, lowest_freq + df * wfall_padded.shape[0]]
    intensity_padded = np.sum(wfall_padded, axis=0)

    # --- Plot setup ---
    fig = plt.figure(figsize=(10, 30))
    gs = GridSpec(2, 1, height_ratios=[1, 3], hspace=0.05)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # Thicken axis spines and ticks for bolder borders across the figure
    for ax in (ax1, ax2):
        for spine in ax.spines.values():
            spine.set_linewidth(10)
            spine.set_edgecolor('black')
        ax.tick_params(axis='both', which='major', width='10', length=8)

    # Title text
    title_text = base_name if title is None else str(title)
    ax1.text(0.02, 0.95, title_text, transform=ax1.transAxes, fontsize=60,
             verticalalignment='top', fontweight='bold', color='black')

    # Title text with offsets and widths
    #offsets_str = ', '.join([f'{o:.1f}' for o in subburst_offsets])
    #widths_str = ', '.join([f'{w:.1f}' for w in onpulse_widths])
    #title_text = f"{base_name}\nOffsets (ms): [{offsets_str}]\nWidths (ms): [{widths_str}]"
    #ax1.text(0.02, 0.95, title_text, transform=ax1.transAxes, fontsize=12,
    #         verticalalignment='top', fontweight='bold', color='black')

    # Intensity plot
    # Make the burst-profile (intensity) line darker and bolder
    ax1.plot(rel_times_padded, intensity_padded, color='black', linewidth=5)
    ax1.grid(True, alpha=0.3, linewidth=1.0)
    ax1.set_xlim(-plot_time, plot_time)
    ax1.set_yticks([])
    ax1.set_xticks([])

    # Waterfall
    im = ax2.imshow(wfall_padded, aspect='auto', origin='lower', interpolation='none',
                    extent=extent, cmap='YlOrBr_r')
    if not no_xlabel:
        ax2.set_xlabel('Time (ms)', fontsize=80, fontweight='bold')
    if not no_ylabel:
        ax2.set_ylabel('Frequency (MHz)', fontsize=80, fontweight='bold')
    ax2.set_xlim(-plot_time, plot_time)
    if freq_max is not None:
        try:
            freq_max_val = float(freq_max)
        except (TypeError, ValueError):
            print(f"Warning: Invalid freq_max={freq_max!r}; ignoring")
        else:
            if freq_max_val > lowest_freq:
                ax2.set_ylim(lowest_freq, freq_max_val)
            else:
                print(f"Warning: freq_max ({freq_max_val}) <= lowest_freq ({lowest_freq}); ignoring")

    if freq_label_max is not None:
        try:
            freq_label_max_val = float(freq_label_max)
        except (TypeError, ValueError):
            print(f"Warning: Invalid freq_label_max={freq_label_max!r}; ignoring")
        else:
            ylim_low, ylim_high = ax2.get_ylim()
            label_high = min(freq_label_max_val, ylim_high)
            if label_high > ylim_low:
                span = label_high - ylim_low
                step = 200.0 if span > 800.0 else 100.0
                start = np.ceil(ylim_low / step) * step
                yticks = np.arange(start, label_high + 0.1 * step, step)
                ax2.set_yticks(yticks)
            else:
                print(f"Warning: freq_label_max ({freq_label_max_val}) <= y-axis min ({ylim_low}); ignoring")
    ax2.tick_params(axis='both', labelsize=60, width=3)
    if no_ytick_values:
        ax2.set_yticklabels([])

    # --- Draw vertical lines and span for each sub-burst's on-pulse region on top plot ---
    colors = ['blue', 'red', 'green', 'purple']  # Cycle colors if many sub-bursts
    for i, (offset, width) in enumerate(zip(subburst_offsets, onpulse_widths)):
        sub_center_rel = offset  # Relative to t_burst (plot_center)
        half_width = width / 2.0
        color = colors[i % len(colors)]
        linestyle = '--'
        linewidth = 3.0
    
        
        # Dashed vertical lines (boundaries)
        ax1.axvline(sub_center_rel - half_width, color=color, linestyle=linestyle, linewidth=linewidth)
        ax1.axvline(sub_center_rel + half_width, color=color, linestyle=linestyle, linewidth=linewidth)
        
        # Full region span (shaded with dashed borders effect via light fill)
        #ax1.axvspan(sub_center_rel - half_width, sub_center_rel + half_width, 
        #            color=color, alpha=0.1, linewidth=0, hatch='//')  # Light fill with hatch for "dashed" texture


    # Save
    save_path = f"{base_name}_plot_paper_final.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved as {save_path}")

# --- Main ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot FRB waterfall and intensity with optional on-pulse width markers for sub-bursts.')
    parser.add_argument('npz_file', type=str, help='Path to the .npz file')
    parser.add_argument('-fdown', '--down_freq', type=int, default=1, help='Downsampling factor for frequency (default: 1)')
    parser.add_argument('-tdown', '--down_time', type=int, default=1, help='Downsampling factor for time (default: 1)')
    parser.add_argument('-time', '--plot_time', type=float, default=20.0, help='Plot limits around center in ms (default: 20.0)')
    parser.add_argument('-suboffsets', '--subburst_offsets', nargs='+', type=float, default=[0.0],
                        help='Offsets in ms from the detected burst peak for each sub-burst center.')
    parser.add_argument('-onwidth', '--onpulse_widths', nargs='+', type=float, default=[10.0],
                        help='Widths (ms) of on-pulse region for each sub-burst (must match number of offsets).')
    parser.add_argument('-noylabel', '--no_ylabel', action='store_true', help='Omit y-axis label')
    parser.add_argument('-noxlabel', '--no_xlabel', action='store_true', help='Omit x-axis label')
    parser.add_argument('-noytickvals', '--no_ytick_values', action='store_true', help='Hide y-axis numeric tick values but keep tick marks')
    parser.add_argument('-title', '--title', type=str, default=None,
                        help='Override title text (default: derived from filename)')
    parser.add_argument('-fmax', '--freq_max', type=float, default=None,
                        help='Maximum frequency (MHz) to show on y-axis (default: show full band)')
    parser.add_argument('-flabelmax', '--freq_label_max', type=float, default=None,
                        help='Maximum frequency (MHz) to label on y-axis ticks (default: label full axis)')

    args = parser.parse_args()

    if args.down_freq < 1 or args.down_time < 1:
        print("Downsample factors must be integers >= 1")
        sys.exit(1)
    if args.plot_time < 0:
        print("Plot time must be >= 0")
        sys.exit(1)

    plot_frb_waterfall(args.npz_file, args.down_freq, args.down_time, args.plot_time,
                       args.no_ylabel, args.no_xlabel, args.no_ytick_values,
                       args.subburst_offsets, args.onpulse_widths,
                       title=args.title, freq_max=args.freq_max, freq_label_max=args.freq_label_max)