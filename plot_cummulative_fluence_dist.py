#!/usr/bin/env python3
"""
Cumulative fluence distribution.

Plots N(>F) for:
- Combined bursts
- Sub-bursts

Log-log scale (recommended for power-law testing).
"""

import argparse
from pathlib import Path
import math

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


DEFAULT_INPUT = "FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2.csv"
FLUENCE_COL = "Fluence (Jy-ms)"


def clean_float(x):
    try:
        val = float(str(x).strip())
        if math.isfinite(val):
            return val
    except:
        pass
    return np.nan


def cumulative_distribution(values):
    """
    Returns sorted values and cumulative N(>X).
    """
    values = np.sort(values)
    N = len(values)
    cumulative = np.arange(N, 0, -1)  # N, N-1, ..., 1
    return values, cumulative


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(DEFAULT_INPUT))
    parser.add_argument("--output", type=Path,
                        default=Path("cumulative_fluence_distribution.png"))
    parser.add_argument("--split-index", type=int, default=98,
                        help="First N rows are Combined bursts; rest Sub-bursts")
    args = parser.parse_args()

    # -----------------------------
    # Load data
    # -----------------------------
    df = pd.read_csv(args.input)

    df[FLUENCE_COL] = df[FLUENCE_COL].apply(clean_float)
    df = df.dropna(subset=[FLUENCE_COL]).reset_index(drop=True)

    # Remove non-physical values
    df = df[df[FLUENCE_COL] > 0]

    # -----------------------------
    # Split burst types
    # -----------------------------
    df["Type"] = "Sub-burst"
    df.loc[: args.split_index - 1, "Type"] = "Combined"

    combined = df[df["Type"] == "Combined"][FLUENCE_COL].values
    subburst = df[df["Type"] == "Sub-burst"][FLUENCE_COL].values

    # -----------------------------
    # Compute cumulative N(>F)
    # -----------------------------
    F_comb, N_comb = cumulative_distribution(combined)
    F_sub, N_sub = cumulative_distribution(subburst)

    # -----------------------------
    # Plot
    # -----------------------------
    plt.figure(figsize=(6, 4))

    plt.plot(F_comb, N_comb, drawstyle="steps-post",
             color="red", label="Combined")

    plt.plot(F_sub, N_sub, drawstyle="steps-post",
             color="navy", label="Sub-burst")

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel("Fluence (Jy-ms)")
    plt.ylabel("N(>F)")

    plt.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    plt.close()

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()