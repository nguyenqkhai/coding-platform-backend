from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.types import CHAR
from sqlalchemy.orm import relationship
from app.database import Base, generate_uuid

class Contest(Base):
    __tablename__ = "contests"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_by = Column(CHAR(36), ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    problems = relationship("ContestProblem", back_populates="contest", cascade="all, delete-orphan")
    participants = relationship("ContestParticipant", back_populates="contest", cascade="all, delete-orphan")

class ContestProblem(Base):
    __tablename__ = "contest_problems"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    contest_id = Column(CHAR(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(CHAR(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, nullable=False)
    points = Column(Integer, default=100)
    
    # Relationships
    contest = relationship("Contest", back_populates="problems")
    problem = relationship("Problem")

class ContestParticipant(Base):
    __tablename__ = "contest_participants"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    contest_id = Column(CHAR(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, default=func.current_timestamp())
    score = Column(Integer, default=0)
    
    # Relationships
    contest = relationship("Contest", back_populates="participants")
    user = relationship("User")