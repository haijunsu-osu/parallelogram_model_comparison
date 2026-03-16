import csv
import os
import shutil


WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPARISON_DIR = os.path.join(WORKSPACE, "comparison")
PRESET_DATA_DIR = os.path.join(COMPARISON_DIR, "preset_data")

FEA_2D_SOURCE_CSV = os.path.join(
    WORKSPACE, "fea_models", "2d", "PARALLOGRAM_FEA_2D_sweep_normalized.csv"
)
FEA_3D_SOURCE_CSV = os.path.join(
    WORKSPACE, "fea_models", "3d", "PARALLOGRAM_FEA_3D_sweep_normalized.csv"
)

PRESET_FILES = {
    "fea_2d": os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_FEA_2D_sweep_normalized.csv"),
    "fea_3d": os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_FEA_3D_sweep_normalized.csv"),
    "linear": os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_LINEAR_sweep_normalized.csv"),
    "bcm": os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_BCM_sweep_normalized.csv"),
    "prb_standard": os.path.join(
        PRESET_DATA_DIR, "PARALLOGRAM_PRB_STANDARD_sweep_normalized.csv"
    ),
    "prb_optimized": os.path.join(
        PRESET_DATA_DIR, "PARALLOGRAM_PRB_OPTIMIZED_sweep_normalized.csv"
    ),
    "guided_beam": os.path.join(
        PRESET_DATA_DIR, "PARALLOGRAM_GUIDED_BEAM_sweep_normalized.csv"
    ),
    "euler_bvp": os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_EULER_BVP_sweep_normalized.csv"),
}

MASTER_PRESET_CSV = os.path.join(PRESET_DATA_DIR, "PARALLOGRAM_ALL_MODELS_master.csv")

PRESET_FIELDNAMES = ["Ay", "Ax", "B", "ux", "uy", "phi", "t"]


def ensure_preset_data_dir():
    os.makedirs(PRESET_DATA_DIR, exist_ok=True)


def preset_key(ay, ax, b):
    return (round(float(ay), 9), round(float(ax), 9), round(float(b), 9))


def _pick(row, *names):
    for name in names:
        if name in row and row[name] != "":
            return row[name]
    raise KeyError(f"Missing field; expected one of {names}, got {list(row)}")


def parse_load_values(row):
    return (
        float(_pick(row, "Ay", "fy")),
        float(_pick(row, "Ax", "fx")),
        float(_pick(row, "B", "M", "m")),
    )


def parse_result_values(row):
    return (
        float(_pick(row, "ux", "Ux")),
        float(_pick(row, "uy", "Uy")),
        float(_pick(row, "phi")),
        float(_pick(row, "t")),
    )


def load_csv_rows(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_exact_index(csv_path):
    index = {}
    for row in load_csv_rows(csv_path):
        ay, ax, b = parse_load_values(row)
        index[preset_key(ay, ax, b)] = row
    return index


def find_exact_row(index, ay, ax, b):
    return index.get(preset_key(ay, ax, b))


def ordered_load_cases(csv_path):
    rows = load_csv_rows(csv_path)
    ordered = []
    seen = set()
    for row in rows:
        ay, ax, b = parse_load_values(row)
        key = preset_key(ay, ax, b)
        if key in seen:
            continue
        seen.add(key)
        ordered.append({"Ay": ay, "Ax": ax, "B": b})
    return ordered


def validate_identical_fea_loads():
    fea_2d_keys = {preset_key(*parse_load_values(row)) for row in load_csv_rows(FEA_2D_SOURCE_CSV)}
    fea_3d_keys = {preset_key(*parse_load_values(row)) for row in load_csv_rows(FEA_3D_SOURCE_CSV)}
    if fea_2d_keys != fea_3d_keys:
        only_2d = sorted(fea_2d_keys - fea_3d_keys)[:5]
        only_3d = sorted(fea_3d_keys - fea_2d_keys)[:5]
        raise RuntimeError(
            "FEA normalized sweeps do not share the same load grid. "
            f"only_2d={only_2d} only_3d={only_3d}"
        )
    return ordered_load_cases(FEA_3D_SOURCE_CSV)


def copy_fea_presets():
    ensure_preset_data_dir()
    shutil.copy2(FEA_2D_SOURCE_CSV, PRESET_FILES["fea_2d"])
    shutil.copy2(FEA_3D_SOURCE_CSV, PRESET_FILES["fea_3d"])
