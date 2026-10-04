# OopsPlayer 两枚徽章问题：等待设备诊断

2026-10-05

## 已确认的现象

用户截图中的实时预览文件名为：

```text
Example.2160p.BluRay.Remux.DV.TrueHD.Atmos.7.1.mkv
```

截图只有 DOLBY VISION、HEVC 两枚自定义徽章和播放器自带 MKV。

将这段完整文件名分别交给原 `all12.json` 和当前 `OopsPlayer.json`，ICU 得到相同的有序结果：

1. 良友4K
2. UHD REMUX · TRUEHD · 蓝光
3. DV+ATMOS
4. 7.1
5. HEVC · H.265

因此，完整文件名上的本地等价性测试没有覆盖这次设备端差异。现有截图不能判定是输入转换、导入后的正则变化、引擎处理、分组显示还是图片加载造成的。

## 可复现的输入假设

[BetterFormatter 的协议代码](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/protocol.mjs) 定义了以 U+2063 包围七位 U+200B／U+200D 的隐藏标记。[其生成器](https://github.com/9mousaa/BetterFormatter/blob/34591035590d1aed4cf564c145056b0aa864ebd3/src/fusion.mjs) 中有直接匹配这些标记的规则。旧版普通文件名预设与这套协议不是同一种输入。

原良友规则兼容单独的 U+2063 作为 DV 线索。如果实际输入只有上述结构化标记，现有良友规则会把标记边框当作 DV，再由既有推断显示 HEVC。其余文件名信息没有以文本形式出现，因而不能命中。把 4K、BluRay、Remux、DV、TrueHD、Atmos、7.1 转成该协议后，可复现截图中的两枚徽章；分别输入协议的 78 种已定义标记也全部得到相同的 DV／HEVC 结果，包括根本不表示 DV 的标记。

**这证明一种可能的故障机制，不证明 OopsPlayer 实际使用了这种输入。** 单独输入文字 `DV` 也会得到同样的两枚。未取得设备输入之前，不据此替换 161 条正式规则，也不删除原有 DV 兼容入口。

## 一次预览诊断

独立导入地址：

https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.Diagnostic.json

1. 在「从 URL 导入」中导入上述地址，并选择 `Badge LiangYou Ver.OopsPlayer.Diagnostic`。
2. 保持上面的示例文件名不变，截取「实时预览」区域。若标签可横向滚动，请同时截取右侧标签。
3. 测试后切回原先的配置。诊断包会强制显示一张图片，不应当作正式影片徽章使用。

截图中有四个配置，诊断包可作为第五个配置导入；无须删除原徽章包。若设备配置数量已变，请按实际剩余名额处理。

| 标签 | 检查内容 |
| --- | --- |
| D5 | 诊断配置已匹配非空输入 |
| RAW | 匹配到了截图中的完整原始文件名 |
| TEXT | 输入含有示例中的可见格式关键词 |
| BF | 输入含有 BetterFormatter 七位隐藏标记 |
| U63 | 输入含有 U+2063；单独出现不能证明是结构化标记 |
| LOOK | 基本预查可以执行 |
| CAP | 零长度捕获和已参与的反向引用可以执行 |
| UNSET | 未参与的反向引用也匹配成功；这与 ICU 的行为不同 |
| B7 | 输入包含与示例对应的七种协议标记；是协议映射探针，不是影片徽章 |
| RULE4K | 当前独立版的完整 4K 正则匹配成功，暂用文字显示以排除 4K 图片加载影响 |
| UHD REMUX · TRUEHD 图片 | 强制加载原来的图片，只检查图片显示，不代表识别到这种片源 |

本地 ICU 的预期：

| 模拟输入 | 可见检测标签（另有强制图片） |
| --- | --- |
| 完整示例文件名 | D5、RAW、TEXT、LOOK、CAP、RULE4K |
| 对应的七种隐藏标记 | D5、BF、U63、LOOK、CAP、B7 |
| 只有 `DV` 文字 | D5、TEXT、LOOK、CAP |

若客户端每组只显示一项，BF 与 U63 可能只出现 BF。客户端也可能裁切或限制标签数量；应结合完整预览判断，不把单个缺失标签直接当成根因。MKV 是播放器自带标签，不属于诊断结果。

RAW／TEXT 缺失而 BF／B7 出现，支持隐藏标记输入的解释。RAW 出现而 RULE4K 不出现，则应继续核对导入后的规则与引擎行为。UNSET 出现提示反向引用语义不兼容。强制图片加载失败则需另外检查图片请求。一次结果可能同时包含多个问题。

## 验证与改动范围

```sh
python tools/diagnose_oopsplayer.py
```

脚本验证原版与独立版对示例均命中五枚、隐藏标记能复现两枚、诊断探针符合 ICU 的预期、每条诊断正则不超过 4096 字节，并核对两个正式 JSON 的字节未改变。最长诊断正则为 895 字节。

结果见 [机器可读报告](oopsplayer-diagnosis.json)。报告明确记录 `cause_confirmed: false` 和 `device_tested: false`；后者表示诊断包尚未实机测试，用户提供的原独立版截图已纳入排查。

这次仅新增诊断包、生成／复现脚本和说明，更新文档中的兼容状态。`all12.json`、原独立版 JSON、其他徽章包和图片均不修改。下一步需要这份诊断配置的实机预览，才能针对实际输入修正独立版。
