"""
Successive Shortest Path (SSP) — Minimum Cost Flow
===================================================
Resolve MCF usando Dijkstra com potenciais nodais (Bellman-Ford inicial).
Mapeado com base no livro de Ahuja, Magnanti & Orlin (Figura 9.9).
"""

from typing import Dict, List, Tuple
from tools import (
    initialize_potentials, build_residual_graph,
    run_dijkstra, trace_shortest_path
)


def successive_shortest_path(
    no_balancos: Dict[str, float],
    conexoes: List[Tuple[str, str, float, float]],
    verbose_callback=None
) -> Tuple[Dict[Tuple[str, str], float], Dict[str, float], List[Dict]]:
    """
    Loop principal do SSP (Mapeado com a Figura 9.9 do livro 'Network Flows').
    """

    V = list(no_balancos.keys())
    E_edges = {(u, v): (cap, cost) for u, v, cap, cost in conexoes}

    # Inicialização
    x = {edge: 0.0 for edge in E_edges}
    excesso = {node: balanco for node, balanco in no_balancos.items()}
    
    # Potenciais iniciais
    pi = initialize_potentials(V, E_edges, excesso)  # Complexidade O(V * E)

    history = []
    iteration = 0

    # Loop principal
    while True:
        sources = [node for node in V if excesso[node] > 1e-5]
        sinks = [node for node in V if excesso[node] < -1e-5]

        if not sources or not sinks:
            break

        iteration += 1

        # Grafo residual
        adj = build_residual_graph(V, E_edges, x, pi)  # Complexidade O(E)

        # Busca de caminho mínimo
        dist, parent = run_dijkstra(V, adj, sources)  # Complexidade O(V²)

        # Filtra sumidouros alcançáveis
        reachable_sinks = [s for s in sinks if dist[s] < float('inf')]
        if not reachable_sinks:
            if verbose_callback:
                verbose_callback(f"[Warning] No active sink reachable in iteration {iteration}.")
            break

        # Seleciona o sumidouro mais próximo
        l = min(reachable_sinks, key=lambda s: dist[s])
        
        # Reconstrói o caminho mínimo
        k, path_edges = trace_shortest_path(l, parent)  # Complexidade O(V)

        iter_state = {
            "iteration": iteration,
            "potentials": pi.copy(),
            "excesses": excesso.copy(),
            "source": k, "sink": l,
            "path": [(u, v, d) for u, v, d, _ in path_edges],
            "distance": dist[l]
        }

        # Atualização de potenciais
        d_max = dist[l]
        for node in V:
            pi[node] -= dist[node] if dist[node] < float('inf') else d_max  # Complexidade O(V)

        # Cálculo do gargalo (delta)
        delta = min(excesso[k], -excesso[l])
        for u, v, direction, edge_key in path_edges:
            for nv, rc, _, dt, _ in adj[u]:
                if nv == v and dt == direction:
                    delta = min(delta, rc)
                    break  # Complexidade O(V)

        # Aumento de fluxo
        for u, v, direction, edge_key in path_edges:
            x[edge_key] += delta if direction == "forward" else -delta  # Complexidade O(V)

        # Atualização dos excessos
        excesso[k] -= delta
        excesso[l] += delta

        iter_state["delta"] = delta
        iter_state["excesses_after"] = excesso.copy()
        history.append(iter_state)

        if verbose_callback:
            path_str = " -> ".join([f"{u}({d[0]})" for u, _, d, _ in path_edges] + [f"{l}"])
            verbose_callback(
                f"Iteration {iteration}:\n"
                f"  Source: {k} ({excesso[k]+delta:.2f} -> {excesso[k]:.2f})\n"
                f"  Sink: {l} ({-excesso[l]+delta:.2f} -> {-excesso[l]:.2f})\n"
                f"  Path: {path_str}\n"
                f"  Delta: {delta:.2f} l/s | Dist: {dist[l]:.4f}"
            )

    return x, pi, history
