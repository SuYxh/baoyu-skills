# baoyu-format-markdown 深度解读

## 一、基础信息速览

| 维度 | 内容 |
|------|------|
| 名称/版本 | `baoyu-format-markdown` v1.57.0 |
| 一句话定位 | 将纯文本或 Markdown 文件美化为结构清晰、重点突出的读者友好格式 |
| 触发关键词 | "format markdown"、"beautify article"、"add formatting"、改善文章排版 |
| 前置依赖 | `bun` 或 `npx`（用于运行 typography 脚本） |
| 适用场景 | 博客文章美化、笔记整理、技术文档格式化、公众号素材排版 |
| 输入→输出 | 单个 `.md` 或纯文本文件 → `{filename}-formatted.md` + `{filename}-analysis.md` |

## 二、架构与设计模式分析

### 7 步 Workflow 流程

```
Read → Analyze → Frontmatter/Title → Format → Save → Typography → Report
 S1      S2           S3               S4      S5       S6          S7
├──────── AI 完成（Steps 1-5）────────────┤  ├─脚本─┤  ├─ AI ─┤
```

这是一个 **AI + 脚本混合架构**：语义理解和创意决策交给 AI，确定性的文本转换交给脚本。这种分工非常精准——AI 擅长判断"哪里该加粗、哪里该分段"，但让 AI 做正则替换引号或检测 CJK 间距既浪费 token 又容易出错。

### 三个脚本的分工

| 脚本 | 角色 | 核心技术 |
|------|------|----------|
| `main.ts` | 入口编排 | unified/remark 解析 AST，遍历节点调用子模块 |
| `quotes.ts` | 引号全角化 | 正则将 `"..."` 和 `「...」` 替换为 `"..."` |
| `autocorrect.ts` | CJK 间距修复 | 调用 `autocorrect-node` CLI 工具 in-place 修复 |

`main.ts` 的设计亮点在于使用 remark AST 处理而非纯正则——通过 `unist-util-visit` 遍历语法树，只对 `text` 节点做引号替换，避免误伤代码块或链接中的引号。`remark-cjk-friendly` 插件专门处理 CJK 粗体/斜体的标点粘连问题。

### 配置体系

EXTEND.md 采用三级查找优先级（Project → XDG → Home），不强制首次设置——这降低了使用门槛。核心配置项 `auto_select` 可跳过标题/摘要的用户选择环节，适合批量处理场景。

### 内容类型检测 & 三种处理路径

```
检测到 Markdown? ──┬── 用户选 Optimize ──→ 完整 7 步流程
                   ├── 用户选 Keep     ──→ 跳到 S5 复制 + S6 脚本
                   └── 用户选 Typography──→ 直接 S6（原地修改）
纯文本? ───────────────────────────────→ 完整 7 步流程
```

这种分级设计让用户可以精确控制"改多少"，避免了对已有良好格式的文章进行过度干预。

## 三、核心能力拆解

### Step 2 分析框架（四维度）

分析不是随意的，而是围绕 4 个具体维度展开：

1. **Highlights & Key Insights** — 找金句、核心论点、反直觉观点
2. **Structure Assessment** — 评估逻辑流、找缺失标题的段落边界
3. **Reader-Important Information** — 可操作建议、关键概念、隐藏的列表
4. **Formatting Issues** — 层级不一致、混排段落、代码未标注

分析结果保存为 `{filename}-analysis.md`，既是 Step 4 的执行蓝图，也是可追溯的决策记录。

### Step 3 标题生成系统

标题生成使用 `references/title-formulas.md` 中的 **8 种 Hook 公式**（颠覆式、方案式、悬念式、具体数字、对比、结果前置、反问、共情），外加直白风格作为平衡选项。流程：

1. 提取核心论点、痛点、金句
2. 选 2-3 个最匹配的 Hook 公式生成候选
3. 再生成 1-2 个直白标题
4. 通过 `AskUserQuestion` 让用户选择（或 `auto_select` 自动取最优）

### Summary 双版本设计

| 字段 | 长度 | 用途 |
|------|------|------|
| `summary` | ~50-80 字符 | 信息流、社交分享、SEO meta |
| `description` | ~100-200 字符 | 文章预览、Newsletter 摘要 |

两个版本直接生成（不走用户选择），各有明确的投放场景。

### Step 4 格式化工具箱

8 种格式元素（Headings / Bold / 无序列表 / 有序列表 / 表格 / 代码 / 引用块 / 分隔线）各有明确的使用场景和"什么时候用"的判断标准。

### Typography 脚本三功能

1. **emphasis 修复**：通过 `remark-cjk-friendly` 处理 CJK 加粗/斜体标记的标点粘连
2. **spacing**：通过 `autocorrect-node` 自动在中英文之间添加空格
3. **quotes**：将 ASCII 引号和日式引号统一为中文全角引号

## 四、Prompt Engineering 学习点

### "只调格式不改内容" 的约束边界设计

> **Core principle**: Only adjust formatting and fix obvious typos. Never add, delete, or rewrite content.

这是整个 skill 的宪法级约束。它出现在文件最开头的第 19 行，确保任何后续指令都在此边界内执行。这种"先声明不可逾越的红线"的做法，在需要 AI 做有限度改动的场景中非常关键。

### "蓝图-实施" 双阶段模式

Step 2 分析生成蓝图文件 → Step 4 依据蓝图执行格式化。这个分离有两个好处：
- AI 在分析阶段可以专注思考"改什么"，不受"怎么改"的干扰
- 分析文件作为中间产物可供用户审查，提升可控性和可追溯性

### 正反面约束的对比写法

Step 4 的格式化原则用了"what NOT to do" + "what TO do" 的双面对照：

> **What NOT to do:**
> - Do NOT add sentences, explanations, or commentary
> - Do NOT rephrase or rewrite the author's words
>
> **What TO do:**
> - Preserve the author's voice, tone, and every word
> - Bold key conclusions and core takeaways — the sentences a reader would highlight

这种正反对照极大减少了 AI 的歧义空间。只写正面规则时，AI 可能"创造性地"找到漏洞；加上反面禁止项，约束网更加严密。

### 值得借鉴的写法摘录

**写法 1 — 具体化的引导优于抽象描述：**

> "Add headings where the topic genuinely shifts — prefer vivid, specific headings over generic ones (e.g., '3 天搞定 vs 传统方案' over '方案对比')"

点评：不是说"标题要好"，而是给出了正例和反例的对比，AI 能直接模仿这种风格。

**写法 2 — Hook 公式配"When to pick"决策表：**

标题公式不是孤立的模板，而是配了一个"什么文章适合什么公式"的决策表。这避免了 AI 随机套用公式的问题。

**写法 3 — 分析维度的操作化定义：**

> "Surprising facts, data points, or counterintuitive claims"
> "Lists or enumerations buried in prose"

每个分析维度都配了具体的搜索信号，告诉 AI "你在文本中找什么"，而非抽象地说"分析内容"。

## 五、教学小结

### 核心 Takeaways

1. **AI + 脚本混合架构是最佳实践**：语义判断（加粗哪里、标题写什么）交给 AI，确定性文本操作（正则替换、AST 重写）交给脚本，各取所长。

2. **"蓝图-实施"分离提升可控性**：先生成分析文件再执行格式化，中间产物可审查、可追溯、可调试，比一步到位更可靠。

3. **约束边界要写在最前面**：核心原则（只改格式不改内容）放在文件开头，作为后续所有指令的"宪法"，确保 AI 不会偏离轨道。

4. **正反面对照减少歧义**：同时告诉 AI "做什么"和"不做什么"，约束网更严密。特别是对于"美化"这种主观性强的任务，反面禁止项比正面鼓励项更重要。

5. **用户控制粒度要分级**：三种处理路径（完整优化 / 保留格式 / 仅排版）+ `auto_select` 开关，让 skill 既适合精细交互也适合批量自动化。

### AI + 脚本混合架构的适用场景

当任务同时涉及"理解语义做判断"和"精确执行文本变换"时，混合架构最有价值。典型场景：代码格式化（AI 判断风格 + prettier 执行）、翻译后处理（AI 翻译 + 脚本修术语表）、内容审校（AI 标记问题 + 脚本修标点）。

### "只改格式不改内容"类 skill 的约束设计方法

1. 在文件最顶部声明核心红线
2. 用分析步骤强制 AI "先想后做"，避免冲动改写
3. 正反面规则对照，堵住创造性偏离的空间
4. 提供具体的正例反例（不只是规则，还要有示范）
5. 中间产物（analysis file）作为审计痕迹，让约束可验证
