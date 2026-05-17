---
name: workflow
description: Detailed workflow for ai-news-briefing
---

# Workflow

## Step 1: Pre-Check

1. 查找 `EXTEND.md`。
2. 未找到时运行 `references/config/first-time-setup.md`。
3. 确认 `source_opml` 存在。
4. 创建 `default_output_dir`。
5. 计算输出文件名：
   - 日报：`YYYY-MM-DD.md`
   - 周报：`YYYY-MM-DD-weekly.md`
   - 用户指定主题：`YYYY-MM-DD-{slug}.md`

## Step 2: Fetch RSS

调用脚本：

```bash
python3 {baseDir}/scripts/fetch_news.py \
  --opml "[source_opml]" \
  --since "[default_time_window]" \
  --fetch-full-text "[fetch_full_text]" \
  --top-full-text "[full_text_top_n]" \
  --timeout 20 \
  --workers 4 \
  --retries 1 \
  --source-health-output "[default_output_dir]/source-health-YYYY-MM-DD.md" \
  --output "[default_output_dir]/raw-YYYY-MM-DD.json"
```

如果使用内置信源，可省略 `--opml`；脚本默认读取 `references/config/default-sources.opml`。

脚本默认跳过 TLS 证书校验以兼容公司代理、自签证书和部分 RSS 代理源。如果需要严格证书校验，追加：

```bash
--verify-tls
```

脚本输出 JSON 后，先读取：

- `items`：候选资讯条目。
- `sources`：信源列表。
- `source_health`：每个信源的成功/失败、耗时、尝试次数、条目数。
- `failed_sources`：失败信源。
- `stats`：抓取、筛选、基础去重统计。

抓取策略：

- 默认小并发 `--workers 4`，避免 RSS 代理源被高并发打爆。
- 默认 `--timeout 20`，因为 `api.xgo.ing` 等源可能单次响应超过 5 秒。
- 默认 `--retries 1`，单次超时只算波动，不直接判定失效。
- 默认 `--insecure-skip-verify` 行为已开启；严格校验时使用 `--verify-tls`。
- 排查时追加 `--progress`，可以看到 `[12/70] OK source` 形式的进度。
- 健康报告中的 `slow` 表示成功但较慢，不等同于失败。

## Step 3: Filter

过滤规则：

1. 只保留时间窗口内的条目。
2. 保留明显 AI 相关内容。
3. 如果 `keywords.include` 非空，包含这些关键词的条目优先保留。
4. 如果 `keywords.exclude` 命中明显垃圾、广告或无关内容，剔除或降权。
5. 不要仅因英文内容剔除条目，最终输出时翻译为中文。

AI 相关判断信号：

- 模型、Agent、多模态、推理、训练、评测、上下文、RAG、工具调用、代码智能体。
- AI 公司、AI 产品、模型 API、IDE、开发者工具、开源模型、论文。
- 产业事件，如融资、并购、定价、监管、算力合作。

## Step 4: Semantic Deduplication

将候选条目聚合为事件簇。以下情况视为同一事件：

- 标题不同但核心实体、动作、时间一致，例如同一模型发布。
- 官方公告、媒体报道、用户讨论都指向同一产品更新。
- 多个来源引用同一论文、仓库或技术报告。
- 相同链接、镜像链接、带不同 UTM 的链接。

不要合并：

- 同一公司在同一天发布的不同产品。
- 同一模型的发布、评测、教程、商业解读，除非内容没有新增信息。
- 大主题相同但具体事件不同的行业评论。

每个事件簇生成一个新闻项：

```yaml
title: 中文标题
summary: 2-3 句中文摘要，覆盖事实和影响
category: 行业动态 | 产品和工具 | 开源 | 融资商业 | 论文
importance: high | medium | low
representative_url: 最可信或信息最完整的链接
source_name: 代表来源名称
source_count: 合并来源数量
published_at: ISO 时间或 null
image_candidates:
  - 可选图片 URL
```

代表来源选择顺序：

1. 官方博客、官方 X/Twitter、论文页、GitHub 仓库。
2. 信息最完整的原文页面。
3. 可信媒体或高质量个人来源。
4. 最早发布且内容清晰的 RSS 条目。

## Step 5: Rank

按重要性排序，优先级如下：

1. `high`：重大模型、产品、API、开源、论文、融资或行业事件。
2. `medium`：有实际信息增量的工具更新、教程、观点、benchmark。
3. `low`：重复讨论、碎片观点、轻量功能、弱相关内容。

重要性评分参考：

| Signal | Effect |
|--------|--------|
| 多来源报道 | 大幅加权 |
| 官方来源 | 加权 |
| source_weights 高 | 加权 |
| 包含 include 关键词 | 加权 |
| 命中 exclude 关键词 | 降权或剔除 |
| 缺少摘要和原文 | 降权 |
| 与 AI 弱相关 | 降权 |

## Step 6: Categorize

默认 5 类：

1. `行业动态`：公司动态、模型发布、平台战略、行业竞争、监管政策。
2. `产品和工具`：AI 应用、Agent 产品、IDE、API、开发者 SaaS、工作流工具。
3. `开源`：开源模型、框架、库、数据集、工程工具。
4. `融资商业`：融资、并购、商业合作、定价、营收、客户案例。
5. `论文`：论文、技术报告、benchmark、研究突破、评测方法。

分类要求：

- 每条只放入一个主分类。
- 空分类可以省略。
- 如果分类名称由用户自定义，沿用用户分类，但仍按相同思路归类。

## Step 7: Generate Markdown

使用 `references/output-template.md`。

写作规则：

- 全文中文。
- 单条资讯默认 2-3 句说明，覆盖“是什么”和“为什么值得关注”。
- 每条资讯使用 `### [标题](representative_url)`，标题必须可点击。
- 不要输出不可点击的 `**标题**：摘要` 形式。
- 标题要自然，不要机械翻译。
- 保留必要英文专名，例如 `GPT-5`、`Claude Code`、`LangChain`、`Qwen`。
- 避免夸张营销词，如"革命性"、"颠覆性"，除非来源明确且确有重大影响。
- 来源信息放在条目末尾，例如 `来源：OpenAI Developers`。
- 如果 `image_candidates` 中有明显相关的高质量图片，每条最多插入 1 张。

图片选择规则：

- 优先使用来自原文 `og:image` / `twitter:image` 或正文首图的图片。
- 其次使用 RSS `media:content`、`enclosure` 或 description 中的图片。
- 跳过头像、logo、icon、emoji、tracking pixel 和无关装饰图。
- 如果不确定图片是否和新闻相关，宁可不插入。

## Step 8: Save And Report

保存 Markdown 后，向用户汇报：

```text
AI 资讯简报已生成
文件：[path]
时间窗口：[window]
候选条目：[n]
去重后：[n]
分类：[category counts]
失败信源：[n]
原始数据：[raw json path]
```

如果没有生成任何新闻项，也要保存空简报，并说明可能原因：

- 时间窗口太短。
- 大量 RSS 抓取失败。
- 信源近期无更新。
- 关键词过滤过严。
