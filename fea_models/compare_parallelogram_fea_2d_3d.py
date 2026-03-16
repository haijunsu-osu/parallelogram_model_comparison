import argparse
import csv
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DEFLECTION_METRICS = ("x", "y", "phi")
ALL_METRICS = ("x", "y", "phi", "t")


@dataclass(frozen=True)
class LoadCase:
    fy: float
    fx: float
    m: float


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Compare 2D and 3D parallelogram FEA sweep results and write a Markdown report."
    )
    parser.add_argument(
        "--csv-2d",
        default=str(root / "2d" / "PARALLOGRAM_FEA_2D_sweep.csv"),
        help="Path to the 2D FEA sweep CSV.",
    )
    parser.add_argument(
        "--csv-3d",
        default=str(root / "3d" / "PARALLOGRAM_FEA_3D_sweep.csv"),
        help="Path to the 3D FEA sweep CSV.",
    )
    parser.add_argument(
        "--output-md",
        default=str(root / "PARALLOGRAM_FEA_2D_vs_3D_REPORT.md"),
        help="Path to the generated Markdown report.",
    )
    parser.add_argument(
        "--large-x-threshold",
        type=float,
        default=10.0,
        help="Absolute x-difference threshold in mm for flagging a large discrepancy.",
    )
    parser.add_argument(
        "--large-y-threshold",
        type=float,
        default=10.0,
        help="Absolute y-difference threshold in mm for flagging a large discrepancy.",
    )
    parser.add_argument(
        "--large-phi-threshold",
        type=float,
        default=0.05,
        help="Absolute phi-difference threshold in rad for flagging a large discrepancy.",
    )
    parser.add_argument(
        "--top-count",
        type=int,
        default=0,
        help="How many large-discrepancy rows to include in the report. Use 0 to include all flagged cases.",
    )
    return parser.parse_args()


def load_results(csv_path: Path) -> dict[LoadCase, dict[str, float]]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return {
            LoadCase(float(row["fy"]), float(row["fx"]), float(row["m"])): {
                metric: float(row[metric]) for metric in ALL_METRICS
            }
            for row in reader
        }


def safe_rel_diff(a: float, b: float, floor: float) -> float:
    scale = max(abs(a), abs(b), floor)
    return abs(b - a) / scale


def fmt_float(value: float, digits: int = 6) -> str:
    if math.isnan(value) or math.isinf(value):
        return str(value)
    return f"{value:.{digits}f}"


def fmt_pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def pct(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return float("nan")
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * fraction)))
    return sorted_values[index]


def summarize_metric(values: list[float]) -> dict[str, float]:
    sorted_values = sorted(values)
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p90": pct(sorted_values, 0.9),
        "max": sorted_values[-1],
    }


def build_report(
    csv_2d: Path,
    csv_3d: Path,
    output_md: Path,
    results_2d: dict[LoadCase, dict[str, float]],
    results_3d: dict[LoadCase, dict[str, float]],
    large_x_threshold: float,
    large_y_threshold: float,
    large_phi_threshold: float,
    top_count: int,
) -> str:
    loads_2d = set(results_2d)
    loads_3d = set(results_3d)
    common = sorted(loads_2d & loads_3d, key=lambda case: (case.fy, case.fx, case.m))
    only_2d = sorted(loads_2d - loads_3d, key=lambda case: (case.fy, case.fx, case.m))
    only_3d = sorted(loads_3d - loads_2d, key=lambda case: (case.fy, case.fx, case.m))

    per_case: list[dict[str, object]] = []
    suspicious_zero_rows: list[tuple[str, LoadCase, float]] = []
    abs_diffs = {metric: [] for metric in ALL_METRICS}
    rel_diffs = {metric: [] for metric in ALL_METRICS}

    for dataset_name, dataset in (("2D", results_2d), ("3D", results_3d)):
        for load_case, row in dataset.items():
            if load_case == LoadCase(0.0, 0.0, 0.0):
                continue
            if row["x"] == 0.0 and row["y"] == 0.0 and row["phi"] == 0.0:
                suspicious_zero_rows.append((dataset_name, load_case, row["t"]))

    for load_case in common:
        row_2d = results_2d[load_case]
        row_3d = results_3d[load_case]
        record: dict[str, object] = {"load_case": load_case, "2d": row_2d, "3d": row_3d}
        for metric in ALL_METRICS:
            abs_diff = abs(row_3d[metric] - row_2d[metric])
            floor = 1e-6 if metric in ("x", "y") else (1e-9 if metric == "phi" else 1e-3)
            rel_diff = safe_rel_diff(row_2d[metric], row_3d[metric], floor)
            record[f"{metric}_abs"] = abs_diff
            record[f"{metric}_rel"] = rel_diff
            abs_diffs[metric].append(abs_diff)
            rel_diffs[metric].append(rel_diff)

        severity = max(
            record["x_abs"] / large_x_threshold,
            record["y_abs"] / large_y_threshold,
            record["phi_abs"] / large_phi_threshold,
        )
        record["severity"] = severity
        record["is_large"] = (
            record["x_abs"] > large_x_threshold
            or record["y_abs"] > large_y_threshold
            or record["phi_abs"] > large_phi_threshold
        )
        per_case.append(record)

    metric_summary = {
        metric: {
            "abs": summarize_metric(abs_diffs[metric]),
            "rel": summarize_metric(rel_diffs[metric]),
        }
        for metric in ALL_METRICS
    }

    large_cases = [record for record in per_case if record["is_large"]]
    large_cases.sort(
        key=lambda record: (
            record["severity"],
            max(record["x_abs"], record["y_abs"], record["phi_abs"]),
        ),
        reverse=True,
    )

    fx_counts = Counter(record["load_case"].fx for record in large_cases)
    fy_counts = Counter(record["load_case"].fy for record in large_cases)
    m_counts = Counter(record["load_case"].m for record in large_cases)

    lines: list[str] = []
    lines.append("# Parallelogram FEA 2D vs 3D Comparison")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- 2D CSV: `{csv_2d}`")
    lines.append(f"- 3D CSV: `{csv_3d}`")
    lines.append(f"- Report: `{output_md}`")
    lines.append("")
    lines.append("## Load Matching")
    lines.append("")
    lines.append(f"- 2D load cases: `{len(loads_2d)}`")
    lines.append(f"- 3D load cases: `{len(loads_3d)}`")
    lines.append(f"- Common load cases: `{len(common)}`")
    lines.append(f"- Present only in 2D: `{len(only_2d)}`")
    lines.append(f"- Present only in 3D: `{len(only_3d)}`")
    lines.append("")

    if suspicious_zero_rows:
        lines.append("## Suspicious Zero-Deflection Rows")
        lines.append("")
        lines.append("Rows with `x = 0`, `y = 0`, and `phi = 0` can indicate a failed or nonconverged solve when the load is nonzero.")
        lines.append("")
        lines.append("| Dataset | fy | fx | m | Runtime t (s) |")
        lines.append("|---|---:|---:|---:|---:|")
        for dataset_name, load_case, runtime in suspicious_zero_rows:
            lines.append(
                f"| {dataset_name} | {fmt_float(load_case.fy, 1)} | {fmt_float(load_case.fx, 1)} | "
                f"{fmt_float(load_case.m, 1)} | {fmt_float(runtime, 3)} |"
            )
        lines.append("")

    lines.append("## Overall Difference Summary")
    lines.append("")
    lines.append("| Metric | Mean | Median | 90th Percentile | Max | Mean Relative | Median Relative | 90th Relative | Max Relative |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for metric in ALL_METRICS:
        summary_abs = metric_summary[metric]["abs"]
        summary_rel = metric_summary[metric]["rel"]
        unit = " (rad)" if metric == "phi" else (" (s)" if metric == "t" else " (mm)")
        lines.append(
            f"| `{metric}`{unit} | {fmt_float(summary_abs['mean'])} | {fmt_float(summary_abs['median'])} | "
            f"{fmt_float(summary_abs['p90'])} | {fmt_float(summary_abs['max'])} | {fmt_pct(summary_rel['mean'])} | "
            f"{fmt_pct(summary_rel['median'])} | {fmt_pct(summary_rel['p90'])} | {fmt_pct(summary_rel['max'])} |"
        )
    lines.append("")

    lines.append("## Large-Discrepancy Rule")
    lines.append("")
    lines.append("A case is flagged as a large discrepancy when any of these absolute differences is exceeded:")
    lines.append("")
    lines.append(f"- `|Δx| > {fmt_float(large_x_threshold, 1)} mm`")
    lines.append(f"- `|Δy| > {fmt_float(large_y_threshold, 1)} mm`")
    lines.append(f"- `|Δphi| > {fmt_float(large_phi_threshold, 3)} rad`")
    lines.append("")
    lines.append(f"Flagged cases: `{len(large_cases)}` / `{len(common)}`")
    lines.append("")

    if large_cases:
        displayed_cases = large_cases if top_count <= 0 else large_cases[:top_count]
        top_fx, top_fx_count = fx_counts.most_common(1)[0]
        top_fy, top_fy_count = fy_counts.most_common(1)[0]
        top_m, top_m_count = m_counts.most_common(1)[0]

        lines.append("## Large-Discrepancy Pattern Summary")
        lines.append("")
        lines.append(f"- Most flagged cases occur at `fx = {top_fx:.1f}`: `{top_fx_count}` cases")
        lines.append(f"- Highest-affected `fy` level: `{top_fy:.1f}` with `{top_fy_count}` cases")
        lines.append(f"- Most common moment level among flagged cases: `{top_m:.1f}` with `{top_m_count}` cases")
        lines.append(
            f"- The strongest cluster in this dataset is around `fy = {top_fy:.1f}`, "
            f"`fx = {top_fx:.1f}`, and `m = {top_m:.1f}`."
        )
        if any(item[0] == "2D" and item[1] == LoadCase(18.0, -10.0, 3.0) for item in suspicious_zero_rows):
            lines.append("- The worst outlier `fy=18, fx=-10, m=3` is amplified by a suspicious zero row in the 2D dataset.")
        lines.append("")

        if len(displayed_cases) == len(large_cases):
            lines.append("## All Large-Discrepancy Cases")
        else:
            lines.append("## Top Large-Discrepancy Cases")
        lines.append("")
        lines.append("| fy | fx | m | 2D x | 3D x | |Δx| | 2D y | 3D y | |Δy| | 2D phi | 3D phi | |Δphi| | Severity |")
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for record in displayed_cases:
            load_case = record["load_case"]
            row_2d = record["2d"]
            row_3d = record["3d"]
            lines.append(
                f"| {fmt_float(load_case.fy, 1)} | {fmt_float(load_case.fx, 1)} | {fmt_float(load_case.m, 1)} | "
                f"{fmt_float(row_2d['x'])} | {fmt_float(row_3d['x'])} | {fmt_float(record['x_abs'])} | "
                f"{fmt_float(row_2d['y'])} | {fmt_float(row_3d['y'])} | {fmt_float(record['y_abs'])} | "
                f"{fmt_float(row_2d['phi'])} | {fmt_float(row_3d['phi'])} | {fmt_float(record['phi_abs'])} | "
                f"{fmt_float(record['severity'])} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    csv_2d = Path(args.csv_2d).resolve()
    csv_3d = Path(args.csv_3d).resolve()
    output_md = Path(args.output_md).resolve()

    results_2d = load_results(csv_2d)
    results_3d = load_results(csv_3d)

    report_text = build_report(
        csv_2d=csv_2d,
        csv_3d=csv_3d,
        output_md=output_md,
        results_2d=results_2d,
        results_3d=results_3d,
        large_x_threshold=args.large_x_threshold,
        large_y_threshold=args.large_y_threshold,
        large_phi_threshold=args.large_phi_threshold,
        top_count=args.top_count,
    )

    output_md.write_text(report_text, encoding="utf-8")
    print(f"Wrote comparison report to {output_md}")


if __name__ == "__main__":
    main()
