![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XIaJt1MSaiaOj8GTWZnKyTNDZ9r9sFiajddwH4HK3icVeEq8zjF5mYdavcg/0?wx_fmt=jpeg)

从 800 行到 1000 行：我的 Agent 实现了分层记忆，接入了 MCP 能力，还暴露了 WebUI
======================================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

回顾上次我们做了什么，[上一篇文章中，我把代码从 300 行，增加到了 800 行](https://mp.weixin.qq.com/s?__biz=MzkxNzY0OTA4Mg==&mid=2247492262&idx=1&sn=073962913c4a35628b7c033dcf431507&scene=21#wechat_redirect)，然后实现了一个 Plan Agent：

*   • 基本对话 + 流式输出
    
*   • 会话持久化（JSONL）
    
*   • 计划管理（createPlan → execute → update）
    
*   • 工具调用（文件读写、Shell 命令、ripgrep 搜索）
    

上一次的迭代，我们可以持久化会话，加载会话继续对话，然后还可以让 agent做规划，并且按照规划一步一步执行，基本上已经是算的上是一个五脏俱全的 Agent 了。

但是我们还要继续追求，这次，我继续迭代，目标是让它更像一个"真正的 Agent"。

### 所以，这次我做了什么?

模块

新增能力

工具系统

模块化拆分 + editFile + lintFile

记忆系统

分层记忆：AGENT.md + 会话摘要 + 滑动窗口

架构

核心逻辑抽离，CLI 和 Web UI 共用

交互

Web UI + WebSocket 实时通信

生态

MCP 协议支持，可接入外部工具

先来看看这些特性

![我本次新增的工具](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XIczDZqNzdfKhCH57QicQTpl3Gz1ZiaJQcOIxeYDFO48fIEHkw3vagw6gg/640?wx_fmt=png&from=appmsg "null")

我本次新增的工具

![mcp 的支持](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XIMrM0DkAxlH67cQKMibX8ZmHWZ6Qzjs3474oPvkGzzkjfrnicXASsumhg/640?wx_fmt=png&from=appmsg "null")

mcp 的支持

代码量从 800 行涨到 1500+ 行，然后增加了已 UI，代码量到了 2500+，其实主要是 webUI 多了快 1000 行来着，实际的逻辑并不复杂。这波更新更重要的是：**我对 Agent 的理解更深了**。

### 一、工具系统重构

我们最初的版本，所有工具都塞在一个 `file.js` 里，400 多行，越来越难维护。为了便于维护，我做了拆分成模块，按职责分类：

`tools/   ├── index.js        # 工具注册中心   ├── filesystem.js   # 文件系统（readFile, writeFile, editFile...）   ├── shell.js        # Shell 命令（runCommand, searchContent）   ├── plan.js         # 计划管理（createPlan, updatePlanStep...）   ├── lint.js         # 代码检查（lintFile, lintFiles）   └── utils.js        # 通用工具（getCurrentTime, think）`

这样做的好处是，我的分类更加明确，要加工具可以增加一个独立的类，甚至我还可做插件挂载，这就非常灵活了。

#### 工具注册中心

`// tools/index.js   const toolModules = [filesystem, shell, plan, utils, lint];      // 自动收集所有工具   const toolRegistry = {};   for (const module of toolModules) {     for (const [name, tool] of Object.entries(module)) {       if (tool?.schema && tool?.execute) {         toolRegistry[tool.schema.function.name] = tool;       }     }   }`

看到没，这样搞的**好处**是：新增工具只需在对应模块里 export，注册中心自动发现。

#### editFile：搜索替换

这是最关键的改进之一，因为要做代码工程迭代开发，这个是必不可少的，我查看了 cursor，Claude Code 的实现，他们都是使用内容块替换的方式，因此我也直接这么实现，没必要搞什么 git diff，这个玩意 AI 输出的不好直接就替换merger 失败，然后整个文件覆盖也不可取，token 消化太大，综合考虑，内容块替换这个方式真香，难怪现在所有的开发工具都几乎这么在玩。

`// 之前：整体覆盖（危险、费 token）   writeFile({ filePath: "app.js", content: "整个文件的所有内容..." })      // 现在：搜索替换（精确、安全）   editFile({     filePath: "app.js",     oldText: "const name = 'old'",     newText: "const name = 'new'"   })`

实现中的关键细节：

``// 检查是否有多处匹配   const matches = content.split(oldText).length - 1;   if (matches > 1) {   return`替换失败: 找到 ${matches} 处匹配，请提供更多上下文使其唯一。`;   }      // 找不到时给出有用的错误提示   if (!content.includes(oldText)) {   const firstLine = oldText.split("\n")[0].trim();   if (content.includes(firstLine)) {       return`找到了相似内容，但不完全匹配。请检查空格、缩进。`;     }   }``

#### lintFile：语法检查

让 Agent 能检查自己写的代码，这个考虑是因为如果拿这个 agent 做项目开发，玩意 AI 输出的代码有语法错误呢，是不是写完之后，整个 lint 检查下，看看有没有语法错误，反正我们是支持 ReAct 模式的，有了语法错误，AI 又会自动修复。

``// 根据文件类型选择检查方式   switch (ext) {   case".js":       return`node --check "${filePath}"`;  // JavaScript   case".ts":       return`npx tsc --noEmit "${filePath}"`;  // TypeScript   case".py":       return`python3 -m py_compile "${filePath}"`;  // Python   case".json":       return`node -e "JSON.parse(require('fs').readFileSync('${filePath}'))"`;   }``

这形成了一个闭环：**写代码 → 检查 → 发现错误 → 修复 → 再检查**。

不过，到了这个地方，我发现上下文可能是个问题，因此，我考虑做一个更加健壮点的上下文管理。

### 二、因此，我设计（偷学）了分层记忆系统，哈哈哈

这是这次最大的架构升级，是的，港真，如果不考 Cursor，Claude Code 他们实现，我也不会相处这种分层记忆模型，他真的很简单，而且很有效。

其实我们现在的问题是，之前的上下文管理很简单：把所有消息都发给 LLM。

`getMessages() {     return this.messages;  // 全部发送   }`

这会造成的问题是：

1.  1\. 对话越来越长，token 越来越贵
    
2.  2\. 超过上下文限制会报错
    
3.  3\. AI 对超长上下文中间部分的"注意力"会下降
    

#### 解决的方式，我就直接抄了，使用三层记忆

![](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XI4cbWNAvtbJ5DtFJQcIbvGiaibwXX6MpxicNkvNawUf0LkDDYWQcjPJFFQ/640?wx_fmt=png&from=appmsg "null")

  

#### AGENT.md：项目级记忆

`# AGENT.md - 项目上下文      ## 技术栈   - Node.js (ESM 模块)   - DeepSeek API (LLM)      ## 编码规范   - 使用 ES6+ 语法   - 注释使用中文`

当然，如果不是代码工程项目，又是另外一种组织方式，以上只是举例说明。这个玩意其实就是 Claude code 那个 CLAUDE.md 文件。哈哈，完美复刻。

这样做的**好处**是：

1.  1\. 每次对话自动加载，AI 始终了解项目背景
    
2.  2\. 用户可以手动编辑，添加偏好
    
3.  3\. 可以 git 提交，团队共享
    

#### 会话摘要，我使用增量压缩

关键问题：如果一次性压缩整个历史，历史本身可能就超出上下文限制。

我的**解决**方式就是：增量摘要。

``// 配置   constCONFIG = {   SUMMARIZE_THRESHOLD: 10,  // 超过 10 轮触发摘要   KEEP_RECENT_TURNS: 5,     // 保留最近 5 轮完整消息   };      // 增量摘要流程   asynccheckAndSummarize() {   // 1. 判断是否需要摘要   if (userMessageCount <= SUMMARIZE_THRESHOLD) return;      // 2. 只摘要 [summarizedUpTo, startIndex] 范围的新消息   const messagesToSummarize = messages.slice(this.summarizedUpTo, startIndex);      // 3. 生成摘要   const newSummary = awaitthis.memory.generateSummary(messagesToSummarize);      // 4. 合并到已有摘要   this.summary = this.summary ? `${this.summary}\n\n${newSummary}` : newSummary;      // 5. 更新 checkpoint   this.summarizedUpTo = startIndex;   }``

#### 构建最终上下文，做了这么多，终于要组装发送给llm了。

``buildContextMessages({ systemPrompt, summary, recentMessages }) {   const messages = [];      // 1. 系统提示词 + AGENT.md（长期记忆）   let fullSystemPrompt = systemPrompt;   if (agentMd) {       fullSystemPrompt = `<project_context>\n${agentMd}\n</project_context>\n\n${systemPrompt}`;     }     messages.push({ role: "system", content: fullSystemPrompt });      // 2. 会话摘要（中期记忆）   if (summary) {       messages.push({         role: "system",         content: `<conversation_summary>\n${summary}\n</conversation_summary>`,       });     }      // 3. 最近的消息（短期记忆）     messages.push(...recentMessages);      return messages;   }``

### 我想添加一个 UI ，看 Cli 挺眼花了，但是这次也要开始新一轮的架构演进：CLI 与 Web UI 共享核心

最初所有代码都在 `index.js` 里，想加个 Web UI 就得复制粘贴大量逻辑。

#### 所以，我们的解决方式就是抽离核心

`agent/   ├── core/   │   └── agent.js      # Agent 核心逻辑   ├── index.js          # CLI 入口   └── server.js         # Web 服务入口`

`core/agent.js` 暴露事件接口：

`class AgentextendsEventEmitter {   asyncchat(userMessage) {       this.emit('assistant_start');              forawait (const chunk of stream) {         this.emit('assistant_chunk', { content: chunk });       }              if (toolCalls.length > 0) {         this.emit('tool_call', { name, args, id });         const result = awaitexecuteTool(name, args);         this.emit('tool_result', { id, result });       }              this.emit('assistant_end');     }   }`

CLI 和 Web Server 只需监听这些事件：

`// CLI   agent.on('assistant_chunk', ({ content }) => {     process.stdout.write(content);   });      // Web Server (WebSocket)   agent.on('assistant_chunk', ({ content }) => {     ws.send(JSON.stringify({ type: 'assistant_chunk', payload: { content } }));   });`

### 抽离完，添加Web UI那还不是小菜一碟

其实原理就是利用 websocket ，建立起后端那个转起来的agent 进程 和 webUI 的，实现消息双向传送就好了。

#### 因此，从命令行到浏览器，我们计划不需要做逻辑，就是做组装拼接：

`web/   ├── src/   │   ├── App.jsx   │   ├── components/   │   │   ├── ChatPanel.jsx   # 对话区域   │   │   ├── MessageItem.jsx # 消息气泡   │   │   └── Sidebar.jsx     # 侧边栏（会话列表、工具列表）   │   └── hooks/   │       └── useWebSocket.js # WebSocket 封装   ├── vite.config.js   └── tailwind.config.js`

#### 实时通信是这么玩的

`// useWebSocket.js   const { sendMessage, lastMessage, connectionStatus } = useWebSocket('ws://localhost:3001/ws');      // 处理流式消息   case 'assistant_chunk':     setMessages(prev => {       const newMessages = [...prev];       const lastMsg = newMessages[newMessages.length - 1];       if (lastMsg?.role === 'assistant') {         lastMsg.content += payload.content;  // 逐字追加       }       return newMessages;     });`

#### 效果

*   • 实时流式输出（打字机效果）
    
*   • 工具调用可视化
    
*   • 会话列表管理
    
*   • 计划进度展示
    

![我实现的一个界面](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XIHh9j8bqCQRf00s9zPp06SmUwU0gGCiciauaG70GskGvoJqm1iaTyWLaNQ/640?wx_fmt=png&from=appmsg "null")

我实现的一个界面

可以看到，我们的界面已经透题了，我接入了 mcp，而且展示我们拥有哪些 mcp 能力，友们加载了多少工具，写文章的时候，发现缺少了点，貌似我么可以会话放出来，点击就可以加载切换，然后，上下文已经是多大的 token 了，要不要主动触发压缩的呀，都可以搞，不是吗？

### MCP 协议接还是不接？开放的工具生态肯定是要的！

MCP（Model Context Protocol）是 Anthropic 提出的标准协议，让 Agent 可以接入外部工具服务器。

#### 配置

`// ~/.agent/mcp.json   {   "servers":{       "filesystem":{         "command":"npx",         "args":["-y","@anthropic/mcp-server-filesystem","/path/to/dir"]       }   }   }`

#### 实现

`// mcp-client.js   classMCPServerextendsEventEmitter {   asyncconnect() {       // 启动子进程       this.process = spawn(command, args, { stdio: ["pipe", "pipe", "pipe"] });              // JSON-RPC 通信       awaitthis.sendRequest("initialize", { capabilities: {} });              // 获取工具列表       const { tools } = awaitthis.sendRequest("tools/list");       this.tools = tools;     }      asynccallTool(name, arguments) {       returnawaitthis.sendRequest("tools/call", { name, arguments });     }   }`

#### 好处

1.  1\. 不用自己实现所有工具，可以复用社区的 MCP 服务器
    
2.  2\. 工具可以用任何语言实现
    
3.  3\. 安全隔离，工具运行在独立进程
    

所以，感觉 MCP 其实就是一些列的工具，本质就是 tool。

### 现如今，2500我学到了什么

#### 1\. 分层是解决复杂性的关键

无论是工具系统、记忆系统还是架构，**分层**都是最有效的武器。

#### 2\. 增量优于全量

不管是摘要还是编辑，**增量处理**比全量处理更安全、更高效。

#### 3\. 协议比实现重要

有了 MCP 协议，我的 Agent 可以接入整个工具生态，而不是从零开始实现每个功能。

#### 4\. 抽象要恰到好处

过早抽象是万恶之源。我是在 CLI 跑通之后，才抽离核心逻辑来支持 Web UI 的。

#### 下一步，当然，可能也不继续迭代了，因为要谈用，我为啥不只直接用 Claude Code，这些其实更好用，也更完善

2500 行代码，从命令行到 Web UI，从单文件到分层架构。其实核心逻辑就是 1000 行而已。

不用框架，理解每一行，这是我这两天总共花 4 个小时的收获。

想要源码？我觉得没多大必要吧，自己从 0 实现，或许才会有点乐趣，拿到源码也就那样，况且 Claude Code 开源的版本肯定比我的要实现得更完整，更加健壮，我想我这个个唯一的优势就是，我顺着我自己的想法去实现，他更好理解而已。好吧，如果你实在要，加我微信试试？

ps，这两天我一直在用 DeepSeek 做我这个agent 的测试，我生成了 4 个 Coding 工程，写了几部小说，讲真，这个价格真的太良心了。

![](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAekVox4HReiaRK3JYlUiaNw5XI4ODzh7ic9MuBu3edH7rK9zISKgrfyw8YvvnZI9elTafZgFTjYficBBJA/640?wx_fmt=png&from=appmsg "null")