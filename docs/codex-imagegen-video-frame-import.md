# Codex Imagegen Video-Frame Import

## Contract

`HumanImageImportReceipt(source_surface="codex_imagegen_tool")` 支持既有
`VideoFrameImageImportReferenceBinding`，真实记录参考 MP4、解码帧号及 PNG 的 exact
hashes、尺寸和 extractor identity。工具身份保持 `codex-imagegen-import/1`；不能声明
automated browser、backend model ID 或不存在的 Provider request ID。

`prepare_human_image_import_commit(..., reference_artifacts=())` 的可选参数承载这些
content-addressed 来源 bytes；默认空 tuple 保持原调用兼容。使用 video-frame reference
时必须提供全部对应 artifacts；缺失、篡改、错误帧或不安全路径仍拒绝。

## Ownership And Replay

唯一写入方仍为 `ProductionStateCommitter`。首次 bootstrap 和正常 import admission
均在写入前验证 MP4 解码帧与声明 PNG 一致；reader/replay 验证已保存 bytes，精确 replay
不重复解码或生成。来源不能通过普通 note 或空 references 替代。

## Compatibility

这是现有 import 的增量支持，不迁移或重写旧 receipts、QA、Manifest 或媒体。
`chatgpt_images_2_web` 不因此获得 video-frame reference 支持；既有 browser import
保持独立工具身份。旧 human/browser receipt hashes 与默认调用形式保持不变。

## Verification

`tests/test_production_image_import.py` 覆盖 Codex frame receipt、首次 bootstrap、正常
commit、exact reopen/replay、错误帧号、缺失/篡改来源以及历史 hash 兼容。
这些检查证明导入契约，不证明生成视频的媒体质量或人审通过。
