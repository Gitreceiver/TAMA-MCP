import subprocess
from rich.console import Console

console = Console()

def create_branch(branch_name: str):
    """Creates and switches to a new Git branch."""
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
        console.print(f"[bold green]Switched to a new branch '{branch_name}'[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error creating branch '{branch_name}': {e.stderr}[/bold red]")

def commit_changes(message: str):
    """Commits staged changes with a given message."""
    try:
        result = subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True, text=True)
        console.print("[bold green]Changes committed.[/bold green]")
        console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error committing changes: {e.stderr}[/bold red]")
