import os
import sqlite3
import logging
import json
from typing import List, Optional

from task_manager.data_models import TasksData, Task, Subtask, MetaData
from config import settings

logger = logging.getLogger(__name__)

def get_db_connection(db_path: Optional[str] = None):
    """Establishes a connection to the SQLite database."""
    if db_path is None:
        db_url = settings.DATABASE_URL
        # If the DATABASE_URL is the default in-memory one, create tama.db in the current directory
        if db_url == 'sqlite:///:memory:':
            db_path = os.path.join(os.getcwd(), 'tama.db')
            logger.debug(f"DATABASE_URL not set, defaulting to local file: {db_path}")
        elif db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            logger.error("DATABASE_URL in settings is not a valid sqlite connection string.")
            raise ValueError("Invalid DATABASE_URL for SQLite.")
    return sqlite3.connect(db_path)

def initialize_database(db_path: Optional[str] = None):
    """Initializes the database by creating the necessary tables if they don't already exist."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            priority TEXT,
            dependencies TEXT,
            details TEXT,
            test_strategy TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER,
            parent_task_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            priority TEXT,
            dependencies TEXT,
            details TEXT,
            test_strategy TEXT,
            PRIMARY KEY (id, parent_task_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS linked_files (
            task_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            PRIMARY KEY (task_id, file_path)
        )
        """)
        conn.commit()
        logger.info("SQLite database initialized successfully.")

def load_tasks() -> TasksData:
    """Loads all tasks and subtasks from the SQLite database."""
    initialize_database()  # Ensure DB is initialized
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Load metadata
        cursor.execute("SELECT * FROM metadata")
        meta_rows = {row['key']: row['value'] for row in cursor.fetchall()}
        meta = MetaData(
            projectName=meta_rows.get('projectName', 'Default Project'),
            version=meta_rows.get('version', '0.1.0')
        )

        # Load tasks
        cursor.execute("SELECT * FROM tasks")
        task_rows = cursor.fetchall()
        tasks = []
        for task_row in task_rows:
            task_dict = dict(task_row)
            task_dict['dependencies'] = json.loads(task_dict.get('dependencies', '[]'))
            cursor.execute("SELECT file_path FROM linked_files WHERE task_id = ?", (str(task_dict['id']),))
            task_dict['linked_files'] = [row['file_path'] for row in cursor.fetchall()]

            # Load subtasks for the current task
            cursor.execute("SELECT * FROM subtasks WHERE parent_task_id = ?", (task_dict['id'],))
            subtask_rows = cursor.fetchall()
            subtasks = []
            for subtask_row in subtask_rows:
                subtask_dict = dict(subtask_row)
                subtask_dict['dependencies'] = json.loads(subtask_dict.get('dependencies', '[]'))
                subtask_id = f"{task_dict['id']}.{subtask_dict['id']}"
                cursor.execute("SELECT file_path FROM linked_files WHERE task_id = ?", (subtask_id,))
                subtask_dict['linked_files'] = [row['file_path'] for row in cursor.fetchall()]
                subtasks.append(Subtask(**subtask_dict))

            task_dict['subtasks'] = subtasks
            tasks.append(Task(**task_dict))

    return TasksData(meta=meta, tasks=tasks)

def save_tasks(tasks_data: TasksData):
    """Saves all tasks and subtasks to the SQLite database, overwriting existing data."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Clear existing data
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM subtasks")
        cursor.execute("DELETE FROM metadata")
        cursor.execute("DELETE FROM linked_files")

        # Save metadata
        cursor.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ('projectName', tasks_data.meta.project_name))
        cursor.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ('version', tasks_data.meta.version))

        # Save tasks and subtasks
        for task in tasks_data.tasks:
            cursor.execute("""
            INSERT INTO tasks (id, title, description, status, priority, dependencies, details, test_strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.title,
                task.description,
                task.status,
                task.priority,
                json.dumps(task.dependencies),
                task.details,
                task.test_strategy
            ))
            for file_path in task.linked_files:
                cursor.execute("INSERT INTO linked_files (task_id, file_path) VALUES (?, ?)", (str(task.id), file_path))
            for subtask in task.subtasks:
                cursor.execute("""
                INSERT INTO subtasks (id, parent_task_id, title, description, status, priority, dependencies, details, test_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    subtask.id,
                    task.id,
                    subtask.title,
                    subtask.description,
                    subtask.status,
                    subtask.priority,
                    json.dumps(subtask.dependencies),
                    subtask.details,
                    subtask.test_strategy
                ))
                subtask_id = f"{task.id}.{subtask.id}"
                for file_path in subtask.linked_files:
                    cursor.execute("INSERT INTO linked_files (task_id, file_path) VALUES (?, ?)", (subtask_id, file_path))
        conn.commit()
        logger.info(f"Successfully saved {len(tasks_data.tasks)} tasks to the SQLite database.")
