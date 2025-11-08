# Test Plan for `tama complete`

This document outlines the test plan for the `tama complete` command.

## Command Synopsis

`tama complete <task_id> [--commit] [--propagate]`

## Test Summary (Executed on 2025-11-08)

During testing, two bugs were identified:
1.  The command would fail with a `ModuleNotFoundError` because the `git_utils.py` file was missing.
2.  The command would output a redundant success message even if the task was already completed.

Both bugs have been **fixed**. The `git_utils.py` file has been restored, and the command now correctly handles already completed tasks. All test cases now pass as expected.

## Test Cases

### 1. Happy Path

- **Test Case 1.1**: Complete a main task.
  - **Prerequisites**: A task exists with ID 1, in "in-progress" status.
  - **Command**: `uv run tama complete 1`
  - **Expected Outcome**: The command succeeds. A message confirms the status is now "done". `tama show 1` verifies the new status.

- **Test Case 1.2**: Complete a task with `--commit`.
  - **Prerequisites**: A task exists with ID 1, in "in-progress" status. There are staged changes in Git.
  - **Command**: `uv run tama complete 1 --commit`
  - **Expected Outcome**: The command succeeds. The task status is updated to "done". A new Git commit is created with a message like "feat: Complete task 1 - <task-title>".

### 2. Error Cases

- **Test Case 2.1**: Task not found.
  - **Prerequisites**: No task with the specified ID exists.
  - **Command**: `uv run tama complete 999`
  - **Expected Outcome**: The command fails with a clear error message stating that the task with ID 999 was not found.

- **Test Case 2.2**: Task already completed.
  - **Prerequisites**: A task exists with ID 1, already in "done" status.
  - **Command**: `uv run tama complete 1`
  - **Expected Outcome**: The command exits gracefully with a message indicating the task is already done. No status change occurs.

### 3. Boundary and Edge Cases

- **Test Case 3.1**: Status propagation to subtasks.
  - **Prerequisites**: A parent task with ID 1 has several subtasks (`1.1`, `1.2`), all in "in-progress" status.
  - **Command**: `uv run tama complete 1 --propagate`
  - **Expected Outcome**: The command succeeds. `tama show 1` confirms that the parent task AND all of its subtasks are now "done".

- **Test Case 3.2**: Status propagation is disabled by default.
  - **Prerequisites**: Same as 3.1.
  - **Command**: `uv run tama complete 1` (without `--propagate`)
  - **Expected Outcome**: The command succeeds. Only the parent task's status is changed. The subtasks remain "in-progress".
