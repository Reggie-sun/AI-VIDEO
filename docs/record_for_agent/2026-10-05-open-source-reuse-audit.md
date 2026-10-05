---
record_kind: research_note
topic_id: open-source-reuse-audit
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Open-Source Reuse Audit Record

Date: 2026-10-05

## Purpose And Scope

完成用户要求的 Buy vs Build / Open-Source Reuse Audit，只写 research / record 文档。
主报告为 [完整审计](../research/2026-10-05-buy-vs-build-open-source-reuse-audit.md)，
补充证据为 [media/UI note](../research/2026-10-05-open-source-media-ui-audit.md)。
报告包含 Module Matrix、Top 10、overengineering、license/security、不可借入项、
Product Canvas 五个交互、target architecture 与三批迁移建议。

本轮没有 vendor、依赖安装、production code、runtime behavior、Provider/media 调用或实施迁移。
recommendation 不构成 accepted implementation spec，也不授权 paid effects。

## Snapshot Identity

`git fetch origin main` 后，`HEAD`、local `main` 与 `origin/main` 均为
`4cc1b55d81c881711175c71fa18a1f4d7326c92f`。源码审计使用 `git archive` 导出，
未将工作区另一任务的 staged native-expression / continuity changes 当作 main 已实现能力。

| Repository | Branch | Inspected commit | License evidence |
| --- | --- | --- | --- |
| AI-VIDEO | main | `4cc1b55d81c881711175c71fa18a1f4d7326c92f` | 未找到 tracked root LICENSE / NOTICE |
| Wind Comic | main | `82bedb596336fc09ee85240ccf211b0edc53ef4d` | LICENSE: MIT |
| CineCrew | main | `3eac773704088f65ae2e24054c48fccbd4172f2d` | LICENSE: Apache-2.0 |
| story-shot-agent | main | `ec7476276ebceb198d79f33da45dc0707b56463c` | LICENSE: MIT |
| AI Video Production Editor | main | `752cd43d3af6421d2bd6d4ce27f2d9815f7acba3` | LICENSE: GPL-3.0 |
| MovieAgent | main | `d84041bed8bc8be460664528d9e9924cdde384ba` | tracked tree 未发现明确 LICENSE |

stars / forks / recent activity 的观察值见报告；default HEAD 日期与 repository `pushed_at` 分开。
外部源码与 metadata 留在 repository 外的本次临时研究目录，不属于交付或 vendoring。

## Findings And Parent Adjudication

- 进入“核心自研 + 外围复用”：KEEP intent / continuity / routing / effects / canonical state / QA lineage。
- 首先收缩已证实的 H3 / Hailuo / Seedance HTTP mechanics；AI 已复用 `httpx`，不再新增通用 Provider framework。
- 没有一个完整外部 Provider service 满足直接 PORT 边界。fallback、prompt sanitize/resubmit、宽松 status parsing 不借入。
- 最清晰的实际 PORT 是 Wind `lib/video-export.ts::buildAspectFilter` 和 tests；它新增 derivative 能力，当前删除代码量为 0。
- retake / compare / activate UI、story authoring templates、progress projection 适合 ADAPT；backend authority 仍在 AI。
- CineCrew 是 stage loop，完整 pipeline 也含 effects，未证明成熟恢复 engine；story-shot-agent 的图存在，但不是生产 QA / lifecycle owner。
- Editor 只 REFERENCE；MovieAgent 无明确许可，code 与 prompt 原文均不复制。
- 未发现安全的完整模块删除对象；`DELETE/SHRINK` 限定到实际重复的 mechanics / expression，而非 speculative task scheduler。
- 实际迁移安排在 H3 A/B 完成或有据的稳定 admission blocker 后，避免改变进行中的实验 snapshot。main 的 admission record 仍不是媒体验收。

native read-only mapping / media documentation 与 Parent 复核均以冻结源码为依据。
独立复核指出 Job projection 不能证明通用 authoring graph 已存在，也不能证明当前有重复 task repository；Parent 已修正报告。

受管 Kimi 使用 sealed read-only `deep` contract、Docker containment 与 qualified route。
canonical invocation 为 `a7649bc4-db03-47e3-bbde-4735b84d794f`，
seal 为 `424074a58e10e909725e3d99ead721f79b3930768d95d0758ed57b640ad9a66e`。
receipt 记录 4 个 wire requests；第 4 个在 `RESPONSE_BODY` 阶段 `CONNECTION_ERROR`，
最终 `OUTCOME_UNKNOWN`、process exit 1、Parent acceptance `NOT_EVALUATED`。
没有重试或采用 partial output 作为完成审查。该 receipt 只记录委托失败，不是视频 Provider execution。
审计结论由 Parent 的实际源码检查和 native bounded mapping 支撑；本轮不触发 implementation final-review gate。

## Verification And Limits

已运行 `make harness-inspect`。它会看到既有 staged 工作，因此不能作为本任务的 completion receipt。
两份 research 文档的 110 个 immutable GitHub module links 已核对 local clone 中的路径及行号范围；
local relative links 同样已核对。发现并修正 export/UI guide 的三个越界行号。

文档 commit 使用三个明确 owned paths，保留原 staged blobs；完成验证绑定该 commit range。
对应 receipt 路径为
`.agent/harness/runs/open-source-reuse-audit-20261005-001/receipt.json`，
只有实际 receipt 的 status / hashes / freshness 可以证明其离线验证结果，本文不预签 PASS。

未运行外部项目 tests、live API、license compatibility integration、CVE/SBOM 或实际媒体验收。
PORT / ADAPT 均为待资格检查的候选；root license 不替代依赖、字体、weights、FFmpeg build 或声音权利核验。
CodeGraph / AOCI 仅 advisory；AOCI dirty/stale、严格认知验证未完成，不作为当前代码结论证据。

## Learning Evaluation And Publication

已按 `distill-ai-video-learning` 评估，结果 `no_candidate`：
本次是静态 research，没有两次独立实验、controlled comparison 或已存在 learning claim 的 materially verified update。
不创建占位 Learning Claim，不修改 Skill / Policy / Gate，不改变历史媒体 verdict。

仅提交本任务 research / record 文档到本地 stable checkpoint；不 push、不发布实施变更。
后续迁移需在正式落地后的最新 main 上重新核对 affected files、ownership、scope、license 与 verification。
