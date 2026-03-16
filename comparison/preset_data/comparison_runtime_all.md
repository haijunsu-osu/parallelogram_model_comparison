# Parallelogram Model Runtime Comparison

This report summarizes the computational performance of all models stored in [PARALLOGRAM_ALL_MODELS_master.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv). The master file contains one row per computed load case and one set of `ux`, `uy`, `phi`, and `t` values for each model.

An augmented symmetry-expanded file is also available at [PARALLOGRAM_ALL_MODELS_master_with_neg_Ay.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master_with_neg_Ay.csv). That larger file includes mirrored `Ay < 0` rows generated from symmetry, not additional independently solved cases.

## 1. FEA Data Generation and Load Range

The FEA entries in the master table come from two precomputed normalized sweep files:

- [PARALLOGRAM_FEA_2D_sweep_normalized.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_2D_sweep_normalized.csv)
- [PARALLOGRAM_FEA_3D_sweep_normalized.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_3D_sweep_normalized.csv)

Both FEA sweeps use the same 1547 directly computed load cases and store normalized stage-center deflections:

- `ux = x / L`
- `uy = y / L`
- `phi` in radians
- `t` as the recorded per-case solve time

The directly computed sweep grid is:

- `Ay ∈ {0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20}`
- `Ax ∈ {-10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10}`
- `B ∈ {-3, -2, -1, 0, 1, 2, 3}`

This gives `17 × 13 × 7 = 1547` total loading conditions.

## 1a. Symmetry Augmentation And Sign Flipping

All preset CSV files in this folder now also have augmented copies with the suffix `_with_neg_Ay.csv`. These expanded files add mirrored `Ay < 0` rows using the symmetry mapping documented in [SYMMETRY_NOTES_NEG_FY.md](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/fea_models/SYMMETRY_NOTES_NEG_FY.md).

The applied mapping is:

- load mapping: `(Ay, Ax, B) -> (-Ay, Ax, -B)`
- response mapping: `(ux, uy, phi) -> (ux, -uy, -phi)`
- runtime mapping: `t -> t`

So for the augmented files:

- `Ay` is extended from `[-20, 20]`
- `Ax` stays unchanged
- `B` is mirrored with sign flip
- `ux` is copied unchanged
- `uy` and `phi` are sign-flipped
- `t` is copied as metadata from the original solved row

Because `Ay = 0` rows are not duplicated, each augmented CSV has:

- original computed rows: `1547`
- mirrored added rows: `1456`
- total augmented rows: `3003`

The 2D FEA data are from the beam-element model, and the 3D FEA data are from the solid-element model. The master table also includes the six analytical models evaluated on the exact same load grid:

- Linear
- BCM
- PRB standard
- PRB optimized
- Guided Beam
- Euler BVP

## 2. Running Platform

The local machine used for the runs reports:

- OS: Microsoft Windows 11 Home 64-bit, version `10.0.26200`
- CPU: Intel Core i7-10700KF
- CPU architecture: x86-64
- Physical cores: 8
- Logical processors: 16
- Windows-reported clock: `3792 MHz`

For the 3D FEA parallel sweep, the run configuration used the user-reported `10` worker processes at about `4.2 GHz`.

## 3. Total Runtime Notes for 3D and 2D FEA

For the 3D FEA sweep:

- the sum of the recorded per-case solver times in the CSV is `68481.16 s`, which is about `19.02 h`
- the actual wall-clock runtime for the parallel job was about `3 h` using `10` CPU workers

For the 2D FEA sweep:

- the run was executed on a single CPU worker
- the total recorded solver time from the CSV is `1949.00 s`, which is about `32.48 min` or `0.54 h`

The difference between the 3D accumulated solver time and the 3D wall-clock runtime is due to parallel execution. In contrast, the 2D sweep total is effectively its wall-clock runtime because it was run on one worker.

Important interpretation note:

- these runtime totals refer to the original `1547` directly computed load cases
- the `_with_neg_Ay.csv` rows were created by symmetry augmentation
- the copied `t` values in those mirrored rows do **not** represent extra solver work
- therefore the augmented `3003`-row files must not be used to recompute total wall-clock cost by simple summation

## 4. Computational Efficiency Comparison

The table below uses **FEA 3D** as the baseline. Two speedup measures are reported:

- `Per-case speedup`: ratio of the mean FEA 3D solve time (`44.27 s/case`) to the model mean time
- `Sweep speedup`: ratio of the user-reported 3D FEA wall-clock runtime (`3.0 h`) to the model total recorded runtime

For Euler BVP, `122` load cases are flagged as failed in the preset data, so the success count is lower than the other models.

This table is based on the original directly computed dataset, not the mirrored `_with_neg_Ay.csv` copies.

| Model | Success / 1547 | Mean `t` per case (s) | Median `t` (s) | Max `t` (s) | Total recorded `t` | Per-case speedup vs 3D FEA | Sweep speedup vs 3D FEA wall-clock |
| ----- | --------------: | --------------------: | -------------: | ----------: | -----------------: | --------------------------: | ----------------------------------: |
| FEA 3D | 1547 | 44.2671 | 40.7084 | 167.4008 | 19.02 h | 1.00x | 1.00x |
| FEA 2D | 1547 | 1.2599 | 0.8758 | 316.5180 | 0.54 h | 35.14x | 5.54x |
| Euler BVP | 1425 | 2.8637 | 1.6371 | 15.0250 | 1.23 h | 15.46x | 2.44x |
| Guided Beam | 1547 | 0.003167 | 0.002994 | 0.031457 | 4.90 s | 13979.51x | 2204.67x |
| PRB standard | 1547 | 0.000084 | 0.000083 | 0.000424 | 0.13 s | 526487.50x | 83030.68x |
| PRB optimized | 1547 | 0.000096 | 0.000092 | 0.001162 | 0.15 s | 460606.72x | 72640.84x |
| BCM | 1547 | 0.00000345 | 0.00000340 | 0.00004920 | 0.0053 s | 12827316.47x | 2023115.97x |
| Linear | 1547 | 0.000000373 | 0.000000300 | 0.000026600 | 0.00058 s | 118678469.58x | 18720748.83x |

## 5. Observations

- 3D FEA is by far the most expensive model, both per case and for the full sweep.
- 2D FEA is much cheaper than 3D FEA, about `35x` faster per case and about `5.5x` faster for the full sweep when compared against the `3 h` parallel 3D run.
- Euler BVP is still much cheaper than 3D FEA, but it is much slower than the reduced-order analytical models and it does not succeed on every load case in the preset data.
- Guided Beam, PRB, BCM, and Linear are effectively instantaneous at sweep scale compared with either FEA model.
- Among the analytical approximations, `Linear` is the fastest, followed by `BCM`, then the two `PRB` variants, then `Guided Beam`, and finally `Euler BVP`.

## 6. Source Files

- [PARALLOGRAM_ALL_MODELS_master.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master.csv)
- [PARALLOGRAM_ALL_MODELS_master_with_neg_Ay.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_ALL_MODELS_master_with_neg_Ay.csv)
- [PARALLOGRAM_FEA_2D_sweep_normalized.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_2D_sweep_normalized.csv)
- [PARALLOGRAM_FEA_2D_sweep_normalized_with_neg_Ay.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_2D_sweep_normalized_with_neg_Ay.csv)
- [PARALLOGRAM_FEA_3D_sweep_normalized.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_3D_sweep_normalized.csv)
- [PARALLOGRAM_FEA_3D_sweep_normalized_with_neg_Ay.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_FEA_3D_sweep_normalized_with_neg_Ay.csv)
- [PARALLOGRAM_EULER_BVP_sweep_normalized.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_EULER_BVP_sweep_normalized.csv)
- [PARALLOGRAM_EULER_BVP_sweep_normalized_with_neg_Ay.csv](/c:/Users/haiju/OneDrive/Documents/antigravity/parallel_guided_beam/comparison/preset_data/PARALLOGRAM_EULER_BVP_sweep_normalized_with_neg_Ay.csv)
