from typing import List, Optional, Union
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
# from rich.tree import Tree # No longer using Tree for details

from task_manager.data_models import Task, Subtask

console = Console()

def get_status_color(status: str) -> str:
    """Return a color based on status."""
    return {
        "pending": "yellow",
        "in-progress": "blue",
        "done": "green",
        "blocked": "red",
        "deferred": "grey70",
        "review": "magenta"
    }.get(status, "white")

def get_priority_color(priority: str) -> str:
    """Return a color based on priority."""
    return {
        "high": "red",
        "medium": "yellow",
        "low": "green"
    }.get(priority, "white")

def get_dep_str(deps: List[Union[int, str]]) -> str:
    """Format dependencies list for display."""
    return ", ".join(str(d) for d in deps) if deps else "None"

def display_tasks_table(tasks: List[Task], status_filter: Optional[str] = None, priority_filter: Optional[str] = None):
    """Display tasks in a rich table format with optional filters."""
    if not tasks:
        console.print("\n[bold]No tasks found.[/bold]\n")
        return

    table = Table(show_header=True, header_style="bold", title="Tasks") # Add a main title for clarity
    table.add_column("ID", style="dim")
    table.add_column(header="Title") # Explicitly use header= parameter
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Dependencies")
    table.add_column("Subtasks", justify="right")

    for task in tasks:
        # Filter subtasks first
        filtered_subtasks = []
        if task.subtasks:
            filtered_subtasks = [
                st for st in task.subtasks
                if (not status_filter or st.status == status_filter)
            ]

        # Determine if the main task should be shown
        task_matches = (not status_filter or task.status == status_filter) and \
                       (not priority_filter or task.priority == priority_filter)

        # Show the task if it matches or if it has subtasks that match
        if task_matches or filtered_subtasks:
            # Format status with color
            status_str = f"[{get_status_color(task.status)}]{task.status}[/]"
            priority_str = f"[{get_priority_color(task.priority)}]{task.priority}[/]"

            table.add_row(
                str(task.id),
                task.title,
                status_str,
                priority_str,
                get_dep_str(task.dependencies),
                str(len(task.subtasks))
            )

            # Add subtasks with indentation if they exist
            subtasks_to_display = filtered_subtasks if (status_filter or priority_filter) else task.subtasks
            for subtask in subtasks_to_display:
                subtask_status = f"[{get_status_color(subtask.status)}]{subtask.status}[/]"
                table.add_row(
                    f"└─ {task.id}.{subtask.id}",
                    f"  {subtask.title}",
                    subtask_status,
                    "N/A",
                    get_dep_str(subtask.dependencies),
                    ""
                )

    console.print("\n[bold]Tasks:[/bold]")
    console.print(table)
    console.print()

def display_task_details(item: Union[Task, Subtask]):
    """Display detailed information about a task or subtask."""
    is_subtask = isinstance(item, Subtask)
    item_id = f"{item.parent_task_id}.{item.id}" if is_subtask else str(item.id)
    title = f"[bold]Details for {'Subtask' if is_subtask else 'Task'} {item_id}: {item.title}[/]"

    renderables = []

    # --- Basic Info ---
    basic_info_table = Table.grid(padding=(0, 1))
    basic_info_table.add_column()
    basic_info_table.add_column()
    basic_info_table.add_row("[bold]Status:[/]", f"[{get_status_color(item.status)}]{item.status}[/]")
    if not is_subtask:
        basic_info_table.add_row("[bold]Priority:[/]", f"[{get_priority_color(item.priority)}]{item.priority}[/]")
    renderables.append(Panel(basic_info_table, title="📋 Basic Information", title_align="left", border_style="blue"))

    # --- Description ---
    if item.description:
        renderables.append(Panel(Text(item.description, justify="left"), title="📝 Description", title_align="left", border_style="blue"))

    # --- Dependencies ---
    if item.dependencies:
         renderables.append(Panel(get_dep_str(item.dependencies), title="🔗 Dependencies", title_align="left", border_style="blue"))

    # --- Linked Files ---
    if item.linked_files:
        linked_files_str = "\n".join([f"- {file}" for file in item.linked_files])
        renderables.append(Panel(linked_files_str, title="📎 Linked Files", title_align="left", border_style="blue"))


    # --- Additional Details ---
    if item.details:
        renderables.append(Panel(Text(item.details, justify="left"), title="ℹ️ Additional Details", title_align="left", border_style="blue"))

    # --- Test Strategy (Tasks only) ---
    if not is_subtask and item.test_strategy:
        renderables.append(Panel(Text(item.test_strategy, justify="left"), title="🧪 Test Strategy", title_align="left", border_style="blue"))

    # --- Subtasks (Tasks only) ---
    if not is_subtask and hasattr(item, 'subtasks') and item.subtasks:
        subtask_table = Table(show_header=False, box=None, padding=0)
        subtask_table.add_column("ID", style="dim")
        subtask_table.add_column("Title")
        subtask_table.add_column("Status")
        for st in item.subtasks:
            status_str = f"[{get_status_color(st.status)}]{st.status}[/]"
            subtask_table.add_row(f"{item.id}.{st.id}", st.title, status_str)
        renderables.append(Panel(subtask_table, title=f"📑 Subtasks ({len(item.subtasks)})", title_align="left", border_style="blue"))

    # Group all renderables under the main title panel
    console.print(Panel(Group(*renderables), title=title, border_style="green", expand=False))
    console.print()
