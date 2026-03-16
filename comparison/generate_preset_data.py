import csv
import math
import os
import sys
import time

import numpy as np

from preset_catalog import (
    PRESET_FIELDNAMES,
    PRESET_FILES,
    copy_fea_presets,
    ensure_preset_data_dir,
    preset_key,
    validate_identical_fea_loads,
)


WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("euler_beam", "guided_beam", "prb", "bcm"):
    path = os.path.join(WORKSPACE, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from bcm_parallelogram import BCMParallelogram
from guided_beam_solver import compute_tip_displacement
from parallelogram_solver import ParallelogramFlexureSolver
from prb_parallelogram import PRBParallelogramModel


W_NORM = 0.30
T_NORM = 0.02


class EulerBvpBatchRunner:
    def __init__(self, w=W_NORM):
        self.solver = ParallelogramFlexureSolver(w=w)
        self.guess_cache = {}

    def _nearest_guess(self, ay, ax, b):
        best_guess = None
        best_dist = None
        for (row_ay, row_ax, row_b), guess in self.guess_cache.items():
            dist = abs(row_ay - ay) + abs(row_ax - ax) + 1.5 * abs(row_b - b)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_guess = guess
        return best_guess

    def solve(self, ax, ay, b):
        attempts = []
        nearest_guess = self._nearest_guess(ay, ax, b)
        if nearest_guess is not None:
            attempts.append(nearest_guess)
        attempts.append(None)

        for guess in attempts:
            ok = self.solver.solve(A_x=ax, A_y=ay, B=b, initial_guess=guess)
            if ok:
                params = np.array(
                    [
                        self.solver.alpha_x1,
                        self.solver.alpha_y1,
                        self.solver.beta_1,
                        self.solver.alpha_x2,
                        self.solver.alpha_y2,
                        self.solver.beta_2,
                    ],
                    dtype=float,
                )
                self.guess_cache[preset_key(ay, ax, b)] = params
                return self.solver.X_p - 1.0, self.solver.Y_p, self.solver.phi

        return math.nan, math.nan, math.nan


def run_linear(ax, ay, b):
    return 0.0, ay / 24.0, 0.0


def run_guided(ax, ay, b):
    delta, ux, _beta = compute_tip_displacement(alpha_y=ay / 2.0, alpha_x=ax / 2.0)
    return ux, delta, 0.0


def run_prb_standard(ax, ay, b):
    model = PRBParallelogramModel(w=W_NORM)
    delta, ux, phi, _theta = model.solve(ay)
    return ux, delta, phi


def run_prb_optimized(ax, ay, b):
    model = PRBParallelogramModel(w=W_NORM)
    model.gamma = 0.90
    model.K_theta_coeff = 2.50
    delta, ux, phi, _theta = model.solve(ay)
    return ux, delta, phi


def run_bcm(ax, ay, b):
    model = BCMParallelogram(w=W_NORM, t=T_NORM)
    result = model.solve(ax, ay, B=b)
    if not result.get("success", False):
        return math.nan, math.nan, math.nan
    return -result["u1"], result["delta"], result["phi"]


def write_rows(csv_path, rows):
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PRESET_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def build_rows(model_label, load_cases, run_case, progress_step=100):
    rows = []
    for index, load_case in enumerate(load_cases, start=1):
        ay = load_case["Ay"]
        ax = load_case["Ax"]
        b = load_case["B"]
        start = time.perf_counter()
        try:
            ux, uy, phi = run_case(ax, ay, b)
        except Exception:
            ux = uy = phi = math.nan
        elapsed = time.perf_counter() - start
        rows.append(
            {
                "Ay": ay,
                "Ax": ax,
                "B": b,
                "ux": ux,
                "uy": uy,
                "phi": phi,
                "t": elapsed,
            }
        )
        if index == 1 or index % progress_step == 0 or index == len(load_cases):
            print(f"[{model_label}] {index}/{len(load_cases)}")
    return rows


def build_bvp_rows(load_cases):
    solver = EulerBvpBatchRunner(w=W_NORM)
    ordered_cases = sorted(
        load_cases,
        key=lambda row: (
            abs(row["Ay"]),
            abs(row["Ax"]),
            abs(row["B"]),
            row["Ay"],
            row["Ax"],
            row["B"],
        ),
    )

    solved = {}
    for index, load_case in enumerate(ordered_cases, start=1):
        ay = load_case["Ay"]
        ax = load_case["Ax"]
        b = load_case["B"]
        start = time.perf_counter()
        ux, uy, phi = solver.solve(ax, ay, b)
        elapsed = time.perf_counter() - start
        solved[preset_key(ay, ax, b)] = {
            "Ay": ay,
            "Ax": ax,
            "B": b,
            "ux": ux,
            "uy": uy,
            "phi": phi,
            "t": elapsed,
        }
        if index == 1 or index % 25 == 0 or index == len(ordered_cases):
            print(f"[Euler BVP] {index}/{len(ordered_cases)}")

    return [solved[preset_key(row["Ay"], row["Ax"], row["B"])] for row in load_cases]


def main():
    ensure_preset_data_dir()
    load_cases = validate_identical_fea_loads()
    print(f"Validated shared FEA load grid: {len(load_cases)} cases")

    copy_fea_presets()
    print("Copied normalized FEA sweeps into comparison/preset_data")

    model_specs = [
        ("linear", "Linear", run_linear, 250),
        ("bcm", "BCM", run_bcm, 250),
        ("prb_standard", "PRB standard", run_prb_standard, 250),
        ("prb_optimized", "PRB optimized", run_prb_optimized, 250),
        ("guided_beam", "Guided Beam", run_guided, 250),
    ]

    for preset_key_name, model_label, run_case, progress_step in model_specs:
        print(f"Generating {model_label} preset CSV ...")
        rows = build_rows(model_label, load_cases, run_case, progress_step=progress_step)
        write_rows(PRESET_FILES[preset_key_name], rows)
        print(f"Wrote {PRESET_FILES[preset_key_name]}")

    print("Generating Euler BVP preset CSV ...")
    bvp_rows = build_bvp_rows(load_cases)
    write_rows(PRESET_FILES["euler_bvp"], bvp_rows)
    print(f"Wrote {PRESET_FILES['euler_bvp']}")


if __name__ == "__main__":
    main()
