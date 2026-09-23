# 良友科技学院 · Apple TV Badges

当前提供两套兼容版本，规则一致，主要区别是图片渲染方式。

## 1. 简化 SVG 兼容版
- 去掉复杂滤镜、模糊和高级 SVG 特性
- 保留矢量清晰度
- 适配 **EplayerX / Forward / Nuvio / RovePlayer**
- 导入地址：
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/badges-lite-svg.json

## 2. PNG 高兼容版
- 使用同一套简化 SVG 图形服务器端栅格化为 PNG
- 更适合预览组件对 SVG 支持不完整的情况
- 适配 **EplayerX / Forward / Nuvio / RovePlayer**
- 导入地址：
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/badges-png.json

## 说明
如果 EplayerX 的资源徽章预览页出现空白，优先测试 PNG 高兼容版。两套版本的匹配规则、徽章数量和视觉结构保持一致。

## 播放器兼容建议

- **RovePlayer**：优先使用 PNG 代理版  
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/badges-png.json

- **EplayerX**：优先使用 GitHub 原生直链版  
  https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/badges-eplayerx.json

- 同时适配 **Forward / Nuvio / RovePlayer / EplayerX**。EplayerX 对第三方图片代理兼容性可能更严格，因此单独提供直链版。
