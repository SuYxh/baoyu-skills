![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/oXqG8ETvAenAlSZAwVEOYcgP9KhpeKJLPbmX5Rg7LdKrSFZ3UgkaTqBaRjApRNEiaSprScbgibSZpzevAhXicXo3A/0?wx_fmt=jpeg)

新增 500 行代码，我实现 Agent Skills 渐进式加载，原理一目了然，这掌控感极好
===============================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

#### [上一篇文章中](https://mp.weixin.qq.com/s?__biz=MzkxNzY0OTA4Mg==&mid=2247492271&idx=1&sn=031c9d7639e4e7c84df47467eac11c0f&scene=21#wechat_redirect)，我们的 Agent 已经具备了：

*   • 分层记忆（AGENT.md + 会话摘要 + 短期记忆）
    
*   • 工具系统（文件操作、Shell 命令、代码检查）
    
*   • MCP 协议支持
    

  

但还有一个问题：**Agent 不够"专业"**。

当用户说"帮我做代码审查"时，Agent 能做，但做得不够系统。它不知道我们团队的风格，应该检查哪些点，输出什么格式，遵循什么流程。

所以，我们需要一种方式，把**领域专业知识**注入给 Agent。

这就是 **Agent Skills**。看看我实现的效果，如下：

![用技能做代码审查](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenAlSZAwVEOYcgP9KhpeKJLXUiaXfQ2Ur85Tz0BWuZIDstLYgtC19juAmPZt0lB9E2GJXVcicNDNN6Q/640?wx_fmt=png&from=appmsg "null")

用技能做代码审查

从图中我们不难发现，当我们要做代码审查时，llm 会立刻意识到我们有技能可用技能可以使用，因为这个抽要信息在系统提示词中。

![Cli 上面list skills](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenAlSZAwVEOYcgP9KhpeKJL9Lh3CcAPFkLxdFaKbztyT2GTpVwvGEw1KamOv8OZdYPiaXAsMgR6VibA/640?wx_fmt=png&from=appmsg "null")

Cli 上面list skills

![WebUI上面也直接展示技能](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenAlSZAwVEOYcgP9KhpeKJLiaia00DYq1ZBsufP17ibV4wYTibIlCYJ3JQQMuILtic4FLsiaIdrCVyxibOOw/640?wx_fmt=png&from=appmsg "null")

WebUI上面也直接展示技能

### 那么，什么是 Agent Skills，可能有些人用过，但是更多的人只是用，不了解这种设计哲学

Agent Skills\[1\] 是 Anthropic 发起的开放标准，已被 Cursor、Claude Code、VS Code、GitHub Copilot 等主流工具采用。

核心理念很简单：

> **Skill = 一个文件夹 + 一个 SKILL.md**

`code-review/   └── SKILL.md    # 包含技能描述和执行指令`

Agent 发现这个文件夹后，就获得了"代码审查"这个技能。

#### Skill 的结构

`---   name: code-review   description: 审查代码质量，检查常见问题。当用户要求代码审查时使用。   ---      # 代码审查 Skill      当用户请求代码审查时，按以下流程执行：      ## 1. 理解代码范围   - 确认要审查的文件或目录   - 使用 readFile 读取关键文件      ## 2. 审查检查项   - [ ] 代码风格一致性   - [ ] 错误处理是否完善   - [ ] 是否有安全隐患   ...`

就这么简单。**Skill 本质上是给 Agent 的操作手册**。

### 为什么不直接写在系统提示词里？

答案非常简单，还是上下文，模型的上下文是有限的。

你可能会问：这些指令直接写在 System Prompt 里不就行了？

问题是：

1.  1. **上下文爆炸** — 如果有 50 个技能，每个 1000 tokens，光技能就占 5 万 tokens
    
2.  2. **干扰注意力** — 太多无关信息会降低 LLM 对关键内容的注意力
    
3.  3. **难以维护** — 所有内容混在一起，更新一个技能要改整个 prompt
    

Agent Skills 的解决方案：**渐进式加载**。但是，怎么实现渐渐式加载的，我相信很多人不知道。

### 渐进式加载的实现原理，当然我这也是一种思路罢了

在我们这个 agent 系统中，我觉得这是我们能想到并且实现的一种简单的设计：

![](https://mmbiz.qpic.cn/mmbiz_png/oXqG8ETvAenAlSZAwVEOYcgP9KhpeKJL1tmoqWxWRMNtlhrCH4exOwSibp548ShOrxvdVjtpLCWwHr2cUfiblssQ/640?wx_fmt=png&from=appmsg "null")

  

**启动时**：只加载 `name` 和 `description`，告诉 Agent "有这些技能可用"

**激活时**：用户说"帮我做代码审查"，Agent 识别出需要 `code-review` 技能，加载完整指令

**执行时**：如果 Skill 有脚本或参考文档，按需读取

这样，100 个技能只占 ~5000 tokens 的初始上下文，而不是 10 万。

### 不废话了，直接看我的实现细节

#### 1\. SkillManager 核心类

`// skills.js   exportclassSkillManager {   constructor(workingDirectory) {       this.skillsCache = newMap();   // name -> metadata       this.activeSkills = newMap();  // name -> full skill     }      // 发现所有可用的 skills（只加载 metadata）   discoverSkills() {       const skills = [];              // 扫描全局目录 ~/.agent/skills/       skills.push(...this.scanDirectory(GLOBAL_SKILLS_DIR, "global"));              // 扫描项目目录 ./.skills/       skills.push(...this.scanDirectory(LOCAL_SKILLS_DIR, "local"));              return skills;     }      // 只解析 YAML frontmatter   parseMetadata(skillMdPath) {       const content = fs.readFileSync(skillMdPath, "utf-8");       const match = content.match(/^---\n([\s\S]*?)\n---/);       // 解析 name, description 等字段       return metadata;     }      // 激活 skill（加载完整指令）   activateSkill(name) {       const skill = this.skillsCache.get(name);       const content = fs.readFileSync(skill.path + "/SKILL.md", "utf-8");       const body = content.replace(/^---\n[\s\S]*?\n---\n*/, "");  // 去掉 frontmatter              return { ...skill, instructions: body };     }   }`

#### 2\. 注入系统提示词

启动时，将可用技能列表注入到 System Prompt：

``function buildSystemPrompt() {   let prompt = BASE_SYSTEM_PROMPT;      // 添加 Skills 信息（只有 metadata）   const skillsXml = skillManager.generatePromptXML();   if (skillsXml) {       prompt += `\n\n${skillsXml}`;     }      return prompt;   }``

生成的 XML 格式：

`<available_skills>     <skill>       <name>code-review</name>       <description>审查代码质量，检查常见问题。</description>       <location>/Users/me/.agent/skills/code-review/SKILL.md</location>     </skill>     <skill>       <name>git-workflow</name>       <description>Git 工作流助手。</description>       <location>/Users/me/.agent/skills/git-workflow/SKILL.md</location>     </skill>   </available_skills>`

Agent 看到这个列表，就知道有哪些技能可用。

#### 3\. Skills 工具

提供给 Agent 使用的工具：

``// 激活 skill   exportconst activateSkill = {   schema: {       type: "function",       function: {         name: "activateSkill",         description: "激活一个 skill，将其完整指令加载到上下文中。",         parameters: {           type: "object",           properties: {             name: { type: "string", description: "skill 名称" },           },           required: ["name"],         },       },     },   execute: async ({ name }, context) => {       const skill = context.skillManager.activateSkill(name);       return`已激活 skill: ${name}\n\n${skill.instructions}`;     },   };``

当用户说"帮我做代码审查"，Agent 会调用 `activateSkill("code-review")`，然后按照返回的指令执行。所谓的激活，其实就是把更多的 skills 相关的上下文喂给模型吃。

#### 4\. 目录结构

`~/.agent/   └── skills/              # 全局 skills       ├── code-review/       │   └── SKILL.md       └── git-workflow/           └── SKILL.md      my-project/   └── .skills/             # 项目级 skills       └── deploy/           └── SKILL.md`

全局 skills 对所有项目生效，项目级 skills 只在特定项目中可用。这个设计思路几乎是所有的 agent 工具都这么玩的，Claude Code 是这样，Codex，cursor 不例外。

### 其实本质上 skills 这种渐渐加载也是一种上下文管理，我觉得和我们这个 agent 的分层记忆是互补的关系

  

分层记忆

Agent Skills

目的

管理对话历史

注入领域知识

层级

长期/中期/短期

Metadata/Instructions/Resources

加载时机

自动（按对话长度）

按需（用户任务触发）

持久化

AGENT.md + 会话摘要

SKILL.md 文件

为什么说是两者互补：

*   • 分层记忆解决"记住我们聊过什么"
    
*   • Agent Skills 解决"知道怎么做某件事"
    

### 在实现 skills 的过程中，我学到了什么

#### 1\. 渐进式加载是上下文管理的利器

无论是记忆管理还是技能加载，核心思想都是：**不要一次性加载所有内容**。

先给 LLM 一个"目录"，让它知道有什么可用，需要时再加载详情。

#### 2\. 开放标准比自己造轮子好

Agent Skills 是开放标准，意味着：

*   • 社区共享的技能可以直接用
    
*   • 我写的技能也能在其他 Agent 产品中使用
    
*   • 格式统一，易于理解和维护
    

#### 3\. 分离"知道做什么"和"知道怎么做"

System Prompt 告诉 Agent 它是谁、有什么工具。  
Skills 告诉 Agent 面对特定任务应该怎么做。

这种分离让两边都更简洁、更专注。

* * *

本次 skills 的实现，大概增加了 600 行代码
---------------------------

文件

行数

功能

skills.js

~300

SkillManager 核心类

tools/skills.js

~230

Skills 相关工具

index.js 更新

+90

集成 Skills 系统

新增约 **620 行代码**，让 Agent 具备了技能扩展能力。

* * *

还能做什么
-----

1.  1. **更多内置 Skills** — API 开发、数据库操作、测试编写
    
2.  2. **Skill 市场** — 从 GitHub 安装社区技能
    
3.  3. **Skill 依赖** — 一个 Skill 可以引用另一个 Skill
    

不过以上的这些我都不想做，因为其实这些原理就是写一个工具做 CV 技能到指定目录而已，并没有太多的技术可言。

好了，从对话到记忆，从工具到技能，我感觉我做的Agent 越来越像一个真正的助手了。四天，每天投入 1-2 个小时，我实现了一个几乎五脏俱全的 agent，我觉得下一步，可以考虑

#### 多 agent能力，从串行到并行，之前可能很多人听说多任务多任务并行，到时究竟怎么并行，他好优劣势是啥，你没实现过，你怎么就这么确定别人告诉你的任务不靠谱是不是因为他不会用还是真的不靠谱。

我一直觉得，能实现，和能用，是一种不同层次的理解。

#### 不知道你手痒了没，要不要也从零实现一个自己的 agent呀

  

#### 源码？会公开在我的某个小范围群中。

#### 引用链接

`[1]` Agent Skills: _https://agentskills.io_