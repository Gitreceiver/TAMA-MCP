# Tama - AI 驱动的任务管理命令行工具 ✨

Tama 是一个命令行界面 (CLI) 工具，专为任务管理而设计，并通过 AI 能力增强，用于任务生成和分解。它利用 AI（特别配置为通过 OpenAI 兼容 API 使用 DeepSeek 模型）来解析产品需求文档 (PRD) 并将复杂任务分解为可管理的子任务。

## 特性

*   **标准任务管理:** 添加、列出、显示详情、更新状态以及移除任务和子任务。
*   **AI 驱动的 PRD 解析:** (`tama prd <文件路径>`) 从 `.txt` 或 `.prd` 文件自动生成结构化的任务列表。
*   **AI 驱动的任务分解:** (`tama expand <任务ID>`) 使用 AI 将高层级任务分解为详细的子任务。
*   **依赖检查:** (`tama deps`) 检测任务中的循环依赖。
*   **报告生成:** (`tama report [markdown|mermaid]`) 生成 Markdown 表格格式或 Mermaid 依赖关系图的任务报告。
*   **代码桩生成:** (`tama gen-file <任务ID>`) 基于任务详情创建占位符代码文件。
*   **下一任务建议:** (`tama next`) 根据状态和依赖关系识别下一个可执行的任务。
*   **富文本 CLI 输出:** 使用 `rich` 库提供格式化且视觉友好的控制台输出（例如表格、面板）。

## 安装与设置

1.  **克隆仓库:**
    ```bash
    git clone <your-repository-url>
    cd tama-project-directory
    ```
2.  **创建并激活虚拟环境(推荐3.12):**
    ```bash
    uv venv -p 3.12
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    # source .venv/bin/activate
    ```
3.  **安装依赖与项目:**
    (需要 `uv` - 如果没有，请使用 `pip install uv` 安装)
    ```bash
    uv pip install .
    ```
    (或者使用 pip: `pip install .`)

## 配置 ⚙️

Tama 的 AI 功能需要 API 密钥。

1.  在项目根目录创建一个 `.env` 文件。
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
    ```bash
    tama list
    tama list --status pending --priority high # 筛选
    ```
*   **显示任务详情:**
    ```bash
    tama show 1       # 显示任务 1
    tama show 1.2     # 显示任务 1 的子任务 2
    ```
*   **添加任务/子任务:**
    ```bash
    # 添加顶级任务
    tama add "实现用户认证" --desc "处理登录和会话" --priority high

    # 为任务 1 添加子任务
    tama add "创建登录 API 端点" --parent 1 --desc "需要处理 JWT"
    ```
*   **设置任务状态:**
    ```bash
    tama status 1 done
    tama status 1.2 in-progress
    ```
    *(有效状态: pending, in-progress, done, deferred, blocked, review)*
*   **移除任务/子任务:**
    ```bash
    tama remove 2
    tama remove 1.3
    ```
*   **查找下一个任务:**
    ```bash
    tama next
    ```

**AI 命令:**

*   **解析 PRD:** (输入文件必须是 `.txt` 或 `.prd`)
    ```bash
    tama prd path/to/your/document.txt
    ```
*   **分解任务:** (提供主任务 ID)
    ```bash
    tama expand 1
    ```

**工具命令:**

*   **检查依赖:**
    ```bash
    tama deps
    ```
*   **生成报告:**
    ```bash
    tama report markdown       # 在控制台打印 Markdown 表格
    tama report mermaid        # 打印 Mermaid 图定义
    tama report markdown --output report.md # 保存到文件
    ```
*   **生成占位符文件:**
    ```bash
    tama gen-file 1
    tama gen-file 2 --output-dir src/generated
    ```

**Shell 自动补全:**

*   可以通过以下命令获取设置 Shell 自动补全的说明:
    ```bash
    tama --install-completion
    ```
    *(注意: 根据你的 Shell 和操作系统设置，这可能需要管理员权限)*

## 开发 🔧

如果你修改了源代码，请记得重新安装包以使更改在 CLI 中生效:

```bash
uv pip install .
```

## 许可证

(假设为 MIT 许可证 - 如果不正确请更新)

本项目采用 MIT 许可证授权。详见 LICENSE 文件。
