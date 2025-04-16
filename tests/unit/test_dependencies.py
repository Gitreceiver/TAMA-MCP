import pytest
from src.task_manager.dependencies import find_circular_dependencies
from src.task_manager.data_models import Task, Subtask

# --- Test Cases for Circular Dependencies ---

def test_no_circular_dependencies():
    """Test with a valid DAG."""
    tasks = [
        Task(id=1, title="T1", dependencies=[]),
        Task(id=2, title="T2", dependencies=[1]),
        Task(id=3, title="T3", dependencies=[1, 2])
    ]
    assert find_circular_dependencies(tasks) is None

def test_simple_circular_dependency():
    """Test a direct cycle: 1 -> 2 -> 1."""
    tasks = [
        Task(id=1, title="T1", dependencies=[2]),
        Task(id=2, title="T2", dependencies=[1])
    ]
    cycle = find_circular_dependencies(tasks)
    assert cycle is not None
    # The exact path reported might vary slightly based on DFS traversal order
    assert '1' in cycle
    assert '2' in cycle

def test_longer_circular_dependency():
    """Test a longer cycle: 1 -> 2 -> 3 -> 1."""
    tasks = [
        Task(id=1, title="T1", dependencies=[2]),
        Task(id=2, title="T2", dependencies=[3]),
        Task(id=3, title="T3", dependencies=[1])
    ]
    cycle = find_circular_dependencies(tasks)
    assert cycle is not None
    assert '1' in cycle
    assert '2' in cycle
    assert '3' in cycle

def test_circular_dependency_with_subtasks():
    """Test cycle involving subtasks: 1 -> 2.1 -> 3 -> 1."""
    tasks = [
        Task(id=1, title="T1", dependencies=["2.1"]),
        Task(id=2, title="T2", dependencies=[], subtasks=[
            Subtask(id=1, title="S2.1", parent_task_id=2, dependencies=[3])
        ]),
        Task(id=3, title="T3", dependencies=[1])
    ]
    cycle = find_circular_dependencies(tasks)
    assert cycle is not None
    assert '1' in cycle
    assert '2.1' in cycle
    assert '3' in cycle

def test_self_dependency():
    """Test a task depending on itself."""
    tasks = [
        Task(id=1, title="T1", dependencies=[1])
    ]
    cycle = find_circular_dependencies(tasks)
    assert cycle is not None
    assert '1' in cycle

def test_subtask_self_dependency():
    """Test a subtask depending on itself."""
    tasks = [
        Task(id=1, title="T1", subtasks=[
            Subtask(id=1, title="S1.1", parent_task_id=1, dependencies=["1.1"])
        ])
    ]
    cycle = find_circular_dependencies(tasks)
    assert cycle is not None
    assert '1.1' in cycle

def test_dependency_on_non_existent_task():
    """Test that dependencies on non-existent tasks are ignored."""
    tasks = [
        Task(id=1, title="T1", dependencies=[99]) # Depends on non-existent 99
    ]
    assert find_circular_dependencies(tasks) is None

def test_empty_task_list():
    """Test with an empty list of tasks."""
    tasks = []
    assert find_circular_dependencies(tasks) is None

def test_complex_graph_no_cycle():
    """Test a more complex graph without cycles."""
    tasks = [
        Task(id=1, title="T1"),
        Task(id=2, title="T2", dependencies=[1]),
        Task(id=3, title="T3", dependencies=[1], subtasks=[
            Subtask(id=1, title="S3.1", parent_task_id=3, dependencies=[2])
        ]),
        Task(id=4, title="T4", dependencies=[2, "3.1"])
    ]
    assert find_circular_dependencies(tasks) is None
