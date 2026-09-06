# Generation Decision Loop Implementation

## Goal And Scope

实现 [accepted task spec](../specs/2026-09-06-ai-video-generation-decision-loop.md) 的纯决策契约与 A1–A18 确定性验证。用户于 2026-09-07 要求实现，覆盖代码、对应 contracts、测试和本地 commit；不包含生成质量提升的 empirical acceptance。

## Ownership And Retirement

- `VideoGenerationResolver.resolve_requirement` 是新任务唯一 selection/fit 入口；消费候选目录、当前 verified requirement、rubric、显式 evidence 和 execution limits。旧 exact binder 改为内部方法；旧 compatibility tests 明确验证内部 seam，不能构成第二条 public selection path。
- Planner 提供组合难度 facts；保持原 plan/confidence/hash 含义。Router 的独立纯模块持有 decision/diagnosis 比较，不读取 Q0、RAG、secrets 或 Provider。
- Native compiler 消费 sealed recipe、显式 seed 与 requirement expression coverage；无法完整表达时 fail closed。历史 bound/request bytes 通过省略新增可选字段保持旧 hash。
- `ProductionStateCommitter`、Dependency Graph、`ResolvedTimeline`、provider execution、Gate/P6 和 explicit recovery owner 不变。不存在通用运行时 caller；本任务交付可调用的纯决策 API，不能宣称自动生产循环已运行。

## Milestones And Verification

1. 建立 typed immutable recipe/evidence/diagnosis contracts 与真实 failure tests。
2. 接入 Router 唯一 selection、Planner facts、compiler seed/coverage，验证 determinism、freshness、continuity lock 和旧 hash。
3. 同步 matrix、历史 spec 的 selection 条款、baseline、roadmap 与 Harness routing；native `reviewer_xhigh` 独立审查。
4. 完成 task-owned exact commit-range Harness、receipt verification 和 durable session record。

Focused command: `python -m pytest -p no:cacheprovider tests/test_production_generation_decision.py tests/test_production_shot_router.py tests/test_production_provider_neutral_adapters.py -q`。最终 checks 由 `.agent/harness/policy.yaml` 确定。

## Constraints

当前已有 staged `runs/jieshi-*` 文件和 untracked 输入 spec，均作为外部工作保留；不修改输入 spec，不 stage/commit 这些文件。无 live/paid/ComfyUI/media effects。Empirical model-quality 结论保持 `not established`。
