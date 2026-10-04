---
record_kind: architecture_implementation
topic_id: metaso-h3-frame-conditioning-coverage
learning_eligibility: ineligible
---

# METASO H3 Frame Capability Continuation

Date: 2026-10-05

## Baseline And Scope

baseline main/origin/main `bf2c81d2bbd2d568a0da78d86b9d4184aacbd05d`，写前 working tree 干净。
用户仅授权 adapter/capability coverage；H3 credential lookup、POST、permit consumption、
poll/fetch、媒体生成均禁止。本记录接续
[此前 admission STOP](2026-10-05-h3-api-opening-state-ab-admission.md)，不覆盖旧记录。

## Current Runtime Truth

`MetasoH3VideoProvider` 在 adaptive profile 增加 single `metaso-h3-fl2va-v1`：
IMAGE_TO_VIDEO、required first_frame、optional last_frame。existing capability grammar 已足够，
无新 GenerationMode/schema/Provider/transport。Ref2VA variant、profile pointer、compiler identity
及旧 native body 保持；fixed ratio profile 继续 Ref2VA-only，frame payload 不静默丢弃封存 ratio。

native content 使用 text → first_frame → optional last_frame；endpoint/model 仍为
`/v2/video_generation` / `MiniMax-H3`。frame 省略 ratio，Context IR 沿用 sealed profile。
Registry resolver 的 bytes/hash/size 精确核验，encoded MIME/dimensions 匹配，图片可验证；
无 resize/crop/transcode 或 unbound URL。first+last 分别合法即可；没有 upstream pair equality 证据。

upstream exact commit `0d1c72b1d80a54237b40adb111ae74d7fe38f4b4`，
nodes/client hashes、字段与 primary links 见
[研究](../research/2026-10-05-metaso-h3-frame-conditioning.md)。
[spec](../superpowers/specs/2026-10-05-metaso-h3-frame-conditioning.md) 和
[plan](../superpowers/plans/2026-10-05-metaso-h3-frame-conditioning.md) 为本 slice 的 self-reviewed 范围。

## Verification And Evidence

新增测试先验证 baseline 缺 frame capability / valid first-frame resolve 失败，再补 adapter。
METASO suite 58 PASS（2.67 秒），包含原 tests 与 38 个新增 parameterized cases。
覆核 old Ref2VA variant fingerprint
`fcfca8c570a0244792f956f9cdfb25c370d81c5ea454a7f220962ca57d78c24f`，
old multimodal native body SHA256
`4e78bc70637ffdba99da736288776f5529fdfc2dc6dcd2da11af32c6ef849cbc` 与 baseline 一致。

offline Router fixtures 的 source/target 都使用真实 METASO frame capability/profile/compiler，
source/destination execution stack 相等；EXACT_TERMINAL 消费 terminal，HardCut/C2 消费
distinct derived keyframe。两者走 existing Router → remote compiler → resolve → preview → native body，
first+last requirement 同样编译通过。explicit soft Ref2VA FULL 继续
`CONTINUITY_FRAME_CONDITIONING_REQUIRED`。没有改变 continuity tests 或任何 owner。

exact request/bound/compiled/resolved/preview/native hashes 与 zero-effect counters 保存在
`runs/metaso-h3-frame-capability-20261005-001/offline-pre-submit-proof.json`；
evidence_kind 明确是 `OFFLINE_ROUTER_FIXTURE_NOT_ACCEPTED_MEDIA`，不授权实际提交。
必要 continuity suite 输出 `runs/metaso-h3-frame-capability-20261005-001/continuity.txt`；
完整 changed-path checks 及 final status 的 canonical owner 为
`.agent/harness/runs/metaso-h3-frame-capability-20261005-001/receipt.json`，
不能用本记录代替 fresh receipt/scope/hash verification。

受管 Kimi read-only mapping：首次 `7d68d310-8520-427e-b52b-854476d153bf` response-body
断连，无 terminal report；partial 隔离。缩小问题后的第二次
`e6b1bbb1-ccec-463a-a92b-f4437f6a7c74` PARSED、2 wire requests，route/report/Read hashes
已核验；Parent 只采纳 optional-last grammar 和 upstream 未声明 pair equality，server behavior 未验证。
Kimi 工程调用不是 H3 视频 submit，也不构成 Provider media acceptance。

## Remaining Blockers

integration 额外发现 `_remote_video_native_prompt.py::_state_text` 只表达 TYPED_TEXT；
canonical sequence 使用 TYPED_HASH，Router 可以选择 frame capability，但 compiler 仍返回
`PROMPT_EXPRESSION_UNSUPPORTED`（open/close state）。专门回归保持这项 fail-closed。
opaque hash 不包含可编译 prose，不能把 digest 写成虚假的语义状态，或为 B 换成 text truth。
本 slice 不改 prompt architecture。完整 text-intent fixtures 的 native body PASS 与 canonical
typed-hash sequence compile BLOCK 是不同证据层，不宣称真实 B 已到 pre-submit。

历史 S02 的 missing activation、typed causal close 与 raw FAIL 未修复；历史 S03
`FAIL / OPENING_STATE_RESET` 不变。下一步仍需要 fresh accepted source，但还须先由现有
native-expression owner 合法处理 typed-state conditioning，之后才能真实 B submit。
没有新增 media-quality/continuity guarantee，没有 production driver 或 architecture expansion。

## Learning Evaluation

`record-ai-video-session` / `distill-ai-video-learning` 结果为 recorded / no_candidate。
这是单次 offline implementation，没有独立真实媒体实验或被 material update 的既有学习 claim；
不创建 learning placeholder，不修改 Skill/Policy/Gate 或历史记录。
