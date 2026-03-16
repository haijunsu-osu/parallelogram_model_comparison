"""
Comparison of Parallelogram Flexure Models with 2D FEA as Ground Truth

Models Compared:
1. 2D FEA Beam Model (Ground Truth) - from simulation database
2. BVP Solver (Euler-Bernoulli nonlinear beam)
3. Guided Beam Model
4. PRB Model (Original: γ=0.8517, k_θ=2.67617)
5. PRB Model (Optimized: γ=0.90, k_θ=2.5)
6. BCM Model (Awtar's Beam Constraint Model)
7. Linear Beam Model

Output: ux, uy, φ, |u| for each model
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Add subdirectories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'euler_beam'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'guided_beam'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'prb'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'bcm'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'fea_models', '2d_beam_dataset'))

# Import Solvers
from parallelogram_solver import ParallelogramFlexureSolver
from guided_beam_solver import solve_guided_beam
from prb_parallelogram import PRBParallelogramModel
from bcm_parallelogram import BCMParallelogram
from fea_database_query import FEADatabase


# =============================================================================
# Model Wrappers (Unified Interface)
# =============================================================================

class FEAModel:
    """2D FEA database model (Ground Truth)."""
    def __init__(self):
        self.db = FEADatabase()
        self.name = "2D FEA (Ground Truth)"
    
    def solve(self, Ax, Ay, B=0):
        result = self.db.query(Ax, Ay, B)
        return {
            'ux': result['ux'],
            'uy': result['uy'],
            'phi': result['phi'],
            'u_mag': np.sqrt(result['ux']**2 + result['uy']**2)
        }


class BVPModel:
    """BVP solver for parallelogram (Euler-Bernoulli nonlinear)."""
    def __init__(self, w=0.3):
        self.solver = ParallelogramFlexureSolver(w=w)
        self.name = "BVP Solver"
    
    def solve(self, Ax, Ay, B=0):
        success = self.solver.solve(A_x=Ax, A_y=Ay, B=B)
        if success:
            res = self.solver.get_results_summary()
            ux = res['platform']['X_p'] - 1.0
            uy = res['platform']['Y_p']
            phi = res['platform']['phi_deg']
            return {
                'ux': ux,
                'uy': uy,
                'phi': phi,
                'u_mag': np.sqrt(ux**2 + uy**2)
            }
        return {'ux': np.nan, 'uy': np.nan, 'phi': np.nan, 'u_mag': np.nan}


class GuidedBeamModel:
    """Guided beam solver for parallelogram."""
    def __init__(self, w=0.3):
        self.w = w
        self.name = "Guided Beam"
    
    def solve(self, Ax, Ay, B=0):
        alpha_x = Ax / 2.0
        alpha_y = Ay / 2.0
        s, x, y, theta, kappa, beta, success = solve_guided_beam(alpha_x, alpha_y)
        if success:
            ux = x[-1] - 1.0
            uy = y[-1]
            phi = 0.0
            return {
                'ux': ux,
                'uy': uy,
                'phi': phi,
                'u_mag': np.sqrt(ux**2 + uy**2)
            }
        return {'ux': np.nan, 'uy': np.nan, 'phi': np.nan, 'u_mag': np.nan}


class PRBModel:
    """PRB model with configurable γ and k_θ."""
    def __init__(self, gamma=0.8517, k_theta=2.67617, w=0.3, name=None):
        self.model = PRBParallelogramModel(w=w)
        self.model.gamma = gamma
        self.model.K_theta_coeff = k_theta
        self.name = name if name else f"PRB (γ={gamma:.4f})"
    
    def solve(self, Ax, Ay, B=0):
        result = self.model.solve(Ay)
        if isinstance(result, tuple) and len(result) == 4:
            delta, ux, phi, theta_sol = result
            return {
                'ux': ux,
                'uy': delta,
                'phi': np.degrees(phi) if abs(phi) > 0 else 0.0,
                'u_mag': np.sqrt(ux**2 + delta**2)
            }
        return {'ux': np.nan, 'uy': np.nan, 'phi': np.nan, 'u_mag': np.nan}


class BCMModel:
    """Awtar's Beam Constraint Model."""
    def __init__(self, w=0.3, t=0.02):
        self.model = BCMParallelogram(w=w, t=t)
        self.name = "BCM (Awtar)"
    
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


class LinearModel:
    """Simple linear beam theory."""
    def __init__(self, w=0.3):
        self.w = w
        self.name = "Linear Theory"
    
    def solve(self, Ax, Ay, B=0):
        uy = Ay / 24.0
        ux = 0.0
        phi = 0.0
        return {
            'ux': ux,
            'uy': uy,
            'phi': phi,
            'u_mag': np.sqrt(ux**2 + uy**2)
        }


# =============================================================================
# Comparison Functions
# =============================================================================

def compare_models_at_point(Ax, Ay, B=0, w=0.3):
    """Compare all models at a single (Ax, Ay) point."""
    models = [
        FEAModel(),
        BVPModel(w=w),
        GuidedBeamModel(w=w),
        PRBModel(gamma=0.8517, k_theta=2.67617, w=w, name="PRB Original"),
        PRBModel(gamma=0.90, k_theta=2.5, w=w, name="PRB Optimized"),
        BCMModel(w=w),
        LinearModel(w=w)
    ]
    
    results = {}
    for model in models:
        try:
            results[model.name] = model.solve(Ax, Ay, B)
        except Exception as e:
            print(f"Error in {model.name}: {e}")
            results[model.name] = {'ux': np.nan, 'uy': np.nan, 'phi': np.nan, 'u_mag': np.nan}
    
    return results


def sweep_ay(Ax=0.0, Ay_range=(-20, 20), n_points=41, w=0.3):
    """Sweep Ay and collect results from all models."""
    Ay_values = np.linspace(Ay_range[0], Ay_range[1], n_points)
    
    models = [
        FEAModel(),
        BVPModel(w=w),
        GuidedBeamModel(w=w),
        PRBModel(gamma=0.8517, k_theta=2.67617, w=w, name="PRB Original"),
        PRBModel(gamma=0.90, k_theta=2.5, w=w, name="PRB Optimized"),
        BCMModel(w=w),
        LinearModel(w=w)
    ]
    
    all_results = {m.name: {'ux': [], 'uy': [], 'phi': [], 'u_mag': []} for m in models}
    
    for Ay in Ay_values:
        for model in models:
            try:
                res = model.solve(Ax, Ay)
                for key in ['ux', 'uy', 'phi', 'u_mag']:
                    all_results[model.name][key].append(res[key])
            except:
                for key in ['ux', 'uy', 'phi', 'u_mag']:
                    all_results[model.name][key].append(np.nan)
    
    for name in all_results:
        for key in all_results[name]:
            all_results[name][key] = np.array(all_results[name][key])
    
    return Ay_values, all_results


def plot_comparison(Ax=0.0, Ay_range=(-20, 20), n_points=41, w=0.3, save_path=None):
    """Create comparison plots for all models."""
    
    print(f"Computing model comparison for Ax={Ax}, Ay in [{Ay_range[0]}, {Ay_range[1]}]...")
    Ay_values, results = sweep_ay(Ax, Ay_range, n_points, w)
    
    colors = {
        '2D FEA (Ground Truth)': '#e94560',
        'BVP Solver': '#00ff88',
        'Guided Beam': '#9b59b6',
        'PRB Original': '#f1c40f',
        'PRB Optimized': '#ff6b35',
        'BCM (Awtar)': '#00d4ff',
        'Linear Theory': '#888888'
    }
    
    line_styles = {
        '2D FEA (Ground Truth)': '-',
        'BVP Solver': '--',
        'Guided Beam': '-.',
        'PRB Original': ':',
        'PRB Optimized': ':',
        'BCM (Awtar)': '--',
        'Linear Theory': ':'
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Model Comparison: Ax = {Ax}', fontsize=14, fontweight='bold')
    
    quantities = [('ux', 'Normalized X Displacement (ux)'),
                  ('uy', 'Normalized Y Displacement (uy)'),
                  ('phi', 'Stage Rotation φ (degrees)'),
                  ('u_mag', 'Displacement Magnitude |u|')]
    
    for ax, (key, title) in zip(axes.flat, quantities):
        for name in results:
            ax.plot(Ay_values, results[name][key], 
                   color=colors.get(name, 'black'),
                   linestyle=line_styles.get(name, '-'),
                   linewidth=2 if '2D FEA' in name else 1.5,
                   label=name)
        
        ax.set_xlabel('Ay (Normalized Force)')
        ax.set_ylabel(title)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='gray', linestyle='-', alpha=0.3)
        ax.axvline(0, color='gray', linestyle='-', alpha=0.3)
    
    axes[0, 0].legend(loc='best', fontsize=8)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to {save_path}")
    
    return fig


def plot_errors(Ax=0.0, Ay_range=(-20, 20), n_points=41, w=0.3, save_path=None):
    """Plot relative errors compared to FEA ground truth."""
    
    print(f"Computing errors for Ax={Ax}...")
    Ay_values, results = sweep_ay(Ax, Ay_range, n_points, w)
    
    gt_name = '2D FEA (Ground Truth)'
    gt = results[gt_name]
    
    colors = {
        'BVP Solver': '#00ff88',
        'Guided Beam': '#9b59b6',
        'PRB Original': '#f1c40f',
        'PRB Optimized': '#ff6b35',
        'BCM (Awtar)': '#00d4ff',
        'Linear Theory': '#888888'
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Relative Errors vs FEA Ground Truth: Ax = {Ax}', fontsize=14, fontweight='bold')
    
    quantities = [('ux', 'ux Error (%)'), ('uy', 'uy Error (%)'),
                  ('phi', 'φ Error (%)'), ('u_mag', '|u| Error (%)')]
    
    for ax, (key, title) in zip(axes.flat, quantities):
        for name in results:
            if name == gt_name:
                continue
            
            with np.errstate(divide='ignore', invalid='ignore'):
                rel_err = np.where(np.abs(gt[key]) > 1e-10,
                                   (results[name][key] - gt[key]) / gt[key] * 100,
                                   np.nan)
            
            ax.plot(Ay_values, rel_err, 
                   color=colors.get(name, 'black'),
                   linewidth=1.5,
                   label=name)
        
        ax.set_xlabel('Ay (Normalized Force)')
        ax.set_ylabel('Relative Error (%)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='gray', linestyle='-', alpha=0.5)
        ax.set_ylim(-50, 50)
    
    axes[0, 0].legend(loc='best', fontsize=8)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved error plot to {save_path}")
    
    return fig


def print_comparison_table(Ax=0.0, Ay=5.0, B=0.0, w=0.3):
    """Print a formatted comparison table."""
    
    results = compare_models_at_point(Ax, Ay, B, w)
    
    gt_name = '2D FEA (Ground Truth)'
    gt = results.get(gt_name, {})
    
    print("\n" + "="*80)
    print(f"MODEL COMPARISON at Ax={Ax}, Ay={Ay}, B={B}")
    print("="*80)
    
    print(f"\n{'Model':<25} {'ux':>12} {'uy':>12} {'φ (deg)':>12} {'|u|':>12}")
    print("-"*80)
    
    for name, res in results.items():
        print(f"{name:<25} {res['ux']:>12.6f} {res['uy']:>12.6f} {res['phi']:>12.4f} {res['u_mag']:>12.6f}")
    
    print("\n" + "-"*80)
    print("ERRORS vs FEA Ground Truth:")
    print("-"*80)
    print(f"\n{'Model':<25} {'ux err%':>12} {'uy err%':>12} {'φ err%':>12} {'|u| err%':>12}")
    print("-"*80)
    
    for name, res in results.items():
        if name == gt_name:
            continue
        
        def err(v, ref):
            if np.isnan(v) or np.isnan(ref) or abs(ref) < 1e-10:
                return np.nan
            return (v / ref - 1) * 100
        
        ux_err = err(res['ux'], gt.get('ux', np.nan))
        uy_err = err(res['uy'], gt.get('uy', np.nan))
        phi_err = err(res['phi'], gt.get('phi', np.nan))
        u_err = err(res['u_mag'], gt.get('u_mag', np.nan))
        
        def fmt(v):
            return f"{v:>12.2f}" if not np.isnan(v) else f"{'N/A':>12}"
        
        print(f"{name:<25} {fmt(ux_err)} {fmt(uy_err)} {fmt(phi_err)} {fmt(u_err)}")
    
    print("="*80 + "\n")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    test_cases = [
        (0.0, 5.0),
        (0.0, 10.0),
        (5.0, 5.0),
        (0.0, -5.0),
    ]
    
    print("\n" + "="*80)
    print("PARALLELOGRAM FLEXURE MODEL COMPARISON")
    print("Ground Truth: 2D FEA Beam Model (from simulation database)")
    print("="*80)
    
    for Ax, Ay in test_cases:
        print_comparison_table(Ax=Ax, Ay=Ay)
    
    print("\nGenerating comparison plots...")
    
    plot_comparison(Ax=0.0, save_path=os.path.join(SCRIPT_DIR, 'comparison_ax0.png'))
    plot_errors(Ax=0.0, save_path=os.path.join(SCRIPT_DIR, 'errors_ax0.png'))
    
    plot_comparison(Ax=5.0, save_path=os.path.join(SCRIPT_DIR, 'comparison_ax5.png'))
    plot_errors(Ax=5.0, save_path=os.path.join(SCRIPT_DIR, 'errors_ax5.png'))
    
    print("\nDone! Plots saved to project directory.")
