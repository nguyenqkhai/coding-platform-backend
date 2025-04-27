from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import uuid

# Tạo engine kết nối đến database
engine = create_engine(settings.DATABASE_URL)

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models
Base = declarative_base()

# Hàm tiện ích để tạo UUID
def generate_uuid():
    return str(uuid.uuid4())

# Hàm để cung cấp session cho các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()