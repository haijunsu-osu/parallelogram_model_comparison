# Euler Beam & Parallelogram Flexure Mechanism Solver

A Python-based solver for large-deflection beam analysis using the nonlinear Euler-Bernoulli beam theory with arc-length parameterization.

This repository is maintained to support the following paper:
> **Su, H.-J., and Survey, B., "Hierarchical Multi-fidelity Modeling Stack for Design and Analysis of Compliant Mechanisms," Proc. of the ASME 2026 IDETC/CIE, Houston, TX, Aug. 23–26, 2026. Paper No. DETC2026-XXXXX.**

## Overview

This repository contains solvers for:
1. **Single Cantilever Beam** - Large deflection analysis of a cantilever beam under arbitrary tip loading
2. **Parallelogram Flexure Mechanism** - Analysis of a parallel-guided flexure stage formed by two identical beams

Both solvers use the **Elastica** formulation (large deflection, geometric nonlinearity) rather than the small-deflection linear theory.

---

## Table of Contents

- [Theory](#theory)
  - [Single Beam Formulation](#single-beam-formulation)
  - [Parallelogram Mechanism Formulation](#parallelogram-mechanism-formulation)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [API Reference](#api-reference)

---

## Theory

### Single Beam Formulation

#### Problem Setup

Consider a flexible cantilever beam with:
- **Material modulus**: $E$
- **Area moment of inertia**: $I$
- **Length**: $L$
- **Left end**: Clamped (fixed position and angle)
- **Right end**: Free, subject to loads $F_x$, $F_y$, and $M_z$

```
    Clamped End                    Free End
        ├─────────────────────────────►
        │                              │
        │      Flexible Beam           ├──► Fx
        │                              │
        └──────────────────────────────▼ Fy
                                       ↻ Mz
```

#### Kinematic Relations

Using arc length $s \in [0, L]$ as the parameter:

| Variable | Definition |
|----------|------------|
| $\theta(s)$ | Angle of beam tangent with horizontal |
| $(x(s), y(s))$ | Position along the beam |
| $\kappa(s)$ | Curvature: $\kappa = d\theta/ds$ |

The **inextensibility constraint** (arc-length parameterization):

$$\frac{dx}{ds} = \cos\theta, \quad \frac{dy}{ds} = \sin\theta$$

#### Euler-Bernoulli Constitutive Law

$$M(s) = EI \cdot \kappa(s) = EI \frac{d\theta}{ds}$$

#### Equilibrium

The bending moment at any section $s$ (considering free body from $s$ to tip):

$$M(s) = M_z + F_x(y_L - y(s)) - F_y(x_L - x(s))$$

Differentiating and substituting:

$$EI \frac{d^2\theta}{ds^2} = F_y \cos\theta - F_x \sin\theta$$

#### Normalized Formulation

Define normalized variables:

| Parameter | Definition | Range/Description |
|-----------|------------|-------------------|
| $\bar{s} = s/L$ | Normalized arc length | $[0, 1]$ |
| $\bar{x} = x/L$, $\bar{y} = y/L$ | Normalized position | - |
| $\bar{\kappa} = L\kappa$ | Normalized curvature | - |
| $\alpha_x = F_x L^2 / EI$ | Normalized horizontal force | - |
| $\alpha_y = F_y L^2 / EI$ | Normalized vertical force | - |
| $\beta = M_z L / EI$ | Normalized tip moment | - |

**Normalized governing equations:**

$$\frac{d\bar{x}}{d\bar{s}} = \cos\theta$$

$$\frac{d\bar{y}}{d\bar{s}} = \sin\theta$$

$$\frac{d\theta}{d\bar{s}} = \bar{\kappa}$$

$$\frac{d\bar{\kappa}}{d\bar{s}} = \alpha_y \cos\theta - \alpha_x \sin\theta$$

**Boundary conditions:**

| Location | Conditions |
|----------|------------|
| Clamped end ($\bar{s}=0$) | $\bar{x}=0$, $\bar{y}=0$, $\theta=0$ |
| Free end ($\bar{s}=1$) | $\bar{\kappa}(1) = \beta$ |

---

### Parallelogram Mechanism Formulation

#### Problem Setup

A parallelogram flexure mechanism consists of:
- **Two identical beams** (modulus $E$, moment of inertia $I$, length $L$)
- **Upper beam (Beam 1)**: Clamped at $(0, W)$
- **Lower beam (Beam 2)**: Clamped at $(0, -W)$
- **Rigid platform**: Connects the two beam tips
- **External load**: $(F_x, F_y, M_z)$ applied at platform center

```
                 Beam 1
    ├═══════════════════════════════╗
    │                               ║
    │ (0, W)                   ┌────╫────┐
    │                          │    ║    │
    ├- - - - - - - - - - - - - │- -►║    │ ← Platform (rigid)
    │                          │    ║    │   Fx, Fy, Mz applied here
    │ (0, -W)                  └────╫────┘
    │                               ║
    ├═══════════════════════════════╝
                 Beam 2
```

#### Variables

For each beam $i = 1, 2$:
- Tip reaction forces: $F_{xi}$, $F_{yi}$
- Tip reaction moment: $M_{zi}$
- Tip position: $(\bar{x}_i(1), \bar{y}_i(1))$
- Tip angle: $\theta_i(1)$

Platform state:
- Center position: $(X_p, Y_p)$
- Rotation angle: $\phi$

#### Normalized Parameters

$$w = \frac{W}{L}, \quad \alpha_{xi} = \frac{F_{xi} L^2}{EI}, \quad \alpha_{yi} = \frac{F_{yi} L^2}{EI}, \quad \beta_i = \frac{M_{zi} L}{EI}$$

External loads (normalized):

$$A_x = \frac{F_x L^2}{EI}, \quad A_y = \frac{F_y L^2}{EI}, \quad B = \frac{M_z L}{EI}$$

#### Beam Equations

Each beam satisfies the same normalized ODEs as the single beam case, with its respective load parameters $(\alpha_{xi}, \alpha_{yi}, \beta_i)$.

#### Constraint Equations (6 Equations, 6 Unknowns)

**Unknowns:** $\alpha_{x1}, \alpha_{y1}, \beta_1, \alpha_{x2}, \alpha_{y2}, \beta_2$

| # | Equation | Physical Meaning |
|---|----------|------------------|
| 1 | $\theta_1(1) = \theta_2(1)$ | Angle compatibility |
| 2 | $\bar{x}_1(1) - \bar{x}_2(1) = -2w\sin\phi$ | x-position compatibility |
| 3 | $\bar{y}_1(1) - \bar{y}_2(1) = 2w(\cos\phi - 1)$ | y-position compatibility |
| 4 | $\alpha_{x1} + \alpha_{x2} = A_x$ | Horizontal force equilibrium |
| 5 | $\alpha_{y1} + \alpha_{y2} = A_y$ | Vertical force equilibrium |
| 6 | $\beta_1 + \beta_2 + w\cos\phi(\alpha_{x1} - \alpha_{x2}) + w\sin\phi(\alpha_{y1} - \alpha_{y2}) = B$ | Moment equilibrium |

Where $\phi = \theta_1(1) = \theta_2(1)$ from angle compatibility.

#### Platform Output

After solving, the platform state is:

$$\bar{X}_p = \frac{\bar{x}_1(1) + \bar{x}_2(1)}{2}$$

$$\bar{Y}_p = \frac{\bar{y}_1(1) + \bar{y}_2(1)}{2}$$

$$\phi = \theta_1(1)$$

---

## Modeling Stack Guide

This repository implements an 8-level hierarchy of models for the parallelogram flexure, ranging from simple linear theory to high-fidelity 3D FEA.

### 1. Analytical & Algebraic Models
- **Level 1: Linear Theory** (`linear_beam/linear_solver.py`)
  - Small-deflection approximation ($u_y = \alpha_y/24$).
  - Does not capture kinematic shortening or buckling.
- **Levels 2-3: Pseudo-Rigid-Body Model** (`prb/prb_parallelogram.py`)
  - Models the mechanism as a 4-bar linkage with torsional springs.
  - **Standard PRB:** Uses textbook coefficients ($\gamma=0.8517, K_\Theta=2.67$).
  - **Optimized PRB:** Uses coefficients tuned via `gamma_study.py` ($\gamma=0.90, K_\Theta=2.50$) for better accuracy under high loads.
- **Level 4: Beam Constraint Model (BCM)** (`bcm/bcm_parallelogram.py`)
  - Uses Awtar’s transcendental constraints for moderate-deflection analysis.

### 2. Nonlinear BVP Solvers
- **Level 5: Fixed-Guided Beam** (`guided_beam/guided_beam_solver.py`)
  - Solves the Euler-Bernoulli BVP for an S-shaped beam with a horizontal tip constraint.
- **Level 6: Euler BVP Parallelogram** (`euler_beam/parallelogram_solver.py`)
  - **Ground Truth Theory:** Solves the full coupled BVP system for the dual-beam mechanism.

### 3. Numerical Validation (FEA)
- **Level 7: 2D FEA** (`fea_Ben/2d/parallelogram_2d_simplified.py`)
  - Beam-element-based nonlinear simulation using **CalculiX**.
- **Level 8: 3D FEA** (`fea_Ben/3d/parallelogram_3d_simplified.py`)
  - Full solid-mesh (C3D10) simulation for capturing cross-section effects and secondary stresses.

---

## Parametric Studies & GUI Tools

### PRB Parametric Study (`prb/gamma_study.py`)
This script performs a systematic sweep of the characteristic radius factor $\gamma$ to minimize the RMSE against the Level 6 Euler BVP ground truth. It is used to justify the selection of $\gamma=0.90$ for the optimized model.

### Interactive Benchmark App (`compare_models_gui.py`)
A comprehensive PyQt/Matplotlib-based GUI that allows users to:
- Sweep loads ($\alpha_x, \alpha_y$) and geometric parameters ($w$) in real-time.
- Visualize deformed shapes across all modeling levels.
- View a live comparison table of deflections ($u_x, u_y, \phi$) and percentage errors.

---

## Installation

### Requirements

- Python 3.8+
- NumPy
- SciPy
- Matplotlib

### Install Dependencies

```bash
pip install numpy scipy matplotlib
```

---

## Usage

### Single Beam Solver

#### Basic Usage

```python
from euler_beam.euler_beam_solver import solve_euler_beam, interactive_solve

# Solve for a beam with vertical tip load
alpha_x = 0.0    # No horizontal force
alpha_y = -5.0   # Downward vertical force
beta = 0.0       # No tip moment

s, x_bar, y_bar, theta, kappa_bar = solve_euler_beam(alpha_x, alpha_y, beta)

print(f"Tip position: ({x_bar[-1]:.4f}, {y_bar[-1]:.4f})")
print(f"Tip angle: {np.degrees(theta[-1]):.2f}°")
```

#### Interactive Mode with Plotting

```python
from euler_beam.euler_beam_solver import interactive_solve

results = interactive_solve(alpha_x=0, alpha_y=-5, beta=0, show_plot=True)
```

#### Command Line

```bash
python euler_beam/euler_beam_solver.py
```

### Interactive Beam Solver (with Sliders)

Launch the interactive GUI with real-time slider controls:

```bash
python euler_beam/euler_beam_interactive.py
```

**Controls:**
- **α_x slider**: Adjust normalized horizontal force (-10 to +10)
- **α_y slider**: Adjust normalized vertical force (-10 to +10)
- **β slider**: Adjust normalized tip moment (-5 to +5)
- **Reset button**: Return to initial values

---

## Examples

### Example 1: Pure Vertical Load

```python
# Beam deflecting under its own weight (approximation)
results = interactive_solve(alpha_x=0, alpha_y=-5, beta=0)
# Expected: Large downward deflection, tip angle ~70°
```

### Example 2: Horizontal Compression

```python
# Beam under axial compression
results = interactive_solve(alpha_x=-3, alpha_y=0, beta=0)
# Expected: Buckling-like behavior
```

### Example 3: Pure Moment Loading

```python
# Beam under tip moment only
results = interactive_solve(alpha_x=0, alpha_y=0, beta=3)
# Expected: Uniform curvature, circular arc shape
```

### Example 4: Combined Loading

```python
# Combined horizontal, vertical force and moment
results = interactive_solve(alpha_x=2, alpha_y=-4, beta=1)
```

---

## API Reference

### `euler_beam_solver.py`

#### `solve_euler_beam(alpha_x, alpha_y, beta, n_points=101)`

Solve the Euler beam equations for given load parameters.

**Parameters:**
- `alpha_x` (float): Normalized horizontal force $(F_x L^2 / EI)$
- `alpha_y` (float): Normalized vertical force $(F_y L^2 / EI)$
- `beta` (float): Normalized tip moment $(M_z L / EI)$
- `n_points` (int): Number of discretization points (default: 101)

**Returns:**
- `s` (ndarray): Normalized arc length array $[0, 1]$
- `x_bar` (ndarray): Normalized x-coordinates
- `y_bar` (ndarray): Normalized y-coordinates
- `theta` (ndarray): Beam angle at each point (radians)
- `kappa_bar` (ndarray): Normalized curvature at each point

#### `interactive_solve(alpha_x, alpha_y, beta, show_plot=True, save_plot=False)`

Solve and optionally visualize the beam.

**Parameters:**
- `alpha_x`, `alpha_y`, `beta`: Load parameters (same as above)
- `show_plot` (bool): Display matplotlib figure
- `save_plot` (bool or str): Save plot to file

**Returns:**
- `dict` with keys: `'s'`, `'x_bar'`, `'y_bar'`, `'theta'`, `'kappa_bar'`, `'x_tip'`, `'y_tip'`, `'theta_tip'`, `'theta_tip_deg'`

---

### `euler_beam_interactive.py`

#### `EulerBeamInteractive` class

Interactive beam solver with matplotlib slider widgets.

**Methods:**
- `__init__()`: Initialize with default parameters
- `solve_beam(n_points=101)`: Solve current beam configuration
- `run()`: Launch the interactive GUI

**Usage:**
```python
from euler_beam.euler_beam_interactive import EulerBeamInteractive

app = EulerBeamInteractive()
app.run()
```

---

## Physical Interpretation of Parameters

| Parameter | Physical Meaning | Typical Values |
|-----------|------------------|----------------|
| $\alpha_x > 0$ | Tensile horizontal force | Small deflection |
| $\alpha_x < 0$ | Compressive horizontal force | May buckle |
| $\alpha_y > 0$ | Upward vertical force | Deflects up |
| $\alpha_y < 0$ | Downward vertical force | Deflects down |
| $\beta > 0$ | Counter-clockwise tip moment | Curves upward |
| $\beta < 0$ | Clockwise tip moment | Curves downward |

### Converting to Physical Units

Given physical beam properties $(E, I, L)$ and desired forces:

```python
# Physical parameters
E = 200e9      # Young's modulus (Pa) - Steel
I = 1e-12      # Moment of inertia (m^4)
L = 0.1        # Length (m)

# Physical forces
Fx = 0.0       # Horizontal force (N)
Fy = -0.5      # Vertical force (N)
Mz = 0.0       # Tip moment (N·m)

# Compute normalized parameters
alpha_x = Fx * L**2 / (E * I)
alpha_y = Fy * L**2 / (E * I)
beta = Mz * L / (E * I)

# Solve
s, x_bar, y_bar, theta, kappa = solve_euler_beam(alpha_x, alpha_y, beta)

# Convert back to physical coordinates
x_physical = x_bar * L  # meters
y_physical = y_bar * L  # meters
```

---

## File Structure

```
parallel_guided_beam/
├── README.md                    # Documentation
├── compare_models_gui.py        # Main Interactive App (Desktop GUI)
├── euler_beam/
│   ├── euler_beam_solver.py     # Single cantilever BVP solver
│   ├── euler_beam_interactive.py # Single beam GUI
│   └── parallelogram_solver.py  # Dual-beam parallelogram BVP solver (Ground Truth)
├── bcm/
│   └── bcm_parallelogram.py     # Beam Constraint Model (Simplified Transcendental)
├── prb/
│   ├── prb_parallelogram.py     # Pseudo-Rigid-Body Model (4-bar linkage)
│   ├── gamma_study.py           # PRB parameter optimization (RMSE vs Ground Truth)
│   └── prb_parameter_study.py   # Multi-variable PRB optimization
├── linear_beam/
│   └── linear_solver.py         # Small-deflection linear approximations
├── guided_beam/
│   ├── guided_beam_solver.py    # Fixed-guided large deflection solver
│   └── guided_beam_interactive.py # Guided beam GUI
├── fea_Ben/
│   ├── 2d/                      # 2D Beam FEA scripts (CalculiX)
│   └── 3d/                      # 3D Solid FEA scripts (CalculiX)
├── comparison/
│   ├── benchmark_data/          # Pre-computed datasets (.csv)
│   └── plot_scripts/            # Evaluation and plotting tools
├── IDETC_2026/                  # LaTeX source for the conference paper
└── images/                      # Generated verification plots and schematics
```

---

## Computational Speed Benchmark

Benchmark results comparing all models using 1000 random load cases with Ay ∈ [-15, 15], Ax=0, B=0:

| Model | Total Time (ms) | Per Solve (μs) | Speedup vs Nonlinear |
|-------|-----------------|----------------|----------------------|
| **Linear** | 0.13 | 0.13 | ~2,347,000× |
| **BCM** | 139.02 | 139.02 | ~2,112× |
| **PRB (Std/Opt)** | ~46.00 | ~46.00 | ~6,400× |
| **Guided Beam** | 1,955.86 | 1,955.86 | **150×** |
| **Nonlinear** | 293,658 (extrap) | 293,658 | 1× |

**Key Observations:**
1. **Guided Beam is ~150x faster** than the full Nonlinear solver while still capturing large deflection physics (geometric nonlinearity). It solves a single BVP without the outer iteration loop required for the parallelogram constraint.
2. **PRB is ~40x faster** than the Guided Beam model and ~6,400x faster than Nonlinear, making it the most efficient model that accounts for nonlinearity (albeit approximately).
3. **BCM** (3rd order polynomial) is slower than the simple PRB (algebraic) but still very fast.
4. **Nonlinear** solver is computationally expensive (~0.3s per solve) due to the nested BVP solution required to enforce parallelogram constraints. but provides exact results

Run the benchmark yourself:
```bash
python speed_benchmark.py
```

### Accuracy vs. Speed Trade-off

### Accuracy vs. Speed Trade-off

### Accuracy vs. Speed Trade-off

Benchmark of **displacement accuracy** ($|U|$) against the exact Nonlinear solver for four **disjoint** load ranges (positive $A_y$ only):
- **Small**: $A_y \in [0, 2.5]$ ($\sim$10% deflection)
- **Intermediate**: $A_y \in [2.5, 5]$ (10-20% deflection)
- **Large**: $A_y \in [5, 10]$ (20-35% deflection)
- **Very Large**: $A_y \in [10, 15]$ (35-48% deflection)

| Model | Speed | Small Err | Interm. Err | Large Err | V. Large Err | Recommendation |
|-------|-------|-----------|-------------|-----------|--------------|----------------|
| **Linear** | ~0 ms | 3.0% | 9.5% | 19.4% | 34.2% | **Initial Sizing** (<$2.5$ only) |
| **BCM** | ~0 ms | **0.3%** | **2.6%** | 9.5% | 24.5% | **Detailed Analysis** (<$5$ only) |
| **PRB (Std)** | ~0.05 ms | 17.8% | 17.3% | 15.9% | 13.7% | *Not Recommended* |
| **PRB (Opt)** | ~0.05 ms | 2.8% | 2.5% | **2.0%** | **2.1%** | **Real-Time Control** (Robust everywhere) |
| **Guided** | ~2.0 ms | **0.00%** | **0.01%** | **0.07%** | **0.31%** | **High Fidelity Surrogate** (Always accurate) |

**Key Takeaways:**
1. **BCM vs Linear**: BCM (Closed Form, Eqs 3.19 & 3.21) is significantly more accurate than Linear theory (3x-10x) because it captures the **kinematic shortening** ($U_x \propto U_y^2$) and parasitic rotation. It is also extremely fast (**~1.6 $\mu$s/solve**), comparable to the Linear model.
2. **Intermediate Range**: BCM is excellent for intermediate deflections (2.6% error) while Linear allows nearly 10% error. 
3. **Robustness**: **PRB (Optimized)** remains the best choice for large deflections ($>5$) where BCM's linearized stiffness assumption breaks down.

---

## PRB Model Optimization

A parameter study was conducted to optimize the PRB model parameters for the parallelogram flexure mechanism.

### Optimization Results

Optimizing for combined error $|U| = \sqrt{U_x^2 + U_y^2}$:

| Parameter | Standard Value | Optimized Value |
|-----------|----------------|-----------------|
| γ (Characteristic Radius Factor) | 0.8517 | **0.90** |
| Kθ (Stiffness Coefficient) | 2.65 | **2.50** |

### Error Comparison

| Metric | PRB Standard | PRB Optimized | Improvement |
|--------|--------------|---------------|-------------|
| RMSE (Uy) | 0.0045 | 0.0031 | 31% |
| RMSE (Ux) | 0.0052 | 0.0041 | 21% |
| RMSE Combined | 0.0069 | 0.0052 | 25% |

Run the parameter study yourself:
```bash
python prb/prb_parameter_study.py
```

---

## Citation

If you use this code or the benchmark dataset in your research, please cite our paper:

```bibtex
@inproceedings{Su2026Hierarchical,
  author = {Su, Hai-Jun and Survey, Ben},
  title = {Hierarchical Multi-fidelity Modeling Stack for Design and Analysis of Compliant Mechanisms},
  booktitle = {Proceedings of the ASME 2026 International Design Engineering Technical Conferences and Computers and Information in Engineering Conference (IDETC/CIE 2026)},
  year = {2026},
  month = {August},
  address = {Houston, TX},
  note = {Paper No. DETC2026-XXXXX}
}
```

---

## License

MIT License

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
