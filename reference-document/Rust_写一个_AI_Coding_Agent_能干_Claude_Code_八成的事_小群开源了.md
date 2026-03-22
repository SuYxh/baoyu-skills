![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/sc9vl5waw2osyv4S3yKLb7gyleNOIvib20A8E1ic2A3QMzlVcOrVsU6WWJ2fkuT3dVOiaJOep9e0WYic3EmkWsZaMfL4ic4e84NRhAUu45tvricq8/0?wx_fmt=jpeg)

Rust 写一个 AI Coding Agent，能干 Claude Code 八成的事，小群开源了
==================================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

一个 6MB 的二进制文件，能做到 Claude Code 八成的事，模型使用 DeepSeek 测试，写代码，迭代项目问题不大，这就是我今天要讲的故事，请搬好你的板凳。

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2r24dXU989Rf6tHnVlhPhoJYnRVFiaS73xr4uT0gE6xiaLTOKskpoJJ9Lp8U53hmlkTA2iaVKaz6WTAbX1dOASpJOtNRrbBhAzffo/640?wx_fmt=png&from=appmsg "null")

  

### 为什么要造这个轮子

市面上的 AI Coding Agent 大多是 TypeScript/Python 写的——Cursor 是 Electron，Claude Code 是 Node.js，Aider 是 Python。它们都很好用，但有几个绕不开的问题：

1.  1. **运行时依赖重** — 需要 Node 20+ 或 Python 3.10+，CI/Docker 里多装一层
    
2.  2. **启动慢** — 冷启动动辄 1-2 秒，Python 的更慢
    
3.  3. **分发不便** — 不是一个文件丢过去就能用的事
    

所以我们用 Rust 从零写了一个：**4800 行代码，14 个依赖，编译出一个 6MB 的二进制**。`scp` 到服务器上就能跑，不需要任何运行时。

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2qhY8lb5s3mkWyWvbIGuiakmkUMJ4vh0GVuvtKAP4CIWj4mlibT1IH8mqIemt3KZEwJ1IUkhGYhmxzqj5eySGqBnhOBekVS6T0Uw/640?wx_fmt=png&from=appmsg)

它不是玩具。它有完整的 ReAct Agent Loop、7 个内置工具、双模型架构、Plan Mode、MCP 协议支持、Skills 系统、长期记忆——该有的都有。

### 核心循环：ReAct in 200 行

Agent 的核心是一个经典的 ReAct（Reason + Act）循环。LLM 思考要做什么 → 调用工具 → 拿到结果 → 继续思考，最多跑 10 轮：

`User: "帮我修复 src/parser.rs 的编译错误"     │     ▼   ┌─────────────────────────────────┐   │  LLM 推理 (SSE Streaming)       │ ◄─── 逐 token 渲染到 TUI   │  "让我先看看错误信息..."         │   │  → tool_call: shell_exec        │   │    args: { cmd: "cargo build" } │   └──────────┬──────────────────────┘              ▼   ┌─────────────────────────────────┐   │  执行工具 (需确认)               │ ◄─── [Y] Yes / [N] No / [A] Always   │  结果: "error[E0308]: ..."      │   └──────────┬──────────────────────┘              ▼   ┌─────────────────────────────────┐   │  LLM 继续推理                    │   │  "类型不匹配，需要改第 42 行..."  │   │  → tool_call: file_edit          │   └──────────┬──────────────────────┘              ▼           ... 重复直到任务完成或达到 10 轮`

实现上，每轮都是一次 SSE streaming 请求。响应里如果包含 `tool_calls`，就执行工具、把结果追加到消息历史、再发下一轮请求。没有 tool\_calls 就是最终回答，循环结束。

关键代码在 `src/agent.rs` 的 `process_message()` 方法里，大约 200 行。

### 7 个内置工具

这 7 个工具覆盖了 "读、写、改、搜、跑、查、委" 的完整开发流程：

Tool

说明

安全级别

`file_read`

读取文件内容

readonly — 工作区内自动执行

`file_write`

创建或覆盖文件，自动创建父目录

write — 需确认

`file_edit`

搜索替换编辑（精确匹配 old\_string → new\_string）

write — 需确认

`search`

ripgrep 全文搜索，支持正则和 glob

readonly

`shell_exec`

执行 shell 命令，支持超时

write — 需确认

`lint`

自动检测项目类型并跑 linter（clippy/eslint/ruff）

write — 需确认

`delegate_task`

委托子任务给独立上下文的子 Agent

write — 需确认

工具通过 `Tool` trait 统一抽象，注册到 `ToolRegistry`，Agent 按名字调用。新增工具只需实现一个 trait：

`#[async_trait]   pubtraitTool: Send + Sync {       fnname(&self) -> &str;       fndescription(&self) -> &str;       fnparameters_schema(&self) -> Value;       fnneeds_confirmation(&self) ->bool;       asyncfnexecute(&self, args: &Value) ->Result<String>;   }`

#### 确认机制：不是 Y/N 那么简单

所有 write 工具执行前需要用户确认。但如果每次 `cargo test` 都要按 Y，体验就太差了。所以我们做了分级：

*   • **`[Y]` Yes** — 本次允许
    
*   • **`[N]` No** — 本次拒绝
    
*   • **`[A]` Always** — 自动批准，但粒度因工具而异
    

`[A]` 的粒度是关键设计点：

Tool

`[A]`

 批准范围

`file_write`

 / `file_edit`

工作区内该工具全部自动批准

`search`

 / `lint`

同上

`shell_exec`

**按二进制名**

批准 ,比如批准 `cargo` 后，`cargo build`、`cargo test`、`cargo clippy` 都自动通过

危险命令

`rm`

、`sudo`、`chmod`、`kill`、`dd`、`mv` 等 — `[A]` 降级为一次性 `[Y]`，永远不能自动批准

这意味着你可以放心地按 `[A]`。Agent 要跑 `cargo test` 你按一次 A，后续所有 cargo 命令都自动通过。但它要跑 `rm -rf build/`？即使按 A 也只批准这一次。

### 双模型架构：快的跑任务，强的做决策

一个有意思的设计：Agent 内部有两个模型角色。

`┌──────────────────────────────────────────────┐   │           rust-agent                         │   │                                              │   │   DEFAULT_MODEL (deepseek-chat)              │   │   ├── 普通对话                                │   │   ├── 工具调用 (ReAct loop)                   │   │   └── Plan Mode 步骤执行                      │   │                                              │   │   THINK_MODEL (deepseek-reasoner)            │   │   ├── /plan 任务拆解                          │   │   ├── 执行失败反思                             │   │   └── 完成后经验提炼                           │   └──────────────────────────────────────────────┘`

日常对话和工具调用用快模型（deepseek-chat），需要深度推理的场景——任务规划、失败反思、经验总结——切换到推理模型（deepseek-reasoner）。两个模型各司其职，兼顾速度和质量。

模型切换在代码层面就是改 `self.model` 字段，但 Agent 会在 Plan Mode 的不同阶段自动切换，用户无感。

### Plan Mode：规划 → 执行 → 反思 → 记忆

这是最复杂也最有价值的功能。当任务太大不适合一股脑丢给 Agent 时，用 `/plan`：

`/plan 重构认证模块，提取公共接口并添加 JWT 支持`

Agent 会启动一个完整的生命周期：

`Planning (THINK_MODEL 生成计划)       ↓   AwaitingApproval ──[N]──→ abort       ↓ [Y]   Executing (DEFAULT_MODEL 逐步执行)       ↓ 某步失败?   Reflecting (THINK_MODEL 分析原因, 最多 2 次)       ↓   Adjusting (修改后续步骤)       ↓ 全部完成   Summarizing (提炼 lessons learned)       ↓   Complete`

TUI 里会实时显示进度：

`Plan: "重构认证模块，提取公共接口并添加 JWT 支持"     1. [✓] 阅读现有认证代码     2. [▶] 提取公共接口     3. [ ] 实现 JWT 验证     4. [ ] 更新测试     5. [ ] 集成测试`

最关键的环节是**反思**。如果第 3 步执行失败，Agent 不会傻傻地重试——它会切换到 THINK\_MODEL 分析"为什么失败了"，然后可能调整后续步骤的策略。这比简单重试有效得多。

完成后，Agent 会自动提炼这次任务的经验教训，存入长期记忆。下次遇到类似任务时，这些经验会自动注入到规划 prompt 中。

### 长期记忆：Agent 会越用越聪明

记忆存储在 `.rust-agent/memory/lessons.json`，格式很简单：

`[     {       "id": "550e8400-...",       "keywords": ["rust", "trait", "refactor"],       "lesson": "提取 trait 时先确认所有实现类的方法签名一致，否则需要引入关联类型",       "created_at": "2025-01-15T10:30:00Z"     }   ]`

下次 `/plan` 时，系统用关键词匹配检索相关记忆，注入 prompt。这是一个极简的 RAG——没有向量数据库，没有 embedding，就是关键词重叠计数。简单，但对于项目级的经验复用已经够用了。

### Session：JSONL 增量持久化

每次启动自动创建 session，对话自动保存，不需要手动操作。

存储格式是 JSONL——第一行是元数据，后续每行一条消息：

`{"id":"20250214-143052","created_at":"...","updated_at":"...","summary":"帮我重构认证模块","message_count":5}   {"role":"user","content":"帮我重构认证模块"}   {"role":"assistant","content":"让我先阅读...","tool_calls":[...]}   {"role":"tool","tool_call_id":"...","content":"..."}`

为什么用 JSONL 而不是 JSON？

1.  1. **增量写入** — 新消息直接 append 一行，不需要读-改-写整个文件
    
2.  2. **抗损坏** — 写入中途崩溃只丢最后一行，不会破坏整个文件
    
3.  3. **列表高效** — `/sessions` 只需要读每个文件的第一行就能拿到摘要，不加载消息
    

Session 相关命令：

`/sessions                      # 列出最近会话，当前标 *   /resume 20250213-091015        # 恢复指定会话   /resume                        # 恢复最近一个   /clear                         # 保存当前，开始新会话`

### MCP：别人造好的轮子，直接接上

通过 Model Context Protocol\[1\] 集成外部工具。MCP 服务器以子进程方式启动，通过 stdin/stdout JSON-RPC 2.0 通信。

配置很简单：

`# .rust-agent/config.toml   [[mcp_servers]]   name = "github"   command = "npx"   args = ["-y", "@modelcontextprotocol/server-github"]   [mcp_servers.env]   GITHUB_TOKEN = "ghp_xxxx"`

启动时自动连接所有 MCP 服务器，发送 `initialize` → `tools/list`，拿到工具定义后注册到 ToolRegistry。对 Agent 来说，MCP 工具和内置工具没有任何区别——统一注册，统一调用，统一确认。

### Skills：可插拔的专家人格

有时候你希望 Agent 切换到一个特定的"模式"——比如专注做 code review，或者按特定的 debug 流程排查问题。

Skills 就是一组注入 system prompt 的指令模板，用 YAML frontmatter + Markdown 格式：

`---   name: code-review   description: Code review expert mode   ---      # Code Review      When reviewing code, systematically analyze:      ## Security   - Injection vulnerabilities   - Authentication issues   ...`

放在 `.rust-agent/skills/code-review/SKILL.md`，然后：

`/skill code-review      # 激活   /skill off              # 关闭`

Skills 支持全局（`~/.rust-agent/skills/`）和工作空间（`./project/.rust-agent/skills/`）两级，同名 skill 工作空间优先。

### 两级配置：全局 + 工作空间

`~/.rust-agent/                     ← 全局 (用户级)   ├── config.toml                    ← API Key, 默认模型   └── skills/                        ← 通用技能      ./project/.rust-agent/             ← 工作空间 (项目级)   ├── config.toml                    ← 项目覆盖配置   ├── skills/                        ← 项目专属技能   ├── sessions/                      ← 会话记录 (JSONL)   └── memory/                        ← 长期记忆       └── lessons.json`

配置优先级：`环境变量 > 工作空间 config.toml > 全局 config.toml > 默认值`

首次运行没有 API Key 时，会交互式引导你完成配置：

`Welcome to rust-agent!      No API key found. Let's set one up.   Enter your DeepSeek API key (sk-...): sk-xxxxx   API base URL (press Enter for default: https://api.deepseek.com/v1):      Config saved to /Users/you/.rust-agent/config.toml`

一个二进制、一个配置文件，就是全部部署物。

### 架构一览

`src/   ├── main.rs           # 事件循环、命令分发、TUI 生命周期       (654 行)   ├── agent.rs          # ReAct loop、SSE streaming、确认流程    (860 行)   ├── app.rs            # 应用状态、消息模型、输入处理             (281 行)   ├── plan.rs           # Plan Mode 7 阶段生命周期               (435 行)   ├── session.rs        # JSONL 会话持久化                        (240 行)   ├── config.rs         # 两级配置加载与合并                       (171 行)   ├── workspace.rs      # 工作空间发现与路径管理                   (144 行)   ├── mcp.rs            # MCP 客户端 (JSON-RPC 2.0 over stdio)   (250 行)   ├── sub_agent.rs      # 子 Agent 隔离执行                       (216 行)   ├── memory.rs         # 长期记忆 (lessons.json)                 (95 行)   ├── skills.rs         # SKILL.md 解析与管理                     (161 行)   ├── prompts.rs        # Plan/反思/提炼 prompt 模板               (89 行)   ├── tools/            # 7 个内置工具                             (575 行)   │   ├── mod.rs        #   Tool trait + ToolRegistry   │   ├── file_read.rs  #   文件读取   │   ├── file_write.rs #   文件写入   │   ├── file_edit.rs  #   搜索替换   │   ├── search.rs     #   ripgrep 搜索   │   ├── shell_exec.rs #   Shell 命令   │   ├── lint.rs       #   自动 Linter   │   └── delegate.rs   #   子任务委托   └── tui/              # 终端界面                                (469 行)       ├── mod.rs        #   终端初始化/恢复       ├── ui.rs         #   渲染：消息流、状态栏、确认弹窗、Plan       └── event.rs      #   键盘事件轮询                                                       ─────────────                                                       合计 ~4800 行`

14 个直接依赖：`tokio`（异步运行时）、`reqwest`（HTTP）、`ratatui` + `crossterm`（TUI）、`serde` + `serde_json`（序列化）、`toml`（配置）、`chrono`（时间）、`uuid`（ID 生成）、`anyhow`（错误处理）、`async-trait`、`tokio-util`、`unicode-width`、`dotenv`。

没有 LLM SDK，没有 Agent 框架——HTTP + SSE 手动解析，这也是 Rust 生态的现状：没有现成的轮子，所以造了一个。

### 几个关键设计决策

*   • **SSE 手动解析** — 没用任何 SSE 库，直接 `reqwest::Response` 按行读，解析 `data: {...}` 行。简单可控，出问题好调试
    
*   • **CancellationToken** — tokio-util 提供。Agent 运行在 `tokio::spawn` 里，主线程持有 cancel handle，Ctrl+C 时 cancel，Agent 在每个 `await` 点检查并退出
    
*   • **Context Window 管理** — 按字符数估算 token（1 char ≈ 1 token 对中文是偏保守的估计），超限时从最旧的消息开始裁剪
    
*   • **网络重试** — 429/500/502/503 自动指数退避重试，最多 3 次
    
*   • **路径沙箱** — readonly 工具限制在工作目录内自动执行，目录外需要确认
    
*   • **Sub-Agent 隔离** — `delegate_task` 启动的子 Agent 有独立的消息历史和工具集（只有 readonly 工具），不污染主 Agent 上下文
    

### 写在最后

需要源码？在此

https://github.com/coder-brzhang/rust-agent

不过需要小群进入小群，或者说看需要的人是否很多，可以考虑拉个公开小群。看私信情况了。

#### 引用链接

`[1]` Model Context Protocol: _https://modelcontextprotocol.io/_