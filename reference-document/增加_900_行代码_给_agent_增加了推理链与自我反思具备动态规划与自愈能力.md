![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFLuWmtliaTcm7pdiavcBDoSjfhyajS9cvNj3ju30ZlrMG2vUXEjdAcW3g/0?wx_fmt=jpeg)

增加 900 行代码，给 agent 增加了推理链与自我反思具备动态规划与自愈能力
=========================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

在之前的文章中，[我们实现了一个简单的 agent](https://mp.weixin.qq.com/s?__biz=MzkxNzY0OTA4Mg==&mid=2247492308&idx=1&sn=14c8c143df9c35c115fe5b42c468daff&scene=21#wechat_redirect)，基本上遵循了当前主流的 agent 的实现方式，为了代码极简。

即便是极简，我们也做了很多 agent的标配：

*   • 工具调用
    
*   • 危险操作确认
    
*   • mcp 接入
    
*   • skill 接入
    
*   • plan -> action
    

![即便是极简，我们也做了很多 agent的标配](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFfGoTZwJDwnIrx6WDjxerO3G30UkzJuY1bicCIktwSorOYtezqKFVVOw/640?wx_fmt=png&from=appmsg "null")

即便是极简，我们也做了很多 agent的标配

不过，在实现的过程中，我们做了非常多的取舍。比如一些边界条件并没有考虑，但是即便是这样，我们发现当前的 agent，其实还是存在很大的问题的。

有这样一个情况，当 Agent 不只「答一句就跑」，而是要做多步任务、会犯错、还要能从失败里恢复时，我们需要两件事：**把「怎么想的」记下来并事后复盘**，以及**把「要做什么」写成可执行、可回滚的计划**。因此本文记录我们为什么需要这两块能力，以及具体怎么设计和实现的。

![增加了反思的能力](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYF13qkZ4DqficflW5iaFDYVRpiaE8JjFrgveog6mKLF1Gb2N2qnpmZt9WLQ/640?wx_fmt=png&from=appmsg "null")

增加了反思的能力

### 首先，我们为什么需要「推理链」？

最开始我们的 Agent 就是一个「用户问 → LLM 答 → 有工具就调 → 再答」的循环。能跑，但有两个问题越来越明显：

**问题 1：黑盒决策。**  
用户问「你为什么先读 A 再改 B？」我们答不上来。模型内部当然有推理，但没被结构化记录，事后既没法解释，也没法复用。

**问题 2：难以在「任务结束后」做统一复盘。**  
我们想加「任务完成后自动总结一下：成功了啥、失败了啥、下次怎么改进」，但如果没有「这一轮里 Agent 到底想了啥、做了啥」的结构化数据，复盘就只能对着零散的对话历史硬猜，质量不稳定。

所以我们得出一个结论：**要把「思考」当成一等公民，用固定结构记下来，而不是只留在模型的隐式上下文里。** 这就是「推理链」要解决的问题：**可记录、可回溯、可被反思使用。**

### 我们这个 agent 中，关于推理链的设计思路

我们不想搞成学术版「思维链」论文复刻，而是希望：

*   • 和现有工具自然结合（尤其是 `think`）；
    
*   • 类型少而清晰，方便 LLM 填、也方便后面反思/摘要用。
    

于是定了五种类型，对应「从观察到决策再到反思」的一条链：

类型

含义

典型用法

observation

从环境/工具结果里看到的信息

读文件后：「文件里当前是 X」

analysis

对观察的解读、分析

「X 说明缺少 Y 配置」

hypothesis

基于分析的假设、推测

「很可能是 Y 没装导致报错」

decision

实际做出的行动决策

「先执行 Y，再检查 Z」

reflection

对决策或结果的反思

「上一步用方案 A 比 B 更稳」

我是这么考虑的

![从观察到决策再到反思](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFFP2mLTD9Qhe5AINiajicXHqwFsUNFpoREqTxUbRCbkdLqt00XvSfA4ng/640?wx_fmt=png&from=appmsg "null")

从观察到决策再到反思

这样设计有几个考虑：

1.  1. **和 `think` 工具一一对应**：LLM 在需要「显式推理」时调用 `think`，传入 `type` + `thought`，我们只做记录和轻量结构化，不改变原有对话流。
    
2.  2. **置信度（confidence）和证据（evidence）**：为「反思」和「复盘」留接口——后面反思时可以看「当时信心高不高、依据是什么」。
    
3.  3. **依赖关系（dependencies）**：当前实现里，新步骤会自动挂到「最近的前置类型步骤」上，这样整条链在逻辑上是连贯的，将来若要画图或剪枝也有依据。
    

所以：**推理链 = 在现有 Agent 循环里，给「思考」一个统一的结构和存储，为「事后反思」和「可解释性」打基础。**

![](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFibdBY6swqMX6eF2rgxs0as3VCNmUeib1ZtcjicDKTzKicbqcBFbIoUibricg/640?wx_fmt=png&from=appmsg "null")

  

这样，**推理链的生命周期和「单次任务」绑定，写进去的就是「这一轮」的思考过程。**

### 有没有想过，agent为什么需要自我反思？

有推理链之后，我们就能在「任务结束」时做一件事：**不要只输出最后一句回复就结束，而是用 LLM 再跑一步，对「目标 + 推理链 + 执行结果」做一次结构化复盘。** 这就是「自我反思」要解决的问题。但是为啥要做这个呢？到底有啥价值

我想的到的具体的价值是：

1.  1. **经验沉淀**：每次任务产出一份「教训 / 改进 / 关键决策 / 模式」，存下来，以后类似任务可以检索到。
    
2.  2. **长期记忆**：把反思写进 `AGENT.md` 或类似长期记忆，Agent 在后续会话里能「记得以前踩过的坑」。
    
3.  3. **可解释性与调试**：人可以看到「系统认为这次成功/失败的原因是什么、下次建议怎么做」。
    

![根据plan 去执行](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFCgUObrUV6YZfwvZCMBQKDw4JWQAeedrymaNUJEJXhsjqSZIEo7CO9A/640?wx_fmt=png&from=appmsg "null")

根据plan 去执行

所以：**反思 = 在「任务结束」这个时间点上，用推理链 + 执行结果，生成一份结构化的「复盘报告」，并持久化、可检索。**

**为什么是「任务结束后」才反思？**  
因为只有这时我们才有完整的「目标 + 推理过程 + 实际执行结果」，复盘才有依据；若在每一步都反思，成本高且容易重复。**为什么存成 JSON + 长期记忆？**  
因为我们要的不只是一次性总结，而是「以后类似任务能查到这些经验」；当前用关键词检索，就是为了简单可落地，后续可以换成向量检索。

![执行完成会反思，当中有错误也会反思，修改计划](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenMDPG9DGcTfanBbAXF2RYFoEIoIRHUXtXQUON4kIxIouDqicz0OZcjw2noYgyL7mAAuy9863CG3Jg/640?wx_fmt=png&from=appmsg "null")

执行完成会反思，当中有错误也会反思，修改计划

### 为什么需要「动态规划与自愈」？

当任务变成「多步、可能失败、需要重试或换方案」时，我们会发现：

*   • **纯「一步步跟着 LLM 走」**：没有显式「计划」，失败后只能重新来或靠模型临时改主意，难以「从某一步之前重来」。
    
*   • **若有一个「计划」**：步骤、分支、备选方案都显式存在，就可以在某一格失败时「换备选」或「回滚到上一个检查点再试」，这就是「自愈」的一种形式。
    

所以我们希望：**计划是「结构化的、可执行的」，并且和「检查点 + 回滚」绑在一起，形成「动态规划 + 自愈」。**

### 动态规划的设计思路

我们需要的不仅仅是「给人类看的 to-do 列表」，而是**机器可执行、可分支、可回滚**的计划，于是做了这些选择：

1.  1. **计划 = 树形结构（PlanNode）**：每个节点可以是普通步骤（STEP）、条件分支（CONDITION）、备选（FALLBACK），还可以标记「是否检查点」。这样既能表达「先 A 再 B」，也能表达「若 X 则 A 否则 B」「A 失败则做 B」。
    
2.  2. **由 LLM 生成计划**：用自然语言描述目标，让 LLM 输出 JSON（steps 里带 id、description、action、condition、then/else、fallback、checkpoint），我们再转成 `PlanNode` 树。这样「计划长什么样」仍然可读、可调，但执行语义是确定的。
    
3.  3. **执行与适应**：执行某一步后，根据结果（成功/失败）更新节点状态；若节点有 `fallback` 且当前失败，则标记失败并「激活」备选，后续执行时走备选分支。这就是「动态」：不改计划结构，但根据执行结果决定下一步走哪条分支。
    
4.  4. **检查点与回滚**：在「关键步骤」或每隔 N 步自动/手动打检查点（保存当前消息列表 + 计划状态）；失败或用户要求时，可以回滚到某个检查点，恢复消息历史和计划状态，再继续或换策略。这就是「自愈」：不从头再来，而是回到上一个「已知好」的状态。
    

所以：**动态规划 = 用「计划树 + 执行结果」驱动下一步；自愈 = 用「检查点 + 回滚」在失败时回到安全点。**

### 最后来串一下整体数据流

1.  1. **用户发话** → Agent 若开启反思，先查 `getRelevantExperience(userMessage)`，把相关历史反思注入上下文（或仅作事件），再进入执行循环。
    
2.  2. **执行过程中** → LLM 可调用 `think`，推理链追加步骤；若有动态计划，则按计划树执行，关键步骤或每 N 步打检查点；某步失败时可走 fallback 或调用 `rollbackToCheckpoint`。
    
3.  3. **任务结束时** → 若有推理链且启用反思，则调用 `reflect(任务描述, reasoningChain, 执行结果)`，得到 `ReflectionResult`，写入 `reflections.json` 并可写入长期记忆；推理链在本轮内可导出/摘要，供反思 prompt 使用。
    
4.  4. **下次类似任务** → 通过 `getRelevantExperience` 拉取相关反思，形成「上次怎么做的、踩了什么坑」的上下文，再配合推理链和动态计划，实现「有记忆、可规划、可回滚」的 Agent。
    

最后总结下，我们这次变更做了些什么？

*   • **推理链**：把「思考」结构化记录（observation → analysis → hypothesis → decision → reflection），和 `think` 工具、单次任务生命周期绑定，为可解释性和反思提供输入。
    
*   • **自我反思**：在任务结束时用「推理链 + 执行结果」生成结构化复盘，持久化并支持检索，用于经验沉淀和长期记忆。
    
*   • **动态规划**：用「计划树（步骤/条件/备选）+ LLM 生成 + 执行时适应」表达多步与分支；用检查点保存消息与计划状态，用回滚恢复，实现失败后的自愈。
    

我这样写出来的目的，是让你能看到：**我们为什么需要这两块（推理+反思、规划+自愈）、每块在设计时在纠结什么、以及最终在代码里是怎么落地的。**