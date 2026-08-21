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
   `all` 会先为两个 corpus 分配近似均分的 candidate quota（`top_k=5` 时为 3/2）。
2. **Document chunking**：Markdown 先按 `#`、`##`、`###` 标题切分；过长 section
   再按约 800 characters 切分，80 characters overlap。每个 chunk 保留 source、title、
   heading path、status、corpus kind 与 authority metadata。
3. **Embedding**：本地 pinned `intfloat/multilingual-e5-small` ONNX 生成 384-dim
   normalized vectors；query 加 `query:` 前缀，document 加 `passage:` 前缀。
4. **Retrieval**：每个 selected collection 以 cosine nearest-neighbor 查询。
   result score 为 `1 - cosine_distance`；它只用于当前 result ordering，不是可信的
   confidence 或 quality threshold。
5. **Merge**：`all` 的两个 corpus candidates 合并后按 score 降序排列，最终截取
   `top_k`；因此 quota 保证两边都有召回机会，但不保证 final result 严格交替。

当前没有 query rewriting、metadata filter、BM25/lexical retrieval、RRF、reranker 或
minimum-score abstention。

## Fitness And Limits

当前设计适合小型、curated project knowledge 的中英文语义查询，例如“以前怎样处理
H3 continuity?”、“是否有关于 StateCommitter recovery 的旧设计？”或“哪些计划讨论过
该架构取舍？”。

它不适合作为精确 symbol/path/commit/error-code 搜索器，也不应单独作为回答、执行、
Provider authorization、quality acceptance 或 durable state mutation 的依据。若真实使用
中持续出现精确术语漏召回或语义排序错误，应基于具体 failure case 再评估增加 lexical
retrieval + dense retrieval 的 RRF，而不是提前扩大实现。

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
