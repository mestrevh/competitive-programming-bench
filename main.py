from pathlib import Path
from typing import Optional
from src.core.orchestrator import Orchestrator
from src.core.config import config, ProviderConfig


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
    print("\nEscolha a linguagem:")
    print(" 0 - Python (python)")
    print(" 1 - C++ (cpp)")
    try:
        choice = input('Escolha um número [0]: ').strip()
        if choice == "1":
            return "cpp"
        return "python"
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


def choice_modality() -> str:
    print("\nEscolha a modalidade do problema:")
    print(" 0 - Apenas texto (text)")
    print(" 1 - Texto com imagens em Base64 (img)")
    while True:
        raw = input('Escolha um número [0]: ').strip()
        if raw == "" or raw == "0":
            return "text"
        elif raw == "1":
            return "img"
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

    language: str = choice_language()
    
    path_problems = Path('database/') / name_env
    questions = [q for q in path_problems.iterdir() if q.is_dir()]

    oracle_raw = input("\nExecute the oracle mod [True, False]: ").strip().lower()
    oracle = oracle_raw in ["true", "t", "tr", "tru", "1", "yes", "y", "sim", "s"]
    
    prompt_name = "oracle"
    prompt_template = ""
    modality = "text"
    llm = None
    
    if not oracle:
        name_llm, llm = choice_llms()
        if llm is None:
            exit_system()
        
        modality = choice_modality()
        
        prompt_name, prompt_template = choice_prompt()
        if prompt_name is None:
            exit_system()

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
            modality=modality
        )
        if success:
            print(f"--- Question {question.name} processed ---")
        else:
            print(f"--- [Error]: Question {question.name} is not processed ---")

    print(f"\n--- Verifique as saídas no diretório results/{name_env} ---")
    

if __name__ == "__main__":
    main()
