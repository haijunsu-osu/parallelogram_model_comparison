# Symmetry Notes For Extending To Negative `fy`

These notes describe how to derive missing `fy < 0` rows from the existing `fy >= 0` FEA sweep data for the symmetric parallelogram mechanism.

## Symmetry Mapping

For mirror symmetry about the `x` axis:

- load mapping:
  - `(fy, fx, m) -> (-fy, fx, -m)`
- response mapping:
  - `(x, y, phi) -> (x, -y, -phi)`
- runtime:
  - `t -> t`

So a source row:

```text
( fy,  fx,  m,  x,  y,  phi, t)
```

maps to the derived row:

```text
(-fy,  fx, -m,  x, -y, -phi, t)
```

## Practical Rules

- Keep `fx` unchanged.
- Flip the sign of `fy`.
- Flip the sign of `m`.
- Keep `x` unchanged.
- Flip the sign of `y`.
- Flip the sign of `phi`.
- Copy `t` as metadata if you want a mirrored runtime value.

## Important Caveat

You cannot derive `(-fy, fx, m)` from `(fy, fx, m)` when `m != 0`.

The correct source row for `(-fy, fx, m)` is:

```text
(fy, fx, -m)
```

That is because the symmetry operation flips both `fy` and `m`.

## Recommended Workflow

1. Keep all existing rows unchanged.
2. For each row with `fy > 0`, generate one mirrored row using the mapping above.
3. Do not generate mirrored duplicates from rows with `fy = 0`.
4. Do not mirror any row that is known to be failed or nonphysical, such as suspicious zero-deflection failure rows.

## Example

Source row:

```text
(fy=5, fx=2, m=-3, x, y, phi, t)
```

Derived row:

```text
(fy=-5, fx=2, m=3, x, -y, -phi, t)
```

## Intended Input Files

These notes are intended for the filtered sweep files that exclude `fx = -10`:

- `fea_models/2d/PARALLOGRAM_FEA_2D_sweep_no_fx_neg10.csv`
- `fea_models/3d/PARALLOGRAM_FEA_3D_sweep_no_fx_neg10.csv`
