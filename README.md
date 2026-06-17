# 💧 Otimização da Rede de Distribuição de Água do Distrito Federal

> **Trabalho acadêmico — PPGI/UnB**
> Modelagem de Fluxo de Custo Mínimo (*Minimum Cost Flow*) aplicada à rede de integração das Estações de Tratamento de Água (ETAs) e Regiões Administrativas (RAs) do DF, resolvida pelo algoritmo **Successive Shortest Path (SSP)**.

---

## 📢 Status e Destaque do Projeto

Este trabalho foi **apresentado e concluído com sucesso**.

O **foco principal** e o real destaque do projeto residem na **modelagem matemática e na resolução algorítmica** da instância de fluxo de custo mínimo da rede de água do DF pelo algoritmo **Successive Shortest Path (SSP)**. Essa contribuição didática e teórica está consolidada no **relatório escrito** (`relatorio.pdf`) e na **apresentação de slides oficial** (`apresentacao.pdf`).

Como um **recurso visual e didático complementar** (um detalhe interessante de enriquecimento visual do que foi alcançado com os resultados de otimização), o projeto conta também com mapas interativos em HTML (`mapa_grafo_ssp.html` e `mapa_grafo_ssp_basico.html`). 

*(Nota: Durante a apresentação original dos slides, os mapas em HTML possuíam pendências técnicas de exibição e alinhamento que foram posteriormente corrigidas por completo — migrando a camada de mapa para o CartoDB Voyager e calibrando os marcadores DivIcon — estando agora 100% funcionais).*

---

## 📂 Estrutura do Repositório

```
trabalho/
├── README.md                       ← Este arquivo
├── .gitignore
│
├── template_slides_unb/            ← 🎓 Recurso extra: Template de slides Beamer/LaTeX da UnB
│   ├── apresentacao.tex            ← Código principal do template
│   ├── apresentacao.pdf            ← PDF compilado demonstrativo do template
│   └── ... (estruturação preâmbulo, capítulos e elementos)
│
└── desenvolvimento/
    ├── escrita_relatorio/          ← 📝 Relatório final completo em LaTeX
    │   ├── relatorio.tex           ← Arquivo LaTeX principal compilador
    │   ├── relatorio.pdf           ← PDF final compilado e revisado
    │   ├── capitulos/              ← Capítulos do relatório escrito
    │   ├── preambulo/              ← Pacotes, estilos e bibliografia do LaTeX
    │   └── referencias.bib         ← Arquivo de citações bibliográficas
    │
    ├── apresentacao_slides/        ← 📊 Apresentação de slides oficial em LaTeX (Beamer)
    │   ├── apresentacao.tex        ← Código-fonte principal da apresentação
    │   ├── apresentacao.pdf        ← PDF compilado dos slides oficiais
    │   └── figuras/                ← Mapas e imagens geradas incluídas nos slides
    │
    ├── python/                     ← 🐍 Código-fonte do algoritmo e mapas
    │   ├── README.md               ← Documentação de execução dos scripts Python
    │   ├── grafo.py                ← Dados do grafo e topologia
    │   ├── ssp_algorithm.py        ← Algoritmo Successive Shortest Path (SSP)
    │   ├── tools.py                ← Funções auxiliares (Bellman-Ford, Dijkstra, etc.)
    │   ├── ssp_solucao.py          ← Orquestrador do algoritmo principal
    │   ├── mapa_ssp_curvado.py     ← Gerador do mapa premium (Bézier + Antpath + Toggle)
    │   ├── grafo_ssp.py            ← Gerador do mapa plano básico
    │   ├── mapa_grafo_ssp.html     ← 🗺️ MAPA INTERATIVO PREMIUM GERADO (abrir no navegador)
    │   ├── mapa_grafo_ssp_basico.html ← MAPA BÁSICO GERADO (abrir no navegador)
    │   └── dados_do_projeto/       ← Bases GIS do Distrito Federal (CSV + GeoJSON)
    │
    └── pdfs/                       ← Artigos acadêmicos e referências consultadas
```

---

## 🧠 Algoritmo SSP — Núcleo da Solução

O coração deste projeto é o algoritmo de fluxo de custo mínimo **Successive Shortest Path (SSP)**, implementado de forma modularizada e estruturado conforme o livro-texto de referência: *"Network Flows: Theory, Algorithms, and Applications"* (Ahuja, Magnanti & Orlin - Figura 9.9).

### Arquitetura e Fluxo de Execução

O código foi dividido de forma a separar os dados da instância, as funções auxiliares e a lógica principal do loop do SSP:

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
| **`tools.py`** | Implementa as **4 primitivas algorítmicas** usadas pelo SSP: (1) Bellman-Ford para potenciais iniciais π; (2) construção do grafo residual G(x) com custos reduzidos c^π; (3) Dijkstra com lista O(V²); (4) reconstrução de caminho mínimo. Cada função possui sua complexidade documentada. |
| **`ssp_algorithm.py`** | Contém a função `successive_shortest_path()` — o **loop principal** do algoritmo. A cada iteração: constrói G(x), roda Dijkstra das fontes, encontra o sumidouro mais próximo, reconstrói o caminho, calcula o gargalo (delta), aumenta o fluxo e atualiza os potenciais. Retorna o fluxo ótimo `x`, potenciais `π` e o histórico de iterações. |
| **`ssp_solucao.py`** | **Orquestrador principal.** Carrega os dados, corrige o balanço de ponto flutuante, executa o SSP, **verifica a otimalidade** (custos reduzidos não-negativos), imprime os fluxos ótimos nas adutoras com custo total, mede o tempo de execução (benchmark) e gera as visualizações estáticas finais (Matplotlib e TikZ). |

### Scripts Auxiliares

| Script | Descrição |
|--------|-----------|
| **`experiment.py`** | Executa o SSP com callback verboso, verifica otimalidade e gera um log detalhado iteração-a-iteração em `ssp_execution_trace.txt`. |
| **`generate_slides_tikz.py`** | Gera automaticamente código TikZ das soluções obtidas para inclusão direta nos slides Beamer. |
| **`grafo_ssp.py`** | Script de modelagem geográfica base: lê os CSVs de dados de entrada, executa transformações de coordenadas UTM→WGS84 e exporta um mapa básico em HTML. |
| **`mapa_ssp_curvado.py`** | Executa a otimização e gera a visualização dinâmica interativa com arcos curvados e animações de fluxo em mapa HTML. |
| **`grafo_visualizacao.py`** | Plota o grafo em layout bipartido estático (Matplotlib) com tema escuro. |
| **`generate_maps_matplotlib.py`** | Gera os mapas georreferenciados estáticos `mapa_topologia.png` e `mapa_fluxos_otimos.png` (Matplotlib) utilizados na apresentação de slides. |
| **`graph_visualization.py`** | Utilitários de desenho auxiliares do grafo. |

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Bibliotecas: `networkx`, `matplotlib`, `folium` (com plugin `AntPath` para a visualização animada)

> **Nota:** Todos os scripts possuem **auto-bootstrap** — ao serem executados no terminal, detectam e ativam automaticamente o ambiente virtual local (`venv/`), se configurado.

### Execução do algoritmo de otimização
Para rodar a otimização principal SSP, verificar condições de otimalidade e gerar saídas de console e gráficas:
```bash
cd desenvolvimento/python/
python3 ssp_solucao.py
```

### Execução de outros experimentos e logs
```bash
# Executa e gera o log detalhado iteração-a-iteração
python3 experiment.py
```

---

## 📊 Resultados e Visualizações

A rede de distribuição modelada é composta por:
- **7 ETAs** (fontes) com capacidade de fornecimento total de **+7.600 l/s**
- **7 RAs** (sumidouros) com demanda total de **-7.600 l/s**
- **26 adutoras** com limites de capacidade variando de 60 a 6.000 l/s e custos lineares (distância geodésica em km)

O algoritmo SSP converge de maneira ótima em menos de **1 ms** em hardware padrão, e os resultados podem ser analisados sob múltiplos formatos de visualização gerados:

### 1. Mapa Interativo Georreferenciado (HTML)
O arquivo `desenvolvimento/python/mapa_grafo_ssp.html` apresenta a solução sobreposta ao mapa geográfico real do Distrito Federal:
- **📍 Nós georreferenciados**: As ETAs e RAs posicionadas geograficamente, com tooltips contendo balanço hídrico, fluxos e custos.
- **🌊 Camada de corpos d'água**: Contorno dos reservatórios do DF (como o Lago Paranoá) obtidos do GeoPortal GDF.
- **🟢 Animações de fluxo**: Os fluxos ativos são representados por arcos curvados com animação *AntPath* (sua velocidade e espessura variam proporcionalmente à magnitude do fluxo).
- **⚪ Elementos de HUD**: Painel de controle para alternar camadas de mapas base (Dark, OpenStreetMap, Positron) e controle visual (exibir rede física inteira ou apenas arcos com fluxos ativos).

*Para visualizar:* Basta abrir o arquivo `desenvolvimento/python/mapa_grafo_ssp.html` diretamente em qualquer navegador Web ou rodar `xdg-open desenvolvimento/python/mapa_grafo_ssp.html`.

### 2. Mapas Estáticos (Matplotlib)
Os mapas `mapa_topologia.png` e `mapa_fluxos_otimos.png` localizados em `desenvolvimento/apresentacao_slides/figuras/` trazem representações geográficas estáticas de alta resolução incorporadas na apresentação de slides.
```bash
# Para gerar/atualizar estes mapas:
python3 generate_maps_matplotlib.py
```

### 3. Diagrama Bipartido de Fluxos (Matplotlib)
Um gráfico clássico de fluxo ligando as fontes no nível superior aos destinos no nível inferior com larguras de linha proporcionais aos fluxos calculados pelo SSP.
```bash
# Para gerar e visualizar:
python3 grafo_visualizacao.py --fluxo
```

---

## 📚 Referências Acadêmicas

- Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993). *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall.
- Atlas de Abastecimento de Água do Distrito Federal — CAESB/GDF.
- GeoPortal do Governo do Distrito Federal — Dados georreferenciados abertos.

---

## 📝 Licença

Projeto acadêmico desenvolvido no contexto do PPGI/UnB. Uso restrito a fins educacionais.
