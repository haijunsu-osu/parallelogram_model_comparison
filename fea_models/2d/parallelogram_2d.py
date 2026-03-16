# Parallelogram Compliant Mechanism 2D FEA
# Based on parallelogram_2d_simplified.py (beam elements, multi-material stage).
# Parameter conventions from parallelogram_t2mm_simple.py:
#   W  = full beam centerline separation (mm)  [W=150 → beams at y=+W/2 and y=-W/2]
#   Ax, Ay, M = normalized loads (Fx*L²/EI, Fy*L²/EI, Mz*L/EI)
#   x, y = stage center displacement (mm);  Ux=x/L, Uy=y/L = normalized
#
# Parameters: L=250, T=5, H=50, W=150, E=210 GPa (Steel), nu=0.3
# Stage: rigid beam segments at x=L, spanning y=−W/2 to y=+W/2
# Moment via force couple at ±MOMENT_ARM from centre
#
# Run: & "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" parallelogram_2d.py

import argparse
import csv
import math
import os
import time

import FreeCAD as App
import ObjectsFem
import Part

start_time = time.time()

# ============================================================
# PARAMETERS
# ============================================================
L = 250.0
W = 150.0          # full centerline separation (mm) — beams at y = +W/2 and y = -W/2
H = 50.0
T = 5.0
E_BEAM  = 210e9    # Steel (Pa)
E_STAGE = 5000e9   # quasi-rigid stage (Pa)
NU = 0.3
MOMENT_ARM = 50.0  # moment arm from centre (mm) — force couple applied at y = ±MOMENT_ARM
BEAM_MESH_CHAR_LEN  = 6.5
STAGE_MESH_CHAR_LEN = 6.5

I_BEAM        = (H / 1000.0) * ((T / 1000.0) ** 3) / 12.0   # m⁴
F_NORM_FACTOR = E_BEAM * I_BEAM / ((L / 1000.0) ** 2)        # N per unit Ax/Ay
M_NORM_FACTOR = E_BEAM * I_BEAM / (L / 1000.0)               # N·m per unit M


# ============================================================
# LOAD CASES
# ============================================================
def default_load_cases():
    ax_values = [0, 1, 2]
    ay_values = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20]
    m_values  = [-3, -2, -1, 0, 1, 2, 3]
    load_cases = []
    for ax_val in ax_values:
        for ay_val in ay_values:
            for m_val in m_values:
                load_cases.append((float(ay_val), float(ax_val), float(m_val)))
    return load_cases


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the 2D parallelogram FEA sweep (beam elements, new parameter conventions)."
    )
    parser.add_argument(
        "--load-cases-csv",
        dest="load_cases_csv",
        default=os.environ.get("FEA_LOAD_CASES_CSV", ""),
        help="Optional CSV with columns Ay, Ax, M (or fy, fx, m).",
    )
    parser.add_argument(
        "--output-csv",
        dest="output_csv",
        default=os.environ.get("FEA_OUTPUT_CSV", ""),
        help="Optional output CSV path.",
    )
    parser.add_argument(
        "--resume-completed-rows",
        dest="resume_completed_rows",
        type=int,
        default=int(os.environ.get("FEA_RESUME_COMPLETED_ROWS", "0") or "0"),
        help="Resume after this many already-completed rows in the output CSV.",
    )
    args, _unknown = parser.parse_known_args()
    return args


def get_row_value(row, candidates):
    normalized = {str(k).strip().lower(): v for k, v in row.items()}
    for c in candidates:
        if c in normalized:
            return normalized[c]
    raise KeyError(f"None of the candidate columns were found: {candidates}")


def load_cases_from_csv(csv_path):
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        load_cases = []
        for row in reader:
            ay_text = str(get_row_value(row, ["ay", "fy"])).strip()
            ax_text = str(get_row_value(row, ["ax", "fx"])).strip()
            m_text  = str(get_row_value(row, ["m"])).strip()
            if not ay_text and not ax_text and not m_text:
                continue
            load_cases.append((float(ay_text), float(ax_text), float(m_text)))
    return load_cases


def latest_result_object(analysis):
    result_objects = [o for o in analysis.Group if o.isDerivedFrom("Fem::FemResultObject")]
    if not result_objects:
        return None
    time_results = [o for o in result_objects if "Time_" in o.Label]
    if not time_results:
        return result_objects[-1]

    def get_time_value(label):
        try:
            return float(label.replace("CCX_Time_", "").replace("_Results", "").replace("_", "."))
        except Exception:
            return 0.0

    time_results.sort(key=lambda o: get_time_value(o.Label))
    return time_results[-1]


def get_result_mesh(result_object):
    mesh_container = result_object.Mesh
    if hasattr(mesh_container, "FemMesh"):
        return mesh_container.FemMesh
    return mesh_container


def clear_existing_results(doc):
    for obj in list(doc.Objects):
        if obj.Name.startswith("CCX_Results"):
            doc.removeObject(obj.Name)
    doc.recompute()


def find_nearest_displacement(result_mesh, displacements, target_point):
    nodes = result_mesh.Nodes
    node_ids = sorted(nodes.keys())
    displacement_map = {nid: displacements[i] for i, nid in enumerate(node_ids)}
    best_nid, best_d2 = None, 1e99
    for nid in node_ids:
        x, y, z = nodes[nid]
        d2 = (x - target_point.x)**2 + (y - target_point.y)**2 + (z - target_point.z)**2
        if d2 < best_d2:
            best_d2 = d2
            best_nid = nid
    return displacement_map[best_nid]


# ============================================================
# SETUP
# ============================================================
args = parse_args()
load_cases = load_cases_from_csv(args.load_cases_csv) if args.load_cases_csv else default_load_cases()
csv_path = (
    args.output_csv if args.output_csv
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "PARALLELOGRAM2D_allcases.csv")
)
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

if args.resume_completed_rows < 0:
    raise ValueError("resume_completed_rows must be non-negative")
if args.resume_completed_rows > len(load_cases):
    raise ValueError(
        f"resume_completed_rows={args.resume_completed_rows} exceeds available load cases ({len(load_cases)})"
    )

print("=" * 60)
print("PARALLELOGRAM FLEXURE 2D FEA")
print("=" * 60)
print(f"Geometry: L={L}, T={T}, H={H}, W={W} mm (full separation)")
print(f"  Beam centrelines at y=+{W/2:.0f} and y=-{W/2:.0f} mm")
print(f"MOMENT_ARM={MOMENT_ARM} mm")
print(f"Material: E_beam={E_BEAM/1e9:.0f} GPa (Steel), E_stage={E_STAGE/1e9:.0f} GPa, nu={NU}")
print(f"I = {I_BEAM:.6e} m^4")
print(f"F_NORM_FACTOR = {F_NORM_FACTOR:.4f} N")
print(f"M_NORM_FACTOR = {M_NORM_FACTOR:.4f} N·m")
print(f"Beam mesh = {BEAM_MESH_CHAR_LEN} mm,  Stage mesh = {STAGE_MESH_CHAR_LEN} mm")
print(f"Load cases: {len(load_cases)}")

# ============================================================
# GEOMETRY
# W = full separation; half = W/2
# Top beam centreline:    y = +W/2
# Bottom beam centreline: y = -W/2
# Stage (at x=L) runs from y=-W/2 to y=+W/2, split at ±MOMENT_ARM and 0
# ============================================================
doc = App.newDocument("Parallelogram2D")

top_beam_shape = Part.makeLine(App.Vector(0.0, W/2, 0.0), App.Vector(L, W/2, 0.0))
top_beam_obj = doc.addObject("Part::Feature", "TopBeam")
top_beam_obj.Shape = top_beam_shape

bottom_beam_shape = Part.makeLine(App.Vector(0.0, -W/2, 0.0), App.Vector(L, -W/2, 0.0))
bottom_beam_obj = doc.addObject("Part::Feature", "BottomBeam")
bottom_beam_obj.Shape = bottom_beam_shape

# Stage segments (rigid beam members connecting both beam tips at x=L)
# Split at MOMENT_ARM to allow moment couple application
stage_top_outer_shape = Part.makeLine(App.Vector(L, W/2, 0.0), App.Vector(L, MOMENT_ARM, 0.0))
stage_top_outer_obj = doc.addObject("Part::Feature", "StageTopOuter")
stage_top_outer_obj.Shape = stage_top_outer_shape

stage_top_inner_shape = Part.makeLine(App.Vector(L, MOMENT_ARM, 0.0), App.Vector(L, 0.0, 0.0))
stage_top_inner_obj = doc.addObject("Part::Feature", "StageTopInner")
stage_top_inner_obj.Shape = stage_top_inner_shape

stage_bottom_inner_shape = Part.makeLine(App.Vector(L, 0.0, 0.0), App.Vector(L, -MOMENT_ARM, 0.0))
stage_bottom_inner_obj = doc.addObject("Part::Feature", "StageBottomInner")
stage_bottom_inner_obj.Shape = stage_bottom_inner_shape

stage_bottom_outer_shape = Part.makeLine(App.Vector(L, -MOMENT_ARM, 0.0), App.Vector(L, -W/2, 0.0))
stage_bottom_outer_obj = doc.addObject("Part::Feature", "StageBottomOuter")
stage_bottom_outer_obj.Shape = stage_bottom_outer_shape

compound_shape = Part.makeCompound([
    top_beam_shape,
    bottom_beam_shape,
    stage_top_outer_shape,
    stage_top_inner_shape,
    stage_bottom_inner_shape,
    stage_bottom_outer_shape,
])
compound_obj = doc.addObject("Part::Feature", "CompoundNode")
compound_obj.Shape = compound_shape
doc.recompute()

# ============================================================
# FEM ANALYSIS
# ============================================================
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")

# Beam cross-section: T (width, bending direction) × H (height, out-of-plane)
beam_section = ObjectsFem.makeElementGeometry1D(doc, "BeamSection")
beam_section.SectionType = "Rectangular"
beam_section.RectWidth  = T
beam_section.RectHeight = H
beam_section.References = [
    (top_beam_obj,    "Edge1"),
    (bottom_beam_obj, "Edge1"),
]
analysis.addObject(beam_section)

# Stage cross-section: square H×H (quasi-rigid)
stage_section = ObjectsFem.makeElementGeometry1D(doc, "StageSection")
stage_section.SectionType = "Rectangular"
stage_section.RectWidth  = H
stage_section.RectHeight = H
stage_section.References = [
    (stage_top_outer_obj,    "Edge1"),
    (stage_top_inner_obj,    "Edge1"),
    (stage_bottom_inner_obj, "Edge1"),
    (stage_bottom_outer_obj, "Edge1"),
]
analysis.addObject(stage_section)

# Material: Steel for beams
steel_mat = ObjectsFem.makeMaterialSolid(doc, "SteelMat")
steel_mat.Material = {
    "Name": "Steel",
    "YoungsModulus": f"{E_BEAM / 1e9} GPa",
    "PoissonRatio": str(NU),
}
steel_mat.References = [
    (top_beam_obj,    "Edge1"),
    (bottom_beam_obj, "Edge1"),
]
analysis.addObject(steel_mat)

# Material: quasi-rigid for stage
rigid_mat = ObjectsFem.makeMaterialSolid(doc, "RigidMat")
rigid_mat.Material = {
    "Name": "RigidStage",
    "YoungsModulus": f"{E_STAGE / 1e9} GPa",
    "PoissonRatio": str(NU),
}
rigid_mat.References = [
    (stage_top_outer_obj,    "Edge1"),
    (stage_top_inner_obj,    "Edge1"),
    (stage_bottom_inner_obj, "Edge1"),
    (stage_bottom_outer_obj, "Edge1"),
]
analysis.addObject(rigid_mat)

# Mesh
mesh_obj = ObjectsFem.makeMeshGmsh(doc, "BeamMesh")
mesh_obj.Shape = compound_obj
mesh_obj.ElementOrder = "2nd"
mesh_obj.CharacteristicLengthMax = STAGE_MESH_CHAR_LEN
analysis.addObject(mesh_obj)

beam_mesh_region = ObjectsFem.makeMeshRegion(doc, mesh_obj)
beam_mesh_region.CharacteristicLength = BEAM_MESH_CHAR_LEN
beam_mesh_region.References = [
    (top_beam_obj,    "Edge1"),
    (bottom_beam_obj, "Edge1"),
]

print(f"Generating mesh (beam={BEAM_MESH_CHAR_LEN}, stage={STAGE_MESH_CHAR_LEN})...")
mesh_start = time.time()
from femmesh import gmshtools
gmsh_tools = gmshtools.GmshTools(mesh_obj)
mesh_error = gmsh_tools.create_mesh()
if mesh_error:
    raise RuntimeError(f"Mesh generation failed: {mesh_error}")
doc.recompute()
mesh_time = time.time() - mesh_start
print(f"Mesh completed in {mesh_time:.2f} s")

# Solver (nonlinear, matching original settings)
solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
solver.AnalysisType = 0
solver.EigenmodesCount = 10
solver.EigenmodeLowLimit = 0.0
solver.EigenmodeHighLimit = 1000000.0
solver.GeometricalNonlinearity = "nonlinear"
solver.IterationsMaximum = 2000000
solver.TimeInitialStep = 1.0
solver.IterationsUserDefinedTimeStepLength = True
solver.TimeEnd = 1.0
solver.ThermoMechSteadyState = True
solver.IterationsControlParameterTimeUse = True
solver.IterationsControlParameterIter = "200000,200000,9,200000,20000,400,,200,,"
solver.TimeMinimumStep = 1e-05
solver.TimeMaximumStep = 1.0
solver.SplitInputWriter = False
solver.MatrixSolverType = 0
solver.BeamShellResultOutput3D = True
solver.OutputFrequency = 100000000
analysis.addObject(solver)

# Fixed BC: both beam left ends (Vertex1 = starting point of each line at x=0)
fixed = ObjectsFem.makeConstraintFixed(doc, "ConstraintFixed")
fixed.References = [
    (top_beam_obj,    "Vertex1"),
    (bottom_beam_obj, "Vertex1"),
]
analysis.addObject(fixed)

# Direction reference lines
dir_x = doc.addObject("Part::Line", "DirX")
dir_x.X1 = dir_x.Y1 = dir_x.Z1 = 0.0
dir_x.X2 = 100.0; dir_x.Y2 = 0.0; dir_x.Z2 = 0.0

dir_y = doc.addObject("Part::Line", "DirY")
dir_y.X1 = dir_y.Y1 = dir_y.Z1 = 0.0
dir_y.X2 = 0.0; dir_y.Y2 = 100.0; dir_y.Z2 = 0.0
doc.recompute()

# Ax (Fx) applied at stage centre: Vertex2 of StageTopInner = (L, 0, 0)
force_x = ObjectsFem.makeConstraintForce(doc, "ConstraintForceX")
force_x.References = [(stage_top_inner_obj, "Vertex2")]
force_x.Direction = (dir_x, ["Edge1"])
force_x.Force = "0 N"
force_x.Reversed = False
analysis.addObject(force_x)

# Ay (Fy) applied at stage centre
force_y = ObjectsFem.makeConstraintForce(doc, "ConstraintForceY")
force_y.References = [(stage_top_inner_obj, "Vertex2")]
force_y.Direction = (dir_y, ["Edge1"])
force_y.Force = "0 N"
force_y.Reversed = False
analysis.addObject(force_y)

# Moment couple:
#   force in +X at (L, +MOMENT_ARM, 0) — Vertex1 of StageTopInner
#   force in -X at (L, -MOMENT_ARM, 0) — Vertex2 of StageBottomInner
# moment_force_value = -M * M_NORM_FACTOR / (MOMENT_ARM/1000)
# (negative sign + Reversed=True on bottom → net CCW moment for M>0)
moment_force_top = ObjectsFem.makeConstraintForce(doc, "ConstraintForceMTop")
moment_force_top.References = [(stage_top_inner_obj, "Vertex1")]
moment_force_top.Direction = (dir_x, ["Edge1"])
moment_force_top.Force = "0 N"
analysis.addObject(moment_force_top)

moment_force_bottom = ObjectsFem.makeConstraintForce(doc, "ConstraintForceMBottom")
moment_force_bottom.References = [(stage_bottom_inner_obj, "Vertex2")]
moment_force_bottom.Direction = (dir_x, ["Edge1"])
moment_force_bottom.Force = "0 N"
moment_force_bottom.Reversed = True
analysis.addObject(moment_force_bottom)
doc.recompute()

# Probe points (beam tips at x=L, on beam centrelines)
target_top    = App.Vector(L,  W/2, 0.0)   # top beam tip
target_bottom = App.Vector(L, -W/2, 0.0)   # bottom beam tip
target_mid    = App.Vector(L,  0.0, 0.0)   # stage centre

from femtools import ccxtools

setup_complete_time = time.time()
results = []

if args.resume_completed_rows > 0:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"resume_completed_rows={args.resume_completed_rows} requested but output CSV not found: {csv_path}"
        )
    with open(csv_path, "r", newline="", encoding="utf-8") as fh:
        existing_reader = csv.DictReader(fh)
        results.extend(existing_reader)

# ============================================================
# SIMULATION LOOP
# ============================================================
csv_mode = "a" if args.resume_completed_rows > 0 else "w"
with open(csv_path, csv_mode, newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=["Ay", "Ax", "M", "x", "y", "Ux", "Uy", "phi", "t"])
    if csv_mode == "w":
        writer.writeheader()

    for case_index, (ay_val, ax_val, m_val) in enumerate(
        load_cases[args.resume_completed_rows:],
        start=args.resume_completed_rows + 1,
    ):
        print(f"\n--- case {case_index}/{len(load_cases)}: Ay={ay_val}, Ax={ax_val}, M={m_val} ---")

        Fy_phys = ay_val * F_NORM_FACTOR           # N
        Fx_phys = ax_val * F_NORM_FACTOR           # N
        Mz_phys = m_val  * M_NORM_FACTOR           # N·m
        moment_force_value = -m_val * M_NORM_FACTOR / (MOMENT_ARM / 1000.0) if m_val != 0 else 0.0

        force_x.Force = str(Fx_phys) + " N"
        force_y.Force = str(Fy_phys) + " N"
        moment_force_top.Force    = str(moment_force_value) + " N"
        moment_force_bottom.Force = str(moment_force_value) + " N"

        clear_existing_results(doc)
        doc.recompute()

        fea = ccxtools.FemToolsCcx(analysis, solver)
        fea.purge_results()
        fea.update_objects()
        fea.write_inp_file()

        solve_start = time.time()
        try:
            fea.run()
            solve_time = time.time() - solve_start
            fea.load_results()
        except Exception:
            import traceback
            solve_time = time.time() - solve_start
            print(f"EXCEPTION:\n{traceback.format_exc()}")
            result_row = {"Ay": ay_val, "Ax": ax_val, "M": m_val,
                          "x": 0, "y": 0, "Ux": 0, "Uy": 0, "phi": 0, "t": solve_time}
            results.append(result_row)
            writer.writerow(result_row)
            fh.flush()
            continue

        if not fea.results_present:
            print("  ERROR: Solver failed - no results present!")
            result_row = {"Ay": ay_val, "Ax": ax_val, "M": m_val,
                          "x": 0, "y": 0, "Ux": 0, "Uy": 0, "phi": 0, "t": solve_time}
            results.append(result_row)
            writer.writerow(result_row)
            fh.flush()
            continue

        result_object = latest_result_object(analysis)
        if result_object is None:
            print("  ERROR: No FemResultObject found!")
            result_row = {"Ay": ay_val, "Ax": ax_val, "M": m_val,
                          "x": 0, "y": 0, "Ux": 0, "Uy": 0, "phi": 0, "t": solve_time}
            results.append(result_row)
            writer.writerow(result_row)
            fh.flush()
            continue

        displacements = result_object.DisplacementVectors
        result_mesh   = get_result_mesh(result_object)

        top_disp    = find_nearest_displacement(result_mesh, displacements, target_top)
        bottom_disp = find_nearest_displacement(result_mesh, displacements, target_bottom)
        mid_disp    = find_nearest_displacement(result_mesh, displacements, target_mid)

        # Stage centre displacement (mm)
        x  = mid_disp.x   # parasitic
        y  = mid_disp.y   # primary

        # Normalized deflections
        Ux = x / L
        Uy = y / L

        # Stage rotation: CCW positive (bottom moves right of top for CCW)
        phi = math.atan2(
            (bottom_disp.x - top_disp.x),
            W - (top_disp.y - bottom_disp.y),
        )

        print(f"  Stage centre: x={x:.6f} mm, y={y:.6f} mm")
        print(f"  Normalized:  Ux={Ux:.6f}, Uy={Uy:.6f}")
        print(f"  phi={phi:.9f} rad,  solver_t={solve_time:.3f} s")

        result_row = {
            "Ay": ay_val, "Ax": ax_val, "M": m_val,
            "x": x, "y": y, "Ux": Ux, "Uy": Uy,
            "phi": phi, "t": solve_time,
        }
        results.append(result_row)
        writer.writerow(result_row)
        fh.flush()

# ============================================================
# SUMMARY
# ============================================================
total_time = time.time() - start_time
setup_time = setup_complete_time - start_time

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"{'Ay':>6} {'Ax':>6} {'M':>6} {'x(mm)':>12} {'y(mm)':>12} {'Ux':>10} {'Uy':>10} {'phi':>14} {'t(s)':>8}")
for row in results:
    print(
        f"{float(row['Ay']):6.3g} {float(row['Ax']):6.3g} {float(row['M']):6.3g} "
        f"{float(row['x']):12.6f} {float(row['y']):12.6f} "
        f"{float(row['Ux']):10.6f} {float(row['Uy']):10.6f} "
        f"{float(row['phi']):14.9f} {float(row['t']):8.3f}"
    )

print(f"\nSaved: {csv_path}")
print(f"Setup: {setup_time:.2f}s,  Mesh: {mesh_time:.2f}s,  Total: {total_time:.2f}s")
print("\n=== Done ===")
