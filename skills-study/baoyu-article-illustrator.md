# baoyu-article-illustrator 深度解读

## 一、基础信息速览

| 维度 | 说明 |
|------|------|
| **名称/版本** | `baoyu-article-illustrator` v1.58.0 |
| **一句话定位** | 分析文章结构，识别需要配图的位置，以 Type × Style × Palette 三维方式批量生成插图 |
| **触发关键词** | "illustrate article"、"add images"、"generate images for article"、"为文章配图" |
| **前置依赖** | 至少一个可用的光栅图像生成后端（Codex `imagegen`、`baoyu-imagine` 等）；首次运行需完成 EXTEND.md 偏好配置 |
| **适用场景** | Markdown 文章配图、教程可视化、知识类内容图解、数据对比图、流程图等 |
| **输入→输出** | 文章文件路径（或粘贴内容）→ 带 YAML frontmatter 的 prompt 文件 + 插入位置标记的多张 PNG 插图 + 更新后的文章 |

---

## 二、架构与设计模式分析

### 6 步 Workflow 完整流程

```
Step 1: Pre-check          Step 2: Analyze          Step 3: Confirm
 ┌──────────────┐          ┌──────────┐           ┌──────────────┐
 │ 1.0 检测引用图 │          │ 内容类型   │           │ Q1 Preset/Type│
 │ 1.1 输入类型   │─────────▶│ 核心论点   │──────────▶│ Q2 Density   │
 │ 1.5 EXTEND.md │          │ 配图位置   │           │ Q3 Style     │
 │   (⛔ BLOCKING)│          │ 参考图分析  │           │ Q4 Palette   │
 └──────────────┘          └──────────┘           │ Q5 Language  │
                                                  └──────┬───────┘
                                                    ⚠️ 硬门控 │
                                                         ▼
Step 4: Outline            Step 5: Generate         Step 6: Finalize
 ┌──────────────┐          ┌──────────────┐        ┌──────────────┐
 │ outline.md   │          │ 5.1 保存 prompt│        │ 插入 Markdown │
 │ YAML front-  │─────────▶│ 5.2 选择后端  │───────▶│ 输出总结报告  │
 │ matter + 条目 │          │ 5.3 处理引用  │        │ 生成统计     │
 └──────────────┘          │ 5.5 批量生成  │        └──────────────┘
                           └──────────────┘
```

### Type × Style × Palette 三维组合系统

这是这个 Skill 最核心的设计亮点。三个维度各自独立、自由组合：

- **Type**（信息结构）：决定"画什么类型的图"——infographic、scene、flowchart、comparison、framework、timeline
- **Style**（渲染风格）：决定"用什么视觉语言画"——23 种风格，从 sketch-notes 到 screen-print
- **Palette**（色彩方案）：可选维度，覆盖 Style 的默认配色——macaron、warm、neon、mono-ink

这三者通过 `styles.md` 中的 **Type × Style 兼容矩阵**（✓✓/✓/✗）来约束推荐，同时通过 **Palette Override Rules** 让颜色层能独立替换而保留风格的渲染规则（线条、纹理、布局指导不变，只换色）。这是一种经典的 **关注点分离** 设计：结构、风格、颜色各管一维，组合爆炸式地扩展了视觉可能性。

### Image Generation Tools 后端选择

后端选择采用 4 级优先级瀑布：

1. 当前请求显式指定 → 2. EXTEND.md `preferred_image_backend` → 3. Auto-select（Codex `imagegen` > 运行时原生工具 > 唯一非原生后端 > 多后端则询问）→ 4. 无可用后端则通知用户

关键约束：**⛔ 绝不用 SVG/HTML/Canvas 代替光栅图像生成**。这条规则与 `baoyu-comic` 共用同一套设计，确保输出始终是 bitmap 资产。

### Confirmation Policy 设计

Step 3 被设计为 **硬门控**（Hard Gate）：

- 默认行为是"生成前必须确认"
- 即使用户提供了文件路径、匹配了 preset、EXTEND.md 有默认值，也**仅作为推荐输入**，不能跳过确认
- 唯一绕过方式：用户在当前请求中明确说"直接生成""不用确认""跳过确认"等

这种设计在 AI 工具中很有价值——它防止了"过度自主"，让用户始终对最终参数有掌控权。

### 输出目录策略（4 种模式）

| 模式 | 输出路径 | Markdown 插入路径 |
|------|---------|------------------|
| `imgs-subdir`（默认） | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| `same-dir` | `{article-dir}/` | `NN-{type}-{slug}.png` |
| `illustrations-subdir` | `{article-dir}/illustrations/` | `illustrations/NN-{type}-{slug}.png` |
| `independent` | `illustrations/{topic-slug}/` | 相对于 cwd 的路径 |

粘贴内容（无文件路径）时强制使用 `independent` 模式。目录内统一存放 `outline.md`、`prompts/` 子目录和生成图片，形成自包含的工作区。

### Reference Images 处理

参考图有三种用法：`direct`（直接作为视觉参考传给后端）、`style`（提取风格特征写入 prompt 文本）、`palette`（提取色彩方案）。关键设计是区分了"文件实际存在"和"口头提取"两条路径——只有文件真正保存到 `references/` 目录时，才能写入 prompt 的 YAML frontmatter；否则只能以文本形式追加到 prompt body。这避免了"幻觉引用"的问题。

---

## 三、核心能力拆解

### 6 种 Type 及适用场景

| Type | 最佳场景 | Prompt 模板核心结构 |
|------|---------|-------------------|
| `infographic` | 数据、指标、技术内容 | ZONES + LABELS + Layout (grid/radial/hierarchical) |
| `scene` | 叙事、情感类文章 | FOCAL POINT + ATMOSPHERE + MOOD + COLOR TEMPERATURE |
| `flowchart` | 流程、步骤、工作流 | STEPS + CONNECTIONS + Layout (left-right/top-down/circular) |
| `comparison` | 并列对比、选项评估 | LEFT SIDE + RIGHT SIDE + DIVIDER |
| `framework` | 模型、架构、概念体系 | STRUCTURE + NODES + RELATIONSHIPS |
| `timeline` | 历史、演进、里程碑 | DIRECTION + EVENTS + MARKERS |

### Style 与 Palette 的自由组合机制

Style 分两个层级：**Core Styles**（7 个简化选项，用于快速选择）和 **Style Gallery**（23 个完整风格）。Core Styles 其实是 Gallery 的"别名映射"，如 `hand-drawn` → `sketch-notes`、`sci-fi` → `blueprint`。

Palette 覆盖时遵循严格规则：读取 style 文件获得渲染规则 → 读取 palette 文件获得颜色和背景 → Palette 颜色**替换** style 默认色板 → Palette 背景色**替换** style 默认背景色 → 保留 style 的纹理描述。

### Preset 快捷方式

Preset 是 type + style + palette 的"一键套餐"，如 `hand-drawn-edu` = infographic + sketch-notes + macaron。文档提供了按场景分类的 Preset 推荐表（Content Type → Preset Recommendations），直接将 Step 2 的内容分析结果映射到推荐的 Preset。用户选了 Preset 后，Q3（Style）自动跳过——减少了交互轮次。

### Step 2 内容分析的 4 个维度

1. **Content Type**：Technical / Tutorial / Methodology / Narrative —— 决定推荐的 Type
2. **Illustration Purpose**：information / visualization / imagination —— 影响视觉风格选择
3. **Core Arguments**：2-5 个核心论点 —— 成为插图的内容来源
4. **Visual Opportunities / Positions**：哪些段落需要配图 —— 决定插入位置和数量

### Step 3 确认的 5 个问题设计

| 问题 | 优先级 | 跳过条件 |
|------|--------|---------|
| Q1: Preset or Type | ⚠️ REQUIRED | 无，必问 |
| Q2: Density | ⚠️ REQUIRED | 无，必问 |
| Q3: Style | ⚠️ REQUIRED | 若 Q1 选了 Preset 则跳过 |
| Q4: Palette | Optional | Preset 已含 palette 或 EXTEND.md 有 `preferred_palette` |
| Q5: Language | Conditional | 文章语言 = EXTEND.md 语言设置时跳过 |

所有问题合并在 **一次** AskUserQuestion 调用中，最多 4 个问题。这是减少交互轮次的关键设计。

### 批量生成 vs 子代理的决策逻辑

- **批量生成**（优先）：当多张插图的 prompt 文件都已保存完毕、任务是纯粹的图像生成时，使用后端的 batch 接口
- **子代理**（备选）：当每张图还需要独立的 prompt 迭代或创意探索时
- **顺序生成**（兜底）：后端没有 batch 接口时

这是一个实用的性能优化决策树——避免了不必要的并发开销，同时保留了需要时的灵活性。

### "Metaphors → visualize underlying concept, NOT literal image" 的设计意图

这条 CRITICAL 规则解决了 AI 配图的常见陷阱：文章说"用电锯切西瓜"是比喻"杀鸡用牛刀"，AI 不应该画一把电锯切开西瓜的画面，而应该可视化"过度使用工具"这个底层概念。这体现了对 AI 理解力局限的清醒认知——通过显式规则来弥补模型在隐喻理解上的不足。

---

## 四、Prompt Engineering 学习点

### AskUserQuestion 问题设计的优先级排序

Q1-Q2 设为 REQUIRED 是因为它们直接决定了生成物的核心属性（类型和数量），没有合理的默认值可以兜底。Q3 通过 Preset 机制实现了"条件性 REQUIRED"——如果 Preset 已经包含 style，就无需再问。Q4-Q5 则是真正可选的，因为有合理默认值。这种分层优先级设计值得在任何需要用户确认的 workflow 中借鉴。

### Prompt Construction 的结构化模板

每种 Type 都有专属的 Prompt 模板，核心结构是 **ZONES / LABELS / COLORS / STYLE / ASPECT** 五段式。以 Infographic 为例：

```
Layout: [grid/radial/hierarchical]
ZONES:   具体的视觉区域描述（非模糊描述）
LABELS:  文章中的实际数据、术语、指标（非占位符）
COLORS:  带语义含义的 hex 色值（red=warning, green=efficient）
STYLE:   线条处理、纹理、氛围
ASPECT:  16:9
```

关键约束是 LABELS 必须使用文章中的 **实际数据**。这是区分"好 prompt"和"泛泛 prompt"的分水岭——generic placeholder 会导致图片缺乏信息量。

### 批量后端 vs 子代理的决策规则设计

这个决策规则的设计体现了"最小复杂度"原则：只在需要时才引入复杂性（子代理）。在 Skill Prompt 层面明确定义这种决策规则，避免了每次执行时的即兴判断。

### Confirmation Policy 的可跳过设计

"直接生成""不用确认""跳过确认""按默认出图"——这些跳过关键词的设计非常务实。它同时满足了两类用户：谨慎型用户获得完整确认流程，高效型用户可以一句话跳过。而且跳过后仍要"在下一次用户可见更新中声明假设的参数"，保证了透明度。

### 值得借鉴的写法

**写法一：Color Specification Rules 中的防御性提示**

> Color values (#hex) and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text in the image.

点评：这是对图像生成模型一个已知缺陷的精准防御——模型容易将 prompt 中出现的文字内容渲染为图片中的可见文本。通过在每个包含 COLORS 段的 prompt 中追加这条指令，从源头解决问题。这种"已知缺陷 → 显式防御指令"的模式非常值得在 Prompt Engineering 中广泛应用。

**写法二：Prompt 文件优先于生成的设计**

> ⛔ BLOCKING: Prompt files MUST be saved before ANY image generation.

点评：将 prompt 文件作为"可复现性记录"（reproducibility record）是一个工程化思维的体现。它让你可以在不重新生成 prompt 的情况下切换后端、重试生成、甚至人工审查和调整 prompt。这种"先落盘再执行"的模式在任何涉及昂贵操作（API 调用、长时间计算）的 workflow 中都应采用。

**写法三：Auto Selection by Content Signals 表**

> | Content Signals | Recommended Type | Recommended Style |
> |---|---|---|
> | **(no strong signal / general article)** | **infographic** | **sketch-notes** |
> | Knowledge, concept, tutorial... | infographic | sketch-notes, vector-illustration, notion |

点评：将内容信号直接映射到推荐配置的查找表，是一种非常实用的"决策外化"策略。它把原本需要 AI 自行推理的决策过程，变成了确定性的表查找，极大提高了输出的一致性和可预测性。

---

## 五、教学小结

### Key Takeaways

1. **三维分离是组合式设计的精髓**：Type（结构）× Style（视觉）× Palette（色彩）三维独立组合，通过兼容矩阵约束推荐而非硬性限制，既保证了灵活性又避免了不合理搭配。这种设计模式可以迁移到任何需要多维度配置的 Skill 中。

2. **硬门控 + 可跳过 = 安全又高效**：Confirmation Policy 默认要求确认（防止过度自主），但允许用户用自然语言关键词跳过（减少交互摩擦）。这比简单的"总是确认"或"总是跳过"更人性化。

3. **Prompt 文件作为可复现性记录**：先保存 prompt 文件再调用生成后端，是一种工程化最佳实践。它将"创意决策"和"执行生成"解耦，让 prompt 成为可审查、可重试、可版本化的资产。

4. **显式防御已知 AI 缺陷**：无论是"不要画字面比喻"还是"不要把色值渲染成文本"，都是通过 prompt 层面的显式规则来弥补模型的已知局限。设计 Skill 时应主动识别这些"坑点"并写入规则。

5. **决策外化为查找表**：Content Signals → Type/Style 映射表、Content Type → Preset 推荐表，都是将隐式推理显式化的手段。它们让 Skill 的行为更可预测、更易调试。

### 如何设计"分析→确认→生成"三段式 Workflow

baoyu-article-illustrator 的 6 步流程本质上是一个 **分析→确认→生成** 三段式架构的精细展开：

- **分析阶段**（Step 1-2）：收集上下文（配置、引用图、文章内容），产出结构化分析结果（内容类型、核心论点、配图位置）
- **确认阶段**（Step 3）：将分析结果转化为用户可选的配置项，以硬门控形式呈现，一次性收集所有决策
- **生成阶段**（Step 4-6）：outline → prompt files → 图像生成 → 文章更新，每步都有验证点

设计类似 workflow 时的要点：分析阶段要产出足够信息供确认阶段构建选项；确认阶段要合并问题减少交互轮次；生成阶段要有中间产物（prompt 文件、outline）作为检查点和回滚基础。

### 与 baoyu-cover-image、baoyu-infographic 的定位差异

- **baoyu-article-illustrator**：面向**整篇文章的多图配图**，强调位置分析和批量生成，输出多张不同类型的插图散布在文章各处
- **baoyu-cover-image**：面向**单张封面图**，聚焦于吸引眼球的标题视觉，是"一图定调"的场景
- **baoyu-infographic**：面向**单张独立信息图**，将整篇文章浓缩为一张结构化的视觉摘要，强调信息密度和布局编排

三者从"单图封面"到"单图摘要"再到"多图散插"，覆盖了文章视觉化的完整谱系。article-illustrator 在三者中复杂度最高，因为它需要处理"在哪里插图"这个额外维度。
