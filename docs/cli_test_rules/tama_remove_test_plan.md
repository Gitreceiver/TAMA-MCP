# Test Plan for `tama remove`

## 1. Basic Functionality

*   **Test Case 1.1: Remove a single, simple task**
    *   **Description**: Test removing a standalone task with no dependencies or subtasks.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
    *   **Command**: `tama remove <task_A_id>`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   `tama list` should no longer show Task A, only Task B.

*   **Test Case 1.2: Remove a task with subtasks**
    *   **Description**: Test removing a parent task that contains subtasks.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add subtask "Subtask A.1" to Task A.
    *   **Command**: `tama remove <task_A_id>`
    *   **Expected Outcome**:
        *   The command should execute directly, without a confirmation prompt.
        *   Both the parent task and all its subtasks should be removed.
        *   `tama list` should show no tasks.

*   **Test Case 1.3: Remove just a subtask**
    *   **Description**: Test removing a specific subtask without affecting the parent task.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add subtask "Subtask A.1" to Task A.
    *   **Command**: `tama remove <subtask_A.1_id>` (e.g., `1.1`)
    *   **Expected Outcome**:
        *   Only the subtask is removed.
        *   The parent task "Task A" remains.
        *   `tama show <task_A_id>` should no longer list the removed subtask.

## 2. Edge Cases & Error Handling

*   **Test Case 2.1: Remove a non-existent task**
    *   **Description**: Test attempting to remove a task ID that does not exist.
    *   **Setup**:
        1.  Ensure no task with ID 999 exists.
    *   **Command**: `tama remove 999`
    *   **Expected Outcome**:
        *   The command should fail with an error message indicating the task was not found.

*   **Test Case 2.2: Remove a task that is a dependency for another task**
    *   **Description**: Test removing a task that another task depends on.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
        3.  Make Task B dependent on Task A (`tama add-dep <task_B_id> <task_A_id>`).
    *   **Command**: `tama remove <task_A_id>`
    *   **Expected Outcome**:
        *   The command should execute directly, without a confirmation prompt.
        *   A message should indicate that the dependent task was updated.
        *   The task should be removed.
        *   The dependency link should be removed from Task B. `tama show <task_B_id>` should no longer show a dependency on Task A.

*   **Test Case 2.3: Incorrect number of arguments**
    *   **Description**: Test calling the command with too few arguments.
    *   **Command**: `tama remove`
    *   **Expected Outcome**:
        *   The command should fail and show the correct usage/help text.
