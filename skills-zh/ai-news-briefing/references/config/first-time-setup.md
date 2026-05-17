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
  - label: "内置信源 (Recommended)"
    description: "使用 references/config/default-sources.opml"
  - label: "自定义 OPML"
    description: "输入你自己的 OPML 文件路径"
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

默认完整配置见 `references/config/defaults.yaml`。创建 `EXTEND.md` 时只需要写入用户想覆盖的字段，不要复制整份默认配置。

```yaml
---
version: 1
source_opml: references/config/default-sources.opml
default_time_window: 24h
default_output_dir: news
fetch:
  insecure_skip_verify: true
output:
  detail_level: standard
  title_links: true
  include_images: true
---
```

## After Setup

1. 创建目标目录。
2. 写入 `EXTEND.md`。
3. 告知用户偏好保存路径。
4. 回到 `SKILL.md` 的主流程继续执行。
