![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/sc9vl5waw2rF4OpCs6fR0r7c08JKoc7qqdr1f8guLkxWsyZvxbG7yFVtlTpa5OylseickMssT8nI3UM4NNf2CyUgQq5HWRZYWkNVKSgHmu8g/0?wx_fmt=jpeg)

安装才7M ,我用 Rust 写了一个 AI Coding Agent，终端和桌面双形态
============================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

从去年底开始，AI Coding Agent 赛道卷得飞起。Cursor、Claude Code、Windsurf、Aider……每隔几周就冒出一个新工具。

但你有没有注意到一个有趣的事实：**这些工具全是 TypeScript 或 Python 写的。**

Cursor 是 Electron，Claude Code 是 Node.js，Aider 是 Python。它们确实好用，但作为一个 Rust 开发者，我总觉得缺了点什么——

*   • 为什么一个开发者工具自己还要装 Node 20+？
    
*   • 为什么冷启动要 1-2 秒？
    
*   • 为什么不能 `scp` 一个二进制文件到服务器上直接用？
    

于是我做了一个可能很蠢但也很酷的决定：**用 Rust 从零写一个 AI Coding Agent。**

不是 wrapper，不是套壳，是从 HTTP 请求、SSE 流解析、ReAct 循环、工具注册、权限确认、上下文管理到 UI 渲染，全部自己实现。

这篇文章聊聊这个项目的设计思路和关键实现。

### 咱们先看成果吧

项目叫 rust-agent\[1\]，顾名思义，就是一个用纯 Rust 写的 agent，已经在内部小群开源。

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2pSJcqyt6KXqGtPz4Q8at1NwahFpNkqJGiaj1GicPDtx59ED43kcbnYyibOSTQyXfoYCGR7Z7JgH82Hxic4GFsia3ugQc3fllibicXJrU/640?wx_fmt=png&from=appmsg "null")

  

目前提供两种形态：

**CLI 模式** — 基于 ratatui 的终端界面，SSE 逐 token 流式输出，适合服务器、SSH、终端重度用户：

![Cli 的方式，非常的丝滑，完善的确认机制](https://mmbiz.qpic.cn/sz_mmbiz_png/sc9vl5waw2qtMEQRxeLPmlrcFD8tbJJVibMZuqCQicia8YkAiaURz5R74ts78xx1V9MmGfSgSGibzWWbLUFquQsoSWUvG0rkHml2GKcqB0ySbCBE/640?wx_fmt=png&from=appmsg "null")

Cli 的方式，非常的丝滑，完善的确认机制

**App 模式** — Tauri v2 + React 桌面应用，Markdown 渲染、深色主题、侧边栏、可视化设置：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/sc9vl5waw2ricoBSgzialQDA0HtsLTl9haBMslAcxXzBSCY4pLHVuzYwEoRYkzobObPVPmjgXgQxQic4AMxaSKf784nVonD13VTGFvrmseLM4E/640?wx_fmt=png&from=appmsg "null")

  

两种模式共享同一套 Rust 核心引擎，数据完全互通。

### 架构：一核双壳

大多数做法是先写一个版本，再移植到另一个平台。我们的做法不同——**先抽出核心引擎，再接不同的壳。**

`┌────────────────────────────────────────────────────┐   │                 rust-agent-core                     │   │  Agent Engine · 9 Tools · MCP · Skills · Memory    │   │  Session · Plan · Config · Orchestrator            │   └──────────┬────────────────────┬────────────────────┘              │                    │       ┌──────▼──────┐     ┌──────▼──────────┐       │ TUI (ratatui)│     │ Tauri v2 + React│       │ 终端原生      │     │ 桌面原生应用     │       └──────────────┘     └─────────────────┘`

核心是一个 Rust workspace，三个 crate：

*   • **`rust-agent-core`**（lib）：Agent 引擎、工具系统、MCP、Session、Memory……所有业务逻辑
    
*   • **`rust-agent-tui`**（bin）：终端界面，基于 ratatui + crossterm
    
*   • **`rust-agent-tauri`**（bin）：桌面应用，Tauri v2 后端 + React/TypeScript 前端
    

关键角色是 `AgentOrchestrator`——它封装了初始化、消息处理、命令分发的所有逻辑。TUI 和 Tauri 都只需要持有一个 Orchestrator 实例，调用同样的接口。

这意味着新增一个功能（比如 task\_plan），只需要改 core 里的代码，两个前端自动获得能力。这个架构决策省了我们无数重复工作。

### ReAct 状态机

很多开源 Agent 的核心循环长这样：

`while True:       response = llm.chat(messages)       if response.has_tool_calls:           for tc in response.tool_calls:               result = execute_tool(tc)               messages.append(result)       else:           break`

看起来简单对吧？但一旦要加上 token 预算管理、上下文压缩、取消机制、重试逻辑，这个 while 循环就会变成意大利面。

我们的做法是把它建模为一个 **显式状态机**：

`enum LoopState {       Prepare,                    // 检查预算、是否需要压缩       Compress,                   // LLM 驱动的上下文摘要       Inference,                  // 调用 API       Dispatch(StreamedResponse), // 分发：有 tool_calls 还是最终回答       ExecuteTools { calls, idx },// 逐个执行工具       Complete(CompleteReason),   // 终止   }`

每个状态有清晰的职责和转移条件。整个循环就是一个 `loop + match`：

`loop {       state = match state {           LoopState::Prepare => { /* 检查预算 → Compress 或 Inference */ }           LoopState::Compress => { /* 压缩上下文 → Prepare */ }           LoopState::Inference => { /* 调 API → Dispatch */ }           LoopState::Dispatch(resp) => { /* 分发 → ExecuteTools 或 Complete */ }           LoopState::ExecuteTools { .. } => { /* 执行工具 → Prepare */ }           LoopState::Complete(_) => { return Ok(()); }       };   }`

这样做的好处：

1.  1. **每个关注点隔离**——预算检查、压缩、推理、工具执行各司其职
    
2.  2. **取消机制天然融入**——每个状态转移前都可以检查 `CancellationToken`
    
3.  3. **新状态易扩展**——后来加 Compress 状态几乎没改已有代码
    

### SSE 手动解析：没有轮子，自己造

Rust 生态里没有趁手的 LLM streaming SDK。Python 有 openai 库，JS 有 @ai-sdk，Rust 呢？基本没有成熟的。

所以我们手搓了 SSE 解析。核心逻辑出奇简单：

`// 拿到 reqwest::Response，按行读   letmut stream = response;   loop {       letchunk = stream.chunk().await?;       line_buffer.push_str(&chunk_str);          whileletSome(newline_pos) = line_buffer.find('\n') {           letline = line_buffer[..newline_pos].trim();              if line == "data: [DONE]" { break; }              ifletSome(data) = line.strip_prefix("data: ") {               letparsed: Value = serde_json::from_str(data)?;               letdelta = &parsed["choices"][0]["delta"];                  // 处理 content delta               ifletSome(content) = delta["content"].as_str() {                   tx.send(AgentUpdate { streaming_delta: Some(content) });               }                  // 处理 tool_call delta（增量拼接）               ifletSome(tc_deltas) = delta["tool_calls"].as_array() {                   // 按 index 拼接 function_name 和 arguments               }           }       }   }`

大约 150 行代码，处理了 content streaming、tool call 增量拼接、reasoning\_content（deepseek-reasoner 的思考过程）、usage 统计、取消。

没有依赖，没有魔法，出了问题直接 debug 原始 JSON，比任何 SDK 都好排查。

### 上下文管理：Token 预算 + LLM 压缩

Agent 跑几十轮工具调用后，上下文很容易爆。我们做了两层保护：

**第一层：tiktoken 预估 + 预算卡控**

每次推理前用 tiktoken 的 BPE 编码器估算当前消息 token 数。超过上限直接停止（不是截断丢消息，是优雅终止并告诉用户）。

**第二层：LLM 驱动的上下文压缩**

当 token 使用率超过 80%，自动触发压缩：

1.  1\. 保留系统消息 + 最近 6 条消息
    
2.  2\. 把旧消息格式化后发给 LLM："请总结这段对话的关键信息"
    
3.  3\. 用摘要替换旧消息
    

`压缩前: [System] [Msg1] [Msg2] ... [Msg20] [Msg21] ... [Msg26]   压缩后: [System] [Summary of Msg1-20] [Msg21] ... [Msg26]`

这比简单丢弃旧消息好得多——Agent 保留了任务的完整上下文理解，只是换了一种更紧凑的表达方式。

用户也可以手动触发 `/compact rust trait 重构`，让压缩器重点保留特定主题。

### 自主规划：让 Agent 自己决定要不要做计划

这是我们最新加的特性，灵感来自 Claude Code，哈哈，直接借鉴

以前的 Plan Mode 需要用户手动输入 `/plan`。但实际使用中，Agent 应该自己判断——你让它改个 typo，不需要计划；你让它重构三个文件，它应该自动拉个计划出来。

实现方式是在 ReAct 循环内新增一个 `task_plan` 工具：

`{     "name":"task_plan",   "parameters":{       "action":"create | update | list",       "task":"任务描述",       "steps":[{"title":"...","description":"..."}],       "step_id":1,       "status":"inProgress | completed | failed"   }   }`

Agent 在系统提示中被告知：当任务需要 3 步以上时，先调用 `task_plan(action: "create")` 创建计划，然后每执行一步就调用 `task_plan(action: "update")` 更新状态。

关键设计：**`task_plan` 工具和 Agent 通过 `Arc<Mutex<TaskPlanState>>` 共享状态。** 工具执行后，Agent 引擎自动读取共享状态，发送 `PlanDisplay` 更新到 UI。UI 层（TUI/App）收到后就地更新计划展示，用户看到的是实时变化的进度条。

数据流：

`LLM: "这个任务比较复杂，让我先做个计划"     → tool_call: task_plan(action: "create", steps: [...])     → 工具更新 TaskPlanState     → Agent 检测到 task_plan → 读取 state → 发送 PlanDisplay     → UI 渲染计划面板      LLM: "第一步完成了"     → tool_call: task_plan(action: "update", step_id: 1, status: "completed")     → UI 就地更新：[ ] → [✓]`

整个过程是 Agent 自主驱动的。用户只管提需求，Agent 自己决定要不要做计划、怎么拆步骤、什么时候推进。

### 工具确认：安全的分级授权

一个 AI Agent 能读你的文件、执行 shell 命令——这事必须谨慎处理。

我们的方案是 **分级确认 + 智能自动批准**：

`readonly 工具 (file_read, search, glob)     → 工作区内自动执行，不弹窗     → 工作区外需要确认      write 工具 (file_write, file_edit, shell_exec, lint)     → 总是需要确认     → 但支持 [A] Always 自动批准`

`[A] Always` 的粒度设计是关键：

*   • `file_edit` 按 A → 工作区内所有文件编辑都自动通过
    
*   • `shell_exec` 按 A → **只按二进制名批准**。你批准了 `cargo`，后续 `cargo build`、`cargo test` 都自动通过。但 `rm` 来了？对不起，降级为一次性 \[Y\]
    

这个设计让你能流畅地工作——按一次 A，后续同类操作不再打扰。但危险操作永远不会被静默批准。

`const DANGEROUS_COMMANDS: &[&str] = &[       "rm", "rmdir", "sudo", "su", "chmod", "chown",       "kill", "pkill", "killall", "shutdown", "reboot",       "mkfs", "fdisk", "dd", "format", "mv",   ];`

碰到这些，`[A]` 自动降级为 `[Y]`，只批准这一次。

### MCP支持：让我们的 agent 可以站在巨人的肩膀上

![](https://mmbiz.qpic.cn/sz_mmbiz_png/sc9vl5waw2ordO1QlsWy1icRZAeuoOk0vKffgFp3jc2gVEDmhrEheeTp2jTa2mM2uPlE0ufnoMwibBu2dbCLaFAGVXgLicKQNSyn9Or2efreKg/640?wx_fmt=png&from=appmsg "null")

  

自己造轮子不意味着什么都自己写。通过 Model Context Protocol\[2\]，我们可以接入社区已有的大量工具。

MCP 服务器以子进程方式启动，通过 stdin/stdout JSON-RPC 2.0 通信：

`[[mcp_servers]]   name = "github"   command = "npx"   args = ["-y", "@modelcontextprotocol/server-github"]   [mcp_servers.env]   GITHUB_TOKEN = "ghp_xxxx"`

启动时：`initialize` → `tools/list` → 注册到 ToolRegistry。

注册完成后，MCP 工具和内置工具没有任何区别——统一的 Tool trait，统一的确认机制，统一的 token 预算管理。Agent 甚至不知道它调用的是内置工具还是 MCP 工具。

在 App 模式下，还有可视化的 MCP 服务器管理界面——添加、删除、重连，能看到每个服务器提供了多少工具。

### Skills支持：让我们的 agent可插拔各种专家分身

有时候你希望 Agent 用特定的思路工作——比如做 code review 时按安全、性能、质量的维度逐项检查，而不是笼统地说"代码看起来不错"。

Skills 系统让你可以给 Agent 注入"人格"：

`---   name: code-review   description: Code review expert mode   ---      # Code Review      When reviewing code, systematically analyze:      ## Security   - Check for injection vulnerabilities   - Verify authentication and authorization   ...`

放在 `.rust-agent/skills/code-review/SKILL.md`，然后 `/skill code-review` 激活。

实现上就是把 Skill 内容追加到系统提示。简单但非常有效——我们内置了 `code-review`、`debug`、`refactor` 三个技能，团队里可以创建项目专属的 skill，让每个成员的 Agent 都用同样的流程工作。

### 长期记忆：越用越聪明

Agent 完成一个 Plan Mode 任务后，会自动提炼经验教训：

`{     "keywords": ["rust", "trait", "refactor"],     "lesson": "提取 trait 时先确认所有实现类的方法签名一致，否则需要引入关联类型"   }`

下次遇到相似任务，这些经验会通过关键词匹配自动注入规划 prompt。

没有向量数据库，没有 embedding，就是关键词重叠计数。为什么不用更复杂的方案？因为项目级的经验通常就那么几十条，关键词匹配的准确率足够高。

工程上最正确的做法往往是最简单的那个。

### 双模型：快的跑任务，强的做决策

Agent 内部维护两个模型角色：

*   • **DEFAULT\_MODEL** — 日常对话、工具调用、Plan 步骤执行
    
*   • **THINK\_MODEL** — 任务规划、失败反思、经验总结
    

`// Plan Mode 规划阶段切到推理模型   agent.set_model_temporarily(&think_model);   let plan = agent.streaming_completion(&plan_prompt, ...).await?;   agent.restore_model();      // 执行阶段切回快模型   agent.process_message(&step_prompt, tx, cancel).await?;`

这不是噱头。推理模型在任务拆解和失败分析上的质量明显优于对话模型，但它慢且贵。日常工具调用完全不需要那么强的推理能力。两个模型各司其职，兼顾了成本、速度和质量。

### Tauri v2：这一次，我们给不爱终端的人一个选择

不是每个人都喜欢终端。所以我们用 Tauri v2 做了一个桌面应用。

Tauri 的核心优势是：**Rust 后端 + Web 前端，但产物是原生应用，不是 Electron 那种打包一个 Chromium 的做法。**

后端是 23 个 Tauri command，通过 `Channel<AgentEvent>` 实现流式推送：

`#[tauri::command]   async fn send_message(       state: State<'_, TauriAppState>,       message: String,       channel: Channel<AgentEvent>,   ) -> Result<(), String> {       // 启动 Agent 处理消息       // 通过 channel 推送 StreamingDelta、ToolCall、PlanUpdate 等事件   }`

前端是 React + TypeScript + Zustand + Vite。用 Zustand 做状态管理，react-markdown 渲染消息，支持 GFM 表格、代码高亮。

设置页面分了 5 个 Tab：General、Workspace、Theme、MCP Servers、Skills。所有配置都可以在 UI 里操作，不用手写 TOML 文件。

两种模式的数据完全互通——Session、Skills、Memory、Config 共享同一套文件系统存储。你可以在终端里开始一个会话，回到桌面继续。

### 几个关键设计决策

回顾整个开发过程，有几个决策影响深远：

**1\. SSE 手动解析，不用 SDK**

Rust LLM 生态不成熟，与其等别人造轮子，不如自己用 reqwest 直接解析。150 行代码，完全可控。好处是出了问题直接看原始 JSON，比任何 SDK 都好 debug。

**2\. CancellationToken 全链路贯穿**

tokio-util 提供的 CancellationToken，从 SSE 流读取、工具执行到 Plan Mode 每个阶段都检查。用户按 Ctrl+C 时，不管 Agent 在干什么，都能在下一个 await 点优雅退出。

**3\. 先抽核心库，再接前端**

如果一开始就把逻辑写在 TUI 代码里，后面加 Tauri 就是噩梦。Orchestrator 抽象让两个前端的接入代码都不超过 500 行。

**4\. 路径沙箱 + 危险命令黑名单**

readonly 工具在工作区内自动执行，目录外需确认。`rm`/`sudo` 等命令永远不能自动批准。安全不是事后补的功能，而是架构层面的约束。

**5\. 状态机而非 while 循环**

把 ReAct 循环建模为显式状态机，让每个关注点（预算、压缩、推理、工具执行）都有独立的状态和清晰的转移条件。加新功能时不用改已有逻辑。

写在最后
----

这个项目不是要替代 Cursor 或 Claude Code——它们有庞大的团队和生态。

这个项目证明的是：**一个人用 Rust 也能做出一个功能完整、体验不差的 AI Coding Agent。** 终端和桌面双形态、9 个内置工具、自主规划、MCP 生态扩展、长期记忆、双模型架构——该有的都有。

Rust 在 AI 应用层目前确实生态薄弱。没有 LangChain，没有 @ai-sdk，连个像样的 OpenAI SDK 都没有。但这恰恰是机会——当你不被框架限制时，你可以从第一性原理出发，做出更精简、更快、更可控的东西。

项目完全开源，MIT 协议。欢迎 Star、Fork、提 Issue。

如果你也是 Rust 开发者，也对 AI Agent 感兴趣——来一起造轮子。

* * *

> **rust-agent** — 用 Rust 写的 AI Coding Agent，终端 + 桌面双形态。

#### 引用链接

`[1]` rust-agent: _https://github.com/coder-brzhang/rust-agent_  
`[2]` Model Context Protocol: _https://modelcontextprotocol.io/_