## 1. Prompt 为什么会越写越长

很多人第一次把 Agent 用顺手，都会经历一个阶段：Prompt 越写越长。

一开始只是几句话：帮我整理一下周报、检查一下代码、总结一下新闻。后来为了让结果更稳定，我们开始往里面加背景、模板、规则、示例、团队术语、注意事项。再后来，这段 Prompt 已经不像指令，更像一个被临时拼起来的小型知识库。

问题也从这里开始。

它太长，不适合每次都贴；它太杂，模型容易被无关信息干扰；它太隐性，别人不知道哪一段是流程，哪一段是资料，哪一段是必须遵守的规则。

但团队里很多事情又确实不是一次性的。周报、发版检查、代码审查、接口更新、资讯日报，这些任务都有相对稳定的流程，也仍然需要 Agent 理解上下文、判断重点和组织表达。

这时我们需要的，不是把 Prompt 再写长一点，也不是把长 Prompt 换个地方保存起来，而是一种新的组织方式：

* Agent 平时只需要知道“有哪些能力可以用”。
* 用户请求命中某类任务时，再加载对应的主流程。
* 真正用到模板、参考资料、示例或脚本时，再继续往下读。

这就是 Skills 的核心思路。它表面上解决了 Prompt 难复用的问题，但更底层解决的是上下文管理问题：能力可以越来越多，但不必一次性全部塞进 Context Window。

所以，理解 Skill 的关键，不是把它看成“保存下来的 Prompt”，而是把它看成一组可被 Agent 发现、选择、加载和执行的能力结构。

## 2. 什么是 Skill

顺着上面的问题，我们先给一个工作定义：

> Skill 是一份可复用的、带元数据的 Agent 能力包。

这句话不长，但刚好对应前面说的那组结构：它要能跨任务复用，要能被 Agent 发现，要能打包流程和资源，还要能按需加载。拆开看，就是四层意思：可复用、带元数据、能力包、按需加载。

### 2.1 可复用

Skill 不绑定某一次对话，也不绑定某一个用户。它沉淀的是一类任务的做法：只要用户请求命中适用场景，Agent 就应该能把它拿出来用。

这和把一段 Prompt 贴在聊天框里不一样。Prompt 很容易散落在不同对话、不同文档、不同人的收藏夹里；Skill 更像一份团队级作业规程，可以跨会话、跨项目、跨 Agent 复用。

### 2.2 带元数据

每个 Skill 都有一段结构化的 Frontmatter，至少包含 `name` 和 `description`。这段元数据不是写给人看的简介，而是写给 Agent 的触发入口。

例如：

```yaml
---
name: pdf-processing
description: 从 PDF 文件中提取文本和表格、填充表单和合并文档。在处理 PDF 文件或用户提及 PDF、表单或文档提取时使用。
---
```

Agent 启动时通常只会先看到这些轻量元数据，再根据用户请求判断要不要加载某个 Skill。也就是说，一个 Skill 写得好不好用，一部分在正文，另一部分就在 `description` 这几十到几百个字里。

`description` 写得太泛，Agent 可能不知道什么时候该用；写得太窄，用户换个说法就可能触发不了；写得和其他 Skill 太像，又容易抢触发。

### 2.3 能力包

这是最容易被低估的一点：Skill 不只是一段 Prompt，也不只是一个 `SKILL.md`。

一个典型 Skill 可以长这样：

```text
pdf/
├── SKILL.md              # 主要说明（触发时加载）
├── FORMS.md              # 表单填充指南（根据需要加载）
├── reference.md          # API 参考（根据需要加载）
├── examples.md           # 使用示例（根据需要加载）
└── scripts/
    ├── analyze_form.py   # 实用脚本（执行，不加载）
    ├── fill_form.py      # 表单填充脚本
    └── validate.py       # 验证脚本
```

`SKILL.md` 负责告诉 Agent 主流程：什么时候用、怎么做、遇到分支怎么判断、需要读哪些资源、需要调用哪些脚本。

但长模板、参考文档、示例数据和可执行脚本，不应该都塞进 `SKILL.md`。它们可以拆到对应目录里：

* `references/`：领域知识、API 说明、业务术语、规则文档。
* `templates/`：周报模板、故障报告模板、PRD 骨架、固定输出结构。
* `examples/`：示例输入输出、历史优秀样例、few-shot 材料。
* `scripts/`：抓取、去重、校验、转换、统计等确定性步骤。

正文给出“怎么想”，附带资源给出“怎么做”。这就是为什么 Skill 更像一个能力包，而不是一段被保存下来的 Prompt。

![把额外资料拆到独立文件](https://platform.claude.com/docs/images/agent-skills-bundling-content.png)

`SKILL.md` 只保留入口和主流程，进阶参考、表单规则等内容通过文件链接按需读取。

### 2.4 按需加载

Skill 遵循 Progressive Disclosure，也就是渐进式披露：元数据常驻上下文，`SKILL.md` 在触发时加载，附带资源在真正需要时再读取或执行。

官方文档把 Skill 内容分成三个加载级别：

| 加载级别 | 什么时候加载 | 典型内容 | 上下文成本 |
| --- | --- | --- | --- |
| 第一级：元数据 | Agent 启动时 | `name` 和 `description` | 很低，通常只是短描述。 |
| 第二级：主说明 | Skill 被触发时 | `SKILL.md` 正文 | 只在命中任务后进入上下文。 |
| 第三级：资源和代码 | 任务确实需要时 | `references/`、`templates/`、`examples/`、`scripts/` | 未使用时不消耗上下文；脚本通常只返回执行结果。 |

PDF Skill 的例子很直观：

1. Agent 启动时，只知道有一个 PDF Processing Skill，能处理 PDF 提取、表单、合并等任务。
2. 用户说：“从这个 PDF 中提取文本并总结。”
3. Agent 判断请求命中 PDF Skill，于是读取 `pdf-skill/SKILL.md`。
4. Agent 发现当前任务不需要填写表单，所以不读取 `FORMS.md`。
5. Agent 按 `SKILL.md` 里的主流程完成文本提取和总结。

这个例子说明：能力可以很完整，但当前任务不需要的部分不进入上下文。

`scripts/` 也属于第三级资源。表单字段提取、PDF 校验、批量转换这类确定性步骤，可以让 Agent 在需要时执行脚本，并只把运行结果带回上下文。

![Skills 如何逐层进入上下文窗口](https://platform.claude.com/docs/images/agent-skills-context-window.png)

Agent 启动时只看到各个 Skill 的短描述；真正命中任务后，才读取 `SKILL.md`，再按需读取额外文件。

所以按需加载不是一个“省 token 的小技巧”，而是 Skill 能规模化的前提。Agent 可以同时知道很多 Skill 的存在，却不会被每个 Skill 的完整正文、模板、参考资料和脚本淹没。



## 3. Skill 不是万能抽屉

我一开始很容易把所有“想复用的东西”都往 Skill 里放。后来发现这样也会出问题。

Skill 最适合的是这类任务：

* 会反复出现。
* 有稳定流程或模板。
* 需要团队上下文。
* 相关资料太多，不适合每次都塞进 Prompt。
* 执行时仍然需要模型判断。
* 无法完全用脚本或工具替代。

反过来，下面这些情况就不太适合：

* 只是一次性任务。
* 完全确定性的计算或转换。
* 只是想保存一段资料，但没有明确的做事意图。
* 需求边界还很模糊，人自己都没形成稳定流程。
* 需要强实时状态、权限治理或事务一致性。

我现在会用一个简单问题做判断：

> 如果下次再遇到同类任务，我希望 Agent 常驻的是一整段长说明，还是只常驻入口，再按需加载细节？

如果需要的是一套流程，而且相关资料会越来越多，就可以考虑 Skill。如果只是资料，放文档或知识库可能更合适。如果是稳定动作，写 Script 或 Tool 可能更合适。



## 4. Skill 和 Prompt、Tool、Script、Hook 的边界

![Prompt、Skill、Tool、Script、Hook 的区别](https://qn.huat.xyz/mac/202605180112906.png)

几个概念放在一起看会更清楚。

| 类型 | 更适合什么 | 我的理解 |
| --- | --- | --- |
| Prompt | 一次性临时任务 | 轻便，但不适合长期复用。 |
| Skill | 可复用、需要判断、上下文较重的工作流 | 让 Agent 先发现能力，再按需加载流程和资料。 |
| Tool | 明确外部能力调用 | 查数据库、发请求、操作服务。 |
| Script | 确定性计算或机械步骤 | 校验、转换、统计、批处理。 |
| Hook | 固定时机触发 | 保存后格式化、提交前检查、启动前更新。 |

一个实用判断是：

* 如果只是问这一次，用 Prompt。
* 如果以后会反复做，用 Skill。
* 如果必须稳定执行，用 Tool 或 Script。
* 如果必须在固定时机自动发生，用 Hook。

Skill 最有价值的地方，是把“上下文按需加载”“模型判断”和“工程约束”放在一起。元数据负责发现，文档负责沉淀规则，模型负责理解和生成，脚本负责稳定执行。



## 5. 如何写好一个 Skill

写 Skill 时，我会先把它当成“写给 AI 的工作说明书”，而不是写给人看的使用文档。

这也是为什么我比较推荐用 `skill-creator` 来生成和优化 Skill。原因不是“AI 写得一定更好”，而是 Skill 本来就是写给 Agent 执行的说明书。让 Agent 参与编写，会更容易暴露触发条件、执行步骤、资源拆分和边界问题。

但这不代表人可以把需求丢给 AI 就不管了。人最重要的责任，是把目标、边界、输入输出和验收标准说清楚。

### 5.1 先把任务讲清楚

不要只说“帮我写一个代码规范 Skill”。这类输入太短，Agent 只能靠猜，很容易生成一份看起来完整、实际很泛的 Skill。

更好的方式，是把任务目标、工作方法、约束和产物要求一起交代清楚：

```markdown
/skill-creator 帮我实现一个技能，根据当前仓库的现有代码，提取出典型的团队代码风格：

1. 首先，通过文件树摸清这个仓库的主要编程语言，然后 propose 几个你认为最重要的文件。
2. 被挑选出的文件个数不能低于 3 个或多于 10 个。
3. 这些文件应该足以了解团队代码的基本风格，并尽可能覆盖不同编程语言、不同架构层，例如配置、数据访问、API 暴露、Thrift 定义等。
4. 提取团队代码在文件夹、文件、方法、成员、类型命名上的规律，细致到例如分页器参数如何命名。
5. 作为 Coding Agent，你应该比团队还要更加了解自己的代码风格，不要事无巨细列出大家都知道的 rules。
6. 总结为简明扼要、方便 AI 理解而不是人类理解的 Markdown 文档：docs/code-convention.md。
```

这个版本把目标、范围、方法、约束和验收标准都讲清楚了。

### 5.2 再让 AI 生成第一版

需求讲清楚后，再让 `skill-creator` 生成第一版 Skill。这里先不要急着追求完美，第一版的价值是把任务结构跑出来：`description` 怎么写、`SKILL.md` 怎么组织、哪些内容可能要拆出去、哪些步骤应该脚本化。

我通常会按这个流程走：

```text
明确任务
  ↓
描述目标、边界和输入输出
  ↓
生成第一版 Skill
  ↓
检查 description
  ↓
检查 SKILL.md 是否只放主流程和加载指引
  ↓
拆分 references/templates/examples/scripts
  ↓
用真实任务测试
  ↓
根据失败点迭代
```

这条链路和后面的 `ai-news-daily-report` 案例是对应的：先澄清需求，再生成初版，然后用真实数据跑一遍，最后根据失败点做异常处理、配置项和脚本优化。

### 5.3 该拆就拆，但不要滥用拆分

如果生成出来的 `SKILL.md` 太长，可以直接让它重构：

```markdown
当前 SKILL.md 太长了，缺乏 progressive-disclosure 机制。请在不滥用拆分的前提下，把长模板、长示例、参考资料和复杂分支拆到 references/templates/examples/scripts 中。
```

这里的重点是“不滥用”。简单 Skill 可以只有一个 `SKILL.md`；复杂 Skill 才需要把参考资料、模板、示例和脚本拆出去。拆分的目的不是让目录看起来漂亮，而是减少上下文负担，让 Agent 在需要时再读取细节。

### 5.4 机械步骤优先脚本化

如果有机械式步骤，也可以继续要求：

```markdown
Skill 里可以机械式执行的部分，请优先用 Python 或 Node.js 脚本实现，并提供清晰的 CLI 参数说明。
```

格式转换、数据校验、批量统计、接口请求、RSS 抓取这类步骤，越确定，越应该从 Prompt 里剥离出来。自然语言负责说明意图，脚本负责稳定执行。

### 5.5 保留 Human-in-the-Loop

好的 Skill 不等于全自动。当任务需要用户确认目标、选择范围、补充上下文或做关键决策时，应该明确要求 Agent 停下来问人。

比如后面的 `ai-news-daily-report`，信源、时间范围、输出格式、是否启用人工确认，都应该在初期澄清；`ls-house-updating-bam` 里如果发现多个 `bam.config.js`，也不应该让 Agent 自行猜测，而是让用户选择。



## 6. 案例一：ai-news-daily-report 怎么长出来的

先简单介绍一下这个 Skill 是什么。它现在在仓库里对应的是 `ai-news-briefing`：一个用来生成 AI 资讯日报或周报的 Skill。你给它 OPML/RSS 信源，或者直接使用内置的默认信源，它会先抓取最近一段时间的 AI 资讯，再做基础清洗、语义去重、重要性排序和主题分类，最后输出一份中文 Markdown 简报。

换句话说，它不是一个“帮我总结新闻”的 Prompt，而是把一整套 AI 资讯整理流程封装成可复用能力：哪些信源要读、最近多久算有效、重复报道怎么合并、哪些新闻更重要、最终 Markdown 长什么样，都被写进 Skill 的规则、配置和脚本里。人只需要发起任务和补充偏好，Agent 负责按这套流程稳定执行。

`ai-news-daily-report` 是一个重量级 Skill。它的目标不是“总结几条 AI 新闻”，而是把 AI 资讯的收集、清洗、筛选、排序和生成简报这条链路沉淀下来。

这个任务一开始看起来只是内容生产，但真正跑起来会发现，它更像一个小型数据处理流程：

* 信源分散，来自 RSS、Newsletter、博客、媒体和社区。
* 重复内容多，同一条新闻会被多个来源转载。
* 不是所有新闻都值得进入日报。
* 不同人整理出来的格式和粒度不一致。
* 某些 RSS 源会失效，网络请求也会失败。

所以这个 Skill 最终要做到：

* 支持 OPML、RSS 或默认信源配置。
* 自动抓取最近资讯。
* 对内容去重、分类和排序。
* 输出结构稳定的中文 Markdown 简报。
* 配置不清楚时主动询问用户。
* 某个信源失败时不要让整个流程中断。

### 6.1 第一版，不急着写代码

第一步不是让 Agent 直接写脚本，而是先把目标讲给 `skill-creator`。

![告诉 skill-creator 需要生成 AI 资讯 Skill](https://qn.huat.xyz/mac/202605172343386.png)

这里最重要的是把“新闻摘要”提升成“可按需加载的 AI 资讯能力”。也就是说，任务不只是摘要，还包括抓取、去重、排序、分类和稳定输出；而这些规则、模板和脚本不应该每次都挤在一段 Prompt 里。

### 6.2 让 Agent 追问，而不是让它猜

复杂 Skill 里最危险的事情，是需求还没说清楚，Agent 已经开始替你做决定。

所以 `skill-creator` 追问信源、时间范围、输出格式、人工确认点时，这一步不能省。

![回答 AI 的问题，补充需求边界](https://qn.huat.xyz/mac/202605172344742.png)

第一轮回答后，Agent 还会继续问默认值、异常处理和输出约束。

![继续回答第二批问题](https://qn.huat.xyz/mac/202605172345613.png)

这些问题看起来琐碎，但它们决定了 Skill 未来能不能稳定触发、按需加载和复用。比如默认抓取最近几天，失败信源是否跳过，是否支持日报和周报，是否限制最大文章数。

### 6.3 结构开始成型

这个 Skill 不适合只写一个超长 `SKILL.md`。更合理的结构是：

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

这里的分层很关键：

* `SKILL.md` 放主流程。
* `references/` 放信源选择和排序规则。
* `templates/` 放简报格式。
* `examples/` 放示例输出。
* `scripts/` 放抓取、去重、排序这些确定性步骤。

这样做的好处不是目录看起来更工程化，而是 Agent 在生成普通日报时不用读取所有排序细则、示例和脚本源码。它只在任务需要时继续往下读。

### 6.4 第一次真实运行，问题马上出现

Skill 生成之后，最重要的不是看目录结构漂不漂亮，而是立刻跑一次真实任务。

第一次运行就暴露了问题：部分订阅源不可用，抓取结果不稳定。

![运行后发现部分订阅源不可用](https://qn.huat.xyz/mac/202605180112529.png)

这类问题如果只修一个 URL，下次还会出现。真正要修的是 Skill 的韧性。

所以第一轮优化应该包括：

* 失效 RSS 源跳过处理。
* 抓取请求增加超时和重试。
* 输出成功和失败的信源摘要。
* 保留可读错误信息，方便后续维护。
* 避免一个信源失败导致整个日报失败。

![第一次优化：多方面增强](https://qn.huat.xyz/mac/202605172347103.png)

### 6.5 后续优化开始关注体验

第一轮优化解决“能不能跑完”。第二轮就该看“跑出来的东西好不好用”。

![第二次优化](https://qn.huat.xyz/mac/202605172348216.png)

这时候要检查：

* 输出内容是否稳定。
* 排序和去重是否符合预期。
* Markdown 是否适合直接阅读和转发。
* 脚本参数是否容易理解。
* 常用参数是否应该沉淀成默认配置。

配置项也会在这个阶段变得重要。

![配置项优化](https://qn.huat.xyz/mac/202605172348265.png)

比如默认信源、默认时间范围、输出路径、最大文章数量、是否启用摘要分类排序、是否在运行前确认配置。

后面又做了并行抓取优化。

![并行抓取优化](https://qn.huat.xyz/mac/202605172349574.png)

并发抓取这种事情，就不要让模型每次临场发挥了。它是确定性工程逻辑，应该放到脚本里，通过 CLI 参数控制。

### 6.6 这个案例给我的判断

`ai-news-daily-report` 真正说明的是：复杂 Skill 通常不是一次生成出来的，而是在真实运行中长出来的。它也说明了为什么 progressive disclosure 重要：复杂任务的上下文一定会膨胀，关键是把它拆成 Agent 能逐层读取的结构。

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
形成可按需加载的可复用能力
```

![ai-news-daily-report 的演进路径](https://qn.huat.xyz/mac/202605180113545.png)

我会把这个案例记成三句话：

* 外部依赖越多，越要真实测试。
* 机械步骤越多，越要脚本化。
* 需求越复杂，越要把 Human-in-the-Loop 提前设计进去。

## 7. 案例二：ls-house-updating-bam 为什么反而很轻

`ls-house-updating-bam` 是另一个方向。它是轻量级业务 Skill，用来自动化前端项目中的 BAM 接口更新流程。

这个案例有意思的地方在于：它没有复杂目录。

```text
ls-house-updating-bam/
└── SKILL.md
```

但它仍然是一个好 Skill，因为它的业务边界很清楚。

它的 `description` 写得很具体：

```yaml
name: ls-house-updating-bam
description: 当用户需要更新或同步 BAM (API 管理平台) 接口定义时使用。触发条件包括提到 "bam update"、"更新一下 bam" 或粘贴包含 "cloud.bytedance.net/bam/rd/" 的 BAM 链接。这个技能将自动探测项目中的 bam.config.js 位置，解析链接中的 PSM 和版本号，更新配置文件，并在正确目录下执行 bam 命令来拉取最新接口文件。
```

它的主流程也很明确：

* 用户提供 BAM 链接时，解析 PSM、版本号或分支名，更新 `bam.config.js`，再执行 `npx bam update`。
* 用户只说“更新一下 bam”时，先找项目里的 `bam.config.js`，再在正确目录执行命令。
* 如果项目里有多个 `bam.config.js`，让用户选择。
* 修改 `services` 配置前，先观察当前文件风格，保持短服务名、完整 PSM、字符串值或对象值等写法一致。

这个案例提醒我：不要为了看起来工程化而过度拆分。

有些 Skill 的价值不是复杂，而是把一段业务 SOP 写准。能用一个清晰的 `SKILL.md` 解决问题，就没有必要强行加 `references/`、`templates/` 和 `scripts/`。

## 8. 测试 Skill，不要只看它“能跑”

Skill 写完后，我会至少做三类检查：

1. 它会不会被正确触发。
2. 触发后能不能稳定完成任务。
3. 失败后能不能定位原因并迭代。

### 8.1 触发测试

`description` 写得准不准，要靠测试验证。

| 类型 | 目的 | 示例 |
| --- | --- | --- |
| 正向触发 | 用户明确需要这个 Skill | “帮我根据这些 RSS 生成一份 AI 日报。” |
| 模糊触发 | 用户没说 Skill 名，但表达了对应意图 | “帮我整理一下今天 AI 圈重要新闻。” |
| 反向触发 | 相似任务但不该使用这个 Skill | “帮我写一篇 AI 科普文章。” |
| 冲突触发 | 多个 Skill 都可能命中 | “帮我整理资料并写成公众号文章。” |

正向触发失败，优先改触发场景。反向触发误命中，优先补充排除边界。

### 8.2 执行测试

执行测试看的是 `SKILL.md` 够不够清楚：

* Agent 是否按步骤执行。
* 是否漏读必要资源。
* 是否在关键节点问用户。
* 是否把机械任务交给脚本。
* 输出格式是否稳定。
* 异常输入有没有处理方式。

如果触发了但执行差，多半是主流程写得不够清楚。

### 8.3 失败归因

Skill 不好用时，我会按这个方向排查：

| 现象 | 可能原因 | 优先修改 |
| --- | --- | --- |
| 没触发 | `description` 太模糊 | 改触发场景。 |
| 误触发 | 缺少排除边界 | 增加 Do not use。 |
| 执行差 | 主流程不清楚 | 改 `SKILL.md`。 |
| 上下文太长 | 缺少渐进披露 | 拆资源文件。 |
| 输出不稳定 | 缺少模板或示例 | 加 `templates/`、`examples/`。 |
| 步骤漏执行 | 机械流程靠模型记忆 | 加 `scripts/`。 |
| 用户体验差 | 关键节点没有确认 | 加 Human-in-the-Loop。 |

## 9. 团队里怎么管理 Skills

个人用 Skill，最重要的是顺手。团队用 Skill，最重要的是一致。

房产业务已经在探索一种更接近 npm 依赖管理的方式：统一仓库管理、统一发布到 Skills Hub，并在业务项目中通过 lock 文件锁定版本。

![团队 Skills 的落地与消费链路](https://qn.huat.xyz/mac/202605180113965.png)

如果 Skills 都散落在个人本地，很快会遇到这些问题：

* 不同人安装的版本不一致。
* SOP 更新后很难同步到所有项目。
* 安装太多 Skill 后，模糊指令容易误触发。
* 项目缺少类似 `package.json` 的依赖声明。
* Skill 质量不可控，容易变成专人专用。

所以团队落地需要把 Skills 收敛到统一仓库，并通过 `skills-lock.json` 控制依赖来源和版本。

房产团队的 Skills 和 CLI 统一沉淀在团队仓库中：

* Skills 仓库：`https://code.byted.org/life_service/fangchan-cli-repo`
* Skills Hub 空间：`https://skills.bytedance.net/space/skills.byted.org%2Flife_service%2Ffangchan`

仓库结构大致是：

```text
fangchan-cli-repo/
├── packages/
│   ├── d2c-cli
│   ├── docs-cli
│   └── icons-cli
├── skills/
│   ├── d2c-diff-workflow
│   ├── doc-cli
│   └── ...
├── AGENTS.md
└── README.md
```

业务项目安装 Skill 后，会生成或更新 `skills-lock.json`：

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

这里的 `computedHash` 就像版本锁，确保团队成员和 AI 使用的是同一份能力。

安装示例：

```bash
# 安装内场 skills CLI
npm i skills -g --registry=https://bnpm.byted.org

# 从团队仓库下载 Skill
npx skills add code.byted.org:life_service/fangchan-cli-repo --skill ls-house-updating-bam

# 从 Skills Hub 下载指定版本
skills add skills.byted.org/life_service/fangchan --skill ls-house-updating-bam --version 1.0.3 -y
```

和 `node_modules` 类似，本地安装出来的 Skills 文件夹更像构建产物，不建议提交。业务项目应该提交的是 `skills-lock.json`。





## 最后

我现在更愿意把 Skill 看成一种团队经验的封装方式。

Prompt 解决的是“这次怎么让 Agent 做对”。Skill 进一步解决的是：当这类经验、模板、资料和脚本越来越多时，Agent 能不能先发现能力，再只加载当前任务真正需要的部分。

所以它值得沉淀的，不只是复用同一套流程，更是用一种可控的方式管理上下文。



## 参考资料

| 资源 | 你可获得什么 |
| --- | --- |
| [Agent Skills](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/overview) | 官方概念介绍，适合理解 Skills 的基本模型。 |
| [技能编写最佳实践](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/best-practices) | 官方编写建议，适合校验 `SKILL.md` 和 `description` 的质量。 |
| [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Anthropic 工程博客，适合理解 Skills 为什么采用文件系统和渐进式披露。 |
| [Introduction to Claude Skills](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) | 入门教程，适合快速了解 Skill 的创建和使用方式。 |
| `skill-creator` 详解：`/Users/bytedance/Desktop/fc/person-project/skills` | 本地 Skill 生成工具参考。 |
| `baoyu-skills` 详解：`/Users/bytedance/Desktop/fc/person-project/baoyu-skills` | 当前项目中的 Skills 实践材料。 |
| [Harness 101 + Skills 101](https://my.feishu.cn/sync/Al7fdhQBqssP3Fb7uNkczV3Cnse) | 内部分享资料，可作为补充阅读。 |
