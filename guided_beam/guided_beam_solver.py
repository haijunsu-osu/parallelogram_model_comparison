"""
Guided Beam Solver for Fixed-Guided Beam with Large Deflections

A "guided" beam has its tip constrained to remain flat (parallel to ground),
with the tip moment being unknown (reaction moment from the constraint).

Solves the normalized Euler-Bernoulli beam equations:
    d(x_bar)/ds = cos(theta)
    d(y_bar)/ds = sin(theta)
    d(theta)/ds = kappa_bar
    d(kappa_bar)/ds = alpha_x * sin(theta) - alpha_y * cos(theta)

Boundary Conditions:
    At s=0 (clamped): x_bar=0, y_bar=0, theta=0
    At s=1 (guided): theta(1) = 0  (tip must be flat)

The tip moment beta = kappa_bar(1) is unknown and determined by the constraint.

Parameters:
    alpha_x = Fx * L^2 / (E * I)  - normalized horizontal force
    alpha_y = Fy * L^2 / (E * I)  - normalized vertical force
"""

import numpy as np
from scipy.integrate import solve_bvp
from scipy.optimize import brentq
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
    dkappa_bar_ds = alpha_x * np.sin(theta) - alpha_y * np.cos(theta)
    
    return np.array([dx_bar_ds, dy_bar_ds, dtheta_ds, dkappa_bar_ds])


def beam_bc_guided(qa, qb):
    """
    Boundary conditions for the GUIDED beam.
    
    At s=0 (clamped end, qa):
        x_bar(0) = 0
        y_bar(0) = 0
        theta(0) = 0
    
    At s=1 (guided end, qb):
        theta(1) = 0  (tip must be flat/parallel to base)
    
    Note: kappa_bar(1) = beta is FREE (unknown reaction moment)
    """
    return np.array([
        qa[0],           # x_bar(0) = 0
        qa[1],           # y_bar(0) = 0
        qa[2],           # theta(0) = 0
        qb[2]            # theta(1) = 0 (guided constraint)
    ])


def solve_guided_beam(alpha_x, alpha_y, n_points=101):
    """
    Solve the Guided beam equations for given load parameters.
    
    The guided constraint requires theta(1) = 0.
    The tip moment beta is computed as the reaction moment.
    
    Parameters:
    -----------
    alpha_x : float
        Normalized horizontal force (Fx * L^2 / EI)
    alpha_y : float
        Normalized vertical force (Fy * L^2 / EI)
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
    beta : float
        Computed tip moment (reaction from guided constraint)
    success : bool
        Whether the solver converged
    """
    # Initial mesh
    s = np.linspace(0, 1, n_points)
    
    # Initial guess for the solution
    # For guided beam, we use a cubic displacement profile guess
    delta_guess = alpha_y / 12.0 if abs(alpha_y) > 0.01 else 0.0
    
    q_init = np.zeros((4, n_points))
    q_init[0] = s  # x_bar ≈ s
    q_init[1] = 3 * delta_guess * s**2 - 2 * delta_guess * s**3  # Cubic y shape
    q_init[2] = 6 * delta_guess * s - 6 * delta_guess * s**2      # theta = dy/ds (zero at both ends)
    q_init[3] = 6 * delta_guess - 12 * delta_guess * s            # curvature
    
    # Wrapper function with parameters
    def ode_wrapper(s, q):
        return beam_ode(s, q, alpha_x, alpha_y)
    
    # Solve the BVP with guided boundary conditions
    try:
        solution = solve_bvp(ode_wrapper, beam_bc_guided, s, q_init, 
                             tol=1e-6, max_nodes=5000, verbose=0)
        
        if solution.success:
            # Evaluate solution on a fine mesh
            s_fine = np.linspace(0, 1, n_points)
            q_fine = solution.sol(s_fine)
            
            x_bar = q_fine[0]
            y_bar = q_fine[1]
            theta = q_fine[2]
            kappa_bar = q_fine[3]
            
            # The tip moment is the curvature at s=1
            beta = kappa_bar[-1]
            
            return s_fine, x_bar, y_bar, theta, kappa_bar, beta, True
    except Exception as e:
        print(f"Solver error: {e}")
    
    # Return fallback on failure
    return s, q_init[0], q_init[1], q_init[2], q_init[3], 0.0, False


def compute_tip_displacement(alpha_y, alpha_x=0.0):
    """
    Compute the tip displacement (delta) for a given vertical load.
    
    Parameters:
    -----------
    alpha_y : float
        Normalized vertical force
    alpha_x : float
        Normalized horizontal force (default=0)
    
    Returns:
    --------
    delta : float
        Normalized tip displacement (y_bar(1))
    ux : float
        Normalized tip shortening (x_bar(1) - 1)
    beta : float
        Reaction moment at the tip
    """
    s, x, y, theta, kappa, beta, success = solve_guided_beam(alpha_x, alpha_y)
    
    if success:
        return y[-1], x[-1] - 1.0, beta
    else:
        return 0.0, 0.0, 0.0


def plot_beam_shape(alpha_x, alpha_y):
    """
    Plot the deformed shape of the guided beam.
    """
    s, x_bar, y_bar, theta, kappa_bar, beta, success = solve_guided_beam(alpha_x, alpha_y)
    
    if not success:
        print("Failed to solve beam equations")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Guided Beam Solution: αx={alpha_x:.2f}, αy={alpha_y:.2f}', fontsize=14)
    
    # Deformed shape
    ax1 = axes[0, 0]
    ax1.plot(x_bar, y_bar, 'b-', lw=2, label='Deformed Shape')
    ax1.plot([0, 1], [0, 0], 'k--', alpha=0.3, label='Undeformed')
    ax1.set_xlabel('x̄')
    ax1.set_ylabel('ȳ')
    ax1.set_title('Deformed Shape')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Angle distribution
    ax2 = axes[0, 1]
    ax2.plot(s, np.degrees(theta), 'r-', lw=2)
    ax2.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax2.set_xlabel('s̄')
    ax2.set_ylabel('θ (degrees)')
    ax2.set_title('Angle Distribution')
    ax2.grid(True, alpha=0.3)
    
    # Curvature distribution
    ax3 = axes[1, 0]
    ax3.plot(s, kappa_bar, 'g-', lw=2)
    ax3.set_xlabel('s̄')
    ax3.set_ylabel('κ̄')
    ax3.set_title('Curvature Distribution')
    ax3.grid(True, alpha=0.3)
    
    # Info panel
    ax4 = axes[1, 1]
    ax4.axis('off')
    info_text = f"""
    GUIDED BEAM RESULTS
    {'='*30}
    
    Tip Displacement (δ = ȳ(1)):  {y_bar[-1]:.6f}
    Tip Shortening (Ux = x̄(1)-1): {x_bar[-1]-1:.6f}
    Tip Moment (β = κ̄(1)):       {beta:.6f}
    
    Angle at tip (θ(1)):          {np.degrees(theta[-1]):.6f}°
    
    Linear Theory Comparison:
    δ_linear = αy/12 = {alpha_y/12:.6f}
    """
    ax4.text(0.1, 0.9, info_text, fontsize=11, fontfamily='monospace',
             verticalalignment='top', transform=ax4.transAxes)
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print("Guided Beam Solver - Demo")
    print("=" * 40)
    
    # Example: Vertical load
    alpha_y = 5.0
    alpha_x = 0.0
    
    print(f"\nSolving for αx = {alpha_x}, αy = {alpha_y}")
    
    s, x, y, theta, kappa, beta, success = solve_guided_beam(alpha_x, alpha_y)
    
    if success:
        print(f"Tip displacement δ = {y[-1]:.6f}")
        print(f"Tip shortening Ux = {x[-1]-1:.6f}")
        print(f"Tip moment β = {beta:.6f}")
        print(f"Angle at tip = {np.degrees(theta[-1]):.6f}° (should be ~0)")
        print(f"Linear theory: δ_linear = αy/12 = {alpha_y/12:.6f}")
        
        plot_beam_shape(alpha_x, alpha_y)
    else:
        print("Solver failed to converge")
