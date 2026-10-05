import base64
import re
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from src.models.problem import Problem


def encode_image_to_base64(image_path: Path) -> str:
    """Lê um arquivo de imagem e o converte para string Base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_mime_type(image_path: Path) -> str:
    """Retorna o tipo MIME apropriado para a imagem."""
    suffix = image_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif suffix == ".png":
        return "image/png"
    elif suffix == ".webp":
        return "image/webp"
    return "image/png"


def format_problem_str(problem: Problem, include_limits: bool = False) -> str:
    """Monta a representação em texto do problema."""
    parts = [f"# {problem.title}\n", f"## Enunciado\n{problem.statement}\n"]
    
    if problem.input:
        parts.append(f"## Formato de Entrada\n{problem.input}\n")
    if problem.output:
        parts.append(f"## Formato de Saída\n{problem.output}\n")
    if problem.constraints:
        parts.append(f"## Restrições\n{problem.constraints}\n")
        
    if include_limits:
        parts.append(
            f"## Limites de Execução\n"
            f"- Tempo Limite: {problem.time_limit} segundo(s)\n"
            f"- Limite de Memória: {problem.memory_limit} MB\n"
        )
        
    if problem.examples:
        parts.append("## Exemplos de Teste:")
        for idx, ex in enumerate(problem.examples, 1):
            parts.append(
                f"\nExemplo {idx}:\nEntrada:\n```\n{ex.input}\n```\nSaída:\n```\n{ex.output}\n```"
            )
            
    return "\n".join(parts)


def build_prompt_payload(
    problem: Problem,
    problem_path: Path,
    prompt_template: str,
    language: str = "python",
    modality: str = "text",
    include_limits: bool = False
) -> Union[str, List[Dict[str, Any]]]:
    """
    Constrói a mensagem final para a LLM respeitando o template do prompt,
    a linguagem, a modalidade (apenas texto ou multimodal com Base64)
    e a opção de informar os limites de tempo e memória.
    """
    problem_str = format_problem_str(problem, include_limits=include_limits)
    
    # Se o template tiver a tag {problem}, faz a substituição.
    # Caso contrário, aplica a estratégia recomendada:
    # [Instruções do Prompt] -> [Problema] -> [Instruções Finais de Saída]
    if "{problem}" in prompt_template:
        text_content = prompt_template.replace("{problem}", problem_str).replace("{language}", language)
    else:
        text_content = (
            f"{prompt_template.strip()}\n\n"
            f"--- DESCRIÇÃO DO PROBLEMA ---\n"
            f"{problem_str}\n\n"
            f"--- INSTRUÇÕES FINAIS ---\n"
            f"Resolva o problema acima na linguagem {language}.\n"
            f"Retorne o código completo dentro de um bloco de código markdown (```{language} ... ```).\n"
            f"Não forneça explicações adicionais fora do bloco de código."
        )

    # Substitui placeholders explícitos de limites se existirem no template
    text_content = text_content.replace("{time_limit}", f"{problem.time_limit}s")
    text_content = text_content.replace("{memory_limit}", f"{problem.memory_limit}MB")

    # Se a modalidade for apenas texto, retorna a string
    if modality != "img" or not problem.imgs:
        return text_content

    # Se a modalidade for img, monta o payload multimodal
    content: List[Dict[str, Any]] = [{"type": "text", "text": text_content}]
    imgs_dir = problem_path / "imgs"

    for img_name in problem.imgs:
        img_path = imgs_dir / img_name
        if img_path.exists():
            mime_type = get_image_mime_type(img_path)
            b64_str = encode_image_to_base64(img_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_str}"
                }
            })
        else:
            print(f"[Aviso]: Imagem '{img_name}' não encontrada no diretório '{imgs_dir}'.")

    return content


def extract_code(response_text: str, language: str = "python") -> str:
    """
    Extrai o código executável da resposta da LLM, removendo blocos markdown.
    """
    if not response_text:
        return ""

    # Tenta encontrar blocos com a linguagem específica: ```python ... ``` ou ```cpp ... ```
    pattern_lang = rf"```(?:{language}|py|cpp|c\+\+)?\s*\n(.*?)```"
    matches = re.findall(pattern_lang, response_text, re.DOTALL | re.IGNORECASE)
    
    if matches:
        # Se encontrou blocos, pega o maior (normalmente a solução completa)
        longest_match = max(matches, key=len)
        return longest_match.strip()

    # Tenta qualquer bloco ``` ... ```
    pattern_generic = r"```\s*\n(.*?)```"
    matches_generic = re.findall(pattern_generic, response_text, re.DOTALL)
    if matches_generic:
        longest_match = max(matches_generic, key=len)
        return longest_match.strip()

    # Caso não haja marcadores de markdown, retorna o texto limpo
    return response_text.strip()
