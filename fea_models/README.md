# FEA Models

This folder contains the current 2D and 3D FreeCAD/CalculiX parallelogram FEA models, sweep datasets, comparison utilities, and analysis notes.

The `old/` folder is intentionally excluded from this summary.

## Top-Level Files

### Comparison Utilities

- `compare_parallelogram_fea_2d_3d.py`
  - Compares the 2D and 3D sweep CSVs by matching `(fy, fx, m)`.
  - Computes differences in `x`, `y`, `phi`, and `t`.
  - Generates Markdown comparison reports.

### Comparison Reports

- `PARALLOGRAM_FEA_2D_vs_3D_REPORT.md`
  - Full comparison report using the original `PARALLOGRAM_FEA_2D_sweep.csv` and `PARALLOGRAM_FEA_3D_sweep.csv`.

- `PARALLOGRAM_FEA_2D_vs_3D_REPORT_no_fx_neg10.md`
  - Comparison report after removing all cases with `fx = -10`.

### Symmetry Note

- `SYMMETRY_NOTES_NEG_FY.md`
  - Documents the symmetry rule used to generate `fy < 0` rows from the `fy >= 0` data.

## `2d/`

### Model Script

- `parallelogram_2d.py`
  - 2D FEA model for the parallelogram compliant mechanism.

### Sweep Data

- `PARALLOGRAM_FEA_2D_sweep.csv`
  - Main 2D sweep results.

- `PARALLOGRAM_FEA_2D_sweep_no_fx_neg10.csv`
  - Filtered 2D sweep with all `fx = -10` rows removed.

- `PARALLOGRAM_FEA_2D_sweep_no_fx_neg10_with_neg_fy.csv`
  - Augmented filtered 2D sweep with mirrored `fy < 0` rows added by symmetry.

### Single-Case Files

- `single_case.csv`
  - One-case input CSV used for spot checks or isolated runs.

- `single_case_result.csv`
  - Result CSV from the single-case 2D run.

## `3d/`

### Model Scripts

- `parallelogram_3d.py`
  - 3D FEA model for the parallelogram compliant mechanism.

- `parallelogram_3d_single.py`
  - Single-case 3D test script used for mesh refinement and spot checks.

### Sweep Data

- `PARALLOGRAM_FEA_3D_sweep.csv`
  - Main 3D sweep results.

- `PARALLOGRAM_FEA_3D_sweep_no_fx_neg10.csv`
  - Filtered 3D sweep with all `fx = -10` rows removed.

- `PARALLOGRAM_FEA_3D_sweep_no_fx_neg10_with_neg_fy.csv`
  - Augmented filtered 3D sweep with mirrored `fy < 0` rows added by symmetry.

### Mesh Refinement Files

- `MESH_REFINEMENT_COMPARISON.md`
  - Summary of the `10 mm` vs `5 mm` mesh comparison for `parallelogram_3d_single.py`.

- `mesh10_run.log`
  - Raw FreeCAD/CalculiX log for the `10 mm` single-case run.

- `mesh5_run.log`
  - Raw FreeCAD/CalculiX log for the `5 mm` single-case run.

### Legacy Single-Run Log

- `single_new_log.txt`
  - Existing 3D single-run log kept for reference.

## Notes

- The filtered `no_fx_neg10` files are intended for comparison work that excludes the `fx = -10` cases.
- The `with_neg_fy` files are symmetry-augmented datasets derived from the filtered files.
- Generated Python bytecode folders such as `__pycache__/` are not part of the analysis workflow.
