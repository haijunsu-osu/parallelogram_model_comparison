import csv
import math
import os
from pathlib import Path

from preset_catalog import PRESET_DATA_DIR


SUFFIX = "_with_neg_Ay"


def negate_value(text):
    value = float(text)
    if math.isnan(value):
        return math.nan
    return -value


def mirror_row(row):
    mirrored = {}
    for key, value in row.items():
        if key == "Ay":
            mirrored[key] = negate_value(value)
        elif key == "B":
            mirrored[key] = negate_value(value)
        elif key == "Ax":
            mirrored[key] = float(value)
        elif key == "uy" or key.startswith("uy_"):
            mirrored[key] = negate_value(value)
        elif key == "phi" or key.startswith("phi_"):
            mirrored[key] = negate_value(value)
        elif key == "ux" or key.startswith("ux_"):
            mirrored[key] = float(value)
        elif key == "t" or key.startswith("t_"):
            mirrored[key] = float(value)
        else:
            mirrored[key] = value
    return mirrored


def augment_csv(csv_path):
    output_path = csv_path.with_name(f"{csv_path.stem}{SUFFIX}{csv_path.suffix}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        rows = list(reader)

    augmented_rows = list(rows)
    for row in rows:
        if float(row["Ay"]) <= 0.0:
            continue
        augmented_rows.append(mirror_row(row))

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(augmented_rows)

    print(f"{csv_path.name} -> {output_path.name} ({len(augmented_rows)} rows)")


def main():
    preset_dir = Path(os.path.abspath(PRESET_DATA_DIR))
    for name in sorted(os.listdir(preset_dir)):
        if not name.endswith(".csv"):
            continue
        if name.endswith(f"{SUFFIX}.csv"):
            continue
        augment_csv(preset_dir / name)


if __name__ == "__main__":
    main()
