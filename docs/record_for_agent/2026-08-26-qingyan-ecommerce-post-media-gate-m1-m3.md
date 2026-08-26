# Qingyan Ecommerce Post-Media Gate M1-M3 Record

Date: 2026-08-26

> Superseded current-facing status (2026-08-26): Ecommerce whole-ad Gate 2、canonical Production caller、P6 semantic binding与Final Acceptance closure现已实现，见`docs/record_for_agent/2026-08-26-ecommerce-final-media-gate-closure.md`。本文M1–M3历史实现、verification与当时的live-media authorization boundary仍有效；“Milestone 5–7未实现/必须等待Milestone 4”不再代表current deterministic Runtime truth。

## Purpose

本文记录 `2026-08-25-qingyan-ecommerce-post-media-gate-repair.md` 的 Milestone 1–3 实现 checkpoint。它保存已落地的 runtime truth、verification 和 remaining authorization boundary，不授权 Provider live call、媒体生成、P6 Gate 2、Final Acceptance 或 release claim。

代码、测试、exact Harness receipt 与当前 runtime evidence 仍是 source of truth；本记录不是第二个 lifecycle owner。

## Implemented Runtime Truth

Milestone 1 已建立 additive Domain acceptance contract：

- `QaPolicy.domain_acceptance` 在缺省时保持旧 serialization/hash identity，在启用时要求 `QaLayer.SEMANTIC` 与 exact content-addressed profile。
- Qingyan Ecommerce profile 使用 stable requirement IDs 与 requirement-level `PASS` / `FAIL` / `NOT_EVALUATED`；Domain policy 不得 fallback 到 generic `semantic_match`。
- authoring readiness、candidate、P6、Final Acceptance 与 human visual verdict 继续保持分层，互不替代。

Milestone 2 已把 generated commercial Shot 绑定进 Manifest `2.13` video lifecycle：

- `GeneratedCommercialShotBinding` 封存 exact plan、projection、profile、Shot、product/source/actor/output identities；`resolved_generation_hash` 由 resolved request 和 downstream intent/evidence 绑定，避免自引用 hash。
- Manifest `2.13` 是 `2.12` additive superset；commercial source approvals、reader、recovery、P0/P5/P6/image/video/render 等既有 version seams 均继续可用。
- `ProductionStateCommitter` 仍是唯一 candidate/activation/recovery writer。commercial-bound request 在 `VALIDATE` 先写 durable intent，再调用 reviewer，再写 exact evidence；required finding 全部 PASS 前不能进入 `CANDIDATE`。
- evaluator intent-only、exception、stale policy/profile/source approval、path replacement、FAIL/NOT_EVALUATED 均 fail closed；replay/recovery 不重跑 evaluator。
- continuity 与 commercial review 共用一次 held-FD measurement，并只生成一份 authoritative probe/provenance capture。
- product-bound activation 会消费并 stale 当前 source approval，但 reader/replay 只通过 exact immutable consumed approval seal 重开；candidate/evaluator 前仍要求 current approval。

Milestone 3 已建立 sequential coordinator：

- 只按 canonical proposal order 处理 `invoke_video_provider=True` 的 Shots；deterministic hero/proof/end-card 不提交 Provider。
- 每个 Shot 必须完成 exact commercial PASS 与 activation，才允许下一 Shot start/submit；任一 non-PASS、STOP、unknown/stale state 都保持 later submit count 为 0。
- production facade 使用 existing local/paid `VideoGenerationService` public action sequence：`start -> submit -> poll -> fetch -> validate -> activate`。
- facade 在 effect boundary 和 per-Shot execution guard 内重开 durable request，并比较 `resolved_generation_hash + plan + projection + Shot`。preflight 后 competing start、same-binding/different-prompt DONE replay、local/paid duplicate invocation 均在错误 effect 前停止。
- project+attempt scoped POSIX execution lock 会跨 `VideoGenerationService` instance/process 串行化同一 Shot；duplicate paid poll/local fetch 不产生第二次 Provider call，local fetch 不留下 orphan temporary MP4。

## Independent Review

同一 `reviewer_xhigh` 对 lifecycle/safety gate 做了多轮 scoped review。早期 review 实际发现并推动关闭：

- policy/source approval drift 后旧 candidate activation；
- product-bound activation 自行 stale approval 后 reader 无法重开；
- facade mapping identity 与 durable request identity 不一致；
- preflight-to-effect TOCTOU；
- concurrent duplicate poll/fetch Provider effect；
- same commercial triple 但不同 `resolved_generation_hash` 的错误 DONE acceptance。

最终 exact follow-up `6896a34..7d44bca` verdict 为 `accept`，blocking issues 与 scoped concerns 均为 None。reviewer focused evidence 为 Ecommerce/local/paid/product `77 passed`，candidate/source/schema/state/video `605 passed`。

## Verification

Final code snapshot：

- task head: `7d44bcab777ddffbff9c1b341ff4e07c913e28e0`
- Harness scope: `ffabfe0b5de177ab676308adfa4af3ac2ff7cab4..7d44bcab777ddffbff9c1b341ff4e07c913e28e0`
- receipt: `.agent/harness/runs/qingyan-ecommerce-post-media-gate-m1-m3-v7/receipt.json`

该 contiguous scope 也包含已经落在 shared `main` 的 module-architecture contract commits `ee106ea` / `ea238aa`；因此不能把 68-path Harness range 描述为纯 M1–M3 diff。M1–M3 最终 follow-up commits 为 `747019a`、`5c50011`、`6896a34`、`7d44bca`，更早 schema/lifecycle/coordinator commits 位于同一 contiguous range 内。

Harness v7 status 为 `passed`：

- docs/policy/Architecture Gate：PASS；Architecture Gate 为 0 errors、6 warnings。
- Harness tests：`185 passed`。
- Architecture tests：`58 passed`。
- Production contracts：`2790 passed, 3 skipped, 1065 deselected`。
- CLI/config：`13 passed`。
- Production review：`624 passed`。
- Commercial source preparation：`851 passed`。
- Production image：`1258 passed`。
- Provider-neutral video requirement：`295 passed`。

receipt 的 integrity、artifact hashes、check records、policy/scope match、snapshot match、closure eligibility 与 completion proof 均通过。在 shared checkout 直接检查时，外部 in-progress `_image_project_reader.py` 等 dirty paths 与 scope 重叠，因此 `scope_worktree_clean=false`；未清理、覆盖或暂存这些外部改动。对 exact `7d44bca` clean local clone 执行同一 receipt freshness API 后，`fresh=true`、`fresh_for_snapshot=true`、`complete_completion_proof=true`。

## Remaining Authorization Boundary

Milestone 4 是一个真实 local/remote Provider pilot Shot 和 mandatory project-local `video-analysis` post-media gate。当前请求没有固定以下 live execution inputs：

- exact Provider 与 model/profile；
- exact one-Shot request、reference inputs 与 output destination；
- finite budget ceiling（remote/paid 时）；
- cloud-egress/credential reference 与 one-use submit permit inputs（remote/paid 时）。

因此本 checkpoint 没有执行 Provider submit、媒体生成、`video-analysis`、人类 normal-speed visual review 或 quality PASS claim。Milestone 4 仍 blocked on explicit task-scoped live authorization。

Milestone 5–7 依赖 Milestone 4 的 exact pilot evidence 与 human verdict，本轮未实现。不得把 M1–M3 Harness PASS 推断为整片 Ecommerce Gate 2、P6 receipt、Final Acceptance、live-ready、release-ready 或视觉质量达标。

## Agent Guardrails

- authoring-ready 不能冒充 media acceptance。
- commercial Shot candidate PASS 不能冒充 whole-ad Gate 2 或 Final Acceptance。
- duplicate/replay 必须在 Provider effect 前重开 exact durable request，并在同一 per-Shot execution guard 内执行。
- current source approval 只用于 evaluator/candidate authority；activation 后 consumed approval 只能通过 immutable seal 精确重开。
- 未取得 Milestone 4 exact live inputs/authorization 前，不得自行选择 Provider/model、猜预算、提交 Shot 或生成媒体。
