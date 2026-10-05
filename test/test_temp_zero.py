import base64
import difflib
import json
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao sys.path para permitir execuções diretas do script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.config import config
from src.models.problem import Problem
from src.services.llm_services import LLM

# Caminho para o problema de teste
PROBLEM_PATH = (
    ROOT_DIR
    / "database"
    / "dataset_obi_python"
    / "A Grande Casquinha"
    / "problem.json"
)

# Configuração para incluir imagens (em Base64) se existirem no problema
INCLUDE_IMAGES = True


def encode_image_to_base64(image_path: Path) -> str:
    """Lê um arquivo de imagem e o converte para string Base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def load_problem(problem_path: Path) -> Problem:
    """Carrega o problem.json e valida usando o modelo Problem."""
    with open(problem_path, "r", encoding="utf-8") as file:
        content_json = json.load(file)
        return Problem(**content_json)


def build_problem_prompt(
    problem: Problem, problem_dir: Path, include_images: bool = True
):
    """Monta o prompt para a LLM a partir dos dados do problem.json."""
    prompt_lines = [
        "Você é um especialista em programação competitiva. Resolva o seguinte problema em Python 3:\n",
        f"# {problem.title}\n",
        f"## Enunciado\n{problem.statement}\n",
    ]
    if problem.input:
        prompt_lines.append(f"## Entrada\n{problem.input}\n")
    if problem.output:
        prompt_lines.append(f"## Saída\n{problem.output}\n")
    if problem.constraints:
        prompt_lines.append(f"## Restrições\n{problem.constraints}\n")
    if problem.examples:
        prompt_lines.append("## Exemplos de Casos de Teste:")
        for idx, ex in enumerate(problem.examples, 1):
            prompt_lines.append(
                f"\nExemplo {idx}:\nEntrada:\n```\n{ex.input}\n```\nSaída:\n```\n{ex.output}\n```"
            )
    prompt_lines.append(
        "\nEscreva o código completo da solução em Python 3. Forneça explicações breves se necessário, mas garanta que o código esteja correto, eficiente e pronto para submissão."
    )
    text_content = "\n".join(prompt_lines)

    # Se não houver imagens ou não devem ser incluídas, retorna apenas o texto
    if not include_images or not problem.imgs:
        return text_content

    # Monta payload multimodal caso haja imagens
    content: list[dict] = [{"type": "text", "text": text_content}]
    for img_name in problem.imgs:
        img_path = problem_dir / "imgs" / img_name
        if img_path.exists():
            base64_str = encode_image_to_base64(img_path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_str}"},
                }
            )
        else:
            print(f"[AVISO]: Imagem '{img_name}' referenciada mas não encontrada em '{img_path}'.")

    return content


def compare_responses(res1: str, res2: str) -> None:
    """Compara duas respostas e exibe métricas de igualdade e similaridade."""
    is_identical = res1 == res2
    similarity = difflib.SequenceMatcher(None, res1, res2).ratio() * 100.0

    print(f"\n{'=' * 60}")
    print("[COMPARAÇÃO DAS RESPOSTAS (Temperatura 0.0)]")
    print(f"{'=' * 60}")
    print(
        f"- Respostas 100% idênticas? {'SIM (Determinístico)' if is_identical else 'NÃO (Variação detectada)'}"
    )
    print(f"- Similaridade: {similarity:.2f}%")
    print(f"- Tamanho Resposta 1: {len(res1)} caracteres ({len(res1.splitlines())} linhas)")
    print(f"- Tamanho Resposta 2: {len(res2)} caracteres ({len(res2.splitlines())} linhas)")

    if is_identical:
        print("[RESULTADO]: O modelo foi estritamente determinístico nesta execução.")
    else:
        print("\n[DIFERENÇAS ENCONTRADAS (Diff unificado)]:")
        diff = list(
            difflib.unified_diff(
                res1.splitlines(keepends=True),
                res2.splitlines(keepends=True),
                fromfile="Resposta_1",
                tofile="Resposta_2",
                n=2,
            )
        )
        print("".join(diff[:60]))
        if len(diff) > 60:
            print(f"... (diff truncado, total de {len(diff)} linhas de diff)")


def main():
    if not PROBLEM_PATH.exists():
        print(f"[ERRO]: Arquivo do problema não encontrado em '{PROBLEM_PATH}'.")
        return

    print(f"[INFO]: Carregando problema: {PROBLEM_PATH}")
    problem = load_problem(PROBLEM_PATH)
    print(f"[INFO]: Problema carregado com sucesso: '{problem.title}'")

    prompt = build_problem_prompt(
        problem=problem,
        problem_dir=PROBLEM_PATH.parent,
        include_images=INCLUDE_IMAGES,
    )

    providers = config.list_providers()
    if not providers:
        print("[AVISO]: Nenhum provedor configurado no .env.")
        print(
            "Configure suas credenciais no arquivo .env (veja .env.example) para executar as chamadas à LLM."
        )
        return

    for provider_name, provider in providers.items():
        model = provider.model_name
        base_url = provider.base_url
        api_key = provider.api_key

        print(f"\n{'=' * 60}")
        print(f"[PROVEDOR]: {provider_name}")
        print(f"[CODIFICADOR]: Modelo LLM: {model}")
        print(f"[CONFIG]: Temperatura: 0.0 (Teste de determinismo)")
        print(f"{'=' * 60}")

        llm_service = LLM(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=0.0,
            seed=42
        )

        try:
            print("\n[CHAMADA 1]: Enviando a questão (temperatura=0.0)...")
            response_1 = llm_service.send_prompt(prompt=prompt)
            print(f"[CHAMADA 1]: Concluída! ({len(response_1)} caracteres recebidos)")

            print("\n[CHAMADA 2]: Enviando a mesma questão novamente (temperatura=0.0)...")
            response_2 = llm_service.send_prompt(prompt=prompt)
            print(f"[CHAMADA 2]: Concluída! ({len(response_2)} caracteres recebidos)")

            print(f"\n{'=' * 60}")
            print("[CONTEÚDO DA RESPOSTA 1]:")
            print(f"{'=' * 60}")
            print(response_1)

            print(f"\n{'=' * 60}")
            print("[CONTEÚDO DA RESPOSTA 2]:")
            print(f"{'=' * 60}")
            print(response_2)

            compare_responses(response_1, response_2)

        except Exception as e:
            print(f"[ERRO]: Falha ao executar o teste com o provedor '{provider_name}': {e}")


if __name__ == "__main__":
    main()