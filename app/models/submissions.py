from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum, func
from sqlalchemy.types import CHAR
from sqlalchemy.orm import relationship
from app.database import Base, generate_uuid
import enum

class LanguageEnum(enum.Enum):
    c = "c"
    cpp = "cpp"
    python = "python"
    pascal = "pascal"

class StatusEnum(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    wrong_answer = "wrong_answer"
    time_limit_exceeded = "time_limit_exceeded"
    memory_limit_exceeded = "memory_limit_exceeded"
    runtime_error = "runtime_error"
    compilation_error = "compilation_error"

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    problem_id = Column(CHAR(36), ForeignKey("problems.id"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(Enum(LanguageEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    execution_time_ms = Column(Integer)
    memory_used_kb = Column(Integer)
    submitted_at = Column(DateTime, default=func.current_timestamp())
    contest_id = Column(CHAR(36), ForeignKey("contests.id"))
    
    # Relationships
    user = relationship("User")
    problem = relationship("Problem")
    contest = relationship("Contest")