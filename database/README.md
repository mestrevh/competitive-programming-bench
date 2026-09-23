## DATABASE

Diretório responsável por colocar todas as base de dados que possuem questões de programação competitiva.
Para o sistema conseguir fazer o benchmarking é preciso seguir algumas regras como Arquitura e formatação do problema.

### Arquitetura do diretório

```
database/
|
├── [nome1]/                    # nome1 irá aparecer na hora de escolher a base de dados
|   |
|   ├── [questao_1]/            # questao_1 estana nos resultados
│   │   ├── imgs/
|   |   |   └── [n.png]         # n fotos que a questão possui
│   │   ├── solutions/          # manter o nome da questão nas soluções (boa prática) 
│   │   |   ├── questao_1.py
│   │   |   └── questao_1.cpp   
│   │   ├── test_cases/         # manter o nome da questão nas soluções (boa prática) 
│   │   |   ├── inputs/
|   |   |   |   └── [n.in]      # n entradas para teste, precisa estar com extensão .in
│   │   |   ├── outputs/
|   |   |   |   └── [n.out]     # n saídas que deve acompanhar a entrada, precisa estar com extensão .out
│   |   └── problem.json        # json com as informações do problema
|   |
│   └── [questao_n]/
```

### Formato do [nome1]/problem.json

Para o Benchmarking ter sucesso é preciso que o `problem.json` siga a estrutura


```json
{
    "title": "string",
    "statement": "string",
    "input": "string",
    "output": "string",
    "constraints": "",
    "examples": [
        {
            "input": "string",
            "output": "string"
        },
        {
            "input": "string",
            "output": "string"
        }
    ],
    "imgs": [
        "string",
        "string"
    ],
    "rating": [
        int,
        int,
        int
    ],
    "year": "string: int",
    "level": "string",
    "period": "string",
    "topics": [
        "string",
        "string"
    ],
    "time_limit": float,
    "memory_limit": int
}
```