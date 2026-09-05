---
record_kind: recovery_incident
topic_id: video-library-hevc-compatible-preview
learning_eligibility: ineligible
---

# Video Library HEVC Compatible Preview

Date: 2026-09-06

## Problem And Ownership

用户截图中的 S01 2.5 修复视频已经进入视频库，但 `ExactPlayer.onError` 把任何
浏览器播放错误都标为文件不可用。原文件通过 strict detail 校验，HTTP Range 为 206，
FFmpeg 全量解码成功；当前 Chrome 对 HEVC Main 10 返回
`DEMUXER_ERROR_NO_SUPPORTED_STREAMS`。因此本例是浏览器解码兼容问题，不是发现遗漏。

错误投影仍由 `provider-console/src/library-preview.js` 与 `ExactPlayer` 独占，
替换旧的无条件 `onUnavailable` 路径。HEAD 404/410 才投影不可用；decode/network
分别显示错误并保留原 token 下载。切换/卸载取消旧请求，刷新允许重试。
没有新增 server endpoint、自动转码、Provider 调用或 Production state writer。

## Authorized Local Derivative

用户确认生成独立 H.264 兼容预览；只执行一次本地 FFmpeg 转码。
原文件保持不变：

`runs/jieshi-e01-seedance25-20260905-repair01/production-s01-repair-v1/state/video-generation/fetch/files/eed2589c7655b89d5e114b5b5146bb3cc2a31bb5983e5af9d796d0dd008df440.mp4`

副本由既有 `artifacts` External 来源发现：

`artifacts/browser-previews/eed2589c7655b89d5e114b5b5146bb3cc2a31bb5983e5af9d796d0dd008df440/界蚀-S01-Seedance2.5修复-H264兼容预览.mp4`

| Measurement | Original | Compatible preview |
| --- | --- | --- |
| SHA-256 | `eed2589c7655b89d5e114b5b5146bb3cc2a31bb5983e5af9d796d0dd008df440` | `574f1a06441cc50bc88f9ad6145fd14074201c317e9ecfec5dde3020cab95ff7` |
| Bytes | 2420329 | 1050152 |
| Codec / pixel format | HEVC Main 10 / yuv420p10le | H.264 / yuv420p |
| Dimensions / fps / frames | 1080×1920 / 24 / 97 | 1080×1920 / 24 / 97 |
| Container duration / audio | 4.042s / none | 4.042s / none |

使用 `libx264 -preset fast -crf 18 -pix_fmt yuv420p`，保留 bt709，启用 faststart，
没有缩放、变速或添加音轨。8-bit 有损副本仅用于浏览；名称中的模型字样不构成已验证
Provider metadata。副本为独立 identity，不替换原选中项，不继承原生成记录或验收状态。
两个 MP4 都是本机产物，不纳入代码 commit。

## Verification And Evidence

- 原文件转码前后 SHA 一致；strict detail valid，2420329 bytes，原 token 的 browser
  fetch 返回 200 / video/mp4 且完整 SHA 匹配。
- Chrome MCP 实际选择兼容副本，`readyState=4`，1080×1920，`duration=4.041667`，
  播放时间从 0 前进至 0.781279，`error=null`；Range 返回
  `206 / bytes 0-1023/1050152 / video/mp4`。
- Chrome MCP 验证原条目显示浏览器无法解码及下载链接，原 `running / validate` 与
  未评估状态保留。工具重连后，另用已安装 puppeteer-core 和 `/usr/bin/google-chrome`
  打开真实 app，点击真实原条目的下载链接，实际保存 MP4 为 2420329 bytes，SHA 与原文件
  一致；不是 HTML player wrapper。没有安装 dependency。
- `node --test provider-console/tests/library-browser.test.mjs` 覆盖错误分类、原 token
  下载展示及请求途中取消；最终 mandatory checks 由 exact commit-range Harness 执行。
  receipt 路径：`.agent/harness/runs/video-library-hevc-preview-20260906/receipt.json`；
  最终状态与 freshness 以该 receipt 和验证输出为准。
- native `reviewer_xhigh`：accept，无 blocking issues。其取消中请求测试建议已加入，
  下载实际落盘的不确定性由上述完整 SHA 验证关闭。

## Boundaries And Learning Evaluation

本次证明文件可读、兼容副本可播与原文件下载正确；没有新增叙事质量、人类验收、
candidate、P6 或 Final Acceptance。原媒体已有 Gate FAIL 不因转码改变，最终 renderer
对原 HEVC 的兼容性仍未验证。

按 `record-ai-video-session` 记录本次稳定修复，并执行 `distill-ai-video-learning`
候选评估：`no_candidate`。这是同一原始素材链的工程兼容修复，不是独立模型实验，
不新增 Learning Claim 或变更 Provider Policy。没有刷新 advisory RAG index。
仅本任务文件进入 local checkpoint；保留其他 writer 的 staged/dirty 文件，不 push/release。
