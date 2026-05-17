# 什么是 skills 

## 一句话定义

> Skill 是一份可复用、带元数据、可被 Agent 主动发现并按需加载的能力包。

它通常包含：

```JSON
my-skill/
├── SKILL.md
├── references/
├── templates/
├── examples/
└── scripts/
```

其中最核心的是 `SKILL.md`，它通常以 YAML Frontmatter 开头：

```YAML
---
name: weekly-report-writer
description: Generate structured weekly reports from raw work logs. Use when the user asks for weekly summaries, progress reports, or status updates.
---

# Weekly Report Writer

Follow this workflow to turn raw work logs into a structured weekly report...
```

## Skill 的本质

Skill 不是一段普通 Prompt，而是一个“声明式能力包”。它有四个关键特征：

| **特征** | **说明**                                                     |
| :------- | :----------------------------------------------------------- |
| 可复用   | **写一次，处处触发**。一个合格的 `Skill` 不绑定具体对话，不绑定具体用户，也不绑定某一次任务。只要上下文命中了它的适用场景，`Agent` 就应当能把它拿出来用。多个 `Agent` 之间也可以共享同一个 `Skill`——它更像一份"团队级的作业规程"，而不是一张贴在某次聊天记录上的便签。 |
| 可发现   | 每个 `Skill` 都有一段结构化的 `Frontmatter`（文件头元数据），至少包含 `name` 和 `description` 两个字段。这段元数据不是写给人看的，是写给 `Agent` 看的——`Agent` 在运行时扫描所有可用 Skill 的元数据，据此判断"这次请求需不需要它"。所以 `description` 的措辞直接决定了一个 Skill 的触发率。一个 `Skill` 写得好不好用，一半功夫在正文，另一半功夫就在这几十个字的元数据里。 |
| 能力包   | 这是最容易被低估的一点。`Skill` **不只是一段 Prompt**。它是一个"包"（Capability Bundle），正文（`SKILL.md`）之外还可以捆绑：参考文档（`references/`）、填充模板（`templates/`）、示例数据（`examples/`）、可执行脚本（`scripts/`）、甚至更深一层的子 Skill（`sub-skills/`）。正文给出"怎么想"，附带资源给出"怎么做"。 |
| 按需加载 | `Skill` 遵循 `Progressive Disclosure（渐进式披露）` 原则——**元数据常驻 Context，正文按需读取，附带资源用时才展开**。这让 `Agent` 可以同时"知道"上百个 Skill 的存在，却不会因此塞爆 `Context Window`。 |

用一句更工程化的话说：

> Skill 是介于 Prompt 和 Tool 之间的能力描述。它不直接执行动作，但会指导 Agent 如何完成一类任务。

## Skill 与 Prompt、Tool、Script、Hook 的区别

| **类型** | **适合解决什么问题**           | **特点**                                 |
| -------- | ------------------------------ | ---------------------------------------- |
| Prompt   | 一次性的临时任务               | 快速、灵活，但难复用                     |
| Skill    | 可复用但仍需要模型判断的工作流 | 适合团队 SOP、模板化产出、领域知识注入   |
| Tool     | 明确的外部能力调用             | 适合发请求、查数据库、操作系统、访问服务 |
| Script   | 确定性计算或机械流程           | 适合校验、转换、统计、批处理             |
| Hook     | 固定时机自动触发的行为         | 适合启动前更新、保存后格式化、提交前检查 |

判断原则：

- 如果只是这一次要问，使用 Prompt。
- 如果一类任务会反复出现，使用 Skill。
- 如果动作必须稳定执行，使用 Tool 或 Script。
- 如果行为必须在固定时机触发，使用 Hook。

## 能做什么 & 不能做什么

Skill 适合做：

- 把团队重复工作流封装成 Agent 可复用能力。
- 给 Agent 注入领域知识，让它更懂团队业务和上下文。
- 保证输出格式稳定，例如固定章节、固定字段、固定模板。
- 引导 Agent 按步骤完成复杂任务，减少遗漏。
- 通过 `references/`、`templates/`、`examples/`、`scripts/` 组织大上下文。
- 让复杂能力逐步拆分成多个子 Skill 或 Sub-agent。

Skill 不是银弹，它有明确边界：

- 不能让弱模型变强。Skill 只能组织模型已有能力，不能创造模型没有的推理能力。
- 不能替代真正的 Tool Use。发邮件、查库、调接口仍然需要工具或脚本执行。
- 不适合解决纯确定性问题。能用 20 行 Python 稳定解决的事，不要写成几百字 Skill。
- 不能保证 100% 触发。触发依赖 `description` 写得是否准确，也依赖模型当下判断。
- 不是越多越好。过多相似 Skill 会互相抢触发，增加选择噪音。

# 什么时候应该写 Skill

## 适合写 Skill 的场景

适合沉淀为 Skill 的任务通常具备以下特征：

| **场景**           | **例子**                       | **为什么适合**               |
| ------------------ | ------------------------------ | ---------------------------- |
| 重复出现的工作流   | 周报、复盘、需求评审、代码审查 | 流程稳定，复用价值高         |
| 团队 SOP           | 发布流程、上线检查、排障步骤   | 需要统一执行标准             |
| 固定格式产出       | PRD、测试报告、技术方案        | 模板稳定，容易规范化         |
| 领域知识注入       | 业务术语、系统架构、接口规则   | Agent 默认不知道团队上下文   |
| 复杂但低确定性任务 | 调研、分析、评审、总结         | 需要模型判断，但可用流程约束 |
| 可组合任务         | 多维数据分析、多角度 review    | 可以拆给多个子任务并行处理   |

## 不适合写 Skill 的场景

不建议写 Skill 的情况：

- 一次性任务，未来很少复用。
- 完全确定性的计算或转换。
- 本质上是权限控制、安装更新、运行时治理的问题。
- 需要强实时状态或强事务一致性的操作。
- 需求边界非常模糊，连人都还没形成稳定流程。
- 只是为了保存一段资料，没有明确“做事意图”。

## 决策口诀

可以用下面这组问题判断：

1. 这个任务以后还会重复出现吗？
2. 它是否有稳定的步骤、模板或判断标准？
3. 它是否需要注入团队领域知识？
4. 它是否仍然需要模型进行理解、判断和生成？
5. 它是否不能完全用脚本或工具替代？

如果多数答案是“是”，它适合写成 Skill。

如果主要是确定性操作，优先写 Script 或 Tool。

# 如何编写一个好的 skills

## Skill 是写给 Agent 执行的能力说明书

**Skill 应该用英文写吗？Skill 用什么编辑器写最好？**首先，Skill 是指导 AI 该如何执行特定的任务，它是写给 AI 看的指令，不是给人类用户看的，因此我们认为 **Skill 必须由 AI 来编写，而不是你来写**。不仅如此，你需要用最贵的模型编写（如 Claude Opus），这样你才能有机会用更便宜的模型（如 Claude Sonnet）执行这个 Skill。至于使用英文还是中文写，也是由 AI 自己来决定的，通常是英文为主。至于编辑器，最好的工具就是 `skill-creator` 这个 Skill 本身，一般的 AI 工具都内置了这个 Skill，你可通过 `/skill-creator` 来执行。理解了这个层面后，接下来我们就来介绍一下 `/skill-creator` 里应该怎么和 AI 沟通你的需求。

**示例：**

```Markdown
/skill-creator 帮我实现一个技能，根据当前仓库的现有代码，提取出典型的团队代码风格：
1. 首先，通过文件树摸清这个仓库的主要编程语言，然后 propose 几个你认为最重要的文件。这些被挑选出的文件个数不能低于 3 个或多于 10 个，这些文件应该足以让你将了解团队代码的基本风格，同时尽可能的涵盖了项目中不同的编程语言、不同的架构层（配置、数据访问、API 暴露、Thrift 定义等）
2. 提取出团队代码的文件夹、文件、方法、成员、类型命名的规律（允许一个类别下有不同的命名方法），细致到例如分页器的参数是如何命名的
3. 作为 Coding Agent，你应该比团队还要更加了解自己的代码风格，而不是事无巨细的列出大家都知道的 rules（token-saving），才足以体现出你的价值
4. 总结为简明扼要的、方便 AI 理解而不是人类理解的 markdown 文档：docs/code-convention.md
```

![img](https://qn.huat.xyz/mac/202605171641239.(null))

AI 生成完了 Skill 后，应该立刻做测试。

![img](https://qn.huat.xyz/mac/202605171641671.(null))

除了手工测试外，一些复杂的场景你可能还需要做评测和反复修正

## `description` 是触发入口

Agent 通常会先看到所有 Skill 的 `name` 和 `description`，再决定是否加载某个 Skill。

所以 `description` 不是随便写的简介，而是 Skill 的触发入口。

一个好的 `description` 至少包含三类信息：

| **信息**     | **说明**                   |
| ------------ | -------------------------- |
| 做什么       | 这个 Skill 的能力是什么    |
| 什么时候用   | 用户出现什么需求时应该触发 |
| 什么时候不用 | 容易误触发时，要说明边界   |

不好的写法：

description: Help write better documents.

问题：

- 太泛。
- 不知道什么文档。
- 不知道触发场景。
- 容易和其他写作类 Skill 冲突。

更好的写法：

description: Create structured technical design documents for software projects. Use when the user needs to draft, review, or refine architecture proposals, implementation plans, RFCs, or engineering decision docs. Do not use for casual writing or marketing copy.

这个版本更好，因为它说明了：

- 能力：创建结构化技术设计文档。
- 场景：架构方案、实施计划、RFC、工程决策文档。
- 边界：不要用于随笔或营销文案。

## `SKILL.md` 只放主流程

`SKILL.md` 不应该变成一个巨大的知识库。

它更像一个入口文件，应该包含：

- 这个 Skill 的任务目标。
- 执行步骤。
- 关键决策点。
- 需要读取哪些资源文件。
- 需要调用哪些脚本或工具。
- 输出结果的格式要求。

建议控制原则：

- 简单 Skill 可以只有一个 `SKILL.md`。
- 中等复杂 Skill 应拆出模板和参考资料。
- 复杂 Skill 应使用 `references/`、`templates/`、`examples/`、`scripts/`。
- 如果 `SKILL.md` 超过 500 行，要检查是否需要渐进式披露。

## 渐进式披露：不要把所有内容塞进上下文

通常我们会把参考资料（reference）、示例（example）、模板（template）和脚本（Node.js / Python script）作为 Skill 渐进式披露的零件。就像我们前面提到的那样，最好的 Skill 编辑器就是 AI 自己，因此在通过 `/skill-creator` 生成了一个庞大的 Skill 后，你只需要对 Agent 说：

当前 SKILL.md 太长了，缺乏 progressive-disclosure 机制，但是也请不要滥用。

剩下来的事情就交给 AI 吧，它会帮你拆分成若干文件。例如，如果你的 Skill 里有模板和示例，并且内容很长，它会帮你拆分到对应目录的 markdown 文件里；再比如你的 Skill 里有类似 `switch...case` 的逻辑分支，并且每一个分支的逻辑都很庞大，它就会帮你把这些逻辑拆分成独立的 Markdown 文件，在运行时只有命中条件的一个或多个逻辑分支才会被加载。

当然，如果你的 Skill 里需要执行“机械式”的逻辑，skill-creator 也会帮你用 Node.js 或 Python 代码来实现，这样就不会在这些环节出现幻觉或漏执行（你也可以主动要求要用脚本执行某些环节），你可以直接对 Agent 说：

Skill 里可以“机械式”执行的部分（如果有）请帮我用 Python 实现。

Skills 利用 Claude 的虚拟机环境提供仅靠提示词无法实现的能力。Claude 在具有文件系统访问权限的虚拟机中运行，允许 Skills 以包含指令、可执行代码和参考材料的目录形式存在，其组织方式类似于您为新团队成员创建的入职指南。

这种基于文件系统的架构实现了渐进式披露：Claude 按需分阶段加载信息，而不是预先消耗上下文。

三种 Skill 内容类型，三个加载级别

Skills 可以包含三种类型的内容，每种内容在不同时间加载：

### 第一级：元数据（始终加载）

内容类型：指令。Skill 的 YAML 前置元数据提供发现信息：

```Plain
---name: pdf-processingdescription: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.---
```

Claude 在启动时加载此元数据并将其包含在系统提示中。这种轻量级方法意味着您可以安装许多 Skills 而不会产生上下文损耗；Claude 只知道每个 Skill 的存在以及何时使用它。

### 第二级：指令（触发时加载）

内容类型：指令。SKILL.md 的主体包含程序性知识：工作流程、最佳实践和指导：

```Plain
# PDF Processing## Quick startUse pdfplumber to extract text from PDFs:```pythonimport pdfplumberwith pdfplumber.open("document.pdf") as pdf:    text = pdf.pages[0].extract_text()```For advanced form filling, see [FORMS.md](FORMS.md).
```

当您的请求与 Skill 的描述匹配时，Claude 通过 bash 从文件系统读取 SKILL.md。只有在此时，这些内容才会进入上下文窗口。

### 第三级：资源和代码（按需加载）

内容类型：指令、代码和资源。Skills 可以捆绑额外的材料：

```Plain
pdf-skill/
├── SKILL.md (main instructions)
├── FORMS.md (form-filling guide)
├── REFERENCE.md (detailed API reference)
└── scripts/
    └── fill_form.py (utility script)
```

指令：包含专业指导和工作流程的额外 markdown 文件（FORMS.md、REFERENCE.md）

代码：Claude 通过 bash 运行的可执行脚本（fill_form.py、validate.py）；脚本提供确定性操作而不消耗上下文

资源：参考材料，如数据库模式、API 文档、模板或示例

Claude 仅在被引用时才访问这些文件。文件系统模型意味着每种内容类型具有不同的优势：指令用于灵活指导，代码用于可靠性，资源用于事实查询。

| 级别               | 加载时机       | Token 成本                 | 内容                                             |
| :----------------- | :------------- | :------------------------- | :----------------------------------------------- |
| 第一级：元数据     | 始终（启动时） | 每个 Skill 约 100 个 token | YAML 前置元数据中的 name 和 description          |
| 第二级：指令       | 触发 Skill 时  | 不超过 5k token            | 包含指令和指导的 SKILL.md 主体                   |
| 第三级及以上：资源 | 按需           | 实际上无限制               | 通过 bash 执行的捆绑文件，不将内容加载到上下文中 |

渐进式披露确保在任何给定时间只有相关的 Skill 内容占用上下文窗口。

### 示例：加载 PDF 处理 Skill

以下是 Claude 加载和使用 PDF 处理 Skill 的方式：

1. 启动：系统提示包含：`PDF Processing - Extract text and tables from PDF files, fill forms, merge documents`
2. 用户请求："从这个 PDF 中提取文本并总结"
3. Claude 调用：`bash: read pdf-skill/SKILL.md` → 指令加载到上下文中
4. Claude 判断：不需要填写表单，因此不读取 FORMS.md
5. Claude 执行：使用 SKILL.md 中的指令完成任务

![img](https://qn.huat.xyz/mac/202605171641322.(null))

该图显示：

1. 预加载系统提示和 Skill 元数据的默认状态
2. Claude 通过 bash 读取 SKILL.md 触发 Skill
3. Claude 根据需要可选地读取额外的捆绑文件，如 FORMS.md
4. Claude 继续执行任务

这种动态加载确保只有相关的 Skill 内容占用上下文窗口。

## 保留 Human-in-the-Loop 的交互

一个好的 Skill 应该适当的引入 Human-in-the-Loop。你可以在 Skill 的 prompt 里明确要求它使用 `AskUserQuestion` 来与用户进行多轮交互。`AskUserQuestion` 工具支持单选、多选和预览单选等交互，同时还支持 Step-by-step 式的向导。

## Bash 命令和 CLI 是最好的工具

很多同学都抱怨说 Skill 里不能执行自定义工具，事实上直接将少量非核心代码作为 Python 或 Node.js 程序写在 Skill 的 scripts 目录中，并且支持命令行参数作为输入，就是最好的工具。

说到这里不得不说一下 CLI。**良好的 CLI 应该也是递进的**、**渐进式披露的**帮助的：

```Markdown
helixent help # 查看 helixent 的总帮助文档，列出一级命令即可
helixent config help # 查看 helixent 中 config 命令的帮助
helixent config model help # 查看 helixent 如何配置模型
helixent config model add help # 查看具体 `add` 方法如何使用
```

若要实现上述效果，Python 和 Node.js 中都有对应的库。如 Python 的 `click`、`typer`，Node.js 里的 `commander` 等，只需要稍微提示 `/skill-creator` 使用上述库即可。

# 实战案例

## ai-news-daily-report  （AI资讯skills）

> 该案例体现了 Progressive Disclosure 的多层资源结构（scripts/ + references/ + assets/）。支持 自定义配置、human-in-the-loop

需求说明

用 skill-creator 生成 Skill

## ls-house-updating-bam  （前端更新bam skills）

> 与 ai-news 的"重量级"形成对比，展示一个只有 SKILL.md 的"轻量级"业务 Skill。

场景介绍

Skill 解剖

# 房产 Skills 管理与开发规范

[房产 Skills 管理指南](https://bytedance.larkoffice.com/wiki/BWGGwgh2piYMXskGyNVca7gZnAd)

# 附录

| 资源                                                         | 你可获得                                                |
| :----------------------------------------------------------- | :------------------------------------------------------ |
| [Agent Skills](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/overview) |                                                         |
| [技能编写最佳实践](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/best-practices) |                                                         |
| [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) |                                                         |
| [Introduction to Claude Skills](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) |                                                         |
| skill-creator 详解                                           | /Users/bytedance/Desktop/fc/person-project/skills       |
| baoyu-skills 详解                                            | /Users/bytedance/Desktop/fc/person-project/baoyu-skills |
| [Harness 101 + Skills 101](https://my.feishu.cn/sync/Al7fdhQBqssP3Fb7uNkczV3Cnse) |                                                         |