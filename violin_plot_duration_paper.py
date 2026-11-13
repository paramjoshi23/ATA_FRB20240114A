#!/usr/bin/env python3
"""
Split violin plot of duration vs center frequency (binned into 4 bins).

Left half  = Combined bursts
Right half = Sub-bursts

Features:
- Uniform x-axis labels from 1000–4500 MHz (step 500 MHz)
- Split violins
- Box summaries
- Mean ± 1σ overlay (black dot + error bar)
- Clean custom legend
- No negative duration extension
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
DURATION_COL = "3-sigma Duration (ms)"

FREQ_START_MHZ = 1000
FREQ_END_MHZ = 4500
FREQ_STEP_MHZ = 500


def clean_float(x):
    try:
        val = float(str(x).strip())
        if math.isfinite(val):
            return val
    except Exception:
        pass
    return np.nan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument("--output", type=Path, default=Path("violin_plot_duration_FINAL.png"))
    parser.add_argument(
        "--split-index",
        type=int,
        default=98,
        help="First N rows are Combined bursts; rest are Sub-bursts",
    )
    args = parser.parse_args()

    # -----------------------------
    # Load and clean data
    # -----------------------------
    df = pd.read_csv(args.input)

    df[CENTERF_COL] = df[CENTERF_COL].apply(clean_float)
    df[DURATION_COL] = df[DURATION_COL].apply(clean_float)

    df = df.dropna(subset=[CENTERF_COL, DURATION_COL]).reset_index(drop=True)

    # Log-scale plots require strictly positive y values
    df = df[df[DURATION_COL] > 0].reset_index(drop=True)
    if df.empty:
        raise ValueError(
            f"No positive values found in '{DURATION_COL}' after cleaning; cannot use log y-scale."
        )

    # -----------------------------
    # Label burst types
    # -----------------------------
    df["Type"] = "Sub-burst"
    df.loc[: args.split_index - 1, "Type"] = "Combined"

    # -----------------------------
    # Create 4 frequency bins across 1000–4500 MHz
    # -----------------------------
    bins = np.linspace(FREQ_START_MHZ, FREQ_END_MHZ, 5)

    df["bin_index"] = np.digitize(df[CENTERF_COL], bins) - 1
    df["bin_index"] = df["bin_index"].clip(0, 3)

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(5, 4))
    sns.set_style("whitegrid")

    sns.violinplot(
        data=df,
        x="bin_index",
        y=DURATION_COL,
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
        y=DURATION_COL,
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
    # Mean ± 1σ overlay
    # -----------------------------
    grouped = df.groupby(["bin_index", "Type"])

    y_floor = df[DURATION_COL].min()

    for (bin_idx, burst_type), group in grouped:
        mean = group[DURATION_COL].mean()
        std = group[DURATION_COL].std()

        if not np.isfinite(mean) or mean <= 0:
            continue

        # On a log scale, keep the lower end of the errorbar > 0
        if not np.isfinite(std) or std < 0:
            std = 0.0
        lower_err = min(std, max(0.0, mean - (0.5 * y_floor)))
        upper_err = std

        offset = -0.15 if burst_type == "Combined" else 0.15

        plt.errorbar(
            bin_idx + offset,
            mean,
            yerr=[[lower_err], [upper_err]],
            fmt="o",
            color="black",
            markersize=5,
            capsize=3,
            elinewidth=1.0,
            zorder=5,
        )

    # -----------------------------
    # Axis formatting
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

    ax.set_yscale("log")
    ax.set_ylim(bottom=0.5 * y_floor)

    plt.xlabel("Center Frequency (MHz)", fontsize=14, fontweight="bold")
    plt.ylabel("Duration (ms)", fontsize=14, fontweight="bold")

    # -----------------------------
    # Custom legend
    # -----------------------------
    legend_elements = [
        Patch(facecolor="red", alpha=0.8, edgecolor="black", label="Combined"),
        Patch(facecolor="blue", alpha=0.8, edgecolor="black", label="Sub-burst"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="black",
            linestyle="None",
            markersize=5,
            label="Mean ± 1σ",
        ),
    ]

    plt.legend(handles=legend_elements, frameon=False)

    plt.tight_layout()
    plt.savefig(args.output, dpi=600)
    plt.close()

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()