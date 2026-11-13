#!/usr/bin/env python3
"""Cumulative spectral energy density distribution with a single power-law fit.

- Uses only combined bursts (first N rows; excludes sub-bursts).
- Spectral energy density is defined as isotropic burst energy divided by
  bandwidth in Hz, giving units of erg/Hz.
- Plots N(>SED) on log-log axes.
- Fits one power law above a reference threshold.
- Adds a vertical reference line at a chosen spectral energy density.

Power-law model:
        N(>SED) = A * SED^{gamma}

The fits are performed on:
        log10 N = log10 A + gamma * log10 SED
"""

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from scipy.optimize import curve_fit
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "scipy is required for curve_fit. Install it with: pip install scipy\n"
        f"Original import error: {exc}"
    )


DEFAULT_INPUT = "FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2.csv"
ENERGY_COL = "Isotropic Burst Energy (ergs)"
BANDWIDTH_COL = "3-sigma Bandwidth (MHz)"
DEFAULT_REF_ENERGY_ERG = 1.28e39
DEFAULT_REF_BANDWIDTH_MHZ = 1344.0
DEFAULT_REF_SED = DEFAULT_REF_ENERGY_ERG / (DEFAULT_REF_BANDWIDTH_MHZ * 1.0e6)


def clean_float(x):
    try:
        val = float(str(x).strip())
        if math.isfinite(val):
            return val
    except Exception:
        pass
    return np.nan


def cumulative_distribution(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns sorted values and cumulative N(>x) counts."""
    values = np.sort(values)
    count = len(values)
    cumulative = np.arange(count, 0, -1)
    return values, cumulative


def powerlaw_log10_model(log10_x: np.ndarray, log10_A: float, gamma: float) -> np.ndarray:
    """log10 N = log10 A + gamma * log10 x"""
    return log10_A + gamma * log10_x


def format_scientific_latex(value: float) -> str:
    exponent = int(math.floor(math.log10(value)))
    mantissa = value / (10 ** exponent)
    return rf"{mantissa:.1f}\times10^{{{exponent}}}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("cumulative_spectral_energy_density_distribution_powerlaw_fit.png"),
    )
    parser.add_argument(
        "--split-index",
        type=int,
        default=98,
        help="First N rows are Combined bursts; rest Sub-bursts",
    )
    parser.add_argument(
        "--ref-sed",
        type=float,
        default=DEFAULT_REF_SED,
        help="Fit and reference line are applied for SED >= this value (erg/Hz)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df[ENERGY_COL] = df[ENERGY_COL].apply(clean_float)
    df[BANDWIDTH_COL] = df[BANDWIDTH_COL].apply(clean_float)
    df = df.dropna(subset=[ENERGY_COL, BANDWIDTH_COL]).reset_index(drop=True)

    df = df[(df[ENERGY_COL] > 0) & (df[BANDWIDTH_COL] > 0)]

    bandwidth_hz = df[BANDWIDTH_COL].values * 1e6
    sed = df[ENERGY_COL].values / bandwidth_hz

    combined_sed = sed[: args.split_index]
    sed_values, cumulative_counts = cumulative_distribution(combined_sed)
    obs_hours = 1167.0
    cumulative_rate = cumulative_counts / obs_hours

    fit_mask = sed_values >= args.ref_sed
    sed_fit_data = sed_values[fit_mask]
    n_fit_data = cumulative_rate[fit_mask]

    if sed_fit_data.size < 3:
        raise SystemExit(
            f"Not enough points for the power-law fit above {args.ref_sed:.3e}. "
            f"Need at least 3 points, found {sed_fit_data.size}."
        )

    x_fit = np.log10(sed_fit_data)
    y_fit = np.log10(n_fit_data)
    p0_fit = (float(np.max(y_fit)), -1.0)

    popt_fit, pcov_fit = curve_fit(
        powerlaw_log10_model,
        x_fit,
        y_fit,
        p0=p0_fit,
        method="lm",
        maxfev=100000,
    )

    log10_A_fit, gamma_fit = popt_fit
    perr_fit = np.sqrt(np.diag(pcov_fit))
    log10_A_fit_err, gamma_fit_err = perr_fit
    y_pred_fit = powerlaw_log10_model(x_fit, log10_A_fit, gamma_fit)
    rmse_fit = float(np.sqrt(np.mean((y_fit - y_pred_fit) ** 2)))

    # Plot
    plt.figure(figsize=(7, 5))

    plt.plot(sed_values, cumulative_rate, drawstyle="steps-post", color="darkred", linewidth=2.0, label="ATA Data")

    plt.axvline(
        args.ref_sed,
        color="navy",
        linestyle="--",
        linewidth=1.8,
        alpha=0.95,
        zorder=4,
        label=rf"Completeness: ${format_scientific_latex(args.ref_sed)}$ erg/Hz",
    )

    sed_fit_line = np.logspace(np.log10(args.ref_sed), np.log10(np.max(sed_fit_data)), 200)
    n_fit_line = 10 ** powerlaw_log10_model(np.log10(sed_fit_line), log10_A_fit, gamma_fit)

    plt.plot(
        sed_fit_line,
        n_fit_line,
        color="purple",
        linestyle="-",
        linewidth=2.0,
        label=f"ATA Power-law fit: $\\gamma$ = {gamma_fit:.2f} ± {gamma_fit_err:.2f}",
    )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(left=min(sed_values.min(), args.ref_sed) * 0.7, right=sed_values.max() * 1.05)

    plt.xlabel("Spectral Energy Density (erg/Hz)", fontsize=12, fontweight="bold")
    plt.ylabel(r"Cumulative Burst Rate, $\mathbf{R(>SED)\ (hr^{-1})}$", fontsize=12, fontweight="bold")
    plt.tick_params(axis="y", labelsize=10)
    plt.setp(plt.gca().get_yticklabels(), fontweight="bold")
    plt.legend(frameon=True, fontsize=10)

    plt.tight_layout()
    output_path = Path("cumulative_spectral_energy_density_dist_powerlaw_fit_ata_FINAL.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")
    print(f"\nSingle power-law fit for SED >= {args.ref_sed:.3e}:")
    print(f"  Points: {sed_fit_data.size}")
    print(f"  Model: R(>SED) proportional to SED^gamma")
    print(f"  gamma = {gamma_fit:.6f} +/- {gamma_fit_err:.6f}")
    print(f"  log10(A) = {log10_A_fit:.6f} +/- {log10_A_fit_err:.6f}")
    print(f"  RMSE(log10 N) = {rmse_fit:.6f}")


if __name__ == "__main__":
    main()