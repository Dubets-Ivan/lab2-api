from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime

app = FastAPI(
    title="Q&A API",
    description="REST API для системи запитань та відповідей",
    version="1.0.0"
)

class QuestionCreate(BaseModel):
    author_id: UUID
    title: str
    body: str

class Question(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    body: str
    votes: int = 0
    created_at: datetime

class AnswerCreate(BaseModel):
    author_id: UUID
    body: str

class Answer(BaseModel):
    id: UUID
    question_id: UUID
    author_id: UUID
    body: str
    votes: int = 0
    created_at: datetime

class VoteRequest(BaseModel):
    vote: int

question_db: dict[UUID, Question] = {}
answer_db: dict[UUID, Answer] = {}

def seed_data():
    q_id = uuid4()
    a_id_1 = uuid4()
    a_id_2 = uuid4()
    user_1 = uuid4()
    user_2 = uuid4()

    question_db[q_id] = Question(
        id=q_id,
        author_id=user_1,
        title="Як працює FastAPI?",
        body="Мені цікаво, як FastAPI обробляє запити та відповіді.",
        votes=5,
        created_at=datetime.now()
    )
    answer_db[a_id_1] = Answer(
        id=a_id_1,
        question_id=q_id,
        author_id=user_2,
        body="FastAPI використовує Starlette для обробки запитів та Pydantic для валідації даних.",
        votes=3,
        created_at=datetime.now()
    )
    answer_db[a_id_2] = Answer(
        id=a_id_2,
        question_id=q_id,
        author_id=user_1,
        body="Також FastAPI підтримує асинхронні функції, що дозволяє обробляти багато запитів одночасно.",
        votes=2,
        created_at=datetime.now()
    )

seed_data()

@app.get("/questions", response_model=list[Question], tags=["Questions"])
def get_all_questions():
    return list(question_db.values())

@app.get("/questions/{question_id}", response_model=Question, tags=["Questions"])
def get_question(question_id: UUID):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    return question_db[question_id]

@app.post("/questions", response_model=Question, status_code=201, tags=["Questions"])
def create_question(data: QuestionCreate):
    question = Question(
        id=uuid4(),
        author_id=data.author_id,
        title=data.title,
        body=data.body,
        votes=0,
        created_at=datetime.now()
    )
    question_db[question.id] = question
    return question

@app.put("/questions/{question_id}", response_model=Question, tags=["Questions"])
def update_question(question_id: UUID, data: QuestionCreate):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    existing = question_db[question_id]
    updated = existing.model_copy(update={
        "title": data.title,
        "body": data.body
    })
    question_db[question_id] = updated
    return updated

@app.delete("/questions/{question_id}", status_code=204, tags=["Questions"])
def delete_question(question_id: UUID):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    del question_db[question_id]

@app.post("/questions/{question_id}/vote", response_model=Question, tags=["Questions"])
def vote_question(question_id: UUID, vote: VoteRequest):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    if vote.value not in (1, -1):
        raise HTTPException(status_code=400, detail="value має бути +1 або -1")
    q = question_db[question_id]
    updated = q.model_copy(update={"votes": q.votes + vote.value})
    question_db[question_id] = updated
    return updated

@app.get("/questions/{question_id}/answers", response_model=list[Answer], tags=["Answers"])
def get_answers_for_question(question_id: UUID):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    return [a for a in answer_db.values() if a.question_id == question_id]

@app.post("/questions/{question_id}/answers", response_model=Answer, status_code=201, tags=["Answers"])
def create_answer(question_id: UUID, data: AnswerCreate):
    if question_id not in question_db:
        raise HTTPException(status_code=404, detail="Question not found")
    answer = Answer(
        id=uuid4(),
        question_id=question_id,
        author_id=data.author_id,
        body=data.body,
        votes=0,
        created_at=datetime.utcnow()
    )
    answer_db[answer.id] = answer
    return answer

@app.put("/answers/{answer_id}", response_model=Answer, tags=["Answers"])
def update_answer(answer_id: UUID, data: AnswerCreate):
    if answer_id not in answer_db:
        raise HTTPException(status_code=404, detail="Відповідь не знайдена")
    existing = answer_db[answer_id]
    updated = existing.model_copy(update={"body": data.body})
    answer_db[answer_id] = updated
    return updated