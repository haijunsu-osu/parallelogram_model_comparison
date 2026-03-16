# Accuracy Comparison For `Ax = -3`, `B = 0`

This report compares the reduced-order models and 2D FEA against **FEA 3D** for the load slice `Ax = -3`, `B = 0`, using the preset master table [PARALLOGRAM_ALL_MODELS_master.csv](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv).

## Method

- Load slice used: `Ax = -3`, `B = 0`.
- Reference model: `FEA 3D`.
- Error metric: **mean absolute percentage error** for `ux`, `uy`, and `phi`.
- When the FEA 3D reference value is exactly zero, percentage error is undefined and that case is excluded for that metric.
- The `Ay` ranges are treated as closed intervals exactly as written, so `Ay = 2`, `5`, and `10` appear in adjacent sections.

## Available `Ay` Values

`0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## Model Availability

| Model | Non-finite cases in this slice |
| ----- | -----------------------------: |
| FEA 2D | 0 |
| Euler BVP | 1 |
| Guided Beam | 0 |
| PRB standard | 0 |
| PRB optimized | 0 |
| BCM | 0 |
| Linear | 0 |

## Range [0, 2]

`Ay` values: 0, 0.5, 1, 2

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.74 | 25.71 | 1200.76 |
| Euler BVP | 29.40 | 28.27 | 89.23 |
| Guided Beam | 29.33 | 28.23 | 100.00 |
| PRB standard | 64.36 | 45.80 | 100.00 |
| PRB optimized | 51.85 | 35.24 | 100.00 |
| BCM | 6.89 | 28.56 | 26.95 |
| Linear | 100.00 | 33.22 | 100.00 |

## Range [2, 5]

`Ay` values: 2, 3, 4, 5

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.72 | 1.00 | 3.03 |
| Euler BVP | 7.71 | 4.31 | 45.10 |
| Guided Beam | 6.98 | 3.96 | 100.00 |
| PRB standard | 48.51 | 26.77 | 100.00 |
| PRB optimized | 30.81 | 12.79 | 100.00 |
| BCM | 13.55 | 7.45 | 2.83 |
| Linear | 100.00 | 8.67 | 100.00 |

## Range [5, 10]

`Ay` values: 5, 6, 7, 8, 9, 10

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.81 | 1.11 | 2.51 |
| Euler BVP | 7.99 | 4.11 | 11.42 |
| Guided Beam | 5.19 | 2.81 | 100.00 |
| PRB standard | 44.79 | 23.89 | 100.00 |
| PRB optimized | 27.11 | 10.33 | 100.00 |
| BCM | 30.43 | 16.68 | 15.51 |
| Linear | 100.00 | 3.62 | 100.00 |

## Range [10, 20]

`Ay` values: 10, 12, 14, 16, 18, 20

| Model | Mean |ux| % error | Mean |uy| % error | Mean |phi| % error |
| ----- | -----------------: | -----------------: | -------------------: |
| FEA 2D | 1.73 | 1.33 | 2.31 |
| Euler BVP | 7.58 | 3.58 | 3.72 |
| Guided Beam | 2.51 | 1.10 | 100.00 |
| PRB standard | 38.07 | 18.48 | 100.00 |
| PRB optimized | 21.55 | 6.33 | 100.00 |
| BCM | 82.90 | 42.94 | 52.98 |
| Linear | 100.00 | 21.50 | 100.00 |

## Summary

- Best overall non-reference model for `ux`: `FEA 2D` with mean absolute percentage error `1.76%`.
- Best analytical model for `ux`: `Guided Beam` with mean absolute percentage error `10.25%`.
- Best overall non-reference model for `uy`: `FEA 2D` with mean absolute percentage error `6.96%`.
- Best analytical model for `uy`: `Guided Beam` with mean absolute percentage error `8.38%`.
- Best overall non-reference model for `phi`: `BCM` with mean absolute percentage error `29.19%`.
- Best analytical model for `phi`: `BCM` with mean absolute percentage error `29.19%`.
