"""
Run a mesh convergence study for the 3D single-case parallelogram model.

This script launches ``parallelogram_3d_single.py`` through FreeCADCmd for a
fixed load case while sweeping mesh sizes. It parses the printed summary from
each run and writes a Markdown report with the numerical results and timings.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time


WORKSPACE = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
FREECAD_DEFAULT = Path(r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe")
SINGLE_CASE_SCRIPT = SCRIPT_DIR / "parallelogram_3d_single.py"
DEFAULT_REPORT_PATH = SCRIPT_DIR / "MESH_CONVERGENCE_STUDY.md"
DEFAULT_MESH_SIZES = (10.0, 7.5, 5.0, 2.5)


RESULT_PATTERNS = {
    "nodes": re.compile(r"Mesh:\s*(\d+)\s+nodes,\s*(\d+)\s+elements"),
    "x_mm": re.compile(r"^\s*x\s*=\s*([-\d.eE+]+)\s*mm", re.MULTILINE),
    "y_mm": re.compile(r"^\s*y\s*=\s*([-\d.eE+]+)\s*mm", re.MULTILINE),
    "ux": re.compile(r"Ux\s*=\s*x/L\s*=\s*([-\d.eE+]+)"),
    "uy": re.compile(r"Uy\s*=\s*y/L\s*=\s*([-\d.eE+]+)"),
    "phi": re.compile(r"phi\s*=\s*([-\d.eE+]+)\s*rad"),
    "times": re.compile(
        r"Times:\s*mesh=([-\d.eE+]+)s\s+solve=([-\d.eE+]+)s\s+total=([-\d.eE+]+)s"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 3D parallelogram mesh convergence study and write a Markdown report."
    )
    parser.add_argument(
        "--freecad",
        default=os.environ.get("FREECAD_CMD", str(FREECAD_DEFAULT)),
        help="Path to FreeCADCmd.exe",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_PATH),
        help="Markdown report output path",
    )
    parser.add_argument(
        "--mesh-sizes",
        nargs="+",
        type=float,
        default=list(DEFAULT_MESH_SIZES),
        help="Mesh sizes in mm to evaluate",
    )
    parser.add_argument("--ax", type=float, default=float(os.environ.get("FEA_AX", "0.0")))
    parser.add_argument("--ay", type=float, default=float(os.environ.get("FEA_AY", "5.0")))
    parser.add_argument("--m", type=float, default=float(os.environ.get("FEA_M", "0.0")))
    parser.add_argument(
        "--log-dir",
        default="",
        help="Optional directory for per-run raw logs",
    )
    return parser.parse_args()


def fmt_mesh_size(mesh_size: float) -> str:
    if float(mesh_size).is_integer():
        return f"{int(mesh_size)} mm"
    return f"{mesh_size:g} mm"


def fmt_value(value: float | None, decimals: int = 4) -> str:
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def fmt_int(value: int | None) -> str:
    if value is None:
        return "N/A"
    return str(value)


def fmt_delta(value: float | None, ref: float | None, decimals: int = 4) -> str:
    if value is None or ref is None or not math.isfinite(value) or not math.isfinite(ref):
        return "N/A"
    return f"{abs(value - ref):.{decimals}f}"


def fmt_rel_delta(value: float | None, ref: float | None, decimals: int = 2) -> str:
    if (
        value is None
        or ref is None
        or not math.isfinite(value)
        or not math.isfinite(ref)
        or math.isclose(ref, 0.0, rel_tol=0.0, abs_tol=1e-15)
    ):
        return "N/A"
    return f"{abs(value - ref) / abs(ref) * 100.0:.{decimals}f}%"


def parse_run_output(output: str) -> dict[str, float | int]:
    parsed: dict[str, float | int] = {}

    node_match = RESULT_PATTERNS["nodes"].search(output)
    if node_match:
        parsed["nodes"] = int(node_match.group(1))
        parsed["elements"] = int(node_match.group(2))

    for key in ("x_mm", "y_mm", "ux", "uy", "phi"):
        match = RESULT_PATTERNS[key].search(output)
        if match:
            parsed[key] = float(match.group(1))

    times_match = RESULT_PATTERNS["times"].search(output)
    if times_match:
        parsed["mesh_time_s"] = float(times_match.group(1))
        parsed["solve_time_s"] = float(times_match.group(2))
        parsed["total_time_s"] = float(times_match.group(3))

    return parsed


def run_single_case(
    freecad_cmd: Path,
    mesh_size: float,
    ax: float,
    ay: float,
    moment: float,
    log_dir: Path | None,
) -> dict[str, object]:
    env = os.environ.copy()
    env["FEA_MESH_FINE_CHAR_LEN"] = str(mesh_size)
    env["FEA_MESH_COARSE_CHAR_LEN"] = str(mesh_size)
    env["FEA_AX"] = str(ax)
    env["FEA_AY"] = str(ay)
    env["FEA_M"] = str(moment)

    started = time.time()
    result = subprocess.run(
        [str(freecad_cmd), str(SINGLE_CASE_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(WORKSPACE),
        check=False,
    )
    wall_time_s = time.time() - started
    output = result.stdout + result.stderr

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"mesh_{str(mesh_size).replace('.', 'p')}mm.log"
        log_path.write_text(output, encoding="utf-8")

    parsed = parse_run_output(output)
    run_data: dict[str, object] = {
        "mesh_size_mm": mesh_size,
        "returncode": result.returncode,
        "wall_time_s": wall_time_s,
        "stdout": output,
        **parsed,
    }
    return run_data


def validate_run(run_data: dict[str, object]) -> None:
    required_fields = (
        "nodes",
        "elements",
        "x_mm",
        "y_mm",
        "ux",
        "uy",
        "phi",
        "mesh_time_s",
        "solve_time_s",
        "total_time_s",
    )
    if int(run_data["returncode"]) != 0:
        raise RuntimeError(
            f"FreeCADCmd failed for mesh {fmt_mesh_size(float(run_data['mesh_size_mm']))} "
            f"with exit code {run_data['returncode']}."
        )
    missing = [field for field in required_fields if field not in run_data]
    if missing:
        tail = "\n".join(str(run_data["stdout"]).splitlines()[-40:])
        raise RuntimeError(
            f"Could not parse {', '.join(missing)} for mesh {fmt_mesh_size(float(run_data['mesh_size_mm']))}.\n"
            f"Last output lines:\n{tail}"
        )


def build_markdown_report(
    runs: list[dict[str, object]],
    ax: float,
    ay: float,
    moment: float,
    freecad_cmd: Path,
) -> str:
    finest = min(runs, key=lambda item: float(item["mesh_size_mm"]))
    finest_mesh = float(finest["mesh_size_mm"])

    lines: list[str] = []
    lines.append("# 3D Mesh Convergence Study")
    lines.append("")
    lines.append("Script:")
    lines.append(f"- `{SINGLE_CASE_SCRIPT.name}`")
    lines.append("")
    lines.append("Load case:")
    lines.append(f"- `Ax = {ax:g}`")
    lines.append(f"- `Ay = {ay:g}`")
    lines.append(f"- `M = {moment:g}`")
    lines.append("")
    lines.append("Mesh sizes:")
    lines.append("- " + ", ".join(f"`{fmt_mesh_size(float(run['mesh_size_mm']))}`" for run in runs))
    lines.append("")
    lines.append("FreeCAD command:")
    lines.append(f"- `{freecad_cmd}`")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(
        "| Mesh | Nodes | Elements | x (mm) | y (mm) | Ux | Uy | phi (rad) | Mesh Time (s) | Solve Time (s) | Total Time (s) | Wall Time (s) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_mesh_size(float(run["mesh_size_mm"])),
                    fmt_int(run.get("nodes")),
                    fmt_int(run.get("elements")),
                    fmt_value(run.get("x_mm"), 4),
                    fmt_value(run.get("y_mm"), 4),
                    fmt_value(run.get("ux"), 6),
                    fmt_value(run.get("uy"), 6),
                    fmt_value(run.get("phi"), 6),
                    fmt_value(run.get("mesh_time_s"), 1),
                    fmt_value(run.get("solve_time_s"), 1),
                    fmt_value(run.get("total_time_s"), 1),
                    fmt_value(run.get("wall_time_s"), 1),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append(f"## Difference From Finest Mesh ({fmt_mesh_size(finest_mesh)})")
    lines.append("")
    lines.append("| Mesh | Abs dx (mm) | Abs dy (mm) | Abs dphi (rad) | dx Rel. | dy Rel. | dphi Rel. |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_mesh_size(float(run["mesh_size_mm"])),
                    fmt_delta(run.get("x_mm"), finest.get("x_mm"), 4),
                    fmt_delta(run.get("y_mm"), finest.get("y_mm"), 4),
                    fmt_delta(run.get("phi"), finest.get("phi"), 6),
                    fmt_rel_delta(run.get("x_mm"), finest.get("x_mm")),
                    fmt_rel_delta(run.get("y_mm"), finest.get("y_mm")),
                    fmt_rel_delta(run.get("phi"), finest.get("phi")),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        f"The `{fmt_mesh_size(finest_mesh)}` mesh is used as the reference for convergence."
    )
    fastest = min(runs, key=lambda item: float(item.get("total_time_s", float("inf"))))
    lines.append(
        f"The fastest run is `{fmt_mesh_size(float(fastest['mesh_size_mm']))}` with a total solver-reported time of "
        f"`{fmt_value(fastest.get('total_time_s'), 1)} s`."
    )
    lines.append(
        "Use the relative differences above to decide whether the runtime increase from mesh refinement is justified for this load case."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    freecad_cmd = Path(args.freecad)
    report_path = Path(args.report_path)
    mesh_sizes = sorted(set(args.mesh_sizes), reverse=True)
    log_dir = Path(args.log_dir) if args.log_dir else None

    if not freecad_cmd.exists():
        raise FileNotFoundError(f"FreeCADCmd not found: {freecad_cmd}")
    if not SINGLE_CASE_SCRIPT.exists():
        raise FileNotFoundError(f"Single-case script not found: {SINGLE_CASE_SCRIPT}")

    runs: list[dict[str, object]] = []
    for mesh_size in mesh_sizes:
        print(f"Running mesh size {fmt_mesh_size(mesh_size)} ...", flush=True)
        run_data = run_single_case(freecad_cmd, mesh_size, args.ax, args.ay, args.m, log_dir)
        validate_run(run_data)
        runs.append(run_data)
        print(
            "  "
            f"x={fmt_value(run_data.get('x_mm'), 4)} mm, "
            f"y={fmt_value(run_data.get('y_mm'), 4)} mm, "
            f"phi={fmt_value(run_data.get('phi'), 6)} rad, "
            f"total={fmt_value(run_data.get('total_time_s'), 1)} s",
            flush=True,
        )

    report = build_markdown_report(runs, args.ax, args.ay, args.m, freecad_cmd)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Markdown report saved to {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
