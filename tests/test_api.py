import pytest
import json
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
def test_create_conversation(api_client):
    response = api_client.post("/conversations")
    assert response.status_code == 200
    assert "conversation_id" in response.json()

@pytest.mark.django_db
def test_chat_greeting(api_client):
    # Mocking the graph execution
    with patch('agent.api.agent_app.invoke') as mock_invoke:
        mock_invoke.return_value = {
            "final_response": "Hello! How can I help you?",
            "shortlisted_projects": []
        }
        
        response = api_client.post(
            "/agents/chat",
            json={"message": "Hi", "conversation_id": "test-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "Hello! How can I help you?"
