# FEA 3D Ax Sweep Summary

## Scope

This study uses the `FEA 3D` results for:
- `Ay = 0` to `20`
- `Ax = [-10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10]`
- `B = 0`

The plots also include the `Linear beam` baseline from [PARALLOGRAM_ALL_MODELS_master.csv](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv) to highlight the softening and stiffening effect of axial load.

Generated figures:
- [ux_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/fea3d_all_metrics_ax_sweep/ux_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png)
- [uy_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/fea3d_all_metrics_ax_sweep/uy_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png)
- [phi_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png](C:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/fea3d_all_metrics_ax_sweep/phi_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png)

## Main Findings

- The axial load clearly changes transverse compliance. Negative `Ax` increases `uy` at a given `Ay`, while positive `Ax` decreases it. In this sweep, negative `Ax` acts as a softening load and positive `Ax` acts as a stiffening load.
- The same trend appears in rotation `phi`. Compression increases stage rotation, while tension suppresses it.
- The parasitic displacement `ux` becomes more negative as `Ay` increases for every `Ax`, and compression magnifies its magnitude.
- The linear beam baseline does not capture axial-load dependence in this dataset. Its `uy` curve depends only on `Ay`, while `ux = 0` and `phi = 0` everywhere. The spread of the `FEA 3D` families around that baseline is the axial-load effect.
- All `uy` and `phi` curves increase monotonically with `Ay` over the sampled range. No abrupt instability appears in these sampled points up to `Ay = 20`.

## Quantitative Checkpoints

Selected `uy` values:

| Ay | Linear beam `uy` | FEA 3D `uy` at `Ax=-10` | FEA 3D `uy` at `Ax=0` | FEA 3D `uy` at `Ax=10` |
|---:|---:|---:|---:|---:|
| 5  | 0.2083 | 0.3374 | 0.1933 | 0.1333 |
| 10 | 0.4167 | 0.5327 | 0.3524 | 0.2556 |
| 20 | 0.8333 | 0.7297 | 0.5599 | 0.4455 |

Interpretation of the `uy` checkpoints:
- At `Ay = 20`, moving from `Ax = 0` to `Ax = -10` raises `uy` by about `30.3%`.
- At `Ay = 20`, moving from `Ax = 0` to `Ax = 10` lowers `uy` by about `20.4%`.
- At `Ay = 20`, the compressive case `Ax = -10` gives about `63.8%` larger `uy` than the tensile case `Ax = 10`.
- Even the softened `Ax = -10` response remains below the linear-beam prediction at `Ay = 20`, but it is much closer to it than the tensile cases.

## Ay = 20 Snapshot

| Ax | `uy` | `uy` vs `Ax=0` | `uy` vs linear beam | `ux` | `phi` |
|---:|---:|---:|---:|---:|---:|
| -10 | 0.729728 | +30.34% | -12.43% | -0.435532 | 0.150078 |
| -5  | 0.633436 | +13.14% | -23.99% | -0.292231 | 0.063692 |
| -4  | 0.617632 | +10.32% | -25.88% | -0.273941 | 0.055811 |
| -3  | 0.602344 | +7.59% | -27.72% | -0.257225 | 0.049119 |
| -2  | 0.587948 | +5.01% | -29.45% | -0.242311 | 0.043784 |
| -1  | 0.573656 | +2.46% | -31.16% | -0.228195 | 0.038831 |
| 0   | 0.559876 | +0.00% | -32.81% | -0.215222 | 0.034597 |
| 1   | 0.546568 | -2.38% | -34.41% | -0.203244 | 0.030942 |
| 2   | 0.533736 | -4.67% | -35.95% | -0.192177 | 0.027789 |
| 3   | 0.521332 | -6.88% | -37.44% | -0.181909 | 0.025040 |
| 4   | 0.509352 | -9.02% | -38.88% | -0.172370 | 0.022637 |
| 5   | 0.498016 | -11.05% | -40.24% | -0.163680 | 0.020572 |
| 10  | 0.445468 | -20.43% | -46.54% | -0.127223 | 0.013119 |

This snapshot shows the three coupled effects clearly:
- `uy` drops steadily as `Ax` moves from compression to tension.
- `|ux|` also drops steadily as `Ax` moves from compression to tension.
- `phi` is highly sensitive to axial load: at `Ay = 20`, `phi` at `Ax = -10` is about `4.34x` the `Ax = 0` value and about `11.4x` the `Ax = 10` value.

## Interpretation

The linear beam baseline is useful as a reference, but it does not represent the axial-load effect because it does not change with `Ax`. The `FEA 3D` sweep shows that compressive axial load makes the stage more compliant in `uy` and more rotation-prone, while tensile axial load suppresses both. In other words:
- negative `Ax` produces softening
- positive `Ax` produces stiffening

That effect is strongest in `phi`, moderate in `uy`, and also visible in the parasitic `ux` response.
