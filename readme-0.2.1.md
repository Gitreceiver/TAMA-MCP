# Tama - AI 驱动的任务管理命令行工具 ✨

[English](https://github.com/Gitreceiver/TAMA-MCP/blob/main/README.md)

Tama 是一个命令行界面 (CLI) 工具，专为任务管理而设计，并通过 AI 能力增强，用于任务生成和分解。它利用 AI（特别配置为通过 OpenAI 兼容 API 使用 DeepSeek 模型）来解析产品需求文档 (PRD) 并将复杂任务分解为可管理的子任务。
## 特性
*   **标准任务管理:** 添加、列出、显示详情、更新状态以及移除任务和子任务，支持依赖关系追踪。
*   **数据持久化:** 使用 **SQLite** 数据库存储任务数据，确保数据操作的稳定性和可靠性。
*   **依赖关系管理:** 添加、删除和追踪任务依赖关系，自动检测循环依赖。
*   **AI 驱动的 PRD 解析:** (`tama prd <文件路径>`) 从 `.txt` 或 `.prd` 文件自动生成结构化的任务列表。
*   **AI 驱动的任务分解:** (`tama expand <任务ID>`) 使用 AI 将高层级任务分解为详细的子任务。
*   **依赖检查:** (`tama deps`) 检测和可视化任务中的循环依赖。
*   **报告生成:** (`tama report [markdown|mermaid]`) 生成 Markdown 表格格式或 Mermaid 依赖关系图的任务报告。
*   **代码桩生成:** (`tama gen-file <任务ID>`) 基于任务详情创建占位符代码文件。
*   **下一任务建议:** (`tama next`) 根据状态和依赖关系识别下一个可执行的任务。
*   **富文本 CLI 输出:** 使用 `rich` 库提供格式化且视觉友好的控制台输出（例如表格、面板）。
*   **Git 集成:** 支持在开始和完成任务时自动创建分支和提交。
*   **文件关联:** 支持将文件链接到任务，方便追踪任务相关代码。

## 安装与设置
1.  **克隆仓库:**

```shell
git clone https://github.com/Gitreceiver/TAMA-MCP.git
cd TAMA-MCP
```

2.  **创建并激活虚拟环境(推荐3.12):**

uv的安装和使用的基本方法可以参考 [uv安装和使用](https://www.cnblogs.com/wang_yb/p/18635441)

```shell
uv venv -p 3.12

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3.  **安装依赖与项目:**

    (需要 `uv` - 如果没有，请使用 `pip install uv` 安装)

```shell
uv pip install -e .
```

    (conda可以使用 pip: `pip install -e .`)

    安装完成后，任务数据将存储在项目根目录下的 `tasks.db` SQLite数据库文件中。数据库会在首次运行时自动创建。

## 配置 ⚙️
Tama 的 AI 功能需要 API 密钥。
1.  在项目根目录创建一个 `.env` 文件。
   （你可以直接复制示例文件）
   ```shell
   cp .env.example .env
   # Windows 下可用：
   copy .env.example .env
   ```
2.  添加你的 DeepSeek API 密钥:

```dotenv
# .env 文件
DEEPSEEK_API_KEY="your_deepseek_api_key_here"
```

*(参考 `.env.example` 文件获取模板)*
   应用程序使用 `src/config/settings.py` 中定义的设置，该文件会从 `.env` 文件加载变量。

## 使用方法 🚀

Tama 命令需要在激活的虚拟环境下的终端中运行。
**核心命令:**
*   **列出任务:**
```shell
tama list
tama list --status pending --priority high # 筛选
```
任务列表现在包含状态和优先级的表情符号指示器，并以清晰的 markdown 表格格式显示依赖关系。

*   **显示任务详情:**

```shell
tama show 1       # 显示任务 1
tama show 1.2     # 显示任务 1 的子任务 2
```

*   **添加任务/子任务:**

```shell
# 添加顶级任务
tama add "实现用户认证" --desc "处理登录和会话" --priority high
# 为任务 1 添加子任务
tama add "创建登录 API 端点" --parent 1 --desc "需要处理 JWT"
```

*   **移除任务/子任务:**
```shell
tama remove 2       # 移除任务 2 及其所有子任务
tama remove 1.3     # 移除任务 1 的子任务 3
```
移除任务时，所有依赖该任务的其他任务将自动更新，并且系统会通知您受影响的依赖关系。

**工作流命令:**

*   **设置任务状态:**

```shell
tama status 1 done
tama status 1.2 in-progress
# 级联更新子任务/依赖任务状态
tama status 1 done --propagate
```

*(有效状态: pending, in-progress, done, deferred, blocked, review)*

> `--propagate` 参数说明：
> - `--propagate` 控制是否将状态变更级联到所有子任务或依赖任务。
> - 默认行为由配置文件决定（settings.PROPAGATE_STATUS_CHANGE）。
> - 显式添加 `--propagate` 可强制本次操作级联更新。

*   **开始任务:**
    此命令会将任务状态设置为 `in-progress`，并自动创建一个 Git 分支。

```shell
tama start 1
```

*   **完成任务:**
    此命令会将任务状态设置为 `done`。如果使用 `--commit` 标志，还会自动提交暂存的更改。

```shell
tama complete 1
tama complete 1 --commit
```

*   **查找下一个任务:**

```shell
tama next
```

**依赖关系命令:**

*   **管理依赖关系:**
```shell
tama add-dep 1 2      # 设置任务 1 依赖于任务 2
tama add-dep 1.2 2.1  # 设置子任务 1.2 依赖于子任务 2.1
tama remove-dep 1 2   # 移除任务 1 对任务 2 的依赖
```

*   **检查依赖:**

```shell
tama deps
```

**AI 命令:**

*   **解析 PRD:** (输入文件必须是 `.txt` 或 `.prd`)

```shell
tama prd path/to/your/document.txt
```

*   **分解任务:** (提供主任务 ID)

```shell
tama expand 1
```

**文件管理命令:**

*   **生成占位符文件:**

```shell
tama gen-file 1
tama gen-file 2 --output-dir src/generated
```

*   **关联文件:**
    将一个或多个文件链接到一个任务。

```shell
tama link 1 src/main.py
```

*   **取消文件关联:**
    从任务中移除一个或多个文件的链接。

```shell
tama unlink 1 src/main.py
```

*   **通过文件查找任务:**
    查找与指定文件关联的所有任务。

```shell
tama find-task src/main.py
```

**其他命令:**

*   **生成报告:**

```shell
tama report markdown       # 在控制台打印 Markdown 表格
tama report mermaid       # 打印 Mermaid 图定义
tama report markdown --output report.md # 保存到文件
```

**Shell 自动补全:**

*   可以通过以下命令获取设置 Shell 自动补全的说明:

```shell
tama --install-completion
```

*(注意: 根据你的 Shell 和操作系统设置，这可能需要管理员权限)*

## 开发 🔧

如果你修改了源代码，请记得重新安装包以使更改在 CLI 中生效:

```shell
uv pip install -e .
```

## MCP 服务器用法

Tama 可以用作 MCP（模型上下文协议）服务器，允许其他应用程序以编程方式与其交互。MCP 服务器提供以下工具：

- `list_tasks`：列出所有任务，可按状态或优先级过滤，返回 markdown 表格。
- `show_task`：根据 ID 显示指定任务或子任务的详细信息。
- `set_status`：设置任务或子任务的状态。
- `next_task`：查找下一个可执行的任务。
- `add_task`：添加新的主任务。
- `add_subtask`：为主任务添加子任务。
- `remove_item`：移除任务或子任务，并自动清理依赖。
- `add_dependency`：为任务或子任务添加依赖。
- `remove_dependency`：移除任务或子任务的依赖。
- `check_dependencies`：检查所有任务中的循环依赖。

要启动服务器，请运行：
```shell
uv --directory /path/to/your/TAMA_MCP run python -m src.mcp_server
```

客户端配置示例：

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

## 许可证

MIT 许可证

本项目采用 MIT 许可证授权。详见 LICENSE 文件。
