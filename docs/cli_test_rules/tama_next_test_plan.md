# Test Plan for `tama next`

This document outlines the test plan for the `tama next` command.

## Command Synopsis

`tama next`

## Test Cases

### 1. Happy Path

- **Test Case 1.1**: Find the next available task.
  - **Prerequisites**: Several tasks exist. Task 1 is "done". Task 2 is "pending" with high priority and no dependencies. Task 3 is "pending" with medium priority.
  - **Command**: `uv run tama next`
  - **Expected Outcome**: The command succeeds and displays the details for Task 2, as it is the highest-priority pending task.

- **Test Case 1.2**: Dependency blocking.
  - **Prerequisites**: Task 1 is "pending". Task 2 is "pending" and depends on Task 1.
  - **Command**: `uv run tama next`
  - **Expected Outcome**: The command displays the details for Task 1. Task 2 is not shown because its dependency is not met.

### 2. Boundary and Edge Cases

- **Test Case 2.1**: No eligible tasks.
  - **Prerequisites**: All tasks are either "done" or "in-progress", or are blocked by pending dependencies.
  - **Command**: `uv run tama next`
  - **Expected Outcome**: The command exits gracefully with a message indicating that no eligible tasks were found.

- **Test Case 2.2**: No tasks at all.
  - **Prerequisites**: The task database is empty.
  - **Command**: `uv run tama next`
  - **Expected Outcome**: The command exits gracefully with a message indicating that no tasks were found.

- **Test Case 2.3**: Dependency as a string.
  - **Prerequisites**: Task 1 is "pending". Task 2 is "pending" and depends on Task 1, with the dependency specified as a string ("1").
  - **Command**: `uv run tama next`
  - **Expected Outcome**: The command displays the details for Task 1. Task 2 is not shown because its dependency is not met. This test case was added to address a bug where string dependencies were not correctly parsed.
