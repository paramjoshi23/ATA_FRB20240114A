#!/usr/bin/env python3
"""Calculate minimum burst energy from a manually provided fluence.

Uses the same constants and energy formula as `calc_burst_energy.py`, but:
- Fluence is provided manually (assumed Jy-ms).
- Bandwidth is fixed to 1344 MHz.

Formula:
    E = 4π * (DL/cm)^2 * (F/Jy s) * (Δν/Hz) × 1e-23 erg

Examples:
    python calc_min_burst_energy_manual_fluence.py 0.5
    python calc_min_burst_energy_manual_fluence.py 0.5 1.2 3.0
"""

from __future__ import annotations

import argparse
import math
from typing import List

# -----------------------------
# 1. CONSTANTS & CONVERSIONS
# -----------------------------

# Luminosity distance in Mpc
DL_mpc = 630.72

# Fixed bandwidth in MHz
BANDWIDTH_MHZ_FIXED = 1344.0

# Unit conversions
MPC_TO_CM = 3.085677581e24  # 1 Mpc in cm
JYMS_TO_JYS = 1e-3  # 1 Jy-ms = 1e-3 Jy-s
MHZ_TO_HZ = 1e6  # 1 MHz = 1e6 Hz

# Convert DL to cm
DL_cm = DL_mpc * MPC_TO_CM

# Energy constant (from paper)
ENERGY_FACTOR = 1e-23  # ×10^-23 erg


def compute_energy(fluence_jys: float, bw_hz: float) -> float:
    """Compute burst energy in erg."""
    return 4.0 * math.pi * (DL_cm**2) * fluence_jys * bw_hz * ENERGY_FACTOR


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute minimum burst energy from manual fluence (Jy-ms) "
            f"using fixed bandwidth {BANDWIDTH_MHZ_FIXED:g} MHz."
        )
    )
    parser.add_argument(
        "fluence_jy_ms",
        nargs="*",
        type=float,
        help="Fluence value(s) in Jy-ms.",
    )
    return parser.parse_args()


def _prompt_for_fluences() -> List[float]:
    raw = input("Enter fluence(s) in Jy-ms (space-separated): ").strip()
    if not raw:
        raise SystemExit("No fluence provided.")
    try:
        return [float(x) for x in raw.split()]
    except ValueError as exc:
        raise SystemExit(f"Could not parse fluence(s): {raw!r}") from exc


def main() -> None:
    args = _parse_args()
    fluence_jy_ms_values = args.fluence_jy_ms if args.fluence_jy_ms else _prompt_for_fluences()

    bw_hz = BANDWIDTH_MHZ_FIXED * MHZ_TO_HZ

    for fluence_jy_ms in fluence_jy_ms_values:
        fluence_jy_s = fluence_jy_ms * JYMS_TO_JYS
        energy_erg = compute_energy(fluence_jy_s, bw_hz)

        # Print one result per line to keep it easy to copy into tables.
        print(f"Fluence = {fluence_jy_ms:g} Jy-ms -> E_min = {energy_erg:.6e} erg")


if __name__ == "__main__":
    main()
