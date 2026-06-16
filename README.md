# 💧 Otimização da Rede de Distribuição de Água do Distrito Federal

> **Trabalho acadêmico — PPGI/UnB**
> Modelagem de Fluxo de Custo Mínimo (*Minimum Cost Flow*) aplicada à rede de integração das Estações de Tratamento de Água (ETAs) e Regiões Administrativas (RAs) do DF, resolvida pelo algoritmo **Successive Shortest Path (SSP)**.

---

## ⚠️ Disclaimer

> **A versão escrita completa do trabalho (documento final em LaTeX/PDF) ainda não está incluída neste repositório.** Assim que a parte escrita estiver finalizada, ela será adicionada aqui. No momento, o repositório contém **todo o código-fonte**, os **dados do projeto**, a **apresentação de slides em LaTeX (Beamer)** e, principalmente, a **visualização interativa em HTML** que permite explorar a rede e os fluxos ótimos georreferenciados sobre o mapa do DF.

---

## 📂 Estrutura do Repositório

```
trabalho/
├── README.md                       ← Este arquivo
├── .gitignore
│
└── desenvolvimento/
    ├── python/                     ← Código-fonte principal
    │   ├── README.md               ← Documentação detalhada dos scripts Python
    │   ├── grafo.py                ← Definição dos dados da instância (nós, arcos, balanços)
    │   ├── ssp_algorithm.py        ← Implementação modularizada do algoritmo SSP
    │   ├── tools.py                ← Ferramentas auxiliares (Bellman-Ford, Dijkstra, grafo residual)
    │   ├── ssp_solucao.py          ← Script principal: executa o SSP, verifica e plota resultados
    │   ├── grafo_ssp.py            ← Gerador do mapa interativo HTML (Folium) — versão base
    │   ├── mapa_ssp_curvado.py     ← Gerador do mapa interativo premium (Bézier + AntPath animado)
    │   ├── grafo_visualizacao.py   ← Visualização estática bipartida (dark theme, Matplotlib)
    │   ├── generate_maps_matplotlib.py  ← Gerador de mapas georreferenciados estáticos (Matplotlib)
    │   ├── experiment.py           ← Experimento e geração de trace detalhado de execução
    │   ├── generate_slides_tikz.py ← Gerador automático de código TikZ para os slides
    │   ├── graph_visualization.py  ← Visualizações auxiliares do grafo
    │   ├── mapa_grafo_ssp.html     ← 🗺️ MAPA INTERATIVO GERADO (abrir no navegador!)
    │   ├── ssp_execution_trace.txt ← Log completo iteração-a-iteração do SSP
    │   ├── grafo_ssp_fluxos_tikz.txt ← Código TikZ gerado para inclusão no LaTeX
    │   ├── grafo_tikz.tex          ← Template TikZ do grafo
    │   ├── dados_do_projeto/       ← Bases de dados georreferenciadas (CSV + GeoJSON)
    │   │   ├── estacoes_tratamento_agua.csv
    │   │   ├── CONSUMO_AGUA_RA.csv
    │   │   ├── CORPOS_DAGUA.json
    │   │   └── ... (outros dados de apoio)
    │   └── venv/                   ← Ambiente virtual Python (ignorado pelo git)
    │
    ├── apresentacao_slides/        ← Apresentação em LaTeX (Beamer)
    │   ├── apresentacao.tex        ← Arquivo principal da apresentação
    │   ├── apresentacao.pdf        ← PDF compilado dos slides
    │   ├── capitulos/              ← Seções da apresentação
    │   ├── elementos/              ← Elementos visuais (capa, etc.)
    │   ├── preambulo/              ← Configurações e pacotes LaTeX
    │   ├── figuras/                ← Imagens usadas nos slides (mapas gerados)
    │   ├── paginas_png/            ← Páginas renderizadas em PNG
    │   └── referencias.bib         ← Referências bibliográficas
    │
    └── pdfs/                       ← Artigos e referências acadêmicas consultadas
        ├── emd_original_paper.pdf  ← Paper original do Earth Mover's Distance
        └── schrodinger_*.pdf/.txt  ← Papers sobre bridges de Schrödinger
```

---

## 🗺️ Visualização Interativa em HTML — Destaque do Projeto

Um dos maiores destaques deste projeto é o **mapa interativo georreferenciado** (`mapa_grafo_ssp.html`), que pode ser aberto diretamente no navegador. Ele apresenta:

- **📍 Nós georreferenciados**: As 7 ETAs e 7 RAs do DF posicionadas em suas coordenadas geográficas reais, com ícones SVG customizados (gotas vermelhas para ETAs, casas azuis para RAs).
- **🌊 Corpos d'água**: Polígonos do Lago Paranoá e demais reservatórios extraídos do portal oficial de dados georreferenciados do GeoPortal do GDF — renderizados como camadas semitransparentes sobre o mapa.
- **🟢 Fluxos ótimos animados**: Arcos curvados com animação *marching ants* (AntPath) em verde, com largura proporcional ao fluxo otimizado — quanto maior o fluxo, mais grossa e rápida a animação.
- **⚪ Conexões ociosas**: Adutoras com capacidade mas sem fluxo ativo exibidas em cinza tracejado.
- **🔀 Toggle Rede Física / Solução Ótima**: Um botão flutuante permite alternar entre a visualização da rede física (todas as adutoras em azul) e a solução ótima do SSP (fluxos ativos em verde).
- **🗺️ Múltiplas camadas de mapa base**: Três opções de base — Mapa Escuro (CARTO Dark Matter), OpenStreetMap e Mapa Claro (CARTO Positron).
- **💡 Tooltips interativos**: Ao passar o mouse sobre qualquer nó ou arco, um painel mostra nome, balanço, capacidade, fluxo e custo.
- **🎨 Design glassmorphism**: Legenda e HUD com efeito glassmorphism (backdrop-filter blur), tipografia premium e paleta de cores cuidadosamente curada.

> **Nota sobre os dados geográficos:** Os mapas e coordenadas utilizados foram extraídos de portais oficiais de dados abertos do Governo do Distrito Federal (GeoPortal/GDF), incluindo as localizações das ETAs, os limites das RAs (em UTM Zona 23S, convertidos para WGS84 por transformação elipsoidal manual) e os polígonos dos corpos d'água.

**Muitas das visualizações e funcionalidades desenvolvidas neste projeto — como os mapas interativos, as múltiplas camadas de base, os toggles de rede/solução, e as animações de fluxo — tiveram que ficar de fora da apresentação de slides por limitações de tempo e formato.** O HTML é a melhor forma de apreciar o trabalho completo.

### Como visualizar:
```bash
# Basta abrir o arquivo no navegador:
xdg-open desenvolvimento/python/mapa_grafo_ssp.html
# ou simplesmente dê duplo-clique no arquivo no gerenciador de arquivos.
```

---

## 🧠 Algoritmo SSP — Arquitetura Modularizada

O algoritmo principal segue a implementação canônica do **Successive Shortest Path** conforme descrita no livro *"Network Flows: Theory, Algorithms, and Applications"* de Ahuja, Magnanti & Orlin (Figura 9.9). O código está dividido em módulos com responsabilidades claras:

### Fluxo de Execução

```
ssp_solucao.py  (Orquestrador Principal)
    │
    ├── grafo.py  (Dados da Instância)
    │   └── Exporta: no_balancos, conexoes
    │
    ├── ssp_algorithm.py  (Loop Principal do SSP)
    │   │
    │   └── tools.py  (Primitivas Algorítmicas)
    │       ├── initialize_potentials()   → Bellman-Ford multi-source  O(V·E)
    │       ├── build_residual_graph()    → Construção de G(x)         O(E)
    │       ├── run_dijkstra()            → Dijkstra com lista         O(V²)
    │       └── trace_shortest_path()     → Reconstrução via parent    O(V)
    │
    └── Saídas:
        ├── Terminal: trace iteração-a-iteração + fluxos + benchmark
        ├── grafo_ssp_fluxos.png  (imagem do grafo com fluxos)
        └── grafo_ssp_fluxos_tikz.txt  (código TikZ para LaTeX)
```

### Descrição dos Módulos

| Módulo | Responsabilidade |
|--------|------------------|
| **`grafo.py`** | Define a instância do problema: os **14 nós** (7 ETAs com injeção positiva, 7 RAs com demanda negativa) e as **26 adutoras** com capacidade e custo (distância geodésica em km). Os dados são *hardcoded* de forma didática e legível. |
| **`tools.py`** | Implementa as **4 primitivas algorítmicas** usadas pelo SSP: (1) Bellman-Ford multi-source para potenciais iniciais π; (2) construção do grafo residual G(x) com custos reduzidos c^π; (3) Dijkstra com lista O(V²); (4) reconstrução de caminho mínimo via parent pointers. Cada função documenta sua complexidade. |
| **`ssp_algorithm.py`** | Contém a função `successive_shortest_path()` — o **loop principal** do algoritmo. A cada iteração: constrói G(x), roda Dijkstra das fontes, encontra o sumidouro mais próximo, reconstrói o caminho, calcula o gargalo (delta), aumenta o fluxo, e atualiza os potenciais. Retorna o fluxo ótimo `x`, potenciais `π` e histórico completo de iterações. |
| **`ssp_solucao.py`** | **Orquestrador principal.** Carrega os dados, corrige o balanço por ponto flutuante, executa o SSP, **verifica a otimalidade** (custos reduzidos não-negativos), imprime os fluxos ótimos nas adutoras com custo total, mede o tempo de execução (benchmark), e gera o grafo visual final com Matplotlib e código TikZ para o relatório LaTeX. |

### Outros Scripts

| Script | Descrição |
|--------|-----------|
| **`grafo_ssp.py`** | Processamento geográfico completo: lê CSVs, converte UTM→WGS84, conecta ETAs às 3 RAs mais próximas via Haversine, gera mapa Folium com corpos d'água. |
| **`mapa_ssp_curvado.py`** | Versão premium do mapa: resolve o SSP, plota arcos Bézier curvados, animação AntPath para fluxos ativos, toggle rede física/solução, design HUD glassmorphism. |
| **`grafo_visualizacao.py`** | Visualização estática bipartida com Matplotlib: fundo escuro, ETAs em cima, RAs embaixo, glow effects, arestas com espessura proporcional ao fluxo. |
| **`generate_maps_matplotlib.py`** | Gera mapas estáticos com corpos d'água e arestas curvadas sobre coordenadas geográficas reais (Matplotlib). Produz `mapa_topologia.png` e `mapa_fluxos_otimos.png`. |
| **`experiment.py`** | Executa o SSP com callback verboso, verifica otimalidade, e salva um trace detalhado de todas as iterações em `ssp_execution_trace.txt`. |
| **`generate_slides_tikz.py`** | Gera automaticamente código TikZ para inclusão nos slides Beamer. |

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Bibliotecas: `networkx`, `matplotlib`, `folium` (com plugin `AntPath`)

> **Nota:** Todos os scripts possuem **auto-bootstrap** — ao serem chamados com o interpretador global, eles detectam e utilizam automaticamente o ambiente virtual local (`venv/`).

### Execução do algoritmo principal

```bash
cd desenvolvimento/python/

# Executa o SSP, imprime os resultados, gera gráfico e código TikZ
python3 ssp_solucao.py
```

**O que acontece ao rodar `ssp_solucao.py`:**

1. **Carrega** os dados de `grafo.py` (14 nós, 26 arcos)
2. **Balanceia** o grafo (correção de ponto flutuante)
3. **Executa** o SSP modularizado (`ssp_algorithm.py` + `tools.py`)
4. **Imprime** cada iteração com: fonte, destino, caminho mínimo, gargalo
5. **Verifica** a otimalidade via custos reduzidos c^π ≥ 0
6. **Imprime** os fluxos finais em todas as adutoras com custo total
7. **Mede** o tempo de execução (benchmark em ms)
8. **Gera** o gráfico visual `grafo_ssp_fluxos.png` (NetworkX + Matplotlib)
9. **Exporta** código TikZ para `grafo_ssp_fluxos_tikz.txt`

### Geração do mapa interativo HTML

```bash
# Versão premium com arcos curvados e animação (recomendado):
python3 mapa_ssp_curvado.py

# Versão base com linhas retas:
python3 grafo_ssp.py
```

### Geração de visualizações estáticas

```bash
# Grafo bipartido com dark theme (com ou sem fluxos):
python3 grafo_visualizacao.py           # Topologia base
python3 grafo_visualizacao.py --fluxo   # Com fluxos SSP ótimos

# Mapas georreferenciados estáticos (com corpos d'água):
python3 generate_maps_matplotlib.py

# Grafo circular simplificado:
python3 grafo.py
```

### Experimento e trace de execução

```bash
# Roda o SSP com verbose e salva trace iteração-a-iteração:
python3 experiment.py
# Saída em: ssp_execution_trace.txt
```

---

## 📊 Resultados

A rede modelada é composta por:
- **7 ETAs** (fontes) com injeção total de **+7.600 l/s**
- **7 RAs** (sumidouros) com demanda total de **-7.600 l/s**
- **26 adutoras** com capacidades variando de 60 a 6.000 l/s e custos de 2,78 a 42,83 km

O algoritmo SSP converge em poucas iterações (< 1 ms em hardware moderno) e encontra a **solução de custo mínimo** verificada pela condição de otimalidade dos custos reduzidos.

---

## 📚 Referências Acadêmicas

- Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993). *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall.
- Atlas de Abastecimento de Água do Distrito Federal — CAESB/GDF.
- GeoPortal do Governo do Distrito Federal — Dados georreferenciados abertos.

---

## 📝 Licença

Projeto acadêmico desenvolvido no contexto do PPGI/UnB. Uso restrito a fins educacionais.
