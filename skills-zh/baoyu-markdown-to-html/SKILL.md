---
name: baoyu-markdown-to-html
description: 将 Markdown 转换为带样式的 HTML，兼容微信主题。支持代码高亮、数学公式、PlantUML、脚注、警告提示、信息图以及可选的底部引用（用于外部链接）。当用户要求"markdown to html"、"convert md to html"、"md 转 html"、"微信外链转底部引用"或需要从 markdown 生成带样式的 HTML 输出时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-markdown-to-html
    requires:
      anyBins:
        - bun
        - npx
---

# Markdown 转 HTML 转换器

将 Markdown 文件转换为带内联 CSS 的精美 HTML，针对微信公众号及其他平台优化。

## 用户输入工具

当此技能需要向用户提问时，遵循以下工具选择规则（按优先级排序）：

1. **优先使用内置用户输入工具** —— 当前代理运行时暴露的工具，例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出带编号的纯文本消息，要求用户回复选择的编号/答案。
3. **批量处理**：如果工具支持单次调用多个问题，将所有适用问题合并为一次调用；如果只支持单个问题，按优先级顺序逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例 —— 在其他运行时中请替换为本地等效工具。

## 脚本目录

**代理执行**：确定此 SKILL.md 所在目录为 `{baseDir}`。解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果有 `npx` → `npx -y bun`；否则建议安装 bun。将 `{baseDir}` 和 `${BUN_X}` 替换为实际值。

| 脚本 | 用途 |
|--------|---------|
| `scripts/main.ts` | 主入口 |

## 偏好设置 (EXTEND.md)

按优先级顺序检查 EXTEND.md —— 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-markdown-to-html/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` | 用户主目录 |

如果都未找到，使用默认值。

**EXTEND.md 支持**：默认主题、自定义 CSS 变量、代码块样式。

## 工作流程

### 步骤 0：预检查（中文内容）

**条件**：仅在输入文件包含中文文本时执行。

**检测**：
1. 读取输入 markdown 文件
2. 检查内容是否包含 CJK 字符（中文/日文/韩文）
3. 如果没有 CJK 内容 → 跳至步骤 1

**格式建议**：

如果检测到 CJK 内容且 `baoyu-format-markdown` 技能可用：

使用 `AskUserQuestion` 询问是否先格式化。格式化可以修复：
- 粗体标记内含标点导致 `**` 解析失败
- CJK/英文间距问题

**如果用户同意**：调用 `baoyu-format-markdown` 技能格式化文件，然后使用格式化后的文件作为输入。

**如果用户拒绝**：继续使用原始文件。

### 步骤 1：确定主题

**主题解析顺序**（第一个匹配生效）：
1. 用户明确指定的主题（CLI `--theme` 或对话中指定）
2. EXTEND.md `default_theme`（此技能自身的 EXTEND.md，在步骤 0 中检查）
3. `baoyu-post-to-wechat` EXTEND.md `default_theme`（跨技能回退）
4. 如果都未找到 → 使用 AskUserQuestion 确认

**跨技能 EXTEND.md 检查**（仅当此技能的 EXTEND.md 没有 `default_theme` 时）：

读取 `$HOME/.baoyu-skills/baoyu-post-to-wechat/EXTEND.md`（如果存在）并查找 `default_theme:` 行。如果存在则使用其值；否则继续后续流程。

**如果主题从 EXTEND.md 解析得到**：直接使用，不要询问用户。

**如果未找到默认值**：使用 `AskUserQuestion` 从下方[主题](#themes)表格中确认主题。

### 步骤 1.5：确定引用模式

**默认**：关闭。默认不询问。

**仅在用户明确要求时启用**："微信外链转底部引用"、"底部引用"、"文末引用"，或传入 `--cite`。

**启用时的行为**：
- 普通外部链接以编号上标形式渲染，并收集到最后的 `引用链接` 部分。
- `https://mp.weixin.qq.com/...` 链接保持为直接链接，不移至底部。
- 链接文本等于 URL 的裸链接保持内联。

### 步骤 2：转换

```bash
${BUN_X} {baseDir}/scripts/main.ts <markdown_file> --theme <theme> [--cite]
```

### 步骤 3：报告结果

显示 JSON 结果中的输出路径。如果创建了备份，请提及。

## 用法

```bash
${BUN_X} {baseDir}/scripts/main.ts <markdown_file> [options]
```

**选项：**

| 选项 | 描述 | 默认值 |
|--------|-------------|---------|
| `--theme <name>` | 主题名称（default, grace, simple, modern） | default |
| `--color <name\|hex>` | 主色调：预设名称或十六进制值 | 主题默认 |
| `--font-family <name>` | 字体：sans, serif, serif-cjk, mono 或 CSS 值 | 主题默认 |
| `--font-size <N>` | 字号：14px, 15px, 16px, 17px, 18px | 16px |
| `--title <title>` | 覆盖 frontmatter 中的标题 | |
| `--cite` | 将外部链接转换为底部引用，追加 `引用链接` 部分 | false（关闭） |
| `--keep-title` | 保留内容中的第一个标题 | false（移除） |
| `--help` | 显示帮助 | |

**颜色预设：**

| 名称 | 十六进制 | 标签 |
|------|-----|-------|
| blue | #0F4C81 | 经典蓝 |
| green | #009874 | 翡翠绿 |
| vermilion | #FA5151 | 活力朱红 |
| yellow | #FECE00 | 柠檬黄 |
| purple | #92617E | 薰衣草紫 |
| sky | #55C9EA | 天空蓝 |
| rose | #B76E79 | 玫瑰金 |
| olive | #556B2F | 橄榄绿 |
| black | #333333 | 石墨黑 |
| gray | #A9A9A9 | 烟灰 |
| pink | #FFB7C5 | 樱花粉 |
| red | #A93226 | 中国红 |
| orange | #D97757 | 暖橙（modern 默认） |

**示例：**

```bash
# 基本转换（使用默认主题，移除第一个标题）
${BUN_X} {baseDir}/scripts/main.ts article.md

# 指定主题
${BUN_X} {baseDir}/scripts/main.ts article.md --theme grace

# 主题搭配自定义颜色
${BUN_X} {baseDir}/scripts/main.ts article.md --theme modern --color red

# 启用底部引用（普通外部链接）
${BUN_X} {baseDir}/scripts/main.ts article.md --cite

# 保留内容中的第一个标题
${BUN_X} {baseDir}/scripts/main.ts article.md --keep-title

# 覆盖标题
${BUN_X} {baseDir}/scripts/main.ts article.md --title "My Article"
```

## 输出

**文件位置**：与输入 markdown 文件同目录。
- 输入：`/path/to/article.md`
- 输出：`/path/to/article.html`

**冲突处理**：如果 HTML 文件已存在，将先进行备份：
- 备份：`/path/to/article.html.bak-YYYYMMDDHHMMSS`

**标准输出 JSON：**

```json
{
  "title": "Article Title",
  "author": "Author Name",
  "summary": "Article summary...",
  "htmlPath": "/path/to/article.html",
  "backupPath": "/path/to/article.html.bak-20260128180000",
  "contentImages": [
    {
      "placeholder": "MDTOHTMLIMGPH_1",
      "localPath": "/path/to/img.png",
      "originalPath": "imgs/image.png"
    }
  ]
}
```

## 主题

| 主题 | 描述 |
|-------|-------------|
| `default` | 经典 - 传统布局，居中标题带底部边框，H2 白色文字配彩色背景 |
| `grace` | 优雅 - 文字阴影，圆角卡片，精致引用块（作者 @brzhang） |
| `simple` | 简约 - 现代极简风，非对称圆角，干净留白（作者 @okooo5km） |
| `modern` | 现代 - 大圆角，胶囊形标题，宽松行高（搭配 `--color red` 可呈现传统红金风格） |

## 支持的 Markdown 特性

| 特性 | 语法 |
|---------|--------|
| 标题 | `# H1` 到 `###### H6` |
| 粗体/斜体 | `**bold**`、`*italic*` |
| 代码块 | ` ```lang ` 带语法高亮 |
| 行内代码 | `` `code` `` |
| 表格 | GitHub 风格 markdown 表格 |
| 图片 | `![alt](src)` |
| 链接 | `[text](url)`；添加 `--cite` 可将普通外部链接移至底部引用 |
| 引用块 | `> quote` |
| 列表 | `-` 无序列表，`1.` 有序列表 |
| 警告提示 | `> [!NOTE]`、`> [!WARNING]` 等 |
| 脚注 | `[^1]` 引用 |
| 注音 | `{base|annotation}` |
| Mermaid | ` ```mermaid ` 图表 |
| PlantUML | ` ```plantuml ` 图表 |

## Frontmatter

支持 YAML frontmatter 元数据：

```yaml
---
title: Article Title
author: Author Name
description: Article summary
---
```

如果未找到标题，将从第一个 H1/H2 标题提取或使用文件名。

## 扩展支持

通过 EXTEND.md 自定义配置。参见**偏好设置**部分了解路径和支持的选项。
