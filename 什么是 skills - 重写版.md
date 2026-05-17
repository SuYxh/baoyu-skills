# 什么是 Skills：从 Prompt 到可复用能力包

## 分享目标

这份文档面向希望把重复工作流沉淀给 Agent 的同学，目标不是介绍一个新名词，而是回答三个更实际的问题：

1. 什么样的任务值得写成 Skill？
2. 一个 Skill 应该如何组织，才能被 Agent 稳定发现和执行？
3. 写完 Skill 之后，如何测试、评测和持续迭代？

读完之后，你应该能够判断一个需求适不适合写成 Skill，并能用 `skill-creator` 生成、拆分、测试一份可复用的 Skill。

## 1. 为什么需要 Skills

在 Agent 使用过程中，我们经常会遇到一类问题：

- 同一类任务会反复出现，例如周报、复盘、需求评审、代码审查、资讯日报。
- 每次任务都需要遵循相似的步骤、模板或判断标准。
- Agent 需要理解团队业务、代码风格、术语、接口规则等上下文。
- 单靠一次性的 Prompt 很难稳定复用，复制粘贴又容易遗漏细节。
- 有些步骤需要模型判断，有些步骤又希望通过脚本稳定执行。

这时，继续写更长的 Prompt 往往不是最优解。更好的方式是把这类重复任务沉淀成一个可被 Agent 主动发现、按需加载、可持续迭代的能力包。

这就是 Skill 的价值。

## 2. Skill 是什么

一句话定义：

> Skill 是一份可复用、带元数据、可被 Agent 主动发现并按需加载的能力包。

一个典型 Skill 通常长这样：

```text
my-skill/
├── SKILL.md
├── references/
├── templates/
├── examples/
└── scripts/
```

其中最核心的是 `SKILL.md`。它通常以 YAML Frontmatter 开头：

```yaml
---
name: weekly-report-writer
description: Generate structured weekly reports from raw work logs. Use when the user asks for weekly summaries, progress reports, or status updates.
---

# Weekly Report Writer

Follow this workflow to turn raw work logs into a structured weekly report...
```

Skill 不是一段普通 Prompt，而是一份“声明式能力包”。它介于 Prompt 和 Tool 之间：

- 它不像 Prompt 那样只服务于一次对话。
- 它不像 Tool 那样直接执行某个确定动作。
- 它会告诉 Agent：遇到哪类任务时，应该按什么流程、参考哪些资料、调用哪些脚本、输出什么结果。

更工程化地说：

> Skill 是对一类任务的可复用执行说明。它不直接替 Agent 做事，但会指导 Agent 如何稳定完成这类任务。

## 3. Skill 的四个核心特征

| 特征 | 说明 |
| --- | --- |
| 可复用 | 写一次，处处触发。一个合格的 Skill 不绑定某次对话，也不绑定某个具体用户，而是沉淀一类可重复出现的任务。 |
| 可发现 | Skill 通过 `name` 和 `description` 暴露给 Agent。Agent 会先看到这些元数据，再决定是否加载正文。 |
| 能力包 | Skill 不只是 `SKILL.md`，还可以包含 `references/`、`templates/`、`examples/`、`scripts/` 等资源。 |
| 按需加载 | Skill 遵循 Progressive Disclosure。元数据常驻上下文，正文和附加资源只在需要时加载。 |

这四个特征决定了 Skill 的基本设计原则：

- `description` 负责让 Agent 找得到它。
- `SKILL.md` 负责描述主流程。
- `references/`、`templates/`、`examples/` 负责承载大上下文。
- `scripts/` 负责处理确定性、机械性、容易出错的步骤。

## 4. Skill 和 Prompt、Tool、Script、Hook 的区别

| 类型 | 适合解决什么问题 | 特点 |
| --- | --- | --- |
| Prompt | 一次性的临时任务 | 快速、灵活，但难复用 |
| Skill | 可复用但仍需要模型判断的工作流 | 适合团队 SOP、模板化产出、领域知识注入 |
| Tool | 明确的外部能力调用 | 适合发请求、查数据库、操作系统、访问服务 |
| Script | 确定性计算或机械流程 | 适合校验、转换、统计、批处理 |
| Hook | 固定时机自动触发的行为 | 适合启动前更新、保存后格式化、提交前检查 |

可以用下面的规则快速判断：

- 如果只是这一次要问，用 Prompt。
- 如果一类任务会反复出现，用 Skill。
- 如果动作必须稳定执行，用 Tool 或 Script。
- 如果行为必须在固定时机自动触发，用 Hook。

Skill 最适合的不是“完全确定的动作”，而是“有稳定流程，但仍需要模型理解、判断和生成”的任务。

## 5. 什么时候应该写 Skill

适合写成 Skill 的任务通常具备以下特征：

| 场景 | 例子 | 为什么适合 |
| --- | --- | --- |
| 重复出现的工作流 | 周报、复盘、需求评审、代码审查 | 流程稳定，复用价值高 |
| 团队 SOP | 发布流程、上线检查、排障步骤 | 需要统一执行标准 |
| 固定格式产出 | PRD、测试报告、技术方案 | 模板稳定，容易规范化 |
| 领域知识注入 | 业务术语、系统架构、接口规则 | Agent 默认不知道团队上下文 |
| 复杂但低确定性任务 | 调研、分析、评审、总结 | 需要模型判断，但可用流程约束 |
| 可组合任务 | 多维数据分析、多角度 Review | 可以拆分为多个子任务并行处理 |

不建议写成 Skill 的情况：

- 只是一次性任务，未来很少复用。
- 完全确定性的计算或转换。
- 本质上是权限控制、安装更新、运行时治理的问题。
- 需要强实时状态或强事务一致性的操作。
- 需求边界非常模糊，连人都还没形成稳定流程。
- 只是为了保存一段资料，没有明确的“做事意图”。

可以用这组问题做决策：

1. 这个任务以后还会重复出现吗？
2. 它是否有稳定的步骤、模板或判断标准？
3. 它是否需要注入团队领域知识？
4. 它是否仍然需要模型进行理解、判断和生成？
5. 它是否不能完全用脚本或工具替代？

如果多数答案是“是”，它适合写成 Skill。

如果主要是确定性操作，优先写 Script 或 Tool。

## 6. 好 Skill 的判断标准

一个好 Skill 不只是“能跑”，而是要做到可发现、可执行、可维护、可验收。

可以用下面 5 条标准判断：

| 标准 | 说明 |
| --- | --- |
| 触发准确 | `description` 能清楚说明什么时候用、什么时候不用。 |
| 边界清楚 | 不和其他 Skill 抢触发，也不包揽不该做的事。 |
| 流程稳定 | `SKILL.md` 写的是可复用工作流，而不是一次性 Prompt。 |
| 渐进披露 | 主流程短，长资料放到 `references/`、`templates/`、`examples/`、`scripts/`。 |
| 可验收 | 有测试样例、失败标准和迭代方法。 |

这 5 条也是后面用 `skill-creator` 编写和测试 Skill 时的检查尺子。

## 7. 用 skill-creator 从 0 到 1 生成一个 Skill

Skill 是写给 Agent 执行的能力说明书，不是写给人类用户阅读的普通文档。因此，推荐用 AI 辅助编写 Skill。

更准确地说：

> 人负责定义目标、边界和验收标准；AI 负责生成结构、补全流程、拆分资源、沉淀脚本和迭代 description。

`skill-creator` 是最适合用来生成和优化 Skill 的工具。一个实用流程如下：

```text
明确任务
  ↓
描述目标、边界和输入输出
  ↓
让 skill-creator 生成第一版 Skill
  ↓
检查 description 是否准确
  ↓
检查 SKILL.md 是否只放主流程
  ↓
拆分 references/templates/examples/scripts
  ↓
用真实任务测试
  ↓
根据失败点迭代
```

### 7.1 第一步：把需求说清楚

不要只对 `skill-creator` 说“帮我写一个 Skill”。更好的方式是把任务目标、适用场景、边界、参考材料和验收要求一起交代清楚。

示例：

```markdown
/skill-creator 帮我实现一个技能，根据当前仓库的现有代码，提取出典型的团队代码风格：

1. 首先，通过文件树摸清这个仓库的主要编程语言，然后 propose 几个你认为最重要的文件。
2. 被挑选出的文件个数不能低于 3 个或多于 10 个。
3. 这些文件应该足以了解团队代码的基本风格，并尽可能覆盖不同编程语言、不同架构层，例如配置、数据访问、API 暴露、Thrift 定义等。
4. 提取团队代码在文件夹、文件、方法、成员、类型命名上的规律，细致到例如分页器参数如何命名。
5. 作为 Coding Agent，你应该比团队还要更加了解自己的代码风格，不要事无巨细列出大家都知道的 rules。
6. 总结为简明扼要、方便 AI 理解而不是人类理解的 Markdown 文档：docs/code-convention.md。
```

这类输入比“帮我写一个代码规范 Skill”更好，因为它明确了：

- 目标：提取团队代码风格。
- 范围：基于当前仓库。
- 方法：先选文件，再归纳规律。
- 约束：文件数量、覆盖范围、输出位置。
- 标准：要体现 Agent 对团队代码风格的理解，而不是泛泛而谈。

### 7.2 第二步：重点检查 description

Agent 通常会先看到所有 Skill 的 `name` 和 `description`，再决定是否加载某个 Skill。

所以 `description` 不是简介，而是触发入口。一个好的 `description` 至少包含三类信息：

| 信息 | 说明 |
| --- | --- |
| 做什么 | 这个 Skill 的能力是什么 |
| 什么时候用 | 用户出现什么需求时应该触发 |
| 什么时候不用 | 容易误触发时，要说明边界 |

不好的写法：

```yaml
description: Help write better documents.
```

问题是太泛，不知道什么文档、不知道触发场景，也容易和其他写作类 Skill 冲突。

更好的写法：

```yaml
description: Create structured technical design documents for software projects. Use when the user needs to draft, review, or refine architecture proposals, implementation plans, RFCs, or engineering decision docs. Do not use for casual writing or marketing copy.
```

这个版本更好，因为它同时说明了：

- 能力：创建结构化技术设计文档。
- 场景：架构方案、实施计划、RFC、工程决策文档。
- 边界：不要用于随笔或营销文案。

### 7.3 第三步：让 SKILL.md 只放主流程

`SKILL.md` 不应该变成一个巨大的知识库。

它更像入口文件，应该包含：

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

### 7.4 第四步：使用渐进式披露

Skills 的文件系统结构让 Agent 可以按需加载信息，而不是一开始就把所有内容塞进上下文。

三种内容类型，对应三个加载级别：

| 级别 | 加载时机 | 内容 |
| --- | --- | --- |
| 第一级：元数据 | 始终加载 | YAML Frontmatter 中的 `name` 和 `description` |
| 第二级：指令 | Skill 被触发时加载 | `SKILL.md` 中的主流程和执行说明 |
| 第三级：资源和代码 | 按需加载 | `references/`、`templates/`、`examples/`、`scripts/` |

示例：

```text
pdf-skill/
├── SKILL.md
├── FORMS.md
├── REFERENCE.md
└── scripts/
    └── fill_form.py
```

当用户说“从这个 PDF 中提取文本并总结”时，Agent 的加载路径可能是：

1. 启动时已经知道：有一个 PDF Processing Skill。
2. 用户请求命中 `description`。
3. Agent 读取 `SKILL.md`。
4. Agent 判断不需要填写表单，因此不读取 `FORMS.md`。
5. Agent 按主流程完成提取和总结。

这就是 Progressive Disclosure 的价值：让 Agent 知道很多能力的存在，但只加载当前任务真正需要的内容。

如果 `skill-creator` 生成的 `SKILL.md` 太长，可以直接要求它优化：

```markdown
当前 SKILL.md 太长了，缺乏 progressive-disclosure 机制。请在不滥用拆分的前提下，把长模板、长示例、参考资料和复杂分支拆到 references/templates/examples/scripts 中。
```

如果 Skill 中存在机械式步骤，也可以要求它沉淀为脚本：

```markdown
Skill 里可以机械式执行的部分，请优先用 Python 或 Node.js 脚本实现，并提供清晰的 CLI 参数说明。
```

### 7.5 第五步：保留 Human-in-the-Loop

一个好的 Skill 不一定要全自动完成所有事情。

当任务需要用户确认目标、选择范围、补充上下文或做关键决策时，Skill 应该明确要求 Agent 使用 Human-in-the-Loop。

例如，可以在 Skill 中要求：

- 当需求边界不清楚时，先向用户提问。
- 当存在多种实现路径时，提供 2 到 4 个选项。
- 当输出会影响真实业务时，先让用户确认再执行。
- 当模板、案例或数据来源缺失时，不要自行编造。

在支持 `AskUserQuestion` 的环境中，Skill 可以明确要求 Agent 使用单选、多选或 Step-by-step 向导来收集用户输入。

### 7.6 第六步：把 CLI 也设计成渐进式披露

如果 Skill 里包含脚本，脚本本身也应该容易理解和调用。

良好的 CLI 帮助应该也是递进的：

```bash
helixent help
helixent config help
helixent config model help
helixent config model add help
```

Python 可以使用 `click`、`typer`，Node.js 可以使用 `commander` 来实现这样的命令行体验。

### 7.7 案例一：ai-news-daily-report

`ai-news-daily-report` 是一个比较典型的“重量级 Skill”案例。

#### 案例背景

AI 资讯更新非常快，日常如果靠人工整理，通常会遇到几个问题：

- 信源分散：信息来自不同 RSS、Newsletter、博客、媒体和社区。
- 重复内容多：同一条新闻会被多个来源转载或改写。
- 筛选成本高：并不是所有新闻都值得进入日报或周报。
- 输出格式不稳定：不同人整理出来的简报结构、粒度和重点不一致。
- 流程容易中断：某些 RSS 源失效、网络请求失败、文章内容抓取不到，都会影响最终产出。

所以这个案例的目标不是让 Agent “随便总结几条新闻”，而是把“AI 资讯收集、清洗、筛选、排序、生成简报”这一整套流程沉淀成一个可复用的 Skill。

它最终希望做到：

- 用户只需要提供 OPML、RSS 或默认配置。
- Agent 能自动抓取最近资讯，并处理失败信源。
- Agent 能对内容做去重、分类和重要性排序。
- 最终输出一份结构稳定、可直接阅读和转发的中文 Markdown 简报。
- 当配置不清楚或需要人工判断时，Agent 能主动询问用户，而不是自行猜测。

这个场景很适合写成 Skill，因为它既有稳定流程，又依赖模型判断；既需要领域理解，也需要脚本处理确定性任务。

这个案例适合拿来分享，是因为它完整体现了一个 Skill 从“需求描述”到“生成初版”再到“运行后优化”的过程。

#### 7.7.1 第一步：把需求交给 skill-creator

第一步不是直接让 Agent 写代码，而是先告诉 `skill-creator`：我们要沉淀的是一个可复用的 AI 资讯 Skill。

这里的关键是要把“我要什么结果”和“这个 Skill 以后怎么被复用”说清楚，而不是只说“帮我写一个新闻摘要工具”。

![告诉 skill-creator 需要生成 AI 资讯 Skill](https://qn.huat.xyz/mac/202605172343386.png)

这一轮的重点是让 Agent 先建立任务边界：

- 这是一个面向“AI 资讯日报/周报”的 Skill。
- 输入可能来自 OPML、RSS 或一组信源配置。
- 输出应该是中文 Markdown 简报。
- 任务不只是摘要，还包括抓取、去重、排序和分类。

#### 7.7.2 第二步：回答 Agent 的澄清问题

复杂 Skill 不应该一次性拍脑袋生成。`skill-creator` 会先追问一些问题，例如信源如何提供、时间范围如何设置、输出格式是什么、是否需要人工确认。

这一步很重要，因为 Skill 写得好不好，取决于人有没有把业务边界讲清楚。

![回答 AI 的问题，补充需求边界](https://qn.huat.xyz/mac/202605172344742.(null))

可以把这一轮理解为 Human-in-the-Loop 的前置设计：

- 人负责回答业务规则和使用习惯。
- Agent 负责把这些规则转成可执行的 Skill 结构。
- 不清楚的地方不要让 Agent 猜，而是通过追问补齐。

#### 7.7.3 第三步：继续补齐第二批问题

第一轮回答后，Agent 还会继续追问更细的问题。

这通常说明 Skill 已经开始进入“工程化设计”阶段：不仅要知道要做什么，还要知道默认值、配置项、异常情况和输出约束。

![继续回答第二批问题](https://qn.huat.xyz/mac/202605172345613.png)

这一阶段要重点确认：

- 默认抓取最近几天的内容。
- 是否需要支持日报和周报两种模式。
- 是否需要限制最大文章数量。
- 是否需要输出中英文标题、来源、链接和推荐理由。
- 是否需要在抓取失败时继续执行，而不是整个流程中断。

#### 7.7.4 第四步：生成初始版本 Skill

需求澄清完成后，`skill-creator` 开始起草初始版本 Skill。

对于 `ai-news-daily-report` 这类任务，一个合适的 Skill 不应该只有一个超长 `SKILL.md`。它更适合拆成多层结构：

```text
ai-news-daily-report/
├── SKILL.md
├── references/
│   ├── source-selection.md
│   └── ranking-rules.md
├── templates/
│   └── briefing-template.md
├── examples/
│   └── sample-briefing.md
└── scripts/
    ├── fetch_feeds.py
    ├── deduplicate.py
    └── rank_articles.py
```

![开始起草初始版本 Skill](https://qn.huat.xyz/mac/202605172345989.png)

这个结构体现了 Progressive Disclosure：

- `SKILL.md` 只描述主流程。
- 信源规则、排序规则放进 `references/`。
- 简报格式放进 `templates/`。
- 示例输出放进 `examples/`。
- 抓取、去重、排序这类机械步骤放进 `scripts/`。

#### 7.7.5 第五步：真实运行后暴露问题

Skill 生成后要立刻测试，而不是停留在“看起来结构很完整”。

第一次运行时暴露了一个典型问题：有些订阅源已经不可用，或者抓取结果不稳定。如果 Skill 没有处理这种异常，就会导致整条资讯生产链路变得脆弱。

![运行后发现部分订阅源不可用](/Users/bytedance/Downloads/image (3).png)

这个问题非常适合作为分享中的重点，因为它说明：

- Skill 不是一次生成就结束。
- 真实数据源会失效，Skill 必须考虑异常和降级。
- 抓取脚本需要有超时、失败跳过、错误摘要和可观测输出。
- 对外部资源依赖越强，越需要测试和迭代。

#### 7.7.6 第六步：第一次优化，多方面增强健壮性

发现订阅源问题后，第一轮优化不应该只修某一个 URL，而是要从系统层面增强 Skill 的健壮性。

![第一次优化：多方面增强](https://qn.huat.xyz/mac/202605172347103.png)

这一轮可以重点优化：

- 对失效 RSS 源做跳过处理。
- 输出哪些信源成功、哪些信源失败。
- 为抓取请求增加超时和重试策略。
- 保留可读的错误摘要，方便后续维护信源列表。
- 避免某一个订阅源失败导致整个日报生成失败。

#### 7.7.7 第七步：第二次优化，继续收敛执行体验

第一次优化解决的是“能不能稳定跑完”，第二次优化更关注“使用体验是否足够顺”。

![第二次优化](https://qn.huat.xyz/mac/202605172348216.png)

这一轮可以继续检查：

- 输出内容是否足够稳定。
- 排序和去重是否符合预期。
- 生成的 Markdown 是否适合直接阅读。
- 脚本参数是否容易理解。
- 是否需要把常用参数沉淀成默认配置。

#### 7.7.8 第八步：配置项优化

当 Skill 从一次性脚本变成可复用能力后，配置项就会变得很重要。

![配置项优化](https://qn.huat.xyz/mac/202605172348265.png)

`ai-news-daily-report` 这类 Skill 至少需要考虑：

- 默认信源配置。
- 默认时间范围。
- 输出文件路径。
- 最大文章数量。
- 是否启用摘要、分类、排序。
- 是否在运行前让用户确认配置。

配置项的价值是让 Skill 既有默认行为，又能适配不同使用场景。

#### 7.7.9 第九步：并行抓取优化

资讯抓取通常会涉及多个信源，如果串行抓取，执行时间会比较长。因此后续又做了并行抓取优化。

![并行抓取优化](https://qn.huat.xyz/mac/202605172349574.png)

这里的设计是：默认并发数为 10，最多支持 50。

这个优化点很适合说明 `scripts/` 的价值：

- 并发抓取属于确定性工程逻辑，不适合靠 Prompt 描述后让模型临场发挥。
- 这类能力应该沉淀到脚本里，通过 CLI 参数控制。
- Skill 负责告诉 Agent 什么时候调用脚本、传什么参数、如何解释结果。

#### 7.7.10 这个案例体现的设计原则

`ai-news-daily-report` 的价值不在于“生成一份新闻简报”，而在于它完整展示了一个复杂 Skill 的演进路径：

```text
描述需求
  ↓
多轮澄清
  ↓
生成初版 Skill
  ↓
真实运行
  ↓
暴露订阅源问题
  ↓
优化异常处理
  ↓
优化配置项
  ↓
优化并行抓取
  ↓
形成可复用能力
```

这个案例也对应了前面提到的几个关键原则：

- 复杂 Skill 需要 Human-in-the-Loop 先把需求讲清楚。
- `SKILL.md` 不应该承载所有细节，要通过 Progressive Disclosure 拆分资源。
- 抓取、去重、排序、并发这类机械流程应该放进 `scripts/`。
- 外部依赖越多，越需要真实运行测试。
- Skill 的质量不是靠一次生成，而是靠“运行问题 → 归因 → 迭代”逐步打磨出来的。

### 7.8 案例二：ls-house-updating-bam

`ls-house-updating-bam` 是一个轻量级业务 Skill，用来自动化前端项目中的 BAM 接口更新流程。

这个案例不是本次分享的重点，但它很适合用来和 `ai-news-daily-report` 做对比：并不是所有 Skill 都需要复杂目录，有些业务 SOP 只靠一个清晰的 `SKILL.md` 就能沉淀下来。

它的 `description` 写得很具体：

```yaml
name: ls-house-updating-bam
description: 当用户需要更新或同步 BAM (API 管理平台) 接口定义时使用。触发条件包括提到 "bam update"、"更新一下 bam" 或粘贴包含 "cloud.bytedance.net/bam/rd/" 的 BAM 链接。这个技能将自动探测项目中的 bam.config.js 位置，解析链接中的 PSM 和版本号，更新配置文件，并在正确目录下执行 bam 命令来拉取最新接口文件。
```

这个 Skill 的主流程非常直接：

- 如果用户提供 BAM 链接，Agent 解析链接中的 PSM、版本号或分支名，更新 `bam.config.js`，再执行 `npx bam update`。
- 如果用户只是说“更新一下 bam”，Agent 先找到项目里的 `bam.config.js`，再在正确目录执行 `npx bam update`。
- 如果项目里有多个 `bam.config.js`，Agent 不自行判断，而是让用户选择。
- 修改 `services` 配置前，Agent 必须先观察当前文件已有风格，保持短服务名、完整 PSM、字符串值或对象值等写法一致。

```text
ls-house-updating-bam/
└── SKILL.md
```

这个案例重点体现：

- 不是所有 Skill 都需要复杂目录结构。
- 轻量 Skill 的关键是把业务 SOP 写清楚。
- `description` 要把内部触发词和业务入口写具体。
- Agent 修改配置前必须先观察项目已有风格，不能强行套固定格式。
- 遇到多个配置文件或无法判断风格时，要引入 Human-in-the-Loop。
- 能用一个清晰的 `SKILL.md` 解决问题，就不要为了“看起来工程化”而强行拆分。

## 8. 如何测试和评测 Skill

Skill 写完之后，不应该直接发布。至少要验证三件事：

1. Skill 会不会被正确触发？
2. Skill 触发后能不能稳定完成任务？
3. Skill 失败后能不能定位原因并迭代？

可以把测试拆成四类：触发测试、执行测试、验收测试、失败归因。

### 8.1 触发测试

触发测试主要验证 `description` 写得准不准。

建议准备四类 Prompt：

| 类型 | 目的 | 示例 |
| --- | --- | --- |
| 正向触发 | 用户明确需要这个 Skill | “帮我根据这些 RSS 生成一份 AI 日报。” |
| 模糊触发 | 用户没有说 Skill 名，但表达了对应意图 | “帮我整理一下今天 AI 圈重要新闻。” |
| 反向触发 | 用户请求相似任务，但不应该使用这个 Skill | “帮我写一篇 AI 科普文章。” |
| 冲突触发 | 多个 Skill 都可能命中时，观察是否选对 | “帮我整理资料并写成公众号文章。” |

如果正向触发失败，优先改 `description` 的触发场景。

如果反向触发误命中，优先补充 `description` 的排除边界。

### 8.2 执行测试

执行测试主要验证 `SKILL.md` 的主流程是否清楚。

重点检查：

- Agent 是否按 `SKILL.md` 的步骤执行？
- Agent 是否漏读必要的 `references/`、`templates/` 或 `examples/`？
- Agent 是否在需要用户确认时引入 Human-in-the-Loop？
- Agent 是否把机械性任务交给 `scripts/`，而不是靠模型猜？
- 输出格式是否稳定？
- 异常输入是否有处理方式？

如果触发了但执行差，通常不是 `description` 的问题，而是 `SKILL.md` 的流程不够清楚。

### 8.3 验收测试

建议为每个 Skill 准备 3 到 5 个代表性任务：

| 任务类型 | 验证内容 |
| --- | --- |
| 简单任务 | 主流程能否跑通 |
| 典型任务 | 最常见业务场景是否稳定 |
| 边界任务 | 容易出错的情况是否有处理 |
| 反例任务 | 不该触发时是否不会触发 |
| 复杂任务 | 是否能按需加载 references/scripts |

验收测试不一定要做成复杂 benchmark。对大多数团队 Skill 来说，先保留一组可复用测试样例，就已经能显著提升可维护性。

### 8.4 失败归因

Skill 不好用时，可以按下面的路径排查：

| 现象 | 可能原因 | 优先修改 |
| --- | --- | --- |
| 没触发 | `description` 太模糊或缺少触发场景 | 修改 `description` |
| 误触发 | `description` 缺少排除边界 | 增加 Do not use 场景 |
| 触发了但执行差 | 主流程不清楚 | 修改 `SKILL.md` |
| 上下文太长 | 缺少 Progressive Disclosure | 拆分资源文件 |
| 输出不稳定 | 缺少模板或示例 | 增加 `templates/`、`examples/` |
| 步骤漏执行 | 机械流程靠模型记忆 | 增加 `scripts/` |
| 用户体验差 | 关键节点没有确认 | 引入 Human-in-the-Loop |



## 9. 团队落地规范与资源

Skill 可以作为个人效率工具，也可以成为团队级能力资产。房产业务已经在探索一套更接近 npm 依赖管理的 Skills 落地方式：统一仓库管理、统一发布到 Skills Hub，并在业务项目中通过 lock 文件锁定依赖版本。

### 9.1 为什么要统一管理

在多代码仓库、多技术栈协作的房产业务场景中，如果 Skills 只散落在个人本地或某个业务仓库里，会遇到几个典型问题：

- 版本不一致：不同开发者、不同项目安装的 Skill 版本不同，执行结果难以对齐。
- 同步困难：业务 SOP 更新后，很难保证所有项目里的 Skill 都及时更新。
- 误触发风险：为了覆盖场景而安装大量 Skills，可能导致模糊指令命中不该触发的“隐身技能”。
- 依赖不可追踪：项目缺少像 `package.json` 一样的 Skill 依赖声明和版本锁定。
- 质量不可控：缺少创建、检测和评估规范，Skill 容易变成“专人专用”而不是团队通用能力。

所以团队落地的目标是：把通用 Skills 收敛到统一仓库，并通过 `skills-lock.json` 精确控制业务项目依赖哪些 Skills、来自哪里、锁定到哪个版本。

### 9.2 团队仓库与 Skills Hub

房产团队的 Skills 和 CLI 统一沉淀在团队仓库中：

- Skills 仓库：`https://code.byted.org/life_service/fangchan-cli-repo`
- Skills Hub 空间：`https://skills.bytedance.net/space/skills.byted.org%2Flife_service%2Ffangchan`

仓库结构大致分为两类：

```text
fangchan-cli-repo/
├── packages/              # CLI 目录
│   ├── d2c-cli
│   ├── docs-cli
│   └── icons-cli
├── skills/                # Skills 目录
│   ├── d2c-diff-workflow
│   ├── doc-cli
│   └── ...
├── AGENTS.md
└── README.md
```

当 Skill 同步到团队仓库的主干后，会自动发布到 Skills Hub，供业务项目安装和消费。

### 9.3 业务项目如何消费 Skills

业务项目通过 `skills` CLI 安装团队 Skill。安装后，项目根目录会生成或更新 `skills-lock.json`，用于声明并锁定依赖版本。

示例：

```json
{
  "version": 1,
  "skills": {
    "ls-house-updating-bam": {
      "source": "code.byted.org:life_service/fangchan-cli-repo",
      "sourceType": "git",
      "computedHash": "0d4c8963eb48e27679ca195d4177d50aa362117a8d7c5c72d91df5a6846a0277"
    }
  }
}
```

这里的关键是 `computedHash`，它相当于 Skill 的版本锁，确保团队成员和 AI 使用的是同一份标准化能力。

安装示例：

```bash
# 安装内场 skills CLI
npm i skills -g --registry=https://bnpm.byted.org

# 从团队仓库下载 Skill
npx skills add code.byted.org:life_service/fangchan-cli-repo --skill ls-house-updating-bam

# 从 Skills Hub 下载指定版本
skills add skills.byted.org/life_service/fangchan --skill ls-house-updating-bam --version 1.0.3 -y
```

与 `node_modules` 类似，本地安装出来的 Skills 文件夹属于构建产物，推荐不要提交到 Git 仓库。业务项目应提交的是 `skills-lock.json`，而不是安装后的 Skill 文件夹。

### 9.4 如何贡献团队 Skill

团队 Skill 的命名需要语义化、清晰、不泛化：

- 统一使用 `ls-house` 前缀，例如 `ls-house-updating-bam`。
- 使用 `kebab-case` 风格。
- 推荐使用 `verb-ing + 名词` 结构，例如 `updating-bam`、`finding-okee-pc-comp`。
- 长度不超过 64 个字符。
- 避免 `helper`、`utils`、`tools`、`data`、`code` 这类模糊名称。

推荐命名：

- `ls-house-debugging-react-error`
- `ls-house-generating-git-commit-message`
- `ls-house-creating-api-documents`

不推荐命名：

- `debugReact`
- `error_debug`
- `gitCommit`
- `commit_msg_gen`
- `makeApiDoc`

开发上，推荐使用 `create-skill` 这类“元技能”来创建、测试、优化和打包 Skill。它会通过交互式引导帮助开发者补齐需求，并在开发前扫描是否已有相似能力，避免重复建设。

### 9.5 团队 Skill 的质检重点

即使使用 `create-skill` 生成，团队通用 Skill 也必须经过质检。重点不是“能不能在我本地跑通”，而是“能不能被别人、别的项目复用”。

质检时至少关注：

- 不写死本地路径，例如不能假设 `bam.config.js` 一定在固定目录。
- 不写死项目配置格式，例如更新 `services` 前要先观察已有风格。
- 不写死输出格式，除非这个格式本身就是团队约定。
- 遇到多个候选项或无法判断时，要引入 Human-in-the-Loop。
- 重要 Skill 要保留测试样例，验证正例、反例和边界场景。
- Skill 的 `description` 要能准确触发，也要避免和其他团队 Skill 抢触发。

房产 Skills 管理的完整规范可以参考本地文档：`/Users/bytedance/Desktop/fc/person-project/baoyu-skills/房产 Skills 管理指南.pdf`

## 附录：参考资料

| 资源 | 你可获得什么 |
| --- | --- |
| [Agent Skills](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/overview) | 官方概念介绍，适合理解 Skills 的基本模型 |
| [技能编写最佳实践](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/best-practices) | 官方编写建议，适合校验 `SKILL.md` 和 `description` 的质量 |
| [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Anthropic 工程博客，适合理解 Skills 为什么采用文件系统和渐进式披露 |
| [Introduction to Claude Skills](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) | 入门教程，适合快速了解 Skill 的创建和使用方式 |
| `skill-creator` 详解：`/Users/bytedance/Desktop/fc/person-project/skills` | 本地 Skill 生成工具参考 |
| `baoyu-skills` 详解：`/Users/bytedance/Desktop/fc/person-project/baoyu-skills` | 当前项目中的 Skills 实践材料 |
| [Harness 101 + Skills 101](https://my.feishu.cn/sync/Al7fdhQBqssP3Fb7uNkczV3Cnse) | 内部分享资料，可作为补充阅读 |
