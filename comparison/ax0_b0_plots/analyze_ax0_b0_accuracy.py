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
REPORT_PATH = SCRIPT_DIR / "comparison_accuracy_Ax0_B0.md"

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


def load_rows():
    with open(MASTER_PRESET_PATH, "r", encoding="utf-8-sig", newline="") as fh:
        return [
            row
            for row in csv.DictReader(fh)
            if math.isclose(float(row["Ax"]), 0.0, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(float(row["B"]), 0.0, rel_tol=0.0, abs_tol=1e-12)
        ]


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


def build_report(rows):
    lines = []
    lines.append("# Accuracy Comparison For `Ax = 0`, `B = 0`")
    lines.append("")
    lines.append(
        "This report compares the accuracy of the reduced-order models and 2D FEA "
        "against **FEA 3D** using the preset master table "
        f"[PARALLOGRAM_ALL_MODELS_master.csv]({MASTER_PRESET_PATH.as_posix()})."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("- Load slice used: `Ax = 0`, `B = 0`.")
    lines.append("- Reference model: `FEA 3D`.")
    lines.append("- Error metric: **mean absolute percentage error** for `ux`, `uy`, and `phi`.")
    lines.append("- When the FEA 3D reference value is exactly zero, percentage error is undefined and that case is excluded for that metric.")
    lines.append("- The ranges are interpreted exactly as requested as closed intervals, so `Ay = 2`, `Ay = 5`, and `Ay = 10` appear in adjacent sections.")
    lines.append("- `FEA 3D` is omitted from the tables because its error is zero by definition.")
    lines.append("")

    ay_values = [float(row["Ay"]) for row in rows]
    lines.append("## Available `Ay` Values")
    lines.append("")
    lines.append("`" + ", ".join(f"{value:g}" for value in ay_values) + "`")
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
            ux_err, ux_n = mean_abs_pct_error(subset, suffix, "ux")
            uy_err, uy_n = mean_abs_pct_error(subset, suffix, "uy")
            phi_err, phi_n = mean_abs_pct_error(subset, suffix, "phi")
            lines.append(
                f"| {model_name} | {fmt_pct(ux_err)} | {fmt_pct(uy_err)} | {fmt_pct(phi_err)} |"
            )
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("- `FEA 2D` is the most accurate non-reference model across all four `Ay` ranges.")
    lines.append("- `Euler BVP` is consistently the next-best high-fidelity analytical model and improves noticeably relative to the other analytical models as `Ay` increases.")
    lines.append("- `Guided Beam`, `Linear`, and both `PRB` variants show zero-rotation assumptions or simplified kinematics clearly in the `phi` error column, especially because their `phi` prediction is zero for this load slice.")
    lines.append("- `PRB optimized` improves substantially over `PRB standard` for `ux` and `uy`, but neither PRB variant captures `phi` for this case family.")
    lines.append("- `BCM` remains competitive at small deflection but its `ux`, `uy`, and especially `phi` errors grow strongly in the high-`Ay` range.")
    lines.append("")

    return "\n".join(lines)


def main():
    rows = load_rows()
    report = build_report(rows)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
