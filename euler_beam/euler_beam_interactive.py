"""
Interactive Euler Beam Solver with Slider Controls

Allows real-time adjustment of load parameters:
    alpha_x = Fx * L^2 / (E * I)  - normalized horizontal force
    alpha_y = Fy * L^2 / (E * I)  - normalized vertical force
    beta = Mz * L / (E * I)       - normalized moment at free end

Use the sliders to change the load parameters and see the beam shape update instantly.
"""

import numpy as np
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox
import warnings
warnings.filterwarnings('ignore')


class EulerBeamInteractive:
    """Interactive Euler beam solver with slider controls."""
    
    def __init__(self):
        # Initial parameter values
        self.alpha_x = 0.0
        self.alpha_y = -3.0
        self.beta = 0.0
        
        # Parameter ranges for sliders
        self.alpha_x_range = (-10.0, 10.0)
        self.alpha_y_range = (-10.0, 10.0)
        self.beta_range = (-5.0, 5.0)
        
        # Cached solution
        self.s = None
        self.x_bar = None
        self.y_bar = None
        self.theta = None
        self.kappa_bar = None
        
        # Setup the figure and axes
        self.setup_figure()
        
        # Initial solve and plot
        self.solve_and_update()
        
    def beam_ode(self, s, q):
        """ODE system for the normalized Euler beam equations."""
        x_bar, y_bar, theta, kappa_bar = q
        
        dx_bar_ds = np.cos(theta)
        dy_bar_ds = np.sin(theta)
        dtheta_ds = kappa_bar
        # Correct sign: dκ/ds = αx·sin(θ) - αy·cos(θ)
        dkappa_bar_ds = self.alpha_x * np.sin(theta) - self.alpha_y * np.cos(theta)
        
        return np.array([dx_bar_ds, dy_bar_ds, dtheta_ds, dkappa_bar_ds])
    
    def beam_bc(self, qa, qb):
        """Boundary conditions for the beam."""
        return np.array([
            qa[0],              # x_bar(0) = 0
            qa[1],              # y_bar(0) = 0
            qa[2],              # theta(0) = 0
            qb[3] - self.beta   # kappa_bar(1) = beta
        ])
    
    def solve_beam(self, n_points=101):
        """Solve the Euler beam equations for current parameters."""
        # Initial mesh
        s = np.linspace(0, 1, n_points)
        
        # Use previous solution as initial guess if available
        if self.x_bar is not None:
            q_init = np.zeros((4, n_points))
            q_init[0] = np.interp(s, self.s, self.x_bar)
            q_init[1] = np.interp(s, self.s, self.y_bar)
            q_init[2] = np.interp(s, self.s, self.theta)
            q_init[3] = np.interp(s, self.s, self.kappa_bar)
        else:
            # Cold start: straight beam initial guess
            q_init = np.zeros((4, n_points))
            q_init[0] = s
            q_init[1] = 0
            q_init[2] = 0
            q_init[3] = self.beta * s
        
        try:
            solution = solve_bvp(self.beam_ode, self.beam_bc, s, q_init,
                                tol=1e-6, max_nodes=3000, verbose=0)
            
            if solution.success:
                s_fine = np.linspace(0, 1, n_points)
                q_fine = solution.sol(s_fine)
                return s_fine, q_fine[0], q_fine[1], q_fine[2], q_fine[3], True
            else:
                return s, q_init[0], q_init[1], q_init[2], q_init[3], False
        except Exception as e:
            print(f"Solver error: {e}")
            return s, q_init[0], q_init[1], q_init[2], q_init[3], False
    
    def setup_figure(self):
        """Setup the matplotlib figure with sliders."""
        # Create figure with custom layout
        self.fig = plt.figure(figsize=(14, 9))
        self.fig.patch.set_facecolor('#1a1a2e')
        
        # Main plot area
        self.ax_main = self.fig.add_axes([0.08, 0.35, 0.55, 0.55])
        self.ax_main.set_facecolor('#16213e')
        
        # Angle plot
        self.ax_angle = self.fig.add_axes([0.70, 0.55, 0.25, 0.35])
        self.ax_angle.set_facecolor('#16213e')
        
        # Curvature plot
        self.ax_curv = self.fig.add_axes([0.70, 0.10, 0.25, 0.35])
        self.ax_curv.set_facecolor('#16213e')
        
        # Slider axes
        slider_color = '#0f3460'
        slider_left = 0.15
        slider_width = 0.35
        slider_height = 0.025
        
        self.ax_slider_alpha_x = self.fig.add_axes([slider_left, 0.22, slider_width, slider_height])
        self.ax_slider_alpha_y = self.fig.add_axes([slider_left, 0.15, slider_width, slider_height])
        self.ax_slider_beta = self.fig.add_axes([slider_left, 0.08, slider_width, slider_height])
        
        # Create sliders with custom styling
        self.slider_alpha_x = Slider(
            self.ax_slider_alpha_x, r'$\alpha_x$', 
            self.alpha_x_range[0], self.alpha_x_range[1],
            valinit=self.alpha_x, valstep=0.1,
            color='#e94560'
        )
        
        self.slider_alpha_y = Slider(
            self.ax_slider_alpha_y, r'$\alpha_y$',
            self.alpha_y_range[0], self.alpha_y_range[1],
            valinit=self.alpha_y, valstep=0.1,
            color='#00ff88'
        )
        
        self.slider_beta = Slider(
            self.ax_slider_beta, r'$\beta$',
            self.beta_range[0], self.beta_range[1],
            valinit=self.beta, valstep=0.1,
            color='#00d4ff'
        )
        
        # Style slider labels
        for slider in [self.slider_alpha_x, self.slider_alpha_y, self.slider_beta]:
            slider.label.set_color('white')
            slider.label.set_fontsize(14)
            slider.valtext.set_color('white')
            slider.valtext.set_fontsize(12)
        
        # Connect sliders to update function
        self.slider_alpha_x.on_changed(self.on_slider_change)
        self.slider_alpha_y.on_changed(self.on_slider_change)
        self.slider_beta.on_changed(self.on_slider_change)
        
        # Reset button
        self.ax_reset = self.fig.add_axes([0.55, 0.08, 0.08, 0.04])
        self.btn_reset = Button(self.ax_reset, 'Reset', color='#0f3460', hovercolor='#e94560')
        self.btn_reset.label.set_color('white')
        self.btn_reset.on_clicked(self.on_reset)
        
        # Info text area
        self.info_text = self.fig.text(0.08, 0.02, '', fontsize=11, color='white',
                                        fontfamily='monospace')
        
        # Title
        self.fig.suptitle('Interactive Euler Beam Solver', fontsize=18, 
                         fontweight='bold', color='white', y=0.96)
        
    def update_plot(self, converged=True):
        """Update all plots with current solution."""
        # Clear axes
        self.ax_main.clear()
        self.ax_angle.clear()
        self.ax_curv.clear()
        
        # Set background colors
        self.ax_main.set_facecolor('#16213e')
        self.ax_angle.set_facecolor('#16213e')
        self.ax_curv.set_facecolor('#16213e')
        
        # Main beam shape plot
        if converged:
            beam_color = '#00ff88'
            status_text = "✓ Converged"
        else:
            beam_color = '#ff6b6b'
            status_text = "✗ Not Converged"
        
        # Plot beam shape
        self.ax_main.plot(self.x_bar, self.y_bar, color=beam_color, linewidth=3, 
                         label='Beam shape')
        
        # Plot clamped end
        self.ax_main.plot(0, 0, 'o', color='#e94560', markersize=15, 
                         markeredgecolor='white', markeredgewidth=2, zorder=5)
        self.ax_main.plot([-0.05, 0], [0, 0], color='#e94560', linewidth=8)
        
        # Plot tip
        tip_x, tip_y = self.x_bar[-1], self.y_bar[-1]
        self.ax_main.plot(tip_x, tip_y, '^', color='#00d4ff', markersize=12,
                         markeredgecolor='white', markeredgewidth=2, zorder=5)
        
        # Draw force arrows at tip
        arrow_scale = 0.12
        arrow_props = dict(arrowstyle='->', lw=2.5, mutation_scale=15)
        
        if abs(self.alpha_x) > 0.1:
            self.ax_main.annotate('', 
                xy=(tip_x + np.sign(self.alpha_x)*arrow_scale, tip_y),
                xytext=(tip_x, tip_y),
                arrowprops=dict(**arrow_props, color='#e94560'))
            self.ax_main.text(tip_x + np.sign(self.alpha_x)*arrow_scale*1.3, tip_y,
                             r'$F_x$', fontsize=12, color='#e94560', 
                             ha='center', va='center')
        
        if abs(self.alpha_y) > 0.1:
            self.ax_main.annotate('',
                xy=(tip_x, tip_y + np.sign(self.alpha_y)*arrow_scale),
                xytext=(tip_x, tip_y),
                arrowprops=dict(**arrow_props, color='#00ff88'))
            self.ax_main.text(tip_x + 0.05, tip_y + np.sign(self.alpha_y)*arrow_scale*1.3,
                             r'$F_y$', fontsize=12, color='#00ff88',
                             ha='center', va='center')
        
        if abs(self.beta) > 0.1:
            # Draw moment arc
            arc_radius = 0.08
            arc_angles = np.linspace(0, np.sign(self.beta) * np.pi * 0.8, 20)
            arc_x = tip_x + arc_radius * np.cos(arc_angles)
            arc_y = tip_y + arc_radius * np.sin(arc_angles)
            self.ax_main.plot(arc_x, arc_y, color='#00d4ff', linewidth=2)
            self.ax_main.annotate('',
                xy=(arc_x[-1], arc_y[-1]),
                xytext=(arc_x[-2], arc_y[-2]),
                arrowprops=dict(**arrow_props, color='#00d4ff'))
            self.ax_main.text(tip_x + arc_radius*1.5, tip_y + np.sign(self.beta)*0.05,
                             r'$M_z$', fontsize=12, color='#00d4ff')
        
        # Style main plot
        self.ax_main.set_xlabel(r'$\bar{x} = x/L$', fontsize=12, color='white')
        self.ax_main.set_ylabel(r'$\bar{y} = y/L$', fontsize=12, color='white')
        self.ax_main.set_title(f'Beam Deformation  [{status_text}]', fontsize=14, 
                              color='white', fontweight='bold')
        self.ax_main.set_aspect('equal', adjustable='box')
        self.ax_main.grid(True, alpha=0.2, color='white')
        self.ax_main.tick_params(colors='white')
        for spine in self.ax_main.spines.values():
            spine.set_color('white')
        
        # Set axis limits with padding
        x_range = max(self.x_bar) - min(self.x_bar)
        y_range = max(self.y_bar) - min(self.y_bar)
        max_range = max(x_range, y_range, 1.0) * 1.3
        
        x_center = (max(self.x_bar) + min(self.x_bar)) / 2
        y_center = (max(self.y_bar) + min(self.y_bar)) / 2
        
        self.ax_main.set_xlim(-0.15, max(1.1, max(self.x_bar) + 0.2))
        self.ax_main.set_ylim(min(-0.1, min(self.y_bar) - 0.15), 
                              max(0.1, max(self.y_bar) + 0.15))
        
        # Angle distribution plot
        self.ax_angle.plot(self.s, np.degrees(self.theta), color='#ffd93d', linewidth=2)
        self.ax_angle.set_xlabel(r'$\bar{s}$', fontsize=10, color='white')
        self.ax_angle.set_ylabel(r'$\theta$ (deg)', fontsize=10, color='white')
        self.ax_angle.set_title('Angle Distribution', fontsize=11, color='white')
        self.ax_angle.grid(True, alpha=0.2, color='white')
        self.ax_angle.tick_params(colors='white', labelsize=9)
        for spine in self.ax_angle.spines.values():
            spine.set_color('white')
        
        # Curvature distribution plot
        self.ax_curv.plot(self.s, self.kappa_bar, color='#c77dff', linewidth=2)
        self.ax_curv.set_xlabel(r'$\bar{s}$', fontsize=10, color='white')
        self.ax_curv.set_ylabel(r'$\bar{\kappa}$', fontsize=10, color='white')
        self.ax_curv.set_title('Curvature Distribution', fontsize=11, color='white')
        self.ax_curv.grid(True, alpha=0.2, color='white')
        self.ax_curv.tick_params(colors='white', labelsize=9)
        for spine in self.ax_curv.spines.values():
            spine.set_color('white')
        
        # Update info text
        info = (f"Tip Position: (x̄, ȳ) = ({tip_x:.4f}, {tip_y:.4f})   |   "
                f"Tip Angle: θ = {np.degrees(self.theta[-1]):.2f}°   |   "
                f"Root Curvature: κ̄ = {self.kappa_bar[0]:.4f}")
        self.info_text.set_text(info)
        
        self.fig.canvas.draw_idle()
    
    def solve_and_update(self):
        """Solve the beam equations and update the plot."""
        self.s, self.x_bar, self.y_bar, self.theta, self.kappa_bar, converged = self.solve_beam()
        self.update_plot(converged)
    
    def on_slider_change(self, val):
        """Callback when any slider value changes."""
        self.alpha_x = self.slider_alpha_x.val
        self.alpha_y = self.slider_alpha_y.val
        self.beta = self.slider_beta.val
        self.solve_and_update()
    
    def on_reset(self, event):
        """Reset sliders to initial values."""
        self.slider_alpha_x.reset()
        self.slider_alpha_y.reset()
        self.slider_beta.reset()
    
    def run(self):
        """Run the interactive application."""
        plt.show()


def main():
    """Main entry point."""
    print("=" * 60)
    print("Interactive Euler Beam Solver")
    print("=" * 60)
    print("\nUse the sliders to adjust:")
    print("  α_x : Normalized horizontal force (Fx·L²/EI)")
    print("  α_y : Normalized vertical force (Fy·L²/EI)")
    print("  β   : Normalized tip moment (Mz·L/EI)")
    print("\nClose the window to exit.")
    print("=" * 60)
    
    app = EulerBeamInteractive()
    app.run()


if __name__ == "__main__":
    main()
