from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, func
from sqlalchemy.types import CHAR
from app.database import Base, generate_uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    rating = Column(Integer, default=0)