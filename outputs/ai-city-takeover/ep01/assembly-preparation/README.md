# EP01 Assembly Input Preparation

这里只准备实际素材的 typed 输入，不创建 `ProductionProject`、Manifest、adoption、CompositionSpec 或 ResolvedTimeline，也不调用 Provider。当前六段实际视频包括四个独立新闻图形、A01-v2 与已取回但尚待最终 Gate 的 C。

## Build And Validate

在仓库根执行：

```bash
PYTHONPATH=src python outputs/ai-city-takeover/ep01/assembly-preparation/prepare.py build
PYTHONPATH=src python outputs/ai-city-takeover/ep01/assembly-preparation/prepare.py validate
PYTHONPATH=src python outputs/ai-city-takeover/ep01/assembly-preparation/prepare.py validate --require-preview-ready
```

最后一条应退出 **2**。它明确列出缺失项，不能用已存在的视频替代歌曲、B 演唱、口型、逐字时间或最终剪点。八个 Shot 候选均为无秒数的 `content_driven`；生成阶段的 6 秒窗口不是剪辑镜长。

## Prepared Data

- `asset-candidates.json`：六个现有 `AssetRecord` 类型的 inspection/import 候选，保留实际 rational FPS、帧数、视频流时长及 bytes identity。
- `registry-candidate.json`：仅四个普通 CFR 图形素材，未采用到实际项目。图形生成来源与实际 review 文件 hash 保存在 content-addressed authoring input 中。
- `payload-map.json`、`prepared-artifacts/evidence/authoring-input/`：未来 committer 所需的真实图形 payload 来源及 sealed 输入。`prepared_graphics_artifacts()` 返回现有 `PreparedArtifact` 对象和真实 bytes，不写目标。
- `qualification-inspections.json`：A/C 单独保留为未 admission 的 source，不混入普通 Registry 候选。真实付费 request/fetch 与当前 Gate 来源保留，不能将它们伪装成 Production 激活。
- `probe-receipts/`、`development-measurements/`：从新鲜 held-FD 的真实 ffprobe 构造公开 `VideoProbeReceipt.create(request, fetch_receipt, measured)`，并通过现有 preview probe validator；明确只用于 `development_preview_measurement_only`。
- `shots/`、`composition-inputs.json`：八个 typed Shot 及角色选择候选。A/C/B 的 primary role 保持未绑定；图形可作为 ordinary import 候选。`web-cache` 只列为独立 editorial explanation，不能贴到 A03 显示器背面。尚未封存其剪辑摆放或复用素材窗口。

`prepared_graphics_artifacts()` 后应由既有 `prepared_authoring_input_references()` 收集来源，再经现有 bootstrap/authoring/committer。不要直接编辑目标 Registry 或 Shot YAML。

## Existing Preview Admission

A/C 的 native VFR 不能改写成 30fps，也不能通过只收整数 FPS 的 `prepare_canvas_video_assets`。普通 primary role 绑定会进入 Production frame-rate contract，不能据此冒充 preview。

既有合法入口是 `production.qualification_preview_input.prepare_qualification_preview_input`。它需要独立 target project/root、原 paid qualification source、准确的 `VideoProbeReceipt` 和已选 `RepairPreviewUse(scope="replacement_audio_preview")`；source 仍保持原生命周期。之后由既有 CompositionSpec 2.3、真实 P4 音轨及 normal-speed preview 条件解析为 `development_audio_preview`。不要给 ResolvedTimeline 手写 usage scope 或另建时间线。

当前 admission 仍要求 `trim_start_frame + trim_duration_frames <= source_native_frame_count`。A01-v2 实测 145 帧；若以后以 30fps preview clock 选择窗口，此边界最多 145 格（约 4.833 秒），不能伪造 180 格。约 4 秒窗口只能作为待歌曲实测后的选择，当前没有封存。

公开 `probe_generated_video_candidate` 已用真实 request/fetch/ffprobe 执行，`probe-admission/` 仍保留严格 Production 输出契约的实际拒绝。现有 development capture 只核验真实 measurement 与 request/fetch/bytes 绑定；因此通过其公开 receipt constructor 准备独立测量 receipt，不改写 FPS、时长或帧数，也没有执行 nominal-endpoint recovery。`development-measurements/` 明确记录 `production_contract_pass=false`，不能把这份测量 receipt 说成 Production probe PASS。

已有真实测量 receipt 可以在 Parent 选定 target project、准确 `RepairPreviewUse` 和真实 P4 音轨后交给现有 qualification preview admission。当前尚未创建该 admission、目标状态或时间线。

## Remaining Inputs

实际 Suno asset/来源、B 演唱源与真实 lip-sync Gate、歌曲实测驱动的八段 trim/duration、字幕时序、target project 与 A/C preview admission、实际 P4 音轨及其约束仍需补齐。C Gate 以当前构建捕获的真实状态为准，未通过时同样阻塞；最新 Parent 已完成其 canonical Gate PASS。源音统一 `MUTE`，最终声轨只归 P4；没有创建空白音轨、伪歌词时间或完整成片。

## Captioned Music Admission

外部歌曲字幕现在可通过显式 `development-qualification-preview/2` 准备；未提供 `captioned_music` 仍使用原 `/1`，原片 DIALOGUE 检查保留。新 binding 封存唯一 global MUSIC/BGM 音轨、音讯 SHA、真实样本窗口及各字幕的 asset ID、bytes SHA、script/transcript hashes。Suno 的真实 GENERATED 来源须保留，不能改成普通 imported audio 或 DIALOGUE。

先经现有 audio/caption preparation 得到实际歌曲与 canonical CaptionTrack 候选，将这些 records 供给 `prepare_qualification_preview_input(..., captioned_music=...)` 做只读核验。目标可先由 committer bootstrap 未消费的捕获素材，再用一次 `prepare_audio_registry_commit` 同时写入歌曲、字幕和 style；未导入前不能解析该 composition。随后重开标准项目、实际选用同一 binding 的 `/2` 视觉，再由 `resolve_composition` 生成唯一 `development_audio_preview`。不得直接写 Registry/Manifest 或手造 timeline。

歌曲必须完整覆盖成片样本窗口；字幕只能引用封存的歌曲及自身确切内容。英文与中文可分别保留不同的 script/transcript identity。binding 证明作者选定的字幕身份，不证明 ASR、演唱、对嘴或人工观感。本轮仅有 fixture 接线验证，尚未创建真实 EP01 歌曲 binding、字幕、剪点或成片。
