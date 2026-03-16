# Accuracy Comparison For `Ax = 0`, `B = 0`

This report compares the accuracy of the reduced-order models and 2D FEA against **FEA 3D** using the preset master table [PARALLOGRAM_ALL_MODELS_master.csv](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv).

## Method

- Load slice used: `Ax = 0`, `B = 0`.
- Reference model: `FEA 3D`.
- Error metric: **mean absolute percentage error** for `ux`, `uy`, and `phi`.
- When the FEA 3D reference value is exactly zero, percentage error is undefined and that case is excluded for that metric.
- The ranges are interpreted exactly as requested as closed intervals, so `Ay = 2`, `Ay = 5`, and `Ay = 10` appear in adjacent sections.
- `FEA 3D` is omitted from the tables because its error is zero by definition.

## Available `Ay` Values

`0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## Range [0, 2]

`Ay` values: 0, 0.5, 1, 2

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.42 | 0.84 | 3.91 |
| Euler BVP | 7.02 | 3.80 | 89.24 |
| Guided Beam | 7.01 | 3.77 | 100.00 |
| PRB standard | 30.61 | 15.51 | 100.00 |
| PRB optimized | 6.26 | 0.94 | 100.00 |
| BCM | 7.57 | 4.09 | 2.83 |
| Linear | 100.00 | 4.09 | 100.00 |

## Range [2, 5]

`Ay` values: 2, 3, 4, 5

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.48 | 0.88 | 2.94 |
| Euler BVP | 7.08 | 3.77 | 54.29 |
| Guided Beam | 6.62 | 3.55 | 100.00 |
| PRB standard | 29.91 | 15.01 | 100.00 |
| PRB optimized | 5.81 | 1.20 | 100.00 |
| BCM | 10.83 | 5.98 | 2.64 |
| Linear | 100.00 | 5.98 | 100.00 |

## Range [5, 10]

`Ay` values: 5, 6, 7, 8, 9, 10

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.59 | 0.98 | 2.24 |
| Euler BVP | 7.02 | 3.65 | 19.03 |
| Guided Beam | 5.20 | 2.80 | 100.00 |
| PRB standard | 27.75 | 13.51 | 100.00 |
| PRB optimized | 4.60 | 1.90 | 100.00 |
| BCM | 22.72 | 12.68 | 12.95 |
| Linear | 100.00 | 12.68 | 100.00 |

## Range [10, 20]

`Ay` values: 10, 12, 14, 16, 18, 20

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.63 | 1.19 | 2.28 |
| Euler BVP | 6.58 | 3.19 | 3.30 |
| Guided Beam | 2.03 | 1.02 | 100.00 |
| PRB standard | 23.79 | 10.69 | 100.00 |
| PRB optimized | 3.43 | 2.64 | 100.00 |
| BCM | 61.60 | 32.99 | 41.93 |
| Linear | 100.00 | 32.99 | 100.00 |

## Summary

- `FEA 2D` is the most accurate non-reference model across all four `Ay` ranges.
- `Euler BVP` is consistently the next-best high-fidelity analytical model and improves noticeably relative to the other analytical models as `Ay` increases.
- `Guided Beam`, `Linear`, and both `PRB` variants show zero-rotation assumptions or simplified kinematics clearly in the `phi` error column, especially because their `phi` prediction is zero for this load slice.
- `PRB optimized` improves substantially over `PRB standard` for `ux` and `uy`, but neither PRB variant captures `phi` for this case family.
- `BCM` remains competitive at small deflection but its `ux`, `uy`, and especially `phi` errors grow strongly in the high-`Ay` range.
