import json
import pandas as pd
from pathlib import Path
from src.services.judge_service import JudgeService
from .file_manager import file_manager
from src.models.problem import Problem
from src.models.evaluation_oracle import EvaluationOracle

class Orchestrator:
    
    def __init__(self, output: str = "default", language: str = "python"):
        self.__output: Path   = Path(f"results/{output}/")
        self.__language: str = language
    
    def __load_problem(self, problem_path: Path) -> Problem:
        try:
            problem = problem_path / 'problem.json'
            with open(problem, 'r', encoding='utf-8') as file:
                content_json = json.load(file)
                return Problem(**content_json)
        except:
            return None
    
    def __get_test_cases(self, problem_path: Path = None) -> list[tuple[str, str]]:
        
        if problem_path is None:
            print("[Error]: problem is not exists")
            return []
        
        test_cases_path = problem_path / "test_cases"
        
        if test_cases_path.exists():
            inputs_cases = []
            
            inputs_test_cases_path = test_cases_path / "inputs"
            for input_path in inputs_test_cases_path.glob("*.in"):
                file_in = file_manager.read_file(input_path)
                inputs_cases.append(file_in)
             
            outputs_cases = []
            outputs_test_cases_path = test_cases_path / "outputs"
            for output_path in outputs_test_cases_path.glob("*.out"):
                file_out = file_manager.read_file(output_path)
                outputs_cases.append(file_out)
            
            test_cases = []
            for inp, out in zip(inputs_cases, outputs_cases):
                test_cases.append((inp, out))
            
            return test_cases
        
        print("[Error]: problem is not exists")
        return []
    
    def __get_code(self, path: str):
        return file_manager.read_file(path)
    
    def __judge(self,
                path: Path          = None,
                code: str           = None,
                timeout: float      = 30.0,
                memory_limit: int   = 2048,
                ) -> tuple[str, dict, int, float]:
        
        judge = JudgeService(code=code,
                             timeout=timeout,
                             language=self.__language,
                             memory_limit=memory_limit,
                             test_cases=self.__get_test_cases(problem_path=path))
        
        status_final, counts, total_cases, max_time = judge.execute()
        print(f"Question executed: {path.name}")
        return status_final, counts, total_cases, max_time
        
        
    
    def execute(self, problem_path: Path, oracle: bool = False) -> bool:
        
        if self.__output == Path('results/default/'):
            print("[Error]: Database is not selected")
            return False
        
        problem = self.__load_problem(problem_path=problem_path)
        
        if problem is None:
            print("[Error]: Question is not format .json")
            return False
        
        if oracle:
            results_path = self.__output / "oracle.csv"
            results = file_manager.read_csv(results_path)
            
            if results is None:
                results = pd.DataFrame(columns=list(EvaluationOracle.model_fields.keys()))
                file_manager.save_csv(content=results,
                                      path=results_path)
            
            ext = "*.py"
            
            if self.__language == "cpp":
                ext = "*.cpp"
            
            
            code_path = problem_path / "solutions"
            list_code = list(code_path.glob(ext))
            
            print(code_path)
            
            if len(list_code) == 0 and ext == "*.cpp":
                list_code = code_path.glob("*.cc")                
            
            if len(list_code) == 0:
                return False
            
            code = self.__get_code(list_code[0])
            
            status_final, counts, total_cases, max_time = self.__judge(
                path=problem_path,
                code=code,
                timeout=problem.time_limit,
                memory_limit=problem.memory_limit
                )
            
            evaluation = EvaluationOracle(
                                        question_name=problem_path.name,
                                        execution_time=max_time,
                                        judge_predict=status_final,
                                        AC=counts['AC'],
                                        WA=counts['WA'],
                                        RE=counts['RE'],
                                        TLE=counts['TLE'],
                                        MLE=counts['MLE'],
                                        CE=counts['CE'],
                                        total_test_cases=total_cases
                                    )
            
            results.loc[len(results)] = evaluation.model_dump()
            
            return file_manager.save_csv(content=results,
                                         path=results_path)
        else:
            print("--- Implementação ---")
            return False