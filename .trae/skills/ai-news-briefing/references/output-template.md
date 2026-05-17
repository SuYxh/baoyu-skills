---
name: output-template
description: Markdown output template for ai-news-briefing
---

# Output Template

生成 Markdown 时使用以下结构。默认输出不再是“一句话列表”，而是可点击标题的信息卡片。

## File Naming

| Type | Filename |
|------|----------|
| Daily | `news/YYYY-MM-DD.md` |
| Weekly | `news/YYYY-MM-DD-weekly.md` |
| Custom topic | `news/YYYY-MM-DD-{topic-slug}.md` |

## Template

```markdown
# AI 资讯简报：YYYY-MM-DD

> 时间窗口：最近 24 小时
> 生成时间：YYYY-MM-DD HH:mm
> 信源：成功 N 个，失败 M 个
> 候选条目：N 条，去重后 M 条

## 今日重点

### [高优先级新闻标题](https://example.com)

这条新闻是什么：用 1 句话说明核心事实，保留必要英文专名。  
为什么值得关注：用 1 句话说明对模型能力、产品趋势、开发者或行业格局的影响。  
来源：OpenAI Developers

![相关配图](https://example.com/image.jpg)

## 行业动态

### [新闻标题](https://example.com)

用 2-3 句话说明事件本身、关键背景和影响。  
来源：来源名称

## 产品和工具

### [新闻标题](https://example.com)

用 2-3 句话说明产品能力、使用场景和适合关注的人群。  
来源：来源名称

## 开源

### [新闻标题](https://example.com)

用 2-3 句话说明项目做什么、亮点是什么、适合谁使用。  
来源：来源名称

## 融资商业

### [新闻标题](https://example.com)

用 2-3 句话说明交易/融资/商业合作细节和行业影响。  
来源：来源名称

## 论文

### [论文或研究标题](https://example.com)

用 2-3 句话说明研究问题、核心发现和可能影响。  
来源：来源名称

## 抓取说明

- 原始条目：N
- 时间窗口内：N
- 基础去重后：N
- 语义去重后：N
- 补抓原文：N
- 失败信源：N
- 原始数据：`news/raw-YYYY-MM-DD.json`
```

## Writing Rules

### Title

标题格式：

```markdown
# AI 资讯简报：YYYY-MM-DD
```

周报格式：

```markdown
# AI 资讯周报：YYYY-MM-DD 至 YYYY-MM-DD
```

### Front Summary

开头引用块用于快速说明范围：

- 时间窗口。
- 生成时间。
- 成功和失败信源数量。
- 候选条目和去重后条目数量。

### Top Highlights

`今日重点` 放 3-5 条最高优先级事件。如果当天高优先级内容不足，可以少于 3 条。今日重点也必须使用可点击标题，不要退回到纯列表。

选择标准：

- 多来源重复报道。
- 官方或一手来源发布。
- 对模型能力、开发者工具、行业格局有明显影响。
- 具有行动价值，例如新 API、开源仓库、论文代码、产品可用。

### Category Sections

默认分类：

- `行业动态`
- `产品和工具`
- `开源`
- `融资商业`
- `论文`

空分类可以省略。

### Item Format

默认单条格式：

```markdown
### [可点击新闻标题](https://representative-url.example)

第一句说明这件事是什么，避免只写标题改写。  
第二句说明为什么重要，或者对开发者、产品、行业有什么影响。  
第三句可选：补充背景、限制、适合关注的人群或后续观察。

来源：来源名称

![图片说明](https://image-url.example/image.jpg)
```

不要输出：

- 多来源列表。
- 不可点击的标题或加粗标题。
- 只有一句话的过短摘要。
- 冗长背景段落。
- 无链接新闻。
- 英文原文摘要。
- 与新闻无关的头像、logo、icon、表情图、tracking pixel。

### Detail Levels

| Level | Format |
|-------|--------|
| `brief` | 每条 1 句话，但标题仍必须可点击 |
| `standard` | 默认；每条 2-3 句，覆盖事实和影响 |
| `detailed` | 每条 1 小段，可包含背景、影响、风险和后续观察 |

默认使用 `standard`。除非用户明确要求“极简”或配置为 `brief`，不要生成一句话列表。

### Title Links

标题链接是强制要求：

```markdown
### [OpenAI Codex 多项更新](https://example.com)
```

不要这样写：

```markdown
- **OpenAI Codex 多项更新**：性能优化…… — 来源：OpenAI Developers
```

因为加粗标题无法点击，用户不能直接跳转原文。

### Images

如果脚本 JSON 中的 `image_candidates` 有高质量候选图，可以在条目末尾插入最多 1 张：

```markdown
![新闻相关配图](https://example.com/image.jpg)
```

插入图片的条件：

- 图片来自 RSS 的 `media:content`、`enclosure`、description 中的 `<img>`，或原文 `og:image` / `twitter:image` / 正文首图。
- 图片与新闻主题明显相关，适合作为读者视觉辅助。
- 不要插入头像、logo、icon、emoji、tracking pixel、小尺寸装饰图。
- 如果不确定图片是否相关，宁可不插入。

默认每条最多 1 张图。不要为了“有图”而插入无关图。

### Fetch Notes

如果 `output.include_stats` 为 true，保留 `抓取说明`。

如果 `output.include_failed_sources` 为 true 且存在失败信源，追加：

```markdown
### 失败信源

- 来源名称：失败原因
- 来源名称：失败原因
```

如果失败信源很多，只列前 10 个，并说明其余数量。
