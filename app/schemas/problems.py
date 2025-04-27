from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

# TestCase schemas
class TestCaseBase(BaseModel):
    input: str
    expected_output: str
    is_sample: bool = False
    order: int

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseResponse(TestCaseBase):
    id: str
    problem_id: str
    
    class Config:
        orm_mode = True

# Problem schemas
class ProblemBase(BaseModel):
    title: str
    description: str
    difficulty: DifficultyEnum
    tags: List[str] = []
    example_input: str
    example_output: str
    constraints: str
    is_public: bool = True
    time_limit_ms: int = 1000
    memory_limit_kb: int = 262144

class ProblemCreate(ProblemBase):
    test_cases: List[TestCaseCreate]

class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[DifficultyEnum] = None
    tags: Optional[List[str]] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    constraints: Optional[str] = None
    is_public: Optional[bool] = None
    time_limit_ms: Optional[int] = None
    memory_limit_kb: Optional[int] = None

class ProblemResponse(ProblemBase):
    id: str
    created_at: datetime
    created_by: str
    
    class Config:
        orm_mode = True

class ProblemDetailResponse(ProblemResponse):
    test_cases: List[TestCaseResponse] = []
    
    class Config:
        orm_mode = True