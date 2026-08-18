# Generated MP4 Composition Compatibility Plan

**Goal:** 将已注册/本地验证 MP4 接入现有 P3/P4 deterministic composition，并用三个 Hailuo clips 产出带 audio stream 的 durable local final MP4。

## Contract

- `ResolvedTimeline`：唯一 frame/sample/trim/Shot-boundary owner。
- `ProductionStateCommitter`：唯一 durable activation owner。
- Retire old path：移除 raster-only visual-span rejection，但保留 static-image exact behavior。
- Unchanged：P4 mixer/captions、P5 precise invalidation、single HyperFrames renderer、Legacy CLI/layout、default no-network。

## Implementation Tasks

- [x] 用 codegraph 与 read-only explorer 映射 composition、HyperFrames、render activation、P5 closure。
- [x] 先写 RED tests：video strategy/type、MP4 metadata/bytes、trim resolution、P4 audio/captions、durable source、P5 closure。
- [x] 扩展 `ResolvedVisualSpan` / `RendererAssetBinding` MIME，不增加 schema version。
- [x] 在 composition resolution 中验证 H.264 MP4、delivery compatibility 与 exact source interval。
- [x] 在 HyperFrames source 中生成 stable-ID muted `<video>`，复用同一个 P4 audio/caption source。
- [x] 扩展 canonical render-source `.mp4` path、bundle validation、state commit 与 active reopen verification。
- [x] 保持 raster committed fixture/hash 不变，并验证 P5 无 resolver change。
- [x] 使用三个本地 Hailuo MP4、本地 narration/soundscape 完成真实 pinned HyperFrames render。
- [x] Native reviewer 检查 final diff、failure modes、semantic scope 与 tests；verdict为`accept with concerns`、无blocking issue，保留真实decodability依赖render gate与future dedicated MP4 reopen test两项concern。
- [ ] 生成并校验 fresh Harness receipt，提交 task-only checkpoint。

## Verification

Focused tests：

```text
pytest -q tests/test_production_composition.py
pytest -q tests/test_production_hyperframes.py
pytest -q tests/test_production_voice_captions_e2e.py
pytest -q tests/test_production_dependency.py tests/test_production_selective_rebuild.py
pytest -q tests/test_production_models.py tests/test_production_project.py
pytest -q tests/test_production_state_commit.py tests/test_production_state_recovery.py
```

Runtime acceptance：

```text
ffprobe runs/generated-video-compat-20260819-001/final/final.mp4
video-analysis.video_probe(runs/generated-video-compat-20260819-001/final/final.mp4)
```

最终 gate：task-only staged Harness snapshot、fresh receipt self-verification、specific-file checkpoint commit；不 pull/rebase/push/release。
