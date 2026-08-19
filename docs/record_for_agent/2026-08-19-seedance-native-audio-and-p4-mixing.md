# Seedance Native Audio And P4 Mixing Record

Date: 2026-08-19

## Purpose

本文记录 Seedance 视频内嵌音频与当前 P4 audio/composition runtime 的真实边界，供后续 Agent 在继续 Provider、composition、audio 或 renderer 工作时复用。

本记录是 architecture/runtime note，不是新的 implementation authorization，也不把尚未实现的 native-audio extraction 描述成当前能力。代码与测试仍是最终 source of truth。

## Current Runtime Truth

当前 Production audio path 由 P4 独占最终音频编排：

1. `CompositionSpec.audio_tracks` 显式声明 `dialogue`、`narration`、`ambience`、`sfx` 与 `bgm`。
2. `resolve_composition()` 将这些输入解析成 sample-accurate `ResolvedTimeline.audio_spans`。
3. HyperFrames 只把这些 `audio_spans` 预混成 canonical stereo WAV，并在最终 MP4 中编码为 AAC。
4. captions 绑定显式 source audio asset、timing fingerprint 与 resolved sample/frame timing。

`ResolvedTimeline` 仍是唯一 timing owner；不得为 Seedance 内嵌音频另建 timeline、renderer、writer 或 direct-mux shortcut。

相关实现：

- `src/ai_video/production/models.py`: `AudioKind`, `AudioTrackSpec`, `ResolvedAudioSpan`, `CompositionSpec`, `ResolvedTimeline`。
- `src/ai_video/production/composition.py`: `_resolve_audio_spans()` 与 caption resolution。
- `src/ai_video/production/hyperframes.py`: `_mix_resolved_audio()`、mixed WAV materialization 与 final AAC verification。

## Generated Video Source Audio Is Muted

`GENERATED_VIDEO` 与 `EXISTING_VIDEO` MP4 当前只作为 visual span 进入既有 composition path。HyperFrames source 使用：

```html
<video ... muted playsinline ...>
```

因此：

- 原始 Seedance MP4 bytes 可以包含 AAC stream。
- MP4 作为 visual asset materialize 时仍保留原始 bytes/hash。
- 内嵌 AAC 不会进入 `ResolvedTimeline.audio_spans`。
- 内嵌 AAC 不会被 HyperFrames mixer 读取、提取或混入最终成片。
- 最终成片的声音只来自显式 P4 audio tracks。

相关实现与测试：

- `src/ai_video/production/visual_media.py`: `render_visual_element()` 对 MP4 强制 `muted`。
- `tests/test_production_hyperframes.py`: `test_mp4_visual_span_is_materialized_as_muted_frame_accurate_media()`。
- `tests/test_production_hyperframes.py`: `test_mp4_visual_span_keeps_p4_mixed_audio_and_captions()`。

## Meaning Of `native_audio`

P8 的 `VideoFlexibleOutputRequirement.native_audio` 当前是 Provider output/validation contract，不是 composition routing policy。

- Seedance adapter 将其序列化为 API payload 的 `generate_audio`。
- Provider capability 用 `native_audio_options` 声明模型是否接受 `false`、`true` 或二者。
- fetched candidate probe 要求 `output.native_audio == (measured.audio_stream_count > 0)`；不一致时 fail closed。
- 当前 `VideoAssetMetadata` 不保存可供 P4 混音使用的 audio codec、sample rate、channel layout、audio kind 或派生 audio asset identity。

因此 `native_audio=true` 只表示“请求并验证 Provider MP4 必须带音轨”，不表示“最终 composition 会采用该音轨”。

当前 dated Seedance matrix 声明：

- `doubao-seedance-2-5-260628`: `native_audio` 可为 `false` 或 `true`。
- `doubao-seedance-2-0-260128`: `native_audio` 可为 `false` 或 `true`。
- `doubao-seedance-2-0-fast-260128`: `native_audio` 可为 `false` 或 `true`。
- `doubao-seedance-2-0-mini-260615`: `native_audio` 可为 `false` 或 `true`。
- `doubao-seedance-1-5-pro-251215`: `native_audio` 可为 `false` 或 `true`。
- `doubao-seedance-1-0-pro-250528`: 只允许 `false`。
- `doubao-seedance-1-0-pro-fast-251015`: 只允许 `false`。

相关实现：

- `src/ai_video/production/seedance.py`: `_payload()` 显式发送 `generate_audio`。
- `src/ai_video/production/seedance_capabilities.py`: dated model capability matrix。
- `src/ai_video/production/video_artifact.py`: measured audio-stream parity gate。
- `src/ai_video/production/models.py`: `VideoAssetMetadata`。

## 2026-08-19 Diagnostic Live Evidence

一次明确授权的 Seedance Mini 5-second diagnostic submit 成功返回真实 MP4：

```text
runs/seedance-mini-5s-live-20260819-r4/state/video-generation/fetch/files/b6ea0864d3b400cf1648868a816eedc1c24f42c2bc605a60335b9f982ea91c67.mp4
```

已测量音频事实：

- codec: AAC
- sample rate: 32000 Hz
- channels: 2
- channel layout: stereo
- audio duration: 5.088 seconds
- file size: 1,278,577 bytes
- file SHA-256: `b6ea0864d3b400cf1648868a816eedc1c24f42c2bc605a60335b9f982ea91c67`

该 diagnostic request 为隔离先前 HTTP 400，省略了 optional/default fields，包括 `generate_audio`。Ark 接受请求并返回带 AAC 的 MP4。这证明该次 diagnostic cloud submit/poll/fetch 成功，也证明省略字段时该模型可能返回音频；它不证明当前 tracked adapter 的 explicit `generate_audio=false` payload 已完成 live acceptance。

不得把这个 diagnostic MP4 当成 `native_audio=false` contract 的成功 candidate；若将它与 `native_audio=false` request 一起进入当前 probe，audio-stream parity gate 应当拒绝它。

## Assessment

当前 P4 音频架构更适合继续承担 production master：

- dialogue/narration：使用显式 Voice Provider asset，保留 script、speaker/voice identity、timing 与 caption provenance。
- BGM：通过显式 gain/fade/ducking 进入 P4。
- SFX/ambience：通过显式 track placement 进入 P4。
- final mux/master timing：继续由同一个 `ResolvedTimeline -> HyperFrames` path 所有。

Seedance native audio 最有价值的潜在用途是与画面天然同步的 ambience/SFX，例如脚步、碰撞、风雨、机械声与空间环境反馈。它不应隐式替换现有 narration、dialogue、BGM 或 caption path。

当前 mixer 的已知能力边界：

- 支持 deterministic sample placement、trim、gain、fade 与 interval-based ducking。
- 输入要求 canonical WAV；不会自动读取 MP4 AAC。
- loudness metadata 当前不会自动驱动 LUFS normalization。
- 多轨相加超幅后使用 PCM16 clamp，不是完整 true-peak limiter/mastering chain。

## Recommended Default Policy

在 native-audio extraction slice 落地前：

1. Production Seedance request 默认使用 `native_audio=false` / `generate_audio=false`。
2. dialogue、narration、BGM、SFX、ambience 与 captions 继续通过当前 P4 contracts。
3. 不得因为 fetched MP4 包含 AAC 就自动播放、保留、抽取或混入该音轨。
4. 若用户明确要求 Seedance synchronized audio，应先说明当前最终 renderer 会静音 source audio，不能声称它已进入成片。
5. 不得通过移除 `<video muted>` 或 direct stream copy 绕过 `ResolvedTimeline`。

## Future Authorized Slice Boundary

若未来产品明确要求采用 Seedance native audio，应建立独立、provider-neutral 的 embedded generated-audio extraction slice。最小目标应是：

1. 从 exact fetched MP4 派生音频，并绑定原视频 SHA-256、Provider task/request identity 与 extraction tool identity。
2. fail closed 地探测 embedded audio，并转成 canonical `48 kHz stereo pcm_s16le WAV`。
3. 测量 loudness、duration、channel layout 与 decoded PCM hash。
4. 创建明确的 generated audio asset；不得利用当前 `AudioImportRequest` 把 generated Provider audio 冒充普通 import。
5. 将派生资产显式分类并绑定为 `AMBIENCE` 或 `SFX` track，再进入现有 `CompositionSpec -> ResolvedTimeline -> HyperFrames` mixer。
6. 如果内嵌音频包含 dialogue/narration，必须先解决 script identity、speaker/voice identity、transcript/caption alignment 与 provenance；不得自动假定 Provider speech 与项目脚本一致。
7. 保持 `ProductionStateCommitter` 为唯一 writer，并提供 candidate/activation/recovery、dependency invalidation 与 exact replay tests。

该 future slice 很可能需要修改 provider-neutral audio/state metadata contract，属于 scope expansion，必须先有独立 spec、plan 和用户实施授权。

## Agent Guardrails

后续 Agent 遇到 Seedance/native audio 工作时必须保持以下区分：

- `MP4 contains AAC` 不等于 `final render uses AAC`。
- `native_audio=true passed candidate probe` 不等于 `audio entered CompositionSpec`。
- `P8 fetched candidate` 不等于 `P4 audio asset activated`。
- `Seedance live submit succeeded` 不等于 `native-audio composition accepted`。
- 没有真实最终 render 与音频测量 evidence 时，不得声称 Seedance audio 已接入最终成片。

任何实现若要求修改 public CLI、schema、renderer contract、writer ownership 或 provider-neutral core，必须停止并报告 scope expansion。
