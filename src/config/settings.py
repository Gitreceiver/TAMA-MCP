import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field, field_validator
from typing import Literal
import logging

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
Priority = Literal["low", "medium", "high"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='E:/TAMA_MCP/.env',
        env_file_encoding='utf-8',
        extra='ignore',  # Ignore extra env vars not defined in the model
        case_sensitive=False,  # Env vars are case-insensitive
        env_nested_delimiter='__',  # Use double underscore for nested env vars
        env_prefix='APP_',  # Optional: prefix all env vars with APP_
    )

    # --- DeepSeek Configuration ---
    DEEPSEEK_API_KEY: SecretStr
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_GENERAL_MODEL: str = Field(default="deepseek-chat", description="Model for general tasks like parsing")
    DEEPSEEK_REASONING_MODEL: str = Field(default="deepseek-coder", description="Model for coding/reasoning tasks")

    # --- AI General Settings ---
    AI_MAX_TOKENS: int = Field(default=8192, gt=0, description="Max tokens for AI response")
    AI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="AI temperature (0.0-2.0)")

    # --- Application Settings ---
    TASKS_JSON_PATH: str = Field(default="tasks.json", description="Path to the main tasks file")
    TASKS_DIR_PATH: str = Field(default="tasks", description="Directory for individual task files")
    LOG_LEVEL: LogLevel = Field(default="INFO", description="Logging level")
    DEFAULT_PRIORITY: Priority = Field(default="medium", description="Default task priority")
    DEFAULT_SUBTASKS: int = Field(default=3, gt=0, description="Default number of subtasks for expansion")
    PROJECT_NAME: str = Field(default="My Python Task Manager", description="Project name for metadata")
    PROJECT_VERSION: str = Field(default="0.1.0", description="Project version for metadata")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    @field_validator('TASKS_JSON_PATH', 'TASKS_DIR_PATH', mode='before')
    @classmethod
    def resolve_path(cls, v):
        # Resolve relative paths based on project root (assuming script runs from root)
        if isinstance(v, str): # Ensure it's a string before resolving
            return os.path.abspath(v)
        return v # Return original value if not a string (or handle error)

# Create a single instance to be imported elsewhere
settings = Settings()

# --- Temporary Debugging --- 
config_logger = logging.getLogger("config.settings")
if settings.DEEPSEEK_API_KEY:
    key_val = settings.DEEPSEEK_API_KEY.get_secret_value()
    config_logger.debug(f"[CONFIG DEBUG] Loaded DEEPSEEK_API_KEY: {key_val[:5]}...{key_val[-4:]}")
else:
    config_logger.debug("[CONFIG DEBUG] DEEPSEEK_API_KEY not found by Settings.")
# --- End Temporary Debugging ---

# Example usage: from src.config.settings import settings
# print(settings.DEEPSEEK_API_KEY.get_secret_value())
