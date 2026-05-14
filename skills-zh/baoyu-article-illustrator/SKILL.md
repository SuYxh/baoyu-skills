---
name: baoyu-article-illustrator
description: 分析文章结构，识别需要视觉辅助的位置，通过类型 × 风格 × 配色三维方法生成插图。当用户要求"为文章配图"、"添加插图"、"生成文章图片"或 "illustrate article" 时使用。
version: 1.58.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-article-illustrator
---

# 文章配图工具

分析文章，识别配图位置，通过类型 × 风格 × 配色保持一致性来生成图片。

## 用户输入工具

当本技能需要向用户提问时，请按以下优先顺序选择工具：

1. **优先使用内置用户输入工具** — 即当前代理运行时暴露的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **降级方案**：如果没有此类工具，则输出带编号的纯文本消息，要求用户回复对应的编号/答案。
3. **批量处理**：如果工具支持每次调用多个问题，则将所有适用问题合并为一次调用；如果仅支持单个问题，则按优先顺序逐一提问。

下文中的 `AskUserQuestion` 引用仅为示例 — 在其他运行时中请替换为本地等效工具。

## 图片生成工具

当本技能需要渲染图片时，按以下顺序确定后端：

1. **当前请求覆盖** — 如果用户在当前消息中指定了特定后端，则使用该后端。
2. **已保存的偏好** — 如果 `EXTEND.md` 将 `preferred_image_backend` 设置为当前可用的后端，则使用它。
3. **自动选择**（当偏好为 `auto`、未设置或指定的后端不可用时）：
   - **Codex (`imagegen`)** — 首先检查可用技能/工具清单。如果列出了名为 `imagegen` 的技能，说明你在 Codex 环境中运行，必须使用它：通过 `Skill` 工具以 `skill: "imagegen"` 调用，传入已保存的提示词文件内容（以及按 Codex `imagegen` 自身参数要求的输出路径和宽高比）。Codex `imagegen` 是该运行时的官方光栅后端，优先级高于任何非原生技能（如 `baoyu-imagine`），除非用户已明确指定不同的 `preferred_image_backend`。
   - **其他运行时原生工具** — 如果运行时暴露了其他原生图片工具（如 Hermes `image_generate`），以相同方式使用。
   - 否则，如果恰好安装了一个非原生后端（如 `baoyu-imagine`），则使用它。
   - 否则（存在多个非原生后端且无运行时原生工具），询问用户一次 — 与其他初始问题合并提问。
4. **如果没有可用后端**，告知用户并询问如何继续。

**⛔ 绝对不要用 SVG、HTML、canvas 或其他基于代码的渲染替代光栅图片生成。** Codex `imagegen` 自身描述指出，它应在"输出应为位图资源而非仓库原生代码或矢量图"时使用。如果无法通过步骤 3 确定光栅后端，则进入步骤 4 询问用户 — **不要**悄悄输出 SVG、编写内联 `<svg>` 标记或生成 HTML/CSS 艺术作为替代。即使文章/章节看起来像"图表"也是如此：调用此规则的消费技能已经决定了需要的是光栅图片。

设置 `preferred_image_backend: ask` 将强制每次运行时都执行步骤 3 的提示，无论可用后端情况如何。用户通过下方的 `## 更改偏好` 部分更改指定的后端。

**提示词文件要求（硬性）**：在调用任何后端之前，将每张图片的完整最终提示词写入 `prompts/` 下的独立文件（命名：`NN-{type}-[slug].md`）。后端接收提示词文件（或其内容）；该文件是可复现性记录，允许你在不重新生成提示词的情况下切换后端。

上述具体工具名称（`imagegen`、`image_generate`、`baoyu-imagine`）仅为示例 — 在相同规则下替换为本地等效工具。

## 确认策略

默认行为：**生成前确认**。

- 将显式技能调用、文件路径、匹配的信号/预设以及 `EXTEND.md` 默认值视为**仅推荐输入**。它们均不授权跳过确认。
- 在用户完成步骤 3 之前，**不要**开始步骤 4 或之后的步骤。
- 仅当当前请求明确表示跳过时才跳过确认，例如："直接生成"、"不用确认"、"跳过确认"、"按默认出图"或等效措辞。
- 如果明确跳过确认，在生成前的下一次面向用户的更新中说明假定的类型/密度/风格/配色/语言/后端。

## 参考图片

用户可通过 `--ref <files...>` 或在对话中提供文件路径/粘贴图片来提供参考图片。参考图片为特定插图提供风格、配色、构图或主题指导。

完整的检测、存储和处理规则见 [references/workflow.md](references/workflow.md)（步骤 1.0 保存到 `references/NN-ref-{slug}.{ext}`；步骤 5.3 处理每个插图的用法 `direct | style | palette`）。当所选后端支持批量输入时，每个提示词文件 `references:` frontmatter 中的 `direct` 用法条目应传播到其批量载荷中，以便后端可以传递它们（例如 `baoyu-imagine` 接受每个任务的 `ref`）。

## 三个维度

| 维度 | 控制内容 | 示例 |
|------|----------|------|
| **类型** | 信息结构 | infographic, scene, flowchart, comparison, framework, timeline |
| **风格** | 渲染方式 | notion, warm, minimal, blueprint, watercolor, elegant |
| **配色** | 配色方案（可选） | macaron, warm, neon — 覆盖风格的默认颜色 |

自由组合：`--type infographic --style vector-illustration --palette macaron`

或使用预设：`--preset edu-visual` → 一个标志包含类型 + 风格 + 配色。见 [风格预设](references/style-presets.md)。

## 类型

| 类型 | 最适用于 |
|------|----------|
| `infographic` | 数据、指标、技术类 |
| `scene` | 叙事、情感类 |
| `flowchart` | 流程、工作流类 |
| `comparison` | 并列对比、选项类 |
| `framework` | 模型、架构类 |
| `timeline` | 历史、演变类 |

## 风格

见 [references/styles.md](references/styles.md) 了解核心风格、完整画廊以及类型 × 风格兼容性。

## 工作流程

```
- [ ] 步骤 1：预检查（EXTEND.md、参考图片、配置）
- [ ] 步骤 2：分析内容
- [ ] 步骤 3：确认设置（AskUserQuestion）
- [ ] 步骤 4：生成大纲
- [ ] 步骤 5：生成图片
- [ ] 步骤 6：完成
```

### 步骤 1：预检查

**1.5 加载偏好设置（EXTEND.md）⛔ 阻塞**

按优先顺序检查 EXTEND.md — 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|--------|------|------|
| 1 | `.baoyu-skills/baoyu-article-illustrator/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-article-illustrator/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-article-illustrator/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|------|------|
| 找到 | 读取、解析、显示摘要 |
| 未找到 | ⛔ 运行[首次设置](references/config/first-time-setup.md) |

完整流程：[references/workflow.md](references/workflow.md#step-1-pre-check)

### 步骤 2：分析

| 分析项 | 输出 |
|--------|------|
| 内容类型 | 技术 / 教程 / 方法论 / 叙事 |
| 目的 | 信息传达 / 可视化 / 想象 |
| 核心论点 | 2-5 个要点 |
| 位置 | 插图能增加价值的位置 |

**关键**：隐喻 → 可视化底层概念，而非字面图像。

完整流程：[references/workflow.md](references/workflow.md#step-2-setup--analyze)

### 步骤 3：确认设置 ⚠️

**硬性门槛**：根据[确认策略](#确认策略)，此步骤为必需 — 在用户确认（或在当前请求中以"直接生成"/等效措辞明确选择退出）之前，步骤 4+ 不能开始。

**一次 AskUserQuestion，最多 4 个问题。Q1-Q2 必填。除非选择了预设，否则 Q3 必填。**

| 问题 | 选项 |
|------|------|
| **Q1：预设或类型** | [推荐预设], [备选预设], 或手动选择：infographic, scene, flowchart, comparison, framework, timeline, mixed |
| **Q2：密度** | minimal（1-2）, balanced（3-5）, per-section（推荐）, rich（6+） |
| **Q3：风格** | [推荐], minimal-flat, sci-fi, hand-drawn, editorial, scene, poster, 其他 — **如果选择了预设则跳过** |
| Q4：配色 | 默认（风格颜色）, macaron, warm, neon — **如果预设包含配色或已设置 preferred_palette 则跳过** |
| Q5：语言 | 当文章语言 ≠ EXTEND.md 设置时 |

完整流程：[references/workflow.md](references/workflow.md#step-3-confirm-settings-)

### 步骤 4：生成大纲

保存 `outline.md`，包含 frontmatter（type, density, style, palette, image_count）和条目：

```yaml
## Illustration 1
**Position**: [章节/段落]
**Purpose**: [原因]
**Visual Content**: [内容]
**Filename**: 01-infographic-concept-name.png
```

完整模板：[references/workflow.md](references/workflow.md#step-4-generate-outline)

### 步骤 5：生成图片

⛔ **阻塞：提示词文件必须在任何图片生成之前保存。** 这是一个硬性要求，无论选择哪个后端 — 提示词文件是可复现性记录。

1. 为每个插图创建提示词文件，参见 [references/prompt-construction.md](references/prompt-construction.md)
2. 保存到 `prompts/NN-{type}-{slug}.md`，包含 YAML frontmatter
3. 提示词**必须**使用带有结构化部分（ZONES / LABELS / COLORS / STYLE / ASPECT）的类型专用模板
4. LABELS **必须**包含文章特定数据：实际数字、术语、指标、引言
5. **不要**在未先保存提示词文件的情况下向 `--prompt` 传递临时内联提示词
6. 通过顶部的 `## 图片生成工具` 规则选择后端：使用可用的后端；如果有多个，询问用户一次。在任何生成之前每个会话执行一次。
7. **执行策略**：当多个插图已保存提示词文件且任务仅为纯生成时，优先使用所选后端的批量接口（如果有的话），而非派生子代理。仅当每张图片仍需要单独的提示词迭代或创意探索时才使用子代理。如果后端没有批量接口，则按顺序生成。
8. 按提示词 frontmatter 处理参考图片（`direct`/`style`/`palette`）
9. 如果 EXTEND.md 启用了水印则应用水印
10. 从已保存的提示词文件生成；失败时重试一次

完整流程：[references/workflow.md](references/workflow.md#step-5-generate-images)

### 步骤 6：完成

在段落后插入 `![description]({relative-path}/NN-{type}-{slug}.png)`。路径根据输出目录设置相对于文章文件计算。

```
文章配图完成！
文章：[path] | 类型：[type] | 密度：[level] | 风格：[style] | 配色：[palette or default]
图片：X/N 已生成
```

## 输出目录

输出目录由 EXTEND.md 中的 `default_output_dir` 决定（在首次设置期间设定）：

| `default_output_dir` | 输出路径 | Markdown 插入路径 |
|----------------------|----------|-------------------|
| `imgs-subdir`（默认） | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| `same-dir` | `{article-dir}/` | `NN-{type}-{slug}.png` |
| `illustrations-subdir` | `{article-dir}/illustrations/` | `illustrations/NN-{type}-{slug}.png` |
| `independent` | `illustrations/{topic-slug}/` | `illustrations/{topic-slug}/NN-{type}-{slug}.png`（相对于 cwd） |

所有辅助文件（大纲、提示词）保存在输出目录内：

```
{output-dir}/
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```

当输入为**粘贴内容**（无文件路径）时，始终使用 `illustrations/{topic-slug}/`，并在旁边保存 `source-{slug}.{ext}`。

**Slug**：2-4 个单词，kebab-case。**冲突**：追加 `-YYYYMMDD-HHMMSS`。

## 修改

| 操作 | 步骤 |
|------|------|
| 编辑 | 更新提示词 → 重新生成 → 更新引用 |
| 添加 | 定位 → 提示词 → 生成 → 更新大纲 → 插入 |
| 删除 | 删除文件 → 移除引用 → 更新大纲 |

## 参考文件

| 文件 | 内容 |
|------|------|
| [references/workflow.md](references/workflow.md) | 详细流程 |
| [references/usage.md](references/usage.md) | 命令语法 |
| [references/styles.md](references/styles.md) | 风格画廊 + 配色画廊 |
| [references/style-presets.md](references/style-presets.md) | 预设快捷方式（类型 + 风格 + 配色） |
| [references/prompt-construction.md](references/prompt-construction.md) | 提示词模板 |
| [references/config/first-time-setup.md](references/config/first-time-setup.md) | 首次设置 |

## 更改偏好

EXTEND.md 位于步骤 1.5 中列出的第一个匹配路径。三种更改方式：

- **直接编辑** — 打开 EXTEND.md 并修改字段。完整 schema：`references/config/preferences-schema.md`。
- **交互式重新配置** — 删除 EXTEND.md（或要求"reconfigure baoyu-article-illustrator preferences"/"重新配置"）。下次运行将重新触发首次设置。
- **常用单行编辑**：
  - `preferred_image_backend: auto` — 默认；运行时原生工具优先，回退到唯一安装的后端，仅在存在多个非原生后端时询问。
  - `preferred_image_backend: codex-imagegen` — 固定使用 Codex 内置后端。
  - `preferred_image_backend: baoyu-imagine` — 固定使用 baoyu-imagine 技能。
  - `preferred_image_backend: ask` — 每次运行确认后端。
  - `preferred_type: infographic`、`preferred_style: notion`、`preferred_palette: macaron`、`language: zh`。
  - `default_output_dir: imgs-subdir` — 设置相对于文章的生成图片写入位置。
