"""把"模型 + 工具 + 提示词 + 各种组件"组装成一个 ReAct agent。

ReAct = Reasoning（想）+ Acting（做）：
  模型先想"我需要什么信息"，然后调用工具；看到工具结果后再想下一步，
  如此循环，直到它认为证据够了，给出最终回答。这个循环由 AgentScope 的 Agent 类负责，
  我们只需要把零件交给它。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/agent/configure-agent.md
"""

import os

from agentscope.agent import Agent, ReActConfig
from agentscope.credential import DeepSeekCredential
from agentscope.model import DeepSeekChatModel
from agentscope.tool import Toolkit
from dotenv import dotenv_values, load_dotenv

import config
from logsec.errors import SetupError
from logsec.prompts import build_system_prompt
from logsec.tools import build_tools


def load_api_key(cli_key: str | None = None) -> str:
    """读取 DeepSeek API key。

    优先级：命令行参数（--api-key）> 环境变量 DEEPSEEK_API_KEY > .env 文件。
    三种方式都不会把 key 写进代码。日常推荐用 .env，临时换 key 才用命令行参数。
    """
    if cli_key and cli_key.strip():
        return cli_key.strip()
    load_dotenv(config.ENV_FILE)  # 默认不覆盖已有的环境变量，所以环境变量优先于 .env
    key = os.getenv(config.API_KEY_ENV, "").strip()
    if not key:
        raise SetupError(
            f"没有找到 {config.API_KEY_ENV}。三种填 key 的方式任选一种：\n"
            f"  1) 把 .env.example 复制成 .env，填 {config.API_KEY_ENV}=你的key（推荐）\n"
            f"  2) 设置环境变量：$env:{config.API_KEY_ENV}=\"你的key\"（PowerShell）\n"
            f"  3) 运行时传参：python ask.py \"问题\" --api-key sk-xxx（最省事，但会留在命令历史里）"
        )
    return key


def key_source(cli_key: str | None = None) -> str:
    """key 是从哪来的（只用于打印提示，不返回 key 本身）。

    注意 load_dotenv() 会把 .env 的内容塞进 os.environ，所以读完 .env 之后
    光看环境变量分不清来源；这里直接读 .env 文件的值和进程环境变量做对比。
    """
    if cli_key and cli_key.strip():
        return "命令行参数 --api-key"
    file_key = (dotenv_values(config.ENV_FILE) or {}).get(config.API_KEY_ENV, "").strip()
    env_key = os.getenv(config.API_KEY_ENV, "").strip()
    if file_key and env_key == file_key:
        return f".env 文件（{config.ENV_FILE.name}）"
    if env_key:
        return f"环境变量 {config.API_KEY_ENV}"
    return "没找到（启动时会报错）"


def build_model(api_key: str | None = None, model_name: str | None = None) -> DeepSeekChatModel:
    return DeepSeekChatModel(
        credential=DeepSeekCredential(api_key=load_api_key(api_key)),
        model=model_name or config.MODEL_NAME,
    )


def build_agent(
    api_key: str | None = None,
    model_name: str | None = None,
    max_iters: int | None = None,
) -> Agent:
    """组装 agent。config.py 里的开关决定要不要加上后面几周的组件。

    三个参数都是为了临时覆盖 config.py 里的默认值（主要是换 key、换模型、调循环上限）：
      api_key      命令行传入的 API key，None 表示按环境变量 / .env 读
      model_name   模型名，None 表示用 config.MODEL_NAME
      max_iters    ReAct 最多循环几轮，None 表示用 config.MAX_ITERS
    """
    if not config.DB_PATH.exists():
        raise SetupError("找不到数据库 data/logsec.db，请先运行：python scripts/build_db.py")

    middlewares = []
    if config.ENABLE_MEMORY:  # 第 5 周
        from logsec.memory import make_memory_middleware
        middlewares.append(make_memory_middleware())
    if config.ENABLE_EVIDENCE_CHECK:  # 第 6 周
        from logsec.evidence import make_evidence_middleware
        middlewares.append(make_evidence_middleware())

    context_config = None  # None = 用 AgentScope 的默认设置
    if config.ENABLE_CONTEXT_MANAGEMENT:  # 第 4 周
        from logsec.context import make_context_config
        context_config = make_context_config()

    return Agent(
        name="LogSec",
        system_prompt=build_system_prompt(),
        model=build_model(api_key, model_name),
        toolkit=Toolkit(tools=build_tools()),
        middlewares=middlewares,
        context_config=context_config,
        react_config=ReActConfig(max_iters=max_iters or config.MAX_ITERS),
    )
