"""【第 3 周 · 同学 C】补齐工具 —— 目前只有占位，需要你来实现。

要做什么：
  实现下面 3 个函数，让 agent 多 3 个只读工具：
    1. get_event_context  看某条事件前后一段时间内、同一案件里发生了什么（还原攻击过程）。
    2. count_events       按 EventID / 主机 / 日志通道统计某个案件的事件数（先看全貌再挑重点）。
    3. lookup_tactic      查询 ATT&CK 战术的中文说明和典型日志迹象（帮模型做判断）。
  写法照抄 logsec/tools.py：普通函数 + 中文 docstring（第一段是给模型看的说明，Args 写参数）
  + 返回紧凑文字 + 结果条数有上限。

怎么算做完（验收）：
  1. 删掉 extra_tools() 里的 not_done_yet(...) 那一行，在 config.py 把 ENABLE_EXTRA_TOOLS 改成 True；
  2. 在 tests/test_tools.py 里给每个新工具加至少 1 个测试，python -m pytest 全部通过；
  3. 跑 python ask.py "case_xxx 里可疑事件前后还发生了什么？"，能看到 agent 调用了新工具。
  4. 新工具同样不能读 labels 表、不能返回文件名或战术标签（lookup_tactic 只返回战术的通用说明，
     不能告诉模型"某个案件属于哪个战术"）。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/tool/python-tool.md （Wrap Function as Tool 一节）
  ATT&CK 战术列表：https://attack.mitre.org/tactics/enterprise/
"""

from agentscope.tool import FunctionTool

from logsec.errors import not_done_yet


def get_event_context(uid: str, window_seconds: int = 60) -> str:
    """（待实现）返回与 uid 同一案件、时间在前后 window_seconds 秒内的事件列表。

    提示：先查出这条事件的 case_id 和 time，再查同案件、时间在区间内的事件，
    按时间排序，最多返回 config.MAX_ROWS 条并提示剩余条数。
    注意 SSH 日志的时间格式是 'MM-DD HH:MM:SS'（没有年份），EVTX 是 'YYYY-MM-DD HH:MM:SS.ffffff'。
    """
    not_done_yet("第 3 周", "工具 get_event_context", "logsec/tools_week3.py")


def count_events(case_id: str, group_by: str = "event_id") -> str:
    """（待实现）统计某个案件的事件数，group_by 可选 "event_id"、"host"、"channel"。

    提示：SELECT group_by 列, COUNT(*) ... GROUP BY ...；group_by 只能从白名单里选，
    不要把用户输入直接拼进 SQL（防 SQL 注入）。
    """
    not_done_yet("第 3 周", "工具 count_events", "logsec/tools_week3.py")


def lookup_tactic(name: str) -> str:
    """（待实现）返回某个 ATT&CK 战术（如 "Credential Access"）的中文说明、常见技术和典型日志迹象。

    提示：可以在 data/ 下放一个 attack_tactics.json（由同学 B 整理），这里读它。
    """
    not_done_yet("第 3 周", "工具 lookup_tactic", "logsec/tools_week3.py")


def extra_tools() -> list[FunctionTool]:
    """把上面 3 个函数包装成工具。实现完上面的函数后，删掉下一行。"""
    not_done_yet("第 3 周", "补齐工具（时间窗上下文 / 统计 / ATT&CK 说明）", "logsec/tools_week3.py")
    return [
        FunctionTool(get_event_context, is_read_only=True),
        FunctionTool(count_events, is_read_only=True),
        FunctionTool(lookup_tactic, is_read_only=True),
    ]
