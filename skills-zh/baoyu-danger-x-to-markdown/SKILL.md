---
name: baoyu-danger-x-to-markdown
description: 将 X（Twitter）推文和文章转换为带有 YAML front matter 的 Markdown。使用逆向工程 API，需要用户同意。当用户提到"X 转 Markdown"、"推文转 Markdown"、"保存推文"或提供 x.com/twitter.com URL 进行转换时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-danger-x-to-markdown
    requires:
      anyBins:
        - bun
        - npx
---

# X 转 Markdown

将 X 内容转换为 Markdown：
- 推文/推文串 → 带有 YAML front matter 的 Markdown
- X 文章 → 完整内容提取

## 用户输入工具

当此技能需要向用户提问时，请遵循以下工具选择规则（按优先级排序）：

1. **优先使用内置的用户输入工具** —— 即当前代理运行时提供的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **备选方案**：如果没有此类工具，发送带编号的纯文本消息，让用户回复所选的编号/答案。
3. **批量处理**：如果工具支持一次调用多个问题，将所有适用问题合并为一次调用；如果只支持单个问题，按优先级顺序逐一提问。

下文中的 `AskUserQuestion` 引用仅为示例 —— 在其他运行时中请替换为本地等效工具。

## 脚本目录

脚本位于 `scripts/` 子目录中。

**路径解析**：
1. `{baseDir}` = 此 SKILL.md 的目录
2. 脚本路径 = `{baseDir}/scripts/main.ts`
3. 解析 `${BUN_X}` 运行时：如果已安装 `bun` → `bun`；如果 `npx` 可用 → `npx -y bun`；否则建议安装 bun

## 同意要求

**在任何转换之前**，需检查并获取用户同意。

### 同意流程

**步骤 1**：检查同意文件

```bash
# macOS
cat ~/Library/Application\ Support/baoyu-skills/x-to-markdown/consent.json

# Linux
cat ~/.local/share/baoyu-skills/x-to-markdown/consent.json
```

**步骤 2**：如果 `accepted: true` 且 `disclaimerVersion: "1.0"` → 打印警告并继续：
```
Warning: Using reverse-engineered X API. Accepted on: <acceptedAt>
```

**步骤 3**：如果缺失或版本不匹配 → 显示免责声明：
```
免责声明

此工具使用逆向工程的 X API，非官方接口。

风险：
- 如果 X 更改 API 可能会失效
- 不提供任何保证或支持
- 可能导致账号限制
- 使用风险自负

是否接受条款并继续？
```

使用 `AskUserQuestion` 提供选项："是的，我接受" | "不，我拒绝"

**步骤 4**：接受后 → 创建同意文件：
```json
{
  "version": 1,
  "accepted": true,
  "acceptedAt": "<ISO timestamp>",
  "disclaimerVersion": "1.0"
}
```

**步骤 5**：拒绝后 → 输出"用户已拒绝。退出。"并停止。

## 偏好设置（EXTEND.md）

按优先级顺序检查 EXTEND.md —— 找到的第一个生效：

| 优先级 | 路径 | 作用域 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-danger-x-to-markdown/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-danger-x-to-markdown/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-danger-x-to-markdown/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|--------|--------|
| 找到 | 读取、解析、应用设置 |
| 未找到 | **必须**执行首次设置（见下文）—— 不要静默创建默认值 |

**EXTEND.md 支持**：默认下载媒体、默认输出目录。

### 首次设置（阻塞操作）

**关键**：当未找到 EXTEND.md 时，你**必须使用 `AskUserQuestion`** 询问用户的偏好设置，然后再创建 EXTEND.md。**绝不**在未询问的情况下使用默认值创建 EXTEND.md。这是一个**阻塞**操作 —— 在设置完成之前不要继续任何转换。

使用 `AskUserQuestion` 将所有问题放在一次调用中：

**问题 1** — 标题："媒体"，问题："如何处理推文中的图片和视频？"
- "每次询问（推荐）" — 保存 Markdown 后，询问是否下载媒体
- "始终下载" — 始终将媒体下载到本地 imgs/ 和 videos/ 目录
- "从不下载" — 在 Markdown 中保留原始远程 URL

**问题 2** — 标题："输出"，问题："默认输出目录？"
- "x-to-markdown（推荐）" — 保存到 ./x-to-markdown/{username}/{tweet-id}.md
- （用户可以选择"其他"来输入自定义路径）

**问题 3** — 标题："保存"，问题："将偏好设置保存在哪里？"
- "用户级（推荐）" — ~/.baoyu-skills/（所有项目）
- "项目级" — .baoyu-skills/（仅限当前项目）

用户回答后，在所选位置创建 EXTEND.md，确认"偏好设置已保存到 [路径]"，然后继续。

完整参考：[references/config/first-time-setup.md](references/config/first-time-setup.md)

### 支持的配置项

| 配置项 | 默认值 | 可选值 | 描述 |
|-----|---------|--------|-------------|
| `download_media` | `ask` | `ask` / `1` / `0` | `ask` = 每次提示，`1` = 始终下载，`0` = 从不下载 |
| `default_output_dir` | 空 | 路径或空 | 默认输出目录（空 = `./x-to-markdown/`） |

**值优先级**：
1. CLI 参数（`--download-media`、`-o`）
2. EXTEND.md
3. 技能默认值

## 用法

```bash
${BUN_X} {baseDir}/scripts/main.ts <url>
${BUN_X} {baseDir}/scripts/main.ts <url> -o output.md
${BUN_X} {baseDir}/scripts/main.ts <url> --download-media
${BUN_X} {baseDir}/scripts/main.ts <url> --json
```

## 选项

| 选项 | 描述 |
|--------|-------------|
| `<url>` | 推文或文章 URL |
| `-o <path>` | 输出路径 |
| `--json` | JSON 输出 |
| `--download-media` | 将图片/视频资源下载到本地 `imgs/` 和 `videos/`，并将 Markdown 中的链接重写为本地相对路径 |
| `--login` | 仅刷新 Cookie |

## 支持的 URL

- `https://x.com/<user>/status/<id>`
- `https://twitter.com/<user>/status/<id>`
- `https://x.com/i/article/<id>`

## 输出

```markdown
---
url: "https://x.com/user/status/123"
author: "Name (@user)"
tweetCount: 3
coverImage: "https://pbs.twimg.com/media/example.jpg"
---

Content...
```

**文件结构**：`x-to-markdown/{username}/{tweet-id}/{content-slug}.md`

当启用 `--download-media` 时：
- 图片保存到 Markdown 文件旁的 `imgs/` 目录
- 视频保存到 Markdown 文件旁的 `videos/` 目录
- Markdown 中的媒体链接重写为本地相对路径

## 媒体下载工作流

基于 EXTEND.md 中的 `download_media` 设置：

| 设置 | 行为 |
|---------|----------|
| `1`（始终） | 使用 `--download-media` 标志运行脚本 |
| `0`（从不） | 不使用 `--download-media` 标志运行脚本 |
| `ask`（默认） | 遵循下方的每次询问流程 |

### 每次询问流程

1. **不使用** `--download-media` 运行脚本 → Markdown 已保存
2. 检查已保存的 Markdown 中是否有远程媒体 URL（图片/视频链接中的 `https://`）
3. **如果未找到远程媒体** → 完成，无需提示
4. **如果找到远程媒体** → 使用 `AskUserQuestion`：
   - 标题："媒体"，问题："是否将 N 个图片/视频下载到本地文件？"
   - "是" — 下载到本地目录
   - "否" — 保留远程 URL
5. 如果用户确认 → **再次**使用 `--download-media` 运行脚本（用本地化链接覆盖 Markdown）

## 认证

1. **环境变量**（首选）：`X_AUTH_TOKEN`、`X_CT0`
2. **Chrome 登录**（备选）：自动打开 Chrome，在本地缓存 Cookie

## 扩展支持

通过 EXTEND.md 进行自定义配置。路径和支持的选项请参阅**偏好设置**部分。
