import typer
from typing import List, Optional
import logging
import os
from rich.panel import Panel
import task_manager.storage as storage
import task_manager.core as core
import task_manager.data_models as data_models
import task_manager.parsing as parsing
import task_manager.expansion as expansion
import task_manager.dependencies as dependencies
import task_manager.complexity as complexity
import task_manager.file_generator as file_generator
import cli.ui as ui
from config.settings import settings
from exceptions import ParentTaskNotFoundError # Import exception

# Configure logging
# Set default console level to WARNING to reduce verbosity
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# You can still control the overall application log level via settings if needed,
# for example, by adding a FileHandler with level=settings.LOG_LEVEL.upper()
# Example (add later if file logging is desired):
# if settings.LOG_FILE:
#     file_handler = logging.FileHandler(settings.LOG_FILE)
#     file_handler.setLevel(settings.LOG_LEVEL.upper())
#     file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logging.getLogger().addHandler(file_handler) # Add handler to root logger

app = typer.Typer(help="AI-Powered Task Manager CLI")

def load_task_data() -> data_models.TasksData:
    """Loads task data, handling potential errors."""
    try:
        tasks_data = storage.load_tasks()
        logger.debug(f"Loaded {len(tasks_data.tasks)} tasks.")
        return tasks_data
    except FileNotFoundError:
        logger.warning(f"Tasks file '{settings.TASKS_JSON_PATH}' not found. Starting with empty list.")
        # Return default structure if file not found
        return data_models.TasksData(meta=data_models.MetaData(projectName=settings.PROJECT_NAME), tasks=[])
    except Exception as e:
        ui.console.print(f"[bold red]Error loading tasks: {e}[/]")
        logger.exception("Failed to load tasks.", exc_info=settings.DEBUG)
        raise typer.Exit(code=1)

def save_task_data(tasks_data: data_models.TasksData):
    """Saves task data, handling potential errors."""
    try:
        storage.save_tasks(tasks_data)
        logger.debug(f"Saved {len(tasks_data.tasks)} tasks.")
    except Exception as e:
        ui.console.print(f"[bold red]Error saving tasks: {e}[/]")
        logger.exception("Failed to save tasks.", exc_info=settings.DEBUG)
        raise typer.Exit(code=1)


@app.command(name="list", help="List tasks, optionally filtering by status or priority.")
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by task status (e.g., pending, done)."),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by task priority (e.g., high, medium).")
):
    """Lists tasks with optional filtering."""
    logger.info(f"Listing tasks with filters: status='{status}', priority='{priority}'")
    tasks_data = load_task_data()
    ui.display_tasks_table(tasks_data.tasks, status_filter=status, priority_filter=priority)

@app.command(help="Show details for a specific task or subtask.")
def show(
    task_id: str = typer.Argument(..., help="The ID of the task or subtask (e.g., '1' or '1.2').")
):
    """Shows details for a specific task or subtask."""
    logger.info(f"Showing details for task/subtask ID: {task_id}")
    tasks_data = load_task_data()
    item = core.get_task_by_id(tasks_data.tasks, task_id)
    if item:
        # Also display complexity
        ui.display_task_details(item)
        if isinstance(item, data_models.Task):
            estimated_comp = complexity.estimate_complexity(item)
            ui.console.print(f"[bold]Estimated Complexity:[/bold] {estimated_comp}") # Display complexity after details
        elif isinstance(item, data_models.Subtask):
            estimated_comp = complexity.estimate_complexity(item)
            ui.console.print(f"[bold]Estimated Complexity:[/bold] {estimated_comp}")
        else:
            ui.console.print(f"[bold]Estimated Complexity:[/bold] N/A")
    else:
        ui.console.print(f"不存在id为 {task_id} 的 task") # User requested message
        logger.warning(f"Task/subtask ID '{task_id}' not found for show command.")
        raise typer.Exit(code=1)

@app.command(name="status", help="Set the status for a task or subtask.")
def set_status_command(
    task_id: str = typer.Argument(..., help="The ID of the task or subtask to update (e.g., '1' or '1.2')."),
    new_status: str = typer.Argument(..., help=f"New status ({', '.join(data_models.Status.__args__)})")
):
    """Sets the status for a specified task/subtask."""
    logger.info(f"Attempting to set status to '{new_status}' for ID: {task_id}")
    # Validate status input against the Literal type
    if new_status not in data_models.Status.__args__:
        # Keep error message concise 
        ui.console.print(Panel(f"[bold red]Invalid status '{new_status}'.[/bold red]\nValid statuses are: {', '.join(data_models.Status.__args__)}", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)

    tasks_data = load_task_data()
    item = core.get_task_by_id(tasks_data.tasks, task_id)
    if not item:
        ui.console.print(Panel(f"[bold red]Task '{task_id}' not found.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)

    # --- Get old status BEFORE updating --- 
    old_status = item.status
    # --- 

    # Prevent updating if status is the same
    if old_status == new_status:
        ui.console.print(Panel(f"Status for '{task_id}' is already '{new_status}'. No update needed.", title="Status Update", border_style="yellow"))
        raise typer.Exit()

    if core.set_task_status(tasks_data.tasks, task_id, new_status):
        save_task_data(tasks_data)
        # --- Optimized Output with old/new status ---
        ui.console.print(Panel(f"Status for '{task_id}' changed from [yellow]'{old_status}'[/yellow] to [green]'{new_status}'[/green].", title="[bold green]✅ Status Updated[/bold green]", border_style="green"))
        # --- 
    else:
        # Error message should have been logged by core.set_task_status
        ui.console.print(Panel(f"[bold red]Failed to update status for '{task_id}'. Check logs.[/bold red]", title="[bold red]❌ Update Failed[/bold red]", border_style="red")) 
        raise typer.Exit(code=1)


@app.command(name="next", help="Show the next eligible task to work on.")
def next_task():
    """Finds and displays the next eligible task."""
    logger.info("Finding the next eligible task.")
    tasks_data = load_task_data()
    next_t = core.find_next_task(tasks_data.tasks)
    if next_t:
        ui.console.print("[bold green]Next eligible task:[/bold green]")
        ui.display_task_details(next_t)
    else:
        ui.console.print("✅ No eligible tasks found to work on right now.")
        logger.info("No eligible tasks found.")

@app.command(name="add", help="Add a new task or subtask.") 
def add_command(
    title: str = typer.Argument(..., help="The title of the task or subtask."),
    # --- Add parent option --- 
    parent_id: Optional[str] = typer.Option(None, "--parent", "-p", help="ID of the parent task to add a subtask to."),
    # --- Add other options corresponding to core functions ---
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description for the task/subtask."),
    priority: Optional[str] = typer.Option(None, "--priority", help=f"Priority ({', '.join(data_models.Priority.__args__)}). Default: {settings.DEFAULT_PRIORITY}"),
    # TODO: Add dependency parsing later
    # dependencies: Optional[List[str]] = typer.Option(None, "--depends", help="Comma-separated list of dependency IDs.") 
):
    """Adds a new task, or adds a subtask if --parent is specified."""
    tasks_data = load_task_data()
    
    # Validate priority if provided
    validated_priority = settings.DEFAULT_PRIORITY
    if priority:
        if priority not in data_models.Priority.__args__:
            ui.console.print(Panel(f"[bold red]Invalid priority '{priority}'.[/bold red]\nValid priorities are: {', '.join(data_models.Priority.__args__)}", title="[bold red]Error[/bold red]", border_style="red"))
            raise typer.Exit(code=1)
        validated_priority = priority

    # TODO: Parse dependencies if provided
    parsed_dependencies = []

    # --- Logic to differentiate task vs subtask --- 
    if parent_id:
        # Adding a subtask
        logger.info(f"Adding new subtask '{title}' to parent {parent_id}")
        try:
            parent_id_int = int(parent_id)
            # Call core.add_subtask
            new_item = core.add_subtask(
                tasks=tasks_data.tasks, 
                parent_task_id=parent_id_int, 
                title=title, 
                description=description,
                priority=validated_priority,
                dependencies=parsed_dependencies
            )
            item_type = "Subtask"
            item_id_str = f"{parent_id_int}.{new_item.id}"
        except ValueError:
             ui.console.print(Panel(f"[bold red]Invalid parent ID format '{parent_id}'. Must be an integer.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
             raise typer.Exit(code=1)
        except ParentTaskNotFoundError as e:
             ui.console.print(Panel(f"[bold red]{e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
             raise typer.Exit(code=1)
        except Exception as e: # Catch other potential errors from core
             ui.console.print(Panel(f"[bold red]Failed to add subtask: {e}[/bold red]", title="[bold red]❌ Error[/bold red]", border_style="red"))
             logger.exception("Error during add_subtask", exc_info=settings.DEBUG)
             raise typer.Exit(code=1)

    else:
        # Adding a new task
        logger.info(f"Adding new task: {title}")
        try:
            # Call core.add_new_task
            new_item = core.add_new_task(
                tasks=tasks_data.tasks, 
                title=title,
                description=description,
                priority=validated_priority,
                dependencies=parsed_dependencies
            )
            item_type = "Task"
            item_id_str = str(new_item.id)
        except Exception as e: # Catch potential errors from core
             ui.console.print(Panel(f"[bold red]Failed to add task: {e}[/bold red]", title="[bold red]❌ Error[/bold red]", border_style="red"))
             logger.exception("Error during add_new_task", exc_info=settings.DEBUG)
             raise typer.Exit(code=1)
    # --- End logic differentiation --- 

    if not new_item:
        # This case might be redundant if core functions raise exceptions
        ui.console.print(Panel(f"[bold red]Failed to add {item_type.lower()}. Check logs.[/bold red]", title="[bold red]❌ Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)

    # Save the updated data
    save_task_data(tasks_data)
    ui.console.print(Panel(f"Successfully added {item_type} '{title}' with ID [bold cyan]{item_id_str}[/bold cyan]", title=f"[bold green]✅ {item_type} Added[/bold green]", border_style="green"))


@app.command(name="remove", help="Remove a task or subtask.")
def remove_command(
    task_id: str = typer.Argument(..., help="The ID of the task or subtask to remove (e.g., '1' or '1.2').")
):
    """Removes a specified task or subtask by rebuilding the list."""
    logger.info(f"Attempting to remove task/subtask ID: {task_id}")
    tasks_data = load_task_data()
    original_tasks = tasks_data.tasks
    new_tasks = []
    removed_count = 0

    try:
        # Handle subtask removal first
        if '.' in task_id:
            parent_id_str, sub_id_str = task_id.split('.', 1)
            parent_id = int(parent_id_str)
            sub_id = int(sub_id_str)

            for task in original_tasks:
                if task.id == parent_id:
                    original_subtask_count = len(task.subtasks)
                    # Rebuild subtask list excluding the one to remove
                    task.subtasks = [st for st in task.subtasks if st.id != sub_id]
                    if len(task.subtasks) < original_subtask_count:
                        removed_count += 1
                        logger.info(f"Removed subtask {task_id} from parent {parent_id}.")
                    # Keep the modified parent task
                    new_tasks.append(task)
                else:
                    # Keep other tasks as they are
                    new_tasks.append(task)

        # Handle main task removal
        else:
            task_id_int = int(task_id)
            for task in original_tasks:
                if task.id == task_id_int:
                    removed_count += 1 # Mark as removed, don't append
                    logger.info(f"Removed task {task_id}.")
                    # TODO: Check dependencies of other tasks on this one?
                else:
                    new_tasks.append(task) # Keep other tasks

    except ValueError:
        ui.console.print(f"[bold red]Error:[/bold red] Invalid ID format '{task_id}'.")
        raise typer.Exit(code=1)

    if removed_count > 0:
        tasks_data.tasks = new_tasks # Assign the newly built list
        save_task_data(tasks_data)
        # Optimized Output
        ui.console.print(Panel(f"Successfully removed task/subtask with ID '{task_id}'", title="[bold green]✅ Removal Complete[/bold green]", border_style="green")) 
        logger.info(f"Successfully removed task/subtask ID: {task_id}")
    else:
        # Optimized Output
        ui.console.print(Panel(f"[bold red]Failed to find task/subtask with ID '{task_id}' to remove.[/bold red]", title="[bold red]❌ Removal Failed[/bold red]", border_style="red")) 
        logger.warning(f"Task/subtask ID '{task_id}' not found for removal.")
        raise typer.Exit(code=1)


# --- AI Powered Commands ---

@app.command(name="prd", help="Parse a PRD file using AI to generate tasks.")
def parse_prd_command(
    prd_filepath: str = typer.Argument(..., help="Path to the Product Requirements Document file.")
):
    """Parses a PRD file to generate and save tasks."""
    logger.info(f"Initiating PRD parsing for: {prd_filepath}") # Keep info log for file
    try:
        # Validate file path
        if not os.path.exists(prd_filepath):
            ui.console.print(Panel(f"[bold red]PRD file not found at '{prd_filepath}'[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            raise typer.Exit(code=1)
        # Validate file extension
        if not prd_filepath.endswith((".prd", ".txt")):
            ui.console.print(Panel(f"[bold red]Invalid file extension. Only .prd and .txt files are supported.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            raise typer.Exit(code=1)
        
        # Optimized Output Start Message
        ui.console.print(Panel(f"Parsing PRD file '{prd_filepath}'...", title="🤖 PRD Parsing", border_style="blue")) 
        success = parsing.parse_prd_and_save(prd_filepath)

        # Optimized Output Final Message
        if success:
            ui.console.print(Panel(f"Successfully parsed PRD and saved tasks to '{settings.TASKS_JSON_PATH}'.", title="[bold green]✅ PRD Parsed[/bold green]", border_style="green")) 
        else:
            ui.console.print(Panel("[bold red]Failed to parse PRD or save tasks. Check logs for details.[/bold red]", title="[bold red]❌ PRD Parsing Failed[/bold red]", border_style="red"))
            raise typer.Exit(code=1)

    except FileNotFoundError: # Should be caught by os.path.exists, but keep for safety
        ui.console.print(Panel(f"[bold red]PRD file not found at '{prd_filepath}'[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)
    except Exception as e: # Catch other potential errors during setup
        ui.console.print(Panel(f"[bold red]An unexpected error occurred during PRD processing: {e}[/bold red]", title="[bold red]❌ Error[/bold red]", border_style="red"))
        logger.exception("Unexpected error in parse_prd_command", exc_info=settings.DEBUG)
        raise typer.Exit(code=1)


@app.command(name="expand", help="Expand a task into subtasks using AI.")
def expand_command(
    task_id: str = typer.Argument(..., help="The ID of the parent task to expand (e.g., '1').")
):
    """Expands a task into subtasks using AI and saves the result."""
    logger.info(f"Initiating AI expansion for task ID: {task_id}") # Keep info log for file

    # Basic validation for task ID format (main task only)
    if '.' in task_id:
        ui.console.print(Panel("[bold red]Cannot expand a subtask. Please provide a main task ID.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)
    try:
        task_id_int = int(task_id) # Check if it's a valid integer
    except ValueError:
         ui.console.print(Panel(f"[bold red]Invalid task ID format: '{task_id}'. Must be an integer.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
         raise typer.Exit(code=1)

    tasks_data = load_task_data()
    task = core.get_task_by_id(tasks_data.tasks, task_id)
    if not task:
        ui.console.print(Panel(f"[bold red]Task '{task_id}' not found.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)
    if not isinstance(task, data_models.Task):
         ui.console.print(Panel(f"[bold red]ID '{task_id}' refers to a subtask, cannot expand.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
         raise typer.Exit(code=1)

    # Optimized Output Start Message
    ui.console.print(Panel(f"Expanding task '{task_id}' ({task.title}) using AI...", title="🤖 Task Expansion", border_style="blue")) 
    success = expansion.expand_and_save(task_id)

    # Optimized Output Final Message
    if success:
        ui.console.print(Panel(f"Successfully expanded task '{task_id}'.", title="[bold green]✅ Expansion Complete[/bold green]", border_style="green")) 
    else:
        # Error should be logged by expand_and_save
        ui.console.print(Panel(f"[bold red]Failed to expand task '{task_id}'. Check logs for details.[/bold red]", title="[bold red]❌ Expansion Failed[/bold red]", border_style="red"))
        raise typer.Exit(code=1)

@app.command(name="deps", help="Check for circular dependencies in tasks.")
def check_dependencies():
    """Checks for and reports circular dependencies."""
    logger.info("Checking for circular dependencies.")
    tasks_data = load_task_data()
    cycle = dependencies.find_circular_dependencies(tasks_data.tasks)
    if cycle:
        ui.console.print(f"[bold red]Error: Circular dependency detected![/bold red]")
        ui.console.print(f"Cycle path (approx): {' -> '.join(cycle)}")
        raise typer.Exit(code=1)
    else:
        ui.console.print("[bold green]✅ No circular dependencies found.[/bold green]")

@app.command(name="gen-file", help="Generate a placeholder file for a task.")
def generate_file_command(
    task_id: str = typer.Argument(..., help="The ID of the task to generate a file for (e.g., '1'). Subtasks not supported."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help=f"Directory to save the file (default: {file_generator.DEFAULT_OUTPUT_DIR}).")
):
    """Generates a placeholder file for a specified task."""
    logger.info(f"Attempting to generate file for task ID: {task_id}")

    if '.' in task_id:
        ui.console.print("[bold red]Error:[/bold red] Cannot generate file for a subtask. Please provide a main task ID.")
        raise typer.Exit(code=1)

    try:
        task_id_int = int(task_id)  # Check if it's a valid integer
    except ValueError:
        ui.console.print(f"[bold red]Error:[/bold red] Invalid task ID format: '{task_id}'. Must be an integer.")
        raise typer.Exit(code=1)

    tasks_data = load_task_data()
    task = core.get_task_by_id(tasks_data.tasks, task_id)

    logger.debug(f"Type of object found for ID '{task_id}': {type(task)}") 

    if not task:
        ui.console.print(f"[bold red]Error:[/bold red] Task with ID '{task_id}' not found.")
        raise typer.Exit(code=1)

    # Removed the check for output_dir existence, assuming generate_file_from_task handles it.
    # if output_dir and not os.path.isdir(output_dir):
    #     ui.console.print(f"[bold red]Error:[/bold red] Invalid output directory: '{output_dir}'. Directory not found.")
    #     raise typer.Exit(code=1)

    ui.console.print(f"📝 Generating file for task '{task.title}'...")
    generated_path = file_generator.generate_file_from_task(task, output_dir=output_dir)

    if generated_path:
        ui.console.print(f"[bold green]✅ Successfully generated file:[/bold green] {os.path.abspath(generated_path)}")
        raise typer.Exit(code=0)
    else:
        ui.console.print(f"[bold red]❌ Failed to generate file for task '{task_id}'. Check logs.[/bold red]")
        raise typer.Exit(code=1)

@app.command(name="report", help="Generate a report (Markdown table or Mermaid diagram).")
def generate_report(
    report_type: str = typer.Argument("markdown", help="Type of report: 'markdown' or 'mermaid'."),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save report to a file.")
):
    """Generates and displays or saves a report."""
    logger.info(f"Generating '{report_type}' report.")
    tasks_data = load_task_data()

    report_content = ""
    # Optimized Output Start Message
    ui.console.print(f"📊 Generating {report_type} report...") 

    if report_type == "markdown":
        report_content = core.generate_markdown_table_tasks_report(tasks_data.tasks)
    elif report_type == "mermaid":
        report_content = dependencies.generate_mermaid_diagram(tasks_data.tasks)
    else:
        ui.console.print(f"[bold red]Error:[/bold red] Invalid report type '{report_type}'. Choose 'markdown' or 'mermaid'.")
        raise typer.Exit(code=1)

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            # Optimized Output Final Message (File)
            ui.console.print(f"[bold green]✅ Report saved to '{output_file}'[/bold green]") 
        except IOError as e:
            ui.console.print(f"[bold red]❌ Error saving report to '{output_file}': {e}[/bold red]")
            raise typer.Exit(code=1)
    else:
        # Print report content using rich console
        ui.console.print("--- Report Start ---")
        ui.console.print(report_content)
        ui.console.print("--- Report End ---")
        # Optimized Output Final Message (Console)
        ui.console.print(f"[bold green]✅ Report generated successfully.[/bold green]") 

if __name__ == "__main__":
    # Ensure tasks directory exists (optional, storage might handle this)
    tasks_dir = os.path.dirname(settings.TASKS_JSON_PATH)
    if tasks_dir and not os.path.exists(tasks_dir):
        try:
            os.makedirs(tasks_dir)
            logger.info(f"Created tasks directory: {tasks_dir}")
        except OSError as e:
            logger.error(f"Could not create tasks directory {tasks_dir}: {e}")
            # Decide if this is fatal or not
    app()
