"""Shared helpers and publication styling for FRB20240114A frequency vs MJD plots."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
FILTERBANK_JSON = ROOT / "Filterbank_FRB_Main_JSON_database.json"
PROPERTIES_JSON = ROOT / "NEW_FINAL_FRB_properties_JSON.json"
EFFELSBERG_CSV = ROOT / "effelsberg_bursts.csv"
PARKES_CSV = ROOT / "parkes_bursts.csv"

STREAM_KEYS = ("spliced_loc", "spliced_lob", "spliced_loa")
MJD_KEY = "Burst_MJD (Topocentric)"
CENTER_F_KEY = "center_f"


def freq_range_mhz(fch1: float, nchans: int, foff: float) -> tuple[float, float]:
    f0 = fch1
    f1 = fch1 + (nchans - 1) * foff
    return (min(f0, f1), max(f0, f1))


def mjd_span(stream: dict) -> tuple[float, float]:
    t0 = float(stream["tstart"])
    dt_days = float(stream["nsamples"]) * float(stream["tsamp"]) / 86400.0
    return t0, t0 + dt_days


def resolve_props_key(name: str, props: dict) -> str | None:
    if name in props:
        return name
    for suffix in ("_1", "_2", "_3"):
        k = f"{name}{suffix}"
        if k in props:
            return k
    return None


def burst_point_for_name(name: str, props: dict) -> tuple[float, float] | None:
    key = resolve_props_key(name, props)
    if key is None:
        return None
    block = props[key].get(key)
    if not isinstance(block, dict):
        return None
    mjd = block.get(MJD_KEY)
    cf = block.get(CENTER_F_KEY)
    if mjd is None or cf is None:
        return None
    return float(mjd), float(cf)


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def load_burst_csv(path: Path) -> tuple[list[float], list[float]]:
    mjd_list: list[float] = []
    fc_list: list[float] = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            mjd_list.append(float(row["mjd"]))
            fc_list.append(float(row["center_frequency_mhz"]))
    return mjd_list, fc_list


def load_ata_bursts(fb: dict, props: dict) -> tuple[list[float], list[float]]:
    unresolved: list[str] = []
    mjd_list: list[float] = []
    fc_list: list[float] = []
    for entry in fb.values():
        b = entry.get("Bursts")
        if not isinstance(b, dict):
            continue
        for bn in b.get("FRB_names") or []:
            pt = burst_point_for_name(bn, props)
            if pt is None:
                unresolved.append(bn)
            else:
                mjd, cf = pt
                mjd_list.append(mjd)
                fc_list.append(cf)
    if unresolved:
        raise SystemExit(f"Could not resolve ATA burst MJD/center_f for: {sorted(set(unresolved))}")
    return mjd_list, fc_list


def load_ata_bands(fb: dict) -> list[tuple[float, float, float, float]]:
    bands: list[tuple[float, float, float, float]] = []
    for entry in fb.values():
        for sk in STREAM_KEYS:
            stream = entry.get(sk)
            if not isinstance(stream, dict):
                continue
            f_lo, f_hi = freq_range_mhz(
                float(stream["fch1"]),
                int(stream["nchans"]),
                float(stream["foff"]),
            )
            mjd_lo, mjd_hi = mjd_span(stream)
            bands.append((mjd_lo, mjd_hi, f_lo, f_hi))
    return bands


def draw_ata_bands(ax: plt.Axes, bands: list[tuple[float, float, float, float]]) -> int:
    teal = "#1b9e77"
    teal_edge = "#0a2e24"
    for mjd_lo, mjd_hi, f_lo, f_hi in bands:
        ax.add_patch(
            Rectangle(
                (mjd_lo, f_lo),
                mjd_hi - mjd_lo,
                f_hi - f_lo,
                facecolor=teal,
                edgecolor=teal_edge,
                linewidth=0.35,
                alpha=0.6,
                zorder=1,
            )
        )
    return len(bands)


def apply_publication_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "font.size": 14,
            "axes.labelsize": 18,
            "axes.labelweight": "bold",
            "axes.titlesize": 17,
            "axes.titleweight": "bold",
            "axes.linewidth": 1.25,
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "xtick.major.width": 1.0,
            "ytick.major.width": 1.0,
            "xtick.major.size": 6,
            "ytick.major.size": 6,
            "xtick.color": "black",
            "ytick.color": "black",
            "legend.fontsize": 14,
            "legend.edgecolor": "black",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def style_axes(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(1.25)
        spine.set_color("black")
    ax.tick_params(axis="both", which="major", width=1.0, length=5, labelsize=15)


def finish_axes(ax: plt.Axes, mjd: list[float], fc: list[float]) -> None:
    ax.set_xlabel("MJD", fontweight="bold")
    ax.set_ylabel("Frequency (MHz)", fontweight="bold")
    ax.grid(True, linestyle=":", linewidth=0.5, color="0.5", alpha=0.4, zorder=0)
    ax.set_xlim(min(mjd) - 5, max(mjd) + 5)
    ax.set_ylim(min(fc) - 150, max(fc) + 150)
    style_axes(ax)


def add_legend(ax: plt.Axes) -> None:
    legend = ax.legend(
        loc="upper left",
        framealpha=1.0,
        fancybox=False,
        edgecolor="black",
        frameon=True,
    )
    legend.get_frame().set_linewidth(1.0)


def save_figure(fig: plt.Figure, png: Path, pdf: Path) -> None:
    fig.tight_layout()
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
