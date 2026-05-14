# baoyu-image-cards 深度解读：社交媒体多图卡片系列生成的设计哲学

> 本文面向想学习编写 Agent Skill 的开发者，以 `baoyu-image-cards` v1.56.2 为案例，拆解其三维组合架构、Image-1 Anchor Chain 一致性设计、Smart Confirm 交互模式，以及面向小红书/微信等平台的特化策略。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-image-cards` v1.56.2 |
| **一句话定位** | 将复杂内容拆解为 1-10 张卡通风格信息图卡片系列，专为社交媒体互动优化 |
| **触发关键词** | 小红书图片、小红书种草、小绿书、微信图文、微信贴图、image cards、图片卡片 |
| **前置依赖** | 需要图像生成后端（Codex `imagegen` / `baoyu-imagine` / 运行时原生工具） |
| **适用场景** | 种草安利、干货分享、个人故事、测评对比、教程步骤、避坑指南、清单合集 |
| **输入→输出** | 用户提供的文章/文本 + 可选参考图 → 多张 PNG 卡片（含 prompt 文件 + outline + analysis） |

**核心特色**：这不是一个简单的"调用图像 API"的 skill，而是一套完整的**社交媒体内容生产流水线**——从内容分析、大纲策划、视觉风格确认到多图串联生成，覆盖了内容创作者的全链路需求。

---

## 二、架构与设计模式分析

### 2.1 四步 Workflow 流程图

```
用户提供内容/文本
        │
        ▼
┌─────────────────────────┐
│ Step 0: Load EXTEND.md  │ ⛔ BLOCKING
│ 查找偏好设置             │
└─────────────────────────┘
        │
   ┌────┴────┐
   │ 找到？   │
   └────┬────┘
  Yes   │     No
   │    │      ├──→ 首次设置（水印 + 风格 + 保存位置）
   │    │      │    写入 EXTEND.md → 继续
   ▼    │      ▼
┌─────────────────────────┐
│ Step 1: Analyze Content │
│ 深度分析 → analysis.md   │
│ Hook 评分 / 受众画像 /    │
│ 互动设计 / 滑动流规划     │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Step 2: Smart Confirm   │ ⚠️ REQUIRED
│ 三条路径确认方案          │
│ Path A / B / C          │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Step 3: Generate Images │
│ Image-1 Anchor Chain    │
│ 逐张生成 + 进度汇报      │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Step 4: Completion      │
│ 输出结构化完成报告        │
└─────────────────────────┘
```

### 2.2 三维组合：Style (12) × Layout (8) × Palette (3)

这是本 skill 最优雅的设计之一——将视觉表现拆解为三个正交维度，自由组合：

| 维度 | 控制内容 | 数量 | 示例 |
|------|----------|------|------|
| **Style** | 视觉美学（线条、装饰、渲染风格） | 12 种 | cute / notion / chalkboard / screen-print |
| **Layout** | 信息结构（密度、排列方式） | 8 种 | sparse / dense / flow / mindmap |
| **Palette** | 配色覆盖（仅替换颜色） | 3 种（可选） | macaron / warm / neon |

**关键设计**：Palette 只替换颜色而保留 Style 的渲染规则（线条、纹理等）。比如 `--style notion --palette neon` 会让极简线条画呈现赛博朋克配色——这种正交分离让组合空间达到 12 × 8 × 4（含默认）= 384 种可能。

### 2.3 Smart Confirm 的三条路径

```
显示自动推荐方案摘要
        │
        ▼
  ┌─────┼─────────┐
  │     │         │
  ▼     ▼         ▼
Path A  Path B   Path C
快速确认 自定义    详细模式
  │     │         │
  │     │    ┌────┴────┐
  │     │    │Step 2a  │ 内容理解（卖点/受众/调性）
  │     │    │Step 2b  │ 生成 3 套大纲变体
  │     │    │Step 2c  │ 用户选择最终方案
  │     │    └─────────┘
  │     │         │
  │     ▼         │
  │  5 个维度调整   │
  │  (策略/布局/    │
  │   配色/数量/    │
  │   备注)        │
  │     │         │
  ▼     ▼         ▼
生成 outline.md → Step 3
```

- **Path A**：信任自动推荐，一键确认，适合快速出图
- **Path B**：保留推荐值作为默认，只调整关心的维度，平衡效率与控制
- **Path C**：生成 A/B/C 三套完全不同的大纲（不同结构 + 不同风格），用户可选或混搭

### 2.4 Image-1 Anchor Chain（视觉一致性链）

**这是本 skill 最核心的技术设计**。多图系列生成面临的最大挑战是：每次 AI 调用独立，角色/配色/风格会漂移。解决方案：

```
Image 1 (Cover)          Image 2              Image 3           ...
────────────────         ────────────         ────────────
无 --ref，建立锚点  ──→   --ref=Image1   ──→   --ref=Image1  ──→  ...
                         ↑                    ↑
                    始终引用第 1 张         始终引用第 1 张
```

**设计要点**：
1. Image 1 不带 `--ref`，自由建立视觉锚点（角色设计、色彩渲染、插画风格）
2. 后续所有图片都引用 Image 1 作为 `--ref`，而非链式引用前一张
3. 即使后端支持 session ID，仍然使用 ref chain（双保险）
4. 用户自定义参考图仅注入 Image 1，通过锚点链自动传播到后续图片

### 2.5 Auto-Selection 信号匹配表

Skill 通过关键词信号自动推荐最佳 Style + Layout 组合：

| 内容信号 | → Style | → Layout | 推荐 Preset |
|----------|---------|----------|-------------|
| beauty, fashion, cute | cute | sparse/balanced | cute-share |
| knowledge, concept, SaaS | notion | dense/list | knowledge-card |
| education, tutorial | chalkboard | balanced/dense | tutorial |
| movie, poster, editorial | screen-print | sparse/comparison | poster |
| hand-drawn, infographic | sketch-notes | flow/balanced | hand-drawn-edu |

首行匹配即停止，无匹配则回退到 `cute-share`——简洁高效的规则引擎。

### 2.6 三种 Outline Strategy

| 策略 | 概念 | 结构 | 典型页数 |
|------|------|------|----------|
| **A — Story-Driven** | 个人经历为线索，情感共鸣优先 | Hook→Problem→Discovery→Experience→Conclusion | 4-6 |
| **B — Information-Dense** | 价值优先，高效信息传递 | Core→Info Card→Pros/Cons→Recommendation | 3-5 |
| **C — Visual-First** | 视觉冲击为核心，文字极简 | Hero→Detail Shots→Lifestyle→CTA | 3-4 |

三套策略不仅结构不同，在 Path C 详细模式下还会各自推荐不同的 Style，并通过 `style_reason` 解释选择逻辑。

---

## 三、核心能力拆解

### 3.1 十二种 Style 全景表

| Style | 美学定位 | 适合场景 | 特殊说明 |
|-------|----------|----------|----------|
| `cute` (默认) | 甜美少女风 | 日常种草、生活分享 | 经典小红书美学 |
| `fresh` | 清爽自然 | 健康/有机/自然主题 | — |
| `warm` | 温馨友好 | 情感故事、生活叙事 | — |
| `bold` | 高冲击力 | 避坑指南、重要提醒 | — |
| `minimal` | 极简高级 | 商务内容、金句 | — |
| `retro` | 复古潮流 | 怀旧分享、经典盘点 | — |
| `pop` | 活力四射 | 惊叹分享、趣味冷知识 | — |
| `notion` | 极简线稿 | 知识卡片、概念图 | 全 Layout 兼容（全 ✓✓） |
| `chalkboard` | 彩色粉笔 | 教程、课堂笔记 | 教育类首选 |
| `study-notes` | 手写照片风 | 学习笔记、考试重点 | 蓝笔+红批注+黄荧光笔 |
| `screen-print` | 丝网印刷海报 | 影评书评、观点文章 | 独特的 Core Principles 覆盖 |
| `sketch-notes` | 手绘教育信息图 | 手绘教程、流程图解 | 默认使用 macaron palette |

### 3.2 八种 Layout 全景表

| Layout | 信息密度 | 点数/图 | 留白 | 最佳场景 |
|--------|----------|---------|------|----------|
| `sparse` (默认) | 低 | 1-2 | 60-70% | 封面、金句、冲击力声明 |
| `balanced` | 中 | 3-4 | 40-50% | 标准内容、教程 |
| `dense` | 高 | 5-8 | 20-30% | 知识卡片、速查表 |
| `list` | 中高 | 4-7 | — | 排行榜、清单、步骤指南 |
| `comparison` | 中 | 2 区块 | — | 前后对比、优缺点 |
| `flow` | 中 | 3-6 步 | — | 流程、时间线、工作流 |
| `mindmap` | 中 | 4-8 分支 | — | 概念图、头脑风暴 |
| `quadrant` | 中 | 4 象限 | — | SWOT、优先级矩阵 |

### 3.3 Style × Layout 兼容性矩阵

|              | sparse | balanced | dense | list | comparison | flow | mindmap | quadrant |
|--------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| cute         | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓  | ✓  | ✓  | ✓  |
| notion       | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| screen-print | ✓✓ | ✓✓ | ✗  | ✓  | ✓✓ | ✓  | ✗  | ✓✓ |
| study-notes  | ✗  | ✓  | ✓✓ | ✓✓ | ✓  | ✓  | ✓✓ | ✓  |
| sketch-notes | ✓  | ✓✓ | ✓✓ | ✓✓ | ✓  | ✓✓ | ✓✓ | ✓  |

（仅摘录代表性行——完整矩阵含 12×8=96 个评分）

**设计意义**：兼容性矩阵作为**前置约束**，在用户选择非默认组合时主动预警。`notion` 全行 ✓✓ 说明极简线稿具有最强适应性；`screen-print` 不兼容 dense/mindmap 是因为丝网印刷追求简洁符号化，高密度信息会破坏其设计语言。

### 3.4 二十七个 Preset 分组

Preset 按场景分为 5 大组：

| 分组 | Preset 数量 | 代表 Preset | 典型用户 |
|------|------------|-------------|----------|
| Knowledge & Learning | 10 | knowledge-card, tutorial, hand-drawn-edu | 知识博主、教育 UP 主 |
| Lifestyle & Sharing | 5 | cute-share, cozy-story, product-review | 生活博主、种草达人 |
| Impact & Opinion | 4 | warning, versus, clean-quote | 观点型博主 |
| Trend & Entertainment | 4 | retro-ranking, hype, pop-facts | 娱乐博主 |
| Poster & Editorial | 3 | poster, editorial, cinematic | 影评人、文化评论 |

其中 `sketch-notes` 系列的 3 个 preset 是唯一自带 `palette: macaron` 的——这体现了 `default_palette` 机制的实际应用。

### 3.5 Content Breakdown 原则

每个系列的图片遵循**位置决定布局**的原则：

| 位置 | 功能 | 典型 Layout | 设计逻辑 |
|------|------|-------------|----------|
| Cover (第 1 张) | Hook + 视觉冲击 | `sparse` | 留白最大化，让标题和主视觉最突出 |
| Content (中间) | 核心价值传递 | `balanced`/`dense`/`list` 等 | 根据信息密度灵活选择 |
| Ending (最后) | CTA + 互动引导 | `sparse` 或 `balanced` | 收束感，留出互动空间 |

### 3.6 Watermark 支持与 Backup 规则

**Watermark**：通过 EXTEND.md 配置（位置、内容、透明度），以 prompt 文本注入方式实现——不是后处理叠加，而是让 AI 在生成时直接绘制水印。

**Backup 规则**：覆盖任何已有文件前，重命名为 `<name>-backup-YYYYMMDD-HHMMSS.<ext>`——这保护了用户对 prompt/outline 的手动编辑，是面向迭代工作流的防御性设计。

---

## 四、Prompt Engineering 学习点

### 4.1 Image-1 Anchor Chain 的精妙设计

**问题**：AI 图像生成模型没有"记忆"，每次调用独立——连续 5 张图可能出现 5 种风格的角色。

**解决方案**：不是尝试用文字描述来维持一致性（不可靠），而是通过**图像引用**建立物理锚点。关键洞察在于选择"星型引用"而非"链式引用"：

- ✗ 链式：Image1 → Image2 → Image3（误差累积，后期漂移）
- ✓ 星型：Image1 → Image2, Image1 → Image3, Image1 → Image4（误差不累积）

这是一个典型的工程决策：用简单的结构约束替代复杂的算法控制。

### 4.2 Smart Confirm 三路径设计的决策树思维

```markdown
用户意图明确度:
├── 高 (只想快速出图) ──→ Path A: 一键确认
├── 中 (知道要调什么) ──→ Path B: 定向修改 5 个维度
└── 低 (需要探索比较) ──→ Path C: 看 3 套方案再选
```

这体现了**渐进式披露**（Progressive Disclosure）原则——默认路径最简，需要更多控制的用户主动深入。注意 Path B 的"留空保留推荐值"设计：它不强迫用户回答所有问题，而是让推荐值成为合理的默认——减少认知负担。

### 4.3 值得借鉴的写法摘录

**摘录 1：Screen-Print Style Override**

```markdown
## Core Principles
- Screen print / silkscreen poster art — flat color blocks, NO gradients
- Bold silhouettes and symbolic shapes over detailed rendering
- Negative space as active storytelling element
```

**点评**：当通用规则不适用于特定 Style 时，不是修修补补，而是直接**整段覆盖** Core Principles。这比"除了 X 之外都适用"的否定式描述清晰得多，避免了 LLM 处理例外时的不确定性。

**摘录 2：Confirmation Policy 的硬性阻断**

```markdown
- Treat explicit skill invocation, a file path, matched signals/presets, and
  EXTEND.md defaults as **recommendation inputs only**. None of them
  authorizes skipping confirmation.
- Do **not** start Step 3 until the user completes Step 2.
```

**点评**：这是一种**防御性 Prompt Engineering**——预见到 LLM 可能"聪明过头"地跳过确认步骤（因为已有足够信息），用显式禁止堵住每一条可能的跳过路径。列举了 4 种"看似合理但不允许"的场景。

**摘录 3：`--yes` 非交互降级**

```markdown
Skip confirmation only when the current request explicitly says to do so,
for example: `--yes`, "直接生成", "不用确认", "跳过确认", "按默认出图"
```

**点评**：支持了 CI/CD 或批处理场景的需求，同时通过枚举多种自然语言表达（中英文混合）来提升触发鲁棒性——这是 Agent Skill 中的"API 兼容性"设计。

### 4.4 Style × Layout 兼容性矩阵的前置约束思路

传统做法是在生成后检查结果质量；这里的做法是在选择阶段就**前置过滤**。当用户选择 `screen-print` + `dense` 时，矩阵标记为 ✗——skill 会主动提醒而非盲目执行。

这种"约束前置"模式的优点：
1. 减少无效生成（节省 API 调用成本）
2. 教育用户理解设计语言的边界
3. 保留用户最终决定权（仅提醒，不阻止）

---

## 五、教学小结

### 核心 Takeaways

1. **正交维度分离**：将"风格-布局-配色"解耦为三个独立轴，让有限的预设产生数百种组合——这是对抗"preset 爆炸"问题的经典策略。

2. **物理锚点优于文本描述**：Image-1 Anchor Chain 证明了在多步生成中，通过参考图建立视觉一致性比用详细文字描述可靠得多——因为图像是精确的，语言是模糊的。

3. **渐进式交互设计**：Smart Confirm 三路径让 80% 的用户走 Path A 一键完成，同时不牺牲高级用户的控制力——这是 Agent Skill 交互设计的黄金法则。

4. **防御性指令工程**：预见 LLM 的"自作聪明"，用显式禁止（而非隐式依赖）确保行为可预测。Confirmation Policy 的写法是这方面的教科书范例。

5. **平台特化分析框架**：`analysis-framework.md` 中的 Hook 评分、滑动流设计、收藏/分享触发点分析——这些不是通用的"内容分析"，而是针对小红书用户行为模式深度定制的框架。

### 多图系列一致性的挑战与解决

多图系列生成是 AI 图像领域的硬核难题。本 skill 的解决方案组合：

| 层次 | 机制 | 保障维度 |
|------|------|----------|
| 结构层 | Prompt 模板统一 + Style/Layout 规范 | 信息布局一致 |
| 视觉层 | Image-1 Anchor Chain | 角色/色彩/风格一致 |
| 会话层 | Session ID (`cards-{slug}-{timestamp}`) | 后端级别的上下文保持 |
| 文件层 | Prompt 文件先写后生成 | 可回溯、可重新生成 |

四层组合使得在当前 AI 图像生成技术的局限下，实现了最优的跨图一致性。

### 面向社交媒体平台的特化设计

本 skill 不是一个通用图像生成器，而是深度绑定了社交媒体内容生产的特定范式：

- **Swipe Flow**：每张图结尾设计"下一页 Hook"，服务于竖屏滑动阅读习惯
- **Safe Zones**：避开平台 UI 叠加区域（点赞按钮、标题栏），确保关键内容可见
- **互动设计**：结尾页内置 CTA 引导（收藏/分享/评论），直接服务于平台算法偏好的互动指标
- **Hook 优先**：封面决定 90% 的曝光转化，因此用 `sparse` 布局最大化首图冲击力

这种"从平台规则倒推技术方案"的思路，值得所有面向特定场景的 Agent Skill 借鉴。
