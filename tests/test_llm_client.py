import pytest
from unittest.mock import patch, MagicMock
from app.core.llm_client import LLMClient


def test_llm_client_init():
    client = LLMClient(base_url="http://test:8080", model_name="test-model")
    assert client.base_url == "http://test:8080"
    assert client.model_name == "test-model"


def test_llm_client_get_settings():
    client = LLMClient()
    settings = client._get_settings()
    assert isinstance(settings, dict)


@patch("app.core.llm_client.httpx.Client")
def test_llm_client_test_connection_success(mock_client):
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_context = MagicMock()
    mock_context.get.return_value = mock_response
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_client.return_value = mock_context

    client = LLMClient(base_url="http://test:8080")
    success, message = client.test_connection()

    assert success == True
    assert "успешно" in message.lower()


@patch("app.core.llm_client.httpx.Client")
def test_llm_client_test_connection_failure(mock_client):
    mock_client.side_effect = Exception("Connection failed")

    client = LLMClient(base_url="http://test:8080")
    success, message = client.test_connection()

    assert success == False


@patch("app.core.llm_client.httpx.Client")
def test_llm_client_chat(mock_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "model": "test-model",
        "usage": {"total_tokens": 100}
    }
    mock_response.raise_for_status = MagicMock()

    mock_context = MagicMock()
    mock_context.post.return_value = mock_response
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_client.return_value = mock_context

    client = LLMClient(base_url="http://test:8080", model_name="test-model")
    response = client.chat("System prompt", "User message")

    assert response.content == "Test response"
    assert response.model == "test-model"
