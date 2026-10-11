---
record_kind: architecture_implementation
topic_id: director-source-preservation
learning_eligibility: ineligible
---

# Director Source Preservation Record

Date: 2026-10-11

## Purpose And Scope

用户明确要求“修改”Director 规则，纠正将按画布复刻默认当成重新导演设计的问题。
本次只修订 advisory routing、prompt authoring 边界与对应历史记录；不恢复尚未完成的
paid-retarget 实现，不改 v3/v4 validator schema，不提交 Seedance 或生成新媒体。
计划为 `docs/superpowers/plans/2026-10-11-director-source-preservation.md`，由 Parent self-review。

## Corrected Boundaries

- 已选来源复刻/原样 baseline：核对 exact 原文与 reference identity/role/order，保持实际生成输入；
  将来源语义不变地导入 approved Shot。缺项目 artifact 不授权优化；缺来源证据、实质歧义或
  contract 无法忠实表达时报告缺口，不为填字段编造镜头、动作、对白或硬验收要求。
- 新创作/已授权优化：继续 Director design 与既有 coverage validator，保留 explicit constraints，
  review source→inventory→coverage 并公开 Director choices。
- 已知失败 repair：绑定 exact 失败与 unmet requirement，保留完整目标和已满足部分，只调整对应范围。
  失败不自动授权全片重设计、retry 或新的 paid call；实质创作变更沿既有 task decision gate。

`open-video` Step 1 是上述 advisory 目的边界；playbook 保持 routing pointer，matrix 同步 owner/invariant。
`seedance-authoring` 与 `authoring-common.md` 要求核对 exact native prompt：长 prompt 中仍有原文引用
不证明原样输入，内部 enums、`unspecified`、验证输出或完整 contract 不机械拼入模型文本。
必要 Provider grammar/reference 技术适配展示 source/input diff，不冒称 unchanged-input baseline；
user-authorized model/resolution 差异单列。复刻不保证相同生成像素，也不构成 exact-replay 授权。

所有分支仍保留 approved Shot、exact selected profile、canonical adapter/committer、凭据、预算、
egress、intent/one-use permit、unknown fail-closed、逐 Shot 媒体 Gate 和真实成片验收。
Product Runtime 不调用 Skill，`runtime_skill_calls = 0`。规则修订没有改变旧片 POV FAIL 或媒体验收状态。

## Mapping And Parent Adjudication

一次受管 read-only Kimi mapping 核对旧 routing 的矛盾及最小 owner，不充当 final implementation review。

- contract: `5ce2d375-294f-4050-8dc0-7b48be3b10a2`；seal:
  `4a3704a41b7b98c1ba4ba3d8bf50dcd4338829576c650a51c145b3fab0edafc4`。
- invocation: `ee9f337b-6890-4f3c-b430-7b37c55cbe9f`；qualification:
  `4f2d5dc8-4234-4665-b382-e82f1ad6cc00`。
- canonical receipt: `/home/reggie/.local/state/agent-subagent-router/runs/ee9f337b-6890-4f3c-b430-7b37c55cbe9f/invocation-receipt.json`；
  report SHA-256: `71f0d133f881b3a70aa4da5e14b06be39f6fe680a7e98cb9908fa530733e2ccc`。
- `PARSED`、exit 0；7 次 mechanically observed `k3`/`max` wire requests、orchestration retries 0，
  internal retry count `unknown`。Parent 核验 artifact hashes 与 10 个 observed read spans 的来源 bytes，
  待该 invocation terminal 后才修改封存路径；不声称 `PARSED` 本身为 acceptance。

Parent 采纳 F1/F3 的“项目格式缺失不等于创作未定”、F2 的 schema 不变、F4/F5 的 canonical input/repair
ownership、F8 的复刻与 creative re-edit 区分。F6 只同步现存测试名的 design scope，未添加镜像文案测试；
F7/F9 核对既有 Harness routing。报告未读 common reference/OpenVideo tests 的不确定性由 Parent 当前读取解决。
复刻留存沿 existing approved Shot 与 source/input evidence，不新增 creative_input_kind 或第二 evidence schema；
授权依据仍归当前用户任务，不由 Director rationale 伪造新的授权。

## Verification And Risk Gate

Focused working-tree tests：`test_open_video_skill.py`、`test_seedance_authoring_skill.py` 与
`test_runtime_skill_boundary.py`，58 passed。playbook 保持 209 lines / 17977 bytes；`git diff --check` 通过。

规则候选的 exact staged Harness：

- base HEAD: `b178413d2ab9b7c08ef355b7eab9f931da953a94`。
- index tree: `2e1d0bd41e5b00346ecd69c337ae9a13e150d2db`；cached patch SHA-256:
  `e08d84573531f62b5b6dff5bd6805687253d83178581968372828c1d83947a27`。
- receipt: `.agent/harness/runs/director-source-preservation-20261011-rules/receipt.json`，10 checks passed。
  `verify-receipt` 核验 fresh、snapshot_matches、artifact_integrity、complete_completion_proof 与 cleanup。
- 其 7 个 changed paths 不包含此前 dirty recovery code/spec/plan/records；验证隔离于 exact staged snapshot。

上述 verification 后 Parent 对该稳定规则候选评估为 `KIMI_REVIEW_NOT_REQUIRED`：用户未要求该 snapshot 的
Kimi review；没有 runtime/credential/paid permit/durable state 实现变更，不存在本 diff 导致重大泄密、严重
越权或难恢复 Production 损坏的具体 failure path。自然语言分类仍需 Agent 判断，但新规则明确保留来源与所有
执行/媒体 gates；未找到同时满足“重大后果、验证后实质缺口、adversarial review 独立增益”的触发证据。
Mapping 未被当作 final review；Parent 仍拥有最终 diff 裁决。

本记录与旧记录 supersession notice 纳入最终 exact staged snapshot，其 completion proof 由
`.agent/harness/runs/director-source-preservation-20261011-final-v2/receipt.json` 的实际 verdict/hash 独占。
新增记录不改变已核验规则 bytes；publication 以该变更 commit 与 origin/main 的实际 SHA 为准。

## Learning Evaluation And Limits

调用 `record-ai-video-session` 并自动评估 `distill-ai-video-learning`：`no_candidate`。
本次是用户直接授权的规则修订，没有新增受控媒体对照或可归因的模型质量证据，不能据此断言扩写更差、
原文一定成功或新规则已修复 POV。无新 Learning Claim，不创建 placeholder，不更改其他 adopted claim。
本地 experience 查询成功，命中仅作为 advisory discovery；本次 reopen 与 supersede 的旧 owner record 为
`docs/record_for_agent/2026-08-30-promptless-long-form-director-preflight.md`，保留其历史验证与 chronology。
没有为记录刷新 RAG、运行媒体分析或追加 Provider 请求；其他 unfinished dirty work 保留，不进入本次提交。
