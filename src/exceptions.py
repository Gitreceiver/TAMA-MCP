class TaskManagerError(Exception):
    """Base exception class for Task Manager errors."""
    pass

class AIResponseParsingError(TaskManagerError):
    """Raised when the AI response cannot be parsed correctly."""
    pass

class ParentTaskNotFoundError(TaskManagerError):
    """Raised when a specified parent task cannot be found."""
    pass

class TaskNotFoundError(TaskManagerError):
    """Raised when a specified task cannot be found."""
    pass

class InvalidStatusError(TaskManagerError):
    """Raised when an invalid status is provided."""
    pass

class DependencyError(TaskManagerError):
    """Raised for errors related to task dependencies."""
    pass

class ConfigurationError(TaskManagerError):
    """Raised for errors related to configuration loading or validation."""
    pass

class FileOperationError(TaskManagerError):
    """Raised for errors during file operations."""
    pass

class InputValidationError(TaskManagerError):
    """Raised for errors during input validation."""
    pass
