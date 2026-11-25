# TCC — Esqueleto LaTeX

Esqueleto LaTeX do Trabalho de Conclusão de Curso **"Avaliação Experimental de LLMs na Resolução de Problemas da Olimpíada Brasileira de Informática: Modalidade Programação, Nível Sênior"** (IC-UFAL), baseado no template [`ufal-tesis`](https://github.com/TETEURYAN/ufal-tesis).

## Estrutura

- `main.tex`: documento principal e preâmbulo (`JITH.cls`, `natbib`, `tikz`, `pgfplots`, `tcolorbox`, `easyReview`).
- `Identificacao.tex`: título, autor, e-mail, orientação, banca, local e data.
- `estilo-visual.tex`: paleta de cores, macros de tabela (`\tfirst`, `\tsecond`, `\gain`, `\loss`, `\barcell`, `\heatmap`), ambiente `quadro` e o comando `\guiasecao{...}` para os roteiros de escrita do esqueleto.
- `macros.tex`: macros matemáticas e tipográficas do domínio (`\passat{1}`, `\veredito{AC}`, `\bigo{...}`).
- `Cap00/`: elementos pré-textuais (`logo_ic.png`, `Dedicatoria.tex`, `Epigrafe.tex`, `Agradecimentos.tex`, `Resumo.tex`, `Abstract.tex`, `Abreviaturas.tex`, `Simbolos.tex`).
- `Cap01/Capitulo1.tex`: Introdução, Perguntas de Pesquisa (PP1–PP5), Objetivos, Relevância e Organização.
- `Cap02/Capitulo2.tex`: Trabalhos Relacionados.
- `Cap03/FundamentacaoTeorica.tex`: Fundamentação Teórica.
- `Cap04/Capitulo4.tex`: Metodologia (base OBI Sênior, arquitetura do benchmark, desenho experimental de PP1–PP5 e limitações).
- `Cap05/Capitulo5.tex`: Resultados e Discussão (organizado por PP1–PP5, ameaças à validade e contribuições).
- `Conc/Conclusao.tex`: Conclusão, Contribuições, Limitações e Trabalhos Futuros.
- `Ref/`: `referencia.tex` e `Referencias.bib`.
- `Apendices/`: `ApendiceA.tex` (prompts em `Apendices/prompts/`), `ApendiceB.tex` (esquema de dados) e `ApendiceC.tex` (materiais complementares).

## Dicas de uso durante a escrita

1. Preencha os dados pessoais em `Identificacao.tex`.
2. Cada seção traz um bloco `\guiasecao{...}` com o roteiro do que redigir e comentários `% TODO:`. Ao finalizar a redação (ou para gerar uma prévia limpa sem as caixas de roteiro), altere `\guiaescritatrue` para `\guiaescritafalse` em `estilo-visual.tex`.
3. Caso o título longo ultrapasse a altura útil da capa (`\capa`), ajuste a escala ou tamanho da fonte do título no arquivo `JITH.cls` (em `\def\capa`).
4. Na versão final de entrega, altere `\setreviewson` para `\setreviewsoff` em `main.tex`.

## Compilação

```bash
cd article-tcc
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```
