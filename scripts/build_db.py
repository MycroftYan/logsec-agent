"""把 data/raw/ 里的两份原始日志导入 SQLite 数据库 data/logsec.db。

用法（在项目根目录下）：
    python scripts/build_db.py

可以重复运行：每次都会删掉旧库、从原始文件重新建。

建出来的三张表：
  events  每行一条日志事件。uid 是事件唯一编号（如 E00042），agent 回答时要引用它。
  cases   每行一个"案件"（= 一个原始 EVTX 文件，或整份 SSH 日志）的概况。
  labels  标准答案（原始文件名 + ATT&CK 战术）。只给评测脚本用，agent 的工具绝不能读它！

为什么要把文件名藏起来？
  EVTX 样本的文件名里常直接写着攻击技术（比如 "...Mimikatz..."），
  如果 agent 能看到文件名，就等于看到了答案，后面的评测就没意义了。
  所以每个文件只给一个不透露信息的编号 case_001、case_002……，
  而且编号顺序是打乱的（不按文件名字母序，否则同一战术的案件会挨在一起）。
"""

import csv
import json
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# 让脚本在任何目录下运行都能找到项目根目录里的 config.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

SHUFFLE_SEED = 20261117   # 固定随机种子：每次建库，同一个文件都得到同一个 case 编号
SSH_CASE_ID = "case_000"  # SSH 日志整体作为一个案件，没有标签
UNLABELED = "未标注"

# 这些列已经单独存成 events 表的列，或者是标准答案，不放进 fields_json
EVTX_SKIP_COLUMNS = {"", "EVTX_FileName", "EVTX_Tactic", "Channel", "Computer",
                     "EventID", "SystemTime"}

# 常见 EventID 的中文含义，只用来生成一行摘要，方便人和模型快速浏览。
# 键是 (日志类别, EventID)。Sysmon 和 Security 的同一个编号含义不同，所以要分开。
EVENT_NAMES = {
    ("sysmon", 1): "进程创建", ("sysmon", 3): "网络连接", ("sysmon", 5): "进程结束",
    ("sysmon", 7): "加载模块", ("sysmon", 8): "创建远程线程", ("sysmon", 10): "进程访问",
    ("sysmon", 11): "文件创建", ("sysmon", 12): "注册表项增删", ("sysmon", 13): "注册表值设置",
    ("sysmon", 18): "命名管道连接",
    ("security", 1102): "安全日志被清除", ("security", 4624): "登录成功",
    ("security", 4625): "登录失败", ("security", 4648): "使用显式凭据登录",
    ("security", 4662): "目录服务对象操作", ("security", 4663): "对象访问",
    ("security", 4672): "特权登录", ("security", 4688): "进程创建",
    ("security", 4697): "安装服务", ("security", 4698): "创建计划任务",
    ("security", 4720): "创建用户", ("security", 4732): "加入本地组",
    ("security", 4769): "请求 Kerberos 服务票据", ("security", 5136): "目录服务对象修改",
    ("security", 5145): "网络共享文件访问", ("security", 5156): "防火墙允许连接",
    ("system", 7045): "安装服务", ("system", 104): "日志被清除",
    ("powershell", 4104): "PowerShell 脚本块",
}

# 摘要里优先展示的字段（按顺序取前 4 个有值的）
SUMMARY_FIELDS = [
    "Image", "CommandLine", "TargetUserName", "IpAddress", "TargetFilename",
    "TargetObject", "ServiceName", "ShareName", "RelativeTargetName", "ObjectName",
    "ImageLoaded", "SourceImage", "TargetImage", "GrantedAccess", "DestinationIp",
    "DestinationPort", "ScriptBlockText", "SubjectUserName", "param1",
]


def channel_kind(channel: str) -> str:
    """把很长的日志通道名归成几类，用来查 EVENT_NAMES。"""
    c = channel.lower()
    for kind in ("sysmon", "security", "powershell", "system"):
        if kind in c:
            return kind
    return c


def clean_key(key: str) -> str:
    """去掉 XML 命名空间前缀：'{http://...}SubjectUserName' -> 'SubjectUserName'。"""
    return re.sub(r"^\{[^}]*\}", "", key)


def evtx_fields(row: dict) -> dict:
    """取出一行 EVTX 里所有"有内容"的字段（这份 CSV 有 326 列，绝大多数是空的）。"""
    fields = {}
    for key, value in row.items():
        value = (value or "").strip()
        if key in EVTX_SKIP_COLUMNS or value in ("", "-"):
            continue
        name = clean_key(key)
        if name in fields:  # 去前缀后撞名了，就保留原名
            name = key
        fields[name] = value
    return fields


def evtx_summary(channel: str, event_id: int, fields: dict) -> str:
    """生成一行摘要，例如：'Sysmon 1 进程创建 | Image=...cmd.exe | CommandLine=...'"""
    kind = channel_kind(channel)
    name = EVENT_NAMES.get((kind, event_id), "")
    parts = [f"{kind} {event_id} {name}".strip()]
    for key in SUMMARY_FIELDS:
        if key in fields:
            parts.append(f"{key}={fields[key][:80]}")
        if len(parts) >= 5:
            break
    return " | ".join(parts)[:240]


def load_evtx_rows() -> list[dict]:
    """读 EVTX CSV。注意：Windows 上不能用 sys.maxsize（会溢出），所以写一个固定的大数。"""
    csv.field_size_limit(100_000_000)
    with open(config.EVTX_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def assign_case_ids(rows: list[dict]) -> dict[str, str]:
    """给每个 EVTX 文件分配一个打乱顺序的 case 编号：{文件名: 'case_001', ...}"""
    files = sorted({r["EVTX_FileName"] for r in rows})
    random.Random(SHUFFLE_SEED).shuffle(files)
    return {name: f"case_{i:03d}" for i, name in enumerate(files, start=1)}


SSH_LINE = re.compile(r"^(\w{3})\s+(\d+) (\d\d:\d\d:\d\d) (\S+) sshd\[(\d+)\]: (.*)$")
MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), start=1)}


def parse_ssh_line(line: str) -> dict | None:
    """解析一行 sshd 日志。原始日志没有年份，所以时间存成 'MM-DD HH:MM:SS'。"""
    m = SSH_LINE.match(line.strip())
    if not m:
        return None
    month, day, clock, host, pid, message = m.groups()
    fields = {"pid": pid, "message": message}
    # 顺手抽出常用的 IP / 用户名 / 端口，方便关键词搜索
    ip = re.search(r"(?:from |rhost=|\[)(\d+\.\d+\.\d+\.\d+)", message)
    user = re.search(r"(?:[Ii]nvalid user |user=|password for (?:invalid user )?)(\S+)", message)
    port = re.search(r"port (\d+)", message)
    if ip:
        fields["ip"] = ip.group(1)
    if user:
        fields["user"] = user.group(1)
    if port:
        fields["port"] = port.group(1)
    return {
        "time": f"{MONTHS[month]:02d}-{int(day):02d} {clock}",
        "host": host,
        "channel": "sshd",
        "event_id": None,
        "summary": message[:240],
        "fields": fields,
    }


def collect_events() -> tuple[dict, dict]:
    """把两份日志都读成统一格式。返回 ({case_id: [事件, ...]}, {case_id: (文件名, 战术, 日志类型)})"""
    events = defaultdict(list)
    meta = {}

    rows = load_evtx_rows()
    case_of_file = assign_case_ids(rows)
    for row in rows:
        case_id = case_of_file[row["EVTX_FileName"]]
        fields = evtx_fields(row)
        event_id = int(row["EventID"]) if row["EventID"].strip().isdigit() else None
        events[case_id].append({
            "time": row["SystemTime"].strip(),
            "host": row["Computer"].strip(),
            "channel": row["Channel"].strip(),
            "event_id": event_id,
            "summary": evtx_summary(row["Channel"], event_id, fields),
            "fields": fields,
        })
        meta[case_id] = (row["EVTX_FileName"], row["EVTX_Tactic"], "windows_evtx")

    with open(config.SSH_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            event = parse_ssh_line(line)
            if event:
                events[SSH_CASE_ID].append(event)
    meta[SSH_CASE_ID] = (config.SSH_LOG.name, UNLABELED, "linux_sshd")
    return events, meta


def event_sort_key(event: dict):
    """同一案件内按时间排序；时间相同再按 EventRecordID（原始记录号）排序。"""
    record = event["fields"].get("EventRecordID", "0")
    return (event["time"], int(record) if record.isdigit() else 0)


SCHEMA = """
CREATE TABLE events (
    uid         TEXT PRIMARY KEY,  -- 事件唯一编号，如 E00042
    case_id     TEXT NOT NULL,
    time        TEXT,              -- EVTX: 'YYYY-MM-DD HH:MM:SS.ffffff'；SSH: 'MM-DD HH:MM:SS'（原日志无年份）
    host        TEXT,
    channel     TEXT,              -- 日志通道，如 Security、Microsoft-Windows-Sysmon/Operational、sshd
    event_id    INTEGER,           -- Windows EventID；SSH 日志没有，为 NULL
    summary     TEXT,              -- 一行摘要
    fields_json TEXT               -- 其余非空字段，JSON 格式
);
CREATE INDEX idx_events_case ON events(case_id);
CREATE INDEX idx_events_eid ON events(event_id);

CREATE TABLE cases (
    case_id    TEXT PRIMARY KEY,
    log_type   TEXT,     -- windows_evtx 或 linux_sshd
    n_events   INTEGER,
    hosts      TEXT,     -- 逗号分隔
    start_time TEXT,
    end_time   TEXT
);

-- 标准答案：只给评测脚本读，agent 工具禁止访问
CREATE TABLE labels (
    case_id     TEXT PRIMARY KEY,
    source_file TEXT,
    tactic      TEXT
);
"""


def build(db_path: Path = config.DB_PATH) -> None:
    events, meta = collect_events()

    # 重复运行：先删旧库
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    counter = 0
    for case_id in sorted(events):
        case_events = sorted(events[case_id], key=event_sort_key)
        for e in case_events:
            counter += 1
            con.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?)",
                (f"E{counter:05d}", case_id, e["time"], e["host"], e["channel"],
                 e["event_id"], e["summary"], json.dumps(e["fields"], ensure_ascii=False)),
            )
        hosts = sorted({e["host"] for e in case_events if e["host"]})
        source_file, tactic, log_type = meta[case_id]
        con.execute(
            "INSERT INTO cases VALUES (?,?,?,?,?,?)",
            (case_id, log_type, len(case_events), ",".join(hosts),
             case_events[0]["time"], case_events[-1]["time"]),
        )
        con.execute("INSERT INTO labels VALUES (?,?,?)", (case_id, source_file, tactic))
    con.commit()

    for table in ("events", "cases", "labels"):
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:7s} {n:6d} 行")
    con.close()
    print(f"数据库已生成：{db_path}")


if __name__ == "__main__":
    build()
