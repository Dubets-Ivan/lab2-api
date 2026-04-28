from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(PG_UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    answers = relationship("Answer", back_populates="question", cascade="all, delete")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(PG_UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    author_id = Column(PG_UUID(as_uuid=True), nullable=False)
    body = Column(Text, nullable=False)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answers")