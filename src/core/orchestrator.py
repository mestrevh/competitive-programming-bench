import ast
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pandas as pd

from src.services.judge_service import JudgeService
from .file_manager import file_manager
from src.models.problem import Problem
from src.models.evaluation_oracle import EvaluationOracle
from src.core.config import ProviderConfig
from src.services.llm_services import LLM, LLMResponse
from src.core.prompt_builder import build_prompt_payload, extract_code


class Orchestrator:
    
    def __init__(self,
                 output: str = "default",
                 language: str = "python",
                 llm_provider: Optional[ProviderConfig] = None,
                 temperature: float = 1.0):
        self.__dataset_name: str = output
        self.__output: Path = Path(f"results/{output}/")
        self.__language: str = language
        self.__llm_provider = llm_provider
        self.__model_name: str = llm_provider.model_name if llm_provider else "default"
        
        if llm_provider is not None:
            self.__LLM = LLM(
                api_key=llm_provider.api_key,
                base_url=llm_provider.base_url,
                model=llm_provider.model_name,
                temperature=temperature,
                input_price=llm_provider.input_price,
                output_price=llm_provider.output_price
            )
        else:
            self.__LLM = None
        
    def __load_problem(self, problem_path: Path) -> Optional[Problem]:
        try:
            problem = problem_path / 'problem.json'
            with open(problem, 'r', encoding='utf-8') as file:
                content_json = json.load(file)
                return Problem(**content_json)
        except Exception as e:
            print(f"[Error]: Falha ao carregar problem.json em {problem_path}: {e}")
            return None
    
    def __get_test_cases(self, problem_path: Path = None) -> list[tuple[str, str]]:
        if problem_path is None:
            print("[Error]: problem does not exist")
            return []
        
        test_cases_path = problem_path / "test_cases"
        if test_cases_path.exists():
            inputs_cases = []
            inputs_test_cases_path = test_cases_path / "inputs"
            for input_path in sorted(inputs_test_cases_path.glob("*.in")):
                file_in = file_manager.read_file(input_path)
                inputs_cases.append(file_in)
             
            outputs_cases = []
            outputs_test_cases_path = test_cases_path / "outputs"
            for output_path in sorted(outputs_test_cases_path.glob("*.out")):
                file_out = file_manager.read_file(output_path)
                outputs_cases.append(file_out)
            
            test_cases = []
            for inp, out in zip(inputs_cases, outputs_cases):
                test_cases.append((inp, out))
            
            return test_cases
        
        print("[Error]: test_cases directory does not exist")
        return []
    
    def __get_code(self, path: str):
        return file_manager.read_file(path)
    
    def __judge(self,
                path: Path          = None,
                code: str           = None,
                timeout: float      = 30.0,
                memory_limit: int   = 2048,
                language: Optional[str] = None,
                ) -> tuple[str, dict, int, float]:
        
        target_language = language if language is not None else self.__language
        judge = JudgeService(code=code,
                             timeout=timeout,
                             language=target_language,
                             memory_limit=memory_limit,
                             test_cases=self.__get_test_cases(problem_path=path))
        
        status_final, counts, total_cases, max_time = judge.execute()
        print(f"Question executed: {path.name}")
        return status_final, counts, total_cases, max_time

    def __get_oracle_candidates(self, code_path: Path) -> list[tuple[Path, str]]:
        """Retorna lista ordenada de (arquivo_solucao, linguagem) disponíveis em solutions/."""
        if not code_path.exists():
            return []

        ext_to_lang = {
            ".py": "python",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".java": "java",
            ".c": "c",
            ".js": "javascript",
        }
        lang_priority = {
            "cpp": 0,
            "c": 1,
            "python": 2,
            "java": 3,
            "javascript": 4,
        }
        deprioritized_tags = ("brute", "naive", "slow", "dummy", "py2")

        def is_runtime_available(lang: str) -> bool:
            if lang == "python":
                return True
            if lang == "cpp":
                return shutil.which("g++") is not None
            if lang == "c":
                return shutil.which("gcc") is not None
            if lang == "java":
                return shutil.which("javac") is not None and shutil.which("java") is not None
            if lang == "javascript":
                return shutil.which("node") is not None
            return False

        candidates: list[tuple[Path, str]] = []
        for file_path in code_path.iterdir():
            if file_path.is_file():
                lang = ext_to_lang.get(file_path.suffix.lower())
                if lang is not None:
                    candidates.append((file_path, lang))

        def is_Incompatible_py2(file_path: Path, lang: str) -> bool:
            if lang != "python":
                return False
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                ast.parse(content)
                return "raw_input" in content or "xrange" in content
            except SyntaxError:
                return True
            except Exception:
                return False

        def sort_key(item: tuple[Path, str]):
            file_path, lang = item
            stem_lower = file_path.stem.lower()
            has_deprioritized_tag = (
                any(tag in stem_lower for tag in deprioritized_tags)
                or is_Incompatible_py2(file_path, lang)
            )
            runtime_missing = not is_runtime_available(lang)
            return (
                1 if runtime_missing else 0,
                1 if has_deprioritized_tag else 0,
                lang_priority.get(lang, 99),
                file_path.name.lower(),
            )

        candidates.sort(key=sort_key)
        return candidates

    def __sanitize_name(self, name: str) -> str:
        """Sanitiza strings para uso seguro como caminhos de diretório/arquivo."""
        return name.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")

    def execute(self,
                problem_path: Path,
                oracle: bool = False,
                prompt_name: str = "zero_shot",
                prompt_template: str = "",
                modality: str = "text",
                include_limits: bool = False) -> bool:
        
        if self.__output == Path('results/default/'):
            print("[Error]: Database is not selected")
            return False
        
        problem = self.__load_problem(problem_path=problem_path)
        if problem is None:
            print("[Error]: Question is not formatted as valid problem.json")
            return False
        
        # --- MODO ORACLE ---
        if oracle:
            results_path = self.__output / "oracle.csv"
            results = file_manager.read_csv(results_path)
            
            if results is None:
                results = pd.DataFrame(columns=list(EvaluationOracle.model_fields.keys()))
                file_manager.save_csv(content=results, path=results_path)
            
            code_path = problem_path / "solutions"
            candidates = self.__get_oracle_candidates(code_path)
            
            if len(candidates) == 0:
                print(f"[Error]: Nenhuma solução encontrada em {code_path}")
                return False
            
            best_result = None
            for sol_file, sol_lang in candidates:
                code = self.__get_code(sol_file)
                if not code:
                    continue
                
                print(f"[Oracle]: Testando solução '{sol_file.name}' ({sol_lang}) para '{problem_path.name}'...")
                status_final, counts, total_cases, max_time = self.__judge(
                    path=problem_path,
                    code=code,
                    timeout=problem.time_limit,
                    memory_limit=problem.memory_limit,
                    language=sol_lang
                )
                
                if best_result is None or counts.get("AC", 0) > best_result[1].get("AC", -1):
                    best_result = (status_final, counts, total_cases, max_time)
                
                if status_final == "AC":
                    break
                print(f"[Oracle]: Solução '{sol_file.name}' obteve '{status_final}'. Tentando próxima opção se disponível...")
            
            if best_result is None:
                print(f"[Error]: Nenhuma solução pôde ser lida em {code_path}")
                return False
            
            status_final, counts, total_cases, max_time = best_result
            
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
            return file_manager.save_csv(content=results, path=results_path)

        # --- MODO LLM / GERAÇÃO DE CÓDIGO ---
        if self.__LLM is None:
            print("[Error]: Provedor LLM não configurado para execução.")
            return False

        print(f"\n>>> Processando questão '{problem_path.name}' via LLM ({self.__model_name}) | Modalidade: {modality} | Prompt: {prompt_name} <<<")
        
        # 1. Montagem do payload (texto ou multimodal com Base64)
        payload = build_prompt_payload(
            problem=problem,
            problem_path=problem_path,
            prompt_template=prompt_template,
            language=self.__language,
            modality=modality,
            include_limits=include_limits
        )

        # 2. Requisição para o modelo
        try:
            llm_res: LLMResponse = self.__LLM.generate(prompt=payload)
        except Exception as e:
            print(f"[Error]: Falha na chamada da API da LLM para '{problem_path.name}': {e}")
            return False

        # 3. Extração limpa do código da resposta
        extracted_code = extract_code(llm_res.content, language=self.__language)

        # 4. Julgamento do código gerado
        status_final, counts, total_cases, max_time = self.__judge(
            path=problem_path,
            code=extracted_code,
            timeout=problem.time_limit,
            memory_limit=problem.memory_limit
        )

        safe_model = self.__sanitize_name(self.__model_name)
        safe_prompt = self.__sanitize_name(prompt_name)

        # 5. Persistência em JSON acumulativo (Array)
        # Caminho: results/[dataset]/[model]/[prompt]/[language]/[text or img]/[name_question].json
        json_dir = self.__output / safe_model / safe_prompt / self.__language / modality
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"{problem_path.name}.json"

        history = []
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        history = loaded
                    else:
                        history = [loaded]
            except Exception as e:
                print(f"[Aviso]: Não foi possível ler histórico anterior em {json_path}: {e}")
                history = []

        attempt_entry = {
            "attempt": len(history) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.__model_name,
            "prompt_name": prompt_name,
            "language": self.__language,
            "modality": modality,
            "include_limits": include_limits,
            "time_limit": problem.time_limit,
            "memory_limit": problem.memory_limit,
            "tokens": {
                "input_tokens": llm_res.prompt_tokens,
                "output_tokens": llm_res.completion_tokens,
                "total_tokens": llm_res.total_tokens
            },
            "cost_usd": {
                "input_cost": llm_res.input_cost_usd,
                "output_cost": llm_res.output_cost_usd,
                "total_cost": llm_res.total_cost_usd
            },
            "raw_response": llm_res.content,
            "extracted_code": extracted_code,
            "judge_result": {
                "judge_predict": status_final,
                "execution_time": max_time,
                "counts": counts,
                "total_test_cases": total_cases
            }
        }

        history.append(attempt_entry)
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print(f"[Sucesso]: Questão salva no histórico JSON: {json_path}")
        except Exception as e:
            print(f"[Error]: Falha ao salvar arquivo JSON em {json_path}: {e}")

        # 6. Gravação linear no CSV do Judge
        # Caminho: results/[dataset]/judge/[model].csv
        judge_dir = self.__output / "judge"
        judge_dir.mkdir(parents=True, exist_ok=True)
        judge_csv_path = judge_dir / f"{safe_model}.csv"

        results = file_manager.read_csv(judge_csv_path)
        if results is None:
            results = pd.DataFrame(columns=list(EvaluationOracle.model_fields.keys()))

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
        return file_manager.save_csv(content=results, path=judge_csv_path)