# baoyu-comic Skill 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-comic` v1.56.1 |
| **一句话定位** | 知识漫画创建器——将教育内容转化为多页漫画 PDF |
| **触发关键词** | 知识漫画、教育漫画、biography comic、tutorial comic、Logicomix-style comic |
| **前置依赖** | `bun` 或 `npx`（用于运行 `merge-to-pdf.ts` 脚本）+ 至少一个 raster 图像生成后端 |
| **适用场景** | 将技术教程、人物传记、历史事件、心理学/商业叙事等内容转化为带叙事结构的多页漫画 |
| **输入** | 文本内容（文件路径或粘贴文本）+ 可选的风格/色调/布局选项 + 可选参考图片 |
| **输出** | `comic/{topic-slug}/` 目录，含分析文档、分镜稿、角色定义、逐页 prompt、逐页 PNG 图片、合并 PDF |

---

## 二、架构与设计模式分析

### 2.1 九步 Workflow 完整流程

这个 skill 设计了一条**九步流水线**，每一步产出明确的中间产物，环环相扣：

```
Step 1: Setup & Analyze
  ├─ 1.1 加载 EXTEND.md 偏好 ⛔ BLOCKING
  ├─ 1.2 深度内容分析 → analysis.md
  └─ 1.3 检查已有目录 ⚠️ REQUIRED
Step 2: Confirmation（风格 + 审阅偏好）⚠️ REQUIRED
Step 3: Generate storyboard + characters
Step 4: Review outline（条件性）
Step 5: Generate prompts → prompts/*.md
Step 6: Review prompts（条件性）
Step 7: Generate images
  ├─ 7.1 Character sheet → characters/characters.png
  └─ 7.2 Pages（with --ref if sheet exists）
Step 8: Merge to PDF → {slug}.pdf
Step 9: Completion report
```

这条流水线的核心设计理念是**可暂停、可审阅、可断点续传**。Step 4 和 Step 6 是用户在 Step 2 中自主选择的条件审阅门，避免了"一路到底不可控"和"每一步都要确认太啰嗦"的两个极端。

### 2.2 三层配置体系

配置的优先级形成一个**三层漏斗**：

| 层级 | 来源 | 作用 |
|------|------|------|
| **持久化配置** | `EXTEND.md`（项目级 > 用户级） | watermark、偏好风格/色调/布局、语言、角色预设 |
| **命令行参数** | `--art`, `--tone`, `--layout`, `--lang`, `--ref` 等 | 单次运行覆盖 |
| **运行时检测** | 内容信号分析 + auto-selection 矩阵 | 智能推荐默认值 |

EXTEND.md 的设计尤其值得学习：它不仅存储偏好，还通过**首次运行引导流程**（first-time setup）实现了"零配置即可用、一次配置永久生效"的体验。当 EXTEND.md 不存在时，Step 1.1 是 **BLOCKING** 的——必须完成首次设置才能继续，这确保了后续步骤不会因缺少配置而出错。

### 2.3 Image Generation Tools 后端选择规则

图像生成后端的选择是一个**四级 fallback 链**：

```
1. 用户当前消息指定的后端
   ↓ 未指定
2. EXTEND.md 中 preferred_image_backend 设置
   ↓ 为 auto / 未设置 / 不可用
3. Auto-select:
   a. Codex imagegen（运行时原生，最高优先）
   b. 其他运行时原生工具（如 Hermes image_generate）
   c. 唯一已安装的非原生后端（如 baoyu-imagine）
   d. 多个非原生后端 → 询问用户
   ↓ 都不可用
4. 告知用户，询问如何处理
```

这种设计的精妙之处在于：**一次选择，全局复用**。后端只在会话开始时解析一次，后续所有页面共享同一后端，避免了重复询问。同时 `preferred_image_backend: ask` 选项允许高级用户每次运行时手动选择。

### 2.4 Reference Images 系统

Reference Images 支持三种使用模式，形成了一套灵活的**视觉参考体系**：

| 模式 | 效果 |
|------|------|
| `direct` | 将文件作为参考图直接传给后端（逐页或选定页面） |
| `style` | 提取线条处理、纹理、氛围等风格特征，注入每页 prompt |
| `palette` | 提取 hex 色值，注入每页 prompt |

用户参考图和自动生成的 Character Sheet 是**两套独立系统**，可以共存——前者引导整体视觉风格，后者锚定角色外观一致性。

### 2.5 Character Sheet 角色一致性链

这是整个 skill 中最精巧的设计之一。AI 图像生成最大的痛点是**跨图一致性**——同一角色在不同页面长得不一样。baoyu-comic 用一条**生成→压缩→引用**链来缓解这个问题：

```
Step 3: 文本定义角色 → characters/characters.md
Step 7.1: 生成角色参考表 → characters/characters.png
         → JPEG 压缩（sips/pngquant）避免 API payload 过大
Step 7.2: 每页生成时 --ref characters-compressed.jpg
         → 失败? 再压缩重试
         → 仍失败? 回退到纯文本描述嵌入 prompt
```

三种策略（A: `--ref` 传递角色表 / B: 嵌入角色描述到 prompt / C: 纯 inline 描述）形成**渐进降级**，确保在任何后端能力下都能工作。

### 2.6 脚本架构

脚本层非常轻量——只有一个 `scripts/merge-to-pdf.ts`，负责将所有生成的 PNG 页面合并为 PDF。运行方式通过 `${BUN_X}` 变量适配 `bun` 或 `npx -y bun`。整个 skill 的"重逻辑"全部在 SKILL.md 的 prompt 中，脚本只处理 Agent 无法直接完成的二进制操作（图片合并为 PDF）。

### 2.7 文件组织结构

```
comic/{topic-slug}/
├── source-{slug}.{ext}          # 源内容
├── analysis.md                  # 内容分析
├── storyboard.md                # 分镜稿
├── characters/
│   ├── characters.md            # 角色定义（文本）
│   └── characters.png           # 角色参考表（图像）
├── refs/                        # 用户参考图副本
├── prompts/
│   └── NN-{cover|page}-[slug].md  # 逐页 prompt
├── NN-{cover|page}-[slug].png   # 逐页生成图
└── {topic-slug}.pdf             # 最终 PDF
```

每个产出物都有明确的命名规则和备份机制（`-backup-YYYYMMDD-HHMMSS` 后缀），确保可追溯、不丢失。

---

## 三、核心能力拆解

### 3.1 三维组合系统：Art Style x Tone x Layout

这是 baoyu-comic 的**视觉设计空间**：

- **Art Style (6)**: `ligne-claire`（丁丁历险记风）、`manga`、`realistic`、`ink-brush`（水墨）、`chalk`（粉笔）、`minimalist`
- **Tone (7)**: `neutral`、`warm`、`dramatic`、`romantic`、`energetic`、`vintage`、`action`
- **Layout (7)**: `standard`、`cinematic`、`dense`、`splash`、`mixed`、`webtoon`、`four-panel`

理论上有 6 x 7 x 7 = 294 种组合，但通过 Compatibility Matrix 进行了"推荐/可用/避免"三级标注。例如 `minimalist` 最佳搭配只有 `neutral`，与 `dramatic`/`action`/`romantic` 都标记为 Avoid。这让 Agent 在推荐时有据可依，而不是随意组合。

### 3.2 五个预设及其特殊规则

预设不只是 art + tone 的快捷方式——每个预设都携带**专属规则集**：

| 预设 | 基底 | 核心特殊规则 |
|------|------|------------|
| **ohmsha** | manga + neutral | 必须用视觉隐喻解释概念、禁止 talking heads、哆啦A梦默认角色、道具揭示模式 |
| **wuxia** | ink-brush + action | 气效果、战斗视觉、大气元素 |
| **shoujo** | manga + romantic | 装饰元素、眼部细节、浪漫节拍 |
| **concept-story** | manga + warm | 视觉符号系统、成长弧线、对话+动作平衡 |
| **four-panel** | minimalist + neutral + four-panel | 严格起承转合四格结构、黑白+点彩、火柴人角色、单页故事 |

ohmsha 预设尤其丰富：它定义了角色原型（Student / Mentor / Challenge / Support）、页面标题约定（叙事标题而非章节标题）、"道具揭示"叙事模式，以及结尾必须包含的四个要素。这本质上是一个**完整的漫画创作方法论**。

### 3.3 Partial Workflow 选项

四个选项实现了流水线的**断点续传**：

| 选项 | 执行范围 | 使用场景 |
|------|---------|---------|
| `--storyboard-only` | Step 1-3 | 先审阅分镜再继续 |
| `--prompts-only` | Step 1-5 | 先审阅 prompt 再继续 |
| `--images-only` | Step 7-9 | 编辑 prompt 后重新生成图片 |
| `--regenerate N` | Step 7（局部）| 只重新生成指定页面 |

这让用户可以在任意阶段介入修改，然后从断点继续，而不需要从头开始。

### 3.4 语言检测优先级链

```
--lang 显式指定 > EXTEND.md language 设置 > 用户对话语言 > 源内容语言
```

所有交互内容（分镜描述、选项确认、进度更新、错误信息）都使用检测到的语言输出，但技术术语保留英文。

### 3.5 Prompt File 可复现性要求

> **Prompt file requirement (hard)**: 在调用任何后端之前，必须先将完整 prompt 写入 `prompts/` 下的独立文件。

这不是可选的最佳实践，而是**硬性要求**。设计哲学是：prompt 文件是**可复现性的记录**，也是后端切换的基础——换一个图像生成后端时，不需要重新生成 prompt，直接用已有文件即可。

### 3.6 角色表压缩策略

Character Sheet 在作为 `--ref` 传递时会遇到 API payload 大小限制。解决方案是**渐进降级**：

```
原始 PNG → JPEG 压缩 (quality=80) → 重试
                                    ↓ 仍失败
                              降低分辨率 (1024px) → 重试
                                                  ↓ 仍失败
                                            放弃 --ref，纯文本描述
```

macOS 下用 `sips`，其他平台用 `pngquant`，体现了**跨平台适配**意识。

---

## 四、Prompt Engineering 学习点

### 4.1 Progress Checklist 的视觉化设计

```
Comic Progress:
- [ ] Step 1: Setup & Analyze
  - [ ] 1.1 Preferences (EXTEND.md) ⛔ BLOCKING
  - [ ] 1.2 Analyze, 1.3 Check existing
- [ ] Step 2: Confirmation ⚠️ REQUIRED
...
```

用 Markdown checkbox 格式让 Agent **追踪自己的进度**。这不是给用户看的 UI，而是给 Agent 的**认知脚手架**——在长流程中防止 Agent 迷失当前位置或跳过步骤。每个 checkbox 是一个**隐式的状态机节点**。

### 4.2 ⛔ BLOCKING 与 ⚠️ REQUIRED 的层级设计

SKILL.md 定义了两个不同严重级别的约束标记：

- **⛔ BLOCKING**：完全阻塞后续流程，不满足条件不能继续（如 EXTEND.md 首次设置）
- **⚠️ REQUIRED**：必须执行但不会阻塞前置步骤（如 Step 2 确认、Step 1.3 目录检查）

这两个层级让 Agent 清楚地知道**哪些步骤绝对不能跳过**。在复杂 prompt 中，单纯说"必须执行"效果有限，而引入视觉化的严重级别标记，让约束力变得立体。

### 4.3 "Never substitute SVG/HTML for raster" 硬约束

> ⛔ Never substitute SVG, HTML, canvas, or other code-based rendering for raster image generation.

这条规则解决了 LLM 的一个常见倾向：当被要求生成图片时，Agent 可能"偷懒"用 SVG 代码或 HTML/CSS 来模拟。Skill 用 ⛔ 标记加粗体明确禁止，并给出了完整的"如果做不到就问用户"的降级路径。**与其让 Agent 产出低质量替代品，不如让它诚实地告知限制**——这是一个重要的 prompt 设计理念。

### 4.4 值得借鉴的写法摘录

**摘录 1：后端选择的 Auto-select 链**

> 3. Auto-select (when the preference is auto, unset, or the pinned backend isn't available):
>    - Codex (imagegen) — first, inspect your available-skills / tool inventory. If a skill named imagegen is listed, you are running inside Codex and MUST use it...
>    - Other runtime-native tools — if the runtime exposes a different native image tool...
>    - Otherwise, if exactly one non-native backend is installed, use it.
>    - Otherwise (multiple non-native backends with no runtime-native tool), ask the user once.

**点评**：这段 prompt 的精妙在于它用**环境检测**（"inspect your available-skills"）而非硬编码来决定行为。它教会 Agent **自省运行时能力**，并据此做出决策。四级 fallback 链的写法——从最优到最差逐级描述——是处理"不确定运行环境"的范式。

**摘录 2：ohmsha 的"Wrong vs Right"对比表**

> | Concept | Wrong (Talking Head) | Right (Visual Metaphor) |
> |---------|---------------------|------------------------|
> | Attention mechanism | Character points at formula on blackboard | "Attention Flashlight" gadget illuminates key words in dark room |
> | Gradient descent | "The algorithm minimizes loss" | Character rides ball rolling down mountain valley |

**点评**：用**反面示例 + 正面示例**的对比表来约束 Agent 行为，比单纯的规则描述有效得多。Agent 能从具体的 wrong/right 对比中归纳出"什么是视觉隐喻"，这比抽象定义更容易被遵循。

**摘录 3：`--ref` failure recovery 的渐进降级**

> 1. Compress/convert reference image
> 2. Retry with compressed image as --ref
> 3. If still fails: Fall back to Strategy C — generate WITHOUT --ref, with character descriptions embedded in prompt text

**点评**：这段展示了一个工程化的**错误恢复策略**。它不是简单的"失败就报错"，而是定义了三步降级路径，确保 Agent 在任何情况下都能继续工作。这种"graceful degradation"思维是复杂 skill 必备的设计意识。

---

## 五、教学小结

### 这个 skill 教会我们什么

1. **中间产物是流水线的灵魂**：每一步（analysis.md → storyboard.md → prompts/*.md → *.png → .pdf）都产出独立的文件，既是下一步的输入，也是可审阅、可修改、可复现的记录。这让 9 步流程不再是一个黑箱，而是一条透明的生产线。

2. **约束要分层级，不能一刀切**：⛔ BLOCKING / ⚠️ REQUIRED / 一般性建议——三个层级让 Agent 知道哪些规则绝对不能违反、哪些必须执行但有灵活空间、哪些是推荐但可选的。在复杂 skill 中，没有层级的约束最终会被 Agent 全部忽略或全部遵循。

3. **为运行环境的不确定性设计**：后端选择的 4 级 fallback、跨平台的压缩命令（sips vs pngquant）、User Input Tools 的 3 级优先级——整个 skill 假设自己可能跑在任何 Agent runtime 上，并为每种情况都准备了应对方案。

4. **可复现性优于效率**：要求先写 prompt 文件再调用后端，看似多了一步，但让每次生成都有据可查、可重试、可跨后端迁移。这种"多写一个文件"的小成本换来了巨大的调试和迭代价值。

5. **用具体示例约束 Agent 行为**：无论是 ohmsha 的 wrong/right 对比表、character template 的 Turing 传记示例，还是 four-panel 的起承转合结构表，skill 大量使用**具体的、可模仿的示例**来传达抽象规则。这是 prompt engineering 中"show, don't tell"原则的典型实践。

### 复杂多步骤 skill 的设计要点

- **状态追踪机制**：用 Progress Checklist 让 Agent 自我追踪，防止在长对话中迷失进度
- **条件分支而非固定路线**：Step 4/6 是否执行由用户在 Step 2 决定，Partial Workflow 选项让用户可以从任意阶段切入
- **渐进降级**：每个可能失败的操作（图像生成、--ref 传递、后端解析）都有明确的 fallback 路径
- **关注点分离**：配置（EXTEND.md）、内容分析（analysis.md）、视觉设计（storyboard.md）、生成指令（prompts/*.md）、最终产物（*.png）——每层只关心自己的职责

### 如何管理跨步骤的一致性

角色外观一致性是 AI 漫画创作的核心挑战。baoyu-comic 的解决方案是一条**三级一致性链**：

1. **文本锚点**（Step 3）：`characters/characters.md` 用详细的文字定义角色外观（脸型、发色、服装配色 hex 值），作为所有后续步骤的"真理之源"
2. **视觉锚点**（Step 7.1）：将文字描述生成为 `characters.png` 参考表，提供 Agent 文字无法精确传达的视觉细节
3. **逐页传递**（Step 7.2）：通过 `--ref` 将角色表传递给每一页的图像生成，或在 prompt 中嵌入角色描述

三级锚点从抽象到具体递进，在 fallback 时也能优雅降级：即使角色表生成失败，纯文本描述仍能维持基本一致性。这种**冗余设计**是管理跨步骤状态一致性的关键思路。
