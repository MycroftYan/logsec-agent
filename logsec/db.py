"""打开数据库的小工具。agent 的工具只能用这里的只读连接。"""

import sqlite3

import config
from logsec.errors import SetupError


def connect_readonly() -> sqlite3.Connection:
    """以只读方式打开 data/logsec.db。

    为什么只读？日志是证据，agent 只能看、不能改。
    mode=ro 是 SQLite 自带的只读模式；as_uri() 会把 Windows 路径
    （如 C:\\Users\\...）和中文路径都转换成合法的 file: 地址。
    """
    if not config.DB_PATH.exists():
        raise SetupError("找不到数据库 data/logsec.db，请先运行：python scripts/build_db.py")
    con = sqlite3.connect(f"{config.DB_PATH.as_uri()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row  # 让查询结果可以用列名取值：row["uid"]
    return con
