# baoyu-post-to-x 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-post-to-x` v1.57.2 |
| **一句话定位** | 通过真实 Chrome 浏览器向 X (Twitter) 发布文本、图片、视频和长文章的 Agent Skill |
| **触发关键词** | "post to X"、"tweet"、"publish to Twitter"、"share on X" |
| **前置依赖** | Google Chrome / Chromium；`bun` 或 `npx`；首次运行需手动登录 X |
| **适用场景** | 发推文、发带图/视频推文、引用转推、发布 X Article 长文（需 Premium） |
| **输入→输出** | 文本/图片/视频/Markdown 文件 → X 平台已发布内容（需用户确认后才执行发布） |

---

## 二、架构与设计模式分析

### 2.1 三种 Execution Mode 的决策树

这是整个 skill 最核心的设计——在同一个发布意图下提供三条完全不同的浏览器控制路径：

```
用户意图: "发推"
      │
      ▼
┌─────────────────────────────────────┐
│ 用户是否明确指定 Codex Chrome 插件？ │
└────────┬──────────────┬─────────────┘
     是  │              │ 否
         ▼              ▼
  Codex Chrome    ┌───────────────────────┐
  Plugin Mode     │ 是否明确指定 Computer Use？│
                  └────┬─────────────┬────┘
                   是  │             │ 否
                       ▼             ▼
              Chrome Computer   ┌────────────────┐
              Use Mode          │ Computer Use 可用？│
                                └──┬──────────┬──┘
                               是  │          │ 否
                                   ▼          ▼
                           Computer Use   CDP Script
                           Mode           Mode (Fallback)
```

**三种模式本质差异**：

| 模式 | 浏览器控制方式 | 会话来源 | 典型工具调用 |
|------|--------------|---------|-------------|
| Codex Chrome Plugin | Chrome Extension Node REPL | 用户已登录 Chrome 的真实 profile | `browser.tabs.*`, `tab.playwright.*`, file chooser |
| Chrome Computer Use | 屏幕级 GUI 操控 | 用户当前可见的 Chrome 窗口 | `mcp__computer_use__.*`, `get_app_state` |
| CDP Script | Chrome DevTools Protocol | 独立 profile 目录（持久化登录） | `x-browser.ts`, `x-article.ts` 等脚本 |

### 2.2 四种 Post Type

| 类型 | 脚本 | 触发条件 |
|------|------|---------|
| Regular Post | `x-browser.ts` | 纯文本 + 可选图片，≤10,000 字符 |
| Video Post | `x-video.ts` | 文本 + 视频文件（MP4/MOV/WebM） |
| Quote Tweet | `x-quote.ts` | 引用已有推文 URL + 评论 |
| X Article | `x-article.ts` + `md-to-html.ts` | Markdown 文件输入（需 Premium） |

### 2.3 脚本架构

```
scripts/
├── x-browser.ts            # 常规帖子（CDP fallback）
├── x-video.ts              # 视频帖子
├── x-quote.ts              # 引用转推
├── x-article.ts            # 长文章发布（最复杂）
├── md-to-html.ts           # Markdown → HTML + image map
├── copy-to-clipboard.ts    # 图片/HTML 写入系统剪贴板
├── paste-from-clipboard.ts # 发送真实粘贴按键
├── check-paste-permissions.ts # 环境与权限预检
└── x-utils.ts              # 共享工具（Chrome 启动/CDP 连接/剪贴板）
```

核心共享层 `x-utils.ts` 提供：Chrome 进程管理（发现/复用/启动）、CDP WebSocket 连接封装、跨平台剪贴板操作（macOS 用 Swift/AppKit，Linux 用 xdotool/ydotool）。

### 2.4 X Article 完整流程

这是四种类型中最复杂的——涉及 Markdown 解析、HTML 富文本粘贴、占位符替换三个阶段：

```
Markdown(.md) → md-to-html.ts → JSON(title + coverImage + contentImages[]) + HTML
                                          │
         ┌────────────────────────────────┘
         ▼
copy-to-clipboard.ts html → 系统剪贴板(Rich HTML)
         │
         ▼ Paste(Cmd+V / Super+V)
X Article Editor ← 包含 XIMGPH_1, XIMGPH_2... 占位符
         │
         ▼ 逐个处理
定位占位符 → Insert → Media → "Add photos or video" → 上传 → 删除占位符文本
         │
         ▼
Post-Composition Check → 验证 XIMGPH_ 全部清除 → Preview → 用户确认 → Publish
```

图片不使用剪贴板粘贴（因为 X 编辑器对合成粘贴事件有检测），而是走编辑器原生的 `Insert → Media` 上传流程。

---

## 三、核心能力拆解

### 3.1 Codex Chrome Plugin Mode

利用 Codex 内置 Chrome Extension 的 Node REPL 客户端控制浏览器：
- **连接验证**：`browser.user.openTabs()` 作为健康检查
- **故障恢复**：`native pipe is closed` → 等待 2s → 重试 → 执行 Chrome skill 健康检查 → 请求用户许可后才开新窗口
- **文件上传**：Chrome plugin file chooser API，如遇 `Not allowed` 则精确提示用户在 `chrome://extensions` 启用文件 URL 访问

### 3.2 Chrome Computer Use Mode

通过屏幕级 GUI 控制：
- 每次操作前 `get_app_state` 确认 Chrome 状态
- 优先使用 element-index actions，仅在文本选择时使用坐标
- 对于不可靠的 file picker 操作，明确停止并报告，而非静默降级

### 3.3 CDP Script Mode 作为 Fallback

所有 `.ts` 脚本的核心逻辑：
1. 发现或启动 Chrome（`--disable-blink-features=AutomationControlled` 绕过反自动化检测）
2. 通过 CDP WebSocket 控制 DOM（`Runtime.evaluate`, `Input.dispatchKeyEvent`）
3. 图片通过 Swift/AppKit 写入系统剪贴板，再用 `osascript` 发送真实 Cmd+V（绕过 X 对合成键盘事件的检测）

### 3.4 安全约束："Never click Publish"

每种模式下都有相同的硬性约束——**绝不在未经用户明确确认前点击 Publish/Post**。CDP 脚本默认不加 `--submit` 参数，浏览器保持打开 60 秒供用户预览。这是"高风险外部副作用"场景下 Agent 行为的标准范式。

### 3.5 字符限制适配

- Premium 用户：10,000 字符
- 非 Premium 用户：280 字符
- X Article：无字符限制，但需要 Premium 订阅

---

## 四、Prompt Engineering 学习点

### 4.1 三模式严格区分约束

> *"In Codex, do not conflate these browser paths"*

这一句开头即建立了"三条路径互不混淆"的基本原则。后续对每条路径都附带了"Do not fall back to ... without telling the user"的禁止静默降级条款。这是**多运行时环境 skill 的核心设计模式**——让 Agent 明确意识到可选路径之间的边界。

### 4.2 "native pipe is closed" 分步恢复流程

```
报错 → 等2s重试 → 运行健康检查 → 检查通过但仍失败 → 请求用户许可 → 开新窗口
```

这是**故障恢复 prompt 的典范**：不是简单说"重试"，而是给出完整的分步判断树，每一步都有明确的条件分支和用户交互点。避免 Agent 陷入"无限重试"或"静默放弃"。

### 4.3 "Never use the in-app Browser" 消极约束

> *"Never use the in-app Browser for X publishing workflows."*

这是一个典型的**消极约束（negative constraint）**——明确禁止一个看似合理但实际会导致失败的路径。因为 Codex 内置浏览器无法携带用户 X 登录态，如果 Agent 尝试使用它会浪费大量步骤后失败。

### 4.4 值得借鉴的写法摘录

**摘录 1：Execution Mode Selection 的精确优先级**

> "1. If the user explicitly asks for the Codex Chrome plugin... use Codex Chrome Plugin Mode. Do not call Computer Use first.  
> 2. If the user explicitly asks for Chrome Computer Use... Do not fall back to CDP, Playwright, the in-app Browser, or the Chrome plugin without telling the user and getting approval."

**点评**：每条规则不仅说"做什么"，还紧跟"不做什么"。这种 positive + negative 的配对写法极大降低了 Agent 的歧义空间。

**摘录 2：图片上传的精确 UI 定位**

> "In the modal, click the icon button with `aria-label="Add photos or video"`; do not click the text/dropzone or hidden file input."

**点评**：精确到 aria-label 级别的 UI 元素指定，同时用 negative constraint 排除了两个容易误点的相似元素。这对 Computer Use 场景下的 Agent 行为控制至关重要。

**摘录 3：占位符清理的防御性操作**

> "If `XIMGPH_N` remains above it, select exactly that placeholder and press `Delete` first. Use `Backspace` only if `Delete` fails and the selected text is confirmed to be exactly the placeholder."

**点评**：对一个看似简单的"删除文本"操作给出了主方案 + 降级方案 + 前置确认条件，避免 Agent 误删周围内容。

---

## 五、教学小结

### Takeaways

1. **多运行时环境 skill 需要"决策树 + 互斥约束"的双重设计**——不仅要告诉 Agent 选哪条路，还要明确禁止路径之间的静默切换。这是此 skill 与单模式 skill 的本质区别。

2. **高风险外部副作用必须设置"人类确认门控"**——`Never click Publish without explicit confirmation` 是 Agent 安全设计的最小必要约束，适用于所有"一旦执行不可撤销"的场景。

3. **故障恢复不能是简单重试，而应是分步判断树**——`native pipe is closed` 的处理展示了"检测→等待→重试→诊断→请求许可→新方案"的完整链路。

4. **绕过平台反自动化检测需要"真实信号链"**——X 能检测合成键盘事件，所以必须用 osascript 发送真实按键、用 Swift/AppKit 写真实剪贴板。这种理解层面的 know-how 直接决定了脚本架构。

5. **消极约束与积极指令同样重要**——"Never use the in-app Browser"、"do not click the dropzone"、"Do not switch to Computer Use silently" 等禁令防止了 Agent 的"创造性误用"。

### 多运行时环境适配的设计挑战

此 skill 面临的核心难题：同一个业务意图（"发推"）需要在三种截然不同的浏览器控制环境中执行，且每种环境的能力边界、失败模式、恢复策略完全不同。这要求 prompt 同时扮演"路由器"（选择模式）、"操作手册"（每种模式的详细步骤）和"安全网"（降级和恢复）三重角色。

### 与同类发布 Skill 的复杂度对比

| 维度 | 微信公众号发布 | 微博发布 | X 发布（本 skill） |
|------|-------------|---------|-------------------|
| 运行时模式 | 单一（通常 CDP） | 单一/双模式 | **三模式决策树** |
| 内容类型 | 富文本文章 | 文本+图片 | **4 种类型（含长文章）** |
| 反自动化对抗 | 中等 | 低 | **高（需真实信号链）** |
| 图片处理复杂度 | 编辑器直接上传 | 简单附件 | **占位符替换流程** |
| 安全约束层级 | 预览确认 | 简单确认 | **多层保护（模式锁定+发布确认+降级审批）** |

X 发布 skill 的复杂度远超同类，根本原因在于：X 平台的反自动化检测最严格、支持的内容类型最多样、Codex 环境提供的浏览器控制方式最丰富。三者叠加使得这个 skill 成为"多环境适配"设计模式的极端案例。
