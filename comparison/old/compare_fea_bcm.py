
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import RectBivariateSpline
import warnings
warnings.filterwarnings('ignore')

# Add subdirectories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'bcm'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'fea_models', '2d_beam_dataset'))

# Import Solvers
from bcm_parallelogram import BCMParallelogram

# Define paths
DB_PATH = os.path.join(SCRIPT_DIR, 'fea_models', '2d_beam_dataset', '2d_beam_database_v2.csv')

# --- Model Wrappers ---

class FastFEAModel:
    """2D FEA database model using fast Spline interpolation."""
    def __init__(self, csv_path=DB_PATH):
        self.df = pd.read_csv(csv_path)
        self.name = "FEA (DB)"
        
        # Extract unique sorted axes
        self.ax_vals = np.sort(self.df['Ax'].unique())
        self.ay_vals = np.sort(self.df['Ay'].unique())
        
        # Pivot to create 2D grids (rows: Ay, cols: Ax)
        # Assuming the CSV covers the full grid. If not, this might fail or have NaNs.
        # pivot_table handles duplicates by aggregation (mean), though unique is expected.
        try:
            self.ux_grid = self.df.pivot_table(index='Ay', columns='Ax', values='ux').values
            self.uy_grid = self.df.pivot_table(index='Ay', columns='Ax', values='uy').values
            self.phi_grid = self.df.pivot_table(index='Ay', columns='Ax', values='phi').values
            
            # Create splines (x=Ay, y=Ax for RectBivariateSpline(x, y, z))
            # degree kx=3, ky=3 (cubic)
            self.spline_ux = RectBivariateSpline(self.ay_vals, self.ax_vals, self.ux_grid, kx=3, ky=3)
            self.spline_uy = RectBivariateSpline(self.ay_vals, self.ax_vals, self.uy_grid, kx=3, ky=3)
            self.spline_phi = RectBivariateSpline(self.ay_vals, self.ax_vals, self.phi_grid, kx=3, ky=3)
            
            print(f"FastFEAModel initialized with {len(self.df)} points.")
        except Exception as e:
            print(f"Error initializing FastFEAModel: {e}")
            raise

    def solve(self, Ax, Ay, B=0):
        # RectBivariateSpline(y, x) -> returns scalar
        # Check bounds? Spline treats out-of-bounds by extrapolation?
        # RegularGridInterpolator does extrapolation or NaN. 
        # RectBivariateSpline does extrapolation usually.
        # But for comparison, extrapolation outside the convex hull (-10, 10) is dangerous.
        # I should manually check bounds and return NaN if outside.
        
        if not (self.ax_vals[0] <= Ax <= self.ax_vals[-1]):
            val_nan = np.nan
            return {'ux': val_nan, 'uy': val_nan, 'phi': val_nan, 'u_mag': val_nan}
        
        if not (self.ay_vals[0] <= Ay <= self.ay_vals[-1]):
            val_nan = np.nan
            return {'ux': val_nan, 'uy': val_nan, 'phi': val_nan, 'u_mag': val_nan}

        ux = self.spline_ux(Ay, Ax)[0, 0]
        uy = self.spline_uy(Ay, Ax)[0, 0]
        phi = self.spline_phi(Ay, Ax)[0, 0]
        
        return {
            'ux': ux,
            'uy': uy,
            'phi': phi,
            'u_mag': np.sqrt(ux**2 + uy**2)
        }

class BCMModel:
    """Awtar's Beam Constraint Model."""
    def __init__(self, w=0.3, t=0.008):
        self.model = BCMParallelogram(w=w, t=t)
        self.name = "BCM"
    
    def solve(self, Ax, Ay, B=0):
        result = self.model.solve(Ax, Ay, B)
        if result.get('success', False):
            uy = result['delta']
            ux = -(result['u1'] + result['u2']) / 2.0
            phi = np.degrees(result['phi'])
            return {
                'ux': ux,
                'uy': uy,
                'phi': phi,
                'u_mag': np.sqrt(ux**2 + uy**2)
            }
        return {'ux': np.nan, 'uy': np.nan, 'phi': np.nan, 'u_mag': np.nan}

# --- Main Comparison Script ---


def plot_comparison(ay_range, output_filename, title_suffix="", axial_samples=None):
    # Parameters matching the system
    w = 0.3
    t = 0.008
    
    # Models
    try:
        fea_model = FastFEAModel()
    except:
        print("Failed to load FEA model. Aborting.")
        return

    bcm_model = BCMModel(w=w, t=t)
    
    # Sampling
    if axial_samples is None:
        Ax_samples = [-10, -5, 0, 5, 10]
    else:
        Ax_samples = axial_samples
        
    Ay_values = np.linspace(ay_range[0], ay_range[1], 100)
    B_val = 0.0 
    
    # Initialize plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    ax_uy = axes[0, 0]
    ax_ux = axes[0, 1]
    ax_phi = axes[1, 0]
    ax_umag = axes[1, 1]
    
    # Colormap: use a fixed range to keep colors consistent if desired, or auto-scale
    # Use -10 to 10 for consistency even if zoomed
    norm = matplotlib.colors.Normalize(vmin=-10, vmax=10)
    cmap = plt.cm.jet
    
    print(f"Generating {output_filename} with Ay range: {ay_range}, Ax: {Ax_samples}")
    
    for Ax in Ax_samples:
        color = cmap(norm(Ax))
        
        # Arrays
        res_fea = {'uy': [], 'ux': [], 'phi': [], 'u_mag': []}
        res_bcm = {'uy': [], 'ux': [], 'phi': [], 'u_mag': []}
        
        for Ay in Ay_values:
            # Solve FEA
            f = fea_model.solve(Ax, Ay, B=B_val)
            res_fea['uy'].append(f['uy'])
            res_fea['ux'].append(f['ux'])
            res_fea['phi'].append(f['phi'])
            res_fea['u_mag'].append(f['u_mag'])
            
            # Solve BCM
            b = bcm_model.solve(Ax, Ay, B=B_val)
            res_bcm['uy'].append(b['uy'])
            res_bcm['ux'].append(b['ux'])
            res_bcm['phi'].append(b['phi'])
            res_bcm['u_mag'].append(b['u_mag'])
            
        # Plotting
        # BCM: Line (solid)
        ax_uy.plot(Ay_values, res_bcm['uy'], '-', color=color, lw=1.5, alpha=0.8)
        ax_ux.plot(Ay_values, res_bcm['ux'], '-', color=color, lw=1.5, alpha=0.8)
        ax_phi.plot(Ay_values, res_bcm['phi'], '-', color=color, lw=1.5, alpha=0.8)
        ax_umag.plot(Ay_values, res_bcm['u_mag'], '-', color=color, lw=1.5, alpha=0.8)

        # FEA: Dots (distinct pattern)
        stride = 2
        ax_uy.plot(Ay_values[::stride], res_fea['uy'][::stride], 'o', color=color, markersize=3, alpha=0.9, markeredgewidth=0)
        ax_ux.plot(Ay_values[::stride], res_fea['ux'][::stride], 'o', color=color, markersize=3, alpha=0.9, markeredgewidth=0)
        ax_phi.plot(Ay_values[::stride], res_fea['phi'][::stride], 'o', color=color, markersize=3, alpha=0.9, markeredgewidth=0)
        ax_umag.plot(Ay_values[::stride], res_fea['u_mag'][::stride], 'o', color=color, markersize=3, alpha=0.9, markeredgewidth=0)

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
        ax.set_xlim(ay_range)
    
    # Global Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='k', lw=2, label='BCM (Line)'),
        Line2D([0], [0], color='k', marker='o', ls='None', markersize=6, label='FEA (Dots)'),
    ]
    leg1 = fig.legend(handles=legend_elements, loc='upper center', ncol=2, 
                      bbox_to_anchor=(0.5, 0.95), fontsize=12, title="Model Types")
    
    # Colorbar for Ax
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    # Filter ticks to show only used Ax values? Or standard ones.
    # Show standard ticks
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.9, label='Axial Force (Ax)')
    if axial_samples:
        cbar.set_ticks(sorted(list(set([-10, 0, 10] + axial_samples))))
    
    plt.suptitle(f"Comparison of BCM vs FEA Results {title_suffix}\nNote: FEA data interpolated", y=0.98, fontsize=14)
    
    # Adjust layout
    plt.subplots_adjust(top=0.90, right=0.85)

    plt.savefig(output_filename, dpi=300)
    print(f"Saved {output_filename}")

def run_comparison():
    # 1. Full Range, Ax=[-10, 10]
    plot_comparison((-20, 20), 'compare_fea_bcm.png', "(Full Range)")
    
    # 2. Zoomed Range, Ax=[-10, 10]
    plot_comparison((-6, 6), 'compare_fea_bcm_zoomed.png', "(Ay=[-6, 6])")
    
    # 3. Limited Ax Range [-5, 5] (Zoomed Ay)
    plot_comparison((-6, 6), 'compare_fea_bcm_Ax5.png', "(Ax=[-5, 5])", axial_samples=[-5, 0, 5])

if __name__ == "__main__":
    run_comparison()
