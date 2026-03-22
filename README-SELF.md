        # baoyu-skills 仓库详细解读

## 📋 项目概述

**baoyu-skills** 是一个由 Jim Liu（宝玉）开发的 **Claude Code 插件市场项目**，提供了一系列 AI 驱动的内容生成和处理技能，旨在提升日常工作效率。当前版本为 **1.76.1**。

这是一个 **Monorepo 架构**的项目，使用 TypeScript 编写，基于 Bun 运行时，无需构建步骤即可运行。

---

## 🏗️ 架构设计

### 整体结构

```
baoyu-skills/
├── .claude-plugin/          # 插件市场配置
│   └── marketplace.json     # 定义插件元数据和技能路径
├── packages/                # 共享包
│   ├── baoyu-chrome-cdp/    # Chrome DevTools Protocol 封装
│   └── baoyu-md/            # Markdown 转 HTML 核心库
├── skills/                  # 技能目录（17个独立技能）
│   ├── baoyu-xhs-images/    # 小红书图文生成
│   ├── baoyu-infographic/   # 信息图表生成
│   ├── baoyu-comic/         # 漫画生成
│   ├── baoyu-slide-deck/    # 幻灯片生成
│   ├── baoyu-cover-image/   # 封面图生成
│   ├── baoyu-image-gen/     # AI 图像生成后端
│   └── ...                  # 其他技能
├── scripts/                 # 仓库维护工具
├── docs/                    # 文档
└── screenshots/             # 风格预览截图
```

### 三大技能类别

| 类别 | 插件名 | 包含技能 |
|------|--------|----------|
| **内容生成** | `content-skills` | 小红书图文、信息图表、封面图、幻灯片、漫画、文章插图、发布到 X/微信/微博 |
| **AI 生成后端** | `ai-generation-skills` | 图像生成（多平台）、Gemini Web |
| **工具类** | `utility-skills` | YouTube 字幕、URL 转 Markdown、图片压缩、Markdown 格式化、翻译等 |

---

## 🎯 核心技能详解

### 1. 内容生成类技能

#### [baoyu-xhs-images](skills/baoyu-xhs-images) - 小红书图文生成器

**特点**：采用 **风格 × 布局** 二维系统

- **9 种风格**：cute、fresh、warm、bold、minimal、retro、pop、notion、chalkboard
- **6 种布局**：sparse、balanced、dense、list、comparison、flow
- **工作流**：分析内容 → 自动推荐风格布局 → 生成 1-10 张卡通风格图文

#### [baoyu-infographic](skills/baoyu-infographic) - 专业信息图表

**特点**：20 种布局 × 17 种视觉风格

- **布局类型**：pyramid、funnel、timeline、venn、mind-map、iceberg 等
- **视觉风格**：craft-handmade、claymation、kawaii、cyberpunk-neon、technical-schematic 等
- **智能推荐**：根据内容自动分析并推荐最佳布局×风格组合

#### [baoyu-comic](skills/baoyu-comic) - 知识漫画创作

**特点**：艺术风格 × 基调 组合系统

- **5 种艺术风格**：ligne-claire、manga、realistic、ink-brush、chalk
- **7 种基调**：neutral、warm、dramatic、romantic、energetic、vintage、action
- **预设模板**：ohmsha（欧姆社学习漫画风格）、wuxia（武侠风）、shoujo（少女漫）
- **6 种布局**：standard、cinematic、dense、splash、mixed、webtoon

#### [baoyu-slide-deck](skills/baoyu-slide-deck) - 幻灯片生成

**特点**：4 维度风格系统

- **纹理** × **情绪** × **字体** × **密度**
- **16 种预设**：blueprint、chalkboard、corporate、minimal、notion 等
- **输出格式**：自动合并为 `.pptx` 和 `.pdf`

#### [baoyu-cover-image](skills/baoyu-cover-image) - 文章封面图

**特点**：5 维度系统

- **类型** × **调色板** × **渲染** × **文字** × **情绪**
- **54 种独特组合**（9 调色板 × 6 渲染风格）

---

### 2. AI 生成后端

#### [baoyu-image-gen](skills/baoyu-image-gen) - 多平台图像生成

**支持的 AI 平台**：

| 平台 | 模型示例 | 特点 |
|------|----------|------|
| OpenAI | gpt-image-1.5 | 官方 API |
| Google | gemini-3-pro-image-preview | 支持参考图 |
| OpenRouter | google/gemini-3.1-flash-image-preview | 聚合平台 |
| DashScope | qwen-image-2.0-pro | 阿里云通义万象 |
| Replicate | google/nano-banana-pro | 开源模型托管 |
| Jimeng | jimeng_t2i_v40 | 即梦（字节跳动） |
| Seedream | doubao-seedream-5-0 | 豆包（字节跳动） |

**智能选择**：自动检测可用 API 密钥，优先使用 Google

#### [baoyu-danger-gemini-web](skills/baoyu-danger-gemini-web) - Gemini Web 逆向

**特点**：
- 使用浏览器 Cookie 认证（非官方 API）
- 支持文本和图像生成
- 首次运行需登录 Google 账号

---

### 3. 社交媒体发布

#### [baoyu-post-to-x](skills/baoyu-post-to-x) - 发布到 X/Twitter

- 支持普通推文（带图片）和 X Articles（长文 Markdown）
- 使用 Chrome CDP 绕过反自动化检测
- 用户手动审核后发布

#### [baoyu-post-to-wechat](skills/baoyu-post-to-wechat) - 发布到微信公众号

**两种模式**：
- **贴图模式**：多图 + 短标题/内容
- **文章模式**：完整 Markdown/HTML，支持主题

**发布方式**：
- **API 方式**（推荐）：需要 AppID/AppSecret
- **浏览器方式**：Chrome 登录，会话持久化

**多账号支持**：通过 `EXTEND.md` 配置多个公众号

#### [baoyu-post-to-weibo](skills/baoyu-post-to-weibo) - 发布到微博

- 普通微博：文本 + 图片/视频（最多 18 个文件）
- 头条文章：长文 Markdown + 封面图

---

### 4. 工具类技能

| 技能 | 功能 | 关键特性 |
|------|------|----------|
| [baoyu-youtube-transcript](skills/baoyu-youtube-transcript) | YouTube 字幕下载 | 多语言、翻译、章节分割、说话人识别 |
| [baoyu-url-to-markdown](skills/baoyu-url-to-markdown) | URL 转 Markdown | Chrome CDP 渲染、支持登录页面 |
| [baoyu-danger-x-to-markdown](skills/baoyu-danger-x-to-markdown) | X 内容转 Markdown | 推文线程、X Articles、媒体下载 |
| [baoyu-compress-image](skills/baoyu-compress-image) | 图片压缩 | 保持质量减小文件大小 |
| [baoyu-format-markdown](skills/baoyu-format-markdown) | Markdown 格式化 | 自动生成 frontmatter、标题、摘要 |
| [baoyu-markdown-to-html](skills/baoyu-markdown-to-html) | Markdown 转 HTML | 微信兼容主题、语法高亮、引用转换 |
| [baoyu-translate](skills/baoyu-translate) | 翻译 | 三种模式（quick/normal/refined）、术语表、受众适配 |

---

## 🔧 技术实现亮点

### 1. Chrome DevTools Protocol (CDP) 自动化

项目封装了 [baoyu-chrome-cdp](packages/baoyu-chrome-cdp) 包，用于：

- 绕过网站反自动化检测
- 使用真实浏览器 Cookie 认证
- 支持动态内容渲染

**应用场景**：Gemini Web、X/Twitter、微信公众号、微博、URL 抓取

### 2. Markdown 处理引擎

[baoyu-md](packages/baoyu-md) 是一个功能丰富的 Markdown 转 HTML 库：

- **70+ 代码高亮主题**
- **10 个扩展**：alert、footnotes、infographic、katex、plantuml、toc 等
- **5 个基础主题**：default、modern、grace、simple、base

### 3. 技能加载机制

**优先级顺序**：
1. 项目级 `skills/` 目录
2. 用户级 `~/.baoyu-skills/`
3. 系统级

**扩展机制**：通过 `EXTEND.md` 文件自定义配置

```bash
# 项目级扩展
.baoyu-skills/<skill-name>/EXTEND.md

# 用户级扩展
~/.baoyu-skills/<skill-name>/EXTEND.md
```

### 4. 环境配置管理

**加载优先级**（高优先级覆盖低优先级）：
1. CLI 环境变量
2. 系统环境变量
3. 项目级 `.baoyu-skills/.env`
4. 用户级 `~/.baoyu-skills/.env`

---

## 📦 依赖与运行时

### 核心依赖

| 依赖 | 用途 |
|------|------|
| **Bun** | TypeScript 运行时（无需构建） |
| **Chrome** | CDP 自动化（多个技能依赖） |
| **AI API Keys** | 图像生成（OpenAI/Google/DashScope 等） |

### 运行方式

```bash
# 检测运行时
if command -v bun &>/dev/null; then BUN_X="bun"
elif command -v npx &>/dev/null; then BUN_X="npx -y bun"
fi

# 执行技能
${BUN_X} skills/<skill>/scripts/main.ts [options]
```

---

## 🔒 安全设计

| 安全规则 | 实现方式 |
|----------|----------|
| **禁止管道安装** | 使用 `brew install` 或 `npm install -g` |
| **远程下载** | 仅 HTTPS，最多 5 次重定向，30 秒超时 |
| **系统命令** | 使用数组形式 `spawn`/`execFile`，不拼接 shell |
| **外部内容** | 视为不可信，不执行代码块，清理 HTML |

---

## 🚀 安装与使用

### 快速安装

```bash
# 方式 1：通过 ClawHub
npx skills add jimliu/baoyu-skills

# 方式 2：注册为插件市场
/plugin marketplace add JimLiu/baoyu-skills

# 方式 3：直接安装特定插件
/plugin install content-skills@baoyu-skills
```

### 使用示例

```bash
# 生成小红书图文
/baoyu-xhs-images posts/article.md --style notion --layout dense

# 生成信息图表
/baoyu-infographic content.md --layout pyramid --style technical-schematic

# 生成漫画
/baoyu-comic source.md --art manga --tone warm --layout cinematic

# 翻译文章
/baoyu-translate article.md --to zh-CN --mode refined

# 发布到微信公众号
/baoyu-post-to-wechat 文章 --markdown article.md --theme grace
```

---

## 📊 项目特色总结

| 特色 | 说明 |
|------|------|
| **模块化设计** | 17 个独立技能，可单独安装使用 |
| **风格系统** | 多维度风格组合（风格×布局、类型×风格等） |
| **智能推荐** | 根据内容自动分析并推荐最佳配置 |
| **多平台支持** | 支持 7 个 AI 图像生成平台 |
| **浏览器自动化** | CDP 技术绕过反自动化检测 |
| **可扩展性** | 通过 EXTEND.md 自定义配置 |
| **中文友好** | 支持小红书、微信、微博等中文平台 |

---

## 📝 开发相关

### 代码风格

- TypeScript，无注释
- async/await
- 短变量名
- 类型安全接口

### 发布流程

使用 `/release-skills` 工作流，必须完成：
1. 更新 `CHANGELOG.md` + `CHANGELOG.zh.md`
2. `marketplace.json` 版本号递增
3. 更新 `README.md` + `README.zh.md`（如适用）
4. 所有文件一起提交后打标签

---

这是一个**功能丰富、设计精良**的 Claude Code 插件集合，特别适合内容创作者、技术写作者和社交媒体运营者使用。项目的模块化设计和多平台支持使其具有很高的实用价值和扩展性。