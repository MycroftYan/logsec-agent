"""【第 5 周 · 同学 D】长期记忆 —— 目前只有占位，需要你来实现。

背景：
  现在每次启动 agent 都是"失忆"的。长期记忆让 agent 把重要结论写成 Markdown 文件，
  下次启动还能读到。AgentScope 提供 AgenticMemoryMiddleware：agent 自己用 Read/Write/Edit
  工具在 workdir/Memory/ 下维护记忆文件，并把索引 MEMORY.md 自动放进系统提示词。

要做什么：
  1. 实现 make_memory_middleware()，返回 AgenticMemoryMiddleware(workdir=...)。
     workdir 建议用 config.PROJECT_DIR / "memory"（.gitignore 已排除这个目录）。
  2. 记忆中间件需要 Read / Write / Edit 三个内置工具，并且要允许它们写 workdir：
     在 logsec/agent.py 里把这三个工具加进 Toolkit，并按文档设置
     PermissionMode.ACCEPT_EDITS + working_directories（只放行 memory 目录，别放行整个项目）。
  3. 在系统提示词里规定"记什么、不记什么"：
       记：已确认的结论（如"case_000 中 IP x 是暴力破解源"）、常见误报（如"某系统进程的某行为是正常的"）；
       不记：未经证实的猜测、原始日志大段内容。
  4. 想一想评测时的问题：如果记忆里存了某个案件的结论，再评测同一个案件就等于"开卷"了。
     评测时应该清空或关闭记忆，写在你的说明里。

怎么算做完（验收）：
  - config.ENABLE_MEMORY = True 后，第一次 chat.py 里让 agent 分析一个案件并要求它记住结论；
    退出、重新启动 chat.py，问"你之前对 case_xxx 的结论是什么"，它能答上来；
  - memory/Memory/ 下能看到它写的 .md 文件，内容符合上面"记什么"的规定。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/long-term-memory.md （Agentic Memory 一节）
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/permission-system/permission-mode.md
"""

from logsec.errors import not_done_yet


def make_memory_middleware():
    """（待实现）返回 agentscope.middleware.AgenticMemoryMiddleware(workdir=...)。"""
    not_done_yet("第 5 周", "长期记忆（AgenticMemoryMiddleware）", "logsec/memory.py")
