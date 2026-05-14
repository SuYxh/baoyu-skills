---
name: baoyu-post-to-x
description: 发布内容和文章到 X (Twitter)。支持带图片/视频的普通帖子和 X Articles（长文 Markdown）。在 Codex 中，当用户明确要求使用 Codex Chrome 插件/@chrome 时，使用 Chrome Extension 工作流；否则在可用时使用 Chrome Computer Use，仅在允许时回退到真实 Chrome CDP 脚本。当用户要求"post to X"、"tweet"、"publish to Twitter"或"share on X"时使用。
version: 1.57.2
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-post-to-x
    requires:
      anyBins:
        - bun
        - npx
---

# 发布到 X (Twitter)

通过真实 Chrome 浏览器将文字、图片、视频和长文发布到 X。

在 Codex 中，不要混淆以下浏览器路径：
- **Codex Chrome 插件 / `@chrome` / Chrome Extension**：使用内置的 `chrome:Chrome` 技能及其 Node REPL 浏览器客户端。当用户说"Codex Chrome plugin"、"Codex 自带的 Chrome 插件"、`@chrome` 或类似表达时必须使用此方式。
- **Chrome Computer Use**：仅当用户要求使用 Computer Use 或未表明 Chrome 插件偏好且 Computer Use 可用时，使用 `mcp__computer_use__.*` 操作可见的 Google Chrome UI。
- **CDP 脚本模式**：仅在所选模式不可用或用户明确要求 CDP/脚本模式时作为回退使用。

## 脚本目录

**重要**：所有脚本位于此技能的 `scripts/` 子目录中。

**代理执行说明**：
1. 确定此 SKILL.md 文件所在目录路径为 `{baseDir}`
2. 脚本路径 = `{baseDir}/scripts/<script-name>.ts`
3. 将本文档中所有 `{baseDir}` 替换为实际路径
4. 解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果有 `npx` → `npx -y bun`；否则建议安装 bun

**脚本参考**：
| 脚本 | 用途 |
|--------|---------|
| `scripts/x-browser.ts` | 普通帖子（文字 + 图片），CDP 回退 |
| `scripts/x-video.ts` | 视频帖子（文字 + 视频），CDP 回退 |
| `scripts/x-quote.ts` | 引用推文并评论，CDP 回退 |
| `scripts/x-article.ts` | 长文发布（Markdown），CDP 回退 |
| `scripts/md-to-html.ts` | Markdown → HTML 转换 |
| `scripts/copy-to-clipboard.ts` | 复制内容到剪贴板 |
| `scripts/paste-from-clipboard.ts` | 发送真实粘贴按键 |
| `scripts/check-paste-permissions.ts` | 验证环境和权限 |

## 执行模式选择（必需）

在与 X 交互前，选择确切的一种模式：

1. 如果用户明确要求使用 Codex Chrome 插件、`@chrome`、Chrome 扩展或"Codex 自带的 Chrome 插件"，使用 **Codex Chrome 插件模式**。不要先调用 Computer Use。
2. 如果用户明确要求使用 Chrome Computer Use，使用 **Chrome Computer Use 模式**。不要在未告知用户并获得批准的情况下回退到 CDP、Playwright、应用内浏览器或 Chrome 插件。
3. 如果用户明确要求 CDP/脚本模式，使用 **CDP 脚本模式**。
4. 否则，优先使用 **Chrome Computer Use 模式**。对于包含本地内容图片的 Markdown **X Articles**，使用经过测试的 X 编辑器流程：在每个占位符处通过工具栏（`Insert` -> `Media` -> 对话框图标按钮 `Add photos or video`）插入正文图片，然后删除占位符文本。仅当所选浏览器控制模式不可用或 UI 上传/选择流程不可靠时，才使用 CDP 脚本模式。

不要使用应用内浏览器进行 X 发布工作流。

## Codex Chrome 插件模式

当用户请求使用 Codex Chrome 插件、`@chrome` 或 Chrome Extension 路径时使用此模式。这通过内置 Chrome 插件使用用户的真实 Chrome 配置文件和 X 登录，而非 Computer Use 或 CDP。

**设置**
1. 在浏览器操作前加载 `chrome:Chrome` 技能。
2. 如果 Node REPL `js` 工具尚不可见，使用 `tool_search` 搜索 `node_repl js`。
3. 按照 Chrome 技能的说明初始化 Chrome 浏览器客户端，然后运行轻量调用（如 `browser.user.openTabs()`）验证扩展连接。
4. 如果首次轻量调用失败，等待 2 秒后重试一次。如果仍然失败，按照 Chrome 技能的扩展检查和恢复步骤操作。如果检查通过但通信仍然失败，在打开新 Chrome 窗口前询问用户。不要静默切换到 Computer Use 或 CDP。

**通用规则**
- 使用 Chrome 插件的 `browser.tabs.*`、`tab.playwright.*`、`tab.cua.*` 和文件选择器 API 进行 X UI 操作。
- Shell 命令允许用于 Markdown 预处理和富文本 HTML 剪贴板准备。对于 X Article 正文图片，不要依赖图片剪贴板粘贴；使用编辑器的 `Insert` -> `Media` 上传流程。
- 如果文件上传失败并报 `Not allowed`，告知用户：`要启用文件上传，请在 Chrome 中访问 chrome://extensions，点击 Codex 扩展下的"详情"，然后启用"允许访问文件网址"。详情参见 https://developers.openai.com/codex/app/chrome-extension#upload-files`。
- 如果 Chrome 插件报告 `native pipe is closed`，等待 2 秒后重试轻量浏览器调用一次，然后运行 Chrome 技能健康检查。如果 Chrome 正在运行、扩展已启用且原生主机清单正确，请求允许打开新 Chrome 窗口并重试。不要通过断开的管道继续发送浏览器操作。
- 未经用户在当前对话中明确最终确认，永远不要点击 `Publish`、`Post` 或任何外部可见的提交操作。

**X Articles**
1. 转换 Markdown 并保留图片映射：
   ```bash
   ${BUN_X} {baseDir}/scripts/md-to-html.ts article.md --save-html /tmp/x-article-body.html > /tmp/x-article.json
   ```
2. 读取 JSON 输出获取 `title`、`coverImage` 和 `contentImages`（`placeholder` → `localPath`）。
3. 在 `https://x.com/compose/articles` 打开或创建文章草稿。
4. 使用 Chrome 插件文件选择器流程上传封面。如果上传因扩展权限被阻止，停止并报告上述确切的权限修复方法。
5. 填入标题，然后复制富文本 HTML：
   ```bash
   ${BUN_X} {baseDir}/scripts/copy-to-clipboard.ts html --file /tmp/x-article-body.html
   ```
6. 通过 Chrome 插件使用真实粘贴按键粘贴到文章正文。macOS 上使用 `Meta+V`。
7. 验证编辑器文本包含文章正文和 `XIMGPH_` 占位符。不要依赖 `tab.clipboard.readText()` 作为 shell 剪贴板写入后系统剪贴板的证明；macOS 上如需验证可使用 `pbpaste`。
8. 按占位符顺序处理每个 `contentImages` 项：
   - 定位可见的占位符文本（`XIMGPH_N`）并点击以将光标放置在那里。
   - 打开工具栏菜单 `Insert` -> `Media`。
   - 在模态框中，点击 `aria-label="Add photos or video"` 的图标按钮；不要点击文本/拖放区域或隐藏的文件输入。
   - 使用文件选择器上传该图片的 `localPath`。
   - 图片出现后，如果 `XIMGPH_N` 仍在其上方，选中确切的占位符文本并先按 `Delete`。仅当 `Delete` 失败且确认选中文本确实是占位符时才使用 `Backspace`。
   - 验证该 `XIMGPH_N` 的占位符计数为 `0`。
9. 打开预览并验证标题、封面、正文、链接和图片。
10. 在点击 `Publish` 前请求明确确认。

## 偏好设置 (EXTEND.md)

按优先级顺序检查 EXTEND.md —— 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-post-to-x/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-post-to-x/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-post-to-x/EXTEND.md` | 用户主目录 |

如果都未找到，使用默认值。

**EXTEND.md 支持**：默认 Chrome 配置文件

## 前置要求

- Google Chrome 或 Chromium
- `bun` 运行时
- 首次运行：需手动登录 X（会话将被保存）

## 飞行前检查（可选）

首次使用前，建议运行环境检查。用户可选择跳过。

```bash
${BUN_X} {baseDir}/scripts/check-paste-permissions.ts
```

检查项：Chrome、配置文件隔离、Bun、辅助功能、剪贴板、粘贴按键、Chrome 冲突。

**如果任何检查失败**，按项目提供修复指导：

| 检查项 | 修复方法 |
|-------|-----|
| Chrome | 安装 Chrome 或设置 `X_BROWSER_CHROME_PATH` 环境变量 |
| 配置文件目录 | 共享配置文件位于 `baoyu-skills/chrome-profile`（参见 CLAUDE.md Chrome Profile 部分） |
| Bun 运行时 | `brew install oven-sh/bun/bun`（macOS）或 `npm install -g bun` |
| 辅助功能 (macOS) | 系统设置 → 隐私与安全性 → 辅助功能 → 启用终端应用 |
| 剪贴板复制 | 确保 Swift/AppKit 可用（macOS Xcode CLI 工具：`xcode-select --install`） |
| 粘贴按键 (macOS) | 与辅助功能修复相同 |
| 粘贴按键 (Linux) | 安装 `xdotool`（X11）或 `ydotool`（Wayland） |

## 参考文档

- **普通帖子**：参见 `references/regular-posts.md` 了解手动工作流、故障排除和技术细节
- **X Articles**：参见 `references/articles.md` 了解长文发布指南

---

## Chrome Computer Use 模式

当用户明确要求使用 Chrome Computer Use，或未表明 Chrome 插件偏好且 Codex 可以通过 Computer Use 控制 `Google Chrome` 时使用此模式。这使用用户现有的 Chrome 窗口、cookie、登录、扩展和 X 会话。

**通用规则**：
- 在控制 Chrome 的每个助手回合开始时，对 `Google Chrome` 调用 `get_app_state`。
- 可用时优先使用元素索引操作；仅在编辑器文本选择或拖拽选择时使用坐标。
- 在此模式下不要使用应用内浏览器、Chrome 插件、Playwright 或 CDP 进行 X UI 操作，除非用户批准模式切换。
- 未经用户在当前对话中明确最终确认，永远不要点击 `Publish`、`Post` 或任何外部可见的提交操作。

**普通帖子**：
1. 在 Chrome 中打开或导航到 `https://x.com/compose/post`。
2. 使用 Computer Use 在编辑器中输入帖子文本。
3. 对每张图片，运行：
   ```bash
   ${BUN_X} {baseDir}/scripts/copy-to-clipboard.ts image /absolute/path/to/image.png
   ```
4. 使用 Computer Use 粘贴（macOS 用 `super+v`，Windows/Linux 用 `control+v`），然后等待 X 完成媒体上传。
5. 在点击 `Post` 前请求确认。

**视频帖子**：
1. 在 Chrome 中打开或导航到 `https://x.com/compose/post`。
2. 输入帖子文本。
3. 使用可见的媒体上传/文件选择器 UI 附加视频。
4. 等待上传和处理完成。
5. 在点击 `Post` 前请求确认。

**引用推文**：
1. 在 Chrome 中打开推文 URL。
2. 使用可见的引用/转发 UI 选择引用。
3. 输入评论。
4. 在点击 `Post` 前请求确认。

**X Articles**：
1. 转换 Markdown 并保留图片映射：
   ```bash
   ${BUN_X} {baseDir}/scripts/md-to-html.ts article.md --save-html /tmp/x-article-body.html > /tmp/x-article.json
   ```
2. 读取 JSON 输出获取 `title`、`coverImage` 和 `contentImages`（`placeholder` → `localPath`）。
3. 在 Chrome 中打开 `https://x.com/compose/articles`，创建或打开草稿，上传封面（如有），填入标题。
4. 将富文本 HTML 复制到剪贴板：
   ```bash
   ${BUN_X} {baseDir}/scripts/copy-to-clipboard.ts html --file /tmp/x-article-body.html
   ```
5. 使用 Computer Use 粘贴到文章正文。
6. 按占位符顺序处理每个 `contentImages` 条目：
   - 定位确切的可见占位符文本（如 `XIMGPH_3`）并点击以设置插入点。
   - 打开工具栏 `Insert` 下拉菜单，选择 `Media`，然后点击模态框中标签为 `Add photos or video` 的图标按钮。
   - 使用原生文件选择器选择该图片的 `localPath`。
   - 等待图片块出现且上传活动结束。
   - 如果占位符仍在插入图片上方，重新选中确切的占位符文本并先按 `Delete`。仅当 `Delete` 失败且确认选中文本确实是占位符时才使用 `Backspace`。
7. 验证没有剩余 `XIMGPH_` 占位符且预期图片已出现。
8. 打开预览并验证标题、封面、正文、链接和图片。
9. 在点击 `Publish` 前请求明确确认。

如果 Computer Use 的选择、工具栏上传或文件选择器控制变得不可靠，停止并报告阻塞问题，而不是静默切换到 Chrome 插件或 CDP。

---

## CDP 脚本模式（回退）

仅当所选浏览器控制模式不可用、不可靠或未被明确请求时，使用以下脚本部分。这些脚本通过 CDP 启动或复用真实 Chrome 实例，并保持浏览器打开以供审核。

当用户明确要求使用 Codex Chrome 插件或 Chrome Computer Use 时，不要使用 CDP 脚本模式，除非在您解释了阻塞问题后用户批准回退。

---

## 帖子类型选择

除非用户明确指定帖子类型：
- **纯文本** + 10,000 字符以内 → **普通帖子**（Premium 会员支持最多 10,000 字符，非 Premium：280）
- **Markdown 文件**（.md）→ **X Article**

## 普通帖子

```bash
${BUN_X} {baseDir}/scripts/x-browser.ts "Hello!" --image ./photo.png
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<text>` | 帖子内容（位置参数） |
| `--image <path>` | 图片文件（可重复，最多 4 张） |
| `--profile <dir>` | 自定义 Chrome 配置文件 |

**注意**：脚本会打开浏览器并填入内容。用户需自行审核并手动发布。

**Codex 模式注意**：如果用户明确要求使用 Codex Chrome 插件，使用 **Codex Chrome 插件模式**。否则，如果 Chrome Computer Use 已启用，使用 **Chrome Computer Use 模式**而非运行 `x-browser.ts`。

---

## 视频帖子

文字 + 视频文件。

```bash
${BUN_X} {baseDir}/scripts/x-video.ts "Check this out!" --video ./clip.mp4
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<text>` | 帖子内容（位置参数） |
| `--video <path>` | 视频文件（MP4, MOV, WebM） |
| `--profile <dir>` | 自定义 Chrome 配置文件 |

**注意**：脚本会打开浏览器并填入内容。用户需自行审核并手动发布。

**Codex 模式注意**：如果用户明确要求使用 Codex Chrome 插件，使用 **Codex Chrome 插件模式**。否则，如果 Chrome Computer Use 已启用，使用 **Chrome Computer Use 模式**而非运行 `x-video.ts`。

**限制**：普通用户最长 140 秒，Premium 最长 60 分钟。处理时间：30-60 秒。

---

## 引用推文

引用现有推文并添加评论。

```bash
${BUN_X} {baseDir}/scripts/x-quote.ts https://x.com/user/status/123 "Great insight!"
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<tweet-url>` | 要引用的 URL（位置参数） |
| `<comment>` | 评论文本（位置参数，可选） |
| `--profile <dir>` | 自定义 Chrome 配置文件 |

**注意**：脚本会打开浏览器并填入内容。用户需自行审核并手动发布。

**Codex 模式注意**：如果用户明确要求使用 Codex Chrome 插件，使用 **Codex Chrome 插件模式**。否则，如果 Chrome Computer Use 已启用，使用 **Chrome Computer Use 模式**而非运行 `x-quote.ts`。

---

## X Articles

长文 Markdown 文章（需要 X Premium）。

```bash
${BUN_X} {baseDir}/scripts/x-article.ts article.md
${BUN_X} {baseDir}/scripts/x-article.ts article.md --cover ./cover.jpg
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<markdown>` | Markdown 文件（位置参数） |
| `--cover <path>` | 封面图 |
| `--title <text>` | 覆盖标题 |

**Frontmatter**：YAML front matter 中支持 `title`、`cover_image`。

**Codex 模式注意**：如果用户明确要求使用 Codex Chrome 插件，按上方 **Codex Chrome 插件模式**操作。如果用户明确要求 Chrome Computer Use，按 **Chrome Computer Use 模式**操作。否则，优先使用 Chrome Computer Use；对于包含本地内容图片的 Markdown 文章，先使用工具栏 `Insert` -> `Media` 图片上传工作流，再回退到 **CDP 脚本模式**的 `x-article.ts`。

**CDP 回退注意**：脚本会打开浏览器并填入文章。用户需自行审核并手动发布，除非使用了 `--submit`。

**发布安全**：除非用户明确确认最终公开发布操作，否则不要使用 `--submit` 或点击 `Publish`。

**发布前检查**：脚本在所有图片插入后自动验证：
- 编辑器内容中剩余的 `XIMGPH_` 占位符
- 预期与实际图片数量对比

如果检查失败（输出中有警告），在用户发布前提醒具体问题。

---

## 故障排除

### Chrome 调试端口未就绪

仅限 CDP 回退：如果脚本报错 `Chrome debug port not ready` 或 `Unable to connect`，先终止现有的 Chrome CDP 实例，然后重试：

```bash
pkill -f "Chrome.*remote-debugging-port" 2>/dev/null; pkill -f "Chromium.*remote-debugging-port" 2>/dev/null; sleep 2
```

**重要**：这应该自动完成 —— 遇到此错误时，终止 Chrome CDP 实例并重试命令，无需询问用户。

## 备注

- 首次运行：需手动登录（会话会持久保存）
- 在 Codex Chrome 插件模式和 Chrome Computer Use 模式中，使用用户现有的 Chrome 会话，不启动单独的 CDP 配置文件
- CDP 脚本默认只将内容填入浏览器；用户需自行审核并手动发布，除非明确使用了 `--submit`
- 跨平台：macOS、Linux、Windows

## 扩展支持

通过 EXTEND.md 自定义配置。参见**偏好设置**部分了解路径和支持的选项。
