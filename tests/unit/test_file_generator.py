import pytest
from unittest.mock import patch
import os
from src.task_manager.file_generator import generate_file_from_task, _sanitize_filename, DEFAULT_OUTPUT_DIR
from src.task_manager.data_models import Task

# --- Test Cases for _sanitize_filename ---

@pytest.mark.parametrize("input_name, expected_output", [
    ("Simple Task", "Simple_Task"),
    ("Task with /\\:*?\"<>| chars", "Task_with__chars"),
    ("  Leading and trailing spaces  ", "__Leading_and_trailing_spaces__"),
    ("VeryLongName" * 10, ("VeryLongName" * 10)[:100]), # Test length limit
    ("python_script", "python_script"),
    ("file.md", "file.md"),
])
def test_sanitize_filename(input_name, expected_output):
    assert _sanitize_filename(input_name) == expected_output

# --- Test Cases for generate_file_from_task ---

def test_generate_file_success_defaults(tmp_path):
    """Test successful file generation with default output dir."""
    task = Task(id=1, title="Test Task Gen", description="Desc.", details="Details.", priority="medium")
    expected_dir = os.path.join(tmp_path, DEFAULT_OUTPUT_DIR) # Use tmp_path for isolation
    expected_filename = "task_1_Test_Task_Gen.md" # Default extension
    expected_filepath = os.path.join(expected_dir, expected_filename)

    # Ensure directory doesn't exist initially (tmp_path handles cleanup)
    assert not os.path.exists(expected_dir)

    generated_path = generate_file_from_task(task, output_dir=expected_dir)

    assert generated_path == expected_filepath
    assert os.path.exists(expected_filepath)

    # Check file content
    with open(generated_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "# Task ID: 1" in content
        assert "# Title: Test Task Gen" in content
        assert "## Description\nDesc." in content
        assert "## Details\nDetails." in content
        assert "# TODO: Implement task logic here" in content

def test_generate_file_success_python_extension(tmp_path):
    """Test correct extension guessing for Python scripts."""
    task = Task(id=2, title="Create Python Script", priority="high")
    expected_dir = tmp_path / DEFAULT_OUTPUT_DIR
    expected_filename = "task_2_Create_Python_Script.py" # Should guess .py
    expected_filepath = expected_dir / expected_filename

    generated_path = generate_file_from_task(task, output_dir=str(expected_dir))

    assert generated_path == str(expected_filepath)
    assert expected_filepath.exists()
    with open(generated_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "# Title: Create Python Script" in content

def test_generate_file_success_custom_output_dir(tmp_path):
    """Test successful file generation with a custom output directory."""
    task = Task(id=3, title="Another Task")
    custom_dir = tmp_path / "custom_output"
    expected_filename = "task_3_Another_Task.md"
    expected_filepath = custom_dir / expected_filename

    generated_path = generate_file_from_task(task, output_dir=str(custom_dir))

    assert generated_path == str(expected_filepath)
    assert custom_dir.exists()
    assert expected_filepath.exists()

def test_generate_file_no_description_or_details(tmp_path):
    """Test file generation when description and details are None."""
    task = Task(id=4, title="Minimal Task")
    expected_dir = tmp_path / DEFAULT_OUTPUT_DIR
    expected_filepath = expected_dir / "task_4_Minimal_Task.md"

    generated_path = generate_file_from_task(task, output_dir=str(expected_dir))

    assert generated_path == str(expected_filepath)
    assert expected_filepath.exists()
    with open(generated_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "## Description" not in content
        assert "## Details" not in content
        assert "# TODO: Implement task logic here" in content

@patch('os.makedirs') # Mock os.makedirs to simulate failure
def test_generate_file_fail_create_dir(mock_makedirs, tmp_path):
    """Test failure when creating the output directory fails."""
    mock_makedirs.side_effect = OSError("Permission denied")
    task = Task(id=5, title="Dir Fail")
    custom_dir = tmp_path / "unwritable_dir" # Path exists, but makedirs fails

    generated_path = generate_file_from_task(task, output_dir=str(custom_dir))

    assert generated_path is None
    mock_makedirs.assert_called_once_with(str(custom_dir), exist_ok=True)
    assert not custom_dir.exists() # Directory should not be created

@patch('builtins.open') # Mock the open function to simulate write failure
def test_generate_file_fail_write_file(mock_open, tmp_path):
    """Test failure when writing the file fails."""
    mock_open.side_effect = IOError("Disk full")
    task = Task(id=6, title="Write Fail")
    output_dir = tmp_path / DEFAULT_OUTPUT_DIR
    expected_filepath = output_dir / "task_6_Write_Fail.md"

    # We need the directory to exist for open to be called
    output_dir.mkdir()

    generated_path = generate_file_from_task(task, output_dir=str(output_dir))

    assert generated_path is None
    mock_open.assert_called_once_with(str(expected_filepath), 'w', encoding='utf-8')
    assert not expected_filepath.exists() # File should not be created
