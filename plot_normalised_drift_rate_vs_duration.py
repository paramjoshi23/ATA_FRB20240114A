#!/usr/bin/env python3

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Point:
    duration_ms: float
    duration_err_ms: float
    norm_drift: float
    norm_drift_err: float
    category: str  # 'multi_component', 'single_no_subbursts', 'subburst'


@dataclass(frozen=True)
class FitResult:
    m: float
    b: float
    m_err: float
    b_err: float
    A: float
    A_err: float
    method: str


def _is_finite(number: float) -> bool:
    return not (math.isnan(number) or math.isinf(number))


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = value.strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _propagate_division_error(
    numerator: float,
    numerator_err: float,
    denominator: float,
    denominator_err: float,
) -> float:
    """Error propagation for y = numerator / denominator (assuming independence)."""

    # y = n / d
    # dy^2 = (∂y/∂n)^2 σ_n^2 + (∂y/∂d)^2 σ_d^2
    # ∂y/∂n = 1/d
    # ∂y/∂d = -n/d^2
    if denominator == 0.0:
        return float("inf")

    term_num = (numerator_err / denominator) ** 2
    term_den = ((numerator * denominator_err) / (denominator**2)) ** 2
    return math.sqrt(term_num + term_den)


def _round_to_sig_figs(value: float, sig_figs: int) -> float:
    if sig_figs < 1:
        raise ValueError("sig_figs must be >= 1")
    if value == 0.0:
        return 0.0
    return round(value, sig_figs - 1 - int(math.floor(math.log10(abs(value)))))


def _format_value_pm_uncertainty(
    value: float,
    uncertainty: float,
    uncertainty_sig_figs: int = 1,
    *,
    keep_value_trailing_zeros: bool = False,
) -> str:
    """Format 'value±uncertainty' with uncertainty rounded to N significant digits,
    and value rounded to the same decimal place.
    """

    if not (_is_finite(value) and _is_finite(uncertainty)) or uncertainty <= 0.0:
        return f"{value}±{uncertainty}"

    unc_rounded = _round_to_sig_figs(uncertainty, uncertainty_sig_figs)
    if unc_rounded == 0.0:
        return f"{value}±{uncertainty}"

    ndigits = -int(math.floor(math.log10(abs(unc_rounded))))
    value_rounded = round(value, ndigits)

    decimals = max(0, ndigits)
    if decimals > 0:
        value_str = f"{value_rounded:.{decimals}f}"
        unc_str = f"{unc_rounded:.{decimals}f}"
        if not keep_value_trailing_zeros:
            value_str = value_str.rstrip("0").rstrip(".")
        unc_str = unc_str.rstrip("0").rstrip(".")
    else:
        value_str = f"{value_rounded:.0f}"
        unc_str = f"{unc_rounded:.0f}"

    # Avoid '-0' artifacts from rounding.
    try:
        if float(value_str) == 0.0:
            value_str = value_str.lstrip("-")
    except ValueError:
        pass

    return f"{value_str}±{unc_str}"


def load_points(
    csv_path: Path,
    slope_max_abs: float,
    slope_err_max: float,
    negative_only: bool,
    duration_sigma: int,
) -> tuple[list[Point], dict[str, int]]:
    dropped = {
        "missing_duration": 0,
        "missing_duration_err": 0,
        "missing_slope": 0,
        "missing_slope_err": 0,
        "missing_Center Frequency (MHz)": 0,
        "missing_Center Frequency Error (MHz)": 0,
        "zero_slope": 0,
        "non_negative_slope": 0,
        "slope_too_large": 0,
        "slope_err_too_large": 0,
    }

    if duration_sigma not in (1, 3):
        raise ValueError("duration_sigma must be 1 or 3")
    duration_scale = duration_sigma / 3.0

    points: list[Point] = []

    component_suffix_re = re.compile(r"^(?P<base>.+)_(?P<comp>[A-Za-z]\d*)$")

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {
            "Index",
            "Burst Duration (ms)",
            "Burst Duration Error (ms)",
            "Drift Rate (MHz/ms)",
            "Drift Rate Error (MHz/ms)",
            "Center Frequency (MHz)",
            "Center Frequency Error (MHz)",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {sorted(missing)}. "
                f"Found: {reader.fieldnames}"
            )

        rows = list(reader)

    bases_with_subbursts: set[str] = set()
    for row in rows:
        Index = (row.get("Index") or "").strip()
        match = component_suffix_re.match(Index)
        if match is None:
            continue
        bases_with_subbursts.add(match.group("base"))

    for row in rows:
        Index = (row.get("Index") or "").strip()
        match = component_suffix_re.match(Index)
        if match is not None:
            category = "subburst"
        else:
            if Index in bases_with_subbursts:
                category = "multi_component"
            else:
                category = "single_no_subbursts"

        duration_3sigma = _parse_float(row.get("Burst Duration (ms)"))
        duration = None if duration_3sigma is None else duration_3sigma * duration_scale
        if duration is None:
            dropped["missing_duration"] += 1
            continue

        duration_err_3sigma = _parse_float(row.get("Burst Duration Error (ms)"))
        duration_err = None if duration_err_3sigma is None else duration_err_3sigma * duration_scale
        if duration_err is None:
            dropped["missing_duration_err"] += 1
            continue

        slope = _parse_float(row.get("Drift Rate (MHz/ms)"))
        if slope is None:
            dropped["missing_slope"] += 1
            continue
        if slope == 0.0:
            dropped["zero_slope"] += 1
            continue

        slope_err = _parse_float(row.get("Drift Rate Error (MHz/ms)"))
        if slope_err is None:
            dropped["missing_slope_err"] += 1
            continue

        center_freq_mhz = _parse_float(row.get("Center Frequency (MHz)"))
        if center_freq_mhz is None:
            dropped["missing_Center Frequency (MHz)"] += 1
            continue

        center_freq_err_mhz = _parse_float(row.get("Center Frequency Error (MHz)"))
        if center_freq_err_mhz is None:
            dropped["missing_Center Frequency Error (MHz)"] += 1
            continue

        if negative_only and slope >= 0:
            dropped["non_negative_slope"] += 1
            continue

        if abs(slope) > slope_max_abs:
            dropped["slope_too_large"] += 1
            continue

        if slope_err > slope_err_max:
            dropped["slope_err_too_large"] += 1
            continue

        norm_drift = center_freq_mhz / slope
        norm_drift_err = _propagate_division_error(
            numerator=center_freq_mhz,
            numerator_err=center_freq_err_mhz,
            denominator=slope,
            denominator_err=slope_err,
        )

        if math.isnan(norm_drift) or math.isinf(norm_drift):
            continue
        if math.isnan(norm_drift_err) or math.isinf(norm_drift_err):
            continue

        points.append(
            Point(
                duration_ms=duration,
                duration_err_ms=duration_err,
                norm_drift=norm_drift,
                norm_drift_err=norm_drift_err,
                category=category,
            )
        )

    return points, dropped


def _fit_line_with_uncertainties(
    x: list[float],
    xerr: list[float],
    y: list[float],
    yerr: list[float],
    fit_intercept: bool = False,
) -> tuple[float, float, float, float, str]:
    """Fit y = A x (or y = m x + b if fit_intercept=True).

    Uses SciPy ODR when available (uncertainties in x and y).
    """

    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit")

    try:
        from scipy import odr  # type: ignore

        if fit_intercept:
            def f(beta: list[float], x_data: float | list[float]):
                return beta[0] * x_data + beta[1]

            model = odr.Model(f)
            data = odr.RealData(x, y, sx=xerr, sy=yerr)
            fit = odr.ODR(data, model, beta0=[-9.0, 0.0])
            output = fit.run()
            m, b = float(output.beta[0]), float(output.beta[1])
            m_err, b_err = float(output.sd_beta[0]), float(output.sd_beta[1])
            return m, b, m_err, b_err, "ODR"
        else:
            def f_no_b(beta: list[float], x_data: float | list[float]):
                return beta[0] * x_data

            model = odr.Model(f_no_b)
            data = odr.RealData(x, y, sx=xerr, sy=yerr)
            fit = odr.ODR(data, model, beta0=[-9.0])
            output = fit.run()
            A = float(output.beta[0])
            A_err = float(output.sd_beta[0])
            return A, 0.0, A_err, 0.0, "ODR (no intercept)"
    except Exception:
        # Fallback weighted least squares
        if not fit_intercept:
            w = [1.0 / (se * se) if se > 0 else 0.0 for se in yerr]
            swxx = sum(wi * xi * xi for wi, xi in zip(w, x))
            swxy = sum(wi * xi * yi for wi, xi, yi in zip(w, x, y))
            A = swxy / swxx if swxx != 0 else 0.0
            A_err = math.sqrt(1.0 / swxx) if swxx != 0 else 0.0
            return A, 0.0, A_err, 0.0, "fallback weighted least squares"
        else:
            w = [1.0 / (se * se) if se > 0 else 0.0 for se in yerr]
            sw = sum(w)
            swx = sum(wi * xi for wi, xi in zip(w, x))
            swy = sum(wi * yi for wi, yi in zip(w, y))
            swxx = sum(wi * xi * xi for wi, xi in zip(w, x))
            swxy = sum(wi * xi * yi for wi, xi, yi in zip(w, x, y))
            delta = sw * swxx - swx * swx
            m = (sw * swxy - swx * swy) / delta
            b = (swxx * swy - swx * swxy) / delta
            m_err = math.sqrt(sw / delta)
            b_err = math.sqrt(swxx / delta)
            return m, b, m_err, b_err, "fallback weighted least squares"


def _compute_fit_result(
    points: list[Point],
    categories: set[str],
    duration_sigma: int,
    fit_intercept: bool = False,
) -> Optional[FitResult]:
    group_points = [p for p in points if p.category in categories]

    # ODR requires strictly positive uncertainties; filter bad points for fitting.
    fit_points: list[Point] = []
    for p in group_points:
        if not (
            _is_finite(p.duration_ms)
            and _is_finite(p.duration_err_ms)
            and _is_finite(p.norm_drift)
            and _is_finite(p.norm_drift_err)
        ):
            continue
        if p.duration_err_ms <= 0.0 or p.norm_drift_err <= 0.0:
            continue
        fit_points.append(p)

    if len(fit_points) < 2:
        return None

    x = [p.duration_ms for p in fit_points]
    xerr = [p.duration_err_ms for p in fit_points]
    y = [p.norm_drift for p in fit_points]
    yerr = [p.norm_drift_err for p in fit_points]

    m, b, m_err, b_err, method = _fit_line_with_uncertainties(
        x=x, xerr=xerr, y=y, yerr=yerr, fit_intercept=fit_intercept
    )

    A = m
    A_err = m_err

    return FitResult(m=m, b=b, m_err=m_err, b_err=b_err, A=A, A_err=A_err, method=method)


def plot_points(
    points: list[Point],
    out_path: Path,
    show: bool,
    duration_sigma: int,
    fit_multi_component: Optional[FitResult],
) -> None:
    multi_x = [p.duration_ms for p in points if p.category == "multi_component"]
    multi_xerr = [p.duration_err_ms for p in points if p.category == "multi_component"]
    multi_y = [p.norm_drift for p in points if p.category == "multi_component"]
    multi_yerr = [p.norm_drift_err for p in points if p.category == "multi_component"]

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, figsize=(7.5, 6.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    if multi_x:
        ax_top.errorbar(
            multi_x,
            multi_y,
            xerr=multi_xerr,
            yerr=multi_yerr,
            fmt="o",
            markersize=5.0,
            linestyle="none",
            color="tab:blue",
            ecolor="tab:blue",
            elinewidth=1.0,
            capsize=2.0,
            alpha=0.85,
            label="Normalised drift rate",
        )

    if fit_multi_component is not None and multi_x:
        xmin, xmax = min(multi_x), max(multi_x)
        xs = [xmin + (xmax - xmin) * (i / 100.0) for i in range(101)]
        ys = [fit_multi_component.A * xi + fit_multi_component.b for xi in xs]
        A_text = _format_value_pm_uncertainty(
            fit_multi_component.A,
            fit_multi_component.A_err,
            uncertainty_sig_figs=1,
            keep_value_trailing_zeros=True,
        )

        if fit_multi_component.b != 0.0:
            b_text = _format_value_pm_uncertainty(fit_multi_component.b, fit_multi_component.b_err, uncertainty_sig_figs=1)
            label_text = f"Fit: $\\nu \\mathrm{{d}}t/\\mathrm{{d}}\\nu = A\\sigma_t + b$ ($A={A_text}$, $b={b_text}$ ms)"
        else:
            label_text = f"Fit: $\\nu \\mathrm{{d}}t/\\mathrm{{d}}\\nu = A\\sigma_t$ ($A={A_text}$)"

        ax_top.plot(
            xs,
            ys,
            color="tab:blue",
            linewidth=2.0,
            alpha=0.9,
            label=label_text,
        )

        # Residuals panel
        residuals = [yi - (fit_multi_component.A * xi + fit_multi_component.b) for xi, yi in zip(multi_x, multi_y)]
        res_errs = [
            math.sqrt(ye**2 + (fit_multi_component.A * xe)**2)
            for xe, ye in zip(multi_xerr, multi_yerr)
        ]

        ax_bottom.errorbar(
            multi_x,
            residuals,
            xerr=multi_xerr,
            yerr=res_errs,
            fmt="o",
            markersize=5.0,
            linestyle="none",
            color="tab:blue",
            ecolor="tab:blue",
            elinewidth=1.0,
            capsize=2.0,
            alpha=0.85,
        )
        ax_bottom.axhline(0.0, color="black", linestyle="--", linewidth=1.2)

    ax_top.set_ylabel(r"Normalised drift rate (ν dt/dν) in ms", fontsize=12, fontweight="bold")
    ax_top.grid(True, alpha=0.25)
    ax_top.legend(frameon=True, fontsize=10)

    ax_bottom.set_xlabel(f"{duration_sigma}-σ duration (ms)", fontsize=12, fontweight="bold")
    ax_bottom.set_ylabel(r"Residuals (ms)", fontsize=11, fontweight="bold")
    ax_bottom.grid(True, alpha=0.25)

    for ax in (ax_top, ax_bottom):
        for spine in ax.spines.values():
            spine.set_linewidth(1.8)
            spine.set_color("black")

    fig.tight_layout()
    fig.subplots_adjust(hspace=0.05)
    fig.savefig(out_path, dpi=600)

    # Also save to plots directory in overleaf folder if path matches
    overleaf_path = Path("ATA_FRB2024_overleaf_Aug2026_review1/plots/normalised_drift_rate_vs_duration_paper_FINAL_June2026.png")
    if overleaf_path.parent.exists():
        fig.savefig(overleaf_path, dpi=600)
        print(f"Saved copy to: {overleaf_path}")

    if show:
        plt.show()
    plt.close(fig)



def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plot normalised drift rate (Center Frequency (MHz) / slope) vs duration for multi-component drift rates "
            "only (i.e., base bursts that have sub-bursts)."
        )
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("FRB2024_paper_FullTableProperties_June2026.csv"),
        help="Input CSV containing duration/slope/slope-error/Center Frequency (MHz) columns.",
    )

    # Backward compatibility: older versions split by row index.
    # This option is now ignored because categories are inferred from Index suffixes.
    parser.add_argument(
        "--split",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--duration-sigma",
        type=int,
        choices=(1, 3),
        default=1,
        help=(
            "Which sigma-level to plot for duration on x-axis. "
            "The input CSV provides 3-sigma durations; 1-sigma is computed as (3-sigma)/3."
        ),
    )
    parser.add_argument(
        "--duration-max-ms",
        type=float,
        default=7.0,
        help=(
            "If set, keep only points with duration <= this value (in ms) on the x-axis. "
            "This filter is applied before plotting and fitting."
        ),
    )
    parser.add_argument(
        "--fit",
        choices=("multi", "intra", "both", "none"),
        default="multi",
        help=(
            "Choose which fits to compute. Only 'multi' is meaningful for this plot; "
            "'intra'/'both' are accepted for backward compatibility but will be treated as 'multi'. "
            "Use 'none' to disable fitting."
        ),
    )

    # Backward compatibility: older versions used --fit-groups combined/subburst/both/none.
    parser.add_argument(
        "--fit-groups",
        choices=("combined", "subburst", "both", "none"),
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--slope-max",
        type=float,
        default=1000.0,
        help="Ignore points with |slope| greater than this.",
    )
    parser.add_argument(
        "--slope-err-max",
        type=float,
        default=100.0,
        help="Ignore points with slope error greater than this.",
    )
    parser.add_argument(
        "--negative-only",
        action="store_true",
        default=True,
        help="Keep only negative slope values (default: enabled).",
    )
    parser.add_argument(
        "--allow-positive",
        action="store_true",
        help="Allow positive/zero slope values (overrides --negative-only).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("normalised_drift_rate_vs_duration_paper_FINAL.png"),
        help="Output image path.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot window (in addition to saving).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print point counts / drop summary.",
    )

    args = parser.parse_args()

    if getattr(args, "fit_groups", None) is not None:
        args.fit = {
            "combined": "multi",
            "subburst": "intra",
            "both": "both",
            "none": "none",
        }[args.fit_groups]

    negative_only = args.negative_only and not args.allow_positive

    points, dropped = load_points(
        csv_path=args.csv,
        slope_max_abs=args.slope_max,
        slope_err_max=args.slope_err_max,
        negative_only=negative_only,
        duration_sigma=args.duration_sigma,
    )

    # Keep only the blue points: multi-component drift rates for bursts that have sub-bursts.
    points = [p for p in points if p.category == "multi_component"]

    if args.duration_max_ms is not None:
        points = [p for p in points if p.duration_ms <= args.duration_max_ms]

    fit_mode = args.fit
    if fit_mode in ("intra", "both"):
        fit_mode = "multi"

    fit_multi_component = None
    if fit_mode == "multi":
        fit_multi_component = _compute_fit_result(
            points=points,
            categories={"multi_component"},
            duration_sigma=args.duration_sigma,
        )

    if not args.quiet:
        n_multi = sum(1 for p in points if p.category == "multi_component")
        print(f"Kept points: {len(points)} (multi_component={n_multi})")
        print("Dropped points: " + ", ".join(f"{k}={v}" for k, v in dropped.items()))
        if fit_multi_component is not None:
            A_text = _format_value_pm_uncertainty(
                fit_multi_component.A,
                fit_multi_component.A_err,
                uncertainty_sig_figs=1,
            )
            b_text = _format_value_pm_uncertainty(
                fit_multi_component.b,
                fit_multi_component.b_err,
                uncertainty_sig_figs=1,
            )
            print(
                "Multi-component fit: "
                f"method={fit_multi_component.method}, "
                f"A={A_text}, "
                f"b={b_text} ms"
            )

    plot_points(
        points=points,
        out_path=args.out,
        show=args.show,
        duration_sigma=args.duration_sigma,
        fit_multi_component=fit_multi_component,
    )

    if not args.quiet:
        print(f"Wrote: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
