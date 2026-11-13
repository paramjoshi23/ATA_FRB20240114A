#!/usr/bin/env python3
"""Cumulative isotropic burst energy distribution with power-law fit.

- Uses only combined bursts (first N rows; excludes sub-bursts).
- Plots R(>E) on log-log axes (here R is the cumulative count).
- Adds a vertical reference line at a chosen energy.
- Fits a power law to the data with E >= reference energy using
  scipy.optimize.curve_fit (least-squares) in log10-space.

Power-law model:
    R(>E) = A * E^{gamma}

The fit is performed on:
    log10 R = log10 A + gamma * log10 E
"""

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from scipy.optimize import curve_fit
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "scipy is required for curve_fit. Install it with: pip install scipy\n"
        f"Original import error: {exc}"
    )


DEFAULT_INPUT = "FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2.csv"
ENERGY_COL = "Isotropic Burst Energy (ergs)"
DEFAULT_REF_ENERGY_ERG = 1.28e39


def clean_float(x):
    try:
        val = float(str(x).strip())
        if math.isfinite(val):
            return val
    except Exception:
        pass
    return np.nan


def cumulative_distribution(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns sorted energies and cumulative R(>E) (as counts)."""
    values = np.sort(values)
    N = len(values)
    cumulative = np.arange(N, 0, -1)  # N, N-1, ..., 1
    return values, cumulative


def powerlaw_log10_model(log10_E: np.ndarray, log10_A: float, gamma: float) -> np.ndarray:
    """log10 R = log10 A + gamma * log10 E"""
    return log10_A + gamma * log10_E


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("cumulative_energy_distribution_powerlaw_fit.png"),
    )
    parser.add_argument(
        "--split-index",
        type=int,
        default=98,
        help="First N rows are Combined bursts; rest Sub-bursts",
    )
    parser.add_argument(
        "--ref-energy",
        type=float,
        default=DEFAULT_REF_ENERGY_ERG,
        help="Fit and reference line are applied for energies >= this value (ergs)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df[ENERGY_COL] = df[ENERGY_COL].apply(clean_float)
    df = df.dropna(subset=[ENERGY_COL]).reset_index(drop=True)
    df = df[df[ENERGY_COL] > 0]

    combined = df.iloc[: args.split_index][ENERGY_COL].values
    E, N = cumulative_distribution(combined)

    # -----------------------------
    # Fit: select data to the right of reference energy
    # -----------------------------
    mask = (E >= args.ref_energy) & (N > 0)
    E_fit_data = E[mask]
    N_fit_data = N[mask]

    if E_fit_data.size < 3:
        raise SystemExit(
            f"Not enough points to fit after ref energy {args.ref_energy:.3e}. "
            f"Have {E_fit_data.size} points; need at least 3."
        )

    x = np.log10(E_fit_data)
    y = np.log10(N_fit_data)

    # Initial guess: gamma < 0 for a decreasing cumulative distribution.
    p0 = (float(np.max(y)), -1.0)

    popt, pcov = curve_fit(
        powerlaw_log10_model,
        x,
        y,
        p0=p0,
        method="lm",  # least-squares (Levenberg–Marquardt)
        maxfev=100000,
    )

    log10_A, gamma = popt
    perr = np.sqrt(np.diag(pcov))
    log10_A_err, gamma_err = perr

    y_pred = powerlaw_log10_model(x, log10_A, gamma)
    rmse_log10 = float(np.sqrt(np.mean((y - y_pred) ** 2)))

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(6, 4))

    plt.plot(E, N, drawstyle="steps-post", color="red")

    plt.axvline(
        args.ref_energy,
        color="blue",
        linestyle="--",
        linewidth=1.2,
    )

    E_fit_line = np.logspace(np.log10(args.ref_energy), np.log10(np.max(E)), 300)
    N_fit_line = 10 ** powerlaw_log10_model(np.log10(E_fit_line), log10_A, gamma)

    plt.plot(
        E_fit_line,
        N_fit_line,
        color="black",
        linewidth=1.5,
        label=f"Power-law fit: $\\gamma$={gamma:.2f}±{gamma_err:.2f}",
    )

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel("Isotropic Burst Energy (ergs)")
    plt.ylabel("N(>E)")

    plt.legend(frameon=False)

    #text = (
    #    f"Fit region: E ≥ {args.ref_energy:.2e} ergs\n"
    #    f"γ = {gamma:.3f} ± {gamma_err:.3f}\n"
    #    f"RMSE(log10 N) = {rmse_log10:.3f}"
    #)
    #plt.gca().text(
        #0.05,
        #0.05,
        #text,
        #transform=plt.gca().transAxes,
        #fontsize=9,
        #va="bottom",
        #ha="left",
    #)

    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    plt.close()

    print(f"Saved: {args.output}")
    print(f"Fit results (E >= {args.ref_energy:.3e}):")
    print("  Model: N(>E) ∝ E^gamma")
    print(f"  gamma = {gamma:.6f} +/- {gamma_err:.6f}")
    print(f"  log10(A) = {log10_A:.6f} +/- {log10_A_err:.6f}")
    print(f"  RMSE(log10 N) = {rmse_log10:.6f}")


if __name__ == "__main__":
    main()
