---
name: baoyu-compress-image
description: 将图片压缩为 WebP（默认）或 PNG 格式，自动选择最佳工具。当用户要求"压缩图片"、"优化图片"、"转换为 webp"或缩小图片文件大小时使用。
version: 1.56.1
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-compress-image
    requires:
      anyBins:
        - bun
        - npx
---

# 图片压缩工具

使用最佳可用工具压缩图片（sips → cwebp → ImageMagick → Sharp）。

## 脚本目录

脚本位于 `scripts/` 子目录中。`{baseDir}` = 此 SKILL.md 的目录路径。解析 `${BUN_X}` 运行时：如果安装了 `bun` → `bun`；如果有 `npx` → `npx -y bun`；否则建议安装 bun。将 `{baseDir}` 和 `${BUN_X}` 替换为实际值。

| 脚本 | 用途 |
|------|------|
| `scripts/main.ts` | 图片压缩 CLI |

## 偏好设置（EXTEND.md）

按优先顺序检查 EXTEND.md — 找到的第一个生效：

| 优先级 | 路径 | 范围 |
|--------|------|------|
| 1 | `.baoyu-skills/baoyu-compress-image/EXTEND.md` | 项目级 |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-compress-image/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-compress-image/EXTEND.md` | 用户主目录 |

如果未找到，使用默认值。

**EXTEND.md 支持**：默认格式、默认质量、保留原文件偏好。

## 使用方法

```bash
${BUN_X} {baseDir}/scripts/main.ts <input> [options]
```

## 选项

| 选项 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `<input>` | | 文件或目录 | 必填 |
| `--output` | `-o` | 输出路径 | 同路径，新扩展名 |
| `--format` | `-f` | webp, png, jpeg | webp |
| `--quality` | `-q` | 质量 0-100 | 80 |
| `--keep` | `-k` | 保留原文件 | false |
| `--recursive` | `-r` | 处理子目录 | false |
| `--json` | | JSON 输出 | false |

## 示例

```bash
# 单文件 → WebP（替换原文件）
${BUN_X} {baseDir}/scripts/main.ts image.png

# 保持 PNG 格式
${BUN_X} {baseDir}/scripts/main.ts image.png -f png --keep

# 递归处理目录
${BUN_X} {baseDir}/scripts/main.ts ./images/ -r -q 75

# JSON 输出
${BUN_X} {baseDir}/scripts/main.ts image.png --json
```

**输出**：
```
image.png → image.webp (245KB → 89KB, 64% reduction)
```

## 扩展支持

通过 EXTEND.md 自定义配置。路径和支持的选项见上方**偏好设置**部分。
