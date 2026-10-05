# Typed Causal Native Expression Research

## Baseline

`git fetch origin main` 后 `HEAD == origin/main == 4cc1b55d81c881711175c71fa18a1f4d7326c92f`；
当前 `main`，初始 working tree 干净。仅离线研究、实现、verification；零真实 Video Provider effects。

## A. Native Expression Owner

[`_remote_video_native_prompt.py`](../../src/ai_video/production/_remote_video_native_prompt.py)
是共享 `remote-video-prose-v1` owner。实际调用者是 METASO H3，以及 recipe 分支的
MiniMax H3、Hailuo、Seedance，Vidu `/4` recipe / named-subject 分支。
[`_vidu_prompt.py`](../../src/ai_video/production/_vidu_prompt.py) 另外拥有 legacy `/1` prose
和 subject labels；subject `/4` 的基础 prose 委托 shared owner。
[`_h3_prompt.py`](../../src/ai_video/production/_h3_prompt.py) 属于 local H3 grammar，
不是 remote adapters 的 prose owner；本任务不迁移其 grammar 或 historical branches。
CodeGraph 已核对 shared compiler 的实际 callers；源码为具体事实。

## B. Compiler Input

shared function 只有 `ProviderNeutralVideoRequirement` 与 optional `voice_route`。
requirement 保存 state kind/hash、intent identity、source-request seal，没有 policy 或 causal facts。
[`ProviderBoundVideoRequest`](../../src/ai_video/production/_shot_router_contracts.py) 有 recipe、
target、route/compiler identity，但没有 transition policy。recipe 保存 expression coverage，
并非 causal fact preimage。route decision 的 policy/binding hashes 也不能反推 facts。
`_state_text` 只支持 `TYPED_TEXT`，因此 opaque digest 正确返回 unsupported。

## C. Authoritative Lineage

`ContinuityProviderRouteBinding.transition_policy.causal_state_changes` 独占 authored edge facts。
policy model 重验 hash、canonical unique dimensions、release/bridge semantics；
`validate_causal_transition_intent` 验 target Shot/intent、完整十维和 CARRY equality。
`validate_continuity_transition` 绑定 target/context/current snapshots、FULL frame obligation。
[`_sequence_source.py`](../../src/ai_video/production/_sequence_source.py) 的
`require_sequence_source` 从标准 Project/Manifest/receipt reader 重开 adjacent activated source、
exact raw media evaluation、hash-bound causal-close PASS、source/target intent 与 stacks，
`require_causal_columns` 重算 previous source-close 和 current target-open 两列 hashes。
cross-stack 还重开 prior destination selection 与 Planner seed derivation。

## D. Minimum Seam

不能仅从 bound request 或 requirement 复用 facts：它们不存在其中。新增的输入只是一份
ephemeral、owner-issued、只读 compiler context，不新增 durable schema、Planning truth 或 selection。
sequence owner 在 current Project 和 exact existing routing 上重开上述证明后签发；
grammar 仅取得 target-open facts，不接收整个 policy、anchors、QA、execution stack 或 route。
context exact 绑定 requirement/selected bound，并在每次表达前重验 seal、complete column hash。
adapter 只转交 context，能力、bindings、payload、transport 不变。

复用既有 `destination_planning_request` preimage 字段，使 same-stack 也保留它；该字段目前
仅 cross-stack 写入。context 签发时通过已有 pure Planner/Readiness seam 重开 final requirement，
核对 embedded policy、source-request hash、authoring-evidence seal，拒绝另一个合法但不相同的 policy。
缺 preimage 的历史 binding 保留 immutable replay bytes，不能取得新 typed-hash prose coverage。

## E. Endpoint And Modes

previous close → current open 是 pairwise edge；不证明 current close。
既有 sequence fixture `_intent` 的 current close 是 `TYPED_HASH(source_close column)`，这是
fixture authored choice，不使 previous-close facts 自动成为 current-close facts。本 slice 不修改它。
仅 current open hash 合法展开；current close hash 或 TYPED_REF 继续 unsupported。
CARRY 保持 existing equality validator；VISIBLE_CHANGE / AUTHORIZED_RELEASE 不添加故事、桥梁或新词表，
只表达已经 authored 的 target-open endpoint，不将前镜到开场的变化误写成本镜必须执行的动作。

## F. Remaining Boundaries

cross-stack prior neutral seed 若自身含 arbitrary typed hash，其无 edge compilation 仍 unsupported；
不得借本任务给它预授权 future policy。任何真实 B 前仍需 exact authored current close、合法 prior
selection（如跨 stack）与 fresh accepted source。旧 S02/S03、FAIL、edited evidence 不修改。
旧 TYPED_TEXT exact bytes/hash、Ref2VA body 和 FULL soft-reference block 必须保持。
