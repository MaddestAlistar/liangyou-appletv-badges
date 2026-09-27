# V12 · Atmos、音轨与新增组合

2026-09-26。基于已发布提交 `758d450e11c7b75cb5a1d150f277c57c18375aa3`，继续处理用户反馈。

## 已复现的漏识别

| 输入示例 | V11 漏掉的内容 | V12 |
| --- | --- | --- |
| `TrueHD7.1Atmos` | Atmos 连写在数字后，缺单词边界 | Atmos＋TrueHD＋7.1 |
| `DDP5.1Atmos`／`EAC3JOC` | Atmos／JOC 连写 | 显示 Atmos，DD+ 让位 |
| `MLP FBA 16-ch` | 没有识别 TrueHD 的附加特征 | Atmos＋TrueHD；不把 16-ch 当作扬声器布局 |
| `HasAtmos=true` | 布尔键名不是单独的 Atmos 单词 | 接受明确正值；False 不作为正值线索 |
| `Language=eng` | 旧规则要求 Audio 前缀或整段只有一个语言名 | 英语音轨 |
| `English - TrueHD - 7.1` | 未覆盖音轨标题格式 | 英语音轨、TrueHD、7.1 |
| `中文 / English`／`中英双语` | 未覆盖独立列表与双语标签 | 中英音轨 |
| `Audio: Cantonese`／`yue-Hant-HK` | 缺少粤语及地区别名 | 归入中文音轨 |
| 同一 JSON 内英语 Audio＋日语 Subtitle | 没有按对象识别 Language | 仅英语音轨 |

同时补充 TrueHD／DD+ 加正数动态对象计数的强线索。普通 TrueHD7.1、普通 DDP5.1／7.1、4K 本身仍不代表 Atmos。原先按需求保留的 DV＋DD+5.1／7.1 兼容推断继续存在，明确 Atmos=False 会阻止这条弱推断。

修复音轨标题、字段、JSON Audio 对象和 MediaInfo Audio 分段时，保留字幕排除。语言声明可以是代码、地区代码、简繁中文、英语、日语、韩语；只有字幕语言或未知语言时，不虚构音轨。

### 技术依据

- [MediaInfo 维护者说明](https://github.com/MediaArea/MediaInfo/issues/286)：TrueHD 的 `Format_AdditionalFeatures=16-ch` 用于区分 Atmos，单纯 TrueHD 没有该特征。Title 是用户输入，仍可能被错误标记。
- [Jellyfin MediaStream 源码](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Entities/MediaStream.cs)：Language 与 DisplayTitle 是不同形式的信息，音轨标题会包含语言与音频信息。这用于构造兼容场景，不代表已确认某款播放器传入完整 Jellyfin JSON。

## 六种新组合的分配顺序

1. 良友4K＋WEB-DL／1080P＋WEB-DL 优先占用对应分辨率与 WEB-DL 来源；不再重复显示 WEB-DL＋音频。音频保留单项或进入另一个有效组合。
2. 1080P＋SDR 仅在 1080P 未合入 WEB-DL 时合成；720P＋SDR 独立判断。必须有明确 SDR，HDR／DV 不回退为 SDR。
3. 现有片源＋音频组合继续优先：TrueHD 已用于 UHD REMUX／Blu-ray 等组合时，不再用于 DV／HDR10 组合。
4. DV 未用于 DV+Atmos，且 TrueHD 未用于其他组合时，显示 DV +TrueHD；副标题为「杜比视界+TrueHD」。HDR10 与可用 TrueHD 同理。HDR10+ 不降为 HDR10。

新图形以现有分辨率、Dolby Vision 和 HDR10 SVG 为模板，保留图标、良字角标和比例。良友4K WEB-DL、DV +TrueHD、HDR10 TrueHD 为橙框；1080P WEB-DL／SDR 为紫框；720P SDR 为蓝框。PNG 960×288，SVG 320×96，字体转轮廓。

九种平台仅将边框换成黑色，保留原有图标和文字。规则与分组中，平台位于视频编码／帧率之后、音轨语言之前，语言分组最后。

新组合和平台样式用于复杂版。EplayerX 同步公共音频识别修复，保留其原有简洁图形集；复杂版单项备用包同步规则和平台黑框，保持单项用途。

## 验证与界限

479 个场景，在复杂版、EplayerX、单项复杂版、EplayerX PNG 四个变体，以及 Python／ICU／ECMAScript 三个引擎中进行 5,748 次完整结果对比。验证实际交付 JSON、全部别名、同文本去重、组合冲突、排序、图片解码、文字标签、黑框颜色及长输入耗时。详情见 [测试报告](portable-validation-v12.json)。

没有读取用户私人服务器或在其设备上实测。上述结果证明所列规则缺口及修复，不证明播放器一定传来这些字段。跨候选取并集仍可能让组合与单项共存；没有语言／Atmos 元数据时，静态徽章 JSON 不能恢复它们。所有合并判断都以同一个候选文本为范围。
