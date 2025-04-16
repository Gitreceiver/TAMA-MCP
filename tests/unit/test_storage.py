import pytest
import json
import os
from unittest.mock import patch, mock_open

from src.config.settings import settings

from src.task_manager.storage import load_tasks, save_tasks
from src.task_manager.data_models import TasksData, MetaData, Task

# Sample valid data matching the Pydantic model
VALID_TASKS_DATA = {
    "meta": {"projectName": "Test Project", "version": "1.0"},
    "tasks": [
        {"id": 1, "title": "Task 1", "status": "pending", "dependencies": [], "priority": "medium", "subtasks": []}
    ]
}
VALID_TASKS_JSON = json.dumps(VALID_TASKS_DATA)

@pytest.fixture
def mock_settings(mocker):
    # Mock the settings object
    settings_mock = mocker.MagicMock()
    settings_mock.TASKS_JSON_PATH = "E:\\TAMA_MCP\\tasks.json"
    settings_mock.PROJECT_NAME = "Test Project"
    settings_mock.PROJECT_VERSION = "1.0.0"
    settings_mock.DEBUG = True
    return settings_mock

def test_load_tasks_success(mocker, mock_settings):
    """Test loading tasks from a valid JSON file."""
    # Mock os.path.exists to return True
    mocker.patch("os.path.exists", return_value=True)
    # Mock open context manager
    m = mocker.patch("builtins.open", mock_open(read_data=VALID_TASKS_JSON))

    # Correct indentation for the following lines
    tasks = load_tasks()

    assert tasks is not None
    # Assert specific attributes instead of direct object comparison
    assert tasks.meta.project_name == VALID_TASKS_DATA["meta"]["projectName"] # Re-applying fix: Use correct attribute name
    assert len(tasks.tasks) == len(VALID_TASKS_DATA["tasks"])
    assert tasks.tasks[0].id == VALID_TASKS_DATA["tasks"][0]["id"]
    assert tasks.tasks[0].title == VALID_TASKS_DATA["tasks"][0]["title"]
    m.assert_called_once_with(settings.TASKS_JSON_PATH, 'r', encoding='utf-8')

def test_load_tasks_file_not_found(mocker, mock_settings):
    """Test loading when the tasks file does not exist."""
    # Mock os.path.exists to return False
    mocker.patch("os.path.exists", return_value=False)
    # Mock open shouldn't be called, but mock it just in case
    m_open = mocker.patch("builtins.open", mock_open())

    # Correct indentation for the following lines
    tasks = load_tasks()

    assert tasks is not None  # Should return a default object
    # Assert specific attributes of the default object
    assert len(tasks.tasks) == 0
    # Check against the actual default metadata used in storage.py
    assert tasks.meta.project_name == "Test Project" # Re-applying fix: Use correct attribute name
    assert tasks.meta.version == "1.0"
    assert tasks.meta.prd_source is None
    m_open.assert_not_called()  # open should not be called

def test_load_tasks_invalid_json(mocker, mock_settings):
    """Test loading tasks from a file with invalid JSON."""
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data="{invalid json"))

    tasks = load_tasks()
    assert len(tasks.tasks) == 0

def test_load_tasks_validation_error(mocker, mock_settings):
    """Test loading tasks with data that doesn't match the Pydantic model."""
    invalid_data = json.dumps({"meta": {}, "tasks": [{"id": "not-a-number", "title": "Bad Task"}]})
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=invalid_data))

    tasks = load_tasks()

from unittest.mock import patch, mock_open, ANY # Import ANY

# ... (other imports and code) ...

def test_save_tasks_success(mocker, mock_settings):
    """Test saving tasks data successfully."""
    tasks_data_obj = TasksData.model_validate(VALID_TASKS_DATA)
    # Mock makedirs and open (just need a basic mock for open now)
    m_makedirs = mocker.patch("os.makedirs")
    mocker.patch("os.path.dirname", return_value="some_dir") # Keep this if needed by makedirs
    # Mock open to prevent file system access, but don't need mock_open features
    mock_file_handle = mocker.MagicMock()
    m_open = mocker.patch("builtins.open", return_value=mock_file_handle)

    # Mock json.dump directly
    mock_json_dump = mocker.patch("json.dump")

    success = save_tasks(tasks_data_obj)

    assert success is True
    m_makedirs.assert_called_once_with("some_dir", exist_ok=True)
    m_open.assert_called_once_with(settings.TASKS_JSON_PATH, 'w', encoding='utf-8')

    # Assert json.dump was called correctly
    expected_data_to_dump = tasks_data_obj.model_dump(by_alias=True)
    # We use ANY for the file handle argument as it's a mock object
    mock_json_dump.assert_called_once_with(expected_data_to_dump, ANY, indent=2)

def test_save_tasks_io_error(mocker, mock_settings):
    """Test saving tasks when an IOError occurs."""
    tasks_data_obj = TasksData.model_validate(VALID_TASKS_DATA)
    m_open = mocker.patch("builtins.open", mock_open())
    m_makedirs = mocker.patch("os.makedirs")
    mocker.patch("os.path.dirname", return_value="some_dir")
    # Simulate IOError on write
    handle = m_open.return_value
    handle.write.side_effect = IOError("Disk full")

    success = save_tasks(tasks_data_obj)

    assert success is False
