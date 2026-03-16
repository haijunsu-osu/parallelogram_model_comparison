"""
Euler Beam Solver for Cantilever Beam with Large Deflections

Solves the normalized Euler-Bernoulli beam equations:
    d(x_bar)/ds = cos(theta)
    d(y_bar)/ds = sin(theta)
    d(theta)/ds = kappa_bar
    d(kappa_bar)/ds = alpha_x * sin(theta) - alpha_y * cos(theta)

Boundary Conditions:
    At s=0 (clamped): x_bar=0, y_bar=0, theta=0
    At s=1 (free): kappa_bar = beta

Parameters:
    alpha_x = Fx * L^2 / (E * I)  - normalized horizontal force
    alpha_y = Fy * L^2 / (E * I)  - normalized vertical force
    beta = Mz * L / (E * I)       - normalized moment at free end
"""

import numpy as np
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt


def beam_ode(s, q, alpha_x, alpha_y):
    """
    ODE system for the normalized Euler beam equations.
    
    State vector q = [x_bar, y_bar, theta, kappa_bar]
    
    Returns dq/ds
    """
    x_bar, y_bar, theta, kappa_bar = q
    
    dx_bar_ds = np.cos(theta)
    dy_bar_ds = np.sin(theta)
    dtheta_ds = kappa_bar
    # Correct sign: dκ/ds = αx·sin(θ) - αy·cos(θ)
    # Positive Fy (upward force) → positive αy → beam curves downward (moment decreases)
    # Negative Fy (downward force) → negative αy → beam curves downward (standard gravity case)
    dkappa_bar_ds = alpha_x * np.sin(theta) - alpha_y * np.cos(theta)
    
    return np.array([dx_bar_ds, dy_bar_ds, dtheta_ds, dkappa_bar_ds])


def beam_bc(qa, qb, beta):
    """
    Boundary conditions for the beam.
    
    At s=0 (clamped end, qa):
        x_bar(0) = 0
        y_bar(0) = 0
        theta(0) = 0
    
    At s=1 (free end, qb):
        kappa_bar(1) = beta
    """
    return np.array([
        qa[0],           # x_bar(0) = 0
        qa[1],           # y_bar(0) = 0
        qa[2],           # theta(0) = 0
        qb[3] - beta     # kappa_bar(1) = beta
    ])


def solve_euler_beam(alpha_x, alpha_y, beta, n_points=101):
    """
    Solve the Euler beam equations for given load parameters.
    
    Parameters:
    -----------
    alpha_x : float
        Normalized horizontal force (Fx * L^2 / EI)
    alpha_y : float
        Normalized vertical force (Fy * L^2 / EI)
    beta : float
        Normalized moment at free end (Mz * L / EI)
    n_points : int
        Number of points for discretization
    
    Returns:
    --------
    s : ndarray
        Normalized arc length array [0, 1]
    x_bar : ndarray
        Normalized x-coordinates
    y_bar : ndarray
        Normalized y-coordinates
    theta : ndarray
        Beam angle at each point
    kappa_bar : ndarray
        Normalized curvature at each point
    """
    # Initial mesh
    s = np.linspace(0, 1, n_points)
    
    # Initial guess for the solution
    # Start with a straight beam and linear curvature distribution
    q_init = np.zeros((4, n_points))
    q_init[0] = s                    # x_bar = s (straight beam)
    q_init[1] = 0                    # y_bar = 0
    q_init[2] = 0                    # theta = 0
    q_init[3] = beta * s             # linear curvature from 0 to beta
    
    # Wrapper functions with parameters
    def ode_wrapper(s, q):
        return beam_ode(s, q, alpha_x, alpha_y)
    
    def bc_wrapper(qa, qb):
        return beam_bc(qa, qb, beta)
    
    # Solve the BVP
    solution = solve_bvp(ode_wrapper, bc_wrapper, s, q_init, 
                         tol=1e-8, max_nodes=5000, verbose=0)
    
    if not solution.success:
        print(f"Warning: BVP solver did not converge. Message: {solution.message}")
    
    # Evaluate solution on a fine mesh
    s_fine = np.linspace(0, 1, n_points)
    q_fine = solution.sol(s_fine)
    
    return s_fine, q_fine[0], q_fine[1], q_fine[2], q_fine[3]


def plot_beam_shape(s, x_bar, y_bar, theta, kappa_bar, alpha_x, alpha_y, beta):
    """
    Plot the beam shape and related quantities.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Beam shape
    ax1 = axes[0, 0]
    ax1.plot(x_bar, y_bar, 'b-', linewidth=2.5, label='Beam shape')
    ax1.plot(0, 0, 'ko', markersize=12, label='Clamped end')
    ax1.plot(x_bar[-1], y_bar[-1], 'r^', markersize=12, label='Free end (tip)')
    
    # Add arrows for forces at the tip
    tip_x, tip_y = x_bar[-1], y_bar[-1]
    arrow_scale = 0.15
    if abs(alpha_x) > 0.01:
        ax1.annotate('', xy=(tip_x + np.sign(alpha_x)*arrow_scale, tip_y), 
                    xytext=(tip_x, tip_y),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax1.text(tip_x + np.sign(alpha_x)*arrow_scale*1.2, tip_y, r'$F_x$', 
                fontsize=12, color='green')
    if abs(alpha_y) > 0.01:
        ax1.annotate('', xy=(tip_x, tip_y + np.sign(alpha_y)*arrow_scale), 
                    xytext=(tip_x, tip_y),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=2))
        ax1.text(tip_x, tip_y + np.sign(alpha_y)*arrow_scale*1.2, r'$F_y$', 
                fontsize=12, color='orange')
    
    ax1.set_xlabel(r'$\bar{x} = x/L$', fontsize=12)
    ax1.set_ylabel(r'$\bar{y} = y/L$', fontsize=12)
    ax1.set_title('Beam Deformation Shape', fontsize=14, fontweight='bold')
    ax1.axis('equal')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best')
    
    # Plot 2: Angle distribution
    ax2 = axes[0, 1]
    ax2.plot(s, np.degrees(theta), 'g-', linewidth=2)
    ax2.set_xlabel(r'$\bar{s} = s/L$', fontsize=12)
    ax2.set_ylabel(r'$\theta$ (degrees)', fontsize=12)
    ax2.set_title('Beam Angle Distribution', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Curvature distribution
    ax3 = axes[1, 0]
    ax3.plot(s, kappa_bar, 'm-', linewidth=2)
    ax3.set_xlabel(r'$\bar{s} = s/L$', fontsize=12)
    ax3.set_ylabel(r'$\bar{\kappa} = L \cdot \kappa$', fontsize=12)
    ax3.set_title('Normalized Curvature Distribution', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Info panel
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Display results
    tip_position = f"Tip Position: ($\\bar{{x}}$, $\\bar{{y}}$) = ({x_bar[-1]:.4f}, {y_bar[-1]:.4f})"
    tip_angle = f"Tip Angle: θ = {np.degrees(theta[-1]):.2f}°"
    
    info_text = (
        f"Load Parameters:\n"
        f"─────────────────────\n"
        f"$\\alpha_x$ = {alpha_x:.4f}\n"
        f"$\\alpha_y$ = {alpha_y:.4f}\n"
        f"$\\beta$ = {beta:.4f}\n\n"
        f"Results:\n"
        f"─────────────────────\n"
        f"Tip Position:\n"
        f"  $\\bar{{x}}_{{tip}}$ = {x_bar[-1]:.6f}\n"
        f"  $\\bar{{y}}_{{tip}}$ = {y_bar[-1]:.6f}\n\n"
        f"Tip Angle: {np.degrees(theta[-1]):.4f}°\n\n"
        f"Curvature at root: {kappa_bar[0]:.6f}\n"
        f"Curvature at tip: {kappa_bar[-1]:.6f}"
    )
    
    ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=12,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax4.set_title('Solution Summary', fontsize=14, fontweight='bold')
    
    plt.suptitle(f'Euler Beam Analysis\n'
                 f'($\\alpha_x$={alpha_x}, $\\alpha_y$={alpha_y}, $\\beta$={beta})',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig


def main():
    """
    Main function to run the beam solver with example parameters.
    """
    print("=" * 60)
    print("EULER BEAM SOLVER - Large Deflection Analysis")
    print("=" * 60)
    
    # Example load parameters
    # You can modify these values to explore different loading conditions
    alpha_x = 0.0      # Normalized horizontal force
    alpha_y = -5.0     # Normalized vertical force (negative = downward)
    beta = 0.0         # Normalized moment at tip
    
    print(f"\nLoad Parameters:")
    print(f"  α_x = {alpha_x} (normalized horizontal force)")
    print(f"  α_y = {alpha_y} (normalized vertical force)")
    print(f"  β   = {beta} (normalized tip moment)")
    
    # Solve the beam equations
    print("\nSolving beam equations...")
    s, x_bar, y_bar, theta, kappa_bar = solve_euler_beam(alpha_x, alpha_y, beta)
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTip Position (normalized):")
    print(f"  x̄_tip = {x_bar[-1]:.6f}")
    print(f"  ȳ_tip = {y_bar[-1]:.6f}")
    print(f"\nTip Angle: θ_tip = {np.degrees(theta[-1]):.4f}°")
    print(f"\nCurvature at root: κ̄(0) = {kappa_bar[0]:.6f}")
    print(f"Curvature at tip:  κ̄(1) = {kappa_bar[-1]:.6f}")
    
    # Plot the results
    fig = plot_beam_shape(s, x_bar, y_bar, theta, kappa_bar, alpha_x, alpha_y, beta)
    plt.savefig('beam_shape.png', dpi=150, bbox_inches='tight')
    print("\nPlot saved to 'beam_shape.png'")
    plt.show()
    
    return s, x_bar, y_bar, theta, kappa_bar


def interactive_solve(alpha_x, alpha_y, beta, show_plot=True, save_plot=False):
    """
    Interactive function to solve and plot beam for given parameters.
    
    Parameters:
    -----------
    alpha_x : float
        Normalized horizontal force
    alpha_y : float
        Normalized vertical force  
    beta : float
        Normalized tip moment
    show_plot : bool
        Whether to display the plot
    save_plot : bool or str
        If True, save as 'beam_shape.png'. If string, use as filename.
    
    Returns:
    --------
    dict with keys: 's', 'x_bar', 'y_bar', 'theta', 'kappa_bar', 
                    'x_tip', 'y_tip', 'theta_tip'
    """
    s, x_bar, y_bar, theta, kappa_bar = solve_euler_beam(alpha_x, alpha_y, beta)
    
    results = {
        's': s,
        'x_bar': x_bar,
        'y_bar': y_bar,
        'theta': theta,
        'kappa_bar': kappa_bar,
        'x_tip': x_bar[-1],
        'y_tip': y_bar[-1],
        'theta_tip': theta[-1],
        'theta_tip_deg': np.degrees(theta[-1])
    }
    
    print(f"Tip Position: (x̄, ȳ) = ({results['x_tip']:.6f}, {results['y_tip']:.6f})")
    print(f"Tip Angle: θ = {results['theta_tip_deg']:.4f}°")
    
    if show_plot or save_plot:
        fig = plot_beam_shape(s, x_bar, y_bar, theta, kappa_bar, alpha_x, alpha_y, beta)
        
        if save_plot:
            filename = save_plot if isinstance(save_plot, str) else 'beam_shape.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"Plot saved to '{filename}'")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
    
    return results


if __name__ == "__main__":
    # Run the main example
    main()
    
    # You can also use the interactive function:
    # results = interactive_solve(alpha_x=0, alpha_y=-5, beta=0)
    # results = interactive_solve(alpha_x=2, alpha_y=-3, beta=1)
