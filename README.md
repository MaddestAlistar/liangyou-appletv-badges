# 良友科技学院 · Apple TV Badges

现在保留两套正式地址：

## Badge LiangYou Ver.all
复杂完整版，保持现有版本不变。

- 适配：**CapyPlayer / RovePlayer / Forward / Nuvio / Rex**
- 文件：`Badge LiangYou Ver.all.json`
- 地址：
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.all.json

## Badge LiangYou Ver.EPX
EplayerX 专用兼容版，基于之前可正常显示的 320×96 结构轻量优化。

- 保持双层细框和左上角「良」标识
- 左侧图标按各格式特点重新设计，但不使用复杂滤镜
- Dolby Vision 与 Dolby Atmos 统一使用紫色边框
- Dolby Vision 副标题：**杜比视界**
- Dolby Atmos 副标题：**杜比全景声**
- 适配：**EplayerX / Forward / RovePlayer / CapyPlayer / Rex**
- 文件：`Badge LiangYou Ver.EPX.json`
- 地址：
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.EPX.json

> EplayerX 优先使用 Ver.EPX；CapyPlayer / RovePlayer 可优先使用 Ver.all。

## 匹配规则优化

Ver.EPX 与 Ver.all 已同步增强媒体信息匹配，徽章外观不变。

- Dolby Atmos：新增 `JOC / E-AC-3 JOC / EAC3 JOC` 场景识别
- Dolby Vision：新增 `dvhe / dvh1` 等常见标识
- HDR10+：兼容 `HDR10+ / HDR10Plus / HDR10P`
- HEVC：新增 `hvc1 / hev1`
- AVC：新增 `avc1`
- AV1 / VP9：新增 `av01 / vp09`
- 5.1 / 7.1：新增 `6ch / 6 channels / 8ch / 8 channels`
- REMUX / Blu-ray / WEB-DL / 分辨率：扩展常见命名和分辨率写法

为减少误判，普通 `EAC3 / DD+` 不会直接当作 Atmos；只有明确出现 Atmos 或 JOC 时才显示 Dolby Atmos。

## 显示优先级

两个正式版本已改为按分组优先级控制显示顺序，避免 WEB-DL 因为属于 Source 组而长期排在第二位。

当前分组顺序：

1. Resolution：良友4K / 1080P / 720P
2. Master Source：REMUX
3. Video Tech：Dolby Vision / HDR10+ / HDR10 / HLG
4. Immersive Audio：Dolby Atmos
5. Audio Tech：TrueHD / DTS:X / DTS-HD / FLAC / AAC
6. Source：Blu-ray / WEB-DL
7. Channels：7.1 / 5.1
8. Video Codec：HEVC / AV1 / AVC / VP9

这样一部典型 4K 影片更容易按接近下面的顺序显示：

**良友4K → REMUX → Dolby Vision → Dolby Atmos → TrueHD → WEB-DL → 7.1/5.1 → HEVC**

其中 REMUX 已从 Source 组独立出来，WEB-DL 保留在普通 Source 组并整体后移。

## EplayerX 播放页兼容优化

参考 6otho/Epx-Badge 的 EplayerX 分组方式，Ver.EPX 已尽量改回 EplayerX 常见标准分组，减少“详情页能显示、进入播放页却不显示”的情况：

- Dolby Atmos：改入 `audio-tech`
- 5.1 / 7.1：改入 `audio-channels`
- REMUX / Blu-ray / WEB-DL：统一使用 `source`
- Dolby Vision / HDR：继续使用 `video-tech`
- `tagStyle` 统一为 `filled`

同时，Ver.EPX 与 Ver.all 的徽章主标题和副标题都会适度放大；Ver.all 的 PNG 由 premium SVG 自动重新渲染。

## EPX 播放页专项修复

针对 EplayerX 出现“详情页有徽章、进入播放页缺徽章”的情况，Ver.EPX 现采用兼容优先策略：

- Dolby Atmos：除 `Atmos / JOC` 外，播放页仅暴露 `EAC3 / E-AC-3 / DDP / DD+` 时也允许显示 Atmos 徽章，以提高播放页命中率。注意：少量普通 Dolby Digital Plus 资源可能因此被识别成 Atmos。
- 7.1：取消 `8ch / 8 channels` 推断，只在明确出现 `7.1` 时显示，避免部分 5.1 资源在播放页被误判成 7.1。
- 5.1：支持明确 `5.1` 以及 `6ch / 6 channels`。
- WEB-DL：增加 `WEBRip / AMZN / Netflix / Disney+ / ATVP` 等常见 WEB 来源标识，提高播放页命中率。
- Ver.EPX 改用新的 `Badge-LiangYou-Ver.EPX-v2` 图片目录，绕过旧 SVG 缓存。
- Ver.EPX 与 Ver.all 的主标题、副标题均再次放大；Ver.all 已重新渲染 PNG，并使用固定提交地址避免旧图片缓存。

## 2026-09-24 EPX v5 / Ver.all 细调

### Badge LiangYou Ver.EPX
- 切换到 `Badge-LiangYou-Ver.EPX-v5`，用于绕过旧 SVG 缓存。
- Dolby Vision / Dolby Atmos：左侧图标进一步左移，分隔线和文字区同步左移，减少右侧顶框。
- 所有已有第二行副标题由 20 提高到 22。
- 参考 6otho/Epx-Badge 的 EplayerX 写法，减少复杂正则和 lookbehind。
- HEVC / AVC 等 codec 匹配改成更接近 EplayerX 参考源的格式。
- HEVC 等视频编码提前参与匹配，降低播放界面因徽章数量限制而被后置丢弃的概率。
- 5.1 / 7.1 改为更严格、互不依赖 8ch 推断的规则，5.1 规则优先。
- DTS-HD MA 改为只在明确出现 MA / Master Audio 时匹配，避免普通 DTS-HD 被误标为 MA。
- 4K 增加对 1080P / 720P 的排除，降低多分辨率文本导致的误判。

### Badge LiangYou Ver.all
- 复杂版已有第二行副标题由 21 提高到 23。
- 良友4K 下方 `ULTRA HD` 向右微调，使视觉对齐更自然。
- 已重新渲染 PNG 并切到新的固定提交资源，避免旧 PNG 缓存。
- 同步收紧 5.1 / 7.1、DTS-HD MA、HEVC / AVC 与 4K 的匹配规则。

## EPX2 播放页兼容校正

对照 6otho/Epx-Badge、9mousaa/BetterFormatter、l3okuGmail/badges 后，对 EplayerX 播放页规则再次收紧：

- 新增 `Badge LiangYou Ver.EPX2.json`，用于绕过 EplayerX 对旧 JSON 地址的缓存。
- 5.1 / 7.1 不再用过宽的纯数字规则，避免把 `L5.1 / L7.1` 这类视频 Profile / Level 数字误判成声道。
- 7.1 不再用 `8ch` 推断，只有明确的 7.1 音频上下文才显示。
- HEVC 保留 `HEVC / H.265 / x265 / hvc1 / hev1`，并增加不含 AV1/VP9 时对 `Main 10` 的兼容回退。
- Dolby Atmos 收紧为 `Atmos / Dolby Atmos / JOC`，不再把普通 EAC3 / DDP 直接当 Atmos。
- 分组 ID 恢复为 EplayerX 参考配置常用的标准组：resolution / source / video-tech / video-codec / audio-tech / audio-channels。
- 6otho 与 l3oku 的公开配置都默认关闭 HEVC / AVC，BetterFormatter 也没有 codec 徽章；因此如果 EPX2 中 HEVC 仍只在资源卡显示、播放页不显示，基本可判断为 EplayerX 播放页没有提供 codec 文本，而不是 JSON 正则问题。

## EPX3 识别规则校正

对照 6otho/Epx-Badge、9mousaa/BetterFormatter 与 l3okuGmail/badges 后，进一步调整 EplayerX 播放页识别：

- 4K：补充 2160p / UHD / Ultra HD / 3840×xxxx / 4096×xxxx。
- HEVC：兼容 HEVC / H.265 / H265 / x265 / hvc1 / hev1 / Main 10，并把 HEVC/AV1/AVC/VP9 从 video-codec 组移入 video-tech，尝试绕过播放页对 video-codec 组的忽略。
- DTS-HD：保留 DTS-HD MA，并新增独立的普通 DTS-HD 规则与专用徽章，避免只有 “DTS-HD” 时不显示。
- Dolby Vision：兼容 Dolby Vision / DolbyVision / DoVi / DV / dvhe / dvh1。
- Dolby Atmos：兼容 Atmos / Dolby Atmos / JOC / E-AC-3 JOC / EAC3 JOC / DDP JOC；不把普通 EAC3 / DDP 直接当 Atmos。
- TrueHD：兼容 TrueHD / True HD / Dolby TrueHD / MLP FBA。
- 显示顺序调整为：分辨率 → REMUX → Dolby Vision → Dolby Atmos → TrueHD → DTS-HD → HDR → 声道 → HEVC/其他编码 → Blu-ray / WEB-DL。

新测试地址：
https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.EPX3.json
