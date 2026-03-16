# Mesh Refinement Comparison

Script:
- `parallelogram_3d_single.py`

Case:
- `Ax = 0`
- `Ay = 5`
- `M = 0`

Meshes included in this update:
- `10 mm`
- `7.5 mm`
- `5 mm`
- `4 mm`
- `3 mm`

Note:
- The `2 mm` run was started but not completed, so it is excluded from this comparison.

## Results

| Mesh | Nodes | Elements | x (mm) | y (mm) | phi (rad) | Mesh Time (s) | Solve Time (s) | Total Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 mm | 9450 | 4878 | -5.7117 | 48.3180 | 0.001255 | 1.3 | 38.1 | 40.8 |
| 7.5 mm | 18566 | 10000 | -5.7370 | 48.4389 | 0.001262 | 1.3 | 82.3 | 85.9 |
| 5 mm | 42682 | 24558 | -5.7515 | 48.5085 | 0.001269 | 2.5 | 222.5 | 229.6 |
| 4 mm | 76246 | 45332 | -5.7655 | 48.5761 | 0.001274 | 4.5 | 511.6 | 523.5 |
| 3 mm | 154796 | 95810 | -5.7723 | 48.6102 | 0.001277 | 8.6 | 1739.9 | 1762.7 |

## Difference From 3 mm Reference

| Mesh | Abs dx (mm) | Abs dy (mm) | Abs dphi (rad) | dx Rel. | dy Rel. | dphi Rel. |
|---|---:|---:|---:|---:|---:|---:|
| 10 mm | 0.0606 | 0.2922 | 0.000022 | 1.05% | 0.60% | 1.72% |
| 7.5 mm | 0.0353 | 0.1713 | 0.000015 | 0.61% | 0.35% | 1.17% |
| 5 mm | 0.0208 | 0.1017 | 0.000008 | 0.36% | 0.21% | 0.63% |
| 4 mm | 0.0068 | 0.0341 | 0.000003 | 0.12% | 0.07% | 0.23% |
| 3 mm | 0.0000 | 0.0000 | 0.000000 | 0.00% | 0.00% | 0.00% |

## Change Between Consecutive Meshes

| Transition | Abs dx (mm) | Abs dy (mm) | Abs dphi (rad) | dx Rel. | dy Rel. | dphi Rel. |
|---|---:|---:|---:|---:|---:|---:|
| 10 mm -> 7.5 mm | 0.0253 | 0.1209 | 0.000007 | 0.44% | 0.25% | 0.55% |
| 7.5 mm -> 5 mm | 0.0145 | 0.0696 | 0.000007 | 0.25% | 0.14% | 0.55% |
| 5 mm -> 4 mm | 0.0140 | 0.0676 | 0.000005 | 0.24% | 0.14% | 0.39% |
| 4 mm -> 3 mm | 0.0068 | 0.0341 | 0.000003 | 0.12% | 0.07% | 0.23% |

## Interpretation

For this load case, the displacement and rotation values continue to move monotonically as the mesh is refined from `10 mm` to `3 mm`, but the change gets smaller at each refinement step.

Using `3 mm` as the reference:
- `10 mm` is already within about `1.05%` in `x`, `0.60%` in `y`, and `1.72%` in `phi`.
- `7.5 mm` improves that to about `0.61%`, `0.35%`, and `1.17%`.
- `5 mm` is within about `0.36%`, `0.21%`, and `0.63%`.
- `4 mm` is within about `0.12%`, `0.07%`, and `0.23%`.

The runtime penalty grows much faster than the result changes:
- total time rises from `40.8 s` at `10 mm` to `85.9 s` at `7.5 mm`
- then to `229.6 s` at `5 mm`
- then to `523.5 s` at `4 mm`
- and `1762.7 s` at `3 mm`

For this case, `4 mm` appears to be a reasonable compromise if a result very close to the `3 mm` mesh is needed without paying the full `3 mm` runtime.

## Raw Logs

- `convergence_logs/mesh_10p0mm.log`
- `convergence_logs/mesh_7p5mm.log`
- `convergence_logs/mesh_5p0mm.log`
- `convergence_logs/mesh_4p0mm.log`
- `convergence_logs/mesh_3p0mm.log`
