# baoyu-danger-x-to-markdown 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-danger-x-to-markdown` v1.56.1 |
| **一句话定位** | X/Twitter 内容全保真抓取——将推文、推文串、长文 Article 转化为带 YAML front matter 的 Markdown，支持媒体本地化 |
| **触发关键词** | "X to markdown"、"tweet to markdown"、"save tweet"、提供 x.com/twitter.com URL；注意 "danger" 前缀表示使用逆向工程 API |
| **前置依赖** | `bun` 或 `npx`（二选一）；本地 Chrome/Chromium/Edge（Cookie 获取 fallback） |
| **适用场景** | 推文内容归档、知识库收录、Thread 长文阅读、Article 离线保存、推文引用素材准备 |
| **输入→输出** | X/Twitter URL → `x-to-markdown/{username}/{tweet-id}/{content-slug}.md` + 可选 `imgs/` `videos/` 本地媒体 |

> **"danger" 前缀**：与 `baoyu-danger-gemini-web` 共享的命名约定，显式标注 skill 依赖逆向工程的非公开 API，随时可能失效或触发账号限制。这是一种对使用者负责的"自我风险标记"设计。

---

## 二、架构与设计模式分析

### 2.1 六步 Workflow 流程图

```
用户提供 X URL
      │
      ▼
┌──────────────────┐
│ 1. Consent       │ ← 检查/获取用户同意（consent.json, disclaimerVersion "1.0"）
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. Config        │ ← 查找 EXTEND.md（Project > XDG > Home），首次触发 Setup 问卷
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. URL Parse     │ ← 识别 tweet/article，提取 ID + username
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. Auth + Fetch  │ ← Cookie 三级加载 → GraphQL API 调用
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 5. Convert       │ ← Thread/Article/单推文 → Markdown 格式化
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 6. Save + Media  │ ← 写入文件 + 可选媒体本地化
└──────────────────┘
```

### 2.2 Consent 机制

与 `baoyu-danger-gemini-web` 完全一致的设计模式——**Agent 执行链中的法律免责前置门控**：

- 存储路径：`~/Library/Application Support/baoyu-skills/x-to-markdown/consent.json`
- 验证字段：`accepted: true` + `disclaimerVersion: "1.0"`
- 失败处理：非 TTY 环境抛出明确错误，提示手动创建 consent 文件

这种可复制到任何逆向工程类 skill 的模式，核心代码仅 50 行（`ensureConsent` 函数）。

### 2.3 认证系统：三级 Cookie 加载策略

```
loadXCookies()
  ├─ Level 1: Environment Variables（X_AUTH_TOKEN + X_CT0）→ 最高优先级
  ├─ Level 2: Cookie File 缓存（~/...baoyu-skills/x-to-markdown/cookies.json）
  └─ Level 3: Chrome CDP 实时提取（启动/复用 Chrome，5 分钟超时等待登录）
```

关键设计点：
- **合并策略**：`{ ...fileMap, ...cdpMap, ...inlineMap }`——环境变量永远覆盖文件缓存
- **自动缓存**：CDP 获取成功后自动写入 cookie file，下次跳过浏览器启动
- **Chrome 复用**：通过 `findExistingChromeDebugPort` 检测已运行的 Chrome 实例

### 2.4 三种 Session 模式（策略模式）

| 文件 | 职责 | 调用时机 |
|------|------|---------|
| `tweet-to-markdown.ts` | 主入口：单推文/Thread + 内嵌 Article 检测 | 所有 tweet URL |
| `thread-markdown.ts` | Thread 格式化：推文串 → 编号列表 + 引用推文 | 多条推文的渲染 |
| `tweet-article.ts` | Article 实体提取 + 按需 API 补充获取 | 检测到推文内嵌 Article 时 |

`tweet-to-markdown.ts` 作为编排器：先调用 `fetchTweetThread` 获取完整线程，然后检测首条推文是否包含 Article 实体，动态选择渲染路径。

### 2.5 脚本架构（17 个文件的精细分工）

```
scripts/
├── main.ts              → CLI 入口 + Consent + 参数解析 + 输出路径解析
├── tweet-to-markdown.ts → 推文→Markdown 编排器（也可独立运行）
├── thread.ts            → Thread 抓取：分页遍历 + 去重 + 排序
├── thread-markdown.ts   → Thread 渲染：编号标题 + 引用推文 + 媒体
├── tweet-article.ts     → Article 实体检测与获取
├── markdown.ts          → Article 内容渲染引擎（700+ 行，最复杂）
├── media-localizer.ts   → 媒体下载 + URL 重写 + 高清图自动升级
├── graphql.ts           → GraphQL 端点动态解析 + API 调用
├── http.ts              → HTTP 基础设施 + 请求头构造 + Feature Flag 解析
├── cookies.ts           → 三级 Cookie 加载 + Chrome CDP 集成
├── cookie-file.ts       → Cookie 文件读写（兼容两种格式）
├── constants.ts         → Bearer Token + Query ID + Feature Switches 配置
├── paths.ts             → 跨平台路径解析（macOS/Linux/Windows/WSL）
├── referenced-tweets.ts → 引用推文批量获取
├── types.ts             → TypeScript 类型定义
├── markdown.test.ts     → 单元测试
└── package.json         → 依赖声明（仅 baoyu-chrome-cdp）
```

这是所有 baoyu-skills 中**模块化程度最高**的一个——每个文件聚焦单一职责，通过明确的 import/export 边界解耦。

---

## 三、核心能力拆解

### 3.1 四种内容类型处理

1. **单推文**：直接获取 Thread（即使只有一条），渲染为带 front matter 的 Markdown
2. **推文串 (Thread)**：通过 `TweetDetail` API 分页遍历，`moreCursor` + `bottomCursor` + `topCursor` 三方向翻页，确保完整性
3. **Article（长文）**：从推文中检测 `article_results`，解析 Draft.js `content_state`（blocks + entityMap）
4. **引用推文 (Quote Tweet)**：递归解析 `quoted_status_result`，渲染为 blockquote 格式

### 3.2 GraphQL API 端点动态管理

这是最精巧的逆向工程设计之一：

```typescript
// 1. 抓取 x.com 首页 HTML
const html = await fetchHomeHtml(userAgent);
// 2. 从 HTML 中提取 JS bundle hash
const apiHash = html.match(/api:"([a-zA-Z0-9_-]+)"/);
// 3. 下载并解析对应 JS chunk
const chunk = await fetchText(`https://abs.twimg.com/.../api.${apiHash}a.js`);
// 4. 从 chunk 中提取最新 queryId 和 featureSwitches
const queryIdMatch = chunk.match(/queryId:"([^"]+)",operationName:"TweetDetail"/);
```

即使 X 更新了 API 版本，只要 bundle 结构不变，skill 就能**自动适应**新的 queryId。同时保留 `FALLBACK_*` 常量作为兜底。

### 3.3 Media Localization（媒体本地化）

`media-localizer.ts` 的关键策略：

- **高清图自动升级**：`pbs.twimg.com` 图片自动请求 `?format=jpg&name=4096x4096`（最高分辨率）
- **视频最优选择**：按 `bit_rate` 降序排序，选择最高码率的 mp4 variant
- **智能类型推断**：hostname → extension → Content-Type → hint 四级判断链
- **URL 重写**：下载完成后，Markdown 中的远程 URL 被替换为 `imgs/img-001-xxx.jpg` 相对路径
- **幂等性**：已有本地化文件时检测 frontmatter 匹配，避免重复下载

### 3.4 Thread 抓取完整性保证

`thread.ts` 的分页策略极为完善：

1. 首次请求获取 focal tweet 的上下文
2. 向上翻页（`topCursor`）获取更早的同线程推文
3. 向下展开（`moreCursor`）获取被折叠的后续推文
4. 以最后一条推文为 focal 再次请求，确保尾部完整
5. 去重 + 按时间排序 + 从 root 截断

设置了 `maxRequestCount = 1000` 的安全阈值防止无限循环。

### 3.5 Cookie 缓存与 Chrome CDP 集成

依赖 `baoyu-chrome-cdp` 包提供的能力：

- 检测已有 Chrome Debug Port → 复用已登录 session
- 无可用实例时启动独立 Chrome profile（隔离数据）
- 每秒轮询 `Network.getCookies` 直到获得 `auth_token` + `ct0`
- 成功后关闭 tab（复用模式）或终止进程（新启动模式）

---

## 四、Prompt Engineering 学习点

### 4.1 "danger" 前缀的约定复用

两个 danger skill 共享同一设计语言：
- 同样的 Consent 流程结构
- 同样的 `disclaimerVersion` 版本控制
- 同样的 "decline → exit" 语义

**教学意义**：创建逆向工程类 skill 时，可以直接复制这套 Consent 模板。

### 4.2 精细模块化的脚本设计

17 个文件，唯一外部依赖仅 `baoyu-chrome-cdp`。对比大多数 skill 用单一脚本完成所有工作，这里展示了如何将复杂逻辑拆解为可测试、可复用的模块：

- `http.ts` 完全不知道 cookie 来源——它只接收 `cookieMap` 参数
- `markdown.ts` 不知道数据如何获取——它只接收 Article 对象
- `thread.ts` 不知道输出格式——它只返回结构化的 `ThreadResult`

### 4.3 值得借鉴的写法摘录

**写法一：动态 GraphQL 端点解析**（`graphql.ts` 第 68-106 行）

```typescript
async function resolveArticleQueryInfo(userAgent: string): Promise<ArticleQueryInfo> {
  const html = await fetchHomeHtml(userAgent);
  const bundleMatch = html.match(/"bundle\\.TwitterArticles":"([a-z0-9]+)"/);
  if (!bundleMatch) {
    return { queryId: FALLBACK_QUERY_ID, featureSwitches: FALLBACK_FEATURE_SWITCHES, ... };
  }
  const chunk = await fetchText(`https://abs.twimg.com/.../bundle.TwitterArticles.${bundleMatch[1]}a.js`);
  // 从 JS chunk 中正则提取 queryId...
}
```

**点评**：优雅的"尝试动态 → fallback 静态"模式。不做 over-engineering——正则足以应对当前结构，fallback 保证最差情况可用。

**写法二：三级 Cookie 加载与合并**（`cookies.ts` 第 262-271 行）

```typescript
export async function loadXCookies(log?): Promise<Record<string, string>> {
  const inlineMap = await loadXCookiesFromInline(log);   // 环境变量
  const fileMap = await loadXCookiesFromFile(log);       // 缓存文件
  const combined = { ...fileMap, ...inlineMap };
  if (hasRequiredXCookies(combined)) return combined;    // 快速路径
  const cdpMap = await loadXCookiesFromCdp(log);        // 浏览器（重操作，最后才触发）
  return { ...fileMap, ...cdpMap, ...inlineMap };
}
```

**点评**：惰性加载——只有前两级不够时才启动浏览器。合并顺序确保用户显式设置（环境变量）始终优先。这是认证系统设计的教科书范例。

**写法三：Thread 完整性三方向翻页**（`thread.ts` 第 186-228 行）

```typescript
while (topCursor && topHasThread && maxRequestCount > 0) {
  const parsed = parseTweetsAndToken(await fetchTweetDetail(tweetId, cookieMap, topCursor));
  topHasThread = inThread(parsed.entries);
  topCursor = parsed.topCursor;
  allEntries = parsed.entries.concat(allEntries);  // 向前拼接
}
```

**点评**：`inThread` 作为守卫条件——一旦翻页结果不再包含同一用户的同一对话，立即停止。避免拉取无关回复。

---

## 五、教学小结

### 核心 Takeaways

1. **"danger" 命名约定 + Consent 机制 = 可复制的逆向工程 skill 模板**。任何使用非公开 API 的 skill 都应该采用这套法律免责设计。

2. **极致模块化的价值**：17 个文件看似过度设计，但每个文件都可以独立测试、独立复用。`tweet-to-markdown.ts` 既是 `main.ts` 的子模块，也能直接 CLI 运行——这种"双入口"设计值得学习。

3. **动态 + 静态 Fallback 的 API 端点管理**：面对随时变更的第三方 API，从前端 bundle 动态提取最新参数，同时保留硬编码兜底值，是逆向工程项目的最佳实践。

4. **认证的分层懒加载**：环境变量（零成本）→ 文件缓存（低成本）→ 浏览器 CDP（高成本），按成本递增触发。这在所有需要认证的数据采集 skill 中都适用。

5. **媒体本地化的幂等设计**：先生成 Markdown 再可选下载媒体，下载后重写链接。已有本地文件时通过 frontmatter 匹配跳过，确保重复运行安全。

### 数据采集类 Skill 设计原则

- 认证与业务逻辑完全解耦（`cookies.ts` vs `graphql.ts`）
- API 响应结构用防御性解析（大量 `??`、optional chaining、`unwrapTweetResult`）
- 输出路径支持多种模式（用户指定文件/目录/默认约定）
- 幂等性：重复运行不产生副作用

### 为什么这是模块化程度最高的 Skill

对比其他 skill 通常用 1-3 个脚本文件完成所有工作，`baoyu-danger-x-to-markdown` 用 17 个文件实现了：
- 类型安全（`types.ts` 独立类型层）
- 可测试性（`markdown.test.ts` 验证渲染逻辑）
- 关注点分离（网络/认证/解析/渲染/文件操作各自独立）
- 最小外部依赖（仅 `baoyu-chrome-cdp`，其余全部用 Node.js 标准库）

这种组织方式特别适合需要长期维护、API 可能频繁变更的逆向工程类项目——当 X 修改某个 API 结构时，只需修改对应模块而不影响其余代码。
