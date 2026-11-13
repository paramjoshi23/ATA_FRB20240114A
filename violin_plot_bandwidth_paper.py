#!/usr/bin/env python3
""" 
Split violin plot of bandwidth vs center frequency (binned into 4 bins).

Left half  = Combined bursts
Right half = Sub-bursts

Features:
- Fixed frequency tick labels on x-axis (1000–4500 MHz, step 500 MHz)
- Split violins
- Box summaries
- Mean ± std overlay
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
BANDWIDTH_COL = "3-sigma Bandwidth (MHz)"

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
    parser.add_argument("--output", type=Path, default=Path("violin_plot_bandwidth_FINAL.png"))
    parser.add_argument("--split-index", type=int, default=98,
                        help="First N rows are Combined bursts; rest Sub-bursts")
    args = parser.parse_args()

    # -----------------------------
    # Load data
    # -----------------------------
    df = pd.read_csv(args.input)

    df[CENTERF_COL] = df[CENTERF_COL].apply(clean_float)
    df[BANDWIDTH_COL] = df[BANDWIDTH_COL].apply(clean_float)

    df = df.dropna(subset=[CENTERF_COL, BANDWIDTH_COL]).reset_index(drop=True)

    # -----------------------------
    # Split burst types
    # -----------------------------
    df["Type"] = "Sub-burst"
    df.loc[: args.split_index - 1, "Type"] = "Combined"

    # -----------------------------
    # Create 4 fixed bins across 1000–4500 MHz
    # -----------------------------
    bins = np.linspace(FREQ_START_MHZ, FREQ_END_MHZ, 5)
    df["bin_index"] = np.digitize(df[CENTERF_COL], bins) - 1
    df["bin_index"] = df["bin_index"].clip(0, 3)

    # Uniform x-axis tick labels (independent of bin count)
    freq_ticks = list(range(FREQ_START_MHZ, FREQ_END_MHZ + FREQ_STEP_MHZ, FREQ_STEP_MHZ))

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(5, 4))
    sns.set_style("whitegrid")

    sns.violinplot(
        data=df,
        x="bin_index",
        y=BANDWIDTH_COL,
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
        y=BANDWIDTH_COL,
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
    # Mean ± std overlay
    # -----------------------------
    grouped = df.groupby(["bin_index", "Type"])

    for (bin_idx, burst_type), group in grouped:
        mean = group[BANDWIDTH_COL].mean()
        std = group[BANDWIDTH_COL].std()

        offset = -0.15 if burst_type == "Combined" else 0.15

        plt.errorbar(
            bin_idx + offset,
            mean,
            yerr=std,
            fmt="o",
            color="black",
            markersize=4,
            capsize=3,
            zorder=5,
        )

    # -----------------------------
    # Formatting
    # -----------------------------
    tick_positions = np.linspace(0, 3, len(freq_ticks))
    plt.xticks(ticks=tick_positions, labels=[str(v) for v in freq_ticks])
    plt.xlim(-0.5, 3.5)

    ax = plt.gca()
    ax.tick_params(axis="both", which="both", bottom=True, top=False, left=True, right=False,
                   length=4, width=1.2, labelsize=10)

    # Make axis spines bolder for stronger borders
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
        spine.set_color("black")

    plt.ylim(bottom=100)

    plt.xlabel("Center Frequency (MHz)", fontsize=14, fontweight="bold")
    plt.ylabel("Bandwidth (MHz)", fontsize=14, fontweight="bold")

    # -----------------------------
    # Custom clean legend
    # -----------------------------
    legend_elements = [
        Patch(facecolor="red", alpha=0.8, edgecolor="black", label="Combined"),
        Patch(facecolor="blue", alpha=0.8, edgecolor="black", label="Sub-burst"),
        Line2D([0], [0],
               marker='o',
               color='black',
               linestyle='None',
               markersize=5,
               label='Mean ± 1σ')
    ]

    plt.legend(handles=legend_elements, frameon=False)

    plt.tight_layout()
    plt.savefig(args.output, dpi=600)
    plt.close()

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()