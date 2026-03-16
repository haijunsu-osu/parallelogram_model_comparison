"""
Comprehensive Model Comparison: T=5mm, Titanium, Ay=5

Compares all 4 models:
1. 2D Beam FEA (FreeCAD/CalculiX)
2. 3D Solid FEA (FreeCAD/CalculiX)
3. BVP Nonlinear Beam Solver
4. BCM Closed-Form (Eq 3.19)
"""

import numpy as np
from parallelogram_solver import ParallelogramFlexureSolver
from bcm_parallelogram import BCMParallelogram

# ============================================================
# PARAMETERS - T=5mm, Titanium, Ay=5
# ============================================================
L = 250.0       # mm
T = 5.0         # mm
H = 50.0        # mm
W = 37.5        # mm (half separation)

E = 114000.0    # MPa (Titanium)
Ay = 5.0
Ax = 0.0
B = 0.0

w = W / L       # = 0.15
t = T / L       # = 0.02

print("=" * 70)
print("MODEL COMPARISON: T=5mm, Titanium, Ay=5")
print("=" * 70)
print(f"Geometry: L={L}mm, T={T}mm, H={H}mm, W={W}mm (2W={2*W}mm)")
print(f"Normalized: w=W/L={w:.3f}, t=T/L={t:.3f}")
print(f"Material: E={E} MPa (Titanium)")
print(f"Load: Ay={Ay}")
print()

# ============================================================
# BCM Closed-Form
# ============================================================
bcm = BCMParallelogram(w=w, t=t)
bcm_result = bcm.solve(Ax, Ay, B)
uy_bcm = bcm_result['delta']
ux_bcm = -bcm_result['u1']
phi_bcm = bcm_result['phi']

# ============================================================
# BVP Solver
# ============================================================
bvp_solver = ParallelogramFlexureSolver(w=w)
bvp_success = bvp_solver.solve(Ax, Ay, B)

if bvp_success:
    bvp_results = bvp_solver.get_results_summary()
    uy_bvp = bvp_results['platform']['Y_p']
    
    # Beam 1 at y = +W (top), Beam 2 at y = -W (bottom)
    x1_tip = bvp_results['beam1']['x_tip']
    x2_tip = bvp_results['beam2']['x_tip']
    Ux_top_bvp = x1_tip - 1.0
    Ux_bot_bvp = x2_tip - 1.0
    ux_bvp = (x1_tip + x2_tip)/2 - 1.0
    
    # Use same formula as FEA: phi = (Ux_bot - Ux_top) / (2w)
    phi_bvp = (Ux_bot_bvp - Ux_top_bvp) / (2 * w)
else:
    uy_bvp = ux_bvp = phi_bvp = None

# ============================================================
# FEA Results (from previous runs with T=5mm)
# ============================================================
# 2D Beam FEA
fea_2d = {
    'name': '2D Beam FEA',
    'uy': 0.190620,
    'ux': -0.022316,
    'phi': 4.850267e-3,
}

# 3D Solid FEA (refined mesh: 2mm elements, quadratic)
fea_3d = {
    'name': '3D Solid FEA',
    'uy': 0.205727,  # Now matches BCM well!
    'ux': -0.025481,
    'phi': 6.507733e-3,
}

# BVP
bvp = {
    'name': 'BVP Solver',
    'uy': uy_bvp,
    'ux': ux_bvp,
    'phi': phi_bvp,
}

# BCM
bcm_data = {
    'name': 'BCM (Eq 3.19)',
    'uy': uy_bcm,
    'ux': ux_bcm,
    'phi': phi_bcm,
}

# ============================================================
# Print Comparison Table
# ============================================================
print("-" * 70)
header = f"{'Model':<20} {'uy':>10} {'ux':>10} {'phi_rad':>12} {'phi_deg':>10} {'Sign':>8}"
print(header)
print("-" * 70)

def sign_str(phi):
    if phi is None:
        return "N/A"
    return "CCW (+)" if phi > 0 else "CW (-)"

def fmt_val(v, width=10, precision=6):
    if v is None:
        return "N/A".center(width)
    return f"{v:>{width}.{precision}f}"

def fmt_phi(v, width=12):
    if v is None:
        return "N/A".center(width)
    return f"{v:>{width}.4e}"

models = [fea_2d, fea_3d, bvp, bcm_data]

for m in models:
    name = m['name']
    uy = m['uy']
    ux = m['ux']
    phi = m['phi']
    
    uy_s = fmt_val(uy)
    ux_s = fmt_val(ux)
    phi_rad_s = fmt_phi(phi)
    phi_deg_s = f"{np.degrees(phi):>10.4f}" if phi is not None else "N/A".center(10)
    sign_s = sign_str(phi)
    
    print(f"{name:<20} {uy_s} {ux_s} {phi_rad_s} {phi_deg_s} {sign_s:>8}")

print("-" * 70)

# ============================================================
# Sign Agreement Matrix
# ============================================================
print()
print("SIGN AGREEMENT MATRIX")
print("-" * 40)

model_names = ['2D Beam', '3D Solid', 'BVP', 'BCM']
phis = [fea_2d['phi'], fea_3d['phi'], phi_bvp, phi_bcm]

for i, (m1, p1) in enumerate(zip(model_names, phis)):
    for j, (m2, p2) in enumerate(zip(model_names, phis)):
        if i < j and p1 is not None and p2 is not None:
            if (p1 > 0) == (p2 > 0):
                print(f"  {m1} vs {m2}: MATCH (both {'CCW' if p1 > 0 else 'CW'})")
            else:
                print(f"  {m1} vs {m2}: DIFFER ({'+' if p1 > 0 else '-'} vs {'+' if p2 > 0 else '-'})")

# ============================================================
# Summary
# ============================================================
# ============================================================
# Summary
# ============================================================
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

# 3D Solid FEA is the Ground Truth
p_ref = fea_3d['phi']
print(f"Ground Truth (3D Solid FEA): phi = {p_ref:.4e} rad = {np.degrees(p_ref):.3f} deg ({sign_str(p_ref)})")
print()

print("Agreement with Ground Truth sign:")
for m in [fea_2d, bvp, bcm_data]:
    if m['phi'] is not None:
        agrees = (m['phi'] > 0) == (p_ref > 0)
        status = "AGREES ✓" if agrees else "DIFFERS ✗"
        print(f"  {m['name']}: {status}")
    else:
        print(f"  {m['name']}: N/A")

print()
print("=" * 70)
