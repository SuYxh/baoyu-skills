![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/sc9vl5waw2ocAt4FdpcO7icB2Ygxibl5Kj1gQgfXKrcWPBsArxmTvY6Lywnj67hQfrCo5bBYysAdNiaJWRLZHkAUcjge0CA5xsTgmPsZicys1B0/0?wx_fmt=jpeg)

让 AI 直接画图？这个 Excalidraw MCP 把我的工作流彻底改了
======================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

#### 一个真实的困扰

上周五下午，我又在画系统架构图。

你知道那种感觉吗？脑子里已经有了完整的设计思路，想的是数据怎么流转、服务怎么调用、消息怎么传递，但手上却在干什么呢？在调矩形框的位置，在拖箭头让它对齐，在纠结用什么颜色显得专业一点。

技术人的痛苦往往不在思考本身，而在把思考转化成可视化表达这个环节。我一直在想，能不能有一种方式，让我用说的，AI 就能把图画出来？

直到我看到了 Excalidraw MCP。 github\[1\]

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2qoCIictmTErF0fbe6yJpkWu9IU5YHkGicPZKdOBqFXmj0G9PMztZSnMWQ8HL2GmAlsUw680ajot9RkDHhEfAbCufZNwzGmQjg8Y/640?wx_fmt=png&from=appmsg "null")

  

我盯着这个 MCP 服务器看了三个小时，终于明白为什么画图可以这么简单

### 首先什么是 MCP？先从这个协议说起，我估计还有很多人是不明白原理的

我得承认，第一次看到"Model Context Protocol"这个词的时候，我脑子里是懵的。

MCP，翻译过来叫"模型上下文协议"。Anthropic 在 2025 年把它作为开源协议发布出来，目的很简单：让 LLM（大语言模型）能够标准化地连接外部数据源和工具。

你可以把它理解成一个"万能遥控器"。以前每个 AI 想调用一个外部工具，都得专门写一套集成代码，这个工具对接 A 模型要写一遍，对接 B 模型又要重写一遍。MCP 出现后，只要工具提供了 MCP Server，任何支持 MCP 的 AI 客户端都能直接调用。

它的架构其实不复杂：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/sc9vl5waw2rO5TVOnK9WaChdGb9MV3sjjWjm30icVgWmeR13HjjgstlG6AKuOuHSSGN2zd98sxrxYR6y5YSxPOTb70aiaibMFovy6pP8nRsMQ0/640?wx_fmt=png&from=appmsg "null")

  

**宿主应用（Host）**：比如 Claude Desktop、Cursor IDE，这些是用户直接交互的界面。

**MCP 客户端（Client）**：内嵌在宿主应用里，负责和 MCP 服务器通信。

**MCP 服务器（Server）**：提供具体功能的服务，比如查询数据库、读取文件，或者——画图。

**传输层**：用 STDIO（本地）或 HTTP+SSE（远程）进行通信，底层都是 JSON-RPC 2.0 协议。

为什么要先说这个协议？因为理解了 MCP，你才能明白 Excalidraw MCP 到底在解决什么问题。

### Excalidraw MCP 的设计思路

Excalidraw 本身是一个开源的手绘风格白板工具。它的特点是轻量、实时协作、手绘风格，很多人喜欢用它画草图和架构图。

但 Excalidraw MCP 做的事情更进一步。它把 Excalidraw 封装成了一个 MCP 服务器，让 AI 可以通过 API 直接操作画布上的元素。

这意味着什么？

你可以对 Claude 说："帮我画一个三层架构，前端、后端、数据库，用箭头连起来。"然后，图就出来了。

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2qdphnIDQBsI9ib2Q4NYfxm8EpE7edUpsw5qEkiaERibym79dvoq9LlfYPj4QJ914GeEmP4VVA3zVndGVGHYDfibV9JAwsgp74pqMw/640?wx_fmt=png&from=appmsg "null")

  

不是生成一张静态图片，而是实时在 Excalidraw 画布上创建元素、调整位置、建立连接。你还可以继续说："把数据库换成 Redis，再加一个消息队列。"它会实时更新。  
我第一次看到这个设计的时候，停下来想了很久。

为什么这个方案比直接让 AI 生成图片好？

**可编辑性**。生成的图是 Excalidraw 格式的，你可以随时手动调整。

**实时同步**。通过 WebSocket 实现了多端同步，你在浏览器里打开画布，AI 的修改会实时显示。

**批量操作**。可以一次创建多个元素，支持分组、对齐、锁定等高级操作。

**双向交互**。不只是生成，还可以查询现有元素、过滤特定属性的图形。

这不是一个"AI 画图工具"，而是一个"AI 操作画布的接口"。

### 它是怎么工作的？

我花了一个晚上把代码看了一遍，把整个数据流程梳理清楚。

#### 架构分层

Excalidraw MCP 分成三层：

1.  1. **前端画布层**：React + Excalidraw 官方包，跑在浏览器里，地址是 `localhost:3000`（默认）。
    
2.  2. **后端服务层**：TypeScript + Express.js，提供 REST API 和 WebSocket 接口。
    
3.  3. **MCP 协议层**：实现 MCP 标准，让 Claude 等 AI 客户端可以调用。
    

#### 数据流转过程

当你在 Claude 里说"画一个矩形"，会发生什么？

**Step 1：自然语言解析**  
Claude 识别出你的意图，决定调用 Excalidraw MCP 的 `create_element` 工具。

**Step 2：构造 MCP 请求**  
Claude 把你的需求转换成 JSON 格式的 MCP 请求：

`{     "type":"rectangle",   "x":100,   "y":100,   "width":200,   "height":100,   "backgroundColor":"#ffffff",   "strokeColor":"#000000"   }`

**Step 3：MCP Server 处理**  
后端收到请求，调用 Excalidraw 的 API 创建元素，生成唯一的 `elementId`。

**Step 4：WebSocket 广播**  
元素创建成功后，通过 WebSocket 把更新推送给所有连接的客户端。

**Step 5：画布渲染**  
浏览器端的 Excalidraw 收到 WebSocket 消息，实时渲染新元素。

整个过程是毫秒级的。

#### 为什么选择这种架构？

我在想，为什么不直接让 AI 生成一个 `.excalidraw` 文件，然后手动导入？

答案在于"实时协作"这个需求。

如果只是生成文件，每次修改都要重新导入，根本做不到流畅的对话式编辑。而 MCP + WebSocket 的方案，可以让你和 AI 一起"盯着同一块画布"工作。

这种设计还带来另一个好处：**可观测性**。你能看到 AI 在画什么，如果不对可以立刻打断。

### 实战：怎么把它跑起来？其实最简单的就是在 Claude.ai 中配置下

![Settings → Connectors → Add custom connector](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2pB5IFDbr4bQyH1urhf5j1BgsEdPYMbLllARHmbiaFv6BmAiczzmnbicEQFFv9GoBiciaibCYjpfUIBGmb2AVYUnvibyWAkoeRShLGB3g/640?wx_fmt=png&from=appmsg "null")

Settings → Connectors → Add custom connector

### 我觉得可以关住下他的API 设计的思考

我特别关注了它提供的 API。

#### 核心操作

**元素创建**：

*   • `create_element`：创建单个元素（矩形、椭圆、菱形、箭头、文本、线条）
    
*   • `create_elements`：批量创建
    

**元素管理**：

*   • `get_elements`：查询元素，支持过滤条件
    
*   • `update_element`：更新元素属性
    
*   • `delete_element`：删除元素
    

**高级操作**：

*   • `group_elements`：元素分组
    
*   • `align_elements`：对齐（左对齐、居中、分布等）
    
*   • `lock_element`：锁定防止误操作
    

### 他们为什么这样设计？

我在想，为什么要提供这么细粒度的 API？

如果只是"画个图"，一个 `create_diagram` 接口不就够了吗？

但仔细想想，细粒度的好处在于**组合能力**。

比如你想画一个系统架构图：

1.  1\. 先创建所有服务模块（批量创建矩形）
    
2.  2\. 添加文本标签（批量创建文本）
    
3.  3\. 用箭头连接服务（创建箭头，指定起点终点）
    
4.  4\. 对齐所有模块（调用对齐接口）
    
5.  5\. 把相同层级的服务分组（调用分组接口）
    

每一步都是独立的 API 调用，AI 可以根据上下文灵活组合。

这种设计还有个好处：**可调试**。如果生成的图不对，你能清楚知道是哪一步出了问题。

### 我觉得他的一些局限性

没有完美的工具。

**布局算法**：目前 MCP Server 不提供自动布局，元素位置需要手动指定或者让 AI 计算。这意味着复杂图表的布局可能不够优雅。

![](https://mmbiz.qpic.cn/mmbiz_png/sc9vl5waw2q5WYMSvOAicJkeDX0aPoFm7IMpT3XicnqarvPpY61RHqEaAfWoJic0DykJtQRvWgRlJuTvFnWXjBO9lqYnR62HOk69iaj1k6n95iaM/640?wx_fmt=png&from=appmsg "null")

  

**样式一致性**：虽然可以指定颜色、线宽、粗糙度，但没有"主题"或"样式模板"的概念。每次都要重新指定样式参数。

**持久化**：默认是内存存储，重启服务后画布会清空。虽然可以导出 `.excalidraw` 文件，但不是自动的。

**协作限制**：虽然支持多端同步，但没有权限控制，所有连接的客户端都能修改。

这些问题不是不能解决，只是当前版本还没做。

### 它能用来做什么？

我列了几个实际场景。

**技术文档配图**：写设计文档时，直接在 Markdown 里描述图表需求，让 AI 生成，然后导出 PNG 嵌入文档。

**架构评审准备**：评审前快速画出多个架构方案对比，省去手动画图的时间。

**教学演示**：讲课时实时画图，比 PPT 更灵活，学生提问可以立刻修改图示。

**头脑风暴**：团队讨论时，一边聊一边让 AI 把想法可视化，所有人都能看到画布。

**代码生成辅助**：先画出数据流图，再让 AI 根据图生成代码骨架。

这些场景的共同点是：**需要快速把想法转化成图形，并且可能频繁修改**。

### 和其他方案的对比

市面上还有其他类似工具。

**Mermaid/PlantUML + MCP**：用 DSL（领域特定语言）描述图表，然后渲染。优点是版本控制友好（纯文本），缺点是灵活性不如 Excalidraw。

**Draw.io MCP**：和 Excalidraw MCP 类似，但 Draw.io 更偏专业绘图，元素库更丰富。Excalidraw 的手绘风格更适合草图。

**直接让 AI 生成图片**：比如 香蕉王 nano pro 画架构图。问题是生成的图不可编辑，修改需要重新生成。

我觉得选择哪个取决于你的使用场景：

*   • 需要快速草图 → Excalidraw MCP
    
*   • 需要专业图表 → Draw.io MCP
    
*   • 需要版本控制 → Mermaid/PlantUML MCP
    
*   • 需要美观展示 → AI 生成图片
    

### 一些延伸思考

用了几天后，我开始想更深的问题。

**AI 理解图形吗？**  
目前 AI 是在"操作"图形，但不是在"理解"图形。它能根据你的描述创建元素，但如果你问"这张图有什么问题"，它其实看不到最终的渲染效果。

有一些高级实现（比如 Draw.io MCP）支持"读"图。AI 可以解析现有图表结构，提出优化建议。Excalidraw MCP 目前还没有这个能力。

**为什么 MCP 比 Plugin 好？**  
以前很多工具用 Plugin 机制扩展功能。MCP 的优势在于**跨平台**。同一个 MCP Server，可以被 Claude Desktop、Cursor、VS Code（如果支持 MCP）同时使用。

**这种模式能推广到其他工具吗？**  
我觉得可以。任何有 API 的工具都能封装成 MCP Server。比如表格工具、笔记工具、项目管理工具。关键在于设计好 API 粒度，让 AI 既能灵活操作，又不会过于复杂。

### 写在最后

回到最开始的问题：为什么画图可以这么简单？

答案不是"AI 会画图了"，而是"AI 可以操作画图工具了"。

Excalidraw MCP 本质上是把 Excalidraw 的能力通过标准协议暴露给 AI。它不是魔法，而是工程设计。

这种设计思路值得学习：

*   • **标准化接口**：用 MCP 协议而不是自定义格式
    
*   • **细粒度 API**：提供组合能力而不是一体化方案
    
*   • **实时反馈**：让用户能看到 AI 的操作过程
    
*   • **可编辑性**：生成的是中间格式而不是最终产物
    

我用了三个小时理解它，又花了一个晚上把它集成到我的工作流里。

现在，我再也不用手动调矩形框的位置了。

**参考资料**：

*   • Excalidraw MCP GitHub 仓库 github\[2\]
    
*   • Model Context Protocol 官方文档 modelcontextprotocol\[3\]
    
*   • Excalidraw 官方项目 github\[4\]
    

#### 引用链接

`[1]` github: _https://github.com/yctimlin/mcp\_excalidraw_  
`[2]` github: _https://github.com/yctimlin/mcp\_excalidraw_  
`[3]` modelcontextprotocol: _https://modelcontextprotocol.io/docs/learn/architecture_  
`[4]` github: _https://github.com/excalidraw/excalidraw_