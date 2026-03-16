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
OUTPUT_PATH = SCRIPT_DIR / "uy_vs_Ay_fea3d_Ax_neg3_to_pos3_B0.png"
B_TARGET = 0.0
AX_VALUES = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]

LINE_SPECS = [
    (-3.0, "#8b0000", "-", "o", r"$\alpha_x=-3$"),
    (-2.0, "#c0392b", "--", "s", r"$\alpha_x=-2$"),
    (-1.0, "#e67e22", "-.", "^", r"$\alpha_x=-1$"),
    (0.0, "#000000", "-", "D", r"$\alpha_x=0$"),
    (1.0, "#2980b9", "-.", "v", r"$\alpha_x=1$"),
    (2.0, "#16a085", "--", "P", r"$\alpha_x=2$"),
    (3.0, "#1e8449", "-", "X", r"$\alpha_x=3$"),
]


def load_rows():
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
            uy = float(row["uy"])
            rows_by_ax[ax].append((ay, uy))

    for ax in rows_by_ax:
        rows_by_ax[ax].sort(key=lambda item: item[0])
    return rows_by_ax


def main():
    rows_by_ax = load_rows()

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    for ax_value, color, linestyle, marker, label in LINE_SPECS:
        series = rows_by_ax[ax_value]
        ay_values = [item[0] for item in series]
        uy_values = [item[1] for item in series]
        ax.plot(
            ay_values,
            uy_values,
            color=color,
            linestyle=linestyle,
            linewidth=2.2 if ax_value == 0.0 else 1.9,
            marker=marker,
            markersize=4.8,
            markerfacecolor="none" if ax_value != 0.0 else color,
            markeredgecolor=color,
            markeredgewidth=1.0,
            label=label,
        )

    ax.set_xlabel(r"$\alpha_y$", fontsize=12)
    ax.set_ylabel(r"$u_y$", fontsize=12)
    ax.set_title(
        r"FEA 3D transverse deflection $u_y$ vs. $\alpha_y$ "
        r"for $\alpha_x \in [-3,3]$ $(\beta = 0)$",
        fontsize=13,
    )
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.axvline(0.0, color="black", linewidth=0.7, alpha=0.35)
    ax.legend(loc="best", fontsize=9, ncol=2, frameon=True)

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
