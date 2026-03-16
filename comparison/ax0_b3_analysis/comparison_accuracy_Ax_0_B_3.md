# Accuracy Comparison For `Ax = 0`, `B = 3`

This study compares all models in the `Ax = 0`, `B = 3`, `Ay in [0, 20]` slice of the master preset table [PARALLOGRAM_ALL_MODELS_master.csv](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv).

## Method

- Slice used: `Ax = 0`, `B = 3`, `0 <= Ay <= 20`.
- Reference model for error calculations: `FEA 3D`.
- Error metrics reported: absolute error and absolute percentage error for `ux`, `uy`, and `phi`.
- Non-finite model outputs are excluded from aggregate error statistics for the affected metric.
- Percentage-error summaries and percentage-error plots exclude the `Ay = 0` point.

## Available `Ay` Values

`0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## `Ay` Values Used For Percentage Error

`0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20`

## Model Availability

| Model | Non-finite `Ay` values |
| ----- | ---------------------- |
| FEA 3D | None |
| FEA 2D | None |
| Euler BVP | 18, 20 |
| Guided Beam | None |
| PRB standard | None |
| PRB optimized | None |
| BCM | None |
| Linear | None |

## $u_x$ Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.004184 | 0.020518 | 16 | 4.01 | 8.94 |
| Euler BVP | 15 | 0.003498 | 0.011727 | 14 | 6.68 | 7.04 |
| Guided Beam | 17 | 0.003111 | 0.019504 | 16 | 3.69 | 8.50 |
| PRB standard | 17 | 0.019392 | 0.061537 | 16 | 29.74 | 32.80 |
| PRB optimized | 17 | 0.005730 | 0.022082 | 16 | 7.99 | 9.62 |
| BCM | 17 | 0.035058 | 0.187204 | 16 | 27.38 | 81.58 |
| Linear | 17 | 0.069431 | 0.229463 | 16 | 100.00 | 100.00 |

## $u_y$ Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.003328 | 0.010216 | 16 | 1.02 | 1.83 |
| Euler BVP | 15 | 0.008071 | 0.016250 | 14 | 3.42 | 3.66 |
| Guided Beam | 17 | 0.004573 | 0.018177 | 16 | 1.83 | 3.17 |
| PRB standard | 17 | 0.036233 | 0.066051 | 16 | 14.44 | 16.99 |
| PRB optimized | 17 | 0.001266 | 0.002996 | 16 | 0.42 | 0.79 |
| BCM | 17 | 0.062404 | 0.259497 | 16 | 15.60 | 45.22 |
| Linear | 17 | 0.062404 | 0.259497 | 16 | 15.60 | 45.22 |

## $\phi$ (rad) Error Summary

| Model | Valid abs cases | Mean abs error | Max abs error | Valid % cases | Mean abs % error | Max abs % error |
| ----- | --------------: | -------------: | ------------: | ------------: | ----------------: | ---------------: |
| FEA 3D | 17 | 0.000000 | 0.000000 | 16 | 0.00 | 0.00 |
| FEA 2D | 17 | 0.005954 | 0.025058 | 16 | 57.98 | 92.44 |
| Euler BVP | 15 | 0.000732 | 0.000958 | 14 | 34.37 | 98.15 |
| Guided Beam | 17 | 0.012351 | 0.052110 | 16 | 100.00 | 100.00 |
| PRB standard | 17 | 0.012351 | 0.052110 | 16 | 100.00 | 100.00 |
| PRB optimized | 17 | 0.012351 | 0.052110 | 16 | 100.00 | 100.00 |
| BCM | 17 | 0.003392 | 0.021947 | 16 | 12.16 | 42.12 |
| Linear | 17 | 0.012351 | 0.052110 | 16 | 100.00 | 100.00 |

## Best Non-reference Models By Mean Absolute Percentage Error

- For `ux`, the best non-reference model is `Guided Beam` with mean absolute percentage error `3.69%`.
- For `uy`, the best non-reference model is `PRB optimized` with mean absolute percentage error `0.42%`.
- For `phi`, the best non-reference model is `BCM` with mean absolute percentage error `12.16%`.

## Generated Images

- `ux_vs_Ay_all_models_Ax_0_B_3.png`
- `ux_abs_error_vs_Ay_all_models_Ax_0_B_3.png`
- `ux_abs_pct_error_vs_Ay_all_models_Ax_0_B_3.png`
- `uy_vs_Ay_all_models_Ax_0_B_3.png`
- `uy_abs_error_vs_Ay_all_models_Ax_0_B_3.png`
- `uy_abs_pct_error_vs_Ay_all_models_Ax_0_B_3.png`
- `phi_vs_Ay_all_models_Ax_0_B_3.png`
- `phi_abs_error_vs_Ay_all_models_Ax_0_B_3.png`
- `phi_abs_pct_error_vs_Ay_all_models_Ax_0_B_3.png`

