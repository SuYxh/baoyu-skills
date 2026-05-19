---
name: ai-news-briefing
description: 生成 AI 资讯日报/周报，读取 OPML/RSS 信源，抓取最近资讯，进行语义去重、重要性排序、主题分类，并输出中文 Markdown 简报。当用户要求"AI 资讯"、"AI 日报"、"AI 周报"、"生成资讯简报"、"聚合 RSS"、"从 OPML 生成新闻摘要"或需要把大量 AI 信源整理成可读 Markdown 时必须使用。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#ai-news-briefing
---

# AI 资讯简报

读取用户配置的 OPML/RSS 信源，生成去重、分类、按重要性排序的中文 Markdown AI 资讯日报/周报。

## 核心目标

| 能力 | 默认行为 |
|------|----------|
| 信源 | 从 OPML 读取 RSS 源，默认使用内置 `references/config/default-sources.opml`，用户可通过 `EXTEND.md` 覆盖 |
| 时间窗口 | 最近 24 小时 |
| 抓取方式 | 脚本抓 RSS；重要条目再抓原文补充 |
| 去重 | 语义去重：同一事件多来源合并 |
| 分类 | 行业动态、产品和工具、开源、融资商业、论文 |
| 排序 | 重要性优先 |
| 输出 | 中文 Markdown，默认保存到 `news/` |
| 来源 | 合并后只保留代表链接 |

## 脚本目录

脚本位于 `scripts/` 子目录中。`{baseDir}` = 此 `SKILL.md` 所在目录。

| 脚本 | 用途 |
|------|------|
| `scripts/fetch_news.py` | 读取 OPML、抓取 RSS、规范化条目、基础去重、可选抓原文，并输出 JSON |

脚本依赖策略：

- 标准库即可运行：使用 `xml.etree.ElementTree`、`urllib`、`email.utils` 解析 OPML/RSS/Atom。
- 检测到 `feedparser` 时自动增强 RSS 解析。
- 检测到 `beautifulsoup4` 时自动增强原文正文抽取。
- 不要求用户先安装依赖；缺失依赖时只降低解析质量，不中断主流程。
- RSS 抓取默认跳过 TLS 证书校验以兼容公司代理、自签证书和部分代理源；如需严格校验，显式追加 `--verify-tls`。

## 偏好设置（EXTEND.md）

按优先顺序检查 `EXTEND.md`，找到的第一个生效：

| 优先级 | 路径 | 范围 |
|--------|------|------|
| 1 | `.baoyu-skills/ai-news-briefing/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/ai-news-briefing/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/ai-news-briefing/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|------|------|
| 找到 | 读取、解析并在执行前简短说明关键偏好 |
| 未找到 | 运行 [首次设置](references/config/first-time-setup.md)，保存 `EXTEND.md` 后继续 |

完整 schema 见 [preferences-schema.md](references/config/preferences-schema.md)。默认配置见 [defaults.yaml](references/config/defaults.yaml)，内置信源见 [default-sources.opml](references/config/default-sources.opml)。

## 默认配置

默认值不在 `SKILL.md` 内展开，避免多处维护。执行时以 [defaults.yaml](references/config/defaults.yaml) 为默认配置，以 [default-sources.opml](references/config/default-sources.opml) 为内置信源；用户的 `EXTEND.md` 只覆盖需要修改的字段。

## 工作流程

```
- [ ] 步骤 1：预检查配置（EXTEND.md、OPML 路径、输出目录）
- [ ] 步骤 2：抓取 RSS（scripts/fetch_news.py）
- [ ] 步骤 3：筛选时间窗口和 AI 相关内容
- [ ] 步骤 4：语义去重并选择代表来源
- [ ] 步骤 5：重要性排序
- [ ] 步骤 6：主题分类
- [ ] 步骤 7：生成 Markdown
- [ ] 步骤 8：保存文件并汇报统计
```

详细执行规则见 [workflow.md](references/workflow.md)。

## 使用方法

### 生成默认日报

```bash
python3 {baseDir}/scripts/fetch_news.py \
  --since 24h \
  --fetch-full-text important-only \
  --timeout 20 \
  --workers 4 \
  --retries 1 \
  --source-health-output news/source-health-YYYY-MM-DD.md \
  --output news/raw-YYYY-MM-DD.json
```

执行脚本后，读取 JSON，继续完成模型侧工作：

1. 根据 `items` 字段进行语义去重：同一事件合并为一个新闻项。
2. 按重要性排序：多源重复、官方来源、模型/产品发布、开源项目、论文/融资优先。
3. 归入默认 5 类。
4. 按 [输出模板](templates/output-template.md) 写入 Markdown：标题必须可点击，默认每条 2-3 句说明，可插入相关图片。

### 用户指定周报

```bash
python3 {baseDir}/scripts/fetch_news.py \
  --opml "[source_opml]" \
  --since 7d \
  --fetch-full-text important-only \
  --timeout 20 \
  --workers 4 \
  --retries 1 \
  --output news/raw-weekly.json
```

排查慢源时追加 `--progress` 查看每个信源完成状态。`api.xgo.ing` 等 RSS 代理源响应时间波动较大，不要仅因单次超时判定信源失效。

## 去重规则

使用两层去重：

| 层级 | 执行者 | 规则 |
|------|--------|------|
| 基础去重 | 脚本 | 规范化 URL，移除 UTM，合并完全相同链接；标题规范化后完全相同也合并 |
| 语义去重 | 模型 | 合并描述同一事件的多来源条目，例如同一模型发布、同一产品更新、同一融资新闻 |

语义去重时保留信息最完整、最可信或最接近官方的代表链接。只在内部记录其他来源，不在正文展开全部来源。

## 分类规则

| 分类 | 收录内容 |
|------|----------|
| 行业动态 | AI 公司、模型发布、平台政策、生态竞争、重要版本更新 |
| 产品和工具 | 面向用户或开发者的 AI 产品、Agent 工具、IDE、API、工作流产品 |
| 开源 | 开源模型、框架、库、数据集、工程工具 |
| 融资商业 | 融资、并购、营收、商业合作、定价、企业客户 |
| 论文 | 论文、技术报告、研究突破、benchmark、评测方法 |

如果一个条目跨多个分类，选择读者最可能查找它的主分类；不要重复出现在多个分类中。

## 重要性排序

默认按以下信号综合判断：

1. 多个独立来源都报道或讨论同一事件。
2. 官方账号、公司博客、论文页、GitHub 仓库等一手来源优先。
3. 模型发布、重大产品能力、开源项目、价格/API 变化优先。
4. 对开发者或 AI 从业者有直接行动价值的内容优先。
5. 单纯观点、营销、重复转发、缺少信息增量的内容降权。

如果 `EXTEND.md` 中配置了 `source_weights`，将来源权重纳入排序，但不要让单一高权重来源压过明显更重要的多源事件。

## Markdown 输出

默认保存路径：

```text
{cwd}/news/YYYY-MM-DD.md
```

输出必须是中文。英文标题和摘要需要翻译或改写为自然中文；可保留必要的英文产品名、模型名、论文名和仓库名。

单条资讯默认使用信息卡格式：

```markdown
### [可点击新闻标题](https://representative-url.example)

用 2-3 句话说明事件本身、关键背景和影响。  
来源：来源名称

![新闻相关配图](https://image-url.example/image.jpg)
```

标题或加粗内容必须可点击跳转到代表链接；不要输出不可点击的 `**标题**：摘要` 形式。图片来自 `image_candidates`，每条最多 1 张，只有明显相关时才插入。

模板见 [output-template.md](templates/output-template.md)。

## 失败处理

| 场景 | 处理 |
|------|------|
| OPML 不存在 | 停止并要求用户提供正确路径，或运行首次设置 |
| RSS 源抓取失败 | 记录到 `failed_sources`，继续处理其他源 |
| 条目发布时间缺失 | 保留条目，但标记 `published_at: null`；时间窗口筛选时降权 |
| 原文抓取失败 | 使用 RSS 摘要继续，不阻塞 |
| TLS 证书失败 | 提醒用户可在可信网络内追加 `--insecure-skip-verify` 重试 |
| 没有匹配条目 | 输出空简报，说明时间窗口和成功抓取的信源数量 |

## 修改偏好

`EXTEND.md` 位于上文列出的第一个匹配路径。常见编辑：

- `source_opml: /path/to/follow.opml`：更换信源。
- `default_time_window: 24h` 或 `7d`：更改默认日报/周报窗口。
- `default_output_dir: news`：更改 Markdown 输出目录。
- `fetch_full_text: rss-only | important-only | all`：控制是否抓原文。
- `full_text_top_n: 20`：控制最多补抓多少个重要条目原文。
- `categories: [...]`：自定义分类集合。
- `source_weights`：为特定来源加权。
- `keywords.include` / `keywords.exclude`：加入偏好关键词或排除关键词。
