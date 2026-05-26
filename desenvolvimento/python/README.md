# Resumo do Desenvolvimento - Rede de Água do DF (SSP)

Esta pasta contém a implementação em Python para a modelagem e visualização da rede de distribuição de água do Distrito Federal, voltada para a aplicação do algoritmo **Successive Shortest Paths (SSP)** para Fluxo de Custo Mínimo (Minimum Cost Flow).

---

## 📂 Estrutura de Diretórios e Arquivos

*   **`dados_do_projeto/`**: Diretório contendo as bases de dados brutas em formato CSV e GeoJSON:
    *   `estacoes_tratamento_agua.csv`: Dados de localização e capacidade das 7 Estações de Tratamento de Água (ETAs).
    *   `CONSUMO_AGUA_RA.csv`: Dados de consumo de água e delimitações geográficas (WKT) das Regiões Administrativas (RAs).
    *   `CORPOS_DAGUA.json`: Polígonos das bacias e corpos d'água da região do DF.
*   **`venv/`**: Ambiente virtual Python contendo as bibliotecas necessárias para execução (`folium`, `networkx`, `matplotlib`).
*   **`grafo_ssp.py`**: Script principal de processamento geográfico e geração do mapa interativo.
*   **`mapa_grafo_ssp.html`**: Mapa interativo gerado contendo a plotagem da rede sobre o DF.
*   **`grafo.py`**: Script simplificado e legível para plotagem abstrata do grafo.
*   **`grafo.png`**: Imagem estática gerada pelo script simplificado.

---

## 🛠️ Descrição dos Scripts Desenvolvidos

### 1. Script Principal: `grafo_ssp.py`
Este script realiza a leitura dos arquivos de dados, o processamento espacial e a geração de um mapa geográfico interativo.

*   **Processamento Geográfico**:
    *   Converte as coordenadas das ETAs do formato `MULTIPOINT ((lat lon))` (corrigindo a inversão lat/lon original).
    *   Calcula o centroide geográfico das RAs a partir de suas coordenadas em formato UTM Zona 23S, utilizando equações elipsoidais manuais para transposição para Latitude/Longitude (WGS84).
*   **Construção da Rede**:
    *   Conecta cada uma das **7 ETAs** às **3 RAs mais próximas** utilizando a distância geodésica calculada pela fórmula de Haversine.
    *   Aloca a injeção total de **+7600 l/s** das fontes (ETAs) e distribui de forma balanceada a demanda correspondente (**-7600 l/s**) entre as RAs de forma proporcional aos pesos de consumo de cada região.
*   **Visualização Geográfica (`mapa_grafo_ssp.html`)**:
    *   Desenha os corpos d'água do DF a partir do GeoJSON.
    *   Plota ETAs (ícones de gotas vermelhas) e RAs (ícones de casas azuis).
    *   Desenha tubulações com espessura proporcional à capacidade da adutora.
    *   **Controle de Camadas (Toggles)**: Permite ocultar completamente o mapa de fundo (OpenStreetMap) e visualizar as estruturas sobre um fundo sólido escuro ou sólido claro para destaque do grafo.
    *   Imprime tabelas formatadas de nós e arestas no terminal durante a execução.

---

### 2. Script Simplificado: `grafo.py`
Focado na clareza de código e visualização esquemática simplificada da topologia da rede.

*   **Código Limpo e Didático**:
    *   Estrutura de dados (balanços, capacidades e custos das conexões) hardcoded diretamente em dicionários e listas simples no Python.
    *   Elimina a necessidade de ler arquivos externos, processar UTMs ou calcular distâncias complexas.
*   **Visualização Abstrata (`grafo.png`)**:
    *   Desenha o grafo completo usando um layout circular simétrico no `NetworkX` e `Matplotlib`.
    *   Rótulos dos nós (nome e balanço de fluxo) posicionados radialmente para fora do círculo para evitar sobreposições.
    *   Rótulos de arestas indicando capacidade (`c:`) e custo/distância (`d:`) exibidos diretamente sobre as setas direcionais.

---

## 🚀 Como Executar os Scripts

Ambos os scripts possuem um mecanismo de **auto-bootstrap** integrado, o que significa que, ao serem chamados com o interpretador global do sistema, eles localizam e utilizam automaticamente o ambiente virtual local (`venv`):

```bash
# Para atualizar o mapa interativo HTML e ver as tabelas de fluxo no terminal:
python3 grafo_ssp.py

# Para gerar a imagem esquemática simplificada (grafo.png):
python3 grafo.py
```
