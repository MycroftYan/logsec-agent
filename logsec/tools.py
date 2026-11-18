"""agent 可以调用的 3 个只读日志工具。

每个工具就是一个普通 Python 函数：
  - 函数名 = 工具名；
  - docstring 第一段 = 给模型看的工具说明；Args 里每一行 = 参数说明；
  - 返回一段紧凑的文字给模型读。
AgentScope 的 FunctionTool 会自动把它们包装成模型能调用的工具（见 build_tools）。

两条铁律：
  1. 只读：只用 db.connect_readonly()，不写库。
  2. 不泄露答案：这里的 SQL 只查 events 和 cases 两张表，永远不要碰 labels 表，
     也不要返回原始文件名或战术标签（tests/test_tools.py 会检查）。

参考文档：https://docs.agentscope.io/en/versions/2.0.12/building-blocks/tool/python-tool.md
"""

import json

from agentscope.tool import FunctionTool

import config
from logsec.db import connect_readonly


def _short_time(t: str | None) -> str:
    """'2019-08-04 08:56:16.228363' -> '2019-08-04 08:56:16'，省 token。"""
    return (t or "")[:19]


def _more_hint(total: int, shown: int, offset: int) -> str:
    """结果没显示完时，告诉模型还剩多少、怎么翻页。"""
    rest = total - offset - shown
    if rest <= 0:
        return ""
    return f"\n……还有 {rest} 条没显示。可把 offset 设为 {offset + shown} 翻页，或换更具体的关键词。"


def _case_exists(con, case_id: str) -> bool:
    return con.execute("SELECT 1 FROM cases WHERE case_id = ?", (case_id,)).fetchone() is not None


# ---------------------------------------------------------------------------
# 工具 1：列出案件概况
# ---------------------------------------------------------------------------
def list_cases(log_type: str = "", offset: int = 0) -> str:
    """列出日志案件的概况：每个案件的编号、日志类型、事件数、主机、时间范围和最常见的事件类型。不确定该查哪个案件时先用它。

    Args:
        log_type: 只看某一类日志，可选 "windows_evtx" 或 "linux_sshd"；留空表示全部。
        offset: 从第几个案件开始列（用于翻页），默认 0。
    """
    con = connect_readonly()
    where, params = "", []
    if log_type:
        where, params = "WHERE log_type = ?", [log_type]
    total = con.execute(f"SELECT COUNT(*) FROM cases {where}", params).fetchone()[0]
    rows = con.execute(
        f"SELECT * FROM cases {where} ORDER BY case_id LIMIT ? OFFSET ?",
        params + [config.MAX_CASES, offset],
    ).fetchall()

    lines = [f"共 {total} 个案件。格式：案件 | 日志类型 | 事件数 | 主机 | 时间范围 | 常见事件(通道 EventID x次数)"]
    for r in rows:
        # 统计这个案件里最常见的 3 种事件，帮模型快速判断案件性质
        top = con.execute(
            "SELECT channel, event_id, COUNT(*) AS n FROM events WHERE case_id = ? "
            "GROUP BY channel, event_id ORDER BY n DESC LIMIT 3",
            (r["case_id"],),
        ).fetchall()
        top_text = ", ".join(
            f"{t['channel'].split('/')[0].replace('Microsoft-Windows-', '')} {t['event_id'] or ''}x{t['n']}"
            for t in top
        )
        lines.append(
            f"{r['case_id']} | {r['log_type']} | {r['n_events']} 条 | {r['hosts']} | "
            f"{_short_time(r['start_time'])} ~ {_short_time(r['end_time'])} | {top_text}"
        )
    con.close()
    return "\n".join(lines) + _more_hint(total, len(rows), offset)


# ---------------------------------------------------------------------------
# 工具 2：在案件里搜索事件
# ---------------------------------------------------------------------------
def search_events(case_id: str = "", keyword: str = "", event_id: int = 0, offset: int = 0) -> str:
    """在日志里搜索事件，返回每条事件的 uid、时间、主机和一行摘要。可以按案件、关键词、EventID 组合筛选；三个条件都不填则列出全部事件（按时间排序）。

    Args:
        case_id: 案件编号，如 "case_007"；留空表示在所有案件里搜。
        keyword: 关键词（不区分大小写），会在摘要和所有字段里查找，如 "powershell"、"lsass"、"Failed password"；留空表示不按关键词筛选。
        event_id: Windows EventID，如 4624、1；填 0 表示不按 EventID 筛选。
        offset: 跳过前多少条（用于翻页），默认 0。
    """
    con = connect_readonly()
    if case_id and not _case_exists(con, case_id):
        con.close()
        return f"没有案件 {case_id}。请先用 list_cases 查看有哪些案件。"

    conditions, params = [], []
    if case_id:
        conditions.append("case_id = ?")
        params.append(case_id)
    if keyword:
        # fields_json 里的反斜杠和引号是转义过的（C:\Windows 存成 C:\\Windows），
        # 所以关键词也按 JSON 的方式转义一份再去匹配字段。
        json_keyword = json.dumps(keyword, ensure_ascii=False)[1:-1]
        conditions.append("(summary LIKE ? OR fields_json LIKE ?)")
        params += [f"%{keyword}%", f"%{json_keyword}%"]
    if event_id:
        conditions.append("event_id = ?")
        params.append(event_id)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = con.execute(f"SELECT COUNT(*) FROM events {where}", params).fetchone()[0]
    rows = con.execute(
        f"SELECT uid, case_id, time, host, summary FROM events {where} "
        f"ORDER BY uid LIMIT ? OFFSET ?",
        params + [config.MAX_ROWS, offset],
    ).fetchall()
    con.close()

    if total == 0:
        return "没有找到符合条件的事件。可以换个关键词，或去掉一些筛选条件。"
    lines = [f"共找到 {total} 条事件，显示第 {offset + 1}-{offset + len(rows)} 条。格式：uid | 案件 | 时间 | 主机 | 摘要"]
    for r in rows:
        lines.append(f"{r['uid']} | {r['case_id']} | {_short_time(r['time'])} | {r['host']} | {r['summary']}")
    return "\n".join(lines) + _more_hint(total, len(rows), offset)


# ---------------------------------------------------------------------------
# 工具 3：按 uid 取单条事件详情
# ---------------------------------------------------------------------------
def get_event(uid: str) -> str:
    """按 uid 查看一条事件的全部字段（命令行、进程路径、用户名、IP 等）。在 search_events 找到可疑事件后用它看细节。

    Args:
        uid: 事件编号，如 "E00042"。
    """
    con = connect_readonly()
    row = con.execute("SELECT * FROM events WHERE uid = ?", (uid.strip(),)).fetchone()
    con.close()
    if row is None:
        return f"没有 uid 为 {uid} 的事件。uid 的格式是 E 加 5 位数字，如 E00042。"

    lines = [
        f"uid: {row['uid']}",
        f"案件: {row['case_id']}",
        f"时间: {row['time']}",
        f"主机: {row['host']}",
        f"通道: {row['channel']}",
        f"EventID: {row['event_id'] if row['event_id'] is not None else '无'}",
        "字段:",
    ]
    for key, value in json.loads(row["fields_json"]).items():
        value = str(value).replace("\r", " ").replace("\n", " ")
        if len(value) > config.MAX_FIELD_CHARS:
            value = value[: config.MAX_FIELD_CHARS] + f"…(已截断，原长 {len(value)} 字符)"
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 把函数包装成 AgentScope 工具
# ---------------------------------------------------------------------------
def build_tools() -> list[FunctionTool]:
    """返回交给 agent 的工具列表。

    is_read_only=True 很重要：FunctionTool 默认每次调用都要用户确认（ASK），
    标成只读后，AgentScope 的权限系统会走"只读快速通道"直接放行，
    这样 ask.py 这种非交互运行就不会卡在"是否允许调用工具？"上。
    参考：https://docs.agentscope.io/en/versions/2.0.12/building-blocks/permission-system/overview.md
    """
    tools = [
        FunctionTool(list_cases, is_read_only=True),
        FunctionTool(search_events, is_read_only=True),
        FunctionTool(get_event, is_read_only=True),
    ]
    if config.ENABLE_EXTRA_TOOLS:  # 第 3 周
        from logsec.tools_week3 import extra_tools
        tools += extra_tools()
    return tools
