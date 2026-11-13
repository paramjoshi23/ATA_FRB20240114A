import numpy as np

# -----------------------------
# 1. CONSTANTS & CONVERSIONS
# -----------------------------

# Luminosity distance in Mpc
DL_mpc = 630.72  

# Unit conversions
MPC_TO_CM = 3.085677581e24        # 1 Mpc in cm
JYMS_TO_JYS = 1e-3                # 1 Jy-ms = 1e-3 Jy-s
MHZ_TO_HZ = 1e6                   # 1 MHz = 1e6 Hz

# Convert DL to cm
DL_cm = DL_mpc * MPC_TO_CM

# Energy constant (from paper)
ENERGY_FACTOR = 1e-23             # ×10^-23 erg


# -----------------------------
# 2. LOAD INPUT FILES
# -----------------------------

fluence_file = "fluence_output_new.txt"       # fluence in Jy-ms
bandwidth_file = "3sigma_bandwidths_new.txt"     # bandwidth in MHz

fluence_jy_ms = np.loadtxt(fluence_file)
bandwidth_mhz = np.loadtxt(bandwidth_file)

# -----------------------------
# 3. UNIT CONVERSION
# -----------------------------

# Convert fluence Jy-ms → Jy-s
fluence_jy_s = fluence_jy_ms * JYMS_TO_JYS

# Convert bandwidth MHz → Hz
bandwidth_hz = bandwidth_mhz * MHZ_TO_HZ


# -----------------------------
# 4. ENERGY CALCULATION
# -----------------------------

def compute_energy(fluence_jys, bw_hz):
    """
    Compute burst energy using:
    E = 4π * (DL/cm)^2 * (F/Jy s) * (Δν/Hz) × 1e-23 erg
    """
    return 4 * np.pi * (DL_cm ** 2) * fluence_jys * bw_hz * ENERGY_FACTOR

energy_erg = compute_energy(fluence_jy_s, bandwidth_hz)

# -----------------------------
# 5. SAVE OUTPUT
# -----------------------------

output_file = "FRB_burst_energy_new.txt"
np.savetxt(output_file, energy_erg, fmt="%.6e")

print(f"Calculated burst energy for {len(energy_erg)} bursts.")
print(f"Saved to: {output_file}")
