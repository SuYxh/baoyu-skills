---
name: baoyu-youtube-transcript
description: 通过 URL 或视频 ID 下载 YouTube 视频字幕/副标题和封面图片。支持多语言、翻译、章节和说话人识别。缓存原始数据以便快速重新格式化。当用户要求"get YouTube transcript"、"download subtitles"、"get captions"、"YouTube字幕"、"YouTube封面"、"视频封面"、"video thumbnail"、"video cover image"，或提供 YouTube URL 并需要提取字幕/副标题文本或封面图片时使用。
version: 1.1.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-youtube-transcript
    requires:
      anyBins:
        - bun
        - npx
---

# YouTube 字幕下载

从 YouTube 视频下载字幕（副标题/说明文字）。支持手动创建和自动生成的字幕。无需 API 密钥或浏览器 — 直接使用 YouTube 的 InnerTube API，并在 YouTube 阻止直接 API 路径时自动回退到 `yt-dlp`。

首次运行时获取视频元数据和封面图片，缓存原始数据以便快速重新格式化。

## 脚本目录

脚本位于 `scripts/` 子目录中。`{baseDir}` = 本 SKILL.md 所在目录路径。解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果 `npx` 可用 → `npx -y bun`；否则建议安装 bun。将 `{baseDir}` 和 `${BUN_X}` 替换为实际值。

| 脚本 | 用途 |
|--------|---------|
| `scripts/main.ts` | 字幕下载 CLI |

## 用法

```bash
# 默认：带时间戳的 markdown（英文）
${BUN_X} {baseDir}/scripts/main.ts <youtube-url-or-id>

# 指定语言（按优先级排序）
${BUN_X} {baseDir}/scripts/main.ts <url> --languages zh,en,ja

# 不带时间戳
${BUN_X} {baseDir}/scripts/main.ts <url> --no-timestamps

# 带章节分段
${BUN_X} {baseDir}/scripts/main.ts <url> --chapters

# 带说话人识别（需要 AI 后处理）
${BUN_X} {baseDir}/scripts/main.ts <url> --speakers

# SRT 字幕文件
${BUN_X} {baseDir}/scripts/main.ts <url> --format srt

# 翻译字幕
${BUN_X} {baseDir}/scripts/main.ts <url> --translate zh-Hans

# 列出可用字幕
${BUN_X} {baseDir}/scripts/main.ts <url> --list

# 强制重新获取（忽略缓存）
${BUN_X} {baseDir}/scripts/main.ts <url> --refresh
```

## 选项

| 选项 | 描述 | 默认值 |
|--------|-------------|---------|
| `<url-or-id>` | YouTube URL 或视频 ID（支持多个） | 必填 |
| `--languages <codes>` | 语言代码，逗号分隔，按优先级排序 | `en` |
| `--format <fmt>` | 输出格式：`text`、`srt` | `text` |
| `--translate <code>` | 翻译到指定语言代码 | |
| `--list` | 列出可用字幕而非获取 | |
| `--timestamps` | 每段包含 `[HH:MM:SS → HH:MM:SS]` 时间戳 | 开启 |
| `--no-timestamps` | 禁用时间戳 | |
| `--chapters` | 从视频描述中提取章节分段 | |
| `--speakers` | 带元数据的原始字幕，用于说话人识别 | |
| `--exclude-generated` | 跳过自动生成的字幕 | |
| `--exclude-manually-created` | 跳过手动创建的字幕 | |
| `--refresh` | 强制重新获取，忽略缓存数据 | |
| `-o, --output <path>` | 保存到指定文件路径 | 自动生成 |
| `--output-dir <dir>` | 基础输出目录 | `youtube-transcript` |

## 可选环境变量

| 变量 | 描述 |
|----------|-------------|
| `YOUTUBE_TRANSCRIPT_COOKIES_FROM_BROWSER` | 在回退时传递给 `yt-dlp --cookies-from-browser`，如 `chrome`、`safari`、`firefox` 或 `chrome:Profile 1` |

## 输入格式

接受以下任何格式作为视频输入：
- 完整 URL：`https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- 短链接：`https://youtu.be/dQw4w9WgXcQ`
- 嵌入 URL：`https://www.youtube.com/embed/dQw4w9WgXcQ`
- Shorts URL：`https://www.youtube.com/shorts/dQw4w9WgXcQ`
- 视频 ID：`dQw4w9WgXcQ`

## 输出格式

| 格式 | 扩展名 | 描述 |
|--------|-----------|-------------|
| `text` | `.md` | 带 frontmatter（含 `description`）的 Markdown，包含标题、摘要、可选目录/封面/时间戳/章节/说话人 |
| `srt` | `.srt` | SubRip 字幕格式，用于视频播放器 |

## 输出目录

```
youtube-transcript/
├── .index.json                          # 视频 ID → 目录路径映射（用于缓存查找）
└── {channel-slug}/{title-full-slug}/
    ├── meta.json                        # 视频元数据（标题、频道、描述、时长、章节等）
    ├── transcript-raw.json              # YouTube API 返回的原始字幕片段（已缓存）
    ├── transcript-sentences.json        # 按句子分段的字幕（按标点分割，跨片段合并）
    ├── imgs/
    │   └── cover.jpg                    # 视频缩略图
    ├── transcript.md                    # Markdown 字幕（从句子生成）
    └── transcript.srt                   # SRT 字幕（从原始片段生成，如使用 --format srt）
```

- `{channel-slug}`：频道名称的 kebab-case 格式
- `{title-full-slug}`：完整视频标题的 kebab-case 格式

`--list` 模式仅输出到 stdout（不保存文件）。

## 缓存

首次获取时，脚本保存：
- `meta.json` — 视频元数据、章节、封面图路径、语言信息
- `transcript-raw.json` — YouTube API 返回的原始字幕片段（`{ text, start, duration }[]`）
- `transcript-sentences.json` — 按句子分段的字幕（`{ text, start: "HH:mm:ss", end: "HH:mm:ss" }[]`），按句末标点（`.?!…。？！` 等）分割，时间戳按字符长度比例分配，支持 CJK 文本合并
- `imgs/cover.jpg` — 视频缩略图

后续对同一视频的运行使用缓存数据（无网络请求）。使用 `--refresh` 强制重新获取。如果请求了不同语言，缓存会自动刷新。

当 YouTube 在直接 InnerTube 路径上返回反机器人/封锁响应时，脚本会使用备用客户端身份重试，然后在 `yt-dlp` 可用时回退到它。如果需要回退但 `yt-dlp` 不可用，代理应自行决定如何让 `yt-dlp` 可用并继续，而不是将安装决策推给用户。

SRT 输出（`--format srt`）从 `transcript-raw.json` 生成。文本/Markdown 输出使用 `transcript-sentences.json` 以获取自然的句子边界。

## 工作流

当用户提供 YouTube URL 并需要字幕时：

1. 如果用户未指定语言，先使用 `--list` 显示可用选项
2. **运行脚本时始终用单引号包裹 URL** — zsh 将 `?` 视为通配符，未加引号的 YouTube URL 会导致"no matches found"：使用 `'https://www.youtube.com/watch?v=ID'`
3. 默认：使用 `--chapters --speakers` 运行以获得最丰富的输出（章节 + 说话人识别）
3. 脚本自动保存缓存数据 + 输出文件并打印文件路径
4. 对于 `--speakers` 模式：脚本保存原始文件后，按下方说话人识别工作流进行后处理以添加说话人标签

当用户只需要封面图或元数据时，使用任何选项运行脚本也会缓存 `meta.json` 和 `imgs/cover.jpg`。

当对同一视频重新格式化时（如先文本后 SRT），使用已缓存数据 — 无需重新获取。

## 章节与说话人工作流

### 章节（`--chapters`）

脚本从视频描述中解析章节时间戳（如 `0:00 Introduction`），按章节边界分段字幕，将片段组合为可读段落，并保存为带目录的 `.md` 文件。无需进一步处理。

如果描述中不存在章节时间戳，字幕将作为分组段落输出，不带章节标题。

### 说话人识别（`--speakers`）

说话人识别需要 AI 处理。脚本输出一个原始 `.md` 文件，包含：
- 带视频元数据的 YAML frontmatter（标题、频道、日期、封面、描述、语言）
- 视频描述（用于提取说话人姓名）
- 描述中的章节列表（如有）
- SRT 格式的原始字幕（预计算的开始/结束时间戳，token 高效）

脚本保存原始文件后，生成一个子代理（使用更便宜的模型如 Sonnet 以提高成本效率）来处理说话人识别：

1. 读取保存的 `.md` 文件
2. 读取 `{baseDir}/prompts/speaker-transcript.md` 中的提示词模板
3. 按提示词处理原始字幕：
   - 使用视频元数据识别说话人（标题 → 嘉宾，频道 → 主持人，描述 → 姓名）
   - 从对话流、问答模式和上下文线索检测说话人切换
   - 分段为章节（如有描述章节则使用，否则从话题转换创建）
   - 使用 `**说话人姓名：**` 标签格式化，段落分组（2-4 句），带 `[HH:MM:SS → HH:MM:SS]` 时间戳
4. 用处理后的字幕覆盖 `.md` 文件（保留 YAML frontmatter）

使用 `--speakers` 时，`--chapters` 被隐含 — 处理后的输出始终包含章节分段。

## 错误情况

| 错误 | 含义 |
|-------|---------|
| Transcripts disabled | 视频完全没有字幕 |
| No transcript found | 请求的语言不可用 |
| Video unavailable | 视频已删除、设为私密或有地区限制 |
| IP blocked | 请求过多，稍后重试 |
| Age restricted | 视频需要登录进行年龄验证 |
| bot detected | 脚本会重试备用客户端然后使用 `yt-dlp`；如果回退工具缺失，代理应自行解决，否则如果仍然失败尝试 `YOUTUBE_TRANSCRIPT_COOKIES_FROM_BROWSER=safari`（或你的浏览器） |
