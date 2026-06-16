"""
SSP Execution Experiment and Trace Generation
=============================================

This script runs the Successive Shortest Path (SSP) algorithm on the balanced
Distrito Federal (DF) water distribution network. It profiles the algorithm,
prints a detailed iteration-by-iteration trace, verifies the final reduced
costs, and checks correctness.

Author: Antigravity Agent
Date: June 2026
"""

import sys
import os
import time

# Auto-bootstrap: ensures we run in the local venv if available
script_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(script_dir, "venv", "bin", "python3")
if os.path.exists(venv_python) and sys.executable != venv_python:
    import subprocess
    result = subprocess.run([venv_python] + sys.argv)
    sys.exit(result.returncode)

# Import graph data from grafo.py
try:
    from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
except ImportError:
    # Adjust path if needed
    sys.path.append(script_dir)
    from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes

from ssp_algorithm import successive_shortest_path

def main():
    # 1. Network Filtering & Balancing
    no_balancos = orig_balancos.copy()
    conexoes = orig_conexoes.copy()

    # Float correction absorbed in Ceilândia
    total_bal = sum(no_balancos.values())
    no_balancos["Ceilândia"] -= total_bal

    print("=" * 80)
    print("             SIMULATION AND EXPERIMENTAL SETUP FOR WATER NETWORK")
    print("=" * 80)
    print(f"Total Nodal Balance (must be 0.0): {sum(no_balancos.values()):.8f}")
    print(f"Nodes in Network: {len(no_balancos)}")
    print(f"Arcs in Network: {len(conexoes)}")
    print("\nInitial Balanced Node Demands:")
    for node, bal in sorted(no_balancos.items()):
        print(f"  - {node:22} : {bal:+.2f} l/s")
        
    print("\nStarting Successive Shortest Path (SSP) Solver...")
    
    # Callback to print execution trace
    def verbose_print(message):
        print(message)
        
    # Start timer
    start_time = time.perf_counter()
    x, pi, history = successive_shortest_path(no_balancos, conexoes, verbose_print)
    elapsed_time = (time.perf_counter() - start_time) * 1000 # in ms

    print("\n" + "=" * 80)
    print("                      ALGORITHM CONVERGED SUCCESSFULLY")
    print("=" * 80)
    print(f"Execution time: {elapsed_time:.3f} ms")
    print(f"Number of iterations: {len(history)}")

    # 2. Verify optimality via reduced costs c^pi >= 0
    print("\nOptimality Verification (c^pi_ij >= 0 in G(x)):")
    E_edges = {(u, v): (cap, cost) for u, v, cap, cost in conexoes}
    all_valid = True
    for (u, v), (cap, cost) in E_edges.items():
        flow = x[(u, v)]
        c_red_f = cost - pi[u] + pi[v]
        c_red_b = -cost - pi[v] + pi[u]
        
        # Check forward arc
        if cap - flow > 1e-5:
            if c_red_f < -1e-5:
                print(f"  [ERROR] Forward arc {u} -> {v} violates reduced cost: c^pi = {c_red_f:.5f}")
                all_valid = False
        # Check backward arc
        if flow > 1e-5:
            if c_red_b < -1e-5:
                print(f"  [ERROR] Backward arc {v} -> {u} violates reduced cost: c^pi = {c_red_b:.5f}")
                all_valid = False
                
    if all_valid:
        print("  [SUCCESS] All reduced costs are non-negative! Optimality condition verified.")
    else:
        print("  [FAILURE] Optimality conditions were violated!")

    # 3. Print optimal flow results
    print("\n" + "=" * 80)
    print("                         OPTIMAL FLOWS IN ADUTORAS")
    print("=" * 80)
    total_cost = 0.0
    for (u, v), flow in sorted(x.items()):
        cap, cost = E_edges[(u, v)]
        if flow > 1e-2:
            cost_contrib = flow * cost
            total_cost += cost_contrib
            print(f"  - {u:20} -> {v:20} : Flow = {flow:8.2f} / {cap:7.2f} l/s | Cost = {cost:5.2f} | Total = {cost_contrib:8.2f}")
            
    print(f"\nTotal Minimum Cost: {total_cost:.4f} km-l/s")
    print("=" * 80)
    
    # Save a detailed log of history for LaTeX documentation
    with open(os.path.join(script_dir, "ssp_execution_trace.txt"), "w", encoding="utf-8") as f:
        f.write("TRACE OF SSP ITERATIONS\n")
        f.write("========================\n\n")
        for state in history:
            f.write(f"Iteration {state['iteration']}:\n")
            f.write(f"  Source Node: {state['source']}\n")
            f.write(f"  Sink Node: {state['sink']}\n")
            f.write("  Path taken:\n")
            for u, v, d in state['path']:
                f.write(f"    {u} -> {v} ({d})\n")
            f.write(f"  Path distance (reduced cost): {state['distance']:.4f}\n")
            f.write(f"  Flow augmented (delta): {state['delta']:.2f} l/s\n")
            f.write("  Node Excesses after update:\n")
            for n, val in sorted(state['excesses_after'].items()):
                f.write(f"    {n}: {val:+.2f} l/s\n")
            f.write("  Node Potentials after update:\n")
            for n, val in sorted(state['potentials'].items()):
                f.write(f"    {n}: {val:+.4f}\n")
            f.write("-" * 50 + "\n")
            
    print("Step-by-step log saved to 'ssp_execution_trace.txt'")

if __name__ == "__main__":
    main()
