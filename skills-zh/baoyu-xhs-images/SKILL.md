---
name: baoyu-xhs-images
description: "[已弃用：请使用 baoyu-image-cards] 生成小红书图片卡片系列，支持 12 种视觉风格、8 种布局和 3 种配色方案。将内容拆分为 1-10 张卡通风格的图片卡，针对小红书互动进行优化。当用户提到"小红书图片"、"XHS images"、"RedNote infographics"、"小红书种草"、"小绿书"、"微信图文"、"微信贴图"，或需要面向中文平台的社交媒体信息图系列时使用。"
version: 1.56.2
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-xhs-images
---


# 图片卡片系列生成器

将复杂内容拆解为吸引眼球的图片卡片系列，支持多种风格选项。

## 用户输入工具

当本技能需要向用户提问时，按以下优先级选择工具：

1. **优先使用内置用户输入工具** — 即当前代理运行时暴露的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，发出带编号的纯文本消息，要求用户回复选项编号/答案。
3. **批量处理**：如果工具支持一次多问题调用，将所有适用问题合并到一次调用中；如果只支持单问题，按优先级逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例 — 在其他运行时中替换为本地等效工具。

## 图片生成工具

当本技能需要渲染图片时，按以下顺序确定后端：

1. **当前请求覆盖** — 如果用户在当前消息中指定了特定后端，使用它。
2. **保存的偏好** — 如果 `EXTEND.md` 将 `preferred_image_backend` 设为当前可用的后端，使用它。
3. **自动选择**（当偏好为 `auto`、未设置、或固定的后端不可用时）：
   - **Codex (`imagegen`)** — 首先检查你的可用技能/工具清单。如果列出了名为 `imagegen` 的技能，说明你正在 Codex 内运行，必须使用它：通过 `Skill` 工具调用，传入 `skill: "imagegen"`，传递保存的提示词文件内容（加上输出路径和宽高比，按 Codex `imagegen` 自身参数）。Codex `imagegen` 是该运行时的官方光栅后端，优先级高于任何非原生技能（如 `baoyu-imagine`），除非用户明确固定了不同的 `preferred_image_backend`。
   - **其他运行时原生工具** — 如果运行时暴露了不同的原生图片工具（如 Hermes `image_generate`），以相同方式使用它。
   - 否则，如果恰好安装了一个非原生后端（如 `baoyu-imagine`），使用它。
   - 否则（多个非原生后端且无运行时原生工具），询问用户一次 — 与其他初始问题批量合并。
4. **如果都不可用**，告知用户并询问如何继续。

**⛔ 绝不使用 SVG、HTML、canvas 或其他基于代码的渲染替代光栅图片生成。** Codex `imagegen` 自身描述说"当输出应该是位图资源而非仓库原生代码或矢量图时"应使用它。如果无法通过步骤 3 解析出光栅后端，走到步骤 4 并询问用户 — 不要静默输出 SVG、写内联 `<svg>` 标记或生成 HTML/CSS 艺术作为替代。即使文章/段落看起来"像图表"也适用：调用此规则的消费技能已经决定需要光栅图片。

设置 `preferred_image_backend: ask` 会强制每次运行都执行步骤 3 的提示，无论可用后端有哪些。用户通过下方的 `## 更改偏好` 部分更改固定后端。

**提示词文件要求（硬性）**：在调用任何后端之前，将每张图片的完整最终提示词写入 `prompts/` 下的独立文件（命名：`NN-{type}-[slug].md`）。该文件是可复现性记录，允许你在不重新生成提示词的情况下切换后端。

上述具体工具名（`imagegen`、`image_generate`、`baoyu-imagine`）仅为示例 — 在相同规则下替换为本地等效工具。

## 确认策略

默认行为：**生成前确认**。

- 将明确的技能调用、文件路径、匹配的信号/预设和 `EXTEND.md` 默认值视为**推荐输入**。它们都不授权跳过确认。
- 在用户完成步骤 2 之前**不要**开始步骤 3。
- 仅当当前请求明确要求跳过时才跳过确认，例如：`--yes`、"直接生成"、"不用确认"、"跳过确认"、"按默认出图"或等效措辞。
- 如果确认被明确跳过，在生成前的下一条用户可见更新中说明假定的策略/风格/布局/配色/数量/后端。

## 语言

在问题、进度、错误和完成摘要中使用用户的语言回复。技术标记（风格名称、文件路径、代码）保持英文。

## 选项

| 选项 | 描述 |
|--------|-------------|
| `--style <name>` | 视觉风格（见下方风格） |
| `--layout <name>` | 信息布局（见下方布局） |
| `--palette <name>` | 配色覆盖：macaron / warm / neon |
| `--preset <name>` | 风格 + 布局 + 可选配色的快捷组合（见下方预设；每个预设的提示词片段在 `references/style-presets.md`） |
| `--ref <files...>` | 参考图片，应用于图片 1 作为系列锚点 |
| `--yes` | 非交互模式：跳过所有确认，使用 EXTEND.md 或内置默认值，自动确认推荐方案（路径 A） |

## 维度

三个独立旋钮可自由组合：

| 维度 | 控制内容 | 选项 |
|-----------|----------|---------|
| **风格** | 视觉美学（线条、装饰、渲染） | 12 种风格（见下方风格） |
| **布局** | 信息结构（密度、排列） | 8 种布局（见下方布局） |
| **配色**（可选） | 颜色覆盖，替换风格的默认颜色 | macaron / warm / neon（见下方配色） |

示例：`--style notion --layout dense` 制作知识型知识卡；添加 `--palette macaron` 可柔化颜色而不改变 notion 的渲染规则。`--preset` 是风格 + 布局（+ 可选配色）的简写。

**配色行为**：无 `--palette` → 风格内置颜色；`--palette <name>` → 仅覆盖颜色，渲染规则不变。某些风格声明了 `default_palette`（如 sketch-notes 默认使用 macaron）。

## 风格（12 种）

| 风格 | 描述 |
|-------|-------------|
| `cute`（默认） | 甜美、可爱、少女风 |
| `fresh` | 清新、清爽、自然 |
| `warm` | 温馨、友好、亲切 |
| `bold` | 高冲击力、吸引注意力 |
| `minimal` | 极简、高级感 |
| `retro` | 复古、怀旧、潮流 |
| `pop` | 活力、充沛、抓眼球 |
| `notion` | 极简手绘线条风、知性 |
| `chalkboard` | 黑板上的彩色粉笔、教育风 |
| `study-notes` | 真实手写照片风，蓝笔 + 红批注 + 黄荧光笔 |
| `screen-print` | 大胆海报艺术、半调网点纹理、有限配色、符号叙事 |
| `sketch-notes` | 手绘教育信息图、马卡龙柔色暖奶油底、摇晃线条 |

每种风格的详细规格：`references/presets/<style>.md`。

## 布局（8 种）

| 布局 | 描述 |
|--------|-------------|
| `sparse`（默认） | 1-2 个要点，最大冲击力 |
| `balanced` | 3-4 个要点，标准 |
| `dense` | 5-8 个要点，知识卡风格 |
| `list` | 列举/排行（4-7 项） |
| `comparison` | 并排对比 |
| `flow` | 流程/时间线（3-6 步） |
| `mindmap` | 中心发散（4-8 个分支） |
| `quadrant` | 四象限/环形分区 |

布局规格：`references/elements/canvas.md`。

## 配色（可选覆盖）

替换风格的颜色，同时保持渲染规则（线条处理、纹理）不变。

| 配色 | 背景 | 区域颜色 | 强调色 | 感觉 |
|---------|------------|-------------|--------|------|
| `macaron` | 暖奶油 #F5F0E8 | 蓝 #A8D8EA、薰衣草 #D5C6E0、薄荷 #B5E5CF、蜜桃 #F8D5C4 | 珊瑚 #E8655A | 柔和、教育感 |
| `warm` | 柔蜜桃 #FFECD2 | 橙 #ED8936、赤陶 #C05621、金 #F6AD55、玫瑰 #D4A09A | 赭 #A0522D | 大地色系、温馨 |
| `neon` | 暗紫 #1A1025 | 青 #00F5FF、品红 #FF00FF、绿 #39FF14、粉 #FF6EC7 | 黄 #FFFF00 | 高能量、未来感 |

配色规格：`references/palettes/<palette>.md`。

## 预设（风格 + 布局快捷组合）

快速启动组合，按场景分组。使用 `--preset <name>` 或在步骤 2 中推荐。

**知识与学习**：

| 预设 | 风格 | 布局 | 最适合 |
|--------|-------|--------|----------|
| `knowledge-card` | notion | dense | 干货知识卡、概念科普 |
| `checklist` | notion | list | 清单、排行榜 |
| `concept-map` | notion | mindmap | 概念图、知识脉络 |
| `swot` | notion | quadrant | SWOT 分析、四象限 |
| `tutorial` | chalkboard | flow | 教程步骤、操作流程 |
| `classroom` | chalkboard | balanced | 课堂笔记、知识讲解 |
| `study-guide` | study-notes | dense | 学习笔记、考试重点 |
| `hand-drawn-edu` | sketch-notes | flow | 手绘教程、流程图解 |
| `sketch-card` | sketch-notes | dense | 手绘知识卡 |
| `sketch-summary` | sketch-notes | balanced | 手绘总结、图文笔记 |

**生活与分享**：

| 预设 | 风格 | 布局 | 最适合 |
|--------|-------|--------|----------|
| `cute-share` | cute | balanced | 少女风分享、日常种草 |
| `girly` | cute | sparse | 甜美封面、氛围感 |
| `cozy-story` | warm | balanced | 生活故事、情感分享 |
| `product-review` | fresh | comparison | 产品对比、测评 |
| `nature-flow` | fresh | flow | 健康流程、自然主题 |

**冲击力与观点**：

| 预设 | 风格 | 布局 | 最适合 |
|--------|-------|--------|----------|
| `warning` | bold | list | 避坑指南、重要提醒 |
| `versus` | bold | comparison | 正反对比 |
| `clean-quote` | minimal | sparse | 金句、极简封面 |
| `pro-summary` | minimal | balanced | 专业总结、商务内容 |

**潮流与娱乐**：

| 预设 | 风格 | 布局 | 最适合 |
|--------|-------|--------|----------|
| `retro-ranking` | retro | list | 复古排行、经典盘点 |
| `throwback` | retro | balanced | 怀旧分享 |
| `pop-facts` | pop | list | 趣味冷知识 |
| `hype` | pop | sparse | 炸裂封面、惊叹分享 |

**海报与编辑**：

| 预设 | 风格 | 布局 | 最适合 |
|--------|-------|--------|----------|
| `poster` | screen-print | sparse | 海报风封面、影评书评 |
| `editorial` | screen-print | balanced | 观点文章、文化评论 |
| `cinematic` | screen-print | comparison | 电影对比、戏剧张力 |

完整提示词片段定义：`references/style-presets.md`。

## 自动选择

将内容信号匹配到最佳组合。第一行关键词匹配即生效；如果都不匹配则回退到 `cute-share`。

| 源内容中的信号 | 风格 | 布局 | 推荐预设 |
|-------------------|-------|--------|--------------------|
| beauty, fashion, cute, girl, pink | `cute` | sparse/balanced | `cute-share`, `girly` |
| health, nature, fresh, organic | `fresh` | balanced/flow | `product-review`, `nature-flow` |
| life, story, emotion, warm | `warm` | balanced | `cozy-story` |
| warning, important, must, critical | `bold` | list/comparison | `warning`, `versus` |
| professional, business, elegant | `minimal` | sparse/balanced | `clean-quote`, `pro-summary` |
| classic, vintage, traditional | `retro` | balanced | `throwback`, `retro-ranking` |
| fun, exciting, wow, amazing | `pop` | sparse/list | `hype`, `pop-facts` |
| knowledge, concept, productivity, SaaS | `notion` | dense/list | `knowledge-card`, `checklist` |
| education, tutorial, learning, classroom | `chalkboard` | balanced/dense | `tutorial`, `classroom` |
| notes, handwritten, study guide, realistic | `study-notes` | dense/list/mindmap | `study-guide` |
| movie, poster, opinion, editorial, cinematic | `screen-print` | sparse/comparison | `poster`, `editorial`, `cinematic` |
| hand-drawn, infographic, workflow, 手绘, 图解 | `sketch-notes` | flow/balanced/dense | `hand-drawn-edu`, `sketch-card`, `sketch-summary` |

## 风格 × 布局矩阵

兼容性评分（✓✓ 强烈推荐，✓ 效果好，✗ 避免）。当用户选择非默认组合时用于提示不佳匹配。

|              | sparse | balanced | dense | list | comparison | flow | mindmap | quadrant |
|--------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| cute         | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓  | ✓  | ✓  | ✓  |
| fresh        | ✓✓ | ✓✓ | ✓  | ✓  | ✓  | ✓✓ | ✓  | ✓  |
| warm         | ✓✓ | ✓✓ | ✓  | ✓  | ✓✓ | ✓  | ✓  | ✓  |
| bold         | ✓✓ | ✓  | ✓  | ✓✓ | ✓✓ | ✓  | ✓  | ✓✓ |
| minimal      | ✓✓ | ✓✓ | ✓✓ | ✓  | ✓  | ✓  | ✓  | ✓  |
| retro        | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓  | ✓  | ✓  | ✓  |
| pop          | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓✓ | ✓  | ✓  | ✓  |
| notion       | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| chalkboard   | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓✓ | ✓  |
| study-notes  | ✗  | ✓  | ✓✓ | ✓✓ | ✓  | ✓  | ✓✓ | ✓  |
| screen-print | ✓✓ | ✓✓ | ✗  | ✓  | ✓✓ | ✓  | ✗  | ✓✓ |
| sketch-notes | ✓  | ✓✓ | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓✓ | ✓  |

## 大纲策略

三种差异化方案 — 每种产生结构上不同的大纲。工作流推荐其一；路径 C 生成全部三种让用户选择。

| 策略 | 概念 | 最适合 | 结构 |
|----------|---------|----------|-----------|
| **A — 故事驱动** | 个人经历为线索，情感共鸣优先 | 测评、个人分享、蜕变 | 钩子 → 问题 → 发现 → 体验 → 结论 |
| **B — 信息密集** | 价值优先，高效信息传递 | 教程、对比、清单 | 核心结论 → 信息卡 → 优缺点 → 推荐 |
| **C — 视觉优先** | 视觉冲击为核心，极少文字 | 高颜值产品、生活方式、氛围内容 | 主图 → 细节图 → 生活场景 → 行动号召 |

## 参考图片

用户提供的参考图与内部"图片 1 作为锚点"链（步骤 3）**分开** — 它们叠加在其上。

**接收**：通过 `--ref <files...>` 或在对话中粘贴的路径。
- 文件路径 → 复制到 `refs/NN-ref-{slug}.{ext}`
- 粘贴无路径 → 要求路径，或提取风格特征作为文本回退

**使用模式**（每个参考图）：

| 使用方式 | 效果 |
|-------|--------|
| `direct` | 将文件传递给后端（通常仅用于图片 1，这样锚点通过链传播） |
| `style` | 提取风格特征并附加到每张卡的提示词正文 |
| `palette` | 提取十六进制颜色并附加到每张卡的提示词正文 |

在每张受影响卡片的提示词 frontmatter 中记录参考图：

```yaml
references:
  - ref_id: 01
    filename: 01-ref-brand.png
    usage: direct
```

生成时：验证文件存在。`usage: direct` 的图片 1 + 支持参考图的后端 → 通过后端的参考图参数传递（成为链锚点）。图片 2+ 继续使用图片 1 作为 `--ref`（按步骤 3）— 不要在其上叠加用户参考图（避免信号冲突）。对于 `style`/`palette`，在每个提示词中嵌入提取的特征。

## 文件布局

```
image-cards/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── outline-strategy-{a,b,c}.md    # 仅路径 C
├── outline.md
├── prompts/NN-{type}-{slug}.md
├── NN-{type}-{slug}.png
└── refs/                          # 仅在使用 --ref 时
```

**Slug**：2-4 个词，kebab-case。"AI 工具推荐" → `ai-tools-recommend`。冲突时追加 `-YYYYMMDD-HHMMSS`。

**备份规则**（全程适用）：覆盖任何文件前 — 源文件、大纲、提示词、图片 — 将已有文件重命名为 `<name>-backup-YYYYMMDD-HHMMSS.<ext>`。这保护用户的编辑。

## 工作流

```
- [ ] 步骤 0：加载 EXTEND.md ⛔ 阻塞（仅交互模式）
- [ ] 步骤 1：分析内容 → analysis.md
- [ ] 步骤 2：智能确认 ⚠️ 必需（路径 A / B / C）
- [ ] 步骤 3：生成图片
- [ ] 步骤 4：完成报告
```

### 步骤 0：加载 EXTEND.md ⛔ 阻塞

按顺序检查这些路径；第一个匹配即生效：

| 路径 | 作用域 |
|------|-------|
| `.baoyu-skills/baoyu-image-cards/EXTEND.md` | 项目 |
| `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-image-cards/EXTEND.md` | XDG |
| `$HOME/.baoyu-skills/baoyu-image-cards/EXTEND.md` | 用户主目录 |

- **找到** → 读取、解析、打印摘要（风格/布局/水印/语言），继续。
- **未找到 + 交互模式** → 运行首次设置（见 `references/config/first-time-setup.md`）并在做其他任何事之前保存。不要分析内容或询问风格问题直到偏好设置存在 — 这保持首次运行行为可预测。
- **未找到 + `--yes`** → 跳过设置，使用内置默认值（无水印，风格/布局自动选择，语言从内容检测）。不提问，不创建 EXTEND.md。

**EXTEND.md 键**：水印、首选风格/布局、自定义风格定义、语言偏好。Schema：`references/config/preferences-schema.md`。

### 步骤 1：分析内容 → `analysis.md`

1. 保存源文件（如果 `source.md` 存在则适用备份规则）。
2. 按 `references/workflows/analysis-framework.md` 中的深度分析框架执行：内容类型、钩子潜力、受众、互动信号、视觉机会图、滑动流。
3. 检测源语言，选择推荐图片数量（2-10）。
4. 使用上方**自动选择**表自动推荐策略 + 风格 + 布局 + 配色。
5. 将所有内容写入 `analysis.md`。

### 步骤 2：智能确认 ⚠️ 必需

**硬性门槛**：根据[确认策略](#确认策略)本步骤为必需 — 用户在此确认之前（或在当前请求中以 `--yes` / 等效措辞明确跳过）不能开始步骤 3。

目标：展示自动推荐方案并让用户确认或调整。在 `--yes` 下完全跳过此步骤 — 使用分析结果和任何 CLI 覆盖以路径 A 继续。

**确认前展示摘要**：

```
📋 内容分析
  主题：[topic] | 类型：[content_type]
  要点：[key points]
  受众：[audience]

🎨 推荐方案（自动匹配）
  策略：[A/B/C] [name]（[reason]）
  风格：[style] · 布局：[layout] · 配色：[palette or 默认] · 预设：[preset]
  图片：[N]张（封面+[N-2]内容+结尾）
  元素：[background] / [decorations] / [emphasis]
```

然后问一个问题 — 三条路径。逐字选项复制：`references/confirmation.md`。

**路径 A — 快速确认**（信任自动推荐）：使用推荐的策略 + 风格生成单个大纲 → 保存到 `outline.md` → 步骤 3。

**路径 B — 自定义**：问五个问题（策略/风格、布局、配色、数量、可选备注），推荐值预填 — 留空保持推荐值。使用用户选择生成一个大纲 → `outline.md` → 步骤 3。详见 `references/confirmation.md`。

**路径 C — 详细模式**：两次子确认。

- *步骤 2a — 内容理解*：询问卖点（多选）、受众、风格偏好（真实/专业/美学/自动）、可选上下文。更新 `analysis.md`。
- *步骤 2b — 三个大纲变体*：生成 `outline-strategy-a.md`、`outline-strategy-b.md`、`outline-strategy-c.md`。每个必须有不同结构且推荐不同风格 — 在 frontmatter 中包含 `style_reason`。页数启发：A ~4-6，B ~3-5，C ~3-4。模板：`references/workflows/outline-template.md`；frontmatter 示例在 `references/confirmation.md`。
- *步骤 2c — 选择*：问三个问题（大纲 A/B/C/混合、风格、视觉元素）。保存选定/合并的大纲到 `outline.md` → 步骤 3。

### 步骤 3：生成图片

使用确认后的大纲 + 风格 + 布局 + 配色：

**视觉一致性 — 图片 1 锚点链**：角色/吉祥物/颜色渲染在不同调用间会漂移，除非你锚定它们。先生成图片 1（封面）不使用 `--ref`，然后将图片 1 作为 `--ref` 传递给每张后续图片。这是本技能最重要的一致性技巧 — 即使后端还支持会话 ID 也不要跳过。

对每张图片（封面、内容、结尾）：

1. 将完整提示词写入 `prompts/NN-{type}-{slug}.md`，使用用户首选语言（适用备份规则）。
2. 生成：
   - **图片 1**：无 `--ref`（建立锚点）。
   - **图片 2+**：添加 `--ref <path-to-image-01.png>`。
   - PNG 文件适用备份规则。
3. 每张图片后报告进度。

**水印**（如果在 EXTEND.md 中启用）：追加到生成提示词：

```
Include a subtle watermark "[content]" positioned at [position].
The watermark should be legible but not distracting.
```

详见 `references/config/watermark-guide.md`。

**后端选择**：按顶部的图片生成工具规则 — 使用可用的，如有多个则在生成前问一次。在 `--yes` 下使用 EXTEND.md 偏好并回退到第一个可用后端。提示词文件必须在调用任何后端之前存在。

**会话 ID**（如果后端支持 `--sessionId`）：对每张图片使用 `cards-{topic-slug}-{timestamp}`；结合参考链可实现最大一致性。

### 步骤 4：完成报告

```
图片卡片系列完成！

主题：[topic]
模式：[快速 / 自定义 / 详细]
策略：[A/B/C/混合]
风格：[name]
配色：[name 或 "默认"]
布局：[name 或 "各异"]
位置：[directory]
图片：共 N 张

✓ analysis.md
✓ outline.md
✓ outline-strategy-a/b/c.md（仅详细模式）

- 01-cover-[slug].png ✓ 封面 (sparse)
- 02-content-[slug].png ✓ 内容 (balanced)
- ...
- NN-ending-[slug].png ✓ 结尾 (sparse)
```

## 内容拆分原则

| 位置 | 用途 | 典型布局 |
|----------|---------|----------------|
| 封面（图片 1） | 钩子 + 视觉冲击 | `sparse` |
| 内容（中间） | 每张一个核心价值 | `balanced` / `dense` / `list` / `comparison` / `flow` |
| 结尾（最后一张） | 行动号召 / 总结 | `sparse` 或 `balanced` |

风格 × 布局兼容性矩阵见上方**风格 × 布局矩阵**。

## 图片修改

| 操作 | 方法 |
|--------|-----|
| 编辑 | 先更新 `prompts/NN-{type}-{slug}.md`，然后使用相同会话 ID 重新生成 |
| 添加 | 指定位置，创建提示词，生成，后续文件重编号 `NN+1`，更新大纲 |
| 删除 | 删除文件，后续重编号 `NN-1`，更新大纲 |

重新生成前始终先更新提示词文件 — 它是唯一真实来源，使更改可复现。

## 参考文件

| 文件 | 内容 |
|------|---------|
| `references/confirmation.md` | 每个确认路径的逐字 AskUserQuestion 文案 |
| `references/style-presets.md` | 完整预设快捷定义 |
| `references/presets/<style>.md` | 每种风格的元素定义 |
| `references/palettes/<name>.md` | 每种配色的颜色定义 |
| `references/elements/canvas.md` | 宽高比、安全区、网格布局 |
| `references/elements/image-effects.md` | 抠图、描边、滤镜 |
| `references/elements/typography.md` | 装饰文字、标签、文字方向 |
| `references/elements/decorations.md` | 强调标记、背景、涂鸦、边框 |
| `references/workflows/analysis-framework.md` | 内容分析框架 |
| `references/workflows/outline-template.md` | 大纲模板与布局指南 |
| `references/workflows/prompt-assembly.md` | 提示词组装指南 |
| `references/config/preferences-schema.md` | EXTEND.md schema |
| `references/config/first-time-setup.md` | 首次设置流程 |
| `references/config/watermark-guide.md` | 水印配置 |

## 注意事项

- 生成失败时自动重试一次，然后再报告错误。
- 对于敏感公众人物，使用风格化卡通替代。
- 智能确认（步骤 2）为必需；详细模式添加第二次确认（2a + 2c）。

## 更改偏好

EXTEND.md 位于步骤 0 中列出的第一个匹配路径。三种更改方式：

- **直接编辑** — 打开 EXTEND.md 并更改字段。完整 schema：`references/config/preferences-schema.md`。
- **交互式重新配置** — 删除 EXTEND.md（或说"reconfigure baoyu-xhs-images preferences"/"重新配置"）。下次运行将重新触发首次设置。
- **常用单行编辑**：
  - `preferred_image_backend: auto` — 默认；运行时原生工具优先，回退到唯一已安装后端，仅在存在多个非原生时询问。
  - `preferred_image_backend: codex-imagegen` — 固定为 Codex 内置。
  - `preferred_image_backend: baoyu-imagine` — 固定为 baoyu-imagine 技能。
  - `preferred_image_backend: ask` — 每次运行确认后端。
  - `preferred_style: notion`、`preferred_layout: dense`、`preferred_palette: macaron`、`language: zh`。
  - `watermark.enabled: true` + `watermark.content: "@handle"` — 添加水印。
