# 来源与许可说明

本项目是北航网安学院本科生科研课堂的课程项目。**代码**（`logsec/`、`ask.py`、`chat.py`、`scripts/`、`eval/`、`tests/`）由课程小组成员编写，框架依赖 [AgentScope](https://github.com/agentscope-ai/agentscope)（Apache-2.0）。

`data/raw/` 下的两份日志来自公开数据集，**不是**本项目的数据，只用于课程学习和测试：

| 文件 | 来源 | 许可 |
|---|---|---|
| `data/raw/evtx_data.csv` | [sbousseaden/EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) | GPL-3.0 |
| `data/raw/OpenSSH_2k.log` | [logpai/loghub](https://github.com/logpai/loghub) | 免费用于研究和学术用途，使用时请引用 Loghub 论文 |

`data/logsec.db` 由 `scripts/build_db.py` 从上述两份文件生成，不提交到仓库。

如果对外分发、发表或用于其他项目，请按各数据集仓库的许可要求注明来源。

参考系统的设计来源（只借鉴设计，不复制其代码）：[APT-Hunter](https://github.com/ahmedkhlief/APT-Hunter)（GPL-3.0）、[Ariadne](https://github.com/epsilla-cloud/ariadne)、ZettelForge、[Agent-Kernel](https://github.com/agentscope-ai/agentscope)，详见 `docs/02-系统方案设计_v0.4.md` 第 2 节。
