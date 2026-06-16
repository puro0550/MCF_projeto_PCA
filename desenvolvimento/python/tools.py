"""
Ferramentas auxiliares para o algoritmo SSP (Successive Shortest Path).
Contém: Bellman-Ford, grafo residual, Dijkstra (lista), reconstrução de caminho.
"""

import math
from typing import Dict, List, Tuple, Optional


# =============================================================================
# BELLMAN-FORD
# =============================================================================

def initialize_potentials(
    V: List[str],
    E_edges: Dict[Tuple[str, str], Tuple[float, float]],
    excesses: Dict[str, float]
) -> Dict[str, float]:
    """
    Bellman-Ford multi-source para calcular potenciais iniciais π(i).
    Garante custos reduzidos c^π_ij = c_ij - π(i) + π(j) ≥ 0.
    """
    dist_BF = {node: float('inf') for node in V}  # Complexidade O(V)
    
    for node in V:
        if excesses[node] > 0:
            dist_BF[node] = 0.0  # Complexidade O(V) para inicializar fontes

    for _ in range(len(V) - 1):  # Roda V - 1 vezes: O(V)
        for (u, v), (_, cost) in E_edges.items():  # Roda E vezes: O(E)
            if dist_BF[u] < float('inf') and dist_BF[v] > dist_BF[u] + cost:
                dist_BF[v] = dist_BF[u] + cost  # Relaxamento das arestas: custo total O(V * E)

    return {node: dist_BF[node] if dist_BF[node] < float('inf') else 0.0 for node in V}  # Complexidade O(V)


# =============================================================================
# GRAFO RESIDUAL
# =============================================================================

def build_residual_graph(
    V: List[str],
    E_edges: Dict[Tuple[str, str], Tuple[float, float]],
    x: Dict[Tuple[str, str], float],
    pi: Dict[str, float]
) -> Dict[str, List[Tuple[str, float, float, str, Tuple[str, str]]]]:
    """
    Constrói o grafo residual G(x) com custos reduzidos c^π.
    Forward (u→v): cap_res = cap - x | Backward (v→u): cap_res = x.
    """
    adj = {node: [] for node in V}  # Complexidade O(V)

    for (u, v), (cap, cost) in E_edges.items():  # Roda E vezes: O(E)
        flow = x[(u, v)]

        r_f = cap - flow
        if r_f > 1e-5:
            c_red = max(0.0, cost - pi[u] + pi[v])  # Custo reduzido: O(1)
            adj[u].append((v, r_f, c_red, "forward", (u, v)))

        r_b = flow
        if r_b > 1e-5:
            c_red = max(0.0, -cost - pi[v] + pi[u])  # Custo reduzido reverso: O(1)
            adj[v].append((u, r_b, c_red, "backward", (u, v)))

    return adj

# =============================================================================
# DIJKSTRA — VERSÃO COM LISTA (O(n²))
# =============================================================================

def run_dijkstra(
    V: List[str],
    adj: Dict[str, List[Tuple[str, float, float, str, Tuple[str, str]]]],
    sources: List[str]
) -> Tuple[Dict[str, float], Dict[str, Optional[Tuple[str, str, Tuple[str, str]]]]]:
    """
    Dijkstra multi-source com lista ordenada. O(n²).
    """
    dist = {node: float('inf') for node in V}  # Complexidade O(V)
    parent = {node: None for node in V}  # Complexidade O(V)

    fila_prioridade = []
    for s in sources:
        dist[s] = 0.0
        fila_prioridade.append((0.0, s))  # Complexidade O(V) para inicializar fontes

    visited = set()

    while fila_prioridade:
        fila_prioridade.sort(key=lambda item: item[0])  # Ordena fila: O(|pq| * log(|pq|))
        d_curr, u = fila_prioridade.pop(0)

        if u in visited:
            continue
        visited.add(u)

        for v, r_cap, weight, direction, edge_key in adj[u]:  # Relaxa arestas adjacentes: O(grau(u))
            if dist[v] > dist[u] + weight:
                dist[v] = dist[u] + weight
                parent[v] = (u, direction, edge_key)
                fila_prioridade.append((dist[v], v))  # Custo total Dijkstra dominado por O(V²) devido aos sorts repetidos

    return dist, parent


# =============================================================================
# RECONSTRUÇÃO DE CAMINHO
# =============================================================================

def trace_shortest_path(
    target_sink: str,
    parent: Dict[str, Optional[Tuple[str, str, Tuple[str, str]]]]
) -> Tuple[str, List[Tuple[str, str, str, Tuple[str, str]]]]:
    """Reconstrói o caminho mínimo do sumidouro até a fonte via parent pointers."""
    path_edges = []
    curr = target_sink
    
    while parent[curr] is not None:  # Roda no máximo O(V) vezes
        prev, direction, edge_key = parent[curr]
        path_edges.append((prev, curr, direction, edge_key))
        curr = prev  # Subida de nível na árvore de caminhos

    source_node = curr
    path_edges.reverse()  # Complexidade O(V) para inverter o caminho
    return source_node, path_edges
