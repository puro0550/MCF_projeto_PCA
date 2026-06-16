"""
Visualização melhorada do grafo de fluxo de rede hídrica do DF.
Layout bipartido: ETAs (fontes) na fileira superior, RAs (sumidouros) na inferior.
Estilo: apresentação científica elegante — fundo escuro, tipografia clara,
arestas com espessura proporcional ao fluxo, rótulos com caixinha semitransparente.

Uso:
    python grafo_visualizacao.py            -> grafo base (capacidades e custos)
    python grafo_visualizacao.py --fluxo    -> grafo com fluxos SSP ótimos
"""

import os
import sys
import math

script_dir = os.path.dirname(os.path.abspath(__file__))

# Auto-bootstrap: garante que roda no ambiente virtual (venv) com as dependências instaladas
try:
    import networkx as nx
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.patheffects as pe
    import numpy as np
except ImportError:
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Instale as dependências: pip install networkx matplotlib numpy")
        sys.exit(1)

# ─────────────────────────────────────────────
# 1. DADOS DA INSTÂNCIA
# ─────────────────────────────────────────────

NO_BALANCOS = {
    "ETA Brasília":      1200.0,
    "ETA Gama":           320.0,
    "ETA Lago Norte":     700.0,
    "ETA Paranoá":        300.0,
    "ETA Planaltina":      60.0,
    "ETA Rio Descoberto": 4450.0,
    "ETA Sobradinho":     570.0,
    "Ceilândia":         -836.17,
    "Guará":            -1067.97,
    "Planaltina":        -927.23,
    "Plano Piloto":     -1763.40,
    "Samambaia":         -852.72,
    "Sobradinho":       -1101.09,
    "Taguatinga":       -1051.42,
}

# (origem, destino, capacidade l/s, custo/distância km)
CONEXOES = [
    ("ETA Brasília",      "Plano Piloto",  1200.0,  4.7),
    ("ETA Brasília",      "Guará",         1200.0, 11.1),
    ("ETA Brasília",      "Taguatinga",    1200.0, 16.0),
    ("ETA Gama",          "Samambaia",      320.0, 18.8),
    ("ETA Gama",          "Guará",          320.0, 20.3),
    ("ETA Gama",          "Ceilândia",      320.0, 23.9),
    ("ETA Lago Norte",    "Plano Piloto",   700.0,  5.3),
    ("ETA Lago Norte",    "Sobradinho",     700.0, 15.2),
    ("ETA Lago Norte",    "Guará",          700.0, 19.9),
    ("ETA Paranoá",       "Plano Piloto",   300.0,  8.6),
    ("ETA Paranoá",       "Sobradinho",     300.0, 17.0),
    ("ETA Paranoá",       "Guará",          300.0, 22.9),
    ("ETA Planaltina",    "Sobradinho",      60.0,  4.3),
    ("ETA Planaltina",    "Plano Piloto",    60.0, 23.8),
    ("ETA Planaltina",    "Planaltina",      60.0, 30.1),
    ("ETA Rio Descoberto","Taguatinga",    6000.0,  6.1),
    ("ETA Rio Descoberto","Ceilândia",     6000.0, 13.4),
    ("ETA Rio Descoberto","Samambaia",     6000.0, 14.3),
    ("ETA Sobradinho",    "Sobradinho",     600.0,  2.8),
    ("ETA Sobradinho",    "Plano Piloto",   600.0, 17.7),
    ("ETA Sobradinho",    "Guará",          600.0, 31.8),
]

# Fluxos ótimos do SSP (resultado da execução)
# Formato: {(origem, destino): fluxo_l_s}
FLUXOS_SSP = {
    ("ETA Brasília",      "Plano Piloto"):   436.6,
    ("ETA Brasília",      "Guará"):          763.4,
    ("ETA Brasília",      "Taguatinga"):       0.0,
    ("ETA Gama",          "Samambaia"):         0.0,
    ("ETA Gama",          "Guará"):             0.0,
    ("ETA Gama",          "Ceilândia"):       320.0,
    ("ETA Lago Norte",    "Plano Piloto"):    700.0,
    ("ETA Lago Norte",    "Sobradinho"):        0.0,
    ("ETA Lago Norte",    "Guará"):             0.0,
    ("ETA Paranoá",       "Plano Piloto"):    300.0,
    ("ETA Paranoá",       "Sobradinho"):        0.0,
    ("ETA Paranoá",       "Guará"):             0.0,
    ("ETA Planaltina",    "Sobradinho"):        0.0,
    ("ETA Planaltina",    "Plano Piloto"):      0.0,
    ("ETA Planaltina",    "Planaltina"):        0.0,
    ("ETA Rio Descoberto","Taguatinga"):     1051.42,
    ("ETA Rio Descoberto","Ceilândia"):       516.17,
    ("ETA Rio Descoberto","Samambaia"):       852.72,
    ("ETA Sobradinho",    "Sobradinho"):      570.0,
    ("ETA Sobradinho",    "Plano Piloto"):      0.0,
    ("ETA Sobradinho",    "Guará"):             0.0,
}


# ─────────────────────────────────────────────
# 2. LAYOUT BIPARTIDO CUSTOMIZADO
# ─────────────────────────────────────────────

def calcular_posicoes():
    """
    Posiciona ETAs (fontes) na fileira superior e RAs (sumidouros) na inferior.
    Dentro de cada fileira, ordena da esquerda para a direita geograficamente
    (oeste → leste) para minimizar cruzamentos.

    Retorna dict {nome_no: (x, y)}.
    """
    # Ordem geográfica aproximada oeste→leste
    etas_ordem = [
        "ETA Rio Descoberto",  # extremo oeste
        "ETA Sobradinho",
        "ETA Planaltina",
        "ETA Paranoá",
        "ETA Lago Norte",
        "ETA Gama",
        "ETA Brasília",        # leste/centro-sul
    ]
    ras_ordem = [
        "Ceilândia",           # extremo oeste
        "Samambaia",
        "Taguatinga",
        "Guará",
        "Plano Piloto",
        "Planaltina",
        "Sobradinho",          # leste/norte
    ]

    pos = {}
    n_eta = len(etas_ordem)
    n_ra  = len(ras_ordem)

    for i, no in enumerate(etas_ordem):
        x = i / (n_eta - 1) * 10  # spread 0..10
        pos[no] = (x, 3.5)

    for i, no in enumerate(ras_ordem):
        x = i / (n_ra - 1) * 10
        pos[no] = (x, 0.0)

    return pos


# ─────────────────────────────────────────────
# 3. PALETA E ESTILO
# ─────────────────────────────────────────────

FUNDO        = "#0f1923"   # azul-noite profundo
COR_ETA      = "#e05252"   # vermelho coral
COR_RA       = "#4a9eda"   # azul médio
COR_ARESTA_ATIVA   = "#00e5c0"   # ciano-turquesa
COR_ARESTA_INATIVA = "#1e3040"   # cinza-azulado muito escuro
COR_TEXTO    = "#e8f4f8"   # branco frio
COR_SUBTEXTO = "#7faec4"   # azul acinzentado


def plotar_grafo(modo_fluxo: bool = False, salvar_como: str = None):
    """
    Gera e exibe (ou salva) o grafo da rede hídrica do DF.

    Parâmetros
    ----------
    modo_fluxo : bool
        Se True, usa os fluxos ótimos do SSP para espessura/opacidade das arestas
        e mostra apenas arestas com fluxo > 0.
        Se False, mostra todas as arestas com espessura uniforme (grafo base).
    salvar_como : str ou None
        Caminho do arquivo de saída (e.g. "grafo.png"). Se None, apenas exibe.
    """

    # --- Grafo e posições ---
    G = nx.DiGraph()
    for no, bal in NO_BALANCOS.items():
        G.add_node(no, balance=bal)
    for orig, dest, cap, custo in CONEXOES:
        G.add_edge(orig, dest, capacity=cap, cost=custo)

    pos = calcular_posicoes()

    # --- Figura ---
    fig, ax = plt.subplots(figsize=(18, 10), facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    ax.axis("off")

    # ── Linha divisória sutil entre as duas fileiras ──
    ax.axhline(y=1.75, color="#1e3040", linewidth=1, linestyle="--", alpha=0.5, zorder=0)

    # ── Arestas ──
    max_fluxo = max(FLUXOS_SSP.values()) if modo_fluxo else 1.0

    for orig, dest, data in G.edges(data=True):
        x0, y0 = pos[orig]
        x1, y1 = pos[dest]

        if modo_fluxo:
            fluxo = FLUXOS_SSP.get((orig, dest), 0.0)
            if fluxo < 1e-3:
                # Aresta inativa: quase invisível
                cor     = COR_ARESTA_INATIVA
                alpha   = 0.25
                lw      = 0.8
                ativo   = False
            else:
                # Espessura proporcional ao fluxo (min 1.5, max 8)
                lw      = 1.5 + 6.5 * (fluxo / max_fluxo)
                cor     = COR_ARESTA_ATIVA
                alpha   = 0.75 + 0.25 * (fluxo / max_fluxo)
                ativo   = True
        else:
            fluxo = data["capacity"]
            lw    = 1.8
            cor   = COR_ARESTA_ATIVA
            alpha = 0.55
            ativo = True

        # Desenha a aresta como anotação com seta (permite curvatura e z-order fino)
        ax.annotate(
            "",
            xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=cor,
                lw=lw,
                alpha=alpha,
                shrinkA=20, shrinkB=20,
                connectionstyle="arc3,rad=0.0"
            ),
            zorder=2
        )

        # Rótulo da aresta — só para arestas ativas
        if ativo:
            xm = (x0 + x1) / 2
            ym = (y0 + y1) / 2

            if modo_fluxo:
                cap = data["capacity"]
                txt = f"{fluxo:.0f} / {cap:.0f} l/s\n{data['cost']:.1f} km"
            else:
                txt = f"cap: {data['capacity']:.0f}\n{data['cost']:.1f} km"

            ax.text(
                xm, ym, txt,
                fontsize=6.5,
                color=COR_ARESTA_ATIVA,
                ha="center", va="center",
                zorder=5,
                fontfamily="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor=FUNDO,
                    edgecolor=COR_ARESTA_ATIVA,
                    alpha=0.85,
                    linewidth=0.6
                )
            )

    # ── Nós ──
    for no, (x, y) in pos.items():
        bal     = NO_BALANCOS[no]
        is_eta  = bal > 0
        cor_no  = COR_ETA if is_eta else COR_RA
        raio    = 0.28 if is_eta else 0.22

        # Halo suave (glowing effect)
        circ_glow = plt.Circle((x, y), raio * 1.6,
                               color=cor_no, alpha=0.12, zorder=3)
        ax.add_patch(circ_glow)

        # Círculo principal
        circ = plt.Circle((x, y), raio,
                           facecolor=cor_no, zorder=4,
                           linewidth=2, edgecolor="white")
        ax.add_patch(circ)

        # Nome do nó
        nome_curto = no.replace("ETA ", "ETA\n") if is_eta else no
        ax.text(
            x, y + (raio + 0.32 if is_eta else -(raio + 0.32)),
            nome_curto,
            ha="center",
            va="bottom" if is_eta else "top",
            fontsize=8.5,
            fontweight="bold",
            color=COR_TEXTO,
            zorder=6
        )

        # Balanço numérico
        sinal = "+" if bal > 0 else ""
        ax.text(
            x, y + (raio + 0.15 if is_eta else -(raio + 0.14)),
            f"{sinal}{bal:.0f} l/s",
            ha="center",
            va="bottom" if not is_eta else "top",
            fontsize=7.5,
            color=COR_SUBTEXTO,
            style="italic",
            zorder=6
        )

    # ── Título ──
    if modo_fluxo:
        total_fluxo = sum(v for v in FLUXOS_SSP.values())
        custo_total = sum(
            FLUXOS_SSP.get((o, d), 0) * c
            for o, d, _, c in CONEXOES
        )
        titulo   = "Rede Hídrica do DF — Fluxo Ótimo SSP"
        subtitulo = f"Fluxo total: {total_fluxo:.0f} l/s  ·  Custo mínimo de transporte: {custo_total:,.0f} km·l/s"
    else:
        titulo    = "Rede Hídrica do DF — Grafo de Fluxo"
        subtitulo = f"{G.number_of_nodes()} nós  ·  {G.number_of_edges()} adutoras"

    ax.text(0.5, 1.01, titulo,
            transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=17, fontweight="bold",
            color=COR_TEXTO)
    ax.text(0.5, 0.985, subtitulo,
            transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=10, color=COR_SUBTEXTO)

    # ── Legenda ──
    leg_patches = [
        mpatches.Patch(color=COR_ETA, label="ETA — Estação de Tratamento (supply)"),
        mpatches.Patch(color=COR_RA,  label="RA — Região Administrativa (demand)"),
    ]
    if modo_fluxo:
        leg_patches += [
            mpatches.Patch(color=COR_ARESTA_ATIVA,   label="Adutora com fluxo ativo"),
            mpatches.Patch(color=COR_ARESTA_INATIVA, label="Adutora sem fluxo (capacidade ociosa)"),
        ]
    ax.legend(
        handles=leg_patches,
        loc="lower center",
        ncol=2,
        frameon=True,
        facecolor="#0d1820",
        edgecolor="#1e3040",
        labelcolor=COR_TEXTO,
        fontsize=9,
        bbox_to_anchor=(0.5, -0.06)
    )

    # ── Rótulos das fileiras ──
    ax.text(-0.3, 3.5, "FONTES", ha="left", va="center",
            fontsize=9, color=COR_ETA, fontweight="bold", alpha=0.7)
    ax.text(-0.3, 0.0, "DEMANDA", ha="left", va="center",
            fontsize=9, color=COR_RA, fontweight="bold", alpha=0.7)

    # ── Limites e margem ──
    ax.set_xlim(-1.2, 11.2)
    ax.set_ylim(-1.6, 5.2)

    plt.tight_layout(pad=1.5)

    if salvar_como:
        # Resolve full path relative to the script directory if it's not absolute
        if not os.path.isabs(salvar_como):
            salvar_como = os.path.join(script_dir, salvar_como)
        plt.savefig(salvar_como, dpi=300, bbox_inches="tight", facecolor=FUNDO)
        print(f"Salvo: {salvar_como}")
    else:
        plt.show()

    plt.close(fig)


# ─────────────────────────────────────────────
# 4. PONTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    modo_fluxo = "--fluxo" in sys.argv

    nome_saida = "grafo_ssp_fluxos_v2.png" if modo_fluxo else "grafo_v2.png"
    plotar_grafo(modo_fluxo=modo_fluxo, salvar_como=nome_saida)
