# 📊 Template de Slides — UnB / PPGI

Template modularizado de apresentação Beamer com as **cores oficiais da Universidade de Brasília (UnB)**.

## 📁 Estrutura do Projeto

```
template_slides_unb/
├── apresentacao.tex          # Arquivo principal (compilar este)
├── referencias.bib           # Referências bibliográficas (BibTeX)
├── README.md                 # Este arquivo
├── preambulo/
│   ├── pacotes.tex           # Pacotes LaTeX utilizados
│   ├── estilo.tex            # Cores e estilo visual UnB
│   └── cabecalho.tex         # Título, autor, orientador, data
├── capitulos/
│   ├── 01_introducao.tex     # Slides de introdução e motivação
│   ├── 02_desenvolvimento.tex # Slides de metodologia e resultados
│   └── 03_conclusao.tex      # Slides de conclusão e referências
├── elementos/
│   └── unb_logo.jpg          # Logo da UnB (usado no rodapé)
└── figuras/
    └── (suas figuras aqui)   # Diretório para imagens dos slides
```

## 🚀 Como Usar

1. **Edite** `preambulo/cabecalho.tex` com o título, seu nome e orientador.
2. **Preencha** os capítulos em `capitulos/` com o conteúdo da sua apresentação.
3. **Adicione** suas referências em `referencias.bib`.
4. **Coloque** suas figuras na pasta `figuras/`.
5. **Compile** com:
   ```bash
   pdflatex apresentacao.tex
   bibtex apresentacao
   pdflatex apresentacao.tex
   pdflatex apresentacao.tex
   ```

## 🎨 Personalização

- **Cores**: As cores oficiais da UnB estão definidas em `preambulo/estilo.tex`.
- **Logo**: Substitua `elementos/unb_logo.jpg` se necessário.
- **Tema Beamer**: O tema base é `Luebeck`. Pode ser alterado em `preambulo/estilo.tex`.
- **Novos capítulos**: Crie novos `.tex` em `capitulos/` e adicione `\input{capitulos/novo_arquivo}` em `apresentacao.tex`.

## 📝 Dicas

- Use `\begin{block}{...}` para blocos de destaque (azul).
- Use `\begin{exampleblock}{...}` para blocos de exemplo (verde).
- Use `\begin{alertblock}{...}` para alertas (amarelo/ouro).
- Use `\begin{columns}...\end{columns}` para layouts em colunas.
- Use `[shrink=N]` no frame para reduzir conteúdo que não cabe.
