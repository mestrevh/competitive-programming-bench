from pydantic import BaseModel

class Example(BaseModel):
    input: str
    output: str