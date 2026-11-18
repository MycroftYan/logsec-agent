"""一条命令启动本项目（不用先激活虚拟环境）。

    python run.py ask "case_010 里发生了什么可疑行为？"   # 单次提问，打印每一步工具调用
    python run.py chat                                   # 多轮对话（本次运行内会记住前文）
    python run.py setup                                  # 建虚拟环境 + 装依赖
    python run.py db                                     # 用原始日志重建数据库
    python run.py test                                   # 跑不花钱的测试
    python run.py                                        # 不带参数 = chat

为什么需要它：仓库里的依赖装在 `.venv` 里，如果直接 `python ask.py`，
用的是系统的 Python，会报 `ModuleNotFoundError: No module named 'agentscope'`。
这个脚本会自动找到 `.venv` 里的 Python 再去运行，Windows / macOS 都能用。

参数会原样传给对应脚本，例如：
    python run.py ask "case_010 里发生了什么？" --model deepseek-v4-pro
    python run.py chat --max-iters 15
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = os.name == "nt"


def venv_python() -> Path:
    """`.venv` 里的 Python 解释器路径（Windows 和 macOS/Linux 位置不同）。"""
    if IS_WINDOWS:
        return PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
    return PROJECT_DIR / ".venv" / "bin" / "python"


def base_env() -> dict:
    """子进程环境：强制 UTF-8，避免 Windows 终端中文乱码。"""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def setup() -> None:
    """建虚拟环境并装依赖。优先用 uv（快），没有 uv 就用标准库 venv。"""
    print("[1/2] 建虚拟环境 .venv ...")
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "--python", "3.11", str(PROJECT_DIR / ".venv")], cwd=PROJECT_DIR, check=True)
        print("[2/2] 用 uv 装依赖 ...")
        subprocess.run(
            ["uv", "pip", "install", "-r", str(PROJECT_DIR / "requirements.txt"),
             "--python", str(venv_python())],
            cwd=PROJECT_DIR, check=True,
        )
    else:
        print("      没找到 uv，用标准库 venv（慢一些）...")
        subprocess.run([sys.executable, "-m", "venv", str(PROJECT_DIR / ".venv")], cwd=PROJECT_DIR, check=True)
        print("[2/2] 装依赖 ...")
        subprocess.run([str(venv_python()), "-m", "pip", "install", "-r", "requirements.txt"], cwd=PROJECT_DIR, check=True)
    print("\n环境就绪。下一步：python run.py db  （建数据库）")


def ensure_ready() -> None:
    """运行前检查：虚拟环境在不在、数据库建没建。缺了就自动补，并说清楚在做什么。"""
    if not venv_python().exists():
        print("没找到虚拟环境 .venv，先自动建一个（只需要一次）……\n")
        setup()
        print()
    if not (PROJECT_DIR / "data" / "logsec.db").exists():
        print("没找到数据库 data/logsec.db，先自动建库……\n")
        subprocess.run([str(venv_python()), str(PROJECT_DIR / "scripts" / "build_db.py")],
                       cwd=PROJECT_DIR, env=base_env(), check=True)
        print()


def exec_script(script: str, args: list[str]) -> int:
    """用 .venv 的 Python 运行项目里的脚本，参数原样透传。"""
    cmd = [str(venv_python()), str(PROJECT_DIR / script), *args]
    return subprocess.run(cmd, cwd=PROJECT_DIR, env=base_env()).returncode


def main() -> int:
    args = sys.argv[1:]
    command = args[0].lower() if args else "chat"
    rest = args[1:]

    if command in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if command == "setup":
        setup()
        return 0

    ensure_ready()

    if command == "ask":
        if not rest:
            print('用法：python run.py ask "你的问题"')
            return 2
        return exec_script("ask.py", rest)
    if command == "chat":
        return exec_script("chat.py", rest)
    if command == "db":
        return exec_script("scripts/build_db.py", rest)
    if command == "test":
        return subprocess.run(
            [str(venv_python()), "-m", "pytest", "-q", *rest],
            cwd=PROJECT_DIR, env=base_env(),
        ).returncode

    print(f"不认识的子命令：{command}\n")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
