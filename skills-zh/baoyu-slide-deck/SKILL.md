---
name: baoyu-slide-deck
description: 从内容生成专业的幻灯片图像。先创建带有样式指令的大纲，然后逐张生成幻灯片图像。当用户要求"创建幻灯片"、"做个演示文稿"、"生成 deck"、"slide deck"或"PPT"时使用。
version: 1.56.2
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-slide-deck
    requires:
      anyBins:
        - bun
        - npx
---

# 幻灯片生成器

将内容转化为专业的幻灯片图像。本套幻灯片专为**阅读和分享**而设计（自解释式幻灯片、逻辑化滚动流、社交媒体友好），而非现场演示——这一假设驱动了以下所有的布局和信息密度决策。

## 用户输入工具

当本技能需要提示用户时，按以下工具选择规则（优先级从高到低）：

1. **优先使用内置用户输入工具**，即当前代理运行时提供的工具——例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出编号的纯文本消息，要求用户针对每个问题回复所选编号/答案。
3. **批量处理**：如果工具支持单次调用中提出多个问题，则将所有适用问题合并为一次调用；如果仅支持单个问题，则按优先级顺序逐一询问。

下文中的 `AskUserQuestion` 引用是示例——在其他运行时中请替换为本地等效工具。

## 图像生成工具

当本技能需要渲染图像时，按以下顺序确定后端：

1. **当前请求覆盖** — 如果用户在当前消息中指定了特定后端，则使用它。
2. **已保存的偏好** — 如果 `EXTEND.md` 将 `preferred_image_backend` 设置为当前可用的后端，则使用它。
3. **自动选择**（当偏好为 `auto`、未设置或固定后端不可用时）：
   - **Codex (`imagegen`)** — 首先检查您的可用技能/工具清单。如果列出了名为 `imagegen` 的技能，则您在 Codex 中运行，必须使用它：通过 `Skill` 工具调用，传入 `skill: "imagegen"`，传递已保存的提示词文件内容（加上 Codex `imagegen` 自身参数所需的输出路径和宽高比）。Codex `imagegen` 是该运行时中官方的光栅图像后端，其优先级高于任何非原生技能（如 `baoyu-imagine`），除非用户明确固定了不同的 `preferred_image_backend`。
   - **其他运行时原生工具** — 如果运行时暴露了不同的原生图像工具（如 Hermes `image_generate`），以相同方式使用。
   - 否则，如果恰好安装了一个非原生后端（如 `baoyu-imagine`），则使用它。
   - 否则（多个非原生后端且无运行时原生工具），询问用户一次——与其他初始问题批量处理。
4. **如果都不可用**，告知用户并询问如何继续。

**⛔ 绝不用 SVG、HTML、canvas 或其他基于代码的渲染来替代光栅图像生成。** Codex `imagegen` 的描述明确说明，当"输出应为位图资源而非仓库原生代码或矢量图"时应使用它。如果您无法通过步骤 3 确定光栅后端，则执行步骤 4 并询问用户——**不要**静默输出 SVG、内联 `<svg>` 标记或生成 HTML/CSS 艺术作为替代。即使文章/章节看起来像"图表"也适用：调用此规则的消费技能已经决定需要的是光栅图像。

将 `preferred_image_backend: ask` 设置后，无论有多少可用后端，每次运行都会强制执行步骤 3 的提示。用户通过下方的 `## 更改偏好` 部分来更改固定后端。

**提示词文件要求（硬性）**：在调用任何后端之前，将每张图像的完整最终提示词写入 `prompts/` 下的独立文件（命名：`NN-slide-[slug].md`）。该文件是可重现性记录，允许您在不重新生成提示词的情况下切换后端。

上文中的具体工具名称（`imagegen`、`image_generate`、`baoyu-imagine`）是示例——按相同规则替换为本地等效工具。

## 确认策略

默认行为：**生成前确认**。

- 将显式技能调用、文件路径、匹配的信号/预设以及 `EXTEND.md` 默认值仅视为**推荐输入**。它们都不能授权跳过确认。
- 在用户完成步骤 2 之前，**不要**开始步骤 3 或之后的步骤。
- 仅当当前请求明确要求跳过确认时才跳过，例如："直接生成"、"不用确认"、"跳过确认"、"按默认出幻灯片"或等效表述。
- 如果确认被明确跳过，在生成前的下一条面向用户的更新中说明假定的样式/受众/幻灯片数量/语言/后端。

## 语言

在问题、进度报告、错误消息和完成摘要中使用用户的语言回复。技术标记（样式名称、文件路径、代码）保持英文。

## 脚本目录

`{baseDir}` = 本 SKILL.md 文件所在目录。解析 `${BUN_X}`：优先使用 `bun`；否则 `npx -y bun`；否则建议 `brew install oven-sh/bun/bun`。

| 脚本 | 用途 |
|--------|---------|
| `scripts/merge-to-pptx.ts` | 将幻灯片合并为 PowerPoint |
| `scripts/merge-to-pdf.ts` | 将幻灯片合并为 PDF |

## 选项

| 选项 | 描述 |
|--------|-------------|
| `--style <name>` | 预设（见下方预设列表）、`custom` 或自定义样式名称 |
| `--audience <type>` | beginners / intermediate / experts / executives / general |
| `--lang <code>` | 输出语言（en、zh、ja 等） |
| `--slides <N>` | 目标幻灯片数量（推荐 8-25，最大 30） |
| `--ref <files...>` | 应用于每张幻灯片的参考图像（样式/色板/构图/主题） |
| `--outline-only` | 在大纲阶段停止 |
| `--prompts-only` | 在提示词阶段停止（跳过图像生成） |
| `--images-only` | 跳到步骤 7；需要已有的 `prompts/` |
| `--regenerate <N>` | 重新生成特定幻灯片：`3` 或 `2,5,8` |

## 样式系统

17 个预设，涵盖技术/教育/生活方式/编辑类用例。每个预设是四个维度（质感/色调/排版/密度）的组合。如果用户在第 1 轮选择"自定义维度"，第 2 轮确认将对每个维度提出一个问题——选项和原文内容在 `references/confirmation.md` 中。

### 预设（17 个）

| 预设 | 维度 | 最佳用途 |
|--------|------------|----------|
| `blueprint`（默认） | grid + cool + technical + balanced | 架构、系统设计 |
| `chalkboard` | organic + warm + handwritten + balanced | 教育、教程 |
| `corporate` | clean + professional + geometric + balanced | 投资者演示、提案 |
| `minimal` | clean + neutral + geometric + minimal | 高管简报 |
| `sketch-notes` | organic + warm + handwritten + balanced | 教育、教程 |
| `hand-drawn-edu` | organic + macaron + handwritten + balanced | 教育图表、流程说明 |
| `watercolor` | organic + warm + humanist + minimal | 生活方式、健康 |
| `dark-atmospheric` | clean + dark + editorial + balanced | 娱乐、游戏 |
| `notion` | clean + neutral + geometric + dense | 产品演示、SaaS |
| `bold-editorial` | clean + vibrant + editorial + balanced | 产品发布、主题演讲 |
| `editorial-infographic` | clean + cool + editorial + dense | 技术解说、研究 |
| `fantasy-animation` | organic + vibrant + handwritten + minimal | 教育叙事 |
| `intuition-machine` | clean + cool + technical + dense | 技术文档、学术 |
| `pixel-art` | pixel + vibrant + technical + balanced | 游戏、开发者演讲 |
| `scientific` | clean + cool + technical + dense | 生物、化学、医学 |
| `vector-illustration` | clean + vibrant + humanist + balanced | 创意、儿童内容 |
| `vintage` | paper + warm + editorial + balanced | 历史、文化遗产 |

每个预设的规格：`references/styles/<preset>.md`。预设→维度映射：`references/dimensions/presets.md`。

### 维度（选择"自定义维度"时）

| 维度 | 选项 | 用途 |
|-----------|---------|---------|
| **质感** | clean、grid、organic、pixel、paper | 背景处理 |
| **色调** | professional、warm、cool、vibrant、dark、neutral、macaron | 色温 |
| **排版** | geometric、humanist、handwritten、editorial、technical | 标题/正文样式 |
| **密度** | minimal、balanced、dense | 每张幻灯片的信息量 |

完整的维度规格：`references/dimensions/*.md`。

### 自动选择

将内容信号匹配到预设。选择第一个信号关键词出现在来源中的行；如果没有匹配则回退到 `blueprint`。

| 来源中的信号 | 预设 |
|-------------------|--------|
| tutorial、learn、education、guide、beginner | `sketch-notes` |
| hand-drawn、infographic、diagram、process、onboarding | `hand-drawn-edu` |
| classroom、teaching、school、chalkboard | `chalkboard` |
| architecture、system、data、analysis、technical | `blueprint` |
| creative、children、kids、cute | `vector-illustration` |
| briefing、academic、research、bilingual | `intuition-machine` |
| executive、minimal、clean、simple | `minimal` |
| saas、product、dashboard、metrics | `notion` |
| investor、quarterly、business、corporate | `corporate` |
| launch、marketing、keynote、magazine | `bold-editorial` |
| entertainment、music、gaming、atmospheric | `dark-atmospheric` |
| explainer、journalism、science communication | `editorial-infographic` |
| story、fantasy、animation、magical | `fantasy-animation` |
| gaming、retro、pixel、developer | `pixel-art` |
| biology、chemistry、medical、scientific | `scientific` |
| history、heritage、vintage、expedition | `vintage` |
| lifestyle、wellness、travel、artistic | `watercolor` |

### 幻灯片数量启发式规则

| 来源长度 | 推荐幻灯片数 |
|---------------|--------------------|
| < 1000 词 | 5-10 |
| 1000-3000 词 | 10-18 |
| 3000-5000 词 | 15-25 |
| > 5000 词 | 20-30（考虑拆分） |

## 参考图像

用户可以提供参考图像来指导样式、色板、布局或主题。

**接收方式**：通过 `--ref <files...>` 或用户在对话中提供文件路径/粘贴图像时接收。
- 文件路径 → 复制到 `{slide-deck-dir}/refs/NN-ref-{slug}.{ext}`
- 粘贴的图像无路径 → 询问路径，或以文本方式口头提取样式特征作为回退

**使用模式**（每个参考）：

| 用途 | 效果 |
|-------|--------|
| `direct` | 将文件作为参考图像传递给后端用于每张幻灯片 |
| `style` | 提取样式特征（线条处理、质感、色调）并附加到每张幻灯片的提示词正文 |
| `palette` | 提取十六进制颜色并附加到每张幻灯片的提示词正文 |

在每张幻灯片的提示词 frontmatter 中记录参考：

```yaml
references:
  - ref_id: 01
    filename: 01-ref-brand.png
    usage: direct
```

在生成时验证文件是否存在。如果 `usage: direct` 且后端接受参考（如 `baoyu-imagine --ref`），则在每张幻灯片上传递该文件。否则将提取的 `style`/`palette` 特征嵌入提示词文本。

## 文件布局

```
slide-deck/{topic-slug}/
├── source-{slug}.{ext}
├── outline.md
├── prompts/NN-slide-{slug}.md
├── NN-slide-{slug}.png
├── {topic-slug}.pptx
└── {topic-slug}.pdf
```

**Slug**：2-4 个词，kebab-case，从主题中提取。"Introduction to Machine Learning" → `intro-machine-learning`。

**备份规则**（适用于所有步骤）：如果即将写入的文件已存在，在写入新文件前将其重命名为 `<name>-backup-YYYYMMDD-HHMMSS.<ext>`。这可以保护用户的编辑并支持回滚。

## 工作流程

复制此检查清单并在完成时逐项勾选：

```
- [ ] 步骤 1：设置与分析
- [ ] 步骤 2：确认 ⚠️ 必需（第 1 轮；仅当选择"自定义维度"时进行第 2 轮）
- [ ] 步骤 3：生成大纲
- [ ] 步骤 4：审查大纲（有条件）
- [ ] 步骤 5：生成提示词
- [ ] 步骤 6：审查提示词（有条件）
- [ ] 步骤 7：生成图像
- [ ] 步骤 8：合并为 PPTX/PDF
- [ ] 步骤 9：输出摘要
```

### 步骤 1：设置与分析

**1.1 加载 EXTEND.md** — 按以下路径顺序检查；找到第一个即生效：

| 路径 | 范围 |
|------|-------|
| `.baoyu-skills/baoyu-slide-deck/EXTEND.md` | 项目级 |
| `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-slide-deck/EXTEND.md` | XDG |
| `$HOME/.baoyu-skills/baoyu-slide-deck/EXTEND.md` | 用户主目录 |

如果找到，读取、解析并打印摘要（样式/受众/语言/审查）。如果未找到，使用默认值继续——首次设置不会阻塞本技能。Schema：`references/config/preferences-schema.md`。

**1.2 分析内容** — 遵循 `references/analysis-framework.md`：分类内容、检测语言、记录样式选择信号、根据长度估算幻灯片数量（参见上方样式系统中的**幻灯片数量启发式规则**）、生成主题 slug。将来源保存为 `source.md`（如果已存在则遵循备份规则）。

**1.3 检查已有输出** ⚠️ 步骤 2 之前必需。如果 `slide-deck/{topic-slug}/` 已存在，询问如何继续——四个选项（重新生成大纲/重新生成图像/备份并重新生成/退出），原文内容在 `references/confirmation.md` 中。

将发现保存到 `analysis.md`：主题、受众、信号、推荐样式和幻灯片数量、语言检测。

### 步骤 2：确认 ⚠️ 必需

**硬性门控**：根据[确认策略](#确认策略)，此步骤为必需——在用户此处确认（或在当前请求中以"直接生成"/等效表述明确选择退出）之前，步骤 3 及之后的步骤无法开始。

**第 1 轮（始终执行）** — 在一次 `AskUserQuestion` 调用中批量提出五个问题：样式、受众、幻灯片数量、是否审查大纲?、是否审查提示词?。原文选项在 `references/confirmation.md` 中。

问题前展示的摘要：
- 内容类型 + 主题
- 检测到的语言
- 推荐样式（基于信号）
- 推荐幻灯片数量（基于长度）

**第 2 轮（仅当第 1 轮选择"自定义维度"时）** — 批量提出四个问题：质感、色调、排版、密度。原文选项在 `references/confirmation.md` 中。四个答案将替代预设。

**确认后**：使用最终选择更新 `analysis.md`，并从 Q4/Q5 存储 `skip_outline_review` / `skip_prompt_review` 标志。

### 步骤 3：生成大纲

解析样式：预设 → `references/styles/{preset}.md`；自定义维度 → 组合 `references/dimensions/` 中的文件。从解析的样式构建 `STYLE_INSTRUCTIONS`，应用确认的受众 + 语言 + 幻灯片数量，遵循 `references/outline-template.md`，保存为 `outline.md`。

如果指定了 `--outline-only` 则在此停止。如果 `skip_outline_review` 则跳过步骤 4。

### 步骤 4：审查大纲（有条件）

展示逐张幻灯片的表格（`# | 标题 | 类型 | 布局`）以及总数和解析后的样式。询问：继续/先编辑大纲/重新生成——原文在 `references/confirmation.md` 中。

选择"先编辑大纲"时，告知用户编辑 `outline.md` 并在准备好后再次询问。选择"重新生成大纲"时，返回步骤 3。

### 步骤 5：生成提示词

对大纲中的每张幻灯片：
1. 读取 `references/base-prompt.md`
2. 从大纲中提取 `STYLE_INSTRUCTIONS`（不重新读取样式文件）
3. 添加幻灯片的内容
4. 如果指定了 `Layout:`，包含 `references/layouts.md` 中的指导
5. 保存到 `prompts/NN-slide-{slug}.md`（适用备份规则）

如果指定了 `--prompts-only` 则在此停止。如果 `skip_prompt_review` 则跳过步骤 6。

### 步骤 6：审查提示词（有条件）

展示提示词索引（`# | 文件名 | 幻灯片标题`）并询问：继续/先编辑提示词/重新生成——原文在 `references/confirmation.md` 中。分支与步骤 4 相同。

### 步骤 7：生成图像

1. 通过顶部的图像生成工具规则确定图像后端——如果安装了多个则询问一次。
2. 确认每个 `prompts/NN-slide-{slug}.md` 都存在（硬性要求；无论使用什么后端，提示词文件都是可重现性记录）。
3. 会话 ID：`slides-{topic-slug}-{timestamp}` — 仅在后端支持会话时传递。
4. 对每张幻灯片：按顺序生成，复用会话 ID。备份规则适用于 PNG 文件。报告进度为 `已生成 X/N`。失败时自动重试一次，然后再报告错误。

`--regenerate N` 仅对指定幻灯片跳到此步骤。`--images-only` 使用已有提示词从此步骤开始。

### 步骤 8：合并

```bash
${BUN_X} {baseDir}/scripts/merge-to-pptx.ts <slide-deck-dir>
${BUN_X} {baseDir}/scripts/merge-to-pdf.ts <slide-deck-dir>
```

### 步骤 9：摘要

```
幻灯片制作完成！
主题：[topic]
样式：[preset 或 "custom: texture+mood+typography+density"]
位置：[directory]
幻灯片数：N

- 01-slide-cover.png
- ...
- NN-slide-back-cover.png

大纲：outline.md
PPTX：{topic-slug}.pptx
PDF：{topic-slug}.pdf
```

## 幻灯片修改

| 操作 | 方法 |
|--------|-----|
| 编辑 | **先**更新 `prompts/NN-slide-{slug}.md`，然后 `--regenerate N` |
| 添加 | 在目标位置创建新的提示词，生成图像，对后续的 `NN` 重新编号（slug 不变），更新 `outline.md`，重新合并 |
| 删除 | 移除 PNG + 提示词，对后续重新编号，更新 `outline.md`，重新合并 |

在重新生成图像之前始终先更新提示词文件——这保证了 prompts 目录作为唯一事实来源，并使更改可重现。重新编号时只有 `NN` 变化；slug 保持稳定，因此引用仍然有效。

详情参见 `references/modification-guide.md`。

## 参考文件

| 文件 | 内容 |
|------|---------|
| `references/confirmation.md` | 每次确认时 AskUserQuestion 选项的原文内容 |
| `references/analysis-framework.md` | 内容分析框架 |
| `references/outline-template.md` | 大纲结构 |
| `references/base-prompt.md` | 图像生成的基础提示词正文 |
| `references/layouts.md` | 布局选项 |
| `references/design-guidelines.md` | 受众、排版、颜色选择 |
| `references/content-rules.md` | 内容指南 |
| `references/modification-guide.md` | 编辑/添加/删除工作流程 |
| `references/styles/<preset>.md` | 每个预设的规格 |
| `references/dimensions/*.md` | 每个维度的规格 |
| `references/config/preferences-schema.md` | EXTEND.md schema |

## 注意事项

- 图像生成每张幻灯片约需 10-30 秒；在生成之间报告进度。
- 对于敏感的公众人物，优先使用风格化替代方案以避免肖像问题。
- 当后端支持时，通过会话 ID 保持视觉一致性。

## 更改偏好

EXTEND.md 位于步骤 1.1 中列出的第一个匹配路径。两种修改方式：

- **直接编辑** — 打开 EXTEND.md 并更改字段。完整 schema：`references/config/preferences-schema.md`。
- **常见单行编辑**：
  - `preferred_image_backend: auto` — 默认；运行时原生工具优先，回退到唯一安装的后端，仅在有多个非原生后端时询问。
  - `preferred_image_backend: codex-imagegen` — 固定为 Codex 内置工具。
  - `preferred_image_backend: baoyu-imagine` — 固定为 baoyu-imagine 技能。
  - `preferred_image_backend: ask` — 每次运行都确认后端。
  - `preferred_style: blueprint`、`preferred_audience: experts`、`language: zh`。
