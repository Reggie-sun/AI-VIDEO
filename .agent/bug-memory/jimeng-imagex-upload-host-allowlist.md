# Jimeng ImageX Upload Host Allowlist

## Symptom And Reproduction

同一 Registry 图片、账号、canvas 和 `JimengBrowserTransport.upload` 间歇性成功/失败；上层将原因折叠为 `Jimeng reference upload did not complete; generation was not submitted.`。2026-10-26 的有界 upload-only 诊断在两次成功后复现 `upload destination invalid`，没有 generation POST。

证据根 `.codex/tmp/jieshi-jimeng-mini-20261026/`：`upload-diagnosis-results.json`、`upload-host-format-results.json`、`root-cause-comparison.json`。输入 SHA `93c4d6bc6d3467bc444a61ba492293ad9e98a5f8b123589cd7afb3476b0fe7d9`。

## Confirmed Cause And Owner

`src/ai_video/production/jimeng_browser.cjs` 的 `upload()` 从 ImageX `ApplyImageUpload` 响应选择 `UploadAddress.UploadHosts[0]`，拼接 binary upload URL 后调用 `safeUpload()`。当前白名单包含 `snssdk.com`，不包含 `bytedancevod.com`。

实际响应在允许的 `tos-*.snssdk.com` 和 `tos-lq-x.bytedancevod.com` 之间变化。后者被当前规则在 binary POST 前拒绝。Apply-only 诊断在第八次观察中取得该 rejected host；其 raw host 无 scheme，拼接后 hostname 仍正确，排除本次观察中的重复 `https://` 拼接。仅从当前源码提取 regex 的离线验证也得到同一允许/拒绝结果。被测 worker SHA `d1cc03b6b5ec39cb2ccebe0f16e75974e1e6acbfa28ca939dc50e3ea87a637a5`。

## Fix And Verification Status

`DIAGNOSED_NOT_FIXED`。未修改域名规则、Provider、permit、budget 或 recovery lifecycle。修复应在该上传准入 owner 内核对委托 host 并保持受限目的地址验证，再覆盖允许/拒绝域名及真实上传；不在 caller 重试或替换输入来掩盖此缺陷。原有失败及未消费普通 runtime grant 必须保留并由 canonical recovery owner 处理。

诊断未新增生成请求，canonical Manifest SHA 与原 checkpoint 一致。此证据证明上传准入缺陷，不证明平台内容审核通过、Mini 能成功生成或原作品质量合格。

## Reuse Boundary

适用于当前 ImageX delegated host 与当前白名单不一致的失败。使用前重验源码及实际返回的 hostname；不保存 token、签名 URL、headers 或原始上传授权响应。原两次 opaque Provider 异常未记录 host，当前 reproducer 不能逐次还原其分配节点。

《界蚀》2026-10-16 Ark API 的 HTTP400 / `InputImageSensitiveContentDetected.PrivacyInformation` 是独立故障：当时 exact body 已包含 `first_frame` 图片，且输入 SHA 为 `13c83ce4…76923`。本次本地 host 拒绝不能作为该历史审核错误的解释。
