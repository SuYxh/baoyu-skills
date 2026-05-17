---
name: ls-house-updating-bam
description: 当用户需要更新或同步 BAM (API 管理平台) 接口定义时使用。触发条件包括提到 "bam update"、"更新一下 bam" 或粘贴包含 "cloud.bytedance.net/bam/rd/" 的 BAM 链接。这个技能将自动探测项目中的 bam.config.js 位置，解析链接中的 PSM 和版本号，更新配置文件，并在正确目录下执行 bam 命令来拉取最新接口文件。
---

# BAM 代码生成器技能

本技能自动化通过 BAM 平台更新前端 API 定义的过程，适用于任意包含 `bam.config.js` 的项目。

## 何时使用此技能

- 用户提供了 BAM 文档链接（例如，`https://cloud.bytedance.net/bam/rd/...`）
- 用户要求更新 BAM 接口（例如，"bam update"、"更新一下 bam"、"拉一下 bam 接口"）

## 前置步骤：自动探测 bam.config.js

每次触发此技能时，首先执行以下探测流程：

1. **搜索配置文件：**
   - 使用 Glob 工具搜索项目中的 `**/bam.config.js`（排除 `node_modules`）。
   - 如果找到 **1 个**，直接使用该文件。
   - 如果找到 **多个**，使用 AskUserQuestion 工具让用户选择要操作的配置文件。
   - 如果 **未找到**，告知用户当前项目中没有 `bam.config.js`，并询问是否需要初始化。
2. **确定执行目录：**
   - 以找到的 `bam.config.js` 所在目录作为执行目录（后续称为 `<config_dir>`）。
   - 后续所有命令均在 `<config_dir>` 下执行 `npx bam update`。

## 工作原理

根据用户的输入，工作流有两种主要场景：

### 场景 1：用户提供了 BAM 链接（新增/更新 PSM）

如果用户提供了类似这样的链接：
`https://cloud.bytedance.net/bam/rd/<psm>/api_doc/show_doc?version=<ver>&cluster=default`

1. **解析链接：**
   - 从 URL 路径中提取完整的 PSM 字符串（例如路径 `/bam/rd/some.team.service_name/api_doc/...` 中的 `some.team.service_name`）。
   - 通过取 PSM 字符串的最后一段（最后一个 `.` 之后的部分）作为配置键（即短服务名）。
   - 提取目标版本或分支：
     - 优先检查查询参数中的 `api_branch`。注意，URL 中的分支名通常是 URL 编码的（例如，`api_branch=feat%2Fmember_combine`），因此必须对其进行解码（例如，`feat/member_combine`）。
     - 如果没有 `api_branch`，则检查 `version`（例如，`version=1.0.81`）。
     - 目标标识是解码后的分支名或版本号。
2. **更新配置（风格自适应）：**
   - 读取探测到的 `<config_dir>/bam.config.js`。
   - **先观察已有** **`services`** **的配置风格**，不同项目的写法差异很大，常见风格包括但不限于：

     **风格 A — 简单字符串值，键为短服务名：**
     ```js
     services: {
       merchant_bff: 'life_service.fangchan.merchant_bff@1.0.607',
       quanyong_api: 'life.fangchan.quanyong_api@feat/some_branch',
     }
     ```
     **风格 B — 对象值（含局部配置），键为完整 PSM：**
     ```js
     services: {
       'life.fangchan.leads_api': {
         psm: `life.fangchan.leads_api@${BRANCH_MAP[process.env.BUILD_TYPE || 'offline']}`,
         generate: {
           injectResponseWrapperType: "import type { LifeRW as RW } from '@/main/utils/request'",
         },
       },
     }
     ```
     也可能存在其他混合写法。
   - **新增或更新条目时，必须遵循当前文件已有的风格：**
     - 观察已有条目的键名格式（短服务名 vs 完整 PSM）。
     - 观察已有条目的值格式（纯字符串 vs 对象）。
     - 如果文件中有环境变量分支映射（如 `BRANCH_MAP`），评估是否需要沿用同样的模式。
     - 新增/更新条目时，保持与已有风格一致。
   - 如果已有风格是简单字符串，值格式为 `[full_psm]@[version_or_branch]`。
   - 如果已有风格是对象，保持对象结构，仅修改 `psm` 字段中的版本/分支部分。
   - **如果无法确定应采用哪种风格，使用 AskUserQuestion 让用户选择。**
   - 保存文件。
3. **执行同步命令：**
   - 切换目录到 `<config_dir>`。
   - 在后台执行 `npx bam update`（使用 Bash 工具的 `run_in_background: true` 参数），以免阻塞后续任务。
   - 使用 `BashOutput` 工具定期检查后台命令的输出或在其完成时检查。
   - 命令完成后，告知用户执行结果（成功或遇到的任何错误）。

### 场景 2：用户只是要求更新 BAM / 拉取 IDL（未提供链接）

如果用户说 "bam update"、"拉一下 bam 接口" 或类似内容而没有提供具体链接：

1. **直接执行同步命令：**
   - 切换目录到 `<config_dir>`。
   - 在后台执行 `npx bam update`（使用 Bash 工具的 `run_in_background: true` 参数），以免阻塞后续任务。
   - 使用 `BashOutput` 工具定期检查后台命令的输出或在其完成时检查。
   - 命令完成后，告知用户执行结果（成功或遇到的任何错误）。

## 重要规则

- **不要自行安装 bam 相关依赖**。使用项目中已有的依赖。
- **始终在** **`bam.config.js`** **所在目录内运行** bam 命令。
- 解析链接时，确保提取短服务名（PSM 路径中最后一个点之后的所有内容）以与 `bam.config.js` 中的键匹配。注意键也可能是完整 PSM，需同时检查两种匹配方式。
- **新增或修改** **`services`** **条目时，必须先阅读已有条目的风格，保持一致。** 不要假设固定格式。
- 提取分支名时，解码任何 URL 编码组件（如 `%2F` 到 `/`）。
- 如果项目中存在多个 `bam.config.js`，务必让用户确认要操作哪一个。

