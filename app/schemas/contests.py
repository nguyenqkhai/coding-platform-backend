from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ContestProblem schemas
class ContestProblemBase(BaseModel):
    problem_id: str
    order: int
    points: int = 100

class ContestProblemCreate(ContestProblemBase):
    pass

class ContestProblemResponse(ContestProblemBase):
    id: str
    contest_id: str
    
    class Config:
        orm_mode = True

class ContestProblemDetailResponse(ContestProblemResponse):
    problem_title: str
    problem_difficulty: str
    
    class Config:
        orm_mode = True

# ContestParticipant schemas
class ContestParticipantBase(BaseModel):
    user_id: str

class ContestParticipantCreate(ContestParticipantBase):
    pass

class ContestParticipantResponse(ContestParticipantBase):
    id: str
    contest_id: str
    joined_at: datetime
    score: int
    
    class Config:
        orm_mode = True

class ContestParticipantDetailResponse(ContestParticipantResponse):
    username: str
    full_name: Optional[str] = None
    
    class Config:
        orm_mode = True

# Contest schemas
class ContestBase(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    is_public: bool = True

class ContestCreate(ContestBase):
    problems: List[ContestProblemCreate]

class ContestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_public: Optional[bool] = None

class ContestResponse(ContestBase):
    id: str
    created_by: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class ContestDetailResponse(ContestResponse):
    problems: List[ContestProblemDetailResponse] = []
    participants: List[ContestParticipantDetailResponse] = []
    
    class Config:
        orm_mode = True