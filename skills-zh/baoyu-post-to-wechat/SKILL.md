---
name: baoyu-post-to-wechat
description: 通过 API 或 Chrome CDP 发布内容到微信公众号。支持文章发布（文章）—— 接受 HTML、markdown 或纯文本输入，以及贴图发布（贴图，原图文）—— 支持多张图片。Markdown 文章工作流默认将普通外部链接转换为底部引用，以生成微信友好的输出。当用户提到"发布公众号"、"post to wechat"、"微信公众号"或"贴图/图文/文章"时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-post-to-wechat
    requires:
      anyBins:
        - bun
        - npx
---

# 发布到微信公众号

## 用户输入工具

当此技能需要向用户提问时，遵循以下工具选择规则（按优先级排序）：

1. **优先使用内置用户输入工具** —— 当前代理运行时暴露的工具，例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出带编号的纯文本消息，要求用户回复选择的编号/答案。
3. **批量处理**：如果工具支持单次调用多个问题，将所有适用问题合并为一次调用；如果只支持单个问题，按优先级顺序逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例 —— 在其他运行时中请替换为本地等效工具。

## 语言

使用用户的语言回复。如果用户使用中文，则用中文回复；如果使用英文，则用英文回复。技术标识（路径、标志、字段名）保持英文。

## 脚本目录

`{baseDir}` = 此 SKILL.md 所在目录。解析 `${BUN_X}`：优先使用 `bun`；否则 `npx -y bun`；否则建议 `brew install oven-sh/bun/bun`。

| 脚本 | 用途 |
|--------|---------|
| `scripts/wechat-browser.ts` | 贴图发布（图文） |
| `scripts/wechat-article.ts` | 通过浏览器发布文章（文章） |
| `scripts/wechat-api.ts` | 通过 API 发布文章（文章） |
| `scripts/md-to-wechat.ts` | Markdown → 微信就绪 HTML（含图片占位符） |
| `scripts/check-permissions.ts` | 验证环境和权限 |

## 偏好设置 (EXTEND.md)

按顺序检查以下路径；找到的第一个生效：

| 路径 | 范围 |
|------|-------|
| `.baoyu-skills/baoyu-post-to-wechat/EXTEND.md` | 项目级 |
| `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-post-to-wechat/EXTEND.md` | XDG |
| `$HOME/.baoyu-skills/baoyu-post-to-wechat/EXTEND.md` | 用户主目录 |

找到 → 读取、解析、应用。未找到 → 在执行任何操作前先运行首次设置（`references/config/first-time-setup.md`）。

**最小必需键**（不区分大小写，接受 `1/0` 或 `true/false`）：

| 键 | 默认值 | 映射 |
|-----|---------|---------|
| `default_author` | 空 | 当 CLI/frontmatter 未提供时作为 `author` 的回退值 |
| `need_open_comment` | `1` | `draft/add` 中的 `articles[].need_open_comment` |
| `only_fans_can_comment` | `0` | `draft/add` 中的 `articles[].only_fans_can_comment` |

**推荐的 EXTEND.md**：

```md
default_theme: default
default_color: blue
default_publish_method: api
default_author: 宝玉
need_open_comment: 1
only_fans_can_comment: 0
chrome_profile_path: /path/to/chrome/profile
```

**主题选项**：default, grace, simple, modern。**颜色预设**：blue, green, vermilion, yellow, purple, sky, rose, olive, black, gray, pink, red, orange（或十六进制值）。

**值优先级**：CLI 参数 → frontmatter → EXTEND.md（账号级 → 全局） → 技能默认值。

## 多账号支持

EXTEND.md 支持 `accounts:` 块用于管理多个公众号。当有 2 个以上条目时，工作流会插入步骤 0.5 提示账号选择（或根据 `default: true` 或 `--account <alias>` 自动选择）。

完整细节 —— 兼容性规则、每账号键、凭据解析、每账号 Chrome 配置文件、CLI 用法 —— 参见 `references/multi-account.md`。

## 飞行前检查（可选）

首次使用前，建议进行环境检查（用户可跳过）：

```bash
${BUN_X} {baseDir}/scripts/check-permissions.ts
```

检查项：Chrome、配置文件隔离、Bun、辅助功能、剪贴板、粘贴按键、API 凭据、Chrome 冲突。

| 检查失败项 | 修复方法 |
|-------------|-----|
| Chrome | 安装 Chrome 或设置 `WECHAT_BROWSER_CHROME_PATH` |
| 配置文件目录 | 共享配置文件位于 `baoyu-skills/chrome-profile` |
| Bun 运行时 | `brew install oven-sh/bun/bun` 或 `npm install -g bun` |
| 辅助功能 (macOS) | 系统设置 → 隐私与安全性 → 辅助功能 → 启用终端应用 |
| 剪贴板复制 | 确保 Swift/AppKit 可用（macOS：`xcode-select --install`） |
| 粘贴按键 (Linux) | 安装 `xdotool`（X11）或 `ydotool`（Wayland） |
| API 凭据 | 按步骤 2 中的引导设置操作，或在 `.baoyu-skills/.env` 中设置 |

## 贴图发布（图文）

带多张图片的短帖子（最多 9 张）：

```bash
${BUN_X} {baseDir}/scripts/wechat-browser.ts --markdown article.md --images ./images/
${BUN_X} {baseDir}/scripts/wechat-browser.ts --title "标题" --content "内容" --image img.png --submit
```

详情：`references/image-text-posting.md`。

## 文章发布工作流（文章）

```
- [ ] 步骤 0：加载偏好设置 (EXTEND.md)
- [ ] 步骤 0.5：解析账号（仅多账号 —— 参见 references/multi-account.md）
- [ ] 步骤 1：确定输入类型
- [ ] 步骤 2：选择方法并配置凭据
- [ ] 步骤 3：解析主题/颜色并验证元数据
- [ ] 步骤 4：发布到微信
- [ ] 步骤 5：报告完成
```

### 步骤 0：加载偏好设置

检查并加载 EXTEND.md（参见上方"偏好设置"）。如果未找到，在提出任何其他问题之前完成首次设置。解析并缓存以供后续步骤使用：`default_theme`、`default_color`、`default_author`、`need_open_comment`、`only_fans_can_comment`。

### 步骤 1：确定输入类型

| 输入 | 检测方式 | 下一步 |
|-------|-----------|------|
| HTML 文件 | 路径以 `.html` 结尾，文件存在 | 跳至步骤 3 |
| Markdown 文件 | 路径以 `.md` 结尾，文件存在 | 步骤 2 |
| 纯文本 | 不是文件路径，或文件不存在 | 保存为 markdown，然后步骤 2 |

**纯文本处理**：

1. 生成 slug（前 2-4 个有意义的词，kebab-case；中文翻译为英文作为 slug）。
2. 保存到 `post-to-wechat/YYYY-MM-DD/<slug>.md`（如需要则创建目录）。
3. 作为 markdown 文件继续处理。

### 步骤 2：选择发布方法并配置

除非在 EXTEND.md 或 CLI 中已指定，否则询问方法：

| 方法 | 速度 | 需要 |
|--------|-------|----------|
| `api`（推荐） | 快速 | API 凭据 |
| `browser` | 较慢 | Chrome + 已登录会话 |

**选择 API + 缺少凭据** → 按 `references/api-setup.md` 运行引导设置（写入 `.baoyu-skills/.env`）。

### 步骤 3：解析主题/颜色并验证元数据

1. **主题**：CLI `--theme` → EXTEND.md `default_theme` → `default`（第一个匹配生效；如果已解析则不要询问）。
2. **颜色**：CLI `--color` → EXTEND.md `default_color` → 省略（使用主题默认）。
3. **验证元数据**（markdown 用 frontmatter，HTML 用 meta 标签）：

| 字段 | 缺失时 → |
|-------|-----------|
| 标题 | 询问，或按 Enter 从内容自动生成 |
| 摘要 | Frontmatter `description` → `summary` → 询问或自动生成 |
| 作者 | CLI `--author` → frontmatter `author` → EXTEND.md `default_author` |

自动生成：标题 = 第一个 H1/H2 或第一句话；摘要 = 第一段，截断至 120 字符。

4. **封面图**（API `article_type=news` 时必需）：CLI `--cover` → frontmatter（`coverImage` / `featureImage` / `cover` / `image`） → `imgs/cover.png` → 第一张内联图片 → 如果仍缺失则停止并要求提供。

### 步骤 4：发布

**重要 —— 不要预先将 markdown 转换为 HTML。** 发布脚本会在内部处理转换，且两种方法渲染图片的方式不同：API 渲染 `<img>` 标签用于上传，浏览器使用占位符进行粘贴替换。传入预转换的 HTML 会导致其中一种方法失效。

**Markdown 引用默认值**：对于 markdown 输入，普通外部链接默认转换为底部引用。仅当用户明确要求保留内联链接时才使用 `--no-cite`。已有的 HTML 输入保持不变。

**API 方法**（接受 `.md` 或 `.html`）：

```bash
${BUN_X} {baseDir}/scripts/wechat-api.ts <file> --theme <theme> [--color <color>] [--title <title>] [--summary <summary>] [--author <author>] [--cover <cover_path>] [--no-cite]
```

即使是 `default` 也始终传入 `--theme`。仅当用户或 EXTEND.md 明确设置时才传入 `--color`。

**`draft/add` 载荷规则**：
- 端点：`POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN`
- `article_type`：`news`（默认）或 `newspic`
- 对于 `news`，需包含 `thumb_media_id`（封面必需）
- 请求体中始终包含 `need_open_comment`（默认 `1`）和 `only_fans_can_comment`（默认 `0`），即使 CLI 不暴露它们

**浏览器方法**（接受 `--markdown` 或 `--html`）：

```bash
${BUN_X} {baseDir}/scripts/wechat-article.ts --markdown <markdown_file> --theme <theme> [--color <color>] [--no-cite]
${BUN_X} {baseDir}/scripts/wechat-article.ts --html <html_file>
```

### 步骤 5：完成报告

```
微信发布完成！

输入：[类型] - [路径]
方法：[API | 浏览器]
主题：[主题] [颜色（如设置）]

文章：
• 标题：[标题]
• 摘要：[摘要]
• 图片：[N] 张内联
• 评论：[开启/关闭]，[仅粉丝/全部]    ← 仅 API 方法

结果：
✓ 草稿已保存到微信公众号
• media_id: [media_id]                         ← 仅 API 方法

后续步骤（API）：
→ 管理草稿：https://mp.weixin.qq.com（登录后进入「内容管理」→「草稿箱」）

创建的文件：
[• post-to-wechat/YYYY-MM-DD/slug.md（如纯文本输入）]
[• slug.html（已转换）]
```

## 功能对比

| 功能 | 贴图 | 文章 (API) | 文章 (浏览器) |
|---------|:---:|:---:|:---:|
| 纯文本输入 | ✗ | ✓ | ✓ |
| HTML 输入 | ✗ | ✓ | ✓ |
| Markdown 输入 | 标题/内容 | ✓ | ✓ |
| 多张图片 | ✓（最多 9 张） | ✓（内联） | ✓（内联） |
| 主题 | ✗ | ✓ | ✓ |
| 自动生成元数据 | ✗ | ✓ | ✓ |
| 默认封面回退（`imgs/cover.png`） | ✗ | ✓ | ✗ |
| 评论控制 | ✗ | ✓ | ✗ |
| 需要 Chrome | ✓ | ✗ | ✓ |
| 需要 API 凭据 | ✗ | ✓ | ✗ |
| 速度 | 中等 | 快速 | 较慢 |

## 故障排除

| 问题 | 修复方法 |
|-------|-----|
| 缺少 API 凭据 | 按步骤 2 中的引导设置操作 |
| 访问令牌错误 | 验证凭据有效且未过期 |
| 未登录（浏览器） | 首次运行会打开浏览器 —— 扫码登录 |
| 找不到 Chrome | 设置 `WECHAT_BROWSER_CHROME_PATH` |
| 标题/摘要缺失 | 使用自动生成或手动提供 |
| 没有封面图 | 添加 frontmatter cover 或在文章目录放置 `imgs/cover.png` |
| 评论默认值错误 | 检查 EXTEND.md 中的 `need_open_comment` / `only_fans_can_comment` |
| 粘贴失败 | 检查系统剪贴板权限 |

## 参考文档

| 文件 | 内容 |
|------|---------|
| `references/image-text-posting.md` | 贴图参数、自动压缩 |
| `references/article-posting.md` | 文章主题、图片处理 |
| `references/multi-account.md` | 多账号兼容性、凭据、Chrome 配置文件、CLI |
| `references/api-setup.md` | 引导式凭据设置 |
| `references/config/first-time-setup.md` | 首次 EXTEND.md 设置 |

## 扩展支持

通过 EXTEND.md 自定义配置。参见"偏好设置"了解路径和支持的选项。
