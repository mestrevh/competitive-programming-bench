# Competitive Programming Bench

Arcabouço experimental automatizado para avaliação de Modelos de Linguagem de Grande Porte (LLMs e MLLMs) na resolução de problemas de programação competitiva com julgamento local multilinguagem, controle de modalidades visuais, engenharia de *prompt* e telemetria de consumo de *tokens* e custos financeiros.

---

## 1. Contexto Acadêmico e Projetos Relacionados

Este repositório foi desenvolvido no âmbito do Trabalho de Conclusão de Curso (TCC) do bacharelado em Ciência da Computação no Instituto de Computação da Universidade Federal de Alagoas (IC-UFAL), em colaboração com o grupo de pesquisa **GEMA-LAB**.

A arquitetura e a base de dados utilizadas neste projeto dão continuidade e expandem dois repositórios fundamentais desenvolvidos pelo grupo:

1. **Extração e Curadoria de Questões da OBI** ([https://github.com/GEMA-LAB/problems-of-the-obi](https://github.com/GEMA-LAB/problems-of-the-obi)): repositório responsável pelo protocolo de coleta, limpeza, estruturação em JSON, descrições textuais de figuras e organização dos gabaritos e casos de teste oficiais da Olimpíada Brasileira de Informática (OBI).
2. **Arquitetura Preliminar de Benchmarking da OBI** ([https://github.com/GEMA-LAB/obi-benchmarking](https://github.com/GEMA-LAB/obi-benchmarking)): implementação inicial do ambiente de avaliação para problemas da OBI, a partir da qual o presente `competitive-programming-bench` foi estendido para incorporar suporte completo a cinco linguagens de programação (`Python`, `C`, `C++`, `Java` e `JavaScript`), validação por modo oráculo, três modalidades de representação de figuras (`text`, `img` em Base64 e `description`), injeção parametrizada de limites de tempo e memória e registro cumulativo de histórico experimental.

---

## 2. Estrutura do Repositório

```text
competitive-programming-bench/
├── article-tcc/             # Código-fonte LaTeX da monografia (TCC IC-UFAL)
├── database/                # Conjuntos de problemas estruturados para avaliação
│   └── dataset_obi_senior/  # Base com 125 problemas do Nível Sênior da OBI (2016-2025)
├── metrics/                 # Cadernos Jupyter para análise estatística dos resultados
├── prompts/                 # Templates de prompt (Zero-Shot, Few-Shot, CoT Pólya)
├── results/                 # Histórico JSON de execuções e sumários CSV do juiz local
├── src/                     # Código-fonte da ferramenta de benchmarking
│   ├── core/                # Configuração (.env), gerenciador de arquivos, prompts e orquestrador
│   ├── models/              # Modelos de dados Pydantic (Problem, Example, EvaluationOracle)
│   └── services/            # Cliente de API compatível com OpenAI (LLM) e juiz local (JudgeService)
├── .env.example             # Modelo de configuração de variáveis de ambiente e provedores
├── main.py                  # Ponto de entrada interativo via linha de comando (CLI)
├── pyproject.toml           # Especificação do projeto e dependências Python
└── uv.lock                  # Arquivo de bloqueio de versões do gerenciador uv
```

---

## 3. Pré-requisitos do Ambiente

Para executar o pipeline completo de geração de código e julgamento local nas cinco linguagens suportadas, o ambiente deve atender aos seguintes requisitos:

### 3.1 Ambiente Python
- **Python**: versão `3.14` ou superior (conforme especificado em `pyproject.toml`).
- **Gerenciador de pacotes**: recomenda-se o uso do `uv` (ou `pip` com ambiente virtual padrão `venv`).

### 3.2 Compiladores e Interpretadores (Juiz Local)
O módulo `JudgeService` (`src/services/judge_service.py`) invoca diretamente os compiladores e interpretadores instalados no sistema operacional. Certifique-se de que as ferramentas correspondentes às linguagens que deseja avaliar estejam disponíveis na variável `PATH` do sistema:

| Linguagem | Comando Exigido no `PATH` | Flags de Compilação / Execução Adotadas |
| :--- | :--- | :--- |
| **Python** | `python` | Execução direta pelo interpretador do ambiente ativo |
| **C** | `gcc` | `gcc -DNDEBUG <arquivo.c> -o <binario> -O2 -lm` |
| **C++** | `g++` | `g++ -include cassert -include cstdint -include cstring -include algorithm -DNDEBUG <arquivo.cpp> -o <binario> -O2` |
| **Java** | `javac` e `java` | `javac -encoding UTF-8 <Classe>.java` e `java -cp <dir> <Classe>` |
| **JavaScript** | `node` | `node --check <arquivo.js>` e `node <arquivo.js>` (com *shim* automático de `scanf`/`printf` padrão OBI) |

Para verificar se todos os compiladores estão acessíveis no terminal, execute:

```bash
python --version
gcc --version
g++ --version
javac -version
node --version
```

---

## 4. Passo a Passo de Instalação e Configuração

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/mestrevh/competitive-programming-bench.git
cd competitive-programming-bench
```

### Passo 2: Instalar as Dependências Python

Utilizando o gerenciador `uv` (recomendado):

```bash
uv sync
```

Alternativamente, utilizando `venv` e `pip`:

```bash
python -m venv .venv
# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# No Linux ou macOS:
source .venv/bin/activate

pip install -e .
```

### Passo 3: Configurar a Base de Dados em `database/`

O repositório já inclui o diretório `database/dataset_obi_senior/` contendo 125 problemas do Nível Sênior da OBI (2016 a 2025) e 4.681 casos de teste oficiais. Caso deseje adicionar novos conjuntos de dados (por exemplo, extraídos de [https://github.com/GEMA-LAB/problems-of-the-obi](https://github.com/GEMA-LAB/problems-of-the-obi)), crie uma subpasta dentro de `database/` obedecendo à seguinte estrutura para cada questão:

```text
database/<nome_do_dataset>/<nome_da_questao>/
├── problem.json             # Enunciado, formato de E/S, restrições, exemplos e metadados
├── imgs/                    # (Opcional) Imagens referenciadas no enunciado (ex.: 1.png)
├── solutions/               # (Opcional) Soluções humanas de referência para o Modo Oráculo
└── test_cases/
    ├── inputs/              # Arquivos de entrada dos casos de teste (*.in)
    └── outputs/             # Arquivos de saída esperada correspondentes (*.out)
```

O arquivo `problem.json` deve conter os campos validados pelo esquema `src/models/problem.py`: `title`, `statement`, `input`, `output`, `constraints`, `examples`, `imgs`, `imgs_description`, `rating`, `year`, `level`, `period`, `topics`, `time_limit` (em segundos) e `memory_limit` (em MB).

### Passo 4: Configurar Provedores de LLM no Arquivo `.env`

Copie o arquivo `.env.example` para um novo arquivo chamado `.env` na raiz do projeto:

```bash
cp .env.example .env
```

O sistema utiliza o delimitador duplo (`__`) para carregar múltiplos provedores dinamicamente por meio do módulo `src/core/config.py`. Para cada modelo que desejar avaliar, defina um prefixo identificador (`<PROVEDOR>`) acompanhado das cinco variáveis abaixo (tarifas expressas em dólares americanos por 1 milhão de *tokens*):

```ini
# Exemplo 1: Provedor compatível com OpenAI
OPENAI__API_KEY=sk-proj-...
OPENAI__BASE_URL=https://api.openai.com/v1
OPENAI__MODEL=openai/gpt-6-luna
OPENAI__INPUT_PRICE=0.10
OPENAI__OUTPUT_PRICE=0.50

# Exemplo 2: Google Gemini (endpoint compatível com OpenAI)
GEMINI__API_KEY=AIzaSy...
GEMINI__BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI__MODEL=gemini-3.8-flash
GEMINI__INPUT_PRICE=0.75
GEMINI__OUTPUT_PRICE=3.75

# Exemplo 3: DeepSeek / OpenRouter
DEEPSEEK__API_KEY=sk-or-v1-...
DEEPSEEK__BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK__MODEL=deepseek/deepseek-v4.1-flash
DEEPSEEK__INPUT_PRICE=0.003
DEEPSEEK__OUTPUT_PRICE=0.60
```

Todos os provedores cadastrados com `API_KEY`, `BASE_URL` e `MODEL` válidos aparecerão automaticamente na listagem interativa do sistema.

### Passo 5: Configurar ou Adicionar Templates de Prompt em `prompts/`

Os modelos de *prompt* ficam armazenados no diretório `prompts/` em arquivos `.txt` ou `.md` (como `zero_shot.txt`, `few_shot_c.txt` e `chain_of_thought_polya.txt`). Durante a execução, o módulo `src/core/prompt_builder.py` substitui automaticamente os seguintes marcadores dinâmicos:

- `{language}`: nome da linguagem de programação selecionada;
- `{problem}`: texto estruturado da questão (título, enunciado, entrada, saída, restrições, exemplos e, quando ativado, limites de execução);
- `{time_limit}`: limite de tempo da questão em segundos;
- `{memory_limit}`: limite de memória da questão em megabytes (MB).

---

## 5. Passo a Passo de Execução

Para iniciar a ferramenta, execute o script principal a partir da raiz do projeto:

```bash
uv run python main.py
# Ou, com o ambiente virtual ativado:
python main.py
```

O sistema opera em dois modos distintos, detalhados a seguir.

### 5.1 Modo 1: Validação Oráculo (`oracle = True`)

O Modo Oráculo verifica a integridade dos casos de teste e a calibração do ambiente local antes da execução com LLMs. Nele, nenhuma API externa é chamada: o sistema localiza as soluções de referência dentro da pasta `solutions/` de cada problema, compila-as e executa-as contra os casos de teste oficiais.

1. **Escolha o dataset**: digite o índice numérico correspondente à base desejada (por exemplo, `0` para `dataset_obi_senior`).
2. **Execute the oracle mod [True, False]**: digite `True` (ou `1` / `sim`).
3. O sistema testará todas as questões da base e salvará a planilha consolidada em `results/<dataset>/oracle.csv`.

### 5.2 Modo 2: Avaliação Experimental de LLMs (`oracle = False`)

Para submeter os problemas de programação a um modelo de linguagem e julgar automaticamente os códigos gerados, siga a sequência de perguntas exibida no terminal:

1. **Escolha o dataset**: selecione o número correspondente à base de dados em `database/` (ex.: `0` para `dataset_obi_senior`).
2. **Execute the oracle mod [True, False]**: digite `False` (ou `0` / `nao`).
3. **Escolha a linguagem**:
   - `0` para `Python` (`python`)
   - `1` para `C++` (`cpp`)
   - `2` para `C` (`c`)
   - `3` para `Java` (`java`)
   - `4` para `JavaScript` (`javascript`)
4. **Escolha a LLM**: selecione o índice do provedor/modelo configurado no arquivo `.env`.
5. **Escolha o escopo de execução**:
   - `0`: avalia todas as questões do *dataset* (ex.: as 125 questões do Nível Sênior) em modo textual (`text`);
   - `1`: filtra apenas o subconjunto de questões que possuem figuras associadas (ex.: as 46 questões multimodais do Nível Sênior) e habilita a seleção da modalidade visual no passo seguinte.
6. **Escolha a modalidade para as questões com imagens** (exibido quando o escopo `1` é selecionado):
   - `1` (`text`): envia apenas o enunciado textual com os marcadores originais de imagem (ex.: `[1.png]`);
   - `2` (`img`): converte as imagens do diretório `imgs/` para Base64 e envia uma requisição multimodal;
   - `3` (`description`): substitui cada marcador `[nome_img]` no corpo do enunciado pela descrição textual estruturada presente no campo `imgs_description` do `problem.json`.
7. **Escolha o prompt**: selecione o número correspondente ao arquivo de *template* listado a partir do diretório `prompts/`.
8. **Informar limites de tempo e memória no prompt?**:
   - `0`: omite a seção explícita de limites no corpo do problema;
   - `1`: injeta explicitamente os valores de `time_limit` e `memory_limit` no texto formatado do problema.

---

## 6. Estrutura dos Resultados e Vereditos

Durante e após a execução, o `Orchestrator` grava dois tipos de artefatos no diretório `results/<dataset>/`:

### 6.1 Histórico Detalhado em JSON
Para cada questão avaliada, é gerado (ou atualizado de forma acumulativa) um arquivo JSON no caminho:

```text
results/<dataset>/<modelo>/<prompt>/<linguagem>/<modalidade>/<nome_da_questao>.json
```

Cada entrada da lista JSON armazena:
- `attempt` e `timestamp` (UTC ISO 8601);
- `model`, `prompt_name`, `language`, `modality`, `include_limits`, `time_limit` e `memory_limit`;
- `prompt`: conteúdo integral enviado à API;
- `tokens`: dicionário com `input_tokens`, `output_tokens` e `total_tokens`;
- `cost_usd`: dicionário com `input_cost`, `output_cost` e `total_cost`;
- `raw_response`: resposta textual bruta retornada pelo modelo;
- `extracted_code`: código-fonte extraído para compilação;
- `judge_result`: objeto contendo o veredito final (`judge_predict`), o maior tempo de execução entre os casos de teste (`execution_time`), a contagem detalhada por categoria (`counts`) e o total de casos avaliados (`total_test_cases`).

### 6.2 Planilhas Consolidadas em CSV
- `results/<dataset>/oracle.csv`: resultados da validação oráculo das soluções de referência.
- `results/<dataset>/judge/<modelo>.csv`: registro tabular linear contendo as colunas `question_name`, `execution_time`, `judge_predict`, `AC`, `WA`, `RE`, `TLE`, `MLE`, `CE` e `total_test_cases`.

### 6.3 Taxonomia de Vereditos do `JudgeService`

| Sigla | Veredito | Critério de Atribuição |
| :--- | :--- | :--- |
| **AC** | *Accepted* | Código compilou com êxito e produziu saída idêntica à esperada em todos os casos de teste, dentro dos limites de tempo e memória. |
| **WA** | *Wrong Answer* | O programa executou dentro dos limites, mas produziu saída divergente do gabarito oficial em ao menos um caso de teste. |
| **RE** | *Runtime Error* | O processo encerrou com código de retorno diferente de zero ou falha de execução (como violação de segmentação ou estouro de pilha). |
| **TLE** | *Time Limit Exceeded* | O tempo de execução ultrapassou o limite `time_limit` definido para a questão. |
| **MLE** | *Memory Limit Exceeded* | O consumo de memória monitorado via `psutil` excedeu o limite `memory_limit` especificado para a questão. |
| **CE** | *Compilation Error* | Falha na compilação/verificação sintática ou ausência de código extraível na resposta do modelo. |

---

## 7. Citação e Referências

Caso utilize esta ferramenta, a base de dados estruturada ou a metodologia experimental em pesquisas acadêmicas, cite os trabalhos abaixo:

```bibtex
@misc{compbench2026,
  author = {{\^A}ngelo, Victor Hugo Silva},
  title  = {{Competitive Programming Bench}: Framework for Benchmarking {LLMs} in Competitive Programming},
  year   = {2026},
  url    = {https://github.com/mestrevh/competitive-programming-bench}
}

@inproceedings{angelo2026ise,
  author    = {{\^A}ngelo, Victor Hugo S. and Anchieta, Lucas Heron S. and Nascimento, Matheus Ryan S. and Fernandes, Ricardo Vinicius A. and Costa, Evandro de B.},
  title     = {Avalia{\c{c}}{\~a}o de {LLMs} Multimodais na Modalidade Programa{\c{c}}{\~a}o da {Olimp{\'\i}ada Brasileira de Inform{\'a}tica}: Uma Arquitetura Experimental},
  booktitle = {Anais do V Workshop Brasileiro de Engenharia de Software Inteligente (ISE)},
  year      = {2026},
  pages     = {141--144},
  publisher = {SBC},
  address   = {Porto Alegre, RS, Brasil},
  doi       = {10.5753/ise.2026.32990},
  url       = {https://sol.sbc.org.br/index.php/ise/article/view/46385}
}
```
