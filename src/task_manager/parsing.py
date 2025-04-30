import logging
import json
from typing import Optional

# Use absolute imports
import task_manager.storage as storage
from task_manager.data_models import TasksData, Task
import ai.client as ai_client
import ai.prompts as prompts
from config import settings

logger = logging.getLogger(__name__)

def parse_prd_and_save(prd_filepath: str) -> bool:
    """
    Reads a PRD file, uses AI to generate tasks, validates, and saves them.

    Args:
        prd_filepath: Path to the Product Requirements Document file.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Starting PRD parsing process for file: {prd_filepath}")

    # 1. Read PRD file content
    try:
        with open(prd_filepath, 'r', encoding='utf-8') as f:
            prd_content = f.read()
        if not prd_content.strip():
            logger.error(f"PRD file '{prd_filepath}' is empty.")
            return False
        logger.debug(f"Successfully read PRD content from '{prd_filepath}'.")
    except FileNotFoundError:
        logger.error(f"PRD file not found: {prd_filepath}")
        return False
    except Exception as e:
        logger.exception(f"Error reading PRD file '{prd_filepath}': {e}", exc_info=settings.DEBUG)
        return False

    # 2. Call AI to generate tasks
    prompt = prompts.get_generate_tasks_prompt(prd_content)
    # Assuming generate_tasks_from_prd uses the correct prompt internally now
    generated_json_str = ai_client.generate_tasks_from_prd(prd_content) # Pass content, not prompt

    if not generated_json_str:
        logger.error("AI failed to generate task structure from PRD.")
        return False

    # 3. Parse the JSON response string
    try:
        generated_data = json.loads(generated_json_str)
        logger.debug("Successfully parsed JSON response from AI.")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from AI: {e}")
        logger.debug(f"Invalid JSON received: {generated_json_str[:500]}...") # Log snippet
        return False

    # 4. Validate the parsed data using Pydantic model
    try:
        # --- Modification Start: Handle missing projectName --- 
        if isinstance(generated_data, dict):
            if 'meta' not in generated_data:
                logger.warning("AI response missing 'meta' object. Adding default.")
                generated_data['meta'] = {}
            if isinstance(generated_data.get('meta'), dict) and 'projectName' not in generated_data['meta']:
                logger.warning("AI response missing 'projectName' in 'meta'. Adding default 'Unknown Project'.")
                generated_data['meta']['projectName'] = "Unknown Project"
            # Add similar check for 'version' if needed
            if isinstance(generated_data.get('meta'), dict) and 'version' not in generated_data['meta']:
                 logger.warning("AI response missing 'version' in 'meta'. Adding default '1.0'.")
                 generated_data['meta']['version'] = "1.0"
        else:
            # Handle case where generated_data is not a dict (e.g., it's a list)
            logger.error(f"AI generated data is not a dictionary as expected for TasksData: {type(generated_data)}")
            # Optionally, try to wrap it if it's a list of tasks?
            # For now, let validation fail
            pass 
        # --- Modification End ---

        # Use model_validate for Pydantic v2
        tasks_data = TasksData.model_validate(generated_data)
        logger.info(f"Successfully validated generated task data for project '{tasks_data.meta.project_name}'. Found {len(tasks_data.tasks)} top-level tasks.")
    except Exception as e: # Catch Pydantic's ValidationError and potentially others
        logger.exception(f"Validation failed for AI-generated task data: {e}", exc_info=settings.DEBUG)
        logger.debug(f"Data that failed validation: {generated_data}")
        return False

    # 5. Add any post-processing logic (Optional - skip for now)
    #    e.g., refining dependencies, checking consistency

    # 6. Save the validated tasks
    try:
        existing_tasks_data = storage.load_tasks()
        new_tasks = []
        from task_manager.data_models import Task # Import Task specifically here
        for task in tasks_data.tasks:
            existing = next((t for t in existing_tasks_data.tasks if t.id == task.id), None)
            if existing is None:
                new_tasks.append(task)
            else:
                # Task exists, check subtasks
                if isinstance(task, Task) and task.subtasks and isinstance(existing, Task):
                    existing_subtask_ids = {st.id for st in existing.subtasks}
                    new_subtasks = [st for st in task.subtasks if st.id not in existing_subtask_ids]
                    existing.subtasks.extend(new_subtasks)
        existing_tasks_data.tasks.extend(new_tasks)
        storage.save_tasks(existing_tasks_data)
        logger.info(f"Successfully saved generated tasks to '{settings.TASKS_JSON_PATH}'.")
        return True
    except Exception as e:
        # save_tasks already logs exceptions, but we log context here
        logger.error(f"Failed to save the generated tasks: {e}")
        return False

# Example usage (for testing, remove later)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
#     # Create a dummy PRD file
#     dummy_prd_path = "dummy_prd.txt"
#     with open(dummy_prd_path, "w") as f:
#         f.write("Feature: User Login\nAs a user, I want to log in with email and password.")
#     # Ensure you have a .env file with DEEPSEEK_API_KEY
#     success = parse_prd_and_save(dummy_prd_path)
#     print(f"PRD Parsing Successful: {success}")
#     # Check tasks.json
