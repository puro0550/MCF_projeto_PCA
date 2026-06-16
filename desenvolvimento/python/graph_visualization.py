"""
Network Flow Graph Visualization and TikZ Exporter
===================================================

This script creates a premium matplotlib/networkx visualization of the water
distribution network with optimal flows, saving it to 'grafo_ssp_fluxos.png'.
It also generates and saves the LaTeX TikZ code for the network to 'grafo_tikz.tex'.

Author: Antigravity Agent
Date: June 2026
"""

import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))

# Auto-bootstrap: ensures we run in the local venv if available
try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Error: Install required libraries: pip install networkx matplotlib")
        sys.exit(1)

import math



# Load data and solver
try:
    from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
except ImportError:
    sys.path.append(script_dir)
    from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
    
from ssp_algorithm import successive_shortest_path

def main():
    # 1. Setup balanced graph
    no_balancos = orig_balancos.copy()
    conexoes = orig_conexoes.copy()

    # Balance adjustments (float precision correction)
    no_balancos["Ceilândia"] -= sum(no_balancos.values())

    # Solve flow
    x, pi, _ = successive_shortest_path(no_balancos, conexoes)

    # 2. Build NetworkX graph for plotting
    G_plot = nx.DiGraph()
    for node, bal in no_balancos.items():
        G_plot.add_node(node, balance=bal)
    for (u, v), flow in x.items():
        cap = next(c[2] for c in conexoes if c[0] == u and c[1] == v)
        cost = next(c[3] for c in conexoes if c[0] == u and c[1] == v)
        G_plot.add_edge(u, v, capacity=cap, cost=cost, flow=flow)

    # Set up layout and figure
    pos = nx.circular_layout(G_plot)
    pos_labels = {}
    for node, coords in pos.items():
        x_c, y_c = coords
        pos_labels[node] = (x_c * 1.25, y_c * 1.25)

    plt.figure(figsize=(16, 14), facecolor="white")

    # Define colors
    node_colors = ["#e74c3c" if "ETA" in node else "#2980b9" for node in G_plot.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G_plot, pos,
        node_color=node_colors,
        node_size=1200,
        edgecolors="white",
        linewidths=2.5
    )

    # Split edges by active flow vs inactive
    active_edges = []
    inactive_edges = []
    active_widths = []

    for u, v, data in G_plot.edges(data=True):
        flow_val = data["flow"]
        if flow_val > 1e-2:
            active_edges.append((u, v))
            # Width proportional to capacity usage
            active_widths.append(1.5 + 4.5 * (flow_val / data["capacity"]))
        else:
            inactive_edges.append((u, v))

    # Draw active edges (green solid)
    nx.draw_networkx_edges(
        G_plot, pos,
        edgelist=active_edges,
        edge_color="#2ecc71",
        width=active_widths,
        arrowsize=22,
        arrowstyle="-|>",
        min_source_margin=22,
        min_target_margin=22
    )

    # Draw inactive edges (grey dashed)
    nx.draw_networkx_edges(
        G_plot, pos,
        edgelist=inactive_edges,
        edge_color="#bdc3c7",
        width=1.0,
        style="--",
        arrowsize=12,
        arrowstyle="-|>",
        min_source_margin=22,
        min_target_margin=22
    )

    # Draw node labels
    node_labels = {}
    for node, bal in no_balancos.items():
        sign = "+" if bal > 0 else ""
        node_labels[node] = f"{node}\n({sign}{bal:.2f} l/s)"

    nx.draw_networkx_labels(
        G_plot, pos_labels,
        labels=node_labels,
        font_size=9.5,
        font_weight="bold",
        font_color="#2c3e50"
    )

    # Draw edge labels
    edge_labels = {}
    for u, v, data in G_plot.edges(data=True):
        flow_val = data["flow"]
        cap_val = data["capacity"]
        cost_val = data["cost"]
        if flow_val > 1e-2:
            edge_labels[(u, v)] = f"f: {flow_val:.1f}/{cap_val:.0f}\nd: {cost_val:.1f}"
        else:
            edge_labels[(u, v)] = f"0/{cap_val:.0f}\nd: {cost_val:.1f}"

    nx.draw_networkx_edge_labels(
        G_plot, pos,
        edge_labels=edge_labels,
        font_size=8,
        font_color="#27ae60",
        label_pos=0.5,
        rotate=True
    )

    total_flow = sum(f for f in x.values() if f > 0)
    total_cost = sum(x[edge] * next(c[3] for c in conexoes if c[0] == edge[0] and c[1] == edge[1]) for edge in x)
    
    plt.title(
        f"DF Water Network - Successive Shortest Path (SSP) Optimal Flows\n"
        f"Total Flow = {total_flow:.2f} l/s | Minimum Transport Cost = {total_cost:.2f} km-l/s",
        fontsize=16,
        fontweight="bold",
        color="#2c3e50",
        pad=30
    )

    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    plt.axis("off")
    plt.tight_layout()

    # Save figure
    output_png = os.path.join(script_dir, "grafo_ssp_fluxos.png")
    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    print(f"Matplotlib flow visualization saved to '{output_png}'")

    # 3. Generate TikZ Code
    tikz_lines = []
    tikz_lines.append(r"\begin{tikzpicture}[>=stealth, node distance=4.5cm, every node/.style={font=\sffamily\scriptsize}]")
    tikz_lines.append(r"  \tikzstyle{eta}=[circle, draw=red!80, fill=red!10, thick, minimum size=1.8cm, align=center]")
    tikz_lines.append(r"  \tikzstyle{ra}=[circle, draw=blue!80, fill=blue!10, thick, minimum size=1.8cm, align=center]")
    tikz_lines.append(r"  \tikzstyle{active_edge}=[draw=green!70!black, ->, ultra thick]")
    tikz_lines.append(r"  \tikzstyle{inactive_edge}=[draw=gray!40, ->, dashed, thin]")
    
    radius = 7.0
    nodes_list = list(G_plot.nodes())
    num_nodes = len(nodes_list)

    tikz_lines.append("")
    tikz_lines.append("  % Node positions")
    for idx, node in enumerate(nodes_list):
        angle = 360.0 * idx / num_nodes
        # Unique short tag for TikZ node reference
        tag = node.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        
        # Line break formatting for node names in TikZ
        label_name = node.replace("ETA ", "ETA\\\\ ").replace("Plano Piloto", "Plano\\\\ Piloto").replace("Rio Descoberto", "Rio\\\\ Descoberto")
        bal = no_balancos[node]
        sign = "+" if bal > 0 else ""
        style_class = "eta" if "ETA" in node else "ra"
        tikz_lines.append(f"  \\node[{style_class}] ({tag}) at ({angle}:{radius:.2f}) {{{label_name}\\\\ \\textbf{{{sign}{bal:.2f} l/s}}}};")

    tikz_lines.append("")
    tikz_lines.append("  % Pipe connections")
    for u, v, data in G_plot.edges(data=True):
        tag_u = u.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        tag_v = v.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        
        flow_val = data["flow"]
        cap_val = data["capacity"]
        cost_val = data["cost"]
        
        is_active = flow_val > 1e-2
        style = "active_edge" if is_active else "inactive_edge"
        
        # Label formatting for TikZ paths
        if is_active:
            edge_label = f"f: {flow_val:.1f}/{cap_val:.0f}\\\\ d: {cost_val:.1f} km"
            tikz_lines.append(f"  \\path[{style}] ({tag_u}) edge node[draw=none,fill=white,inner sep=1pt,sloped,align=center,font=\\tiny\\color{{green!50!black}}] {{{edge_label}}} ({tag_v});")
        else:
            edge_label = f"0/{cap_val:.0f}\\\\ d: {cost_val:.1f} km"
            tikz_lines.append(f"  \\path[{style}] ({tag_u}) edge node[draw=none,fill=white,inner sep=1pt,sloped,align=center,font=\\tiny\\color{{gray}}] {{{edge_label}}} ({tag_v});")

    tikz_lines.append(r"\end{tikzpicture}")

    output_tikz = os.path.join(script_dir, "grafo_tikz.tex")
    with open(output_tikz, "w", encoding="utf-8") as f:
        f.write("\n".join(tikz_lines))
        
    print(f"LaTeX TikZ representation saved to '{output_tikz}'")

if __name__ == "__main__":
    main()
