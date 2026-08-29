---
record_kind: session_summary
topic_id: drama-m6-d-shot-01-preflight-stop
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Drama M6-D Shot 01 Preflight Stop Record

Date: 2026-08-29

## Purpose

本文记录B-D0通过后首次获授权启动的M6-D empirical slice，以及它在任何Provider submit前触发的exact
readiness stop。该checkpoint不是Drama media attempt、quality verdict、P6、Final Acceptance或新的fixture/
baseline decision。

## Current Runtime Truth

Current user已明确授权“开始M6-D”。该授权允许进入accepted execution path，但不放宽
`VideoPlanningRequest -> VideoPlanner.plan -> require_current_video_plan -> ShotReadinessGate`、Router、adapter、
canonical Provider lifecycle或per-Shot post-media gate。

Initial canonical pre-submit在进入Planner前缺少Project/Registry materialization：没有selected Project/Registry
revision/content hashes，也没有Project-selected Drama Character/Scene/Shot revisions。当前只可重新打开sealed
Shot 01 authoring facts：

- canonical Shot：`drama.shot.waiting-room.001@1`；
- covered character revisions：`drama.character.lin-lan@1`、`drama.character.lin-jun@1`；
- duration：minimum `4.5s`、target `5.0s`、maximum `6.0s`；
- source-audio authoring-intent proposal：`GENERATED + KEEP`；Provider尚未selected，故没有resolved
  SourceAudioPolicy或exact request binding；该proposal不是accepted SourceAudioPolicy；
- retry boundary：effective submit limit `0`，没有进入OpenVideo或Provider retry。

未产生或保留diagnostic `VideoPlanningRequest`：historical baseline helper的test-template Character/Scene facts与sealed
Drama事实不一致，不能作为M6-D projection或下游risk evidence。Planner、Router、adapter、resolved request、
`VideoGenerationService.start`与submit均未进入。

## Independent Provider-Candidate Inspection

`minimax-h3-t8-t2va-quality-v1`只是本次未到达的candidate capability，不是selected Provider。Sealed profile facts：

- profile content hash：`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`；
- workflow SHA-256：`6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5`；
- binding SHA-256：`3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564`；
- exact output capability：124 frames、24 fps、1344x768、MP4、native audio required；
- profile ComfyUI commit：`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- current clean ComfyUI checkout：`e01fb4c56b7a88149d469b99cbbfe3223d715054`。

T8 node、VideoHelperSuite与SageAttention identities匹配profile，但ComfyUI commit不匹配；这是unreached advisory
candidate risk，不是Router decision或current primary blocker。
`ComfyUIT8VideoProvider.preflight()`按current code必须fail closed。ComfyUI在检查时为inactive，本轮没有为了制造
readiness而切换external checkout、启动server或修改runtime。

## Verification And Evidence

Exact local-only blocker record：

```text
runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-execution-preflight.json
SHA-256: 8c7031f42a068b953a75a7f7b0bb9dfd5611d516c0821657dc34d94723683d5c
```

它绑定accepted authoring package、fixture、baseline、execution-gate与historical accepted rubric SHA，明确记录
canonical Project/Registry materialization缺失、仅来自sealed fixture的Shot facts、未resolved的source-audio intent、
未到达的candidate profile inspection、zero effects与`next_shot_submit_allowed=false`。JSON已通过
`python -m json.tool`。独立native explorer与`reviewer_xhigh`复核了fixture、canonical-entry contract及candidate
runtime boundary；reviewer拒绝了含test-template facts的早期diagnostic projection，当前record已完全移除该evidence。

本轮effects：

- Provider selection/preview/start/submit/fetch：0；
- ComfyUI start：0；
- Provider-native prompt authoring：0；
- generated/retried/repaired/assembled media：0；
- project-local `video-analysis` calls：0；
- Manifest/Registry activation、P6、Final Acceptance：0。

## Assessment

At the initial stop，`B-D0=PASS`保持不变；`M6-D=NOT_EVALUATED`并处于`STOP_BEFORE_SUBMIT`。这不是per-Shot HUMAN FAIL，因为没有
exact Shot MP4可以播放或判定。Commercial `M6-C=HUMAN_FAIL`与`B-X=FAIL`也不向Drama继承任何finding。

At the initial stop，primary blocker是sealed Drama package尚未通过current canonical seam materialize为Project/Registry-selected Shot；
historical baseline helper创建的test project加in-memory Shot copy不能替代该authority。该缺口不能在本slice内通过
手工构造runtime models、借用Commercial media、把baseline reference MP4改作conditioning input、修改sealed
fixture/baseline或绕过canonical authoring/loading seam来处理。future selected Provider/runtime也须从新的canonical
projection开始重新取得current executable proof。

## Remaining Work And Guardrails

Initial next step要求独立owner选择并批准canonical Drama Project/Registry materialization seam；该授权已由current
user在后续turn明确给出。Initial slice本身禁止修改runtime/code/tests，因此当时正确停在这里。

任何未来resume必须重新打开本record与exact preflight JSON，重跑fresh Planner/readiness，并在得到current
`VerifiedGenerationRequirementProjection`之后才可进入Router selection。新run、new Shot bytes或任何input/profile/
rubric/runtime identity变化都不得继承本次blocked decision之外的evidence。

## Authorized Materialization Follow-up

Current user随后明确授权且只授权canonical Drama Project/Registry materialization seam：不得改变fixture/baseline，
不得选择Provider、编写native prompt、启动ComfyUI、submit或生成media。Implementation保持
`ProductionStateCommitter.bootstrap_initial_state()`为唯一初始writer，并新增最小additive pre-generation contract：

- `AssetRoleRequirement.asset_ids`可以显式为空，但strict `generated_video` validation只接受一个empty target role，且
  `allowed_asset_types`必须exact为`VIDEO`；其他visual strategies仍须绑定concrete assets；
- existing generated-video candidate path继续把该same target role替换为exact output asset ID，并由existing committer
  原子选择Project/Registry/Graph candidate；pending state不注册fake MP4或placeholder AssetRecord；
- provider-neutral intent新增显式`GenerationOperation.TEXT_TO_VIDEO`。它不能携带media reference role/asset，且在
  exact-terminal/reference continuity存在时fail closed；Character/Scene只作为exact typed semantic context，不冒充media
  evidence。

Run-local driver从accepted package envelope绑定的exact Git blobs读取package与fixture，忠实投影Brief、Story、两个
Character、Scene、Storyboard与三个ordered Shots，再以empty content-addressed Registry完成canonical bootstrap。它没有
import或复用`tests/production_project_factory.py`，没有手写Manifest/Registry，也没有读取historical baseline helper。

Current exact evidence：

```text
runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-canonical-materialization.json
SHA-256: 75be2e494e44b5b253d730f9c9daca366806e09209c7e5e5e231c014a1b09f71

selected Project content hash:
940f0ceee3148ba1d4dab4a5b7bcbc2adc3229c5964f1705149bec1e9d14dfc1

selected empty Registry identity:
13a9404d3ec6bb3de0ec00871cd22dd5ca861ca8ea413fdfe13ea145e6c2ec1b

Shot 01 VideoPlanningRequest hash:
92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f

Shot 01 verified generation projection hash:
9481519d2b4929e6abd9b0826cc5731ea54f60526ec414ffa07279d32f0a57fb
```

Strict reopen得到exact selected Character/Scene/ordered Shot content hashes；Planner outcome为`proposed`、generation mode
为`text_to_video`，Shot Readiness返回verified requirement。Canonical bootstrap exact replay对14个Production files验证
为zero-write。最新focused contract组合为`218 passed`；扩展Production compatibility组合为`1040 passed`。此外，
`python -m scripts.architecture_gate check`、`python -m scripts.docs_contract_gate check`、
`python -m scripts.agent_harness policy-audit`与`git diff --check`均通过；Architecture Gate只报告pre-existing warning/info，
没有error。

## Current Assessment After Follow-up

原`CANONICAL_PROJECT_REGISTRY_PROJECTION_NOT_MATERIALIZED` blocker已由current executable evidence解除，但M6-D仍为
`NOT_EVALUATED / STOP_BEFORE_SUBMIT`。新的唯一primary blocker是
`ACTIVE_PRE_GENERATION_DEPENDENCY_GRAPH_NOT_MATERIALIZED`：current Manifest为2.0且没有active Dependency Graph；
`begin_video_generation()`要求Manifest >=2.7与active graph。Current generic graph/composition path仍要求concrete visual
layer asset，不能用empty graph、fake asset、baseline MP4或第二writer补造。

本follow-up effects仍为零：未选择Provider，未写native prompt，未启动ComfyUI，未submit/fetch，未生成、repair或拼接
media，未调用`video-analysis`，未产生`DRAMA-MEDIA-*` HUMAN verdict、P6或Final Acceptance；下一Shot submit仍禁止。
