import os
import sys
import math
import time

# Auto-bootstrap: garante que roda no ambiente virtual (venv) com as dependências instaladas se disponível.
# Caso contrário, executa apenas a lógica do algoritmo (sem gerar gráficos PNG/TikZ).
has_visualization = True
try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        try:
            os.execv(venv_python, [venv_python] + sys.argv)
        except Exception:
            has_visualization = False
    else:
        has_visualization = False

# Importa os dados originais
from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes

# ==============================================================================
# 1. PREPARAÇÃO DOS DADOS DO GRAFO E GARANTIA DE BALANCEAMENTO
# ==============================================================================

# Carrega os dados originais diretamente (incluindo Planaltina e as novas conexões)
no_balancos = orig_balancos.copy()
conexoes = orig_conexoes.copy()

# Corrige pequenos desvios de ponto flutuante para garantir que a soma seja exatamente 0.0
total_bal = sum(no_balancos.values())
# Absorve o desvio no nó de Ceilândia
no_balancos["Ceilândia"] -= total_bal

print("=" * 80)
print("             REDE DE DISTRIBUIÇÃO DE ÁGUA DO DF (AJUSTADA E VIÁVEL)")
print("=" * 80)
print(f"Balanço total da rede (deve ser 0.0): {sum(no_balancos.values()):.6f}")
print("\nBalanços Nodais:")
for no, bal in no_balancos.items():
    print(f"  - {no}: {bal:+.2f} l/s")

# ==============================================================================
# 2. EXECUÇÃO DO ALGORITMO SUCCESSIVE SHORTEST PATH (SSP)
# ==============================================================================
from ssp_algorithm import successive_shortest_path

# Nós e arcos originais para posterior verificação e plotagem
V = list(no_balancos.keys())
E_edges = {(u, v): (cap, cost) for u, v, cap, cost in conexoes}

print("\nExecutando o algoritmo Successive Shortest Path (modularizado)...")
# Executa a função do algoritmo e mede o tempo de execução para benchmark
start_time = time.perf_counter()
x, pi, history = successive_shortest_path(no_balancos, conexoes)
execution_time_ms = (time.perf_counter() - start_time) * 1000

# Reconstruindo e imprimindo as informações de cada iteração a partir do histórico
total_flow_sent = 0.0
for iter_state in history:
    iteration = iter_state["iteration"]
    k = iter_state["source"]
    l = iter_state["sink"]
    delta = iter_state["delta"]
    dist_l = iter_state["distance"]
    path_edges = iter_state["path"]
    
    # Reconstrói a string do caminho
    path_str = f"{k}"
    for u, v, direction in path_edges:
        path_str += f" -> {v} ({'F' if direction == 'forward' else 'B'})"
        
    e_before_k = iter_state["excesses"][k]
    e_before_l = iter_state["excesses"][l]
    e_after_k = iter_state["excesses_after"][k]
    e_after_l = iter_state["excesses_after"][l]
    
    print(f"\nIteração {iteration}:")
    print(f"  - Fonte: {k} (excesso restante: {e_before_k:.2f} -> {e_after_k:.2f})")
    print(f"  - Destino: {l} (déficit restante: {-e_before_l:.2f} -> {-e_after_l:.2f})")
    print(f"  - Caminho Mínimo: {path_str}")
    print(f"  - Distância (custo reduzido): {dist_l:.4f}")
    print(f"  - Gargalo (delta): {delta:.2f} l/s")
    total_flow_sent += delta
    
# Verificar custos reduzidos finais
print("\n" + "="*80)
print("                      VERIFICAÇÃO DE CUSTOS REDUZIDOS FINAIS")
print("="*80)
all_non_negative = True
for (u, v), (cap, cost) in E_edges.items():
    flow = x[(u, v)]
    c_red_f = cost - pi[u] + pi[v]
    c_red_b = -cost - pi[v] + pi[u]
    
    if cap - flow > 1e-5:
        if c_red_f < -1e-5:
            print(f"  [ERRO] Arco direto ({u} -> {v}) violado! c^pi={c_red_f:.4f}, fluxo={flow:.2f}/{cap:.2f}")
            all_non_negative = False
    if flow > 1e-5:
        if c_red_b < -1e-5:
            print(f"  [ERRO] Arco reverso ({v} -> {u}) violado! c^pi={c_red_b:.4f}, fluxo={flow:.2f}/{cap:.2f}")
            all_non_negative = False

if all_non_negative:
    print("  [Sucesso] Todos os custos reduzidos das arestas residuais ativas são não-negativos (c^pi >= 0)!")
else:
    print("  [Falha] Alguma restrição de custo reduzido foi violada.")

# Imprime o fluxo ótimo final nas adutoras
print("\n" + "="*80)
print("                         FLUXOS FINAIS ÓTIMOS NAS ADUTORAS")
print("="*80)
total_cost = 0.0
for (u, v), flow in x.items():
    cost = E_edges[(u, v)][1]
    if flow > 1e-2:
        flow_cost = flow * cost
        total_cost += flow_cost
        print(f"  - {u:20} -> {v:20} : Fluxo = {flow:8.2f} / {E_edges[(u,v)][0]:7.2f} l/s | Custo unitário = {cost:5.2f} km | Custo total = {flow_cost:8.2f}")

print(f"\nCusto Total Otimizado da Distribuição (Fluxo x Custo): {total_cost:.4f}")
print(f"Tempo de Execução do Algoritmo (Benchmark): {execution_time_ms:.3f} ms")

# ==============================================================================
# 3. VISUALIZAÇÃO E PLOTAGEM DO GRAFO COM FLUXOS (OPCIONAL)
# ==============================================================================

if has_visualization:
    # Cria o grafo com NetworkX para plotagem
    G_plot = nx.DiGraph()
    for no, bal in no_balancos.items():
        G_plot.add_node(no, balance=bal)
    for (u, v), flow in x.items():
        cap, cost = E_edges[(u, v)]
        G_plot.add_edge(u, v, capacity=cap, cost=cost, flow=flow)

    # Posições circulares para os nós
    pos = nx.circular_layout(G_plot)
    pos_rotulos = {}
    for no, coords in pos.items():
        x_c, y_c = coords
        pos_rotulos[no] = (x_c * 1.25, y_c * 1.25)

    plt.figure(figsize=(16, 14), facecolor="white")

    # Desenha os nós
    cores_nos = ["#e74c3c" if "ETA" in no else "#2980b9" for no in G_plot.nodes()]
    nx.draw_networkx_nodes(G_plot, pos, node_color=cores_nos, node_size=1100, edgecolors="white", linewidths=2.5)

    # Desenha as arestas
    # Vamos desenhar as arestas com fluxos ativos em verde grosso, e as sem fluxo em cinza pontilhado
    edges_with_flow = []
    edges_no_flow = []
    widths_with_flow = []

    for u, v, data in G_plot.edges(data=True):
        flow_val = data["flow"]
        if flow_val > 1e-2:
            edges_with_flow.append((u, v))
            # Largura proporcional ao fluxo
            widths_with_flow.append(1.5 + 4.5 * (flow_val / data["capacity"]))
        else:
            edges_no_flow.append((u, v))

    # Desenha arestas com fluxo (verde sólido)
    nx.draw_networkx_edges(
        G_plot, pos,
        edgelist=edges_with_flow,
        edge_color="#2ecc71",
        width=widths_with_flow,
        arrowsize=22,
        arrowstyle="-|>",
        min_source_margin=20,
        min_target_margin=20
    )

    # Desenha arestas sem fluxo (cinza pontilhado e fino)
    nx.draw_networkx_edges(
        G_plot, pos,
        edgelist=edges_no_flow,
        edge_color="#bdc3c7",
        width=1.0,
        style="--",
        arrowsize=12,
        arrowstyle="-|>",
        min_source_margin=20,
        min_target_margin=20
    )

    # Rótulos dos nós (Nome + Balanço)
    rotulos_nos = {}
    for no, bal in no_balancos.items():
        sinal = "+" if bal > 0 else ""
        rotulos_nos[no] = f"{no}\n({sinal}{bal:.2f} l/s)"

    nx.draw_networkx_labels(
        G_plot, pos_rotulos,
        labels=rotulos_nos,
        font_size=9.5,
        font_weight="bold",
        font_color="#2c3e50"
    )

    # Rótulos das arestas (Fluxo / Capacidade | Custo)
    rotulos_arestas = {}
    for u, v, data in G_plot.edges(data=True):
        flow_val = data["flow"]
        cap_val = data["capacity"]
        cost_val = data["cost"]
        if flow_val > 1e-2:
            rotulos_arestas[(u, v)] = f"f: {flow_val:.1f}/{cap_val:.0f}\nd: {cost_val:.1f}"
        else:
            rotulos_arestas[(u, v)] = f"f: 0/{cap_val:.0f}\nd: {cost_val:.1f}"

    nx.draw_networkx_edge_labels(
        G_plot, pos,
        edge_labels=rotulos_arestas,
        font_size=8,
        font_color="#27ae60",
        label_pos=0.5,
        rotate=True
    )

    plt.title(
        f"Solução Ótima pelo Algoritmo Successive Shortest Path (SSP)\n"
        f"Fluxo Total Otimizado = {total_flow_sent:.2f} l/s | Custo = {total_cost:.2f} km-l/s | Tempo = {execution_time_ms:.3f} ms",
        fontsize=15,
        fontweight="bold",
        color="#2c3e50",
        pad=30
    )

    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    plt.axis("off")
    plt.tight_layout()

    # Salva a imagem final
    output_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grafo_ssp_fluxos.png")
    plt.savefig(output_img, dpi=300, bbox_inches="tight")
    print(f"\n[Sucesso] Gráfico final de fluxos salvo em: {output_img}")

    # ==============================================================================
    # 4. GERAÇÃO DO CÓDIGO TIKZ PARA O RELATÓRIO LATEX
    # ==============================================================================

    # Vamos gerar o código TikZ de forma automática e limpa para inclusão no arquivo .tex
    tikz_lines = []
    tikz_lines.append(r"\begin{tikzpicture}[>=stealth, node distance=4.5cm, every node/.style={font=\sffamily\scriptsize}]")

    # Adiciona estilos para os nós
    tikz_lines.append(r"  \tikzstyle{eta}=[circle, draw=red!80, fill=red!10, thick, minimum size=1.8cm, align=center]")
    tikz_lines.append(r"  \tikzstyle{ra}=[circle, draw=blue!80, fill=blue!10, thick, minimum size=1.8cm, align=center]")
    tikz_lines.append(r"  \tikzstyle{active_edge}=[draw=green!70!black, ->, ultra thick]")
    tikz_lines.append(r"  \tikzstyle{inactive_edge}=[draw=gray!40, ->, dashed, thin]")

    # Posiciona os nós em círculo
    # O raio do círculo no TikZ será de 7.0 cm para que a visualização fique bem espaçada e legível
    radius = 7.0
    nodes_list = list(G_plot.nodes())
    num_nodes = len(nodes_list)

    tikz_lines.append("")
    tikz_lines.append("  % Posicionamento dos nós")
    for idx, node in enumerate(nodes_list):
        angle = 360.0 * idx / num_nodes
        # Gera uma tag curta e única para o nó (ex: eta_brasilia, ra_ceilandia)
        tag = node.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        # Formata o nome de exibição com quebra de linha
        label_name = node.replace("ETA ", "ETA\\\\\\\\ ").replace("Plano Piloto", "Plano\\\\\\\\ Piloto").replace("Rio Descoberto", "Rio\\\\\\\\ Descoberto")
        bal = no_balancos[node]
        sinal = "+" if bal > 0 else ""
        # Define a classe do estilo
        style_class = "eta" if "ETA" in node else "ra"
        tikz_lines.append(f"  \\node[{style_class}] ({tag}) at ({angle}:{radius:.2f}) {{{label_name}\\\\ \\textbf{{{sinal}{bal:.2f} l/s}}}};")

    tikz_lines.append("")
    tikz_lines.append("  % Conexões (Arestas)")
    for u, v, data in G_plot.edges(data=True):
        tag_u = u.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        tag_v = v.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ã", "a").replace("ô", "o")
        
        flow_val = data["flow"]
        cap_val = data["capacity"]
        cost_val = data["cost"]
        
        is_active = flow_val > 1e-2
        style = "active_edge" if is_active else "inactive_edge"
        
        # Formatação do rótulo da aresta
        if is_active:
            edge_label = f"f: {flow_val:.1f}/{cap_val:.0f}\\\\ d: {cost_val:.1f} km"
            # Ajusta a posição do texto
            tikz_lines.append(f"  \\path[{style}] ({tag_u}) edge node[draw=none,fill=white,inner sep=1pt,sloped,align=center,font=\\tiny\\color{{green!50!black}}] {{{edge_label}}} ({tag_v});")
        else:
            edge_label = f"0/{cap_val:.0f}\\\\ d: {cost_val:.1f} km"
            tikz_lines.append(f"  \\path[{style}] ({tag_u}) edge node[draw=none,fill=white,inner sep=1pt,sloped,align=center,font=\\tiny\\color{{gray}}] {{{edge_label}}} ({tag_v});")

    tikz_lines.append(r"\end{tikzpicture}")

    output_tikz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grafo_ssp_fluxos_tikz.txt")
    with open(output_tikz, "w", encoding="utf-8") as f:
        f.write("\n".join(tikz_lines))
        
    print(f"[Sucesso] Código TikZ exportado com sucesso para: {output_tikz}\n")
    print("=" * 80)
else:
    print("\n" + "="*80)
    print("                     VISUALIZAÇÃO GRÁFICA PULADA")
    print("="*80)
    print("  [Aviso] Bibliotecas 'networkx' e 'matplotlib' não foram encontradas.")
    print("  O algoritmo SSP foi executado com sucesso e os resultados numéricos estão acima.")
    print("  Para gerar o gráfico PNG e o código TikZ, instale as dependências:")
    print("      pip install networkx matplotlib")
    print("=" * 80)
