"""
Systematic Study of Gamma Coefficient in PRB Model.
Varying Gamma in [0.80, 0.95] and comparing against Nonlinear Beam Ground Truth.
Load Range: Ay in [-15, 15].
"""

import numpy as np
import matplotlib.pyplot as plt
from parallelogram_solver import ParallelogramFlexureSolver
from prb_parallelogram import PRBParallelogramModel

def run_study():
    # Parameters
    ay_values = np.linspace(-15, 15, 31)
    gamma_values = [0.80, 0.85, 0.8517, 0.90, 0.95]
    
    # Storage
    gt = {'uy': [], 'ux': []}
    prb_results = {g: {'uy': [], 'ux': []} for g in gamma_values}
    
    # 1. Compute Ground Truth (Nonlinear) with Homotopy
    print("Computing Ground Truth (Nonlinear) with Homotopy...")
    solver_nl = ParallelogramFlexureSolver(w=0.3)
    
    # Helper to extract full solution vector for continuation
    def get_sol_vector(slv):
        return np.array([slv.alpha_x1, slv.alpha_y1, slv.beta_1, 
                         slv.alpha_x2, slv.alpha_y2, slv.beta_2])

    temp_map = {}
    
    # Function to sweep load
    def sweep_load(loads):
        current_guess = None
        for ay in loads:
            # Skip 0 if already done? No, safe to redo or skip.
            success = solver_nl.solve(0, ay, 0, initial_guess=current_guess)
            if success:
                temp_map[ay] = (solver_nl.Y_p, solver_nl.X_p - 1.0)
                current_guess = get_sol_vector(solver_nl)
                # print(f"Solved Ay={ay:.2f}")
            else:
                print(f"Warning: NL Solver failed at Ay={ay:.2f}")
                temp_map[ay] = (np.nan, np.nan)
                # Try to persist previous guess for next step?
                # or reset? usually stick with previous valid is best attempt.

    # Sweep Positive: 0 to 3.0, skip 3.1-3.4, continue from 3.5 to 15
    positive_loads = np.concatenate([
        np.linspace(0, 3.0, 31),     # 0 to 3.0, step 0.1
        np.linspace(3.5, 15, 24)     # 3.5 to 15, step 0.5
    ])
    sweep_load(positive_loads)
    
    # Sweep Negative: 0 to -3.0, skip -3.4 to -3.1, continue from -3.5 to -15
    solver_nl.solve(0, 0, 0)  # Reset
    negative_loads = np.concatenate([
        np.linspace(0, -3.0, 31),
        np.linspace(-3.5, -15, 24)
    ])
    sweep_load(negative_loads)
        
    # Assemble ordered list for the target ay_values
    for ay in ay_values:
        # Find nearest key
        keys = np.array(list(temp_map.keys()))
        if len(keys) == 0:
            gt['uy'].append(np.nan)
            gt['ux'].append(np.nan)
            continue
            
        idx = (np.abs(keys - ay)).argmin()
        nearest_ay = keys[idx]
        
        # Ensure we matched close enough
        if abs(nearest_ay - ay) < 1e-4:
            res = temp_map[nearest_ay]
        else:
            # This implies the fine grid missed the coarse grid point? 
            # 0.25 step hits integers. Safe.
            res = (np.nan, np.nan)
            
        gt['uy'].append(res[0])
        gt['ux'].append(res[1])
        
    # 2. Compute PRB for each Gamma
    print("Computing PRB Models...")
    solver_prb = PRBParallelogramModel(w=0.3)
    solver_prb.K_theta_coeff = 2.65 # Keep K fixed, or should it vary?
    # Usually K_theta implies optimal fit for specific gamma.
    # But here we test sensitivity to gamma alone.
    
    for g in gamma_values:
        solver_prb.gamma = g
        for ay in ay_values:
            d, ux, _, _ = solver_prb.solve(ay)
            prb_results[g]['uy'].append(d)
            prb_results[g]['ux'].append(ux)
            
    # 3. Visualization
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('#1a1a2e')
    
    # Style helper
    def style_ax(ax, title, xlabel, ylabel):
        ax.set_facecolor('#16213e')
        ax.set_title(title, color='white', fontsize=12)
        ax.set_xlabel(xlabel, color='white')
        ax.set_ylabel(ylabel, color='white')
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('white')
        
    # Plot Uy
    ax1 = axes[0]
    style_ax(ax1, "Vertical Deflection (Uy) vs Load (Ay)", "Normalize Load Ay", "Uy")
    ax1.plot(ay_values, gt['uy'], 'w-', lw=3, label='Ground Truth (NL)')
    
    # Plot Ux
    ax2 = axes[1]
    style_ax(ax2, "Parasitic Shortening (Ux) vs Load (Ay)", "Normalize Load Ay", "Ux")
    ax2.plot(ay_values, gt['ux'], 'w-', lw=3, label='Ground Truth (NL)')
    
    # Error Analysis
    avg_errs = []
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(gamma_values)))
    
    for i, g in enumerate(gamma_values):
        c = colors[i]
        lbl = f'PRB $\gamma$={g:.2f}'
        
        # Plot curves
        ax1.plot(ay_values, prb_results[g]['uy'], '--', color=c, lw=2, label=lbl)
        ax2.plot(ay_values, prb_results[g]['ux'], '--', color=c, lw=2)
        
        # Calculate Error
        # RMSE for Uy
        err = np.sqrt(np.mean((np.array(prb_results[g]['uy']) - np.array(gt['uy']))**2))
        avg_errs.append(err)

    ax1.legend(facecolor='#16213e', edgecolor='white', labelcolor='white')
    
    # Plot 3: Error vs Gamma
    ax3 = axes[2]
    style_ax(ax3, "RMSE Error (Uy) vs Gamma", "Gamma", "RMSE Error")
    ax3.plot(gamma_values, avg_errs, 'o-', color='#e94560', lw=2)
    
    # Annotate minimum
    min_idx = np.argmin(avg_errs)
    best_g = gamma_values[min_idx]
    best_err = avg_errs[min_idx]
    ax3.annotate(f'Best: {best_g:.3f}', xy=(best_g, best_err), xytext=(best_g, best_err*1.5),
                 arrowprops=dict(facecolor='white', shrink=0.05), color='white')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_study()
