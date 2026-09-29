import tempfile
import os
import time
import subprocess
import sys
import threading
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional

class JudgeService:
    def __init__(self,
                 code: str                                  = None,
                 timeout: float                             = 30.0,
                 memory_limit: int                          = 1024,
                 language: str                              = "python",
                 test_cases: Optional[List[Tuple[str, str]]] = None):
        
        self.__language     = language.lower()
        self.__code         = code
        self.__test_cases   = test_cases if test_cases is not None else []
        self.__timeout      = timeout
        self.__memory_limit = memory_limit
        
        if self.__language == "python":
            self.__extension = "py"
            self.__python_cmd = sys.executable 
        elif self.__language == "cpp":
            self.__extension = "cpp"
        else:
            self.__extension = self.__language

    def __run_single_test(self,
                          cmd: List[str],
                          stdin: str,
                          expected: str,
                          timeout: float,
                          memory_limit: int) -> Tuple[str, float]:
        limit_bytes = memory_limit * 1024 * 1024
        exec_time = 0.0

        try:
            start_mark = time.perf_counter()
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            mle_occurred = threading.Event()
            stop_monitoring = threading.Event()
            max_memory_seen = [0]

            def monitor():
                try:
                    p = psutil.Process(process.pid)
                    while not stop_monitoring.is_set():
                        try:
                            mem_info = p.memory_info()
                            curr_mem = getattr(mem_info, "peak_wset", mem_info.rss)
                            for child in p.children(recursive=True):
                                try:
                                    child_mem = child.memory_info()
                                    curr_mem += getattr(child_mem, "peak_wset", child_mem.rss)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass

                            if curr_mem > max_memory_seen[0]:
                                max_memory_seen[0] = curr_mem

                            if curr_mem > limit_bytes:
                                mle_occurred.set()
                                try:
                                    for child in p.children(recursive=True):
                                        child.kill()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                                p.kill()
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            break
                        time.sleep(0.005)
                except Exception:
                    pass

            monitor_thread = threading.Thread(target=monitor, daemon=True)
            monitor_thread.start()

            try:
                stdout, _ = process.communicate(input=stdin, timeout=timeout)
                exec_time = time.perf_counter() - start_mark
            except subprocess.TimeoutExpired:
                stop_monitoring.set()
                try:
                    p = psutil.Process(process.pid)
                    for child in p.children(recursive=True):
                        child.kill()
                    p.kill()
                except Exception:
                    process.kill()
                process.communicate()
                return "TLE", timeout
            finally:
                stop_monitoring.set()
                monitor_thread.join(timeout=0.1)

            if mle_occurred.is_set() or max_memory_seen[0] > limit_bytes:
                return "MLE", exec_time

            if process.returncode != 0:
                return "RE", exec_time

            if stdout.strip() == expected.strip():
                return "AC", exec_time
            else:
                return "WA", exec_time

        except Exception:
            return "RE", exec_time

    def __print_summary(self,
                        status_final: str,
                        counts: dict,
                        total_cases: int,
                        max_time: float) -> None:
        print("\n" + "="*30)
        print(f"RESUMO DOS TESTES ({total_cases} casos)")
        print("-" * 30)
        print(f"  Accepted (AC):      {counts.get('AC', 0)}")
        print(f"  Wrong Answer (WA):  {counts.get('WA', 0)}")
        print(f"  Runtime Error (RE): {counts.get('RE', 0)}")
        print(f"  Time Limit (TLE):   {counts.get('TLE', 0)}")
        print(f"  Memory Limit (MLE): {counts.get('MLE', 0)}")
        print(f"  Comp. Error (CE):   {counts.get('CE', 0)}")
        print("-" * 30)
        print(f"MAIOR TEMPO: {max_time:.3f}s")
        print(f"STATUS:      {status_final}")
        print("="*30)

    def execute(self) -> Tuple[str, dict, int, float]:
        """
        Retorna: (status judge, dict com contagem de casos, total casos, maior tempo)
        """
        total_cases = len(self.__test_cases)
        counts = {
                    "AC": 0,
                    "WA": 0,
                    "RE": 0,
                    "TLE": 0,
                    "MLE": 0,
                    "CE": total_cases }
        
        if total_cases == 0:
            return "NO TEST CASES", counts, 0, 0.0
        
        if not self.__code:
            return "CE", counts, total_cases, 0.0

        print(f"\n--- Iniciando Judge: {self.__language.upper()} ---")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_file = tmp_path / f"code.{self.__extension}"
            source_file.write_text(self.__code, encoding="utf-8")

            if self.__language == "cpp":
                executable = tmp_path / ("program.exe" if sys.platform == "win32" else "program.out")
                try:
                    compile_res = subprocess.run(
                        ["g++", str(source_file), "-o", str(executable), "-O2"],
                        capture_output=True, text=True, timeout=15.0
                    )
                    if compile_res.returncode != 0:
                        self.__print_summary("CE", counts, total_cases, 0.0)
                        return "CE", counts, total_cases, 0.0
                except FileNotFoundError:
                    print("[Error]: Compilador 'g++' não encontrado no sistema.")
                    counts = {
                        "AC": 0,
                        "WA": 0,
                        "RE": 0,
                        "TLE": 0,
                        "MLE": 0,
                        "CE": total_cases
                    }
                    self.__print_summary("CE", counts, total_cases, 0.0)
                    return "CE", counts, total_cases, 0.0
                cmd = [str(executable)]
            else:
                cmd = [self.__python_cmd, str(source_file)]

            def worker(case):
                inp, exp = case
                return self.__run_single_test(cmd, inp, exp, self.__timeout, self.__memory_limit)

            #max_workers = min(32, (os.cpu_count() or 1) * 4)
            with ThreadPoolExecutor(max_workers=1) as executor:
                results_with_time = list(executor.map(worker, self.__test_cases))

        statuses = [r[0] for r in results_with_time]
        times = [r[1] for r in results_with_time]
        
        max_time = max(times) if times else 0.0

        counts = {
            "AC": statuses.count("AC"),
            "WA": statuses.count("WA"),
            "RE": statuses.count("RE"),
            "TLE": statuses.count("TLE"),
            "MLE": statuses.count("MLE"),
            "CE": statuses.count("CE")
        }

        if counts["CE"] > 0:
            status_final = "CE"
        elif counts["AC"] == total_cases:
            status_final = "AC"
        else:
            status_final = next(s for s in statuses if s != "AC")

        self.__print_summary(status_final, counts, total_cases, max_time)

        return status_final, counts, total_cases, max_time
