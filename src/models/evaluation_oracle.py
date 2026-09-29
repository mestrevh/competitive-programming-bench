from pydantic import BaseModel

class EvaluationOracle(BaseModel):
    question_name: str
    execution_time: float
    judge_predict: str
    AC: int
    WA: int
    RE: int
    TLE: int
    MLE: int
    CE: int
    total_test_cases: int