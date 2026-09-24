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
