# baoyu-post-to-wechat 深度解读

## 一、基础信息速览

| 维度 | 说明 |
|------|------|
| **名称/版本** | `baoyu-post-to-wechat` v1.56.1 |
| **一句话定位** | 将内容发布到微信公众号——支持文章（Article）和图文/贴图（Image-Text）两种形态 |
| **触发关键词** | "发布公众号"、"post to wechat"、"微信公众号"、"贴图"、"图文"、"文章" |
| **前置依赖** | `bun`（或 `npx -y bun`）；API 方法需 AppID + AppSecret 凭证；Browser 方法需 Chrome + 登录态 |
| **适用场景** | Markdown/HTML/纯文本发布为公众号文章草稿；多图贴图发布；多账号批量管理 |
| **输入→输出** | `.md` / `.html` / 纯文本 + 可选封面图 → 公众号草稿（media_id）+ 本地 HTML 副本 |

---

## 二、架构与设计模式分析

### 5 步 Article Workflow 流程图

```
Step 0: Load Prefs          Step 0.5: Account         Step 1: Input Type
┌──────────────────┐       ┌──────────────────┐      ┌──────────────────┐
│ 查找 EXTEND.md    │       │ 多账号?           │      │ .html → Step 3   │
│ project > XDG >  │──────▶│ 1个 → 自动选      │─────▶│ .md   → Step 2   │
│   home           │       │ 2+ → prompt/CLI  │      │ 纯文本 → 保存.md  │
│                  │       │ --account alias   │      │         → Step 2  │
│ 未找到 → 首次设置 │       └──────────────────┘      └──────────────────┘
│ (⛔ BLOCKING)     │
└──────────────────┘
                    Step 2: Method + Creds        Step 3: Theme/Meta
                    ┌──────────────────┐          ┌──────────────────┐
                    │ API (推荐,快)     │          │ Theme: CLI > ext │
                    │ Browser (慢)     │          │ Color: CLI > ext │
                    │                  │─────────▶│ 验证 title/      │
                    │ API 缺凭证 →     │          │ summary/author/  │
                    │ guided setup     │          │ cover fallback   │
                    └──────────────────┘          └────────┬─────────┘
                                                           │
Step 5: Report              Step 4: Publish                ▼
┌──────────────────┐        ┌──────────────────────────────────────┐
│ 完成报告          │◀───────│ ⚠️ Never pre-convert md→HTML          │
│ media_id (API)   │        │ API: wechat-api.ts + draft/add       │
│ 草稿箱链接        │        │ Browser: wechat-article.ts + CDP paste│
│ 文件清单          │        └──────────────────────────────────────┘
└──────────────────┘
```

### 双发布方法：API vs Browser CDP

这是该 Skill 最核心的架构决策——同一目标，两条完全不同的技术路径：

| 维度 | API 方法 | Browser 方法 |
|------|---------|-------------|
| 速度 | 快（直接 HTTP 调用） | 慢（启动 Chrome、CDP 操控） |
| 凭证 | AppID + AppSecret | Chrome 登录态（扫码） |
| 图片处理 | `<img>` 标签 → 上传获取 media_id | placeholder `WECHATIMGPH_N` → 逐个剪贴板粘贴 |
| 评论控制 | ✓（`need_open_comment`） | ✗ |
| 封面图 | 必需（`thumb_media_id`） | 不需要 |

两种方法对图片的处理方式截然不同，这正是 **"Never pre-convert markdown to HTML"** 约束的根本原因。

### Multi-Account 支持设计

通过 EXTEND.md 的 `accounts:` 块实现渐进式多账号：
- 无 `accounts` 块 → 单账号，原始行为不变
- 1 个条目 → 自动选择，无提示
- 2+ 条目 → 插入 Step 0.5 提示选择
- `default: true` → 预选但可切换

每个账号拥有独立的凭证解析链和 Chrome Profile 隔离（`wechat-{alias}/`），互不干扰。

### Image-Text（贴图）vs Article（文章）两条路径

Skill 支持两种微信内容形态：
- **Image-Text**：短内容（≤1000 字）+ 多图（≤9 张），使用 `wechat-browser.ts`，标题自动压缩到 20 字
- **Article**：长文章，支持完整 Markdown 排版、主题渲染、引用转换，API 或 Browser 两种发布方式

### Pre-flight Check 机制

`check-permissions.ts` 是一个"可选但建议"的环境诊断脚本，覆盖 8 项检查：Chrome 可用性、Profile 隔离、Bun 运行时、macOS Accessibility 权限、剪贴板、粘贴按键模拟、API 凭证、Chrome 进程冲突。用户可以跳过，但首次使用时会主动建议运行。

### Citation 默认开启

Markdown 输入时，普通外链默认转换为底部引用（citation），因为微信公众号不支持外链跳转。`--no-cite` 仅在用户明确要求时使用。这是一个对平台限制的优雅适配。

---

## 三、核心能力拆解

### API 方法：draft/add 接口

```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN
```

关键 payload 字段：
- `article_type`: `news`（默认）或 `newspic`
- `thumb_media_id`: 封面图的 media_id（`news` 类型必需）
- `need_open_comment` / `only_fans_can_comment`: 评论控制

Access Token 管理通过 5 级 Credential Resolution 链实现（内联 → 环境变量 → 项目 .env → 用户 .env → 无前缀 fallback）。

### Browser 方法：Chrome CDP 控制

图片处理流程堪称巧妙：
1. Markdown 中图片 → 替换为 `WECHATIMGPH_N` 占位符
2. HTML 粘贴到微信编辑器
3. 逐个定位占位符文字 → 选中 → 删除 → 从剪贴板粘贴图片

这种"占位-替换"模式绕过了微信编辑器不支持 HTML `<img>` 直接粘贴的限制。

### Theme/Color 系统

4 种主题 + 13 种颜色预设（或自定义 hex）：

| 主题 | 默认色 | 风格描述 |
|------|--------|---------|
| default | blue | 居中标题 + 边框，白字色底 H2 |
| grace | purple | 文字阴影，圆角卡片，精致引用 |
| simple | green | 非对称圆角，大量留白 |
| modern | orange | 大圆角，药丸标题，宽松排版 |

### 元数据验证的 Fallback 链

| 字段 | 优先级链 |
|------|---------|
| Title | CLI `--title` → frontmatter `title` → 首个 H1/H2 → 首句 → 手动输入 |
| Summary | frontmatter `description` → `summary` → 首段截断 120 字 → 手动输入 |
| Author | CLI `--author` → frontmatter → EXTEND.md `default_author` |
| Cover | CLI `--cover` → frontmatter（`coverImage`/`featureImage`/`cover`/`image`）→ `imgs/cover.png` → 首个行内图 → 要求提供 |

### Feature Comparison 三方对比

| 特性 | Image-Text | Article (API) | Article (Browser) |
|------|:---:|:---:|:---:|
| Markdown 输入 | 仅标题/内容 | ✓ | ✓ |
| 主题渲染 | ✗ | ✓ | ✓ |
| 多图 | ✓ (≤9) | ✓ (行内) | ✓ (行内) |
| 评论控制 | ✗ | ✓ | ✗ |
| 需要 Chrome | ✓ | ✗ | ✓ |
| 需要 API 凭证 | ✗ | ✓ | ✗ |

### Troubleshooting 关键问题

| 问题 | 解决方案 |
|------|---------|
| API 凭证缺失 | Step 2 guided setup 引导写入 `.baoyu-skills/.env` |
| Access Token 过期 | 验证凭证有效性，重新获取 |
| 粘贴失败 | macOS: 检查 Accessibility 权限；Linux: 安装 xdotool/ydotool |
| Chrome 未找到 | 设置 `WECHAT_BROWSER_CHROME_PATH` 环境变量 |
| 封面图缺失 | 添加 frontmatter cover 或放置 `imgs/cover.png` |

---

## 四、Prompt Engineering 学习点

### 1. 双方法架构的选择设计

Skill 没有强制选择一种方法，而是提供 **"推荐 + 备选"** 的柔性架构。API 标注为 `(Recommended)`，但 Browser 方法作为无需凭证的降级方案始终可用。这种设计让 Skill 在任何环境下都能工作——低门槛入门（Browser），高效率进阶（API）。

### 2. "Never pre-convert markdown to HTML" 的防御性约束

> **Important — never pre-convert markdown to HTML.** Publishing scripts handle the conversion internally and the two methods render images differently: API renders `<img>` tags for upload, browser uses placeholders for paste-and-replace. Passing a pre-converted HTML breaks one or the other.

这是一条典型的 **防御性 Prompt 约束**：AI agent 天然倾向于"提前做好转换"来帮用户省事，但这里提前转换会导致两种方法之一必然失败。通过明确说明 *为什么不能这样做*（而非仅说"不要"），让 LLM 理解约束背后的因果关系，从而更可靠地遵守。

### 3. 配置优先级的 5 级 Fallback

```
CLI args → frontmatter → EXTEND.md (account-level) → EXTEND.md (global) → skill defaults
```

这个 5 级优先级链是一个值得借鉴的通用模式：
- **CLI args**：一次性覆盖，最高优先
- **frontmatter**：与内容绑定的元数据
- **EXTEND.md account-level**：多账号场景下的分离配置
- **EXTEND.md global**：用户通用偏好
- **skill defaults**：开箱即用兜底

每一级都有明确的语义和使用场景，避免了"配了但没生效"的困惑。

### 4. Multi-Account 作为高级特性的渐进式暴露

多账号不是在首次设置时就暴露，而是通过 EXTEND.md 的 `accounts:` 块 *按需启用*。单账号用户完全感知不到多账号逻辑的存在；多账号用户通过编辑配置文件自行进入高级模式。这是 **Progressive Disclosure** 在 Skill 设计中的教科书应用。

### 5. 值得借鉴的写法摘录

**摘录 1——First-Time Setup 的 BLOCKING 声明**：
> **BLOCKING OPERATION**: This setup MUST complete before ANY other workflow steps. Do NOT: Ask about content or files to publish / Ask about themes or publishing methods / Proceed to content conversion or publishing.

点评：用全大写 + 明确的"不要做"清单来防止 LLM 的过度主动性。在有多步骤的工作流中，LLM 容易跳过配置直接进入"核心任务"，这种 BLOCKING 声明是有效的锚定技术。

**摘录 2——Credential Resolution 的伪代码**：
```
if no accounts block:
    → single-account mode (original behavior)
elif accounts.length == 1:
    → auto-select the only account
elif --account <alias> CLI arg:
    → select matching account
elif one account has default: true:
    → pre-select, display: "Using account: <name> (--account to switch)"
else:
    → prompt user to choose from the list
```

点评：用 if-elif 伪代码代替自然语言描述分支逻辑，消除歧义。LLM 对代码结构的理解精度远高于散文描述，这种"说人话 + 写伪代码"的混合模式特别适合条件分支复杂的场景。

**摘录 3——Step 5 的结构化模板**：

Completion Report 使用固定模板 + 条件插槽（`← API method only`），让 LLM 输出格式稳定可预测。模板中每个字段的位置和格式都是确定的，避免了自由发挥导致的信息遗漏。

---

## 五、教学小结

### 核心 Takeaways

1. **双路径架构是平台发布类 Skill 的最佳实践**：一条快速路径（API）+ 一条兼容路径（Browser），确保任何环境都能完成任务，同时为高级用户提供最优体验。

2. **防御性约束需要解释"为什么"**：仅说"不要做 X"不够，必须解释做了 X 会导致什么后果。LLM 在理解因果关系后遵守约束的可靠性显著提升。

3. **配置系统设计的黄金模式是"多级 Fallback + 渐进暴露"**：让 zero-config 用户开箱即用，让 power user 精细控制，同时保证不同层级的配置不会相互冲突。

4. **平台限制应转化为 Skill 的默认行为**：微信不支持外链 → 默认开启 citation 转换；微信编辑器不支持 img 粘贴 → 使用占位符替换。把限制变成默认值比在文档中警告用户更有效。

5. **BLOCKING 声明 + NEVER 约束是控制 LLM 工作流顺序的有效手段**：在关键决策点（如首次设置、格式转换）使用强约束语言，防止 LLM 的"热心"跳步行为。

### 平台发布类 Skill 的通用设计模式

- **Credential 管理三件套**：环境变量 → .env 文件 → Guided Setup（检测 → 引导 → 持久化）
- **Pre-flight Check 脚本**：独立诊断脚本，非强制但建议，覆盖运行时环境所有依赖项
- **Completion Report 模板**：固定结构 + 条件字段，确保用户始终获得可操作的"下一步"指引
- **多账号 = 独立 Profile + 独立凭证 + CLI 选择器**：三个支柱缺一不可

### 如何处理平台限制

| 微信平台限制 | Skill 的应对策略 |
|-------------|-----------------|
| 不支持外链跳转 | 默认将外链转为底部引用（citation） |
| 编辑器不支持 img HTML 粘贴 | 占位符 + CDP 逐个图片粘贴替换 |
| 评论需后台配置 | API payload 自动携带 `need_open_comment` |
| 贴图标题限 20 字 | 自动压缩（中文语义提取） |
| 贴图最多 9 张 | 脚本内置约束检查 |
| 草稿箱管理需登录后台 | Completion Report 中直接给出后台链接和操作路径 |

核心思路：**不对抗平台限制，而是将其内化为 Skill 的默认行为和自动处理逻辑**，用户无需了解限制即可获得正确结果。
