---
record_kind: research_note
topic_id: supergrok-subscription-media-provider
learning_eligibility: ineligible
---

# SuperGrok Subscription Media Provider Preflight Record

Date: 2026-10-12

## Supersession Notice — 2026-10-12

下方等待共享 writer、implementation 尚未开始的状态已由用户“开workree实现”及
[Implementation Record](2026-10-12-supergrok-media-provider-implementation.md) 取代。
Grok auth/image/video 与 canonical wiring 已在 dedicated worktree 实现，candidate-8
完整离线 Harness 已通过；真实 generation 仍因 included-only 扣费边界未知而 `BLOCKED`。
首次必要审查触及输出上限，不构成 review PASS；最终整合、审查和 publication 必须读取
新 record 所指 exact delivery evidence。保留本文件其余历史调查与原 scope，不把
preflight publication 当作 activation。

## Purpose And User Direction

用户购买 SuperGrok 后要求接入 AI-VIDEO；明确选择视频/图片媒体 Provider、优先消费订阅权益。
同文件 ownership 确认后，用户选择先等另一任务提交共享文件，再修改它们。
因此本 checkpoint 交付新 [Spec](../superpowers/specs/2026-10-12-supergrok-media-provider.md)
和 [Plan](../superpowers/plans/2026-10-12-supergrok-media-provider.md)，实现尚未开始。
没有新费用、Auto Top Up、API-key fallback 或 Cookie 抓取授权；本轮未读取凭据或发起登录。

## Verified Findings

[xAI 官方公告](https://x.ai/news/grok-openclaw) 已支持外部工具使用 SuperGrok OAuth；
其链接的 [OpenClaw Provider 文档](https://docs.openclaw.ai/providers/xai) 说明同一认证可用于
image/video。不得沿用旧“订阅一定不能用于程序调用”的假设。
不过 [官方 FAQ](https://docs.x.ai/grok/faq) 同时描述 Extra Usage Credits / Auto Top Up，
不能把 OAuth 成功或 usage percentage 当成保证零额外扣费。

当前 `production/video.py` 的 registry/provider protocol 可注入新 adapter。
Kimi 提出的“已有 METERED 路径能承载新 video adapter”仅在真实收费/订阅契约成立时适用；
Parent 不接受凭空设置 monetary upper bound 来冒充订阅授权。
`production/image.py` preview、authorization、provenance 和 candidate 均硬限制 local-only；
其 remote integration 需要实际扩展原授权与 committer lifecycle，不能只增加 API wrapper。
compiler 是否需要修改由恢复实现时的 exact grammar seam 决定，不因新 Provider 名称机械修改。

真实 Grok account eligibility、media model、endpoint 的订阅计费、quota、overage hard boundary、
media quality 和 Final Acceptance 均为 `NOT_EVALUATED`。

## Investigation Evidence

- Read-only Kimi invocation：`f52b7836-c545-48dd-9999-07f2e627b8bd`；
  `subagent receipt` 核验 artifacts；classification=`PARSED`，2 wire requests，
  actual provider=`api.kimi.ai/k3`，effective route=`deep/k3[1m]/max`。
  Seal=`e044c68329ed199bfced98ef9862db740dbd77b94611803e3afacc46d23bb940`。
- Canonical receipt 位于 repository 外
  `~/.local/state/agent-subagent-router/runs/f52b7836-c545-48dd-9999-07f2e627b8bd/invocation-receipt.json`。
  Scope 实际读取 `vidu.py`、`image.py`、`video.py`；未修改文件、未执行 code/media、未访问 Grok。
  worker report SHA-256=`c1cdd0cf410f3ae43eb816799dbc3194ce2b675682662b44d579ba7492740a49`。
  Parent 重开当前代码核验关键 local-only、billing 和 registry claims；报告不是 implementation review。
- CodeGraph 核对 `ViduVideoProvider` 与现有 wiring/integration tests 的关系；源码仍为事实。
- Project Agent Memory RAG 两次在 system/current project Python 下均因缺少 `langchain_core`
  退出；没有 index rebuild、dependency install、网络 fallback 或进一步 RAG retry。
- `make harness-inspect` 默认 shell Python 缺少依赖；使用现有 `ai-video-p2` Python 和
  `PYTHONPATH=src:.` 后 inspect 成功。Working-tree inspect 仅解释当前 foreign delta，
  不构成该任务 nonempty exact snapshot receipt 或 tests PASS。
- 公开 OAuth source reference commit：`46fe51413407bdba71ceb3114b9e7f0079c82a7e`。
  无 Grok credential lookup、OAuth login、billing/account API query、image/video submit 或媒体生成。

## Ownership And Next Execution

本任务只拥有本新 record、Spec 和 Plan。现有 staged/unstaged Canvas/source/repair 修改保持原 ownership。
重点共享冲突是 policy、matrix、baseline 与可能需适配的 compiler/Router；用户选择等待其提交。
后续先核对 current HEAD、clean target paths 和 live writers，再按 Plan 实现、verify、Risk Gate、
commit/push。不要将本 docs checkpoint 的 publication 当成 Provider activation。

## Learning Evaluation

`distill-ai-video-learning` 结果为 `no_candidate`：这是单次 protocol/code investigation，
没有真实独立生成实验、controlled comparison 或已有 Learning Claim 的 material update。
不创建 pending claim，不修改任何 Skill/Policy/Gate。
