"""
Nonlinearity Analysis for Parallelogram Flexure Mechanism

This script analyzes subtle nonlinear effects in parallelogram flexures:
1. Parasitic rotation (φ) as a function of vertical load
2. X-shortening (kinematic nonlinearity) 
3. Comparison with linear theory
4. Load-stiffening effects
"""

import numpy as np
import matplotlib.pyplot as plt
from parallelogram_solver import ParallelogramFlexureSolver

def analyze_nonlinearity(w=0.3, Ay_max=10.0, n_points=50):
    """
    Comprehensive nonlinearity analysis.
    
    Parameters:
    -----------
    w : float
        Normalized half beam separation (W/L)
    Ay_max : float
        Maximum normalized vertical load
    n_points : int
        Number of load steps
    """
    solver = ParallelogramFlexureSolver(w=w)
    
    Ay_values = np.linspace(0.1, Ay_max, n_points)
    
    # Results storage
    results = {
        'Ay': [],
        'Y_p': [],
        'Y_p_linear': [],
        'X_p': [],
        'phi_deg': [],
        'alpha_x1': [],
        'alpha_x2': [],
        'alpha_y1': [],
        'alpha_y2': [],
        'beta_1': [],
        'beta_2': [],
        'converged': []
    }
    
    print("Analyzing nonlinear effects in parallelogram flexure...")
    print(f"Parameters: w = {w}, Ay range = [0.1, {Ay_max}]")
    print("=" * 60)
    
    for i, Ay in enumerate(Ay_values):
        success = solver.solve(A_x=0, A_y=Ay, B=0)
        r = solver.get_results_summary()
        linear = solver.get_linear_theory_prediction(0, Ay, 0)
        
        results['Ay'].append(Ay)
        results['Y_p'].append(r['platform']['Y_p'])
        results['Y_p_linear'].append(linear['Y_p_linear'])
        results['X_p'].append(r['platform']['X_p'])
        results['phi_deg'].append(r['platform']['phi_deg'])
        results['alpha_x1'].append(r['beam1']['alpha_x'])
        results['alpha_x2'].append(r['beam2']['alpha_x'])
        results['alpha_y1'].append(r['beam1']['alpha_y'])
        results['alpha_y2'].append(r['beam2']['alpha_y'])
        results['beta_1'].append(r['beam1']['beta'])
        results['beta_2'].append(r['beam2']['beta'])
        results['converged'].append(success)
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n_points} (Ay = {Ay:.1f})")
    
    # Convert to numpy arrays
    for key in results:
        results[key] = np.array(results[key])
    
    return results


def plot_nonlinearity_analysis(results, save_fig=True):
    """Plot comprehensive nonlinearity analysis."""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.patch.set_facecolor('#1a1a2e')
    
    for ax in axes.flat:
        ax.set_facecolor('#16213e')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        for spine in ax.spines.values():
            spine.set_color('white')
    
    Ay = results['Ay']
    
    # 1. Y-deflection comparison
    ax1 = axes[0, 0]
    ax1.plot(Ay, results['Y_p'], 'c-', linewidth=2, label='Large deflection')
    ax1.plot(Ay, results['Y_p_linear'], 'orange', linewidth=2, linestyle='--', label='Linear theory')
    ax1.set_xlabel(r'$A_y$ (normalized load)')
    ax1.set_ylabel(r'$\bar{Y}_p$ (platform deflection)')
    ax1.set_title('Platform Y-Deflection')
    ax1.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    ax1.grid(True, alpha=0.3)
    
    # 2. Y-deflection error
    ax2 = axes[0, 1]
    y_error = (results['Y_p'] - results['Y_p_linear']) / np.abs(results['Y_p_linear']) * 100
    ax2.plot(Ay, y_error, 'm-', linewidth=2)
    ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
    ax2.set_xlabel(r'$A_y$ (normalized load)')
    ax2.set_ylabel('Error (%)')
    ax2.set_title('Y-Deflection Error (Nonlinear vs Linear)')
    ax2.grid(True, alpha=0.3)
    
    # 3. Parasitic rotation
    ax3 = axes[0, 2]
    ax3.plot(Ay, results['phi_deg'], 'lime', linewidth=2)
    ax3.axhline(0, color='white', linestyle=':', alpha=0.5)
    ax3.set_xlabel(r'$A_y$ (normalized load)')
    ax3.set_ylabel(r'$\phi$ (degrees)')
    ax3.set_title('Parasitic Rotation (should be ≈ 0)')
    ax3.grid(True, alpha=0.3)
    
    # 4. X-shortening (kinematic effect)
    ax4 = axes[1, 0]
    x_shortening = 1.0 - results['X_p']
    ax4.plot(Ay, x_shortening, 'r-', linewidth=2)
    ax4.set_xlabel(r'$A_y$ (normalized load)')
    ax4.set_ylabel(r'$1 - \bar{X}_p$ (shortening)')
    ax4.set_title('X-Shortening (Kinematic Nonlinearity)')
    ax4.grid(True, alpha=0.3)
    
    # 5. Internal axial loads
    ax5 = axes[1, 1]
    ax5.plot(Ay, results['alpha_x1'], 'r-', linewidth=2, label=r'$\alpha_{x1}$')
    ax5.plot(Ay, results['alpha_x2'], 'b-', linewidth=2, label=r'$\alpha_{x2}$')
    ax5.axhline(0, color='white', linestyle=':', alpha=0.5)
    ax5.set_xlabel(r'$A_y$ (normalized load)')
    ax5.set_ylabel('Axial load')
    ax5.set_title('Internal Axial Loads (Nonlinear Effect)')
    ax5.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    ax5.grid(True, alpha=0.3)
    
    # 6. Internal moments
    ax6 = axes[1, 2]
    ax6.plot(Ay, results['beta_1'], 'r-', linewidth=2, label=r'$\beta_1$')
    ax6.plot(Ay, results['beta_2'], 'b-', linewidth=2, label=r'$\beta_2$')
    linear_beta = -Ay / 4  # Linear theory prediction
    ax6.plot(Ay, linear_beta, 'orange', linewidth=2, linestyle='--', label='Linear theory')
    ax6.set_xlabel(r'$A_y$ (normalized load)')
    ax6.set_ylabel('Tip moment')
    ax6.set_title('Internal Tip Moments')
    ax6.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    ax6.grid(True, alpha=0.3)
    
    fig.suptitle('Nonlinearity Analysis: Parallelogram Flexure under Vertical Load\n(w = 0.3)',
                 fontsize=14, fontweight='bold', color='white')
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('nonlinearity_analysis.png', dpi=150, bbox_inches='tight', 
                    facecolor='#1a1a2e')
        print("\nFigure saved to 'nonlinearity_analysis.png'")
    
    plt.show()
    
    return fig


def print_summary(results):
    """Print summary of nonlinear effects."""
    print("\n" + "=" * 60)
    print("NONLINEARITY SUMMARY")
    print("=" * 60)
    
    # At maximum load
    i_max = -1
    Ay_max = results['Ay'][i_max]
    
    print(f"\nAt maximum load (Ay = {Ay_max:.1f}):")
    print(f"  Y-deflection (nonlinear): {results['Y_p'][i_max]:.6f}")
    print(f"  Y-deflection (linear):    {results['Y_p_linear'][i_max]:.6f}")
    
    y_error = (results['Y_p'][i_max] - results['Y_p_linear'][i_max]) / abs(results['Y_p_linear'][i_max]) * 100
    print(f"  Y-deflection error:       {y_error:+.2f}%")
    
    print(f"\n  Parasitic rotation φ:     {results['phi_deg'][i_max]:.4f}°")
    print(f"  X-shortening:             {1 - results['X_p'][i_max]:.6f}")
    
    print(f"\n  Internal axial loads:")
    print(f"    α_x1 = {results['alpha_x1'][i_max]:+.4f}")
    print(f"    α_x2 = {results['alpha_x2'][i_max]:+.4f}")
    
    print(f"\n  Internal moments:")
    print(f"    β_1 = {results['beta_1'][i_max]:+.4f}")
    print(f"    β_2 = {results['beta_2'][i_max]:+.4f}")
    
    # Convergence
    n_converged = np.sum(results['converged'])
    print(f"\n  Solver convergence: {n_converged}/{len(results['converged'])}")


if __name__ == "__main__":
    # Run analysis
    results = analyze_nonlinearity(w=0.3, Ay_max=10.0, n_points=30)
    
    # Print summary
    print_summary(results)
    
    # Plot results
    plot_nonlinearity_analysis(results)
