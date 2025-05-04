import pytest
from unittest.mock import patch, MagicMock, call
import time
from openai import APITimeoutError, APIConnectionError, RateLimitError, OpenAIError

# Use absolute paths for imports
from src.ai import client as ai_client
from src.config.settings import settings

# --- Test Fixtures ---

@pytest.fixture(autouse=True)
def mock_settings(mocker):
    """Ensure specific settings are mocked for tests."""
    mocker.patch('src.ai.client.settings.DEEPSEEK_API_KEY', "fake-api-key")
    mocker.patch('src.ai.client.settings.DEEPSEEK_BASE_URL', "http://fake-url.com")
    mocker.patch('src.ai.client.settings.DEEPSEEK_REASONING_MODEL', "mock-reasoning-model")
    mocker.patch('src.ai.client.settings.AI_TEMPERATURE', 0.5)
    mocker.patch('src.ai.client.settings.DEBUG', False)
    # Re-initialize client with mocked settings if necessary, or mock the client instance directly
    # For simplicity, we'll mock the 'create' method on the client instance below.

@pytest.fixture
def mock_openai_client(mocker):
    """Mocks the OpenAI client instance and its methods."""
    # Mock the client instance directly within the ai_client module
    mock_client_instance = MagicMock()
    mock_chat_completions = MagicMock()
    mock_client_instance.chat.completions = mock_chat_completions
    mocker.patch('src.ai.client.client', mock_client_instance) # Patch the initialized client
    return mock_chat_completions # Return the mock for 'create' method

# --- Tests for call_deepseek ---

def test_call_deepseek_success(mock_openai_client):
    """Test successful API call on the first attempt."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=" Success response "))]
    mock_openai_client.create.return_value = mock_response

    messages = [{"role": "user", "content": "test"}]
    result = ai_client.call_deepseek("test-model", messages, temperature=0.8)

    assert result == "Success response"
    mock_openai_client.create.assert_called_once_with(
        model="test-model",
        messages=messages,
        temperature=0.8, # Check override
        max_tokens=settings.AI_MAX_TOKENS  # Check default
    )


def test_call_deepseek_retry_on_timeout(mock_openai_client, mocker):
    """Test retry logic on APITimeoutError."""
    mock_sleep = mocker.patch('time.sleep', return_value=None)
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Success after retry"))]
    mock_openai_client.create.side_effect = [
        APITimeoutError("Timeout"),
        mock_response
    ]

    messages = [{"role": "user", "content": "retry test"}]
    result = ai_client.call_deepseek("retry-model", messages, max_retries=3, retry_delay=1)

    assert result == "Success after retry"
    assert mock_openai_client.create.call_count == 2
    mock_sleep.assert_called_once_with(1) # Check retry delay

def test_call_deepseek_retry_on_connection_error(mock_openai_client, mocker):
    """Test retry logic on APIConnectionError."""
    mock_sleep = mocker.patch('time.sleep', return_value=None)
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Success"))]
    mock_openai_client.create.side_effect = [
        APIConnectionError(request=MagicMock()),
        mock_response
    ]

    messages = [{"role": "user", "content": "conn test"}]
    result = ai_client.call_deepseek("conn-model", messages, max_retries=3, retry_delay=2)

    assert result == "Success"
    assert mock_openai_client.create.call_count == 2
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(2)

def test_call_deepseek_fail_after_retries(mock_openai_client, mocker):
    """Test failure after exceeding max retries."""
    mock_sleep = mocker.patch('time.sleep', return_value=None)
    mock_openai_client.create.side_effect = RateLimitError("Rate limited", response=MagicMock(), body=None)

    messages = [{"role": "user", "content": "fail test"}]
    result = ai_client.call_deepseek("fail-model", messages, max_retries=2, retry_delay=1)

    assert result is None
    assert mock_openai_client.create.call_count == 2
    assert mock_sleep.call_count == 1 # Only sleeps before the last retry

def test_call_deepseek_unexpected_error(mock_openai_client):
    """Test failure on an unexpected OpenAIError."""
    mock_openai_client.create.side_effect = OpenAIError("Something else went wrong")

    messages = [{"role": "user", "content": "unexpected"}]
    result = ai_client.call_deepseek("unexpected-model", messages)

    assert result is None
    mock_openai_client.create.assert_called_once()

def test_call_deepseek_client_not_initialized(mocker):
    """Test behavior when the client is not initialized (e.g., missing API key)."""
    mocker.patch('src.ai.client.client', None) # Simulate client initialization failure
    messages = [{"role": "user", "content": "no client"}]
    result = ai_client.call_deepseek("no-client-model", messages)
    assert result is None

# --- Tests for generate_tasks_from_prd ---

@patch('src.ai.client.call_deepseek')
def test_generate_tasks_from_prd_success(mock_call_deepseek):
    """Test successful task generation."""
    mock_call_deepseek.return_value = '{"meta": {{}}, "tasks": [{{"id": 1}}]}'
    prd_content = "Build a thing."
    result = ai_client.generate_tasks_from_prd(prd_content)

    assert result == '{"meta": {{}}, "tasks": [{{"id": 1}}]}'
    mock_call_deepseek.assert_called_once()
    args, kwargs = mock_call_deepseek.call_args
    # Check messages in kwargs instead of args
    assert "messages" in kwargs
    assert isinstance(kwargs["messages"], list)
    assert len(kwargs["messages"]) == 1
    assert "Build a thing." in kwargs["messages"][0]["content"]
    assert "Output ONLY the JSON object" in kwargs["messages"][0]["content"]

@patch('src.ai.client.call_deepseek')
def test_generate_tasks_from_prd_api_fail(mock_call_deepseek):
    """Test failure when the API call fails."""
    mock_call_deepseek.return_value = None
    result = ai_client.generate_tasks_from_prd("Build a thing.")
    assert result is None
    mock_call_deepseek.assert_called_once()

@patch('src.ai.client.call_deepseek')
def test_generate_tasks_from_prd_invalid_json_response(mock_call_deepseek):
    """Test handling of non-JSON response from AI."""
    mock_call_deepseek.return_value = "This is not JSON."
    result = ai_client.generate_tasks_from_prd("Build a thing.")
    assert result is None
    mock_call_deepseek.assert_called_once()

# --- Tests for expand_task_with_ai ---

@patch('src.ai.client.call_deepseek')
def test_expand_task_with_ai_success(mock_call_deepseek):
    """Test successful subtask expansion."""
    mock_call_deepseek.return_value = '[{"title": "Subtask 1"}]'
    result = ai_client.expand_task_with_ai("Parent Task", "Description", "Context")

    assert result == '[{"title": "Subtask 1"}]'
    mock_call_deepseek.assert_called_once()
    args, kwargs = mock_call_deepseek.call_args
    # Check messages in kwargs instead of args
    assert "messages" in kwargs
    assert isinstance(kwargs["messages"], list)
    assert len(kwargs["messages"]) == 1
    assert "Parent Task" in kwargs["messages"][0]["content"]
    assert "Description" in kwargs["messages"][0]["content"]
    assert "Context" in kwargs["messages"][0]["content"]
    assert "JSON list" in kwargs["messages"][0]["content"] # Check prompt instructions

@patch('src.ai.client.call_deepseek')
def test_expand_task_with_ai_api_fail(mock_call_deepseek):
    """Test failure when the API call fails."""
    mock_call_deepseek.return_value = None
    result = ai_client.expand_task_with_ai("Parent Task", None, "Context")
    assert result is None
    mock_call_deepseek.assert_called_once()

@patch('src.ai.client.call_deepseek')
def test_expand_task_with_ai_invalid_json_response(mock_call_deepseek):
    """Test handling of non-JSON list response from AI."""
    mock_call_deepseek.return_value = '{"title": "Not a list"}' # Return JSON object, not list
    result = ai_client.expand_task_with_ai("Parent Task", None, "Context")
    assert result is None
    mock_call_deepseek.assert_called_once()
