# Automated Image Import From A Video Frame

## Scope

`AutomatedBrowserImageImportReceipt.references` 可以通过
`VideoFrameImageImportReferenceBinding` 如实描述生成图片时使用的原视频帧。
该 binding 只表示来源，不表示源视频或新图片已通过 QA、已激活或获准交付。
旧角色／场景 reference、Human import receipt 和历史 content hash 保持原格式。

## Exact Binding

`src/ai_video/production/image_import_video_frame.py` 保存该 reference 的验证逻辑。
绑定包含原 MP4 与参考 PNG 的 SHA-256、size、PNG 尺寸、从零计数的 frame index
及 ffmpeg extraction identity。证据文件路径限定在
`evidence/video-frame-import/<sha256>.mp4` 和同目录的 `<sha256>.png`。
它不伪装成 Character、Scene 或已注册的 Shot endpoint。

`prepare_automated_browser_image_import_commit(..., reference_artifacts=...)`
接收对应的 `PreparedArtifact`，验证实际解码帧与 PNG 的 RGB 像素一致，再交给
既有 `ProductionStateCommitter` 写入。解码只允许本地 file/pipe，并有超时；
不上传、不调用生成 Provider，不改变源媒体。

## Reopen And Bootstrap

标准 reader 验证 receipt、完整来源文件的 hash/size、PNG 格式／尺寸和安全路径；
重新读取不执行解码或生成媒体。Bootstrap 必须包含完整的来源文件闭包；首次接入
验证帧推导，已有 bundle 的 exact replay 不重跑解码。
缺失来源、篡改文件、错误帧、错误 extractor identity 或不安全路径必须拒绝。

## Verification Boundary

回归覆盖由 `tests/test_production_image_import.py` 与
`tests/test_production_bootstrap.py` 维护。测试证明来源绑定行为，不能证明
电影感、动作自然度、语义连续性或音画同步；这些仍需要 exact 媒体证据与适用 QA。
