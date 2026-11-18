"""【第 6 周 · 同学 D】证据校验 —— 目前只有占位，需要你来实现。

背景：
  系统提示词要求"每个结论都引用事件 uid"，但模型仍可能编造一个不存在的 uid。
  我们用 AgentScope 的"中间件"在 agent 回答结束前做一道检查。

要做什么：
  写一个 MiddlewareBase 的子类，在 on_reply 钩子里：
    1. 拿到 agent 最终回答的文字，用正则（如 r"E\\d{5}"）找出所有引用的 uid；
    2. 用 logsec.db.connect_readonly() 查 events 表，看哪些 uid 不存在；
    3. 处理方式二选一（写清楚你选了哪个、为什么）：
       a. 简单版：在回答末尾追加一行"证据校验：E12345 不存在"；
       b. 进阶版：吞掉结束事件、往上下文里加一条提示让模型改正，再跑一轮（文档里
          ContinueOnceMiddleware 的写法），注意设置最多重试次数，防止死循环。
    4. 顺便统计"回答里一个 uid 都没引用"的情况，也给出提示。

怎么算做完（验收）：
  - config.ENABLE_EVIDENCE_CHECK = True 后，正常提问不受影响；
  - 写一个不调模型的测试：构造一段含假 uid（如 E99999）的文字，校验函数能把它找出来；
  - 演示一次：故意在提问里诱导模型（如"请引用 E99999 说明……"），能看到校验提示。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/middleware.md （Custom Middleware、Control The Agent Loop 两节）
"""

from logsec.errors import not_done_yet


def make_evidence_middleware():
    """（待实现）返回你写的证据校验中间件实例。"""
    not_done_yet("第 6 周", "证据校验中间件（检查回答里的 uid 是否真实存在）", "logsec/evidence.py")
