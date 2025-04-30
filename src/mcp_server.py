#!/usr/bin/env python
import logging
import os
import base64
import subprocess
from typing import List, Optional, Union

from mcp.server.fastmcp import FastMCP, Context

# Absolute imports
from task_manager.core import (
    get_task_by_id as core_get_task_by_id,
    find_next_task as core_find_next_task,
    set_task_status as core_set_task_status,
    add_new_task as core_add_new_task,
    add_subtask as core_add_subtask,
    remove_subtask as core_remove_subtask,
)
from task_manager.data_models import Task, Subtask, Status, Priority, Dependency, TasksData
from task_manager.storage import load_tasks, save_tasks
from config import settings

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

# --- State Management (Simple Global Variable Approach) ---

# Determine the task file path
TASK_FILE = settings.TASKS_JSON_PATH
logger.info(f"Using task file: {TASK_FILE}")

# Load initial tasks
if os.path.exists(TASK_FILE):
    tasks_data = load_tasks()
    tasks_list: List[Task] = tasks_data.tasks
    logger.info(f"Loaded {len(tasks_list)} tasks from {TASK_FILE}")
else:
    tasks_list: List[Task] = []
    logger.warning(f"Task file {TASK_FILE} not found. Starting with empty list.")

# Helper to save tasks after modification
def _save_current_tasks():
    try:
        #save_tasks(tasks_list, TASK_FILE)
        tasks_data = TasksData(tasks=tasks_list)
        save_tasks(tasks_data)
        logger.debug(f"Saved {len(tasks_list)} tasks to {TASK_FILE}")
    except Exception as e:
        logger.error(f"Failed to save tasks to {TASK_FILE}: {e}", exc_info=settings.DEBUG)

# --- MCP Server Definition ---
mcp = FastMCP("TAMA Task Manager", description="MCP server for managing TAMA tasks.")

# --- MCP Tools ---

@mcp.tool()
def get_task(task_id_str: str) -> Optional[Union[Task, Subtask]]:
    """
    Finds and returns a task or subtask by its ID string (e.g., '1' or '1.2').
    Returns the task/subtask object or null if not found.
    """
    logger.info(f"[MCP Tool] get_task called with id: {task_id_str}")
    # No state modification, just read from the global list
    return core_get_task_by_id(tasks_list, task_id_str)

@mcp.tool()
def find_next_task() -> Optional[Task]:
    """
    Finds the next available task to work on based on status and dependencies.
    Returns the highest priority, dependency-met task or null if none available.
    """
    logger.info("[MCP Tool] find_next_task called")
    # No state modification
    return core_find_next_task(tasks_list)

@mcp.tool()
def set_task_status(task_id_str: str, new_status: Status) -> bool:
    """
    Sets the status ('todo', 'in_progress', 'done', 'blocked') for a task or subtask.
    Returns true on success, false otherwise (e.g., task not found, invalid status).
    Saves changes on success.
    """
    logger.info(f"[MCP Tool] set_task_status called for id: {task_id_str} to status: {new_status}")
    success = core_set_task_status(tasks_list, task_id_str, new_status)
    if success:
        _save_current_tasks()
    return success

@mcp.tool()
def add_task(
    title: str,
    description: Optional[str] = None,
    priority: Priority = settings.DEFAULT_PRIORITY,
    dependencies: List[Dependency] = []
) -> Optional[Task]:
    """
    Adds a new main task to the list.
    Returns the newly created task object or null on failure.
    Saves changes on success.
    """
    logger.info(f"[MCP Tool] add_task called with title: {title}")
    try:
        new_task = core_add_new_task(tasks_list, title, description, priority, dependencies)
        _save_current_tasks()
        return new_task
    except Exception as e:
        logger.error(f"Error in add_task tool: {e}", exc_info=settings.DEBUG)
        return None

@mcp.tool()
def add_subtask(
    parent_task_id: int,
    title: str,
    description: Optional[str] = None,
    priority: Priority = settings.DEFAULT_PRIORITY,
    dependencies: List[Dependency] = []
) -> Optional[Subtask]:
    """
    Adds a new subtask to the specified parent task ID.
    Returns the newly created subtask object or null on failure (e.g., parent not found).
    Saves changes on success.
    """
    logger.info(f"[MCP Tool] add_subtask called for parent: {parent_task_id} with title: {title}")
    try:
        new_subtask = core_add_subtask(tasks_list, parent_task_id, title, description, priority, dependencies)
        _save_current_tasks()
        return new_subtask
    except ValueError as ve: # Catch specific error for not found parent
        logger.error(f"Error adding subtask: {ve}")
        return None
    except Exception as e:
        logger.error(f"Error in add_subtask tool: {e}", exc_info=settings.DEBUG)
        return None

@mcp.tool()
def remove_subtask(task_id_str: str, subtask_id: int) -> bool:
    """
    Removes a subtask with the given subtask_id from the task specified by task_id_str.
    Returns true on success, false otherwise (e.g., task or subtask not found).
    Saves changes on success.
    """
    logger.info(f"[MCP Tool] remove_subtask called for task: {task_id_str}, subtask: {subtask_id}")
    success = core_remove_subtask(tasks_list, task_id_str, subtask_id)
    if success:
        _save_current_tasks()
    if success:
        _save_current_tasks()
    return success

@mcp.tool()
def get_tasks_table_report() -> str:
    """
    Generates a Markdown table representing the task structure and returns it as a string.
    """
    logger.info("[MCP Tool] get_tasks_table_report called")
    from task_manager.core import generate_markdown_table_tasks_report
    markdown_table = generate_markdown_table_tasks_report(tasks_list)
    return markdown_table

# --- Run the Server ---
if __name__ == "__main__":
    logger.info("Starting TAMA MCP server...")
    # Add necessary dependencies if they aren't automatically picked up (optional)
    # mcp.dependencies = ["pydantic", "rich", ...] # Add if needed
    mcp.run()
    logger.info("TAMA MCP server stopped.")
