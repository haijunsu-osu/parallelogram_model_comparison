import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
COMPARISON_DIR = SCRIPT_DIR.parent

if str(COMPARISON_DIR) not in sys.path:
    sys.path.insert(0, str(COMPARISON_DIR))

from preset_catalog import MASTER_PRESET_CSV


MASTER_PRESET_PATH = Path(MASTER_PRESET_CSV)
OUTPUT_DIR = SCRIPT_DIR
AX_TARGET = -3.0
B_TARGET = 0.0

MODEL_SPECS = [
    ("FEA 3D", "fea3d", "#000000", "-", 2.8, "o", "#000000"),
    ("FEA 2D", "fea2d", "#4f5d75", "-", 2.2, "s", "none"),
    ("Euler BVP", "euler", "#1b9e77", "--", 2.0, "^", "#1b9e77"),
    ("Guided Beam", "guided", "#7b2cbf", "-.", 1.9, "D", "none"),
    ("PRB standard", "prb", "#c79200", ":", 1.9, "v", "none"),
    ("PRB optimized", "prb_opt", "#e36414", (0, (5, 2)), 1.9, "P", "#e36414"),
    ("BCM", "bcm", "#0077b6", "--", 1.9, ">", "none"),
    ("Linear", "linear", "#8d99ae", ":", 1.7, "x", "#8d99ae"),
]

PLOT_SPECS = [
    ("uy", r"$u_y$", "uy_vs_Ay_all_models_Ax_neg3_B0.png"),
    ("ux", r"$u_x$", "ux_vs_Ay_all_models_Ax_neg3_B0.png"),
    ("phi", r"$\phi$ (rad)", "phi_vs_Ay_all_models_Ax_neg3_B0.png"),
]

ERROR_PLOT_SPECS = [
    ("uy", r"Error in $u_y$ (%)", "uy_error_pct_vs_Ay_all_models_Ax_neg3_B0.png"),
    ("ux", r"Error in $u_x$ (%)", "ux_error_pct_vs_Ay_all_models_Ax_neg3_B0.png"),
    ("phi", r"Error in $\phi$ (%)", "phi_error_pct_vs_Ay_all_models_Ax_neg3_B0.png"),
]

ZOOM_PLOT_SPECS = [
    ("uy", r"$u_y$", "uy_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
    ("ux", r"$u_x$", "ux_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
    ("phi", r"$\phi$ (rad)", "phi_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
]

ZOOM_ERROR_PLOT_SPECS = [
    ("uy", r"Error in $u_y$ (%)", "uy_error_pct_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
    ("ux", r"Error in $u_x$ (%)", "ux_error_pct_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
    ("phi", r"Error in $\phi$ (%)", "phi_error_pct_vs_Ay_all_models_Ax_neg3_B0_zoom_0_to_5.png"),
]


def load_rows():
    with MASTER_PRESET_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = [
            row
            for row in csv.DictReader(fh)
            if math.isclose(float(row["Ax"]), AX_TARGET, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(float(row["B"]), B_TARGET, rel_tol=0.0, abs_tol=1e-12)
        ]
    rows.sort(key=lambda row: float(row["Ay"]))
    return rows


def plot_metric(rows, metric, ylabel, output_name):
    fig, ax = plt.subplots(figsize=(8.5, 5.8))

    ay_values = [float(row["Ay"]) for row in rows]
    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in rows:
            value = float(row[f"{metric}_{suffix}"])
            values.append(value if math.isfinite(value) else math.nan)
        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(
        rf"{ylabel} vs. $\alpha_y$ for all models "
        rf"$(\alpha_x = -3,\ \beta = 0)$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = OUTPUT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def plot_metric_zoom(rows, metric, ylabel, output_name, ay_max):
    zoom_rows = [row for row in rows if float(row["Ay"]) <= ay_max]
    fig, ax = plt.subplots(figsize=(8.5, 5.8))

    ay_values = [float(row["Ay"]) for row in zoom_rows]
    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in zoom_rows:
            value = float(row[f"{metric}_{suffix}"])
            values.append(value if math.isfinite(value) else math.nan)
        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(
        rf"{ylabel} vs. $\alpha_y$ for all models "
        rf"$(\alpha_x = -3,\ \beta = 0,\ 0 \leq \alpha_y \leq {ay_max:g})$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = OUTPUT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def relative_error_pct(value, reference):
    if not math.isfinite(value) or not math.isfinite(reference):
        return math.nan
    if math.isclose(reference, 0.0, rel_tol=0.0, abs_tol=1e-15):
        return math.nan
    return (value - reference) / abs(reference) * 100.0


def plot_error_metric(rows, metric, ylabel, output_name):
    fig, ax = plt.subplots(figsize=(8.5, 5.8))

    filtered_rows = rows
    if metric in {"uy", "phi"}:
        filtered_rows = [
            row
            for row in rows
            if not math.isclose(float(row["Ay"]), 0.0, rel_tol=0.0, abs_tol=1e-12)
        ]

    ay_values = [float(row["Ay"]) for row in filtered_rows]
    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in filtered_rows:
            if suffix == "fea3d":
                values.append(0.0)
                continue
            reference = float(row[f"{metric}_fea3d"])
            value = float(row[f"{metric}_{suffix}"])
            values.append(relative_error_pct(value, reference))
        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(
        rf"{ylabel} vs. $\alpha_y$ relative to FEA 3D "
        rf"$(\alpha_x = -3,\ \beta = 0)$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = OUTPUT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def plot_error_metric_zoom(rows, metric, ylabel, output_name, ay_max):
    zoom_rows = [row for row in rows if float(row["Ay"]) <= ay_max]
    fig, ax = plt.subplots(figsize=(8.5, 5.8))

    filtered_rows = zoom_rows
    if metric in {"uy", "phi"}:
        filtered_rows = [
            row
            for row in zoom_rows
            if not math.isclose(float(row["Ay"]), 0.0, rel_tol=0.0, abs_tol=1e-12)
        ]

    ay_values = [float(row["Ay"]) for row in filtered_rows]
    for label, suffix, color, linestyle, linewidth, marker, marker_face in MODEL_SPECS:
        values = []
        for row in filtered_rows:
            if suffix == "fea3d":
                values.append(0.0)
                continue
            reference = float(row[f"{metric}_fea3d"])
            value = float(row[f"{metric}_{suffix}"])
            values.append(relative_error_pct(value, reference))
        ax.plot(
            ay_values,
            values,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker,
            markersize=5.0 if suffix.startswith("fea") else 4.2,
            markerfacecolor=marker_face,
            markeredgecolor=color,
            markeredgewidth=1.1,
            alpha=0.95,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(
        rf"{ylabel} vs. $\alpha_y$ relative to FEA 3D "
        rf"$(\alpha_x = -3,\ \beta = 0,\ 0 \leq \alpha_y \leq {ay_max:g})$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.35)
    ax.set_xlim(min(ay_values), max(ay_values))
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    output_path = OUTPUT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def main():
    rows = load_rows()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for metric, ylabel, output_name in PLOT_SPECS:
        plot_metric(rows, metric, ylabel, output_name)
    for metric, ylabel, output_name in ERROR_PLOT_SPECS:
        plot_error_metric(rows, metric, ylabel, output_name)
    for metric, ylabel, output_name in ZOOM_PLOT_SPECS:
        plot_metric_zoom(rows, metric, ylabel, output_name, ay_max=5.0)
    for metric, ylabel, output_name in ZOOM_ERROR_PLOT_SPECS:
        plot_error_metric_zoom(rows, metric, ylabel, output_name, ay_max=5.0)


if __name__ == "__main__":
    main()
