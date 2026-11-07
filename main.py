from pathlib import Path
from typing import Optional
from src.core.orchestrator import Orchestrator
from src.core.config import config, ProviderConfig
from src.core.prompt_builder import has_images


def choice_dir(path: Path) -> Optional[str]:
    dirs = [d for d in path.iterdir() if d.is_dir()]
    while True:
        print("\nEscolha o dataset:")
        print("-1 - Sair")
        for i, d in enumerate(dirs):
            print(f" {i} - {d.name}")
        
        try:
            choice = int(input('Escolha um número: '))
            if 0 <= choice < len(dirs):
                return dirs[choice].name
            elif choice == -1:
                return None
            else:
                print("[ERROR]: Opção não existe")
        except ValueError:
            print('[ERROR]: Apenas números são permitidos')


def choice_language() -> str:
    languages = {
        "0": "python",
        "1": "cpp",
        "2": "c",
        "3": "java",
        "4": "javascript",
    }
    print("\nEscolha a linguagem (geração da LLM e avaliação do Judge):")
    print(" 0 - Python (python)")
    print(" 1 - C++ (cpp)")
    print(" 2 - C (c)")
    print(" 3 - Java (java)")
    print(" 4 - JavaScript (javascript)")
    while True:
        try:
            choice = input('Escolha um número [0]: ').strip()
            if choice == "":
                return "python"
            if choice in languages:
                return languages[choice]
            print("[ERROR]: Opção inválida. Escolha entre 0 e 4.")
        except Exception:
            return "python"


def choice_llms() -> tuple[Optional[str], Optional[ProviderConfig]]:
    list_op = config.list_providers()
    keys = list(list_op.keys())
    
    if not keys:
        print("[ERRO]: Nenhum provedor configurado no .env.")
        return None, None

    while True:
        print("\nEscolha a LLM:")
        print("-1 - Sair")
        for i, key in enumerate(keys):
            print(f" {i} - {key} ({list_op[key].model_name})")
        
        try:
            choice = int(input('Escolha um número: '))
            if 0 <= choice < len(keys):
                selected_key = keys[choice]
                return selected_key, list_op[selected_key]
            elif choice == -1:
                return None, None
            else:
                print("[ERROR]: Opção não existe")
        except ValueError:
            print('[ERROR]: Apenas números são permitidos')


def choice_prompt(prompt_dir: Path = Path('prompts/')) -> tuple[Optional[str], Optional[str]]:
    if not prompt_dir.exists():
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
    prompt_files = sorted(list(prompt_dir.glob("*.txt")) + list(prompt_dir.glob("*.md")))
    if not prompt_files:
        print("[Aviso]: Nenhum arquivo de prompt encontrado em 'prompts/'. Usando prompt padrão.")
        default_prompt = "Você é um programador competitivo experiente. Resolva o seguinte problema:\n\n{problem}"
        return "default", default_prompt

    while True:
        print("\nEscolha o prompt:")
        print("-1 - Sair")
        for i, pf in enumerate(prompt_files):
            print(f" {i} - {pf.name}")
        
        try:
            choice = int(input('Escolha um número: '))
            if 0 <= choice < len(prompt_files):
                selected_file = prompt_files[choice]
                with open(selected_file, "r", encoding="utf-8") as f:
                    content = f.read()
                return selected_file.stem, content
            elif choice == -1:
                return None, None
            else:
                print("[ERROR]: Opção não existe")
        except ValueError:
            print('[ERROR]: Apenas números são permitidos')


def choice_execution_scope(total_all: int, total_imgs: int) -> str:
    print("\nEscolha o escopo de execução:")
    print(f" 0 - Todas as questões ({total_all} questões) [padrão]")
    print(f" 1 - Apenas as questões com imagens ({total_imgs} questões)")
    while True:
        raw = input('Escolha um número [0]: ').strip()
        if raw == "" or raw == "0":
            return "all"
        elif raw == "1":
            return "only_images"
        else:
            print("[ERROR]: Opção inválida. Digite 0 ou 1.")


def choice_image_modality() -> str:
    print("\nEscolha a modalidade para as questões com imagens:")
    print(" 1 - Prompt com apenas texto (text)")
    print(" 2 - Prompt com as imagens na Base64 (img)")
    print(" 3 - Prompt com as imagens em forma descritiva (description) [Plano a ser definido]")
    while True:
        raw = input('Escolha um número [1]: ').strip()
        if raw in ["", "1"]:
            return "text"
        elif raw == "2":
            return "img"
        elif raw == "3":
            print("[Aviso]: O plano para a modalidade descritiva será configurado nos próximos passos.")
            return "description"
        else:
            print("[ERROR]: Opção inválida. Escolha 1, 2 ou 3.")


def choice_include_limits() -> bool:
    print("\nInformar limites de tempo e memória no prompt?")
    print(" 0 - Não (padrão)")
    print(" 1 - Sim (inclui time_limit e memory_limit)")
    while True:
        raw = input('Escolha um número [0]: ').strip()
        if raw == "" or raw == "0":
            return False
        elif raw == "1":
            return True
        else:
            print("[ERROR]: Opção inválida. Digite 0 ou 1.")


def exit_system():
    print("-" * 20 + " END SYSTEM " + 20 * "-")
    exit(1)


def main():  
    print("-" * 20 + " START SYSTEM " + 20 * "-")
    
    name_env = choice_dir(Path('database/'))
    if name_env is None:
        exit_system()

    path_problems = Path('database/') / name_env
    questions = sorted([q for q in path_problems.iterdir() if q.is_dir()])

    oracle_raw = input("\nExecute the oracle mod [True, False]: ").strip().lower()
    oracle = oracle_raw in ["true", "t", "tr", "tru", "1", "yes", "y", "sim", "s"]
    
    language: str = "python"
    prompt_name = "oracle"
    prompt_template = ""
    modality = "text"
    include_limits = False
    llm = None
    
    if not oracle:
        language = choice_language()

        name_llm, llm = choice_llms()
        if llm is None:
            exit_system()
        
        questions_with_images = [q for q in questions if has_images(q)]
        scope = choice_execution_scope(total_all=len(questions), total_imgs=len(questions_with_images))

        if scope == "only_images":
            if not questions_with_images:
                print("[ERROR]: Nenhuma questão com imagens encontrada neste dataset.")
                exit_system()
            questions = questions_with_images
            modality = choice_image_modality()
            print(f"\n[Info]: Selecionadas {len(questions)} questões com imagens. Modalidade: '{modality}'.")
        else:
            modality = "text"
            print(f"\n[Info]: Selecionadas todas as {len(questions)} questões. Modalidade: '{modality}'.")
        
        prompt_name, prompt_template = choice_prompt()
        if prompt_name is None:
            exit_system()

        include_limits = choice_include_limits()

    orch = Orchestrator(
        output=name_env,
        language=language,
        llm_provider=llm
    )
    
    for question in questions:
        success = orch.execute(
            problem_path=question,
            oracle=oracle,
            prompt_name=prompt_name,
            prompt_template=prompt_template,
            modality=modality,
            include_limits=include_limits
        )
        if success:
            print(f"--- Question {question.name} processed ---")
        else:
            print(f"--- [Error]: Question {question.name} is not processed ---")

    print(f"\n--- Verifique as saídas no diretório results/{name_env} ---")
    

if __name__ == "__main__":
    main()
