from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Enum, func
from sqlalchemy.types import CHAR, JSON
from sqlalchemy.orm import relationship
from app.database import Base, generate_uuid
import enum

class DifficultyEnum(enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyEnum), nullable=False)
    tags = Column(JSON, default='[]')
    example_input = Column(Text, nullable=False)
    example_output = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    created_by = Column(CHAR(36), ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    time_limit_ms = Column(Integer, default=1000)
    memory_limit_kb = Column(Integer, default=262144)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    problem_id = Column(CHAR(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)
    
    # Relationships
    problem = relationship("Problem", back_populates="test_cases")