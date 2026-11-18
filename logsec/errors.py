"""两种"友好的"错误：程序遇到它们时打印一句中文说明然后退出，而不是甩出一大串报错。"""


class SetupError(Exception):
    """环境没准备好，比如没建数据库、没填 API key。"""


class NotDoneYet(NotImplementedError):
    """某个后续周的功能开关被打开了，但功能还没写。"""


def not_done_yet(week: str, task: str, where: str) -> None:
    """占位函数里调用它：直接抛出一条说清楚"谁、在哪、做什么"的错误。

    例：not_done_yet("第 4 周", "上下文管理", "logsec/context.py")
    """
    raise NotDoneYet(
        f"[{week}任务，尚未实现] {task}\n"
        f"  -> 需要先完成：{where}\n"
        f"  -> 如果是 config.py 里的开关触发的，也可以先把那个开关改回 False。\n"
        f"  -> 具体要求见 README.md 的「按周待办」。"
    )
