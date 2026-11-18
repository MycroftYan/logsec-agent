# logsec-agent：日志安全分析对话智能体

[![tests](https://github.com/MycroftYan/logsec-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/MycroftYan/logsec-agent/actions/workflows/tests.yml)

一个能在终端里对话的"日志安全分析员"。你用中文提问（比如"case_000 里有没有暴力破解？"），
它会自己决定调用哪些日志查询工具、查到证据，再给出**带事件编号（uid）**的结论。

- 框架：[AgentScope 2.0.12](https://docs.agentscope.io/en/versions/2.0.12/index.md)（注意 2.x 和 1.x 的写法完全不同，查文档认准 2.0.12）
- 模型：DeepSeek `deepseek-flash`
- 数据：两份公开日志，已导入 SQLite（Windows 攻击样本 EVTX + Linux sshd 日志）
- 代码仓库：<https://github.com/MycroftYan/logsec-agent>
- 平台：macOS 和 Windows 都跑通了（Windows 实测见[下面](#windows-实测记录)）

现在完成的是第 1–2 周的**最小可运行版本**。记忆、上下文管理、更多工具等组件都**故意留空**，
由大家在第 3–8 周一点点加上去，见下面的[按周待办](#按周待办)。

---

## 5 分钟跑起来

需要 Python 3.11 或更高版本。推荐用 [uv](https://docs.astral.sh/uv/) 管理环境（下面两种写法任选其一）。

### 最省事：一条命令（不用激活虚拟环境）

```powershell
cd logsec-agent
python run.py setup          # 只需一次：建 .venv + 装依赖
copy .env.example .env       # 然后把 key 填进 .env
python run.py chat           # 多轮对话
python run.py ask "case_010 里发生了什么可疑行为？请给出证据"   # 单次提问
python run.py test           # 跑不花钱的测试
```

`run.py` 会自动找到 `.venv` 里的 Python 再运行脚本，所以**不会出现"用错 Python 报 No module named 'agentscope'"**；
数据库没建时它也会自动先建库。子命令只有 5 个：`chat` / `ask` / `setup` / `db` / `test`。

> 为什么需要它：直接 `python ask.py` 用的是系统 Python（本机是 3.14），依赖装在 `.venv` 里，会报
> `ModuleNotFoundError: No module named 'agentscope'`。

### 手动方式（想看清楚每一步的话）

#### macOS / Linux

```bash
cd logsec-agent
uv venv --python 3.11 .venv          # 建虚拟环境（没有 uv 就用：python3 -m venv .venv）
source .venv/bin/activate            # 激活
uv pip install -r requirements.txt   # 装依赖（没有 uv 就用：pip install -r requirements.txt）
cp .env.example .env                 # 然后编辑 .env，填上 DeepSeek API key
python scripts/build_db.py           # 建数据库（1 秒左右）
python -m pytest                     # 不花钱的测试，应该全部通过
python ask.py "case_010 里发生了什么可疑行为？请给出证据"
python chat.py                       # 多轮对话，输入 exit 退出
```

#### Windows（PowerShell）

```powershell
cd logsec-agent
uv venv --python 3.11 .venv          # 没有 uv 就用：py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1           # 激活（cmd 里用 .venv\Scripts\activate.bat）
uv pip install -r requirements.txt   # 没有 uv 就用：pip install -r requirements.txt
copy .env.example .env               # 然后用记事本编辑 .env，填上 DeepSeek API key
python scripts\build_db.py
python -m pytest
python ask.py "case_010 里发生了什么可疑行为？请给出证据"
python chat.py
```

> 装 uv：macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh | sh`；
> Windows `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`。

### 单次提问 vs 多轮对话

| 入口 | 行为 | 用在哪 |
|---|---|---|
| `ask.py`（`run.py ask`） | 问一个问题就退出，打印每一步工具调用 | 演示 ReAct、跑评测、看单题 |
| `chat.py`（`run.py chat`） | 一直聊，**同一次运行内记住前面所有内容**，输入 `exit` 退出 | 日常分析、给老师演示"追问" |

`ask.py` 加 `--quiet` 只看最终回答。

多轮对话实测（两轮，第二轮没有重复查库，直接用第一轮的上下文回答）：

```text
user> case_010 有几条登录成功的事件？
LogSec> case_010 共有 2 条登录成功事件，均为 EventID 4624：…… [E02102]、[E02106]

user> 刚才那几条登录分别来自哪个 IP？
LogSec> 刚才 2 条登录成功事件分别来自：Administrator ← 172.16.66.37 [E02102]；机器账户 01566S-WIN16-IR$ ← ::1 [E02106]
```

完整记录见 [`docs/demo-chat.md`](docs/demo-chat.md)。

> 注意"多轮对话"和"跨会话记忆"是两件事：多轮对话靠框架的会话状态，**关掉程序就忘**；
> 跨会话记住结论是第 5 周的记忆组件（`config.ENABLE_MEMORY`，现在故意关着）。

### 三种给 API key 的方式（优先级从高到低）

| 方式 | 怎么写 | 适合什么时候 |
|---|---|---|
| 命令行参数 | `python ask.py "问题" --api-key sk-xxx` | 临时换 key、给别人演示 |
| 环境变量 | `$env:DEEPSEEK_API_KEY="sk-xxx"`（PowerShell） | 一台机器上多个项目共用 key |
| `.env` 文件 | 复制 `.env.example` 成 `.env`，填 `DEEPSEEK_API_KEY=sk-xxx` | **日常推荐**，不用每次敲 |

同时还能临时覆盖模型和循环上限：

```bash
python ask.py "case_010 里发生了什么可疑行为？" --model deepseek-v4-pro   # 换更强（更贵）的模型
python chat.py --max-iters 15                                            # 允许多循环几轮
```

`.env` 已在 `.gitignore` 里，不会被提交；代码里也没有任何硬编码的 key。
> 用 `--api-key` 传参会留在 shell 历史里，公用电脑上请优先用 `.env`。

### Windows 实测记录

2026-11-18 在 Windows 11 + Python 3.11.5 + `agentscope==2.0.12` 上完整跑通：

| 步骤 | 结果 |
|---|---|
| `uv venv --python 3.11 .venv` + `uv pip install -r requirements.txt` | 成功，装好 60 多个依赖 |
| `python scripts\build_db.py` | 建库成功：events 6,633 / cases 250 / labels 250 |
| `python -m pytest` | 9 项测试全部通过（5.4 秒，不花钱） |
| `python ask.py "case_010 里发生了什么可疑行为？请给出证据"` | 自行调用 11 次工具，还原出"清安全日志 → 远程 Administrator 登录 → SAMR/LSARPC 枚举 → 重置机器账户密码"的链条，输入 27,441 / 输出 2,828 token |
| `python ask.py "case_000 里有没有暴力破解？哪个来源 IP 最活跃？"` | 结论对（183.62.140.253 最活跃、仅 1 条成功登录且与爆破无关），但**撞到 10 轮上限**：28 次工具调用、输入 120,162 token。原因是没有统计工具，只能一页页翻搜索结果 —— 这正是第 3 周要补的 |
| `python run.py chat` 连问两轮（"case_010 有几条登录成功？" → "**刚才**那几条登录来自哪个 IP？"） | 多轮对话正常：第二轮理解"刚才"指代，只补查了 `get_event` 详情，没有重新搜索；输入 4,719 token |

完整对话记录（含每一步工具调用、以及用 SQL 回查模型给出的数字）见
[`docs/demo-case010.md`](docs/demo-case010.md)、[`docs/demo-chat.md`](docs/demo-chat.md) 和
[`docs/demo-case000-ssh.md`](docs/demo-case000-ssh.md)。


---

## 目录结构

```
logsec-agent/
├── README.md            本文件
├── NOTICE.md            代码与数据来源、许可说明
├── requirements.txt     依赖（agentscope==2.0.12 等）
├── .env.example         API key 模板（复制成 .env 再填；.env 不会被提交）
├── config.py            路径、模型名、输出上限、各周功能开关（默认全关）
├── run.py               一条命令启动（自动找 .venv 的 Python，子命令 chat/ask/setup/db/test）
├── ask.py               单次提问，打印工具调用过程（演示 ReAct 用）
├── chat.py              多轮对话（同一次运行内记住前文）
├── docs/                设计文档与实测记录
│   ├── 02-系统方案设计_v0.4.md   小组的完整方案（8 周排期、分工、评测）
│   ├── demo-case010.md          一次完整 ReAct 对话的记录与解读
│   ├── demo-case010.log         上面那次对话的原始终端输出
│   ├── demo-case000-ssh.md      一次撞上循环上限的提问（含数字回查）
│   ├── demo-case000-ssh.log     上面那次对话的原始终端输出
│   ├── demo-chat.md             多轮对话实测（追问时复用上文）
│   └── 测试数据说明.md          两份数据的来源、规模与局限
├── logsec/              agent 本体
│   ├── agent.py         组装 agent：模型 + 工具 + 提示词 + 组件
│   ├── tools.py         3 个只读日志工具（已完成）
│   ├── prompts.py       系统提示词；第 3 周的固定回答格式占位
│   ├── db.py            只读打开数据库
│   ├── errors.py        友好的中文错误提示
│   ├── tools_week3.py   【第 3 周占位】补齐工具
│   ├── context.py       【第 4 周占位】上下文管理
│   ├── memory.py        【第 5 周占位】长期记忆
│   ├── evidence.py      【第 6 周占位】证据校验
│   └── ui.py            【第 6 周占位】界面 / 调用轨迹展示
├── scripts/
│   └── build_db.py      把原始日志导入 SQLite
├── eval/                【第 7 周】评测
│   ├── questions.json   3 道示例题
│   └── run_eval.py      评测脚本骨架（读标准答案已写好，主循环待实现）
├── tests/
│   └── test_tools.py    不调用模型的测试
└── data/
    ├── raw/             原始日志（evtx_data.csv、OpenSSH_2k.log）
    └── logsec.db        build_db.py 生成的数据库（不提交，可随时重建）
```

每个占位文件开头都写清楚了：**要做什么、怎么算做完、参考哪页文档**。

---

## 数据说明

| 表 | 内容 | 谁能读 |
|---|---|---|
| `events` | 6,633 条事件。`uid`（如 `E00042`）、`case_id`、时间、主机、日志通道、EventID、一行摘要、其余字段（JSON） | agent 工具 |
| `cases` | 250 个案件的概况：类型、事件数、主机、时间范围 | agent 工具 |
| `labels` | 标准答案：原始文件名 + ATT&CK 战术 | **只有评测脚本** |

- `case_000`：Linux sshd 日志（2,000 行，来自 [loghub](https://github.com/logpai/loghub)），大量暴力破解失败登录。原日志没有年份，时间存成 `MM-DD HH:MM:SS`。没有战术标签。
- `case_001`～`case_249`：每个对应一个 Windows EVTX 攻击样本文件（来自 [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)），共 4,633 条事件、8 种战术。
- **为什么要藏文件名**：EVTX 文件名里常直接写着技术名（如 `...Mimikatz...`），等于答案。所以案件编号是打乱的、不透露信息的；任何 agent 工具都不能返回 `labels` 表、文件名或战术标签（`tests/test_tools.py` 会逐条检查）。

---

## 已完成（第 1–2 周）

- [x] `scripts/build_db.py`：两份日志导入 SQLite，三张表，可重复运行
- [x] 3 个只读工具：`list_cases`（案件概况）、`search_events`（按案件/关键词/EventID 搜索）、`get_event`（单条详情）。输出紧凑、带 uid、有条数上限并提示"还有多少条没显示"
- [x] ReAct agent（AgentScope `Agent`）+ 中文系统提示词：结论必须引用 uid、查不到就说不知道
- [x] `chat.py` 多轮对话、`ask.py` 单次提问并打印工具调用序列和 token
- [x] 不调用模型的测试：建库行数、工具能查到东西、不泄露标签、工具不会卡在权限确认上

---

## 按周待办

分工：**同学 C**（大二）负责循环与工具；**同学 D**（大二）负责上下文、记忆与界面；**同学 B**（大三网安）负责数据、场景题目与评测判分。

每项做完的通用流程：在占位文件里实现 → 把 `config.py` 里对应开关改成 `True` → 按"验收"一栏检查 → `python -m pytest` 仍然全部通过。

| 周 | 负责 | 做什么 | 改哪个文件 | 怎么验收 |
|---|---|---|---|---|
| 1–2 | 全体 | 跑通本项目；每人读一遍 `logsec/agent.py`、`logsec/tools.py`；用 `ask.py` 各问 3 个问题，记录工具调用序列 | — | 每人能讲清楚"一次提问里 agent 调了哪些工具、为什么" |
| 3 | C | 补 3 个工具：事件前后时间窗上下文、按 EventID/主机计数、ATT&CK 战术说明查询 | `logsec/tools_week3.py`，开关 `ENABLE_EXTRA_TOOLS` | 每个新工具有测试；`ask.py` 中能看到新工具被调用；新工具不泄露标签 |
| 3 | C | 提示词要求固定输出"战术判断 + 置信度 + 证据 uid" | `logsec/prompts.py`，开关 `ENABLE_ANSWER_FORMAT` | 分析 3 个不同案件，输出都符合格式 |
| 3 | B | 整理 8 个战术的中文说明和典型日志迹象（给 `lookup_tactic` 用），把示例题扩到 10 道 | `data/attack_tactics.json`（新建）、`eval/questions.json` | C 的工具能读到；题目覆盖至少 5 种战术 |
| 4 | D | 用 `ContextConfig` 配自动压缩和工具结果截断，做开/关对比 | `logsec/context.py`，开关 `ENABLE_CONTEXT_MANAGEMENT` | 一张对比表（轮数、token、回答是否正确）；能指出压缩发生在哪一轮 |
| 5 | D | 接 `AgenticMemoryMiddleware` 长期记忆；规定记什么（已确认的结论、常见误报）、不记什么 | `logsec/memory.py`、`logsec/agent.py`，开关 `ENABLE_MEMORY` | 重启 `chat.py` 后还记得上次的结论；`memory/` 下的文件内容符合规定 |
| 5 | B | 整理"常见误报"清单（哪些看着可疑其实正常），作为记忆的种子内容 | 写在 `logsec/memory.py` 的说明或单独的 md | D 能用上 |
| 6 | D | 证据校验中间件：检查回答里引用的 uid 是否真实存在 | `logsec/evidence.py`，开关 `ENABLE_EVIDENCE_CHECK` | 不调模型的测试能抓出假 uid（如 `E99999`）；演示一次校验提示 |
| 6 | D | 网页界面 / 全屏界面 / 调用轨迹导出（三选一） | `logsec/ui.py`，开关 `ENABLE_FANCY_UI` | `chat.py` 打开新界面，能看到每次工具调用 |
| 7 | B（C 协助） | 评测：逐个案件让 agent 判断战术，与 `labels` 对比算准确率；各组件开/关对比 | `eval/run_eval.py` | 至少 20 个案件的准确率；至少两种配置的对比表 |
| 8 | 全体 | 整理结果、演示、写报告 | — | 现场演示一次完整的"提问 → 调工具 → 带证据回答"，展示评测对比表 |

**扩展（不排期，有余力再做）**：多智能体协作（如"分析员 + 复核员"，见 AgentScope 的 [Team Pipeline](https://docs.agentscope.io/en/versions/2.0.12/building-blocks/pipeline/team.md)）；服务化接口（见 [Agent as Service](https://docs.agentscope.io/en/versions/2.0.12/deploy/agent-service.md)）。

---

## 常见问题

**Q：问一句程序就退出了，是不是不能多轮对话？**
能。`ask.py` 是刻意做成"单次提问、打印每一步"的演示工具；多轮对话用 `chat.py`（或 `python run.py chat`），
同一次运行里会记住前面聊的内容。实测见 [`docs/demo-chat.md`](docs/demo-chat.md)。
另外注意：**关掉程序就忘**，因为 `launch_console` 不做会话持久化；跨会话记忆是第 5 周的组件。

**Q：报 `ModuleNotFoundError: No module named 'agentscope'`？**
用了系统的 Python 直接跑脚本，而依赖装在 `.venv` 里。两个办法：先 `.venv\Scripts\Activate.ps1` 激活虚拟环境，
或者直接用 `python run.py chat`（它会自动找 `.venv` 里的 Python）。

**Q：运行时提示"[第 X 周任务，尚未实现]"？**
你（或别人）把 `config.py` 里某个开关改成了 `True`，但对应功能还没写。把开关改回 `False`，或者去提示里的文件把功能写完。

**Q：提示"找不到数据库"或"没有找到 DEEPSEEK_API_KEY"？**
数据库：`python run.py db`（`run.py` 的其他子命令也会自动建）。key：看上面[三种给 key 的方式](#三种给-api-key-的方式优先级从高到低)；
key 只能放在 `.env` 里，**不要写进代码、截图或发到群里**。

**Q：Windows 上中文乱码或 `UnicodeEncodeError`？**
程序已经把输出设成 UTF-8。如果还有问题，先运行 `$env:PYTHONUTF8=1`（PowerShell）或 `set PYTHONUTF8=1`（cmd）再启动；也可以换用 Windows Terminal。

**Q：Windows PowerShell 激活虚拟环境时报"禁止运行脚本"？**
运行一次 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，或者改用 cmd 的 `.venv\Scripts\activate.bat`。

**Q：重新建库时报"文件被占用"（Windows）？**
关掉正在运行的 `chat.py` 和打开着 `logsec.db` 的软件（如 DB Browser for SQLite）再试。

**Q：一次提问要花多少 token？为什么有时显示"结束原因：exceed_max_iters"？**
实测：小案件（如 case_010，7 条事件）约 2 万输入 token、9 次工具调用；"case_000 里哪个 IP 最活跃"这类需要统计的问题约 16 万输入 token，
因为现在没有计数工具，agent 只能一页页翻搜索结果，翻满 10 轮（`config.MAX_ITERS`）后框架会强制它总结作答（回答通常仍可用）。
这正是第 3 周要补"统计类工具"的原因。

**Q：为什么工具调用不需要我确认？**
AgentScope 2.x 的 `FunctionTool` 默认每次调用都要用户确认。我们的工具都是只读的，在 `logsec/tools.py` 的 `build_tools()` 里标了
`is_read_only=True`，权限系统会走"只读快速通道"自动放行（见[权限文档](https://docs.agentscope.io/en/versions/2.0.12/building-blocks/permission-system/overview.md)）。
以后新加的工具如果会写东西，**不要**随手标只读。

**Q：日志里的 `RuleName` 字段写着 `technique_name=Credential Dumping`，这算泄露答案吗？**
不算我们泄露的：这是 Sysmon 配置里检测规则的命中名，是日志本身的内容（真实环境中分析员也看得到）。但它确实是很强的线索，
同学 B 做评测时可以加一组"屏蔽 RuleName"的对比实验。

**Q：想换更强的模型？**
改 `config.py` 里的 `MODEL_NAME = "deepseek-v4-pro"`。
