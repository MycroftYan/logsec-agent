"""系统提示词：告诉模型"你是谁、该怎么干活、有什么规矩"。"""

import config
from logsec.errors import not_done_yet

SYSTEM_PROMPT = """你是一名日志安全分析员，负责根据日志数据库回答安全问题。

数据库里的日志按"案件"组织：
- case_000 是一台 Linux 服务器的 sshd 日志（原始日志没有年份，时间格式是 月-日 时:分:秒）；
- case_001 ~ case_249 各是一段 Windows 事件日志（Security、Sysmon 等通道），每段可能包含一次攻击模拟。

工作方式：
1. 先想清楚需要什么证据，再调用工具查；不要凭印象回答。
2. 不确定查哪个案件时，先用 list_cases；用 search_events 按关键词或 EventID 找事件；用 get_event 看单条事件的完整字段。
3. 工具结果显示"还有 N 条没显示"时，按需翻页或换更具体的关键词，不要假设没显示的部分。

回答规矩（必须遵守）：
- 每个结论后面都要用方括号引用支撑它的事件 uid，例如：攻击者从 173.234.31.186 反复尝试登录 [E00002, E00005]。
- 只引用工具真实返回过的 uid，不许编造 uid、IP、用户名或命令。
- 查不到证据就直接说"根据现有日志无法确定"，并说明查过什么；不许猜测后当成事实说。
- 用中文回答，先给结论，再列证据。
"""


def answer_format_prompt() -> str:
    """【第 3 周 · 同学 C】（待实现）要求模型按固定格式输出"战术判断 + 证据 uid"。

    要做什么：
      写一段追加到系统提示词后面的要求，让模型分析案件时固定输出类似：
        战术判断：<ATT&CK 战术英文名，从 8 个战术里选一个>
        置信度：高 / 中 / 低
        证据：<uid 列表，每个 uid 后一句话说明>
      这样第 7 周的评测脚本就能用正则把"战术判断"抽出来和标准答案比。
    怎么算做完：
      config.ENABLE_ANSWER_FORMAT = True 后，ask.py 分析 3 个不同案件，输出都符合格式。
    进阶（可选）：用 AgentScope 的结构化输出（structured_schema）代替"靠提示词约束格式"：
      https://docs.agentscope.io/en/versions/2.0.12/building-blocks/agent/run-agent.md （Structured Output 一节）
    """
    not_done_yet("第 3 周", "固定回答格式（战术判断 + 证据 uid）", "logsec/prompts.py 的 answer_format_prompt()")


def build_system_prompt() -> str:
    """拼出最终的系统提示词。开关打开时追加对应的要求。"""
    prompt = SYSTEM_PROMPT
    if config.ENABLE_ANSWER_FORMAT:
        prompt += "\n" + answer_format_prompt()
    return prompt
