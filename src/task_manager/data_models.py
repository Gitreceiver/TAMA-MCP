from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Union, Literal
from config import settings

Status = Literal["pending", "in-progress", "done", "deferred", "blocked", "review"]
Priority = Literal["low", "medium", "high"]
Dependency = Union[int, str]  # int for task ID, str for subtask ID like "1.2"

class Subtask(BaseModel):
    id: int = Field(..., gt=0)
    title: str
    description: Optional[str] = None
    status: Status = "pending"
    priority: Priority = settings.DEFAULT_PRIORITY
    dependencies: List[Dependency] = []
    details: Optional[str] = None
    test_strategy: Optional[str] = Field(default=None, alias="testStrategy")
    parent_task_id: Optional[int] = None  # Added for easier reference
    linked_files: List[str] = []

class Task(BaseModel):
    id: int = Field(..., gt=0)
    title: str
    description: Optional[str] = None
    status: Status = "pending"
    dependencies: List[Dependency] = []
    priority: Priority = settings.DEFAULT_PRIORITY  # Use default from settings
    details: Optional[str] = None
    test_strategy: Optional[str] = Field(default=None, alias="testStrategy")
    subtasks: List[Subtask] = []
    linked_files: List[str] = []

    # Ensure subtask parent_task_id is set correctly using a model validator
    @model_validator(mode='before')
    @classmethod
    def set_subtask_parent_ids(cls, data):
        # data is the raw input dict before validation
        if isinstance(data, dict) and 'id' in data and 'subtasks' in data and isinstance(data['subtasks'], list):
            parent_id = data.get('id') # Get potential parent ID
            if parent_id is not None:
                for subtask_data in data['subtasks']:
                    if isinstance(subtask_data, dict):
                        # Set parent_task_id if not already present
                        subtask_data.setdefault('parent_task_id', parent_id)
                    # Handle case where subtask might already be an object? Less likely with mode='before'
                    # elif isinstance(subtask_data, Subtask) and subtask_data.parent_task_id is None:
                    #     subtask_data.parent_task_id = parent_id
        return data # Return the potentially modified data dict for further validation

class MetaData(BaseModel):
    project_name: str = Field(alias="projectName")
    version: str
    # Add other meta fields from original project if needed
    prd_source: Optional[str] = Field(default=None, alias="prdSource")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")

class TasksData(BaseModel):
    meta: MetaData
    tasks: List[Task]
