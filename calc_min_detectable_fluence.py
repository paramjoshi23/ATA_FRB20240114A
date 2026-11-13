#!/usr/bin/env python3
"""Compute minimum detectable flux density and fluence for a burst.

Uses the radiometer-equation:

    S_nu,min = (SNR * SEFD) / sqrt(npol * tau * Delta_nu)

where:
- SEFD is in Jy
- tau is the burst duration in seconds
- Delta_nu is the bandwidth in Hz

This script reports:
- S_nu,min in Jy
- Minimum detectable fluence in Jy-ms (fluence = S_nu,min * duration_ms)

By default, it uses fixed values for SNR, duration, bandwidth, and npol:
- SNR = 10
- duration = 1 ms
- bandwidth = 1344 MHz
- npol = 2
"""

from __future__ import annotations

import argparse
import math


SNR_FIXED = 10.0
DURATION_MS_FIXED = 1.0
BANDWIDTH_MHZ_FIXED = 1344.0
NPOL_FIXED = 2.0


def min_detectable_flux_density_jy(
    *, sefd_jy: float,
    snr: float = SNR_FIXED,
    duration_ms: float = DURATION_MS_FIXED,
    bandwidth_mhz: float = BANDWIDTH_MHZ_FIXED,
    npol: float = NPOL_FIXED,
) -> float:
    duration_s = duration_ms / 1000.0
    bandwidth_hz = bandwidth_mhz * 1e6

    if sefd_jy <= 0:
        raise ValueError("SEFD must be > 0 Jy")
    if snr <= 0:
        raise ValueError("SNR must be > 0")
    if duration_s <= 0:
        raise ValueError("Duration must be > 0")
    if bandwidth_hz <= 0:
        raise ValueError("Bandwidth must be > 0")
    if npol <= 0:
        raise ValueError("npol must be > 0")

    return (snr * sefd_jy) / math.sqrt(npol * duration_s * bandwidth_hz)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compute minimum detectable flux density (Jy) and fluence (Jy-ms) "
            "for a burst, given SEFD (Jy), using fixed SNR=10, duration=1 ms, "
            "bandwidth=1344 MHz, npol=2."
        )
    )
    parser.add_argument(
        "sefd_jy",
        type=float,
        help="System Equivalent Flux Density (SEFD) in Jy",
    )
    args = parser.parse_args()

    flux_jy = min_detectable_flux_density_jy(sefd_jy=args.sefd_jy)
    fluence_jy_ms = flux_jy * DURATION_MS_FIXED

    print(f"Inputs: SEFD={args.sefd_jy:g} Jy")
    print(
        "Fixed: "
        f"SNR={SNR_FIXED:g}, duration={DURATION_MS_FIXED:g} ms, "
        f"bandwidth={BANDWIDTH_MHZ_FIXED:g} MHz, npol={NPOL_FIXED:g}"
    )
    print(f"S_nu,min (flux density) = {flux_jy:.6g} Jy")
    print(f"Minimum detectable fluence = {fluence_jy_ms:.6g} Jy-ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
