import sqlite3
import logging
from config import settings

logger = logging.getLogger(__name__)

def initialize_database():
    """
    Initializes the database by creating the necessary tables if they don't already exist.
    """
    if not settings.DATABASE_URL.startswith("sqlite:///"):
        logger.error("DATABASE_URL in settings is not a valid sqlite connection string.")
        return

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT,
            priority TEXT,
            description TEXT,
            dependencies TEXT,
            linked_files TEXT,
            details TEXT,
            test_strategy TEXT
        )
        """)

        # Create subtasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER,
            parent_task_id INTEGER,
            title TEXT NOT NULL,
            status TEXT,
            dependencies TEXT,
            linked_files TEXT,
            description TEXT,
            details TEXT,
            test_strategy TEXT,
            PRIMARY KEY (id, parent_task_id)
        )
        """)

        conn.commit()
        logger.info("SQLite database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"An error occurred during SQLite database initialization: {e}")
    finally:
        if conn:
            conn.close()
