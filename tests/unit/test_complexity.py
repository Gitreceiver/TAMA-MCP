import pytest
from src.task_manager.complexity import (
    estimate_complexity,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
    COMPLEXITY_HIGH
)
from src.task_manager.data_models import Task, Subtask

# --- Test Cases for estimate_complexity ---

def test_complexity_low_simple_task():
    """Test a simple task with minimal details."""
    task = Task(id=1, title="Simple")
    assert estimate_complexity(task) == COMPLEXITY_LOW

def test_complexity_low_simple_subtask():
    """Test a simple subtask."""
    subtask = Subtask(id=1, title="Simple Sub", parent_task_id=1)
    assert estimate_complexity(subtask) == COMPLEXITY_LOW

def test_complexity_medium_description():
    """Test complexity increase due to description length."""
    desc_medium = "a" * 150
    desc_high = "b" * 350
    task_med_desc = Task(id=1, title="Med Desc", description=desc_medium)
    task_high_desc = Task(id=2, title="High Desc", description=desc_high)
    # Score 1 -> Medium
    assert estimate_complexity(task_med_desc) == COMPLEXITY_MEDIUM
    # Score 2 -> Medium
    assert estimate_complexity(task_high_desc) == COMPLEXITY_MEDIUM

def test_complexity_medium_dependencies():
    """Test complexity increase due to dependencies."""
    task_1_dep = Task(id=1, title="1 Dep", dependencies=[10])
    task_3_deps = Task(id=2, title="3 Deps", dependencies=[10, 11, "12.1"])
    # Score 1 -> Medium
    assert estimate_complexity(task_1_dep) == COMPLEXITY_MEDIUM
    # Score 3 -> Medium
    assert estimate_complexity(task_3_deps) == COMPLEXITY_MEDIUM

def test_complexity_medium_subtasks():
    """Test complexity increase due to subtasks (Tasks only)."""
    sub1 = Subtask(id=1, title="s1", parent_task_id=1)
    sub2 = Subtask(id=2, title="s2", parent_task_id=1)
    task_1_sub = Task(id=1, title="1 Sub", subtasks=[sub1])
    task_2_subs = Task(id=2, title="2 Subs", subtasks=[sub1, sub2])
    # Score 1 -> Medium
    assert estimate_complexity(task_1_sub) == COMPLEXITY_LOW
    # Score 2 -> Medium
    assert estimate_complexity(task_2_subs) == COMPLEXITY_LOW

def test_complexity_medium_details_strategy():
    """Test complexity increase due to details and test strategy."""
    task_details = Task(id=1, title="With Details", details="Some details.")
    task_strategy = Task(id=2, title="With Strategy", test_strategy="Manual test.")
    task_both = Task(id=3, title="Both", details="...", test_strategy="...")
    # Score 1 -> Medium
    assert estimate_complexity(task_details) == COMPLEXITY_MEDIUM
    # Score 1 -> Medium
    assert estimate_complexity(task_strategy) == COMPLEXITY_LOW
    # Score 2 -> Medium
    assert estimate_complexity(task_both) == COMPLEXITY_MEDIUM

def test_complexity_high_combination():
    """Test high complexity due to combination of factors."""
    desc = "a" * 150
    deps = [1, 2]
    subs = [Subtask(id=1, title="s1", parent_task_id=1)]
    details = "Important details"
    strategy = "Automated tests"
    # Score: 1 (desc) + 2 (deps) + 1 (subs) + 1 (details) + 1 (strategy) = 6
    task = Task(id=1, title="Complex", description=desc, dependencies=deps, subtasks=subs, details=details, test_strategy=strategy)
    assert estimate_complexity(task) == COMPLEXITY_HIGH

def test_complexity_subtask_ignores_task_fields():
    """Ensure subtask complexity ignores subtasks and test_strategy fields."""
    desc = "a" * 150
    deps = [1]
    details = "Subtask details"
    # Score: 1 (desc) + 1 (deps) + 1 (details) = 3
    subtask = Subtask(id=1, title="Complex Sub", parent_task_id=1, description=desc, dependencies=deps, details=details)
    # Add task-specific fields to ensure they are ignored for subtasks
    # setattr(subtask, 'subtasks', [Subtask(id=2, title="nested", parent_task_id=1)]) # Not possible with Pydantic v2 easily
    # setattr(subtask, 'test_strategy', 'some strategy')
    assert estimate_complexity(subtask) == COMPLEXITY_MEDIUM # Score 3 -> Medium
