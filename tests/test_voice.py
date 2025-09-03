"""
Tests for voice functionality.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.handlers.voice_handler import router
from src.services.voice_service import VoiceService


@pytest.fixture
def voice_app():
    """Create test app with voice router."""
    app = FastAPI()
    app.include_router(router, prefix="/voice")
    return app


@pytest.fixture
def client(voice_app):
    """Create test client."""
    return TestClient(voice_app)


def test_voice_twiml_endpoint(client):
    """Test TwiML generation endpoint."""
    response = client.post("/voice/twiml")
    assert response.status_code == 200
    assert "ConversationRelay" in response.text


def test_voice_test_endpoint(client):
    """Test voice service health check."""
    response = client.get("/voice/test")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_voice_session_creation():
    """Test voice session creation."""
    service = VoiceService()
    session = await service.create_voice_session("test_call_sid", "+1234567890")
    
    assert session.call_sid == "test_call_sid"
    assert session.phone_number == "+1234567890"
    assert session.status.value == "setup"