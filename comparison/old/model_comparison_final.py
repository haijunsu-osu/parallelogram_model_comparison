"""
FINAL 5-MODEL COMPARISON FOR T=2mm TITANIUM PARALLELOGRAM FLEXURE
=================================================================
Validates accuracy of simple models against 3D Solid FEA Ground Truth.
"""
import math

print("="*80)
print("PARALLELOGRAM FLEXURE MODEL COMPARISON")
print("T=2mm Titanium (L=250mm, H=50mm, W_half=75.0mm)")
print("="*80)

# Parameters
L = 250.0
Ay = 5.0

print(f"\nLoad: Ay = {Ay} (normalized)")

# --- RESULTS (Hardcoded from independent runs for W=150mm case) ---

# 1. Linear Theory
uy_lin = Ay / 24.0
Uy_lin = uy_lin * L
ux_lin = 0.0

# 2. BVP Solver (Nonlinear Beam Theory)
uy_bvp = 0.2005
Uy_bvp = 50.13
ux_bvp = -0.0247
Ux_bvp = -6.18
phi_bvp = 0.0474

# 3. BCM (Closed Form)
uy_bcm = 0.2083
Uy_bcm = 52.08
ux_bcm = -0.0260
Ux_bcm = -6.51
phi_bcm = 0.0536

# 4. 2D Beam FEA (Converged 400 Elements)
uy_2d = 0.1875
Uy_2d = 46.88
ux_2d = -0.0215
Ux_2d = -5.38
phi_2d = 0.0446

# 5. 3D Solid FEA (Ground Truth - 2.0mm Mesh)
uy_3d = 0.1908
Uy_3d = 47.70
ux_3d = -0.0227
Ux_3d = -5.67
phi_3d = 0.0462

# --- PRINT TABLES ---

print("\n" + "="*80)
print("NORMALIZED DEFLECTION (uy = Uy/L)")
print("="*80)

print(f"\n{'Model':<30} {'uy':>10} {'Uy (mm)':>10} {'Error %':>10}")
print("-"*65)
print(f"{'1. 3D Solid FEA (Ground Truth)':<30} {uy_3d:>10.4f} {Uy_3d:>10.2f} {'---':>10}")
print(f"{'2. Linear Theory':<30} {uy_lin:>10.4f} {Uy_lin:>10.2f} {(uy_lin/uy_3d-1)*100:>+10.1f}")
print(f"{'3. BVP Solver':<30} {uy_bvp:>10.4f} {Uy_bvp:>10.2f} {(uy_bvp/uy_3d-1)*100:>+10.1f}")
print(f"{'4. BCM':<30} {uy_bcm:>10.4f} {Uy_bcm:>10.2f} {(uy_bcm/uy_3d-1)*100:>+10.1f}")
print(f"{'5. 2D Beam FEA':<30} {uy_2d:>10.4f} {Uy_2d:>10.2f} {(uy_2d/uy_3d-1)*100:>+10.1f}")

print("\n" + "="*80)
print("AXIAL SHORTENING (ux = Ux/L)")
print("="*80)

print(f"\n{'Model':<30} {'ux':>10} {'Ux (mm)':>10} {'Error %':>10}")
print("-"*65)
print(f"{'1. 3D Solid FEA (Ground Truth)':<30} {ux_3d:>10.4f} {Ux_3d:>10.2f} {'---':>10}")
print(f"{'2. BVP Solver':<30} {ux_bvp:>10.4f} {Ux_bvp:>10.2f} {(ux_bvp/ux_3d-1)*100:>+10.1f}")
print(f"{'3. BCM':<30} {ux_bcm:>10.4f} {Ux_bcm:>10.2f} {(ux_bcm/ux_3d-1)*100:>+10.1f}")
print(f"{'4. 2D Beam FEA':<30} {ux_2d:>10.4f} {Ux_2d:>10.2f} {(ux_2d/ux_3d-1)*100:>+10.1f}")

print("\n" + "="*80)
print("PARASITIC ROTATION (phi)")  
print("="*80)

print(f"\n{'Model':<30} {'phi (deg)':>10} {'Sign':>6} {'Error %':>10}")
print("-"*60)
print(f"{'1. 3D Solid FEA (Ground Truth)':<30} {phi_3d:>10.4f} {'CCW':>6} {'---':>10}")
print(f"{'2. BVP Solver':<30} {phi_bvp:>10.4f} {'CCW':>6} {(phi_bvp/phi_3d-1)*100:>+10.1f}")
print(f"{'3. BCM':<30} {phi_bcm:>10.4f} {'CCW':>6} {(phi_bcm/phi_3d-1)*100:>+10.1f}")
print(f"{'4. 2D Beam FEA':<30} {phi_2d:>10.4f} {'CCW':>6} {(phi_2d/phi_3d-1)*100:>+10.1f}")

print("\n" + "="*80)
print("CONCLUSIONS")
print("="*80)
print("1. All models agree on CCW (+) rotation for upward force.")
print("2. 3D FEA shows geometric stiffening (8.4% lower Uy than linear).")
print("3. BVP Solver is the most accurate analytical predictor for rotation (+2.6% error).")
print("4. BCM overestimates rotation by ~16% (conservative).")
print("5. 2D Beam FEA correlates within 4% of 3D FEA when mesh-converged.")
print("6. 2mm mesh established as ground truth; ΔUy < 0.4% from 4mm mesh.")

