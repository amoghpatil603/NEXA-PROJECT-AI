import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.api.ai_service import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_readiness_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True

def test_system_status_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_chat_endpoint_empty_message():
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 400
    
def test_chat_endpoint_missing_models():
    # Because models are missing, it should return 501 Not Implemented
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 501
    assert "error" in response.json()

def test_voice_endpoint_missing_models():
    # Because voice models are missing, it should return 501
    response = client.post("/voice", json={"text": "Test"})
    assert response.status_code == 501

def test_vision_endpoint_missing_image():
    response = client.post("/vision")
    # File is required
    assert response.status_code == 422
