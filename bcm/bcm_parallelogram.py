"""
Shorya Awtar's Beam Constraint Model (BCM) - Interactive Solver.

Reference: Handbook of Compliant Mechanisms, Case Study 3.4 & Table 3.1.
This script implements the closed-form BCM using polynomial coefficients to
analyze parasitic error motions in a parallelogram flexure.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.optimize import root
import sys

# =============================================================================
# BCM Implementation (Table 3.1 Polynomials)
# =============================================================================

class BeamConstraintModel:
    """
    Implements the Beam Constraint Model using Series Expansions 
    from Table 3.1 of the Handbook of Compliant Mechanisms.
    """
    
    def get_stiffness_coeffs(self, P):
        """
        Calculate normalized stiffness coefficients a, b, c as function of P.
        P = Normalized Axial Force (positive = tension).
        """
        a = 12.0 + 1.2*P - (P**2)/700.0
        b = 4.0 + (2.0/15.0)*P - (11.0*P**2)/6300.0
        c = -6.0 - 0.1*P + (P**2)/1400.0
        return a, b, c

    def get_stiffness_forces(self, P, delta, phi):
        """Calculate normalized Fy and M."""
        a, b, c = self.get_stiffness_coeffs(P)
        fy = a * delta + c * phi
        m  = c * delta + b * phi
        return fy, m

    def get_shortening(self, P, delta, phi):
        """
        Calculate kinematic shortening u using geometric weighting coefficients.
        u = C_dd*delta^2 + C_dt*delta*phi + C_tt*phi^2
        """
        C_dd = 0.6 - P/700.0
        C_dt = -0.1 + P/1400.0
        C_tt = (1.0/15.0) - (11.0*P)/6300.0
        
        u = C_dd * delta**2 + C_dt * delta * phi + C_tt * phi**2
        return u

class BCMParallelogram:
    """
    Solves Parallelogram Flexure using Awtar's Closed-Form BCM Formulae (Eq 3.19).
    Includes parasitic rotation and axial stretch.
    """
    def __init__(self, w=0.3, t=0.02):
        self.w = w # Normalized width (W/L), default 0.3, beam seperation = 2W
        self.t = t # Normalized thickness (T/L), default 0.02
        
    def solve(self, Ax, Ay, B=0, guess=None):
        """
        Solves using derived closed-form equations (Handbook Eq 3.19).
        
        uy = fy / (24 + 1.2 fx)
        ux = fx*(0.5/k33) - 0.6*uy^2 + uy^2*fx/1400
        theta_z = (0.5/w^2)*(t^2/12 + uy^2/700)*(mz + uy*(12+0.1*fx))
        """
        # 1. Transverse Displacement (uy)
        denom_y = 24.0 + 1.2 * Ax
        
        if abs(denom_y) <= 1e-9:
             return {
                 'success': False, 
                 'message': 'Unstable (Ax < -20)',
                 'delta': 0.0, 'phi': 0.0, 
                 'P1': Ax/2.0, 'P2': Ax/2.0, 
                 'u1': 0.0, 'u2': 0.0
             }
             
        uy = Ay / denom_y
        
        # 2. Axial Displacement (ux)
        # k33 = 12 / t^2 (Axial stiffness coeff)
        k33 = 12.0 / (self.t**2)
        ux = Ax * (0.5 / k33) - 0.6 * (uy**2) + (uy**2 * Ax) / 1400.0
        
        # 3. Rotation (theta_z)
        # terms for parasitic rotation
        term1 = 0.5 / (self.w**2)
        term2 = (self.t**2 / 12.0) + (uy**2 / 700.0)
        # Handbook of Compliant Mechanisms, p.49, Eq. (3.19):
        # theta_z = 1/(2 w^2) * (t^2/12 + uy^2/700) * [mz + uy (12 + 0.1 fx)]
        # This is already the reduced form after substituting the Table 3.1
        # simple-beam coefficients into Eq. (3.18); term3 should use uy, not fy.
        term3 = B + uy * (12.0 + 0.1 * Ax)
        
        theta_z = term1 * term2 * term3
        
        # Internal params
        P = Ax / 2.0
        
        # Return results
        # Note: compare_models calculates ux as -(u1+u2)/2. 
        # So set u1 = u2 = -ux to pass the correct ux value logic.
        return {
            'success': True,
            'delta': uy,
            'phi': theta_z,
            'P1': P, 
            'P2': P,
            'u1': -ux, 
            'u2': -ux,
            'P_diff': 0.0,
            'guess': None
        }

# =============================================================================
# Interactive GUI
# =============================================================================

class BCMInteractive:
    def __init__(self):
        self.model = BCMParallelogram(w=0.3)
        self.last_guess = None
        
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.fig.canvas.manager.set_window_title("BCM Parallelogram Solver")
        plt.subplots_adjust(bottom=0.35)
        
        # Initial Plot (Empty)
        self.line1, = self.ax.plot([], [], 'b-', lw=2, label='Beam 1 (Tension)')
        self.line2, = self.ax.plot([], [], 'r-', lw=2, label='Beam 2 (Compression)')
        self.plat_line, = self.ax.plot([], [], 'k-', lw=3, label='Platform')
        self.ax.legend(loc='upper left')
        self.ax.grid(True)
        self.ax.set_aspect('equal')
        self.ax.set_xlabel('Normalized X')
        self.ax.set_ylabel('Normalized Y')
        self.ax.set_title("Parallelogram Flexure Deformation (BCM)")
        
        # Info Text
        self.info_text = self.fig.text(0.02, 0.40, "", fontsize=10, verticalalignment='top')
        
        # Sliders
        ax_ay = plt.axes([0.25, 0.20, 0.65, 0.03])
        ax_ax = plt.axes([0.25, 0.15, 0.65, 0.03])
        ax_b  = plt.axes([0.25, 0.10, 0.65, 0.03])
        ax_w  = plt.axes([0.25, 0.05, 0.65, 0.03])
        
        self.s_ay = Slider(ax_ay, 'Ay (Vert)', -12.0, 12.0, valinit=5.0)
        self.s_ax = Slider(ax_ax, 'Ax (Horiz)', -10.0, 10.0, valinit=0.0)
        self.s_b  = Slider(ax_b,  'B (Moment)', -5.0, 5.0, valinit=0.0)
        self.s_w  = Slider(ax_w,  'w (Width/L)', 0.1, 1.0, valinit=0.3)
        
        self.s_ay.on_changed(self.update)
        self.s_ax.on_changed(self.update)
        self.s_b.on_changed(self.update)
        self.s_w.on_changed(self.update)
        
        # Initial draw
        self.update(0)

    def draw_beam(self, w_offset, u, delta, phi):
        """Reconstruct cubic beam shape for visualization."""
        xi = np.linspace(0, 1, 50)
        # BCM Shape Function (Cubic Hermite)
        # y(0)=0, y'(0)=0, y(1)=delta, y'(1)=phi
        # y = (phi - 2*delta)*xi^3 + (3*delta - phi)*xi^2
        y_local = (phi - 2*delta)*xi**3 + (3*delta - phi)*xi**2
        
        # Map to deformed coordinates
        # x_global = xi * (1 - u)
        # y_global = w_offset + y_local
        x_glob = xi * (1.0 - u)
        y_glob = w_offset + y_local
        return x_glob, y_glob

    def update(self, val):
        ay = self.s_ay.val
        ax = self.s_ax.val
        b  = self.s_b.val
        w  = self.s_w.val
        
        self.model.w = w
        
        res = self.model.solve(ax, ay, b, guess=self.last_guess)
        
        if res['success']:
            self.last_guess = res['guess']
            d = res['delta']
            p = res['phi']
            u1 = res['u1']
            u2 = res['u2']
            P1 = res['P1']
            P2 = res['P2']
            
            # Draw Beam 1 (Upper)
            x1, y1 = self.draw_beam(w, u1, d, p)
            self.line1.set_data(x1, y1)
            
            # Draw Beam 2 (Lower)
            x2, y2 = self.draw_beam(-w, u2, d, p)
            self.line2.set_data(x2, y2)
            
            # Draw Platform
            # Connect tips
            tip1 = (x1[-1], y1[-1])
            tip2 = (x2[-1], y2[-1])
            self.plat_line.set_data([tip1[0], tip2[0]], [tip1[1], tip2[1]])
            
            # Update Axes Limits
            self.ax.set_ylim(-w - 0.5 - abs(d), w + 0.5 + abs(d))
            self.ax.set_xlim(-0.1, 1.2)
            
            # Update Text
            ux = -(u1 + u2)/2.0
            uy = d
            theta_z_deg = np.degrees(p)
            
            direction = "CW" if p < 0 else "CCW"
            
            txt = (f"Results (Normalized):\n"
                   f"  Ay = {ay:.2f}\n"
                   f"  u_y (delta) = {uy:.6f}\n"
                   f"  u_x (short.) = {ux:.6f}\n"
                   f"  theta_z (phi) = {theta_z_deg:.6f}°\n"
                   f"  Direction: {direction}\n\n"
                   f"Internal:\n"
                   f"  P1 (Top) = {P1:.4f}\n"
                   f"  P2 (Bot) = {P2:.4f}\n"
                   f"  u1={u1:.4f}, u2={u2:.4f}")
            self.info_text.set_text(txt)
            
        else:
            self.info_text.set_text("Solver Failed!")
            
        self.fig.canvas.draw_idle()

# =============================================================================
# Case Study 3.4 Verification
# =============================================================================

def case_study_3_4():
    print("="*70)
    print("HANDBOOK CASE STUDY 3.4: PARALLELOGRAM FLEXURE")
    print("Verification of Beam Constraint Model (BCM)")
    print("="*70)
    
    # Assume standard parameters if not specified (L=100mm example)
    print("Using Normalized Parameters for Verification:")
    Ay_verify = 10.0
    print(f"  Applied Vertical Load (Ay): {Ay_verify}")
    print(f"  Applied Horizontal Load (Ax): 0")
    print(f"  Applied Moment (B): 0")
    print("-" * 70)
    
    model = BCMParallelogram(w=0.3)
    res = model.solve(0, Ay_verify, 0)
    
    if res['success']:
        d = res['delta']
        p = res['phi']
        u1 = res['u1']
        u2 = res['u2']
        ux = -(u1 + u2)/2.0
        
        print("COMPUTED ACTUAL DEFORMATION (Normalized):")
        print(f"  u_y (Vertical Deflection):   {d:.6f}")
        print(f"  u_x (Parasitic X-Motion):    {ux:.6f}")
        print(f"  theta_z (Parasitic Rotation): {np.degrees(p):.6f}°")
        print("-" * 70)
        print("PHYSICAL INTERPRETATION (If L = 100 mm):")
        print(f"  u_y = {d * 100:.4f} mm")
        print(f"  u_x = {ux * 100:.4f} mm")
        print(f"  theta_z = {np.degrees(p):.4f}°")
    else:
        print("Solver failed for case study.")
    
    print("="*70)
    print("\nLaunching Interactive GUI...")

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    case_study_3_4()
    app = BCMInteractive()
    plt.show()
