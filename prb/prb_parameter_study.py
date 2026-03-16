"""
PRB Parameter Study: Effect of gamma and K_theta on model accuracy.
Varying:
  - gamma in [0.80, 0.95]
  - K_theta in [2.4, 2.8]
Comparing against Nonlinear Beam Ground Truth.
"""

import numpy as np
import matplotlib.pyplot as plt
from parallelogram_solver import ParallelogramFlexureSolver
from prb_parallelogram import PRBParallelogramModel

def run_study():
    print("PRB Parameter Study: gamma vs K_theta")
    print("=" * 50)
    
    # Parameter ranges
    gamma_values = np.linspace(0.80, 0.95, 7)
    k_theta_values = np.linspace(2.4, 2.8, 9)
    
    # Load range (skip problematic 3.1-3.4 region)
    ay_values = np.concatenate([
        np.linspace(0, 3.0, 31),
        np.linspace(3.5, 15, 24)
    ])
    
    # 1. Compute Ground Truth (Nonlinear)
    print("Computing Ground Truth (Nonlinear)...")
    solver_nl = ParallelogramFlexureSolver(w=0.3)
    
    gt_uy = []
    gt_ux = []
    
    for ay in ay_values:
        ok = solver_nl.solve(0, ay, 0)
        if ok:
            gt_uy.append(solver_nl.Y_p)
            gt_ux.append(solver_nl.X_p - 1.0)
        else:
            gt_uy.append(np.nan)
            gt_ux.append(np.nan)
            print(f"Warning: NL failed at Ay={ay:.2f}")
    
    gt_uy = np.array(gt_uy)
    gt_ux = np.array(gt_ux)
    
    # 2. Compute PRB for each (gamma, K_theta) combination
    print("Computing PRB models for parameter grid...")
    
    # Store RMSE errors in a 2D grid
    error_grid_uy = np.zeros((len(gamma_values), len(k_theta_values)))
    error_grid_ux = np.zeros((len(gamma_values), len(k_theta_values)))
    error_grid_combined = np.zeros((len(gamma_values), len(k_theta_values)))
    
    solver_prb = PRBParallelogramModel(w=0.3)
    
    for i, g in enumerate(gamma_values):
        for j, k in enumerate(k_theta_values):
            solver_prb.gamma = g
            solver_prb.K_theta_coeff = k
            
            prb_uy = []
            prb_ux = []
            
            for ay in ay_values:
                d, ux, _, _ = solver_prb.solve(ay)
                prb_uy.append(d)
                prb_ux.append(ux)
            
            prb_uy = np.array(prb_uy)
            prb_ux = np.array(prb_ux)
            
            # Compute RMSE (excluding NaN)
            valid = ~np.isnan(gt_uy)
            rmse_uy = np.sqrt(np.mean((prb_uy[valid] - gt_uy[valid])**2))
            rmse_ux = np.sqrt(np.mean((prb_ux[valid] - gt_ux[valid])**2))
            
            # Combined error: sqrt(rmse_uy^2 + rmse_ux^2)
            rmse_combined = np.sqrt(rmse_uy**2 + rmse_ux**2)
            
            error_grid_uy[i, j] = rmse_uy
            error_grid_ux[i, j] = rmse_ux
            error_grid_combined[i, j] = rmse_combined
    
    # Find optimal parameters for COMBINED error
    min_idx = np.unravel_index(np.argmin(error_grid_combined), error_grid_combined.shape)
    best_gamma = gamma_values[min_idx[0]]
    best_k_theta = k_theta_values[min_idx[1]]
    best_rmse_combined = error_grid_combined[min_idx]
    best_rmse_uy = error_grid_uy[min_idx]
    best_rmse_ux = error_grid_ux[min_idx]
    
    print(f"\nOptimal Parameters for Combined Error sqrt(Uy^2 + Ux^2):")
    print(f"  gamma = {best_gamma:.4f}")
    print(f"  K_theta = {best_k_theta:.4f}")
    print(f"  RMSE Combined = {best_rmse_combined:.6f}")
    print(f"  RMSE Uy = {best_rmse_uy:.6f}")
    print(f"  RMSE Ux = {best_rmse_ux:.6f}")
    
    # 3. Visualization
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.patch.set_facecolor('#1a1a2e')
    fig.suptitle('PRB Parameter Study: Effect of γ and Kθ', color='white', fontsize=14)
    
    # Style helper
    def style_ax(ax, title):
        ax.set_facecolor('#16213e')
        ax.set_title(title, color='white', fontsize=12)
        ax.set_xlabel('Kθ', color='white')
        ax.set_ylabel('γ', color='white')
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): 
            spine.set_color('white')
    
    # Plot 1: Combined RMSE Heatmap (main optimization target)
    ax1 = axes[0]
    style_ax(ax1, 'Combined Error sqrt(Uy² + Ux²)')
    
    K, G = np.meshgrid(k_theta_values, gamma_values)
    c1 = ax1.contourf(K, G, error_grid_combined, levels=20, cmap='viridis')
    ax1.plot(best_k_theta, best_gamma, 'r*', markersize=15, label=f'Optimal ({best_gamma:.2f}, {best_k_theta:.2f})')
    ax1.legend(facecolor='#16213e', labelcolor='white')
    cbar1 = plt.colorbar(c1, ax=ax1)
    cbar1.ax.yaxis.set_tick_params(color='white')
    cbar1.ax.yaxis.label.set_color('white')
    plt.setp(plt.getp(cbar1.ax.axes, 'yticklabels'), color='white')
    
    # Plot 2: Uy RMSE Heatmap
    ax2 = axes[1]
    style_ax(ax2, 'RMSE Error for Uy')
    
    c2 = ax2.contourf(K, G, error_grid_uy, levels=20, cmap='plasma')
    ax2.plot(best_k_theta, best_gamma, 'r*', markersize=15)
    cbar2 = plt.colorbar(c2, ax=ax2)
    cbar2.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar2.ax.axes, 'yticklabels'), color='white')
    
    # Plot 3: Uy curves for optimal vs default parameters
    ax3 = axes[2]
    ax3.set_facecolor('#16213e')
    ax3.set_title('Uy Comparison', color='white', fontsize=12)
    ax3.set_xlabel('Normalized Load Ay', color='white')
    ax3.set_ylabel('Uy', color='white')
    ax3.tick_params(colors='white')
    for spine in ax3.spines.values(): 
        spine.set_color('white')
    ax3.grid(True, alpha=0.3)
    
    # Ground Truth
    ax3.plot(ay_values, gt_uy, 'w-', lw=3, label='Ground Truth (NL)')
    
    # Default PRB (gamma=0.8517, K=2.65)
    solver_prb.gamma = 0.8517
    solver_prb.K_theta_coeff = 2.65
    default_uy = [solver_prb.solve(ay)[0] for ay in ay_values]
    ax3.plot(ay_values, default_uy, '--', color='#e94560', lw=2, label='Default (0.85, 2.65)')
    
    # Optimal PRB
    solver_prb.gamma = best_gamma
    solver_prb.K_theta_coeff = best_k_theta
    optimal_uy = [solver_prb.solve(ay)[0] for ay in ay_values]
    ax3.plot(ay_values, optimal_uy, '--', color='#00ff88', lw=2, label=f'Optimal ({best_gamma:.2f}, {best_k_theta:.2f})')
    
    ax3.legend(facecolor='#16213e', labelcolor='white')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_study()
