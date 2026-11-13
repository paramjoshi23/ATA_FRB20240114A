#!/usr/bin/env python3
"""
Violin plot of drift-rate magnitude vs center frequency.

- Uses only first N rows (combined bursts)
- Keeps only negative drift rates and plots their magnitudes (first quadrant)
- Removes outliers by magnitude: |drift rate| < max_drift
- Frequency-binned violins
- Boxplot inside violins
- Mean ± std overlaid
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import mean, stdev
from matplotlib.ticker import FuncFormatter
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


CENTERF_COL = "center_f"
SLOPE_COL = "slope (mhz/ms)"
DEFAULT_INPUT = "FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv"

FREQ_START_MHZ = 1000
FREQ_END_MHZ = 4500
FREQ_STEP_MHZ = 500


def _to_float(val):
    try:
        x = float(val)
        if not math.isfinite(x):
            return None
        return x
    except Exception:
        return None


def read_data(csv_path: Path, n_combined: int, max_drift: float):
    center_f = []
    slopes = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if i >= n_combined:
                break

            cf = _to_float(row.get(CENTERF_COL))
            sl = _to_float(row.get(SLOPE_COL))

            if cf is None or sl is None:
                continue

            # Keep only negative drift rates
            if sl >= 0:
                continue

            # OUTLIER CUT (by magnitude)
            if abs(sl) >= max_drift:
                continue

            center_f.append(cf)
            slopes.append(-sl)

    return np.array(center_f), np.array(slopes)


def setup_style():
    mpl.rcParams.update(
        {
            "figure.figsize": (5.0, 4.0),
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.8,
        }
    )


def make_violin_plot(center_f, slopes, bins, output, title=None):

    setup_style()

    edges = np.linspace(FREQ_START_MHZ, FREQ_END_MHZ, bins + 1)

    bin_idx = np.digitize(center_f, edges) - 1
    bin_idx = np.clip(bin_idx, 0, bins - 1)

    binned_slopes = []
    bin_centers = []

    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        vals = slopes[bin_idx == i]
        binned_slopes.append(vals)
        bin_centers.append((lo + hi) / 2)

    fig, ax = plt.subplots(constrained_layout=True)

    vp = ax.violinplot(
        binned_slopes,
        positions=bin_centers,
        widths=(edges[1] - edges[0]) * 0.6,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )

    for body in vp["bodies"]:
        #body.set_facecolor("#0F808A")
        body.set_facecolor("blue")
        body.set_edgecolor("black")
        body.set_alpha(0.7)

    ax.boxplot(
        binned_slopes,
        positions=bin_centers,
        widths=(edges[1] - edges[0]) * 0.25,
        patch_artist=True,
        showfliers=False,
        boxprops=dict(facecolor="white", edgecolor="black", linewidth=0.8),
        medianprops=dict(color="black", linewidth=1.0),
        whiskerprops=dict(color="black", linewidth=0.8),
        capprops=dict(color="black", linewidth=0.8),
    )

    means = []
    stds = []

    for vals in binned_slopes:
        if len(vals) > 0:
            means.append(mean(vals))
            stds.append(stdev(vals) if len(vals) > 1 else 0.0)
        else:
            means.append(np.nan)
            stds.append(np.nan)

    ax.errorbar(
        bin_centers,
        means,
        yerr=stds,
        fmt="o",
        color="black",
        markersize=4,
        capsize=3,
        label="Mean ± 1σ",
        zorder=10,
    )


    # Make axis spines bolder
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
        spine.set_color("black")

    ax.set_xlabel("Center Frequency (MHz)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Drift Rate (MHz ms$^{-1}$)", fontsize=14, fontweight="bold")

    # Keep the plot in the first quadrant, but label tick values as negative.
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: "0" if y == 0 else f"-{y:g}")
    )

    freq_ticks = list(range(FREQ_START_MHZ, FREQ_END_MHZ + FREQ_STEP_MHZ, FREQ_STEP_MHZ))
    # Add horizontal padding so there's space around the first/last ticks
    margin = FREQ_STEP_MHZ / 2
    ax.set_xlim(FREQ_START_MHZ - margin, FREQ_END_MHZ + margin)
    ax.set_xticks(freq_ticks)
    ax.set_xticklabels([str(v) for v in freq_ticks])
    ax.tick_params(axis="x", which="both", bottom=True, top=False, length=4, width=0.8)

    if title:
        ax.set_title(title)

    ax.grid(True, alpha=0.3)
    #ax.minorticks_on()
    ax.legend(frameon=False)

    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument("--output", type=Path, default=Path("violin_plot_drift_rate_FINAL.png"))
    parser.add_argument("--bins", type=int, default=4)
    parser.add_argument("--n-combined", type=int, default=98)

    parser.add_argument(
        "--max-drift",
        type=float,
        default=1000.0,
        help="Maximum |drift rate| to keep (MHz ms^-1)"
    )

    parser.add_argument("--title", type=str, default=None)

    args = parser.parse_args()

    center_f, slopes = read_data(
        args.input,
        n_combined=args.n_combined,
        max_drift=args.max_drift,
    )

    if len(slopes) == 0:
        raise ValueError("No data left after outlier cut")

    make_violin_plot(
        center_f=center_f,
        slopes=slopes,
        bins=args.bins,
        output=args.output,
        title=args.title,
    )

    print(f"Outlier cut applied: |drift rate| < {args.max_drift}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()