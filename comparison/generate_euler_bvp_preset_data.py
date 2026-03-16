import argparse
import csv
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

from preset_catalog import PRESET_FIELDNAMES, PRESET_FILES, preset_key, validate_identical_fea_loads


WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("euler_beam",):
    path = os.path.join(WORKSPACE, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from parallelogram_solver import ParallelogramFlexureSolver


W_NORM = 0.30


def parse_args():
    parser = argparse.ArgumentParser(description="Generate bounded-time Euler BVP preset data.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=300.0,
        help="Per-case timeout in seconds for the Euler BVP solve.",
    )
    parser.add_argument(
        "--output-csv",
        default=PRESET_FILES["euler_bvp"],
        help="Output CSV path.",
    )
    return parser.parse_args()


def load_existing_keys(csv_path):
    if not os.path.exists(csv_path):
        return set()
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return {
            preset_key(float(row["Ay"]), float(row["Ax"]), float(row["B"]))
            for row in reader
        }


def solve_bvp_case_worker(ax, ay, b, guess, queue):
    solver = ParallelogramFlexureSolver(w=W_NORM)
    ok = solver.solve(A_x=ax, A_y=ay, B=b, initial_guess=guess)
    if not ok:
        queue.put({"success": False})
        return
    queue.put(
        {
            "success": True,
            "ux": solver.X_p - 1.0,
            "uy": solver.Y_p,
            "phi": solver.phi,
            "guess": [
                solver.alpha_x1,
                solver.alpha_y1,
                solver.beta_1,
                solver.alpha_x2,
                solver.alpha_y2,
                solver.beta_2,
            ],
        }
    )


class TimedEulerBvpRunner:
    def __init__(self, timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.ctx = mp.get_context("spawn")
        self.guess_cache = {}

    def nearest_guess(self, ay, ax, b):
        best_guess = None
        best_dist = None
        for (row_ay, row_ax, row_b), guess in self.guess_cache.items():
            dist = abs(row_ay - ay) + abs(row_ax - ax) + 1.5 * abs(row_b - b)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_guess = guess
        return best_guess

    def solve(self, ax, ay, b):
        guess = self.nearest_guess(ay, ax, b)
        queue = self.ctx.Queue()
        proc = self.ctx.Process(target=solve_bvp_case_worker, args=(ax, ay, b, guess, queue))
        start = time.perf_counter()
        proc.start()
        proc.join(self.timeout_seconds)
        elapsed = time.perf_counter() - start

        if proc.is_alive():
            proc.terminate()
            proc.join()
            return {
                "Ay": ay,
                "Ax": ax,
                "B": b,
                "ux": math.nan,
                "uy": math.nan,
                "phi": math.nan,
                "t": elapsed,
            }

        if queue.empty():
            return {
                "Ay": ay,
                "Ax": ax,
                "B": b,
                "ux": math.nan,
                "uy": math.nan,
                "phi": math.nan,
                "t": elapsed,
            }

        result = queue.get()
        row = {
            "Ay": ay,
            "Ax": ax,
            "B": b,
            "ux": math.nan,
            "uy": math.nan,
            "phi": math.nan,
            "t": elapsed,
        }
        if result.get("success"):
            row["ux"] = result["ux"]
            row["uy"] = result["uy"]
            row["phi"] = result["phi"]
            self.guess_cache[preset_key(ay, ax, b)] = np.array(result["guess"], dtype=float)
        return row


def main():
    args = parse_args()
    load_cases = validate_identical_fea_loads()
    sorted_cases = sorted(
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

    output_csv = args.output_csv
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    runner = TimedEulerBvpRunner(timeout_seconds=args.timeout_seconds)
    existing_keys = load_existing_keys(output_csv)
    remaining_cases = [
        load_case
        for load_case in sorted_cases
        if preset_key(load_case["Ay"], load_case["Ax"], load_case["B"]) not in existing_keys
    ]
    mode = "a" if existing_keys else "w"
    print(
        f"Euler BVP timeout sweep: completed={len(existing_keys)} "
        f"remaining={len(remaining_cases)} timeout={args.timeout_seconds:.1f}s"
    )

    with open(output_csv, mode, encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PRESET_FIELDNAMES)
        if not existing_keys:
            writer.writeheader()
        for index, load_case in enumerate(remaining_cases, start=len(existing_keys) + 1):
            row = runner.solve(load_case["Ax"], load_case["Ay"], load_case["B"])
            writer.writerow(row)
            if (
                index == len(existing_keys) + 1
                or index % 25 == 0
                or index == len(sorted_cases)
            ):
                print(f"[Euler BVP timeout sweep] {index}/{len(sorted_cases)}")


if __name__ == "__main__":
    main()
