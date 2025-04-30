import logging
import os
import re
from typing import Optional

# Use absolute imports
# from .data_models import Task # Relative
# from ..config.settings import settings # Relative
from task_manager.data_models import Task # Absolute
from config import settings # Absolute

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "generated_files"

def _sanitize_filename(name: str) -> str:
    """Removes or replaces characters unsuitable for filenames."""
    # Remove invalid characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Limit length (optional)
    return name[:100]

def generate_file_from_task(task: Task, output_dir: Optional[str] = None) -> Optional[str]:
    """
    Generates a basic placeholder file based on a task's details.

    Args:
        task: The Task object.
        output_dir: The directory to save the file in. Defaults to DEFAULT_OUTPUT_DIR.

    Returns:
        The full path to the generated file if successful, otherwise None.
    """
    logger.info(f"Attempting to generate file for task: {task.id} - {task.title}")

    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR

    # 1. Determine filename (simple example: task_id_title.py)
    sanitized_title = _sanitize_filename(task.title)
    # Basic guess for extension, could be smarter based on title/desc
    extension = ".py" if "python" in task.title.lower() or "script" in task.title.lower() else ".md"
    filename = f"task_{task.id}_{sanitized_title}{extension}"
    filepath = os.path.join(output_dir, filename)

    # 2. Generate basic content
    content = f"# Task ID: {task.id}\n"
    content += f"# Title: {task.title}\n\n"
    if task.description:
        content += f"## Description\n{task.description}\n\n"
    if task.details:
        content += f"## Details\n{task.details}\n\n"
    content += "# TODO: Implement task logic here\n"

    # 3. Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {output_dir}")
    except OSError as e:
        logger.error(f"Failed to create output directory '{output_dir}': {e}")
        return None

    # 4. Write the file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully generated file: {filepath}")
        return filepath
    except IOError as e:
        logger.exception(f"Failed to write generated file '{filepath}': {e}", exc_info=settings.DEBUG)
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during file generation for '{filepath}': {e}", exc_info=settings.DEBUG)
        return None

# Example usage (for testing, remove later)
# if __name__ == '__main__':
#     from data_models import Task
#     logging.basicConfig(level=logging.DEBUG)

#     test_task = Task(id=101, title="Create Login Script", description="Script to handle user login.", priority="high")
#     generated_path = generate_file_from_task(test_task)
#     print(f"Generated file path: {generated_path}")

#     test_task_md = Task(id=102, title="Write API Docs", description="Document the login endpoint.", priority="medium")
#     generated_path_md = generate_file_from_task(test_task_md)
#     print(f"Generated file path: {generated_path_md}")
