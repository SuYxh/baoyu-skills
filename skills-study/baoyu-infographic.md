# baoyu-infographic 深度解读：462 种组合的信息图生成系统设计

> 本文面向想学习编写 Agent Skill 的开发者，以 `baoyu-infographic` v1.58.0 为案例，拆解其双维度参数空间设计、7 步 Workflow 硬门控模式，以及大参数空间下的用户引导策略。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-infographic` v1.58.0 |
| **一句话定位** | 21 种布局 × 22 种风格的专业信息图生成器 |
| **触发关键词** | infographic、信息图、visual summary、可视化、高密度信息大图 |
| **前置依赖** | 需要一个 raster image 后端（Codex `imagegen`、`baoyu-imagine` 或其他 runtime-native 工具） |
| **适用场景** | 教育科普、产品选购指南、流程教程、数据对比、时间线、概念关系可视化 |
| **输入→输出** | 用户内容（文本/文件）+ 可选参考图 → `infographic.png` + 分析文件 + prompt 文件 |

---

## 二、架构与设计模式分析

### 2.1 七步 Workflow 流程图

```
用户输入（文本/文件/URL）
        │
        ▼
┌─────────────────────────────┐
│ Step 1: Setup & Analyze      │
│  1.1 加载 EXTEND.md 偏好设置  │  ⛔ BLOCKING（首次未找到则触发 First-Time Setup）
│  1.2 分析内容 → analysis.md   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Step 2: Structured Content   │
│  结构化转换 → structured-     │
│  content.md                  │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Step 3: Recommend            │
│  3.1 Keyword Shortcuts 匹配  │
│  3.2 推荐 3-5 个 layout×style│
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Step 4: Confirm Options      │  ⛔ HARD GATE — 必须用户确认才能继续
│  确认组合 / 比例 / 语言 / 后端 │
└─────────────────────────────┘
        │ (用户确认)
        ▼
┌─────────────────────────────┐
│ Step 5: Generate Prompt      │
│  合并 layout def + style def │
│  + base template + content   │
│  → prompts/infographic.md    │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Step 6: Generate Image       │
│  调用 image backend 生成      │
│  失败自动重试 1 次            │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Step 7: Output Summary       │
│  报告所有选项与文件路径        │
└─────────────────────────────┘
```

### 2.2 Layout (21) × Style (22) = 462 种组合的双维度系统

这是本 Skill 最核心的设计哲学——将信息图拆分为两个正交维度：

| 维度 | 含义 | 数量 | 存储位置 |
|------|------|------|----------|
| **Layout** | 信息架构（数据的组织结构） | 21 种 | `references/layouts/<name>.md` |
| **Style** | 视觉美学（颜色、质感、字体） | 22 种 | `references/styles/<name>.md` |

任意 layout 可与任意 style 自由组合，产生 21×22=462 种独特的视觉呈现。这种"结构与表现分离"的设计（类似 CSS 与 HTML 的关系）极大提升了系统的可扩展性——添加 1 个新 layout 即获得 22 种新组合。

### 2.3 Keyword Shortcuts 快捷匹配机制

当用户输入包含特定关键词时，跳过内容推断，直接锁定推荐组合：

- "高密度信息大图" → 直接推荐 `dense-modules` layout + 4 种专属风格
- "信息图" → 直接推荐 `bento-grid` + `craft-handmade`

这是一种**意图识别捷径**——减少 AI 的推断不确定性，让高频场景快速命中。

### 2.4 Confirmation Policy（Step 4 硬门控）

**设计要点**：无论来源是什么（keyword 匹配、EXTEND.md 偏好、默认值），都**不能**跳过确认。只有用户**当前请求**中显式使用 `--no-confirm` / "直接生成" 等措辞才可跳过。

这是防止"默认组合不符合预期"的安全阀——462 种组合空间下，自动推断的准确率不可能 100%，因此强制确认是必要的 UX 保护。

### 2.5 Reference Images 处理

支持三种使用模式：`direct`（直接传递给后端）、`style`（提取风格特征写入 prompt）、`palette`（提取配色方案）。元数据记录在 prompt 文件的 frontmatter 中，确保可复现性。

### 2.6 输出文件结构

```
infographic/{topic-slug}/
├── source-{slug}.{ext}          # 原始内容
├── analysis.md                  # 内容分析
├── structured-content.md        # 结构化内容
├── prompts/infographic.md       # 完整 prompt（可复现记录）
└── infographic.png              # 最终图片
```

每个中间产物都持久化，既是调试手段，也是复现保障。

---

## 三、核心能力拆解

### 3.1 Layout 全景表（21 种，按用途分类）

| 用途分类 | Layout | 适用场景 |
|----------|--------|----------|
| **时间/流程** | `linear-progression` | 时间线、步骤教程 |
| | `winding-roadmap` | 旅程、里程碑 |
| | `circular-flow` | 循环流程 |
| | `funnel` | 转化漏斗 |
| **对比/分类** | `binary-comparison` | A vs B |
| | `comparison-matrix` | 多因素对比 |
| | `periodic-table` | 分类集合 |
| | `venn-diagram` | 交叉概念 |
| **层次/结构** | `hierarchical-layers` | 金字塔、优先级 |
| | `tree-branching` | 分类树 |
| | `hub-spoke` | 中心辐射 |
| | `structural-breakdown` | 爆炸图 |
| **叙事/概览** | `bento-grid` | 多主题概览（默认） |
| | `comic-strip` | 叙事、故事 |
| | `story-mountain` | 情节弧线 |
| | `iceberg` | 表面 vs 深层 |
| | `bridge` | 问题-解决方案 |
| **数据/专业** | `dashboard` | KPI、指标 |
| | `isometric-map` | 空间关系 |
| | `jigsaw` | 互锁部件 |
| | `dense-modules` | 高密度信息 |

### 3.2 Style 全景表（22 种，按风格分类）

| 风格分类 | Style | 视觉特征 |
|----------|-------|----------|
| **手绘/有机** | `craft-handmade`（默认） | 手绘纸艺 |
| | `storybook-watercolor` | 水彩绘本 |
| | `morandi-journal` | 莫兰迪色手帐 |
| | `hand-drawn-edu` | 马卡龙色教育手绘 |
| **3D/质感** | `claymation` | 黏土动画 |
| | `origami` | 折纸几何 |
| | `lego-brick` | 乐高积木 |
| **复古/艺术** | `aged-academia` | 学术复古 |
| | `pixel-art` | 8-bit 像素 |
| | `retro-pop-grid` | 70 年代波普 |
| | `retro-popup-pop` | 复古弹窗拼贴 |
| **专业/现代** | `corporate-memphis` | 扁平矢量 |
| | `technical-schematic` | 工程蓝图 |
| | `ui-wireframe` | 灰度线框 |
| | `pop-laboratory` | 实验室坐标网格 |
| **主题化** | `chalkboard` | 黑板粉笔 |
| | `cyberpunk-neon` | 赛博霓虹 |
| | `bold-graphic` | 漫画风 |
| | `kawaii` | 日系可爱 |
| | `subway-map` | 地铁图 |
| | `ikea-manual` | 极简线稿 |
| | `knolling` | 平铺俯拍 |

### 3.3 推荐组合表（18 种）

Skill 内置 18 种经过验证的最佳搭配，覆盖高频场景。例如：

| 场景 | 推荐组合 |
|------|----------|
| 时间线 | `linear-progression` + `craft-handmade` |
| 技术指南 | `dense-modules` + `pop-laboratory` |
| 产品指南 | `dense-modules` + `morandi-journal` |
| 教育图解 | `hub-spoke` + `hand-drawn-edu` |
| 旅程地图 | `winding-roadmap` + `storybook-watercolor` |

### 3.4 Keyword Shortcuts 表

| 用户关键词 | 映射 Layout | 推荐 Styles | 默认比例 |
|-----------|-------------|-------------|----------|
| 高密度信息大图 / high-density-info | `dense-modules` | morandi-journal, pop-laboratory, retro-pop-grid, retro-popup-pop | portrait |
| 信息图 / infographic | `bento-grid` | craft-handmade | landscape |

### 3.5 结构化内容模板

`structured-content-template.md` 定义了从"分析"到"设计师可读格式"的桥接结构，包含：标题 → 学习目标 → 逐节内容（Key Concept / Content / Visual Element / Text Labels）→ 逐字数据点 → 设计指令。这种分层确保 prompt 可以精确组装。

### 3.6 Analysis Framework

基于教学设计（Instructional Design）理论的分析框架，包含 6 个维度：内容类型分类 → 学习目标识别 → 受众分析 → 复杂度评估 → 视觉机会映射 → 数据逐字提取。每个维度都有对应的 layout/style 信号。

### 3.7 安全设计：Strip Credentials

在 Core Principles 和 Step 2 规则中反复强调："strip any credentials, API keys, tokens, or secrets before including in outputs"——防止用户粘贴的源内容中包含敏感信息被原样写入公开的 prompt 文件或图片中。

---

## 四、Prompt Engineering 学习点

### 4.1 Keyword Shortcuts 作为"意图识别捷径"

传统做法是让 AI 分析内容后推断最佳 layout，但这有推断失败的风险。Keyword Shortcuts 的设计模式是：**在用户显式表达意图时，直接跳过推断**。这种"关键词 → 组合"的硬映射在大参数空间中能显著减少交互轮次。

### 4.2 推荐组合表的"最佳实践内置"思路

462 种组合对用户而言是决策负担。通过内置 18 种推荐组合（Recommended Combinations），将经验沉淀为 Skill 内置知识，降低用户决策成本。这类似于"预设模板"模式——不限制自由度，但提供快车道。

### 4.3 Confirmation Policy 中的措辞技巧

> "Treat explicit skill invocation, a file path, a matched keyword shortcut, EXTEND.md defaults, and the documented default combination as **recommendation inputs only**. None of them authorizes skipping confirmation."

这段 prompt 的精妙之处在于**穷举所有可能被 AI 误解为"用户已确认"的信号**，然后逐一声明它们不构成确认授权。这种"负面清单"写法比简单说"必须确认"更能防止 AI 推断跳过。

### 4.4 Aspect Ratio 的双入口设计

```
Named presets: landscape (16:9), portrait (9:16), square (1:1)
Custom W:H:   任意比例如 3:4, 4:3, 2.35:1
```

既降低了普通用户的认知门槛（选名字即可），又满足了专业用户的精确需求（自定义比例）。这是参数设计的经典"分层暴露"模式。

### 4.5 值得借鉴的写法摘录

**摘录 1 — Prompt file requirement (hard)**：
> "Write each image's full, final prompt to a standalone file under `prompts/` BEFORE invoking any backend. The backend receives the prompt file; the file is the reproducibility record."

**点评**：将"先写文件再调用后端"定义为硬性规则。关键词 `(hard)` 显式标注严格程度，`reproducibility record` 解释了原因——AI 在理解"为什么"后更不容易违反规则。

**摘录 2 — Image Generation Tools 的优先级链**：
> "Current-request override > Saved preference > Auto-select"

**点评**：用清晰的优先级数字（1-4）编排决策逻辑，并在每层内部也有子逻辑（如 Auto-select 内先查 runtime-native，再查 non-native，最后 ask）。这种多层瀑布式决策描述是 Skill prompt 中处理"多后端兼容"的典范写法。

**摘录 3 — ⛔ Never substitute SVG, HTML...**：
> "Never substitute SVG, HTML, canvas, or other code-based rendering for raster image generation."

**点评**：用 ⛔ emoji 做视觉标记 + 明确列举被禁止的替代方案。防止 AI 在找不到后端时"创造性地"用 HTML 画图——这种反模式在实践中确实会发生。

---

## 五、教学小结

### Takeaways

1. **正交双维度设计** — Layout（结构）× Style（表现）的分离设计，使 N+M 个定义文件产生 N×M 种组合能力，是"乘法扩展性"的经典范例。

2. **硬门控 > 软提示** — 在 AI 容易"自作主张"的环节（如跳过确认直接生成），用 Confirmation Policy 的穷举式负面清单做硬门控，比"请记住确认"有效得多。

3. **大参数空间的用户引导三板斧** — Keyword Shortcuts（高频场景快速命中）+ Recommended Combinations（最佳实践内置）+ First-Time Setup + Step 4 确认（兜底安全网）。三者协同，让 462 种组合不再是选择负担。

4. **中间产物全持久化** — analysis.md → structured-content.md → prompts/infographic.md → 最终图片。每步可回溯、可复现、可单独修改后重新生成。

5. **安全意识嵌入日常** — "Strip credentials/secrets" 规则散布在 Core Principles 和具体步骤中，将安全从"额外检查"变为"默认行为"。

### 与 baoyu-image-cards 的定位差异

| 维度 | baoyu-infographic | baoyu-image-cards |
|------|-------------------|-------------------|
| **输出** | 单张高密度信息图 | 多张系列卡片 |
| **核心能力** | 462 种布局×风格组合 | 统一视觉风格的多页内容 |
| **典型场景** | "用一张图解释 X" | "把文章拆成 N 张卡片发小红书" |
| **信息密度** | 单图信息量极大 | 每张卡片信息量适中、易于逐张浏览 |
| **交互重点** | 选对组合（layout+style） | 内容分页与视觉一致性 |

一个是"浓缩为一"，一个是"展开为多"——二者互补而非竞争。
