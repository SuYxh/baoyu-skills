---
name: preferences-schema
description: EXTEND.md YAML schema for ai-news-briefing preferences
---

# Preferences Schema

默认完整配置保存在 `defaults.yaml`。`EXTEND.md` 是覆盖文件：只写需要覆盖的字段即可，未写字段从默认配置继承。

## Full Schema

```yaml
---
version: 1

source_opml: references/config/default-sources.opml

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
  insecure_skip_verify: true

categories:
  - 行业动态
  - 产品和工具
  - 开源
  - 融资商业
  - 论文

source_weights:
  OpenAI(@OpenAI): 1.3
  Anthropic(@AnthropicAI): 1.3
  Hugging Face(@huggingface): 1.2

keywords:
  include:
    - agent
    - model
    - benchmark
  exclude:
    - giveaway
    - discount

output:
  detail_level: standard
  title_links: true
  include_images: true
  image_mode: remote
  max_images_per_item: 1
  include_source_line: true
  include_stats: true
  include_failed_sources: true
  include_raw_json_path: true
---
```

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | int | 1 | Schema version |
| `source_opml` | string | `references/config/default-sources.opml` | OPML 文件路径；可使用内置信源或用户自定义路径 |
| `default_time_window` | string | `24h` | 默认时间窗口，支持 `12h`、`24h`、`7d` |
| `default_output_dir` | string | `news` | Markdown 输出目录 |
| `language` | enum | `zh` | 输出语言；当前默认要求中文 |
| `max_items` | int/null | `null` | 最多输出条目数；`null` 表示不限 |
| `dedupe_mode` | enum | `semantic` | `strict`、`semantic`、`loose` |
| `ranking_mode` | enum | `importance` | `time`、`importance`、`source_weight` |
| `fetch_full_text` | enum | `important-only` | `rss-only`、`important-only`、`all` |
| `full_text_top_n` | int | 20 | `important-only` 时最多补抓原文数量 |
| `fetch.timeout` | int | 20 | 单次请求超时秒数 |
| `fetch.workers` | int | 4 | RSS 抓取并发数 |
| `fetch.retries` | int | 1 | 首次失败后的重试次数 |
| `fetch.retry_backoff` | float | 1.5 | 重试前等待秒数，按尝试次数递增 |
| `fetch.max_feed_bytes` | int | 5000000 | 单个 RSS feed 最大压缩读取字节数 |
| `fetch.insecure_skip_verify` | bool | true | 是否跳过 TLS 证书校验；脚本默认跳过，严格校验时传 `--verify-tls` |
| `categories` | string[] | 5 个默认分类 | Markdown 输出分类集合 |
| `source_weights` | map | `{}` | 来源权重，key 建议使用 OPML 中的 `text` 或 `title` |
| `keywords.include` | string[] | `[]` | 提升排序或保留的关键词 |
| `keywords.exclude` | string[] | `[]` | 降权或排除的关键词 |
| `output.detail_level` | enum | `standard` | `brief`、`standard`、`detailed` |
| `output.title_links` | bool | true | 标题是否必须链接到代表原文 |
| `output.include_images` | bool | true | 是否允许插入新闻相关图片 |
| `output.image_mode` | enum | `remote` | `remote`、`download`、`none`；当前默认远程图片链接 |
| `output.max_images_per_item` | int | 1 | 每条资讯最多插入图片数 |
| `output.include_source_line` | bool | true | 是否在条目末尾输出来源行 |
| `output.include_stats` | bool | true | 是否输出抓取统计 |
| `output.include_failed_sources` | bool | true | 是否列出失败信源 |
| `output.include_raw_json_path` | bool | true | 是否在末尾记录原始 JSON 路径 |

## Time Window

| Value | Meaning |
|-------|---------|
| `24h` | 最近 24 小时 |
| `7d` | 最近 7 天 |
| `2026-05-01..2026-05-07` | 指定日期区间，闭区间 |

## Deduplication Modes

| Value | Description |
|-------|-------------|
| `strict` | 只合并相同 URL 或高度相似标题 |
| `semantic` | 合并同一事件的多来源报道，默认推荐 |
| `loose` | 将相近趋势或话题也归并，简报更短但更容易损失细节 |

## Fetch Full Text Modes

| Value | Description |
|-------|-------------|
| `rss-only` | 只使用 RSS 标题和摘要 |
| `important-only` | 先基于 RSS 选出重要条目，再补抓原文 |
| `all` | 尽量抓取所有条目原文，速度慢且失败率更高 |

## Example: Minimal Preferences

```yaml
---
version: 1
source_opml: /Users/bytedance/Desktop/fc/person-project/baoyu-skills/follow.opml
---
```

## Example: Project Preferences

```yaml
---
version: 1
source_opml: /Users/bytedance/Desktop/fc/person-project/baoyu-skills/follow.opml
default_time_window: 24h
default_output_dir: news
language: zh
fetch_full_text: important-only
full_text_top_n: 20
categories:
  - 行业动态
  - 产品和工具
  - 开源
  - 融资商业
  - 论文
source_weights:
  OpenAI(@OpenAI): 1.3
  Anthropic(@AnthropicAI): 1.3
  Qwen(@Alibaba_Qwen): 1.2
keywords:
  include:
    - Agent
    - multimodal
    - benchmark
  exclude:
    - coupon
---
```
