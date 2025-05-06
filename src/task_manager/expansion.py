import logging
import json
from typing import Optional, List

# Use absolute imports
import task_manager.storage as storage
import task_manager.core as core
from task_manager.data_models import TasksData, Task, Subtask
import ai.client as ai_client
import ai.prompts as prompts
from config import settings
from exceptions import AIResponseParsingError

logger = logging.getLogger(__name__)

def expand_and_save(parent_task_id_str: str) -> bool:
    """
    Expands a given task into subtasks using AI, validates, and saves them.

    Args:
        parent_task_id_str: The ID string of the parent task to expand (e.g., '3').

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Starting task expansion process for parent task ID: {parent_task_id_str}")

    # 1. Load existing tasks
    try:
        tasks_data = storage.load_tasks()
    except Exception as e:
        # load_tasks should log details
        logger.error(f"Failed to load tasks for expansion: {e}")
        return False

    # 2. Find the parent task
    parent_task = core.get_task_by_id(tasks_data.tasks, parent_task_id_str)

    if not parent_task:
        logger.error(f"Parent task with ID '{parent_task_id_str}' not found for expansion.")
        return False
    # Check if the ID indicates a subtask (contains '.') - prevent expanding subtasks directly
    if '.' in parent_task_id_str:
        logger.error(f"Item with ID '{parent_task_id_str}' is a subtask, cannot expand directly.")
        return False
    # The isinstance check was incorrect and is removed. get_task_by_id handles finding the Task object.

    if parent_task.status == 'done':
        logger.warning(f"Task '{parent_task_id_str}' is already marked as done. Skipping expansion.")
        # Or maybe allow expansion anyway? For now, skip.
        return False # Indicate no action taken, but not necessarily an error

    logger.debug(f"Found parent task: {parent_task.title}")

    # 3. Determine the next subtask ID
    next_sub_id = 1
    if parent_task.subtasks:
        next_sub_id = max(st.id for st in parent_task.subtasks) + 1
    logger.debug(f"Next subtask ID will be: {next_sub_id}")

    # 4. Prepare context for AI (can be enhanced)
    # Simple context for now: parent task details
    context = f"Parent Task Title: {parent_task.title}\nParent Task Description: {parent_task.description or 'N/A'}\nParent Task Priority: {parent_task.priority}\nExisting Subtasks Count: {len(parent_task.subtasks)}"
    # TODO: Consider adding project meta, related tasks, etc. for better context

    # 5. Call AI to generate subtasks
    generated_json_str = ai_client.expand_task_with_ai(
        task_title=parent_task.title,
        task_description=parent_task.description,
        context=context
    )

    if not generated_json_str:
        logger.error(f"AI failed to generate subtasks for task '{parent_task_id_str}'.")
        return False

    # 6. Parse the JSON response (expecting a list of subtask-like dicts)
    try:
        # --- Modification Start: Robust JSON Extraction ---
        extracted_json_str = None
        if generated_json_str: # Ensure we have a string to work with
            try:
                # Find the start of the JSON list
                start_index = generated_json_str.find('[')
                # Find the end of the JSON list (last closing bracket)
                end_index = generated_json_str.rfind(']')
                
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    extracted_json_str = generated_json_str[start_index : end_index + 1].strip()
                    # Basic check if it looks like a list
                    if not extracted_json_str.startswith('['):
                        extracted_json_str = None # Reset if the extracted part doesn't start correctly
                else:
                    logger.debug(f"Could not find valid JSON list structure ('[...]') in raw AI response: {generated_json_str[:200]}...")
            except Exception as e:
                logger.warning(f"Error during JSON extraction attempt in expansion.py: {e}")
                extracted_json_str = None

        if not extracted_json_str:
             # Raise or handle the error if extraction failed
             raise AIResponseParsingError(f"Could not extract a valid JSON list from AI response: {generated_json_str[:200]}...")
        # --- Modification End ---

        # Now parse the *extracted* JSON string
        generated_subtasks_data = json.loads(extracted_json_str)
        if not isinstance(generated_subtasks_data, list):
            # This check might be redundant now but kept for safety
            raise AIResponseParsingError("Extracted JSON is not a list.")
        logger.debug(f"Successfully parsed JSON list response from AI. Found {len(generated_subtasks_data)} potential subtasks.")
    except (json.JSONDecodeError, AIResponseParsingError) as e:
        logger.error(f"Failed to parse JSON list response from AI for subtasks: {e}")
        # Log the original string if parsing the extracted one failed
        logger.debug(f"Original Invalid JSON received: {generated_json_str[:500]}...") 
        return False

    # 7. Validate and process generated subtasks
    newly_added_subtasks: List[Subtask] = []
    # 构建标题到完整ID的映射，便于依赖项转换
    title_to_full_id = {}
    for i, sub_data in enumerate(generated_subtasks_data):
        sub_id = next_sub_id + i
        full_id = f"{parent_task.id}.{sub_id}"
        title_to_full_id[sub_data['title']] = full_id

    for i, sub_data in enumerate(generated_subtasks_data):
        # 修正 dependencies 字段，将标题依赖转换为完整ID
        if 'dependencies' in sub_data and sub_data['dependencies']:
            new_deps = []
            for dep in sub_data['dependencies']:
                # 如果依赖项是标题字符串且能在 title_to_full_id 里找到，替换为完整 id
                if isinstance(dep, str) and dep in title_to_full_id:
                    new_deps.append(title_to_full_id[dep])
                else:
                    new_deps.append(dep)
            sub_data['dependencies'] = new_deps
        try:
            # Add the essential parent_task_id and assign a new ID
            sub_data['parent_task_id'] = parent_task.id
            sub_data['id'] = next_sub_id + i
            # Validate using the Subtask model
            # Note: AI might return extra fields, Pydantic should ignore them by default
            validated_subtask = Subtask.model_validate(sub_data)
            # Set default status if not provided by AI (though prompt asks not to)
            if 'status' not in sub_data:
                 validated_subtask.status = 'pending'
            newly_added_subtasks.append(validated_subtask)
            logger.debug(f"Validated and processed generated subtask: {validated_subtask.title}")
        except Exception as e: # Catch Pydantic's ValidationError etc.
            logger.warning(f"Validation failed for generated subtask data: {e}. Skipping subtask: {sub_data.get('title', 'N/A')}", exc_info=settings.DEBUG)
            # Continue processing other generated subtasks

    if not newly_added_subtasks:
        logger.warning("AI generated subtasks, but none were valid after validation.")
        return False # Indicate that no valid subtasks were added

    # 8. Append validated subtasks to the parent task
    if not parent_task.subtasks:
        parent_task.subtasks = []
    parent_task.subtasks.extend(newly_added_subtasks)
    logger.info(f"Added {len(newly_added_subtasks)} new subtasks to task '{parent_task_id_str}'.")

    # 9. Save the updated tasks data
    try:
        storage.save_tasks(tasks_data)
        logger.info(f"Successfully saved updated tasks with new subtasks for task '{parent_task_id_str}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to save tasks after adding subtasks: {e}")
        return False

# Example usage (for testing, remove later)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
#     # Assume tasks.json exists and has a task with ID 3
#     # Ensure you have a .env file with DEEPSEEK_API_KEY
#     parent_id_to_expand = "3"
#     print(f"\nAttempting to expand task {parent_id_to_expand}...")
#     success = expand_and_save(parent_id_to_expand)
#     print(f"Task Expansion Successful: {success}")
#     # Check tasks.json for new subtasks under task 3
