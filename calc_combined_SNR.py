import numpy as np

def combined_snr(snrs, widths):
    numerator = np.sum(snrs * np.sqrt(widths))
    denominator = np.sqrt(np.sum(widths))
    return numerator / denominator

# Change this to your input filename
input_file = "subbursts_SNR.txt"

# Load the two-column data
data = np.loadtxt(input_file)
snrs = data[:, 0]
widths = data[:, 1]

# Compute combined SNR
snr_total = combined_snr(snrs, widths)

# Print to terminal
print("Combined SNR:", snr_total)
