"""
Compare BVP Solver and BCM with FEA Results
"""
import numpy as np
from parallelogram_solver import ParallelogramFlexureSolver
from bcm_parallelogram import BCMParallelogram

# Parameters matching FreeCAD model
L = 250.0  # mm
T = 5.0    # mm
H = 50.0   # mm
W = 75.0   # mm

w = W / L  # Normalized beam separation = 0.3
t = T / L  # Normalized thickness = 0.02

# Load case
Ay = 5.0
Ax = 0.0
B = 0.0

print("=" * 60)
print("MODEL COMPARISON: BVP vs BCM vs FEA")
print("=" * 60)
print(f"\nGeometry: L={L} mm, T={T} mm, H={H} mm, W={W} mm")
print(f"Normalized: w = {w}, t = {t}")
print(f"Load: Ay = {Ay}, Ax = {Ax}, B = {B}")

# ===================
# 1. BVP (Nonlinear) Solver
# ===================
print("\n" + "-" * 40)
print("1. BVP (Nonlinear) Solver")
print("-" * 40)

solver = ParallelogramFlexureSolver(w=w)
success = solver.solve(Ax, Ay, B)

if success:
    results = solver.get_results_summary()
    
    # Extract from structured result
    uy_bvp = results['platform']['Y_p']  # Normalized Y displacement
    phi_bvp = results['platform']['phi_rad']
    ux_bvp = results['platform']['X_p'] - 1.0  # X_p is final position, subtract initial
    
    # Get beam tip info
    x1_tip = results['beam1']['x_tip']
    x2_tip = results['beam2']['x_tip']
    
    print(f"  Platform Y_p (uy) = {uy_bvp:.6e}")
    print(f"  Platform X_p = {results['platform']['X_p']:.6e}")
    print(f"  ux = X_p - 1 = {ux_bvp:.6e}")
    print(f"  phi = {phi_bvp:.6e} rad = {np.degrees(phi_bvp):.6f} deg")
    print(f"  Beam1 x_tip = {x1_tip:.6e}")
    print(f"  Beam2 x_tip = {x2_tip:.6e}")
    
    if phi_bvp > 0:
        print("  → phi > 0: POSITIVE (CCW rotation)")
    else:
        print("  → phi < 0: NEGATIVE (CW rotation)")
else:
    print("  FAILED TO CONVERGE")
    uy_bvp = ux_bvp = phi_bvp = float('nan')

# ===================
# 2. BCM (Closed-Form)
# ===================
print("\n" + "-" * 40)
print("2. BCM (Closed-Form, Eq 3.19)")
print("-" * 40)

bcm = BCMParallelogram(w=w, t=t)
bcm_result = bcm.solve(Ax, Ay, B)

uy_bcm = bcm_result['delta']
phi_bcm = bcm_result['phi']
ux_bcm = -bcm_result['u1']  # Already averaged

print(f"  uy (delta) = {uy_bcm:.6e}")
print(f"  ux = {ux_bcm:.6e}")
print(f"  phi = {phi_bcm:.6e} rad = {np.degrees(phi_bcm):.6f} deg")

if phi_bcm > 0:
    print("  → phi > 0: POSITIVE (CCW rotation)")
else:
    print("  → phi < 0: NEGATIVE (CW rotation)")

# ===================
# 3. FEA Results (from user's run)
# ===================
print("\n" + "-" * 40)
print("3. FEA Results (FreeCAD CalculiX)")
print("-" * 40)

# From user's FEA output
uy_fea = 1.233920e-01
ux_fea = -9.041400e-03
phi_fea = -3.181867e-03  # rad

print(f"  uy = {uy_fea:.6e}")
print(f"  ux = {ux_fea:.6e}")
print(f"  phi = {phi_fea:.6e} rad = {np.degrees(phi_fea):.6f} deg")

if phi_fea > 0:
    print("  → phi > 0: POSITIVE (CCW rotation)")
else:
    print("  → phi < 0: NEGATIVE (CW rotation)")

# ===================
# Comparison Table
# ===================
print("\n" + "=" * 60)
print("COMPARISON SUMMARY")
print("=" * 60)
print(f"\n{'Model':<15} {'uy':>12} {'ux':>12} {'phi (deg)':>12} {'phi sign':>10}")
print("-" * 60)
print(f"{'FEA':15} {uy_fea:>12.6f} {ux_fea:>12.6f} {np.degrees(phi_fea):>12.6f} {'CW (-)':>10}")
print(f"{'BVP':15} {uy_bvp:>12.6f} {ux_bvp:>12.6f} {np.degrees(phi_bvp):>12.6f} {'CCW (+)' if phi_bvp > 0 else 'CW (-)':>10}")
print(f"{'BCM':15} {uy_bcm:>12.6f} {ux_bcm:>12.6f} {np.degrees(phi_bcm):>12.6f} {'CCW (+)' if phi_bcm > 0 else 'CW (-)':>10}")

print("\n" + "-" * 60)
print("KEY FINDING:")
if (phi_fea < 0 and phi_bvp < 0) or (phi_fea > 0 and phi_bvp > 0):
    print("  ✓ BVP agrees with FEA on phi sign!")
else:
    print("  ✗ BVP DISAGREES with FEA on phi sign!")

if (phi_fea < 0 and phi_bcm < 0) or (phi_fea > 0 and phi_bcm > 0):
    print("  ✓ BCM agrees with FEA on phi sign!")
else:
    print("  ✗ BCM DISAGREES with FEA on phi sign!")
print()
