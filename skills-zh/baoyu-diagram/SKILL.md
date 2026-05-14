---
name: baoyu-diagram
description: 创建专业的深色主题 SVG 图表，支持任意类型 —— 架构图、流程图、时序图、结构图、思维导图、时间线、概念/示意图等。当用户请求任何类型的技术或概念图表、系统可视化、流程图、数据流图、组件关系图、网络拓扑图、决策树、组织架构图、状态机或任何结构/逻辑/流程的可视化表示时使用此技能。当用户说"画个图"、"画一个架构图"、"diagram"、"flowchart"、"sequence diagram"、"draw me a ..." 或上传内容并要求可视化时也会触发。输出始终为独立的 .svg 文件。
---

# 图表生成器

创建多种类型的专业 SVG 图表。所有输出为单个自包含的 `.svg` 文件，内嵌样式和字体。

## 支持的图表类型

| 类型 | 适用场景 | 主要特征 |
|------|-------------|-------------------|
| **架构图** | 系统组件与关系 | 分组方框、连接箭头、区域边界 |
| **流程图** | 决策逻辑、处理步骤 | 菱形决策、圆角步骤框、方向性流向 |
| **时序图** | 参与者之间的时间顺序交互 | 垂直生命线、水平消息、激活条 |
| **结构图** | 类图、ER 图、组织架构图 | 分区方框、类型化关系（继承、组合） |
| **思维导图** | 头脑风暴、主题探索 | 中心节点、辐射分支、有机布局 |
| **时间线** | 按时间排列的事件 | 水平/垂直轴、事件标记、时间跨度 |
| **示意图** | 概念解释、对比 | 自由布局、图标、注释、视觉隐喻 |
| **状态机** | 状态转换、生命周期 | 圆角状态节点、带标签的转换、起止标记 |
| **数据流图** | 数据转换管道 | 处理气泡、数据存储、外部实体 |

## 设计系统

### 调色板

按组件类别划分的语义颜色：

| 类别 | 填充色（rgba） | 描边色 | 用途 |
|----------|-------------|--------|---------|
| 主要 | `rgba(8, 51, 68, 0.4)` | `#22d3ee`（青色） | 前端、面向用户、输入 |
| 次要 | `rgba(6, 78, 59, 0.4)` | `#34d399`（翡翠绿） | 后端、服务、处理 |
| 第三 | `rgba(76, 29, 149, 0.4)` | `#a78bfa`（紫色） | 数据库、存储、持久化 |
| 强调 | `rgba(120, 53, 15, 0.3)` | `#fbbf24`（琥珀色） | 云、基础设施、区域 |
| 警告 | `rgba(136, 19, 55, 0.4)` | `#fb7185`（玫红色） | 安全、错误、警告 |
| 连接器 | `rgba(251, 146, 60, 0.3)` | `#fb923c`（橙色） | 总线、队列、中间件 |
| 中性 | `rgba(30, 41, 59, 0.5)` | `#94a3b8`（石板灰） | 外部、通用、未知 |
| 高亮 | `rgba(59, 130, 246, 0.3)` | `#60a5fa`（蓝色） | 活跃状态、焦点、当前步骤 |

对于流程图和时序图，按角色（参与者、决策、处理）而非技术来分配颜色。

### 排版

使用嵌入的 SVG `@font-face` 或系统等宽字体回退：

```svg
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap');
  text { font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace; }
</style>
```

按角色划分的字体大小：
- **标题：** 16px，字重 700
- **组件名称：** 11-12px，字重 600
- **副标签 / 描述：** 9px，字重 400，颜色 `#94a3b8`
- **注释 / 备注：** 8px，字重 400
- **小标签（箭头上）：** 7-8px

### 核心视觉元素

**背景：** `#0f172a`（slate-900）带微妙网格：
```svg
<defs>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
  </pattern>
</defs>
<rect width="100%" height="100%" fill="#0f172a"/>
<rect width="100%" height="100%" fill="url(#grid)"/>
```

**箭头标记（标准）：**
```svg
<marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/>
</marker>
```

**箭头标记（彩色）—— 按需为每种颜色创建：**
```svg
<marker id="arrow-cyan" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#22d3ee"/>
</marker>
```

**开放箭头（用于异步/返回消息）：**
```svg
<marker id="arrow-open" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polyline points="0 0, 10 3.5, 0 7" fill="none" stroke="#64748b" stroke-width="1.5"/>
</marker>
```

### SVG 结构与图层

按以下顺序绘制元素以获得正确的 z 序（SVG 从后往前绘制）：

1. 背景填充 + 网格图案
2. 区域/分组边界（虚线轮廓）
3. 连接箭头和线条
4. 不透明遮罩矩形（与组件框位置相同，`fill="#0f172a"`）
5. 组件框（半透明填充 + 描边）
6. 文字标签
7. 图例（右下角或底部区域，在所有边界之外）
8. 标题块（左上角）

不透明遮罩矩形技巧至关重要 —— 没有它，半透明的组件填充会透出下方的箭头：
```svg
<!-- 遮罩层：不透明背景用于隐藏箭头 -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="#0f172a"/>
<!-- 视觉层：带样式的组件 -->
<rect x="100" y="100" width="160" height="60" rx="6" fill="rgba(8,51,68,0.4)" stroke="#22d3ee" stroke-width="1.5"/>
<text x="180" y="125" fill="white" font-size="11" font-weight="600" text-anchor="middle">API Gateway</text>
<text x="180" y="141" fill="#94a3b8" font-size="9" text-anchor="middle">Kong / Nginx</text>
```

### 间距规则

这些规则防止重叠 —— 请严格遵循：

- **组件框高度：** 50-70px（标准），80-120px（大型/复杂）
- **组件之间最小间距：** 垂直 40px，水平 30px
- **箭头标签间距：** 距任何框边缘 10px
- **区域边界内边距：** 包含组件周围内边距 20px
- **图例放置：** 至少在最低图表元素下方 20px
- **标题块：** 距左上角 20px，在图表内容区域之外
- **viewBox：** 始终扩展以适应所有内容 + 四边 30px 内边距

### 组件模式

**标准框（服务/处理）：**
```svg
<rect x="X" y="Y" width="160" height="60" rx="6" fill="#0f172a"/>
<rect x="X" y="Y" width="160" height="60" rx="6" fill="FILL" stroke="STROKE" stroke-width="1.5"/>
<text x="CX" y="Y+24" fill="white" font-size="11" font-weight="600" text-anchor="middle">Name</text>
<text x="CX" y="Y+40" fill="#94a3b8" font-size="9" text-anchor="middle">description</text>
```

**决策菱形（流程图）：**
```svg
<g transform="translate(CX, CY)">
  <polygon points="0,-35 50,0 0,35 -50,0" fill="#0f172a"/>
  <polygon points="0,-35 50,0 0,35 -50,0" fill="rgba(120,53,15,0.3)" stroke="#fbbf24" stroke-width="1.5"/>
  <text y="4" fill="white" font-size="10" font-weight="600" text-anchor="middle">Condition?</text>
</g>
```

**数据库圆柱体：**
```svg
<g transform="translate(X, Y)">
  <rect x="0" y="10" width="120" height="50" rx="2" fill="#0f172a"/>
  <ellipse cx="60" cy="10" rx="60" ry="12" fill="#0f172a"/>
  <ellipse cx="60" cy="60" rx="60" ry="12" fill="#0f172a"/>
  <rect x="0" y="10" width="120" height="50" fill="rgba(76,29,149,0.4)"/>
  <ellipse cx="60" cy="10" rx="60" ry="12" fill="rgba(76,29,149,0.4)" stroke="#a78bfa" stroke-width="1.5"/>
  <ellipse cx="60" cy="60" rx="60" ry="12" fill="rgba(76,29,149,0.4)" stroke="#a78bfa" stroke-width="1.5"/>
  <line x1="0" y1="10" x2="0" y2="60" stroke="#a78bfa" stroke-width="1.5"/>
  <line x1="120" y1="10" x2="120" y2="60" stroke="#a78bfa" stroke-width="1.5"/>
  <text x="60" y="40" fill="white" font-size="11" font-weight="600" text-anchor="middle">PostgreSQL</text>
</g>
```

**区域边界：**
```svg
<rect x="X" y="Y" width="W" height="H" rx="12" fill="none" stroke="#fbbf24" stroke-width="1" stroke-dasharray="8,4"/>
<text x="X+12" y="Y+16" fill="#fbbf24" font-size="9" font-weight="600">AWS us-east-1</text>
```

**安全组：**
```svg
<rect x="X" y="Y" width="W" height="H" rx="8" fill="none" stroke="#fb7185" stroke-width="1" stroke-dasharray="4,4"/>
<text x="X+10" y="Y+14" fill="#fb7185" font-size="8" font-weight="500">VPC / Security Group</text>
```

## 特定类型的布局指南

确定此 SKILL.md 文件的目录路径为 `{baseDir}`。在开始布局前，请阅读对应图表类型的参考文件。参考文件位于 `{baseDir}/references/`，包含详细的布局算法和示例。

### 架构图
→ 阅读 `{baseDir}/references/architecture.md`

要点：从左到右或从上到下的数据流。在区域边界中分组相关服务。层之间使用总线/连接器。数据库放在底部或右侧。

### 流程图
→ 阅读 `{baseDir}/references/flowchart.md`

要点：从上到下的主要流向。菱形用于决策，出口箭头标注是/否。圆角矩形用于起止节点。使用高亮颜色标注正常路径。

### 时序图
→ 阅读 `{baseDir}/references/sequence.md`

要点：参与者在顶部显示为方框，垂直虚线为生命线，水平箭头为消息（实线=同步，虚线=返回）。时间向下流动。激活条表示处理中。复杂交互可对消息编号。

### 结构图
→ 阅读 `{baseDir}/references/structural.md`

要点：分区方框（类图中为名称/属性/方法）。关系线：实心填充菱形=组合，空心菱形=聚合，虚线箭头=依赖，实心三角=继承。

### 思维导图
从中心概念辐射的自由形式布局。分支使用有机曲线（带三次贝塞尔曲线的 `<path>`）。使用调色板中的不同颜色区分分支。中心节点字体较大，向外逐渐减小。

### 时间线
水平或垂直轴线。事件标记为轴线上的圆形或菱形。描述文字交替偏移到两侧以避免重叠。使用颜色对事件类型进行分类。

### 状态机
圆角矩形状态，双边框表示复合状态。实心圆为初始状态，靶心圆为终止状态。自转换使用弯曲箭头。所有转换标注 `event [guard] / action` 格式。

## 输出规则

1. 输出**单个 `.svg` 文件** —— 除 Google Fonts 导入外无外部依赖
2. 设置 `viewBox` 以适应所有内容并留 30px 内边距；不要设置固定的 `width`/`height` 属性（让 SVG 响应式缩放）
3. 在根 `<svg>` 元素上包含 `xmlns="http://www.w3.org/2000/svg"`
4. 将所有 `<style>`、`<defs>`、标记和图案放在 SVG 顶部
5. 使用 `text-anchor="middle"` 居中标签；确保文字不超出框
6. **中文文本支持：** 当标签包含中文字符时，使用 `font-family: 'JetBrains Mono', 'Noto Sans SC', 'PingFang SC', sans-serif'` 并增加框宽度 —— CJK 字符更宽
7. **保存位置：** 如果输入是文件，保存到 `{inputFileDir}/diagram/`。否则保存到 `{projectDir}/diagram/{topic-slug}/`。如果目录不存在则创建

## 脚本

确定此 SKILL.md 文件的目录路径为 `{baseDir}`。脚本路径：`{baseDir}/scripts/main.ts`。

解析 `${BUN_X}` 运行时：如果已安装 `bun` → `bun`；如果 `npx` 可用 → `npx -y bun`；否则建议安装 bun。

### SVG → @2x PNG

保存 SVG 后，将其转换为 @2x PNG：

```bash
${BUN_X} {baseDir}/scripts/main.ts <svg-path> [options]
```

选项：
- `-s, --scale <n>` — 缩放倍数（默认：2）
- `-o, --output <path>` — 自定义输出路径（默认：`<input>@2x.png`）
- `--json` — JSON 输出

## 流程

1. 从用户请求中识别图表类型
2. 如果该类型存在参考文件，则阅读相关参考文件
3. 规划布局：列出所有组件，确定分组和流向，计算位置
4. 按上述图层顺序编写 SVG
5. 验证间距规则 —— 无重叠、图例在边界外、viewBox 足够大
6. 保存 SVG 文件
7. 运行 `${BUN_X} {baseDir}/scripts/main.ts <svg-path>` 生成 @2x PNG
8. 向用户展示两个文件
