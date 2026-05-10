from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_questions_empty():
    response = client.get("/questions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_question():
    payload = {
        "author_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Тестове питання",
        "body": "Тіло тестового питання"
    }
    response = client.post("/questions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестове питання"
    assert "id" in data

def test_get_question_not_found():
    response = client.get("/questions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_vote_invalid_value():
    payload = {"author_id": "550e8400-e29b-41d4-a716-446655440000",
               "title": "Q", "body": "B"}
    q = client.post("/questions", json=payload).json()
    
    response = client.post(f"/questions/{q['id']}/vote", json={"value": 5})
    assert response.status_code == 400