# Composition Playbooks

## Status

Decision C-lite experimental/shadow。这里的 Playbooks 属于 Development Governance，供
Codex、显式 development helper、tests 或 shadow proposal tooling 读取。AI-VIDEO Product
Runtime 不读取本目录，也不依赖这些 YAML。

## Ownership Boundary

Playbook 只表达适用条件、advisory strategy preference、禁止的 fallback、所需 evidence、
known limitations、expected failure modes、review重点与repair建议。它不拥有或记录
Production Manifest state、Asset/Registry identity、Provider/model/profile/task state、budget、
permit、active output、QA verdict、Final Acceptance、ResolvedTimeline 或 Dependency Graph state。

当前链路固定为：

```text
Codex + Composition Playbook
  -> CompositionStrategyProposal (shadow evidence)
  -> compare only
  -> existing VideoPlanner decision
  -> ShotReadinessGate
  -> Shot Router
  -> selected Provider path
```

Playbook 版本与 proposal 不进入 `VideoPlanningRequest.request_content_hash`、
`VideoGenerationPlan.plan_hash`、`ProviderNeutralVideoRequirement.requirement_hash` 或 desired
generation fingerprint。修改 Playbook 不会使 Production downstream 自动 stale。

Comparison 覆盖 current HEAD 的全部 `GenerationMode`，包括 `VIDEO_EDIT` 与
`VIDEO_EXTEND`。Unknown strategy在proposal validation处直接失败，不会作为弱类型值进入comparison；
`NOT_COMPARABLE`用于target Shot identity不一致等“不是同一对象”的情况。

## Validation

`schema.json` 是 JSON Schema 表达；`scripts/composition_playbooks.py` 使用同一 strict Pydantic
model生成预期 schema、验证 checked-in schema 完全一致，再以 no-network YAML loader 解析。
Unknown fields、duplicate mapping/list values、empty required collections、invalid enum/version、
duplicate playbook id/name、absolute paths 与 Provider/runtime-state fields 都 fail closed。

Focused command：

```bash
python -m pytest -p no:cacheprovider tests/test_composition_playbooks.py -q
```

## Pilot And Stage 3 Gate

下一步是 20–50 个真实 Shots 的 shadow Pilot，不是继续抽象。每个 Shot 至少关联：selected
Playbook、Agent proposal、current Planner strategy、最终人工/Production选择、Provider、result、
human quality result、retry count 与 manual intervention。可复用现有 Quality Intelligence exact
record pointer/hash做轻量关联，但本目录不写 Production Manifest，也不新建数据库。

只有固定 rubric 数据证明 proposal改善结果、发现 Planner重复盲点、Playbook被重复使用、字段稳定，
或 disagreement与真实quality outcome相关，才可设计 Stage 3 的 Product Planning Validator / Planner
integration。Formal `CompositionSkillLibrary`、Planner schema/hash integration、`ExecutionTrace`、
Promotion Gate 与 Skill Evolution 全部 deferred。
