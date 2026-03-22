![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/sc9vl5waw2qKlFKR58ia9sSku3iahbOicybRQicKCn3nibQYSZjqL1jCctAt14XCpkD2eWlhok1avuZhZyPZmbUd1mQzFVdOoicZCSc8FkzAIGeGE/0?wx_fmt=jpeg)

让 AI 拥有"肉身"：这个开源项目用 50 行代码实现了 AI 自拍
===================================

原创 小张 小张 [老码小张](javascript:void\(0\);)

在小说阅读器中沉浸阅读

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/sc9vl5waw2oFEIaoDXcsF7Fp4KTwoibKuRIMIF8gvZrXFWlRAS5iclaIbXP92ia2HoiaTWziaXsTHrPCybiaEtxoI6NGKZXoSdzLyK4Js3a9b0MmE/640?wx_fmt=png&from=appmsg)

你有没有想过一个问题：

当你跟 AI 聊天时，对方是一个"没有身体"的存在。你问它"在干嘛"，它只能说"我在等你的消息"；你让它"发张照片"，它只能说"抱歉，我没有这个能力"。

这种割裂感，让 AI 始终像一个工具，而不是一个"人"。

最近 GitHub 上出现了一个有意思的项目——**Clawra**，它用一种巧妙的方式，让 AI Agent 拥有了"自拍"能力：固定一张参考图，用 xAI 的图像编辑模型实时生成不同场景的照片，然后发送到你的聊天窗口。

一句话：**让 AI 有了"肉身"**。

* * *

### 所以，这个玩意它到底是什么？

本质上来说，**Clawra** 是 OpenClaw（一个开源 AI Agent 框架）的一个 Skill 插件。

它的核心功能是：

> 当用户说"发张自拍"、"你在干嘛"、"给我看看你穿这件衣服的样子"时，AI 会生成一张与请求相符的照片，并发送到聊天窗口。

  

  

支持的平台包括：Discord、Telegram、WhatsApp、Slack、Signal，几乎覆盖了所有主流聊天工具。

**项目地址**：https://github.com/SumeLabs/clawra

* * *

### 他其实有点技术亮点：固定参考图 + AI 编辑

很多人第一反应是：这不就是 AI 画图吗？

不完全是。

如果你用过 Midjourney 或 Stable Diffusion，就会知道一个问题：**每次生成的人物都不一样**。今天生成一个长发女孩，明天可能变成短发，后天可能变成另一个人。

这对于"AI 虚拟形象"来说是致命的——你总不能每次发照片都换一张脸吧？

Clawra 的解决方案非常聪明：

#### 1\. 固定一张参考图

项目使用一张固定的参考图片，托管在 CDN 上：

`https://cdn.jsdelivr.net/gh/SumeLabs/clawra@main/assets/clawra.png`

这张图就是 AI 的"脸"，永远不变。

#### 2\. 用 AI 编辑图片

然后，使用 xAI 的 **Grok Imagine** 模型（通过 fal.ai 调用）对这张参考图进行编辑。

注意，是**编辑**，不是**生成**。

编辑的好处是：保留原图的核心特征（脸、体型），只改变场景、服装、姿势。

这样就解决了"每次生成不一样"的问题。是不是比较巧妙，说破了其实就这样。或者所，脑袋和我一样聪明的你，应该不看源码都能想明白。

### 我们在仔细看看他的双模式设计：Mirror vs Direct

Clawra 设计了两种自拍模式：

模式

适用场景

示例

**Mirror**

（镜子自拍）

展示穿搭、全身照

"穿着圣诞帽的样子"

**Direct**

（直接自拍）

特写、场景照

"在咖啡厅的样子"

系统会根据用户输入的关键词自动选择模式：

`function detectMode(userContext) {   const mirrorKeywords = /outfit|wearing|clothes|dress|suit|fashion/i;   const directKeywords = /cafe|restaurant|beach|park|portrait|smile/i;      if (directKeywords.test(userContext)) return"direct";   if (mirrorKeywords.test(userContext)) return"mirror";   return"mirror"; // 默认   }`

这个设计很贴心——用户不需要了解技术细节，只管说人话，系统自动判断。

### 再来品味下其核心代码解析

整个流程分三步：

#### Step 1：构造 Prompt

根据用户输入和模式，生成给 AI 的指令：

``function buildPrompt(userContext, mode) {     if (mode === "direct") {       return `a close-up selfie taken by herself at ${userContext},                direct eye contact with the camera,                looking straight into the lens,                eyes centered and clearly visible,                not a mirror selfie,                phone held at arm's length,                face fully visible`;     }     return `make a pic of this person, but ${userContext}.              the person is taking a mirror selfie`;   }``

这里的 Prompt 设计很讲究：

*   • 明确指定"自拍"姿势
    
*   • 强调"眼神直视镜头"
    
*   • 区分镜子自拍和直接自拍
    

#### Step 2：调用 xAI Grok Imagine

`curl -X POST "https://fal.run/xai/grok-imagine-image/edit" \     -H "Authorization: Key $FAL_KEY" \     -H "Content-Type: application/json" \     -d '{       "image_url": "https://cdn.jsdelivr.net/.../clawra.png",       "prompt": "make a pic of this person, but wearing a cowboy hat...",       "num_images": 1,       "output_format": "jpeg"     }'`

听说，最近有很多免费的逆向的 xAI 的 API，这里分享1个了。

`baseUrl : http://104.250.139.178:10922/   密钥      sk-0czyC3eKjcRAighrvaWroLDWWmqEL2QAQa187uzWZ6reLuI2      支持模型      grok-2,grok-2-vision,grok-2-vision-1212,grok-3,grok-3-beta,grok-3-fast-beta,grok-3-mini,grok-3-mini-beta,grok-3-mini-beta-high,grok-3-mini-beta-low,grok-3-mini-beta-medium,grok-3-mini-fast-beta,grok-3-mini-fast-beta-high,grok-3-mini-fast-beta-low,grok-3-mini-fast-beta-medium,grok-4,grok-4-0709,grok-4-0709-search,grok-4-1-fast-non-reasoning,grok-4-1-fast-reasoning,grok-vision-beta,grok-code-fast-1,grok-beta,grok-4-fast-reasoning,grok-4-fast-non-reasoning`

返回值中包含编辑后的图片 URL。

#### Step 3：发送到聊天平台

`openclaw message send \     --channel "#general" \     --message "这是你要的照片~" \     --media "$IMAGE_URL"`

OpenClaw 会自动处理不同平台的差异，同一套代码可以发送到 Discord、Telegram、WhatsApp 等任何平台。

### 一键安装

Clawra 的安装体验做得非常好，一行命令搞定：

`npx clawra@latest`

这个命令会：

1.  1\. 检查 OpenClaw 是否已安装
    
2.  2\. 引导你获取 fal.ai API Key
    
3.  3\. 自动安装 Skill 到 `~/.openclaw/skills/`
    
4.  4\. 更新 OpenClaw 配置文件
    
5.  5\. 注入 AI 人设到 SOUL.md
    

完全不需要手动配置，对新手非常友好。

### 一些延伸思考

Clawra 这个项目让我想到一个更大的问题：

**AI 的"具身化"会是下一个趋势吗？**

现在的 AI 都是"无形"的——一个聊天框，一段文字。但人类是视觉动物，我们天生更容易对"有形象"的存在产生情感连接。

Clawra 用图片编辑的方式实现了"伪具身化"，这只是第一步。未来可能会有：

*   • 实时视频生成（AI 直播？）
    
*   • 3D 虚拟形象（结合 VR/AR）
    
*   • 机器人载体（真正的"肉身"）
    

从这个角度看，Clawra 虽然只是一个小项目，但它指向了一个很大的方向。

**如果你也在做 AI Agent 相关的项目，这个 Skill 的设计思路值得借鉴。**

代码不多，但思路很清晰。有时候，解决问题的关键不是写多少代码，而是找到那个最巧妙的切入点。