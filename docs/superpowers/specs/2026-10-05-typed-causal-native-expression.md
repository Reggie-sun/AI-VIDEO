# Typed Causal Native Expression Spec

## Goal And Authorization

在 `4cc1b55d81c881711175c71fa18a1f4d7326c92f` 上修复 verified sequence opening
`TYPED_HASH` 的 remote native-expression coverage。用户授权 bounded implementation；
Parent self-review 后继续。零真实 Provider credential/POST/poll/fetch/media/paid consumption。

## Root Cause And Owner

hash 是 seal，`_state_text` 不能从 requirement 的 digest 反推 facts。
唯一 facts owner 为 existing route binding → policy v2 → `causal_state_changes`。
source acceptance、column hashes、target intent/identity 由现有 sequence validators 证明。
详细调用关系见 [research](../../research/2026-10-05-typed-causal-native-expression.md)。

## Compiler Evidence Contract

新增 private ephemeral `VerifiedCausalOpeningExpression`，由 `_sequence_source.py` 签发。
签发必须重开 current loaded Project、existing accepted source、policy/binding、existing
materialized planning request preimage、Planner-derived final requirement、selected bound target/route。
复用 `destination_planning_request` 字段保存 same-stack preimage；无新 durable state/schema。
context 只携带 complete causal column 的只读语义投影与 exact requirement/bound/proof seals；
任意 construction / copy / reseal 不能取得 owner issuance；进程内 weak identity registry独立保存
原始issuance seal，拒绝复制或原对象/nested facts篡改后重封的context。无Adapter mint authority。
native grammar 每次消费检查 owner issuance、sealed identity、target/hash 对应，再确定性排序表达 facts。
原 hash 仅为 control-path coverage，不进入 narrative text；全局 5000 字符预算仍适用。

## Endpoint Contract

current `open_state` 仅使用 `target_open`；previous `source_close` 只用于校验 lineage。
current `close_state` 若是 hash，无 authoritative current-close owner，本 slice 继续 unsupported。
不得复制 current open 或 previous close 冒充 current close，即使 digest 相等也禁止。
所有 authored fact text 原样进入 endpoint prose；不硬编码人物、道具、对白、release 或方位。
transition modes 继续由现有 policy validator 裁决；不增加 vocabulary，不把 edge change 误写为本镜动作。

## Failure And Compatibility

non-sequence hash、missing context/preimage、wrong policy/binding/target/intent、missing/duplicate dimension、
CARRY mismatch、column mismatch、forged/tampered context 均 fail closed。
shared expression 拒绝时保留 `PROMPT_EXPRESSION_UNSUPPORTED`；owner lineage reopen 使用 existing typed
failure，不 fallback 到 digest、unspecified、legacy prompt 或 TYPED_TEXT。
TYPED_TEXT 的既有 bytes/hash 与所有不涉及新 context 的 request/native body 保持不变。
TYPED_REF 不新增 coverage。现有 public two-argument adapter calls 保持有效。

## Provider Scope And Replay

共享 remote grammar 的 METASO、MiniMax H3、Hailuo、Seedance、Vidu `/4`/subject 基础 prose
可消费 optional context。grammar support 仅为 compiler interface declaration，不参与 Router selection
或 Provider capability advertisement。local H3 / Vidu legacy grammar 不迁移。
标准 preparation 和 effect 前 current compilation 必须重新由 sequence owner签发 context；
不 persist context、不恢复 process token、不用旧 prompt 旁路。voice/subject exact recompile 使用同一输入。

Compiler 对 native control-path 的新 hash coverage重新调用 shared owner，不能仅相信 caller
自报；subject grammar例外须绑定selected subject compiler且必经subject exact recompile。
Recipe 原 native_text 中派生的 opening digest，在这一已验证 coverage 下只从临时
lexical projection移除；原 recipe、QA observable、intent path与所有其他文本义务保持原样。
Vidu named-subject R2V 的 FULL conditioning gate保持阻断，未提供新的 FULL subject route。

## Verification

覆盖 text exact regression、arbitrary hash、ten dimensions、hash/target/policy/binding mismatch、
missing/duplicate/CARRY、current close refusal、owner token tamper、canonical sequence source reopen、
HardCut/FULL/C2 METASO compile/resolve/native pre-submit、EXACT_TERMINAL、soft Ref2VA FULL block、
normal Ref2VA body hash，以及所有 shared adapters/voice/subject regression。
真实媒体、质量和 remote source资格均 NOT_EVALUATED；fixture evidence 不冒充 accepted media。
exact staged Harness、task Architecture Gate 和 applicable stable-snapshot independent review。
full suite现有1800s上限在约5.9k tests、约37%进度时timeout；仅将有限verification wall budget
调整为7200s，保留旧receipt，不减check、覆盖范围或通过标准，不改变任何Provider预算。

## Non Goals

不修改 `ContinuityTransitionPolicy`、`CausalStateChange`、`TypedStateReference` schema/invariant；
不改 Planner derivation、classification、Router selection/authority、capabilities、transport、QA acceptance。
不处理旧 S02、不生成 fresh source、不解除历史 FAIL。无新 prompt architecture、fallback 或 Provider。

## Self Review

Option 1 不成立：existing bound/requirement 没有 facts；existing route binding/preimage可在 owner
中复用，因此仅新增 process-local compiler context（Option 2），不复制 continuity truth。
current-close / cross-stack seed 缺证保留 blocker；不为理想链路修改 authored state。
同一 exact final snapshot按 repository T3 做双独立 read-only final review；Parent裁决 findings。
