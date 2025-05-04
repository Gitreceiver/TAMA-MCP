import os
import logging
from dotenv import load_dotenv

# 日志等级类型
# LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
# 优先级类型
# Priority = Literal["low", "medium", "high"]

# 加载 .env 文件（路径相对于本文件）
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path=dotenv_path)

# --- DeepSeek 配置 ---
# API 密钥（必填）
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', None)
# API 基础地址
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
# 通用模型
DEEPSEEK_GENERAL_MODEL = os.getenv('DEEPSEEK_GENERAL_MODEL', 'deepseek-chat')
# 推理/编码模型
DEEPSEEK_REASONING_MODEL = os.getenv('DEEPSEEK_REASONING_MODEL', 'deepseek-reasoner')

# --- AI 通用设置 ---
# AI 响应最大 token 数
AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 8192))
# AI 温度参数
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.7))

# --- 应用设置 ---
# 主任务文件路径
TASKS_JSON_PATH = os.path.abspath(os.getenv('TASKS_JSON_PATH', 'tasks.json'))
# 任务文件夹路径
TASKS_DIR_PATH = os.getenv('TASKS_DIR_PATH', 'tasks')
# 日志等级
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
# 默认优先级
DEFAULT_PRIORITY = os.getenv('DEFAULT_PRIORITY', 'medium')  # low, medium, high
# 默认子任务数
DEFAULT_SUBTASKS = int(os.getenv('DEFAULT_SUBTASKS', 3))
# 项目名称
PROJECT_NAME = os.getenv('PROJECT_NAME', 'My Python Task Manager')
# 项目版本
PROJECT_VERSION = os.getenv('PROJECT_VERSION', '0.1.0')
# 是否开启调试模式
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
# 是否主任务状态变更时级联影响子任务
# 默认值为False，即不级联（如需级联请在.env中设置PROPAGATE_STATUS_CHANGE=True）
PROPAGATE_STATUS_CHANGE = os.getenv('PROPAGATE_STATUS_CHANGE', 'False').lower() in ('true', '1', 'yes')

# --- 临时调试日志 ---
config_logger = logging.getLogger("config.settings")
if DEEPSEEK_API_KEY:
    config_logger.debug(f"[CONFIG DEBUG] Loaded DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:5]}...{DEEPSEEK_API_KEY[-4:]}")
else:
    config_logger.debug("[CONFIG DEBUG] DEEPSEEK_API_KEY not found.")

# 用法示例：from src.config import settings
# print(DEEPSEEK_API_KEY)

# 封装为Settings类，便于外部统一导入
class Settings:
    def __init__(self):
        self.DEEPSEEK_API_KEY = DEEPSEEK_API_KEY
        self.DEEPSEEK_BASE_URL = DEEPSEEK_BASE_URL
        self.DEEPSEEK_GENERAL_MODEL = DEEPSEEK_GENERAL_MODEL
        self.DEEPSEEK_REASONING_MODEL = DEEPSEEK_REASONING_MODEL
        self.AI_MAX_TOKENS = AI_MAX_TOKENS
        self.AI_TEMPERATURE = AI_TEMPERATURE
        self.TASKS_JSON_PATH = TASKS_JSON_PATH
        self.TASKS_DIR_PATH = TASKS_DIR_PATH
        self.LOG_LEVEL = LOG_LEVEL
        self.DEFAULT_PRIORITY = DEFAULT_PRIORITY
        self.DEFAULT_SUBTASKS = DEFAULT_SUBTASKS
        self.PROJECT_NAME = PROJECT_NAME
        self.PROJECT_VERSION = PROJECT_VERSION
        self.DEBUG = DEBUG
        self.PROPAGATE_STATUS_CHANGE = PROPAGATE_STATUS_CHANGE

# 导出settings实例，供外部import
settings = Settings()
