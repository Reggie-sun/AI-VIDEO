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

`285757a feat: add scoped multilingual agent memory retrieval` 引入 named corpora：

- `experience`：`docs/record_for_agent/`，authority 为 `advisory_experience`；
- `superpowers`：`docs/superpowers/`，authority 为 `historical_design_plan`。

默认 scope 是 `experience`。`superpowers` 的命中必须显示其 historical
design/plan 身份，不能被当成 current runtime truth、implementation authorization
或 accepted contract。

CLI 是显式、local-only 的：

```bash
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

## Matching Pipeline

1. **Scope selection**：`experience` 与 `superpowers` 使用独立 Chroma collection；
   `all` 会先为两个 corpus 分配近似均分的 result quota（默认 `top_n=8` 时为 4/4）。
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
   `lexical_relevance_score`、`fusion_score`；lexical representation 包含 chunk body、
   canonical source、title 与 heading metadata。不会把 Enterprise RAG 的 ACL、department
   scope、query router、answerability fallback 或 citation policy 搬入本仓库。
6. **Relevance gate**：raw BM25 通过固定函数 `1 - exp(-BM25 / 0.2)` 映射为 bounded
   lexical relevance，Agent-facing `score` 取它与 dense cosine score 的较大值。只保留
   `score >= 0.7` 的命中；`score == 0.7` 通过，低于 `0.7` 不返回。这个固定 admission
   heuristic 不会因 candidate set 的第一名而自动归一化为 1，也不是事实可信度或质量证明。
7. **Merge**：先在各 corpus quota 内按 `fusion_score` 排序，再合并 experience、
   superpowers 与可选 run-summary hits，按 fusion、relevance 与 lane score 稳定排序并截取
   Agent-facing `top_n`（默认 8）；quota 保证不同 scope 都有召回机会，但不保证 final
   result 严格交替。现有 CLI `--top-k` 保留为 `top_n` 的兼容覆盖参数。

当前没有 query rewriting、metadata filter、reranker 或动态 query-specific threshold。

## Fitness And Limits

当前设计适合小型、curated project knowledge 的中英文语义查询，例如“以前怎样处理
H3 continuity?”、“是否有关于 StateCommitter recovery 的旧设计？”或“哪些计划讨论过
该架构取舍？”。

Hybrid retrieval 改善了 exact symbol、path、commit 与 error-code 的召回，同时保留中英文
语义查询能力；它仍不应单独作为回答、执行、Provider authorization、quality acceptance
或 durable state mutation 的依据。固定 BM25 映射提供稳定 admission scale，但仍不是
跨语料可比较的 calibrated confidence。

## Freshness And Maintenance

Index manifest 绑定 exact corpus digest、chunking configuration、embedding identity、
collection identity 与 library versions。语料、模型或 collection 不匹配时 search 必须
fail closed，并提示 explicit rebuild：

```bash
python -m scripts.agent_memory --scope all build
```

Index 位于 `.agent/memory/index/`，是 local derived state，不是 repository runtime
truth 或 committed evidence。新增或修改 `docs/record_for_agent/` / `docs/superpowers/`
后，旧 index 会因 source digest mismatch 变 stale；需要在本机显式 rebuild 后才可继续
检索。本文新增本身也触发该要求。

## Guardrails

- `experience` 记录是 advisory experience，不等于 code/runtime truth。
- `superpowers` 记录是 historical design/plan，不等于 accepted current contract。
- score 高不等于事实已验证；使用命中前必须回到当前 code、tests、runtime evidence 与
  canonical docs。
- index build/search 不读取 Provider secret、不调用 remote Provider、不改变
  Production state，也不自动升级任何历史计划为执行授权。
