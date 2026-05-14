---
name: baoyu-url-to-markdown
description: 使用 baoyu-fetch CLI（Chrome CDP 配合站点特定适配器）抓取任意 URL 并转换为 markdown。内置 X/Twitter、YouTube 字幕、Hacker News 讨论串及通用页面（通过 Defuddle）的适配器。通过交互等待模式处理登录/验证码。当用户想将网页保存为 markdown 时使用。
version: 1.61.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-url-to-markdown
    requires:
      anyBins:
        - bun
---

# URL 转 Markdown

通过 `baoyu-fetch` CLI（Chrome CDP + 站点特定适配器）抓取任意 URL 并将其转换为干净的 markdown。

## 用户输入工具

当本技能需要提示用户时，按以下工具选择规则（优先级从高到低）：

1. **优先使用内置用户输入工具**，即当前代理运行时提供的工具——例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出编号的纯文本消息，要求用户针对每个问题回复所选编号/答案。
3. **批量处理**：如果工具支持单次调用中提出多个问题，则将所有适用问题合并为一次调用；如果仅支持单个问题，则按优先级顺序逐一询问。

下文中的 `AskUserQuestion` 引用是示例——在其他运行时中请替换为本地等效工具。

## CLI 设置

**重要**：CLI 源代码已内置在 `{baseDir}/scripts/lib` 中。`scripts/package.json` 仅安装第三方运行时依赖。

**代理执行指令**：
1. 确定本 SKILL.md 文件的目录路径为 `{baseDir}`
2. 解析 `${BUN}` 运行时：如果安装了 `bun` → `bun`；否则建议安装 Bun
3. 如果 `{baseDir}/scripts/node_modules` 不存在，运行 `${BUN} install --cwd {baseDir}/scripts`
4. `${READER}` = `{baseDir}/scripts/baoyu-fetch`
5. 将本文档中所有 `${READER}` 替换为解析后的值

## 偏好设置（EXTEND.md）

按优先级顺序检查 EXTEND.md——找到第一个即生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-url-to-markdown/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-url-to-markdown/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-url-to-markdown/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|--------|--------|
| 找到 | 读取、解析、应用设置 |
| 未找到 | **必须**运行首次设置（见下方）——不要静默创建默认值 |

**EXTEND.md 支持**：默认下载媒体、默认输出目录。

### 首次设置 ⛔ 阻塞性

当找不到 EXTEND.md 时，您**必须**使用 `AskUserQuestion` 收集偏好设置后才能创建 EXTEND.md。**绝不**用静默默认值创建 EXTEND.md。在设置完成前生成被**阻塞**。将所有三个问题批量放入一次调用：

- **Q1 — 媒体**（标题"媒体"）："如何处理页面中的图片和视频？"
  - "每次询问（推荐）" — 每次保存后提示
  - "始终下载" — 下载到本地 `imgs/` 和 `videos/`
  - "不下载" — 保留远程 URL
- **Q2 — 输出**（标题"输出"）："默认输出目录？"
  - "url-to-markdown（推荐）" — 保存到 `./url-to-markdown/{domain}/{slug}.md`
  - 用户可选择"其他"并输入自定义路径
- **Q3 — 保存**（标题"保存"）："偏好设置保存在哪里？"
  - "用户级（推荐）" — `~/.baoyu-skills/`（所有项目）
  - "项目级" — `.baoyu-skills/`（仅本项目）

回答后，写入 EXTEND.md，确认"偏好设置已保存到 [path]"，然后继续。

完整模板：[references/config/first-time-setup.md](references/config/first-time-setup.md)。

### 支持的键

| 键 | 默认值 | 值 | 描述 |
|-----|---------|--------|-------------|
| `download_media` | `ask` | `ask` / `1` / `0` | `ask` = 每次提示，`1` = 始终下载，`0` = 不下载 |
| `default_output_dir` | 空 | 路径或空 | 默认输出目录（空 = `./url-to-markdown/`） |

**EXTEND.md → CLI 映射**：

| EXTEND.md 键 | CLI 参数 | 备注 |
|---------------|-------------|-------|
| `download_media: 1` | `--download-media` | 需要设置 `--output` |
| `default_output_dir: ./posts/` | 代理构建 `--output ./posts/{domain}/{slug}.md` | 代理生成路径，非直接标志 |

**值优先级**：CLI 参数 → EXTEND.md → 技能默认值。

## 用法

```bash
# 默认：无头抓取，markdown 输出到标准输出
${READER} <url>

# 保存到文件
${READER} <url> --output article.md

# 保存并下载媒体
${READER} <url> --output article.md --download-media

# 等待交互（登录/验证码）— 自动检测并继续
${READER} <url> --wait-for interaction --output article.md

# 等待交互 — 手动控制（按 Enter 继续）
${READER} <url> --wait-for force --output article.md

# JSON 输出
${READER} <url> --format json --output article.json

# 强制使用特定适配器
${READER} <url> --adapter youtube --output transcript.md
```

## 选项

| 选项 | 描述 |
|--------|-------------|
| `<url>` | 要抓取的 URL |
| `--output <path>` | 输出文件路径（默认：标准输出） |
| `--format <type>` | 输出格式：`markdown`（默认）或 `json` |
| `--json` | `--format json` 的简写 |
| `--adapter <name>` | 强制适配器：`x`、`youtube`、`hn` 或 `generic`（默认：自动检测） |
| `--headless` | 强制无头 Chrome（无可见窗口） |
| `--wait-for <mode>` | 交互等待模式：`none`（默认）、`interaction` 或 `force` |
| `--wait-for-interaction` | `--wait-for interaction` 的别名 |
| `--wait-for-login` | `--wait-for interaction` 的别名 |
| `--timeout <ms>` | 页面加载超时时间（默认：30000） |
| `--interaction-timeout <ms>` | 登录/验证码等待超时（默认：600000 = 10 分钟） |
| `--interaction-poll-interval <ms>` | 交互检查的轮询间隔（默认：1500） |
| `--download-media` | 下载图片/视频到本地 `imgs/` 和 `videos/`，重写 markdown 链接。需要 `--output` |
| `--media-dir <dir>` | 下载媒体的基础目录（默认：与 `--output` 相同的目录） |
| `--cdp-url <url>` | 复用已有的 Chrome DevTools Protocol 端点 |
| `--browser-path <path>` | 自定义 Chrome/Chromium 二进制文件路径 |
| `--chrome-profile-dir <path>` | Chrome 用户数据目录（默认：`BAOYU_CHROME_PROFILE_DIR` 环境变量或 `./baoyu-skills/chrome-profile`） |
| `--debug-dir <dir>` | 写入调试产物（document.json、markdown.md、page.html、network.json） |

## 代理质量门控

**关键**：将默认无头抓取视为临时性结果。某些网站在无头模式下渲染不同，可能在不触发 CLI 失败的情况下静默返回低质量内容。

每次无头运行后，检查保存的 markdown。完整检查清单、恢复工作流程和抓取模式表参见 [references/quality-gate.md](references/quality-gate.md)。当运行看起来可疑或用户询问登录/验证码处理时阅读该文件。

## 输出路径生成

代理必须构建输出文件路径——`baoyu-fetch` 不会自动生成路径。

**算法**：
1. 从 EXTEND.md `default_output_dir` 确定基础目录，或使用默认的 `./url-to-markdown/`
2. 从 URL 提取域名（例如 `example.com`）
3. 从 URL 路径或页面标题生成 slug（kebab-case，2-6 个词）
4. 构建：`{base_dir}/{domain}/{slug}/{slug}.md` — 每个 URL 有自己的目录，使媒体文件保持隔离
5. 冲突解决：追加时间戳 `{slug}-YYYYMMDD-HHMMSS/{slug}-YYYYMMDD-HHMMSS.md`

将构建的路径传递给 `--output`。媒体文件（`--download-media`）保存在 markdown 文件旁的子目录中，使每个 URL 的资源自包含。

## 适配器与媒体

适配器目录（X、YouTube、Hacker News、通用）、每个适配器的注意事项、媒体下载流程（`ask`/始终/不下载）和 JSON 输出 schema 参见 [references/adapters.md](references/adapters.md)。在回答适配器相关问题或处理媒体提示前阅读该文件。

## 环境变量

| 变量 | 描述 |
|----------|-------------|
| `BAOYU_CHROME_PROFILE_DIR` | Chrome 用户数据目录（也可使用 `--chrome-profile-dir`） |

**故障排除**：Chrome 未找到 → 使用 `--browser-path`。超时 → 增加 `--timeout`。登录/验证码 → `--wait-for interaction`。调试 → `--debug-dir` 检查捕获的 HTML 和网络日志。

## 扩展支持

通过 EXTEND.md 进行自定义配置。路径和支持的键参见上方**偏好设置**部分。
