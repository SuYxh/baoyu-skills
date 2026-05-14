# baoyu-image-gen 深度解读 [Deprecated]

> 本文以教学视角解读已废弃的 `baoyu-image-gen` skill，重点分析其历史意义、与继任者 `baoyu-imagine` 的演进对比，以及从中提炼的 Skill 版本管理最佳实践。

---

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-image-gen` v1.56.4 |
| **一句话定位** | ⚠️ **[已废弃]** AI 多 Provider 图像生成 Skill，已被 `baoyu-imagine` (v1.58.0) 取代 |
| **触发关键词** | generate / create / draw images |
| **前置依赖** | `bun` 或 `npx`（二选一） |
| **适用场景** | 文生图、参考图编辑、批量生成、多 Provider 切换 |
| **输入→输出** | Prompt 文本/文件 + 配置参数 → PNG/JPG 图像文件 |

---

## 二、架构与设计模式分析

### 2.1 Workflow 流程对比

两个版本共享相同的核心工作流：

```
Step 0 (BLOCKING): 加载 EXTEND.md 偏好设置
    ↓
Provider 选择 → Model 解析 → 参数组装
    ↓
单图顺序生成 / 批量并行生成（--batchfile）
    ↓
错误重试（最多 3 次）→ 输出图像文件
```

**关键差异**：`baoyu-imagine` 在 Step 0 中新增了 **Legacy compatibility** 逻辑——若旧路径 `.baoyu-skills/baoyu-image-gen/EXTEND.md` 存在而新路径不存在，运行时会自动将其重命名为 `baoyu-imagine`。这是版本迁移的平滑过渡设计。

### 2.2 配置体系（基本一致）

两者共用同一套配置层次结构：

- **优先级**：CLI args > EXTEND.md > env vars > `.baoyu-skills/.env`
- **EXTEND.md 搜索路径**：Project → XDG → User Home
- **Schema**：`references/config/preferences-schema.md`

唯一区别是目录名：`baoyu-image-gen/` → `baoyu-imagine/`。

### 2.3 脚本架构

两者均采用 TypeScript + Bun 运行时的架构，主入口为 `scripts/main.ts`。新版 `baoyu-imagine` 在 providers 目录结构上与旧版完全一致（google/openai/azure/dashscope/zai/minimax/jimeng/seedream/replicate/openrouter），且附带完整的 `.test.ts` 测试文件——这是旧版未在 SKILL.md 中体现的改进。

---

## 三、核心能力拆解

### 3.1 功能差异对比表

| 功能 | baoyu-image-gen (旧) | baoyu-imagine (新) |
|------|---------------------|-------------------|
| **GPT Image 2 支持** | ❌ 不支持 | ✅ 作为 OpenAI 默认模型 |
| **OpenAI 默认模型** | 未明确指定 | `gpt-image-2` |
| **gpt-image-2 尺寸规则** | 无 | 宽高须为 16 的倍数，最大边 3840px，比例不超 3:1 |
| **gpt-image-2 质量映射** | 无 | `normal`→`quality=medium`，`2k`→`quality=high` |
| **DashScope ref 支持** | ❌ 不支持 | ✅ `wan2.7-image-pro` / `wan2.7-image` |
| **Legacy 配置迁移** | 无（是源头） | ✅ 自动重命名旧配置目录 |
| **Azure gpt-image-2 指引** | 无 | ✅ 部署名与模型名的对应说明 |
| **GPT Image 快照选择** | 无 | ✅ `gpt-image-1.5`、`gpt-image-1` 可选 |

### 3.2 支持的 Provider 列表（两者一致）

| Provider | 环境变量 | 特性 |
|----------|---------|------|
| Google | `GOOGLE_API_KEY` | Multimodal ref、imageSize 控制 |
| OpenAI | `OPENAI_API_KEY` | GPT Image 系列 |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | Deployment 模式 |
| OpenRouter | `OPENROUTER_API_KEY` | Chat completions 流式 |
| DashScope | `DASHSCOPE_API_KEY` | Qwen-Image 家族 |
| Z.AI | `ZAI_API_KEY` | GLM-Image / cogview-4 |
| MiniMax | `MINIMAX_API_KEY` | Subject-reference 人像一致性 |
| Replicate | `REPLICATE_API_TOKEN` | Nano-banana / Seedream / Wan |
| Jimeng (即梦) | `JIMENG_ACCESS_KEY_ID` | 火山引擎 |
| Seedream (豆包) | `ARK_API_KEY` | 火山引擎 ARK |

### 3.3 旧版缺少的功能

1. **gpt-image-2 原生支持**：这是新版最核心的新增，包括自定义尺寸、quality 映射、快照模型选择
2. **DashScope 参考图**：`wan2.7-image-pro`/`wan2.7-image` 家族的 `--ref` 支持
3. **配置迁移机制**：用户从旧版升级到新版时，配置无需手动迁移
4. **更完善的 Azure 指导**：如何处理部署名 vs 模型名的对应关系

---

## 四、Prompt Engineering 学习点

### 4.1 废弃 Skill 的 Description 设计

旧版 description 以方括号前缀标注：

```
"[Deprecated: use baoyu-imagine] AI image generation with..."
```

这是一个精妙的设计模式：
- **LLM 可读**：方括号前缀是明确的语义信号，Agent 能立即识别该 Skill 已废弃
- **指向性明确**：直接告诉用户（和 Agent）应该使用什么替代品
- **保留原始描述**：方括号后保留完整功能描述，用于搜索匹配——即使用户按旧名搜索也能命中并被引导到新版

### 4.2 版本迁移的平滑过渡设计

`baoyu-imagine` 中的 Legacy compatibility 段落展示了教科书式的迁移策略：

```
若 .baoyu-skills/baoyu-image-gen/EXTEND.md 存在且新路径不存在
  → 运行时自动重命名为 baoyu-imagine
若两者都存在
  → 保持不变，使用新路径
```

这种设计确保：
1. **零摩擦升级**：用户无需手动操作
2. **无数据丢失**：旧配置不会被覆盖
3. **冲突安全**：若用户已手动创建新配置，不会被旧配置覆盖

### 4.3 如何让旧 Skill 优雅退场

从 baoyu-image-gen 的退场策略中，我们看到三层设计：

1. **Description 层**：`[Deprecated]` 前缀 + 替代品指引
2. **配置层**：新版运行时自动兼容旧版配置路径
3. **环境变量层**：两版共用相同的 `BAOYU_IMAGE_GEN_*` 环境变量前缀（未重命名），最大化向后兼容

注意旧版并未被删除——它仍然存在于 `skills/` 目录中，保证已安装旧版的用户不会突然失去功能。这是"优雅退场"而非"强制下线"。

---

## 五、教学小结

### 从废弃历史中学到什么

1. **功能演进是渐进的**：从 v1.56.4 到 v1.58.0，核心架构未变，变化集中在新模型支持（gpt-image-2）和边缘能力扩展（DashScope ref）。这说明 Skill 拆分/重命名的动机是"API 代际更迭"而非"架构重写"。

2. **命名反映定位变化**：`image-gen`（image generation 的缩写）→ `imagine`（更简洁、更具品牌感）。当一个工具从"实验阶段"进入"产品阶段"，命名往往会简化。

3. **废弃不等于消失**：旧版 Skill 保留在仓库中，其 description 承担"路标"角色——将流量导向新版，而非制造死胡同。

### Skill 版本管理与迁移的最佳实践

| 实践 | 说明 |
|------|------|
| **Description 前缀标注** | `[Deprecated: use X]` 是最小侵入的废弃信号 |
| **配置自动迁移** | 运行时检测旧路径并重命名，用户无感 |
| **环境变量不改名** | 共用环境变量前缀避免用户重新配置 |
| **保留旧版可用** | 不删除旧 Skill，让存量用户有缓冲期 |
| **新版文档标注兼容性** | 在新版 SKILL.md 中明确写出 Legacy compatibility 段 |

这套模式可以推广到任何需要版本迁移的 Skill 项目中——核心原则是 **"让迁移成本归零，让发现成本归零"**。
