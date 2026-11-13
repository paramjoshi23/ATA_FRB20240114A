import numpy as np

# Input files
flux_file = "flux_output_new.txt"
width_file = "3sigma_durations_new.txt"

# Output file
output_file = "fluence_output_new.txt"
# Load values (one per line)
flux_vals = np.loadtxt(flux_file)
width_vals = np.loadtxt(width_file)

# Compute fluence: fluence = flux * width (Jy * ms)
fluence_vals = flux_vals * width_vals

# Save output
np.savetxt(output_file, fluence_vals, fmt="%.6f")

print(f"Computed fluence for {len(fluence_vals)} bursts.")
print(f"Results written to: {output_file}")