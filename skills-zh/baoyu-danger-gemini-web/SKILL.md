---
name: baoyu-danger-gemini-web
description: 通过逆向工程的 Gemini Web API 生成图像和文本。支持文本生成、根据提示词生成图像、参考图像用于视觉输入以及多轮对话。当其他技能需要图像生成后端，或用户请求"用 Gemini 生成图像"、"Gemini 文本生成"或需要具备视觉能力的 AI 生成时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-danger-gemini-web
    requires:
      anyBins:
        - bun
        - npx
---

# Gemini Web 客户端

通过 Gemini Web API 进行文本/图像生成。支持参考图像和多轮对话。

## 用户输入工具

当此技能需要向用户提问时，请遵循以下工具选择规则（按优先级排序）：

1. **优先使用内置的用户输入工具** —— 即当前代理运行时提供的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **备选方案**：如果没有此类工具，发送带编号的纯文本消息，让用户回复所选的编号/答案。
3. **批量处理**：如果工具支持一次调用多个问题，将所有适用问题合并为一次调用；如果只支持单个问题，按优先级顺序逐一提问。

下文中的 `AskUserQuestion` 引用仅为示例 —— 在其他运行时中请替换为本地等效工具。

## 脚本目录

**重要**：所有脚本位于此技能的 `scripts/` 子目录中。

**代理执行说明**：
1. 确定此 SKILL.md 文件的目录路径为 `{baseDir}`
2. 脚本路径 = `{baseDir}/scripts/<script-name>.ts`
3. 解析 `${BUN_X}` 运行时：如果已安装 `bun` → `bun`；如果 `npx` 可用 → `npx -y bun`；否则建议安装 bun
4. 将本文档中所有 `{baseDir}` 和 `${BUN_X}` 替换为实际值

**脚本参考**：
| 脚本 | 用途 |
|--------|---------|
| `scripts/main.ts` | 文本/图像生成的 CLI 入口 |
| `scripts/gemini-webapi/*` | `gemini_webapi` 的 TypeScript 移植（GeminiClient、类型、工具函数） |

## 同意检查（必需）

首次使用前，需验证用户对使用逆向工程 API 的同意。

**同意文件位置**：
- macOS: `~/Library/Application Support/baoyu-skills/gemini-web/consent.json`
- Linux: `~/.local/share/baoyu-skills/gemini-web/consent.json`
- Windows: `%APPDATA%\baoyu-skills\gemini-web\consent.json`

**流程**：
1. 检查同意文件是否存在，且 `accepted: true` 以及 `disclaimerVersion: "1.0"`
2. 如果存在有效同意 → 打印包含 `acceptedAt` 日期的警告信息，继续执行
3. 如果没有同意记录 → 显示免责声明，通过 `AskUserQuestion` 询问用户：
   - "是的，我接受" → 创建包含 ISO 时间戳的同意文件，继续执行
   - "不，我拒绝" → 输出拒绝消息，停止执行
4. 同意文件格式：`{"version":1,"accepted":true,"acceptedAt":"<ISO>","disclaimerVersion":"1.0"}`

---

## 偏好设置（EXTEND.md）

按优先级顺序检查 EXTEND.md —— 找到的第一个生效：

| 优先级 | 路径 | 作用域 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-danger-gemini-web/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-danger-gemini-web/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-danger-gemini-web/EXTEND.md` | 用户主目录 |

如果未找到，使用默认值。

**EXTEND.md 支持**：默认模型、代理设置、自定义数据目录。

## 用法

```bash
# 文本生成
${BUN_X} {baseDir}/scripts/main.ts "Your prompt"
${BUN_X} {baseDir}/scripts/main.ts --prompt "Your prompt" --model gemini-3-flash

# 图像生成
${BUN_X} {baseDir}/scripts/main.ts --prompt "A cute cat" --image cat.png
${BUN_X} {baseDir}/scripts/main.ts --promptfiles system.md content.md --image out.png

# 视觉输入（参考图像）
${BUN_X} {baseDir}/scripts/main.ts --prompt "Describe this" --reference image.png
${BUN_X} {baseDir}/scripts/main.ts --prompt "Create variation" --reference a.png --image out.png

# 多轮对话
${BUN_X} {baseDir}/scripts/main.ts "Remember: 42" --sessionId session-abc
${BUN_X} {baseDir}/scripts/main.ts "What number?" --sessionId session-abc

# JSON 输出
${BUN_X} {baseDir}/scripts/main.ts "Hello" --json
```

## 选项

| 选项 | 描述 |
|--------|-------------|
| `--prompt`, `-p` | 提示词文本 |
| `--promptfiles` | 从文件读取提示词（拼接） |
| `--model`, `-m` | 模型：gemini-3-pro（默认）、gemini-3-flash、gemini-3-flash-thinking、gemini-3.1-pro-preview |
| `--image [path]` | 生成图像（默认：generated.png） |
| `--reference`, `--ref` | 用于视觉输入的参考图像 |
| `--sessionId` | 多轮对话的会话 ID |
| `--list-sessions` | 列出已保存的会话 |
| `--json` | 以 JSON 格式输出 |
| `--login` | 刷新 Cookie，然后退出 |
| `--cookie-path` | 自定义 Cookie 文件路径 |
| `--profile-dir` | Chrome 配置文件目录 |

## 模型

| 模型 | 描述 |
|-------|-------------|
| `gemini-3-pro` | 默认，最新的 3.0 Pro |
| `gemini-3-flash` | 快速、轻量的 3.0 Flash |
| `gemini-3-flash-thinking` | 带思考能力的 3.0 Flash |
| `gemini-3.1-pro-preview` | 3.1 Pro 预览版（空 header，自动路由） |

## 认证

首次运行会打开浏览器进行 Google 认证。Cookie 会自动缓存。

当未设置明确的配置文件目录时，Cookie 刷新可能会复用已运行的本地 Chrome/Chromium 调试会话（绑定到标准用户数据目录）。
设置 `--profile-dir` 或 `GEMINI_WEB_CHROME_PROFILE_DIR` 可强制使用专用配置文件，跳过现有会话复用。
这是一种尽力而为的 CDP 会话复用路径，而非 Chrome 官方文档中描述的基于 Chrome DevTools MCP prompt 的 `--autoConnect` 流程。

支持的浏览器（自动检测）：Chrome、Chrome Canary/Beta、Chromium、Edge。

强制刷新：`--login` 标志。覆盖浏览器：`GEMINI_WEB_CHROME_PATH` 环境变量。

## 环境变量

| 变量 | 描述 |
|----------|-------------|
| `GEMINI_WEB_DATA_DIR` | 数据目录 |
| `GEMINI_WEB_COOKIE_PATH` | Cookie 文件路径 |
| `GEMINI_WEB_CHROME_PROFILE_DIR` | Chrome 配置文件目录 |
| `GEMINI_WEB_CHROME_PATH` | Chrome 可执行文件路径 |
| `HTTP_PROXY`, `HTTPS_PROXY` | 访问 Google 的代理（与命令内联设置） |

## 会话

会话文件存储在数据目录下的 `sessions/<id>.json`。

包含：`id`、`metadata`（Gemini 聊天状态）、`messages` 数组、时间戳。

## 扩展支持

通过 EXTEND.md 进行自定义配置。路径和支持的选项请参阅**偏好设置**部分。
