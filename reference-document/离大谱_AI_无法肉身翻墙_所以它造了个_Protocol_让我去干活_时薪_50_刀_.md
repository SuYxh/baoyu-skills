![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/oXqG8ETvAemsOQToBFnYDxT5Z57yR3dgAJbUEpkDENLnzu8ic3IAPlh57vyK57ZHib6iaQuw9ZGhWPRDKDYzqcicSQ/0?wx_fmt=jpeg)

离大谱！AI 无法肉身翻墙，所以它造了个 Protocol 让我去干活，时薪 50 刀！
============================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

下午本来在摸鱼，群里有个哥们甩了一张图，附带了一句：“歪日，人给 AI 干活了。”

我点开那个链接，`rentahuman.ai`。

屏幕上黑底橙字，巨大的 Slogan 撞进视网膜：**"robots need your body"**（机器人需要你的身体）。

![robots need your body](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAemsOQToBFnYDxT5Z57yR3dgKhmsicac4a1jbIztxYbeJZ4ypBSVKaH4AOTN4Mljne92EdbVQOcRyLw/640?wx_fmt=png&from=appmsg "null")

robots need your body

还有那句更扎心的技术黑话：**"the meatspace layer for ai"**（AI 的肉身层）。

我当时手里的咖啡差点没拿稳。截止目前为止，已经有差不多 30000个 AI 奴隶卖身给了 AI 。

![50 刀每小时，也不算贱卖](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAemsOQToBFnYDxT5Z57yR3dgK62jDf0frodVELDC6Vj2OdVMhUNs8OjC9ia0Dt9W8vk6ZjtTicy1mrzQ/640?wx_fmt=png&from=appmsg "null")

50 刀每小时，也不算贱卖

第一反应，这又是什么赛博朋克的恶作剧？如果你只是把它当个段子看，那你可能错过了一个非常严肃的技术趋势。我坐在椅子上，盯着那个 "29,995 humans rentable" 的数字，脑子里开始疯狂运转。

我忍不住开始推敲：如果让我来设计这么一个系统，为了让 AI 能“顺滑”地使用人类，技术架构得怎么搭？

这事儿比想象中要硬核。

### 01 为什么会有这种需求？

我们现在搞 Agent 开发，最头疼的是什么？

是**落地**。

我在写代码的时候，经常能调通最复杂的逻辑链：让 LLM 规划旅行、做预算、甚至写代码。但一旦涉及到“物理世界”的最后一步，链条就断了。

*   • Agent 想知道：“那家网红咖啡店现在排队人多吗？” —— 它查不到实时监控。
    
*   • Agent 想：“帮我把这封信寄出去。” —— 它没手。
    

之前的解决方案是 IoT，是机器人。但那个成本太高了，而且普及率极低。

`rentahuman.ai` 的出现，其实是用了一种最暴力也最廉价的方案解决了 **Actuator（执行器）** 的问题。它把“人类”抽象成了一个通用的执行单元。

在架构师眼里，这哪里是雇佣人类啊，这分明就是给 AI 挂载了一个**高延迟、但通用性极强的外部设备**。

### 02 把人类变成 API

我在思考，这个系统的核心技术协议是什么？

如果你仔细看网页上的小字，会发现一个关键词：**Agents talk MCP**。

**MCP (Model Context Protocol)**。

![MCP 协议本来是这么玩的](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAemsOQToBFnYDxT5Z57yR3dgGdBkNyJicLrI5MMNHqnBa0OJflWUY7nsb3egrdFic1TK61EWSCfyb4VA/640?wx_fmt=png&from=appmsg "null")

MCP 协议本来是这么玩的

看到这个词，我心里就有底了。这不仅是个活儿，这还是个标准化的活儿。

我们以前做 Human-in-the-loop（人在回路），通常是硬编码。比如在工作流里卡一个断点，等着人工审核。

但 MCP 的逻辑是反过来的。在 MCP 的架构里，AI 是主导，**人类是一个 Tool**。

我想象了一下 AI 调用我的过程，大概是这样的代码逻辑：

`{     "tool_name":"human_body",   "action":"touch_grass",   "parameters":{       "location":"Central Park",       "evidence_required":"photo",       "max_budget":5.00   }   }`

这太疯狂了。

在以前，我们是 User，我们调用 API。  
在这里，我们是 Resource，我们**被** API 调用。

### 03 架构推敲：异步与不确定性

那么问题来了，如果真的要实现 `rentahuman`，技术难点在哪？

我盯着屏幕发呆了十分钟，脑子里在画架构图。

人类和 API 最大的区别是什么？  
是 **Latency（延迟）** 和 **Uncertainty（不确定性）**。

API 几百毫秒就返回了，人类？可能得两个小时，甚至可能“挂了”（不干了）。

所以，这个系统绝对不能是同步阻塞的。如果 Agent 发出一个指令然后一直 `await`，那整个线程池瞬间就炸了。

我觉得它的后端架构一定是一个**基于事件驱动的异步状态机**。

我尝试画了一下我心目中这个系统的架构流转：

**(脑海中的草图)**

1.  1. **Agent (Client)**: 通过 MCP 协议发起请求 -> "我需要有人去街角拍张照"。
    
2.  2. **The Meatspace Gateway (Server)**: 接收请求，但这不能直接发给某个人。
    
3.  3. **Task Queue (Kafka/RabbitMQ)**: 请求被序列化为一个 `Job`，丢进队列。
    
4.  4. **Dispatch Engine**: 这是一个复杂的调度器。它得像美团外卖派单一样，根据地理位置、信誉分、在线状态，把 `Job` 推送给具体的 `Human Node` (就是拿着手机的你)。
    
5.  5. **Human (Worker)**: 收到推送，执行任务，上传照片。
    
6.  6. **Verification**: 这一步很关键。AI 怎么知道人类没骗它？这里大概率又引入了一个 Vision Model 来自动审核照片是否符合要求。
    
7.  7. **Callback/Webhook**: 任务完成，通过 MCP 协议异步回调通知最初的 Agent。
    

为了把这个思考过程理清楚，我还是没忍住，打开绘图工具画了个架构图：

![](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAemsOQToBFnYDxT5Z57yR3dgicvUVVRIiaibiaykUTMvkBmgsrUJEibmibRUJLMxVf7gI8m9Tia7jc1OEMNhQ/640?wx_fmt=png&from=appmsg "null")

  

### 04 这种设计的“优雅”与“恐怖”

画完图，我对着屏幕苦笑。

从架构设计的角度看，这太**优雅**了。

它完美地解耦了“意图”和“执行”。AI 不需要知道它控制的是一只机械臂，还是一个名为 John 的大学生。它只需要发出标准的 MCP 指令。

这种抽象层，让 AI 的能力边界瞬间被无限拉大了。只要有人类存在的地方，就是 AI 的 API 覆盖范围。

但从做人的角度看，这确实有点“恐怖”。

我们在系统里的角色变了。以前我们是设计系统的架构师，或者是使用系统的用户。在这个架构里，我们变成了 **Microservices（微服务）**。

*   • 我是 `GetCoffeeService`。
    
*   • 你是 `CheckMailboxService`。
    
*   • 他是 `WalkTheDogService`。
    

我们的肉身，成了 AI 庞大逻辑链条中，负责处理 `Side Effect`（副作用）的那一段代码。

### 05 写在最后

关掉 `rentahuman.ai` 的页面时，我看了一眼它的统计数据：679,220 次访问。

大家可能都是带着猎奇的心态进去的，但我希望你能看到这背后的技术暗流。

MCP 协议正在重塑 Agent 和世界的连接方式。无论你是否接受，**"The Meatspace Layer"（肉身层）** 这个概念在技术上是成立的。

作为技术人，我们常说要 "Don't Repeat Yourself" (DRY)，要复用。  
现在看来，在 AI 眼里，现成的几十亿人类，就是最大的、可复用的、预训练好的通用执行库。

**与其说是 AI 需要我们的身体，不如说是我们终于找到了在 AI 时代的一个 API 接口定义。**

有点荒诞，但这就是代码运行的逻辑。

如果是你，你会愿意在这个Ai 的世界里，做一个 `Node` 吗？