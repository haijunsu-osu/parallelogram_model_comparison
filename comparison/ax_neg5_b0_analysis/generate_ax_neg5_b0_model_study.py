import csv
import math
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SCRIPT_DIR = Path(__file__).resolve().parent
COMPARISON_DIR = SCRIPT_DIR.parent

if str(COMPARISON_DIR) not in sys.path:
    sys.path.insert(0, str(COMPARISON_DIR))

from preset_catalog import MASTER_PRESET_CSV


MASTER_PRESET_PATH = Path(MASTER_PRESET_CSV)
REPORT_PATH = SCRIPT_DIR / "comparison_accuracy_Ax_neg5_B_0.md"
AX_TARGET = -5.0
B_TARGET = 0.0
AY_MIN = 0.0
AY_MAX = 20.0

MODEL_SPECS = [
    ("FEA 3D", "fea3d", "#000000", "-", 2.8, "o", "#000000"),
    ("FEA 2D", "fea2d", "#4f5d75", "-", 2.2, "s", "none"),
    ("Euler BVP", "euler", "#1b9e77", "--", 2.0, "^", "#1b9e77"),
    ("Guided Beam", "guided", "#7b2cbf", "-.", 1.9, "D", "none"),
    ("PRB standard", "prb", "#c79200", ":", 1.9, "v", "none"),
    ("PRB optimized", "prb_opt", "#e36414", (0, (5, 2)), 1.9, "P", "#e36414"),
    ("BCM", "bcm", "#0077b6", "--", 1.9, ">", "none"),
    ("Linear", "linear", "#8d99ae", ":", 1.7, "x", "#8d99ae"),
]

METRIC_SPECS = [
    (
        "ux",
        r"$u_x$",
        "ux_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute error in $u_x$",
        "ux_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute percentage error in $u_x$ (%)",
        "ux_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png",
    ),
    (
        "uy",
        r"$u_y$",
        "uy_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute error in $u_y$",
        "uy_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute percentage error in $u_y$ (%)",
        "uy_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png",
    ),
    (
        "phi",
        r"$\phi$ (rad)",
        "phi_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute error in $\phi$ (rad)",
        "phi_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png",
        r"Absolute percentage error in $\phi$ (%)",
        "phi_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png",
    ),
]


def load_rows():
    with MASTER_PRESET_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = [
            row
            for row in csv.DictReader(fh)
            if math.isclose(float(row["Ax"]), AX_TARGET, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(float(row["B"]), B_TARGET, rel_tol=0.0, abs_tol=1e-12)
            and AY_MIN <= float(row["Ay"]) <= AY_MAX
        ]
    rows.sort(key=lambda row: float(row["Ay"]))
    return rows


def parse_value(row, metric, suffix):
    return float(row[f"{metric}_{suffix}"])


def is_pct_error_row(row, metric):
    if math.isclose(float(row["Ay"]), 0.0, rel_tol=0.0, abs_tol=1e-12):
        return False
    reference = parse_value(row, metric, "fea3d")
    return not math.isclose(reference, 0.0, rel_tol=0.0, abs_tol=1e-15)


def abs_error(value, reference):
    if not math.isfinite(value) or not math.isfinite(reference):
        return math.nan
    return abs(value - reference)


def abs_pct_error(value, reference):
    if not math.isfinite(value) or not math.isfinite(reference):
        return math.nan
    if math.isclose(reference, 0.0, rel_tol=0.0, abs_tol=1e-15):
        return math.nan
    return abs((value - reference) / reference) * 100.0


def summarize_metric(rows, suffix, metric):
    abs_errors = []
    abs_pct_errors = []
    for row in rows:
        reference = parse_value(row, metric, "fea3d")
        value = parse_value(row, metric, suffix)
        err = abs_error(value, reference)
        if math.isfinite(err):
            abs_errors.append(err)
        if is_pct_error_row(row, metric):
            pct = abs_pct_error(value, reference)
            if math.isfinite(pct):
                abs_pct_errors.append(pct)

    return {
        "abs_count": len(abs_errors),
        "mean_abs_error": statistics.fmean(abs_errors) if abs_errors else None,
        "max_abs_error": max(abs_errors) if abs_errors else None,
        "pct_count": len(abs_pct_errors),
        "mean_abs_pct_error": statistics.fmean(abs_pct_errors) if abs_pct_errors else None,
        "max_abs_pct_error": max(abs_pct_errors) if abs_pct_errors else None,
    }


def nonfinite_cases(rows, suffix):
    ay_values = []
    for row in rows:
        values = [parse_value(row, metric, suffix) for metric, *_rest in METRIC_SPECS]
        if any(not math.isfinite(value) for value in values):
            ay_values.append(float(row["Ay"]))
    return ay_values


def pct_error_ay_values(rows, metric):
    return [float(row["Ay"]) for row in rows if is_pct_error_row(row, metric)]


def fmt_num(value, decimals=6):
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def fmt_pct(value):
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.2f}"


def plot_series(rows, metric, ylabel, output_name):
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    ay_values = [float(row["Ay"]) for row in rows]

    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in rows:
            value = parse_value(row, metric, suffix)
            values.append(value if math.isfinite(value) else math.nan)
        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(
        rf"{ylabel} vs. $\alpha_y$ for all models $(\alpha_x = -5,\ \beta = 0)$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = SCRIPT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def plot_error(rows, metric, ylabel, output_name, pct=False):
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    plot_rows = [row for row in rows if is_pct_error_row(row, metric)] if pct else rows
    ay_values = [float(row["Ay"]) for row in plot_rows]

    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in plot_rows:
            if suffix == "fea3d":
                values.append(0.0)
                continue
            reference = parse_value(row, metric, "fea3d")
            value = parse_value(row, metric, suffix)
            err = abs_pct_error(value, reference) if pct else abs_error(value, reference)
            values.append(err if math.isfinite(err) else math.nan)

        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    title_label = "absolute percentage error" if pct else "absolute error"
    ax.set_title(
        rf"{title_label.title()} vs. $\alpha_y$ relative to FEA 3D $(\alpha_x = -5,\ \beta = 0)$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = SCRIPT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def best_model_by_metric(rows, metric):
    candidates = []
    for model_name, suffix, *_rest in MODEL_SPECS[1:]:
        summary = summarize_metric(rows, suffix, metric)
        score = summary["mean_abs_pct_error"]
        if score is None:
            continue
        candidates.append((score, model_name))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0]


def build_report(rows):
    ay_values = [float(row["Ay"]) for row in rows]
    lines = []
    lines.append("# Accuracy Comparison For `Ax = -5`, `B = 0`")
    lines.append("")
    lines.append(
        "This study compares all models in the `Ax = -5`, `B = 0`, `Ay in [0, 20]` slice "
        "of the master preset table "
        f"[PARALLOGRAM_ALL_MODELS_master.csv]({MASTER_PRESET_PATH.as_posix()})."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("- Slice used: `Ax = -5`, `B = 0`, `0 <= Ay <= 20`.")
    lines.append("- Reference model for error calculations: `FEA 3D`.")
    lines.append("- Error metrics reported: absolute error and absolute percentage error for `ux`, `uy`, and `phi`.")
    lines.append("- Non-finite model outputs are excluded from aggregate error statistics for the affected metric.")
    lines.append("- Percentage-error summaries and percentage-error plots exclude the `Ay = 0` point and any row where the FEA 3D reference value is zero for that metric.")
    lines.append("")
    lines.append("## Available `Ay` Values")
    lines.append("")
    lines.append("`" + ", ".join(f"{value:g}" for value in ay_values) + "`")
    lines.append("")
    lines.append("## `Ay` Values Used For Percentage Error")
    lines.append("")
    for metric, _ylabel, *_rest in METRIC_SPECS:
        pct_ays = pct_error_ay_values(rows, metric)
        lines.append(f"- `{metric}`: `" + ", ".join(f"{value:g}" for value in pct_ays) + "`")
    lines.append("")
    lines.append("## Model Availability")
    lines.append("")
    lines.append("| Model | Non-finite `Ay` values |")
    lines.append("| ----- | ---------------------- |")
    for model_name, suffix, *_rest in MODEL_SPECS:
        bad_ays = nonfinite_cases(rows, suffix)
        bad_text = ", ".join(f"{value:g}" for value in bad_ays) if bad_ays else "None"
        lines.append(f"| {model_name} | {bad_text} |")
    lines.append("")

    for metric, ylabel, *_rest in METRIC_SPECS:
        lines.append(f"## {ylabel} Error Summary")
        lines.append("")
        lines.append(
            "| Model | Valid abs cases | Mean abs error | Max abs error | "
            "Valid % cases | Mean abs % error | Max abs % error |"
        )
        lines.append(
            "| ----- | --------------: | -------------: | ------------: | "
            "------------: | ----------------: | ---------------: |"
        )
        for model_name, suffix, *_ignored in MODEL_SPECS:
            summary = summarize_metric(rows, suffix, metric)
            lines.append(
                f"| {model_name} | {summary['abs_count']} | "
                f"{fmt_num(summary['mean_abs_error'])} | {fmt_num(summary['max_abs_error'])} | "
                f"{summary['pct_count']} | {fmt_pct(summary['mean_abs_pct_error'])} | "
                f"{fmt_pct(summary['max_abs_pct_error'])} |"
            )
        lines.append("")

    lines.append("## Best Non-reference Models By Mean Absolute Percentage Error")
    lines.append("")
    for metric, _ylabel, *_rest in METRIC_SPECS:
        best = best_model_by_metric(rows, metric)
        if best is None:
            continue
        lines.append(
            f"- For `{metric}`, the best non-reference model is `{best[1]}` "
            f"with mean absolute percentage error `{best[0]:.2f}%`."
        )
    lines.append("")
    lines.append("## Generated Images")
    lines.append("")
    for _metric, _ylabel, curve_name, _abs_err_label, abs_err_name, _pct_label, pct_name in METRIC_SPECS:
        lines.append(f"- `{curve_name}`")
        lines.append(f"- `{abs_err_name}`")
        lines.append(f"- `{pct_name}`")
    lines.append("")

    return "\n".join(lines)


def main():
    rows = load_rows()
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    for (
        metric,
        ylabel,
        curve_name,
        _abs_err_label,
        abs_err_name,
        _pct_err_label,
        pct_err_name,
    ) in METRIC_SPECS:
        plot_series(rows, metric, ylabel, curve_name)
        plot_error(rows, metric, f"Absolute error in {ylabel}", abs_err_name, pct=False)
        plot_error(rows, metric, f"Absolute percentage error in {ylabel} (%)", pct_err_name, pct=True)

    report = build_report(rows)
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"Saved {REPORT_PATH}")


if __name__ == "__main__":
    main()
