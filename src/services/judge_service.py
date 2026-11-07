import tempfile
import os
import re
import time
import subprocess
import sys
import threading
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional

_OBI_JS_SHIM = """
const __obi_fs = require('fs');
const __obi_input = __obi_fs.readFileSync(0, 'utf8');
let __obi_pos = 0;
function scanf(__obi_fmt) {
    const __obi_specs = __obi_fmt.match(/%[dfsc]/g) || [];
    for (let __obi_i = 0; __obi_i < __obi_specs.length; __obi_i++) {
        const __obi_spec = __obi_specs[__obi_i];
        const __obi_target = arguments[__obi_i + 1];
        if (__obi_spec === '%c') {
            if (__obi_pos < __obi_input.length) {
                const __obi_ch = __obi_input[__obi_pos++];
                eval(__obi_target + ' = ' + JSON.stringify(__obi_ch));
            }
            if (__obi_fmt.includes('%c\\n') && __obi_pos < __obi_input.length && (__obi_input[__obi_pos] === '\\r' || __obi_input[__obi_pos] === '\\n')) {
                if (__obi_input[__obi_pos] === '\\r') __obi_pos++;
                if (__obi_input[__obi_pos] === '\\n') __obi_pos++;
            }
        } else {
            while (__obi_pos < __obi_input.length && __obi_input.charCodeAt(__obi_pos) <= 32) __obi_pos++;
            let __obi_start = __obi_pos;
            while (__obi_pos < __obi_input.length && __obi_input.charCodeAt(__obi_pos) > 32) __obi_pos++;
            const __obi_tok = __obi_input.slice(__obi_start, __obi_pos);
            if (__obi_spec === '%d') eval(__obi_target + ' = ' + (__obi_tok ? parseInt(__obi_tok, 10) : 0));
            else if (__obi_spec === '%f') eval(__obi_target + ' = ' + (__obi_tok ? parseFloat(__obi_tok) : 0.0));
            else eval(__obi_target + ' = ' + JSON.stringify(__obi_tok));
        }
    }
}
function printf(__obi_fmt) {
    let __obi_idx = 1;
    const __obi_out = String(__obi_fmt).replace(/%(?:\\.(\\d+))?([dfsc])/g, (_, __obi_prec, __obi_type) => {
        const __obi_val = arguments[__obi_idx++];
        if (__obi_type === 'd') return Math.trunc(Number(__obi_val)).toString();
        if (__obi_type === 'f') return __obi_prec !== undefined ? Number(__obi_val).toFixed(Number(__obi_prec)) : Number(__obi_val).toString();
        return String(__obi_val);
    });
    process.stdout.write(__obi_out);
}
"""

class JudgeService:
    def __init__(self,
                 code: str                                  = None,
                 timeout: float                             = 30.0,
                 memory_limit: int                          = 1024,
                 language: str                              = "python",
                 test_cases: Optional[List[Tuple[str, str]]] = None):
        
        lang_norm = language.lower().strip().lstrip(".")
        lang_aliases = {
            "py": "python",
            "python": "python",
            "cpp": "cpp",
            "c++": "cpp",
            "cc": "cpp",
            "c": "c",
            "java": "java",
            "js": "javascript",
            "javascript": "javascript",
        }
        self.__language     = lang_aliases.get(lang_norm, lang_norm)
        self.__code         = code
        self.__test_cases   = test_cases if test_cases is not None else []
        self.__timeout      = timeout
        self.__memory_limit = memory_limit
        self.__python_cmd   = sys.executable
        
        ext_map = {
            "python": "py",
            "cpp": "cpp",
            "c": "c",
            "java": "java",
            "javascript": "js",
        }
        self.__extension = ext_map.get(self.__language, self.__language)

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
                monitor_thread.join(timeout=0.2)
                if process.stdin:
                    process.stdin.close()
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

            if mle_occurred.is_set() or max_memory_seen[0] > limit_bytes:
                return "MLE", exec_time

            if process.returncode != 0:
                return "RE", exec_time

            out_lines = [line.rstrip() for line in stdout.strip().splitlines()]
            exp_lines = [line.rstrip() for line in expected.strip().splitlines()]
            if out_lines == exp_lines:
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

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_file = tmp_path / f"code.{self.__extension}"

            stack_bytes = self.__memory_limit * 1024 * 1024

            if self.__language == "cpp":
                source_file.write_text(self.__code, encoding="utf-8")
                executable = tmp_path / ("program.exe" if sys.platform == "win32" else "program.out")
                cpp_cmd = [
                    "g++",
                    "-include", "cassert",
                    "-include", "cstdint",
                    "-include", "cstring",
                    "-include", "algorithm",
                    "-DNDEBUG",
                    str(source_file),
                    "-o", str(executable),
                    "-O2",
                ]
                if sys.platform == "win32":
                    cpp_cmd.append(f"-Wl,--stack,{stack_bytes}")
                try:
                    compile_res = subprocess.run(
                        cpp_cmd,
                        capture_output=True, text=True, timeout=15.0
                    )
                    if compile_res.returncode != 0:
                        self.__print_summary("CE", counts, total_cases, 0.0)
                        return "CE", counts, total_cases, 0.0
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print("[Error]: Compilador 'g++' não encontrado ou tempo esgotado.")
                    self.__print_summary("CE", counts, total_cases, 0.0)
                    return "CE", counts, total_cases, 0.0
                cmd = [str(executable)]

            elif self.__language == "c":
                source_file.write_text(self.__code, encoding="utf-8")
                executable = tmp_path / ("program.exe" if sys.platform == "win32" else "program.out")
                c_cmd = [
                    "gcc",
                    "-DNDEBUG",
                    str(source_file),
                    "-o", str(executable),
                    "-O2",
                    "-lm",
                ]
                if sys.platform == "win32":
                    c_cmd.append(f"-Wl,--stack,{stack_bytes}")
                try:
                    compile_res = subprocess.run(
                        c_cmd,
                        capture_output=True, text=True, timeout=15.0
                    )
                    if compile_res.returncode != 0:
                        self.__print_summary("CE", counts, total_cases, 0.0)
                        return "CE", counts, total_cases, 0.0
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print("[Error]: Compilador 'gcc' não encontrado ou tempo esgotado.")
                    self.__print_summary("CE", counts, total_cases, 0.0)
                    return "CE", counts, total_cases, 0.0
                cmd = [str(executable)]

            elif self.__language == "java":
                match = (
                    re.search(r"public\s+class\s+([A-Za-z_]\w*)", self.__code)
                    or re.search(r"class\s+([A-Za-z_]\w*)", self.__code)
                )
                class_name = match.group(1) if match else "Main"
                source_file = tmp_path / f"{class_name}.java"
                source_file.write_text(self.__code, encoding="utf-8")
                try:
                    compile_res = subprocess.run(
                        ["javac", "-encoding", "UTF-8", str(source_file)],
                        capture_output=True, text=True, timeout=20.0
                    )
                    if compile_res.returncode != 0:
                        self.__print_summary("CE", counts, total_cases, 0.0)
                        return "CE", counts, total_cases, 0.0
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print("[Error]: Compilador 'javac' não encontrado ou tempo esgotado.")
                    self.__print_summary("CE", counts, total_cases, 0.0)
                    return "CE", counts, total_cases, 0.0
                cmd = ["java", "-cp", str(tmp_path), class_name]

            elif self.__language == "javascript":
                js_code = self.__code
                if (
                    re.search(r"\b(scanf|printf)\s*\(", js_code)
                    and not re.search(r"function\s+(scanf|printf)\b", js_code)
                ):
                    js_code = _OBI_JS_SHIM + "\n" + js_code
                source_file.write_text(js_code, encoding="utf-8")
                try:
                    check_res = subprocess.run(
                        ["node", "--check", str(source_file)],
                        capture_output=True, text=True, timeout=10.0
                    )
                    if check_res.returncode != 0:
                        self.__print_summary("CE", counts, total_cases, 0.0)
                        return "CE", counts, total_cases, 0.0
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print("[Error]: Runtime 'node' não encontrado ou tempo esgotado.")
                    self.__print_summary("CE", counts, total_cases, 0.0)
                    return "CE", counts, total_cases, 0.0
                cmd = ["node", str(source_file)]

            else:
                source_file.write_text(self.__code, encoding="utf-8")
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
