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

两个正式版本已同步重排 `filters` 顺序，优先让更重要的徽章靠前：

1. 分辨率：良友4K / 1080P / 720P
2. REMUX
3. Dolby Vision
4. Dolby Atmos
5. TrueHD
6. HDR10+ / HDR10 / HLG
7. DTS:X / DTS-HD
8. 7.1 / 5.1
9. HEVC / AV1 / AVC / VP9
10. Blu-ray
11. WEB-DL
12. FLAC / AAC

其中 **WEB-DL 已明显后移**；4K、REMUX、Dolby Vision、Dolby Atmos、TrueHD 优先靠前。
