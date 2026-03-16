"""
Compare FEA 2D (beam elements) vs BCM (Awtar) for Parallelogram Flexure.

Sweep:  Ay in [-20, 20],  Ax in [-10, -5, 0, 5, 10],  M = 0
Geometry: L=250 mm, T=5 mm, H=50 mm, W=150 mm (full), E=210 GPa (Steel)
Normalised: w = W/(2L) = 0.30,  t = T/L = 0.02

Usage:
  python comparison/compare_fea2d_bcm.py  # use preset FEA 2D data then plot
"""

import argparse
import csv
import math
import os
import subprocess
import sys
import time

import numpy as np
from scipy.interpolate import interp1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from preset_catalog import PRESET_FILES

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE  = os.path.dirname(SCRIPT_DIR)
FREECAD    = r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe"

FEA_2D_SCRIPT   = os.path.join(WORKSPACE, "fea_models", "2d", "parallelogram_2d.py")
DATA_CSV        = PRESET_FILES["fea_2d"]
LIVE_DATA_CSV   = os.path.join(SCRIPT_DIR, "fea2d_sweep_data.csv")
LOAD_CASES_CSV  = os.path.join(SCRIPT_DIR, "fea2d_sweep_cases.csv")
OUTPUT_PNG          = os.path.join(SCRIPT_DIR, "compare_fea2d_bcm.png")
OUTPUT_ERR_PNG      = os.path.join(SCRIPT_DIR, "compare_fea2d_bcm_error.png")
OUTPUT_ZOOM_PNG     = os.path.join(SCRIPT_DIR, "compare_fea2d_bcm_zoomed.png")
OUTPUT_ZOOM_ERR_PNG = os.path.join(SCRIPT_DIR, "compare_fea2d_bcm_error_zoomed.png")

# ── Model parameters ───────────────────────────────────────────────────────
W_NORM = 0.30   # w = (W/2) / L  = 75 / 250
T_NORM = 0.02   # t = T / L      =  5 / 250

# ── Load parameters ────────────────────────────────────────────────────────
AX_SAMPLES = [-10, -5, 0, 5, 10]
AY_FEA     = list(range(-20, 21, 2))   # every 2 units → 21 values per Ax
AY_FINE    = np.linspace(-20, 20, 200) # fine grid for BCM curves

# ── BCM solver ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(WORKSPACE, "bcm"))
from bcm_parallelogram import BCMParallelogram

_bcm = BCMParallelogram(w=W_NORM, t=T_NORM)


def bcm_solve(Ax, Ay):
    """Return (Ux, Uy, phi_deg) or (nan, nan, nan) on failure."""
    res = _bcm.solve(Ax, Ay, B=0)
    if not res.get("success", False):
        return np.nan, np.nan, np.nan
    Uy  = res["delta"]
    Ux  = -res["u1"]
    phi = math.degrees(res["phi"])   # → degrees for plotting
    return Ux, Uy, phi


# ── FEA data generation ────────────────────────────────────────────────────

def write_load_cases():
    """Write all (Ay, Ax, M=0) combinations to LOAD_CASES_CSV."""
    rows = []
    for ax in AX_SAMPLES:
        for ay in AY_FEA:
            rows.append((ay, ax, 0))
    with open(LOAD_CASES_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ay", "Ax", "M"])
        w.writerows(rows)
    print(f"Written {len(rows)} load cases → {LOAD_CASES_CSV}")
    return len(rows)


def run_fea_2d():
    """Run FEA 2D for all sweep cases; output → DATA_CSV."""
    n = write_load_cases()
    env = os.environ.copy()
    env["FEA_LOAD_CASES_CSV"] = LOAD_CASES_CSV
    env["FEA_OUTPUT_CSV"]     = LIVE_DATA_CSV

    print(f"Running FEA 2D for {n} cases — this may take several minutes …")
    t0 = time.time()
    result = subprocess.run(
        [FREECAD, FEA_2D_SCRIPT],
        capture_output=True, text=True, env=env
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print("FreeCAD stderr:\n", result.stderr[-3000:])
        raise RuntimeError(f"FreeCADCmd exited with code {result.returncode}")

    print(f"FEA 2D finished in {elapsed:.0f} s  →  {LIVE_DATA_CSV}")


# ── Load FEA results ────────────────────────────────────────────────────────

def load_fea_data(csv_path=DATA_CSV):
    """Return dict keyed by (Ax, Ay) → (Ux, Uy, phi_deg)."""
    data = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if float(row["B"]) != 0.0:
                continue
            ax  = float(row["Ax"])
            ay  = float(row["Ay"])
            Ux  = float(row["ux"])
            Uy  = float(row["uy"])
            phi = math.degrees(float(row["phi"]))  # rad → deg for plotting
            data[(ax, ay)] = (Ux, Uy, phi)
            if ay > 0.0:
                data[(ax, -ay)] = (Ux, -Uy, -phi)
    print(f"Loaded {len(data)} FEA rows from {csv_path}")
    return data


# ── Plotting ────────────────────────────────────────────────────────────────

def _ylim_with_margin(vals, margin=0.05):
    """Compute y-limits from a list of finite values with a fractional margin."""
    finite = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not finite:
        return None
    lo, hi = min(finite), max(finite)
    span = hi - lo if hi != lo else abs(hi) or 1.0
    return lo - margin * span, hi + margin * span


def make_comparison_plot(fea_data, output_path, ay_range=(-20, 20)):
    """4-panel plot: Uy, Ux, φ, displacement magnitude — BCM lines, FEA markers."""
    norm = matplotlib.colors.Normalize(vmin=-10, vmax=10)
    cmap = plt.cm.jet

    ay_fine = np.linspace(ay_range[0], ay_range[1], 500)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    ax_uy   = axes[0, 0]
    ax_ux   = axes[0, 1]
    ax_phi  = axes[1, 0]
    ax_umag = axes[1, 1]

    # Accumulate y-values per panel to compute tight limits afterwards
    yvals = {ax_uy: [], ax_ux: [], ax_phi: [], ax_umag: []}

    for Ax in AX_SAMPLES:
        color = cmap(norm(Ax))

        # ── BCM — smooth curves ─────────────────────────────
        bcm_Ux, bcm_Uy, bcm_phi, bcm_mag = [], [], [], []
        for Ay in ay_fine:
            ux, uy, phi = bcm_solve(Ax, Ay)
            bcm_Ux.append(ux)
            bcm_Uy.append(uy)
            bcm_phi.append(phi)
            bcm_mag.append(math.sqrt(ux**2 + uy**2) if not math.isnan(ux) else np.nan)

        ax_uy.plot(ay_fine, bcm_Uy,  '-', color=color, lw=2, alpha=0.85)
        ax_ux.plot(ay_fine, bcm_Ux,  '-', color=color, lw=2, alpha=0.85)
        ax_phi.plot(ay_fine, bcm_phi, '-', color=color, lw=2, alpha=0.85)
        ax_umag.plot(ay_fine, bcm_mag, '-', color=color, lw=2, alpha=0.85)
        yvals[ax_uy].extend(bcm_Uy);  yvals[ax_ux].extend(bcm_Ux)
        yvals[ax_phi].extend(bcm_phi); yvals[ax_umag].extend(bcm_mag)

        # ── FEA 2D — markers ────────────────────────────────
        # Collect as tuples so origin can be added and list stays sorted
        fea_pts = []
        for ay in sorted(AY_FEA):
            if ay < ay_range[0] or ay > ay_range[1]:
                continue
            key = (float(Ax), float(ay))
            if key not in fea_data:
                continue
            ux, uy, phi = fea_data[key]
            fea_pts.append((ay, ux, uy, phi, math.sqrt(ux**2 + uy**2)))
        # Always include undeflected origin (Ay=0, all zero)
        if not any(p[0] == 0 for p in fea_pts):
            fea_pts.append((0, 0.0, 0.0, 0.0, 0.0))
            fea_pts.sort(key=lambda p: p[0])
        fea_ay  = [p[0] for p in fea_pts]
        fea_Ux  = [p[1] for p in fea_pts]
        fea_Uy  = [p[2] for p in fea_pts]
        fea_phi = [p[3] for p in fea_pts]
        fea_mag = [p[4] for p in fea_pts]

        ax_uy.plot(fea_ay, fea_Uy,   'o', color=color, ms=5, alpha=0.95, mew=0)
        ax_ux.plot(fea_ay, fea_Ux,   'o', color=color, ms=5, alpha=0.95, mew=0)
        ax_phi.plot(fea_ay, fea_phi,  'o', color=color, ms=5, alpha=0.95, mew=0)
        ax_umag.plot(fea_ay, fea_mag, 'o', color=color, ms=5, alpha=0.95, mew=0)
        yvals[ax_uy].extend(fea_Uy);  yvals[ax_ux].extend(fea_Ux)
        yvals[ax_phi].extend(fea_phi); yvals[ax_umag].extend(fea_mag)

    # ── Axes decoration ─────────────────────────────────────
    for ax, xlabel, ylabel, title in [
        (ax_uy,   "Ay (normalised)", "Uy (normalised)",  "Transverse Displacement"),
        (ax_ux,   "Ay (normalised)", "Ux (normalised)",  "Axial Shortening"),
        (ax_phi,  "Ay (normalised)", "φ (degrees, CCW+)", "Stage Rotation"),
        (ax_umag, "Ay (normalised)", "|u| (normalised)", "Displacement Magnitude"),
    ]:
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlim(ay_range[0] - 0.5, ay_range[1] + 0.5)
        lim = _ylim_with_margin(yvals[ax])
        if lim:
            ax.set_ylim(*lim)
        ax.axhline(0, color="k", lw=0.5, alpha=0.4)
        ax.axvline(0, color="k", lw=0.5, alpha=0.4)

    # ── Legend ──────────────────────────────────────────────
    legend_handles = [
        Line2D([0], [0], color="k", lw=2,   label="BCM (line)"),
        Line2D([0], [0], color="k", lw=0, marker="o", ms=6, label="FEA 2D (markers)"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=2,
               bbox_to_anchor=(0.5, 0.96), fontsize=12, title="Model")

    # ── Colorbar for Ax ─────────────────────────────────────
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.9,
                        label="Normalised axial force (Ax)", pad=0.02)
    cbar.set_ticks(AX_SAMPLES)

    plt.suptitle(
        "FEA 2D (beam elements) vs BCM (Awtar)\n"
        "L=250 mm, T=5 mm, H=50 mm, W=150 mm, E=210 GPa (Steel), M=0",
        y=0.99, fontsize=13
    )
    plt.subplots_adjust(top=0.90, right=0.88, hspace=0.35, wspace=0.30)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved → {output_path}")
    plt.close()


def make_error_plot(fea_data, output_path, ay_range=(-20, 20)):
    """3-panel plot of relative errors: eUy, eUx, eφ vs Ay for each Ax.

    BCM is evaluated on a fine Ay grid; FEA is interpolated to the same grid
    so the error curves are smooth continuous lines.
    At Ay=0 the error is exactly 0 (both models agree at zero load); a point
    at (0, 0) is added to each curve so the curves pass through the origin.
    """
    norm = matplotlib.colors.Normalize(vmin=-10, vmax=10)
    cmap = plt.cm.jet

    # Fine grids on each side of zero; Ay=0 inserted explicitly as error=0
    AY_NEG = np.linspace(ay_range[0], -0.5, 300)
    AY_POS = np.linspace(0.5, ay_range[1], 300)
    AY_ERR = np.concatenate([AY_NEG, AY_POS])

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    ax_euy, ax_eux, ax_ephi = axes

    yvals = {ax_euy: [], ax_eux: [], ax_ephi: []}

    for Ax in AX_SAMPLES:
        color = cmap(norm(Ax))

        # ── Collect FEA sample points (excluding Ay=0) ──────
        fea_ay_s = sorted(ay for ay in AY_FEA
                          if (float(Ax), float(ay)) in fea_data and ay != 0)
        fUy_s  = [fea_data[(float(Ax), ay)][1]  for ay in fea_ay_s]
        fUx_s  = [fea_data[(float(Ax), ay)][0]  for ay in fea_ay_s]
        fphi_s = [fea_data[(float(Ax), ay)][2]  for ay in fea_ay_s]

        if len(fea_ay_s) < 3:
            continue

        # ── Cubic interpolants for FEA quantities ────────────
        interp_Uy  = interp1d(fea_ay_s, fUy_s,  kind="cubic", fill_value="extrapolate")
        interp_Ux  = interp1d(fea_ay_s, fUx_s,  kind="cubic", fill_value="extrapolate")
        interp_phi = interp1d(fea_ay_s, fphi_s, kind="cubic", fill_value="extrapolate")

        # ── BCM at fine grid; interpolated FEA at same grid ──
        eUy_fine, eUx_fine, ephi_fine = [], [], []
        for ay in AY_ERR:
            bUx, bUy, bphi = bcm_solve(Ax, float(ay))
            if math.isnan(bUy):
                eUy_fine.append(np.nan)
                eUx_fine.append(np.nan)
                ephi_fine.append(np.nan)
                continue
            fUy  = float(interp_Uy(ay))
            fUx  = float(interp_Ux(ay))
            fphi = float(interp_phi(ay))
            eUy_fine.append((bUy  - fUy)  / abs(fUy)  * 100 if fUy  != 0 else np.nan)
            eUx_fine.append((bUx  - fUx)  / abs(fUx)  * 100 if fUx  != 0 else np.nan)
            ephi_fine.append((bphi - fphi) / abs(fphi) * 100 if fphi != 0 else np.nan)

        # Insert error=0 at Ay=0 (both models agree at zero load)
        ay_full  = np.concatenate([AY_NEG, [0.0], AY_POS])
        eUy_full  = np.concatenate([eUy_fine[:len(AY_NEG)],  [0.0], eUy_fine[len(AY_NEG):]])
        eUx_full  = np.concatenate([eUx_fine[:len(AY_NEG)],  [0.0], eUx_fine[len(AY_NEG):]])
        ephi_full = np.concatenate([ephi_fine[:len(AY_NEG)], [0.0], ephi_fine[len(AY_NEG):]])

        label = f"Ax={Ax}"
        ax_euy.plot(ay_full,  eUy_full,  '-', color=color, lw=2, label=label)
        ax_eux.plot(ay_full,  eUx_full,  '-', color=color, lw=2)
        ax_ephi.plot(ay_full, ephi_full, '-', color=color, lw=2)
        yvals[ax_euy].extend(eUy_full.tolist());  yvals[ax_eux].extend(eUx_full.tolist())
        yvals[ax_ephi].extend(ephi_full.tolist())

        # ── Overlay FEA sample markers ───────────────────────
        ax_euy.plot(fea_ay_s,
                    [(bcm_solve(Ax, ay)[1] - fUy_s[i]) / abs(fUy_s[i]) * 100
                     for i, ay in enumerate(fea_ay_s)],
                    'o', color=color, ms=4, mew=0)

    for ax, title, ylabel in [
        (ax_euy,  "Transverse Displacement Uy", "Error (BCM − FEA) / |FEA|  (%)"),
        (ax_eux,  "Axial Shortening Ux",        "Error (BCM − FEA) / |FEA|  (%)"),
        (ax_ephi, "Stage Rotation φ",            "Error (BCM − FEA) / |FEA|  (%)"),
    ]:
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Ay (normalised)", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.axhline(0, color="k", lw=1, alpha=0.5)
        ax.axvline(0, color="k", lw=0.5, alpha=0.3)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlim(ay_range[0] - 0.5, ay_range[1] + 0.5)
        lim = _ylim_with_margin(yvals[ax])
        if lim:
            ax.set_ylim(*lim)

    ax_euy.legend(fontsize=9, loc="best")
    plt.suptitle(
        "BCM vs FEA 2D — Relative Error (%)\n"
        "L=250 mm, T=5 mm, H=50 mm, W=150 mm, E=210 GPa (Steel), M=0",
        y=1.01, fontsize=13
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved → {output_path}")
    plt.close()


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Compare FEA 2D vs BCM.")
    parser.add_argument(
        "--refresh-live-fea",
        action="store_true",
        help="Regenerate the local subset CSV instead of using comparison/preset_data.",
    )
    args = parser.parse_args()

    if args.refresh_live_fea:
        run_fea_2d()
        fea_data = load_fea_data(LIVE_DATA_CSV)
    else:
        if not os.path.exists(DATA_CSV):
            raise FileNotFoundError(f"Preset data CSV not found: {DATA_CSV}")
        fea_data = load_fea_data(DATA_CSV)

    # Full range: Ay ∈ [−20, 20]
    make_comparison_plot(fea_data, OUTPUT_PNG,          ay_range=(-20, 20))
    make_error_plot(     fea_data, OUTPUT_ERR_PNG,      ay_range=(-20, 20))

    # Zoomed range: Ay ∈ [−6, 6]
    make_comparison_plot(fea_data, OUTPUT_ZOOM_PNG,     ay_range=(-6, 6))
    make_error_plot(     fea_data, OUTPUT_ZOOM_ERR_PNG, ay_range=(-6, 6))

    print("Done.")


if __name__ == "__main__":
    main()
