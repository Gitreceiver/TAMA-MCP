# Defines standardized prompts for interacting with the AI model.

# --- Task Generation from PRD ---

# Instructions for the AI on how to structure the output JSON
# This should align perfectly with the TasksData model in data_models.py
JSON_STRUCTURE_GUIDE = """
The output MUST be a valid JSON object with the following structure:
{
  "meta": {
    "projectName": "string (Extracted or inferred from PRD)",
    "version": "string (e.g., '1.0')"
  },
  "tasks": [
    {
      "id": integer (Start from 1, sequential),
      "title": "string (Concise task title)",
      "description": "string | null (Detailed description)",
      "status": "string (Default: 'pending')",
      "priority": "string ('high', 'medium', or 'low', inferred)",
      "dependencies": [integer | string] (List of IDs of tasks/subtasks this depends on, e.g., [1, "2.1"]),
      "details": "string | null (Any extra notes or context)",
      "test_strategy": "string | null (How to test this task)",
      "subtasks": [
        {
          "id": integer (Start from 1 for each parent, sequential),
          "title": "string (Concise subtask title)",
          "description": "string | null",
          "status": "string (Default: 'pending')",
          # Subtasks inherit priority from parent, no explicit field needed here
          "dependencies": [integer | string] (List of IDs, can depend on parent task's other subtasks e.g., [1] meaning subtask 3.1),
          "details": "string | null",
          "parent_task_id": integer (ID of the parent task) # MUST be included
        }
      ]
    }
  ]
}

- Ensure all fields match the specified types.
- Generate sequential IDs for tasks starting from 1.
- Generate sequential IDs for subtasks starting from 1 *within each parent task*.
- Infer dependencies logically based on the PRD flow. Use integer IDs for main tasks and "parent_id.subtask_id" format for subtask dependencies.
- Infer priority based on importance mentioned or implied in the PRD.
- **Crucially, ensure the 'meta' object contains a 'projectName' field extracted or inferred from the PRD.**
- Keep descriptions concise but informative.
- Provide a basic test strategy if applicable.
- Include the correct `parent_task_id` for all subtasks.
- Output ONLY the JSON object, with no introductory text or explanations.
"""

def get_generate_tasks_prompt(prd_content: str) -> str:
    """Generates the prompt for creating tasks from a PRD."""
    return f"""
Analyze the following Product Requirements Document (PRD) and generate a detailed, structured list of tasks required to implement the features described.

**PRD Content:**
```
{prd_content}
```

**Instructions:**
{JSON_STRUCTURE_GUIDE}
"""

# --- Subtask Expansion ---

# Instructions for the AI on how to structure the subtask list JSON
SUBTASK_JSON_STRUCTURE_GUIDE = """
The output MUST be a valid JSON list containing subtask objects with the following structure:
[
  {
    "title": "string (Concise subtask title)",
    "description": "string | null (Detailed description)",
    # Status, priority, and parent_task_id will be handled by the calling code
    "dependencies": [integer | string] (List of IDs of *other subtasks within the same parent* this depends on, e.g., [1] meaning the first subtask in this list),
    "details": "string | null (Any extra notes or context)"
  }
]

- Break the parent task down into logical, actionable steps.
- Infer dependencies *only between the generated subtasks*. Use the sequential index (starting from 1) of the subtask in the generated list as the dependency ID.
- Keep titles and descriptions focused.
- Output ONLY the JSON list, with no introductory text or explanations.
"""

def get_expand_subtasks_prompt(task_title: str, task_description: str | None, context: str) -> str:
    """Generates the prompt for expanding a task into subtasks."""
    return f"""
Break down the following main task into smaller, actionable subtasks based on the provided context.

**Main Task Title:** {task_title}
**Main Task Description:** {task_description or 'N/A'}

**Context:**
```
{context}
```

**Instructions:**
{SUBTASK_JSON_STRUCTURE_GUIDE}
"""
