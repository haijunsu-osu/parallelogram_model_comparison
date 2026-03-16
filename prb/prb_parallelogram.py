"""
Pseudo-Rigid-Body (PRB) Model for Parallelogram Flexure.

Reference: Handbook of Compliant Mechanisms, Section 3.4.
This script implements the PRB approximation where each flexible beam is 
modeled as a 2R pseudo-rigid-body linkage (Symmetric 1R models).

The model assumes:
1. Fixed-Guided boundary conditions for the beams.
2. Symmetry about the beam center (Inflection point).
3. Primary motion is vertical deflection (delta).
4. Parasitic rotation (phi) is assumed zero in this simplified kinematic model.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.optimize import fsolve

class PRBParallelogramModel:
    """
    PRB Model for a fixed-guided beam (Parallelogram Flexure Beam).
    
    Model:
    The beam of length L is treated as two cantilevers of length L/2 in series.
    Each L/2 segment is modeled by a 1R Pseudo-Rigid-Body Model.
    
    Parameters (from Howell, Table 5.1 for End Forces):
    gamma = 0.8517  (Characteristic Radius Factor)
    K_theta = 2.67617 (Stiffness Coefficient)
    """
    
    def __init__(self, w=0.3):
        self.w = w # Normalized half beam separation (used for visualization)
        # Standard PRBM Coefficients for end force loading
        self.gamma = 0.8517
        self.K_theta_coeff = 2.67617 
        
    def solve(self, Ay):
        """
        Solve for equilibrium angle Theta.
        
        Ay: Normalized vertical load on the PLATFORM (Total).
        Force per beam = Ay / 2.
        Force on half-beam = Ay / 2.
        
        Normalization:
        Stiffness K = K_theta_coeff * E * I / (L_char)
        L_char = L / 2
        K_normalized (relative to EI/L) = K_theta_coeff * 2
        
        Moment Equilibrium at Pivot:
        T = F_beam * (Moment Arm)
        K * Theta = (Ay/2) * (gamma * L_char * cos(Theta))
        
        In normalized usage (L=1):
        (K_theta_coeff * 2) * Theta = (Ay/2) * (gamma * 0.5 * cos(Theta))
        """
        if abs(Ay) < 1e-6:
            return 0.0, 0.0, 0.0, 0.0
            
        # Constants
        k_spring = self.K_theta_coeff * 2.0  # Stiffness relative to EI/L
        f_beam = Ay / 2.0
        moment_arm_coeff = self.gamma * 0.5
        
        # Residual function for Theta
        def residual(theta):
            # T_spring - T_load = 0
            lhs = k_spring * theta
            rhs = f_beam * moment_arm_coeff * np.cos(theta)
            return lhs - rhs
            
        # Initial guess: Linear approx
        # Linear: delta = Ay/24. Theta approx delta / (gamma * L). 
        # Actually simpler: Theta is small.
        theta_guess = 0.1 * np.sign(Ay)
        
        theta_sol = fsolve(residual, theta_guess)[0]
        
        # Calculate Kinematics
        # Deflection delta = 2 * (gamma * L/2 * sin(Theta))
        # = gamma * sin(Theta)
        delta = self.gamma * np.sin(theta_sol)
        
        # Shortening ux (Geometric)
        # x_tip = 2 * [ (1-gamma)*L/2 + gamma*L/2*cos(Theta) ]
        # x_tip = (1-gamma) + gamma*cos(Theta)
        # ux = x_tip - 1.0 = gamma * (cos(Theta) - 1)
        # Note: This is usually negative
        ux = self.gamma * (np.cos(theta_sol) - 1.0)
        
        # PRB model usually assumes phi (platform rotation) is zero for symmetric loading
        phi = 0.0 
        
        return delta, ux, phi, theta_sol

class PRBInteractive:
    def __init__(self):
        self.model = PRBParallelogramModel(w=0.3)
        self.setup_figure()
        self.update(None)
        
    def setup_figure(self):
        # Dark Theme (matching compare_models.py)
        colors = {'bg': '#1a1a2e', 'plot': '#16213e', 'line': '#e94560', 'link': '#00ff88'}
        
        self.fig = plt.figure(figsize=(10, 8))
        self.fig.patch.set_facecolor(colors['bg'])
        self.fig.canvas.manager.set_window_title("PRB Model Visualization")
        
        self.ax_plot = self.fig.add_axes([0.1, 0.35, 0.8, 0.6])
        self.ax_plot.set_facecolor(colors['plot'])
        self.ax_plot.set_aspect('equal')
        self.ax_plot.grid(True, alpha=0.2, color='white')
        self.ax_plot.set_title("Pseudo-Rigid-Body Model (1R Symmetric)", color='white')
        
        # Linkage Visualization Handles
        self.line_beam1, = self.ax_plot.plot([], [], 'o-', color=colors['link'], lw=2, label='PRB Linkage')
        self.line_beam2, = self.ax_plot.plot([], [], 'o-', color=colors['link'], lw=2)
        self.line_plat, = self.ax_plot.plot([], [], '-', color='white', lw=3, label='Platform')
        
        # Legend
        leg = self.ax_plot.legend(facecolor=colors['plot'], edgecolor='white')
        plt.setp(leg.get_texts(), color='white')
        
        # Slider
        ax_ay = self.fig.add_axes([0.2, 0.15, 0.6, 0.05])
        self.s_ay = Slider(ax_ay, 'Ay', -15.0, 15.0, valinit=5.0, color=colors['line'])
        self.s_ay.label.set_color('white')
        self.s_ay.valtext.set_color('white')
        self.s_ay.on_changed(self.update)
        
        # Info Text
        self.info_text = self.fig.text(0.05, 0.05, "", color='white', family='monospace')

    def get_prb_coords(self, theta_prb, y_offset, w):
        """Calculate coordinates of the PRB links."""
        gamma = self.model.gamma
        L_half = 0.5
        
        # Points: Start -> Pivot1 -> Midpoint(Inflection) -> Pivot2 -> End
        # 1. Start (Fixed)
        x0, y0 = 0, y_offset
        
        # 2. Pivot 1 (Fixed translation from Start)
        # Length (1-gamma)*L_half
        x1 = x0 + (1 - gamma) * L_half
        y1 = y0
        
        # 3. Midpoint (Rotated by Theta_prb)
        # Length gamma*L_half
        x2 = x1 + gamma * L_half * np.cos(theta_prb)
        y2 = y1 + gamma * L_half * np.sin(theta_prb)
        
        # 4. Pivot 2 (Symmetric about Midpoint in terms of slope?)
        # Wait, S-shape symmetry.
        # The second half is a mirror image of the first half rotated 180?
        # Beam shape: starts flat, goes up, ends flat.
        # Midpoint slope is maximum.
        # PRB for S-shape:
        # Segment 1 (0 to L/2): Angle 0 to Theta.
        # Segment 2 (L/2 to L): Angle Theta to 0.
        # This implies Pivot 2 is at angle Theta relative to... what?
        # Actually, standard visual is:
        # Start -> (1-g)L/2 -> Pivot -> gL/2 -> Mid -> gL/2 -> Pivot -> (1-g)L/2 -> End
        # Midpoint is at (x2, y2).
        # Section 2 is mirror of Section 1 about the midpoint (point symmetry).
        # Vector P2-Mid = Vector Mid-P1 ?
        # x3 = x2 + (x2 - x1) = x2 + gamma*L_half*cos(theta)
        # y3 = y2 + (y2 - y1) = y2 + gamma*L_half*sin(theta)
        # x4 = x3 + (1-gamma)*L_half
        # y4 = y3
        
        # Let's clean this up:
        # Vector 1 (Rigid Base): dx = (1-g)/2, dy = 0
        # Vector 2 (Link):       dx = g/2 cos(th), dy = g/2 sin(th)
        # Vector 3 (Link):       dx = g/2 cos(th), dy = g/2 sin(th)
        # Vector 4 (Rigid Tip):  dx = (1-g)/2, dy = 0
        
        x_pts = [0]
        y_pts = [y_offset]
        
        # Pt 1
        x_pts.append(x_pts[-1] + (1-gamma)*L_half)
        y_pts.append(y_pts[-1] + 0)
        
        # Pt 2
        x_pts.append(x_pts[-1] + gamma*L_half*np.cos(theta_prb))
        y_pts.append(y_pts[-1] + gamma*L_half*np.sin(theta_prb))
        
        # Pt 3 (Symmetric)
        x_pts.append(x_pts[-1] + gamma*L_half*np.cos(theta_prb))
        y_pts.append(y_pts[-1] + gamma*L_half*np.sin(theta_prb))
        
        # Pt 4
        x_pts.append(x_pts[-1] + (1-gamma)*L_half)
        y_pts.append(y_pts[-1] + 0)
        
        return x_pts, y_pts

    def update(self, val):
        ay = self.s_ay.val
        
        d, ux, phi, theta = self.model.solve(ay)
        
        w = self.model.w
        
        # Beam 1
        x1, y1 = self.get_prb_coords(theta, w, w)
        self.line_beam1.set_data(x1, y1)
        
        # Beam 2
        x2, y2 = self.get_prb_coords(theta, -w, w)
        self.line_beam2.set_data(x2, y2)
        
        # Platform
        self.line_plat.set_data([x1[-1], x2[-1]], [y1[-1], y2[-1]])
        
        self.ax_plot.set_xlim(-0.1, 1.1)
        self.ax_plot.set_ylim(-1.0, 1.0)
        
        txt = (f"Normalized Load Ay = {ay:.2f}\n"
               f"Deflection (delta) = {d:.4f}\n"
               f"Shortening (ux)    = {ux:.4f}\n"
               f"PRB Angle (Theta)  = {np.degrees(theta):.2f} deg")
        self.info_text.set_text(txt)
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    app = PRBInteractive()
    plt.show()
