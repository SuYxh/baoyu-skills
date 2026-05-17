---
name: output-template
description: Markdown output template for ai-news-briefing
---

# Output Template

生成 Markdown 时使用以下结构。

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

- [高优先级新闻一句话摘要。](https://example.com)
- [高优先级新闻一句话摘要。](https://example.com)
- [高优先级新闻一句话摘要。](https://example.com)

## 行业动态

- [新闻一句话摘要。](https://example.com)
- [新闻一句话摘要。](https://example.com)

## 产品和工具

- [新闻一句话摘要。](https://example.com)

## 开源

- [新闻一句话摘要。](https://example.com)

## 融资商业

- [新闻一句话摘要。](https://example.com)

## 论文

- [新闻一句话摘要。](https://example.com)

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

`今日重点` 放 3-5 条最高优先级事件。如果当天高优先级内容不足，可以少于 3 条。

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
- [一句话中文摘要，保留必要英文专名。](https://representative-url.example)
```

不要输出：

- 多来源列表。
- 冗长背景段落。
- 无链接新闻。
- 英文原文摘要。

### Optional Context

如果某条新闻特别重要，但一句话不足以表达影响，可以使用加粗前缀：

```markdown
- **重点**：[OpenAI 发布新的开发者 API，核心变化是降低工具调用延迟并扩展多模态输入。](https://example.com)
```

谨慎使用，避免整篇都是重点。

### Fetch Notes

如果 `output.include_stats` 为 true，保留 `抓取说明`。

如果 `output.include_failed_sources` 为 true 且存在失败信源，追加：

```markdown
### 失败信源

- 来源名称：失败原因
- 来源名称：失败原因
```

如果失败信源很多，只列前 10 个，并说明其余数量。
