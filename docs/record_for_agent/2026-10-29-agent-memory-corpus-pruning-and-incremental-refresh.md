---
record_kind: architecture_implementation
topic_id: agent-memory-corpus-and-refresh
learning_eligibility: ineligible
---

# Agent Memory Corpus Pruning And Incremental Refresh Record

Date: 2026-10-29

## Purpose

用户认为 `retrieve-ai-video-memory` 检索到的文件有些多余、完全过期，希望去掉，并让检索能自动更新。
用户选择"索引自动跟上文档 + 过期内容按规则自动排除"两者都要，移出范围交由 Agent 判断。
本次只改 developer-only Agent Memory 与相关文档，不涉及 Product Runtime、Provider、付费或媒体 Gate。

## Diagnosis

- 检索语料：`docs/record_for_agent` 352 份、`docs/superpowers` 250 份（其中 `plans/` 138 份 4039 chunks、
  `artifacts/` 33 份 466 chunks）、top-level `docs/*.md` 28 份、`docs/research` 33 份、`docs/when_to_do` 4 份，
  另有独立 run-summary lane（39 个 `runs/*/SUMMARY.md`，15 个带 `Status:` 可索引，30 个属 2026-09-06 同批 jieshi 实验）。
- 6 个真实问题实测（`--scope all`）：同一文件在 8 个结果中最多占 3 个；`when_to_do` 几乎每次占一个弱相关名额；
  `jieshi-s01-h3-horizontal-20260906-001` 的 run summary 出现在无关的 Seedance 付费恢复问题中；
  `docs/superpowers/artifacts/` 的作品制作包被标成 `historical_design_plan`。
- 更新是被动的：shard 只在有人搜索时才发现 stale，当次只能拿旧片段；整片重建会重新 embed 全部 chunk
  （experience 6492 chunks × 约 0.12 s ≈ 13 分钟），所以原设计禁止前台重建。
- `when_to_do` 逐份核对：`continuity-review-coordinator-and-human-evidence-ui.md` 状态仍写"准备实现"，
  但其 recap 证明已实现，移出；recap、`decision-c-lite`（20–50 Shot shadow Pilot 未做）、`post-qa-q0`
  （automatic caller 未实现）仍是有效待定决策，保留。

## Session Work And Decisions

- 检索排除（`corpus.iter_corpus_markdown_files`，digest 与加载共用）：`docs/superpowers/plans/`、
  `docs/superpowers/artifacts/` 按路径排除；任何 Markdown 的 frontmatter 含 `retrieval: retired`
  即排除（容忍引号、大小写、BOM、行内 ` #` 注释），文件仍留 Git。`superpowers` 从 6471 降到 1966 chunks。
- 移除 run-summary lane：`.agent/memory/run-summaries` index、`--runs-root/--runs-index`、`run_*` Hit
  字段、maintenance kind 与相关测试；本机该派生缓存（968K，gitignored）已删除。理由：结论已写入经验记录，
  且实测是噪音来源。`distill-ai-video-learning` 仍可直接读取 `SUMMARY.md` 作证据。
- 增量重建：`build_scoped_index` 按 chunk id 复用当前 shard 中的向量，仅当 manifest 通过
  `validate_manifest(manifest, (), embedding)`（schema、embedding identity、chunking、library versions）；
  chunk id 改为 corpus-root-relative 路径，使复用不依赖 cwd。`build --full` 强制全量重算，用于修改
  embedding 计算方式（前缀、截断、pooling）之后。
- 自动刷新：CLI `search` 发现 stale shards 时，先做 non-waiting 前台增量刷新，一次 search 内所有 shard 共享
  `FOREGROUND_REFRESH_MAX_NEW_CHUNKS = 64` 的 `EmbeddingBudget`；超出、builder 占用、migration 缺失或其他
  刷新失败时，仍返回已校验的 tagged last-good 片段并 queue detached refresh。detached worker 同样受益于复用。
- 每个文档在每个 collection 中至多返回一个最高分片段；`all` 的 `2/2/2/1/1` quota 设计不变
  （各 corpus 的 RRF 分数不可比，quota 保证可见性）。
- 顺带修复两个既有缺陷：shard database 损坏时 `_release_cached_client` 的 `stop()` 异常会让 `build`
  无法恢复；`search` 遇到无法打开的 database 以原始 traceback exit 1。现在 build 可恢复，search 以 exit 2 fail closed。
- `record-ai-video-session` 新增规则：旧记录的全部 current-facing 结论被取代时，加 `retrieval: retired`
  与 `superseded_by:`；部分取代只加 notice。`when_to_do` 中已实现的计划已加该标记。
- 同步：retrieve skill 与三份 scope reference、README、playbook §6、runtime baseline，
  [原 scope 记录](2026-08-21-agent-memory-rag-scope-and-retrieval.md) 加 supersession notice。

## Verification And Evidence

- `tests/test_agent_memory.py`（fake embedding）：108 passed。新增覆盖：排除规则、retired marker、增量只
  embed 改动 chunk、复用向量与 chunk 正确配对（含删除、修改、排序靠前的新文件）、library 版本不一致不复用、
  不同 cwd 仍复用、预算在改动 active index 前检查、non-waiting 锁、bounded 调用拒绝 migration、
  `build --full`、`all` 共享预算（反向验证：改为按 shard 预算时该测试失败）、retired 端到端、
  每文档一片段（反向验证：去掉去重时失败）、损坏 database 的 build 恢复（反向验证：旧释放逻辑复现
  `AttributeError`）与 search exit 2。
- 真实模型校准（`-k local_multilingual`，真实 `docs/` 快照 + pinned E5）：首轮 2 passed（485 s）；
  reviewer 修复后的最终代码复跑 2 passed（453 s）。中文召回、乱码拒答与 null probe 判定仍成立。
- 本机真实索引上同 6 个问题复测（`--scope all --top-k 8`）：全部 `fresh`；每个结果来自不同文件；
  无 run summary、plans 或 artifacts。首个问题恰逢新记录使 experience stale，前台增量刷新后返回，
  总耗时 11.9 s；其余问题各约 3.9 s（含模型加载）。仍见 `post-qa-q0` deferred 片段以 0.87 进入 2 个问题。
- 本机真实索引用最终代码 `--scope all build` 全量重建：7 分 46 秒；experience 352/6492、superpowers 79/1966、
  current_docs 28/896、research 33/719、deferred 3/37（documents/chunks）。
- 独立 reviewer（`oh-my-claudecode:code-reviewer`，只读）两轮：首轮 REQUEST_CHANGES（1 HIGH 已复现：损坏
  shard 无法重建；4 MEDIUM：计算方式漂移无逃生口、按 shard 预算与耗时表述不准、测试缺口、记录未建；8 LOW），
  采纳修复后复审 APPROVE。未采纳：刷新后复用首次查询结果（约 1 s）、dense margin 与去重的关系（既有校准）。

## Remaining Risks Or Next Work

- embedding 计算方式（`passage:` 前缀、截断、pooling）不在 identity 里；修改 `embeddings.py` 后必须跑
  `build --full`，否则未改动 chunk 会沿用旧向量。可选加固：在 chunk id 中加入 recipe 常量，改代码时随之改常量。
- 其他 clone/worktree 的旧 shard 首次 stale 时 chunk id 全部不匹配，会超出前台预算并排队全量重算（一次性）。
- 前台刷新每个 stale shard 有重写 staging 副本的固定开销（experience 约 4–5 s），未做原地 upsert 优化。
- `all` 的 deferred quota 仍可能放入一个仅 dense 通过的弱相关片段（`when_to_do` 现只剩 3 份）。
- `.git/agent-memory-refresh/` 下旧 queue key 目录不再使用，未清理。

## Agent Guardrails

- 让过期文档退出检索用 `retrieval: retired` + `superseded_by:`，不要删除历史文件，也不要靠手工名单。
- 不要在 skill 流程里手动跑 `build`；CLI 的有界前台刷新与 detached queue 负责维护。修改 embedding
  计算代码后才需要显式 `build --full`。
- 真实模型校准测试会全量 embed `docs/` 快照（约 8 分钟），放后台运行；不要把它当成卡死。
