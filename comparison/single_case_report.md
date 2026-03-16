# Parallelogram Flexure - Single-Case Model Comparison

**Test case:** Ax = 0.0,  Ay = 5.0,  M = 0.0

**Geometry / material:**
- L = 250.0 mm, T = 5.0 mm, H = 50.0 mm
- W = 150.0 mm (full centreline separation; beams at y = +/-75 mm)
- E = 210 GPa (Steel), nu = 0.3
- Normalised: w = W/(2L) = 0.30, t = T/L = 0.0200

**Ground truth:** FEA 3D solid-element model

**FEA 2D source:** preset sweep: PARALLOGRAM_FEA_2D_sweep_normalized.csv
**FEA 3D source:** preset sweep: PARALLOGRAM_FEA_3D_sweep_normalized.csv
**Linear source:** preset sweep: PARALLOGRAM_LINEAR_sweep_normalized.csv
**BCM source:** preset sweep: PARALLOGRAM_BCM_sweep_normalized.csv
**PRB standard source:** preset sweep: PARALLOGRAM_PRB_STANDARD_sweep_normalized.csv
**PRB optimised source:** preset sweep: PARALLOGRAM_PRB_OPTIMIZED_sweep_normalized.csv
**Guided Beam source:** preset sweep: PARALLOGRAM_GUIDED_BEAM_sweep_normalized.csv
**Euler BVP source:** preset sweep: PARALLOGRAM_EULER_BVP_sweep_normalized.csv

> **Sign convention:** phi is CCW-positive throughout. FEA uses
> `phi = atan2(Delta x_bot - Delta x_top, W_sep - Delta y_sep)`.

## Results

| Model                    | Ux         | Uy         | phi (rad)    | eUx (%)   | eUy (%)   | ephi (%)   | t (s)    |
| ------------------------ | ---------- | ---------- | ------------ | --------- | --------- | ---------- | -------- |
| Linear theory            | 0.000000   | 0.208333   | 0.000000     | +100.00%  | +7.79%    | -100.00%   | 0.000    |
| BCM (Awtar)              | -0.026042  | 0.208333   | 0.001324     | -13.98%   | +7.79%    | +5.50%     | 0.000    |
| PRB standard             | -0.016164  | 0.165142   | 0.000000     | +29.25%   | -14.55%   | -100.00%   | 0.000    |
| PRB optimised            | -0.021613  | 0.196052   | 0.000000     | +5.40%    | +1.44%    | -100.00%   | 0.000    |
| Guided Beam              | -0.024273  | 0.199738   | 0.000000     | -6.24%    | +3.35%    | -100.00%   | 0.003    |
| Euler BVP                | -0.024463  | 0.200513   | 0.000828     | -7.08%    | +3.75%    | -34.03%    | 1.537    |
| FEA 2D (beam, preset)    | -0.022499  | 0.191514   | 0.001225     | +1.52%    | -0.91%    | -2.44%     | 0.573    |
| FEA 3D (ground, preset) **<** | -0.022847  | 0.193272   | 0.001255     | +0.00%    | +0.00%    | +0.00%     | 40.257   |

## Ground Truth (FEA 3D)

| Quantity | Value |
| -------- | ----- |
| Ux       | -0.022847 |
| Uy       | 0.193272 |
| phi (rad) | 0.001255 |
| Runtime  | 40.3 s |

## Notes

- **FEA 3D**: 3D solid-element model (BooleanFragments + Slice, CalculiX linear static).
- **FEA 2D**: 2D beam-element model (Euler-Bernoulli beams + quasi-rigid stage, CalculiX).
- When the load matches the preset sweep grid, the report uses the precomputed preset CSV rows for all models.
- If the load is outside the preset grid, analytical models solve live and FEA falls back to FreeCAD.
- **Euler BVP**: exact nonlinear solution of coupled beam BVPs plus rigid-stage compatibility.
- **Guided Beam**: single fixed-guided beam BVP with half-load approximation.
- **PRB standard / optimised**: reduced-order nonlinear approximations for the same geometry.
- **Linear theory**: Uy = Ay/24 with Ux = 0 and phi = 0.

*Report generated: 2026-03-14 21:33:43*