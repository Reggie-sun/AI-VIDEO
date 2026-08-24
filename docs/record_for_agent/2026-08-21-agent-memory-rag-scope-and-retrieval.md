# Agent Memory RAG Scope And Retrieval Record

Date: 2026-08-21

## Purpose

本文记录 AI-VIDEO Agent Memory RAG 的当前定位、触发条件、匹配规则、适用边界与维护
要求，供后续 Agent 在需要历史经验或历史设计依据时使用。

它不是 Production runtime、Provider、Manifest、Asset Registry、Dependency Graph、
`ResolvedTimeline`、Renderer 或 activation 的 owner；检索结果仅是 local advisory
evidence，不能覆盖用户指令、current code/tests、runtime evidence 或 architecture
contracts。

## Current Implementation

`285757a feat: add scoped multilingual agent memory retrieval` 引入 named corpora；
当前实现把 `docs/` 的有效 Markdown 扩展为五个 main-index corpora：

- `experience`：`docs/record_for_agent/`，authority 为 `advisory_experience`；
- `superpowers`：`docs/superpowers/`，authority 为 `historical_design_plan`；
- `current_docs`：仅 top-level `docs/*.md`，按 exact path 标记 current contract、
  runtime baseline、roadmap 或 generic current-project advisory；
- `research`：`docs/research/`，authority 为 `advisory_research`；
- `deferred`：`docs/when_to_do/`，authority 为
  `deferred_decision_advisory`。

这样覆盖了 `docs/` 下全部 Markdown，同时避免 nested corpus 重复摄入。HTML、TXT
与其他非 Markdown 文件不会进入索引。Auto-generated run summaries 继续使用独立
derived index 和独立 authority。

默认 scope 是 `experience`。`superpowers` 的命中必须显示其 historical
design/plan 身份，不能被当成 current runtime truth、implementation authorization
或 accepted contract。

CLI 是显式、local-only 的：

```bash
python -m scripts.agent_memory --scope all build
python -m scripts.agent_memory --scope experience search "H3 continuity"
python -m scripts.agent_memory --scope superpowers search "state commit recovery"
python -m scripts.agent_memory --scope all search "provider-neutral planning"
```

它没有 background trigger、Production runtime hook、Provider submit、网络 fallback
或 automatic model download。

## Agent Trigger Rules

在 substantial execution 前，task 涉及以下主题时应查询 `experience`：

- real media production、rough-cut 或 final quality；
- known regression、repeated failure 或 incident recovery；
- Provider/model behavior；
- continuity、identity drift、reference usage 或 image/video generation strategy；
- 有历史 rejected approach 的 architecture decision。

只有 task 需要历史 architecture/spec/plan evidence 时，才查询 `superpowers` 或
`all`。formatting、typo、与历史 production experience 无关的 isolated refactor 或
trivial test 不应触发检索。

涉及 production quality、Provider behavior 或 known failure domain 的 task 在完成前
应再次做 relevant search，避免重复已知错误。

## Project Skill Routing

Project-level routing skill 位于 `.agents/skills/retrieve-ai-video-memory/`。其
`agents/openai.yaml` 保持 `allow_implicit_invocation: true`，让 Agent 在命中上述
substantial-task trigger 时加载 routing instructions；它不会在 background 自动运行 RAG。

Skill 先选择一个 scope，再只读取对应的一份 reference：

- `references/experience.md`：经验记录、真实 failure/recovery、Provider/model、continuity、
  media quality 与 eligible run summaries；
- `references/superpowers.md`：历史 specs/plans、architecture intent 与 rejected approaches；
- `references/all.md`：需要跨 current docs、experience、historical design、research
  或 deferred decision evidence。

三个 reference 分别拥有 query shape 与 authority interpretation。Skill 不注册 lifecycle
hook，不进入 Product Runtime，不把 retrieval 结果升级为 implementation、Provider、activation、
quality acceptance、push 或 release authorization。

该 Skill 由 local commit `db5edc5 feat: add AI-VIDEO memory retrieval skill` 引入。
`quick_validate.py` 返回 `Skill is valid!`；native `reviewer_xhigh` 最终 verdict 为 `accept`；
exact staged Harness receipt 位于
`.agent/harness/runs/20260824T103450748348Z/receipt.json`，documentation/control-plane
checks 为 `176 passed`，receipt integrity/freshness/snapshot checks 全部通过。没有执行 Project
RAG search、Provider、媒体或网络操作。

## Matching Pipeline

1. **Scope selection**：五个 main corpora 使用独立 Chroma collection；narrow
   `experience` 与 `superpowers` 行为保持不变。`all` 在默认 `top_n=8` 时按
   `2/2/2/1/1` 为 experience、superpowers、current_docs、research、deferred
   分配 quota。
2. **Document chunking**：Markdown 先按 `#`、`##`、`###` 标题切分；过长 section
   再按约 800 characters 切分，80 characters overlap。每个 chunk 保留 source、title、
   heading path、status、corpus kind 与 authority metadata。
3. **Embedding**：本地 pinned `intfloat/multilingual-e5-small` ONNX 生成 384-dim
   normalized vectors；query 加 `query:` 前缀，document 加 `passage:` 前缀。
4. **Candidate retrieval**：每个 selected collection 从同一批 indexed chunks 走两条
   local lane。Dense lane 使用现有 Chroma cosine nearest-neighbor；lexical lane 使用
   dependency-free BM25（`k1=1.5`、`b=0.75`），保留 identifier/路径 token，并为中文
   连续文本增加 bigram。两条 lane 的 candidate `top_k` 都是 30。
5. **Fusion**：两条 lane 用 stable Chroma chunk ID 去重，再以 equal-weight weighted RRF
   （`k=60`）排序。每个 hit 分别保留 `dense_score`、raw `lexical_score` 与
   `lexical_relevance_score`、`lexical_query_coverage`、`fusion_score`、
   `dense_null_score`、`dense_null_excess`、`dense_top1_margin` 与 `admission_lane`；
   lexical representation 包含 chunk body、canonical source、title 与 heading metadata。
   RRF 只决定 ordering，不决定 admission。
6. **Lane-aware answerability**：lexical lane 将 raw BM25 通过固定函数
   `1 - exp(-BM25 / 0.2)` 映射，并要求 exact token/bigram 覆盖至少 30% query terms；
   relevance 达到 `0.7` 后才可独立放行，单个偶然中文 bigram 不足以通过。Dense lane
   针对同一 collection 运行与 query writing system 匹配的固定 irrelevant control query；candidate 必须同时满足
   `dense_score >= 0.7`、相对 null Top-1 的 excess `>= 0.005`，且真实 query 的
   Top-1/Top-2 margin `>= 0.0015`。CJK null probe 使用语法自然但明确与输入无关、且不含
   项目 domain 词的固定 control query；罕见乱码会把 baseline 人为压低，使自然中文离题句虚假通过。
   只有一个 candidate 时没有可定义的 Top-2 margin，
   因而仅使用 score 与 null excess fail-closed 判定。最终 `score` 只取已放行 lane 的 score，标记为
   `lexical`、`dense` 或 `hybrid`；两条 lane 都不通过时返回空。该 gate 不会把 dense
   cosine 的整体高分误当 answerability，也不会把 lexical 第一名自动归一化为 1。
7. **Merge**：先在各 corpus quota 内按 `fusion_score` 排序，再合并五个 main
   corpora 与可选 run-summary hits，按 fusion、relevance 与 lane score 稳定排序并截取
   Agent-facing `top_n`（默认 8）；quota 保证不同 scope 都有召回机会，但不保证 final
   result 严格交替。现有 CLI `--top-k` 保留为 `top_n` 的兼容覆盖参数。

当前没有 query rewriting、metadata filter、reranker、learned answerability model 或
answerability fallback；也没有搬入 Enterprise RAG 的 ACL、department scope、query router
或 citation policy。

## Fitness And Limits

当前设计适合小型、curated project knowledge 的中英文语义查询，例如“以前怎样处理
H3 continuity?”、“是否有关于 StateCommitter recovery 的旧设计？”或“哪些计划讨论过
该架构取舍？”。

Hybrid retrieval 改善了 exact symbol、path、commit 与 error-code 的召回，同时保留中英文
语义查询能力；项目语料 calibration 覆盖跨镜头角色连续性正例与中英文 nonsense 负例。
它仍不应单独作为回答、执行、Provider authorization、quality acceptance
或 durable state mutation 的依据。固定 BM25 映射提供稳定 admission scale，但仍不是
跨语料可比较的 calibrated confidence。Dense null probes 与 margin 是基于当前真实 E5
语料分布的 precision-first conservative heuristic；缺少 lexical anchor 且没有清晰 dense
separation 的自由改写会主动 abstain。语料或 embedding identity 变化后仍需重新实测。
五 corpus 扩展后的真实 local E5 实测中，experience continuity 正例为 null excess
`0.014398`、Top-1 margin `0.001826`；同一中文离题句在 experience、superpowers、
current_docs、research、deferred 的 null excess 分别为 `-0.003528`、`0.001106`、
`-0.007325`、`0.000066`、`-0.002329`，全部低于 `0.005`。因此五个 collection 均拒答，
同时正例保留 dense admission。

## Freshness And Maintenance

Index manifest 绑定 exact corpus digest、chunking configuration、embedding identity、
collection identity 与 library versions。Materialization 与 query 是两个独立 phase：
`build` 是唯一能够通过 staging 构建并替换 derived index 的 owner；`experience` / `all`
build 也会同步 materialize eligible run-summary index。`search` 只校验并查询，绝不创建、
刷新或修复 index。主 index 或 run-summary index 缺失、corpus bytes/digest 改变、requested
scope 尚未 materialize、schema / embedding / chunking / metric / library identity / corpus
authority / collection contract 不匹配，或 physical collection partial/corrupt 时，search
均 fail closed，并提示对 shared index 做 explicit build：

```bash
python -m scripts.agent_memory --scope all build
```

Index 位于 `.agent/memory/index/`，是 local derived state，不是 repository runtime
truth 或 committed evidence。新增或修改五个 corpus 拥有的 Markdown 或 eligible
run summary 后，必须先显式运行 build，再执行 search。这样耗时的 embedding / Chroma
写入不会占用 query timeout，也不会让一次只读检索产生 workspace-local derived writes。

## 2026-08-24 Build And Search Phase Split

Local commit `c72906e fix: split agent memory build and search` 完成了 phase ownership
收敛：

- `scripts.agent_memory cmd_build()` 是唯一 materialization owner。`experience` / `all`
  build 在同一显式 phase 中分别构建 main index 与 eligible run-summary index；
  `superpowers` 不触达 run summaries。
- `retrieval.search()` 只执行 index identity、requested scope、physical collection、source
  freshness（调用方提供 corpus roots 时）与 query validation。它不调用任何 build、refresh、
  repair 或 compatibility fallback。
- 无 corpus roots 的 legacy/public direct call 仍会用 manifest 检查 schema、embedding、
  chunking、library identity、requested scopes，以及 physical collection presence/count；
  因为没有 authoritative source roots，它不会伪称已验证 source freshness。
- missing、stale、partial、corrupt 或 identity-mismatched index 均 fail closed，并要求显式
  build。旧 `ensure_scoped_index()` 与 `ensure_run_summary_index()` 路径已删除。
- build 在任何写入前验证 main/run index path 隔离；替换已打开的 Chroma index 前释放
  path-scoped cached client。missing `runs/` 仍贡献零 run hit，且不创建 run index。
- public scopes、schema v1、dense/lexical candidate `top_k=30`、Agent-facing `top_n=8`、
  inclusive `0.7` lane-aware answerability、hit metadata 与 authority ordering 保持不变。

Exact commit-range Harness receipt：
`.agent/harness/runs/20260824T131220193543Z/receipt.json`。该 run 对
`c72906e^..c72906e` 得到 Agent Memory `74 passed`、Harness `177 passed`，documentation、
policy audit 与 task Architecture Gate 全部 PASS；receipt integrity、freshness、snapshot 与
scope checks 全部为 true。Native `reviewer_xhigh` 首轮发现 root-free direct call 会把 partial
index 误报为 `[]`，修复并补 regression test 后 scoped re-review 为 `accept with concerns`；
其唯一 concern 是 docstring 应明确 root-free freshness 边界，已在同一提交前修正。

该提交仅存在于 local `main`，未 push 或 release。本轮没有 Provider、媒体、网络或 Product
Runtime 操作；Project RAG 仍由 prompt-aware skill 显式调用，不注册 runtime hook。

## Guardrails

- `experience` 记录是 advisory experience，不等于 code/runtime truth。
- `superpowers` 记录是 historical design/plan，不等于 accepted current contract。
- `current_docs` 命中必须 reopen exact source；baseline 与 roadmap 的 freshness/authority
  仍不同，RAG score 不得提升它们的权威。
- `research` 是 advisory evidence，`deferred` 是 conditional timing guidance；两者都不
  构成当前 implementation 或 execution authorization。
- score 高不等于事实已验证；使用命中前必须回到当前 code、tests、runtime evidence 与
  canonical docs。
- index build/search 不读取 Provider secret、不调用 remote Provider、不改变
  Production state，也不自动升级任何历史计划为执行授权。
