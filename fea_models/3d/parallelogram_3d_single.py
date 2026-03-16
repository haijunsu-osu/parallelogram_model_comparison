# Single-case test of parallelogram_3d.py
# Case: Ax=0, Ay=5, M=0  (Steel, T=5mm, W=150mm full separation)
# Run: & "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" parallelogram_3d_single.py

import math
import time
import os
import FreeCAD as App
import Part
import ObjectsFem
import BOPTools.SplitFeatures

start_time = time.time()

# ============================================================
# PARAMETERS
# ============================================================
L = 250.0
T = 5.0
H = 50.0
W = 150.0          # full centerline separation; beams at y = ±W/2 = ±75 mm
E_beam = 210e9     # Steel (Pa)
E_stage = 5000e9   # quasi-rigid stage (Pa)
nu = 0.3

stage_len = 50.0
MomentArm = 10.0
MeshFineCharLen = float(os.environ.get("FEA_MESH_FINE_CHAR_LEN", "10.0"))
MeshCoarseCharLen = float(os.environ.get("FEA_MESH_COARSE_CHAR_LEN", "10.0"))

# Single test case
Ax = float(os.environ.get("FEA_AX", "0.0"))
Ay = float(os.environ.get("FEA_AY", "5.0"))
M  = float(os.environ.get("FEA_M", "0.0"))

I_beam = (H / 1000.0) * ((T / 1000.0) ** 3) / 12.0
FNormFactor = E_beam * I_beam / ((L / 1000.0) ** 2)
MNormFactor = E_beam * I_beam / (L / 1000.0)

print("=" * 60)
print("SINGLE CASE TEST  (new script - Steel, T=5, W=150 full)")
print("=" * 60)
print(f"L={L}, T={T}, H={H}, W={W} mm  →  beams at y=±{W/2:.0f}")
print(f"E_beam={E_beam/1e9:.0f} GPa (Steel), nu={nu}")
print(f"I = {I_beam:.4e} m^4")
print(f"FNormFactor = {FNormFactor:.6f} N,  MNormFactor = {MNormFactor:.6f} N·m")
print(f"Test case: Ax={Ax}, Ay={Ay}, M={M}")
print(f"  → Fx={Ax*FNormFactor:.4f} N, Fy={Ay*FNormFactor:.4f} N, Mz={M*MNormFactor:.4f} N·m")

# ============================================================
# GEOMETRY
# ============================================================
doc = App.newDocument("SingleTest_Ti")

beam_top_shp = Part.makeBox(L, T, H, App.Vector(0,  W/2.0 - T/2.0, -H/2.0))
beam_top_obj = doc.addObject("Part::Feature", "BeamTop")
beam_top_obj.Shape = beam_top_shp

beam_bot_shp = Part.makeBox(L, T, H, App.Vector(0, -(W/2.0 + T/2.0), -H/2.0))
beam_bot_obj = doc.addObject("Part::Feature", "BeamBot")
beam_bot_obj.Shape = beam_bot_shp

stage_w = W + T
stage_shp = Part.makeBox(stage_len, stage_w, H,
                         App.Vector(L, -(W/2.0 + T/2.0), -H/2.0))
stage_obj = doc.addObject("Part::Feature", "Stage")
stage_obj.Shape = stage_shp
doc.recompute()

bf = BOPTools.SplitFeatures.makeBooleanFragments(name='BooleanFragments')
bf.Objects = [beam_top_obj, beam_bot_obj, stage_obj]
bf.Mode = 'Standard'
doc.recompute()

line_z0 = Part.makeLine(App.Vector(L, -(W/2.0 + T), 0.0),
                        App.Vector(L,  (W/2.0 + T), 0.0))
line_z0_obj = doc.addObject("Part::Feature", "LineZ0")
line_z0_obj.Shape = line_z0

line_y0 = Part.makeLine(App.Vector(L, 0.0, -H), App.Vector(L, 0.0, H))
line_y0_obj = doc.addObject("Part::Feature", "LineY0")
line_y0_obj.Shape = line_y0

line_yp = Part.makeLine(App.Vector(L,  MomentArm, -H), App.Vector(L,  MomentArm, H))
line_yp_obj = doc.addObject("Part::Feature", "LineYP")
line_yp_obj.Shape = line_yp

line_ym = Part.makeLine(App.Vector(L, -MomentArm, -H), App.Vector(L, -MomentArm, H))
line_ym_obj = doc.addObject("Part::Feature", "LineYM")
line_ym_obj.Shape = line_ym
doc.recompute()

slice_obj = BOPTools.SplitFeatures.makeSlice(name='Slice')
slice_obj.Base = bf
slice_obj.Tools = [line_z0_obj, line_y0_obj, line_yp_obj, line_ym_obj]
slice_obj.Mode = 'Split'
doc.recompute()

n_solids = len(slice_obj.Shape.Solids)
print(f"Solids after Slice: {n_solids}")

# ============================================================
# FEM SETUP
# ============================================================
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")

solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
solver.GeometricalNonlinearity = "nonlinear"
solver.IterationsMaximum = 2000
solver.TimeInitialStep = 1.0
solver.TimeEnd = 1.0
solver.TimeMinimumStep = 1e-05
solver.TimeMaximumStep = 1.0
analysis.addObject(solver)

beam_solid_refs  = [(slice_obj, f"Solid{i+1}") for i, s in enumerate(slice_obj.Shape.Solids) if s.CenterOfMass.x < L]
stage_solid_refs = [(slice_obj, f"Solid{i+1}") for i, s in enumerate(slice_obj.Shape.Solids) if s.CenterOfMass.x >= L]
print(f"Beam solids: {len(beam_solid_refs)},  Stage solids: {len(stage_solid_refs)}")

mat_beam = ObjectsFem.makeMaterialSolid(doc, "TitaniumMat")
mat_beam.Material = {"Name": "Steel", "YoungsModulus": "210 GPa", "PoissonRatio": "0.3"}
mat_beam.References = beam_solid_refs
analysis.addObject(mat_beam)

mat_rigid = ObjectsFem.makeMaterialSolid(doc, "RigidMat")
mat_rigid.Material = {"Name": "RigidStage", "YoungsModulus": "5000 GPa", "PoissonRatio": "0.3"}
mat_rigid.References = stage_solid_refs
analysis.addObject(mat_rigid)

mesh_obj = ObjectsFem.makeMeshGmsh(doc, "FEMMeshGmsh")
mesh_obj.Shape = slice_obj
mesh_obj.CharacteristicLengthMax = MeshCoarseCharLen
mesh_obj.ElementOrder = "2nd"
mesh_obj.SecondOrderLinear = False
analysis.addObject(mesh_obj)

mesh_region = ObjectsFem.makeMeshRegion(doc, mesh_obj)
mesh_region.CharacteristicLength = MeshFineCharLen
mesh_region.References = beam_solid_refs
doc.recompute()

print(f"Meshing...")
mesh_start = time.time()
from femmesh import gmshtools
mesher = gmshtools.GmshTools(mesh_obj)
mesher.create_mesh()
doc.recompute()
mesh_time = time.time() - mesh_start
n_nodes = mesh_obj.FemMesh.NodeCount
n_elems = mesh_obj.FemMesh.VolumeCount
print(f"Mesh: {n_nodes} nodes, {n_elems} elements  ({mesh_time:.1f} s)")

# Fixed BC
fixed_ids = [i+1 for i, f in enumerate(slice_obj.Shape.Faces) if abs(f.CenterOfMass.x) < 0.5]
print(f"Fixed faces at x=0: {len(fixed_ids)}")
fixed = ObjectsFem.makeConstraintFixed(doc, "ConstraintFixed")
fixed.References = [(slice_obj, f"Face{fid}") for fid in fixed_ids]
analysis.addObject(fixed)

# Inner faces at x=L for moment couple
inner_ids = [i+1 for i, f in enumerate(slice_obj.Shape.Faces)
             if abs(f.CenterOfMass.x - L) < 0.5
             and abs(f.CenterOfMass.y) < W/2.0 + T]
strip_plus_ids  = [fid for fid in inner_ids if  0.1 < slice_obj.Shape.Faces[fid-1].CenterOfMass.y < MomentArm]
strip_minus_ids = [fid for fid in inner_ids if -MomentArm < slice_obj.Shape.Faces[fid-1].CenterOfMass.y < -0.1]
print(f"Moment strips: +{strip_plus_ids}  -{strip_minus_ids}")

# Vertex at (L, 0, 0) for Fx/Fy
vtx_mid_idx = min(range(1, len(slice_obj.Shape.Vertexes)+1),
                  key=lambda i: (slice_obj.Shape.Vertexes[i-1].Point - App.Vector(L, 0, 0)).Length)

dir_x = doc.addObject("Part::Line", "DirX")
dir_x.X1 = dir_x.Y1 = dir_x.Z1 = 0.0; dir_x.X2 = 100.0; dir_x.Y2 = dir_x.Z2 = 0.0
dir_y = doc.addObject("Part::Line", "DirY")
dir_y.X1 = dir_y.Y1 = dir_y.Z1 = 0.0; dir_y.Y2 = 100.0; dir_y.X2 = dir_y.Z2 = 0.0
doc.recompute()

Fy_phys = Ay * FNormFactor
Fx_phys = Ax * FNormFactor
Mz_phys = M  * MNormFactor
MomentForceValue = Mz_phys / (MomentArm / 1000.0) if M != 0 else 0.0

force_x = ObjectsFem.makeConstraintForce(doc, "ConstraintForceX")
force_x.References = [(slice_obj, f"Vertex{vtx_mid_idx}")]
force_x.Force = str(abs(Fx_phys)) + " N"
force_x.Direction = (dir_x, ["Edge1"])
force_x.Reversed = (Fx_phys < 0)
analysis.addObject(force_x)

force_y = ObjectsFem.makeConstraintForce(doc, "ConstraintForceY")
force_y.References = [(slice_obj, f"Vertex{vtx_mid_idx}")]
force_y.Force = str(abs(Fy_phys)) + " N"
force_y.Direction = (dir_y, ["Edge1"])
force_y.Reversed = (Fy_phys < 0)
analysis.addObject(force_y)

force_m_plus = ObjectsFem.makeConstraintForce(doc, "ConstraintMomentPlus")
force_m_plus.References = [(slice_obj, f"Face{fid}") for fid in strip_plus_ids]
force_m_plus.Force = str(abs(MomentForceValue)) + " N"
force_m_plus.Reversed = False
analysis.addObject(force_m_plus)

force_m_minus = ObjectsFem.makeConstraintForce(doc, "ConstraintMomentMinus")
force_m_minus.References = [(slice_obj, f"Face{fid}") for fid in strip_minus_ids]
force_m_minus.Force = str(abs(MomentForceValue)) + " N"
force_m_minus.Reversed = True
analysis.addObject(force_m_minus)
doc.recompute()

# ============================================================
# PROBE NODES
# ============================================================
fem_mesh = mesh_obj.FemMesh
mesh_nodes = fem_mesh.Nodes

def find_closest_node(nodes_dict, target_pt):
    best_nid, best_d = None, 1e99
    for nid, pos in nodes_dict.items():
        d = (pos - target_pt).Length
        if d < best_d:
            best_d = d
            best_nid = nid
    return best_nid, best_d

target_top = App.Vector(L,  W/2.0 + T/2.0, 0.0)
target_bot = App.Vector(L, -(W/2.0 + T/2.0), 0.0)
target_mid = App.Vector(L, 0.0, 0.0)

top_node, _ = find_closest_node(mesh_nodes, target_top)
bot_node, _ = find_closest_node(mesh_nodes, target_bot)
mid_node, _ = find_closest_node(mesh_nodes, target_mid)

p_top = mesh_nodes[top_node]
p_bot = mesh_nodes[bot_node]
p_mid = mesh_nodes[mid_node]
print(f"Probe top: ({p_top.x:.1f}, {p_top.y:.1f}, {p_top.z:.1f})")
print(f"Probe bot: ({p_bot.x:.1f}, {p_bot.y:.1f}, {p_bot.z:.1f})")
print(f"Probe mid: ({p_mid.x:.1f}, {p_mid.y:.1f}, {p_mid.z:.1f})")

# ============================================================
# SOLVE
# ============================================================
from femtools import ccxtools
print("\nRunning CalculiX...")
solve_start = time.time()
fea = ccxtools.FemToolsCcx(analysis, solver)
fea.purge_results()
fea.update_objects()
fea.write_inp_file()
fea.run()
solve_time = time.time() - solve_start
fea.load_results()

if not fea.results_present:
    print("ERROR: Solver failed!")
    import sys; sys.exit(1)

print(f"Solved in {solve_time:.1f} s")

res_objs = [o for o in analysis.Group if o.isDerivedFrom("Fem::FemResultObject")]
time_res = [o for o in res_objs if "Time_" in o.Label]
if time_res:
    def get_t(lbl):
        try: return float(lbl.replace("CCX_Time_","").replace("_Results","").replace("_","."))
        except: return 0.0
    time_res.sort(key=lambda o: get_t(o.Label))
    res_obj = time_res[-1]
else:
    res_obj = res_objs[-1]

disp = res_obj.DisplacementVectors
node_numbers = res_obj.NodeNumbers
node_idx_map = {n: i for i, n in enumerate(node_numbers)}

def get_disp(n_id):
    return disp[node_idx_map[n_id]] if n_id in node_idx_map else disp[n_id-1]

top_d = get_disp(top_node)
bot_d = get_disp(bot_node)
mid_d = get_disp(mid_node)

x   = mid_d[0]           # parasitic x displacement (mm)
y   = mid_d[1]           # primary y displacement (mm)
Ux  = x / L              # normalized
Uy  = y / L              # normalized
phi = math.atan2((bot_d[0] - top_d[0]), (W + T) - (top_d[1] - bot_d[1]))  # CCW positive

total_time = time.time() - start_time

print("\n" + "=" * 60)
print("RESULTS  (new script: Steel T=5 W=150full)")
print("=" * 60)
print(f"Normalized load:  Ax={Ax},  Ay={Ay},  M={M}")
print(f"Physical forces:  Fx={Fx_phys:.4f} N,  Fy={Fy_phys:.4f} N,  Mz={Mz_phys:.4f} N·m")
print(f"Stage center displacement:")
print(f"  x  = {x:.4f} mm   (parasitic)")
print(f"  y  = {y:.4f} mm   (primary)")
print(f"  Ux = x/L = {Ux:.6f}")
print(f"  Uy = y/L = {Uy:.6f}")
print(f"  phi = {phi:.6f} rad  ({math.degrees(phi):.4f} deg)")
print(f"BCM linear estimate:  Uy = Ay/24 = {Ay/24:.6f}")
print(f"Mesh: {n_nodes} nodes, {n_elems} elements")
print(f"Times: mesh={mesh_time:.1f}s  solve={solve_time:.1f}s  total={total_time:.1f}s")
print("=== Done ===")
