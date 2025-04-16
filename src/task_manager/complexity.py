import logging
from typing import Union, Optional

# Use absolute imports
from task_manager.data_models import Task, Subtask

logger = logging.getLogger(__name__)

# Define complexity levels (example)
COMPLEXITY_LOW = "Low"
COMPLEXITY_MEDIUM = "Medium"
COMPLEXITY_HIGH = "High"
COMPLEXITY_UNKNOWN = "Unknown"

def estimate_complexity(item: Union[Task, Subtask]) -> str:
    """
    Estimates the complexity of a task or subtask based on simple heuristics.

    Args:
        item: The Task or Subtask object.

    Returns:
        A string representing the estimated complexity level.
    """
    logger.debug(f"Estimating complexity for item: {item.title}")

    score = 0

    # Factor 1: Description length
    if item.description and len(item.description) > 100:
        score += 1
    if item.description and len(item.description) > 300:
        score += 1

    # Factor 2: Number of dependencies
    if item.dependencies:
        score += len(item.dependencies)

    # Factor 3: Number of subtasks (for Tasks only)
    if isinstance(item, Task) and item.subtasks:
        score += len(item.subtasks)
        # Optionally add complexity based on subtask complexity? (Too complex for now)

    # Factor 4: Explicit details or test strategy
    if item.details:
        score += 1
    if isinstance(item, Task) and item.test_strategy:
        score += 1

    # Determine level based on score (example thresholds)
    if score == 0:
        complexity = COMPLEXITY_LOW
    elif score <= 3:
        complexity = COMPLEXITY_MEDIUM
    else:
        complexity = COMPLEXITY_HIGH

    logger.debug(f"Estimated complexity for '{item.title}' (Score: {score}): {complexity}")
    return complexity

# Example usage (for testing, remove later)
# if __name__ == '__main__':
#     from data_models import Task, Subtask
#     logging.basicConfig(level=logging.DEBUG)

#     task_simple = Task(id=1, title="Simple Task")
#     print(f"{task_simple.title}: {estimate_complexity(task_simple)}") # Expected: Low

#     task_medium = Task(id=2, title="Medium Task", description="This is a description over 100 chars long.", dependencies=[1], subtasks=[Subtask(id=1, title="Sub", parent_task_id=2)])
#     print(f"{task_medium.title}: {estimate_complexity(task_medium)}") # Expected: Medium (1 + 1 + 1 = 3)

#     task_complex = Task(id=3, title="Complex Task", description="Very long description..." * 10, dependencies=[1, 2], subtasks=[Subtask(id=1, title="S1", parent_task_id=3), Subtask(id=2, title="S2", parent_task_id=3)], details="Some details", test_strategy="Manual test")
#     print(f"{task_complex.title}: {estimate_complexity(task_complex)}") # Expected: High (2 + 2 + 2 + 1 + 1 = 8)
