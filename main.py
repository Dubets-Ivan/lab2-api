from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db, engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Q&A API",
    description="REST API з PostgreSQL persistence шаром",
    version="2.0.0"
)

class QuestionCreate(BaseModel):
    author_id: UUID
    title: str
    body: str

class QuestionOut(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    body: str
    votes: int
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerCreate(BaseModel):
    author_id: UUID
    body: str

class AnswerOut(BaseModel):
    id: UUID
    question_id: UUID
    author_id: UUID
    body: str
    votes: int
    created_at: datetime

    class Config:
        from_attributes = True

class VoteRequest(BaseModel):
    value: int


def seed_data(db: Session):
    if db.query(models.Question).first():
        return

    user_1, user_2 = uuid4(), uuid4()

    q1 = models.Question(
        author_id=user_1,
        title="Як працює FastAPI?",
        body="Мені цікаво, як FastAPI обробляє запити та відповіді.",
        votes=5
    )

    q2 = models.Question(
        author_id=user_2,
        title="Що таке судовий прецедент?",
        body="Часто чую про судові прецеденти...",
        votes=10
    )

    q3 = models.Question(
        author_id=user_1,
        title="Що таке судова практика?",
        body="Поясніть, будь ласка...",
        votes=4
    )

    q4 = models.Question(
        author_id=user_2,
        title="Що таке правовий звичай?",
        body="Мені цікаво...",
        votes=3
    )

    db.add_all([q1, q2, q3, q4])
    db.commit()

    a1 = models.Answer(
        question_id=q1.id,
        author_id=user_2,
        body="FastAPI використовує Starlette...",
        votes=3
    )

    a2 = models.Answer(
        question_id=q1.id,
        author_id=user_1,
        body="Також FastAPI підтримує async/await...",
        votes=2
    )

    a3 = models.Answer(
        question_id=q2.id,
        author_id=user_1,
        body="Судовий прецедент — рішення суду...",
        votes=8
    )

    a4 = models.Answer(
        question_id=q3.id,
        author_id=user_2,
        body="Судова практика — сукупність рішень...",
        votes=6
    )

    a5 = models.Answer(
        question_id=q4.id,
        author_id=user_1,
        body="Правовий звичай — історично сформоване правило...",
        votes=5
    )

    db.add_all([a1, a2, a3, a4, a5])
    db.commit()


@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_data(db)


@app.get("/questions", response_model=list[QuestionOut], tags=["Questions"])
def get_all_questions(db: Session = Depends(get_db)):
    return db.query(models.Question).all()


@app.get("/questions/{question_id}", response_model=QuestionOut, tags=["Questions"])
def get_question(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    return q


@app.post("/questions", response_model=QuestionOut, status_code=201, tags=["Questions"])
def create_question(data: QuestionCreate, db: Session = Depends(get_db)):
    q = models.Question(
        author_id=data.author_id,
        title=data.title,
        body=data.body
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@app.put("/questions/{question_id}", response_model=QuestionOut, tags=["Questions"])
def update_question(question_id: UUID, data: QuestionCreate, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    q.title = data.title
    q.body = data.body
    db.commit()
    db.refresh(q)
    return q


@app.delete("/questions/{question_id}", status_code=204, tags=["Questions"])
def delete_question(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    db.delete(q)
    db.commit()


@app.post("/questions/{question_id}/vote", response_model=QuestionOut, tags=["Questions"])
def vote_question(question_id: UUID, vote: VoteRequest, db: Session = Depends(get_db)):
    if vote.value not in (1, -1):
        raise HTTPException(status_code=400, detail="value має бути +1 або -1")
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    q.votes += vote.value
    db.commit()
    db.refresh(q)
    return q


@app.get("/questions/{question_id}/answers", response_model=list[AnswerOut], tags=["Answers"])
def get_answers(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    return db.query(models.Answer).filter(models.Answer.question_id == question_id).all()


@app.post("/questions/{question_id}/answers", response_model=AnswerOut, status_code=201, tags=["Answers"])
def create_answer(question_id: UUID, data: AnswerCreate, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    a = models.Answer(
        question_id=question_id,
        author_id=data.author_id,
        body=data.body
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@app.put("/answers/{answer_id}", response_model=AnswerOut, tags=["Answers"])
def update_answer(answer_id: UUID, data: AnswerCreate, db: Session = Depends(get_db)):
    a = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Відповідь не знайдена")
    a.body = data.body
    db.commit()
    db.refresh(a)
    return a


@app.get("/users/{user_id}/answers", response_model=list[AnswerOut], tags=["Users"])
def get_user_answers(user_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.Answer).filter(models.Answer.author_id == user_id).all()


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "db": "postgresql", "service": "Q&A API v2"}