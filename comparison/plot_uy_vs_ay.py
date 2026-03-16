"""Quick plot: Uy vs Ay in [0, 6] for Ax in {-5, 0, 5} — BCM lines + FEA markers."""

import csv
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from preset_catalog import PRESET_FILES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE  = os.path.dirname(SCRIPT_DIR)
DATA_CSV   = PRESET_FILES["fea_2d"]
OUTPUT_PNG = os.path.join(SCRIPT_DIR, "uy_vs_ay.png")

sys.path.insert(0, os.path.join(WORKSPACE, "bcm"))
from bcm_parallelogram import BCMParallelogram

_bcm = BCMParallelogram(w=0.30, t=0.02)

AX_LIST   = [-5, 0, 5]
AY_RANGE  = (0, 6)
COLORS    = {-5: "#e05c2e", 0: "#2e7de0", 5: "#2eac47"}

# ── Load FEA data ────────────────────────────────────────────────────────────
fea_data = {}
with open(DATA_CSV, newline="") as f:
    for row in csv.DictReader(f):
        if float(row["B"]) != 0.0:
            continue
        ax = float(row["Ax"])
        ay = float(row["Ay"])
        uy = float(row["uy"])
        fea_data[(ax, ay)] = uy
        if ay > 0.0:
            fea_data[(ax, -ay)] = -uy

# ── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))

ay_fine = np.linspace(AY_RANGE[0], AY_RANGE[1], 300)

for Ax in AX_LIST:
    color = COLORS[Ax]
    label = f"Ax = {Ax:+d}"

    # BCM — smooth line
    bcm_Uy = []
    for Ay in ay_fine:
        res = _bcm.solve(Ax, Ay, B=0)
        bcm_Uy.append(res["delta"] if res.get("success") else np.nan)
    ax.plot(ay_fine, bcm_Uy, '-', color=color, lw=2, label=f"BCM {label}")

    # FEA — markers for Ay in [0, 6]
    fea_ay, fea_Uy = [], []
    for Ay in range(0, 7, 2):        # 0, 2, 4, 6
        key = (float(Ax), float(Ay))
        if key in fea_data:
            fea_ay.append(Ay)
            fea_Uy.append(fea_data[key])
    ax.plot(fea_ay, fea_Uy, 'o', color=color, ms=7, mew=1.5,
            mec="white", label=f"FEA 2D {label}")

ax.set_xlabel("Ay (normalised)", fontsize=12)
ax.set_ylabel("Uy (normalised)", fontsize=12)
ax.set_title("Transverse Displacement — BCM vs FEA 2D\n"
             "L=250 mm, T=5 mm, H=50 mm, W=150 mm, E=210 GPa, M=0", fontsize=11)
ax.set_xlim(-0.2, 6.3)
ax.axhline(0, color="k", lw=0.5, alpha=0.4)
ax.axvline(0, color="k", lw=0.5, alpha=0.4)
ax.grid(True, linestyle=":", alpha=0.5)

# Legend: group BCM lines first, then FEA markers
handles, labels = ax.get_legend_handles_labels()
bcm_h = [(h, l) for h, l in zip(handles, labels) if "BCM" in l]
fea_h = [(h, l) for h, l in zip(handles, labels) if "FEA" in l]
ordered = bcm_h + fea_h
ax.legend([h for h, _ in ordered], [l for _, l in ordered],
          fontsize=9, ncol=2, loc="upper left")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight")
print(f"Saved → {OUTPUT_PNG}")
