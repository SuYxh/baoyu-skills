# baoyu-imagine 深度解读：一个工业级 AI 图像生成 Skill 的设计哲学

> 本文面向想学习编写 Agent Skill 的开发者，以 `baoyu-imagine` v1.58.0 为案例，拆解其架构设计、Prompt Engineering 技巧和多后端适配模式。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-imagine` v1.58.0 |
| **一句话定位** | 统一 10 家 AI 图像生成 API 的 Agent Skill，支持 text-to-image、reference images、批量并行生成 |
| **触发关键词** | generate / create / draw images |
| **前置依赖** | `bun` 或 `npx`（二选一即可） |
| **适用场景** | 单图生成、批量插图、文章配图、漫画分镜、信息图、幻灯片配图 |
| **输入→输出** | Prompt 文本/文件 + 可选参考图 → PNG/JPG 图像文件 |

**被谁依赖？** 这个 skill 是整个 baoyu-skills 生态的**图像生成后端**——至少 6 个 skill 依赖它：`baoyu-article-illustrator`（文章配图）、`baoyu-cover-image`（封面图）、`baoyu-comic`（漫画）、`baoyu-infographic`（信息图）、`baoyu-slide-deck`（幻灯片）、`baoyu-xhs-images`（小红书图片）、`baoyu-image-cards`（图文卡片）。这意味着它的稳定性和兼容性要求极高——一个 breaking change 会波及整个生态。

---

## 二、架构与设计模式分析

### 2.1 Workflow 流程图

```
用户发起图像生成请求
        │
        ▼
┌─────────────────────────┐
│ Step 0: Load Preferences│ ⛔ BLOCKING
│ (查找 EXTEND.md)         │
└─────────────────────────┘
        │
   ┌────┴────┐
   │ 找到？   │
   └────┬────┘
    Yes │      No
        │       ├──→ First-Time Setup (AskUserQuestion)
        │       │    收集 provider + model + quality
        │       │    写入 EXTEND.md → 继续
        ▼       ▼
┌─────────────────────────┐
│ 解析 CLI args + config   │
│ 配置优先级链合并          │
└─────────────────────────┘
        │
   ┌────┴────┐
   │ 模式？   │
   └────┬────┘
  单图  │    批量
   │    │      │
   ▼    │      ▼
┌──────┐│ ┌──────────────┐
│生成  ││ │ 并行 Worker   │
│单图  ││ │ + Provider    │
│      ││ │   Rate Limit  │
│重试  ││ │ + 最多3次重试  │
│≤3次  ││ └──────────────┘
└──────┘│         │
        ▼         ▼
    输出结果 (文件 / JSON)
```

### 2.2 配置优先级链

这是整个 skill 最值得学习的设计之一——一个清晰的 5 层配置覆盖链：

```
CLI args > EXTEND.md > env vars > <cwd>/.baoyu-skills/.env > ~/.baoyu-skills/.env
```

**为什么这样设计？** 每一层对应不同的使用场景：

| 层级 | 场景 | 示例 |
|------|------|------|
| CLI args | 临时覆盖 | `--provider openai --model gpt-image-2` |
| EXTEND.md | 持久化偏好 | 默认用 Google、默认 2K 质量 |
| 环境变量 | CI/CD 或系统级 | `OPENAI_API_KEY=sk-xxx` |
| 项目 .env | 项目级密钥 | 各项目用不同 API Key |
| 用户 .env | 全局兜底 | 个人默认 Key |

以 Model Resolution 为例，同样遵循这条链：CLI `--model` > EXTEND.md `default_model.[provider]` > 环境变量 `<PROVIDER>_IMAGE_MODEL` > 内置默认值。这确保了"越具体的场景，优先级越高"的直觉。

### 2.3 EXTEND.md 配置体系

EXTEND.md 是一个 YAML frontmatter 格式的配置文件，它的设计有三个精妙之处：

**路径查找策略**——三级 fallback 保证灵活性：
1. `.baoyu-skills/baoyu-imagine/EXTEND.md`（项目级）
2. `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-imagine/EXTEND.md`（XDG 标准）
3. `$HOME/.baoyu-skills/baoyu-imagine/EXTEND.md`（用户级）

**首次运行阻塞机制**——如果 EXTEND.md 不存在，skill 不会猜测默认值然后悄悄运行，而是**强制停下来**引导用户完成 first-time setup。这看似"不友好"，实际上避免了更大的问题：用户不知道在用哪个 provider、消耗了哪个 Key 的配额。

**Legacy 兼容**——从旧版 `baoyu-image-gen` 迁移时，runtime 会自动检测旧路径并重命名，做到无缝升级。

### 2.4 脚本架构

```
scripts/
├── main.ts              # 入口：CLI 解析、配置加载、Provider 路由、
│                        #       单图/批量分发、重试逻辑、输出
├── types.ts             # 类型定义：Provider、CliArgs、BatchFile、ExtendConfig
├── build-batch.ts       # 批量文件构建器：从 outline.md + prompts/ 组装 batch.json
│                        # 供 baoyu-article-illustrator 等上游 skill 使用
└── providers/
    ├── google.ts        # Google Gemini multimodal
    ├── openai.ts        # OpenAI GPT Image (含 /images 和 /chat 双通道)
    ├── azure.ts         # Azure OpenAI (Deployment 路由)
    ├── openrouter.ts    # OpenRouter (/chat/completions 流)
    ├── dashscope.ts     # DashScope (qwen-image + wan2.7 双族)
    ├── zai.ts           # Z.AI (同步 API + URL 下载)
    ├── minimax.ts       # MiniMax (subject reference 人物一致性)
    ├── jimeng.ts        # 即梦 (Volcengine 签名认证)
    ├── seedream.ts      # 豆包 Seedream (ARK API)
    ├── replicate.ts     # Replicate (多模型族 + 本地 guardrail)
    └── *.test.ts        # 每个 Provider 配对单元测试
```

每个 Provider 模块导出统一接口：

```typescript
type ProviderModule = {
  getDefaultModel: () => string;
  generateImage: (prompt: string, model: string, args: CliArgs) => Promise<Uint8Array>;
  validateArgs?: (model: string, args: CliArgs) => void;
  getDefaultOutputExtension?: (model: string, args: CliArgs) => string;
};
```

这是一个经典的 **Strategy Pattern**——`main.ts` 负责编排，具体的 API 调用细节封装在各 Provider 内部。新增 Provider 只需实现这个接口即可，不影响核心逻辑。

### 2.5 与其他 Skill 的协作

`baoyu-imagine` 扮演"图像基础设施"角色。上游 skill 的典型协作模式：

1. **直接调用**：上游 skill 组装好 prompt 后调用 `main.ts` 的 CLI 接口
2. **batch 集成**：`baoyu-article-illustrator` 生成 `outline.md` + `prompts/` 目录，然后通过 `build-batch.ts` 组装成 `batch.json`，再调用批量模式一次性生成所有配图

---

## 三、核心能力拆解

### 3.1 十大 Provider 全景对比

| Provider | 默认模型 | Ref 图 | 自定义 Size | 特色 |
|----------|---------|--------|------------|------|
| **Google** | gemini-3-pro-image-preview | ✅ | AR 模式 | 最灵活，推荐默认 |
| **OpenAI** | gpt-image-2 | ✅ (edits) | 16 倍数, ≤3840px | 4K 输出, quality 分级 |
| **Azure** | gpt-image-2 (deployment) | ✅ (edits) | 同 OpenAI | 企业合规路由 |
| **OpenRouter** | gemini-3.1-flash-image-preview | ✅ (multimodal) | imageSize 1K/2K/4K | 聚合多模型 |
| **DashScope** | qwen-image-2.0-pro | ⚠️ wan2.7 only | 自由尺寸 | 中文文字渲染强 |
| **Z.AI** | glm-image | ❌ | 32 倍数, ≤2048px | 海报/文字布局 |
| **MiniMax** | image-01 | ✅ (character) | 8 倍数, 512-2048px | 人物一致性 |
| **Replicate** | google/nano-banana-2 | ⚠️ 模型相关 | 模型相关 | 多族 guardrail |
| **Jimeng** | jimeng_t2i_v40 | ❌ | - | 火山引擎签名 |
| **Seedream** | doubao-seedream-5-0 | ✅ 4.0/4.5/5.0 | - | 豆包 ARK API |

### 3.2 Provider 自动选择策略

自动选择逻辑是一段精心设计的优先级决策树：

1. **有 `--ref`（参考图）且未指定 provider** → 按 Google → OpenAI → Azure → OpenRouter → Replicate → Seedream → MiniMax 顺序选第一个有 Key 的
2. **手动指定 `--provider`** → 直接使用（如果带 `--ref` 但 provider 不支持则报错）
3. **只有一个 API Key** → 自动用那个 provider
4. **多个 Key** → 默认优先级：Google → OpenAI → Azure → OpenRouter → DashScope → Z.AI → MiniMax → Replicate → Jimeng → Seedream

注意 ref 场景下 MiniMax 被排到最后——因为它的 subject reference 更偏向"人物/肖像一致性"，不是通用的图像编辑。这种细粒度的排序反映了作者对各 API 能力边界的深入理解。

### 3.3 Quality Presets 与 Aspect Ratio 矩阵

Quality 只有两档：`normal`（1K 级）和 `2k`（默认），但映射到各 Provider 时各不相同：

- **OpenAI**：`normal` → `quality=medium` + 低分辨率尺寸；`2k` → `quality=high` + 2048px 级尺寸
- **Google/OpenRouter**：直接对应 `imageSize` 的 1K/2K
- **DashScope**：`quality` 不是 API 原生参数，而是 baoyu-imagine 的**兼容层抽象**

Aspect Ratio 支持 `1:1`、`16:9`、`9:16`、`4:3`、`3:4`、`2.35:1`，但不同 Provider 的实现方式完全不同——有的用原生 AR 参数，有的要换算成像素尺寸，有的只支持固定档位。这些差异全被封装在各 Provider 模块内部。

### 3.4 顺序 vs 批量生成

SKILL.md 给出了一个非常实用的决策表：

| 场景 | 推荐模式 | 原因 |
|------|---------|------|
| 1-2 张简单图片 | 顺序 | 协调开销低，易调试 |
| 已有多组 prompt 文件 | Batch (`--batchfile`) | 复用 prompt，共享限流/重试 |
| 每张图需要独立推理 | Subagents | 探索性工作需要独立上下文 |
| 来自上游 skill 的 outline + prompts | Batch + `build-batch.ts` | 数据已就绪，直接组装 |

核心判断原则：**一旦 prompt 已定稿、任务是"把这些都生成出来"，就用 batch；只有当生成和思考耦合时才用 subagents。**

批量模式内部有精细的限流机制——每个 Provider 有独立的 `concurrency`（并发数）和 `start_interval_ms`（启动间隔），例如 Replicate 5 并发/700ms 间隔，而其他 Provider 多为 3 并发/1100ms 间隔。这是为了在吞吐量和 API RPM 限制之间找到平衡。

### 3.5 OpenAI-Compatible Gateway Dialects

这是一个很有前瞻性的设计。当 `provider=openai` 时，实际的后端未必是 OpenAI——可能是一个兼容网关，但图像 API 的 wire format 可能不同。skill 通过 `dialect` 参数解决这个问题：

- `openai-native`：标准 OpenAI 格式，像素级 `size`（如 `1536x1024`）
- `ratio-metadata`：网关格式，发送 AR `size`（如 `16:9`）+ `metadata.resolution`（如 `2K`）

这种设计让一个 Provider 实现可以适配多种后端，避免了为每个网关写独立 Provider 的冗余。

### 3.6 错误处理与重试

四层错误处理，从具体到通用：
1. **Missing API Key** → 报错 + 给出配置指引
2. **生成失败** → 自动重试最多 3 次（`MAX_ATTEMPTS = 3`）
3. **不支持的 AR** → 警告但继续用默认值
4. **不支持的 Ref + Provider** → 直接报错 + 给出修复提示

批量模式下，单个任务失败不会终止整个 batch，最终汇总报告成功/失败数和各任务的失败原因。

---

## 四、Prompt Engineering 学习点

### 4.1 "⛔ BLOCKING" 阻塞标记

SKILL.md 中有一个非常醒目的设计：

> **Step 0: Load Preferences ⛔ BLOCKING**
>
> This step MUST complete before any image generation — generation is blocked until EXTEND.md exists.

`⛔ BLOCKING` 不是普通的注释——它是对 LLM 的**行为约束指令**。在 Agent Skill 的上下文中，LLM 倾向于"尽快完成任务"，可能跳过配置步骤直接生成图片。这个标记用视觉上的醒目符号（⛔）+ 大写关键词（BLOCKING）双重强调，告诉 LLM："这里是一道无法绕过的门，必须先过这关。"

这种设计本质上是在**用 Prompt 模拟同步编程中的阻塞语义**——LLM 不能"await"，但可以被明确告知"不可跳过"。

### 4.2 Step 0 阻塞设计的精妙之处

首次运行的阻塞不仅仅是"让用户配置"这么简单。它解决了三个问题：

1. **避免静默消费**——不会在用户不知情时消耗某个 Provider 的配额
2. **建立心理模型**——通过首次交互，用户理解了"Provider → Model → Quality"的概念层次
3. **持久化偏好**——一次配置，后续所有生成都受益，避免每次重复询问

同时，当 EXTEND.md 存在但 `default_model.[provider]` 为 null 时，只问模型选择，不重复问其他问题——这是"最小打扰"原则的体现。

### 4.3 "Display model info before each generation" 的透明度设计

> - `Using [provider] / [model]`
> - `Switch model: --model <id> | EXTEND.md default_model.[provider] | env <PROVIDER>_IMAGE_MODEL`

每次生成前显示当前使用的 provider 和 model，并告诉用户如何切换。这是一种**透明度设计**——用户始终知道"谁在帮我干活"以及"如何换人"。在多后端系统中，这种可见性极其重要，否则用户会困惑"为什么这次的风格和上次不一样"。

### 4.4 值得借鉴的写法

**片段 1：User Input Tools 的运行时适配**

> 1. **Prefer built-in user-input tools** exposed by the current agent runtime — e.g., `AskUserQuestion`, `request_user_input`, `clarify`, `ask_user`, or any equivalent.
> 2. **Fallback**: if no such tool exists, emit a numbered plain-text message and ask the user to reply with the chosen number/answer for each question.

**点评**：这段解决了一个关键问题——SKILL.md 可能被不同的 Agent 运行时加载（Claude、Cursor、Windsurf 等），每个运行时的用户交互工具名称不同。作者没有硬编码工具名，而是给出优先级策略 + fallback，让 skill 在任何运行时都能正常工作。这是写**跨平台 Skill** 的范例。

**片段 2：Provider Selection 的条件决策树**

> 1. `--ref` provided + no `--provider` → auto-select Google → OpenAI → Azure → OpenRouter → Replicate → Seedream → MiniMax
> 2. `--provider` specified → use it
> 3. Only one API key present → use that provider
> 4. Multiple keys → default priority: Google → OpenAI → Azure → ...

**点评**：四条规则覆盖了所有场景，且优先级从"功能约束最强"到"最宽松"排列。规则 1 最具体（有 ref 图的场景），规则 4 最通用（纯文本生成）。这种"从约束到默认"的决策结构，在任何多后端路由场景都可以复用。

**片段 3：Generation Mode 的决策表**

> Rule of thumb: once prompt files are saved and the task is "generate all of these", prefer batch over subagents. Use subagents only when generation is coupled with per-image thinking or divergent creative exploration.

**点评**：一句话就把 batch 和 subagents 的边界划清楚了。这不是技术文档的表达方式，更像一个有经验的工程师在传授决策心法。好的 SKILL.md 不仅要描述"怎么做"，更要教 Agent"什么时候该做什么"。

---

## 五、教学小结

### 这个 Skill 教会我们什么

1. **配置优先级链是多后端 Skill 的骨架**——5 层 fallback（CLI > EXTEND.md > env > 项目 .env > 用户 .env）的设计，让同一套代码在 CI/CD、本地开发、多项目环境中都能合理工作。这是"Convention over Configuration"的升级版——有 convention，但每一层都可以 override。

2. **首次运行体验值得独立设计**——Step 0 的 BLOCKING + first-time-setup 流程，把"新用户怎么办"作为第一优先级来解决。很多 skill 会直接 fallback 到默认值然后出奇怪的错误——这个 skill 选择**停下来好好聊**。

3. **Strategy Pattern 天然适合多 Provider 架构**——统一 `ProviderModule` 接口 + 各 Provider 独立实现 + main.ts 做路由编排，新增 Provider 的成本是 O(1)。每个 Provider 配单元测试，保证隔离性。

4. **SKILL.md 是写给 LLM 的"操作手册"，不是写给人的 README**——`⛔ BLOCKING` 标记、明确的决策表、优先级数字列表，这些都是在约束 LLM 的行为路径。好的 SKILL.md 读起来像一份"SOP（标准操作流程）"。

5. **透明度是信任的基础**——每次生成前显示 provider/model 信息，给出切换方式。在涉及付费 API 的场景下，这种透明度不是锦上添花，而是必需品。

### 如果要写类似 Skill 需注意的关键点

- **配置持久化不可省**：如果你的 skill 需要 API Key 或有偏好设置，一定要设计 EXTEND.md 级别的持久化方案，不要每次都问用户
- **Provider 接口要统一**：不管后端 API 差异多大，对外暴露的接口必须一致（`getDefaultModel` + `generateImage`），差异封装在内部
- **批量模式要内置限流**：不能简单地 `Promise.all` 并发所有请求，要考虑各 Provider 的 RPM/并发限制
- **错误要分级处理**：配置错误（缺 Key）→ 阻塞；运行时错误（API 失败）→ 重试；兼容性警告（不支持的 AR）→ 降级
- **Legacy 兼容不能忽略**：用户可能还在用旧版配置，要设计平滑的迁移路径

### 与 baoyu-image-gen（已废弃版本）的差异

`baoyu-image-gen`（v1.56.4）已被标记为 `[Deprecated: use baoyu-imagine]`。主要差异：

| 维度 | baoyu-image-gen (旧) | baoyu-imagine (新) |
|------|---------------------|-------------------|
| **名称** | 功能描述型（image-gen） | 品牌化（imagine） |
| **OpenAI 模型** | 无 GPT Image 2 强调 | 默认 gpt-image-2，支持 1/1.5/2 全系列 |
| **Dialect 机制** | 无 | 新增 `openai-native` / `ratio-metadata` 适配网关 |
| **build-batch.ts** | 无 | 新增，支持从 outline+prompts 自动组装批量任务 |
| **Provider 文档** | references 较薄 | 5 个 Provider 独立详细文档 |
| **Legacy 兼容** | 无需 | 自动检测旧 EXTEND.md 路径并迁移 |

本质上，`baoyu-imagine` 是 `baoyu-image-gen` 的演进重命名——从"能用"升级到"好用"。代码结构基本一致（同样的 Provider Pattern），但在配置灵活性、模型覆盖度、与上游 skill 的集成深度上都有显著提升。

---

> **延伸阅读**：想看实际的 Provider 实现细节，可以直接阅读 `scripts/providers/*.ts`。每个 Provider 模块 + 对应的 `.test.ts` 是学习"如何封装第三方 API 差异"的极佳素材。
