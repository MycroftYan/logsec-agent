"""【第 4 周 · 同学 D】上下文管理 —— 目前只有占位，需要你来实现。

背景：
  多轮对话越聊越长、工具一次返回很多事件，都会把模型的"上下文窗口"塞满，
  导致变慢、变贵，甚至报错。AgentScope 用 ContextConfig 管两件事：
    - 自动压缩：上下文快满时，把较早的对话总结成一段摘要；
    - 工具结果截断：单个工具结果超过 tool_result_limit 个 token 就截断。

要做什么：
  1. 实现 make_context_config()，返回一个 ContextConfig（参数自己选，并在注释里写为什么）。
     为了方便演示，可以先把阈值设得很低（比如 trigger_ratio 小一点，或给模型设小的 context_size），
     这样聊几轮就能看到压缩发生。
  2. 做开/关对比：同一组多轮问题，ENABLE_CONTEXT_MANAGEMENT 为 True / False 各跑一遍，
     记录每轮的 token 用量（ask.py 末尾会打印）和回答是否还正确，写进 README 或一份小报告。

怎么算做完（验收）：
  - config.ENABLE_CONTEXT_MANAGEMENT = True 后，chat.py 能正常多轮对话；
  - 有一张开/关对比的表格（轮数、token 用量、回答质量）；
  - 能指出压缩发生在哪一轮（ConsoleRenderer 的 debug 模式或 on_compress_context 中间件可以看到）。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/context/compress-context.md
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/context/overview.md
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/agent/configure-agent.md （With Custom Context Config）
"""

from logsec.errors import not_done_yet


def make_context_config():
    """（待实现）返回 agentscope.agent.ContextConfig(...)。

    示例写法（来自官方文档，参数需要你自己斟酌）：
        from agentscope.agent import ContextConfig
        return ContextConfig(trigger_ratio=0.7, reserve_ratio=0.2, tool_result_limit=1000)
    """
    not_done_yet("第 4 周", "上下文管理（ContextConfig 自动压缩 + 工具结果截断）", "logsec/context.py")
