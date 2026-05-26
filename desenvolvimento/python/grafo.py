import os
import sys
import math

# Auto-bootstrap: garante que roda no ambiente virtual (venv) com as dependências instaladas
try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Erro: Instale as bibliotecas necessárias: pip install networkx matplotlib")
        sys.exit(1)

# 1. Definição dos Dados do Grafo (Simplificado)
# Balanço de cada nó (positivo = injeção/ETA, negativo = demanda/RA)
no_balancos = {
    # ETAs (Fontes de água)
    "ETA Brasília": 1200.0,
    "ETA Gama": 320.0,
    "ETA Lago Norte": 700.0,
    "ETA Paranoá": 300.0,
    "ETA Planaltina": 60.0,
    "ETA Rio Descoberto": 4450.0,
    "ETA Sobradinho": 570.0,
    # RAs (Consumidores/Sumidouros)
    "Ceilândia": -836.17,
    "Guará": -1067.97,
    "Planaltina": -927.23,
    "Plano Piloto": -1763.40,
    "Samambaia": -852.72,
    "Sobradinho": -1101.09,
    "Taguatinga": -1051.42
}

# Lista de adutoras: (Origem, Destino, Capacidade em l/s, Custo/Distância em km)
conexoes = [
    ("ETA Brasília", "Plano Piloto", 1200.0, 4.7),
    ("ETA Brasília", "Guará", 1200.0, 11.1),
    ("ETA Brasília", "Taguatinga", 1200.0, 16.0),
    
    ("ETA Gama", "Samambaia", 320.0, 18.8),
    ("ETA Gama", "Guará", 320.0, 20.3),
    ("ETA Gama", "Ceilândia", 320.0, 23.9),
    
    ("ETA Lago Norte", "Plano Piloto", 700.0, 5.3),
    ("ETA Lago Norte", "Sobradinho", 700.0, 15.2),
    ("ETA Lago Norte", "Guará", 700.0, 19.9),
    
    ("ETA Paranoá", "Plano Piloto", 300.0, 8.6),
    ("ETA Paranoá", "Sobradinho", 300.0, 17.0),
    ("ETA Paranoá", "Guará", 300.0, 22.9),
    
    ("ETA Planaltina", "Sobradinho", 60.0, 4.3),
    ("ETA Planaltina", "Plano Piloto", 60.0, 23.8),
    ("ETA Planaltina", "Planaltina", 60.0, 30.1),
    
    ("ETA Rio Descoberto", "Taguatinga", 6000.0, 6.1),
    ("ETA Rio Descoberto", "Ceilândia", 6000.0, 13.4),
    ("ETA Rio Descoberto", "Samambaia", 6000.0, 14.3),
    
    ("ETA Sobradinho", "Sobradinho", 600.0, 2.8),
    ("ETA Sobradinho", "Plano Piloto", 600.0, 17.7),
    ("ETA Sobradinho", "Guará", 600.0, 31.8)
]

# 2. Criação do Objeto do Grafo
G = nx.DiGraph()

# Adiciona os nós
for no, balanco in no_balancos.items():
    G.add_node(no, balance=balanco)

# Adiciona as arestas
for origem, destino, cap, custo in conexoes:
    G.add_edge(origem, destino, capacity=cap, cost=custo)

# 3. Cálculo das Posições (Layout Circular bem distribuído)
pos = nx.circular_layout(G)

# Ajuste radial para colocar os rótulos fora dos círculos dos nós
pos_rotulos = {}
for no, coords in pos.items():
    x, y = coords
    pos_rotulos[no] = (x * 1.20, y * 1.20) # Multiplica por 1.20 para afastar do centro

# 4. Configuração Visual da Figura
plt.figure(figsize=(15, 13), facecolor="white")

# Define as cores dos nós: vermelho para ETAs, azul para RAs
cores_nos = ["#e74c3c" if "ETA" in no else "#2980b9" for no in G.nodes()]

# Desenha os nós
nx.draw_networkx_nodes(
    G, pos,
    node_color=cores_nos,
    node_size=1000,
    edgecolors="white",
    linewidths=2
)

# Desenha as arestas com setas
nx.draw_networkx_edges(
    G, pos,
    edge_color="#2ecc71",
    width=2.5,
    arrowsize=20,
    arrowstyle="-|>",
    min_source_margin=18,
    min_target_margin=18
)

# 5. Adiciona os Rótulos dos Nós (Nome + Balanço de fluxo)
rotulos_nos = {}
for no, bal in no_balancos.items():
    sinal = "+" if bal > 0 else ""
    rotulos_nos[no] = f"{no}\n({sinal}{bal:.1f} l/s)"

nx.draw_networkx_labels(
    G, pos_rotulos,
    labels=rotulos_nos,
    font_size=9,
    font_weight="bold",
    font_color="#2c3e50"
)

# 6. Adiciona os Rótulos das Arestas (Capacidade e Custo)
rotulos_arestas = {}
for u, v, data in G.edges(data=True):
    rotulos_arestas[(u, v)] = f"c: {data['capacity']:.0f}\nd: {data['cost']:.1f}"

nx.draw_networkx_edge_labels(
    G, pos,
    edge_labels=rotulos_arestas,
    font_size=8,
    font_color="#27ae60",
    label_pos=0.5,
    rotate=True
)

# 7. Título e Exibição
plt.title(
    "Modelo de Grafo de Fluxo - Rede de Água DF (Abstrato Simplificado)",
    fontsize=16,
    fontweight="bold",
    color="#1a252f",
    pad=30
)

# Ajusta os limites da imagem para garantir que os rótulos não sejam cortados
plt.xlim(-1.45, 1.45)
plt.ylim(-1.45, 1.45)

# Remove as bordas do gráfico
plt.axis("off")
plt.tight_layout()

# Salva a imagem final
plt.savefig("grafo.png", dpi=300, bbox_inches="tight")
print("Grafo plotado e salvo como 'grafo.png'!")
