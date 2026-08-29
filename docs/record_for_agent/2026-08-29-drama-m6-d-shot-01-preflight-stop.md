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

Current canonical pre-submit在进入Planner前缺少Project/Registry materialization：没有selected Project/Registry
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

`B-D0=PASS`保持不变；`M6-D=NOT_EVALUATED`并处于`STOP_BEFORE_SUBMIT`。这不是per-Shot HUMAN FAIL，因为没有
exact Shot MP4可以播放或判定。Commercial `M6-C=HUMAN_FAIL`与`B-X=FAIL`也不向Drama继承任何finding。

Primary blocker是sealed Drama package尚未通过current canonical seam materialize为Project/Registry-selected Shot；
historical baseline helper创建的test project加in-memory Shot copy不能替代该authority。该缺口不能在本slice内通过
手工构造runtime models、借用Commercial media、把baseline reference MP4改作conditioning input、修改sealed
fixture/baseline或绕过canonical authoring/loading seam来处理。future selected Provider/runtime也须从新的canonical
projection开始重新取得current executable proof。

## Remaining Work And Guardrails

下一步必须先由独立owner选择并批准canonical Drama Project/Registry materialization seam；随后再决定是否形成并
accept新的exact input revision，或实现能够在不降低identity contract的情况下表达sealed Drama intent的current
Planner/adapter seam。本次task禁止改变fixture/baseline或修改runtime/code/tests，因此停在这里。

任何未来resume必须重新打开本record与exact preflight JSON，重跑fresh Planner/readiness，并在得到current
`VerifiedGenerationRequirementProjection`之后才可进入Router selection。新run、new Shot bytes或任何input/profile/
rubric/runtime identity变化都不得继承本次blocked decision之外的evidence。
