# Test Plan for `tama remove-dep`

## 1. Basic Functionality

*   **Test Case 1.1: Remove an existing dependency**
    *   **Description**: Test removing a dependency from a task.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
        3.  Make Task B dependent on Task A (`tama add-dep <task_B_id> <task_A_id>`).
    *   **Command**: `tama remove-dep <task_B_id> <task_A_id>`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   `tama show <task_B_id>` should no longer list Task A as a dependency.
        *   Running `tama next` should now consider both Task A and Task B as eligible (depending on priority/ID).

## 2. Edge Cases & Error Handling

*   **Test Case 2.1: Remove a dependency that does not exist**
    *   **Description**: Test trying to remove a dependency that isn't set.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
    *   **Command**: `tama remove-dep <task_B_id> <task_A_id>`
    *   **Expected Outcome**:
        *   The command should fail or give a warning, indicating that the dependency does not exist.

*   **Test Case 2.2: Remove a dependency from a non-existent task**
    *   **Description**: Test calling the command with a target task ID that does not exist.
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command**: `tama remove-dep 999 <task_A_id>`
    *   **Expected Outcome**:
        *   The command should fail with an error message indicating the target task was not found.

*   **Test Case 2.3: Remove a non-existent dependency ID from an existing task**
    *   **Description**: Test calling the command with a dependency task ID that does not exist.
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command**: `tama remove-dep <task_A_id> 999`
    *   **Expected Outcome**:
        *   The command should fail or give a warning, indicating that the dependency ID to be removed was not found.

*   **Test Case 2.4: Incorrect number of arguments**
    *   **Description**: Test calling the command with too few arguments.
    *   **Command 1**: `tama remove-dep`
    *   **Command 2**: `tama remove-dep 1`
    *   **Expected Outcome**:
        *   Both commands should fail and show the correct usage/help text.
