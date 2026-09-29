from typing import List, Optional
from pydantic import BaseModel
from .example import Example

class Problem(BaseModel):
    title: str
    statement: str
    input: Optional[str] = None
    output: str
    constraints: Optional[str] = None
    examples: List[Example]
    imgs: Optional[list] = None
    rating: Optional[list[int]] = None
    year: str
    level: Optional[str]
    period: Optional[str]
    topics: Optional[list]
    time_limit: float
    memory_limit: int