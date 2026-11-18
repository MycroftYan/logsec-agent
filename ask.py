"""单次提问：python ask.py "你的问题"

会实时打印 agent 的思考过程、每次工具调用和结果（用 AgentScope 自带的 ConsoleRenderer），
最后再打印一份小结：调用了哪些工具、花了多少 token。适合演示 ReAct 过程。

加 --quiet 只看最终回答。
API key 可以三种方式给：--api-key 参数 / 环境变量 DEEPSEEK_API_KEY / .env 文件（推荐 .env）。
"""

import argparse
import asyncio
import sys

from agentscope.console import ConsoleRenderer
from agentscope.event import EventType
from agentscope.message import Msg, UserMsg

from logsec.agent import build_agent
from logsec.errors import NotDoneYet, SetupError


def print_summary(calls: dict, final: Msg) -> None:
    """按顺序列出本次回答中所有工具调用，再打印 token 用量。"""
    print("\n" + "=" * 60)
    print(f"工具调用序列（共 {len(calls)} 次）：")
    for i, (name, args) in enumerate(calls.values(), start=1):
        print(f"  {i}. {name}({args})")
    if final is not None and final.usage:
        print(f"token 用量（本次回答所有模型调用合计）：输入 {final.usage.input_tokens}，输出 {final.usage.output_tokens}")
    if final is not None:
        print(f"结束原因：{final.finished_reason}")


async def ask(
    question: str,
    quiet: bool = False,
    api_key: str | None = None,
    model_name: str | None = None,
    max_iters: int | None = None,
) -> tuple[dict, Msg]:
    agent = build_agent(api_key=api_key, model_name=model_name, max_iters=max_iters)
    renderer = ConsoleRenderer(verbosity="quiet" if quiet else "default", max_tool_result_lines=8)
    calls = {}  # 工具调用编号 -> [工具名, 参数文本]
    final = None
    # reply_stream 会一边运行一边吐出事件（模型输出的文字、工具调用、工具结果……）；
    # yield_final_msg=True 让它最后再吐出完整的回答消息。
    async for item in agent.reply_stream(UserMsg(name="user", content=question), yield_final_msg=True):
        if isinstance(item, Msg):
            final = item
            continue
        renderer.render(item)  # 交给 AgentScope 自带的渲染器打印
        # 顺便记下工具调用：START 事件带工具名，DELTA 事件一段段带来参数
        if item.type == EventType.TOOL_CALL_START:
            calls[item.tool_call_id] = [item.tool_call_name, ""]
        elif item.type == EventType.TOOL_CALL_DELTA and item.tool_call_id in calls:
            calls[item.tool_call_id][1] += item.delta
    print_summary(calls, final)
    return calls, final


def main() -> None:
    # Windows 终端默认编码可能不是 UTF-8，这里统一一下，避免中文乱码或报错
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="向日志安全分析 agent 提一个问题",
        epilog="API key 优先级：--api-key 参数 > 环境变量 DEEPSEEK_API_KEY > .env 文件。",
    )
    parser.add_argument("question", help='问题，例如 "case_000 里有暴力破解吗？"')
    parser.add_argument("--quiet", action="store_true", help="只显示最终回答")
    parser.add_argument(
        "--api-key",
        default=None,
        help="临时指定 DeepSeek API key（不想写进 .env 时用；注意会留在命令历史里）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="临时换模型，默认用 config.py 里的 deepseek-flash；可选 deepseek-v4-pro（更强更贵）",
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=None,
        help="ReAct 最多循环几轮，默认 10（config.MAX_ITERS）",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            ask(
                args.question,
                args.quiet,
                api_key=args.api_key,
                model_name=args.model,
                max_iters=args.max_iters,
            )
        )
    except (SetupError, NotDoneYet) as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
