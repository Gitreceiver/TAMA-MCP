# Test Plan for `tama link`

## 1. Basic Functionality

*   **Test Case 1.1: Link two existing tasks**
    *   **Description**: Test linking two existing tasks.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
    *   **Command**: `tama link <task_A_id> <task_B_id>`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   Task B should now have a dependency on Task A.
        *   Running `tama next` should propose Task A, not Task B.
        *   `tama detail <task_B_id>` should show Task A as a dependency.

*   **Test Case 1.2: Link a task to a completed task**
    *   **Description**: Test linking a pending task to a completed task.
    *   **Setup**:
        1.  Add task "Task A" and mark it as complete.
        2.  Add task "Task B".
    *   **Command**: `tama link <task_B_id> <task_A_id>`
    *   **Expected Outcome**:
        *   The command should execute successfully.
        *   Task B should still be available as the next task, as its dependency is already complete.
        *   `tama detail <task_B_id>` should show Task A as a dependency.

## 2. Edge Cases & Error Handling

*   **Test Case 2.1: Link a task to itself**
    *   **Description**: Test linking a task to itself.
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command**: `tama link <task_A_id> <task_A_id>`
    *   **Expected Outcome**:
        *   The command should fail with an error message indicating a task cannot depend on itself.

*   **Test Case 2.2: Link a non-existent task**
    *   **Description**: Test linking to or from a task ID that does not exist.
    *   **Setup**:
        1.  Add task "Task A".
    *   **Command 1**: `tama link <task_A_id> 999`
    *   **Command 2**: `tama link 999 <task_A_id>`
    *   **Expected Outcome**:
        *   Both commands should fail with an error message indicating the task ID was not found.

*   **Test Case 2.3: Circular Dependencies**
    *   **Description**: Test creating a circular dependency.
    *   **Setup**:
        1.  Add task "Task A".
        2.  Add task "Task B".
        3.  Link Task B to Task A (`tama link <task_B_id> <task_A_id>`).
    *   **Command**: `tama link <task_A_id> <task_B_id>`
    *   **Expected Outcome**:
        *   The command should fail with an error message warning about creating a circular dependency.

*   **Test Case 2.4: Incorrect number of arguments**
    *   **Description**: Test calling the command with too few or too many arguments.
    *   **Command 1**: `tama link`
    *   **Command 2**: `tama link 1`
    *   **Command 3**: `tama link 1 2 3`
    *   **Expected Outcome**:
        *   All commands should fail and show the correct usage/help text.
