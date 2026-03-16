# ASME IDETC/CIE 2026 Paper: Hierarchical Multi-fidelity Modeling Stack

## Project Purpose
This project focuses on the development and validation of a **Hierarchical Multi-fidelity Modeling Stack** for the design and analysis of compliant mechanisms. The core problem addressed is the seamless integration of fast, low-order static approximations (like Pseudo-Rigid-Body Models) with high-fidelity nonlinear Finite Element Analysis (FEA) for large deflection regimes.

The modeling stack is specifically validated using a **parallelogram flexure mechanism**, characterizing its kinematic non-linearities, parasitic rotations, and load-stiffening effects.

## Content Overview
- `CM_model_stack.tex`: Main LaTeX source file for the ASME IDETC 2026 conference paper.
- `CM_model_stack.bib`: BibTeX bibliography file containing references for beam theory, compliant mechanisms, and FEA.
- **Research Data & Plots**: The workspace includes various Python scripts and data files used to generate the benchmarks and plots presented in the paper.
- **Modeling Levels**:
  1. Linear Theory
  2. Beam Constraint Model (BCM)
  3. Standard Pseudo-Rigid-Body Model (PRBM)
  4. Optimized PRBM
  5. Guided Beam BVP
  6. exact Euler BVP (Shooting method)
  7. 2D Beam FEA
  8. 3D Solid FEA (Ground Truth)

## Usage
To compile the paper:
```bash
pdflatex CM_model_stack.tex
bibtex CM_model_stack
pdflatex CM_model_stack.tex
pdflatex CM_model_stack.tex
```

## Authors
- **Hai-Jun Su** (The Ohio State University)
- **Ben Survey** (The Ohio State University)
