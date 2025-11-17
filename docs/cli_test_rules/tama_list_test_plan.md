# Test Plan for `tama list`

## 1. Basic Functionality

*   **Test Case 1.1: List all tasks**
    *   **Description**: Test listing all tasks when no filters are applied.
    *   **Setup**:
        1.  Add task "Task A" (status: pending, priority: medium).
        2.  Add task "Task B" (status: in-progress, priority: high).
        3.  Add task "Task C" (status: done, priority: low).
    *   **Command**: `tama list`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should be a table displaying all three tasks with their correct details.

## 2. Filtering

*   **Test Case 2.1: Filter by status**
    *   **Description**: Test filtering the task list by status.
    *   **Setup**:
        1.  Add task "Task A" (status: pending).
        2.  Add task "Task B" (status: in-progress).
        3.  Add task "Task C" (status: pending).
    *   **Command**: `tama list --status pending`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should only display "Task A" and "Task C".

*   **Test Case 2.2: Filter by priority**
    *   **Description**: Test filtering the task list by priority.
    *   **Setup**:
        1.  Add task "Task A" (priority: high).
        2.  Add task "Task B" (priority: medium).
        3.  Add task "Task C" (priority: high).
    *   **Command**: `tama list --priority high`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should only display "Task A" and "Task C".

*   **Test Case 2.3: Filter by both status and priority**
    *   **Description**: Test filtering the task list by both status and priority simultaneously.
    *   **Setup**:
        1.  Add task "Task A" (status: pending, priority: high).
        2.  Add task "Task B" (status: pending, priority: medium).
        3.  Add task "Task C" (status: in-progress, priority: high).
        4.  Add task "Task D" (status: pending, priority: high).
    *   **Command**: `tama list --status pending --priority high`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should only display "Task A" and "Task D".

## 3. Edge Cases

*   **Test Case 3.1: List with no tasks**
    *   **Description**: Test the output when no tasks have been added.
    *   **Setup**:
        1.  Ensure the task list is empty.
    *   **Command**: `tama list`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should indicate that no tasks were found or display an empty table.

*   **Test Case 3.2: Filter with no matching tasks**
    *   **Description**: Test the output when a filter is applied that matches no tasks.
    *   **Setup**:
        1.  Add task "Task A" (status: pending, priority: medium).
    *   **Command**: `tama list --status done`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The output should indicate that no tasks were found or display an empty table.
