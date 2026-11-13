import numpy as np

def compute_flux(sefd, snr, width, bandwidth, npol=2):
    """
    Compute FRB peak flux using:
    S = (SNR * SEFD) / sqrt(npol * B * W)
    
    sefd: SEFD in Jy
    snr: peak S/N
    width: width in seconds
    bandwidth: bandwidth in Hz
    """
    return (snr * sefd) / np.sqrt(npol * bandwidth * width)


# Input files
sefd_file = "sefd.txt"
snr_file = "snr.txt"
width_file = "3sigma_durations_new.txt"
bandwidth_file = "3sigma_bandwidths_new.txt"

# Output file
output_file = "flux_output_new.txt"

# Load values (one per line)
sefd_vals = np.loadtxt(sefd_file)
snr_vals = np.loadtxt(snr_file)
width_vals = np.loadtxt(width_file)
bandwidth_vals = np.loadtxt(bandwidth_file)

# Convert units: duration from ms to s, bandwidth from MHz to Hz
width_vals = width_vals / 1000
bandwidth_vals = bandwidth_vals * 1e6

# Compute flux for each entry
flux_vals = compute_flux(sefd_vals, snr_vals, width_vals, bandwidth_vals)

# Save output
np.savetxt(output_file, flux_vals, fmt="%.6f")

print(f"Computed flux for {len(flux_vals)} bursts.")
print(f"Results written to: {output_file}")
