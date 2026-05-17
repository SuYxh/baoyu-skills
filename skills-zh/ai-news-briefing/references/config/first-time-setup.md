---
name: first-time-setup
description: First-time setup flow for ai-news-briefing preferences
---

# First-Time Setup

当没有找到 `EXTEND.md` 时，先完成偏好设置，再进入抓取流程。

**阻塞规则**：首次设置完成前，不要抓取 RSS、不要读取 OPML、不要生成 Markdown。先询问必要配置，保存 `EXTEND.md`，再继续主流程。

## Setup Flow

```
No EXTEND.md found
        │
        ▼
Ask user setup questions
        │
        ▼
Create EXTEND.md
        │
        ▼
Continue workflow
```

## Questions

优先使用运行时提供的用户输入工具，例如 `AskUserQuestion`。如果没有此类工具，则输出编号问题，让用户回复选项。

### Question 1: OPML Source

```text
header: "OPML"
question: "默认使用哪个 OPML 信源文件？"
options:
  - label: "follow.opml (Recommended)"
    description: "/Users/bytedance/Desktop/fc/person-project/baoyu-skills/follow.opml"
  - label: "稍后配置"
    description: "先保存为空，运行时再要求用户提供"
```

### Question 2: Time Window

```text
header: "时间窗口"
question: "默认生成多长时间范围内的 AI 资讯？"
options:
  - label: "24h (Recommended)"
    description: "日报默认值，抓取最近 24 小时"
  - label: "7d"
    description: "周报默认值，抓取最近 7 天"
  - label: "自定义"
    description: "例如 12h、3d、2026-05-01..2026-05-07"
```

### Question 3: Output Directory

```text
header: "输出目录"
question: "Markdown 简报默认保存到哪里？"
options:
  - label: "news/ (Recommended)"
    description: "在当前工作目录的 news/ 目录归档"
  - label: "当前目录"
    description: "直接保存到当前目录"
  - label: "自定义"
    description: "输入你自己的目录路径"
```

### Question 4: Save Location

```text
header: "保存位置"
question: "偏好设置保存到哪里？"
options:
  - label: "Project"
    description: ".baoyu-skills/ai-news-briefing/EXTEND.md，仅当前项目生效"
  - label: "User"
    description: "~/.baoyu-skills/ai-news-briefing/EXTEND.md，所有项目生效"
```

## Save Locations

| Choice | Path | Scope |
|--------|------|-------|
| Project | `.baoyu-skills/ai-news-briefing/EXTEND.md` | 当前项目 |
| User | `~/.baoyu-skills/ai-news-briefing/EXTEND.md` | 当前用户所有项目 |

## EXTEND.md Template

```yaml
---
version: 1
source_opml: /Users/bytedance/Desktop/fc/person-project/baoyu-skills/follow.opml
default_time_window: 24h
default_output_dir: news
language: zh
max_items: null
dedupe_mode: semantic
ranking_mode: importance
fetch_full_text: important-only
full_text_top_n: 20
fetch:
  timeout: 20
  workers: 4
  retries: 1
  retry_backoff: 1.5
  max_feed_bytes: 5000000
categories:
  - 行业动态
  - 产品和工具
  - 开源
  - 融资商业
  - 论文
source_weights: {}
keywords:
  include: []
  exclude: []
---
```

## After Setup

1. 创建目标目录。
2. 写入 `EXTEND.md`。
3. 告知用户偏好保存路径。
4. 回到 `SKILL.md` 的主流程继续执行。
