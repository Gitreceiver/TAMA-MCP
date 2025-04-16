# Tama - AI-Powered Task Manager CLI ✨

Tama is a Command-Line Interface (CLI) tool designed for managing tasks, enhanced with AI capabilities for task generation and expansion. It utilizes AI (specifically configured for DeepSeek models via their OpenAI-compatible API) to parse Product Requirements Documents (PRDs) and break down complex tasks into manageable subtasks.

## Features

*   **Standard Task Management:** Add, list, show details, update status, and remove tasks and subtasks.
*   **AI-Powered PRD Parsing:** (`tama prd <filepath>`) Automatically generate a structured task list from a `.txt` or `.prd` file.
*   **AI-Powered Task Expansion:** (`tama expand <task_id>`) Break down a high-level task into detailed subtasks using AI.
*   **Dependency Checking:** (`tama deps`) Detect circular dependencies within your tasks.
*   **Reporting:** (`tama report [markdown|mermaid]`) Generate task reports in Markdown table format or as a Mermaid dependency graph.
*   **Code Stub Generation:** (`tama gen-file <task_id>`) Create placeholder code files based on task details.
*   **Next Task Suggestion:** (`tama next`) Identify the next actionable task based on status and dependencies.
*   **Rich CLI Output:** Uses `rich` for formatted and visually appealing console output (e.g., tables, panels).

## Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd tama-project-directory 
    ```
2.  **Create and Activate Virtual Environment（Recommend python 3.12）:**
    ```bash
    uv venv -p 3.12
    # Windows
    .\.venv\Scripts\activate 
    # macOS/Linux
    # source .venv/bin/activate 
    ```
3.  **Install Dependencies & Project:**
    (Requires `uv` - install with `pip install uv` if you don't have it)
    ```bash
    uv pip install .
    ```
    (Alternatively, using pip: `pip install .`)

## Configuration ⚙️

Tama requires API keys for its AI features.

1.  Create a `.env` file in the project root directory.
2.  Add your DeepSeek API key:

    ```dotenv
    # .env file
    DEEPSEEK_API_KEY="your_deepseek_api_key_here" 
    ```
    *(See `.env.example` for a template)*

    The application uses settings defined in `src/config/settings.py`, which loads variables from the `.env` file.

## Usage 🚀

Tama commands are run from your terminal within the activated virtual environment.

**Core Commands:**

*   **List Tasks:**
    ```bash
    tama list 
    tama list --status pending --priority high # Filter
    ```
*   **Show Task Details:**
    ```bash
    tama show 1       # Show task 1
    tama show 1.2     # Show subtask 2 of task 1
    ```
*   **Add Task/Subtask:**
    ```bash
    # Add a top-level task
    tama add "Implement user authentication" --desc "Handle login and sessions" --priority high

    # Add a subtask to task 1
    tama add "Create login API endpoint" --parent 1 --desc "Needs JWT handling" 
    ```
*   **Set Task Status:**
    ```bash
    tama status 1 done 
    tama status 1.2 in-progress
    ```
    *(Valid statuses: pending, in-progress, done, deferred, blocked, review)*
*   **Remove Task/Subtask:**
    ```bash
    tama remove 2
    tama remove 1.3
    ```
*   **Find Next Task:**
    ```bash
    tama next
    ```

**AI Commands:**

*   **Parse PRD:** (Input file must be `.txt` or `.prd`)
    ```bash
    tama prd path/to/your/document.txt
    ```
*   **Expand Task:** (Provide a main task ID)
    ```bash
    tama expand 1 
    ```

**Utility Commands:**

*   **Check Dependencies:**
    ```bash
    tama deps
    ```
*   **Generate Report:**
    ```bash
    tama report markdown       # Print markdown table to console
    tama report mermaid        # Print mermaid graph definition
    tama report markdown --output report.md # Save to file
    ```
*   **Generate Placeholder File:**
    ```bash
    tama gen-file 1 
    tama gen-file 2 --output-dir src/generated
    ```

**Shell Completion:**

*   Instructions for setting up shell completion can be obtained via:
    ```bash
    tama --install-completion
    ```
    *(Note: This might require administrator privileges depending on your shell and OS settings)*

## Development 🔧

If you modify the source code, remember to reinstall the package to make the changes effective in the CLI:

```bash
uv pip install . 
```

## License

(Assumed MIT License - Please update if incorrect)

This project is licensed under the MIT License. See the LICENSE file for details.
