from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class LanguageEnum(str, Enum):
    c = "c"
    cpp = "cpp"
    python = "python"
    pascal = "pascal"

class StatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    wrong_answer = "wrong_answer"
    time_limit_exceeded = "time_limit_exceeded"
    memory_limit_exceeded = "memory_limit_exceeded"
    runtime_error = "runtime_error"
    compilation_error = "compilation_error"

# Submission schemas
class SubmissionBase(BaseModel):
    problem_id: str
    code: str
    language: LanguageEnum
    contest_id: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionResponse(SubmissionBase):
    id: str
    user_id: str
    status: StatusEnum
    execution_time_ms: Optional[int] = None
    memory_used_kb: Optional[int] = None
    submitted_at: datetime
    
    class Config:
        orm_mode = True

class SubmissionDetailResponse(SubmissionResponse):
    problem_title: str
    username: str
    contest_title: Optional[str] = None
    
    class Config:
        orm_mode = True