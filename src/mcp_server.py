#!/usr/bin/env python
import logging
import os
import base64
import subprocess
from typing import List, Optional, Union, Tuple

from mcp.server.fastmcp import FastMCP, Context

# Absolute imports
from task_manager.core import (
    get_task_by_id as core_get_task_by_id,
    find_next_task as core_find_next_task,
    set_task_status as core_set_task_status,
    add_new_task as core_add_new_task,
    add_subtask as core_add_subtask,
    remove_item as core_remove_item,
    add_dependency as core_add_dependency,
    remove_single_dependency as core_remove_single_dependency,
)
from task_manager.data_models import Task, Subtask, Status, Priority, Dependency, TasksData
from task_manager.storage import load_tasks, save_tasks
from task_manager.dependencies import find_circular_dependencies
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
        tasks_data = TasksData(tasks=tasks_list)
        save_tasks(tasks_data)
        logger.debug(f"Saved {len(tasks_list)} tasks to {TASK_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save tasks to {TASK_FILE}: {e}", exc_info=settings.DEBUG)
        return False

# --- MCP Server Definition ---
mcp = FastMCP("TAMA Task Manager", description="MCP server for managing TAMA tasks.")

# --- Task Management Tools ---

@mcp.tool()
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> str:
    """
    列出所有任务，可选按状态或优先级过滤，返回markdown格式的列表。
    
    Args:
        status: 可选的状态过滤 (pending, in-progress, done, deferred, blocked, review)
        priority: 可选的优先级过滤 (high, medium, low)
        
    Returns:
        markdown格式的任务列表字符串
    """
    filtered_tasks = tasks_list.copy()
    
    if status:
        filtered_tasks = [t for t in filtered_tasks if t.status == status]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
    
    # 状态对应的emoji
    status_emoji = {
        "done": "✅",
        "pending": "⚪",
        "in-progress": "⏳",
        "blocked": "⛔",
        "deferred": "📅",
        "review": "🔍"
    }
    
    # 优先级对应的emoji
    priority_emoji = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    
    # 生成markdown格式的列表
    markdown = "# 任务列表\n\n"
    
    # 添加过滤信息
    filters = []
    if status:
        filters.append(f"状态: {status_emoji.get(status, '')} {status}")
    if priority:
        filters.append(f"优先级: {priority_emoji.get(priority, '')} {priority}")
    if filters:
        markdown += "**过滤条件:** " + ", ".join(filters) + "\n\n"
    
    if not filtered_tasks:
        markdown += "*没有找到符合条件的任务*\n"
        return markdown
    
    # 添加表头
    markdown += "| ID | 标题 | 状态 | 优先级 | 依赖项 | 子任务数 |\n"
    markdown += "|:---|:-----|:-----|:-------|:-------|:---------|\n"
    
    # 添加任务行
    for task in filtered_tasks:
        task_id = str(task.id)
        title = task.title
        status = f"{status_emoji.get(task.status, '')} {task.status}"
        priority = f"{priority_emoji.get(task.priority, '')} {task.priority}"
        dependencies = ", ".join(map(str, task.dependencies)) if task.dependencies else "-"
        subtasks_count = len(task.subtasks)
        
        markdown += f"| {task_id} | {title} | {status} | {priority} | {dependencies} | {subtasks_count} |\n"
        
        # 添加子任务（缩进显示）
        for subtask in task.subtasks:
            subtask_id = f"{task.id}.{subtask.id}"
            subtask_title = f"└─ {subtask.title}"
            subtask_status = f"{status_emoji.get(subtask.status, '')} {subtask.status}"
            subtask_priority = f"{priority_emoji.get(subtask.priority, '')} {subtask.priority}"
            subtask_deps = ", ".join(map(str, subtask.dependencies)) if subtask.dependencies else "-"
            
            markdown += f"| {subtask_id} | {subtask_title} | {subtask_status} | {subtask_priority} | {subtask_deps} | - |\n"
    
    return markdown

@mcp.tool()
def show_task(task_id: str) -> Optional[Union[Task, Subtask]]:
    """
    显示指定任务或子任务的详细信息。
    
    Args:
        task_id: 任务或子任务的ID (例如: "1" 或 "1.2")
        
    Returns:
        任务或子任务对象，如果未找到则返回None
    """
    return core_get_task_by_id(tasks_list, task_id)

@mcp.tool()
def set_status(task_id: str, new_status: str) -> bool:
    """
    设置任务或子任务的状态。
    
    Args:
        task_id: 任务或子任务的ID (例如: "1" 或 "1.2")
        new_status: 新状态 (pending, in-progress, done, deferred, blocked, review)
        
    Returns:
        更新成功返回True，失败返回False
    """
    if core_set_task_status(tasks_list, task_id, new_status):
        return _save_current_tasks()
    return False

@mcp.tool()
def next_task() -> Optional[Task]:
    """
    查找下一个可执行的任务。
    
    Returns:
        下一个可执行的任务，如果没有则返回None
    """
    return core_find_next_task(tasks_list)

@mcp.tool()
def add_task(
    title: str,
    description: Optional[str] = None,
    priority: Priority = settings.DEFAULT_PRIORITY,
    dependencies: List[Dependency] = []
) -> Optional[Task]:
    """
    添加新的主任务。
    
    Args:
        title: 任务标题
        description: 可选的任务描述
        priority: 任务优先级 (high, medium, low)
        dependencies: 依赖任务ID列表
        
    Returns:
        新创建的任务对象，失败返回None
    """
    try:
        new_task = core_add_new_task(tasks_list, title, description, priority, dependencies)
        if _save_current_tasks():
            return new_task
        return None
    except Exception as e:
        logger.error(f"Error in add_task tool: {e}", exc_info=settings.DEBUG)
        return None

@mcp.tool()
def add_subtask(
    parent_id: str,
    title: str,
    description: Optional[str] = None,
    priority: Priority = settings.DEFAULT_PRIORITY,
    dependencies: List[Dependency] = []
) -> Optional[Subtask]:
    """
    添加子任务。
    
    Args:
        parent_id: 父任务ID
        title: 子任务标题
        description: 可选的子任务描述
        priority: 子任务优先级 (high, medium, low)
        dependencies: 依赖任务ID列表
        
    Returns:
        新创建的子任务对象，失败返回None
    """
    try:
        parent_id_int = int(parent_id)
        new_subtask = core_add_subtask(tasks_list, parent_id_int, title, description, priority, dependencies)
        if _save_current_tasks():
            return new_subtask
        return None
    except Exception as e:
        logger.error(f"Error in add_subtask tool: {e}", exc_info=settings.DEBUG)
        return None

@mcp.tool()
def remove_item(task_id: str) -> Tuple[bool, List[Tuple[str, str]]]:
    """
    删除任务或子任务。
    
    Args:
        task_id: 要删除的任务或子任务ID (例如: "1" 或 "1.2")
        
    Returns:
        (是否删除成功, 受影响的依赖项列表)
    """
    success, affected_deps = core_remove_item(tasks_list, task_id)
    if success:
        if _save_current_tasks():
            return True, affected_deps
    return False, []

@mcp.tool()
def add_dependency(task_id: str, dependency_id: str) -> bool:
    """
    为任务添加依赖项。
    
    Args:
        task_id: 要添加依赖的任务ID (例如: "1" 或 "1.2")
        dependency_id: 要添加的依赖任务ID (例如: "1" 或 "1.2")
        
    Returns:
        添加成功返回True，失败返回False
    """
    if core_add_dependency(tasks_list, task_id, dependency_id):
        return _save_current_tasks()
    return False

@mcp.tool()
def remove_dependency(task_id: str, dependency_id: str) -> bool:
    """
    从任务中移除依赖项。
    
    Args:
        task_id: 要移除依赖的任务ID (例如: "1" 或 "1.2")
        dependency_id: 要移除的依赖任务ID (例如: "1" 或 "1.2")
        
    Returns:
        移除成功返回True，失败返回False
    """
    if core_remove_single_dependency(tasks_list, task_id, dependency_id):
        return _save_current_tasks()
    return False

@mcp.tool()
def check_dependencies() -> Optional[List[str]]:
    """
    检查任务中是否存在循环依赖。
    
    Returns:
        如果存在循环依赖，返回循环路径；否则返回None
    """
    return find_circular_dependencies(tasks_list)

# --- Run the Server ---
if __name__ == "__main__":
    logger.info("Starting TAMA MCP server...")
    # Add necessary dependencies if they aren't automatically picked up (optional)
    # mcp.dependencies = ["pydantic", "rich", ...] # Add if needed
    mcp.run()
    logger.info("TAMA MCP server stopped.")
