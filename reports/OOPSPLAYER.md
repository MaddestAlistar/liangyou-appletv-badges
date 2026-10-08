# OopsPlayer 独立版 BF3

2026-10-08

新导入地址：

https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.BF3.json

`OopsPlayer.json`、`OopsPlayer.BF1.json` 和 `OopsPlayer.BF2.json` 入口同步为同一份内容。BF3 使用新文件名，方便确认选中了本次修正版。若已导入诊断包，可删除 `OopsPlayer.Diagnostic` 腾出一个配置名额，再导入 BF3。

## BF3：SDR 单项重复

在 BF2 基础上仅修改 `ly12-sdr`：独立 SDR 也要求同一条匹配输入带分辨率，避免完整信息生成「1080P SDR／720P SDR」后，孤立 SDR 字段再次补出单项。其余 165 条过滤项与 BF2 完全一致，WEB-DL 修复保留。

4K SDR、576P／480P SDR、1080P WEB-DL＋SDR 和 4K WEB-DL＋SDR 仍保留独立 SDR，因为相应组合没有包含 SDR。HDR／DV 等画面优先级保留。只有 SDR、没有分辨率的输入不再显示独立 SDR，这是本次回退调整的取舍。详见 [SDR 专项说明](OOPSPLAYER-SDR.md)。

## BF2：WEB-DL 单项重复

BF2 收紧了 OopsPlayer 中独立 WEB-DL 的回退条件：要求同一条匹配输入带有分辨率。完整信息产生 4K／1080P WEB-DL 或 WEB-DL＋音频组合后，孤立的 `WEB-DL`、来源缩写、Web 隐藏标记不再额外补出单项。BF3 继续保留这项策略。

这项适配有明确取舍：只有 WEB-DL、没有分辨率的输入不再显示独立 WEB-DL；720P／576P／480P 等有分辨率、又未合入来源组合的输入仍保留单项。截图没有提供实际候选字段抓包，跨字段合并是本地复现机制，尚需重新导入后的实机验证。详见 [专项修复、测试与边界](OOPSPLAYER-WEBDL.md)。

## 两枚徽章的原因

用户的设备诊断显示 **D5、BF、U63、LOOK、CAP 和测试图片**，没有 RAW、TEXT、RULE4K。这确认实际匹配输入包含结构化隐藏标记，截图中可见的完整文件名及格式关键词未命中对应探针；基本预查、捕获及原图加载正常。

此前良友规则把 U+2063 当作旧式 DV 标志；BetterFormatter 则把它用作所有七位隐藏标记的边框。结果是其他标记也触发 DV，再触发既有 HEVC 推断，真正的分辨率、音频和声道标记没有被识别。仅缩短正则不能解决这种输入协议差异。

BF1 直接识别每种标记对应的事实，再执行原版 Boolean 条件树。这次修复输入识别，徽章图案与合成优先级保留。

## 保留的内容与长度

- 原 `all12.json`、其他旧版 JSON 和全部图片不修改。
- 161 枚徽章的名称、图片、颜色、分组及相对顺序保留。
- 片源＋音频、编码＋位深、分辨率＋WEB-DL／SDR、DV＋Atmos／TrueHD、HDR10＋TrueHD、多语言音轨的原有组合条件保留。只有独立 WEB-DL／SDR 回退按上面的 BF2／BF3 策略收紧。
- 没有结构化标记时继续使用原有普通文件名／元数据识别，包括旧式单独 U+2063。

| 指标 | 原 all12 | BF3 |
| --- | ---: | ---: |
| 徽章图案 | 161 | 161 |
| JSON 过滤条目 | 161 | 166 |
| 最长正则字符数 | 12,337 | 3,963 |
| 最长正则 UTF-8 字节数 | — | 4,095 |
| 超过 4096 的正则 | 45 | 0 |

四条较长规则（UHD REMUX 回退、BluRay 回退、WEB-DL 回退、DD+）把文本入口与隐藏标记入口拆开。BF2 的 WEB-DL 文本入口再按有／无 REMUX 拆成两个互斥入口，以满足长度限制。因此共 166 条物理过滤项、161 枚逻辑徽章。同一输入只会进入同一徽章的一个入口；图片、名称和相对顺序保留。

文本优化沿用公共前后缀提取、布尔化简与 ICU 零长度捕获复用；存在性检测的起始分隔符改为等价左边界。BF2 仅在 WEB-DL 两条格式存在性检测中使用 DOTALL 来节省长度，并针对 CRLF 和其他换行符验证；语言收集器及其余规则继续保留 `[\s\S]`。

## 协议映射及无法恢复的信息

协议依据 BetterFormatter 提交 `34591035590d1aed4cf564c145056b0aa864ebd3` 的 [protocol.mjs](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/protocol.mjs) 和 [formatters.mjs](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/formatters.mjs)。上游把 `BluRay REMUX` 映射为 Remux 标记，把 `WEB-DL` 映射为 Web 标记，所以适配时按这些含义还原事实。Remux 不要求同时出现独立的 BluRay 标记。

对七位标记输入，仅使用协议明确表达的事实。该协议没有专用的 HEVC／AVC／AV1、8bit／10bit、帧率、平台、PCM、AAC 等标记，原规则仍保存在文本入口，但不能从只有标记的输入恢复未传入的信息。HEVC 只按原版的 DV／UHD 蓝光／4K REMUX 推断条件出现；普通 4K 标记不凭空变成 HEVC 或 10bit。

未知 ID、排名、评分和不支持的语言不会被当作 DV。中文、英语、日语、韩语标记按原语言组合处理；标记本身不记录它来自音轨还是字幕，客户端需要提供正确来源。文本入口仍保留原有音轨／字幕区分。

检测到结构化标记时选用协议入口；没有标记时选用文本入口。若客户端只在可见描述中保留某项信息，却没有对应标记，协议入口不能利用那项信息。跨候选字段合并仍由播放器决定。

## 验证与实机边界

以原版在同一 ICU 引擎下的完整、有序结果为对照，分别测试普通文本，以及隐藏标记解码后的规范事实。BF1 的 **5,206 组普通文本、2,241 组标记输入，共 7,447 组对照**曾全部与原版相同。BF2／BF3 沿用这些对照，并明确从期望结果中移除缺少分辨率时的独立 WEB-DL／SDR，分别统计这些预期差异，不将其称为与 all12 完全等价。

BF2 的上述 **7,447 组对照全部通过，非预期差异为 0**；其中 67 组文本、104 组标记按新策略移除了无分辨率 WEB-DL 单项。另增加 **473 项专项检查**，覆盖来源独立字段与完整输入取并集、普通文本和隐藏标记混用、4K／1080P／音频组合、低分辨率单项、分辨率尺寸写法和不同换行符。具体结果见 [自动化报告](oopsplayer-validation.json) 和 [WEB-DL 专项报告](oopsplayer-webdl-validation.json)。

BF3 的 **7,447 组整包回归、287 项 SDR 专项检查及 473 项 WEB-DL 检查全部通过**，非预期差异为 0。SDR 专项覆盖 1080P／720P SDR 组合后合并孤立字段、4K／WEB-DL 等合法 SDR 单项、HDR／DV 互斥、尺寸写法、标记顺序和换行符。整包对照中，31 组文本、57 组标记按新策略移除了无分辨率 SDR 单项，WEB-DL 的预期移除数量与 BF2 相同。详见 [SDR 专项报告](oopsplayer-sdr-validation.json) 和当前 [整包验证报告](oopsplayer-validation.json)。

例如，Remux、4K、DV、TrueHD、Atmos、7.1 六种协议标记应得到：

**良友4K → UHD REMUX＋TrueHD → DV＋Atmos → 7.1 → HEVC**。

用户后续实机截图已确认 **BF1 在同一示例中显示上述五枚徽章**；详情页也已出现分辨率／SDR、DD+、5.1、英语音轨。验证范围限于提供的截图，未声称所有媒体和全部规则都已实机测试。诊断里的 B7 未出现，也没有取得完整设备输入抓包。

2026-10-05 另有图片占位过宽的观察，详见 [间距排查与客户端调整建议](OOPSPLAYER-LAYOUT.md)。三个代表性 PNG 几乎铺满画布，原图裁边不足以解决当时截图中的宽空隙。BF2／BF3 仅调整单项回退规则，不涉及该布局问题。

`device_tested: false` 表示尚未在用户设备验证 BF3；BF1 的后续实机结果记录在 [布局与设备观察](oopsplayer-layout-observations.json)。[诊断记录](OOPSPLAYER-DIAGNOSIS.md) 保留最初的排查阶段。

## 重新生成

```sh
python tools/oopsplayer_badges.py
python tools/test_oopsplayer_badges.py
python tools/test_oopsplayer_webdl.py
python tools/test_oopsplayer_sdr.py
python tools/diagnose_oopsplayer.py
```

正式生成器只写 `OopsPlayer.json`、`OopsPlayer.BF1.json`、`OopsPlayer.BF2.json` 与 `OopsPlayer.BF3.json`，不写原版。诊断脚本只写独立诊断包及报告。
