# baoyu-post-to-weibo 深度解读：浏览器自动化发布的安全设计哲学

> 本文面向想学习编写 Agent Skill 的开发者，以 `baoyu-post-to-weibo` v1.56.1 为案例，拆解其纯 CDP 架构、双路径发布设计、人工确认安全模式，以及浏览器进程管理的精准清理策略。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-post-to-weibo` v1.56.1 |
| **一句话定位** | 通过真实 Chrome 浏览器向微博发布普通帖文和头条文章 |
| **触发关键词** | post to Weibo、发微博、发布微博、publish to Weibo、share on Weibo、写微博、微博头条文章 |
| **前置依赖** | `bun` 运行时（或 `npx`）+ Google Chrome / Chromium |
| **适用场景** | 发布短文本微博（附图/视频）、发布 Markdown 长文为头条文章 |
| **输入→输出** | 文本/图片/视频 或 Markdown 文件 → Chrome 中预填内容，等待用户手动点击发布 |

**核心特色**：这是一个"只填不发"的自动化 skill——脚本负责打开浏览器、填充内容，但**最终的发布按钮由用户手动点击**，体现了对社交平台自动发布风险的高度敬畏。

---

## 二、架构与设计模式分析

### 2.1 两条发布路径

```
用户输入
    │
    ├─ .md 文件 ────────→ Headline Article（头条文章）
    │                       weibo-article.ts
    │                       card.weibo.com/article/v3/editor
    │
    └─ 纯文本/图片/视频 ──→ Regular Post（普通微博）
                            weibo-post.ts
                            weibo.com 首页编辑框
```

Post Type 通过文件扩展名自动检测：`.md` 走头条文章路径，其余走普通帖文。用户也可显式指定。

### 2.2 纯 Browser CDP 架构

与某些平台 skill 可能采用 API + 浏览器双方法不同，本 skill **完全依赖 Chrome DevTools Protocol (CDP)**。原因很直接——微博没有开放的个人发布 API，只能通过真实浏览器绕过反爬检测。

架构中的共享层 `weibo-utils.ts` 封装了：
- Chrome 进程发现与复用（`findExistingChromeDebugPort`）
- CDP WebSocket 连接管理（`CdpConnection`）
- 跨平台 Chrome 路径检测（macOS / Windows / Linux / WSL）
- 剪贴板操作工具链（`copyHtmlToClipboard` / `pasteFromClipboard`）

### 2.3 脚本职责分工

| 脚本 | 职责 |
|------|------|
| `weibo-post.ts` | 普通帖文：文本输入 + 文件上传（CDP `DOM.setFileInputFiles`）|
| `weibo-article.ts` | 头条文章：Markdown→HTML→ProseMirror 粘贴 + 图片逐张替换 |
| `weibo-utils.ts` | Chrome 生命周期管理、CDP 连接、剪贴板桥接 |
| `copy-to-clipboard.ts` | 将图片/HTML 写入系统剪贴板 |
| `paste-from-clipboard.ts` | 模拟真实粘贴键击 |
| `md-to-html.ts` | Markdown 解析与 HTML 转换 |

### 2.4 "Script fills, user publishes" 人工确认设计

这是本 skill 最核心的设计决策。脚本执行完毕后输出：

```
[weibo-post] Post composed. Please review and click the publish button in the browser.
[weibo-post] Browser remains open for manual review.
```

浏览器保持打开，用户可以检查内容、修改措辞、确认无误后手动发布。这规避了误发、内容错误、平台封号等风险。

---

## 三、核心能力拆解

### 3.1 Regular Post：文本 + 媒体文件

- 文本通过 `Input.insertText` CDP 命令注入，带有 `execCommand` fallback
- 图片/视频通过 `DOM.setFileInputFiles` 直接设置到隐藏的 `<input type="file">` 上
- 硬限制：最多 18 个文件（`MAX_FILES = 18`）
- 上传后自动验证：检查 `blob:` / `data:` 图片或 `<video>` 元素是否出现

### 3.2 Headline Article：Markdown → ProseMirror

工作流精巧且复杂：
1. 解析 Markdown（支持 YAML frontmatter 中的 title/summary/cover_image）
2. 转为 HTML 并写入临时文件
3. 打开文章编辑器，点击"写文章"按钮
4. 等待编辑器可编辑（检测 `textarea[placeholder="请输入标题"]` 非 readonly）
5. 填充标题和导语
6. 通过剪贴板将 HTML 粘贴到 ProseMirror 富文本编辑器
7. 逐张替换图片占位符（copy image → select placeholder → paste）

### 3.3 字符限制的硬编码处理

```typescript
const TITLE_MAX_LENGTH = 32;
const SUMMARY_MAX_LENGTH = 44;
```

标题超限时的截断策略很有讲究——优先在中文标点（`：`、`，`、`、`等）处断句，如果前 40% 内没有合适断点才硬截断。这比简单的 `slice(0, 32)` 友好得多。

### 3.4 Post-Composition Check（WBIMGPH_ 验证）

文章发布前自动检查编辑器中是否还残留 `WBIMGPH_` 占位符。如果图片替换不完整，脚本会输出警告，Agent 需要在用户发布前告知具体问题。

### 3.5 Chrome CDP 冲突处理与安全约束

`killChromeByProfile` 的实现体现了精准清理理念：

```typescript
// 只杀带有特定 profile 目录且有 --remote-debugging-port 的 Chrome 进程
for (const line of result.stdout.split('\n')) {
  if (!line.includes(profileDir) || !line.includes('--remote-debugging-port=')) continue;
  // 精准终止
}
```

SKILL.md 中用 **CRITICAL** 级别标注：

> **CRITICAL**: Never kill all Chrome processes. Only kill Chrome instances launched by CDP with the baoyu-skills profile directory.

这保护了用户正在使用的普通浏览器窗口不被误杀。

---

## 四、Prompt Engineering 学习点

### 4.1 安全发布模式的设计哲学

"User reviews and publishes manually" 不仅是功能设计，更是 **prompt 对 Agent 行为的硬约束**。SKILL.md 通过多处重复强调（Notes 部分、脚本输出、参数说明）确保 Agent 不会尝试自动点击发布按钮。

### 4.2 自动恢复 + 精准清理

Troubleshooting 章节的设计非常值得借鉴：

> **Important**: This should be done automatically -- when encountering this error, kill the CDP Chrome instances and retry the command without asking the user.

这把"遇到端口冲突时的恢复流程"直接编码到 prompt 中，让 Agent 能自主处理常见故障而不打断用户。

### 4.3 值得借鉴的写法

**摘录 1**——Troubleshooting 的"自动执行"指令：

```markdown
**CRITICAL**: Never kill all Chrome processes (`pkill -f "Google Chrome"`). 
Only kill Chrome instances launched by CDP with the baoyu-skills profile directory.
**Important**: This should be done automatically -- when encountering this error, 
kill the CDP Chrome instances and retry the command without asking the user.
```

**点评**：这段同时设置了"做什么"和"绝对不做什么"两个边界，用 CRITICAL 和 Important 两级标注区分严重程度。这种"约束对"模式（positive + negative）在安全敏感场景中非常有效。

**摘录 2**——Post Type 自动检测规则：

```markdown
Unless the user explicitly specifies the post type:
- **Markdown file** (`.md`) → **Headline Article** (头条文章)
- **Plain text** / text with images → **Regular Post**
```

**点评**：两行代码级的清晰规则，让 Agent 无需猜测。"Unless explicitly specifies" 前置条件保留了用户覆盖的能力。简洁即正义。

### 4.4 与 baoyu-post-to-wechat 的对比

| 维度 | Weibo Skill | WeChat Skill（推测）|
|------|-------------|---------------------|
| 发布方法 | 纯 CDP | 可能有 API + CDP 双方法 |
| 自动化程度 | 只填不发 | 类似的人工确认 |
| 平台限制 | 18 文件、32/44 字符 | 不同的字符/文件限制 |
| 反爬绕过 | `--disable-blink-features=AutomationControlled` | 各平台不同策略 |

---

## 五、教学小结

### 3 条 Takeaway

1. **"只填不发"是浏览器自动化 skill 的黄金原则**——自动化应止于内容准备，发布决策权保留给用户。这不仅防止误发，也在平台风控层面降低被封号的风险。

2. **精准进程管理是安全设计的基石**——绝不用 `pkill -f "Google Chrome"` 这种大杀器。通过 profile 目录 + `--remote-debugging-port` 双条件过滤，确保只影响 skill 自己启动的实例。

3. **平台限制要"硬编码 + 智能降级"**——32/44 字符不是建议而是硬限，超限时的断句截断比简单截断更体现对用户内容的尊重。

### 浏览器自动化类 Skill 的安全设计清单

- ✅ 永远不自动点击发布/提交按钮
- ✅ 只终止自己启动的浏览器进程（按 profile 过滤）
- ✅ CDP 端口冲突时自动恢复，不打断用户
- ✅ 媒体上传后自动验证（检查 DOM 变化）
- ✅ 内容填充后做 Post-Composition Check
- ✅ 首次登录后 session 持久化，不反复要求认证

### 与其他发布类 Skill 的横向对比

相比 X/Twitter 发布 skill 可能调用官方 API，微博 skill 因平台限制被迫采用纯浏览器方案，反而成就了其在 CDP 实践上的深度——从进程管理、DOM 操作、剪贴板桥接到 ProseMirror 编辑器交互，是一套完整的浏览器自动化教科书。这种"因限制而精深"的技术路线，对所有需要与无 API 平台交互的 skill 都有参考价值。
