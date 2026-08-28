---
record_kind: media_experiment
topic_id: qingyan-caption-final-acceptance
learning_eligibility: eligible
evidence_index_version: "1"
---

# Qingyan Caption Final Acceptance Record

Date: 2026-08-29

## Purpose

本文记录 Qingyan V4 review-only 成片为何不能进入 `Final Acceptance`，以及一次不调用 Provider、
不联网、不付费的 local canonicalization 如何把同一已支持素材收敛为 exact Production render，完成
TECHNICAL / LAYOUT / CAPTION / SEMANTIC 四层 P6，并由唯一 writer
`ProductionStateCommitter` 写入 durable `Final Acceptance`。

Primary Production root：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/`

本记录只声明该 exact selected-policy Production closure。它不等于用户主观审美验收、广告投放合规、
claim substantiation、publication、push、release 或市场效果。

## Previous Blocker

V4 review artifact：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`

SHA-256 `087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`。

它不能进入 `Final Acceptance` 的原因不是“文件无法播放”，而是 proof layer 不完整：旧
`production/` root 没有绑定 V4 exact bytes 的 active render / selected QA policy，Registry 中仍是英文
`Hello/world` CaptionTrack；三张尾卡包含未核验百分比、时长、机理与 testimonial claims。抽帧可读、
ffmpeg decode、Whisper region 与 local review verdict 都不能替代 canonical identity、CAPTION P6、
Domain Gate 或 Final Acceptance receipt。

## Canonicalization Decisions

V9 保留 V4 与所有历史 attempt bytes，不覆盖 review-only artifact。新的 canonical candidate 只使用
本地已支持素材，通过 `ResolvedTimeline -> HyperFrames -> ProductionStateCommitter` 标准路径生成。

为满足 selected Qingyan Ecommerce profile，执行了以下最小内容修复：

- 移除 `清爽舒适`、`抑汗净味`、`近距离更从容`、百分比、持续时间、机理与 testimonial authoring；
  authored copy 只保留问题、递瓶、使用指令与品牌名。
- 音轨静音区间覆盖未核验功效与 slogan，只保留 `0-6s` 问题/递瓶/喷一下和
  `21.08-22.08s` 品牌 `青颜`；canonical WAV 为 `48kHz stereo pcm_s16le`。
- 结尾从 4 秒黑底卡收敛为 `26-28s` 两秒 end card；`22-26s` 保留受支持的户外产品 beauty shot。
- 移除 `17-22s` 的另一位现代女性/男性，改为同一蓝衣银饰主角的“喷用 -> 微笑” payoff，关闭
  `ad.continuity.character` blocker。
- 视频时间线收敛为 exact `672` frames / `28.000s`。早期 `28.041667s` arm 在 AAC verification
  出现 encoder priming / padding 后 `32 samples` 边界差异，严格失败后未 blind retry；改用 exact
  `1,344,000` source samples 后标准 HyperFrames verification 通过。

V5-V8 是同一 canonicalization experiment 内的诊断 arms：end-card cap、人物 continuity、slowdown
timebase 与一秒残留人物分别被 exact frame sheets 拒绝，均未获得 P6 或 Final Acceptance。只有 V9
进入 durable review transaction。

## Current Runtime Truth

Final MP4：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/render/outputs/9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2.mp4`

- SHA-256: `9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2`
- size: `17,291,842` bytes
- video: H.264 High, `720x1280`, `24fps`, `672` decoded frames
- audio: AAC stereo, `48000Hz`
- container duration: `28.022s`; canonical video timeline: `28.000s`
- decoded unique-frame hashes: `669 / 672`
- minimum frame-average luma: `67.1827 / 255` (`263` milli)
- audio peak: `-1.330973 dB`; NaN / Inf: `0 / 0`
- `blackdetect` full-frame intervals: `0`

Project-local `video-analysis` MCP 绑定上述 exact MP4，重新测得 `672` frames、`720x1280`、AAC
`48kHz`，并只转写三段保留语音：`0.0-2.88s`、`3.28-6.08s`、`21.08-22.08s`；未转写已删除的
功效、百分比、持续时间或 testimonial 文案。

Final visual evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-acceptance-canonicalization-20260829/v9-final-dense-1s-contact-sheet.png`
  SHA-256 `b483f889fdfca43703cb81cfc693c9020cbf398887f230d65265d7a58b343e64`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-acceptance-canonicalization-20260829/v9-final-cue-and-gap-contact-sheet.png`
  SHA-256 `445ccaaff0e89c2f02da0f8aea657a4dcb3f34815c1e81a680a19ff81d3deb2c`

Dense sheet 覆盖全片逐秒状态；cue/gap sheet 覆盖五个 authored cues 与无 cue 区间。Exact visual
inspection 确认字幕位于 bottom safe area、无双层 authored subtitle、无 claim cards、人物保持同一主角，
并且 26 秒后才进入两秒 end card。包装上原生印刷内容属于已支持 source bytes；本轮没有把它改写为
新的 authored efficacy claim。

## P6 And Final Acceptance

Manifest strict reopen truth：

- schema: `2.15`
- revision: `20`
- timeline fingerprint:
  `4cd6392477e69a7162e7fa846b29c2d20f27dac3378c3862f4b3174fc3b6b10b`
- active render output SHA-256:
  `9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2`

Current passing review receipts：

| Layer | Review content hash | Evidence boundary |
| --- | --- | --- |
| TECHNICAL | `53799fecccdfd85a764ac782321fa2050e1d5c7e11e53cdfe00dfa589b5a2d43` | full video/audio decode、672 frames、luma、peak、NaN/Inf、motion |
| LAYOUT | `5a2ce4a60c4051178087e951609d6cb22445c9adefedadf3e815ba77c1a293a0` | exact dense/cue sheets、safe area、collision、transition boundary |
| CAPTION | `356c470a584b9a8e515ce6eb3ba31387e7837e86eedf4b4b8f54204e4326072d` | six canonical groups、five exact cue subjects、whole-render unintended-text domain |
| SEMANTIC | `21ef74a11f4ef1b646e674580aa1a1ff8549b49766bbb36d663f5d0ebe95999a` | all 15 Qingyan whole-ad requirements, including claim compliance and continuity |

Final Acceptance receipt：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/acceptance/final.2ac31c13692c47eeca778def2c0a4d6bad2921da2ed64d88a3275c8f91566e90.json`

- semantic content hash:
  `2ac31c13692c47eeca778def2c0a4d6bad2921da2ed64d88a3275c8f91566e90`
- file SHA-256:
  `61c5e99814489784aa59e7e5ecf5b03d17a040abc7b35f4341f64810ee8d5444`
- state: `fresh`
- desired / applied fingerprint:
  `004dfaa28e58ae112b05e639d8d8cf992ef6e0663b6092f62d725c0c3170d892`

完成后重新运行 `load_production_project()`、
`ProductionStateCommitter.current_final_media_target()` 与四层 receipt strict reopen，全部返回 current
PASS；final MP4 又执行一次 ffmpeg full decode，SHA-256 未漂移。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qingyan-v4-production-entry | qingyan-v4-review-only | qingyan-final-acceptance-canonicalization-20260829 | caption-repaired-v4 | review-only-source | 087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1 | PRODUCTION_GATE | NOT_EVALUATED | CANONICAL_IDENTITY_AND_CLAIMS | CONCLUSION_SUPERSEDED | qingyan-v9-final-acceptance | `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md` |
| qingyan-v9-exact-media | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | EXACT_MEDIA_ANALYZER_AND_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-acceptance-canonicalization-20260829/` |
| qingyan-v9-caption-p6 | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | CAPTION_P6 | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | qingyan-v9-exact-media | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/reviews/` |
| qingyan-v9-final-acceptance | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | FINAL_ACCEPTANCE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | qingyan-v9-caption-p6 | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/acceptance/final.2ac31c13692c47eeca778def2c0a4d6bad2921da2ed64d88a3275c8f91566e90.json` |

## Assessment

当前 gate 不再是 V4 时的 `NOT_EVALUATED`：V9 exact artifact 已真实进入 selected Qingyan
Ecommerce Production path，四层 P6 与 Final Acceptance 都有 content-addressed durable receipt，且可
strict reopen。这个结论只绑定上方 exact bytes、timeline、Registry、graph、policy 与 receipts；任何新
剪辑、替换音频、claim card、字体、分辨率或重新编码都会使 identity 失效，需要重新 Gate。

保留的边界：

- `Final Acceptance PASS` 不等于用户已完成 full-speed subjective watch/listen。
- 移除未核验 authored claims 不等于为包装印刷内容或未来广告文案提供 substantiation。
- local Production state 未 push、publish 或 release；remote availability 未验证。
- generic `video-analysis` scene detector 报一个连续 scene，不能替代本轮逐秒/边界 visual inspection；
  landscape-oriented resolution hint 也不改变 selected `720x1280` vertical delivery contract。

## Agent Guardrails

- 后续 Agent 必须从 `production-final-v9/project.yaml` strict reopen，不得把 V4 review-only MP4、
  V5-V8 diagnostic root 或文件名当作 current accepted truth。
- 不得通过复制 MP4、修改 Manifest JSON、伪造 evaluator payload 或只看 receipt 字段来继承
  `Final Acceptance`；必须保持 exact content identities 与 strict reopen。
- 新 Provider submit、paid call、claim 恢复、publication、push、release 或 subjective user approval
  都是独立 scope。
- 本轮 Provider / paid / network call 为 `0`。记录阶段没有新增媒体测试或 Production mutation。
- repository RAG index 未因本记录自动刷新；历史 retrieval 结果在独立 refresh 完成前可能仍返回 V4
  current-facing wording。
