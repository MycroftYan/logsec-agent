# 实测记录：多轮对话（chat.py）

验证"同一次运行内会记住前面说过的内容"，用的是 `run.py chat`（等价于 `python chat.py`，只是自动用 `.venv` 里的 Python）。

| 项目 | 内容 |
|---|---|
| 日期 | 2026-11-18 |
| 环境 | Windows 11、Python 3.11.5、AgentScope 2.0.12、`deepseek-flash` |
| 命令 | `python run.py chat`（用管道喂了两轮问题，等价于在终端里手打） |
| 结果 | 两轮都答对；第二轮**没有重新查库**，直接用第一轮的工具结果回答 |

## 终端里的样子

```text
================================================================
日志安全分析 agent · 多轮对话
  模型：deepseek-flash    key 来源：.env 文件（.env）
  本次运行内会记住前面聊过的内容（关掉程序就忘了；跨会话记忆是第 5 周的组件）
  示例：case_010 里发生了什么可疑行为？ / case_000 里有没有暴力破解？
  输入 exit 或 Ctrl+D 退出；回答过程中按 Ctrl+C 可打断当前回答
================================================================
Chat with the agent. Type 'exit' (or Ctrl+D) to quit.

user> case_010 有几条登录成功的事件？
  → search_events {"case_id": "case_010", "event_id": 4624}
  ✓ 共找到 2 条事件
  → search_events {"case_id": "case_010", "keyword": "登录成功"}
  ✓ 共找到 2 条事件
LogSec> case_010 共有 2 条登录成功事件，均为 EventID 4624：
  1. 2020-09-17 10:57:44，Administrator 从 172.16.66.37 登录成功 [E02102]
  2. 2020-09-17 10:57:53，机器账户 01566S-WIN16-IR$ 从 ::1 登录成功 [E02106]

user> 刚才那几条登录分别来自哪个 IP？
  ✓ get_event E02102 / E02106      ← 只补查详情，没有重新搜索
LogSec> 这两条登录分别来自以下 IP：
  - Administrator 的登录来源 IP 是 172.16.66.37，源端口 49959 [E02102]
  - 01566S-WIN16-IR$ 的登录来源是 ::1（本机 IPv6 回环），源端口 53668 [E02106]
```

## 从这里能看出什么

- 第二轮问的是"**刚才**那几条"，模型理解指代，说明历史消息确实在上下文里（框架的 `agent.state` 保存会话）。
- 第二轮 token 只有 4,719 输入——它调用了 `get_event` 补端口，但没有重新 `search_events`，说明它复用第一轮的结果。
- **会话不落盘**：关掉程序重开，它就忘了。这是 `launch_console` 的设计（"no session management, no persistence"），
  也正是第 5 周记忆组件要补的：`config.ENABLE_MEMORY` 打开后，跨会话记住"已确认的结论、常见误报"。

## 两个常见误会

| 现象 | 原因 | 怎么办 |
|---|---|---|
| 问一句就退出了，好像不能多轮 | 用的是 `ask.py`（设计上就是单次提问、用来演示每一步） | 用 `python run.py chat` 或 `python chat.py` |
| 报 `ModuleNotFoundError: No module named 'agentscope'` | 直接 `python ask.py`，用的是系统 Python（3.14），依赖装在 `.venv` 里 | 用 `python run.py chat`，它自动找 `.venv` 里的 Python |
| 重开程序后不记得上次的结论 | 会话状态不持久化，属预期行为 | 第 5 周的记忆组件（现在开关是 `False`） |

## API key 从哪来

`python run.py chat` 自己不做模型调用，key 由它启动的 `chat.py` 读取，优先级：
`--api-key` 参数 > 环境变量 `DEEPSEEK_API_KEY` > 项目里的 `.env` 文件。

三种都没配时，`run.py` 会在启动前**问一次**并把 key 写进 `.env`（写进去之后就不再问了）：

```text
还没有 DeepSeek API key。三种给法任选一种：
  1) 现在粘贴一次，会存进本机 .env（推荐，之后不用再输）
  2) 跟着命令传：python run.py chat --api-key sk-xxx
  3) 设环境变量：$env:DEEPSEEK_API_KEY="sk-xxx"
  请粘贴 DEEPSEEK_API_KEY（输入时不显示）：
  已保存到 …\logsec-agent\.env
```
