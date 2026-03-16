import csv
import math
import statistics
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMPARISON_DIR = SCRIPT_DIR.parent

if str(COMPARISON_DIR) not in sys.path:
    sys.path.insert(0, str(COMPARISON_DIR))

from preset_catalog import MASTER_PRESET_CSV


MASTER_PRESET_PATH = Path(MASTER_PRESET_CSV)
REPORT_PATH = SCRIPT_DIR / "comparison_accuracy_Ax_neg3_B0.md"
AX_TARGET = -3.0
B_TARGET = 0.0

MODELS = [
    ("FEA 2D", "fea2d"),
    ("Euler BVP", "euler"),
    ("Guided Beam", "guided"),
    ("PRB standard", "prb"),
    ("PRB optimized", "prb_opt"),
    ("BCM", "bcm"),
    ("Linear", "linear"),
]

RANGES = [
    ("[0, 2]", lambda ay: 0.0 <= ay <= 2.0),
    ("[2, 5]", lambda ay: 2.0 <= ay <= 5.0),
    ("[5, 10]", lambda ay: 5.0 <= ay <= 10.0),
    ("[10, 20]", lambda ay: 10.0 <= ay <= 20.0),
]

METRICS = ("ux", "uy", "phi")


def load_rows():
    with MASTER_PRESET_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = [
            row
            for row in csv.DictReader(fh)
            if math.isclose(float(row["Ax"]), AX_TARGET, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(float(row["B"]), B_TARGET, rel_tol=0.0, abs_tol=1e-12)
        ]
    rows.sort(key=lambda row: float(row["Ay"]))
    return rows


def mean_abs_pct_error(rows, suffix, metric):
    errors = []
    for row in rows:
        ref = float(row[f"{metric}_fea3d"])
        value = float(row[f"{metric}_{suffix}"])
        if not math.isfinite(ref) or not math.isfinite(value):
            continue
        if math.isclose(ref, 0.0, rel_tol=0.0, abs_tol=1e-15):
            continue
        errors.append(abs((value - ref) / ref) * 100.0)
    if not errors:
        return None, 0
    return statistics.fmean(errors), len(errors)


def fmt_pct(value):
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def failure_count(rows, suffix):
    count = 0
    for row in rows:
        values = [row[f"{metric}_{suffix}"] for metric in METRICS]
        if any(not math.isfinite(float(value)) for value in values):
            count += 1
    return count


def best_model(rows, metric, analytical_only=False):
    candidates = MODELS[1:] if analytical_only else MODELS
    scored = []
    for model_name, suffix in candidates:
        err, _ = mean_abs_pct_error(rows, suffix, metric)
        if err is None:
            continue
        scored.append((err, model_name))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0])
    return scored[0]


def build_report(rows):
    ay_values = [float(row["Ay"]) for row in rows]
    lines = []
    lines.append("# Accuracy Comparison For `Ax = -3`, `B = 0`")
    lines.append("")
    lines.append(
        "This report compares the reduced-order models and 2D FEA against "
        "**FEA 3D** for the load slice `Ax = -3`, `B = 0`, using the preset "
        f"master table [PARALLOGRAM_ALL_MODELS_master.csv]({MASTER_PRESET_PATH.as_posix()})."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("- Load slice used: `Ax = -3`, `B = 0`.")
    lines.append("- Reference model: `FEA 3D`.")
    lines.append("- Error metric: **mean absolute percentage error** for `ux`, `uy`, and `phi`.")
    lines.append("- When the FEA 3D reference value is exactly zero, percentage error is undefined and that case is excluded for that metric.")
    lines.append("- The `Ay` ranges are treated as closed intervals exactly as written, so `Ay = 2`, `5`, and `10` appear in adjacent sections.")
    lines.append("")

    lines.append("## Available `Ay` Values")
    lines.append("")
    lines.append("`" + ", ".join(f"{value:g}" for value in ay_values) + "`")
    lines.append("")

    lines.append("## Model Availability")
    lines.append("")
    lines.append("| Model | Non-finite cases in this slice |")
    lines.append("| ----- | -----------------------------: |")
    for model_name, suffix in MODELS:
        lines.append(f"| {model_name} | {failure_count(rows, suffix)} |")
    lines.append("")

    for range_label, predicate in RANGES:
        subset = [row for row in rows if predicate(float(row["Ay"]))]
        ay_subset = [float(row["Ay"]) for row in subset]
        lines.append(f"## Range {range_label}")
        lines.append("")
        lines.append("`Ay` values: " + ", ".join(f"{value:g}" for value in ay_subset))
        lines.append("")
        lines.append("| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |")
        lines.append("| ----- | -----------------: | -----------------: | -------------------: |")
        for model_name, suffix in MODELS:
            ux_err, _ = mean_abs_pct_error(subset, suffix, "ux")
            uy_err, _ = mean_abs_pct_error(subset, suffix, "uy")
            phi_err, _ = mean_abs_pct_error(subset, suffix, "phi")
            lines.append(
                f"| {model_name} | {fmt_pct(ux_err)} | {fmt_pct(uy_err)} | {fmt_pct(phi_err)} |"
            )
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    for metric in METRICS:
        overall_best = best_model(rows, metric, analytical_only=False)
        analytical_best = best_model(rows, metric, analytical_only=True)
        metric_label = {"ux": "`ux`", "uy": "`uy`", "phi": "`phi`"}[metric]
        if overall_best is not None:
            lines.append(
                f"- Best overall non-reference model for {metric_label}: "
                f"`{overall_best[1]}` with mean absolute percentage error `{overall_best[0]:.2f}%`."
            )
        if analytical_best is not None:
            lines.append(
                f"- Best analytical model for {metric_label}: "
                f"`{analytical_best[1]}` with mean absolute percentage error `{analytical_best[0]:.2f}%`."
            )
    lines.append("")

    return "\n".join(lines)


def main():
    rows = load_rows()
    report = build_report(rows)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
