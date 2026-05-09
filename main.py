import time
import uuid as uuid_module
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from database import get_db, engine
import models
from logger import setup_logger

models.Base.metadata.create_all(bind=engine)

logger = setup_logger("qa_api")

app = FastAPI(
    title="Q&A API",
    description="REST API з логуванням та метриками",
    version="3.0.0"
)

Instrumentator().instrument(app).expose(app)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware виконується для КОЖНОГО запиту.
    Логує: метод, шлях, статус, час виконання, request_id.
    """
    request_id = str(uuid_module.uuid4())[:8]  # короткий ID для трасування
    start_time = time.time()

    logger.info("request_started", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown"
    })

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    log_level = logger.warning if response.status_code >= 400 else logger.info
    log_level("request_finished", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms
    })

    return response

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

@app.get("/questions", response_model=list[QuestionOut], tags=["Questions"])
def get_all_questions(db: Session = Depends(get_db)):
    logger.debug("fetching_all_questions")
    questions = db.query(models.Question).all()
    logger.info("questions_fetched", extra={"count": len(questions)})
    return questions


@app.get("/questions/{question_id}", response_model=QuestionOut, tags=["Questions"])
def get_question(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        logger.warning("question_not_found", extra={"question_id": str(question_id)})
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    logger.info("question_fetched", extra={"question_id": str(question_id)})
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
    logger.info("question_created", extra={
        "question_id": str(q.id),
        "author_id": str(data.author_id),
        "title": data.title
    })
    return q


@app.put("/questions/{question_id}", response_model=QuestionOut, tags=["Questions"])
def update_question(question_id: UUID, data: QuestionCreate, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        logger.warning("question_not_found_for_update", extra={"question_id": str(question_id)})
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    q.title = data.title
    q.body = data.body
    db.commit()
    db.refresh(q)
    logger.info("question_updated", extra={"question_id": str(question_id)})
    return q


@app.delete("/questions/{question_id}", status_code=204, tags=["Questions"])
def delete_question(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        logger.warning("question_not_found_for_delete", extra={"question_id": str(question_id)})
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    db.delete(q)
    db.commit()
    logger.info("question_deleted", extra={"question_id": str(question_id)})


@app.post("/questions/{question_id}/vote", response_model=QuestionOut, tags=["Questions"])
def vote_question(question_id: UUID, vote: VoteRequest, db: Session = Depends(get_db)):
    if vote.value not in (1, -1):
        logger.warning("invalid_vote_value", extra={"value": vote.value})
        raise HTTPException(status_code=400, detail="value має бути +1 або -1")
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        logger.warning("question_not_found_for_vote", extra={"question_id": str(question_id)})
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    q.votes += vote.value
    db.commit()
    db.refresh(q)
    logger.info("question_voted", extra={
        "question_id": str(question_id),
        "vote": vote.value,
        "new_votes": q.votes
    })
    return q

@app.get("/questions/{question_id}/answers", response_model=list[AnswerOut], tags=["Answers"])
def get_answers(question_id: UUID, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    answers = db.query(models.Answer).filter(models.Answer.question_id == question_id).all()
    logger.info("answers_fetched", extra={"question_id": str(question_id), "count": len(answers)})
    return answers


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
    logger.info("answer_created", extra={
        "answer_id": str(a.id),
        "question_id": str(question_id)
    })
    return a


@app.put("/answers/{answer_id}", response_model=AnswerOut, tags=["Answers"])
def update_answer(answer_id: UUID, data: AnswerCreate, db: Session = Depends(get_db)):
    a = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not a:
        logger.warning("answer_not_found", extra={"answer_id": str(answer_id)})
        raise HTTPException(status_code=404, detail="Відповідь не знайдена")
    a.body = data.body
    db.commit()
    db.refresh(a)
    logger.info("answer_updated", extra={"answer_id": str(answer_id)})
    return a


@app.get("/users/{user_id}/answers", response_model=list[AnswerOut], tags=["Users"])
def get_user_answers(user_id: UUID, db: Session = Depends(get_db)):
    answers = db.query(models.Answer).filter(models.Answer.author_id == user_id).all()
    logger.info("user_answers_fetched", extra={"user_id": str(user_id), "count": len(answers)})
    return answers

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(models.text("SELECT 1"))
        logger.info("health_check_ok", extra={"db": "connected"})
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error("health_check_failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="DB недоступна")


@app.get("/debug/error", tags=["System"])
def trigger_error():
    logger.error("intentional_error_triggered", extra={
        "reason": "debug endpoint called",
        "severity": "demo"
    })
    raise HTTPException(status_code=500, detail="Демонстраційна помилка для логів")