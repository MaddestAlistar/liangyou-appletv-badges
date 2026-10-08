# OopsPlayer BF3：SDR 组合后重复单项

2026-10-08

## 观察与复现

用户播放页截图同时出现「1080P SDR」组合和独立 SDR，后面还有 AAC、2.0、HEVC 和音轨语言组合。

在 BF2 中，单条完整输入 `1080p SDR AAC 2.0 HEVC 中英日韩音轨` 只产生 SDR 组合，不产生独立 SDR。但把它与独立的 `SDR` 字段分别匹配、再取并集，就会补出独立 SDR。完整分辨率／SDR 隐藏标记与孤立 SDR 标记也能复现同类问题。截图没有实际候选字段抓包，因此这是与截图一致的复现机制，不是客户端内部行为的直接证明。

## 调整范围与取舍

BF3 只为 `ly12-sdr` 增加「同一条匹配输入含分辨率」的条件。相较 BF2，其余 165 条过滤项逐条一致，包括上一轮 WEB-DL 修复；全部组合条件、图案、名称、颜色、分组和顺序保持不变。原版 all12、其他播放器配置和图片均不修改。

| 输入情况 | BF3 显示 |
| --- | --- |
| 1080P＋SDR | 1080P SDR 组合 |
| 720P＋SDR | 720P SDR 组合 |
| 上述完整输入，再附加孤立 SDR 字段或标记 | 不再额外补出独立 SDR |
| 4K＋SDR | 良友4K、独立 SDR |
| 1080P／4K＋WEB-DL＋SDR | 分辨率＋WEB-DL 组合、独立 SDR |
| 720P＋WEB-DL＋SDR | 720P SDR 组合、独立 WEB-DL，或原有 WEB-DL＋音频组合 |
| 576P／480P＋SDR | 分辨率、独立 SDR |
| HDR／HDR10／HDR10+／HLG／DV 与 SDR 同时出现 | 沿用原画面优先级，不补 SDR |
| 只有 SDR、没有分辨率 | 不显示独立 SDR；这是本次调整的明确取舍 |

没有分辨率的 `SDR AAC` 只保留 AAC；如果客户端仅提供孤立 SDR 而没有任何完整输入，配置也无法确认 SDR 是否已经用于某个组合，因此会省略这枚单项。无状态正则不能既保留全部孤立字段回退，又保证跨任意输入全局去重。解决任意冲突仍需要客户端先合并事实，或在合并徽章后去除已经包含的单项。

## 验证

- 287 项 SDR 专项检查：普通文本、七位标记、标记顺序、9 种换行／分隔方式、36 组完整与不完整候选组合、合法 SDR 单项及 HDR／DV 互斥。
- 重跑 473 项 WEB-DL 专项检查，确认上一轮修复保留。
- 7,447 组整包有序对照全部通过，非预期差异为 0。31 组文本、57 组标记按 BF3 策略移除了无分辨率 SDR；WEB-DL 的预期移除仍为 67 组文本、104 组标记，其余结果与原 all12 一致。
- BF2→BF3 只有 SDR 的正则变化；四份 OopsPlayer 导入入口内容一致，原 all12 哈希保留。
- 共 166 条物理过滤项、161 枚逻辑徽章；最长 3,963 字符、4,095 UTF-8 字节，均未超过 4096。

[SDR 专项报告](oopsplayer-sdr-validation.json) · [整包回归报告](oopsplayer-validation.json) · [WEB-DL 专项报告](oopsplayer-webdl-validation.json)

验证为本地 ICU 规则测试，BF3 仍需用户重新导入后在相同片源上实测。

## 导入

https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.BF3.json

重新导入并选中 BF3。`OopsPlayer.json`、`OopsPlayer.BF1.json` 和 `OopsPlayer.BF2.json` 同步为相同内容；不要混用多份旧配置验证去重。配置名额不足时，可先删除旧诊断包。
