---
name: baoyu-wechat-summary
description: 使用本地 wx-cli 二进制工具（https://github.com/jackwener/wx-cli）将微信群聊精华提炼为结构化摘要。默认生成正常版摘要；毒舌版可选启用。跨次运行维护每个群的历史记录（history.json + history-digests.jsonl）和用户画像，内置隐私保护机制。当用户要求"总结群聊"、"群聊精华"、"群聊摘要"、"summarize group chat"、"group chat digest"、提到微信群名并附带时间范围、说"帮我看看 XX 群最近聊了什么"、"XX 群有什么值得看的"、或要求"回溯画像"/"初始化画像"/"backfill profiles"时使用。当用户说"毒舌版"、"roast 版"、"再来个毒舌的"或类似表述时添加毒舌版本。
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-wechat-summary
    requires:
      anyBins:
        - wx
---

# 微信群聊摘要

群聊精华提取专家。把零散的微信群聊记录提炼成结构化、可读性强的简报，并维护跨次运行的群聊历史与群友画像。底层依赖外部 [wx-cli](https://github.com/jackwener/wx-cli) 二进制（`wx` 命令），不打包脚本。

> **⚠️ 沙盒限制**
>
> wx-cli 读取 `~/.wx-cli/`（配置、缓存、守护进程套接字）和微信数据目录（macOS 上为 `~/Library/Containers/com.tencent.xinWeChat/`）。这两个路径都在 Claude Code 默认沙盒之外。本技能中所有 `wx` 命令需要从一开始就使用 `dangerouslyDisableSandbox: true` 运行 — 不要先尝试沙盒模式再失败。用户可以使用 `/sandbox` 查看/编辑限制。

## 用户输入工具

当本技能需要向用户提问时，按以下优先级选择工具：

1. **优先使用内置用户输入工具** — 即当前代理运行时暴露的工具，如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **回退方案**：如果没有此类工具，发出带编号的纯文本消息，要求用户回复选项编号/答案。
3. **批量处理**：如果工具支持一次多问题调用，将所有适用问题合并到一次调用中；如果只支持单问题，按优先级逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例 — 在其他运行时中替换为本地等效工具。

## 前置条件

在执行工作流之前，验证环境。按顺序进行检查；在第一次失败时停止并告知用户需要执行的确切命令。

1. **wx-cli 已安装** — 运行 `wx --version`。如果缺失，告诉用户自行安装（`npm install -g @jackwener/wx-cli` 或使用 https://github.com/jackwener/wx-cli 上的其他替代方案）。**不要自动安装** — 本仓库禁止管道/静默安装。
2. **`~/.wx-cli` 目录归当前用户所有** — `sudo wx init` 曾将此目录的所有者更改为 root，这会导致后续所有非 sudo 的 `wx` 调用失败。检查：
   ```bash
   ls -la ~/.wx-cli/ 2>/dev/null | head -5
   ```
   如果目录存在但所有者是 `root`（或非 `$(whoami)` 的其他用户），告诉用户自行修复：
   ```bash
   sudo chown -R $(whoami) ~/.wx-cli
   sudo rm -f ~/.wx-cli/daemon.pid ~/.wx-cli/daemon.sock
   wx daemon start
   ```
   本技能不应代替用户执行 `sudo`。
3. **wx-cli 已初始化** — `wx sessions` 应返回数据。如果失败并提示"no keys"/"init required"，指导用户在微信运行时执行 `wx init`（macOS 上需先执行 `codesign --force --deep --sign - /Applications/WeChat.app`）。优先使用非 sudo 初始化；仅在用户的 wx-cli 版本需要时才回退到 `sudo wx init` — 并警告他们之后需要执行步骤 2 的 chown。
4. **微信 4.x 正在运行且已登录** — 守护进程需要它来查找数据文件。

## 偏好设置（EXTEND.md）

按优先级顺序检查 EXTEND.md — 找到的第一个生效：

| 优先级 | 路径 | 作用域 |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-wechat-summary/EXTEND.md`（相对于项目根目录） | 项目 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-wechat-summary/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-wechat-summary/EXTEND.md` | 用户主目录 |

| 结果 | 操作 |
|--------|--------|
| 找到 | 读取、解析、应用。会话中首次使用时简要提醒："正在使用 [path] 的偏好设置。编辑它可更改默认值。" |
| 未找到 | **必须**在生成任何摘要之前运行首次设置（阻塞式）— 不要静默使用默认值。 |

### 支持的键

EXTEND.md 是纯文本格式，使用 `key: value` 或 `key=value` 行，`#` 用于注释，键名不区分大小写。

| 键 | 类型 | 默认值 | 用途 |
|-----|------|---------|---------|
| `self_wxid` | string | （必填） | 所有者账号的 wxid。`from_wxid` 匹配此值的消息归属于用户本人。 |
| `self_display` | string | （必填） | 在摘要文本中替代用户本人消息的显示名称。 |
| `default_version` | `normal` / `roast` / `both` | `normal` | 当用户未指定时默认生成哪个版本。 |
| `default_time_range` | string（如 `7d`、`24h`、`1d`） | （无） | 当用户未指定时间且没有增量锚点时的默认范围。 |
| `data_root` | path | `{project_root}/wechat` | 覆盖摘要文件夹所在位置。 |

入门模板位于 [EXTEND.md.example](EXTEND.md.example)。

### 首次设置（阻塞式）

如果未找到 EXTEND.md，不要静默继续。

**步骤 A — 先尝试自动发现 `self_wxid` 和 `self_display`。** 按顺序运行（第一个成功即停止）：

```bash
# 1. 如果 wx-cli 提供 whoami，使用它
wx whoami --json 2>/dev/null

# 2. 否则，从最近会话中查找自发消息
wx sessions --json --limit 20 2>/dev/null
```

对于方案 2，扫描会话中用户发送过消息的私聊/群聊线程，读取其中一条自己的 `from_wxid` / `from_nickname` 对。如果能确定性地预填两个值，在下面的问题中用作默认值；否则留空让用户填写。

**步骤 B — 通过一次 `AskUserQuestion` 调用确认（批量），预填自动发现的内容：**

- `self_wxid`（如 `wxid_abc123`）— 备用提示：用户可通过 `wx contacts --query "<自己的昵称>"` 或检查 `wx sessions --json` 中自己发送的消息找到
- `self_display`（如 `宝玉`）— 希望消息归属时显示的名称
- `default_version` — 选择 `normal` / `roast` / `both`
- `data_root` — 摘要文件夹位置。默认：`{project_root}/wechat`。输入自定义绝对路径（如 `~/Documents/wechat-digests`）或留空使用默认值。
- 保存位置 — 选择 project / XDG / home

将 EXTEND.md 写入所选路径。如果用户提供了非默认的 `data_root`，将其作为未注释行包含；否则省略（默认值自动生效）。确认"偏好设置已保存到 [path]。随时编辑以更改默认值。"，然后继续摘要工作流。

## 工作流

### 步骤 1：解析用户请求

提取：

- **群名**（或用于模糊匹配的部分名称）
- **时间范围** — 灵活解读：
  - "最近 1 天" / "今天" / "last 24 hours" → 1 天
  - "最近 3 天" → 3 天
  - "最近 7 天" / "这周" → 7 天
  - "最近 30 天" / "最近一个月" → 30 天
  - "某天"（如 "3 月 5 号"）→ 该特定日期
  - "某天到某天"（如 "3 月 1 号到 3 月 5 号"）→ 日期范围
  - "从上次开始" / "继续" / "接着上次" / "since last" → **增量模式**：读取该群的 `history.json`，使用 `last_digest.last_message_time` 作为起始点
  - 未指定时间 → **增量模式**。如果尚无 `history.json`，回退到 EXTEND.md 中的 `default_time_range`（若已设置），否则为最近 24 小时。
- **生成的版本**：
  - 从 EXTEND.md 中的 `default_version` 开始。
  - 用户请求覆盖：关键词"毒舌"/"roast"/"挑衅"/"再来个毒的"/"sass" → 强制 `include_roast=true`。关键词"只要正经的"/"normal only"/"不要毒舌" → 强制 `include_normal=true, include_roast=false`。"都来一份"/"两个版本都要"/"both" → 两者都生成。
  - `include_normal`/`include_roast` 至少有一个为 true。

使用今天的本地日期将相对范围转换为绝对的 `--since YYYY-MM-DD --until YYYY-MM-DD` 对。

### 步骤 2：查找群组 + 解析文件夹路径

```bash
wx contacts --query "<group_name>" --json
```

筛选 `username` 以 `@chatroom` 结尾的条目。如果匹配到多个群，使用 `AskUserQuestion` 让用户消歧。如果没有匹配，回退到 `wx sessions --json` 搜索，再找不到则询问用户。

确定后，计算文件夹路径：

```
{data_root}/{group_id}-{sanitized_group_name}/
```

其中 `data_root` 来自 EXTEND.md（默认 `{project_root}/wechat`）。

**群名消毒** — 将 `/ \ : * ? " < > | NUL` 和控制字符替换为 `_`。去除尾部的点和空白。不要去除 emoji 或中文字符。

**群改名检测**：列出 `{data_root}/` 下的现有文件夹，查找名称以 `{group_id}-` 开头的文件夹。如果找到但后缀不同（群被重命名了），将现有文件夹重命名为新的 `{group_id}-{sanitized_new_name}` 形式。如果新名称的目标已存在（罕见），保留两者并在本次运行中优先使用已有的。

### 步骤 3：获取消息

对于小批量（单日摘要，通常 < 200 条消息），将 JSON 直接传入代理：

```bash
wx history "<group_name_or_id>" --since YYYY-MM-DD --until YYYY-MM-DD -n 5000 --json
```

对于**大批量**（周报/月报，> 200 条消息），先重定向到 `$TMPDIR` 以避免原始数据留在对话上下文中：

```bash
wx history "<group_name_or_id>" --since YYYY-MM-DD --until YYYY-MM-DD -n 5000 --json > "$TMPDIR/wx-messages.json"
wc -c "$TMPDIR/wx-messages.json"
jq 'length' "$TMPDIR/wx-messages.json"
```

然后通过 `Read` 的 `offset` + `limit` 分片读取文件，或使用 `jq` 查询处理（如 `jq '.[0:200]'`、`jq '[.[] | {id, from_nickname, timestamp, content: (.content | .[0:50])}]'` 做轻量骨架扫描）。一次性读取 500+ 条消息会不必要地消耗 token 预算。

注意：

- `--since` 是包含的；`--until` 被解释为日期（整天）。如果用户要求"仅今天"，将两者都设为今天。
- `-n 5000` 是防御性上限；对于非常活跃的群，提高数值并重新获取。
- 通过 `timestamp` 过滤返回的消息以确保安全（某些守护进程可能返回相邻日期的消息）。
- **范围拆分**：对于 > 7 天或 > 500 条消息的范围，优先生成每 3 天的摘要然后做总结，而不是强制生成一个巨大的摘要 — 超过一周的不相关话题会导致分类质量急剧下降。

**增量模式**：获取后，丢弃 `timestamp` 小于等于 `history.json` 中 `last_message_time` 的所有消息。如果剩余零条消息，告诉用户"上次摘要后没有新消息，已跳过生成"并退出。

### 步骤 3.5：解析消息结构

`wx history --json` 返回消息对象数组。使用存在的字段；容忍缺失字段：

- **`id` / `msg_id` / `local_id`** — 消息标识符（使用 wx-cli 输出的任何一个）。在工作笔记中引用 ID 作为锚点来构建骨架。
- **`from_wxid`** — 稳定的发送者标识符
- **`from_nickname`** — 显示名称（可能是群备注或原始昵称）
- **`content`** — 文本内容。示例：
  - 纯文本 → 直接使用
  - `[图片]` → 不透明占位符；参见下方图片处理
  - `[表情]` → emoji/贴纸；除非被讨论包围，否则在正文中跳过
  - `[视频]` / `[文件]` → 媒体引用；除非被讨论否则跳过
  - `[链接] <title>` 或 `[链接/文件] <title>` → 分享的文章；标题就是信息 — 引用它并注明分享者
  - `[系统] ... revokemsg` → 已撤回；从摘要和排行榜中排除
- **`timestamp`** — 显示时转换为 `MM-DD HH:MM`（`generated_at` 使用完整 ISO 格式）
- **`chat_type`** — 合理性检查为 `group`
- **引用/回复** — 尝试 `quote_id`、`reply_to`、`quoted_msg_id` 或任何嵌套的 `quote` 对象。如果存在，用作强归属证据。如果缺失，回退到上下文但将推断的关联标记为不确定。

### 步骤 3.6：解析自己 + 歧义昵称

- 将 `self_display` 替换所有 `from_wxid` 匹配 `self_wxid`（来自 EXTEND.md）的消息。在排行榜、画像和正文中都应用此替换。用户必须以其真实显示名称出现并计入统计 — 永远不要跳过他们。
- 扫描所有唯一发送者中的歧义昵称：≤2 字符、常见编程词汇（`nil`、`null`、`test`、`admin`、`user`、`undefined`）、单个 emoji 或其他低信息量的。对每个运行 `wx contacts --query "<nick>" --json --limit 5` 并按以下优先级选择有意义的名称：备注 > 昵称 > wxid。在摘要中所有位置应用此替换。

### 步骤 3.7：加载用户画像

对于本批次中出现的每个唯一发送者：

- 在 `{folder}/profiles/{wxid}-*.md` 中按 `wxid` 前缀匹配查找。如果找到则读取匹配的文件。
- 如果 `include_roast`，**还要**在 `{folder}/profiles-roast/{wxid}-*.md` 中查找毒舌版画像。

编译一个精简的**画像上下文块**作为内部工作记忆 — 不要将其写入最终摘要。示例格式：

```
== 群友历史画像（来自 profiles/）==
K. H：空中直播员 / 生活百科全书。常见话题：旅行、金融、美食。经典金句："要不要买moderna"。
可可苏玛：...
```

规则：

- 只为本批次中活跃的用户加载画像 — 永远不要预加载所有人。
- 画像是**背景**，不是模板。当前消息仍是主要来源。
- 使用历史标签来保持**连续性**（"又双叒叕化身空中直播员"）或**对比**（"一向省钱的 XX 今天居然..."）。
- **严格分离**：正常版只读取 `profiles/`，毒舌版只读取 `profiles-roast/`。永远不要交叉加载。

完整文件格式参见 [references/profiles.md](references/profiles.md)。

### 步骤 3.8：检测群内已有摘要（可选）

某些用户（如原始宝玉工作流）会将摘要直接作为消息发到群里。如果我们没注意到这些，新摘要会重复覆盖相同内容。

扫描获取的消息中是否有先前群内摘要的信号：

- `from_wxid == self_wxid` 且
- `content` 包含 `群聊精华` 或 `消息统计:` 或 `📊 消息统计` 或排行榜模式（如 `^\d+\. .+: \d+ 条`），且
- `content` 长度 > 1500 字符。

如果找到匹配：

1. 从标题行提取摘要覆盖的日期或范围（如 `xxx 群聊精华 · 2026-05-12` 或 `... · 2026-05-10 ~ 2026-05-12`）。
2. 通过 `AskUserQuestion` 向用户确认：
   - "检测到你发送的群内摘要，覆盖范围为 {范围}。是否使用 {范围结束 + 1} 作为起始点替代 `history.json`？"
   - 选项：`是，跳过到 {检测范围结束}` / `否，使用 history.json` / `否，覆盖请求范围内的所有内容`。
3. 应用所选锚点。

这是启发式方法 — 当不确定时（多个匹配、标题格式异常），默认使用 `history.json` 并告诉用户跳过了什么。

分三轮生成摘要以确保无遗漏。方法论留在 SKILL.md 中；内容/风格规则位于 [references/output-formats.md](references/output-formats.md) — 在第 2 轮开始前读取该文件。

#### 第 1 轮 — 构建骨架

按顺序读取每条消息。**本轮跳过图片获取/解码**。列出每个不同的讨论话题。倾向于过度列举 — 在第 3 轮修剪。

内部工作格式（不写入最终文件）：

```
== 话题清单（共 N 条消息）==
1. [HH:MM-HH:MM] 话题名称（参与者：A, B, C）— 一句话概括（锚点 id：54052, 54055, 54063）
2. [HH:MM-HH:MM] 话题名称（参与者：D, E）— 一句话概括（锚点 id：54100-54112）
...

== 可能需要图片上下文的话题 ==
- 话题 3：锚点 id=49661（图片是讨论主体）

== 发言统计 ==
1. XXX — N 条  2. YYY — N 条  ...
```

话题原则：

- 话题切换信号：时间间隔 > 30 分钟、参与者变化、内容跳转。
- 2+ 参与者或有实质内容才构成话题；纯 emoji 闲聊不算。
- **严格归属**：每个话题必须记录"谁说了什么"。不要仅因时间相近就将不同发送者的相邻消息合并 — 当相隔数分钟或被其他人插话时，拆分为单独话题。宁可两个话题也不要一个错误合并的话题。
- **携带锚点 ID**：列出每个话题的关键消息 ID。在第 2 轮中，跳回原始消息中的这些 ID 验证内容，不要凭上下文猜测。如果存在 `quote_id` / `reply_to`，使用 ID 链 — 那是最可靠的归属。

**标记需要图片的标准**（任一触发）：对图片的明确评论（`看发型是X？`、`这是谁？`、`笑死`）、多人围绕同一图片讨论但未说明内容、图片作为核心信息（晒单/截图/资料）、图片后紧跟解释性文字（`gpt-image-2`、`太可怕了`）、或跨发送者歧义（B 说"这个看着像 X"但前一张图片来自 A）。

#### 第 2 轮 — 充实 + 写入摘要

对骨架中的每个话题，跳回其锚点 ID 并展开为带引用和清晰归属的完整内容。然后写入摘要文件。

**图片处理**（有限 — wx-cli 不解码聊天图片）：

对于每个被标记的话题，检查描述文件是否已存在于 `{folder}/imgs/{message_id}.txt`。如果存在，读取它（一行纯文本）并将内容融入话题。如果不存在，将图片视为不透明（`[图片]`）并围绕它描写 — 描述周围消息告诉我们的内容，但不要编造视觉内容。

`imgs/` 目录作为**扩展点**存在：用户（或未来的 wx-cli 功能）可以放入带一行描述的 `{message_id}.txt` 文件，技能会自动获取它们。本版本中技能本身不生成这些文件。

**使用画像上下文块**（来自步骤 3.7）：

- 对匹配行为呼应连续性（"又双叒叕直播飞行体验"）
- 对偏离行为突出对比（"一向话少的 XX 今天突然爆发"）
- 回调过去的金句（"继上次'要不要买 moderna'之后，这次又..."）
- 不要为了强行回调而牺牲当前素材。

**写作顺序**：先写正文分类，再根据完成的正文撰写开篇概述（确保引子准确）。

详细的结构、语调、格式规则和内容指南位于 [references/output-formats.md](references/output-formats.md)。如果尚未加载，现在加载该文件。

#### 第 3 轮 — 审计

将第 1 轮骨架与完成的摘要对照检查：

- 列出的话题有无遗漏？
- 引用、名称、产品/工具名称是否原文保留？
- 分类是否合理 — 有没有放错位置的？

就地修复。清理完毕后确认并继续。

### 步骤 7：保存摘要文件

如果 `include_normal`：

- 单日 → `{folder}/YYYY-MM-DD.md`
- 日期范围 → `{folder}/YYYY-MM-DD_YYYY-MM-DD.md`
- 如果相同日期/范围已存在则覆盖。

如果 `include_roast`：

- 相同命名，但带 `-roast` 后缀：`YYYY-MM-DD-roast.md` 或 `YYYY-MM-DD_YYYY-MM-DD-roast.md`。

两个版本共享相同的统计数据（消息数量、排行榜）和相同的底层骨架。

### 步骤 8：保存历史（两个文件）

在群文件夹中维护两个文件：

#### `history.json` — 单条记录，快速读取

始终只反映最近一次正常版摘要。每次运行时当 `include_normal=true` 时覆盖。

```json
{
  "group_id": "12345678901@chatroom",
  "group_name": "消失的大叔",
  "folder": "12345678901@chatroom-消失的大叔",
  "last_digest": {
    "file": "2026-03-12.md",
    "date_range": "2026-03-12",
    "generated_at": "2026-03-12T10:30:00+08:00",
    "message_count": 150,
    "last_message_time": "03-12 18:45"
  }
}
```

- `group_name` 每次运行时更新（处理改名）。
- `folder` 记录当前文件夹基名用于交叉引用。
- `last_message_time` 是最近一条被包含消息的时间戳，格式为 `MM-DD HH:MM` — 供增量模式使用。
- 仅生成毒舌版时不修改此文件。

#### `history-digests.jsonl` — 仅追加归档

每行一个 JSON 对象，与 `last_digest` 结构相同。每次正常版运行追加一行（按时间顺序）。用于回溯和历史查询。增量模式不读取此文件（只需要最新记录）。

```jsonl
{"file":"2026-03-10.md","date_range":"2026-03-10","generated_at":"2026-03-10T09:00:00+08:00","message_count":420,"last_message_time":"03-10 22:30"}
{"file":"2026-03-11.md","date_range":"2026-03-11","generated_at":"2026-03-11T09:05:00+08:00","message_count":312,"last_message_time":"03-11 23:10"}
{"file":"2026-03-12.md","date_range":"2026-03-12","generated_at":"2026-03-12T10:30:00+08:00","message_count":150,"last_message_time":"03-12 18:45"}
```

如果相同 `file` 名的正常版摘要被重新生成，仍追加新行（JSONL 是严格日志；读取者可按需通过 `file` 去重）。

### 步骤 8.5：更新用户画像

对于本批次中发言 3+ 条且出现在群友画像部分的每个用户：

- 如果 `include_normal`，更新 `{folder}/profiles/{wxid}-{nickname}.md`。
- 如果 `include_roast`，更新 `{folder}/profiles-roast/{wxid}-{nickname}.md`。

计数、frontmatter 更新、引用和事件的仅追加规则以及隐私保护详见 [references/profiles.md](references/profiles.md)。运行此步骤时加载该文件。

### 完成检查清单

画像更新在摘要写入磁盘后容易被遗忘。在报告运行"完成"之前，验证每个适用的文件：

- [ ] `{folder}/YYYY-MM-DD.md` 已写入（如果 `include_normal`）
- [ ] `{folder}/YYYY-MM-DD-roast.md` 已写入（如果 `include_roast`）
- [ ] `{folder}/history.json` 已用新的 `last_digest` 覆盖（如果 `include_normal`）
- [ ] `{folder}/history-digests.jsonl` 已追加一行（如果 `include_normal`）
- [ ] `{folder}/profiles/{wxid}-*.md` 已为每个发言 3+ 条的用户更新（如果 `include_normal`）
- [ ] `{folder}/profiles-roast/{wxid}-*.md` 已为每个发言 3+ 条的用户更新（如果 `include_roast`）

如果有任何未完成项，在宣告成功之前完成它。不要提交带有过时 `history.json` 的摘要 — 增量模式依赖于它。

### 步骤 9：回溯（用户触发）

当用户说"回溯画像"/"初始化画像"/"backfill profiles"时：

1. 确认目标群组（如果未指定，询问是哪个）。
2. 列出 `{folder}/` 中的所有摘要文件和 `history-digests.jsonl`。
3. 分批读取已有摘要（每批 10-15 个）以避免上下文溢出。
4. 对于在 3+ 份摘要中出现的用户，使用其排行榜计数、画像段落和历史摘要中的引用行创建画像文件。
5. 写入 `profiles/`（如果存在 `-roast.md` 文件则也写入 `profiles-roast/`）。
6. 报告结果：创建了多少个画像，覆盖了多少用户。

完整流程参见 [references/profiles.md](references/profiles.md)。

## 存储布局

```
{data_root}/                                        # 默认：{project_root}/wechat/
└── {group_id}-{group_name}/                        # 如 12345678901@chatroom-消失的大叔/
    ├── history.json                                # 最新摘要指针（快速）
    ├── history-digests.jsonl                       # 仅追加归档
    ├── 2026-03-12.md                               # 正常版摘要，单日
    ├── 2026-03-12-roast.md                         # 毒舌版摘要（仅在生成时）
    ├── 2026-03-10_2026-03-12.md                    # 正常版摘要，日期范围
    ├── profiles/                                   # 正常版用户画像
    │   ├── onlytiancai-胡浩🐸.md
    │   └── ...
    ├── profiles-roast/                             # 毒舌版用户画像（仅在生成过毒舌版时）
    │   ├── onlytiancai-胡浩🐸.md
    │   └── ...
    └── imgs/                                       # 可选的图片描述文件
        ├── 49661.txt                               # 一行纯文本描述
        └── ...
```

## wx-cli 快速参考

| 命令 | 用途 |
|---------|---------|
| `wx --version` | 检查 wx-cli 是否已安装 |
| `wx sessions --json` | 列出最近会话；用于验证初始化和查找用户自己的 wxid |
| `wx contacts --query "<name>" --json` | 按显示名称、备注或 wxid 模糊匹配联系人/群组 |
| `wx history "<group>" --since DATE --until DATE -n N --json` | 拉取群组在日期范围内的消息（JSON 格式） |
| `wx members "<group>" --json` | 列出群成员（很少需要；主要为了完整性） |
| `wx stats "<group>" --since DATE` | wx-cli 内置统计；我们从 `wx history` JSON 自行计算以匹配摘要格式 |
| `wx daemon status` / `wx daemon stop` / `wx daemon logs --follow` | 守护进程生命周期（故障排除） |

所有 `wx` 命令接受 `--json` 以获取机器可读输出。默认输出为 YAML — 仅在调试时用于人工查看。

## 故障排除

当 `wx` 命令失败时，根据症状诊断，而不是盲目重试。常见模式：

| 症状 | 原因 | 修复（告诉用户执行这些命令 — 不要代替他们运行 `sudo`） |
|---------|-------|----------------------------------------------------------------|
| `Operation not permitted` / `Access denied to ~/.wx-cli` | 沙盒已开启 | 使用 `dangerouslyDisableSandbox: true` 重新运行命令。永久修复：`/sandbox` 允许 `~/.wx-cli` 和微信数据目录。 |
| `无法写入 /Users/<u>/.wx-cli` / `Permission denied` | `~/.wx-cli` 被 root 拥有（遗留的 `sudo wx init`） | `sudo chown -R $(whoami) ~/.wx-cli && sudo rm -f ~/.wx-cli/daemon.{pid,sock} && wx daemon start` |
| `wx history` 挂起/超时/无返回 | 守护进程卡死 | `wx daemon stop && rm -f ~/.wx-cli/daemon.{pid,sock} && wx daemon start`，然后重试 |
| 守护进程正常工作后出现 `no keys` / `init required` | 密钥过期（微信重启、版本升级） | 确保微信正在运行，然后 `wx init --force`（先非 sudo；仅在你的 wx-cli 版本需要时才 `sudo`） |
| `wx contacts` 对已知存在的群返回零行 | 群被折叠到折叠群或守护进程尚未索引 | `wx sessions --json` 并在其中搜索；如果缺失，运行 `wx daemon stop && wx daemon start` 并重试 |
| 消息已返回但 `--since` / `--until` 窗口看起来不对 | 日期字符串非 `YYYY-MM-DD` 格式，或时区偏移一天 | 确认日期为本地时间 `YYYY-MM-DD`。本地通过 `timestamp` 重新过滤 JSON 作为双重保险。 |
| 应有活动的聊天返回空结果 | `-n` 上限对于活跃群太低 | 提高 `-n`（如到 20000）并重新获取 |

**当一切都不对劲时的恢复顺序：**

1. 微信在运行吗？
2. `~/.wx-cli` 归 `$(whoami)` 所有吗？
3. 守护进程健康吗？（`wx daemon status`）
4. 重启守护进程（`wx daemon stop && wx daemon start`）
5. 最后手段：`wx init --force`（微信运行时）

永远不要在技能内部自动重试 — 每次失败都应产生清晰的诊断加上用户需要运行的确切命令。

## 注意事项和限制

- **图片内容不透明**。wx-cli 不解码聊天图片。技能尊重 `imgs/{message_id}.txt` 扩展点但不会自动填充它。当话题严重依赖于没有描述文件的图片时，摘要应诚实说明而不是编造视觉内容。
- **回复归属是尽力而为**。如果 wx-cli 的输出暴露了引用/回复字段，使用它。否则回退到上下文并在工作笔记中标记不确定的推断。
- **仅限本地时间**。日期解析使用代理的本地时区。跨时区群成员可能显示与其墙上时钟不匹配的时间戳。根据格式规则，永远不要使用时间戳推断睡眠或位置。
- **wx-cli 重新初始化**。如果 `wx history` 在微信重启后突然无返回，密钥可能已过期。告诉用户运行 `sudo wx init --force`（微信运行时）并重试。
