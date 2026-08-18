# AI-VIDEO Primary Contract Matrix

这份矩阵是 Codex、Claude 以及类似编码 Agent 共用的执行契约。

请与 `AGENTS.md` 配合使用：在修改某个表面前，先找到对应行，保留列出的不变量，并运行要求的验证。

## Global Rules

| Contract Area | 中文说明 |
| --- | --- |
| Product Scope | 当前 `0.1.x` runtime 是 local-first Python CLI + default-local ComfyUI；v0.2 是 Agent-first AI Video / AI Comic Production Harness 的分阶段目标，未落地的 slice 不属于当前行为。 |
| Truth Source | 用户请求 > 代码/测试/运行时证据 > 仓库契约 > plans/specs > `.workflow/` 草稿记录。 |
| Change Style | 小步、可测试、低漂移，并保持模块边界稳定。 |
| Error Model | 跨模块统一使用 `AiVideoError` 与 `ErrorCode`。 |
| Dependency Policy | 除非有明确理由且获得请求，否则不新增运行时依赖。 |
| Output Policy | Legacy run 保持当前 flat `runs/<run_id>/` layout；v2 layout 只能由显式 v2 config 和已批准的 Manifest v2 slice 创建。 |
| Version Gate | P0-P5 已完成各自阶段，P5 已于 `0d663566c4db4542922e38d770608e3e02d53745` 合入并 push 到 `origin/main`，merged-main full verification 为 `1386 passed, 4 skipped`。P6 已完成、独立 review `accept with concerns` 并通过 `be28dc4` checkpoint 整合 local `main`；focused `739 passed`、整合并行 local-main commits 后 full `1462 passed, 4 skipped`；P6 未 push/release。P7 已在独立 branch 完成 runtime acceptance；其 lineage 与 P3-P7 combined Base AI Comic E2E 已在 `codex/base-ai-comic-e2e` 验收，仍未 merge 到 `main`、push/release。P8 runtime 与 Paid Provider Gate 均未实现；后续 slice 仍必须有独立 plan、授权、验收、rollback 和 contract/docs/tests 更新。 |
| Agent Boundary | Codex 是 Production Agent；仓库提供 durable state、validation、provenance、dependency、render 和 QA harness，不实现第二套通用 Agent runtime。 |
| Renderer Ownership | P3/P4 `ResolvedTimeline` 是唯一 frame/sample ordering 与 timing 真相源；P4 只向它增加 canonical audio spans 与 caption cues，不另造 audio timeline。当前唯一实现的 renderer 是 pinned local HyperFrames；caption layout/drawing 归 selected renderer。Remotion、Captions.ai final-render path 与其它 renderer 仍未实现并必须 fail closed；不得 fallback、串联或 double render。 |

## Contract Matrix

| Surface | Canonical Files | Invariants To Preserve | Common Safe Changes | Required Validation |
| --- | --- | --- | --- | --- |
| CLI Contract | `src/ai_video/cli.py`、`README.md`、`tests/test_cli.py` | 公共命令保持为 `validate`、`run`、`resume`。`validate` 必须无副作用。类型化失败要输出面向用户的错误信息，而不是原始 traceback。 | 增加小型参数、优化提示文案、接入新的内部选项、扩展进度输出。 | `pytest tests/test_cli.py -v` |
| Config Loading & Path Resolution | `src/ai_video/config.py`、`src/ai_video/models.py`、`tests/test_config.py` | project 和 shot 文件通过 YAML + Pydantic 加载。相对路径解析为干净的绝对路径。非本地 ComfyUI 主机需要显式 opt-in。未知角色必须报错。 | 增加校验、优化标准化逻辑、扩展兼容字段且不破坏现有配置。 | `pytest tests/test_config.py -v` |
| Workflow Loading | `src/ai_video/workflow_loader.py`、`tests/test_workflow_loader.py` | 同时接受 API JSON 和 UI workflow JSON。UI 图转换必须走标准 loader，而不是在别处重复实现。 | 优化校验或转换规则，同时保持现有 fixture 格式继续可用。 | `pytest tests/test_workflow_loader.py -v` |
| Workflow Rendering | `src/ai_video/workflow_renderer.py`、`tests/test_workflow_renderer.py` | 渲染必须是纯逻辑：把 template + binding + shot context 转成渲染后的 workflow，且不触发网络访问。binding 失败要给出可定位的 path 信息。 | 增加 binding 覆盖、优化 output prefix 处理、通过同一 path helper 支持新映射字段。 | `pytest tests/test_workflow_renderer.py -v` |
| ComfyUI Transport | `src/ai_video/comfy_client.py`、`tests/test_comfy_client.py` | client 只负责 HTTP 传输、轮询、产物收集和清理钩子。它不能知道 shot 编排顺序。本地优先策略不变。 | 优化重试行为、错误映射、轮询细节或产物选择。 | `pytest tests/test_comfy_client.py -v` |
| Pipeline Orchestration | `src/ai_video/pipeline.py`、`tests/test_pipeline.py`、`tests/test_resume_e2e.py` | shots 必须按顺序执行。上一帧可喂给下一 shot。重试要有边界。progress callback 应为可选且不侵入。resume 必须基于 manifest 状态并跳过仍然有效的工作。 | 优化进度输出、重试记录、stale 处理或 resume 决策。 | `pytest tests/test_pipeline.py tests/test_resume_e2e.py -v` |
| Manifest Persistence | `src/ai_video/manifest.py`、`tests/test_manifest.py` | manifest 写入必须原子化。哈希必须代表已持久化产物。成功 shot 的有效性必须基于哈希判断。下游 stale 状态必须来自上游变化。 | 增加 helper、扩展 manifest 校验、收紧 stale 检测。 | `pytest tests/test_manifest.py -v` |
| ffmpeg Boundary | `src/ai_video/ffmpeg_tools.py`、`tests/test_ffmpeg_tools.py` | ffmpeg helper 负责 probe、校验、抽帧、标准化与最终拼接。当 stream copy 不可用时，拼接必须具备兜底能力。 | 优化 fallback 行为、标准化参数或命令构造，同时保持输出兼容。 | `pytest tests/test_ffmpeg_tools.py -v` |
| Test Fixtures & Realism | `tests/conftest.py`、所有测试 | 在可行时，测试夹具应复用生产加载路径。编排测试优先使用 fake。除非用户明确要求，否则真实 ComfyUI 只是可选项。 | 扩展 fixtures、增加 e2e 风格 fake 测试、提高真实性但不引入网络依赖。 | 如果 fixture 改动较广，运行受影响测试文件外加 `pytest -v`。 |
| Architecture Harness Gate | `architecture_gate.toml`、`.architecture/architecture-baseline.json`、`scripts/architecture_gate/**`、`tests/test_architecture_gate*.py` | Gate 只做 deterministic local source analysis：effective LOC debt ratchet、module-body first-party import cycle regression 与 non-blocking fan-out signal。Normal check 永不写 baseline；historical debt 不是永久豁免，显式 baseline update 不得用于隐藏 regression。 | 收紧低误报规则、generated/vendor conventions 或 structured finding；不得复用 production dependency graph、改变业务 runtime、把 transaction lifecycle 机械拆散。 | `python -m pytest tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q && python -m scripts.architecture_gate check` |
| Output Layout | `README.md`、`src/ai_video/pipeline.py`、manifest 相关测试 | runs 必须写入 `runs/<run_id>/`，包含 manifest、shot 产物、normalized clips 和 final output。路径必须足够稳定，便于 resume 和排查工具使用。 | 增加额外元数据或调试产物，但不能破坏现有预期文件。 | `pytest tests/test_pipeline.py tests/test_manifest.py -v` |
| v2 Production Project Core | `src/ai_video/production/**`、`tests/test_production_*.py` | P2 只读加载 Manifest-selected project/registry exact revision；creative/asset refs 必须 content-addressed 且留在固定 project roots。不拥有 writer、lifecycle 或 desired fingerprint。 | 收紧 schema、strategy、reference、hash 或 containment validation，保持 no-network 和 Legacy isolation。 | `pytest tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_config.py tests/test_cli.py -q` |
| P2A Production State Commit | `src/ai_video/production/models.py`、`src/ai_video/production/project.py`、`src/ai_video/production/state_commit.py`、`tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py` | `ProductionManifest` 是唯一 lifecycle owner；nested project/registry pointer 必须固定 exact path、semantic identity 和 file hash。`ProductionStateCommitter` 是唯一 writer/recovery owner；POSIX same-filesystem `state/commit.lock` 下 snapshot temp 必须 file-fsync、promote-without-overwrite、parent-directory-fsync 并 reopen verify。running/failed lifecycle 也会 durable Manifest write；仅 final active-pointer replace 是 single logical commit point。恢复必须显式，只接受 exact old/new pair；bounded owned temp 可清理，complete orphan 只能 preserve/report。P2 reader 仍只读，root `project.yaml` 是 stable validated entrypoint 而非 active bytes truth。 | 补强 P2A integrity/recovery validation，不能增加第二 writer/control plane、auto-recovery、CLI 或改变 Legacy Manifest/layout。 | `pytest tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P3 Deterministic Composition + HyperFrames | `src/ai_video/production/composition.py`、`src/ai_video/production/hyperframes.py`、P2/P2A render-state extensions、`tests/test_production_composition.py`、`tests/test_production_hyperframes.py` | 只接受 local raster `STATIC_IMAGE` + zero-duration `CUT`；`ResolvedTimeline` 是唯一时序真相。只运行 exact `hyperframes@0.7.103`，每个 tool process fresh user/net/PID namespace、controlled env、非 version root `--json`、无 fallback。Selection 必须先 durable；source/lint/check/render/held-FD verify 后，P2A writer 才能切换一个 `active_render_state`。Manifest 2.0/2.1/2.2 reader兼容并保留历史 pair-change pointer 行为；Manifest 2.3 由 P5 precise lifecycle 取代 blanket stale。Recovery按 exact selected identities，完整 orphan只 preserve/report。 | 收紧 composition/source/receipt/path/replay/recovery validation；P4 只能通过既有 Composition/ResolvedTimeline/HyperFrames contract 增加 audio/caption 输入。不能导出低层 runner/adapter、增加 Remotion、CLI 或远程 fallback。 | `python -m pytest tests/test_production_models.py tests/test_production_project.py tests/test_production_composition.py tests/test_production_hyperframes.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P4 Voice and Captions | `src/ai_video/production/audio.py`、`src/ai_video/production/captions.py`、`src/ai_video/production/elevenlabs.py`、P2/P2A/Composition/HyperFrames extensions、`tests/test_production_audio.py`、`tests/test_production_captions.py`、`tests/test_production_elevenlabs.py`、`tests/test_production_voice_captions_e2e.py` | Audio kinds 固定为 `dialogue | narration | ambience | sfx | bgm`；`VoiceGenerationRequest` immutable/self-sealing，provider flow 必须 preview budget/egress、R+1 request、R+2 submit intent + committer-issued one-use permit、materialize/probe/hash/register/alignment、cost/provenance receipt、R+3 candidate 与 R+4 activation。`CaptionTrack` 是 structured canonical source，不能退化为 burned-in pixels。`ResolvedTimeline` 继续唯一 order/frame/sample/timing owner；`ProductionStateCommitter` 继续唯一 Manifest / Registry writer/recovery owner。Unknown outcome 禁止 blind resubmit，replay 不得再次调用 provider/renderer。 | 收紧 audio/caption/receipt/fingerprint/path/replay/recovery validation；默认只用 deterministic fixtures、fake provider 和 no-network。ElevenLabs adapter 仅 explicit opt-in candidate，不从 package root 导出；真实调用须另获授权并重新满足 budget、egress、secret 与 crash-safe persistence gate。P5 可消费这里暴露的 typed fingerprints，但不能把 lifecycle 写回 P4 modules；不能增加 Captions.ai/Remotion、第二 renderer/writer、CLI 或 cloud fallback。 | `python -m pytest tests/test_production_audio.py tests/test_production_captions.py tests/test_production_elevenlabs.py tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_production_composition.py tests/test_production_hyperframes.py tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_voice_captions_e2e.py tests/test_config.py tests/test_cli.py -q` |
| P5 Dependency Graph + Selective Rebuild | `src/ai_video/production/dependency.py`、P5 models/project/state-commit extensions、`tests/test_production_dependency.py`、`tests/test_production_selective_rebuild.py`、P5 commit/recovery tests | `DependencyGraphSnapshot` immutable/content-addressed，只含 typed nodes/edges/reasons/contributions；`ProductionManifest` 2.3+ 独占 active graph、desired/applied fingerprints 与 fresh/stale/failed/blocked/superseded lifecycle；`ProductionStateCommitter` 独占 graph snapshot write/co-activation/recovery。Desired fingerprint canonical递归消费 upstream desired，same input stop propagation；failed same-desired 不auto-retry。`ResolvedTimeline` 仍唯一 order/frame/sample/timing owner。Composition、ResolvedTimeline、renderer source与render必须由同一次final render activation原子证明，旧render pointer不得分别推进其中任何node。 | 收紧 graph/schema/hash/path/resolution/frontier/replay/recovery validation，使用 deterministic fake/no-network fixtures。不得增加第二 Manifest/registry/graph writer、auto recovery、blanket stale、timeline 推导、第二 renderer、CLI 或 Legacy layout change；P6/P7 只能复用该 resolver，不得把 QA/image lifecycle 写进 graph 或 `dependency.py`。 | `python -m pytest tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_models.py tests/test_production_registry.py tests/test_production_project.py tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_composition.py tests/test_production_hyperframes.py tests/test_production_audio.py tests/test_production_captions.py tests/test_production_elevenlabs.py tests/test_production_voice_captions_e2e.py tests/test_config.py tests/test_cli.py -q` |
| P6 Codex Review and Repair Harness | `src/ai_video/production/review.py`、P6 models/project/state-commit extensions、`src/ai_video_mcp/tools/review.py`、`src/ai_video_mcp/tools/optimize_plan.py`、`src/ai_video_mcp/tools/apply_optimization.py`、`tests/test_production_review.py`、`tests/test_production_repair.py`、对应 MCP/commit/recovery tests | `video-analysis` 只拥有 technical raw evidence collection；Manifest 2.4 是 selected QA policy、review/repair/outcome/final-acceptance lifecycle 的唯一 mutable owner，`ProductionStateCommitter` 仍是唯一 receipt/Manifest writer 和 recovery owner。Review Receipt 必须 immutable/content-addressed/versioned，并绑定 exact graph revision、timeline、render/output、policy、evidence 和 tool identity。`technical | layout | strategy | semantic | final_acceptance` 全部 fail closed；semantic pass 只接受 policy-selected evaluator/human durable evidence。Repair 默认拒绝，只能由 trusted authorizer 批准并绑定 exact targets/P5 closure；禁止 blanket stale。Policy-only change 只 stale affected review，final acceptance 必须绑定当前 graph/timeline/render 与 fresh receipts。 | 收紧 strategy-aware adjudication、durable evidence/reopen、authorization、exact invalidation、replay/unknown-outcome/recovery。必须保持 P5 graph immutable 且不含 review status，`ResolvedTimeline` 继续唯一时序 owner，final render activation 继续原子 fresh；不得增加第二 QA/repair control path、writer、automatic recovery、renderer、Provider、CLI 或 Legacy layout change。默认仅使用 deterministic fake/no-network evidence。 | `python -m pytest -p no:cacheprovider tests/test_mcp_review.py tests/test_mcp_optimize_plan.py tests/test_mcp_apply_optimization.py tests/test_production_models.py tests/test_production_review.py tests/test_production_repair.py tests/test_production_project.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P7 Image Asset Generation | `src/ai_video/production/image.py`、P7 models/project/state-commit extensions、`tests/test_production_image.py`、`tests/test_production_image_e2e.py`、对应 commit/recovery tests | `ImageGenerationRequest` immutable/self-sealing，必须绑定 exact target Shot/role、prompt/parameters、Character/Scene/reference identities 与 base project/registry/graph。`ImageAssetProvider` 只接受 committer-issued one-use permit；repository 只保证 local injected contract，不提供 concrete/live Provider。Manifest 2.5 独占 image lifecycle，并在后续 voice/render/review/repair/recovery writes 中完整保留 P7 evidence；`ProductionStateCommitter` 是 request/submit intent/result/PNG/provenance、target-only Shot revision、append-only Registry、graph activation和explicit recovery的唯一public writer。P7复用未修改的P5 resolver；exact replay零 provider/materializer/Manifest write，recovery不remint permit或blind resubmit。 | 收紧 request/result/PNG/provenance/path/candidate/replay/recovery validation，默认只用 deterministic fake/no-network fixtures。不得增加 concrete/remote Provider、第二 writer/resolver、automatic reference regeneration、renderer、video generation、CLI 或 Legacy layout change。 | `python -m pytest -p no:cacheprovider tests/test_production_image.py tests/test_production_image_e2e.py tests/test_production_models.py tests/test_production_registry.py tests/test_production_validation.py tests/test_production_project.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_review.py tests/test_production_repair.py -q` |
| Base AI Comic E2E | `tests/test_production_base_ai_comic_e2e.py`、`tests/production_e2e_support.py`、`tests/production_project_factory.py`、P3-P7 production owners | No-Video-Provider path 必须从 exact Character/Scene references 和 two-Shot P7 PNGs 完成 voice/captions、canonical timeline、initial render、strategy-aware FAIL、approved exact repair closure、rerender、PASS reviews 与 Final Acceptance。Manifest 2.5 必须跨全链保留 P7 evidence；repair 只 stale `composition:main`、`timeline:main`、`renderer-source:main`、`render:main`，不得 regenerate P7 assets。Fresh runtime 必须 reopen durable evidence，exact replay 的 image/voice/analyzer/renderer calls 和 Manifest writes 全为零。 | 只补强 combined E2E、restart/replay counters、2.0-2.5 compatibility 或 read-only evidence reopen。不得增加 schema、public CLI、production coordinator、第二 writer/resolver、Video Provider、Paid Provider Gate、asset layout 或 runtime dependency。 | Task 8 focused command + `python -m pytest -p no:cacheprovider -q` + `python -m scripts.architecture_gate check` |

## Cross-Cutting Contracts

### Resume Contract

任何触及 resume 的改动，都必须保留以下规则：

- resume 从 `manifest.json` 启动，而不是重新启动一个新 run。
- 已完成且仍有效的 shots 要被跳过。
- 无效、失败或 stale 的 shots 可以被重跑。
- 缺失的下游产物应触发修复或重跑，而不是静默成功。
- 恢复成功后，最终输出和 manifest 终态必须再次持久化。

最低验证：

```bash
pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -v
```

### Manifest Contract

任何触及 manifest 结构或持久化的改动，都必须保留：

- 原子写入，
- 稳定、可读的 JSON，
- 可持久化的 `final_output`，
- 在可用时可持久化的 config/template/binding 路径与哈希字段，
- 用于有效性检查的 per-shot 产物哈希。

最低验证：

```bash
pytest tests/test_manifest.py tests/test_pipeline.py -v
```

### Local-First Contract

Agent 不得悄悄侵蚀本地优先承诺。

在没有用户明确指示时，不得引入以下内容：

- 远程服务依赖，
- 云端托管的视频生成 API，
- ComfyUI 的后台进程管理器，
- 遥测或外部状态同步，
- 把前端或 API server 变成 CLI 的隐式前置条件。

### v0.2 Planning Gate

- 当前 code/tests 仍是 runtime truth；spec 和 plan 不能覆盖未实现行为。
- P0 只迁移 product/contract 文档；不得把 spec 写成 runtime truth。
- 本地 P1 只稳定 Legacy runtime，未引入新 product domain；其 plan 作为 historical stabilization record 保留。
- P2 已建立 ProductionProject、Assets、Shot visual strategy 的 read-only durable contract；它不拥有 writer、renderer 或云服务。
- P2A 已 independently accepted：唯一 writer/recovery owner 写 immutable v2 snapshots，并通过 nested active pointers and one Manifest replace activate exact pair。它不改变 P2 reader 的只读语义或 Legacy Manifest v1/layout；已随 P5 ancestry 进入 `origin/main`，尚未 release。
- P3 已于 `3296b713` fast-forward 合入并保留独立 review、committed-fixture render 与 fail-closed trace proof；已随 P5 ancestry 进入 `origin/main`，尚未 release。当前只允许一个 pinned local HyperFrames path，Remotion 与其它 renderer 必须拒绝。
- P4 已于 `f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80` fast-forward 合入并随 P5 ancestry 进入 `origin/main`；merged-main full verification 为 `1094 passed, 4 skipped`，尚未 release。ElevenLabs 只有 thin explicit-opt-in adapter，未进行 live call、secret 读取或 quota 使用；runtime authorization 不等于 live-call authorization。
- P5 已于 `0d663566c4db4542922e38d770608e3e02d53745` 合入并 push 到 `origin/main`，实现 immutable graph、Manifest 2.3 lifecycle、precise resolver 与 explicit recovery，并以 deterministic mutation matrix 完成 acceptance；canonical `1256 passed, 3 skipped`、Legacy `58 passed`、merged-main full `1386 passed, 4 skipped`；尚未 release。P5 不改变 Legacy CLI/Manifest/layout。
- P6 已完成、独立 review `accept with concerns` 并通过 `be28dc4` checkpoint 整合 local `main`；Manifest 2.4 与 `ProductionStateCommitter` 拥有 durable review/repair/final acceptance，P5 graph 仍不保存 mutable review status。Focused `739 passed`、full `1462 passed, 4 skipped`；无 blocking issue，尚未 push/release。
- P7 已在 `codex/p7-image-assets-20260817` 完成 runtime acceptance；Manifest 2.5 与 `ProductionStateCommitter` 拥有 durable image request/submit/result/provenance/activation/recovery，既有 P5 resolver 未修改。Canonical `1128 passed`、image E2E `7 passed`、full `1686 passed, 4 skipped`、Architecture Gate PASS；无 network/live Provider/renderer/video generation，尚未 merge 到 `main`、push/release。
- Base AI Comic E2E 已在 `codex/base-ai-comic-e2e` 完成 acceptance，证明 P3-P7 no-Video-Provider path、exact repair closure、restart reopen 与 zero-side-effect replay；该 branch 尚未 merge 到 `main`、push/release，也没有新增 schema、CLI、coordinator、Provider 或 asset layout。
- Production QA 必须使用 Shot `visual_strategy` 与 exact timeline windows；当前 `static_visuals` heuristic 不得自动否决合法的 `static_image`、`image_motion` 或 `motion_graphics` Shot。
- P8 runtime 与 Paid Provider Gate 仍未实现。开始 P8 前必须先单独设计、计划、实现并验收 Paid Provider Gate；任何 paid Provider submit 仍受 Budget Guard、Cloud Egress、secret redaction 和 crash-safe persistence gate。
- 新 CLI、Manifest schema、artifact layout、远程行为、Audio 或 dependency 仍命中下方 Change Escalation Matrix。

## Change Escalation Matrix

| Proposed Change | Default Agent Action |
| --- | --- |
| Tighten validation while keeping current examples working | 直接实现，并补测试。 |
| Add an optional field compatible with existing configs | 直接实现；如果用户可见则同步补测试和文档。 |
| Change CLI names, flags, or exit-code meanings | 暂停并确认。 |
| Change manifest schema or artifact layout | 暂停并确认。 |
| Add a runtime dependency | 暂停并确认。 |
| Introduce remote/networked product behavior beyond local ComfyUI | 暂停并确认。 |
| Add frontend / API / server subsystems | 暂停并确认。 |

## Minimum Done Criteria

Agent 在宣称完成前，至少确认：

1. 上表中被改动到的契约行仍然成立。
2. 对应测试已经运行。
3. 用户可见行为变化已反映到 `README.md` 或相关文档。
4. 任何剩余缺口都已明确说明。
