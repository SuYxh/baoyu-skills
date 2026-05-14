---
name: baoyu-comic
description: 知识漫画创作工具，支持多种画风和色调。创建具有详细分镜布局和顺序图片生成的原创教育漫画。当用户要求创建"知识漫画"、"教育漫画"、"人物传记漫画"、"教程漫画"或 "Logicomix 风格漫画"时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-comic
    requires:
      anyBins:
        - bun
        - npx
---

# 知识漫画创作工具

创建原创知识漫画，灵活组合画风 × 色调。

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

## 参考图片

用户可提供参考图片来指导画风、配色、场景构图或主题。这与自动生成的角色设定图（步骤 7.1）是**分开的** — 两者可以共存：用户参考图指导外观，角色设定图锚定重复出现的角色身份。

**接收方式**：通过 `--ref <files...>` 或用户在对话中提供文件路径/粘贴图片接收。
- 文件路径 → 复制到漫画输出旁的 `refs/NN-ref-{slug}.{ext}`
- 粘贴图片无路径 → 询问用户路径（按上方用户输入工具规则），或作为文本降级方案口头提取风格特征
- 无参考图 → 跳过此部分

**使用模式**（每个参考图）：

| 用法 | 效果 |
|------|------|
| `direct` | 将文件作为参考图片传递给后端，用于每一页（或选定页面） |
| `style` | 提取风格特征（线条处理、纹理、氛围）并附加到每一页的提示词正文 |
| `palette` | 提取十六进制颜色并附加到每一页的提示词正文 |

**当参考图存在时，记录在每一页的提示词 frontmatter 中**：

```yaml
references:
  - ref_id: 01
    filename: 01-ref-scene.png
    usage: direct
```

**生成时**：
- 验证每个引用的文件在磁盘上存在
- 如果 `usage: direct` 且所选后端支持多个参考图片 → 通过后端的 ref 参数同时传递角色设定图（步骤 7.2）和用户参考图；先压缩图片（参见步骤 7.1 的指导）以避免载荷失败
- 如果后端仅接受一个参考图 → 对有重复角色的页面优先使用角色设定图；将用户参考图特征嵌入提示词正文
- 对于 `style`/`palette` 用法 → 将提取的特征嵌入每一页的提示词文本（无论后端能力如何均适用）

## 选项

### 视觉维度

| 选项 | 值 | 描述 |
|------|-----|------|
| `--art` | ligne-claire（默认）, manga, realistic, ink-brush, chalk, minimalist | 画风/渲染技法 |
| `--tone` | neutral（默认）, warm, dramatic, romantic, energetic, vintage, action | 情绪/氛围 |
| `--layout` | standard（默认）, cinematic, dense, splash, mixed, webtoon, four-panel | 分镜排列 |
| `--aspect` | 3:4（默认，纵向）, 4:3（横向）, 16:9（宽屏） | 页面宽高比 |
| `--lang` | auto（默认）, zh, en, ja 等 | 输出语言 |
| `--ref <files...>` | 文件路径 | 应用于每一页的参考图片，用于风格/配色/场景指导。见上方[参考图片](#参考图片)。 |

### 部分工作流选项

| 选项 | 描述 |
|------|------|
| `--storyboard-only` | 仅生成分镜脚本，跳过提示词和图片 |
| `--prompts-only` | 生成分镜脚本 + 提示词，跳过图片 |
| `--images-only` | 从现有提示词目录生成图片 |
| `--regenerate N` | 仅重新生成特定页面（如 `3` 或 `2,5,8`） |

详情：[references/partial-workflows.md](references/partial-workflows.md)

### 画风、色调与预设目录

- **画风**（6 种）：`ligne-claire`、`manga`、`realistic`、`ink-brush`、`chalk`、`minimalist`。完整定义见 `references/art-styles/<style>.md`。
- **色调**（7 种）：`neutral`、`warm`、`dramatic`、`romantic`、`energetic`、`vintage`、`action`。完整定义见 `references/tones/<tone>.md`。
- **预设**（5 种）带有超越简单画风+色调的特殊规则：

  | 预设 | 等效 | 特色 |
  |------|------|------|
  | `ohmsha` | manga + neutral | 视觉隐喻，无对话头像，道具展示 |
  | `wuxia` | ink-brush + action | 气效果，战斗画面，氛围感 |
  | `shoujo` | manga + romantic | 装饰元素，眼部细节，浪漫节拍 |
  | `concept-story` | manga + warm | 视觉符号系统，成长弧线，对话+动作平衡 |
  | `four-panel` | minimalist + neutral + four-panel 布局 | 起承转合结构，黑白+点缀色，简笔画角色 |

  完整规则见 `references/presets/<preset>.md` — 选择预设时加载该文件。

- **兼容性矩阵**和**内容信号 → 预设**对照表见 [references/auto-selection.md](references/auto-selection.md)。在步骤 2 推荐组合之前请阅读。

## 脚本目录

**重要**：所有脚本位于本技能的 `scripts/` 子目录中。

**代理执行说明**：
1. 确定此 SKILL.md 文件的目录路径为 `{baseDir}`
2. 脚本路径 = `{baseDir}/scripts/<script-name>.ts`
3. 将本文档中所有 `{baseDir}` 替换为实际路径
4. 解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果有 `npx` → `npx -y bun`；否则建议安装 bun

**脚本参考**：
| 脚本 | 用途 |
|------|------|
| `scripts/merge-to-pdf.ts` | 合并漫画页面为 PDF |

## 文件结构

输出目录：`comic/{topic-slug}/`
- Slug：从主题提取 2-4 个单词的 kebab-case（如 `alan-turing-bio`）
- 冲突：追加时间戳（如 `turing-story-20260118-143052`）

**内容**：
| 文件 | 描述 |
|------|------|
| `source-{slug}.{ext}` | 源文件 |
| `analysis.md` | 内容分析 |
| `storyboard.md` | 含分镜细节的分镜脚本 |
| `characters/characters.md` | 角色定义 |
| `characters/characters.png` | 角色设定图 |
| `prompts/NN-{cover\|page}-[slug].md` | 生成提示词 |
| `NN-{cover\|page}-[slug].png` | 生成的图片 |
| `{topic-slug}.pdf` | 最终合并的 PDF |

## 语言处理

**检测优先级**：
1. `--lang` 标志（显式指定）
2. EXTEND.md `language` 设置
3. 用户对话语言
4. 源内容语言

**规则**：对所有交互使用用户的输入语言或已保存的语言偏好：
- 分镜脚本大纲和场景描述
- 图片生成提示词
- 用户选择选项和确认
- 进度更新、问题、错误、摘要

技术术语保持英文。

## 工作流程

### 进度清单

```
漫画进度：
- [ ] 步骤 1：设置与分析
  - [ ] 1.1 偏好设置（EXTEND.md）⛔ 阻塞
    - [ ] 找到 → 加载偏好 → 继续
    - [ ] 未找到 → 运行首次设置 → 必须在其他步骤之前完成
  - [ ] 1.2 分析，1.3 检查现有内容
- [ ] 步骤 2：确认 - 风格与选项 ⚠️ 必需
- [ ] 步骤 3：生成分镜脚本 + 角色
- [ ] 步骤 4：审查大纲（有条件）
- [ ] 步骤 5：生成提示词
- [ ] 步骤 6：审查提示词（有条件）
- [ ] 步骤 7：生成图片
  - [ ] 7.1 生成角色设定图（如需要）→ characters/characters.png
  - [ ] 7.2 生成页面（如果角色设定图存在则使用 --ref）
- [ ] 步骤 8：合并为 PDF
- [ ] 步骤 9：完成报告
```

### 流程

```
输入 → [偏好设置] ─┬─ 找到 → 继续
                   │
                   └─ 未找到 → 首次设置 ⛔ 阻塞
                                      │
                                      └─ 完成设置 → 保存 EXTEND.md → 继续
                                                                        │
        ┌───────────────────────────────────────────────────────────────┘
        ↓
分析 → [检查现有？] → [确认：风格 + 审查] → 分镜脚本 → [审查？] → 提示词 → [审查？] → 图片 → PDF → 完成
```

### 步骤摘要

| 步骤 | 操作 | 关键输出 |
|------|------|----------|
| 1.1 | 加载 EXTEND.md 偏好 ⛔ 未找到时阻塞 | 配置已加载 |
| 1.2 | 分析内容 | `analysis.md` |
| 1.3 | 检查现有目录 | 处理冲突 |
| 2 | 确认风格、重点、受众、审查 | 用户偏好 |
| 3 | 生成分镜脚本 + 角色 | `storyboard.md`、`characters/` |
| 4 | 审查大纲（如有请求） | 用户批准 |
| 5 | 生成提示词 | `prompts/*.md` |
| 6 | 审查提示词（如有请求） | 用户批准 |
| 7.1 | 生成角色设定图（如需要） | `characters/characters.png` |
| 7.2 | 生成页面（如果角色设定图可用则带参考图） | `*.png` 文件 |
| 8 | 合并为 PDF | `{slug}.pdf` |
| 9 | 完成报告 | 摘要 |

### 步骤 7：图片生成

**使用顶部的 `## 图片生成工具` 规则每个会话选择一次后端。** 如果后端是仓库技能（如 `baoyu-imagine`），请阅读其 `SKILL.md` 并使用其文档化的接口，而非其脚本。

**7.1 角色设定图** — 当漫画为多页且有重复角色时生成它（到 `characters/characters.png`，宽高比 `4:3`）。对于简单预设（如 four-panel minimalist）或单页漫画可跳过。使用前压缩为 JPEG（macOS 上用 `sips -s format jpeg -s formatOptions 80 …`，其他系统用 `pngquant --quality=65-80 …`）以避免载荷失败。位于 `characters/characters.md` 的提示词文件必须在调用后端之前存在。

**7.2 页面** — 每一页的提示词必须已在 `prompts/NN-{cover|page}-[slug].md` 存在后才能调用后端；该文件是可复现性记录。策略取决于角色设定图：

| 角色设定图 | 后端 `--ref` | 策略 |
|------------|-------------|------|
| 存在 | 支持 | 每一页传递设定图作为 `--ref` |
| 存在 | 不支持 | 在每个提示词文件前添加角色描述 |
| 已跳过 | — | 所有描述内联在提示词中 |

**备份规则**：现有 `prompts/…md` 和 `…png` 文件 → 重新生成前以 `-backup-YYYYMMDD-HHMMSS` 后缀重命名。宽高比来自分镜脚本（默认 `3:4`；预设可能覆盖）。

**`--ref` 失败恢复**：压缩设定图 → 重试 → 仍然失败 → 放弃 `--ref` 并将角色描述嵌入提示词文本。

完整的逐步工作流程（分析、分镜脚本、审查门槛、重新生成变体）：[references/workflow.md](references/workflow.md)。

### EXTEND.md 路径 ⛔ 阻塞

如果未找到 EXTEND.md，首次设置为**阻塞** — 在任何内容分析或风格/色调问题之前完成它。

| 优先级 | 路径 | 范围 |
|--------|------|------|
| 1 | `.baoyu-skills/baoyu-comic/EXTEND.md` | 项目级 |
| 2 | `$HOME/.baoyu-skills/baoyu-comic/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|------|------|
| 找到 | 读取、解析、显示摘要 → 继续 |
| 未找到 | ⛔ 运行首次设置（[references/config/first-time-setup.md](references/config/first-time-setup.md)）→ 保存 EXTEND.md → 继续 |

**EXTEND.md 支持**：水印、首选画风/色调/布局、自定义风格定义、角色预设、语言偏好。Schema：[references/config/preferences-schema.md](references/config/preferences-schema.md)。

## 参考文件

**核心模板**：
- [analysis-framework.md](references/analysis-framework.md) - 深度内容分析
- [character-template.md](references/character-template.md) - 角色定义格式
- [storyboard-template.md](references/storyboard-template.md) - 分镜脚本结构
- [ohmsha-guide.md](references/ohmsha-guide.md) - Ohmsha 漫画规范

**风格定义**：
- `references/art-styles/` - 画风（ligne-claire, manga, realistic, ink-brush, chalk, minimalist）
- `references/tones/` - 色调（neutral, warm, dramatic, romantic, energetic, vintage, action）
- `references/presets/` - 带特殊规则的预设（ohmsha, wuxia, shoujo, concept-story, four-panel）
- `references/layouts/` - 布局（standard, cinematic, dense, splash, mixed, webtoon, four-panel）

**工作流程**：
- [workflow.md](references/workflow.md) - 完整工作流程详情
- [auto-selection.md](references/auto-selection.md) - 内容信号分析
- [partial-workflows.md](references/partial-workflows.md) - 部分工作流选项

**配置**：
- [config/preferences-schema.md](references/config/preferences-schema.md) - EXTEND.md schema
- [config/first-time-setup.md](references/config/first-time-setup.md) - 首次设置
- [config/watermark-guide.md](references/config/watermark-guide.md) - 水印配置

## 页面修改

| 操作 | 步骤 |
|------|------|
| **编辑** | **先更新提示词文件** → `--regenerate N` → 重新生成 PDF |
| **添加** | 在位置创建提示词 → 使用角色参考图生成 → 重新编号后续页面 → 更新分镜脚本 → 重新生成 PDF |
| **删除** | 移除文件 → 重新编号后续页面 → 更新分镜脚本 → 重新生成 PDF |

**重要**：更新页面时，始终**先**更新提示词文件（`prompts/NN-{cover|page}-[slug].md`），然后再重新生成。这确保更改有记录且可复现。

## 注意事项

- 图片生成：每页 10-30 秒
- 生成失败时自动重试一次
- 对敏感公众人物使用风格化替代形象
- 通过会话 ID 保持风格一致性
- **步骤 2 确认为必需** - 不要跳过
- **步骤 4/6 为有条件** - 仅在用户于步骤 2 中请求时执行
- **步骤 7.1 角色设定图** - 建议用于多页漫画，简单预设可选
- **步骤 7.2 角色参考** - 如果设定图存在则使用 `--ref`；失败时压缩/转换；降级到仅提示词
- 水印/语言在 EXTEND.md 中一次性配置

## 更改偏好

EXTEND.md 位于 `.baoyu-skills/baoyu-comic/EXTEND.md`（项目级）或 `~/.baoyu-skills/baoyu-comic/EXTEND.md`（用户级）。三种更改方式：

- **直接编辑** — 打开 EXTEND.md 并修改字段。完整 schema：`references/config/preferences-schema.md`。
- **交互式重新配置** — 删除 EXTEND.md（或要求"reconfigure baoyu-comic preferences"/"重新配置"）。下次运行将重新触发首次设置。
- **常用单行编辑**：
  - `preferred_image_backend: auto` — 默认；运行时原生工具优先，回退到唯一安装的后端，仅在存在多个非原生后端时询问。
  - `preferred_image_backend: codex-imagegen` — 固定使用 Codex 内置后端。
  - `preferred_image_backend: baoyu-imagine` — 固定使用 baoyu-imagine 技能。
  - `preferred_image_backend: ask` — 每次运行确认后端。
  - `watermark.enabled: true`、`preferred_art`、`preferred_tone`、`preferred_layout`、`language` — 调整自动选择默认值和外观选项。
