"""不调用模型的最小测试（不花钱、几秒跑完）。

运行：python -m pytest
检查三件事：
  1. 数据库建好了，行数对；
  2. 3 个工具能查到东西、格式对、会提示"还有多少条没显示"；
  3. 工具输出里不含标准答案（原始文件名、EVTX_FileName / EVTX_Tactic 字段），
     工具代码里也没有查询 labels 表；工具都被权限系统自动放行（不会卡在确认上）。
"""

import asyncio
import re
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from logsec import tools  # noqa: E402

UID = re.compile(r"\bE\d{5}\b")


@pytest.fixture(scope="module", autouse=True)
def database():
    """如果还没建库，先建一次。"""
    if not config.DB_PATH.exists():
        from scripts.build_db import build
        build()


def read_labels():
    con = sqlite3.connect(config.DB_PATH)
    rows = con.execute("SELECT case_id, source_file, tactic FROM labels").fetchall()
    con.close()
    return rows


# ---------- 1. 数据库 ----------
def test_table_counts():
    con = sqlite3.connect(config.DB_PATH)
    count = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
    assert count("SELECT COUNT(*) FROM events") == 4633 + 2000
    assert count("SELECT COUNT(*) FROM cases") == 249 + 1
    assert count("SELECT COUNT(*) FROM labels") == 250
    assert count("SELECT COUNT(DISTINCT tactic) FROM labels WHERE tactic != '未标注'") == 8
    con.close()


# ---------- 2. 工具能查到东西 ----------
def test_list_cases():
    out = tools.list_cases()
    assert "case_000" in out and "linux_sshd" in out
    assert "还有" in out  # 250 个案件，一页显示不完
    assert "case_000" not in tools.list_cases(log_type="windows_evtx")


def test_search_events_keyword_and_limit():
    out = tools.search_events(case_id="case_000", keyword="Failed password")
    assert UID.search(out)
    assert "还有" in out
    assert len(UID.findall(out)) == config.MAX_ROWS


def test_search_events_event_id():
    out = tools.search_events(event_id=4624)
    assert "4624" in out and UID.search(out)


def test_search_events_bad_case():
    assert "没有案件" in tools.search_events(case_id="case_999")


def test_get_event():
    uid = UID.search(tools.search_events(case_id="case_000", keyword="Invalid user")).group()
    out = tools.get_event(uid)
    assert f"uid: {uid}" in out and "case_000" in out
    assert "没有 uid" in tools.get_event("E99999")


# ---------- 3. 不泄露标准答案 ----------
def test_tool_code_never_reads_labels():
    source = Path(tools.__file__).read_text(encoding="utf-8")
    assert not re.search(r"(FROM|JOIN)\s+labels", source, re.IGNORECASE)


def test_no_label_leak_in_outputs():
    filenames = [f for _, f, t in read_labels() if t != "未标注"]
    outputs = [tools.list_cases(offset=o) for o in range(0, 250, config.MAX_CASES)]
    con = sqlite3.connect(config.DB_PATH)
    uids = [r[0] for r in con.execute("SELECT uid FROM events")]
    case_ids = [r[0] for r in con.execute("SELECT case_id FROM cases")]
    con.close()
    outputs += [tools.search_events(case_id=c) for c in case_ids]
    outputs += [tools.get_event(u) for u in uids]  # 每一条事件都查一遍
    text = "\n".join(outputs)
    assert "EVTX_FileName" not in text and "EVTX_Tactic" not in text
    leaked = [f for f in filenames if f in text]
    assert not leaked, f"工具输出里出现了原始文件名：{leaked[:3]}"


def test_tools_are_auto_allowed():
    """FunctionTool 默认要用户确认；我们标了 is_read_only=True，应该在默认模式下直接放行。"""
    from agentscope.permission import PermissionBehavior, PermissionContext, PermissionEngine

    engine = PermissionEngine(PermissionContext())
    for tool in tools.build_tools():
        decision = asyncio.run(engine.check_permission(tool, {}))
        assert decision.behavior == PermissionBehavior.ALLOW, tool.name
