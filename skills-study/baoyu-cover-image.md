# baoyu-cover-image 深度解读

## 一、基础信息速览

| 维度 | 说明 |
|------|------|
| **名称/版本** | `baoyu-cover-image` v1.56.2 |
| **一句话定位** | 五维定制系统生成文章封面图（Type × Palette × Rendering × Text × Mood + Font） |
| **触发关键词** | "generate cover image"、"create article cover"、"make cover"、"生成封面图" |
| **前置依赖** | 至少一个光栅图像生成后端（Codex `imagegen`、Hermes `image_generate`、`baoyu-imagine` 等）；首次运行需完成 EXTEND.md 偏好配置（⛔ BLOCKING） |
| **适用场景** | 文章/博客封面、公众号头图、社交媒体分享卡片、YouTube 缩略图 |
| **输入→输出** | 文章文件/粘贴内容/主题描述 + 可选参考图 → `prompts/cover.md` prompt 文件 + `cover.png` 封面图 |

---

## 二、架构与设计模式分析

### 6 步 Workflow 流程图（Step 0 → Step 5）

```
Step 0: Preferences ⛔       Step 1: Analyze           Step 2: Confirm ⚠️
┌────────────────────┐       ┌──────────────────┐      ┌──────────────────┐
│ 检查 EXTEND.md     │       │ 保存参考图 (refs)  │      │ AskUserQuestion  │
│ 优先级: project >  │──────▶│ 保存源内容        │─────▶│ Q1: Type         │
│   XDG > home       │       │ 分析内容/语言     │      │ Q2: Palette      │
│                    │       │ 确定输出目录      │      │ Q3: Rendering    │
│ 未找到 → 首次设置  │       │ 深度分析参考图 ⚠️  │      │ Q4: Font+Settings│
│ (⛔ 阻塞式)        │       └──────────────────┘      └────────┬─────────┘
└────────────────────┘                                    --quick│跳过
                                                               ▼
Step 5: Report              Step 4: Generate           Step 3: Prompt
┌──────────────────┐        ┌──────────────────┐      ┌──────────────────┐
│ 完成报告         │◀───────│ 选择后端          │◀─────│ 保存到 prompts/  │
│ 参数 + 文件清单   │        │ 处理参考图 --ref  │      │ cover.md         │
│ 输出目录路径      │        │ 调用生成          │      │ YAML frontmatter │
└──────────────────┘        │ 失败自动重试 ×1   │      │ + 结构化 body    │
                            └──────────────────┘      └──────────────────┘
```

### 五维定制系统（Type × Palette × Rendering × Text × Mood + Font）

这是该 Skill 的核心设计亮点——用 5+1 维度来精确控制封面图的视觉输出：

- **Type**（6 种）：封面的构图类型——hero/conceptual/typography/metaphor/scene/minimal
- **Palette**（11 种）：色彩方案——warm/elegant/cool/dark/earth/vivid/pastel/mono/retro/duotone/macaron
- **Rendering**（7 种）：渲染风格——flat-vector/hand-drawn/painterly/digital/pixel/chalk/screen-print
- **Text**（4 级）：文字密度——none/title-only/title-subtitle/text-rich
- **Mood**（3 级）：情绪强度——subtle/balanced/bold
- **Font**（4 种）：字体风格——clean/handwritten/serif/display

五维独立组合通过 **兼容性矩阵**（Palette×Rendering、Type×Rendering、Type×Text、Type×Mood、Font×Rendering）来约束推荐。矩阵使用 ✓✓/✓/✗ 三级标记，不是硬性禁止，而是"不推荐"——给用户最终决策权的同时提供专业建议。

### EXTEND.md 配置体系与首次运行阻塞

EXTEND.md 是持久化用户偏好的核心机制。查找优先级：

1. `.baoyu-skills/baoyu-cover-image/EXTEND.md`（项目级）
2. `${XDG_CONFIG_HOME}/baoyu-skills/baoyu-cover-image/EXTEND.md`（XDG 标准）
3. `$HOME/.baoyu-skills/baoyu-cover-image/EXTEND.md`（用户级）

**⛔ BLOCKING 设计**：若未找到 EXTEND.md，必须完成首次设置（8 个问题一次性收集：watermark、type、palette、rendering、aspect、output dir、quick mode、保存位置），**禁止**在此期间询问任何其他问题。这种"前置阻塞"确保了后续步骤有稳定的配置基础。

### Image Generation Tools 后端选择规则

4 级优先级瀑布：当前请求显式指定 → EXTEND.md `preferred_image_backend` → Auto-select（Codex `imagegen` > 运行时原生工具 > 唯一非原生后端 > 多后端则询问）→ 无可用后端通知用户。

**硬约束**：⛔ 绝不用 SVG/HTML/Canvas 代替光栅图像生成。即便内容看起来像"图表"，也必须使用 raster backend。

### Confirmation Policy（--quick 快速模式 vs 确认模式）

默认行为是 **确认后才生成**，文件路径、关键词匹配、EXTEND.md 默认值都**仅作为推荐**，不能跳过确认。跳过条件：
- `--quick` 标志或 `quick_mode: true`
- "直接生成"、"不用确认"、"跳过确认"等自然语言
- 跳过时仍必须声明假设参数，保证透明度

### 输出目录策略

| 模式 | 路径 | 典型场景 |
|------|------|---------|
| `independent`（默认） | `cover-image/{topic-slug}/` | 粘贴内容/独立创作 |
| `imgs-subdir` | `{article-dir}/imgs/` | 文章配套目录 |
| `same-dir` | `{article-dir}/` | 与文章同目录 |

目录内形成自包含结构：`source-*.md` + `refs/` + `prompts/cover.md` + `cover.png`。

### Reference Images 处理（双路径设计）

参考图中包含人物时的关键分支：

| 后端能力 | 处理方式 |
|---------|---------|
| 支持 `--ref`（Google/OpenAI/Seedream 4.0+） | 复制图片到 `refs/`，生成时直接传递 `--ref`，无需描述文件 |
| 不支持 `--ref`（Jimeng/Seedream 3.0） | 复制图片 + 创建 `refs/ref-NN-*.md` 描述文件，将外貌描述嵌入 prompt 文本 |

深度分析要求提取**具体可复现**的元素（hex 色值、具体图案描述、精确布局比例），用 "MUST"/"REQUIRED" 前缀写入 prompt。

---

## 三、核心能力拆解

### Type (6) × Palette (11) × Rendering (7) = 462 种基础组合

仅前三维就有 462 种可能。加上 Text (4) × Mood (3) × Font (4)，理论总组合高达 **22,176 种**。通过以下机制管理这个巨大的参数空间：

1. **Auto-selection**：基于内容信号的查找表映射，每个维度有独立的信号→值对照表
2. **Style Presets**：25 个预设快捷方式，每个展开为 palette + rendering 组合（如 `--style chalkboard` = dark + chalk）
3. **兼容性矩阵**：5 张交叉表指导推荐组合，Step 2 中自动将 ✓✓ 排在选项首位
4. **默认值**：Type=auto, Palette=auto, Rendering=auto, Text=title-only, Mood=balanced, Font=clean

### Text 层级

| 级别 | 可视面积 | 文字元素 |
|------|---------|---------|
| `none` | 100% | 无文字，纯视觉 |
| `title-only` | 85% | 仅标题（默认） |
| `title-subtitle` | 75% | 标题 + 副标题 |
| `text-rich` | 60% | 标题 + 副标题 + 2-4 标签 |

关键规则：标题必须使用用户/源内容的**原始标题**，绝不自行编造。

### Mood 层级对渲染的影响

Mood 不仅改变色彩饱和度，还影响渲染的物理特征——例如 `bold` 下 flat-vector 线条更粗、hand-drawn 笔触更重、screen-print 半调更密。这种"Mood 修饰 Rendering"的设计让同一个 rendering 在不同 mood 下呈现不同质感。

### Font 选择与兼容性

Font 维度与 Rendering 存在强兼容约束：clean 最适合 flat-vector/digital，handwritten 最适合 hand-drawn/painterly/chalk，display 则是"万金油"（与 flat-vector/digital/pixel/screen-print 都高度兼容）。这体现了"视觉语言一致性"原则。

### Style Presets 快捷方式

25 个预设覆盖常见场景：`elegant`（elegant+hand-drawn）、`blueprint`（cool+digital）、`chalkboard`（dark+chalk）、`cinematic`（duotone+screen-print）等。预设可被 `--palette`/`--rendering` 显式覆盖，实现"预设为基、按需微调"。

### Auto-selection 自动推荐逻辑

每个维度独立运行信号匹配：
- 文章提到"架构、系统、API" → Type=`conceptual`, Palette=`cool`, Rendering=`digital`
- 文章关于"个人故事、情感" → Type=`scene`, Palette=`warm`, Font=`handwritten`

这是一种**决策外化为查找表**的策略，将 AI 的隐式推理转为确定性的表匹配。

### 构图原则

- **40-60% 留白**：保证视觉呼吸感
- **视觉锚点**：主元素居中或偏左放置
- **人物处理**：仅用简化剪影；**禁止写实人物**
- **标题忠实**：使用用户原始标题，不发挥创造

---

## 四、Prompt Engineering 学习点

### 多维度参数设计如何避免"选择困难"

22,176 种组合对用户来说是灾难性的选择负担。Skill 用三层机制化解：
1. **Auto-selection**（查找表）提供推荐值——用户不需要了解所有选项
2. **Style Presets**（快捷方式）将常见组合命名——降低认知负荷
3. **交互确认**（AskUserQuestion）每个问题把推荐项置顶并附带理由——用户只需"接受推荐"或"点选替代"

这种"预设 + 推荐 + 确认"的三层设计模式，适用于任何高维度参数空间的用户交互设计。

### Confirmation Policy 的两种模式设计

确认模式不是简单的 boolean 开关，而是"默认确认 + 多种跳过触发"：
- CLI 标志：`--quick`
- 自然语言："直接生成"、"不用确认"
- 配置持久化：`quick_mode: true`

同时，跳过确认后仍要**声明假设参数**——这既是透明度保障，也给用户"看一眼就知道对不对"的快速验证机会。

### Step 1 中人物照片的双路径处理设计

这是一个教科书级的"能力降级"设计：

```
参考图含人物？
├── 后端支持 --ref → 直接传图，模型"看脸"
└── 后端不支持 --ref → 生成文字描述（发色、眼镜、肤色、服装）
                       → 嵌入 prompt 作为 MUST/REQUIRED 指令
```

关键洞察：当硬件/API 能力不足时，通过"将视觉信息转化为文本指令"实现降级，而非简单放弃。这种 graceful degradation 思维在 Skill 设计中非常值得借鉴。

### AskUserQuestion 的信息密度优化

Step 2 的 4 个问题（Type/Palette/Rendering/Font+Settings）合并为**单次** AskUserQuestion 调用，每个问题：
- 推荐项置顶 + "(Recommended)" 标记 + 理由
- 替代项展示简短描述（一句话定位）
- "Other" 选项兜底自定义输入

相比逐轮询问，这种"批量问题 + 结构化选项"设计将交互轮次从 6+ 轮压缩到 1 轮，大幅降低用户疲劳度。

### 值得借鉴的写法

**写法一：Prompt 文件作为可复现性记录**

> **Prompt file requirement (hard)**: write each image's full, final prompt to a standalone file under `prompts/` BEFORE invoking any backend. The backend receives the prompt file (or its content); the file is the reproducibility record and lets you switch backends without regenerating prompts.

点评：将"先落盘再执行"设计为 hard requirement 而非 best practice。Prompt 文件成为可审查、可重试、可跨后端迁移的资产。当后端换了（从 Codex 换到 baoyu-imagine），prompt 不需要重写——这是"创意决策"与"执行引擎"解耦的最佳实践。

**写法二：Color Constraint 防御性指令**

> Color constraint: Color values (#hex) and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text in the image.

点评：这是对图像生成模型已知缺陷的精准防御。模型容易将 prompt 中的文字内容（如 "#2D4A3E"）渲染为画面中的可见文本。通过在 prompt template 中固化这条约束，从源头消除问题。这种"已知 AI 缺陷 → 显式防御规则"的模式应成为 Prompt Engineering 的标准实践。

**写法三：References 的"MUST INCORPORATE"强制语义**

> Reference elements in body MUST be detailed, prefixed with "MUST"/"REQUIRED", with integration approach.

点评：当 reference images 是高优先级输入时，仅仅传 `--ref` 参数是不够的——模型经常忽略视觉参考。Skill 要求在 prompt body 中用 "MUST"/"REQUIRED" 前缀逐条列出参考元素，并写明"集成方式"（具体布局指令）。这种"双保险"策略（文件引用 + 文本强调）对任何依赖参考素材的生成任务都适用。

---

## 五、教学小结

### Key Takeaways

1. **五维分离 + 兼容矩阵 = 可控的组合爆炸**：每个维度独立变化，通过 5 张兼容矩阵给出推荐组合而非硬性约束。用户既能享受"一键预设"的便捷，也能精细调整任意维度。设计高维参数空间时，"维度正交 + 推荐矩阵"优于"扁平选项列表"。

2. **首次设置⛔ BLOCKING 保证了状态一致性**：在没有配置的情况下强制完成初始化，避免后续步骤因缺少偏好值而反复询问或使用不一致的默认值。这种"前置阻塞式初始化"模式适用于任何有持久化配置需求的 Skill。

3. **三层机制化解选择困难**：Auto-selection（查找表推荐）+ Style Presets（命名快捷方式）+ Confirmation（结构化选项卡），三层协作将 22,000+ 种组合压缩为"接受推荐或点选替代"的轻量决策。

4. **Graceful Degradation 而非 Hard Failure**：人物照片在 `--ref` 不可用时转为文字描述嵌入 prompt，而非报错或放弃。设计 Skill 时应预判能力缺失场景并规划降级路径。

5. **Prompt 文件是第一公民**：将 prompt 视为独立资产（先写后用、独立存储、可复现、可迁移），而非一次性的 API 调用参数。这让调试、迭代和后端切换都变得轻量。

### 如何设计高维度参数空间的用户交互

baoyu-cover-image 的做法可以总结为 4 条原则：

1. **推荐在前、选择在后**：每个维度先通过内容信号计算推荐值，用户看到的是"推荐 + 备选"而非空白选择
2. **一次批量、减少轮次**：4 个问题合并为单次 AskUserQuestion，减少来回交互
3. **预设降维**：25 个 Style Presets 将 palette+rendering 二维降为一维选择
4. **显式跳过机制**：`--quick` 给高效用户一条"绿色通道"，不强制所有人走完整流程

### 与 baoyu-article-illustrator 的定位差异

| 维度 | baoyu-cover-image | baoyu-article-illustrator |
|------|-------------------|--------------------------|
| **产出数量** | 单张封面图 | 多张插图（散布全文） |
| **核心职责** | "一图定调"——吸引点击 | "图文并茂"——辅助理解 |
| **维度体系** | 5+1 维（Type/Palette/Rendering/Text/Mood/Font） | 3 维（Type/Style/Palette） |
| **位置决策** | 不需要（封面就是封面） | 需要分析"在哪里插图" |
| **构图约束** | 40-60% 留白、禁止写实人物 | 随 type 变化（flowchart/timeline 等结构化布局） |
| **复杂度来源** | 参数组合的广度（462×48=22,176） | 批量生成的编排（位置分析+outline+多 prompt） |

两者定位互补：cover-image 聚焦"第一印象"的单图极致优化，article-illustrator 聚焦"阅读体验"的多图系统编排。
