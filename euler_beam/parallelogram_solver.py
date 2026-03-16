"""
Parallelogram Flexure Mechanism Solver

Solves the coupled beam equations for a parallelogram flexure mechanism
consisting of two identical flexible beams connected by a rigid platform.

External loads: F_x, F_y, M_z (applied at platform center)
Outputs: Platform position (X_p, Y_p), rotation angle φ, internal loads

Sign Convention:
- φ (platform rotation) is positive counter-clockwise (CCW)
- Force F_x positive in +x direction
- Force F_y positive in +y direction  
- Moment M_z positive counter-clockwise
"""

import numpy as np
from scipy.integrate import solve_bvp
from scipy.optimize import fsolve, root
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import FancyArrowPatch, Arc
import warnings
warnings.filterwarnings('ignore')


class ParallelogramFlexureSolver:
    """Solver for parallelogram flexure mechanism."""
    
    def __init__(self, w=0.3):
        """
        Initialize solver.
        
        Parameters:
        -----------
        w : float
            Normalized half beam separation (W/L), default 0.3
            Total separation is 2*W. w = (total_separation/2) / L.
        """
        self.w = w  # Normalized half beam separation (W/L)
        
        # External loads (normalized)
        self.A_x = 0.0   # Normalized horizontal force
        self.A_y = 0.0   # Normalized vertical force
        self.B = 0.0     # Normalized moment
        
        # Internal loads for each beam (solution)
        self.alpha_x1 = 0.0
        self.alpha_y1 = 0.0
        self.beta_1 = 0.0
        self.alpha_x2 = 0.0
        self.alpha_y2 = 0.0
        self.beta_2 = 0.0
        
        # Beam solutions
        self.beam1_solution = None
        self.beam2_solution = None
        
        # Platform state
        self.X_p = 1.0
        self.Y_p = 0.0
        self.phi = 0.0
        
    def beam_ode(self, s, q, alpha_x, alpha_y):
        """ODE system for normalized Euler beam equations."""
        x_bar, y_bar, theta, kappa_bar = q
        
        dx_ds = np.cos(theta)
        dy_ds = np.sin(theta)
        dtheta_ds = kappa_bar
        # Correct sign: dκ/ds = αx·sin(θ) - αy·cos(θ)
        # Positive Fy (upward) → beam curves upward (positive y deflection)
        dkappa_ds = alpha_x * np.sin(theta) - alpha_y * np.cos(theta)
        
        return np.array([dx_ds, dy_ds, dtheta_ds, dkappa_ds])
    
    def beam_bc(self, qa, qb, beta):
        """Boundary conditions: clamped at s=0, moment at s=1."""
        return np.array([
            qa[0],           # x_bar(0) = 0
            qa[1],           # y_bar(0) = 0
            qa[2],           # theta(0) = 0
            qb[3] - beta     # kappa_bar(1) = beta
        ])
    
    def solve_single_beam(self, alpha_x, alpha_y, beta, n_points=101):
        """
        Solve single beam BVP with high precision for capturing subtle nonlinearities.
        
        Returns:
        --------
        s, x_bar, y_bar, theta, kappa_bar, success
        """
        s = np.linspace(0, 1, n_points)
        
        # Initial guess - use cubic polynomial from linear beam theory
        # For fixed-guided beam: y(s) = (3*delta)*s^2 - (2*delta)*s^3, theta(s) = dy/ds
        # where delta ≈ alpha_y / 12 (from linear stiffness)
        delta_est = alpha_y / 12.0 if abs(alpha_y) > 0.01 else 0.0
        
        q_init = np.zeros((4, n_points))
        q_init[0] = s  # x_bar ≈ s (ignore shortening for guess)
        q_init[1] = 3 * delta_est * s**2 - 2 * delta_est * s**3  # Cubic y shape
        q_init[2] = 6 * delta_est * s - 6 * delta_est * s**2  # theta = dy/ds
        # Curvature guess: d(theta)/ds
        q_init[3] = 6 * delta_est - 12 * delta_est * s + beta
        
        def ode(s, q):
            return self.beam_ode(s, q, alpha_x, alpha_y)
        
        def bc(qa, qb):
            return self.beam_bc(qa, qb, beta)
        
        try:
            # Relaxed tolerance for robustness at challenging loads
            sol = solve_bvp(ode, bc, s, q_init, tol=1e-4, max_nodes=5000, verbose=0)
            if sol.success:
                s_fine = np.linspace(0, 1, n_points)
                q_fine = sol.sol(s_fine)
                return s_fine, q_fine[0], q_fine[1], q_fine[2], q_fine[3], True
        except:
            pass
        
        # Retry with denser initial mesh
        try:
            s_dense = np.linspace(0, 1, 201)
            q_dense = np.zeros((4, 201))
            q_dense[0] = s_dense
            q_dense[1] = 3 * delta_est * s_dense**2 - 2 * delta_est * s_dense**3
            q_dense[2] = 6 * delta_est * s_dense - 6 * delta_est * s_dense**2
            q_dense[3] = 6 * delta_est - 12 * delta_est * s_dense + beta
            
            sol = solve_bvp(ode, bc, s_dense, q_dense, tol=1e-3, max_nodes=10000, verbose=0)
            if sol.success:
                s_fine = np.linspace(0, 1, n_points)
                q_fine = sol.sol(s_fine)
                return s_fine, q_fine[0], q_fine[1], q_fine[2], q_fine[3], True
        except:
            pass
        
        # Return initial guess if failed
        return s, q_init[0], q_init[1], q_init[2], q_init[3], False
    
    def constraint_residuals(self, params):
        """
        Compute residuals of the 6 constraint equations.
        
        Parameters:
        -----------
        params : array-like, shape (6,)
            [alpha_x1, alpha_y1, beta_1, alpha_x2, alpha_y2, beta_2]
        
        Returns:
        --------
        residuals : array, shape (6,)
        """
        alpha_x1, alpha_y1, beta_1, alpha_x2, alpha_y2, beta_2 = params
        
        # Solve both beams
        s1, x1, y1, theta1, kappa1, ok1 = self.solve_single_beam(alpha_x1, alpha_y1, beta_1)
        s2, x2, y2, theta2, kappa2, ok2 = self.solve_single_beam(alpha_x2, alpha_y2, beta_2)
        
        # Get tip states
        x1_tip, y1_tip, theta1_tip = x1[-1], y1[-1], theta1[-1]
        x2_tip, y2_tip, theta2_tip = x2[-1], y2[-1], theta2[-1]
        
        # Platform angle (from angle compatibility)
        phi = (theta1_tip + theta2_tip) / 2  # Average for stability
        
        # Constraint equations
        # 1. Angle compatibility: theta1(1) = theta2(1)
        r1 = theta1_tip - theta2_tip
        
        # 2. x-position compatibility: x1(1) - x2(1) = -2w*sin(phi)
        r2 = (x1_tip - x2_tip) - (-2 * self.w * np.sin(phi))
        
        # 3. y-position compatibility: y1(1) - y2(1) = 2w*(cos(phi) - 1)
        # Assuming beams are at global y = +w and -w.
        # Deflection relationship: (w + y1) - (-w + y2) = 2w * cos(phi)
        r3 = (y1_tip - y2_tip) - (2 * self.w * (np.cos(phi) - 1))
        
        # 4. Horizontal force equilibrium: alpha_x1 + alpha_x2 = A_x
        r4 = alpha_x1 + alpha_x2 - self.A_x
        
        # 5. Vertical force equilibrium: alpha_y1 + alpha_y2 = A_y
        r5 = alpha_y1 + alpha_y2 - self.A_y
        
        # 6. Moment equilibrium
        delta_alpha_x = alpha_x1 - alpha_x2
        delta_alpha_y = alpha_y1 - alpha_y2
        r6 = (beta_1 + beta_2 - 
              self.w * np.cos(phi) * delta_alpha_x - 
              self.w * np.sin(phi) * delta_alpha_y - self.B)
        
        return np.array([r1, r2, r3, r4, r5, r6])
    
    def solve(self, A_x=0.0, A_y=0.0, B=0.0, initial_guess=None):
        """
        Solve the parallelogram mechanism for given external loads.
        
        Parameters:
        -----------
        A_x : float
            Normalized horizontal force (F_x * L^2 / EI)
        A_y : float
            Normalized vertical force (F_y * L^2 / EI)
        B : float
            Normalized moment (M_z * L / EI)
        initial_guess : array-like, optional
            Initial guess for [alpha_x1, alpha_y1, beta_1, alpha_x2, alpha_y2, beta_2]
        
        Returns:
        --------
        success : bool
        """
        self.A_x = A_x
        self.A_y = A_y
        self.B = B
        
        # Try multiple initial guesses and solver methods for robustness
        initial_guesses = []
        
        # Primary guess: divide external loads equally (symmetric)
        initial_guesses.append(np.array([
            A_x / 2,  # alpha_x1
            A_y / 2,  # alpha_y1
            -A_y / 4, # beta_1 (estimated from fixed-guided constraint)
            A_x / 2,  # alpha_x2
            A_y / 2,  # alpha_y2
            -A_y / 4  # beta_2
        ]))
        
        # Use provided initial guess if available
        if initial_guess is not None:
            initial_guesses.insert(0, initial_guess)
        
        # Secondary guess: zero internal loads
        initial_guesses.append(np.zeros(6))
        
        # Try different solver methods
        methods = ['hybr', 'lm', 'broyden1']
        
        best_result = None
        best_residual = float('inf')
        
        for guess in initial_guesses:
            for method in methods:
                try:
                    result = root(self.constraint_residuals, guess, 
                                 method=method, tol=1e-8)
                    
                    max_residual = np.max(np.abs(result.fun))
                    
                    if max_residual < best_residual:
                        best_residual = max_residual
                        best_result = result
                    
                    # If we found a good solution, stop early
                    if max_residual < 1e-6:
                        break
                except:
                    continue
            
            if best_residual < 1e-6:
                break
        
        # Use the best result found
        if best_result is not None and best_residual < 1e-3:
            params = best_result.x
            self.alpha_x1 = params[0]
            self.alpha_y1 = params[1]
            self.beta_1 = params[2]
            self.alpha_x2 = params[3]
            self.alpha_y2 = params[4]
            self.beta_2 = params[5]
            
            # Solve beams with final parameters
            self.beam1_solution = self.solve_single_beam(
                self.alpha_x1, self.alpha_y1, self.beta_1)
            self.beam2_solution = self.solve_single_beam(
                self.alpha_x2, self.alpha_y2, self.beta_2)
            
            # Compute platform state
            x1_tip = self.beam1_solution[1][-1]
            y1_tip = self.beam1_solution[2][-1]
            theta1_tip = self.beam1_solution[3][-1]
            
            x2_tip = self.beam2_solution[1][-1]
            y2_tip = self.beam2_solution[2][-1]
            theta2_tip = self.beam2_solution[3][-1]
            
            self.phi = (theta1_tip + theta2_tip) / 2
            self.X_p = (x1_tip + x2_tip) / 2
            self.Y_p = (y1_tip + y2_tip) / 2
            
            # Validate that BVP actually succeeded for final solution
            ok1 = self.beam1_solution[5]
            ok2 = self.beam2_solution[5]
            if not ok1 or not ok2:
                return False  # BVP failed, reject this solution
            
            return best_residual < 1e-6
        
        return False
    
    def get_results_summary(self):
        """Get a summary of the solution."""
        return {
            'platform': {
                'X_p': self.X_p,
                'Y_p': self.Y_p,
                'phi_rad': self.phi,
                'phi_deg': np.degrees(self.phi)
            },
            'beam1': {
                'alpha_x': self.alpha_x1,
                'alpha_y': self.alpha_y1,
                'beta': self.beta_1,
                'x_tip': self.beam1_solution[1][-1] if self.beam1_solution else None,
                'y_tip': self.beam1_solution[2][-1] if self.beam1_solution else None,
                'theta_tip_deg': np.degrees(self.beam1_solution[3][-1]) if self.beam1_solution else None
            },
            'beam2': {
                'alpha_x': self.alpha_x2,
                'alpha_y': self.alpha_y2,
                'beta': self.beta_2,
                'x_tip': self.beam2_solution[1][-1] if self.beam2_solution else None,
                'y_tip': self.beam2_solution[2][-1] if self.beam2_solution else None,
                'theta_tip_deg': np.degrees(self.beam2_solution[3][-1]) if self.beam2_solution else None
            }
        }
    
    def get_linear_theory_prediction(self, A_x, A_y, B):
        """
        Compute small deflection (linear) beam theory prediction.
        
        Assumptions:
        - Two beams carry identical load (Fy/2 each)
        - No axial load effect (Fx = 0)
        - Platform does not rotate (fixed-guided constraint)
        - Each beam acts as fixed-guided (clamped-guided) beam
        
        For a fixed-guided beam with tip load P:
        - Tip deflection: δ = PL³/(12EI)
        - Tip angle: θ = 0 (guided constraint)
        - Required tip moment: M = -PL/2
        
        In normalized form:
        - αy_per_beam = A_y / 2
        - ȳ_tip = αy_per_beam / 12 = A_y / 24
        - x-deflection: zero (no rotation, straight line motion)
        
        Returns:
        --------
        dict with linear theory predictions
        """
        # Each beam carries half the vertical load
        alpha_y_per_beam = A_y / 2
        
        # Fixed-guided beam tip deflection (normalized)
        # δ/L = (P*L²)/(12*EI) = α_y / 12
        y_tip_linear = alpha_y_per_beam / 12.0
        
        # Platform y-deflection (same as beam tip for parallel motion)
        Y_p_linear = y_tip_linear
        
        # For fixed-guided constraint, x-deflection is approximately:
        # Δx ≈ 0 for small deflection (purely vertical motion)
        X_p_linear = 1.0  # Remains at x = L = 1 (normalized)
        
        # Platform rotation = 0 (parallel motion assumption)
        phi_linear = 0.0
        
        # Required moment at each beam tip to enforce zero rotation
        # For cantilever with load P and tip moment M:
        # θ_tip = PL²/(2EI) + ML/(EI) = 0
        # M = -PL/2
        # In normalized form: β = M*L/(EI) = -P*L²/(2*EI) = -α_y/2
        beta_per_beam = -alpha_y_per_beam / 2.0
        
        return {
            'Y_p_linear': Y_p_linear,
            'X_p_linear': X_p_linear,
            'phi_linear': phi_linear,
            'alpha_y_per_beam': alpha_y_per_beam,
            'beta_per_beam': beta_per_beam,
            'y_tip_per_beam': y_tip_linear
        }


class ParallelogramInteractive:
    """Interactive visualization for parallelogram flexure mechanism."""
    
    def __init__(self, w=0.3):
        """Initialize interactive visualization."""
        self.solver = ParallelogramFlexureSolver(w=w)
        self.w = w
        
        # Load ranges
        self.A_x_range = (-5.0, 5.0)
        self.A_y_range = (-10.0, 10.0)
        self.B_range = (-3.0, 3.0)
        
        # Current loads
        self.A_x = 0.0
        self.A_y = 0.0
        self.B = 0.0
        
        self.setup_figure()
        self.update()
        
    def setup_figure(self):
        """Setup matplotlib figure with sliders."""
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.patch.set_facecolor('#1a1a2e')
        
        # Main mechanism plot
        self.ax_main = self.fig.add_axes([0.05, 0.35, 0.55, 0.55])
        self.ax_main.set_facecolor('#16213e')
        
        # Info panel
        self.ax_info = self.fig.add_axes([0.65, 0.35, 0.30, 0.55])
        self.ax_info.set_facecolor('#16213e')
        
        # Slider axes
        slider_left = 0.15
        slider_width = 0.35
        slider_height = 0.025
        
        self.ax_slider_Ax = self.fig.add_axes([slider_left, 0.22, slider_width, slider_height])
        self.ax_slider_Ay = self.fig.add_axes([slider_left, 0.15, slider_width, slider_height])
        self.ax_slider_B = self.fig.add_axes([slider_left, 0.08, slider_width, slider_height])
        
        # Create sliders
        self.slider_Ax = Slider(
            self.ax_slider_Ax, r'$A_x$ (Force)', 
            self.A_x_range[0], self.A_x_range[1],
            valinit=0.0, valstep=0.1, color='#e94560'
        )
        self.slider_Ay = Slider(
            self.ax_slider_Ay, r'$A_y$ (Force)',
            self.A_y_range[0], self.A_y_range[1],
            valinit=0.0, valstep=0.1, color='#00ff88'
        )
        self.slider_B = Slider(
            self.ax_slider_B, r'$B$ (Moment)',
            self.B_range[0], self.B_range[1],
            valinit=0.0, valstep=0.1, color='#00d4ff'
        )
        
        # Style sliders
        for slider in [self.slider_Ax, self.slider_Ay, self.slider_B]:
            slider.label.set_color('white')
            slider.label.set_fontsize(12)
            slider.valtext.set_color('white')
            slider.valtext.set_fontsize(11)
        
        # Connect sliders
        self.slider_Ax.on_changed(self.on_slider_change)
        self.slider_Ay.on_changed(self.on_slider_change)
        self.slider_B.on_changed(self.on_slider_change)
        
        # Reset button
        self.ax_reset = self.fig.add_axes([0.55, 0.08, 0.08, 0.04])
        self.btn_reset = Button(self.ax_reset, 'Reset', color='#0f3460', hovercolor='#e94560')
        self.btn_reset.label.set_color('white')
        self.btn_reset.on_clicked(self.on_reset)
        
        # Title
        self.fig.suptitle('Parallelogram Flexure Mechanism Solver', 
                         fontsize=18, fontweight='bold', color='white', y=0.96)
        
        # Status text
        self.status_text = self.fig.text(0.05, 0.02, '', fontsize=10, color='white')
    
    def update(self):
        """Solve and update visualization."""
        self.A_x = self.slider_Ax.val
        self.A_y = self.slider_Ay.val
        self.B = self.slider_B.val
        
        # Use previous solution as initial guess
        if self.solver.beam1_solution is not None:
            initial_guess = np.array([
                self.solver.alpha_x1, self.solver.alpha_y1, self.solver.beta_1,
                self.solver.alpha_x2, self.solver.alpha_y2, self.solver.beta_2
            ])
        else:
            initial_guess = None
        
        success = self.solver.solve(self.A_x, self.A_y, self.B, initial_guess)
        
        self.plot_mechanism(success)
        self.plot_info(success)
        
        status = "✓ Solution converged" if success else "✗ Solution did not converge"
        self.status_text.set_text(f"Status: {status}  |  w = {self.w:.2f}")
        
        self.fig.canvas.draw_idle()
    
    def plot_mechanism(self, converged):
        """Plot the mechanism configuration."""
        self.ax_main.clear()
        self.ax_main.set_facecolor('#16213e')
        
        w = self.w
        
        # Get beam solutions
        if self.solver.beam1_solution is not None:
            s1, x1, y1, theta1, kappa1, _ = self.solver.beam1_solution
            s2, x2, y2, theta2, kappa2, _ = self.solver.beam2_solution
            
            # Transform to global coordinates
            # Beam 1: origin at (0, w)
            X1 = x1
            Y1 = w + y1
            
            # Beam 2: origin at (0, -w)
            X2 = x2
            Y2 = -w + y2
            
            beam_color = '#00ff88' if converged else '#ff6b6b'
        else:
            # Undeformed configuration
            X1 = np.linspace(0, 1, 50)
            Y1 = np.ones_like(X1) * w
            X2 = np.linspace(0, 1, 50)
            Y2 = np.ones_like(X2) * (-w)
            beam_color = '#888888'
        
        # Draw ground/fixed support
        self.ax_main.fill([-0.08, 0, 0, -0.08], [-w-0.3, -w-0.3, w+0.3, w+0.3], 
                         color='#4a4a6a', hatch='///')
        self.ax_main.plot([0, 0], [-w-0.3, w+0.3], 'w-', linewidth=3)
        
        # Draw beams
        self.ax_main.plot(X1, Y1, color=beam_color, linewidth=3, label='Beam 1 (upper)')
        self.ax_main.plot(X2, Y2, color=beam_color, linewidth=3, label='Beam 2 (lower)')
        
        # Draw undeformed configuration (dashed)
        self.ax_main.plot([0, 1], [w, w], '--', color='#666666', linewidth=1, alpha=0.5)
        self.ax_main.plot([0, 1], [-w, -w], '--', color='#666666', linewidth=1, alpha=0.5)
        self.ax_main.plot([1, 1], [-w, w], '--', color='#666666', linewidth=1, alpha=0.5)
        
        # Draw platform
        tip1 = (X1[-1], Y1[-1])
        tip2 = (X2[-1], Y2[-1])
        platform_x = [tip2[0], tip1[0]]
        platform_y = [tip2[1], tip1[1]]
        self.ax_main.plot(platform_x, platform_y, color='#ff6b6b', linewidth=5, 
                         solid_capstyle='round')
        
        # Draw platform center
        center_x = (tip1[0] + tip2[0]) / 2
        center_y = (tip1[1] + tip2[1]) / 2
        self.ax_main.plot(center_x, center_y, 'o', color='yellow', markersize=10,
                         markeredgecolor='white', markeredgewidth=2, zorder=10)
        
        # Draw beam tips
        self.ax_main.plot(tip1[0], tip1[1], 's', color='#00d4ff', markersize=8,
                         markeredgecolor='white', markeredgewidth=1.5)
        self.ax_main.plot(tip2[0], tip2[1], 's', color='#00d4ff', markersize=8,
                         markeredgecolor='white', markeredgewidth=1.5)
        
        # Draw clamped ends
        self.ax_main.plot(0, w, 'o', color='#e94560', markersize=12,
                         markeredgecolor='white', markeredgewidth=2)
        self.ax_main.plot(0, -w, 'o', color='#e94560', markersize=12,
                         markeredgecolor='white', markeredgewidth=2)
        
        # Draw external forces
        arrow_scale = 0.15
        
        if abs(self.A_x) > 0.1:
            dx = np.sign(self.A_x) * arrow_scale * min(abs(self.A_x), 3) / 3
            self.ax_main.annotate('', xy=(center_x + dx, center_y),
                                 xytext=(center_x, center_y),
                                 arrowprops=dict(arrowstyle='->', color='#e94560', lw=3))
            self.ax_main.text(center_x + dx*1.3, center_y + 0.02, f'$F_x$',
                             fontsize=12, color='#e94560', ha='center')
        
        if abs(self.A_y) > 0.1:
            dy = np.sign(self.A_y) * arrow_scale * min(abs(self.A_y), 3) / 3
            self.ax_main.annotate('', xy=(center_x, center_y + dy),
                                 xytext=(center_x, center_y),
                                 arrowprops=dict(arrowstyle='->', color='#00ff88', lw=3))
            self.ax_main.text(center_x + 0.05, center_y + dy*1.3, f'$F_y$',
                             fontsize=12, color='#00ff88', ha='center')
        
        if abs(self.B) > 0.1:
            # Draw moment arc - CCW is positive
            arc_r = 0.08
            if self.B > 0:
                # Positive moment: CCW arc (counterclockwise)
                arc = Arc((center_x, center_y), 2*arc_r, 2*arc_r, 
                         angle=0, theta1=-60, theta2=60, color='#00d4ff', lw=2)
                self.ax_main.add_patch(arc)
                # Arrow at end pointing CCW (upward on left side)
                arrow_angle = np.radians(60)
                arrow_dir = np.radians(60 + 90)  # Tangent direction (CCW)
                self.ax_main.annotate('', 
                    xy=(center_x + arc_r*np.cos(arrow_angle) + 0.015*np.cos(arrow_dir),
                        center_y + arc_r*np.sin(arrow_angle) + 0.015*np.sin(arrow_dir)),
                    xytext=(center_x + arc_r*np.cos(arrow_angle), 
                            center_y + arc_r*np.sin(arrow_angle)),
                    arrowprops=dict(arrowstyle='->', color='#00d4ff', lw=2))
            else:
                # Negative moment: CW arc (clockwise)
                arc = Arc((center_x, center_y), 2*arc_r, 2*arc_r,
                         angle=0, theta1=-60, theta2=60, color='#00d4ff', lw=2)
                self.ax_main.add_patch(arc)
                # Arrow at end pointing CW (downward on left side)
                arrow_angle = np.radians(-60)
                arrow_dir = np.radians(-60 - 90)  # Tangent direction (CW)
                self.ax_main.annotate('', 
                    xy=(center_x + arc_r*np.cos(arrow_angle) + 0.015*np.cos(arrow_dir),
                        center_y + arc_r*np.sin(arrow_angle) + 0.015*np.sin(arrow_dir)),
                    xytext=(center_x + arc_r*np.cos(arrow_angle), 
                            center_y + arc_r*np.sin(arrow_angle)),
                    arrowprops=dict(arrowstyle='->', color='#00d4ff', lw=2))
            self.ax_main.text(center_x + 0.12, center_y + 0.02, f'$M_z$',
                             fontsize=12, color='#00d4ff')
        
        # Labels and styling
        self.ax_main.set_xlabel(r'$\bar{x} = x/L$', fontsize=12, color='white')
        self.ax_main.set_ylabel(r'$\bar{y} = y/L$', fontsize=12, color='white')
        self.ax_main.set_title('Mechanism Configuration', fontsize=14, 
                              color='white', fontweight='bold')
        self.ax_main.set_aspect('equal')
        self.ax_main.grid(True, alpha=0.2, color='white')
        self.ax_main.tick_params(colors='white')
        for spine in self.ax_main.spines.values():
            spine.set_color('white')
        
        # Set limits with padding
        all_x = np.concatenate([X1, X2])
        all_y = np.concatenate([Y1, Y2])
        x_margin = 0.2
        y_margin = 0.15
        self.ax_main.set_xlim(-0.15, max(1.2, np.max(all_x) + x_margin))
        self.ax_main.set_ylim(min(-w - y_margin, np.min(all_y) - y_margin),
                             max(w + y_margin, np.max(all_y) + y_margin))
        
        self.ax_main.legend(loc='upper left', fontsize=9, 
                           facecolor='#16213e', edgecolor='white', labelcolor='white')
    
    def plot_info(self, converged):
        """Plot information panel."""
        self.ax_info.clear()
        self.ax_info.set_facecolor('#16213e')
        self.ax_info.axis('off')
        
        results = self.solver.get_results_summary()
        linear = self.solver.get_linear_theory_prediction(self.A_x, self.A_y, self.B)
        
        # Title
        self.ax_info.text(0.5, 0.98, 'Solution Summary', fontsize=14, 
                         fontweight='bold', color='white', ha='center',
                         transform=self.ax_info.transAxes)
        
        # Platform results
        y_pos = 0.90
        self.ax_info.text(0.05, y_pos, '─── Platform (Large Deflection) ───', fontsize=11, 
                         color='#ff6b6b', fontweight='bold',
                         transform=self.ax_info.transAxes)
        y_pos -= 0.055
        
        platform = results['platform']
        self.ax_info.text(0.05, y_pos, f"Position: X̄ₚ = {platform['X_p']:.4f}", 
                         fontsize=10, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.04
        self.ax_info.text(0.05, y_pos, f"          Ȳₚ = {platform['Y_p']:.4f}", 
                         fontsize=10, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.04
        self.ax_info.text(0.05, y_pos, f"Rotation: φ = {platform['phi_deg']:.3f}°", 
                         fontsize=10, color='yellow', transform=self.ax_info.transAxes)
        
        # Linear Theory Comparison
        y_pos -= 0.07
        self.ax_info.text(0.05, y_pos, '─── Small Deflection Theory ───', fontsize=11,
                         color='#ffa500', fontweight='bold',
                         transform=self.ax_info.transAxes)
        y_pos -= 0.055
        
        self.ax_info.text(0.05, y_pos, f"Ȳₚ (linear) = {linear['Y_p_linear']:.4f}", 
                         fontsize=10, color='#ffa500', transform=self.ax_info.transAxes)
        y_pos -= 0.04
        self.ax_info.text(0.05, y_pos, f"φ (linear)  = 0° (assumed)", 
                         fontsize=10, color='#ffa500', transform=self.ax_info.transAxes)
        y_pos -= 0.04
        
        # Compute error
        if abs(linear['Y_p_linear']) > 1e-6:
            y_error = (platform['Y_p'] - linear['Y_p_linear']) / abs(linear['Y_p_linear']) * 100
            self.ax_info.text(0.05, y_pos, f"Ȳₚ Error: {y_error:+.1f}%", 
                             fontsize=10, color='#ff6b6b' if abs(y_error) > 10 else '#aaaaaa',
                             transform=self.ax_info.transAxes)
        else:
            self.ax_info.text(0.05, y_pos, f"(No vertical load)", 
                             fontsize=10, color='#aaaaaa', transform=self.ax_info.transAxes)
        y_pos -= 0.04
        self.ax_info.text(0.05, y_pos, f"β (linear)  = {linear['beta_per_beam']:.4f} per beam", 
                         fontsize=9, color='#aaaaaa', transform=self.ax_info.transAxes)
        
        # Beam 1 results (detailed)
        y_pos -= 0.065
        self.ax_info.text(0.05, y_pos, '─── Beam 1 (Upper) ───', fontsize=11,
                         color='#00ff88', fontweight='bold',
                         transform=self.ax_info.transAxes)
        y_pos -= 0.04
        
        beam1 = results['beam1']
        self.ax_info.text(0.05, y_pos, f"αₓ₁ = {beam1['alpha_x']:+.4f}  (axial)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"αᵧ₁ = {beam1['alpha_y']:+.4f}  (transverse)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"β₁  = {beam1['beta']:+.4f}  (moment, +CCW)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        if beam1['x_tip'] is not None:
            self.ax_info.text(0.05, y_pos, f"Tip: ({beam1['x_tip']:.4f}, {beam1['y_tip']:.4f})  θ={beam1['theta_tip_deg']:.2f}°", 
                             fontsize=9, color='#aaaaaa', transform=self.ax_info.transAxes)
        
        # Beam 2 results (detailed)
        y_pos -= 0.055
        self.ax_info.text(0.05, y_pos, '─── Beam 2 (Lower) ───', fontsize=11,
                         color='#00ff88', fontweight='bold',
                         transform=self.ax_info.transAxes)
        y_pos -= 0.04
        
        beam2 = results['beam2']
        self.ax_info.text(0.05, y_pos, f"αₓ₂ = {beam2['alpha_x']:+.4f}  (axial)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"αᵧ₂ = {beam2['alpha_y']:+.4f}  (transverse)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"β₂  = {beam2['beta']:+.4f}  (moment, +CCW)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        if beam2['x_tip'] is not None:
            self.ax_info.text(0.05, y_pos, f"Tip: ({beam2['x_tip']:.4f}, {beam2['y_tip']:.4f})  θ={beam2['theta_tip_deg']:.2f}°", 
                             fontsize=9, color='#aaaaaa', transform=self.ax_info.transAxes)
        
        # External loads with more detail
        y_pos -= 0.055
        self.ax_info.text(0.05, y_pos, '─── External Loads (on platform) ───', fontsize=11,
                         color='#00d4ff', fontweight='bold',
                         transform=self.ax_info.transAxes)
        y_pos -= 0.04
        self.ax_info.text(0.05, y_pos, f"Aₓ = {self.A_x:+.2f}  (+right)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"Aᵧ = {self.A_y:+.2f}  (+up)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)
        y_pos -= 0.032
        self.ax_info.text(0.05, y_pos, f"B  = {self.B:+.2f}  (+CCW)", 
                         fontsize=9, color='white', transform=self.ax_info.transAxes)

    
    def on_slider_change(self, val):
        """Handle slider changes."""
        self.update()
    
    def on_reset(self, event):
        """Reset sliders."""
        self.slider_Ax.reset()
        self.slider_Ay.reset()
        self.slider_B.reset()
    
    def run(self):
        """Run the interactive application."""
        plt.show()


def main():
    """Main entry point."""
    print("=" * 70)
    print("PARALLELOGRAM FLEXURE MECHANISM SOLVER")
    print("=" * 70)
    print()
    print("Interactive solver for a parallel-guided flexure stage.")
    print()
    print("Use the sliders to adjust:")
    print("  A_x : Normalized horizontal force (F_x·L²/EI)")
    print("  A_y : Normalized vertical force (F_y·L²/EI)")
    print("  B   : Normalized moment (M_z·L/EI)")
    print()
    print("Sign Convention:")
    print("  - Platform rotation φ is positive CCW (counter-clockwise)")
    print("  - Forces positive in +x, +y directions")
    print("  - Moment positive CCW")
    print()
    print("Close the window to exit.")
    print("=" * 70)
    
    # Create and run interactive app
    app = ParallelogramInteractive(w=0.3)
    app.run()


if __name__ == "__main__":
    main()
