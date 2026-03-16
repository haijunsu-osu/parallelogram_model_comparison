"""
Single-case comparison of all parallelogram flexure models.

Default case: Ax=0, Ay=5, M=0

FEA source priority:
  1. Preset sweep CSVs in comparison/preset_data
  2. Live FreeCADCmd fallback if the requested load is not in the sweep

Outputs: comparison/single_case_report.md
"""

import argparse
import csv
from functools import lru_cache
import math
import os
import re
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREECAD = r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe"

FEA_3D_SCRIPT = os.path.join(WORKSPACE, "fea_models", "3d", "parallelogram_3d_single.py")
FEA_2D_SCRIPT = os.path.join(WORKSPACE, "fea_models", "2d", "parallelogram_2d.py")
FEA_2D_CSV = os.path.join(WORKSPACE, "comparison", "_single_case_2d_input.csv")
FEA_2D_OUT = os.path.join(WORKSPACE, "comparison", "_single_case_2d_output.csv")
REPORT_PATH = os.path.join(WORKSPACE, "comparison", "single_case_report.md")

# Add submodule paths so we can import the analytical solvers
for sub in ("euler_beam", "bcm", "prb", "guided_beam"):
    p = os.path.join(WORKSPACE, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from parallelogram_solver import ParallelogramFlexureSolver
from bcm_parallelogram import BCMParallelogram
from prb_parallelogram import PRBParallelogramModel
from guided_beam_solver import compute_tip_displacement
from preset_catalog import PRESET_FILES, find_exact_row, load_exact_index

# ---------------------------------------------------------------------------
# Geometry / normalisation constants (must match FEA scripts)
# ---------------------------------------------------------------------------
L = 250.0        # mm
T = 5.0          # mm
H = 50.0         # mm
W = 150.0        # mm  (full beam-centreline separation)
E = 210e9        # Pa  (Steel)
nu = 0.3

w_norm = (W / 2.0) / L    # = 0.30  (half-separation / L)
t_norm = T / L            # = 0.02


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Compare all parallelogram models for one load case.")
    parser.add_argument("--ax", type=float, default=float(os.environ.get("COMPARE_AX", "0.0")))
    parser.add_argument("--ay", type=float, default=float(os.environ.get("COMPARE_AY", "5.0")))
    parser.add_argument("--m", type=float, default=float(os.environ.get("COMPARE_M", "0.0")))
    parser.add_argument("--report-path", default=REPORT_PATH)
    return parser.parse_args()


def rel_err(val, ref):
    """Relative error (%) vs reference. Returns None if ref == 0."""
    if ref == 0.0:
        return None
    return (val - ref) / abs(ref) * 100.0


def fmt_err(e):
    if e is None:
        return "N/A"
    return f"{e:+.2f}%"


def fmt_val(v, decimals=6):
    return f"{v:.{decimals}f}"


def is_finite_result(*values):
    return all(value is not None and math.isfinite(value) for value in values)


def is_suspicious_zero_result(fy, fx, m_load, x_mm, y_mm, phi):
    return (
        not math.isclose(fy, 0.0, rel_tol=0.0, abs_tol=1e-12)
        or not math.isclose(fx, 0.0, rel_tol=0.0, abs_tol=1e-12)
        or not math.isclose(m_load, 0.0, rel_tol=0.0, abs_tol=1e-12)
    ) and math.isclose(x_mm, 0.0, rel_tol=0.0, abs_tol=1e-12) and math.isclose(
        y_mm, 0.0, rel_tol=0.0, abs_tol=1e-12
    ) and math.isclose(phi, 0.0, rel_tol=0.0, abs_tol=1e-12)


@lru_cache(maxsize=None)
def get_preset_index(csv_path):
    return load_exact_index(csv_path)


def load_preset_row(csv_path, ay, ax, m_load):
    return find_exact_row(get_preset_index(csv_path), ay, ax, m_load)


def preset_row_to_result(row):
    x_mm = None
    y_mm = None
    if "x" in row and "y" in row:
        x_mm = float(row["x"])
        y_mm = float(row["y"])
    elif "ux" in row and "uy" in row:
        x_mm = float(row["ux"]) * L
        y_mm = float(row["uy"]) * L
    Ux = float(row.get("ux", row.get("Ux")))
    Uy = float(row.get("uy", row.get("Uy")))
    phi = float(row["phi"])
    solve_t = float(row["t"])
    return Ux, Uy, phi, solve_t, x_mm, y_mm


# ---------------------------------------------------------------------------
# Runner: FEA 3D (solid elements)
# ---------------------------------------------------------------------------
def run_fea_3d(ax, ay, m_load):
    preset_row = load_preset_row(PRESET_FILES["fea_3d"], ay, ax, m_load)
    if preset_row is not None:
        print(f"Using preset FEA 3D sweep row for Ax={ax}, Ay={ay}, M={m_load} ...")
        Ux, Uy, phi, solve_t, _x_mm, _y_mm = preset_row_to_result(preset_row)
        if is_suspicious_zero_result(ay, ax, m_load, Ux, Uy, phi):
            preset_row = None
        else:
            print(f"  Ux={Ux:.6f}  Uy={Uy:.6f}  phi={phi:.6f}  solver_t={solve_t:.1f}s")
            return (
                Ux,
                Uy,
                phi,
                solve_t,
                None,
                None,
                f"preset sweep: {os.path.basename(PRESET_FILES['fea_3d'])}",
            )

    print("Running FEA 3D (solid) via FreeCADCmd fallback ...")
    env = os.environ.copy()
    env["FEA_AX"] = str(ax)
    env["FEA_AY"] = str(ay)
    env["FEA_M"] = str(m_load)

    wall_start = time.time()
    result = subprocess.run([FREECAD, FEA_3D_SCRIPT], capture_output=True, text=True, env=env)
    wall = time.time() - wall_start

    out = result.stdout + result.stderr
    Ux = Uy = phi = x_mm = y_mm = solve_t = None

    for line in out.splitlines():
        m = re.search(r"^\s*x\s*=\s*([-\d.eE+]+)\s*mm", line)
        if m:
            x_mm = float(m.group(1))
        m = re.search(r"^\s*y\s*=\s*([-\d.eE+]+)\s*mm", line)
        if m:
            y_mm = float(m.group(1))
        m = re.search(r"Ux\s*=\s*x/L\s*=\s*([-\d.eE+]+)", line)
        if m:
            Ux = float(m.group(1))
        m = re.search(r"Uy\s*=\s*y/L\s*=\s*([-\d.eE+]+)", line)
        if m:
            Uy = float(m.group(1))
        m = re.search(r"phi\s*=\s*([-\d.eE+]+)\s*rad", line)
        if m:
            phi = float(m.group(1))
        m = re.search(r"Times:\s*mesh=[-\d.eE+]+s\s+solve=([-\d.eE+]+)s", line)
        if m:
            solve_t = float(m.group(1))

    if Ux is None or Uy is None or phi is None:
        print("  ERROR: could not parse FEA 3D output.")
        print("  stdout:", out[:2000])
        return None, None, None, wall, None, None, "live FreeCAD fallback (failed)"

    if solve_t is None:
        solve_t = wall
    print(f"  Ux={Ux:.6f}  Uy={Uy:.6f}  phi={phi:.6f}  solver_t={solve_t:.1f}s")
    return Ux, Uy, phi, solve_t, x_mm, y_mm, "live FreeCAD fallback"


# ---------------------------------------------------------------------------
# Runner: FEA 2D (beam elements)
# ---------------------------------------------------------------------------
def run_fea_2d(ax, ay, m_load):
    preset_row = load_preset_row(PRESET_FILES["fea_2d"], ay, ax, m_load)
    if preset_row is not None:
        print(f"Using preset FEA 2D sweep row for Ax={ax}, Ay={ay}, M={m_load} ...")
        Ux, Uy, phi, solve_t, _x_mm, _y_mm = preset_row_to_result(preset_row)
        if not is_suspicious_zero_result(ay, ax, m_load, Ux, Uy, phi):
            print(f"  Ux={Ux:.6f}  Uy={Uy:.6f}  phi={phi:.6f}  solver_t={solve_t:.1f}s")
            return (
                Ux,
                Uy,
                phi,
                solve_t,
                None,
                None,
                f"preset sweep: {os.path.basename(PRESET_FILES['fea_2d'])}",
            )

    print("Running FEA 2D (beam) via FreeCADCmd fallback ...")
    with open(FEA_2D_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Ay", "Ax", "M"])
        writer.writeheader()
        writer.writerow({"Ay": ay, "Ax": ax, "M": m_load})

    wall_start = time.time()
    result = subprocess.run(
        [FREECAD, FEA_2D_SCRIPT, "--load-cases-csv", FEA_2D_CSV, "--output-csv", FEA_2D_OUT],
        capture_output=True,
        text=True,
    )
    wall = time.time() - wall_start
    out = result.stdout + result.stderr

    if result.returncode != 0 or not os.path.exists(FEA_2D_OUT):
        print("  ERROR: could not read FEA 2D output.")
        print("  stdout:", out[:2000])
        return None, None, None, wall, None, None, "live FreeCAD fallback (failed)"

    with open(FEA_2D_OUT, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("  ERROR: FEA 2D output CSV is empty.")
        print("  stdout:", out[:2000])
        return None, None, None, wall, None, None, "live FreeCAD fallback (failed)"

    last_row = rows[-1]
    x_mm = float(last_row["x"])
    y_mm = float(last_row["y"])
    Ux = float(last_row["Ux"])
    Uy = float(last_row["Uy"])
    phi = float(last_row["phi"])
    solve_t = float(last_row["t"])

    print(f"  Ux={Ux:.6f}  Uy={Uy:.6f}  phi={phi:.6f}  solver_t={solve_t:.1f}s")
    return Ux, Uy, phi, solve_t, x_mm, y_mm, "live FreeCAD fallback"


# ---------------------------------------------------------------------------
# Analytical model runners
# ---------------------------------------------------------------------------
def compute_euler_bvp(ax, ay, m_load):
    t0 = time.time()
    solver = ParallelogramFlexureSolver(w=w_norm)
    solver.solve(ax, ay, m_load)
    elapsed = time.time() - t0
    Ux = solver.X_p - 1.0
    Uy = solver.Y_p
    phi = solver.phi
    return Ux, Uy, phi, elapsed


def compute_guided_beam(ax, ay):
    t0 = time.time()
    delta, ux, beta = compute_tip_displacement(alpha_y=ay / 2.0, alpha_x=ax / 2.0)
    elapsed = time.time() - t0
    Uy = delta
    Ux = ux
    phi = 0.0
    return Ux, Uy, phi, elapsed


def compute_prb_standard(ay):
    t0 = time.time()
    model = PRBParallelogramModel(w=w_norm)
    delta, ux, phi_prb, theta = model.solve(ay)
    elapsed = time.time() - t0
    return ux, delta, phi_prb, elapsed


def compute_prb_optimised(ay):
    t0 = time.time()
    model = PRBParallelogramModel(w=w_norm)
    model.gamma = 0.90
    model.K_theta_coeff = 2.50
    delta, ux, phi_prb, theta = model.solve(ay)
    elapsed = time.time() - t0
    return ux, delta, phi_prb, elapsed


def compute_bcm(ax, ay, m_load):
    t0 = time.time()
    model = BCMParallelogram(w=w_norm, t=t_norm)
    res = model.solve(ax, ay, B=m_load)
    elapsed = time.time() - t0
    Uy = res["delta"]
    Ux = -res["u1"]
    phi = res["phi"]
    return Ux, Uy, phi, elapsed


def compute_linear(ay):
    t0 = time.time()
    Uy = ay / 24.0
    Ux = 0.0
    phi = 0.0
    elapsed = time.time() - t0
    return Ux, Uy, phi, elapsed


def run_preset_or_live(csv_path, label, ay, ax, m_load, live_runner):
    preset_row = load_preset_row(csv_path, ay, ax, m_load)
    if preset_row is not None:
        Ux, Uy, phi, solve_t, _x_mm, _y_mm = preset_row_to_result(preset_row)
        print(f"Using preset {label} row for Ax={ax}, Ay={ay}, M={m_load} ...")
        if not is_finite_result(Ux, Uy, phi):
            print(f"  FAILED  solver_t={solve_t:.4f}s")
            return None, None, None, solve_t, f"preset sweep: {os.path.basename(csv_path)} (failed)"
        print(f"  Ux={Ux:.6f}  Uy={Uy:.6f}  phi={phi:.6f}  solver_t={solve_t:.4f}s")
        return Ux, Uy, phi, solve_t, f"preset sweep: {os.path.basename(csv_path)}"
    Ux, Uy, phi, solve_t = live_runner()
    return Ux, Uy, phi, solve_t, "live analytical solve"


def run_linear(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["linear"],
        "Linear",
        ay,
        ax,
        m_load,
        lambda: compute_linear(ay),
    )


def run_bcm(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["bcm"],
        "BCM",
        ay,
        ax,
        m_load,
        lambda: compute_bcm(ax, ay, m_load),
    )


def run_prb_standard(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["prb_standard"],
        "PRB standard",
        ay,
        ax,
        m_load,
        lambda: compute_prb_standard(ay),
    )


def run_prb_optimised(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["prb_optimized"],
        "PRB optimized",
        ay,
        ax,
        m_load,
        lambda: compute_prb_optimised(ay),
    )


def run_guided_beam(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["guided_beam"],
        "Guided Beam",
        ay,
        ax,
        m_load,
        lambda: compute_guided_beam(ax, ay),
    )


def run_euler_bvp(ax, ay, m_load):
    return run_preset_or_live(
        PRESET_FILES["euler_bvp"],
        "Euler BVP",
        ay,
        ax,
        m_load,
        lambda: compute_euler_bvp(ax, ay, m_load),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    ax = args.ax
    ay = args.ay
    m_load = args.m

    print("=" * 60)
    print(f"Single-case comparison: Ax={ax}, Ay={ay}, M={m_load}")
    print(f"Geometry: L={L}mm, T={T}mm, H={H}mm, W={W}mm (full), E={E/1e9:.0f}GPa")
    print("=" * 60)

    # ---- Run all models ----
    lin_Ux, lin_Uy, lin_phi, lin_t, lin_source = run_linear(ax, ay, m_load)
    bcm_Ux, bcm_Uy, bcm_phi, bcm_t, bcm_source = run_bcm(ax, ay, m_load)
    prbs_Ux, prbs_Uy, prbs_phi, prbs_t, prbs_source = run_prb_standard(ax, ay, m_load)
    prbo_Ux, prbo_Uy, prbo_phi, prbo_t, prbo_source = run_prb_optimised(ax, ay, m_load)
    gb_Ux, gb_Uy, gb_phi, gb_t, gb_source = run_guided_beam(ax, ay, m_load)
    eu_Ux, eu_Uy, eu_phi, eu_t, eu_source = run_euler_bvp(ax, ay, m_load)

    fea2_Ux, fea2_Uy, fea2_phi, fea2_t, fea2_x_mm, fea2_y_mm, fea2_source = run_fea_2d(ax, ay, m_load)
    fea3_Ux, fea3_Uy, fea3_phi, fea3_t, fea3_x_mm, fea3_y_mm, fea3_source = run_fea_3d(ax, ay, m_load)

    gt_Ux = fea3_Ux
    gt_Uy = fea3_Uy
    gt_phi = fea3_phi

    if gt_Ux is None:
        print("\nERROR: FEA 3D failed - cannot produce report.")
        return

    fea2_label = "FEA 2D (beam, preset)" if fea2_source.startswith("preset") else "FEA 2D (beam, live)"
    fea3_label = "FEA 3D (ground, preset)" if fea3_source.startswith("preset") else "FEA 3D (ground, live)"

    rows = [
        ("Linear theory", lin_Ux, lin_Uy, lin_phi, lin_t),
        ("BCM (Awtar)", bcm_Ux, bcm_Uy, bcm_phi, bcm_t),
        ("PRB standard", prbs_Ux, prbs_Uy, prbs_phi, prbs_t),
        ("PRB optimised", prbo_Ux, prbo_Uy, prbo_phi, prbo_t),
        ("Guided Beam", gb_Ux, gb_Uy, gb_phi, gb_t),
        ("Euler BVP", eu_Ux, eu_Uy, eu_phi, eu_t),
        (fea2_label, fea2_Ux, fea2_Uy, fea2_phi, fea2_t),
        (fea3_label, fea3_Ux, fea3_Uy, fea3_phi, fea3_t),
    ]

    hdr = f"{'Model':<24}  {'Ux':>10}  {'Uy':>10}  {'phi(rad)':>12}  "
    hdr += f"{'eUx%':>8}  {'eUy%':>8}  {'ephi%':>9}  {'t(s)':>8}"
    print("\n" + hdr)
    print("-" * len(hdr))
    for lbl, Ux, Uy, phi, t in rows:
        is_gt = "(ground" in lbl
        if not is_finite_result(Ux, Uy, phi):
            print(f"  {lbl:<24}  {'FAILED':>10}")
            continue
        eUx = fmt_err(rel_err(Ux, gt_Ux))
        eUy = fmt_err(rel_err(Uy, gt_Uy))
        ephi = fmt_err(rel_err(phi, gt_phi))
        gt_mark = " <" if is_gt else ""
        print(
            f"  {lbl:<24}  {Ux:>10.6f}  {Uy:>10.6f}  {phi:>12.6f}  "
            f"{eUx:>8}  {eUy:>8}  {ephi:>9}  {t:>8.3f}{gt_mark}"
        )

    lines = []
    lines.append("# Parallelogram Flexure - Single-Case Model Comparison")
    lines.append("")
    lines.append(f"**Test case:** Ax = {ax},  Ay = {ay},  M = {m_load}")
    lines.append("")
    lines.append("**Geometry / material:**")
    lines.append(f"- L = {L} mm, T = {T} mm, H = {H} mm")
    lines.append(f"- W = {W} mm (full centreline separation; beams at y = +/-{W/2:.0f} mm)")
    lines.append(f"- E = {E/1e9:.0f} GPa (Steel), nu = {nu}")
    lines.append(f"- Normalised: w = W/(2L) = {w_norm:.2f}, t = T/L = {t_norm:.4f}")
    lines.append("")
    lines.append("**Ground truth:** FEA 3D solid-element model")
    lines.append("")
    lines.append(f"**FEA 2D source:** {fea2_source}")
    lines.append(f"**FEA 3D source:** {fea3_source}")
    lines.append(f"**Linear source:** {lin_source}")
    lines.append(f"**BCM source:** {bcm_source}")
    lines.append(f"**PRB standard source:** {prbs_source}")
    lines.append(f"**PRB optimised source:** {prbo_source}")
    lines.append(f"**Guided Beam source:** {gb_source}")
    lines.append(f"**Euler BVP source:** {eu_source}")
    lines.append("")
    lines.append("> **Sign convention:** phi is CCW-positive throughout. FEA uses")
    lines.append("> `phi = atan2(Delta x_bot - Delta x_top, W_sep - Delta y_sep)`.")
    lines.append("")

    lines.append("## Results")
    lines.append("")
    col_w = [24, 10, 10, 12, 9, 9, 10, 8]
    header_cells = ["Model", "Ux", "Uy", "phi (rad)", "eUx (%)", "eUy (%)", "ephi (%)", "t (s)"]
    sep_cells = ["-" * w for w in col_w]

    def md_row(cells):
        return "| " + " | ".join(f"{c:<{col_w[i]}}" for i, c in enumerate(cells)) + " |"

    lines.append(md_row(header_cells))
    lines.append(md_row(sep_cells))

    for lbl, Ux, Uy, phi, t in rows:
        is_gt = "(ground" in lbl
        if not is_finite_result(Ux, Uy, phi):
            lines.append(md_row([lbl, "FAILED", "", "", "", "", "", ""]))
            continue
        eUx = fmt_err(rel_err(Ux, gt_Ux))
        eUy = fmt_err(rel_err(Uy, gt_Uy))
        ephi = fmt_err(rel_err(phi, gt_phi))
        gt_mark = " **<**" if is_gt else ""
        t_str = f"{t:.3f}" if t < 1000 else f"{t:.1f}"
        cells = [lbl + gt_mark, fmt_val(Ux), fmt_val(Uy), fmt_val(phi), eUx, eUy, ephi, t_str]
        lines.append(md_row(cells))

    lines.append("")
    lines.append("## Ground Truth (FEA 3D)")
    lines.append("")
    lines.append("| Quantity | Value |")
    lines.append("| -------- | ----- |")
    lines.append(f"| Ux       | {gt_Ux:.6f} |")
    lines.append(f"| Uy       | {gt_Uy:.6f} |")
    if fea3_x_mm is not None and fea3_y_mm is not None:
        lines.append(f"| x (mm)   | {fea3_x_mm:.6f} |")
        lines.append(f"| y (mm)   | {fea3_y_mm:.6f} |")
    lines.append(f"| phi (rad) | {gt_phi:.6f} |")
    lines.append(f"| Runtime  | {fea3_t:.1f} s |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **FEA 3D**: 3D solid-element model (BooleanFragments + Slice, CalculiX linear static).")
    lines.append("- **FEA 2D**: 2D beam-element model (Euler-Bernoulli beams + quasi-rigid stage, CalculiX).")
    lines.append("- When the load matches the preset sweep grid, the report uses the precomputed preset CSV rows for all models.")
    lines.append("- If the load is outside the preset grid, analytical models solve live and FEA falls back to FreeCAD.")
    lines.append("- **Euler BVP**: exact nonlinear solution of coupled beam BVPs plus rigid-stage compatibility.")
    lines.append("- **Guided Beam**: single fixed-guided beam BVP with half-load approximation.")
    lines.append("- **PRB standard / optimised**: reduced-order nonlinear approximations for the same geometry.")
    lines.append("- **Linear theory**: Uy = Ay/24 with Ux = 0 and phi = 0.")
    lines.append("")
    lines.append(f"*Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*")

    report_text = "\n".join(lines)
    with open(args.report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nReport saved: {args.report_path}")


if __name__ == "__main__":
    main()
