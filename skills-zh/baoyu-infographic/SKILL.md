---
name: baoyu-infographic
description: 生成专业信息图，支持 21 种布局类型和 22 种视觉风格。分析内容，推荐布局×风格组合，生成可发布的信息图。当用户要求创建"infographic"、"信息图"、"visual summary"、"可视化"或"高密度信息大图"时使用。
version: 1.58.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-infographic
---

# 信息图生成器

两个维度：**布局**（信息结构）× **风格**（视觉美学）。任何布局可与任何风格自由组合。

## 用户输入工具

当本技能需要提示用户时，按以下优先级选择工具：

1. **优先使用内置用户输入工具** —— 当前代理运行时暴露的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出编号纯文本消息，要求用户回复对应编号/答案。
3. **批量处理**：如果工具支持单次调用多个问题，将所有适用问题合并为一次调用；如果仅支持单个问题，按优先级逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例——在其他运行时中请替换为本地等效工具。

## 图片生成工具

当本技能需要渲染图片时，按以下顺序确定后端：

1. **当前请求覆盖** —— 如果用户在当前消息中指定了特定后端，使用它。
2. **已保存偏好** —— 如果 `EXTEND.md` 将 `preferred_image_backend` 设置为当前可用的后端，使用它。
3. **自动选择**（当偏好为 `auto`、未设置或固定后端不可用时）：
   - **Codex (`imagegen`)** —— 首先检查可用技能/工具清单。如果列出了名为 `imagegen` 的技能，说明你在 Codex 中运行，必须使用它：通过 `Skill` 工具调用，传入 `skill: "imagegen"`，附带保存的提示词文件内容（以及输出路径和宽高比，按 Codex `imagegen` 自身参数）。Codex `imagegen` 是该运行时中的官方光栅后端，优先级高于任何非原生技能（如 `baoyu-imagine`），除非用户明确固定了不同的 `preferred_image_backend`。
   - **其他运行时原生工具** —— 如果运行时暴露了其他原生图片工具（如 Hermes `image_generate`），以相同方式使用。
   - 否则，如果恰好安装了一个非原生后端（如 `baoyu-imagine`），使用它。
   - 否则（多个非原生后端且无运行时原生工具），向用户询问一次——与其他初始问题一起批量提问。
4. **如果没有可用后端**，告知用户并询问如何继续。

**⛔ 绝不使用 SVG、HTML、canvas 或其他基于代码的渲染替代光栅图片生成。** Codex `imagegen` 的描述明确指出应在"输出应为位图资源而非仓库原生代码或矢量图"时使用。如果通过步骤 3 无法确定光栅后端，进入步骤 4 询问用户——**不要**静默输出 SVG、编写内联 `<svg>` 标记或生成 HTML/CSS 艺术作为替代。即使文章/章节看起来像"图表"也同样适用：调用此规则的消费技能已经决定需要的是光栅图片。

设置 `preferred_image_backend: ask` 将强制每次运行时执行步骤 3 的提示，无论可用后端如何。用户可通过下方 `## 更改偏好设置` 部分更改固定后端。

**提示词文件要求（硬性）**：在调用任何后端之前，将每张图片的完整最终提示词写入 `prompts/` 下的独立文件（命名：`NN-{type}-[slug].md`）。后端接收提示词文件（或其内容）；该文件是可复现性记录，允许你在不重新生成提示词的情况下切换后端。

上述具体工具名称（`imagegen`、`image_generate`、`baoyu-imagine`）仅为示例——在相同规则下替换为本地等效工具。

## 参考图片

用户可以提供参考图片来指导风格、配色、构图或主题。

**接收方式**：通过 `--ref <files...>` 或用户在对话中提供文件路径/粘贴图片时接收。
- 文件路径 → 复制到 `refs/NN-ref-{slug}.{ext}`（与输出同目录）
- 无路径粘贴图片 → 要求用户提供路径（按上方用户输入工具规则），或口头提取风格特征作为文本回退
- 无参考图 → 跳过此部分

**使用模式**（每个参考图）：

| 用法 | 效果 |
|-------|--------|
| `direct` | 将文件作为参考图片传递给后端 |
| `style` | 提取风格特征（线条处理、纹理、氛围）并附加到提示词正文 |
| `palette` | 从图片提取十六进制颜色并附加到提示词正文 |

**当存在参考图时，在 `prompts/infographic.md` frontmatter 中记录**：

```yaml
references:
  - ref_id: 01
    filename: 01-ref-brand.png
    usage: direct
```

**生成时**：
- 验证每个引用的文件在磁盘上存在
- 如果 `usage: direct` 且所选后端接受参考图片（如 `baoyu-imagine` 通过 `--ref`）→ 通过后端的 ref 参数传递文件
- 否则 → 在提示词文本中嵌入提取的 `style`/`palette` 特征

## 确认策略

默认行为：**生成前确认**。

- 将明确的技能调用、文件路径、匹配的关键词快捷方式、`EXTEND.md` 默认值以及文档记录的默认组合视为**仅推荐输入**。它们都不构成跳过确认的授权。
- 在用户确认组合/宽高比/语言/后端选择之前，**不要**开始步骤 5 或步骤 6。
- 仅当当前请求明确要求时才跳过确认，例如：`--no-confirm`、"直接生成"、"不用确认"、"跳过确认"、"按默认出图"或等效表述。
- 如果确认被明确跳过，在生成之前的下一条面向用户的更新中说明假定的组合/宽高比/语言/后端。

## 选项

| 选项 | 值 |
|--------|--------|
| `--layout` | 21 个选项（见布局画廊），默认：bento-grid |
| `--style` | 22 个选项（见风格画廊），默认：craft-handmade |
| `--aspect` | 命名预设：landscape (16:9)、portrait (9:16)、square (1:1)。自定义：任意 W:H 比例（如 3:4、4:3、2.35:1） |
| `--lang` | en, zh, ja 等 |
| `--no-confirm` | 仅当用户明确要求直接生成时跳过步骤 4 |
| `--ref <files...>` | 参考图片（文件路径），用于风格/配色/构图/主题指导 |

## 布局画廊（21 种）

| 布局 | 最佳用途 |
|--------|----------|
| `linear-progression` | 时间线、流程、教程 |
| `binary-comparison` | A 对比 B、前后对比、优缺点 |
| `comparison-matrix` | 多因素对比 |
| `hierarchical-layers` | 金字塔、优先级层次 |
| `tree-branching` | 分类、分类学 |
| `hub-spoke` | 中心概念与相关项目 |
| `structural-breakdown` | 分解图、剖面图 |
| `bento-grid` | 多主题、概览（默认） |
| `iceberg` | 表面与隐藏层面 |
| `bridge` | 问题-解决方案 |
| `funnel` | 转化、筛选 |
| `isometric-map` | 空间关系 |
| `dashboard` | 指标、KPI |
| `periodic-table` | 分类集合 |
| `comic-strip` | 叙事、序列 |
| `story-mountain` | 情节结构、张力弧线 |
| `jigsaw` | 相互关联的部分 |
| `venn-diagram` | 重叠概念 |
| `winding-roadmap` | 旅程、里程碑 |
| `circular-flow` | 循环、重复流程 |
| `dense-modules` | 高密度模块、数据密集型指南 |

完整定义见 `references/layouts/<layout>.md`。

## 风格画廊（22 种）

| 风格 | 描述 |
|-------|-------------|
| `craft-handmade` | 手绘、纸工艺（默认） |
| `claymation` | 3D 粘土人物、定格动画 |
| `kawaii` | 日式可爱、柔和色调 |
| `storybook-watercolor` | 柔和水彩、奇幻风 |
| `chalkboard` | 黑板上的粉笔画 |
| `cyberpunk-neon` | 霓虹光效、未来感 |
| `bold-graphic` | 漫画风格、半调 |
| `aged-academia` | 复古科学、泛黄色调 |
| `corporate-memphis` | 扁平矢量、鲜艳色彩 |
| `technical-schematic` | 蓝图、工程制图 |
| `origami` | 折纸、几何造型 |
| `pixel-art` | 复古 8-bit 像素风 |
| `ui-wireframe` | 灰度界面线框图 |
| `subway-map` | 地铁线路图 |
| `ikea-manual` | 极简线条艺术 |
| `knolling` | 整齐排列俯视图 |
| `lego-brick` | 积木拼搭造型 |
| `pop-laboratory` | 蓝图网格、坐标标记、实验室精确感 |
| `morandi-journal` | 手绘涂鸦、温暖莫兰迪色调 |
| `retro-pop-grid` | 1970 年代复古波普、瑞士网格、粗轮廓 |
| `hand-drawn-edu` | 马卡龙柔和色调、手绘抖动线条、火柴人 |
| `retro-popup-pop` | 复古弹窗拼贴、复古 UI、粗轮廓、扁平波普色 |

完整定义见 `references/styles/<style>.md`。

## 推荐组合

| 内容类型 | 布局 + 风格 |
|--------------|----------------|
| 时间线/历史 | `linear-progression` + `craft-handmade` |
| 分步教程 | `linear-progression` + `ikea-manual` |
| A 对比 B | `binary-comparison` + `corporate-memphis` |
| 层次结构 | `hierarchical-layers` + `craft-handmade` |
| 概念重叠 | `venn-diagram` + `craft-handmade` |
| 转化漏斗 | `funnel` + `corporate-memphis` |
| 循环流程 | `circular-flow` + `craft-handmade` |
| 技术类 | `structural-breakdown` + `technical-schematic` |
| 指标数据 | `dashboard` + `corporate-memphis` |
| 教育类 | `bento-grid` + `chalkboard` |
| 旅程地图 | `winding-roadmap` + `storybook-watercolor` |
| 分类集合 | `periodic-table` + `bold-graphic` |
| 产品指南 | `dense-modules` + `morandi-journal` |
| 技术指南 | `dense-modules` + `pop-laboratory` |
| 潮流指南 | `dense-modules` + `retro-pop-grid` |
| 复古波普指南 | `dense-modules` + `retro-popup-pop` |
| 教育图解 | `hub-spoke` + `hand-drawn-edu` |
| 流程教程 | `linear-progression` + `hand-drawn-edu` |

默认组合：`bento-grid` + `craft-handmade`（仅作为回退推荐——按[确认策略](#确认策略)，默认值不会绕过步骤 4）。

## 关键词快捷方式

当用户输入包含这些关键词时，使用映射的布局作为步骤 3 的首要推荐，并将列出的风格提升到步骤 3 列表顶部。对匹配的关键词跳过基于内容的布局推断。将任何 `提示词备注` 附加到步骤 5 的提示词中。

| 用户关键词 | 布局 | 推荐风格 | 默认宽高比 | 提示词备注 |
|--------------|--------|--------------------|----------------|--------------|
| 高密度信息大图 / high-density-info | `dense-modules` | `morandi-journal`, `pop-laboratory`, `retro-pop-grid`, `retro-popup-pop` | portrait | — |
| 信息图 / infographic | `bento-grid` | `craft-handmade` | landscape | 极简主义：干净画布，充足留白，无复杂背景纹理。仅使用简单卡通元素和图标。 |

## 输出结构

```
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```

Slug：从主题提取 2-4 个单词，kebab-case。冲突时附加 `-YYYYMMDD-HHMMSS`。

## 核心原则

- 忠实保留源数据——不总结或改写（但在输出中**剥离任何凭证、API 密钥、令牌或密码**）
- 在组织内容之前先定义学习目标
- 为视觉传达构建结构（标题、标签、视觉元素）

## 工作流程

### 步骤 1：设置与分析

**1.1 加载偏好设置（EXTEND.md）**

按优先级顺序检查 EXTEND.md——首次找到的生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-infographic/EXTEND.md` | 项目 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-infographic/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-infographic/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|--------|--------|
| 找到 | 读取、解析、显示一行摘要 |
| 未找到 | 使用 `AskUserQuestion` 询问用户（见 `references/config/first-time-setup.md`） |

**EXTEND.md 支持**：首选布局/风格、默认宽高比、语言偏好、首选图片后端、自定义风格定义。

Schema：`references/config/preferences-schema.md`

**1.2 分析内容 → `analysis.md`**

1. 保存源内容（文件路径或粘贴 → `source.md`）
   - **备份规则**：如果 `source.md` 存在，重命名为 `source-backup-YYYYMMDD-HHMMSS.md`
2. 分析：主题、数据类型、复杂度、语调、受众
3. 检测源语言和用户语言
4. 从用户输入中提取设计指令
5. 保存分析
   - **备份规则**：如果 `analysis.md` 存在，重命名为 `analysis-backup-YYYYMMDD-HHMMSS.md`

详细格式见 `references/analysis-framework.md`。

### 步骤 2：生成结构化内容 → `structured-content.md`

将内容转换为信息图结构：
1. 标题和学习目标
2. 各部分包含：核心概念、内容（逐字保留）、视觉元素、文本标签
3. 数据点（所有统计数据/引用原样复制）
4. 来自用户的设计指令

**规则**：仅使用 Markdown。不添加新信息。忠实保留数据。从输出中剥离任何凭证或密码。

详细格式见 `references/structured-content-template.md`。

### 步骤 3：推荐组合

**3.1 首先检查关键词快捷方式**：如果用户输入匹配**关键词快捷方式**表中的关键词，使用关联的布局作为首要推荐，并将关联风格优先作为顶部推荐。跳过基于内容的布局推断。

**3.2 否则**，基于以下因素推荐 3-5 个布局×风格组合：
- 数据结构 → 匹配布局
- 内容语调 → 匹配风格
- 受众期望
- 用户设计指令

### 步骤 4：确认选项

**硬性门控**：此步骤按[确认策略](#确认策略)为必需——步骤 5-6 在用户确认之前不能开始（或在当前请求中使用 `--no-confirm` / 等效表述明确选择退出）。

按本文件顶部的[用户输入工具](#用户输入工具)规则询问用户确认以下问题（如果运行时支持多问题则批量为一次调用；否则按优先级逐个提问）。

| 优先级 | 问题 | 何时询问 | 选项 |
|----------|----------|------|---------|
| 1 | **组合** | 始终 | 3+ 个布局×风格组合及理由 |
| 2 | **宽高比** | 始终 | 命名预设（landscape/portrait/square）或自定义 W:H 比例（如 3:4、4:3、2.35:1） |
| 3 | **语言** | 仅当源语言 ≠ 用户语言时 | 文本内容语言 |
| 4 | **图片后端** | 仅当 `## 图片生成工具` 规则的步骤 3 需要询问时（无运行时原生工具且有多个非原生后端，或 `preferred_image_backend: ask`） | 可用后端 |

### 步骤 5：生成提示词 → `prompts/infographic.md`

**备份规则**：如果 `prompts/infographic.md` 存在，重命名为 `prompts/infographic-backup-YYYYMMDD-HHMMSS.md`

组合以下内容：
1. 来自 `references/layouts/<layout>.md` 的布局定义
2. 来自 `references/styles/<style>.md` 的风格定义
3. 来自 `references/base-prompt.md` 的基础模板
4. 步骤 2 的结构化内容
5. 所有文本使用确认的语言

**宽高比解析**（用于 `{{ASPECT_RATIO}}`）：
- 命名预设 → 比例字符串：landscape→`16:9`，portrait→`9:16`，square→`1:1`
- 自定义 W:H 比例 → 原样使用（如 `3:4`、`4:3`、`2.35:1`）

### 步骤 6：生成图片

1. 按本文件顶部的 `## 图片生成工具` 规则确定后端。
2. 确保完整的最终提示词已保存在 `prompts/infographic.md`（步骤 5 中已写入），然后再调用后端——该文件是可复现性记录。
3. **检查现有文件**：生成前检查 `infographic.png` 是否存在
   - 如果存在：重命名为 `infographic-backup-YYYYMMDD-HHMMSS.png`
4. 使用提示词文件和输出路径调用所选后端
5. 失败时自动重试一次

### 步骤 7：输出摘要

报告：主题、布局、风格、宽高比、语言、图片后端、输出路径、创建的文件。

## 参考文件

- `references/analysis-framework.md` - 分析方法论
- `references/structured-content-template.md` - 内容格式
- `references/base-prompt.md` - 提示词模板
- `references/layouts/<layout>.md` - 21 种布局定义
- `references/styles/<style>.md` - 21 种风格定义

## 更改偏好设置

EXTEND.md 位于步骤 1.1 中首个匹配的路径。三种更改方式：

- **直接编辑** —— 打开 EXTEND.md 并更改字段。完整 schema：`references/config/preferences-schema.md`。
- **交互式重新配置** —— 删除 EXTEND.md（或要求"重新配置 baoyu-infographic 偏好"/"重新配置"）。下次运行将重新触发首次设置。
- **常见单行编辑**：
  - `preferred_image_backend: auto` —— 默认；运行时原生工具优先，回退到唯一安装的后端，仅在存在多个非原生后端时询问。
  - `preferred_image_backend: codex-imagegen` —— 固定到 Codex 内置。
  - `preferred_image_backend: baoyu-imagine` —— 固定到 baoyu-imagine 技能。
  - `preferred_image_backend: ask` —— 每次运行确认后端。
  - `preferred_layout: dense-modules`、`preferred_style: morandi-journal`、`preferred_aspect: portrait`、`language: zh` —— 调整步骤 3 的推荐和步骤 4 的默认值（按[确认策略](#确认策略)，这些不会绕过步骤 4）。
