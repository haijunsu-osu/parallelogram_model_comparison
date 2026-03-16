# Parallelogram Flexure 3D FEA - Steel
# Based on parallelogram_3d_simplified.py (BooleanFragments + Slice, multi-material)
# Parameter conventions from parallelogram_t2mm_simple.py:
#   W = full beam centerline separation (mm)  [W=150 means beams at y=+75 and y=-75]
#   Ax, Ay, M = normalized loads (Fx*L^2/EI, Fy*L^2/EI, Mz*L/EI)
#   x, y = stage center displacement (mm), Ux=x/L, Uy=y/L = normalized
#
# Parameters: L=250, T=5, H=50, W=150, E=210 GPa (Steel), nu=0.3
# Stage: x from L to L+stage_len (50 mm long), quasi-rigid (E=5000 GPa)
# Moment via force couple (MomentArm=10 mm)
#
# Run: & "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" parallelogram_3d.py

import math
import time
import os
import csv
import FreeCAD as App
import Part
import ObjectsFem
import BOPTools.SplitFeatures
from FreeCAD import Units

start_time = time.time()

# ============================================================
# PARAMETERS
# ============================================================
L = 250.0          # beam length (mm)
T = 5.0            # beam thickness (mm)
H = 50.0           # out-of-plane height (mm)
W = 150.0          # full beam centerline separation (mm) — beams at y=+W/2 and y=-W/2
E_beam = 210e9     # Steel Young's modulus (Pa)
E_stage = 5000e9   # stage Young's modulus (Pa) - quasi-rigid
nu = 0.3           # Poisson's ratio (Steel)

stage_len = 50.0   # stage extends from x=L to x=L+stage_len (250 to 300)
MomentArm = 10.0   # moment arm for force couple (mm)

MeshFineCharLen = 10.0   # mesh size for beams (mm)
MeshCoarseCharLen = 10.0 # mesh size for stage (mm)

# Normalized load sweep values
AxVal = [-10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10]
AyVal = [0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20]
MVal  = [-3, -2, -1, 0, 1, 2, 3]

# Force/Moment normalization factors (SI: Pa, m, N)
I_beam = (H / 1000.0) * ((T / 1000.0) ** 3) / 12.0   # m^4  (bending about z-axis)
FNormFactor = E_beam * I_beam / ((L / 1000.0) ** 2)   # N per unit normalized force
MNormFactor = E_beam * I_beam / (L / 1000.0)          # N·m per unit normalized moment

print("=" * 60)
print("PARALLELOGRAM FLEXURE 3D FEA (Titanium)")
print("=" * 60)
print(f"Geometry: L={L}, T={T}, H={H}, W={W} mm (full separation)")
print(f"  Beam centerlines at y=+{W/2:.1f} and y=-{W/2:.1f} mm")
print(f"Stage: {stage_len} mm, MomentArm={MomentArm} mm")
print(f"Material: E_beam={E_beam/1e9:.0f} GPa (Steel), nu={nu}, E_stage={E_stage/1e9:.0f} GPa")
print(f"I = {I_beam:.6e} m^4")
print(f"FNormFactor = {FNormFactor:.4f} N")
print(f"MNormFactor = {MNormFactor:.4f} N·m")

# ============================================================
# GEOMETRY
# W = full separation; half separation = W/2
# Top beam centerline at y = +W/2  → box y from  W/2-T/2 to  W/2+T/2
# Bottom beam centerline at y = -W/2 → box y from -(W/2+T/2) to -(W/2-T/2)
# Stage spans from y = -(W/2+T/2) to y = +(W/2+T/2), width = W+T
# Z midplane: z from -H/2 to +H/2
# ============================================================
doc = App.newDocument("Parallelogram3D_Ti")

# Top beam
beam_top_shp = Part.makeBox(L, T, H, App.Vector(0, W/2.0 - T/2.0, -H/2.0))
beam_top_obj = doc.addObject("Part::Feature", "BeamTop")
beam_top_obj.Shape = beam_top_shp

# Bottom beam
beam_bot_shp = Part.makeBox(L, T, H, App.Vector(0, -(W/2.0 + T/2.0), -H/2.0))
beam_bot_obj = doc.addObject("Part::Feature", "BeamBot")
beam_bot_obj.Shape = beam_bot_shp

# Stage block: x from L to L+stage_len, y spanning both beams
stage_w = W + T   # total stage width
stage_shp = Part.makeBox(stage_len, stage_w, H,
                         App.Vector(L, -(W/2.0 + T/2.0), -H/2.0))
stage_obj = doc.addObject("Part::Feature", "Stage")
stage_obj.Shape = stage_shp
doc.recompute()

# ============================================================
# BOOLEAN FRAGMENTS - merge bodies, ensure shared mesh nodes
# ============================================================
bf = BOPTools.SplitFeatures.makeBooleanFragments(name='BooleanFragments')
bf.Objects = [beam_top_obj, beam_bot_obj, stage_obj]
bf.Mode = 'Standard'
doc.recompute()

# ============================================================
# SLICE - partition inner face at x=L for moment force couple
# Lines at z=0, y=0, y=+MomentArm, y=-MomentArm
# ============================================================
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
print(f"Slice: {n_solids} solids")
for i, s in enumerate(slice_obj.Shape.Solids):
    com = s.CenterOfMass
    print(f"  Solid{i+1}: CoM=({com.x:.1f}, {com.y:.1f}, {com.z:.1f}), Vol={s.Volume:.0f}")

# ============================================================
# HELPERS
# ============================================================
def find_faces(shape, condition):
    result = []
    for i, f in enumerate(shape.Faces):
        if condition(f.CenterOfMass):
            result.append(i + 1)
    return result

def find_nearest_vertex(shape, target):
    best_idx, best_d = None, 1e99
    for i, v in enumerate(shape.Vertexes):
        d = (v.Point - target).Length
        if d < best_d:
            best_idx = i + 1
            best_d = d
    return best_idx, best_d

# ============================================================
# FEM ANALYSIS
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

# ============================================================
# MATERIALS - beam solids (x < L) vs stage solids (x > L)
# ============================================================
beam_solid_refs = []
stage_solid_refs = []
for i, s in enumerate(slice_obj.Shape.Solids):
    solid_name = f"Solid{i + 1}"
    if s.CenterOfMass.x < L:
        beam_solid_refs.append((slice_obj, solid_name))
    else:
        stage_solid_refs.append((slice_obj, solid_name))

print(f"Beam solids: {len(beam_solid_refs)}, Stage solids: {len(stage_solid_refs)}")

mat_beam = ObjectsFem.makeMaterialSolid(doc, "TitaniumMat")
mat_beam.Material = {
    "Name": "Steel",
    "YoungsModulus": "210 GPa",
    "PoissonRatio": "0.3",
}
mat_beam.References = beam_solid_refs
analysis.addObject(mat_beam)

mat_rigid = ObjectsFem.makeMaterialSolid(doc, "RigidMat")
mat_rigid.Material = {
    "Name": "RigidStage",
    "YoungsModulus": "5000 GPa",
    "PoissonRatio": "0.3",
}
mat_rigid.References = stage_solid_refs
analysis.addObject(mat_rigid)

# ============================================================
# MESH
# ============================================================
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

print(f"Generating mesh (coarse={MeshCoarseCharLen}, fine={MeshFineCharLen})...")
mesh_start = time.time()
from femmesh import gmshtools
mesher = gmshtools.GmshTools(mesh_obj)
mesher.create_mesh()
doc.recompute()
mesh_time = time.time() - mesh_start

n_nodes = mesh_obj.FemMesh.NodeCount
n_elems = mesh_obj.FemMesh.VolumeCount
print(f"Mesh: {n_nodes} nodes, {n_elems} volume elements ({mesh_time:.1f} s)")

# ============================================================
# FIXED BC - faces at x=0
# ============================================================
fixed_face_ids = find_faces(slice_obj.Shape, lambda com: abs(com.x) < 0.5)
print(f"Fixed faces at x=0: {len(fixed_face_ids)}")
for fid in fixed_face_ids:
    f = slice_obj.Shape.Faces[fid - 1]
    print(f"  Face{fid}: CoM=({f.CenterOfMass.x:.1f}, {f.CenterOfMass.y:.1f}, {f.CenterOfMass.z:.1f}), Area={f.Area:.1f}")

fixed = ObjectsFem.makeConstraintFixed(doc, "ConstraintFixed")
fixed.References = [(slice_obj, f"Face{fid}") for fid in fixed_face_ids]
analysis.addObject(fixed)

# ============================================================
# FORCE CONSTRAINTS - Ax (Fx), Ay (Fy), and Moment Couple
# ============================================================
# Inner faces at x=L (stage left face, split by Slice)
inner_face_ids = find_faces(slice_obj.Shape, lambda com: abs(com.x - L) < 0.5)
inner_face_ids = [fid for fid in inner_face_ids
                  if abs(slice_obj.Shape.Faces[fid-1].CenterOfMass.y) < W/2.0 + T]

# Narrow moment strips between y=0 and y=±MomentArm
strip_plus_ids = []
strip_minus_ids = []
for fid in inner_face_ids:
    com_y = slice_obj.Shape.Faces[fid-1].CenterOfMass.y
    if 0.1 < com_y < MomentArm:
        strip_plus_ids.append(fid)
    elif -MomentArm < com_y < -0.1:
        strip_minus_ids.append(fid)

print(f"Moment strip+ faces (0<y<{MomentArm}mm): {strip_plus_ids}")
print(f"Moment strip- faces (-{MomentArm}<y<0mm): {strip_minus_ids}")
for fid in strip_plus_ids + strip_minus_ids:
    f = slice_obj.Shape.Faces[fid-1]
    print(f"  Face{fid}: CoM=({f.CenterOfMass.x:.1f}, {f.CenterOfMass.y:.1f}, {f.CenterOfMass.z:.1f}), Area={f.Area:.1f}")

# Fx/Fy applied at center vertex (L, 0, 0)
stage_center_pt = App.Vector(L, 0.0, 0.0)
vtx_mid_idx, vtx_dist = find_nearest_vertex(slice_obj.Shape, stage_center_pt)
print(f"Ax/Ay vertex: Vertex{vtx_mid_idx} at dist={vtx_dist:.2f}")

# Direction reference lines
dir_x = doc.addObject("Part::Line", "DirX")
dir_x.X1 = dir_x.Y1 = dir_x.Z1 = 0.0
dir_x.X2 = 100.0; dir_x.Y2 = dir_x.Z2 = 0.0

dir_y = doc.addObject("Part::Line", "DirY")
dir_y.X1 = dir_y.Y1 = dir_y.Z1 = 0.0
dir_y.Y2 = 100.0; dir_y.X2 = dir_y.Z2 = 0.0
doc.recompute()

# ForceX (Ax direction)
force_x = ObjectsFem.makeConstraintForce(doc, "ConstraintForceX")
force_x.References = [(slice_obj, f"Vertex{vtx_mid_idx}")]
force_x.Force = "0.00 N"
force_x.Direction = (dir_x, ["Edge1"])
force_x.Reversed = True
analysis.addObject(force_x)

# ForceY (Ay direction)
force_y = ObjectsFem.makeConstraintForce(doc, "ConstraintForceY")
force_y.References = [(slice_obj, f"Vertex{vtx_mid_idx}")]
force_y.Force = "0.00 N"
force_y.Direction = (dir_y, ["Edge1"])
force_y.Reversed = True
analysis.addObject(force_y)

# Moment couple: force couple on narrow strips at y = ±MomentArm
force_m_plus = ObjectsFem.makeConstraintForce(doc, "ConstraintMomentPlus")
force_m_plus.References = [(slice_obj, f"Face{fid}") for fid in strip_plus_ids]
force_m_plus.Force = "0.00 N"
force_m_plus.Reversed = False
analysis.addObject(force_m_plus)

force_m_minus = ObjectsFem.makeConstraintForce(doc, "ConstraintMomentMinus")
force_m_minus.References = [(slice_obj, f"Face{fid}") for fid in strip_minus_ids]
force_m_minus.Force = "0.00 N"
force_m_minus.Reversed = True
analysis.addObject(force_m_minus)

doc.recompute()

# ============================================================
# PROBE NODES - stage center and beam tips (outer edges)
# top probe: (L, +W/2+T/2, 0),  bot probe: (L, -W/2-T/2, 0)
# mid probe: (L, 0, 0)
# ============================================================
target_top = App.Vector(L,  W/2.0 + T/2.0, 0.0)
target_bot = App.Vector(L, -(W/2.0 + T/2.0), 0.0)
target_mid = App.Vector(L, 0.0, 0.0)

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

top_node, dist_top = find_closest_node(mesh_nodes, target_top)
bot_node, dist_bot = find_closest_node(mesh_nodes, target_bot)
mid_node, dist_mid = find_closest_node(mesh_nodes, target_mid)

p_top = mesh_nodes[top_node]
p_bot = mesh_nodes[bot_node]
p_mid = mesh_nodes[mid_node]
print(f"\nProbe Top: ({target_top.x:.1f},{target_top.y:.1f},{target_top.z:.1f}) → Node {top_node} at ({p_top.x:.1f},{p_top.y:.1f},{p_top.z:.1f}) [d={dist_top:.4f}]")
print(f"Probe Bot: ({target_bot.x:.1f},{target_bot.y:.1f},{target_bot.z:.1f}) → Node {bot_node} at ({p_bot.x:.1f},{p_bot.y:.1f},{p_bot.z:.1f}) [d={dist_bot:.4f}]")
print(f"Probe Mid: ({target_mid.x:.1f},{target_mid.y:.1f},{target_mid.z:.1f}) → Node {mid_node} at ({p_mid.x:.1f},{p_mid.y:.1f},{p_mid.z:.1f}) [d={dist_mid:.4f}]\n")

# ============================================================
# RUN SIMULATIONS
# ============================================================
results = []
save_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

for ax_val in AxVal:
    for ay_val in AyVal:
        for m_val in MVal:
            print(f"\n--- Ay={ay_val}, Ax={ax_val}, M={m_val} ---")

            # Clear previous results
            for obj in list(doc.Objects):
                if obj.Name.startswith("CCX_Results"):
                    doc.removeObject(obj.Name)
            doc.recompute()

            # Convert normalized loads to physical (SI)
            Fy_phys = ay_val * FNormFactor   # N
            Fx_phys = ax_val * FNormFactor   # N
            Mz_phys = m_val  * MNormFactor   # N·m
            # Moment couple: two forces at ±MomentArm distance
            # Torque = F * MomentArm  (matching old script convention)
            MomentForceValue = Mz_phys / (MomentArm / 1000.0) if m_val != 0 else 0.0

            force_y.Force = str(abs(Fy_phys)) + " N"
            force_y.Reversed = (Fy_phys < 0)   # False → +Y, True → -Y

            force_x.Force = str(abs(Fx_phys)) + " N"
            force_x.Reversed = (Fx_phys < 0)   # False → +X, True → -X

            force_m_plus.Force  = str(abs(MomentForceValue)) + " N"
            force_m_minus.Force = str(abs(MomentForceValue)) + " N"

            print(f"  Fy = {Fy_phys:.4f} N, Fx = {Fx_phys:.4f} N, Mz = {Mz_phys:.4f} N·m")
            if m_val != 0:
                print(f"  Moment couple: {abs(MomentForceValue):.4f} N at ±{MomentArm} mm")
            doc.recompute()

            # Run solver
            from femtools import ccxtools
            solve_start = time.time()
            fea = ccxtools.FemToolsCcx(analysis, solver)
            fea.purge_results()
            fea.update_objects()

            try:
                fea.write_inp_file()
                print(f"  INP: {fea.inp_file_name}")
                fea.run()
                solve_time = time.time() - solve_start
                fea.load_results()

                if not fea.results_present:
                    print("  ERROR: Solver failed - no results!")
                    results.append([ay_val, ax_val, m_val, 0, 0, 0, 0, 0, solve_time])
                    continue
            except Exception as e:
                import traceback
                solve_time = time.time() - solve_start
                print(f"  EXCEPTION:\n{traceback.format_exc()}")
                results.append([ay_val, ax_val, m_val, 0, 0, 0, 0, 0, solve_time])
                continue

            print(f"  Solver completed in {solve_time:.1f} s")

            # Extract result object (last time step for nonlinear)
            res_objs = [o for o in analysis.Group if o.isDerivedFrom("Fem::FemResultObject")]
            if not res_objs:
                print("  ERROR: No FemResultObject found!")
                results.append([ay_val, ax_val, m_val, 0, 0, 0, 0, 0, solve_time])
                continue

            time_res = [o for o in res_objs if "Time_" in o.Label]
            if time_res:
                def get_time(o_label):
                    try:
                        return float(o_label.replace("CCX_Time_", "").replace("_Results", "").replace("_", "."))
                    except:
                        return 0.0
                time_res.sort(key=lambda o: get_time(o.Label))
                res_obj = time_res[-1]
            else:
                res_obj = res_objs[-1]

            print(f"  Results from: {res_obj.Label}")

            disp = res_obj.DisplacementVectors
            node_numbers = res_obj.NodeNumbers
            node_idx_map = {n_id: idx for idx, n_id in enumerate(node_numbers)}

            def get_disp(n_id):
                if n_id in node_idx_map:
                    return disp[node_idx_map[n_id]]
                return disp[n_id - 1]

            top_disp = get_disp(top_node)
            bot_disp = get_disp(bot_node)
            mid_disp = get_disp(mid_node)

            top_dx = top_disp[0]; top_dy = top_disp[1]
            bot_dx = bot_disp[0]; bot_dy = bot_disp[1]
            mid_dx = mid_disp[0]; mid_dy = mid_disp[1]

            # Stage center displacement (mm)
            x = mid_dx   # parasitic (x) displacement
            y = mid_dy   # primary (y) displacement

            # Normalized deflections
            Ux = x / L
            Uy = y / L

            # Stage rotation phi: CCW positive (bot moves right of top for CCW)
            phi = math.atan2(
                (bot_dx - top_dx),
                (W + T) - (top_dy - bot_dy)
            )

            print(f"  Stage center: x={x:.4f} mm, y={y:.4f} mm")
            print(f"  Normalized:  Ux={Ux:.6f}, Uy={Uy:.6f}")
            print(f"  phi={phi:.6f} rad")

            results.append([ay_val, ax_val, m_val, x, y, Ux, Uy, phi, solve_time])

# ============================================================
# OUTPUT
# ============================================================
total_time = time.time() - start_time

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"{'Ay':>6} {'Ax':>6} {'M':>6} {'x(mm)':>12} {'y(mm)':>12} {'Ux':>10} {'Uy':>10} {'phi':>14} {'t(s)':>8}")
for r in results:
    print(f"{r[0]:6.1f} {r[1]:6.1f} {r[2]:6.1f} {r[3]:12.4f} {r[4]:12.4f} {r[5]:10.6f} {r[6]:10.6f} {r[7]:14.6f} {r[8]:8.2f}")

csv_path = save_path + "PARALLELOGRAM3D_Ti_allcases.csv"
with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Ay', 'Ax', 'M', 'x', 'y', 'Ux', 'Uy', 'phi', 't'])
    writer.writerows(results)

print(f"\nCSV saved: {csv_path}")
print(f"Nodes: {n_nodes}, Elements: {n_elems}")
print(f"Mesh: {mesh_time:.1f}s, Total: {total_time:.1f}s")
print("\n=== Done ===")
