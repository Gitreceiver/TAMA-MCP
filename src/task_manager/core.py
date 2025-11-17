import logging
import os
from typing import List, Optional, Union
from collections import defaultdict
from enum import Enum

class LinkResult(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"


# Using relative imports for robustness within the installed package.
from task_manager.data_models import Task, Subtask, Status, Priority, Dependency
from task_manager.storage_sqlite import load_tasks, save_tasks
from config import settings
from exceptions import ParentTaskNotFoundError
from functools import lru_cache
import datetime

logger = logging.getLogger(__name__)

# --- Task Execution History ---
task_execution_history = []
# Removed lru_cache and cached_get_task_by_id as Pydantic models are not hashable by default

# --- Read Operations ---

def get_task_by_id(tasks: List[Task], task_id_str: str) -> Optional[Union[Task, Subtask]]:
    """Finds a task or subtask by its ID string (e.g., '1' or '1.2')."""
    logger.debug(f"Searching for task/subtask with ID: {task_id_str}")
    
    # Validate ID format
    if not task_id_str or not isinstance(task_id_str, str):
        logger.warning(f"Invalid task ID: must be non-empty string")
        return None
        
    try:
        if '.' in task_id_str:
            parts = task_id_str.split('.')
            if len(parts) != 2 or not parts[0] or not parts[1]:
                logger.warning(f"Invalid subtask ID format: {task_id_str}")
                return None
                
            parent_id = int(parts[0])
            sub_id = int(parts[1])
            
            parent_task = next((t for t in tasks if t.id == parent_id), None)
            if not parent_task:
                logger.debug(f"Parent task {parent_id} not found for subtask {task_id_str}")
                return None
                
            if not parent_task.subtasks:
                logger.debug(f"No subtasks found for parent task {parent_id}")
                return None
                
            subtask = next((st for st in parent_task.subtasks if st.id == sub_id), None)
            if subtask:
                return subtask
            else:
                logger.debug(f"Subtask {sub_id} not found in parent task {parent_id}")
                return None
                
        else:
            task_id = int(task_id_str)
            task = next((t for t in tasks if t.id == task_id), None)
            if not task:
                logger.debug(f"Task {task_id} not found")
            return task
            
    except ValueError:
        logger.warning(f"Invalid task ID format: {task_id_str}")
    except Exception as e:
        logger.error(f"Error finding task '{task_id_str}': {e}", exc_info=settings.DEBUG)
    return None

def find_next_task(tasks: List[Task]) -> Optional[Task]:
    """Finds the next task to work on based on status and dependencies."""
    logger.debug("Finding next available task...")
    completed_ids = set()
    # Build set of completed task/subtask IDs
    for t in tasks:
        if t.status == 'done':
            completed_ids.add(str(t.id))
        if t.subtasks:
            for st in t.subtasks:
                if st.status == 'done':
                    completed_ids.add(f"{t.id}.{st.id}")
            # Also add completed subtasks using "parent.sub" format
            # (Assuming subtask IDs are unique within parent only)
            # if t.subtasks:
            #     for st in t.subtasks:
            #         if st.status == 'done':
            #             completed_ids.add(f"{t.id}.{st.id}") # Need consistent format

    eligible = []
    for task in tasks:
        # Only skip tasks that are already done
        if task.status == 'done':
            continue

        # Enhanced dependency check - needs to handle both task and subtask deps
        deps_met = True
        if task.dependencies:
            for dep_id in task.dependencies:
                if (isinstance(dep_id, int) or (isinstance(dep_id, str) and dep_id.isdigit())) and '.' not in str(dep_id): # Dependency is a main task
                    if str(dep_id) not in completed_ids:
                        deps_met = False
                        break
                elif isinstance(dep_id, str) and '.' in dep_id: # Dependency is a subtask
                    # Find the subtask and check its status (more complex)
                    dep_subtask = get_task_by_id(tasks, dep_id)
                    if not dep_subtask or dep_subtask.status != 'done':
                         deps_met = False
                         break
                else: # Unknown dependency format
                     logger.warning(f"Task {task.id} has unknown dependency format: {dep_id}")
                     deps_met = False
                     break

        if deps_met and task.status == 'pending' and task.status != 'blocked':
            eligible.append(task)

    if not eligible and all(task.status == 'blocked' for task in tasks):
        logger.info("All tasks are blocked, no eligible tasks found.")
        return None
    elif not eligible:
        logger.info("No eligible tasks found to work on next.")
        return None

    priority_map = {"high": 3, "medium": 2, "low": 1}
    # Sort by priority (desc), then ID (asc)
    eligible.sort(key=lambda t: (-priority_map.get(t.priority, 2), t.id))

    next_t = eligible[0]
    logger.info(f"Next task identified: ID {next_t.id} - '{next_t.title}'")
    return next_t

# --- Write Operations ---

def set_task_status(tasks: List[Task], task_id_str: str, new_status: str, propagate: bool = False) -> bool:
    """设置任务或子任务的状态。可选是否级联影响子任务。"""
    logger.info(f"Attempting to set status of '{task_id_str}' to '{new_status}' (propagate={propagate})")
    
    # 校验状态
    if new_status not in Status.__args__:
        logger.error(f"Invalid status '{new_status}'.")
        return False

    item = get_task_by_id(tasks, task_id_str)
    if not item:
        logger.error(f"Item with ID '{task_id_str}' not found for status update.")
        return False

    start_time = datetime.datetime.now()
    old_status = item.status
    
    # 状态未变直接返回
    if old_status == new_status:
        logger.debug(f"Status already set to '{new_status}' for '{task_id_str}'")
        return True

    item.status = new_status
    logger.info(f"Updated status of '{task_id_str}' from '{old_status}' to '{item.status}'")

    # 记录执行历史
    end_time = datetime.datetime.now()
    task_execution_history.append({
        "task_id": task_id_str,
        "old_status": old_status,
        "new_status": new_status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "execution_time": (end_time - start_time).total_seconds(),
        "success": True
    })

    # 处理状态级联
    if isinstance(item, Task) and item.subtasks:
        # 仅当propagate为True时，主任务状态变更同步所有子任务
        if propagate:
            logger.info(f"Propagating '{new_status}' status to subtasks of task {item.id}")
            for subtask in item.subtasks:
                if subtask.status != new_status:
                    subtask.status = new_status
                    logger.debug(f"  - Set subtask {item.id}.{subtask.id} to {new_status}.")
        # 否则不做任何子任务状态变更

    elif isinstance(item, Subtask) and item.status == "done":
        parent_task = next((t for t in tasks if t.id == item.parent_task_id), None)
        if parent_task and parent_task.subtasks:
            all_subs_done = all(st.status == 'done' for st in parent_task.subtasks)
            if all_subs_done and parent_task.status != 'done':
                logger.info(f"All subtasks of Task {parent_task.id} are done. Setting parent to done.")
                parent_task.status = 'done'

    return True

# --- Add Task/Subtask (Manual version, AI version would be in parsing/expansion) ---
def add_new_task(tasks: List[Task], title: str, description: Optional[str] = None, priority: Priority = settings.DEFAULT_PRIORITY, dependencies: List[Dependency] = []) -> Task:
    """Manually adds a new task."""
    logger.info(f"Adding new manual task: '{title}'")
    if not tasks:
         new_id = 1
    else:
         new_id = max(t.id for t in tasks) + 1

    # Validate dependencies exist
    valid_deps = []
    # Removed tuple conversion, call get_task_by_id directly
    for dep_id in dependencies:
        if get_task_by_id(tasks, str(dep_id)): # Use str for consistency
            valid_deps.append(dep_id)
        else:
             logger.warning(f"Dependency '{dep_id}' for new task '{title}' not found. Skipping.")

    new_task = Task(
        id=new_id,
        title=title,
        description=description,
        priority=priority,
        dependencies=valid_deps
        # Other fields use defaults from Pydantic model
    )
    tasks.append(new_task)
    logger.info(f"Added new task with ID {new_id}")
    return new_task

def add_subtask(tasks: List[Task], parent_task_id: int, title: str, description: Optional[str] = None, priority: Priority = settings.DEFAULT_PRIORITY, dependencies: List[Dependency] = []) -> Subtask:
    """Adds a new subtask to an existing task."""
    logger.info(f"Adding new subtask to task {parent_task_id}: '{title}'")
    parent_task = next((t for t in tasks if t.id == parent_task_id), None)
    if not parent_task:
        logger.error(f"Parent task with ID '{parent_task_id}' not found")
        raise ParentTaskNotFoundError(f"Parent task with ID '{parent_task_id}' not found")

    if not parent_task.subtasks:
        new_id = 1
    else:
        new_id = max(st.id for st in parent_task.subtasks) + 1

    # Validate dependencies exist
    valid_deps = []
    # Removed tuple conversion, call get_task_by_id directly
    for dep_id in dependencies:
        if get_task_by_id(tasks, str(dep_id)):  # Use str for consistency
            valid_deps.append(dep_id)
        else:
            logger.warning(f"Dependency '{dep_id}' for new subtask '{title}' not found. Skipping.")

    new_subtask = Subtask(
        id=new_id,
        title=title,
        description=description,
        priority=priority,
        dependencies=valid_deps,
        parent_task_id=parent_task_id
        # Other fields use defaults from Pydantic model
    )
    parent_task.subtasks.append(new_subtask)
    logger.info(f"Added new subtask with ID {parent_task_id}.{new_id}")
    return new_subtask

def find_dependent_tasks(tasks: List[Task], task_id_str: str) -> List[tuple[str, str]]:
    """查找依赖于指定任务的所有任务和子任务。
    
    Args:
        tasks: 任务列表
        task_id_str: 要查找的任务ID (例如: "1" 或 "1.2")
        
    Returns:
        依赖项列表，每项为 (任务ID, 任务标题) 的元组
    """
    dependent_items = []
    
    # 遍历所有任务和子任务，检查依赖关系
    for task in tasks:
        # 检查主任务的依赖
        if task_id_str in task.dependencies:
            dependent_items.append((str(task.id), task.title))
            
        # 检查子任务的依赖
        for subtask in task.subtasks:
            if task_id_str in subtask.dependencies:
                dependent_items.append((f"{task.id}.{subtask.id}", subtask.title))
                
    return dependent_items

def remove_dependency(tasks: List[Task], removed_id: str):
    """从所有任务中移除对指定任务的依赖。
    
    Args:
        tasks: 任务列表
        removed_id: 被删除的任务ID
    """
    for task in tasks:
        # 更新主任务的依赖
        if removed_id in task.dependencies:
            task.dependencies.remove(removed_id)
            
        # 更新子任务的依赖
        for subtask in task.subtasks:
            if removed_id in subtask.dependencies:
                subtask.dependencies.remove(removed_id)

def remove_item(tasks: List[Task], task_id_str: str) -> tuple[bool, List[tuple[str, str]]]:
    """删除任务或子任务，并返回受影响的依赖项。
    
    Args:
        tasks: 任务列表
        task_id_str: 要删除的任务ID (例如: "1" 或 "1.2")
        
    Returns:
        (是否删除成功, 受影响的依赖项列表)
    """
    logger.info(f"Removing item with ID: {task_id_str}")
    
    # 检查并解析任务ID
    if not task_id_str or not isinstance(task_id_str, str):
        logger.error("Invalid task ID: must be a non-empty string")
        return False, []
        
    try:
        # 在删除之前查找依赖项
        dependent_items = find_dependent_tasks(tasks, task_id_str)
        
        # 处理子任务删除
        if '.' in task_id_str:
            parent_id_str, sub_id_str = task_id_str.split('.')
            parent_id = int(parent_id_str)
            sub_id = int(sub_id_str)
            
            # 查找父任务
            parent_task = next((t for t in tasks if t.id == parent_id), None)
            if not parent_task:
                logger.error(f"Parent task {parent_id} not found")
                return False, []
                
            # 删除子任务
            original_length = len(parent_task.subtasks)
            parent_task.subtasks = [st for st in parent_task.subtasks if st.id != sub_id]
            
            if len(parent_task.subtasks) < original_length:
                # 更新其他任务的依赖
                remove_dependency(tasks, task_id_str)
                return True, dependent_items
            return False, []
            
        else:
            # 处理主任务删除
            try:
                task_id = int(task_id_str)
            except ValueError:
                logger.error(f"Invalid task ID format: {task_id_str}")
                return False, []
            
            # 删除主任务
            original_length = len(tasks)
            tasks[:] = [t for t in tasks if t.id != task_id]
            
            if len(tasks) < original_length:
                # 更新其他任务的依赖
                remove_dependency(tasks, task_id_str)
                return True, dependent_items
            return False, []
            
    except ValueError as e:
        logger.error(f"Error parsing task ID: {e}")
        return False, []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, []

def generate_markdown_table_tasks_report(tasks: List[Task]) -> str:
    """Generates a Markdown table representing the task structure."""

    def get_status_emoji(status: str) -> str:
        if status == "done":
            return "✅"
        elif status == "pending":
            return "⚪"
        elif status == "in-progress":
            return "⏳"
        elif status == "blocked":
            return "⛔"
        elif status == "deferred":
            return "📅"
        elif status == "review":
            return "🔍"
        else:
            return ""

    markdown_table = "| 任务 ID | 标题 | 状态 | 优先级 | 依赖任务 | 子任务 |\n"
    markdown_table += "|---|---|---|---|---|---|\n"

    for task in tasks:
        task_id = f"**{task.id}**"
        task_title = task.title
        task_status = get_status_emoji(task.status)  # 使用 Emoji
        task_priority = get_priority_emoji(task.priority)
        task_dependencies = ", ".join(map(str, task.dependencies)) if task.dependencies else ""
        task_subtasks = ", ".join([st.title for st in task.subtasks]) if task.subtasks else ""

        markdown_table += f"| {task_id} | {task_title} | {task_status} | {task_priority} | {task_dependencies} | {task_subtasks} |\n"

        if task.subtasks:
            for subtask in task.subtasks:
                subtask_id = f"{task.id}.{subtask.id}"
                subtask_title = "&nbsp;&nbsp;&nbsp;" + subtask.title  # 缩进子任务
                subtask_status = get_status_emoji(subtask.status) # 使用 Emoji
                subtask_priority = get_priority_emoji(subtask.priority)
                subtask_dependencies = ", ".join(map(str, subtask.dependencies)) if subtask.dependencies else ""

                markdown_table += f"| {subtask_id} | {subtask_title} | {subtask_status} | {subtask_priority} | {subtask_dependencies} |  |\n"

    # Remove the "状态说明" section
    # markdown_table += "\n**状态说明:**\n"
    # markdown_table += "* done: 完成\n"
    # markdown_table += "* pending: 待办\n"
    # markdown_table += "* in-progress: 进行中\n"
    # markdown_table += "* blocked: 阻塞\n"
    # markdown_table += "* deferred: 延期\n"
    # markdown_table += "* review: 审查中\n"
    # markdown_table += "\n**优先级说明:**\n"
    # markdown_table += "* high: 高优先级\n"
    # markdown_table += "* medium: 中优先级\n"
    # markdown_table += "* low: 低优先级\n"

    import datetime
    now = datetime.datetime.now()
    markdown_table += f"\n*最近更新时间: {now.strftime('%Y-%m-%d %H:%M:%S')}*\n"

    return markdown_table

# def generate_mermaid_tasks_diagram(tasks: List[Task]) -> str:
#     """Generates a Mermaid diagram representing the task structure."""
#     mermaid_string = "graph LR\n"
#     for task in tasks:
#         task_id = f"Task{task.id}"
#         task_title = task.title.replace("\"", "'")  # Escape double quotes
#         status_text = f"[状态: {task.status}]"
#         mermaid_string += f"    subgraph {task_id}: {task_title} {status_text}\n"
#         mermaid_string += f"    style {task_id} {get_status_style(task.status)}\n"

#         if task.subtasks:
#             for subtask in task.subtasks:
#                 subtask_id = f"{task_id}.{subtask.id}"
#                 subtask_title = subtask.title.replace("\"", "'")  # Escape double quotes
#                 status_text = f"[状态: {subtask.status}]"
#                 mermaid_string += f"        {subtask_id}({subtask.id}. {subtask_title} {status_text})\n"
#                 mermaid_string += f"    style {subtask_id} {get_status_style(subtask.status)}\n"
#                 mermaid_string += f"        {task_id} --> {subtask_id}\n"
#         mermaid_string += "    end\n"
#     return mermaid_string

def get_priority_emoji(priority: str) -> str:
    if priority == "high":
        return "🔥"
    elif priority == "medium":
        return "⭐"
    elif priority == "low":
        return "⚪"
    else:
        return ""

def get_status_emoji(status: str) -> str:
    """Returns the Mermaid style string for a given task status."""
    if status == "in-progress":
        return "fill:#9f9,stroke:#333,stroke-width:2px"
    elif status == "done":
        return "fill:#ccf,stroke:#333,stroke-width:2px"
    elif status == "blocked":
        return "fill:#fcc,stroke:#333,stroke-width:2px"
    elif status == "deferred":
        return "fill:#ccc,stroke:#333,stroke-width:2px"
    elif status == "review":
        return "fill:#ffc,stroke:#333,stroke-width:2px"
    else:
        return "fill:#f9f,stroke:#333,stroke-width:2px" # Default style for pending

# Add implementations for add_subtask, remove_subtask etc. later
# based on task_manager.test.js requirements

def add_dependency(tasks: List[Task], task_id_str: str, dependency_id: str) -> bool:
    """为指定任务添加依赖项。
    
    Args:
        tasks: 任务列表
        task_id_str: 要添加依赖的任务ID (例如: "1" 或 "1.2")
        dependency_id: 要添加的依赖任务ID (例如: "1" 或 "1.2")
        
    Returns:
        bool: 添加成功返回True，失败返回False
    """
    logger.info(f"Adding dependency {dependency_id} to task {task_id_str}")
    
    # 检查目标任务是否存在
    target_item = get_task_by_id(tasks, task_id_str)
    if not target_item:
        logger.error(f"Target task {task_id_str} not found")
        return False
        
    # 检查依赖任务是否存在
    dep_item = get_task_by_id(tasks, dependency_id)
    if not dep_item:
        logger.error(f"Dependency task {dependency_id} not found")
        return False
        
    # 检查是否已经存在该依赖
    if dependency_id in target_item.dependencies:
        logger.warning(f"Dependency {dependency_id} already exists for task {task_id_str}")
        return False
        
    # 检查是否会造成循环依赖
    temp_deps = target_item.dependencies.copy()
    temp_deps.append(dependency_id)
    if _would_create_cycle(tasks, task_id_str, temp_deps):
        logger.error(f"Adding dependency {dependency_id} would create a circular dependency")
        return False
        
    # 添加依赖
    target_item.dependencies.append(dependency_id)
    logger.info(f"Successfully added dependency {dependency_id} to task {task_id_str}")
    return True

def remove_single_dependency(tasks: List[Task], task_id_str: str, dependency_id: str) -> bool:
    """从指定任务中移除单个依赖项。
    
    Args:
        tasks: 任务列表
        task_id_str: 要移除依赖的任务ID (例如: "1" 或 "1.2")
        dependency_id: 要移除的依赖任务ID (例如: "1" 或 "1.2")
        
    Returns:
        bool: 移除成功返回True，失败返回False
    """
    logger.info(f"Removing dependency {dependency_id} from task {task_id_str}")
    
    # 检查目标任务是否存在
    target_item = get_task_by_id(tasks, task_id_str)
    if not target_item:
        logger.error(f"Target task {task_id_str} not found")
        return False
        
    # 检查依赖是否存在
    if dependency_id not in target_item.dependencies:
        logger.warning(f"Dependency {dependency_id} not found in task {task_id_str}")
        return False
        
    # 移除依赖
    target_item.dependencies.remove(dependency_id)
    logger.info(f"Successfully removed dependency {dependency_id} from task {task_id_str}")
    return True

def _would_create_cycle(tasks: List[Task], task_id: str, new_deps: List[str]) -> bool:
    """检查添加新依赖是否会造成循环依赖。
    
    Args:
        tasks: 任务列表
        task_id: 要检查的任务ID
        new_deps: 新的依赖列表
        
    Returns:
        bool: 如果会造成循环依赖返回True，否则返回False
    """
    # 构建临时依赖图
    graph = defaultdict(set)
    
    # 添加所有现有依赖
    for task in tasks:
        task_id_str = str(task.id)
        for dep in task.dependencies:
            graph[task_id_str].add(str(dep))
            
        # 添加子任务的依赖
        for subtask in task.subtasks:
            subtask_id = f"{task.id}.{subtask.id}"
            for dep in subtask.dependencies:
                graph[subtask_id].add(str(dep))
                
    # 添加新的依赖关系
    for dep in new_deps:
        graph[task_id].add(str(dep))
        
    # 检查是否有循环
    visited = set()
    path = set()
    
    def has_cycle(node: str) -> bool:
        if node in path:
            return True
        if node in visited:
            return False
            
        visited.add(node)
        path.add(node)
        
        for neighbor in graph[node]:
            if has_cycle(neighbor):
                return True
                
        path.remove(node)
        return False
        
    return has_cycle(task_id)

def link_file_to_task(tasks: List[Task], task_id_str: str, file_path: str) -> LinkResult:
    """Links a file path to a specific task or subtask."""
    logger.info(f"Linking file '{file_path}' to task/subtask '{task_id_str}'")

    item = get_task_by_id(tasks, task_id_str)

    if not item:
        logger.error(f"Task/subtask with ID '{task_id_str}' not found.")
        return LinkResult.NOT_FOUND

    if file_path in item.linked_files:
        logger.warning(f"File '{file_path}' is already linked to task/subtask '{task_id_str}'.")
        return LinkResult.ALREADY_EXISTS

    item.linked_files.append(file_path)
    logger.debug(f"Successfully added link for '{task_id_str}'.")
    return LinkResult.SUCCESS

def unlink_file_from_task(tasks: List[Task], task_id_str: str, file_path: str) -> bool:
    """Unlinks a file path from a specific task or subtask."""
    logger.info(f"Unlinking file '{file_path}' from task/subtask '{task_id_str}'")

    item = get_task_by_id(tasks, task_id_str)

    if not item:
        logger.error(f"Task/subtask with ID '{task_id_str}' not found.")
        return False

    # Normalize file paths for comparison
    abs_file_path = os.path.abspath(file_path)

    # Check if the absolute path or the provided path is in the list
    if abs_file_path in item.linked_files:
        item.linked_files.remove(abs_file_path)
        logger.debug(f"Successfully removed link for '{task_id_str}'.")
        return True
    elif file_path in item.linked_files:
        item.linked_files.remove(file_path)
        logger.debug(f"Successfully removed link for '{task_id_str}'.")
        return True
    else:
        logger.warning(f"File '{file_path}' is not linked to task/subtask '{task_id_str}'.")
        return False


def find_tasks_by_file(tasks: List[Task], file_path: str) -> List[Union[Task, Subtask]]:
    """Finds all tasks and subtasks linked to a specific file."""
    logger.info(f"Finding tasks linked to file: {file_path}")
    linked_items = []
    abs_file_path = os.path.abspath(file_path)

    for task in tasks:
        if abs_file_path in task.linked_files:
            linked_items.append(task)
        for subtask in task.subtasks:
            if abs_file_path in subtask.linked_files:
                linked_items.append(subtask)

    return linked_items
