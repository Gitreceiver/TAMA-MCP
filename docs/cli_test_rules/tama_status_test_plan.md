# Test Plan for `tama status`

## 1. Basic Functionality

*   **Test Case 1.1: Set a task's status**
    *   **Description**: Test changing the status of a task from 'pending' to 'in-progress'.
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command**: `tama status <task_A_id> in-progress`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   `tama show <task_A_id>` should display the status as 'in-progress'.

*   **Test Case 1.2: Set a subtask's status**
    *   **Description**: Test changing the status of a subtask.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add subtask "Subtask A.1" to Task A.
    *   **Command**: `tama status <subtask_A.1_id> done`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   `tama show <task_A_id>` should show the subtask with the status 'done'.

## 2. Edge Cases & Error Handling

*   **Test Case 2.1: Set status on a non-existent task**
    *   **Description**: Test attempting to set the status for a task ID that does not exist.
    *   **Setup**:
        1.  Ensure no task with ID 999 exists.
    *   **Command**: `tama status 999 pending`
    *   **Expected Outcome**:
        *   The command should fail with an error message indicating the task was not found.

*   **Test Case 2.2: Use an invalid status value**
    *   **Description**: Test the command with a status that is not one of the allowed values (pending, in-progress, done, blocked).
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command**: `tama status <task_A_id> invalid-status`
    *   **Expected Outcome**:
        *   The command should fail with an error message indicating that 'invalid-status' is not a valid choice.

*   **Test Case 2.3: Incorrect number of arguments**
    *   **Description**: Test calling the command with too few or too many arguments.
    *   **Command 1**: `tama status`
    *   **Command 2**: `tama status 1`
    *   **Command 3**: `tama status 1 pending extra-arg`
    *   **Expected Outcome**:
        *   All commands should fail and show the correct usage/help text.

## 3. Regression Tests

*   **Test Case 3.1: Parent task status updates when last subtask is completed**
    *   **Description**: Test that when the only subtask of a parent task is marked as 'done', the parent task's status is also updated to 'done'. This is a regression test for a bug that caused an `AttributeError`.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add subtask "Subtask A.1" to Task A.
    *   **Command**: `tama status <subtask_A.1_id> done`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   The parent task's status should automatically be updated to 'done'.
