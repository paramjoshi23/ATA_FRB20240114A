#!/usr/bin/env python3
"""
Split violin plot of isotropic burst energy vs center frequency (4 bins).

Features:
- 4 frequency bins across 1000–4500 MHz
- Uniform x-axis labels from 1000–4500 MHz (step 500 MHz)
- Split violins (Combined vs Sub-burst)
- Box summaries
- Geometric mean ± 1σ (computed in log10 space)
- Log-scale y-axis
- Clean custom legend
"""

import argparse
from pathlib import Path
import math

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


DEFAULT_INPUT = "FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2.csv"
CENTERF_COL = "center_f"
ENERGY_COL = "Isotropic Burst Energy (ergs)"

FREQ_START_MHZ = 1000
FREQ_END_MHZ = 4500
FREQ_STEP_MHZ = 500


def clean_float(x):
    try:
        val = float(str(x).strip())
        if math.isfinite(val):
            return val
    except:
        pass
    return np.nan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument("--output", type=Path, default=Path("violin_plot_energy_FINAL.png"))
    parser.add_argument("--split-index", type=int, default=98,
                        help="First N rows are Combined bursts; rest Sub-bursts")
    args = parser.parse_args()

    # -----------------------------
    # Load data
    # -----------------------------
    df = pd.read_csv(args.input)

    df[CENTERF_COL] = df[CENTERF_COL].apply(clean_float)
    df[ENERGY_COL] = df[ENERGY_COL].apply(clean_float)

    df = df.dropna(subset=[CENTERF_COL, ENERGY_COL]).reset_index(drop=True)

    # Remove non-positive energy (required for log)
    df = df[df[ENERGY_COL] > 0]

    # -----------------------------
    # Split burst types
    # -----------------------------
    df["Type"] = "Sub-burst"
    df.loc[: args.split_index - 1, "Type"] = "Combined"

    # -----------------------------
    # Create 4 bins across 1000–4500 MHz
    # -----------------------------
    bins = np.linspace(FREQ_START_MHZ, FREQ_END_MHZ, 5)

    df["bin_index"] = np.digitize(df[CENTERF_COL], bins) - 1
    df["bin_index"] = df["bin_index"].clip(0, 3)

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(8, 5))
    sns.set_style("whitegrid")

    sns.violinplot(
        data=df,
        x="bin_index",
        y=ENERGY_COL,
        hue="Type",
        split=True,
        inner=None,
        cut=0,
        palette={"Combined": "red", "Sub-burst": "blue"},
        alpha=0.9,
        linewidth=0.8,
    )

    sns.boxplot(
        data=df,
        x="bin_index",
        y=ENERGY_COL,
        hue="Type",
        width=0.2,
        showcaps=True,
        boxprops={"facecolor": "none", "edgecolor": "black", "alpha": 0.8},
        showfliers=False,
        whiskerprops={"linewidth": 1, "color": "black", "alpha": 0.8},
        capprops={"color": "black", "alpha": 0.8},
        legend=False,
        dodge=True,
    )

    # -----------------------------
    # Geometric mean ± 1σ (log space)
    # -----------------------------
    grouped = df.groupby(["bin_index", "Type"])

    for (bin_idx, burst_type), group in grouped:

        log_vals = np.log10(group[ENERGY_COL])

        mean_log = log_vals.mean()
        std_log = log_vals.std()

        geom_mean = 10 ** mean_log
        lower = 10 ** (mean_log - std_log)
        upper = 10 ** (mean_log + std_log)

        yerr = [[geom_mean - lower], [upper - geom_mean]]

        offset = -0.15 if burst_type == "Combined" else 0.15

        plt.errorbar(
            bin_idx + offset,
            geom_mean,
            yerr=yerr,
            fmt="o",
            color="black",
            markersize=4,
            capsize=3,
            zorder=5,
        )

    # -----------------------------
    # Formatting
    # -----------------------------
    freq_ticks = list(range(FREQ_START_MHZ, FREQ_END_MHZ + FREQ_STEP_MHZ, FREQ_STEP_MHZ))
    tick_positions = np.linspace(0, 3, len(freq_ticks))
    plt.xticks(ticks=tick_positions, labels=[str(v) for v in freq_ticks])
    plt.xlim(-0.5, 3.5)

    ax = plt.gca()
    ax.tick_params(axis="x", which="both", bottom=True, top=False, length=4, width=0.8)

    # Make axis spines bolder
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
        spine.set_color("black")

    plt.yscale("log")

    plt.xlabel("Center Frequency (MHz)", fontsize=14, fontweight="bold")
    plt.ylabel("Isotropic Burst Energy (ergs)", fontsize=14, fontweight="bold")

    # -----------------------------
    # Custom legend
    # -----------------------------
    legend_elements = [
        Patch(facecolor="red", alpha=0.8, edgecolor="black", label="Combined"),
        Patch(facecolor="blue", alpha=0.8, edgecolor="black", label="Sub-burst"),
        Line2D([0], [0],
               marker='o',
               color='black',
               linestyle='None',
               markersize=5,
               label='Geometric Mean ± 1σ')
    ]

    plt.legend(handles=legend_elements, frameon=False, loc="upper left")

    plt.tight_layout()
    plt.savefig(args.output, dpi=600)
    plt.close()

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()