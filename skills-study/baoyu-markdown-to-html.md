# baoyu-markdown-to-html Skill 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| **名称/版本** | `baoyu-markdown-to-html` v1.56.1 |
| **一句话定位** | Markdown → 带内联 CSS 的精美 HTML 转换器，针对微信公众号等平台深度优化 |
| **触发关键词** | "markdown to html"、"convert md to html"、"md 转 html"、"微信外链转底部引用"、styled HTML output |
| **前置依赖** | `bun` 或 `npx`（二选一）；核心渲染逻辑由 `baoyu-md` npm 包提供 |
| **适用场景** | 将技术文章、翻译稿件、博客长文转为可直接粘贴到微信编辑器的 HTML；外链需要转底部引用时尤为适用 |
| **输入 → 输出** | `.md` 文件 → 同目录下 `.html` 文件 + JSON 元数据（title/author/summary/images/backupPath） |

---

## 二、架构与设计模式分析

### 2.1 "3.5 步" Workflow

这个 skill 的工作流精炼为 **3.5 步**，编号本身就传递了设计意图——Step 0 是"可选前置"，Step 1.5 是"条件性插入步骤"：

```
Step 0  : Pre-check —— CJK 内容预检 + 跨 skill 格式化协作
Step 1  : Theme     —— 4 级 fallback 解析主题
Step 1.5: Citation  —— 判断是否开启底部引用模式
Step 2  : Convert   —— 调用 main.ts 执行转换
Step 3  : Report    —— 输出路径 + 备份提示
```

与动辄七八步的复杂 skill 不同，这里刻意将流程压缩到最少步骤，体现了**管道型 skill 的轻量哲学**——它是发布链路中的一环，不是终点。

### 2.2 Step 0：CJK 内容预检 + `baoyu-format-markdown` 跨 skill 协作

Step 0 展示了一种优雅的"**可选前置协作**"模式：

1. 读取输入文件，检测是否包含 CJK 字符
2. 若无 CJK 内容 → 直接跳到 Step 1
3. 若有 CJK 内容且 `baoyu-format-markdown` skill 可用 → 询问用户是否先格式化

这解决了一个实际痛点：中文 Markdown 中常见 `**加粗**` 与标点冲突、中英文缺少空格等问题。但设计上**不强制依赖**另一个 skill，而是"检测 → 建议 → 用户决定"，保持了 skill 的独立可用性。

### 2.3 Theme 解析的 4 级 fallback 链

主题解析是本 skill 设计最精巧的部分，设计了一条清晰的 fallback 链：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | CLI `--theme` 或对话中指定 | 用户显式意图最优先 |
| 2 | 本 skill 的 EXTEND.md `default_theme` | 用户级持久化偏好 |
| 3 | `baoyu-post-to-wechat` 的 EXTEND.md `default_theme` | **跨 skill 配置复用** |
| 4 | 询问用户 | 最终兜底 |

第 3 级是亮点：如果用户已经在发布 skill 中配置了默认主题，转换 skill 会自动复用，避免用户重复配置。这种**跨 skill 配置 fallback** 是一种实用的设计模式。

### 2.4 脚本架构：单脚本设计

整个执行层只有一个 `scripts/main.ts`，依赖唯一的 npm 包 `baoyu-md`。`main.ts` 本身约 250 行，职责清晰：参数解析 → frontmatter 提取 → 图片占位符替换 → 调用 `renderMarkdownDocument` → 写文件 → 输出 JSON。核心渲染逻辑全部封装在 `baoyu-md` 包中，skill 脚本只做"胶水"工作。

### 2.5 Citation Mode：微信兼容的底部引用设计

Citation Mode 默认关闭，仅在用户显式请求时启用，遵循三条精确规则来处理链接（详见第三节）。这种"默认不干预 + 关键词触发"的设计避免了误伤普通转换场景。

---

## 三、核心能力拆解

### 3.1 4 种主题

| 主题 | 风格特点 |
|------|---------|
| `default` | 经典布局，居中标题 + 底部边框，H2 白字彩色背景 |
| `grace` | 优雅风，文字阴影 + 圆角卡片 + 精致引用块（社区贡献 @brzhang） |
| `simple` | 极简风，非对称圆角 + 大量留白（社区贡献 @okooo5km） |
| `modern` | 现代感，大圆角 + 胶囊标题 + 宽松行高，搭配 `--color red` 可呈现传统红金风 |

### 3.2 13 种颜色预设

从 Classic Blue (`#0F4C81`) 到 China Red (`#A93226`)，覆盖了从科技到传统的色调需求。同时支持传入任意 hex 值，预设只是快捷方式。

### 3.3 丰富的 Markdown 特性

除标准 Markdown 外，支持 **Mermaid 图表**、**PlantUML 图表**、**Ruby text**（`{底|dǐ}`注音标注）、**GitHub Alerts**（`[!NOTE]`/`[!WARNING]` 等）、**Footnotes**（`[^1]`脚注），覆盖了技术写作和翻译场景的高频需求。

### 3.4 Citation Mode 的三条规则

当 `--cite` 启用时，链接处理遵循三条精确规则：

1. **微信链接保留**：`https://mp.weixin.qq.com/...` 链接保持原样，不移到底部——因为微信内链在公众号中可直接点击
2. **裸链接内联**：链接文本等于 URL 本身的裸链接保持内联——移到底部没有信息增益
3. **普通链接转底部引用**：其余外链替换为编号上标，末尾统一生成 `引用链接` 区域

这三条规则精确命中了微信公众号的实际限制：外链无法点击，只能引导读者到文末查看。

### 3.5 Frontmatter 元数据提取 + 冲突备份

- **Frontmatter**：自动从 YAML 头部提取 title/author/description；若无 title 则回退到首个 H1/H2 标题，再回退到文件名
- **冲突备份**：若输出 `.html` 已存在，自动备份为 `.html.bak-YYYYMMDDHHMMSS`，不覆盖用户的已有产出

---

## 四、Prompt Engineering 学习点

### 4.1 跨 skill 配置 fallback

读取 `baoyu-post-to-wechat` 的 EXTEND.md 作为主题配置的第三优先级来源，是一种**零耦合的配置复用**：不依赖对方 skill 的存在，只是"如果配置文件恰好在就用"。这种模式适用于所有存在上下游关系的 skill 组合。

### 4.2 "可选前置协作"模式

Step 0 的设计可以提炼为一个通用模式：

```
IF 输入内容满足某条件 AND 某前置 skill 可用
  → 建议用户先执行前置 skill
  → 用户同意则执行，拒绝则继续
```

这比硬性依赖更灵活，比完全忽略更贴心。值得在多 skill 协作场景中复用。

### 4.3 Citation Mode 的默认关闭 + 关键词触发

Citation Mode 没有设计为"自动检测外链就开启"，而是**默认关闭，仅关键词触发**（"微信外链转底部引用"、"底部引用"、`--cite`）。这避免了"自作聪明"的问题——多数 Markdown 转 HTML 场景并不需要底部引用，只有发微信公众号时才需要。

### 4.4 值得借鉴的写法

**Fallback 链的表格化表达**——SKILL.md 中用优先级编号表格列出 EXTEND.md 的查找路径：

> | Priority | Path | Scope |
> |----------|------|-------|
> | 1 | `.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` | Project |
> | 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/...` | XDG |
> | 3 | `$HOME/.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` | User home |

**点评**：用表格把 fallback 逻辑从散文变成结构化数据，Agent 解析零歧义。这比写一段"先检查 A，如果没有再检查 B"的自然语言描述更不容易出错，尤其是当 fallback 层级较多时。

**User Input Tools 的运行时适配段落**——SKILL.md 开头定义了一个通用的用户交互工具选择规则（优先内置工具 → fallback 纯文本 → 支持批量则合并提问），使 skill 可在不同 Agent 运行时中工作。这种**运行时无关的交互层设计**值得所有需要用户输入的 skill 借鉴。

---

## 五、教学小结

### 核心 Takeaway

1. **管道 skill 要轻量**：一个 `main.ts` + 一个 npm 依赖，做好"接收 Markdown、输出 HTML"这一件事，不越界、不膨胀。核心渲染逻辑封装在 `baoyu-md` 包中，脚本只负责 I/O 胶水。

2. **跨 skill 配置复用优于重复配置**：通过读取 `baoyu-post-to-wechat` 的 EXTEND.md 来获取默认主题，实现了零耦合的偏好继承。上下游 skill 之间共享配置时，这种"有则用、无则跳"的 fallback 是最佳实践。

3. **可选前置 > 硬依赖**：Step 0 的 CJK 预检 + 格式化建议展示了 skill 间柔性协作的范式——检测条件、建议操作、用户拍板，三步缺一不可。

4. **默认不干预，关键词触发高级功能**：Citation Mode 的设计哲学是"不问不答"，避免给 80% 的普通场景增加噪音，只在用户明确需要时激活。

5. **结构化表达 > 散文描述**：fallback 链、选项表、主题对比等信息都用表格呈现，Agent 解析准确率远高于自然语言段落。

### 管道式 skill 在发布链路中的角色

`baoyu-markdown-to-html` 在完整的微信公众号发布链路中处于中间环节：

```
baoyu-format-markdown（格式化）
    → baoyu-markdown-to-html（转 HTML）← 你在这里
        → baoyu-post-to-wechat（发布到微信）
```

它向上游"借"格式化能力（Step 0 的可选协作），向下游"借"主题配置（fallback 到 post-to-wechat 的 EXTEND.md），自身只专注转换这一环。这种设计让每个 skill 保持独立可用，同时在组合使用时产生 1+1>2 的协同效果。

### 轻量 skill 的设计哲学

本 skill 是"轻量 skill"的典范：**单脚本入口**（无复杂目录结构）、**可选配置**（EXTEND.md 不存在也能正常工作）、**跨 skill 复用**（不重造轮子，复用已有配置和能力）。当你的 skill 定位为管道中的一环而非终端产品时，这种克制的设计哲学值得遵循。
