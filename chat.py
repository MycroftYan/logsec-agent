"""终端多轮对话：python chat.py

用的是 AgentScope 自带的 launch_console：输入问题回车即可，agent 会记住同一次运行里之前聊过的内容。
输入 exit 或 quit（或按 Ctrl+D）退出；回答过程中按 Ctrl+C 可以打断当前回答。

API key 可以三种方式给：--api-key 参数 / 环境变量 DEEPSEEK_API_KEY / .env 文件（推荐 .env）。

参考文档：https://docs.agentscope.io/en/versions/2.0.12/building-blocks/console.md
"""

import argparse
import asyncio
import sys

from agentscope.console import launch_console

import config
from logsec.agent import build_agent
from logsec.errors import NotDoneYet, SetupError


async def chat(api_key: str | None = None, model_name: str | None = None, max_iters: int | None = None) -> None:
    agent = build_agent(api_key=api_key, model_name=model_name, max_iters=max_iters)
    print("日志安全分析 agent 已启动。试试问：case_000 里有暴力破解的迹象吗？（输入 exit 退出）")
    if config.ENABLE_FANCY_UI:  # 第 6 周
        from logsec.ui import launch_fancy_ui

        await launch_fancy_ui(agent)
    else:
        await launch_console(agent, max_tool_result_lines=8)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="和日志安全分析 agent 多轮对话",
        epilog="API key 优先级：--api-key 参数 > 环境变量 DEEPSEEK_API_KEY > .env 文件。",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="临时指定 DeepSeek API key（不想写进 .env 时用；注意会留在命令历史里）",
    )
    parser.add_argument("--model", default=None, help="临时换模型，默认 deepseek-flash")
    parser.add_argument("--max-iters", type=int, default=None, help="ReAct 最多循环几轮，默认 10")
    args = parser.parse_args()

    try:
        asyncio.run(
            chat(api_key=args.api_key, model_name=args.model, max_iters=args.max_iters)
        )
    except (SetupError, NotDoneYet) as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
