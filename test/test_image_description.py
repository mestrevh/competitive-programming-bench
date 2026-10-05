import base64
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao sys.path para permitir execuções diretas do script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.config import config
from src.services.llm_services import LLM

# Caminho para a imagem de teste
IMAGE_PATH = (
    ROOT_DIR
    / "database"
    / "dataset_obi_python"
    / "A Grande Casquinha"
    / "imgs"
    / "1.png"
)

def encode_image_to_base64(image_path: Path) -> str:
    """Lê um arquivo de imagem e o converte para string Base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def main():
    if not IMAGE_PATH.exists():
        print(f"[ERRO]: Imagem não encontrada em '{IMAGE_PATH}'.")
        return

    print(f"[INFO]: Imagem encontrada: {IMAGE_PATH}")
    print("[INFO]: Codificando imagem em Base64...")
    base64_image = encode_image_to_base64(IMAGE_PATH)

    # Prompt simples com texto e a imagem em Base64 (formato compatível com OpenAI/Vision)
    prompt = [
        {
            "type": "text",
            "text": "O que você sabe sobre esta imagem? Descreva detalhadamente o que você vê e o que ela representa.",
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            },
        },
    ]

    providers = config.list_providers()
    if not providers:
        print("[AVISO]: Nenhum provedor configurado no .env.")
        print("Configure suas credenciais no arquivo .env (veja .env.example) para executar a chamada à LLM.")
        return

    for provider_name, provider in providers.items():
        model = provider.model_name
        base_url = provider.base_url
        api_key = provider.api_key

        print(f"\n{'=' * 60}")
        print(f"[PROVEDOR]: {provider_name}")
        print(f"[CODIFICADOR]: Modelo LLM: {model}")
        print(f"{'=' * 60}")

        llm_service = LLM(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=0.0,
        )

        try:
            print("[INFO]: Enviando requisição com imagem para o modelo...")
            response = llm_service.send_prompt(prompt=prompt)
            print("\n[RESPOSTA DA LLM]:")
            print(response)
        except Exception as e:
            print(f"[ERRO]: Falha ao executar o teste com o provedor '{provider_name}': {e}")

if __name__ == "__main__":
    main()