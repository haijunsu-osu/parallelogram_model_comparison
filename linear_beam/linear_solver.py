import numpy as np

def solve_cantilever(alpha_x, alpha_y, beta, L_over_t=50.0):
    """
    Linear theory for a single cantilever beam under arbitrary tip loads.
    
    Parameters:
    alpha_x : float : Normalized horizontal tip force
    alpha_y : float : Normalized vertical tip force
    beta    : float : Normalized tip moment
    L_over_t: float : Ratio of beam length to thickness (for axial stiffness)
    
    Returns:
    ux, uy, theta : Normalized tip displacements and rotation
    """
    # Normalized axial stiffness k33
    k33 = 12.0 * (L_over_t**2)
    
    ux = alpha_x / k33
    uy = (alpha_y / 3.0) + (beta / 2.0)
    theta = (alpha_y / 2.0) + beta
    
    return ux, uy, theta

def solve_fixed_guided(alpha_x, alpha_y, L_over_t=50.0):
    """
    Linear theory for a single fixed-guided beam (horizontal tip constraint).
    The required moment to keep theta(1)=0 is beta = -alpha_y / 2.
    
    Returns:
    ux, uy, theta : theta is identically zero
    """
    beta = -alpha_y / 2.0
    ux, uy, theta = solve_cantilever(alpha_x, alpha_y, beta, L_over_t)
    return ux, uy, 0.0

def solve_parallelogram(alpha_x, alpha_y, beta_ext=0.0, L_over_t=50.0):
    """
    Linear theory for a parallelogram flexure mechanism (two fixed-guided beams).
    Total stiffness is doubled compared to a single fixed-guided beam.
    
    Returns:
    ux, uy, phi : phi is identically zero
    """
    # Total external load is shared between two beams
    # Equivalent to a single beam under half the load
    ux, uy, theta = solve_fixed_guided(alpha_x / 2.0, alpha_y / 2.0, L_over_t)
    
    # Alternatively: uy = alpha_y / 24.0
    return ux, uy, 0.0

if __name__ == "__main__":
    # Test cases
    print("Linear Beam Theory Consolidation")
    print("=" * 60)
    
    load_ay = 1.0
    load_ax = 0.0
    
    print(f"Testing with alpha_y = {load_ay}, alpha_x = {load_ax}")
    print("-" * 60)
    
    # 1. Cantilever (Pure transverse load)
    ux, uy, theta = solve_cantilever(load_ax, load_ay, 0.0)
    print(f"Cantilever:        uy = {uy:.6f} (expected 0.333333), theta = {theta:.6f}")
    
    # 2. Fixed-Guided (Pure transverse load)
    ux, uy, theta = solve_fixed_guided(load_ax, load_ay)
    print(f"Fixed-Guided:      uy = {uy:.6f} (expected 0.083333), theta = {theta:.6f}")
    
    # 3. Parallelogram (Pure transverse load)
    ux, uy, phi = solve_parallelogram(load_ax, load_ay)
    print(f"Parallelogram:    uy = {uy:.6f} (expected 0.041667), phi   = {phi:.6f}")
    
    print("-" * 60)
    print("Refactoring complete.")
