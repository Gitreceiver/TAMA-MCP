import json
import logging
import os
from typing import List, Optional

from pydantic import ValidationError

from task_manager.data_models import TasksData, Task, MetaData
from config import settings

logger = logging.getLogger(__name__)

def load_tasks() -> TasksData:
    """Loads tasks from the JSON file."""
    tasks_path = settings.TASKS_JSON_PATH
    logger.debug(f"Loading tasks from: {tasks_path}")
    try:
        if not os.path.exists(tasks_path):
            logger.warning(f"Tasks file not found: {tasks_path}")
            return TasksData(meta=MetaData(projectName="Test Project", version="1.0"), tasks=[])

        with open(tasks_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            # Deserialize and validate
            tasks_data = TasksData.model_validate(raw_data)
            logger.info(f"Successfully loaded {len(tasks_data.tasks)} tasks.")
            return tasks_data
    except FileNotFoundError:
        logger.error(f"Tasks file not found: {tasks_path}")
        return TasksData(meta=MetaData(projectName="Test Project", version="1.0"), tasks=[])
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in tasks file: {e}")
        return TasksData(meta=MetaData(projectName="Test Project", version="1.0"), tasks=[])
    except ValidationError as e:
        logger.error(f"Validation error loading tasks: {e}")
        return TasksData(meta=MetaData(projectName="Test Project", version="1.0"), tasks=[])
    except Exception as e:
        logger.error(f"Unexpected error loading tasks: {e}", exc_info=settings.DEBUG)
        return TasksData(meta=MetaData(projectName="Test Project", version="1.0"), tasks=[])

def save_tasks(tasks_data: TasksData) -> bool:
    """Saves tasks to the JSON file."""
    tasks_path = settings.TASKS_JSON_PATH
    logger.debug(f"Saving tasks to: {tasks_path}")
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(tasks_path), exist_ok=True)

        # Serialize and write
        with open(tasks_path, "w", encoding="utf-8") as f:
            json.dump(tasks_data.model_dump(by_alias=True), f, indent=2)
        logger.info(f"Successfully saved {len(tasks_data.tasks)} tasks.")
        return True
    except IOError as e:
        logger.error(f"IO error saving tasks: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving tasks: {e}", exc_info=settings.DEBUG)
        return False
