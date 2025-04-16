import pytest
from unittest.mock import patch
from src.task_manager.expansion import expand_and_save
from src.task_manager.data_models import Task, Subtask, TasksData, MetaData
from src.exceptions import AIResponseParsingError, ParentTaskNotFoundError
from unittest.mock import ANY # Import ANY if needed for other mocks

# Sample Data Fixture
@pytest.fixture
def sample_tasks_list() -> list[Task]:
    # Deep copy equivalent
    data = {
        "meta": {"projectName": "Test", "version": "1.0"},
        "tasks": [
            {"id": 1, "title": "Task 1", "status": "done", "dependencies": [], "priority": "high", "subtasks": []},
            {"id": 2, "title": "Task 2", "status": "pending", "dependencies": [1], "priority": "medium", "subtasks": []},
        {"id": 3, "title": "Task 3", "status": "pending", "dependencies": [1], "priority": "high", "subtasks": []},
            {"id": 4, "title": "Task 4", "status": "pending", "dependencies": [2], "priority": "low", "subtasks": []}
        ]
    }
    tasks_data = TasksData.model_validate(data)
    return tasks_data.tasks

@pytest.fixture
def sample_tasks_data() -> TasksData:
    # Deep copy equivalent
    data = {
        "meta": {"projectName": "Test", "version": "1.0"},
        "tasks": [
            {"id": 1, "title": "Task 1", "status": "done", "dependencies": [], "priority": "high", "subtasks": []},
            {"id": 2, "title": "Task 2", "status": "pending", "dependencies": [1], "priority": "medium", "subtasks": []},
            {"id": 3, "title": "Task 3", "status": "pending", "dependencies": [1], "priority": "high", "subtasks": []},
            {"id": 4, "title": "Task 4", "status": "pending", "dependencies": [2], "priority": "low", "subtasks": []}
        ]
    }
    tasks_data = TasksData.model_validate(data)
    return tasks_data

@patch("src.task_manager.expansion.core.get_task_by_id")
@patch("src.task_manager.expansion.storage.load_tasks")
@patch("src.task_manager.expansion.storage.save_tasks")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_success(mock_ai_client, mock_save_tasks, mock_load_tasks, mock_get_task, sample_tasks_data):
    """Test successful expansion and saving."""
    # Mock load_tasks to return fixture data
    mock_load_tasks.return_value = sample_tasks_data
    # Mock get_task_by_id to return Task 3
    task3 = next((t for t in sample_tasks_data.tasks if t.id == 3), None)
    assert task3 is not None
    mock_get_task.return_value = task3
    # Mock AI client
    mock_ai_client.return_value = '[{"title": "Subtask 1", "description": "Desc 1"}]'
    # Mock save_tasks
    mock_save_tasks.return_value = True

    result = expand_and_save("3")

    assert result is True
    mock_ai_client.assert_called_once()
    mock_save_tasks.assert_called_once()
    # Check that the task list passed to save_tasks has the new subtask
    saved_data = mock_save_tasks.call_args[0][0]
    saved_task3 = next((t for t in saved_data.tasks if t.id == 3), None)
    assert saved_task3 is not None
    assert len(saved_task3.subtasks) == 1
    assert saved_task3.subtasks[0].title == "Subtask 1"

@patch("src.task_manager.expansion.core.get_task_by_id")
@patch("src.task_manager.expansion.storage.load_tasks")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_ai_failure(mock_ai_client, mock_load_tasks, mock_get_task, sample_tasks_data):
    """Test when AI client fails."""
    mock_load_tasks.return_value = sample_tasks_data
    task3 = next((t for t in sample_tasks_data.tasks if t.id == 3), None)
    assert task3 is not None
    mock_get_task.return_value = task3
    mock_ai_client.return_value = None # Simulate AI failure

    result = expand_and_save("3")

    assert result is False
    mock_ai_client.assert_called_once() # AI should still be called

@patch("src.task_manager.expansion.core.get_task_by_id")
@patch("src.task_manager.expansion.storage.load_tasks")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_invalid_json(mock_ai_client, mock_load_tasks, mock_get_task, sample_tasks_data):
    """Test when AI returns invalid JSON."""
    mock_load_tasks.return_value = sample_tasks_data
    task3 = next((t for t in sample_tasks_data.tasks if t.id == 3), None)
    assert task3 is not None
    mock_get_task.return_value = task3
    mock_ai_client.return_value = 'invalid json' # Simulate invalid JSON

    result = expand_and_save("3")

    assert result is False
    mock_ai_client.assert_called_once()

# Test case for non-list JSON response remains largely the same, 
# but needs load_tasks mocked now for the initial get_task_by_id call in expand_and_save
@patch("src.task_manager.expansion.storage.load_tasks") # Add load_tasks mock
@patch("src.task_manager.expansion.core.get_task_by_id")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_ai_response_not_list(mock_ai_client, mock_get_task_by_id, mock_load_tasks, sample_tasks_data: TasksData):
    """Test when AI returns a valid JSON object but not a list."""
    # Mock load_tasks first
    mock_load_tasks.return_value = sample_tasks_data
    # Mock get_task_by_id to return Task 3 (target for expansion)
    task3 = next((t for t in sample_tasks_data.tasks if t.id == 3), None)
    assert task3 is not None
    mock_get_task_by_id.return_value = task3
    # Mock AI response
    mock_ai_client.return_value = '{"title": "Not a list"}'

    result = expand_and_save("3")
    # Expect failure because parsing expects a list
    assert result is False 
    mock_ai_client.assert_called_once()

@patch("src.task_manager.expansion.storage.load_tasks")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_parent_not_found(mock_expand_task_with_ai, mock_load_tasks, sample_tasks_data):
    # Mock AI client to return a valid JSON response
    mock_expand_task_with_ai.return_value = '[{"title": "Subtask 1", "description": "Desc 1"}, {"title": "Subtask 2", "description": "Desc 2"}]'
    mock_load_tasks.return_value = sample_tasks_data

    # Call expand_and_save with a non-existent parent task ID
    result = expand_and_save("99")

    # Assert that the function returns False (parent not found)
    assert result is False

@patch("src.task_manager.expansion.storage.load_tasks")
@patch("src.task_manager.expansion.storage.save_tasks")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_storage_failure(mock_expand_task_with_ai, mock_save_tasks, mock_load_tasks, sample_tasks_data):
    # Mock AI client to return a valid JSON response
    mock_expand_task_with_ai.return_value = '[{"title": "Subtask 1", "description": "Desc 1"}, {"title": "Subtask 2", "description": "Desc 2"}]'
    mock_load_tasks.return_value = sample_tasks_data
    # Mock save_tasks to simulate failure
    mock_save_tasks.side_effect = IOError("Failed to save file")


    # Call expand_and_save
    result = expand_and_save("3")

    # Assert that the function returns False (storage failure)
    assert result is False

@patch("src.task_manager.expansion.core.get_task_by_id")
@patch("src.task_manager.expansion.ai_client.expand_task_with_ai")
def test_expand_and_save_parent_not_found_2(mock_expand_task_with_ai, mock_get_task_by_id, sample_tasks_data):
    # Mock AI client to return a valid JSON response
    mock_expand_task_with_ai.return_value = '[{"title": "Subtask 1", "description": "Desc 1"}, {"title": "Subtask 2", "description": "Desc 2"}]'
    mock_get_task_by_id.return_value = None

    # Call expand_and_save with a non-existent parent task ID
    result = expand_and_save("99")

    # Assert that the function returns False (parent not found)
    assert result is False
