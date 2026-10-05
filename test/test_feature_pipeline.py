import json
import tempfile
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.problem import Problem
from src.core.prompt_builder import (
    format_problem_str,
    build_prompt_payload,
    extract_code,
    encode_image_to_base64
)
from src.services.llm_services import LLMResponse
from src.core.orchestrator import Orchestrator
from src.core.config import ProviderConfig


def test_code_extraction():
    print("Testing code extraction...")
    raw_markdown = """
Here is the solution to your problem:
```python
def solve():
    n = int(input())
    print(n * 2)

if __name__ == '__main__':
    solve()
```
Explanation of the solution...
"""
    extracted = extract_code(raw_markdown, language="python")
    assert "def solve():" in extracted
    assert "```" not in extracted
    assert "Explanation of the solution" not in extracted
    print("[PASS] Markdown extraction with language tag passed.")

    raw_no_tag = """
```
print("hello world")
```
"""
    extracted2 = extract_code(raw_no_tag, language="python")
    assert extracted2 == 'print("hello world")'
    print("[PASS] Markdown extraction without language tag passed.")

    plain_code = 'x = 10\nprint(x)'
    extracted3 = extract_code(plain_code, language="python")
    assert extracted3 == plain_code
    print("[PASS] Plain code extraction passed.")


def test_prompt_builder():
    print("\nTesting prompt builder...")
    problem_path = ROOT_DIR / "database" / "dataset_obi_python" / "A Grande Casquinha"
    with open(problem_path / "problem.json", "r", encoding="utf-8") as f:
        problem = Problem(**json.load(f))

    template_with_placeholder = "INSTRUCAO\n{problem}\nFIM"
    payload_text = build_prompt_payload(
        problem=problem,
        problem_path=problem_path,
        prompt_template=template_with_placeholder,
        language="python",
        modality="text"
    )
    assert isinstance(payload_text, str)
    assert "A Grande Casquinha" in payload_text
    assert "INSTRUCAO" in payload_text
    print("[PASS] Text payload with placeholder passed.")

    payload_img = build_prompt_payload(
        problem=problem,
        problem_path=problem_path,
        prompt_template=template_with_placeholder,
        language="python",
        modality="img"
    )
    assert isinstance(payload_img, list)
    assert payload_img[0]["type"] == "text"
    assert payload_img[1]["type"] == "image_url"
    assert "data:image/png;base64," in payload_img[1]["image_url"]["url"]
    print("[PASS] Multimodal payload with Base64 passed.")

    payload_with_limits = build_prompt_payload(
        problem=problem,
        problem_path=problem_path,
        prompt_template=template_with_placeholder,
        language="python",
        modality="text",
        include_limits=True
    )
    assert "Limites de Execução" in payload_with_limits
    assert f"Tempo Limite: {problem.time_limit}" in payload_with_limits
    assert f"Limite de Memória: {problem.memory_limit}" in payload_with_limits
    print("[PASS] Payload with execution limits passed.")


def test_llm_response_and_cost():
    print("\nTesting LLMResponse and cost calculations...")
    input_tokens = 1_000_000
    output_tokens = 500_000
    input_price = 0.15   # $0.15 por 1M tokens
    output_price = 0.60  # $0.60 por 1M tokens

    input_cost = (input_tokens / 1_000_000.0) * input_price
    output_cost = (output_tokens / 1_000_000.0) * output_price
    total_cost = input_cost + output_cost

    resp = LLMResponse(
        content="print('test')",
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        input_cost_usd=round(input_cost, 6),
        output_cost_usd=round(output_cost, 6),
        total_cost_usd=round(total_cost, 6)
    )

    assert resp.input_cost_usd == 0.15
    assert resp.output_cost_usd == 0.30
    assert resp.total_cost_usd == 0.45
    print("[PASS] Cost calculation verified.")


def test_orchestrator_json_accumulation_and_judge_csv():
    print("\nTesting Orchestrator JSON accumulation and Judge CSV...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Mock problem path
        problem_dir = tmp_path / "mock_problem"
        problem_dir.mkdir(parents=True, exist_ok=True)
        test_cases_dir = problem_dir / "test_cases"
        (test_cases_dir / "inputs").mkdir(parents=True, exist_ok=True)
        (test_cases_dir / "outputs").mkdir(parents=True, exist_ok=True)

        with open(test_cases_dir / "inputs" / "01.in", "w") as f:
            f.write("2\n")
        with open(test_cases_dir / "outputs" / "01.out", "w") as f:
            f.write("4\n")

        mock_problem_data = {
            "title": "Mock Problem",
            "statement": "Multiply by 2",
            "input": "n",
            "output": "2*n",
            "constraints": "n > 0",
            "examples": [{"input": "2", "output": "4"}],
            "year": "2024",
            "time_limit": 2.0,
            "memory_limit": 1024
        }
        with open(problem_dir / "problem.json", "w", encoding="utf-8") as f:
            json.dump(mock_problem_data, f)

        # Mock LLM provider
        mock_provider = ProviderConfig(
            api_key="fake-key",
            model_name="mock-model",
            base_url="https://mock.url",
            input_price=1.0,
            output_price=2.0
        )

        orch = Orchestrator(
            output="test_dataset",
            language="python",
            llm_provider=mock_provider
        )

        # Monkey-patch __LLM.generate to simulate 2 calls without making real network requests
        class MockLLM:
            def __init__(self):
                self.calls = 0
            def generate(self, prompt, **kwargs):
                self.calls += 1
                return LLMResponse(
                    content=f"```python\nn = int(input())\nprint(n * 2)\n```",
                    prompt_tokens=100 * self.calls,
                    completion_tokens=50 * self.calls,
                    total_tokens=150 * self.calls,
                    input_cost_usd=0.0001 * self.calls,
                    output_cost_usd=0.0001 * self.calls,
                    total_cost_usd=0.0002 * self.calls
                )

        orch._Orchestrator__LLM = MockLLM()
        orch._Orchestrator__output = tmp_path / "results" / "test_dataset"

        # Call 1 (com include_limits=True)
        res1 = orch.execute(
            problem_path=problem_dir,
            oracle=False,
            prompt_name="zero_shot",
            prompt_template="Solve {problem}",
            modality="text",
            include_limits=True
        )
        assert res1 == True

        # Call 2 (com include_limits=False)
        res2 = orch.execute(
            problem_path=problem_dir,
            oracle=False,
            prompt_name="zero_shot",
            prompt_template="Solve {problem}",
            modality="text",
            include_limits=False
        )
        assert res2 == True

        # Verify JSON
        json_file = tmp_path / "results" / "test_dataset" / "mock-model" / "zero_shot" / "python" / "text" / "mock_problem.json"
        assert json_file.exists(), f"JSON file {json_file} does not exist!"
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        assert isinstance(records, list)
        assert len(records) == 2, f"Expected 2 accumulated records, got {len(records)}"
        assert records[0]["attempt"] == 1
        assert records[0]["include_limits"] == True
        assert records[0]["time_limit"] == 2.0
        assert records[0]["memory_limit"] == 1024

        assert records[1]["attempt"] == 2
        assert records[1]["include_limits"] == False
        assert records[0]["judge_result"]["judge_predict"] == "AC"
        assert records[1]["judge_result"]["judge_predict"] == "AC"
        print(f"[PASS] JSON accumulated array properly verified with {len(records)} attempts and limit tracking.")

        # Verify Judge CSV
        csv_file = tmp_path / "results" / "test_dataset" / "judge" / "mock-model.csv"
        assert csv_file.exists(), f"CSV file {csv_file} does not exist!"
        import pandas as pd
        df = pd.read_csv(csv_file)
        expected_cols = ["question_name", "execution_time", "judge_predict", "AC", "WA", "RE", "TLE", "MLE", "CE", "total_test_cases"]
        assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)} vs {expected_cols}"
        assert len(df) == 2, f"Expected 2 rows in CSV, got {len(df)}"
        print(f"[PASS] Judge CSV verified with columns: {list(df.columns)}")


if __name__ == "__main__":
    test_code_extraction()
    test_prompt_builder()
    test_llm_response_and_cost()
    test_orchestrator_json_accumulation_and_judge_csv()
    print("\nALL FEATURE TESTS PASSED SUCCESSFULLY!")
