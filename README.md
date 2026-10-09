# 良友徽章 · LiangYou Media Badges

由 **良哥看未来** 整理维护，把片源、分辨率、杜比与音轨信息变成直观的媒体徽章。

**[资源中心](https://maddestalistar.github.io/LiangYou-ResourceHub/)** · **[Telegram · 良友科技学院](https://t.me/liangyouuniversity)** · **[小红书 · 良哥看未来](https://xhslink.cn/o/9jFC2Fv0osJ)**

## 三个正式版本

| 版本 | 适用说明 | 导入地址 |
| --- | --- | --- |
| **简易版** | 原 EplayerX 版，SVG 简洁样式；EplayerX 首选。 | [复制 / 打开简易版 JSON](https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.EPX12.json) |
| **合成徽章版** | 原 OopsPlayer BF3 版；组合展示片源、杜比与音轨，保留 WEB-DL、SDR 重复显示修复。 | [复制 / 打开合成徽章版 JSON](https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.BF3.json) |
| **复杂版** | 原 V12 完整配置保持不变；适合支持完整规则格式的客户端。 | [复制 / 打开复杂版 JSON](https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.all12.json) |

2026-10-10 起统一使用以上三个版本名称；本次整理入口与说明，识别规则、图片和原订阅地址保持不变。旧版与诊断文件只作兼容或历史记录，不再作为额外版本推荐。

支持徽章的播放器包括 **EplayerX、OopsPlayer、Rex（Forward）、Roveplayer、Vidora、Capyplayer**。不同 App 的规则格式、图片支持与显示方式可能不同，请按所选版本说明导入；支持徽章不代表每个客户端都兼容所有配置。

## 使用方法

1. 在播放器中找到「徽章规则」或「自定义徽章」入口。
2. 选择上表一个版本，复制完整 JSON 地址并导入。
3. 启用所选配置，重新加载媒体信息；同一时间只启用一个徽章包，避免重复显示。

已经正常使用原地址的用户无需重新导入。简易版与合成徽章版只是统一展示名称，链接中的 `EPX12`、`OopsPlayer.BF3` 继续用于保持订阅兼容。

## 合成徽章示例

| 良友4K | UHD REMUX / TrueHD |
| --- | --- |
| ![良友4K](assets/2026-09-25-v9/all/png/4k.png) | ![UHD REMUX / TrueHD](assets/2026-09-25-compact-v10/all/png/combo-uhd-remux-truehd.png) |
| **DV + ATMOS** | **7.1 环绕声道** |
| ![DV + ATMOS](assets/2026-09-25-v9/all/png/combo-dv-atmos.png) | ![7.1 环绕声道](assets/2026-09-25-v9/all/png/71.png) |

徽章依次表达分辨率、片源、画面与声音信息。示例展示常见组合，实际数量与排版由媒体信息和播放器决定。

**常用顺序：** 分辨率 → REMUX / 片源 → 杜比与画面 → 音频格式 → 版本 → 声道 → 编码与位深 / 帧率 → 平台 → 音轨语言。

## 使用边界与反馈

- 徽章依据播放器提供的媒体信息匹配，不代表设备实际输出格式。
- 资料卡与播放页传入的字段不同，可能产生不同结果；缺失的元数据不能通过徽章配置恢复。
- 合成徽章版沿用 BF3 的 WEB-DL、SDR 回退策略：孤立字段不再补出已合成的单项，完整输入仍保留应显示的单项。详见 [WEB-DL 说明](reports/OOPSPLAYER-WEBDL.md)与 [SDR 说明](reports/OOPSPLAYER-SDR.md)。
- 反馈时请附 App 名称、版本、所选徽章包、片源信息与截图，可提交 Issue 或到 Telegram 交流。

<details>
<summary>维护、兼容入口与历史记录</summary>

旧编号、备用与诊断文件继续保留，供已添加的订阅及历史排查使用；新用户只需选择首页三个正式版本之一。

- 简易版：`Badge LiangYou Ver.EPX12.json`
- 合成徽章版：`Badge LiangYou Ver.OopsPlayer.BF3.json`
- 复杂版：`Badge LiangYou Ver.all12.json`

构建与规则验证方式见 [V12 历史技术记录](reports/README-v12-historical.md)。其中旧版名称、备用文件和当时的测试结论仅供维护参考。

[OopsPlayer 适配记录](reports/OOPSPLAYER.md) · [间距排查](reports/OOPSPLAYER-LAYOUT.md) · [V12 规则说明](reports/AUDIO-AND-COMBOS-v12.md)

</details>
