# Generated MP4 Composition Compatibility

**Status:** Implemented and locally accepted on 2026-08-19
**Scope:** 已注册并带 `VideoAssetMetadata` 的本地 H.264 MP4 进入既有 P3/P4/HyperFrames render path。

## Goal

让 `GENERATED_VIDEO` / `EXISTING_VIDEO` Shot 的本地 MP4 作为 frame-accurate visual span 被现有 `CompositionSpec -> ResolvedTimeline -> HyperFrames` 消费，并由同一次 P4 render invocation 混合 audio、绘制 captions、完成最终 mux。

## Ownership and Invariants

- Single timing owner 仍是 `ResolvedTimeline`；Shot start/end、frame/sample duration 与 source trim 均在 composition resolution 时一次性确定。
- Durable owner 仍是 `ProductionStateCommitter`；source bundle、render receipt、output 与 render-state activation 没有第二 writer。
- Renderer 仍只有 pinned local `hyperframes@0.7.103`；不得增加 alternate renderer 或 fallback。
- P4 `dialogue | narration | ambience | sfx | bgm` mixing、caption half-open timing 与 single final mux semantics 不变。
- P5 继续消费 opaque timeline fingerprint；video layer 的 trim/spec change 只 stale `composition -> timeline -> renderer-source -> render` closure。
- Legacy CLI/layout、default no-network、static-image spans 与 existing P4 contracts 不变。

## Input Contract

一个 video visual span 必须同时满足：

- Shot strategy 是 `GENERATED_VIDEO` 或 `EXISTING_VIDEO`；role 与 Registry asset 都是 `AssetType.VIDEO`。
- Registry record 有 `VideoAssetMetadata`，MIME 为 `video/mp4`，container 为 MP4，codec 为 H.264。
- MP4 suffix、MIME 与 top-level `ftyp` / `moov` box structure 一致；bytes、size 与 registered SHA-256 保持 exact match。
- measured width/height 与 composition delivery profile 一致；measured rational fps 等于 delivery fps。
- `trim_start_frame >= 0`；省略 `trim_duration_frames` 时 canonicalize 为 resolved Shot duration，显式值也必须等于该 duration；source frame count 必须覆盖整个 half-open trim interval。

Unsupported codec/container、metadata drift、too-short source、tampered bytes、unsafe/unreadable path 或 malformed MP4 top-level box structure 必须在 renderer invocation 前 fail closed；真正的 codec decodability 仍由 sealed HyperFrames render/verify gate 证明。

## Renderer Contract

HyperFrames source bundle 为 video span 物化 hash-named `.mp4`，并生成带 stable deterministic `id` 的 muted local `<video>`。`data-start`、`data-duration` 与 `data-media-start` 分别来自 resolved Shot start、duration 与 source trim；native video audio 永不绕过 P4 mixer。

`.mp4` 加入既有 canonical `state/render/sources/<bundle>/assets/<sha>.mp4` allowlist、bundle pointer validation、active render reopen 与 state-commit payload verification。Static raster HTML 在没有 video span 时保持原字节/hash。

## Acceptance Evidence

- Composition、HyperFrames、P4、models/project/state commit 与 P5 selective rebuild tests 覆盖 accept/reject、trim、source materialization、durable path、audio/caption preservation 与 precise invalidation。
- 本地集成 run 使用三个授权 Hailuo MP4，解析为 `423` frames / `846000` samples；本地 `libespeak-ng` narration 与 FFmpeg library soundscape 通过 P4 audio tracks 混合。
- `runs/generated-video-compat-20260819-001/final/final.mp4` 经 held-FD render verification、`ffprobe` 与 project-local `video-analysis` 证明含一个 H.264 video stream 与一个 AAC audio stream。

## Out of Scope

本 slice 不实现 Provider submit/poll/fetch、Registry candidate activation、Paid Provider Gate、Cloud Egress、CLI、manifest schema、new dependency、native video audio passthrough、transition/crossfade、retiming、looping、frame interpolation 或 remote renderer。
