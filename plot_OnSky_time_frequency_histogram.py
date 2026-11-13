#!/usr/bin/env python3
"""
Create a histogram of observing frequency weighted by on-sky hours.

Saves `frequency_histogram_bold.png` in the current folder.

Usage:
    python3 plot_frequency_histogram.py

Optional to show interactively:
    python3 plot_frequency_histogram.py --show
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt


def make_histogram(freqs, hours, out_png='frequency_histogram_bold.png', show=False):
    fig, ax = plt.subplots(figsize=(8,6))

    # choose nice bin edges from ~900 to ~7620 MHz (10 bins)
    bins = np.linspace(900, 7620, 11)

    # Each frequency is a center frequency with a bandwidth of 672 MHz
    half_bw = 336.0  # MHz

    # Compute hours-per-bin by distributing each observation's hours
    # uniformly across its frequency interval [f-half_bw, f+half_bw],
    # then summing the overlap with each histogram bin.
    bin_hours = np.zeros(len(bins) - 1)
    bin_left = bins[:-1]
    bin_right = bins[1:]
    for f, h in zip(freqs, hours):
        int_left = f - half_bw
        int_right = f + half_bw
        # overlap with each bin
        overlaps = np.maximum(0.0, np.minimum(bin_right, int_right) - np.maximum(bin_left, int_left))
        # fraction of the observation's bandwidth in each bin
        frac = overlaps / (2.0 * half_bw)
        bin_hours += h * frac

    # Plot as bar chart with computed hours per bin
    widths = bin_right - bin_left
    ax.bar(bin_left, bin_hours, width=widths, align='edge', color='blue', edgecolor='black', linewidth=1)

    # Bold, large axis labels
    ax.set_xlabel('Observed Frequency (in MHz)', fontsize=15, fontweight='bold')
    ax.set_ylabel('On-Sky Time (in hours)', fontsize=15, fontweight='bold')

    # Make tick labels bigger and bold
    ax.tick_params(axis='both', which='major', labelsize=13, width=2)
    for label in ax.get_xticklabels() + ax.get_yticklabels():

    # Ensure all spines (axes borders) are visible and bold on all sides
     for name, spine in ax.spines.items():
        spine.set_visible(True)
        spine.set_linewidth(2.5)
        spine.set_edgecolor('black')

    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    print(f'Wrote {out_png}')
    if show:
        plt.show()
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='Plot frequency histogram with bold labels and borders')
    parser.add_argument('--show', action='store_true', help='Show plot interactively')
    args = parser.parse_args()

    # Data from the table (hours observed, frequency in MHz)
    hours = [336.4, 525.69, 369.48, 180.16, 155.62, 155.62, 155.0, 155.0, 150.5, 150.5]
    freqs = [1236, 1908, 2580, 3252, 3924, 4596, 5268, 5940, 6612, 7284]

    make_histogram(freqs, hours, show=args.show)


if __name__ == '__main__':
    main()
