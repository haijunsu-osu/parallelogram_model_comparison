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

from preset_catalog import PRESET_FILES


FEA_3D_PRESET_PATH = Path(PRESET_FILES["fea_3d"])
MASTER_PRESET_PATH = COMPARISON_DIR / "preset_data" / "PARALLOGRAM_ALL_MODELS_master.csv"
B_TARGET = 0.0
AX_VALUES = [-10.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0]

PLOT_SPECS = [
    (
        "ux",
        r"$u_x$",
        "ux_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png",
        r"FEA 3D parasitic displacement $u_x$ vs. $\alpha_y$ "
        r"for varying $\alpha_x$ $(\beta = 0)$",
    ),
    (
        "uy",
        r"$u_y$",
        "uy_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png",
        r"FEA 3D transverse displacement $u_y$ vs. $\alpha_y$ "
        r"for varying $\alpha_x$ $(\beta = 0)$",
    ),
    (
        "phi",
        r"$\phi$ (rad)",
        "phi_vs_Ay_fea3d_Ax_neg10_to_pos10_B0.png",
        r"FEA 3D rotation $\phi$ vs. $\alpha_y$ "
        r"for varying $\alpha_x$ $(\beta = 0)$",
    ),
]

LINE_STYLES = {
    -10.0: ("#4b0000", "-", "o"),
    -5.0: ("#8b0000", "--", "s"),
    -4.0: ("#a61c00", "-.", "^"),
    -3.0: ("#c0392b", ":", "v"),
    -2.0: ("#d35400", (0, (5, 2)), "P"),
    -1.0: ("#e67e22", "-", "X"),
    0.0: ("#000000", "-", "D"),
    1.0: ("#2980b9", "-", "o"),
    2.0: ("#1f618d", "--", "s"),
    3.0: ("#16a085", "-.", "^"),
    4.0: ("#117864", ":", "v"),
    5.0: ("#1e8449", (0, (5, 2)), "P"),
    10.0: ("#145a32", "-", "X"),
}


def load_rows_by_ax():
    rows_by_ax = {ax: [] for ax in AX_VALUES}
    with FEA_3D_PRESET_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            ax = float(row["Ax"])
            ay = float(row["Ay"])
            b = float(row["B"])
            if not math.isclose(b, B_TARGET, rel_tol=0.0, abs_tol=1e-12):
                continue
            if ax not in rows_by_ax:
                continue
            rows_by_ax[ax].append(row)

    for ax in rows_by_ax:
        rows_by_ax[ax].sort(key=lambda row: float(row["Ay"]))
    return rows_by_ax


def load_linear_series():
    series = []
    seen_ay = set()
    with MASTER_PRESET_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            ay = float(row["Ay"])
            b = float(row["B"])
            if not math.isclose(b, B_TARGET, rel_tol=0.0, abs_tol=1e-12):
                continue
            if ay in seen_ay:
                continue
            seen_ay.add(ay)
            series.append(row)
    series.sort(key=lambda row: float(row["Ay"]))
    return series


def plot_metric(rows_by_ax, linear_rows, metric, ylabel, output_name, title):
    fig, ax = plt.subplots(figsize=(9.4, 6.2))

    for ax_value in AX_VALUES:
        series = rows_by_ax[ax_value]
        ay_values = [float(row["Ay"]) for row in series]
        metric_values = [float(row[metric]) for row in series]
        color, linestyle, marker = LINE_STYLES[ax_value]
        ax.plot(
            ay_values,
            metric_values,
            color=color,
            linestyle=linestyle,
            linewidth=2.4 if ax_value == 0.0 else 1.85,
            marker=marker,
            markersize=4.6,
            markerfacecolor=color if ax_value == 0.0 else "none",
            markeredgecolor=color,
            markeredgewidth=1.0,
            alpha=0.95,
            label=rf"$\alpha_x={ax_value:g}$",
        )

    linear_ay = [float(row["Ay"]) for row in linear_rows]
    linear_values = [float(row[f"{metric}_linear"]) for row in linear_rows]
    ax.plot(
        linear_ay,
        linear_values,
        color="#6c757d",
        linestyle=(0, (8, 3)),
        linewidth=2.6,
        marker=None,
        alpha=0.95,
        label="Linear beam",
    )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.legend(loc="best", fontsize=8.3, ncol=4, frameon=True)

    output_path = SCRIPT_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output_path}")


def main():
    rows_by_ax = load_rows_by_ax()
    linear_rows = load_linear_series()
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    for metric, ylabel, output_name, title in PLOT_SPECS:
        plot_metric(rows_by_ax, linear_rows, metric, ylabel, output_name, title)


if __name__ == "__main__":
    main()
