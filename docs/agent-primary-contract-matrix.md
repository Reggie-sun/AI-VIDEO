# AI-VIDEO Contract Routing Matrix

本文件是修改代码前使用的契约路由索引。它回答四个问题：谁拥有该行为、哪些不变量必须保持、哪些替代路径禁止出现，以及最小相关验证是什么。

本文件不是 runtime 状态总账、phase tracker、implementation authorization 或历史验收记录。当前实现真相、阶段方向与 Agent 权限分别由下表中的 canonical source 管理；代码、测试和已验证运行时行为始终优先于文档摘要。

## Document Roles

| Concern | Canonical Source |
| --- | --- |
| Agent authority、工作边界、decision gates、Git 与 completion rules | `AGENTS.md` |
| Changed-path category、mandatory checks 与 local run receipt | `.agent/harness/policy.yaml`、`scripts/agent_harness.py`、`.agent/harness/runs/` |
| 当前已实现行为、local/origin/release truth、已验证与未验证边界 | `docs/v0.2-runtime-baseline.md` |
| Phase dependency、status、future gates 与 slice direction | `docs/v0.2-agentic-production-roadmap.md` |
| 单个 slice 的 accepted scope、tradeoff 与 implementation detail | active spec / plan |
| Executable behavior | source code、tests 与本轮实际 runtime evidence |

使用方法：先用 `make harness-inspect` 根据 task-owned changed paths 查看 mandatory checks，再定位受影响的 surface，确认唯一 owner，保持 `Invariants`，不得引入 `Forbidden Alternate Path`。完成前运行 `make harness-verify` 并保留 passing receipt。下表的 `Focused Verification` 是 human-readable contract；`.agent/harness/policy.yaml` 是对应 executable routing，二者变更时必须同步。

## Cross-Cutting Contracts

| Contract | Invariant |
| --- | --- |
| Product Isolation | Legacy `0.1.x` CLI/Manifest/flat run layout 与 v2 Production Python APIs 保持隔离；除非独立获批，不得借 v2 change 修改 Legacy public surface。 |
| Mutation Ownership | `ProductionStateCommitter` façade及其 private implementation modules 是 v2 project、registry、render、graph、review、repair、image evidence、Manifest activation 与 explicit recovery 的唯一 writer owner。 |
| Timeline and Dependency Ownership | `ResolvedTimeline` 独占 order/frame/sample/timing；P5 resolver 独占 desired fingerprint、precise invalidation 与 rebuild frontier。其它模块只能消费，不得复制推导。 |
| Replay and Recovery | Exact replay 不重复 provider、renderer、analyzer 或 Manifest write；unknown outcome fail closed；recovery 必须显式且不得 blind retry、remint permit、猜测 mixed state 或删除 complete orphan evidence。 |
| Local-First and Provider Safety | Legacy 默认只连接 local ComfyUI；v2 local adapter 必须 loopback-only。任何 remote/paid Provider、live submit、secret 或 cloud egress 继续受 `AGENTS.md` decision gates 约束，且不得成为 fallback。 |
| Evidence Truth | Immutable evidence 必须 content-addressed 并绑定 exact selected inputs。Plan、console text、Agent memory 或 heuristic 不得升级成 runtime、semantic acceptance 或 quality acceptance。 |
| Error Model | 跨模块失败使用 `AiVideoError` 与 `ErrorCode`；retryability 由 typed metadata 决定，常规 CLI 输出不得泄露 raw traceback。 |

## Development Control Surface

| Surface | Primary Owner | Invariants | Forbidden Alternate Path | Focused Verification |
| --- | --- | --- | --- | --- |
| Development Verification Harness | `scripts/agent_harness.py`、`.agent/harness/policy.yaml`、`Makefile` | 只根据 task-owned paths 选择已有 checks；commands 使用 argv + `shell=False`；每次 verify 原子写 local ignored receipt；unknown path fail safe 到 full tests + Architecture Gate。 | Agent dispatch、产品 state mutation、network/live smoke、把历史 receipt 当本轮 proof、静默忽略 unmapped path。 | `make harness-test && make harness-inspect HARNESS_ARGS="--path scripts/agent_harness.py"`；Architecture Gate 仅由对应 source category 选择。 |

## Legacy Runtime Surfaces

| Surface | Primary Owner | Invariants | Forbidden Alternate Path | Focused Verification |
| --- | --- | --- | --- | --- |
| CLI | `src/ai_video/cli.py` | Public commands 保持 `validate`、`run`、`resume`；`validate` 无副作用；typed failure 转成用户可理解的输出。 | 在其他模块解析 CLI、增加隐式 v2 command、绕过 typed error mapping。 | `python -m pytest tests/test_cli.py -q` |
| Config and Paths | `src/ai_video/config.py` | YAML + Pydantic loading；持久化路径为干净绝对路径；non-local ComfyUI 必须 explicit opt-in。 | 在 pipeline/render/client 中重复路径策略或默认放行 remote host。 | `python -m pytest tests/test_config.py -q` |
| Workflow Loading | `src/ai_video/workflow_loader.py` | API JSON 与 UI workflow JSON 都走标准 production loader。 | 裸 JSON/YAML parsing 形成第二条 UI-to-API conversion path。 | `python -m pytest tests/test_workflow_loader.py -q` |
| Workflow Rendering | `src/ai_video/workflow_renderer.py` | Template + binding + shot context 的转换保持纯逻辑、no-network，并提供可定位的 binding path error。 | 在 CLI/pipeline 写死 node ID 或在 renderer 内执行 transport。 | `python -m pytest tests/test_workflow_renderer.py -q` |
| ComfyUI Transport | `src/ai_video/comfy_client.py` | 只负责 HTTP transport、polling、artifact collection 与 typed transport failure；不知道 Shot orchestration。 | 在 client 中实现 Shot order、resume、state activation 或 remote fallback。 | `python -m pytest tests/test_comfy_client.py -q` |
| Pipeline and Resume | `src/ai_video/pipeline.py` | 顺序 Shot execution、bounded typed retry、optional last-frame chaining；resume 从既有 manifest 恢复并跳过仍有效工作。 | 对同一 `run_id` 再调用 `run()` 模拟 resume，或使用 blanket downstream rerun。 | `python -m pytest tests/test_pipeline.py tests/test_resume_e2e.py -q` |
| Legacy Manifest and Output | `src/ai_video/manifest.py`、`src/ai_video/pipeline.py` | Manifest 原子写入；artifact hash 代表已持久化 bytes；flat `runs/<run_id>/` layout、terminal state 与 `final_output` 保持可恢复。 | 非原子终态写入、带 `..` 的持久化路径、无 schema authorization 的 layout mutation。 | `python -m pytest tests/test_manifest.py tests/test_pipeline.py -q` |
| ffmpeg | `src/ai_video/ffmpeg_tools.py` | 负责 probe、clip validation、frame extraction、normalize 与 stitch；stream-copy 不可用时使用既有 re-encode fallback。 | 在 pipeline 复制 ffmpeg policy，或把 v2 renderer ownership隐式并入 Legacy helper。 | `python -m pytest tests/test_ffmpeg_tools.py -q` |
| Architecture Gate | `scripts/architecture_gate/**`、`architecture_gate.toml` | Gate 只做 deterministic local source analysis；normal check 不写 baseline；historical debt 不得掩盖 regression。 | 复用 production dependency graph、通过刷新 baseline 隐藏 regression、机械拆散 cohesive transaction lifecycle。 | `python -m pytest tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q && python -m scripts.architecture_gate check` |

## Production Runtime Surfaces

| Surface | Primary Owner | Invariants | Forbidden Alternate Path | Focused Verification |
| --- | --- | --- | --- | --- |
| P2 Production Reader | `src/ai_video/production/models.py`、`hashing.py`、`paths.py`、`validation.py`、`registry.py`、`project.py` | Strict/read-only/no-network loading of Manifest-selected exact project/registry revision；semantic hash、reference 和 root containment 必须验证。 | 在 reader/registry/validation 中写入、恢复、激活 state，或绕过 exact selected revision。 | `python -m pytest tests/test_production_models.py tests/test_production_validation.py tests/test_production_registry.py tests/test_production_project.py tests/test_config.py tests/test_cli.py -q` |
| P2A State Commit and Recovery | `src/ai_video/production/state_commit.py`、`_state_commit_*` | Single committer owner；immutable snapshot write/fsync/promote/reopen；final Manifest replace 是 logical commit point；recovery 只接受 exact old/new state。 | 第二 writer、reader auto-recovery、overwrite promotion、schema downgrade、猜测或自动激活 orphan。 | `python -m pytest tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_models.py tests/test_production_project.py -q` |
| P3 Composition and HyperFrames | `src/ai_video/production/composition.py`、`hyperframes.py` | `ResolvedTimeline` 是唯一时序真相；只运行 pinned local HyperFrames path；selection 先 durable，verified source/output/state 后才能原子 activation。 | 第二 timeline、alternate renderer fallback、未验证 output activation、导出低层 runner 形成旁路。 | `python -m pytest tests/test_production_composition.py tests/test_production_hyperframes.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P4 Voice and Captions | `src/ai_video/production/audio.py`、`captions.py`、`elevenlabs.py` | Provider-neutral sealed request；budget/egress preview 和 durable intent precede submit；`CaptionTrack` 是 canonical structured source；audio/caption timing 仍归同一 `ResolvedTimeline`。 | 第二 audio timeline、burned-in pixels 充当 caption truth、blind provider retry、ElevenLabs implicit/default path。 | `python -m pytest tests/test_production_audio.py tests/test_production_captions.py tests/test_production_elevenlabs.py tests/test_production_voice_captions_e2e.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P5 Dependency and Selective Rebuild | `src/ai_video/production/dependency.py` | Graph snapshot immutable 且不存 mutable lifecycle；Manifest 独占 desired/applied states；canonical desired recursion 与 precise transitive invalidation保持不变；render unit 只能 final activation 后一起 fresh。 | Blanket stale、第二 resolver、graph 推导 timeline、单独推进 composition/timeline/source/render node。 | `python -m pytest tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P6 Review and Repair | `src/ai_video/production/review.py`、`src/ai_video_mcp/tools/review.py`、`optimize_plan.py`、`apply_optimization.py` | `video-analysis` 只收集 raw evidence；Manifest/committer拥有 review/repair/final-acceptance lifecycle；semantic PASS 需要 policy-selected durable evidence；repair 绑定 exact approved P5 closure。 | Analyzer 自判 Production verdict、heuristic 自升 semantic PASS、未经授权 repair、第二 QA/control path。 | `python -m pytest -p no:cacheprovider tests/test_mcp_review.py tests/test_mcp_optimize_plan.py tests/test_mcp_apply_optimization.py tests/test_production_review.py tests/test_production_repair.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P7 Image Contract and Activation | `src/ai_video/production/image.py`、P7 state-commit/reader extensions | Request 绑定 exact target Shot/role、prompt/parameters、Character/Scene/reference 与 base tuple；measured PNG/provenance durable；committer原子切换 target-only project/registry/graph。 | P7 自建 resolver/writer、automatic reference regeneration、remote Provider、renderer/video generation 或 Legacy CLI path。 | `python -m pytest -p no:cacheprovider tests/test_production_image.py tests/test_production_image_e2e.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
| P7.1 Local Image Adapter and Human Import | `src/ai_video/production/comfy_image.py`、`image_import.py`、sealed workflows/profiles | Concrete adapter 只接受 profile-listed loopback origin并禁用 proxy/redirect；exact components/workflow/nodes 在 R+1 前 preflight；human import 只记录 truthful actor/source/PNG evidence。 | Remote/fallback endpoint、preflight 后补验证、虚构 web backend/request/automation、第二 import writer。 | `python -m pytest -p no:cacheprovider tests/test_production_comfy_image.py tests/test_production_image_import.py tests/test_production_p7_1_local_image_e2e.py tests/test_comfy_client.py tests/test_workflow_loader.py -q`；涉及 host inventory 时另运行 `scripts/check_p7_1_comfy_compatibility.py` |
| Base AI Comic E2E | `tests/test_production_base_ai_comic_e2e.py`、P3-P7 owners | No-Video-Provider path 必须沿唯一 committer/resolver/timeline/review control path完成 durable reopen、exact repair 与 zero-side-effect replay；repair不得 regenerate unaffected P7/voice/caption assets。 | 新 production coordinator、第二 writer/resolver、隐式 Video Provider、用 E2E acceptance 推导 paid/live authorization。 | `python -m pytest -p no:cacheprovider tests/test_production_base_ai_comic_e2e.py -q && python -m scripts.architecture_gate check` |

## Completion Use

本矩阵只定义 surface-level focused gate。最终交付仍必须遵守 `AGENTS.md`：检查实际 diff ownership，通过 Development Harness 运行全部受影响 surface 的 mandatory checks，报告 fresh receipt path，区分本轮执行证据与历史记录，并明确 remaining risk、未验证区域和 publication 状态。
