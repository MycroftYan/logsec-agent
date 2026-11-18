"""【第 6 周 · 同学 D】更好的界面 / 调用轨迹展示 —— 目前只有占位，需要你来实现。

背景：
  现在 chat.py 用的是 AgentScope 自带的 launch_console（逐行打印，能看到工具调用）。
  演示和答辩时，最好有一个更直观的界面，能看清 agent "想了什么、调了什么工具、拿到什么结果"。

要做什么（三选一，做完一个就算完成，写清楚选了哪个）：
  A. 全屏终端界面：AgentScope 自带 launch_tui（需要 pip install "agentscope[tui]==2.0.12"）。
  B. 网页界面：用 gradio 或 streamlit 写一个聊天页面，左边对话、右边列出本轮的工具调用和结果。
     （对话驱动用 agent.reply_stream()，事件类型见 message-and-event 文档。）
  C. 调用轨迹导出：每次回答后把工具调用序列、参数、结果摘要、token 用量写成一个 HTML 或 Markdown 文件。

怎么算做完（验收）：
  - config.ENABLE_FANCY_UI = True 后，python chat.py 打开的是你的界面；
  - 能完整演示一轮"提问 -> 调工具 -> 带 uid 的回答"，并能看到每次工具调用。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/console.md （launch_tui、ConsoleRenderer）
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/message-and-event.md （事件类型）
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/middleware.md （Tracing 一节，可接 OpenTelemetry）
"""

from logsec.errors import not_done_yet


async def launch_fancy_ui(agent) -> None:
    """（待实现）用你选的界面和 agent 对话。"""
    not_done_yet("第 6 周", "网页界面 / 全屏界面 / 调用轨迹展示", "logsec/ui.py")
