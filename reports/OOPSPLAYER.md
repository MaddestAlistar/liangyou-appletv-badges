# OopsPlayer 独立版 BF1

2026-10-05

新导入地址：

https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.BF1.json

原 `OopsPlayer.json` 入口同步为同一份内容。BF1 使用新文件名，方便避开旧配置缓存并确认选中了修正版。若已导入诊断包，可删除 `OopsPlayer.Diagnostic` 腾出一个配置名额，再导入 BF1。

## 两枚徽章的原因

用户的设备诊断显示 **D5、BF、U63、LOOK、CAP 和测试图片**，没有 RAW、TEXT、RULE4K。这确认实际匹配输入包含结构化隐藏标记，截图中可见的完整文件名及格式关键词未命中对应探针；基本预查、捕获及原图加载正常。

此前良友规则把 U+2063 当作旧式 DV 标志；BetterFormatter 则把它用作所有七位隐藏标记的边框。结果是其他标记也触发 DV，再触发既有 HEVC 推断，真正的分辨率、音频和声道标记没有被识别。仅缩短正则不能解决这种输入协议差异。

BF1 直接识别每种标记对应的事实，再执行原版 Boolean 条件树。这次修复输入识别，徽章图案与合成优先级保留。

## 保留的内容与长度

- 原 `all12.json`、其他旧版 JSON 和全部图片不修改。
- 161 枚徽章的名称、图片、颜色、分组及相对顺序保留。
- 片源＋音频、编码＋位深、分辨率＋WEB-DL／SDR、DV＋Atmos／TrueHD、HDR10＋TrueHD、多语言音轨的原有组合条件、互斥和回退逻辑保留。
- 没有结构化标记时继续使用原有普通文件名／元数据识别，包括旧式单独 U+2063。

| 指标 | 原 all12 | BF1 |
| --- | ---: | ---: |
| 徽章图案 | 161 | 161 |
| JSON 过滤条目 | 161 | 165 |
| 最长正则字符数 | 12,337 | 4,043 |
| 最长正则 UTF-8 字节数 | — | 4,095 |
| 超过 4096 的正则 | 45 | 0 |

四条较长规则（UHD REMUX 回退、BluRay 回退、WEB-DL 回退、DD+）把文本入口与隐藏标记入口拆开。同一输入只会进入其中一个，使用同一枚图片，未增加新的徽章或改变合成条件。新增入口 ID 以 `-bf` 结尾，紧接对应的原 ID。

文本优化沿用公共前后缀提取、布尔化简与 ICU 零长度捕获复用；存在性检测的起始分隔符改为等价左边界，给长度限制留出空间。保留 `[\s\S]`，避免 ICU DOTALL 对 CRLF 的特殊处理改变边界行为。

## 协议映射及无法恢复的信息

协议依据 BetterFormatter 提交 `34591035590d1aed4cf564c145056b0aa864ebd3` 的 [protocol.mjs](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/protocol.mjs) 和 [formatters.mjs](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/formatters.mjs)。上游把 `BluRay REMUX` 映射为 Remux 标记，把 `WEB-DL` 映射为 Web 标记，所以适配时按这些含义还原事实。Remux 不要求同时出现独立的 BluRay 标记。

对七位标记输入，仅使用协议明确表达的事实。该协议没有专用的 HEVC／AVC／AV1、8bit／10bit、帧率、平台、PCM、AAC 等标记，原规则仍保存在文本入口，但不能从只有标记的输入恢复未传入的信息。HEVC 只按原版的 DV／UHD 蓝光／4K REMUX 推断条件出现；普通 4K 标记不凭空变成 HEVC 或 10bit。

未知 ID、排名、评分和不支持的语言不会被当作 DV。中文、英语、日语、韩语标记按原语言组合处理；标记本身不记录它来自音轨还是字幕，客户端需要提供正确来源。文本入口仍保留原有音轨／字幕区分。

检测到结构化标记时选用协议入口；没有标记时选用文本入口。若客户端只在可见描述中保留某项信息，却没有对应标记，协议入口不能利用那项信息。跨候选字段合并仍由播放器决定。

## 验证与实机边界

以原版在同一 ICU 引擎下的完整、有序结果为对照，分别测试普通文本，以及隐藏标记解码后的规范事实。**5,206 组普通文本、2,241 组标记输入，共 7,447 组对照通过，零差异。** 同时检查元数据与顺序、互斥入口不重复显示、未知标记不误报、长度和原文件哈希。

例如，Remux、4K、DV、TrueHD、Atmos、7.1 六种协议标记应得到：

**良友4K → UHD REMUX＋TrueHD → DV＋Atmos → 7.1 → HEVC**。

用户已经实机确认的是诊断包及输入格式，**BF1 修正版仍需重新导入后的设备预览验证**。诊断里的 B7 未出现，不能据此声称已取得设备上全部标记 ID。

具体用例数量、长度与结果见 [验证报告](oopsplayer-validation.json)。[诊断记录](OOPSPLAYER-DIAGNOSIS.md) 保留最初的现象和这次截图结论。

## 重新生成

```sh
python tools/oopsplayer_badges.py
python tools/test_oopsplayer_badges.py
python tools/diagnose_oopsplayer.py
```

正式生成器只写 `OopsPlayer.json` 与 `OopsPlayer.BF1.json`，不写原版。诊断脚本只写独立诊断包及报告。
