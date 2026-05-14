---
name: baoyu-translate
description: 在语言之间翻译文章和文档，提供三种模式——快速（直接翻译）、普通（先分析后翻译）和精细（分析、翻译、审校、润色）。支持通过 EXTEND.md 自定义术语表和术语一致性。当用户要求"translate"、"翻译"、"精翻"、"translate article"、"translate to Chinese/English"、"改成中文"、"改成英文"、"convert to Chinese"、"localize"、"本地化"或需要任何文档翻译时使用。也会在"refined translation"、"精细翻译"、"proofread translation"、"快速翻译"、"快翻"、"这篇文章翻译一下"或提供 URL/文件并带有翻译意图时触发。
version: 1.59.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-translate
    requires:
      anyBins:
        - bun
        - npx
---

# 翻译器

三模式翻译技能：**快速**用于直接翻译，**普通**用于基于分析的翻译，**精细**用于完整的出版级工作流程（含审校和润色）。

## 用户输入工具

当本技能需要提示用户时，按以下工具选择规则（优先级从高到低）：

1. **优先使用内置用户输入工具**，即当前代理运行时提供的工具——例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出编号的纯文本消息，要求用户针对每个问题回复所选编号/答案。
3. **批量处理**：如果工具支持单次调用中提出多个问题，则将所有适用问题合并为一次调用；如果仅支持单个问题，则按优先级顺序逐一询问。

下文中的 `AskUserQuestion` 引用是示例——在其他运行时中请替换为本地等效工具。

## 脚本目录

脚本位于 `scripts/` 子目录。`{baseDir}` = 本 SKILL.md 文件所在目录路径。解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果 `npx` 可用 → `npx -y bun`；否则建议安装 bun。将 `{baseDir}` 和 `${BUN_X}` 替换为实际值。

| 脚本 | 用途 |
|--------|---------|
| `scripts/main.ts` | CLI 入口点。默认操作将 markdown 分割为块；也支持显式的 `chunk` 子命令 |
| `scripts/chunk.ts` | `main.ts` 使用的 Markdown 分块实现，也保持兼容以支持直接调用 |

## 偏好设置（EXTEND.md）

按优先级顺序检查 EXTEND.md——找到第一个即生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-translate/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-translate/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-translate/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|--------|--------|
| 找到 | 读取、解析、应用。在会话首次使用时简要提醒："正在使用 [path] 中的偏好设置。您可以编辑 EXTEND.md 来自定义术语表、受众等。" |
| 未找到 | **必须**运行首次设置（见下方）——不要静默使用默认值 |

**EXTEND.md 支持**：默认目标语言、默认模式、目标受众、自定义术语表（内联或文件路径）、翻译风格、分块设置。

Schema：[references/config/extend-schema.md](references/config/extend-schema.md)。

### 首次设置（阻塞性）

**关键**：当找不到 EXTEND.md 时，您**必须**在任何翻译之前运行首次设置。这是一个**阻塞性**操作。

完整参考：[references/config/first-time-setup.md](references/config/first-time-setup.md)

使用 `AskUserQuestion` 在一次调用中包含所有问题（目标语言、模式、受众、风格、保存位置）。用户回答后，在选定位置创建 EXTEND.md，确认"偏好设置已保存到 [path]"，然后继续。

## 默认值

所有可配置值集中在此。EXTEND.md 覆盖这些默认值；CLI 标志覆盖 EXTEND.md。

| 设置 | 默认值 | EXTEND.md 键 | CLI 标志 | 描述 |
|---------|---------|---------------|----------|-------------|
| 目标语言 | `zh-CN` | `target_language` | `--to` | 翻译目标语言 |
| 模式 | `normal` | `default_mode` | `--mode` | 翻译模式 |
| 受众 | `general` | `audience` | `--audience` | 目标读者画像 |
| 风格 | `storytelling` | `style` | `--style` | 翻译风格偏好 |
| 分块阈值 | `4000` | `chunk_threshold` | — | 触发分块翻译的字数 |
| 分块最大字数 | `5000` | `chunk_max_words` | — | 每块最大字数 |

## 模式

| 模式 | 标志 | 步骤 | 适用场景 |
|------|------|-------|-------------|
| 快速 | `--mode quick` | 翻译 | 短文本、非正式内容、快速任务 |
| 普通 | `--mode normal`（默认） | 分析 → 翻译 | 文章、博客帖子、一般内容 |
| 精细 | `--mode refined` | 分析 → 翻译 → 审校 → 润色 | 出版级质量、重要文档 |

**默认模式**：普通（可通过 EXTEND.md `default_mode` 设置覆盖）。

**风格预设** — 控制翻译的语气和语调（独立于受众）：

| 值 | 描述 | 效果 |
|-------|-------------|--------|
| `storytelling` | 引人入胜的叙事流（默认） | 吸引读者，流畅过渡，生动措辞 |
| `formal` | 专业、结构化 | 中性语调，清晰组织，无口语化表达 |
| `technical` | 精确、文档风格 | 简洁，术语密集，极少修饰 |
| `literal` | 贴近原文结构 | 极少重组，保留源句型 |
| `academic` | 学术、严谨 | 正式语域，允许复杂从句，引用感知 |
| `business` | 简洁、结果导向 | 行动导向，高管友好，要点化思维 |
| `humorous` | 保留并适配幽默 | 机智，俏皮，在目标语言中重现喜剧效果 |
| `conversational` | 随意、口语化 | 友好，亲切，如同向朋友解释 |
| `elegant` | 文学性、精心打磨的散文 | 审美精致，节奏感强，措辞精心雕琢 |

也接受自定义风格描述，例如 `--style "poetic and lyrical"`。

**自动检测**：
- "快翻"、"quick"、"直接翻译" → 快速模式
- "精翻"、"refined"、"publication quality"、"proofread" → 精细模式
- 其他 → 默认模式（普通）

**升级提示**：普通模式完成后，显示：
> 翻译已保存。如需进一步审校和润色，请回复"继续润色"或"refine"。

如果用户回复，则对已有输出继续执行审校 → 润色步骤（与精细模式 refined-workflow.md 中的步骤 4-6 相同）。

**受众预设**：

| 值 | 描述 | 效果 |
|-------|-------------|--------|
| `general` | 普通读者（默认） | 通俗语言，对术语添加更多译注 |
| `technical` | 开发者/工程师 | 对常见技术术语减少注释 |
| `academic` | 研究人员/学者 | 正式语域，精确术语 |
| `business` | 商务人士 | 商务友好语调，解释技术概念 |

也接受自定义受众描述，例如 `--audience "AI感兴趣的普通读者"`。

## 工作流程

### 步骤 1：加载偏好设置

1.1 检查 EXTEND.md（见上方偏好设置部分）

1.2 如果可用，加载语言对的内置术语表：
- EN→ZH：[references/glossary-en-zh.md](references/glossary-en-zh.md)

1.3 合并术语表：EXTEND.md `glossary`（内联）+ EXTEND.md `glossary_files`（外部文件，路径相对于 EXTEND.md 位置）+ 内置术语表 + `--glossary` 文件（CLI 覆盖所有）

### 步骤 2：物化来源与创建输出目录

物化来源（文件原样使用，内联文本/URL → 保存到 `translate/{slug}.md`），然后创建输出目录：`{source-dir}/{source-basename}-{target-lang}/`。如果未指定 `--from`，则检测源语言。

完整详情：[references/workflow-mechanics.md](references/workflow-mechanics.md)

**输出目录内容**（所有中间和最终文件都在此）：

| 文件 | 模式 | 描述 |
|------|------|-------------|
| `translation.md` | 所有 | 最终翻译（始终使用此名称） |
| `01-analysis.md` | 普通、精细 | 内容分析（领域、语调、术语） |
| `02-prompt.md` | 普通、精细 | 组装的翻译提示词 |
| `03-draft.md` | 精细 | 审校前的初始草稿 |
| `04-critique.md` | 精细 | 批判性审校发现（仅诊断） |
| `05-revision.md` | 精细 | 基于批判性审校的修订翻译 |
| `chunks/` | 分块 | 来源块 + 已翻译块 |

### 步骤 3：评估内容长度

快速模式不分块——无论长度如何直接翻译。翻译前估算字数。如果内容超过分块阈值（默认 4000 字），主动提醒："本文约 ~{N} 字。快速模式在一次通过中翻译且不分块——对于长内容，`--mode normal` 通过术语一致性产生更好的结果。"如果用户不切换则继续。

对于普通和精细模式：

| 内容 | 操作 |
|---------|--------|
| < 分块阈值 | 作为单个单元翻译 |
| >= 分块阈值 | 分块翻译（见步骤 3.1） |

**3.1 长内容准备**（普通/精细模式，仅 >= 分块阈值时）

翻译分块前：

1. **提取术语**：扫描整个文档中的专有名词、技术术语、重复短语
2. **构建会话术语表**：将提取的术语与已加载的术语表合并，建立一致的翻译
3. **分割为块**：使用 `${BUN_X} {baseDir}/scripts/main.ts <file> [--max-words <chunk_max_words>] [--output-dir <output-dir>]`
   - 解析 markdown 块（标题、段落、列表、代码块、表格等）
   - 在 markdown 块边界处分割以保持结构
   - 如果单个块超过阈值，回退到行分割，然后是词分割
4. **组装翻译提示词**：
   - 主代理读取 `01-analysis.md`（如果存在）并使用 [references/subagent-prompt-template.md](references/subagent-prompt-template.md) 的第 1 部分组装共享上下文——内联：目标风格、内容背景、合并的术语表和翻译挑战
   - 保存为输出目录中的 `02-prompt.md`（仅共享上下文，不含任务指令）
5. **通过子代理草稿翻译**（如果 Agent 工具可用）：
   - 每个块生成一个子代理，全部并行（模板的第 2 部分）
   - 每个子代理读取 `02-prompt.md` 获取共享上下文，接收块位置信息（第 N 块/共 M 块 + 其在论述中位置的简要上下文），翻译其块，保存到 `chunks/chunk-NN-draft.md`
   - 一致性通过共享的 `02-prompt.md` 保证（术语表、修辞手法映射、理解难点、源文语态和来自分析的翻译挑战）
   - 如果无块（内容低于阈值）：为整个源文件生成一个子代理
   - 如果 Agent 工具不可用，使用 `02-prompt.md` 按顺序内联翻译各块
6. **合并**：所有子代理完成后，按顺序组合已翻译的块。如果 `chunks/frontmatter.md` 存在则前置。保存为 `03-draft.md`（精细）或 `translation.md`（普通）
7. 所有中间文件（来源块 + 已翻译块）保留在 `chunks/` 中

**分块草稿合并后**，将控制权返回主代理进行批判性审校、修订和润色（步骤 4）。

### 步骤 4：翻译与精炼

**翻译原则**（适用于所有模式）：

- **重写，不是翻译**：将内容重写为自然、引人入胜的目标语言，如同一位熟练的母语作者从零撰写。质量测试："这读起来像是最初就用目标语言写的吗？"
- **准确性第一**：事实、数据和逻辑必须与原文完全一致
- **自然流畅**：使用地道的目标语言语序。将长源句拆分为更短、更自然的句子。通过意图含义解释隐喻和习语，而非逐字翻译
- **术语**：始终一致地使用标准翻译。专业术语首次出现时：在括号中标注原文
- **保留格式**：保持所有 markdown 格式（标题、粗体、斜体、图片、链接、代码块）
- **主动释义**：对于目标受众可能缺乏上下文的术语或概念，以**粗体括号** `（**解释**）`添加简洁说明。注释宜少——仅在对理解确实必要时添加
- **Frontmatter**：如果源文有 YAML frontmatter，将源元数据字段重命名为 `source` 前缀（camelCase：`url`→`sourceUrl`、`title`→`sourceTitle` 等），添加翻译值作为新的顶层字段（如果正文有 H1 则跳过 `title`），其他字段保持不变

#### 快速模式

直接翻译 → 保存到 `translation.md`。应用以上所有翻译原则。

#### 普通模式

1. **分析** → `01-analysis.md`（领域、语调、术语、翻译挑战）
2. **组装提示词** → `02-prompt.md`（带上下文、术语表、挑战的翻译指令）
3. **翻译**（遵循 `02-prompt.md`） → `translation.md`

完成后提示用户："翻译已保存。如需进一步审校和润色，请回复**继续润色**或**refine**。"

如果用户继续，则进行批判性审校 → 修订 → 润色（与下方精细模式步骤 4-6 相同），保存 `03-draft.md`（重命名当前 `translation.md`）、`04-critique.md`、`05-revision.md` 和更新后的 `translation.md`。

#### 精细模式

出版级质量的完整工作流程。详细的每步指南参见 [references/refined-workflow.md](references/refined-workflow.md)。

子代理（如在步骤 3.1 中使用）仅处理初始草稿。所有后续步骤（批判性审校、修订、润色）由主代理处理，主代理可自行决定是否委派给子代理。

步骤及保存文件（全部在输出目录中）：
1. **分析** → `01-analysis.md`（领域、语调、术语、翻译挑战）
2. **组装提示词** → `02-prompt.md`（内联上下文的翻译指令）
3. **草稿** → `03-draft.md`（带译注的初始翻译；如分块则来自子代理）
4. **批判性审校** → `04-critique.md`（仅诊断：准确性、欧化语言、策略执行、表达问题）
5. **修订** → `05-revision.md`（应用所有审校发现生成修订翻译）
6. **润色** → `translation.md`（最终出版级翻译）

每个步骤读取上一步的文件并在其基础上构建。

### 步骤 5：输出

最终翻译始终位于输出目录中的 `translation.md`。

最终翻译写入后，进行轻量级图片语言检查：

1. 从翻译文章中收集图片引用
2. 识别可能包含大量文字的图片，如封面、截图、图表、图形、框架图和信息图
3. 如果任何图片可能包含与翻译文章语言不匹配的主要文字语言，主动提醒用户
4. 提醒必须仅为列表形式。除非用户要求，不要自动本地化这些图片

提醒格式（使用文章中已有的图片语法——标准 markdown 或 wikilink）：
```text
可能需要图片本地化：
- ![example cover](attachments/example-cover.png)：可能仍包含源语言文字，而文章现在为目标语言
- ![example diagram](attachments/example-diagram.png)：可能是包含大量文字的框架图，检查标签是否需要翻译
```

显示摘要：
```
**翻译完成**（{mode} 模式）

来源：{source-path}
语言：{from} → {to}
输出目录：{output-dir}/
最终文件：{output-dir}/translation.md
应用的术语表词条：{count}
```

如果发现了语言不匹配的图片候选项，在摘要后附加简短说明告知用户某些嵌入图片可能仍需进行图片文字本地化，后跟候选列表。

## 扩展支持

通过 EXTEND.md 进行自定义配置。路径和支持的选项参见**偏好设置**部分。
