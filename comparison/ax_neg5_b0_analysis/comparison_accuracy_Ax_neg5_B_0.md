# Accuracy Comparison For `Ax = -5`, `B = 0`

This study compares all models in the `Ax = -5`, `B = 0`, `Ay in [0, 20]` slice of the master preset table [PARALLOGRAM_ALL_MODELS_master.csv](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv).

## Method

- Slice used: `Ax = -5`, `B = 0`, `0 <= Ay <= 20`.
- Reference model for error calculations: `FEA 3D`.
- Error metrics reported: absolute error and absolute percentage error for `ux`, `uy`, and `phi`.
- Non-finite model outputs are excluded from aggregate error statistics for the affected metric.
- Percentage-error summaries and percentage-error plots exclude the `Ay = 0` point and any row where the FEA 3D reference value is zero for that metric.

## Available `Ay` Values

`0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## `Ay` Values Used For Percentage Error

- `ux`: `0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`
- `uy`: `0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`
- `phi`: `0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## Model Availability

| Model | Non-finite `Ay` values |
| ----- | ---------------------- |
| FEA 3D | None |
| FEA 2D | None |
| Euler BVP | 20 |
| Guided Beam | None |
| PRB standard | None |
| PRB optimized | None |
| BCM | None |
| Linear | None |

## $u_x$ Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.001877 | 0.005141 | 16 | 1.96 | 2.17 |
| Euler BVP | 16 | 0.006998 | 0.020187 | 15 | 8.23 | 8.94 |
| Guided Beam | 17 | 0.004315 | 0.021965 | 16 | 5.29 | 8.92 |
| PRB standard | 17 | 0.046304 | 0.124305 | 16 | 54.02 | 67.09 |
| PRB optimized | 17 | 0.032642 | 0.084850 | 16 | 39.99 | 55.51 |
| BCM | 17 | 0.090603 | 0.453002 | 16 | 53.19 | 155.02 |
| Linear | 17 | 0.096343 | 0.292231 | 16 | 100.00 | 100.00 |

## $u_y$ Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.004485 | 0.010700 | 16 | 1.29 | 1.69 |
| Euler BVP | 16 | 0.012278 | 0.020107 | 15 | 4.37 | 4.96 |
| Guided Beam | 17 | 0.006992 | 0.017488 | 16 | 2.90 | 4.95 |
| PRB standard | 17 | 0.084984 | 0.127842 | 16 | 29.62 | 36.02 |
| PRB optimized | 17 | 0.047544 | 0.067493 | 16 | 17.57 | 23.53 |
| BCM | 17 | 0.124324 | 0.477675 | 16 | 27.45 | 75.41 |
| Linear | 17 | 0.047102 | 0.199897 | 16 | 15.28 | 31.56 |

## $\phi$ (rad) Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.000395 | 0.001631 | 16 | 3.14 | 4.31 |
| Euler BVP | 16 | 0.000859 | 0.004849 | 15 | 26.05 | 97.27 |
| Guided Beam | 17 | 0.014495 | 0.063692 | 16 | 100.00 | 100.00 |
| PRB standard | 17 | 0.014495 | 0.063692 | 16 | 100.00 | 100.00 |
| PRB optimized | 17 | 0.014495 | 0.063692 | 16 | 100.00 | 100.00 |
| BCM | 17 | 0.009855 | 0.063873 | 16 | 29.81 | 100.29 |
| Linear | 17 | 0.014495 | 0.063692 | 16 | 100.00 | 100.00 |

## Best Non-reference Models By Mean Absolute Percentage Error

- For `ux`, the best non-reference model is `FEA 2D` with mean absolute percentage error `1.96%`.
- For `uy`, the best non-reference model is `FEA 2D` with mean absolute percentage error `1.29%`.
- For `phi`, the best non-reference model is `FEA 2D` with mean absolute percentage error `3.14%`.

## Generated Images

- `ux_vs_Ay_all_models_Ax_neg5_B_0.png`
- `ux_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png`
- `ux_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png`
- `uy_vs_Ay_all_models_Ax_neg5_B_0.png`
- `uy_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png`
- `uy_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png`
- `phi_vs_Ay_all_models_Ax_neg5_B_0.png`
- `phi_abs_error_vs_Ay_all_models_Ax_neg5_B_0.png`
- `phi_abs_pct_error_vs_Ay_all_models_Ax_neg5_B_0.png`

