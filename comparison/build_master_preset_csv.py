import csv

from preset_catalog import MASTER_PRESET_CSV, PRESET_FILES, ensure_preset_data_dir, load_exact_index


MODEL_SUFFIXES = [
    ("fea_3d", "fea3d"),
    ("fea_2d", "fea2d"),
    ("euler_bvp", "euler"),
    ("guided_beam", "guided"),
    ("prb_standard", "prb"),
    ("prb_optimized", "prb_opt"),
    ("bcm", "bcm"),
    ("linear", "linear"),
]

METRICS = ("ux", "uy", "phi", "t")


def build_fieldnames():
    fieldnames = ["Ay", "Ax", "B"]
    for _model_key, suffix in MODEL_SUFFIXES:
        for metric in METRICS:
            fieldnames.append(f"{metric}_{suffix}")
    return fieldnames


def main():
    ensure_preset_data_dir()
    indexes = {model_key: load_exact_index(PRESET_FILES[model_key]) for model_key, _suffix in MODEL_SUFFIXES}
    reference_rows = list(indexes["fea_3d"].values())
    fieldnames = build_fieldnames()

    with open(MASTER_PRESET_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for ref_row in reference_rows:
            ay = float(ref_row["Ay"])
            ax = float(ref_row["Ax"])
            b = float(ref_row["B"])
            row = {"Ay": ay, "Ax": ax, "B": b}

            for model_key, suffix in MODEL_SUFFIXES:
                model_row = indexes[model_key].get((round(ay, 9), round(ax, 9), round(b, 9)))
                if model_row is None:
                    raise KeyError(f"Missing {model_key} row for Ay={ay}, Ax={ax}, B={b}")
                row[f"ux_{suffix}"] = float(model_row["ux"])
                row[f"uy_{suffix}"] = float(model_row["uy"])
                row[f"phi_{suffix}"] = float(model_row["phi"])
                row[f"t_{suffix}"] = float(model_row["t"])

            writer.writerow(row)

    print(f"Wrote {MASTER_PRESET_CSV}")


if __name__ == "__main__":
    main()
