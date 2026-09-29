from pathlib import Path
from src.core.orchestrator import Orchestrator

def choice_dir(path: Path) -> str:

    while True:
        i = 0
        list_op = list(path.glob("*"))
        print("-1 - Sair")
        for op in list_op:
            if op.is_dir():
                print(f" {i} - {op.name}")
                i += 1
        
        try:
            choice = int(input('Escolha um número: '))
            if choice >= 0 and choice <= len(list_op):
                return list_op[choice].name
            elif choice == -1:
                return None
            else:
                print("[ERROR]: Option is not exist")
        except:
            print('[ERROR]: Only number')
            return None

def choice_language() -> str:
    return "python"

def exit_system():
    exit(1)
    print("-" * 20 + " END SYSTEM " + 20 * "-")
    
def main():  
    print("-" * 20 + " START SYSTEM " + 20 * "-")
    
    name_env: Path = choice_dir(Path('database/'))
    language: str = choice_language()
    
    if name_env == None:
        exit_system()
    else:
        path_problems = Path('database/') / name_env
        questions = list(path_problems.glob("*"))

        oracle = input("Execute the oracle mod [True, False]: ")
        
        oracle = oracle.strip()
        oracle = oracle.lower()
        oracle = oracle == "true" or oracle == "t" or oracle == "tr" or oracle == "tru"
        
        for question in questions:
            orch = Orchestrator(output=name_env,
                                language=language)
            if orch.execute(problem_path=question,
                            oracle=oracle):
                print(f"--- Question {question.name} processed ---")
            else:
                print(f"--- [Error]: Question {question.name} is not processed ---")

    print(f"--- Verifique as saídas no diretório {name_env} ---")
    
if __name__ == "__main__":
    main()
