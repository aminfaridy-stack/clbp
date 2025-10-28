import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Database URL
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models (SQLAlchemy ORM) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String)
    role = Column(String(20)) # 'admin', 'clinician', 'patient'
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Questionnaire(Base):
    __tablename__ = "questionnaires"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True)
    title_fa = Column(String(255))
    title_en = Column(String(255))
    description_fa = Column(Text)
    description_en = Column(Text)
    version = Column(Integer, default=1)
    questions = relationship("Question", back_populates="questionnaire")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    index = Column(Integer)
    text_fa = Column(Text)
    text_en = Column(Text)
    input_type = Column(String(50))
    options_fa = Column(JSON)
    options_en = Column(JSON)
    reverse_scored = Column(Boolean, default=False)
    questionnaire = relationship("Questionnaire", back_populates="questions")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    time_point = Column(String(5)) # 't0', 't1', 't2'
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    time_point = Column(String(5))
    score = Column(Integer)
    category_fa = Column(String(100))
    category_en = Column(String(100))
    breakdown_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    time_point = Column(String(5))
    model_version = Column(String(50))
    risk_percentage = Column(Integer)
    risk_category_fa = Column(String(50))
    risk_category_en = Column(String(50))
    shap_summary_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50))
    algo = Column(String(50))
    metrics_json = Column(JSON)
    uploaded_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    entity = Column(String(100))
    entity_id = Column(Integer)
    meta_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Pydantic Models for API ---
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: UserInDB
    
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class QuestionSchema(BaseModel):
    id: int
    index: int
    text_fa: str
    text_en: str
    input_type: str
    options_fa: Optional[List[str]]
    options_en: Optional[List[str]]
    reverse_scored: bool

    class Config:
        from_attributes = True

class QuestionnaireSchema(BaseModel):
    id: int
    key: str
    title_fa: str
    title_en: str
    description_fa: str
    description_en: str
    version: int
    questions: List[QuestionSchema]

    class Config:
        from_attributes = True
    
class ResponseIn(BaseModel):
    user_id: int
    questionnaire_id: int
    time_point: str
    responses: List[Dict[str, Any]]
    
class PredictionResult(BaseModel):
    risk_percentage: int
    risk_category_fa: str
    risk_category_en: str
    explanations: Dict[str, Any]
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()