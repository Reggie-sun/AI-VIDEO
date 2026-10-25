# Approved Dialogue Caption Preview

**Goal:** 将用户已认可的 S01 HD005 原片输出为1920×1080、24fps的原声字幕审看副本。

**Scope:** 复用 qualification capture、CaptionTrack、CompositionSpec、ResolvedTimeline 与 HyperFramesAdapter；不重生成视频，不改变源项目审核、qualification 或 activation。

**Contract:** 现有 replacement_audio_preview 允许字幕及与捕获视频严格同源的 derived DIALOGUE 音轨；保留音乐、音效与静态旁白原有约束，voice_sources 仍禁止。字幕仅绑定实际注册音轨，样本时间归唯一 ResolvedTimeline。

**Ownership:** bounded_worker 独占 `_composition_visual.py`、`composition_contracts.py` 与新增精准测试；Parent 负责当前任务媒体、计划与记录。保留既有 dirty 内容。直接复用公开 HyperFramesAdapter.render，不新建 renderer、timeline 或导出控制面。

## Milestones

1. Parent 从 exact HD005 提取原声并保留哈希、转写与句级对齐证据；建立独立 development review 项目，源 MP4 与源 Manifest 字节不变。
2. Worker 实现同源对话及字幕的有限 preview 接入；验证异源对话被拒、原有 preview 禁止 activation 的边界继续有效。Parent 验证，必要时独立审查。
3. Canonical CaptionTrack 注册、唯一时间线解析、HyperFrames lint/check/render；显式 project-local video-analysis 检查 exact 输出，检查中文、字幕边界、构图与声音保留，交用户审看。

## Verification

精准及关联回归覆盖新增入口与原有 preview/qualification fence；不以测试替代媒体验收。输出保留 development usage_scope、原片认可事实与字幕副本待审事实。最终字幕版须核验1080p/24fps及原声、对白完整性。已有未知的 audio-understand 调用不重试，无新付费生成。

## Self Review

用户“认可”绑定 HD005 SHA `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`。该认可触发现有字幕规则，不等同 Provider Production qualification。以上范围满足先认可原片后制作字幕，未改变拍摄方案或表演。
