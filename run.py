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

API key 怎么给（三种都行，优先级从高到低）：
    1) 直接跟着命令传：python run.py chat --api-key sk-xxx
    2) 环境变量：      $env:DEEPSEEK_API_KEY="sk-xxx"   （PowerShell）
    3) .env 文件：     第一次运行 run.py 时会问你要，输入一次就存进 .env，以后不用再输
   .env 在 .gitignore 里，不会被提交。

参数会原样传给对应脚本，例如：
    python run.py ask "case_010 里发生了什么？" --model deepseek-v4-pro
    python run.py chat --max-iters 15
"""

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = os.name == "nt"
ENV_FILE = PROJECT_DIR / ".env"
ENV_KEY = "DEEPSEEK_API_KEY"


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


# ---------------------------------------------------------------------------
# API key：命令行参数 > 环境变量 > .env 文件；都没有就问一次，存进 .env
# ---------------------------------------------------------------------------
def arg_api_key(args: list[str]) -> str:
    """从命令参数里找 --api-key sk-xxx（和 --api-key=sk-xxx 两种写法）。"""
    for i, arg in enumerate(args):
        if arg == "--api-key" and i + 1 < len(args):
            return args[i + 1].strip()
        if arg.startswith("--api-key="):
            return arg.split("=", 1)[1].strip()
    return ""


def env_file_key() -> str:
    """.env 文件里已经写好的 key（没有就返回空串）。"""
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == ENV_KEY:
            return value.strip().strip('"').strip("'")
    return ""


def has_api_key(args: list[str]) -> bool:
    return bool(
        arg_api_key(args)
        or os.environ.get(ENV_KEY, "").strip()
        or env_file_key()
    )


def save_api_key(key: str) -> None:
    """把 key 写进 .env：已有该行就替换，没有就追加；其它行（注释）保留。"""
    lines = []
    replaced = False
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{ENV_KEY}=") or stripped.startswith(f"{ENV_KEY} ="):
                lines.append(f"{ENV_KEY}={key}")
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        if not lines:
            lines.append("# 本文件不提交到 Git（见 .gitignore）。key 只放本机。")
        lines.append(f"{ENV_KEY}={key}")
    ENV_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ensure_api_key(args: list[str]) -> bool:
    """没有 key 就现场问一次，存进 .env。返回是否拿到了 key。"""
    if has_api_key(args):
        return True
    if any(a in ("-h", "--help") for a in args):
        return True  # 只是看帮助，不用 key

    print("还没有 DeepSeek API key。三种给法任选一种：")
    print("  1) 现在粘贴一次，会存进本机 .env（推荐，之后不用再输）")
    print("  2) 跟着命令传：python run.py chat --api-key sk-xxx")
    print("  3) 设环境变量：$env:DEEPSEEK_API_KEY=\"sk-xxx\"")
    print(f"  key 在 https://platform.deepseek.com/api_keys 生成；.env 不会被提交到 Git。\n", flush=True)
    try:
        if sys.stdin.isatty():
            # 终端里交互：输入时不回显
            key = getpass.getpass(f"  请粘贴 {ENV_KEY}（输入时不显示）：").strip()
        else:
            # 输入被重定向（脚本、管道）时不能用 getpass，否则会卡在等键盘
            key = input(f"  {ENV_KEY}= ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  已取消。也可以手动把 .env.example 复制成 .env 再填。")
        return False
    if not key:
        print("  没有输入内容，已跳过。之后可以手动填 .env。")
        return False
    if not key.startswith("sk-"):
        print(f"  提醒：DeepSeek 的 key 通常以 sk- 开头，你输入的是「{key[:3]}…」（仍然保存）")
    save_api_key(key)
    print(f"  已保存到 {ENV_FILE}\n", flush=True)
    return True


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
    if command == "ask" and not rest:
        print('用法：python run.py ask "你的问题"')
        return 2

    if command in ("chat", "ask"):
        if not ensure_api_key(rest):  # 没有 key 就问一次，存进 .env
            return 2
        ensure_ready()
    else:
        ensure_ready()

    if command == "ask":
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
