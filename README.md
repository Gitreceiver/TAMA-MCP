# Tama - AI-Powered Task Manager CLI ✨

![TAMA-icon|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504171218630.jpg)

[中文](https://github.com/Gitreceiver/TAMA-MCP/blob/main/README_zh.md)

Tama is a Command-Line Interface (CLI) tool designed for managing tasks, enhanced with AI capabilities for task generation and expansion. It utilizes AI (specifically configured for DeepSeek models via their OpenAI-compatible API) to parse Product Requirements Documents (PRDs) and break down complex tasks into manageable subtasks.

## Features

*   **Standard Task Management:** Add, list, show details, update status, and remove tasks and subtasks with dependency tracking.
*   **Dependency Management:** Add, remove, and track task dependencies with automatic cycle detection.
*   **AI-Powered PRD Parsing:** (`tama prd <filepath>`) Automatically generate a structured task list from a `.txt` or `.prd` file.
*   **AI-Powered Task Expansion:** (`tama expand <task_id>`) Break down a high-level task into detailed subtasks using AI.
*   **Dependency Checking:** (`tama deps`) Detect and visualize circular dependencies within your tasks.
*   **Reporting:** (`tama report [markdown|mermaid]`) Generate task reports in Markdown table format or as a Mermaid dependency graph.
*   **Code Stub Generation:** (`tama gen-file <task_id>`) Create placeholder code files based on task details.
*   **Next Task Suggestion:** (`tama next`) Identify the next actionable task based on status and dependencies.
*   **Rich CLI Output:** Uses `rich` for formatted and visually appealing console output (e.g., tables, panels).

## Installation & Setup
1.  **Clone the Repository:**

```shell
git clone https://github.com/Gitreceiver/TAMA-MCP.git
cd TAMA-MCP
```

  

2.  **Create and Activate Virtual Environment（Recommend python 3.12）:**

[uv install and usage](https://www.cnblogs.com/wang_yb/p/18635441)

```shell
uv venv -p 3.12

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

  
3.  **Install Dependencies & Project:**
    (Requires `uv` - install with `pip install uv` if you don't have it)
    ```shell
    uv pip install -e .
    ```

(Alternatively, if you use conda ,using pip: `pip install -e .`)

Once installed, the `tama` command will be available globally within your activated virtual environment.
### Accessing `tama` Globally

After following the installation steps, the `tama` command-line tool should be accessible globally *within the activated virtual environment*. You can run `tama --version` (or any other `tama` command) from any directory in your terminal.

**Troubleshooting:**

If you type `tama` and get a "command not found" error (or similar), try the following:
*   **Ensure Virtual Environment is Active:** The most common reason is that the virtual environment where you installed `tama` is not active. Refer to step 2 of the "Installation & Setup" section to activate it. You usually see the environment name in your terminal prompt (e.g., `(.venv)`) when it's active.
*   **Verify Installation Path:** In rare cases, the Python scripts directory might not be in your system's PATH. If you installed with `uv pip install -e .` or `pip install -e .`, the `tama` script is placed in the `bin` (Linux/macOS) or `Scripts` (Windows) directory of your virtual environment. When the virtual environment is active, this directory is automatically added to your PATH. If it's still not working, you might need to check your shell's PATH configuration or try reinstalling the package.
*   **Reinstall:** Try reinstalling the package: `uv pip install -e . --force-reinstall`

## Configuration ⚙️
Tama requires API keys for its AI features.
1.  Create a `.env` file in the project root directory.
   (You can copy the example file:)
   ```shell
   cp .env.example .env
   # Windows ：
   copy .env.example .env
   ```
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
```shell
tama list
tama list --status pending --priority high # Filter
```
The task list now includes emoji indicators for status and priority, and displays dependencies in a clear markdown table format.


*   **Show Task Details:**
```shell
tama show 1      # Show task 1
tama show 1.2    # Show subtask 2 of task 1
```

![tama-show|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162321747.png)

  

*   **Add Task/Subtask:**

```shell
# Add a top-level task
tama add "Implement user authentication" --desc "Handle login and sessions" --priority high

# Add a subtask to task 1
tama add "Create login API endpoint" --parent 1 --desc "Needs JWT handling"
```

![tama-add-1|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162324506.png)

![tama-add-2|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162327993.png)

  
*   **Set Task Status:**

```shell
tama status 1 done
tama status 1.2 in-progress
# Cascade update subtasks/dependent tasks status
tama status 1 done --propagate
```

*(Valid statuses: pending, in-progress, done, deferred, blocked, review)*

> `--propagate` param details：
> - `--propagate` controls whether status changes are cascaded to all subtasks or dependent tasks.
> - The default behavior is determined by the configuration file (settings.PROPAGATE_STATUS_CHANGE).
> - Explicitly adding --propagate forces the status update to be cascaded for this operation.


![tama-status1|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162329503.png)

![tama-status2|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162316531.png)

*   **Remove Task/Subtask:**
```shell
tama remove 2       # Remove task 2 and all its subtasks
tama remove 1.3     # Remove subtask 3 of task 1
```
When removing a task, all dependent tasks will be automatically updated, and you'll be notified of any affected dependencies.

*   **Manage Dependencies:**
```shell
tama add-dep 1 2      # Make task 1 depend on task 2
tama add-dep 1.2 2.1  # Make subtask 1.2 depend on subtask 2.1
tama rm-dep 1 2       # Remove dependency of task 1 on task 2
```

*   **Find Next Task:**
```shell
tama next
```

![tama-next|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162331771.png)

  

**AI Commands:**
*   **Parse PRD:** (Input file must be `.txt` or `.prd`)
```shell
tama prd path/to/your/document.txt
```

![tama-prd|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162316997.png)

*   **Expand Task:** (Provide a main task ID)

```shell
tama expand 1
```

![tama-expand|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504162317158.png)

  
**Utility Commands:**
*   **Check Dependencies:**

```shell
tama deps
```

*   **Generate Report:**
```shell
tama report markdown      # Print markdown table to console
tama report mermaid       # Print mermaid graph definition
tama report markdown --output report.md # Save to file
```

*   **Generate Placeholder File:**

```shell
tama gen-file 1
tama gen-file 2 --output-dir src/generated
```


**Shell Completion:**
*   Instructions for setting up shell completion can be obtained via:

```shell
tama --install-completion
```
*(Note: This might require administrator privileges depending on your shell and OS settings)*


## Development 🔧

If you modify the source code, remember to reinstall the package to make the changes effective in the CLI:
```shell
uv pip install -e .
```


## MCP Server Usage
Tama can be used as an MCP (Model Context Protocol) server, allowing other applications to interact with it programmatically. The MCP server provides the following tools:

- `list_tasks`: List all tasks, optionally filter by status or priority, returns a markdown table.
- `show_task`: Show details of a specific task or subtask by ID.
- `set_status`: Set the status of a task or subtask.
- `next_task`: Find the next actionable task.
- `add_task`: Add a new main task.
- `add_subtask`: Add a subtask to a main task.
- `remove_item`: Remove a task or subtask, with dependency cleanup.
- `add_dependency`: Add a dependency to a task or subtask.
- `remove_dependency`: Remove a dependency from a task or subtask.
- `check_dependencies`: Check for circular dependencies in all tasks.

To start the server:
```shell
uv --directory /path/to/your/TAMA_MCP run python -m src.mcp_server
```

in your mcp client: (cline,cursor,claude)

```json
{
  "mcpServers": {
    "TAMA-MCP-Server": {
        "command": "uv",
        "args": [
            "--directory",
            "/path/to/your/TAMA_MCP",
            "run",
            "python",
            "-m",
            "src.mcp_server"
        ],
        "disabled": false,
        "transportType": "stdio",
        "timeout": 60
    },
  }
}
```

## License

MIT License
This project is licensed under the MIT License. See the LICENSE file for details.

=======
# TAMA-MCP
AI-Powered Task Manager CLI with MCP Server

Contact me by wechat:
![b70873c85169d30dcfbff19a76f17fc.jpg|500](https://raw.gitmirror.com/Gitreceiver/Obsidian-pics/refs/heads/main/obsidian/202504302350685.jpg)