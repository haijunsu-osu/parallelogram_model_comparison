"""
Interactive GUI for Guided Beam Solver

Provides an interactive visualization for exploring the behavior of a 
fixed-guided beam under various loading conditions.

The "guided" boundary condition constrains the tip to remain flat (θ(1)=0),
while the tip moment (β) is an unknown reaction.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from guided_beam_solver import solve_guided_beam

class GuidedBeamInteractive:
    def __init__(self):
        # Initial load parameters
        self.alpha_x = 0.0
        self.alpha_y = 5.0
        
        # Dark theme colors
        self.colors = {
            'bg': '#1a1a2e',
            'plot_bg': '#16213e',
            'text': '#ffffff',
            'beam': '#00ff88',
            'straight': '#ffffff',
            'slider_bg': '#0f3460'
        }
        
        self.setup_figure()
        self.update(None)
        
    def setup_figure(self):
        # Create figure with dark theme
        self.fig = plt.figure(figsize=(14, 9))
        self.fig.patch.set_facecolor(self.colors['bg'])
        self.fig.canvas.manager.set_window_title("Guided Beam Solver - Interactive")
        
        # Main plot for beam shape
        self.ax_shape = self.fig.add_axes([0.08, 0.40, 0.40, 0.50])
        self.ax_shape.set_facecolor(self.colors['plot_bg'])
        self.ax_shape.set_title('Deformed Beam Shape', color='white', fontsize=14)
        
        # Angle distribution plot
        self.ax_angle = self.fig.add_axes([0.55, 0.55, 0.40, 0.35])
        self.ax_angle.set_facecolor(self.colors['plot_bg'])
        self.ax_angle.set_title('Angle Distribution θ(s)', color='white', fontsize=12)
        
        # Curvature distribution plot
        self.ax_kappa = self.fig.add_axes([0.55, 0.10, 0.40, 0.35])
        self.ax_kappa.set_facecolor(self.colors['plot_bg'])
        self.ax_kappa.set_title('Curvature Distribution κ̄(s)', color='white', fontsize=12)
        
        # Style axes
        for ax in [self.ax_shape, self.ax_angle, self.ax_kappa]:
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            ax.grid(True, linestyle=':', alpha=0.3, color='white')
        
        self.ax_shape.set_xlabel('x̄', color='white')
        self.ax_shape.set_ylabel('ȳ', color='white')
        self.ax_angle.set_xlabel('s̄', color='white')
        self.ax_angle.set_ylabel('θ (deg)', color='white')
        self.ax_kappa.set_xlabel('s̄', color='white')
        self.ax_kappa.set_ylabel('κ̄', color='white')
        
        # Plot lines
        self.line_beam, = self.ax_shape.plot([], [], '-', color=self.colors['beam'], lw=3, label='Guided Beam')
        self.line_straight, = self.ax_shape.plot([0, 1], [0, 0], '--', color='gray', alpha=0.5, lw=1, label='Undeformed')
        
        # Markers for endpoints
        self.marker_base, = self.ax_shape.plot([0], [0], 's', color='white', markersize=10)
        self.marker_tip, = self.ax_shape.plot([1], [0], 'o', color=self.colors['beam'], markersize=10)
        
        # Angle and curvature lines
        self.line_angle, = self.ax_angle.plot([], [], '-', color='#e94560', lw=2)
        self.line_kappa, = self.ax_kappa.plot([], [], '-', color='#f1c40f', lw=2)
        
        # Add legend
        self.ax_shape.legend(facecolor=self.colors['plot_bg'], edgecolor='white', 
                            labelcolor='white', loc='upper right')
        
        # Results text
        self.text_results = self.fig.text(0.08, 0.35, '', color='white', fontsize=11,
                                          fontfamily='monospace', verticalalignment='top')
        
        # Sliders
        slider_left = 0.15
        slider_width = 0.30
        
        ax_ay = self.fig.add_axes([slider_left, 0.18, slider_width, 0.03])
        ax_ax = self.fig.add_axes([slider_left, 0.12, slider_width, 0.03])
        
        # Style sliders
        def style_slider(s, color):
            s.poly.set_facecolor(color)
            s.label.set_color('white')
            s.valtext.set_color('white')
        
        self.s_ay = Slider(ax_ay, 'αy', -15.0, 15.0, valinit=self.alpha_y, valstep=0.1)
        self.s_ax = Slider(ax_ax, 'αx', -10.0, 10.0, valinit=self.alpha_x, valstep=0.1)
        
        style_slider(self.s_ay, '#e94560')
        style_slider(self.s_ax, '#00ff88')
        
        ax_ay.set_facecolor(self.colors['slider_bg'])
        ax_ax.set_facecolor(self.colors['slider_bg'])
        
        # Connect sliders
        self.s_ay.on_changed(self.update)
        self.s_ax.on_changed(self.update)
        
        # Reset button
        ax_reset = self.fig.add_axes([0.08, 0.04, 0.12, 0.04])
        self.btn_reset = Button(ax_reset, 'Reset', color=self.colors['slider_bg'], hovercolor='#2a2a5e')
        self.btn_reset.label.set_color('white')
        self.btn_reset.on_clicked(self.reset)
        
        # Title
        self.fig.text(0.5, 0.97, 'Fixed-Guided Beam: Tip constrained to be flat (θ(1)=0)', 
                     ha='center', va='top', fontsize=16, color='white', fontweight='bold')
        
    def update(self, val):
        alpha_y = self.s_ay.val
        alpha_x = self.s_ax.val
        
        # Solve guided beam
        s, x, y, theta, kappa, beta, success = solve_guided_beam(alpha_x, alpha_y)
        
        if success:
            # Update beam shape
            self.line_beam.set_data(x, y)
            self.marker_tip.set_data([x[-1]], [y[-1]])
            
            # Update angle plot
            self.line_angle.set_data(s, np.degrees(theta))
            
            # Update curvature plot
            self.line_kappa.set_data(s, kappa)
            
            # Update plot limits
            y_max = max(abs(y.max()), abs(y.min()), 0.1)
            self.ax_shape.set_xlim(-0.1, 1.3)
            self.ax_shape.set_ylim(-y_max - 0.1, y_max + 0.1)
            self.ax_shape.set_aspect('equal')
            
            self.ax_angle.set_xlim(0, 1)
            theta_max = max(abs(np.degrees(theta).max()), abs(np.degrees(theta).min()), 1)
            self.ax_angle.set_ylim(-theta_max * 1.2, theta_max * 1.2)
            
            self.ax_kappa.set_xlim(0, 1)
            kappa_max = max(abs(kappa.max()), abs(kappa.min()), 0.1)
            self.ax_kappa.set_ylim(-kappa_max * 1.2, kappa_max * 1.2)
            
            # Linear theory comparison
            delta_linear = alpha_y / 12.0
            
            # Update results text
            results = f"""GUIDED BEAM RESULTS
{'='*35}
Tip Displacement δ:    {y[-1]:+.6f}
Tip Shortening Ux:     {x[-1]-1:+.6f}
Tip Moment β:          {beta:+.6f}
Angle at tip θ(1):     {np.degrees(theta[-1]):+.6f}°

LINEAR COMPARISON
{'-'*35}
δ_linear = αy/12:      {delta_linear:+.6f}
Error:                 {abs(y[-1]-delta_linear):.6f} ({abs(y[-1]-delta_linear)/abs(delta_linear)*100 if abs(delta_linear)>1e-6 else 0:.1f}%)

BOUNDARY CONDITIONS
{'-'*35}
At s=0 (Clamped): x̄=0, ȳ=0, θ=0
At s=1 (Guided):  θ=0 (flat tip)
"""
            self.text_results.set_text(results)
            
        else:
            self.text_results.set_text("Solver failed to converge")
        
        self.fig.canvas.draw_idle()
        
    def reset(self, event):
        self.s_ay.reset()
        self.s_ax.reset()


def main():
    print("=" * 60)
    print("Interactive Guided Beam Solver")
    print("=" * 60)
    print("\nThe 'guided' beam has:")
    print("  - Fixed end at s=0: x̄=0, ȳ=0, θ=0")
    print("  - Guided end at s=1: θ=0 (tip must be flat)")
    print("  - Tip moment β is an unknown reaction")
    print("\nUse the sliders to adjust:")
    print("  αy : Normalized vertical force (Fy·L²/EI)")
    print("  αx : Normalized horizontal force (Fx·L²/EI)")
    print("\nClose the window to exit.")
    print("=" * 60)
    
    app = GuidedBeamInteractive()
    plt.show()


if __name__ == "__main__":
    main()
