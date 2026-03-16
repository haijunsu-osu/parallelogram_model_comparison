
import os
import sys
import json
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Add subdirectories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'bcm'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'fea_models', '2d_beam_dataset'))

# Import BCM
from bcm_parallelogram import BCMParallelogram

# Parameters
W = 0.3
T = 0.008  # T=2mm, L=250mm
L_mm = 250.0

# FreeCAD Detection
FREECAD_CMD = None
freecad_paths = [
    r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
    r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
    r"C:\Program Files (x86)\FreeCAD 1.0\bin\FreeCADCmd.exe",
]
for path in freecad_paths:
    if os.path.exists(path):
        FREECAD_CMD = path
        break

def run_online_fea(ax_samples, ay_range_max):
    """Run FEA simulation for specified Ax samples and Ay range."""
    if not FREECAD_CMD:
        print("FreeCAD not found. Cannot run online FEA.")
        return None

    fea_dir = os.path.join(SCRIPT_DIR, 'fea_models', '2d_beam_dataset')
    worker_script = os.path.join(fea_dir, 'fea_worker_2.py')
    config_path = os.path.join(fea_dir, 'temp_online_config.json')
    output_path = os.path.join(fea_dir, 'temp_online_results.json')
    
    # Configure simulation
    # ay_range_max should be positive (mag)
    # n_steps = int(ay_range_max) to get integer steps (assuming 1.0 spacing)
    n_steps = int(abs(ay_range_max))
    
    config = {
        "worker_id": "online_comparison",
        "ax_values": ax_samples,
        "ay_max_pos": float(ay_range_max),
        "ay_max_neg": -float(ay_range_max),
        "n_steps": n_steps,
        "output_file": output_path
    }
    
    print(f"Running FreeCAD simulation for Ax={ax_samples}, Ay +/-{ay_range_max}...")
    print(f"Steps per ramp: {n_steps}")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    try:
        # Run FreeCAD
        result = subprocess.run(
            [FREECAD_CMD, worker_script, config_path],
            capture_output=True,
            text=True,
            cwd=fea_dir,
            timeout=300 # 5 minutes timeout
        )
        
        if result.returncode != 0:
            print("FreeCAD Error:")
            print(result.stderr)
            return None
            
        print("Simulation completed.")
        
        # Load results
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                data = json.load(f)
            # Cleanup
            # os.remove(config_path)
            # os.remove(output_path)
            return data
        else:
            print("Output file not found.")
            return None
            
    except Exception as e:
        print(f"Error running simulation: {e}")
        return None

def process_fea_results(data):
    """Organize FEA results by Ax."""
    # Structure: {'ax_val': {'ay': [], 'ux': [], ...}}
    
    results = {}
    for entry in data:
        # Worker returns "Ax" and "Ay" (capitalized)
        ax_val = entry.get('Ax')
        if ax_val is None: continue
        
        # Round to avoid float mismatch
        ax_key = round(ax_val, 2)
        
        if ax_key not in results:
            results[ax_key] = {'ay': [], 'ux': [], 'uy': [], 'phi': [], 'u_mag': []}
            
        # Worker outputs "ux" and "uy" which are ALREADY normalized (Ux/L)
        # "phi" is in degrees
        
        ux_norm = entry.get('ux', 0.0)
        uy_norm = entry.get('uy', 0.0)
        phi_deg = entry.get('phi', 0.0)
        ay_norm = entry.get('Ay', 0.0)
        
        results[ax_key]['ay'].append(ay_norm)
        results[ax_key]['ux'].append(ux_norm)
        results[ax_key]['uy'].append(uy_norm)
        results[ax_key]['phi'].append(phi_deg)
            
    # Calculate mag and sort by ay
    import math
    for ax in results:
        # Sort by ay (since we have pos and neg ramps appended)
        arrays = sorted(zip(results[ax]['ay'], results[ax]['ux'], results[ax]['uy'], results[ax]['phi']))
        # Remove duplicates
        unique_arrays = []
        seen_ay = set()
        for v in arrays:
            ay_rounded = round(v[0], 4)
            if ay_rounded not in seen_ay:
                unique_arrays.append(v)
                seen_ay.add(ay_rounded)
        
        if not unique_arrays: continue
        ay, ux, uy, phi = zip(*unique_arrays)
        
        results[ax]['ay'] = np.array(ay)
        results[ax]['ux'] = np.array(ux)
        results[ax]['uy'] = np.array(uy)
        results[ax]['phi'] = np.array(phi)
        results[ax]['u_mag'] = np.sqrt(results[ax]['ux']**2 + results[ax]['uy']**2)
        
    return results

def run_comparison_online():
    # Parameters
    w = 0.3
    t = 0.008
    Ax_samples = [-5, 0, 5]
    Ay_max = 6.0
    
    # 1. Run Online FEA
    fea_raw_data = run_online_fea(Ax_samples, Ay_max)
    if not fea_raw_data:
        print("Aborting.")
        return

    fea_results = process_fea_results(fea_raw_data)
    
    # 2. Compute BCM (High Res)
    bcm_model = BCMParallelogram(w=w, t=t)
    Ay_hr = np.linspace(-Ay_max, Ay_max, 100)
    
    # 3. Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    ax_uy = axes[0, 0]
    ax_ux = axes[0, 1]
    ax_phi = axes[1, 0]
    ax_umag = axes[1, 1]
    
    norm = matplotlib.colors.Normalize(vmin=-5, vmax=5)
    cmap = plt.cm.jet
    
    print("Generating compare_fea_bcm_online.png...")
    
    for Ax in Ax_samples:
        color = cmap(norm(Ax))
        
        # BCM (Line)
        bcm_res = {'ay': [], 'ux': [], 'uy': [], 'phi': [], 'u_mag': []}
        for Ay in Ay_hr:
            res = bcm_model.solve(Ax, Ay, 0)
            if res['success']:
                ux = -(res['u1'] + res['u2']) / 2.0
                uy = res['delta']
                phi = np.degrees(res['phi'])
                bcm_res['ay'].append(Ay)
                bcm_res['ux'].append(ux)
                bcm_res['uy'].append(uy)
                bcm_res['phi'].append(phi)
                bcm_res['u_mag'].append(np.sqrt(ux**2 + uy**2))
        
        # Plot BCM
        ax_uy.plot(bcm_res['ay'], bcm_res['uy'], '-', color=color, lw=1.5, alpha=0.8)
        ax_ux.plot(bcm_res['ay'], bcm_res['ux'], '-', color=color, lw=1.5, alpha=0.8)
        ax_phi.plot(bcm_res['ay'], bcm_res['phi'], '-', color=color, lw=1.5, alpha=0.8)
        ax_umag.plot(bcm_res['ay'], bcm_res['u_mag'], '-', color=color, lw=1.5, alpha=0.8)
        
        # Plot FEA (Dots)
        if Ax in fea_results:
            fr = fea_results[Ax]
            # Use marker 'o', linestyle None
            ax_uy.plot(fr['ay'], fr['uy'], 'o', color=color, markersize=5, alpha=0.9, markeredgecolor='k', markeredgewidth=0.5)
            ax_ux.plot(fr['ay'], fr['ux'], 'o', color=color, markersize=5, alpha=0.9, markeredgecolor='k', markeredgewidth=0.5)
            # Scaling Phi? Worker might return degrees or radians. The processing function should handle it.
            # Assuming GUI uses same worker, let's assume it returns something needing conversion or not.
            # I added conversion logic in process_fea_results if 'phi_rad' key exists.
            ax_phi.plot(fr['ay'], fr['phi'], 'o', color=color, markersize=5, alpha=0.9, markeredgecolor='k', markeredgewidth=0.5)
            ax_umag.plot(fr['ay'], fr['u_mag'], 'o', color=color, markersize=5, alpha=0.9, markeredgecolor='k', markeredgewidth=0.5)

    # Decoration
    titles = [
        (ax_uy, 'Ay (Normalized)', 'uy (Normalized)', 'Transverse Displacement'),
        (ax_ux, 'Ay (Normalized)', 'ux (Normalized)', 'Axial Shortening'),
        (ax_phi, 'Ay (Normalized)', 'φ (degrees)', 'Stage Rotation'),
        (ax_umag, 'Ay (Normalized)', '|u| (Normalized)', 'Displacement Magnitude')
    ]
    
    for ax, xlab, ylab, title in titles:
        ax.set_xlabel(xlab)
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_xlim(-Ay_max, Ay_max)
    
    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='k', lw=2, label='BCM (Line)'),
        Line2D([0], [0], color='k', marker='o', ls='None', markersize=6, markeredgecolor='k', label='Online FEA (Dots)'),
    ]
    fig.legend(handles=legend_elements, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 0.95), fontsize=12)
    
    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.9, label='Axial Force (Ax)')
    cbar.set_ticks([-5, 0, 5])
    
    plt.suptitle("Comparison of BCM vs Online FEA Results\n(Real-time Simulation)", y=0.98, fontsize=14)
    plt.subplots_adjust(top=0.90, right=0.85)
    
    plt.savefig('compare_fea_bcm_online.png', dpi=300)
    print("Saved compare_fea_bcm_online.png")

if __name__ == "__main__":
    run_comparison_online()
