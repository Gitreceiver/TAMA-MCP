import logging
import os
from typing import List, Optional, Union

# Use absolute imports
# from .data_models import Task, Subtask, Status, Priority, Dependency # Relative
# from .storage import load_tasks, save_tasks # Relative
# from ..config.settings import settings # Relative
# from ..exceptions import ParentTaskNotFoundError # Relative
from task_manager.data_models import Task, Subtask, Status, Priority, Dependency
from task_manager.storage import load_tasks, save_tasks
from config.settings import settings
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
            completed_ids.add(t.id)
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
                if isinstance(dep_id, int): # Dependency is a main task
                    if dep_id not in completed_ids:
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

        if deps_met and task.status != 'blocked':
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

def set_task_status(tasks: List[Task], task_id_str: str, new_status: str) -> bool:
    """Sets the status of a task or subtask. Modifies the list in-place."""
    logger.info(f"Attempting to set status of '{task_id_str}' to '{new_status}'")
    
    # Validate status first
    if new_status not in Status.__args__:
        logger.error(f"Invalid status '{new_status}'.")
        return False

    item = get_task_by_id(tasks, task_id_str)
    if not item:
        logger.error(f"Item with ID '{task_id_str}' not found for status update.")
        return False

    start_time = datetime.datetime.now()
    old_status = item.status
    
    # Skip if status is already set
    if old_status == new_status:
        logger.debug(f"Status already set to '{new_status}' for '{task_id_str}'")
        return True

    item.status = new_status
    logger.info(f"Updated status of '{task_id_str}' from '{old_status}' to '{item.status}'")

    # Record execution history
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

    # Handle status propagation
    if isinstance(item, Task) and item.status == "done" and item.subtasks:
        logger.info(f"Propagating 'done' status to subtasks of task {item.id}")
        for subtask in item.subtasks:
            if subtask.status != "done":
                subtask.status = "done"
                logger.debug(f"  - Set subtask {item.id}.{subtask.id} to done.")

    elif isinstance(item, Subtask) and item.status == "done":
        parent_task = next((t for t in tasks if t.id == item.parent_task_id), None)
        if parent_task and parent_task.subtasks:
            all_subs_done = all(st.status == 'done' for st in parent_task.subtasks)
            if all_subs_done and parent_task.status != 'done':
                logger.info(f"All subtasks of Task {parent_task.id} are done. Setting parent to done.")
                parent_task.status = 'done'
                # Recursively check if this affects parent's parent
                if parent_task.parent_task_id:  # If parent is also a subtask
                    set_task_status(tasks, str(parent_task.parent_task_id), 'done')

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


def remove_subtask(tasks: List[Task], task_id_str: str, subtask_id: int) -> bool:
    """Removes a subtask from a task."""
    logger.info(f"Removing subtask {subtask_id} from task {task_id_str}")
    task = get_task_by_id(tasks, task_id_str)
    if not task or not task.subtasks:
        logger.error(f"Task with ID '{task_id_str}' not found or has no subtasks.")
        return False

    original_length = len(task.subtasks)
    task.subtasks = [st for st in task.subtasks if st.id != subtask_id]
    if len(task.subtasks) < original_length:
        logger.info(f"Removed subtask {subtask_id} from task {task_id_str}")
        return True
    else:
        logger.error(f"Subtask with ID '{subtask_id}' not found in task '{task_id_str}'.")
        return False

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
