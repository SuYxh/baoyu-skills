# baoyu-diagram 深度解读：自包含 Design System 驱动的 SVG 图表生成 Skill

> 本文面向想学习编写 Agent Skill 的开发者，以 `baoyu-diagram` 为案例，拆解其"代码生成型" Skill 的设计模式——如何在一个 SKILL.md 中内嵌完整的设计系统、分层渲染规范和布局算法，使 LLM 能直接输出生产级 SVG 代码。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称** | `baoyu-diagram` |
| **一句话定位** | 专业暗色主题 SVG 图表生成器，覆盖 9 种图表类型 |
| **触发关键词** | 画个图、画一个架构图、diagram、flowchart、sequence diagram、draw me a ...、visualize it |
| **前置依赖** | `bun`（首选）或 `npx`（用于 SVG→PNG 转换） |
| **适用场景** | 系统架构、流程决策、时序交互、类图/ER 图、脑图、时间线、状态机、数据流、概念说明 |
| **输入→输出** | 用户描述/文件 → `.svg`（自适应缩放）+ `@2x.png`（高清位图） |

---

## 二、架构与设计模式分析

### 2.1 八步 Process 流程

```
用户请求 → 识别图表类型 → 读取对应 reference → 规划布局（列出组件、分组、流向、坐标）
    → 按分层顺序写 SVG → 验证间距规则 → 保存 .svg → 脚本转 @2x PNG → 交付双文件
```

这 8 步没有 Hard Gate（不需要用户中间确认），是**一次性完整执行**的流水线。这是"代码生成型" Skill 的典型模式——输出本身就是结果，不需要中间工具调用的 side-effect 确认。

### 2.2 Design System 体系

Skill 在 SKILL.md 中完整内嵌了一套暗色 Design System，包含：

- **8 色语义调色板**：Primary/Secondary/Tertiary/Accent/Alert/Connector/Neutral/Highlight，每色带 `rgba` 填充 + 描边色
- **字体规范**：JetBrains Mono 为主，5 级字号（16/12/9/8/7px）对应 Title→Tiny label
- **核心视觉元素**：`#0f172a` 背景 + 40px 网格 + 标准/彩色/开放三种 arrowhead marker

### 2.3 SVG 八层分层渲染顺序

这是本 Skill 的**核心设计约束**——利用 SVG "后绘制者覆盖前者"的渲染机制：

| 层序 | 内容 | 作用 |
|------|------|------|
| 1 | Background + Grid | 暗色画布 |
| 2 | Region/Group boundaries | 虚线分区（最底层可见元素） |
| 3 | Connection arrows | 连接线（会被后续组件遮盖） |
| 4 | **Opaque masking rects** | 与组件同位置的不透明矩形，遮盖穿过的箭头 |
| 5 | Component boxes | 半透明填充 + 描边 |
| 6 | Text labels | 文字在最上层 |
| 7 | Legend | 图例（图外区域） |
| 8 | Title block | 标题（左上角） |

第 4 层"遮罩矩形"是精妙设计——如果没有它，半透明的组件填充会让底层箭头透出来，破坏视觉层次。

### 2.4 类型特定布局引导（references/）

四个 reference 文件提供了**类型特化的布局算法**：

| 文件 | 核心内容 |
|------|----------|
| `architecture.md` | LTR/TTB 两种方向选择、层级分配算法、Message Bus 模式、多区域嵌套 |
| `flowchart.md` | 形状词汇表（5 种）、Happy Path 居中策略、决策分支偏移 200px、颜色按角色分配 |
| `sequence.md` | Actor 150-200px 间距、Activation bar 计算、Alt/Loop frame 画法、消息编号策略 |
| `structural.md` | 三格式类图盒子、6 种关系线（继承/组合/聚合等）、ER 图 crow's foot 记法、组织架构树布局 |

### 2.5 脚本架构（scripts/main.ts）

一个 100 行的 TypeScript CLI 工具，职责单一：

1. 解析 SVG 的 `viewBox`（或 `width`/`height`）获取画布尺寸
2. 用 `sharp` 库以 `density = 72 × scale` 渲染 SVG 为 PNG
3. 输出 `@2x` 后缀的高清位图

选择 `bun` 作为 runtime 并提供 `npx -y bun` 的 fallback，保证了跨环境可用性。

---

## 三、核心能力拆解

### 3.1 九种图表类型全景

| 类型 | 典型场景 | 关键特征 |
|------|----------|----------|
| Architecture | 微服务系统 | 分组盒子 + 区域边界 + 连接箭头 |
| Flowchart | 审批流程 | 菱形决策 + 圆角起止 + 方向流 |
| Sequence | API 调用链 | 垂直生命线 + 水平消息 + 激活条 |
| Structural | 类图/ER | 分格盒子 + 类型化关系线 |
| Mind Map | 头脑风暴 | 中心辐射 + 贝塞尔曲线分支 |
| Timeline | 版本历程 | 轴线 + 事件标记 + 交替文字 |
| Illustrative | 概念解释 | 自由布局 + 图标 + 注释 |
| State Machine | 生命周期 | 圆角状态 + 标注转换 + 初始/终止 |
| Data Flow | ETL 管道 | 过程气泡 + 数据存储 + 外部实体 |

### 3.2 八色语义调色板系统

调色板的设计遵循**"按语义分配，而非按美观分配"**的原则：

- 前端/用户侧 → Primary (cyan)
- 后端/服务层 → Secondary (emerald)
- 存储/持久化 → Tertiary (violet)
- 基础设施/云 → Accent (amber)
- 安全/告警 → Alert (rose)
- 中间件/总线 → Connector (orange)

针对 Flowchart/Sequence 有特殊规则：**按角色而非技术栈分配颜色**，确保图表的语义可读性。

### 3.3 组件模式库

SKILL.md 内嵌了 5 种可复用的 SVG 代码模板：

- **Standard Box**：160×60px 标准服务盒子（遮罩 + 填充 + 双行文字）
- **Decision Diamond**：通过 polygon 点坐标实现的菱形，带居中文字
- **Database Cylinder**：椭圆 + 矩形组合模拟圆柱体，带侧边描边线
- **Region Boundary**：虚线圆角矩形 + 左上角文字标签
- **Security Group**：更细的虚线 + rose 配色区分安全边界

### 3.4 间距规则（硬约束）

这些是**必须遵守的数值约束**而非建议：

- 组件最小间距：垂直 40px、水平 30px
- 箭头标签与盒子边缘：≥ 10px
- 区域边界内边距：20px
- viewBox 外边距：四边各 30px
- Legend 与最低元素：≥ 20px

### 3.5 SVG 输出规则

- **viewBox 自适应**：只设 `viewBox`，不设 `width`/`height`，使 SVG 可在任何容器内缩放
- **CJK 字体处理**：检测到中文时追加 `'Noto Sans SC', 'PingFang SC'` 字体栈并加宽盒子
- **单文件自包含**：通过 Google Fonts `@import` 内嵌字体声明，无外部 CSS 依赖

---

## 四、Prompt Engineering 学习点

### 4.1 无 EXTEND.md / 无 Confirmation 的简约设计

与 `baoyu-infographic` 的 7 步带 Hard Gate 流程对比，本 Skill **没有用户确认步骤、没有偏好持久化文件**。原因在于：

- 代码生成型 Skill 的输出本身就是可审查的终态
- 修改成本低（用户说"把颜色改一下"即可重新生成）
- 不存在不可逆操作（不调用外部 API、不花费 token 去生成位图）

这提示我们：**Confirmation Gate 的必要性取决于操作的不可逆程度和试错成本**。

### 4.2 "Opaque Masking Rect Trick" 的内联教学

```svg
<!-- Mask layer: opaque background to hide arrows -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="#0f172a"/>
<!-- Visual layer: styled component -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="rgba(8,51,68,0.4)" stroke="#22d3ee" stroke-width="1.5"/>
```

**点评**：这段代码不仅是参考模板，更是在教 LLM 一个 SVG 渲染的"trick"——先画不透明背景遮住底层元素，再画半透明可见层。注释 `<!-- Mask layer: opaque background to hide arrows -->` 精确说明了 *why*，帮助 LLM 在新场景中泛化应用。

### 4.3 Design System 完整内嵌

本 Skill 将**所有设计规范都写在 SKILL.md 中**，不依赖外部 JSON/YAML 配置。好处：

- LLM 在单次 prompt 加载中获得完整上下文
- 无需额外文件读取步骤（减少 tool call 开销）
- 避免外部文件版本不一致的问题

代价是 SKILL.md 较长（约 248 行），但对于"生成完整代码"这一任务类型，充分的上下文远比简洁更重要。

### 4.4 值得借鉴的写法摘录

**摘录 1 — Spacing Rules 的硬约束写法：**

> "These prevent overlapping — follow them strictly"

**点评**：用"prevent overlapping"解释 *why*，用"follow them strictly"设立 *enforcement level*。这比单纯列数值有效得多——LLM 会理解这不是建议而是约束。

**摘录 2 — 类型分发的条件引导：**

> "For flowcharts and sequence diagrams, assign colors by role (actor, decision, process) rather than by technology."

**点评**：一句话完成了"例外规则"的教学。它不是在每个图表类型中重复完整的调色板规则，而是在调色板定义处附加条件性覆盖——这减少了 prompt 冗余。

**摘录 3 — Reference 文件的"懒加载"设计：**

> "Read the reference file for the specific diagram type before starting layout."

**点评**：将 4 个详细的布局算法文档放到 `references/` 而非全部塞进 SKILL.md，实现了**按需加载**——LLM 只在需要画架构图时才读取 architecture.md，节省了其他 8 种类型的上下文窗口空间。

---

## 五、教学小结

### Takeaways

1. **代码生成型 Skill 的核心是 Design System 内嵌**——把颜色、字号、间距、分层规则全部写进 prompt，LLM 就能像执行规范文档一样生成一致的代码输出。

2. **"可执行代码片段"比纯文字描述有效 10 倍**——本 Skill 用 SVG 代码模板（带占位符如 `X`, `Y`, `CX`）作为"活文档"，LLM 可以直接填值使用。

3. **分层约束优于笼统要求**——8 层渲染顺序、间距硬约束、语义调色板，这三者的组合使得即使 LLM 在布局上有偏差，输出的 SVG 在视觉上也不会崩溃。

4. **按需加载的 reference 文件设计**——把 9 种图表的布局细节分散到 4 个外部文件中（其余 5 种通过主文件的简短描述覆盖），平衡了上下文窗口和信息完整性。

5. **简约流程适用于低成本试错场景**——没有确认步骤、没有偏好文件、没有多轮交互，因为生成一个 SVG 的成本几乎为零，用户不满意可以立刻重来。

### "代码生成型" vs "API 调用型" Skill 的设计差异

| 维度 | 代码生成型（如 baoyu-diagram） | API 调用型（如 baoyu-imagine） |
|------|-------------------------------|-------------------------------|
| 核心 prompt 内容 | Design System + 代码模板 + 约束规则 | API 参数说明 + prompt 模板 + 质量指南 |
| 流程复杂度 | 线性（无 gate） | 多步带确认（参数确认 → 调用 → 验证） |
| 试错成本 | 极低（重新生成即可） | 中高（消耗 API quota / 时间） |
| 输出可审查性 | 极高（SVG 代码可直接阅读） | 低（位图需要人眼判断） |
| EXTEND.md 需求 | 不需要（规则自包含） | 通常需要（持久化用户偏好） |

### Design System 内嵌 vs 外部引用的权衡

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **内嵌**（本 Skill 做法） | 单次加载完整上下文；无文件读取开销 | SKILL.md 较长；修改需编辑主文件 | 规则总量 < 300 行、需要全局一致性 |
| **外部引用**（JSON/YAML） | 主文件简洁；可被多 Skill 共享 | 需要额外 tool call 读取；有同步风险 | 规则复杂度高、多 Skill 共享设计系统 |
| **混合**（本 Skill 实际做法） | 核心规则内嵌 + 类型细节外部按需加载 | 需约定加载时机 | 主规则稳定 + 类型扩展频繁 |

`baoyu-diagram` 实际采用的是**混合策略**：调色板、字体、分层规则等全局规范内嵌在 SKILL.md 中，而 4 种复杂布局算法放在 `references/` 按需读取——这是一个值得学习的平衡点。
