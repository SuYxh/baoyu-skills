---
name: baoyu-imagine
description: 基于 OpenAI GPT Image 2、Azure OpenAI、Google、OpenRouter、DashScope、Z.AI GLM-Image、MiniMax、即梦、Seedream 和 Replicate API 的 AI 图片生成。支持文生图、参考图片、宽高比和从保存的提示词文件批量生成。默认顺序执行；当用户已有多个提示词或需要稳定的多图吞吐时使用批量并行生成。当用户要求生成、创建或绘制图片时使用。
version: 1.58.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-imagine
    requires:
      anyBins:
        - bun
        - npx
---

# 图片生成（AI SDK）

基于官方 API 的图片生成。支持 OpenAI GPT Image 2、Azure OpenAI、Google、OpenRouter、DashScope（阿里通义万象）、Z.AI GLM-Image、MiniMax、Jimeng（即梦）、Seedream（豆包）和 Replicate。

## 用户输入工具

当本技能需要提示用户时，按以下优先级选择工具：

1. **优先使用内置用户输入工具** —— 当前代理运行时暴露的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，输出编号纯文本消息，要求用户回复对应编号/答案。
3. **批量处理**：如果工具支持单次调用多个问题，将所有适用问题合并为一次调用；如果仅支持单个问题，按优先级逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例——在其他运行时中请替换为本地等效工具。

## 脚本目录

`{baseDir}` = 本 SKILL.md 所在目录。主脚本：`{baseDir}/scripts/main.ts`。解析 `${BUN_X}`：优先 `bun`；否则 `npx -y bun`；否则建议 `brew install oven-sh/bun/bun`。

## 步骤 0：加载偏好设置 ⛔ 阻塞

此步骤必须在任何图片生成之前完成——在 EXTEND.md 存在之前生成被阻塞。

按以下顺序检查路径；首次命中即生效：

| 路径 | 范围 |
|------|-------|
| `.baoyu-skills/baoyu-imagine/EXTEND.md` | 项目 |
| `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-imagine/EXTEND.md` | XDG |
| `$HOME/.baoyu-skills/baoyu-imagine/EXTEND.md` | 用户主目录 |

- **找到** → 加载、解析、应用。如果 `default_model.[provider]` 为 null → 仅询问模型。
- **未找到** → 运行首次设置（`references/config/first-time-setup.md`），使用 AskUserQuestion 收集提供商 + 模型 + 质量 + 保存位置。保存 EXTEND.md，然后继续。在此完成之前不要生成图片。

旧版兼容性：如果 `.baoyu-skills/baoyu-image-gen/EXTEND.md` 存在而新路径不存在，运行时会将其重命名为 `baoyu-imagine`。如果两者都存在，运行时保持不变并使用新路径。

**EXTEND.md 键**：默认提供商、默认质量、默认宽高比、默认图片尺寸、OpenAI 图片 API 方言、默认模型、批量工作线程上限、提供商特定批量限制。Schema：`references/config/preferences-schema.md`。

## 用法

最小可用示例——完整示例集（包括各提供商调用和批量模式）见 `references/usage-examples.md`。

```bash
# 基础用法
${BUN_X} {baseDir}/scripts/main.ts --prompt "A cat" --image cat.png

# 指定宽高比和高质量
${BUN_X} {baseDir}/scripts/main.ts --prompt "A landscape" --image out.png --ar 16:9 --quality 2k

# 从文件读取提示词
${BUN_X} {baseDir}/scripts/main.ts --promptfiles system.md content.md --image out.png

# 使用参考图片
${BUN_X} {baseDir}/scripts/main.ts --prompt "Make blue" --image out.png --ref source.png

# 指定提供商
${BUN_X} {baseDir}/scripts/main.ts --prompt "A cat" --image out.png --provider dashscope --model qwen-image-2.0-pro

# OpenAI GPT Image 2
${BUN_X} {baseDir}/scripts/main.ts --prompt "A cat" --image out.png --provider openai --model gpt-image-2

# 批量模式
${BUN_X} {baseDir}/scripts/main.ts --batchfile batch.json --jobs 4
```

## 选项

| 选项 | 描述 |
|--------|-------------|
| `--prompt <text>`, `-p` | 提示词文本 |
| `--promptfiles <files...>` | 从文件读取提示词（拼接） |
| `--image <path>` | 输出图片路径（单图模式必需） |
| `--batchfile <path>` | 多图生成的 JSON 批量文件 |
| `--jobs <count>` | 批量模式工作线程数（默认：auto，最大值来自配置，内置默认 10） |
| `--provider google\|openai\|azure\|openrouter\|dashscope\|zai\|minimax\|jimeng\|seedream\|replicate` | 强制指定提供商（默认：自动检测） |
| `--model <id>`, `-m` | 模型 ID——见各提供商参考文档了解默认值和允许值 |
| `--ar <ratio>` | 宽高比（`16:9`、`1:1`、`4:3`……） |
| `--size <WxH>` | 显式尺寸（如 `1024x1024`；对于 `gpt-image-2`，宽/高必须是 16 的倍数，最大边 3840px，比例不超过 3:1） |
| `--quality normal\|2k` | 质量预设（默认：`2k`） |
| `--imageSize 1K\|2K\|4K` | Google/OpenRouter 的图片尺寸（默认：来自 quality） |
| `--imageApiDialect openai-native\|ratio-metadata` | OpenAI 兼容端点方言——对期望宽高比 `size` 加 `metadata.resolution` 的网关使用 `ratio-metadata` |
| `--ref <files...>` | 参考图片。支持：Google 多模态、OpenAI GPT Image 编辑、Azure OpenAI 编辑（仅 PNG/JPG）、OpenRouter 多模态模型、Replicate 支持的系列、MiniMax 主体参考、Seedream 5.0/4.5/4.0、DashScope `wan2.7-image-pro`/`wan2.7-image`。不支持：即梦、Seedream 3.0、SeedEdit 3.0 或 `wan2.7-image*` 系列之外的任何 DashScope 模型 |
| `--n <count>` | 图片数量。Replicate 需要 `--n 1`（单输出保存语义） |
| `--json` | JSON 输出 |

## 环境变量

| 变量 | 描述 |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API 密钥 |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 密钥 |
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 |
| `GOOGLE_API_KEY` | Google API 密钥 |
| `DASHSCOPE_API_KEY` | DashScope API 密钥 |
| `ZAI_API_KEY`（别名 `BIGMODEL_API_KEY`） | Z.AI API 密钥 |
| `MINIMAX_API_KEY` | MiniMax API 密钥 |
| `REPLICATE_API_TOKEN` | Replicate API 令牌 |
| `JIMENG_ACCESS_KEY_ID`, `JIMENG_SECRET_ACCESS_KEY` | 即梦火山引擎凭证 |
| `ARK_API_KEY` | Seedream（豆包）火山引擎 ARK API 密钥 |
| `<PROVIDER>_IMAGE_MODEL` | 各提供商模型覆盖（`OPENAI_IMAGE_MODEL`、`GOOGLE_IMAGE_MODEL`、`DASHSCOPE_IMAGE_MODEL`、`ZAI_IMAGE_MODEL`/`BIGMODEL_IMAGE_MODEL`、`MINIMAX_IMAGE_MODEL`、`OPENROUTER_IMAGE_MODEL`、`REPLICATE_IMAGE_MODEL`、`JIMENG_IMAGE_MODEL`、`SEEDREAM_IMAGE_MODEL`） |
| `AZURE_OPENAI_DEPLOYMENT`（别名 `AZURE_OPENAI_IMAGE_MODEL`） | Azure 默认部署 |
| `<PROVIDER>_BASE_URL` | 各提供商端点覆盖 |
| `AZURE_API_VERSION` | Azure 图片 API 版本（默认 `2025-04-01-preview`） |
| `JIMENG_REGION` | 即梦区域（默认 `cn-north-1`） |
| `OPENAI_IMAGE_API_DIALECT` | `openai-native` \| `ratio-metadata` |
| `OPENROUTER_HTTP_REFERER`, `OPENROUTER_TITLE` | 可选 OpenRouter 归属信息 |
| `BAOYU_IMAGE_GEN_MAX_WORKERS` | 覆盖批量工作线程上限 |
| `BAOYU_IMAGE_GEN_<PROVIDER>_CONCURRENCY` | 各提供商并发数（如 `BAOYU_IMAGE_GEN_REPLICATE_CONCURRENCY`） |
| `BAOYU_IMAGE_GEN_<PROVIDER>_START_INTERVAL_MS` | 各提供商启动间隔 |

**加载优先级**：CLI 参数 > EXTEND.md > 环境变量 > `<cwd>/.baoyu-skills/.env` > `~/.baoyu-skills/.env`

## 模型解析

优先级（最高 → 最低）适用于所有提供商：

1. CLI 标志 `--model <id>`
2. EXTEND.md `default_model.[provider]`
3. 环境变量 `<PROVIDER>_IMAGE_MODEL`
4. 内置默认值

对于 OpenAI，内置默认值为 `gpt-image-2`。`gpt-image-1.5`、`gpt-image-1` 和 GPT Image 快照仍可通过 `--model` 或 `OPENAI_IMAGE_MODEL` 选择。

对于 Azure，`--model` / `default_model.azure` 是 Azure 部署名称。`AZURE_OPENAI_DEPLOYMENT` 是首选环境变量；`AZURE_OPENAI_IMAGE_MODEL` 作为向后兼容别名保留。如果你的 Azure 部署以底层模型命名，使用 `gpt-image-2`；否则使用确切的自定义部署名称。

EXTEND.md 覆盖环境变量：如果 EXTEND.md 设置了 `default_model.google: "gemini-3-pro-image-preview"` 而环境变量设置了 `GOOGLE_IMAGE_MODEL=gemini-3.1-flash-image-preview`，EXTEND.md 优先。

**每次生成前显示模型信息**：

- `Using [provider] / [model]`
- `Switch model: --model <id> | EXTEND.md default_model.[provider] | env <PROVIDER>_IMAGE_MODEL`

## OpenAI 兼容网关方言

`provider=openai` 表示认证和路由入口点是 OpenAI 兼容的。这**不**保证上游图片 API 使用 OpenAI 原生语义。当网关期望不同的传输格式时，在 EXTEND.md 中设置 `default_image_api_dialect`、`OPENAI_IMAGE_API_DIALECT` 或 `--imageApiDialect`：

- `openai-native`：像素 `size`（`1536x1024`）和原生 OpenAI quality 字段
- `ratio-metadata`：宽高比 `size`（`16:9`）加 `metadata.resolution`（`1K|2K|4K`）和 `metadata.orientation`

对 OpenAI 原生 API 或严格克隆使用 `openai-native`；对 Gemini 或类似模型前面的兼容网关尝试 `ratio-metadata`。当前限制：`ratio-metadata` 仅适用于文生图；参考图片编辑仍需 `openai-native` 或具有一流编辑支持的提供商。

## 提供商特定指南

每个提供商都有自己的特点（模型系列、尺寸规则、参考图支持、限制）。当用户选择该提供商或请求非默认行为时阅读这些指南：

| 提供商 | 参考文档 |
|----------|-----------|
| DashScope（Qwen-Image 系列，自定义尺寸） | `references/providers/dashscope.md` |
| Z.AI（GLM-Image, cogview-4） | `references/providers/zai.md` |
| MiniMax（image-01，主体参考） | `references/providers/minimax.md` |
| OpenRouter（多模态模型，`/chat/completions` 流程） | `references/providers/openrouter.md` |
| Replicate（nano-banana, Seedream, Wan） | `references/providers/replicate.md` |

## 提供商选择

1. 提供了 `--ref` + 未指定 `--provider` → 自动选择 Google → OpenAI → Azure → OpenRouter → Replicate → Seedream → MiniMax（MiniMax 的主体参考更专注于角色/肖像一致性）
2. 指定了 `--provider` → 使用它（如果有 `--ref`，必须是 google/openai/azure/openrouter/replicate/seedream/minimax）
3. 仅存在一个 API 密钥 → 使用该提供商
4. 多个密钥 → 默认优先级：Google → OpenAI → Azure → OpenRouter → DashScope → Z.AI → MiniMax → Replicate → Jimeng → Seedream

## 质量预设

| 预设 | Google imageSize | OpenAI 尺寸 | OpenRouter 尺寸 | Replicate 分辨率 | 使用场景 |
|--------|------------------|-------------|-----------------|----------------------|----------|
| `normal` | 1K | 1024px 目标 | 1K | 1K | 快速预览 |
| `2k`（默认） | 2K | 2048px 目标 | 2K | 2K | 封面、插图、信息图 |

Google/OpenRouter `imageSize` 可通过 `--imageSize 1K|2K|4K` 覆盖。

对于 OpenAI 原生 `gpt-image-2`，`normal` 映射为 `quality=medium` 和接近请求宽高比的低延迟有效尺寸；`2k` 映射为 `quality=high` 和 2048px 级别尺寸如 `2048x2048`、`2048x1152` 或 `1152x2048`。使用显式 `--size` 获得有效的自定义或 4K 输出，如 `3840x2160`。

## 宽高比

支持：`1:1`、`16:9`、`9:16`、`4:3`、`3:4`、`2.35:1`。

- Google 多模态：`imageConfig.aspectRatio`
- OpenAI：`gpt-image-2` 使用请求比例最接近的有效自定义尺寸；旧版 GPT Image 和 DALL·E 模型使用最接近的支持固定尺寸
- OpenRouter：`imageGenerationOptions.aspect_ratio`；如果仅给出 `--size <WxH>`，则推断比例
- Replicate：行为因模型而异——`google/nano-banana*` 使用 `aspect_ratio`，`bytedance/seedream-*` 使用 Replicate 文档记录的比例，Wan 2.7 将 `--ar` 映射为具体 `size`
- MiniMax：官方 `aspect_ratio` 值；如果给出 `--size <WxH>` 但未指定 `--ar`，则为 `image-01` 发送 `width`/`height`

## 生成模式

**默认**：顺序执行。**批量并行**：当 `--batchfile` 包含 2+ 个待处理任务时自动启用。

| 场景 | 推荐 | 原因 |
|-----------|--------|-----|
| 一张图片，或 1-2 张简单图片 | 顺序执行 | 协调开销更低，调试更容易 |
| 多张图片且已保存提示词文件 | 批量（`--batchfile`） | 复用已定稿的提示词，应用共享节流/重试，吞吐量可预测 |
| 每张图片仍需独立推理/提示词编写/风格探索 | 子代理 | 工作仍是探索性的，每张需要独立分析 |
| 输入为 `outline.md` + `prompts/`（如来自 `baoyu-article-illustrator`） | 批量——使用 `scripts/build-batch.ts` 组装负载 | 大纲 + 提示词文件已包含所有所需内容 |

经验法则：一旦提示词文件已保存且任务是"生成所有这些"，优先使用批量而非子代理。仅在生成与逐图思考或发散性创意探索耦合时使用子代理。

**并行行为**：

- 默认工作线程数为自动，受配置上限约束，内置默认 10
- 提供商特定节流仅在批量模式下应用；默认值经过调优以获得吞吐量同时避免 RPM 突发
- 通过 `--jobs <count>` 覆盖
- 每张图片最多重试 3 次
- 最终输出包括成功数、失败数和每张图片的失败原因

## 错误处理

- API 密钥缺失 → 错误并附设置说明
- 生成失败 → 每张图片自动重试最多 3 次
- 无效宽高比 → 警告，使用默认值继续
- 参考图片配合不支持的提供商/模型 → 错误并附修复提示

## 参考文件

| 文件 | 内容 |
|------|---------|
| `references/usage-examples.md` | 各提供商和批量模式的扩展 CLI 示例 |
| `references/providers/dashscope.md` | DashScope 系列、尺寸、限制 |
| `references/providers/zai.md` | Z.AI GLM-image / cogview-4 |
| `references/providers/minimax.md` | MiniMax image-01 + 主体参考 |
| `references/providers/openrouter.md` | OpenRouter 多模态流程 |
| `references/providers/replicate.md` | Replicate 支持的系列 + 护栏 |
| `references/config/preferences-schema.md` | EXTEND.md Schema |
| `references/config/first-time-setup.md` | 首次设置流程 |

## 扩展支持

通过 EXTEND.md 进行自定义配置。路径和 schema 见步骤 0。
