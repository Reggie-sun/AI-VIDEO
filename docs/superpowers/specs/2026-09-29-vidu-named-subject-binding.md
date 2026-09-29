# Vidu Named Subject And Voice Binding

## Goal And Authority

`SCOPE AUTHORIZED / SELF-REVIEWED`。依据当前用户指令接通 Vidu Q3 R2V 的角色参考、命名主体与 typed 声线字段，保留原 COCO / Nosha 目标及全部八次历史 physical submits。原声线、对白一次、正常速度、因果链及跨 Shot 连续性仍由真实媒体 gates 验收。用户允许分 Shot，不再要求固定 17 秒或整片一镜到底。

## Current Evidence And Corrected Premise

当前 `vidu.py` 只发送 flat `images`；Planner、requirement 和 Router 已有 Character、Scene、owner-bound references 和 `VoiceSpeakerRequirement`，compiler 转为 generic image binding 时丢失角色归属及 voice ID。

2026-09-29 重新核对 [international R2V](https://platform.vidu.com/docs/reference-to-video) 的 `subjects.name/images/voice_id`、每主体最多三图、`@name` 与 5000 字符；[domestic R2V](https://platform.vidu.cn/docs/reference-to-video) 附有 Q3 声线限制，[subject library](https://platform.vidu.cn/docs/subjects) 明确写 Q3 不支持音色 ID。字段存在不能证明该模型使用它。当前接入只声明 named image references，`voice_ids_supported=False`；fixed/native original-voice 请求在 effect 前 typed unsupported。不得借国际站缺少警告证明功能有效或换 egress。

原 COCO 音频为 6504 ms / 208173 bytes / SHA `32b3e405b704bff738882fe433c9cb2aa984f08b991109541668170b5db15c7a`；[clone API](https://platform.vidu.com/docs/voice-clone) 要求至少 10 秒。禁止重复、补静音、合成或借 failed candidate 伪造原素材。当前账号 exact Secret Service supplier 经正确本用户 bus 可用，两次 bounded GET 返回 200，私有主体列表为空；这不证明所有 standalone cloned voices 都不存在，也不证明 Q3 entitlement 或音色有效。

## Owners And Contract

- Character / Scene / canonical Shot `voice_routing` 继续独占创作身份及台词归属；不增设 parallel authoring owner。
- 新 `video_subjects.py` 独占 immutable subject shape、兼容序列化与 image partition。`_vidu_subjects.py` 只从 exact requirement + owner-bound Router inputs 推导 Vidu subject names/images/voice metadata，复核 owner ID/hash 和 authored reference membership。
- `video_compiler.py` 保持 sole request constructor；native prompt 的 subject projection 必须与重新推导值相同，不能允许 adapter/caller 自报另一映射。
- `video.py` request/resolved/activation hashes 绑定所有 populated subject fields；current execution binding 重新核对该 projection。新 hashes 分别为 request `/9`、resolved `/10`、activation `/8`、compilation `/2`；empty fields 完全省略，历史 bytes/hashes 保持。
- Request fingerprint 投影移到既有 `video_request_models.py` immutable request contract boundary；保留 `VideoGenerationRequest._fingerprint_payload` 的 public 调用与历史 hash，防止 oversized `video.py` 增长。
- `vidu_profile.py` 为 `viduq3` / `viduq3-turbo` 增加独立 `r2v-subjects-v1` capability，最多七主体、三图/主体、七图总计。既有 capability IDs/profile pointers 与 flat 请求恢复保持；不使用 I2V `viduq3-pro` 代替 R2V。
- `shot_router.py` 在 canonical routing 时检查 named capability 与 compiler v4 配对，避免旧 compiler 因新 variant 出现重复候选歧义。通用 compiler 与 execution binding 重算 exact named prompt，不接受仅重封 hash 的映射/文字替换。
- `_vidu_prompt.py` 的新 version `4` 机械表达 named reference 职责与 dialogue speaker `@name`；完整 intent 使用现有 remote native prose。v2/v3 保持历史路径，不重编译旧请求。无法表达角色归属、非 canonical references、重复/遗漏 images 或声线控制则 typed unsupported。
- `vidu.py` 对 populated bindings 只发送 `subjects`，显式 `auto_subjects=false`；所有图片先经 exact byte/size/SHA 校验。voice field 有 typed protocol 投影，但当前 capability 拒绝任何 populated voice ID，禁止静默忽略。Flat 路径继续使用原 `images`、原 prompt limit。

## Safety And Compatibility

不修改 credential supplier、预算账本、permit、unknown recovery、committer、timeline、QA 或原声线资格。现有 native voice identity blocker 保持。新的 field projection 不能创建 clone、上传素材、自动选路、fallback、activation 或代替 acceptance。跨角色共享同一 image、任意声线 label 和 owner/hash 篡改拒绝。历史 request/receipt/source/消费 immutable，不复用旧 grants/permits。

## Acceptance And Verification

工程 criteria：标准 Router/compiler/request/resolve seam 可表达三图的不同职责；payload 与 canonical ownership、request/resolved/activation seals 一致；unsupported voice 在任何 transport/secret/permit consume 前拒绝；旧 flat hash/replay 和 payload 保持。覆盖真实行为、篡改、geometry/count、missing owner、legacy reopen 与 voice rejection。

针对性 suite：Vidu、subject、remote prompt、provider-neutral、generation execution 和 native voice identity。完成时检查 exact staged paths 的 policy 路由、实际 checks 与 source hashes。用户禁止 worktree，禁止运行会创建 worktree 的 Harness verify；direct policy evidence 必须清楚标出 `canonical_isolated_harness_receipt=null`，不冒充 canonical receipt。

媒体 criteria 仍需 exact original voice 身份、实际有效 Q3 control、有限新 quota、标准 generation seam、逐 Shot MCP Gate 与成片观看/聆听。当前 capability/input blocker 保留；不为绕过它生成无原声线视频。

## Self Review And Implementation Review

Parent 已核对 code、官方矛盾、原素材与当前 account reads；选择 typed mapping + fail-closed capability，而非从字段存在推导原声线有效。属于 T2 Provider/shared request change，不改变 paid/credential/recovery/QA acceptance semantics。完成 native verification 后，对 stable exact target 执行一次受管 read-only Kimi adversarial review；最多三轮，失败按 `SUBAGENTS.md` fallback，findings 由 Parent 逐项裁决。该 review 不产生媒体 acceptance。
