"""
Interactive comparison GUI for parallelogram flexure models.

Data sources:
- comparison/preset_data/*.csv
- fea_models/2d/parallelogram_2d.py
- fea_models/3d/parallelogram_3d_single.py
"""

import csv
import math
import os
import re
import subprocess
import sys
import tempfile
import warnings

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc
from matplotlib.widgets import Button, CheckButtons, Slider

warnings.filterwarnings("ignore")

try:
    from scipy.interpolate import LinearNDInterpolator

    SCIPY_AVAILABLE = True
except ImportError:
    LinearNDInterpolator = None
    SCIPY_AVAILABLE = False


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(SCRIPT_DIR))
COMPARISON_DIR = os.path.join(WORKSPACE, "comparison")

if COMPARISON_DIR not in sys.path:
    sys.path.insert(0, COMPARISON_DIR)

for sub in ("euler_beam", "guided_beam", "prb", "bcm"):
    path = os.path.join(WORKSPACE, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from bcm_parallelogram import BCMParallelogram
from guided_beam_solver import solve_guided_beam
from parallelogram_solver import ParallelogramFlexureSolver
from prb_parallelogram import PRBParallelogramModel
from preset_catalog import PRESET_FILES


L = 250.0
W = 150.0
T = 5.0
H = 50.0
E_GPA = 210.0

FEA_2D_SWEEP = PRESET_FILES["fea_2d"]
FEA_3D_SWEEP = PRESET_FILES["fea_3d"]
ANALYTICAL_SWEEPS = {
    "BVP": PRESET_FILES["euler_bvp"],
    "Guided": PRESET_FILES["guided_beam"],
    "PRB Orig": PRESET_FILES["prb_standard"],
    "PRB Opt": PRESET_FILES["prb_optimized"],
    "BCM": PRESET_FILES["bcm"],
    "Linear": PRESET_FILES["linear"],
}
FEA_2D_SCRIPT = os.path.join(WORKSPACE, "fea_models", "2d", "parallelogram_2d.py")
FEA_3D_SCRIPT = os.path.join(WORKSPACE, "fea_models", "3d", "parallelogram_3d_single.py")

FREECAD_CANDIDATES = [
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
    r"C:\Program Files (x86)\FreeCAD 1.0\bin\FreeCADCmd.exe",
]


def find_freecad_cmd():
    for path in FREECAD_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


FREECAD_CMD = find_freecad_cmd()
FREECAD_AVAILABLE = FREECAD_CMD is not None


def load_normalized_rows(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    records = []
    for row in rows:
        ux = float(row["ux"])
        uy = float(row["uy"])
        phi_deg = math.degrees(float(row["phi"]))
        solve_t = float(row["t"])
        success = all(np.isfinite([ux, uy, phi_deg]))
        record = {
            "Ax": float(row["Ax"]),
            "Ay": float(row["Ay"]),
            "B": float(row["B"]),
            "ux": ux,
            "uy": uy,
            "phi": phi_deg,
            "t": solve_t,
            "success": success,
        }
        records.append(record)
        if record["Ay"] > 0.0:
            records.append(
                {
                    "Ax": record["Ax"],
                    "Ay": -record["Ay"],
                    "B": -record["B"],
                    "ux": record["ux"],
                    "uy": -record["uy"],
                    "phi": -record["phi"],
                    "t": record["t"],
                    "success": success,
                }
            )
    return records


class SweepDatabase:
    def __init__(self, csv_path, label):
        self.label = label
        self.records = load_normalized_rows(csv_path)
        self.exact = {
            (round(r["Ax"], 6), round(r["Ay"], 6), round(r["B"], 6)): r for r in self.records
        }
        self.points = np.array([[r["Ax"], r["Ay"], r["B"]] for r in self.records], dtype=float)
        self.ux = np.array([r["ux"] for r in self.records], dtype=float)
        self.uy = np.array([r["uy"] for r in self.records], dtype=float)
        self.phi = np.array([r["phi"] for r in self.records], dtype=float)
        self.t = np.array([r["t"] for r in self.records], dtype=float)
        if SCIPY_AVAILABLE:
            self.ux_interp = LinearNDInterpolator(self.points, self.ux)
            self.uy_interp = LinearNDInterpolator(self.points, self.uy)
            self.phi_interp = LinearNDInterpolator(self.points, self.phi)
            self.t_interp = LinearNDInterpolator(self.points, self.t)

    def query(self, ax, ay, b):
        key = (round(ax, 6), round(ay, 6), round(b, 6))
        if key in self.exact:
            result = dict(self.exact[key])
            result["source"] = f"{self.label} exact"
            return result

        if SCIPY_AVAILABLE:
            point = np.array([[ax, ay, b]], dtype=float)
            ux = float(self.ux_interp(point)[0])
            uy = float(self.uy_interp(point)[0])
            phi = float(self.phi_interp(point)[0])
            t_s = float(self.t_interp(point)[0])
            if all(np.isfinite([ux, uy, phi, t_s])):
                return {
                    "Ax": ax,
                    "Ay": ay,
                    "B": b,
                    "ux": ux,
                    "uy": uy,
                    "phi": phi,
                    "t": t_s,
                    "success": True,
                    "source": f"{self.label} interpolated",
                }

        idx = int(np.argmin(np.sum((self.points - np.array([ax, ay, b])) ** 2, axis=1)))
        result = dict(self.records[idx])
        result["source"] = f"{self.label} nearest"
        return result

    def query_exact(self, ax, ay, b):
        key = (round(ax, 6), round(ay, 6), round(b, 6))
        if key not in self.exact:
            return None
        result = dict(self.exact[key])
        result["source"] = f"{self.label} exact"
        return result


def run_live_fea_2d(ax, ay, b):
    with tempfile.TemporaryDirectory(prefix="para_2d_live_") as temp_dir:
        input_csv = os.path.join(temp_dir, "single_case_input.csv")
        output_csv = os.path.join(temp_dir, "single_case_output.csv")
        with open(input_csv, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["Ay", "Ax", "M"])
            writer.writeheader()
            writer.writerow({"Ay": ay, "Ax": ax, "M": b})

        env = os.environ.copy()
        env["FEA_LOAD_CASES_CSV"] = input_csv
        env["FEA_OUTPUT_CSV"] = output_csv

        result = subprocess.run(
            [FREECAD_CMD, FEA_2D_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(FEA_2D_SCRIPT),
            env=env,
        )
        if result.returncode != 0 or not os.path.exists(output_csv):
            raise RuntimeError((result.stdout + result.stderr)[-1000:])

        with open(output_csv, "r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        row = rows[-1]
        return {
            "ux": float(row["Ux"]),
            "uy": float(row["Uy"]),
            "phi": math.degrees(float(row["phi"])),
            "t": float(row["t"]),
            "success": True,
            "source": "2D FEA live",
        }


def run_live_fea_3d(ax, ay, b):
    env = os.environ.copy()
    env["FEA_AX"] = str(ax)
    env["FEA_AY"] = str(ay)
    env["FEA_M"] = str(b)

    result = subprocess.run(
        [FREECAD_CMD, FEA_3D_SCRIPT],
        capture_output=True,
        text=True,
        timeout=900,
        cwd=os.path.dirname(FEA_3D_SCRIPT),
        env=env,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise RuntimeError(output[-1200:])

    ux = uy = phi_rad = solve_t = None
    for line in output.splitlines():
        match = re.search(r"Ux\s*=\s*x/L\s*=\s*([-\d.eE+]+)", line)
        if match:
            ux = float(match.group(1))
        match = re.search(r"Uy\s*=\s*y/L\s*=\s*([-\d.eE+]+)", line)
        if match:
            uy = float(match.group(1))
        match = re.search(r"phi\s*=\s*([-\d.eE+]+)\s*rad", line)
        if match:
            phi_rad = float(match.group(1))
        match = re.search(r"Times:\s*mesh=[-\d.eE+]+s\s+solve=([-\d.eE+]+)s", line)
        if match:
            solve_t = float(match.group(1))
    if None in (ux, uy, phi_rad):
        raise RuntimeError(output[-1200:])

    return {
        "ux": ux,
        "uy": uy,
        "phi": math.degrees(phi_rad),
        "t": solve_t if solve_t is not None else math.nan,
        "success": True,
        "source": "3D FEA live",
    }


class ModelComparison:
    def __init__(self):
        self.fea_2d_db = SweepDatabase(FEA_2D_SWEEP, "2D sweep")
        self.fea_3d_db = SweepDatabase(FEA_3D_SWEEP, "3D sweep")
        self.preset_dbs = {
            label: SweepDatabase(path, f"{label} preset") for label, path in ANALYTICAL_SWEEPS.items()
        }
        self.bvp_solver = ParallelogramFlexureSolver(w=0.3)
        self.prb_original = PRBParallelogramModel(w=0.3)
        self.prb_optimized = PRBParallelogramModel(w=0.3)
        self.prb_optimized.gamma = 0.90
        self.prb_optimized.K_theta_coeff = 2.5
        self.bcm_model = BCMParallelogram(w=0.3, t=0.02)

        self.Ax = 0.0
        self.Ay = 5.0
        self.B = 0.0
        self.w = 0.3
        self.fea_2d_live = None
        self.fea_3d_live = None
        self.fea_running = False
        self.visible_models = {
            "FEA 3D": True,
            "FEA 2D": True,
            "BVP": True,
            "Guided": True,
            "PRB Orig": True,
            "PRB Opt": True,
            "BCM": True,
            "Linear": True,
        }

        self.colors = {
            "bg": "#1a1a2e",
            "plot_bg": "#16213e",
            "fea3d": "#e94560",
            "fea2d": "#ff9f1c",
            "bvp": "#00ff88",
            "guided": "#9b59b6",
            "prb_orig": "#f1c40f",
            "prb_opt": "#ff6b35",
            "bcm": "#00d4ff",
            "linear": "#888888",
            "slider_bg": "#0f3460",
        }

        self.setup_gui()
        self.update(None)

    def setup_gui(self):
        self.fig = plt.figure(figsize=(16, 11))
        self.fig.patch.set_facecolor(self.colors["bg"])
        self.fig.canvas.manager.set_window_title("Parallelogram Flexure Model Comparison")

        self.ax_shape = self.fig.add_axes([0.04, 0.33, 0.52, 0.62])
        self.ax_shape.set_facecolor(self.colors["plot_bg"])
        self.ax_shape.set_aspect("equal")
        self.ax_shape.set_title("Normalized Deformed Shape Comparison", color="white", fontsize=12)

        self.lines = {
            "FEA 3D": self._create_mechanism_lines(self.colors["fea3d"], "-", 3.0, "FEA 3D"),
            "FEA 2D": self._create_mechanism_lines(self.colors["fea2d"], "-", 2.2, "FEA 2D"),
            "BVP": self._create_mechanism_lines(self.colors["bvp"], "--", 2.0, "BVP"),
            "Guided": self._create_mechanism_lines(self.colors["guided"], "-.", 2.0, "Guided"),
            "PRB Orig": self._create_mechanism_lines(self.colors["prb_orig"], "-", 1.7, "PRB Original"),
            "PRB Opt": self._create_mechanism_lines(self.colors["prb_opt"], "-", 1.7, "PRB Optimized"),
            "BCM": self._create_mechanism_lines(self.colors["bcm"], "--", 1.5, "BCM"),
            "Linear": self._create_mechanism_lines(self.colors["linear"], ":", 1.5, "Linear"),
        }

        legend = self.ax_shape.legend(loc="upper left", fontsize=8, facecolor=self.colors["plot_bg"], edgecolor="white")
        for text in legend.get_texts():
            text.set_color("white")
        for spine in self.ax_shape.spines.values():
            spine.set_color("white")
        self.ax_shape.tick_params(colors="white")
        self.ax_shape.grid(True, linestyle=":", alpha=0.3, color="white")
        self.ax_shape.axvline(x=0, color="gray", linestyle="-", alpha=0.5)
        self.ax_shape.annotate("", xy=(1.0, -0.55), xytext=(0.0, -0.55), arrowprops=dict(arrowstyle="<->", color="white", lw=1.2))
        self.ax_shape.text(0.5, -0.48, "L = 1", color="white", ha="center", fontsize=9)
        self.ax_shape.annotate("", xy=(-0.08, 0.3), xytext=(-0.08, -0.3), arrowprops=dict(arrowstyle="<->", color="white", lw=1.2))
        self.ax_shape.text(-0.15, 0.0, "2w", color="white", ha="center", va="center", fontsize=9, rotation=90)

        self.Ay_arrow = self.ax_shape.annotate("", xy=(1.0, 0.15), xytext=(1.0, 0.0), arrowprops=dict(arrowstyle="->", color="#f1c40f", lw=2))
        self.Ax_arrow = self.ax_shape.annotate("", xy=(1.12, 0.0), xytext=(1.0, 0.0), arrowprops=dict(arrowstyle="->", color="#00d4ff", lw=2))
        self.B_arc = Arc((1.0, 0.0), 0.10, 0.10, angle=0, theta1=-135, theta2=135, color="#9b59b6", lw=2)
        self.ax_shape.add_patch(self.B_arc)
        self.B_arrow = self.ax_shape.annotate("", xy=(1.035, 0.035), xytext=(1.025, 0.020), arrowprops=dict(arrowstyle="->", color="#9b59b6", lw=2))

        self.ax_table = self.fig.add_axes([0.58, 0.31, 0.40, 0.45])
        self.ax_table.set_facecolor(self.colors["plot_bg"])
        self.ax_table.axis("off")
        self.text_table = self.ax_table.text(0.01, 0.99, "", color="white", fontsize=7.5, va="top", fontfamily="monospace")

        self.ax_notes = self.fig.add_axes([0.58, 0.84, 0.40, 0.11])
        self.ax_notes.set_facecolor(self.colors["plot_bg"])
        self.ax_notes.axis("off")
        self.text_notes = self.ax_notes.text(0.01, 0.98, "", color="white", fontsize=8.6, va="top", fontfamily="monospace")

        toggle_left = self.fig.add_axes([0.58, 0.77, 0.18, 0.06])
        toggle_right = self.fig.add_axes([0.79, 0.77, 0.19, 0.06])
        self._style_toggle_axes(toggle_left)
        self._style_toggle_axes(toggle_right)
        self.toggle_group_left = CheckButtons(toggle_left, ["FEA 3D", "FEA 2D", "BVP", "Guided"], [True, True, True, True])
        self.toggle_group_right = CheckButtons(toggle_right, ["PRB Orig", "PRB Opt", "BCM", "Linear"], [True, True, True, True])
        self._style_checkbuttons(self.toggle_group_left)
        self._style_checkbuttons(self.toggle_group_right)
        self.toggle_group_left.on_clicked(self.toggle_model_visibility)
        self.toggle_group_right.on_clicked(self.toggle_model_visibility)

        slider_left = 0.08
        slider_width = 0.40
        self.slider_ay = Slider(self.fig.add_axes([slider_left, 0.23, slider_width, 0.03]), "Ay", -20.0, 20.0, valinit=self.Ay, color=self.colors["fea3d"])
        self.slider_ax = Slider(self.fig.add_axes([slider_left, 0.18, slider_width, 0.03]), "Ax", -10.0, 10.0, valinit=self.Ax, color=self.colors["bcm"])
        self.slider_b = Slider(self.fig.add_axes([slider_left, 0.13, slider_width, 0.03]), "B", -3.0, 3.0, valinit=self.B, color=self.colors["prb_orig"])
        self.slider_w = Slider(self.fig.add_axes([slider_left, 0.08, slider_width, 0.03]), "w", 0.1, 0.5, valinit=self.w, color=self.colors["guided"])
        for slider in (self.slider_ay, self.slider_ax, self.slider_b, self.slider_w):
            slider.label.set_color("white")
            slider.valtext.set_color("white")
            slider.on_changed(self.update)

        self.reset_btn = Button(
            self.fig.add_axes([0.58, 0.24, 0.09, 0.04]),
            "Reset",
            color=self.colors["slider_bg"],
            hovercolor="0.4",
        )
        self.reset_btn.label.set_color("white")
        self.reset_btn.on_clicked(self.reset)

        btn_color_2d = self.colors["fea2d"] if FREECAD_AVAILABLE else "#555555"
        btn_color_3d = self.colors["fea3d"] if FREECAD_AVAILABLE else "#555555"
        self.run_2d_btn = Button(
            self.fig.add_axes([0.69, 0.24, 0.10, 0.04]),
            "Run 2D",
            color=btn_color_2d,
            hovercolor="0.5",
        )
        self.run_3d_btn = Button(
            self.fig.add_axes([0.81, 0.24, 0.10, 0.04]),
            "Run 3D",
            color=btn_color_3d,
            hovercolor="0.6",
        )
        self.run_2d_btn.label.set_color("white")
        self.run_3d_btn.label.set_color("white")
        self.run_2d_btn.on_clicked(self.run_online_fea_2d)
        self.run_3d_btn.on_clicked(self.run_online_fea_3d)

        self.ax_status = self.fig.add_axes([0.58, 0.14, 0.33, 0.07])
        self.ax_status.set_facecolor(self.colors["plot_bg"])
        self.ax_status.axis("off")
        self.fea_status = self.ax_status.text(0.01, 0.98, "", color="white", fontsize=8.8, ha="left", va="top", fontfamily="monospace")
        if not FREECAD_AVAILABLE:
            self.fea_status.set_text("FreeCADCmd.exe not found")
            self.fea_status.set_color("#888888")

    def _create_mechanism_lines(self, color, linestyle, linewidth, label):
        line1, = self.ax_shape.plot([], [], linestyle, color=color, lw=linewidth, label=label)
        line2, = self.ax_shape.plot([], [], linestyle, color=color, lw=linewidth)
        line3, = self.ax_shape.plot([], [], linestyle, color=color, lw=linewidth)
        return line1, line2, line3

    def _style_toggle_axes(self, ax):
        ax.set_facecolor(self.colors["plot_bg"])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def _style_checkbuttons(self, widget):
        for label in widget.labels:
            label.set_color("white")
            label.set_fontsize(8)
        for rect in getattr(widget, "rectangles", []):
            rect.set_edgecolor("white")
            rect.set_facecolor(self.colors["plot_bg"])
        for pair in getattr(widget, "lines", []):
            for line in pair:
                line.set_color("white")

    def toggle_model_visibility(self, label):
        self.visible_models[label] = not self.visible_models[label]
        self.update(None)

    def reset(self, event):
        self.slider_ay.reset()
        self.slider_ax.reset()
        self.slider_b.reset()
        self.slider_w.reset()

    def set_status(self, text, color="white"):
        self.fea_status.set_text(text)
        self.fea_status.set_color(color)
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.01)

    def _compute_results(self):
        ax = float(np.clip(self.Ax, -10.0, 10.0))
        ay = float(np.clip(self.Ay, -20.0, 20.0))
        b = float(np.clip(self.B, -3.0, 3.0))
        results = {
            "FEA 3D": dict(self.fea_3d_live) if self.fea_3d_live else self.fea_3d_db.query(ax, ay, b),
            "FEA 2D": dict(self.fea_2d_live) if self.fea_2d_live else self.fea_2d_db.query(ax, ay, b),
        }

        try:
            preset = self.preset_dbs["BVP"].query_exact(ax, ay, b)
            if preset is not None:
                results["BVP"] = preset
            else:
                self.bvp_solver.w = self.w
                if self.bvp_solver.solve(A_x=ax, A_y=ay, B=b):
                    summary = self.bvp_solver.get_results_summary()
                    results["BVP"] = {
                        "ux": summary["platform"]["X_p"] - 1.0,
                        "uy": summary["platform"]["Y_p"],
                        "phi": summary["platform"]["phi_deg"],
                        "success": True,
                        "source": "BVP live",
                    }
                else:
                    results["BVP"] = {"success": False}
        except Exception:
            results["BVP"] = {"success": False}

        try:
            preset = self.preset_dbs["Guided"].query_exact(ax, ay, b)
            if preset is not None:
                results["Guided"] = preset
            else:
                _, x, y, _, _, _, success = solve_guided_beam(ax / 2.0, ay / 2.0)
                results["Guided"] = {
                    "ux": x[-1] - 1.0,
                    "uy": y[-1],
                    "phi": 0.0,
                    "success": success,
                    "source": "Guided live",
                }
        except Exception:
            results["Guided"] = {"success": False}

        try:
            preset = self.preset_dbs["PRB Orig"].query_exact(ax, ay, b)
            if preset is not None:
                results["PRB Orig"] = preset
            else:
                delta, ux, phi, _ = self.prb_original.solve(ay)
                results["PRB Orig"] = {
                    "ux": ux,
                    "uy": delta,
                    "phi": math.degrees(phi),
                    "success": True,
                    "source": "PRB standard live",
                }
        except Exception:
            results["PRB Orig"] = {"success": False}

        try:
            preset = self.preset_dbs["PRB Opt"].query_exact(ax, ay, b)
            if preset is not None:
                results["PRB Opt"] = preset
            else:
                delta, ux, phi, _ = self.prb_optimized.solve(ay)
                results["PRB Opt"] = {
                    "ux": ux,
                    "uy": delta,
                    "phi": math.degrees(phi),
                    "success": True,
                    "source": "PRB optimized live",
                }
        except Exception:
            results["PRB Opt"] = {"success": False}

        try:
            preset = self.preset_dbs["BCM"].query_exact(ax, ay, b)
            if preset is not None:
                results["BCM"] = preset
            else:
                self.bcm_model.w = self.w
                bcm = self.bcm_model.solve(ax, ay, b)
                if bcm.get("success"):
                    results["BCM"] = {
                        "ux": -bcm["u1"],
                        "uy": bcm["delta"],
                        "phi": math.degrees(bcm["phi"]),
                        "success": True,
                        "source": "BCM live",
                    }
                else:
                    results["BCM"] = {"success": False}
        except Exception:
            results["BCM"] = {"success": False}

        preset = self.preset_dbs["Linear"].query_exact(ax, ay, b)
        if preset is not None:
            results["Linear"] = preset
        else:
            results["Linear"] = {
                "ux": 0.0,
                "uy": ay / 24.0,
                "phi": 0.0,
                "success": True,
                "source": "Linear live",
            }
        return results

    def update(self, val):
        self.Ax = self.slider_ax.val
        self.Ay = self.slider_ay.val
        self.B = self.slider_b.val
        self.w = self.slider_w.val
        if val is not None:
            self.fea_2d_live = None
            self.fea_3d_live = None
            if FREECAD_AVAILABLE:
                self.set_status("")
        results = self._compute_results()
        self._update_shapes(results)
        self._update_table(results)
        self.fig.canvas.draw_idle()

    def _update_shapes(self, results):
        for name, lines in self.lines.items():
            result = results.get(name, {})
            is_visible = self.visible_models.get(name, True)
            for line in lines:
                line.set_visible(is_visible)
            if not is_visible or not result.get("success"):
                for line in lines:
                    line.set_data([], [])
                continue

            ux = result["ux"]
            uy = result["uy"]
            phi = math.radians(result["phi"])
            x_p = 1.0 + ux
            y_p = uy
            dx = self.w * math.sin(phi)
            dy = self.w * math.cos(phi)
            p_top = (x_p - dx, y_p + dy)
            p_bot = (x_p + dx, y_p - dy)

            s = np.linspace(0.0, 1.0, 60)
            x_beam = s + ux * (3 * s**2 - 2 * s**3)
            y_beam = uy * (3 * s**2 - 2 * s**3)
            lines[0].set_data(x_beam, y_beam + self.w)
            lines[1].set_data(x_beam, y_beam - self.w)
            lines[2].set_data([p_bot[0], p_top[0]], [p_bot[1], p_top[1]])

        max_uy = max([abs(r["uy"]) for r in results.values() if r.get("success")], default=0.3)
        y_limit = max(self.w + max_uy + 0.2, 0.6)
        self.ax_shape.set_xlim(-0.2, 1.55)
        self.ax_shape.set_ylim(-y_limit, y_limit)

        fea = results["FEA 3D"]
        px = 1.0 + fea["ux"]
        py = fea["uy"]
        self.Ay_arrow.xy = (px, py + 0.15)
        self.Ay_arrow.set_position((px, py))
        self.Ax_arrow.xy = (px + 0.12, py)
        self.Ax_arrow.set_position((px, py))
        self.B_arc.center = (px, py)
        self.B_arrow.xy = (px + 0.035, py + 0.035)
        self.B_arrow.set_position((px + 0.025, py + 0.020))

    def _update_table(self, results):
        ref = results["FEA 3D"]
        ref_label = ref.get("source", "FEA 3D")

        def fmt(v):
            return f"{v:+9.5f}" if np.isfinite(v) else "    N/A "

        def err(v, ref_val):
            if not np.isfinite(v) or not np.isfinite(ref_val) or abs(ref_val) < 1e-10:
                return "  N/A "
            return f"{(v / ref_val - 1.0) * 100:+6.1f}%"

        rows = [
            ("FEA3D", "FEA 3D"),
            ("FEA2D", "FEA 2D"),
            ("BVP", "BVP"),
            ("Guided", "Guided"),
            ("PRB-O", "PRB Orig"),
            ("PRB-X", "PRB Opt"),
            ("BCM", "BCM"),
            ("Linear", "Linear"),
        ]
        lines = [
            "PARALLELOGRAM FLEXURE MODEL COMPARISON",
            f"Ref: {ref_label}",
            f"Ax={self.Ax:+.2f}  Ay={self.Ay:+.2f}  B={self.B:+.2f}  w={self.w:.2f}",
            "",
            "Model      ux         uy       phi(deg)    ex%     ey%   ephi%",
            "---------------------------------------------------------------",
        ]
        for label, key in rows:
            if not self.visible_models.get(key, True):
                continue
            result = results.get(key, {})
            ux = result.get("ux", np.nan)
            uy = result.get("uy", np.nan)
            phi = result.get("phi", np.nan)
            if key == "FEA 3D":
                ex, ey, ep = " --- ", " --- ", " --- "
            else:
                ex = err(ux, ref.get("ux", np.nan))
                ey = err(uy, ref.get("uy", np.nan))
                ep = err(phi, ref.get("phi", np.nan))
            lines.append(f"{label:<8} {fmt(ux)} {fmt(uy)} {fmt(phi)} {ex:>7} {ey:>7} {ep:>7}")
        self.text_table.set_text("\n".join(lines))

        notes = [
            "LEGEND & NOTES",
            "",
            f"- Geometry: L={L:.0f}mm, T={T:.0f}mm, H={H:.0f}mm, W_half={W/2:.0f}mm",
            f"- Material: Steel, E={E_GPA:.0f}GPa",
            "- Loads: Ax = Fx*L^2/EI, Ay = Fy*L^2/EI, B = M*L/EI",
            "- CSV sweeps store normalized ux, uy directly",
            f"- FEA 3D source: {results['FEA 3D'].get('source', 'n/a')}",
            f"- FEA 2D source: {results['FEA 2D'].get('source', 'n/a')}",
            "- Exact preset loads use comparison/preset_data first",
            "- Negative Ay is mirrored from positive Ay by symmetry",
            "- Run 2D and Run 3D call the current FreeCAD solvers",
        ]
        self.text_notes.set_text("\n".join(notes))

    def _confirm(self, title, body):
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        ok = messagebox.askyesno(title, body)
        root.destroy()
        return ok

    def run_online_fea_2d(self, event):
        if not FREECAD_AVAILABLE or self.fea_running:
            return
        if not self._confirm("Run 2D FEA", f"Run live 2D FEA?\n\nAx={self.Ax:.2f}, Ay={self.Ay:.2f}, B={self.B:.2f}\n\nEstimated time: 1-3 seconds"):
            return
        self.fea_running = True
        self.set_status("2D FEA status\nrunning...", "#ffff00")
        try:
            self.fea_2d_live = run_live_fea_2d(self.Ax, self.Ay, self.B)
            self.set_status(
                "2D FEA status\n"
                "done\n"
                f"ux={self.fea_2d_live['ux']:+.5f}  uy={self.fea_2d_live['uy']:+.5f}\n"
                f"phi={self.fea_2d_live['phi']:+.3f} deg  t={self.fea_2d_live['t']:.2f}s",
                "#00ff88",
            )
        except Exception as exc:
            self.fea_2d_live = None
            self.set_status(f"2D FEA status\nfailed\n{str(exc)[:90]}", "#ff6666")
        finally:
            self.fea_running = False
            self.update(None)

    def run_online_fea_3d(self, event):
        if not FREECAD_AVAILABLE or self.fea_running:
            return
        if not self._confirm("Run 3D FEA", f"Run live 3D FEA?\n\nAx={self.Ax:.2f}, Ay={self.Ay:.2f}, B={self.B:.2f}\n\nEstimated time: 40-70 seconds"):
            return
        self.fea_running = True
        self.set_status("3D FEA status\nrunning...", self.colors["fea3d"])
        try:
            self.fea_3d_live = run_live_fea_3d(self.Ax, self.Ay, self.B)
            self.set_status(
                "3D FEA status\n"
                "done\n"
                f"ux={self.fea_3d_live['ux']:+.5f}  uy={self.fea_3d_live['uy']:+.5f}\n"
                f"phi={self.fea_3d_live['phi']:+.3f} deg  t={self.fea_3d_live['t']:.2f}s",
                "#00ff88",
            )
        except Exception as exc:
            self.fea_3d_live = None
            self.set_status(f"3D FEA status\nfailed\n{str(exc)[:90]}", "#ff6666")
        finally:
            self.fea_running = False
            self.update(None)

    def run(self):
        plt.show()


if __name__ == "__main__":
    ModelComparison().run()
