"""全局配置：路径、模型、工具输出上限，以及"后面几周才做"的功能开关。

同学们以后加功能，主要就是：
  1. 在对应的占位文件里把功能写出来；
  2. 回到这里把开关改成 True；
  3. 跑一遍 README 里写的验收方法。

开关打开但功能还没写时，程序会打印"第 X 周任务，尚未实现"并退出，不会静默忽略。
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 路径（全部用 pathlib，Windows / macOS 通用）
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
EVTX_CSV = RAW_DIR / "evtx_data.csv"
SSH_LOG = RAW_DIR / "OpenSSH_2k.log"
DB_PATH = PROJECT_DIR / "data" / "logsec.db"
ENV_FILE = PROJECT_DIR / ".env"

# ---------------------------------------------------------------------------
# 模型（DeepSeek）。API key 只从环境变量 / .env 读取，绝不写进代码。
# ---------------------------------------------------------------------------
MODEL_NAME = "deepseek-flash"  # 另一个可选：deepseek-v4-pro（更强、更贵）
API_KEY_ENV = "DEEPSEEK_API_KEY"
MAX_ITERS = 10  # ReAct 最多循环几轮（想一次 + 调一次工具 = 一轮）

# ---------------------------------------------------------------------------
# 工具输出上限：返回给模型的文字越短，花的 token 越少
# ---------------------------------------------------------------------------
MAX_ROWS = 20          # 一次搜索最多返回多少条事件
MAX_CASES = 30         # 一次最多列出多少个案件
MAX_FIELD_CHARS = 300  # 单个字段值最长多少字符（太长就截断）

# ---------------------------------------------------------------------------
# 后续周的功能开关（默认全部关闭）
# 打开前先去对应文件把功能写完，详见 README 的"按周待办"。
# ---------------------------------------------------------------------------
ENABLE_EXTRA_TOOLS = False         # 第 3 周：时间窗上下文 / 统计 / ATT&CK 说明工具  -> logsec/tools_week3.py
ENABLE_ANSWER_FORMAT = False       # 第 3 周：要求输出"战术判断 + 证据 uid"固定格式 -> logsec/prompts.py
ENABLE_CONTEXT_MANAGEMENT = False  # 第 4 周：ContextConfig 自动压缩 + 工具结果截断  -> logsec/context.py
ENABLE_MEMORY = False              # 第 5 周：AgenticMemoryMiddleware 长期记忆       -> logsec/memory.py
ENABLE_EVIDENCE_CHECK = False      # 第 6 周：检查回答里引用的 uid 是否真实存在       -> logsec/evidence.py
ENABLE_FANCY_UI = False            # 第 6 周：网页界面 / 全屏界面 / 调用轨迹展示      -> logsec/ui.py
