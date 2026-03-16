"""
5-MODEL COMPARISON FOR PARALLELOGRAM FLEXURE
============================================

This script summarizes results from all models for the parallelogram flexure mechanism.

Models:
1. BVP Solver (Euler-Bernoulli beam theory, normalized)
2. BCM (Beam Constraint Model, closed-form)  
3. 2D Beam FEA (Timoshenko beam elements, nonlinear)
4. 3D Solid FEA (Continuum elements, linear/nonlinear)
5. Linear Theory (baseline)
"""

import math

print("="*80)
print("PARALLELOGRAM FLEXURE - 5-MODEL COMPARISON")
print("="*80)

# Geometry (common)
L = 250.0  # mm
H = 50.0   # mm
W_half = 37.5  # mm (BVP/BCM convention)
W_full = 75.0  # mm (3D FEA convention)
Ay = 5.0  # Normalized force

print(f"\nGeometry: L={L}mm, H={H}mm, W_half={W_half}mm (W_full={W_full}mm)")
print(f"Normalized load: Ay = {Ay}")

# ===== T = 5mm CASE (Steel, E=210000 MPa) =====
print("\n" + "="*80)
print("T = 5mm CASE (Steel, E=210000 MPa, nu=0.30)")
print("="*80)

T = 5.0
E_steel = 210000.0
I_beam = H * T**3 / 12.0
F_y = Ay * E_steel * I_beam / L**2
w_n = W_half / L  # = 0.15
t_n = T / L       # = 0.02

print(f"I_beam = {I_beam:.2f} mm^4, Fy = {F_y:.2f} N")

# Linear theory
uy_linear = Ay / 24.0
Uy_linear_mm = uy_linear * L
print(f"\n1. Linear Theory: uy = {uy_linear:.6f}, Uy = {Uy_linear_mm:.2f} mm")

# BVP (from solver)
# BVP gives same normalized result regardless of T (pure EB)
uy_bvp = 0.2029  # from solver output
phi_bvp_deg = 0.1932
print(f"2. BVP Solver:    uy = {uy_bvp:.6f}, phi = {phi_bvp_deg:.4f} deg")

# BCM
uy_bcm = Ay / 24.0
phi_bcm = 0.5/(w_n**2) * ((t_n**2/12) + (uy_bcm**2/700)) * (uy_bcm * 12)
phi_bcm_deg = math.degrees(phi_bcm)
print(f"3. BCM:           uy = {uy_bcm:.6f}, phi = {phi_bcm_deg:.4f} deg")

# 2D Beam FEA (from parallelogram_2d_nonlinear.py)
uy_2dfea_mm = 47.655 / L
phi_2dfea_deg = 0.278
print(f"4. 2D Beam FEA:   uy = {uy_2dfea_mm:.6f}, phi = {phi_2dfea_deg:.4f} deg")

# 3D Solid FEA (from t5mm run)
Uy_3dfea_mm = 30.848
uy_3dfea = Uy_3dfea_mm / L
Ux_top_3d = -2.374
Ux_bot_3d = -2.135
phi_3dfea = (Ux_top_3d - Ux_bot_3d) / W_full
phi_3dfea_deg = math.degrees(phi_3dfea)
print(f"5. 3D Solid FEA:  uy = {uy_3dfea:.6f}, phi = {phi_3dfea_deg:.4f} deg (Uy={Uy_3dfea_mm:.2f}mm)")

print("\nNormalized uy comparison:")
print(f"  Linear:  {uy_linear:.6f} (baseline)")
print(f"  BVP:     {uy_bvp:.6f} ({(uy_bvp-uy_linear)/uy_linear*100:+.1f}%)")
print(f"  BCM:     {uy_bcm:.6f} (same as linear)")
print(f"  2D FEA:  {uy_2dfea_mm:.6f} ({(uy_2dfea_mm-uy_linear)/uy_linear*100:+.1f}%)")
print(f"  3D FEA:  {uy_3dfea:.6f} ({(uy_3dfea-uy_linear)/uy_linear*100:+.1f}%)")

print("\nParasitic rotation phi comparison:")
print(f"  BVP:     {phi_bvp_deg:.4f} deg")
print(f"  BCM:     {phi_bcm_deg:.4f} deg")
print(f"  2D FEA:  {phi_2dfea_deg:.4f} deg")
print(f"  3D FEA:  {phi_3dfea_deg:.4f} deg")

# ===== T = 2mm CASE (Titanium, E=114000 MPa) =====
print("\n" + "="*80)
print("T = 2mm CASE (Titanium, E=114000 MPa, nu=0.34)")
print("="*80)

T = 2.0
E_ti = 114000.0
I_beam = H * T**3 / 12.0
F_y = Ay * E_ti * I_beam / L**2
t_n = T / L  # = 0.008

print(f"I_beam = {I_beam:.2f} mm^4, Fy = {F_y:.2f} N")

# Linear theory (same normalized value)
print(f"\n1. Linear Theory: uy = {uy_linear:.6f}, Uy = {Uy_linear_mm:.2f} mm")

# BVP (same as T=5mm - pure EB, normalized)
print(f"2. BVP Solver:    uy = {uy_bvp:.6f}, phi = {phi_bvp_deg:.4f} deg")

# BCM (different t_n)
phi_bcm_t2 = 0.5/(w_n**2) * ((t_n**2/12) + (uy_bcm**2/700)) * (uy_bcm * 12)
phi_bcm_t2_deg = math.degrees(phi_bcm_t2)
print(f"3. BCM:           uy = {uy_bcm:.6f}, phi = {phi_bcm_t2_deg:.4f} deg")

# 2D Beam FEA (from parallelogram_2d_slender.py)
Uy_2d_t2 = 46.326
uy_2dfea_t2 = Uy_2d_t2 / L
phi_2dfea_t2 = 0.1729
print(f"4. 2D Beam FEA:   uy = {uy_2dfea_t2:.6f}, phi = {phi_2dfea_t2:.4f} deg")

# 3D Solid FEA (from t2mm run - note: this used E=114 GPa)
Uy_3d_t2 = 6.93  # mm (very low - something wrong)
uy_3dfea_t2 = Uy_3d_t2 / L
print(f"5. 3D Solid FEA:  uy = {uy_3dfea_t2:.6f} (Uy={Uy_3d_t2:.2f}mm) - CHECK SETUP!")

print("\n" + "="*80)
print("OBSERVATIONS")
print("="*80)
print("""
1. BVP gives identical results for T=5mm and T=2mm because it uses 
   fully normalized Euler-Bernoulli equations where T doesn't appear.

2. BCM shows smaller phi for T=2mm (0.214 deg) than T=5mm (0.303 deg)
   because the term t_n^2/12 in the phi formula scales with thickness.

3. 2D Beam FEA (Timoshenko) shows:
   - T=5mm: phi = 0.278 deg (between BVP and BCM)
   - T=2mm: phi = 0.173 deg (below BVP, expected for slender beam)

4. 3D Solid FEA for T=5mm gives uy = 0.123 (about 60% of linear).
   This reduction is due to geometric stiffening in the nonlinear analysis.

5. 3D Solid FEA for T=2mm needs debugging - displacement too low.
""")
