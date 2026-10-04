# OopsPlayer 独立版

2026-10-04

导入地址：

https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/Badge%20LiangYou%20Ver.OopsPlayer.json

以 `Badge LiangYou Ver.all12.json` 为基准，单独生成 OopsPlayer 版。原版及各旧版 JSON 不做修改；本次只新增一个导入版本，不同步覆盖原有入口。

## 保留的内容

- 全部 161 个徽章、ID、分组、名称、图片地址、颜色、启用状态和显示顺序。
- 原有片源＋音频、编码＋位深、分辨率＋WEB-DL／SDR、DV＋Atmos／TrueHD、HDR10＋TrueHD 以及多语言音轨组合。
- 原有单项回退、优先级、互斥和排除条件，包括音轨与字幕的区分。

配置中只改变 `pattern` 字段。图片继续使用原文件，不重新制作、不更换图案。

## 长度限制与优化方法

按反馈的“每条正则不超过 4096”进行约束，不是要求整个 JSON 文件小于 4096 字节。

| 指标 | 原版 | OopsPlayer 版 |
| --- | ---: | ---: |
| 徽章数量 | 161 | 161 |
| 最长单条正则字符数 | 12,337 | 4,041 |
| 超过 4096 字符的规则 | 45 | 0 |
| 新版最长单条 UTF-8 字节数 | — | 4,083 |

优化通过布尔条件化简、公共前后缀提取和重复条件复用完成。多语言规则将同一套上下文识别逻辑共享给四种语言，仍分别判断语言是否出现，再选择对应的单语／双语／三语／四语徽章。

保留 `[\s\S]` 扫描方式；没有用 DOTALL 的 `.` 替代它，因为 ICU 对 CRLF 换行的处理会产生边界差异。

重复条件使用 ICU 的零长度捕获和反向引用。正向预查固定每次判断结果，语言检测最多进行四轮，每轮记录一个尚未记录的语言。这属于 ICU 正则写法，不应直接交给 JavaScript RegExp 使用。

## 验证与边界

验证直接比较原版与新版在同一个 ICU 引擎下的**完整、有序徽章列表**，并检查全部非正则字段一致、长度达标、原版文件哈希不变。场景包含仓库原有样例、随机组合、多语言音轨、字幕干扰、换行、Unicode 大小写折叠和长文本。

具体数量与结果见 [验证报告](oopsplayer-validation.json)。

这是配置和 ICU 引擎级验证，尚未在 OopsPlayer 实机导入测试。若客户端另有正则语法白名单、输入字段拆分或导入器限制，需要依据实际报错继续适配。播放器未传入的音轨／Atmos 信息也无法由正则恢复；原版的跨字段合成边界继续保留。

## 重新生成

```sh
python tools/oopsplayer_badges.py
python tools/test_oopsplayer_badges.py
```

生成器只写 `Badge LiangYou Ver.OopsPlayer.json`。测试报告写入 `reports/oopsplayer-validation.json`，不改写其他徽章包。

生成前会检查 V12 源生成器与 `all12.json` 内容一致；源规则变化后，必须重新运行长度与等价性验证。
