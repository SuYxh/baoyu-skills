---
name: baoyu-cover-image
description: 通过 5 个维度（类型、配色、渲染、文字、氛围）生成文章封面图片，组合 11 种配色方案和 7 种渲染风格。支持电影宽幅（2.35:1）、宽屏（16:9）和正方形（1:1）宽高比。当用户要求"生成封面图"、"创建文章封面"或"制作封面"时使用。
version: 1.56.2
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-cover-image
---

# 封面图片生成器

为文章生成精美封面图片，支持 5 维自定义。

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

- 将显式技能调用、文件路径、匹配的关键词/预设、`EXTEND.md` 默认值以及任何文档化的自动选择视为**仅推荐输入**。它们均不授权跳过确认。
- 在用户确认维度/宽高比/语言/后端选择之前，**不要**开始步骤 3 或步骤 4。
- 仅当当前请求明确表示跳过时才跳过确认，例如：`--quick`、"直接生成"、"不用确认"、"跳过确认"、"按默认出图"或等效措辞。`EXTEND.md` 中的 `quick_mode: true` 视为长期明确选择退出 — 仅当你希望每次运行都跳过步骤 2 时才设置它。
- 如果明确跳过确认，在生成前的下一次面向用户的更新中说明假定的维度/宽高比/语言/后端。

## 选项

| 选项 | 描述 |
|------|------|
| `--type <name>` | hero, conceptual, typography, metaphor, scene, minimal |
| `--palette <name>` | warm, elegant, cool, dark, earth, vivid, pastel, mono, retro, duotone, macaron |
| `--rendering <name>` | flat-vector, hand-drawn, painterly, digital, pixel, chalk, screen-print |
| `--style <name>` | 预设简写（见 [风格预设](references/style-presets.md)） |
| `--text <level>` | none, title-only, title-subtitle, text-rich |
| `--mood <level>` | subtle, balanced, bold |
| `--font <name>` | clean, handwritten, serif, display |
| `--aspect <ratio>` | 16:9（默认）, 2.35:1, 4:3, 3:2, 1:1, 3:4 |
| `--lang <code>` | 标题语言（en, zh, ja 等） |
| `--no-title` | `--text none` 的别名 |
| `--quick` | 跳过确认，使用自动选择 |
| `--ref <files...>` | 用于风格/构图指导的参考图片 |

## 五个维度

| 维度 | 值 | 默认值 |
|------|-----|--------|
| **类型** | hero, conceptual, typography, metaphor, scene, minimal | auto |
| **配色** | warm, elegant, cool, dark, earth, vivid, pastel, mono, retro, duotone, macaron | auto |
| **渲染** | flat-vector, hand-drawn, painterly, digital, pixel, chalk, screen-print | auto |
| **文字** | none, title-only, title-subtitle, text-rich | title-only |
| **氛围** | subtle, balanced, bold | balanced |
| **字体** | clean, handwritten, serif, display | clean |

自动选择规则：[references/auto-selection.md](references/auto-selection.md)

## 画廊

**类型**：hero, conceptual, typography, metaphor, scene, minimal
→ 详情：[references/types.md](references/types.md)

**配色**：warm, elegant, cool, dark, earth, vivid, pastel, mono, retro, duotone, macaron
→ 详情：[references/palettes/](references/palettes/)

**渲染**：flat-vector, hand-drawn, painterly, digital, pixel, chalk, screen-print
→ 详情：[references/renderings/](references/renderings/)

**文字层级**：none（纯视觉）| title-only（默认）| title-subtitle | text-rich（含标签）
→ 详情：[references/dimensions/text.md](references/dimensions/text.md)

**氛围层级**：subtle（低对比度）| balanced（默认）| bold（高对比度）
→ 详情：[references/dimensions/mood.md](references/dimensions/mood.md)

**字体**：clean（无衬线）| handwritten | serif | display（粗体装饰）
→ 详情：[references/dimensions/font.md](references/dimensions/font.md)

## 文件结构

输出目录根据 `default_output_dir` 偏好设置决定：
- `same-dir`：`{article-dir}/`
- `imgs-subdir`：`{article-dir}/imgs/`
- `independent`（默认）：`cover-image/{topic-slug}/`

```
<output-dir>/
├── source-{slug}.{ext}    # 源文件
├── refs/                  # 参考图片（如有提供）
│   ├── ref-01-{slug}.{ext}
│   └── ref-01-{slug}.md   # 描述文件
├── prompts/cover.md       # 生成提示词
└── cover.png              # 输出图片
```

**Slug**：2-4 个单词，kebab-case。冲突：追加 `-YYYYMMDD-HHMMSS`

## 工作流程

### 进度清单

```
封面图片进度：
- [ ] 步骤 0：检查偏好设置（EXTEND.md）⛔ 阻塞
- [ ] 步骤 1：分析内容 + 保存参考图 + 确定输出目录
- [ ] 步骤 2：确认选项（6 个维度）⚠️ 除非 --quick
- [ ] 步骤 3：创建提示词
- [ ] 步骤 4：生成图片
- [ ] 步骤 5：完成报告
```

### 流程

```
输入 → [步骤 0：偏好设置] ─┬─ 找到 → 继续
                           └─ 未找到 → 首次设置 ⛔ 阻塞 → 保存 EXTEND.md → 继续
        ↓
分析 + 保存参考图 → [输出目录] → [确认：6 个维度] → 提示词 → 生成 → 完成
                                        ↓
                               （如果 --quick 或全部已指定则跳过）
```

### 步骤 0：加载偏好设置 ⛔ 阻塞

按优先顺序检查 EXTEND.md — 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|--------|------|------|
| 1 | `.baoyu-skills/baoyu-cover-image/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-cover-image/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-cover-image/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|------|------|
| 找到 | 加载、显示摘要 → 继续 |
| 未找到 | ⛔ 运行首次设置（[references/config/first-time-setup.md](references/config/first-time-setup.md)）→ 保存 → 继续 |

**关键**：如果未找到，在任何其他步骤或问题之前完成设置。

### 步骤 1：分析内容

1. **保存参考图片**（如有提供）→ [references/workflow/reference-images.md](references/workflow/reference-images.md)
2. **保存源内容**（如为粘贴内容，保存到 `source.md`）
3. **分析内容**：主题、语气、关键词、视觉隐喻
4. **深度分析参考图** ⚠️：提取具体、明确的元素（见 reference-images.md）
5. **检测语言**：比较源内容、用户输入、EXTEND.md 偏好
6. **确定输出目录**：按文件结构规则

**⚠️ 参考图片中的人物：**

如果参考图片包含应出现在封面中的**人物**：

- **模型支持 `--ref`**（默认）：将图片复制到 `refs/`，生成时通过 `--ref` 传递。无需描述文件 — 模型直接看到面部。
- **模型不支持 `--ref`**（即梦、Seedream 3.0）：创建 `refs/ref-NN-{slug}.md`，包含逐角色描述（发型、眼镜、肤色、服装）。在提示词文本中作为 MUST/REQUIRED 指令嵌入。

完整决策表见 [reference-images.md](references/workflow/reference-images.md)。

### 步骤 2：确认选项 ⚠️

**硬性门槛**：根据[确认策略](#确认策略)，此步骤为必需 — 在用户确认（或通过 `--quick` / `quick_mode: true` / 当前请求中的等效措辞明确选择退出）之前，步骤 3-4 不能开始。

**必须使用 `AskUserQuestion` 工具**以交互式选择方式呈现选项 — 而非纯文本表格。在一次 `AskUserQuestion` 调用中呈现最多 4 个问题（类型、配色、渲染、字体 + 设置）。每个问题首先显示推荐选项及原因，然后是备选方案。

完整确认流程和问题格式：[references/workflow/confirm-options.md](references/workflow/confirm-options.md)

| 条件 | 跳过 | 仍需询问 |
|------|------|----------|
| `--quick` 或 `quick_mode: true` | 6 个维度 | 宽高比（除非指定了 `--aspect`） |
| 全部 6 个 + `--aspect` 已指定 | 全部 | 无 |

### 步骤 3：创建提示词

保存到 `prompts/cover.md`。模板：[references/workflow/prompt-template.md](references/workflow/prompt-template.md)

**关键 - Frontmatter 中的参考图片**：
- 保存到 `refs/` 的文件 → 添加到 frontmatter `references` 列表
- 口头提取的风格（无文件）→ 省略 `references`，在正文中描述
- 写入前 → 验证：`test -f refs/ref-NN-{slug}.{ext}`

**正文中的参考元素**必须详细，以"MUST"/"REQUIRED"为前缀，并附带整合方式。

### 步骤 4：生成图片

1. **备份现有** `cover.png`（如为重新生成）
2. **选择后端** — 通过顶部的 `## 图片生成工具` 规则：使用可用的后端；如果有多个，询问用户一次。在任何生成之前每个会话执行一次。
3. **将完整最终提示词写入** `prompts/01-cover-[slug].md`（硬性要求），然后再调用后端。
4. **处理参考图片** — 来自提示词 frontmatter：
   - `direct` 用法 → 通过 `--ref` 传递（使用支持参考图的后端）
   - `style`/`palette` → 提取特征，附加到提示词
5. **生成**：使用提示词文件、输出路径、宽高比调用所选后端
6. 失败时：自动重试一次

### 步骤 5：完成报告

```
封面已生成！

主题：[topic]
类型：[type] | 配色：[palette] | 渲染：[rendering]
文字：[text] | 氛围：[mood] | 字体：[font] | 宽高比：[ratio]
标题：[title 或 "纯视觉"]
语言：[lang] | 水印：[已启用/已禁用]
参考图片：[N 张图片 或 "已提取风格" 或 "无"]
位置：[directory path]

文件：
✓ source-{slug}.{ext}
✓ prompts/cover.md
✓ cover.png
```

## 图片修改

| 操作 | 步骤 |
|------|------|
| **重新生成** | 备份 → 先更新提示词文件 → 重新生成 |
| **更改维度** | 备份 → 确认新值 → 更新提示词 → 重新生成 |

## 构图原则

- **留白**：40-60% 呼吸空间
- **视觉锚点**：主要元素居中或偏左放置
- **角色**：简化剪影；不使用写实人物
- **标题**：使用用户/源内容中的确切标题；不要自行创造

## 更改偏好

EXTEND.md 位于**步骤 0** 中所述的路径。三种更改方式：

- **直接编辑** — 打开 EXTEND.md 并修改字段。完整 schema：[references/config/preferences-schema.md](references/config/preferences-schema.md)。
- **交互式重新配置** — 删除 EXTEND.md（或要求"reconfigure baoyu-cover-image preferences"/"重新配置"）。下次运行将重新触发首次设置。
- **常用单行编辑**：
  - `preferred_image_backend: auto` — 默认；运行时原生工具优先，回退到唯一安装的后端，仅在存在多个非原生后端时询问。
  - `preferred_image_backend: codex-imagegen` — 固定使用 Codex 内置后端。
  - `preferred_image_backend: baoyu-imagine` — 固定使用 baoyu-imagine 技能。
  - `preferred_image_backend: ask` — 每次运行确认后端。
  - `watermark.enabled: true`、`preferred_type`、`preferred_palette`、`preferred_rendering`、`default_aspect`、`quick_mode: true`、`language` — 调整自动选择默认值和确认流程。

## 参考文件

**维度**：[text.md](references/dimensions/text.md) | [mood.md](references/dimensions/mood.md) | [font.md](references/dimensions/font.md)
**配色**：[references/palettes/](references/palettes/)
**渲染**：[references/renderings/](references/renderings/)
**类型**：[references/types.md](references/types.md)
**自动选择**：[references/auto-selection.md](references/auto-selection.md)
**风格预设**：[references/style-presets.md](references/style-presets.md)
**兼容性**：[references/compatibility.md](references/compatibility.md)
**视觉元素**：[references/visual-elements.md](references/visual-elements.md)
**工作流程**：[confirm-options.md](references/workflow/confirm-options.md) | [prompt-template.md](references/workflow/prompt-template.md) | [reference-images.md](references/workflow/reference-images.md)
**配置**：[preferences-schema.md](references/config/preferences-schema.md) | [first-time-setup.md](references/config/first-time-setup.md) | [watermark-guide.md](references/config/watermark-guide.md)
