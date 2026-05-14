---
name: baoyu-post-to-weibo
description: 发布内容到微博。支持包含文字、图片和视频的普通帖子，以及通过 Chrome CDP 发布 Markdown 输入的头条文章。当用户要求"post to Weibo"、"发微博"、"发布微博"、"publish to Weibo"、"share on Weibo"、"写微博"或"微博头条文章"时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-post-to-weibo
    requires:
      anyBins:
        - bun
        - npx
---

# 发布到微博

通过真实 Chrome 浏览器将文字、图片、视频和长文发布到微博（绕过反机器人检测）。

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
| `scripts/weibo-post.ts` | 普通帖子（文字 + 图片） |
| `scripts/weibo-article.ts` | 头条文章发布（Markdown） |
| `scripts/copy-to-clipboard.ts` | 复制内容到剪贴板 |
| `scripts/paste-from-clipboard.ts` | 发送真实粘贴按键 |

## 偏好设置 (EXTEND.md)

按优先级顺序检查 EXTEND.md —— 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-post-to-weibo/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-post-to-weibo/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-post-to-weibo/EXTEND.md` | 用户主目录 |

如果都未找到，使用默认值。

**EXTEND.md 支持**：默认 Chrome 配置文件

## 前置要求

- Google Chrome 或 Chromium
- `bun` 运行时
- 首次运行：需手动登录微博（会话将被保存）

---

## 普通帖子

文字 + 图片/视频（总计最多 18 个文件）。发布在微博主页。

```bash
${BUN_X} {baseDir}/scripts/weibo-post.ts "Hello Weibo!" --image ./photo.png
${BUN_X} {baseDir}/scripts/weibo-post.ts "Watch this" --video ./clip.mp4
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<text>` | 帖子内容（位置参数） |
| `--image <path>` | 图片文件（可重复） |
| `--video <path>` | 视频文件（可重复） |
| `--profile <dir>` | 自定义 Chrome 配置文件 |

**注意**：脚本会打开浏览器并填入内容。用户需自行审核并手动发布。

---

## 头条文章

在 `https://card.weibo.com/article/v3/editor` 发布的长文 Markdown 文章。

```bash
${BUN_X} {baseDir}/scripts/weibo-article.ts article.md
${BUN_X} {baseDir}/scripts/weibo-article.ts article.md --cover ./cover.jpg
```

**参数**：
| 参数 | 描述 |
|-----------|-------------|
| `<markdown>` | Markdown 文件（位置参数） |
| `--cover <path>` | 封面图 |
| `--title <text>` | 覆盖标题（最多 32 字符，超长则截断） |
| `--summary <text>` | 覆盖摘要（最多 44 字符，超长则从内容自动重新生成） |
| `--profile <dir>` | 自定义 Chrome 配置文件 |

**Frontmatter**：YAML front matter 中支持 `title`、`summary`、`cover_image`。

**字符限制**：
- 标题：最多 32 字符（超长时截断并给出警告）
- 摘要/导语：最多 44 字符（超长时从内容自动重新生成）

**Markdown 转 HTML**：转换 markdown 为 HTML 时不要传任何 `--theme` 参数。使用默认主题（不带主题参数）。

**文章工作流**：
1. 打开 `https://card.weibo.com/article/v3/editor`
2. 点击"写文章"按钮，等待编辑器变为可编辑状态
3. 填入标题（验证 32 字符限制）
4. 填入摘要/导语（验证 44 字符限制）
5. 通过粘贴将 HTML 内容插入 ProseMirror 编辑器
6. 逐一替换图片占位符（复制图片 → 选中占位符 → 粘贴）

**发布前检查**：脚本在所有图片插入后自动验证：
- 编辑器内容中剩余的 `WBIMGPH_` 占位符
- 预期与实际图片数量对比

如果检查失败（输出中有警告），在用户发布前提醒具体问题。

---

## 帖子类型选择

除非用户明确指定帖子类型：
- **Markdown 文件**（`.md`）→ **头条文章**
- **纯文本** / 文字配图片 → **普通帖子**

## 故障排除

### Chrome 调试端口未就绪

如果脚本报错 `Chrome debug port not ready` 或 `Unable to connect`，仅终止 CDP Chrome 实例（带有 `--remote-debugging-port` 且使用 baoyu-skills 配置文件的实例），然后重试：

```bash
pkill -f "remote-debugging-port.*baoyu-skills/chrome-profile" 2>/dev/null; sleep 2
```

**关键**：永远不要终止所有 Chrome 进程（`pkill -f "Google Chrome"`）。只终止由 CDP 启动并使用 baoyu-skills 配置文件目录的 Chrome 实例。用户可能有正常的 Chrome 窗口在使用。

**重要**：这应该自动完成 —— 遇到此错误时，终止 CDP Chrome 实例并重试命令，无需询问用户。

## 备注

- 首次运行：需手动登录（会话会持久保存）
- 所有脚本只是将内容填入浏览器，用户需自行审核并手动发布
- 跨平台：macOS、Linux、Windows

## 扩展支持

通过 EXTEND.md 自定义配置。参见**偏好设置**部分了解路径和支持的选项。
