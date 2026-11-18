"""【第 7 周 · 同学 B】评测脚本 —— 读标准答案的部分已写好，跑评测的主循环留给你。

运行：python eval/run_eval.py
现在运行会先打印标准答案的统计（证明 load_labels 能用），然后提示"主循环尚未实现"。

评测思路：
  对每个 EVTX 案件，让 agent 判断"这个案件属于哪种 ATT&CK 战术"，
  把它的回答和 labels 表里的标准答案比，算准确率；
  再把 config.py 里的组件开关（工具补齐 / 上下文管理 / 记忆 / 证据校验）开、关各跑一遍，比较准确率、
  token 用量、引用的 uid 是否真实存在。

要做什么：
  1. extract_tactic()：从 agent 的回答里抽出它判断的战术（依赖第 3 周的固定回答格式）。
  2. main() 里的主循环：
       for 每个案件（先抽 20~30 个试跑，全量 249 个会比较花钱）：
           agent = build_agent()            # 每个案件新建一个 agent，避免上一题的对话影响下一题
           问它 QUESTION_TEMPLATE.format(case_id=...)
           抽出战术，和 labels 比，记下对错、token 用量、调用了几次工具
       打印总准确率、各战术的准确率，结果存成 eval/results_<日期>.csv
     调用 agent 的写法可以参考 ask.py 的 ask() 函数。
  3. 开/关对比：在建 agent 之前改 config 里的开关，例如
       import config; config.ENABLE_EXTRA_TOOLS = True
     每种配置跑同一批案件，做成一张对比表。
  4. 注意"开卷"问题：评测时要关掉长期记忆（或清空 memory/ 目录），
     否则 agent 可能直接从记忆里读到之前的结论。
     另外 Sysmon 的 RuleName 字段有时直接写着技术名（如 technique_name=Credential Dumping），
     这是日志自带的检测规则命中信息，不是我们泄露的标签；可以考虑做一组"屏蔽 RuleName"的对比实验。

怎么算做完（验收）：
  - python eval/run_eval.py 能跑完至少 20 个案件并打印准确率；
  - 有至少两种配置的对比表（例如：基础版 vs 加了第 3 周工具）。

参考文档：
  https://docs.agentscope.io/en/versions/2.0.12/building-blocks/agent/run-agent.md
  （Structured Output 一节：让 agent 直接返回 {"tactic": ...}，比用正则抽取更稳）
"""

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from logsec.errors import NotDoneYet, not_done_yet  # noqa: E402

QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.json"
QUESTION_TEMPLATE = "请分析案件 {case_id}，判断它最可能属于哪一种 ATT&CK 战术，并给出证据 uid。"

# 数据集里出现的 8 种战术（标准答案只会是其中之一）
TACTICS = [
    "Command and Control", "Credential Access", "Defense Evasion", "Discovery",
    "Execution", "Lateral Movement", "Persistence", "Privilege Escalation",
]


def load_labels() -> dict[str, str]:
    """读标准答案：{case_id: 战术}。只有评测脚本能读 labels 表，agent 的工具不能。

    SSH 案件没有标签（"未标注"），不参与战术评测。
    """
    con = sqlite3.connect(config.DB_PATH)
    rows = con.execute("SELECT case_id, tactic FROM labels WHERE tactic != '未标注'").fetchall()
    con.close()
    return dict(rows)


def load_questions() -> list[dict]:
    """读示例题目 eval/questions.json。"""
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))


def extract_tactic(answer: str) -> str | None:
    """（待实现）从 agent 的回答文字里抽出它判断的战术，返回 TACTICS 里的一个，抽不出来返回 None。"""
    not_done_yet("第 7 周", "从回答中抽取战术判断", "eval/run_eval.py 的 extract_tactic()")


def main() -> None:
    if not config.DB_PATH.exists():
        print("找不到数据库，请先运行：python scripts/build_db.py")
        sys.exit(2)

    labels = load_labels()
    print(f"标准答案：{len(labels)} 个有标签的案件")
    for tactic, n in Counter(labels.values()).most_common():
        print(f"  {tactic:22s} {n} 个案件")
    print(f"示例题目：{len(load_questions())} 道（见 eval/questions.json）\n")

    try:
        not_done_yet("第 7 周", "评测主循环（逐个案件提问、抽取战术、和标准答案对比）",
                     "eval/run_eval.py 的 main()")
    except NotDoneYet as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
