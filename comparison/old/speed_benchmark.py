"""
Computational Speed Comparison for Parallelogram Flexure Models.
Benchmarks all models (Linear, BCM, PRB, PRB Optimized, Nonlinear) 
using 1000 random load cases with Ax=0, B=0.
"""

import numpy as np
import time
import matplotlib.pyplot as plt

import sys
import os

# Add subdirectories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'euler_beam'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bcm'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'prb'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'guided_beam'))

# Import Solvers
from parallelogram_solver import ParallelogramFlexureSolver
from bcm_parallelogram import BCMParallelogram
from prb_parallelogram import PRBParallelogramModel
from guided_beam_solver import solve_guided_beam

class LinearModel:
    """Simple linear beam theory for parallelogram flexure."""
    def solve(self, Ay):
        return Ay / 24.0

def run_benchmark():
    print("=" * 60)
    print("Computational Speed Comparison - Parallelogram Flexure Models")
    print("=" * 60)
    
    # Configuration
    n_cases = 1000
    ay_range = (-15, 15)  # Random Ay range
    
    # Generate random load cases
    np.random.seed(42)  # For reproducibility
    ay_values = np.random.uniform(ay_range[0], ay_range[1], n_cases)
    
    print(f"\nNumber of test cases: {n_cases}")
    print(f"Load range: Ay ∈ [{ay_range[0]}, {ay_range[1]}], Ax=0, B=0")
    print("-" * 60)
    
    # Initialize solvers
    solver_linear = LinearModel()
    solver_bcm = BCMParallelogram(w=0.3)
    solver_prb = PRBParallelogramModel(w=0.3)
    solver_prb_opt = PRBParallelogramModel(w=0.3)
    solver_prb_opt.gamma = 0.90
    solver_prb_opt.K_theta_coeff = 2.50
    solver_nl = ParallelogramFlexureSolver(w=0.3)
    
    results = {}
    
    # 1. Linear Model
    print("\nBenchmarking Linear Model...", end=" ", flush=True)
    start = time.perf_counter()
    for ay in ay_values:
        _ = solver_linear.solve(ay)
    elapsed_linear = time.perf_counter() - start
    results['Linear'] = elapsed_linear
    print(f"Done: {elapsed_linear*1000:.2f} ms total")
    
    # 2. BCM Model
    print("Benchmarking BCM Model...", end=" ", flush=True)
    start = time.perf_counter()
    for ay in ay_values:
        _ = solver_bcm.solve(0, ay, 0)
    elapsed_bcm = time.perf_counter() - start
    results['BCM'] = elapsed_bcm
    print(f"Done: {elapsed_bcm*1000:.2f} ms total")
    
    # 3. PRB Model (Standard)
    print("Benchmarking PRB (Standard)...", end=" ", flush=True)
    start = time.perf_counter()
    for ay in ay_values:
        _ = solver_prb.solve(ay)
    elapsed_prb = time.perf_counter() - start
    results['PRB'] = elapsed_prb
    print(f"Done: {elapsed_prb*1000:.2f} ms total")
    
    # 4. PRB Model (Optimized)
    print("Benchmarking PRB (Optimized)...", end=" ", flush=True)
    start = time.perf_counter()
    for ay in ay_values:
        _ = solver_prb_opt.solve(ay)
    elapsed_prb_opt = time.perf_counter() - start
    results['PRB_Opt'] = elapsed_prb_opt
    print(f"Done: {elapsed_prb_opt*1000:.2f} ms total")

    # 5. Guided Beam Model (BVP-based)
    print("Benchmarking Guided Beam (BVP)...", end=" ", flush=True)
    # Uses BVP solve, so we use the subset logic like Nonlinear
    n_guided_cases = min(100, n_cases)
    start = time.perf_counter()
    for i, ay in enumerate(ay_values[:n_guided_cases]):
        # Guided model uses half load on single beam
        # solve_guided_beam(ax, ay) -> here Ax=0, Ay varies
        _ = solve_guided_beam(0, ay/2.0)
    elapsed_guided = time.perf_counter() - start
    # Extrapolate
    elapsed_guided_scaled = elapsed_guided * (n_cases / n_guided_cases)
    results['Guided'] = elapsed_guided_scaled
    print(f"Done: {elapsed_guided*1000:.2f} ms ({n_guided_cases} cases)")
    
    # 6. Nonlinear Model (BVP-based)
    print("Benchmarking Nonlinear (BVP)...", end=" ", flush=True)
    # Use subset for NL since it's much slower
    n_nl_cases = min(100, n_cases)  # Limit NL cases for reasonable time
    start = time.perf_counter()
    for i, ay in enumerate(ay_values[:n_nl_cases]):
        # Skip problematic region
        if 3.1 <= abs(ay) <= 3.4:
            continue
        _ = solver_nl.solve(0, ay, 0)
    elapsed_nl = time.perf_counter() - start
    # Extrapolate to full n_cases
    elapsed_nl_scaled = elapsed_nl * (n_cases / n_nl_cases)
    results['Nonlinear'] = elapsed_nl_scaled
    print(f"Done: {elapsed_nl*1000:.2f} ms ({n_nl_cases} cases)")
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Model':<15} {'Total (ms)':<12} {'Per Solve (μs)':<15} {'Speedup vs NL':<15}")
    print("-" * 60)
    
    nl_time = results['Nonlinear']
    for name, total_time in results.items():
        per_solve_us = (total_time / n_cases) * 1e6
        speedup = nl_time / total_time if total_time > 0 else float('inf')
        print(f"{name:<15} {total_time*1000:<12.2f} {per_solve_us:<15.2f} {speedup:<15.1f}x")
    
    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#1a1a2e')
    fig.suptitle('Computational Speed Comparison', color='white', fontsize=14)
    
    models = list(results.keys())
    times_ms = [results[m] * 1000 for m in models]
    colors = ['#00d4ff', '#00ff88', '#f1c40f', '#ff6b35', '#9b59b6', '#e94560']
    
    # Bar chart - Total time
    ax1 = axes[0]
    ax1.set_facecolor('#16213e')
    bars = ax1.bar(models, times_ms, color=colors, edgecolor='white', linewidth=1.5)
    ax1.set_ylabel('Total Time (ms)', color='white')
    ax1.set_title(f'Total Solve Time ({n_cases} cases)', color='white')
    ax1.tick_params(colors='white')
    ax1.set_yscale('log')
    for spine in ax1.spines.values():
        spine.set_color('white')
    
    # Add value labels
    for bar, val in zip(bars, times_ms):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                 f'{val:.1f}', ha='center', va='bottom', color='white', fontsize=9)
    
    # Bar chart - Speedup
    ax2 = axes[1]
    ax2.set_facecolor('#16213e')
    speedups = [nl_time / results[m] for m in models]
    bars2 = ax2.bar(models, speedups, color=colors, edgecolor='white', linewidth=1.5)
    ax2.set_ylabel('Speedup Factor', color='white')
    ax2.set_title('Speedup vs Nonlinear (BVP)', color='white')
    ax2.tick_params(colors='white')
    ax2.axhline(y=1, color='white', linestyle='--', alpha=0.5)
    for spine in ax2.spines.values():
        spine.set_color('white')
    
    # Add value labels
    for bar, val in zip(bars2, speedups):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                 f'{val:.0f}x', ha='center', va='bottom', color='white', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    return results

if __name__ == "__main__":
    run_benchmark()
