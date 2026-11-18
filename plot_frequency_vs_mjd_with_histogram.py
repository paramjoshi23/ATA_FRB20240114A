#!/usr/bin/env python3
"""Multi-telescope frequency vs MJD plot with a sideways on-sky-time histogram.

Left panel: ATA filterbank coverage plus ATA, Effelsberg, and Murriyang bursts.
Right panel: observing hours vs frequency, using the same centre frequencies,
bandwidths, and on-sky hours as plot_OnSky_time_frequency_histogram.py.

Outputs:
  - frb20240114a_frequency_vs_mjd_with_histogram.png / .pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_frequency_common import (
    EFFELSBERG_CSV,
    FILTERBANK_JSON,
    PARKES_CSV,
    PROPERTIES_JSON,
    apply_publication_style,
    draw_ata_bands,
    load_ata_bands,
    load_ata_bursts,
    load_burst_csv,
    load_json,
    style_axes,
)

ROOT = Path(__file__).resolve().parent
OUT_PNG = ROOT / "frb20240114a_frequency_vs_mjd_with_histogram.png"
OUT_PDF = ROOT / "frb20240114a_frequency_vs_mjd_with_histogram.pdf"

# On-sky hours and centre frequencies from plot_OnSky_time_frequency_histogram.py
ONSKY_HOURS = [336.4, 525.69, 369.48, 180.16, 155.62, 155.62, 155.0, 155.0, 150.5, 150.5]
ONSKY_FREQS = [1236, 1908, 2580, 3252, 3924, 4596, 5268, 5940, 6612, 7284]
HALF_BW_MHZ = 336.0
HIST_BINS = np.linspace(900, 7620, 11)


def onsky_hours_per_bin(
    freqs: list[float] | np.ndarray,
    hours: list[float] | np.ndarray,
    bins: np.ndarray,
    half_bw: float = HALF_BW_MHZ,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Distribute each observation's hours uniformly across its 672 MHz band."""
    bin_hours = np.zeros(len(bins) - 1)
    bin_left = bins[:-1]
    bin_right = bins[1:]
    for f, h in zip(freqs, hours):
        int_left = f - half_bw
        int_right = f + half_bw
        overlaps = np.maximum(
            0.0,
            np.minimum(bin_right, int_right) - np.maximum(bin_left, int_left),
        )
        frac = overlaps / (2.0 * half_bw)
        bin_hours += h * frac
    return bin_left, bin_right, bin_hours


def main() -> None:
    apply_publication_style()

    fb = load_json(FILTERBANK_JSON)
    props = load_json(PROPERTIES_JSON)
    ata_mjd, ata_fc = load_ata_bursts(fb, props)
    bands = load_ata_bands(fb)

    if not EFFELSBERG_CSV.is_file() or not PARKES_CSV.is_file():
        raise SystemExit(
            "Missing burst CSV catalogues. Run: python build_burst_catalogs.py"
        )
    eff_mjd, eff_fc = load_burst_csv(EFFELSBERG_CSV)
    mur_mjd, mur_fc = load_burst_csv(PARKES_CSV)

    fig, (ax, axh) = plt.subplots(
        1,
        2,
        figsize=(10.8, 5.6),
        dpi=150,
        sharey=True,
        layout="constrained",
        gridspec_kw={"width_ratios": [4.2, 1.15]},
    )

    draw_ata_bands(ax, bands)
    ax.scatter(
        eff_mjd,
        eff_fc,
        marker="o",
        s=14,
        c="#d62728",
        edgecolors="black",
        linewidths=0.25,
        alpha=0.40,
        zorder=3,
        label="Effelsberg",
    )
    ax.scatter(
        mur_mjd,
        mur_fc,
        marker="D",
        s=12,
        c="#377eb8",
        edgecolors="black",
        linewidths=0.25,
        alpha=0.40,
        zorder=3,
        label="Murriyang",
    )
    ax.scatter(
        ata_mjd,
        ata_fc,
        marker="*",
        s=140,
        c="gold",
        edgecolors="black",
        linewidths=0.5,
        alpha=1.0,
        zorder=5,
        label="ATA",
    )

    all_mjd = list(ata_mjd) + list(eff_mjd) + list(mur_mjd)
    all_fc = list(ata_fc) + list(eff_fc) + list(mur_fc)
    ax.set_xlim(min(60330, min(all_mjd) - 5), max(60620, max(all_mjd) + 5))
    ax.set_ylim(min(850, min(all_fc) - 150), max(7700, max(all_fc) + 150))
    ax.set_xlabel("MJD", fontweight="bold")
    ax.set_ylabel("Frequency (MHz)", fontweight="bold")
    ax.grid(True, linestyle=":", linewidth=0.5, color="0.5", alpha=0.4, zorder=0)
    style_axes(ax)
    leg = ax.legend(
        loc="upper left",
        framealpha=1.0,
        fancybox=False,
        edgecolor="black",
        frameon=True,
        fontsize=12,
    )
    leg.get_frame().set_linewidth(1.0)

    bin_left, bin_right, bin_hours = onsky_hours_per_bin(
        ONSKY_FREQS, ONSKY_HOURS, HIST_BINS
    )
    heights = bin_right - bin_left
    axh.barh(
        bin_left,
        bin_hours,
        height=heights,
        align="edge",
        color="#1b9e77",
        edgecolor="#0a2e24",
        linewidth=0.8,
        alpha=0.75,
        zorder=2,
    )
    axh.set_xlabel("On-sky time (h)", fontweight="bold")
    axh.set_xlim(0, max(bin_hours) * 1.12)
    axh.grid(True, axis="x", linestyle=":", linewidth=0.5, color="0.5", alpha=0.4, zorder=0)
    axh.tick_params(axis="y", which="both", left=False, labelleft=False)
    style_axes(axh)

    fig.savefig(OUT_PNG, dpi=300, facecolor="white")
    fig.savefig(OUT_PDF, facecolor="white")
    plt.close(fig)
    print(
        f"Wrote {OUT_PNG} and {OUT_PDF} "
        f"(bursts: ATA={len(ata_mjd)}, Effelsberg={len(eff_mjd)}, "
        f"Murriyang={len(mur_mjd)}; histogram total {bin_hours.sum():.1f} h)."
    )


if __name__ == "__main__":
    main()
