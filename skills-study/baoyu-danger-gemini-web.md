# baoyu-danger-gemini-web 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-danger-gemini-web` v1.56.1 |
| **一句话定位** | 通过逆向工程 Gemini Web API 实现文本/图像生成的 Agent Skill，名称中 "danger" 前缀标识其非官方 API 的风险属性 |
| **触发关键词** | "generate image with Gemini"、"Gemini text generation"、需要 vision-capable AI generation |
| **前置依赖** | `bun` 或 `npx`（二选一）；本地 Chrome/Chromium/Edge 浏览器（用于认证） |
| **适用场景** | 其他 skill 需要图像生成后端时、用户要求 Gemini 原生能力（含图生图、多轮对话）时 |
| **输入→输出** | 文本 prompt（+ 可选参考图）→ 生成文本 / 生成图像文件 / JSON 结构化输出 |

> **关于 "danger" 前缀**：这是一个命名约定，明确告知使用者该 skill 依赖逆向工程的非公开 API，存在随时失效、违反 ToS 等风险。这种"自我标记"设计在开源生态中值得推广。

---

## 二、架构与设计模式分析

### 2.1 Workflow 流程图

```
用户触发 Skill
      │
      ▼
┌─────────────────┐
│ Consent Check   │ ← 检查 consent.json（disclaimerVersion: "1.0"）
│ (强制前置门控)   │
└────────┬────────┘
         │ accepted: true
         ▼
┌─────────────────┐
│ Load Preferences│ ← 按优先级查找 EXTEND.md（Project > XDG > Home）
│ (可选配置)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Authentication  │ ← Cookie 缓存 → Chrome CDP 复用 → 启动浏览器登录
│ (分层认证策略)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generation      │ ← GeminiClient.generate_content() / ChatSession.send_message()
│ (核心生成)      │
└────────┬────────┘
         │
         ▼
   输出文本/图像/JSON
```

### 2.2 Consent 机制详细拆解

这是该 skill 最独特的设计模式——**在 Agent 执行链中嵌入法律责任免除环节**：

- **存储路径**（跨平台）：
  - macOS: `~/Library/Application Support/baoyu-skills/gemini-web/consent.json`
  - Linux: `~/.local/share/baoyu-skills/gemini-web/consent.json`
  - Windows: `%APPDATA%\baoyu-skills\gemini-web\consent.json`

- **版本控制字段** `disclaimerVersion: "1.0"`：当免责条款更新时，只需递增版本号即可强制所有用户重新确认。这避免了"一次同意、永久生效"的法律盲区。

- **文件格式**：
  ```json
  {
    "version": 1,
    "accepted": true,
    "acceptedAt": "2025-01-15T10:30:00.000Z",
    "disclaimerVersion": "1.0"
  }
  ```

### 2.3 脚本架构

```
scripts/
├── main.ts                      # CLI 入口：参数解析、会话管理、输出格式化
├── package.json                 # 依赖：baoyu-chrome-cdp
├── bun.lock
└── gemini-webapi/               # 核心子模块：Gemini Web API 的 TypeScript 移植
    ├── index.ts                 # 统一导出
    ├── client.ts                # GeminiClient + ChatSession 核心类
    ├── constants.ts             # Endpoint、Headers、Model 定义、ErrorCode
    ├── exceptions.ts            # 异常层次结构（AuthError → APIError → GeminiError）
    ├── components/
    │   └── gem-mixin.ts         # Gem（自定义角色）CRUD 的 mixin 模式
    ├── types/
    │   ├── index.ts, gem.ts, image.ts, candidate.ts, modeloutput.ts, grpc.ts
    └── utils/
        ├── load-browser-cookies.ts  # Chrome CDP 认证核心
        ├── get-access-token.ts      # 多候选策略的 token 获取
        ├── rotate-1psidts.ts        # Cookie 自动刷新
        ├── cookie-file.ts           # Cookie 持久化读写
        ├── paths.ts                 # 跨平台路径解析
        ├── http.ts, parsing.ts, upload-file.ts, logger.ts, decorators.ts
        └── index.ts
```

### 2.4 认证流程：分层降级策略

认证设计是该 skill 的技术亮点，采用**多候选并行竞争 + 逐步降级**：

1. **Cookie 文件缓存**（最快路径）→ 读取 `cookies.json`，尝试 `SNlM0e` token 提取
2. **复用已运行的 Chrome 实例**（零干扰路径）→ 通过 `discoverRunningChromeDebugPort()` 发现本地 Chrome 调试端口，CDP 连接获取 Cookie
3. **启动独立 Chrome Profile**（完整认证路径）→ 打开浏览器窗口，等待用户完成 Google 登录
4. **后台自动刷新**（保活机制）→ `rotate_1psidts()` 每 540 秒调用 `RotateCookies` endpoint 刷新 `__Secure-1PSIDTS`

关键代码中使用 `Promise.any()` 并行尝试多组 Cookie 候选，取最先成功的结果——这是处理"Cookie 可能过期"场景的优雅模式。

---

## 三、核心能力拆解

### 3.1 支持的模型

| 模型标识 | Model Header | 说明 |
|---------|-------------|------|
| `gemini-3-pro` | 自定义 `x-goog-ext-525001261-jspb` header | 默认模型，最新 3.0 Pro |
| `gemini-3-flash` | 自定义 header（不同 hash） | 轻量快速版 |
| `gemini-3-flash-thinking` | 自定义 header | Flash + 思维链 |
| `gemini-3.1-pro-preview` | 空 header（auto-routed） | 3.1 预览版 |

模型区分通过 HTTP header `x-goog-ext-525001261-jspb` 中的 hash 值实现——这是逆向工程发现的 Gemini Web 内部路由机制。

### 3.2 文本生成 vs 图像生成 vs 视觉输入

- **纯文本生成**：`--prompt "Hello"` → 输出文本
- **图像生成**：`--prompt "A cute cat" --image cat.png` → 从响应中提取 `lh3.googleusercontent.com/gg-dl/` URL 并下载
- **视觉输入（reference images）**：`--reference image.png` → 先通过 `upload_file()` 上传到 Google content-push API，再附带到 prompt 中
- **组合使用**：参考图 + 图像生成 = 图生图能力

### 3.3 多轮会话机制

会话通过 `metadata: [conversationId, responseId, choiceId]` 三元组维护状态：

```typescript
// 会话创建：metadata 初始为 [null, null, null]
chat = c.start_chat({ metadata: sess.metadata, model });
// 每轮结束后，从响应中提取新的 metadata 写回 session 文件
sess.metadata = chat.metadata.slice(0, 3);
```

Session 文件以 JSON 存储在 `<dataDir>/sessions/<id>.json`，包含完整的消息历史，支持跨进程恢复对话。代码中还处理了 `LegacySessionV1` 的向前兼容。

### 3.4 Cookie 管理与 Chrome Profile 复用

- Cookie 持久化为 `{ version, updatedAt, cookieMap, source }` 格式
- `source` 字段记录来源（`"cdp"`/`"cdp-existing"`/`"client"`/`"refresh"`/`"init"`）便于调试
- Chrome Profile 复用逻辑：无显式 `--profile-dir` 时，优先通过 `discoverRunningChromeDebugPort()` 复用已有浏览器会话；有显式 profile 时，走独立 Chrome 启动路径

---

## 四、Prompt Engineering 学习点

### 4.1 "danger" 前缀的命名约定

这是一种**语义化风险标识设计**：

- 在 skill 名称中直接内嵌风险等级，让 Agent 和用户在**调用前**就能感知风险
- 类比：npm 中的 `@deprecated` 标记、Git 中的 `BREAKING CHANGE` 前缀
- 建议推广为约定：`danger-*`（逆向工程/非官方）、`experimental-*`（实验性）、`internal-*`（内部使用）

### 4.2 Consent 机制作为 "责任免除" 模式

这是 Agent Skill 设计中极具参考价值的模式：

```
SKILL.md 中的 Consent Flow 设计（摘录点评）：

1. Check if consent file exists with `accepted: true` and `disclaimerVersion: "1.0"`
   → 点评：双重校验——不仅要 accepted，还要版本匹配

2. If valid consent exists → print warning with `acceptedAt` date, proceed
   → 点评：即使已同意，仍每次打印警告。"持续提醒"比"一次性告知"更负责

3. If no consent → show disclaimer, ask user via AskUserQuestion
   → 点评：利用 Agent Runtime 的交互能力，而非静默跳过

4. Consent file format includes ISO timestamp
   → 点评：带时间戳的同意记录，具有可审计性
```

**设计启发**：任何涉及 ToS 风险、数据隐私、或不可逆操作的 skill，都应考虑引入类似的 consent gate。

### 4.3 与官方 API skill (baoyu-imagine) 的定位差异

| 维度 | baoyu-imagine（官方） | baoyu-danger-gemini-web（逆向） |
|------|---------------------|-------------------------------|
| API 来源 | OpenAI/Google/Azure 等官方 SDK | Gemini Web 前端逆向 |
| 认证方式 | API Key | Browser Cookie + CDP |
| 稳定性 | 高（SLA 保障） | 低（随时可能因前端变更而失效） |
| 成本 | 按 token/图片计费 | 免费（利用 Google 账号配额） |
| Consent | 无需 | 强制要求 |
| 模型丰富度 | 多供应商多模型 | 仅 Gemini 系列 |
| 适用场景 | 生产环境 | 实验/个人项目 |

### 4.4 disclaimerVersion 的版本控制思路

`disclaimerVersion: "1.0"` 的设计精妙之处：

- 当 Google 更新 ToS、或 skill 作者需要修改免责声明时，只需将版本号改为 `"1.1"`
- 此时所有现有 `consent.json` 自动失效（版本不匹配），用户被迫重新阅读并确认
- 这比"删除 consent 文件要求重新同意"更优雅——保留了历史同意记录

### 4.5 值得借鉴的片段

**认证的多候选竞争模式**（get-access-token.ts）：

```typescript
// 收集所有可能的 Cookie 候选（文件缓存、CDP、环境变量...）
const unique: Record<string, string>[] = [];
// 去重后并行尝试
const attempts = unique.map(async (c, i) => {
  return await send_request(c, verbose);
});
return (await Promise.any(attempts));
```

**点评**：这种"宽进严出"策略非常适合认证场景——Cookie 可能来自多个来源且有效性不确定，与其串行逐个尝试，不如并行竞争取最快成功者。`Promise.any` 的错误聚合也意味着只有**全部失败**时才真正报错。

---

## 五、教学小结

### 关键 Takeaway

1. **"danger" 命名约定是优秀的风险通信设计**——在名称层面就传达了"这不是生产级工具"的信号，比文档中的警告更直接有效。

2. **Consent Gate 是逆向工程类 skill 的必备模式**——它不仅是法律保护，更是对用户的尊重：让用户在充分知情后做出选择，而非替用户承担风险。

3. **分层降级的认证策略具有通用价值**——"缓存 → 复用已有会话 → 交互式登录"的三级降级，在任何需要 Browser Session 的自动化场景中都适用。

4. **逆向工程 API 的脆弱性需要防御性编码**——观察 `client.ts` 中大量的 `get_nested_value` 安全访问、fallback URL 扫描、以及详细的 ErrorCode 映射，这些都是与"不稳定数据结构"共处的实战经验。

5. **版本化的 Consent + 会话持久化 = 可审计的 Agent 行为**——每次操作都有 timestamp、每次同意都有版本记录，这种设计让 Agent 的行为链条可追溯。

### 逆向工程类 Skill 的设计伦理与安全实践

- **明确标识**：通过 "danger" 前缀、Consent 门控、每次调用的 warning 输出，三重标识风险
- **最小权限**：只请求必要的 Cookie（`__Secure-1PSID`、`__Secure-1PSIDTS`），不收集用户的其他浏览数据
- **不缓存敏感数据到日志**：Cookie 值不出现在 console 输出中，只记录 metadata
- **提供退出路径**：用户可以随时 decline consent，skill 立即停止

### "danger" 命名约定的推广价值

建议在 Agent Skill 生态中建立分级命名标准：

- `baoyu-<name>`：稳定的官方 API 封装
- `baoyu-danger-<name>`：逆向工程/非官方 API，可能违反 ToS
- `baoyu-experimental-<name>`：实验性功能，接口不稳定

这种约定让 Agent 在自动选择 skill 时能做出**风险感知的决策**——优先使用官方版本，仅在明确需要时才 fallback 到 danger 版本。
