import os
import sys
from typing import Dict, List, Tuple

# Import the original graph structure from work directory
sys.path.append("/home/mano-arthur/brain/projetos/ppgi/trabalho/desenvolvimento/python")
from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
from tools import initialize_potentials, build_residual_graph, run_dijkstra, trace_shortest_path

# Balance network
bal = orig_balancos.copy()
total_bal = sum(bal.values())
bal["Ceilândia"] -= total_bal

conn = orig_conexoes.copy()

COORDS = {
    "ETA Rio Descoberto": (0.0, 3.5),
    "ETA Brasília": (2.2, 3.5),
    "ETA Lago Norte": (4.4, 3.5),
    "ETA Gama": (6.6, 3.5),
    "ETA Paranoá": (8.8, 3.5),
    "ETA Sobradinho": (11.0, 3.5),
    "ETA Planaltina": (13.2, 3.5),
    
    "Ceilândia": (0.0, 0.0),
    "Samambaia": (2.2, 0.0),
    "Taguatinga": (4.4, 0.0),
    "Guará": (6.6, 0.0),
    "Plano Piloto": (8.8, 0.0),
    "Sobradinho": (11.0, 0.0),
    "Planaltina": (13.2, 0.0)
}

def clean_name(name: str) -> str:
    mapping = {
        "ETA Rio Descoberto": "\\textbf{ETA}\\\\\\textbf{Desc.}",
        "ETA Brasília": "\\textbf{ETA}\\\\\\textbf{Bras.}",
        "ETA Lago Norte": "\\textbf{ETA}\\\\\\textbf{L.Nte}",
        "ETA Gama": "\\textbf{ETA}\\\\\\textbf{Gama}",
        "ETA Paranoá": "\\textbf{ETA}\\\\\\textbf{Par.}",
        "ETA Sobradinho": "\\textbf{ETA}\\\\\\textbf{Sob.}",
        "ETA Planaltina": "\\textbf{ETA}\\\\\\textbf{Plan.}",
        "Ceilândia": "\\textbf{Ceil.}",
        "Samambaia": "\\textbf{Sam.}",
        "Taguatinga": "\\textbf{Tag.}",
        "Guará": "\\textbf{Guará}",
        "Plano Piloto": "\\textbf{Plano}\\\\\\textbf{Piloto}",
        "Sobradinho": "\\textbf{Sobrad.}",
        "Planaltina": "\\textbf{Planalt.}"
    }
    return mapping.get(name, name)

def clean_id(name: str) -> str:
    return name.replace(" ", "").replace("í", "i").replace("â", "a")

def generate_tikz_diagram(
    nodes_data: Dict[str, dict], # {node: {'e': val, 'pi': val}}
    edges_data: List[dict], # list of {'u': u, 'v': v, 'type': 'forward'/'backward', 'cost': val, 'cap': val, 'in_path': bool}
    is_input: bool = False,
    is_final: bool = False
) -> str:
    tikz = []
    tikz.append("\\begin{tikzpicture}[")
    tikz.append("    scale=0.9,")
    tikz.append("    node/.style={circle, draw=unbazul, fill=unboffwhite, thick, minimum size=1.1cm, align=center, font=\\tiny},")
    tikz.append("    edge/.style={->, >=stealth, thin, draw=gray!35},")
    tikz.append("    path_edge/.style={->, >=stealth, line width=2.5pt, draw=orange},")
    tikz.append("    back_edge/.style={->, >=stealth, dashed, thin, draw=red!45},")
    tikz.append("    edge_label/.style={font=\\tiny, fill=white, inner sep=0.8pt, opacity=0.9, text opacity=1.0}")
    tikz.append("]")
    
    # 1. Place Nodes
    for node, pos in COORDS.items():
        x, y = pos
        label = clean_name(node)
        node_id = clean_id(node)
        if is_input:
            b_val = bal[node]
            node_str = f"\\node[node] ({node_id}) at ({x}, {y}) {{{label} \\\\ $b = {b_val:+.1f}$}};"
        else:
            e_val = nodes_data[node]['e']
            pi_val = nodes_data[node]['pi']
            node_str = f"\\node[node] ({node_id}) at ({x}, {y}) {{{label} \\\\ $e = {e_val:.1f}$ \\\\ $\\pi = {pi_val:.1f}$}};"
        tikz.append("    " + node_str)
        
    # Group edges by node pair to identify parallel edges (forward + backward)
    edges_by_pair = {}
    for edge in edges_data:
        u = edge['u']
        v = edge['v']
        pair = tuple(sorted([u, v]))
        if pair not in edges_by_pair:
            edges_by_pair[pair] = []
        edges_by_pair[pair].append(edge)
        
    # 2. Draw Edges
    for pair, pair_edges in edges_by_pair.items():
        has_parallel = len(pair_edges) == 2
        
        for idx, edge in enumerate(pair_edges):
            u = clean_id(edge['u'])
            v = clean_id(edge['v'])
            u_orig = edge['u']
            v_orig = edge['v']
            cost = edge['cost']
            cap = edge['cap']
            
            # Determine style
            if edge['in_path']:
                style = "path_edge"
            elif edge.get('type') == 'backward':
                style = "back_edge"
            else:
                style = "edge"
                
            # Stagger label position to avoid overlap
            if has_parallel:
                pos_str = "pos=0.35" if idx == 0 else "pos=0.65"
                bend_str = "bend left=12" if idx == 0 else "bend right=12"
            else:
                bend_str = ""
                xu = COORDS[u_orig][0]
                xv = COORDS[v_orig][0]
                idx_diff = int(round(abs(xu - xv) / 2.2))
                pos_val = 0.25 + 0.15 * (idx_diff % 3)
                pos_str = f"pos={pos_val:.2f}"
            
            if is_input:
                label_str = f"$(u={cap:.0f}; c={cost:.1f})$"
                tikz.append(f"    \\draw[{style}] ({u}) -- ({v}) node[{pos_str}, edge_label, sloped] {{{label_str}}};")
            elif is_final:
                flow = edge['flow']
                if flow > 0.01:
                    label_str = f"${flow:.1f}/{cap:.0f}$"
                    tikz.append(f"    \\draw[path_edge] ({u}) -- ({v}) node[{pos_str}, edge_label, sloped] {{{label_str}}};")
                else:
                    tikz.append(f"    \\draw[edge] ({u}) -- ({v});")
            else:
                label_str = f"$({cost:.1f}; {cap:.1f})$"
                if edge['in_path'] or edge.get('type') == 'backward':
                    if bend_str:
                        tikz.append(f"    \\draw[{style}, {bend_str}] ({u}) to node[{pos_str}, edge_label, sloped] {{{label_str}}} ({v});")
                    else:
                        tikz.append(f"    \\draw[{style}] ({u}) -- ({v}) node[{pos_str}, edge_label, sloped] {{{label_str}}};")
                else:
                    if bend_str:
                        tikz.append(f"    \\draw[{style}, {bend_str}] ({u}) to ({v});")
                    else:
                        tikz.append(f"    \\draw[{style}] ({u}) -- ({v});")
                
    tikz.append("\\end{tikzpicture}")
    return "\n".join(tikz)

def replace_frame(content: str, marker: str, new_frame: str) -> str:
    idx = content.find(marker)
    if idx == -1:
        print(f"Warning: Marker '{marker}' not found!")
        return content
    
    frame_start = content.rfind("\\begin{frame}", 0, idx)
    if frame_start == -1:
        print(f"Warning: \\begin{{frame}} not found before marker '{marker}'!")
        return content
        
    frame_end = content.find("\\end{frame}", idx)
    if frame_end == -1:
        print(f"Warning: \\end{{frame}} not found after marker '{marker}'!")
        return content
        
    return content[:frame_start] + new_frame + content[frame_end + len("\\end{frame}"):]

def main():
    V = list(bal.keys())
    E_edges = {(u, v): (cap, cost) for u, v, cap, cost in conn}
    
    # 1. Input Graph TikZ
    edges_input = [{'u': u, 'v': v, 'cost': cost, 'cap': cap, 'in_path': False} for (u, v), (cap, cost) in E_edges.items()]
    input_tikz = generate_tikz_diagram(None, edges_input, is_input=True)
    
    # Run SSP step-by-step
    x = {edge: 0.0 for edge in E_edges}
    e = {node: b for node, b in bal.items()}
    pi = initialize_potentials(V, E_edges, e)
    
    iterations_data = {}
    
    iteration = 0
    while True:
        sources = [node for node in V if e[node] > 1e-5]
        sinks = [node for node in V if e[node] < -1e-5]
        if not sources or not sinks:
            break
            
        iteration += 1
        adj = build_residual_graph(V, E_edges, x, pi)
        dist, parent = run_dijkstra(V, adj, sources)
        
        reachable_sinks = [s for s in sinks if dist[s] < float('inf')]
        if not reachable_sinks:
            break
            
        l = min(reachable_sinks, key=lambda s: dist[s])
        k, path_edges = trace_shortest_path(l, parent)
        
        # Capture state right before augmentation
        nodes_state = {node: {'e': e[node], 'pi': pi[node]} for node in V}
        path_set = {(u, v, direction) for u, v, direction, _ in path_edges}
        
        edges_state = []
        for u in V:
            for v, r_cap, c_red, direction, edge_key in adj[u]:
                in_path = (u, v, direction) in path_set
                edges_state.append({
                    'u': u, 'v': v,
                    'type': direction,
                    'cost': c_red, 'cap': r_cap,
                    'in_path': in_path
                })
                
        iterations_data[iteration] = {
            'nodes_state': nodes_state,
            'edges_state': edges_state,
            'source': k,
            'sink': l,
            'path': path_edges,
            'dist': dist[l]
        }
        
        # update pi
        d_max = dist[l]
        for node in V:
            pi[node] -= dist[node] if dist[node] < float('inf') else d_max
            
        # delta
        delta = min(e[k], -e[l])
        for u, v, direction, edge_key in path_edges:
            for nv, rc, _, dt, _ in adj[u]:
                if nv == v and dt == direction:
                    delta = min(delta, rc)
                    break
        iterations_data[iteration]['delta'] = delta
        
        # augment
        for u, v, direction, edge_key in path_edges:
            x[edge_key] += delta if direction == 'forward' else -delta
        e[k] -= delta
        e[l] += delta
        
    # Final Graph TikZ
    nodes_final = {node: {'e': e[node], 'pi': pi[node]} for node in V}
    edges_final = [{'u': u, 'v': v, 'cost': cost, 'cap': cap, 'flow': x[(u,v)], 'in_path': False} for (u, v), (cap, cost) in E_edges.items()]
    final_tikz = generate_tikz_diagram(nodes_final, edges_final, is_final=True)
    
    # Save TikZ blocks to dictionary
    tikz_blocks = {
        'input': input_tikz,
        'final': final_tikz
    }
    for i in [1, 2, 3, 8]:
        tikz_blocks[i] = generate_tikz_diagram(
            iterations_data[i]['nodes_state'],
            iterations_data[i]['edges_state']
        )
        
    # Read 02_desenvolvimento.tex
    file_path = "/home/mano-arthur/brain/projetos/ppgi/trabalho/desenvolvimento/apresentacao_slides/capitulos/02_desenvolvimento.tex"
    with open(file_path, "r") as f:
        content = f.read()
        
    # Re-build frames
    setup_frame = f"""\\begin{{frame}}[shrink=5]{{Setup da Instância Hídrica}}
  \\begin{{itemize}}
    \\item \\textbf{{Rede Balanceada}}: Total Supply = $7600.0$ l/s e Total Demand = $-7600.0$ l/s.
    \\item \\textbf{{Interconexões (Atlas DF)}}: Incluímos todas as RAs (como Planaltina) através de adutoras de integração reais do Atlas, garantindo a viabilidade física e a resolução matemática da rede sem filtros manuais.
  \\end{{itemize}}
  \\begin{{figure}}
    \\centering
    \\scalebox{{0.60}}{{
{tikz_blocks['input']}
    }}
    \\caption{{Grafo Base com Capacidades ($c$) e Custos ($d$)}}
  \\end{{figure}}
\\end{{frame}}"""
    
    iter1_frame = f"""\\begin{{frame}}{{SSP --- Iteração 1}}
  \\small
  \\textbf{{Aumento Local}}: ETA Sobradinho $\\rightarrow$ Sobradinho \\hfill \\textbf{{Custo}}: 5.56 | \\textbf{{Fluxo}}: 570.00 l/s \\\\
  \\textit{{Resultado}}: Demanda suprida localmente (2.8 km).
  
  \\vspace{{0.1cm}}
  \\centering
  \\scalebox{{0.65}}{{
{tikz_blocks[1]}
  }}
\\end{{frame}}"""

    iter2_frame = f"""\\begin{{frame}}{{SSP --- Iteração 2}}
  \\small
  \\textbf{{Aumento Local}}: ETA Rio Descoberto $\\rightarrow$ Ceilândia \\hfill \\textbf{{Custo}}: 0.00 | \\textbf{{Fluxo}}: 836.17 l/s \\\\
  \\textit{{Resultado}}: Atendimento à maior demanda via adutora principal.
  
  \\vspace{{0.1cm}}
  \\centering
  \\scalebox{{0.65}}{{
{tikz_blocks[2]}
  }}
\\end{{frame}}"""

    iter3_frame = f"""\\begin{{frame}}{{SSP --- Iteração 3}}
  \\small
  \\textbf{{Aumento Local}}: ETA Brasília $\\rightarrow$ Guará \\hfill \\textbf{{Custo}}: 0.00 | \\textbf{{Fluxo}}: 1067.97 l/s \\\\
  \\textit{{Resultado}}: Atendimento direto (11.1 km).
  
  \\vspace{{0.1cm}}
  \\centering
  \\scalebox{{0.65}}{{
{tikz_blocks[3]}
  }}
\\end{{frame}}"""

    iter8_frame = f"""\\begin{{frame}}{{SSP --- Exemplo de Caminho Residual}}
  \\small
  \\textbf{{Caminho Aumentante Residual}}: ETA Paranoá $\\rightarrow$ Sobradinho $\\rightarrow$ ETA Sobradinho $\\rightarrow$ Planaltina \\\\
  \\textbf{{Custo}}: 0.00 | \\textbf{{Fluxo}}: 167.23 l/s \\hfill \\textit{{Nota}}: Utiliza o arco reverso Sobradinho $\\rightarrow$ ETA Sobradinho (reversão).
  
  \\vspace{{0.1cm}}
  \\centering
  \\scalebox{{0.65}}{{
{tikz_blocks[8]}
  }}
\\end{{frame}}"""

    final_frame = f"""\\begin{{frame}}{{Resultados --- Visualização Geográfica}}
  \\begin{{figure}}
    \\centering
    \\scalebox{{0.60}}{{
{tikz_blocks['final']}
    }}
    \\caption{{Visualização da Solução Ótima SSP (Adutoras Ativas em Laranja)}}
  \\end{{figure}}
\\end{{frame}}"""

    # Apply frame replacements
    content = replace_frame(content, "Setup da Instância Hídrica", setup_frame)
    content = replace_frame(content, "SSP --- Iteração 1", iter1_frame)
    content = replace_frame(content, "SSP --- Iteração 2", iter2_frame)
    content = replace_frame(content, "SSP --- Iteração 3", iter3_frame)
    content = replace_frame(content, "SSP --- Exemplo de Caminho Residual", iter8_frame)
    content = replace_frame(content, "Resultados --- Visualização Geográfica", final_frame)
    
    # Save the updated file
    with open(file_path, "w") as f:
        f.write(content)
        
    print("02_desenvolvimento.tex updated successfully with horizontal TikZ diagrams!")

if __name__ == "__main__":
    main()
