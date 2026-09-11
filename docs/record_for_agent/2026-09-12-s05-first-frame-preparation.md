---
record_kind: session_summary
topic_id: jieshi-s05-first-frame-preparation
learning_eligibility: ineligible
---

# S05 First-Frame Preparation

## Outcome

2026-09-12 后续人审：用户对“S05 的画面、倒影同步和原生声音，你确认可以保留吗？”回答“通过”。重新核验 exact MP4 `17010995…0e8424` 后，保存 `preparation-s05-v1/s05-attempt01-human-confirmation.json` 与 `s05-attempt01-human-next-shot-gate.json`。结合既有 sampled MCP evidence，raw Gate PASS、holistic KEEP；P4 final-composition 仍 NOT_EVALUATED，无 activation。下文生成 checkpoint 的待人审状态已由该确认取代。

2026-09-12 更新：用户对展示的 S05 首帧回答“可以”，随后要求“继续”。已完成单次 Vidu Q3 Pro I2V 提交与原生音轨 MP4 下载；下文“待首帧确认、未导入、未生成”的初始 checkpoint 保留为历史，已由本节取代。当前 raw Gate `NOT_EVALUATED`、holistic `UNDECIDED`，等待 exact MP4 正常速度人审；未 activation 或提交 S06。

## Native-Audio Generation Result

- Exact MP4：`runs/jieshi-e01-i2v-20260907-attempt10/production-s05-v1/state/video-generation/fetch/files/17010995fa25ad2d41d15c45010e940d611df6c2b02aa075dddd85b8780e8424.mp4`；SHA-256 同文件名；3,048,481 bytes。MCP probe：4.042 秒、1080×1920、24fps、97 帧、AAC 48kHz 双声道。
- 一次实际 POST，于 2026-09-11 16:35:15 UTC 接受；body SHA-256 `076f7c37e22598feaf373fe0b7913d406335c6a7e35d2ff3634d476884821f40`，submission fingerprint `643538fd6b7b0b7e4eeb521692b2ece0af6fe265484989ed86fb615391690b1c`。16:37:06 UTC 观测 succeeded，16:37:35 UTC fetched。Ceiling=1、used=1，没有第二次生成。
- 第一次 fetch 被 public HTTPS 地址检查拦截；复用已审查的进程内 GET-only public DNS helper，限定原 CDN host，保留原始 hostname/SNI/TLS 和 public-address validation。仅恢复同一已成功任务的下载，无全局网络修改、重新提交或新 permit。
- project-local `video-analysis` MCP 已执行 exact probe、review、0.5 秒间隔抽帧。Parent 查看 0、0.5、1.5、2、3、4 秒：左手从低位抬起，尾态握拳，窗中存在对应手势，右手手机低位；采样不能证明全程光学正确或精确同步。FFmpeg 完整音轨 decode 成功，mean -34.2 dB、peak -21.1 dB；非静音不证明声音语义或听感。
- 当前 `s05-attempt01-post-media-gate.json` 对 QA inventory 逐项保存 `NOT_EVALUATED`，阻断下一 Shot；P4 final-composition 单独保留待验证。MCP 原始文本与抽帧 metadata 位于同 preparation 目录。没有将工具的 `issues=[]` 解释为人审通过。

## Preparation And Verification

- 使用已确认 PNG `d3be37aed9166fa06b7df968c3f8ce76ad63d273feff4040131604b167c5c23f`、941×1672，经真实 `HumanImageImportReceipt` 引用 registered S01 image，canonical committer bootstrap S05。依既有 authoring 为 S05 增加 `B03-SC01` storyboard beat，没有错误沿用 S04 的 B02。
- 编译第一次拒绝 QA `s05-natural-motion` 的 composite `generation_intent.motion_envelope` expression。将其绑定到已表达的 string `generation_intent.subject_action.progression`，observable/tolerance/proof 保持；通过唯一 committer 发布 QA revision 2/profile 1.1。保留旧 QA artifact，没有重建 root、绕过编译或修改产品源码。
- 当前 QA `91f817495c847bc5b90f5101a4d37846c8b60af45f45b8e5fabf4acb05306325`；binding `de097785545ba9fedc0cc16c493f522cb49a10bf81dbb757e9a83f01a2ac3342`；resolved `d18a47e2c04e009ad9d85efdad1aa6ffe191df5da42bc0f4449c833d69762408`；preview `e40ec596317a65b0cc43b640e6c68934c3c9dfc8d21da011a05f2beb5049662a`。2332 字符 prompt 保留抬左手、缓慢握拳、同步反射与 native audio。
- `reviewer_xhigh` 对最终封存结果审查为 `accept with concerns`，无 blocking issues；parent 再次通过 `binding.validate_current_project()` 并核对请求、PNG、前镜 Gate、S03/S04 Manifest hashes。Fetch 后标准 loader reopen 为 Manifest r12，前镜 Manifest 未变。
- Vidu/execution guards/image-import/recovery focused tests：140 passed；runtime Skill boundary：2 passed。初次误写 runtime test filename 未运行测试，随后按 policy 中正确文件执行通过。Policy audit 仍有既存三个 unmapped paths，无 fresh exact Harness receipt；不声称工程 Harness closure。真实 Provider/media 结果与离线 tests 分开记录。
- 本轮 `record-ai-video-session` 更新同一记录，`distill-ai-video-learning` 自动评估为 `no_candidate`：一个未获人审的 S05 attempt 不构成同 scope 的重复证据或受控多臂比较，也不将不同 Shot 的调用数当作模型质量支持。

## Historical First-Frame Checkpoint

用户要求开始 S05，并明确确认 S04 画面与原生声音可保留。本轮保存 S04 exact 人审和 next-Shot raw Gate，制作 S05 首帧候选。尚未提交视频、创建 S05 Production root、导入候选或签发 permit。

S05 按既有分镜回到林砚的窗与座位，抬左手并慢慢握拳，倒影同步恢复；原生声音延续开启意图。静态候选保持左手低位，窗中已出现林砚倒影。动态同步与成片质量尚未验证。

## Evidence

- S04 MP4 SHA-256：`a2a0251715de19e52d5ba80c335db06afb89f083c0c546cf5cd7c246b64aee4e`，本轮重新计算匹配；人审原话“可以”及所回答问题保存在 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s04-v1/s04-attempt01-human-confirmation.json`。新的 `s04-attempt01-human-next-shot-gate.json` 保留旧 Gate hash；只更新 raw acceptance，不证明 P4 混音。
- 使用 `load_production_project()` strict reopen `production-s04-v1/project.yaml` 定位 S01 registered image，参考 SHA-256 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`；不是 S04 尾帧或未注册视频截图。
- 内置 `image_gen.imagegen` 编辑该参考一次；实际 prompt、候选、测量与来源保存于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s05-v1/`。候选名 `s05-first-frame-candidate-v1.png`，完整 SHA/尺寸见 `first-frame-result.json`。不声称具体 backend model。
- `retrieve-ai-video-memory` 已执行 experience 查询，返回含 stale 的 advisory fragments；本轮事实来自 exact 本地输入、分镜与当前代码。没有将历史提示当作当前 PASS。

## Remaining Boundary

`HumanImageImportReceipt` 需要 human approval，且时间不得早于 image import。用户对 S04 的确认不自动覆盖之后才生成的 S05 PNG；候选需展示并获确认后，才能通过既有导入与 Planner/Router/compiler/Provider seam。视频 task ceiling=1，used=0，未新建付费调用。当前首帧制作是 Agent 为 S05 机位与反射状态选择的准备动作，不宣称 Router 已比较并判定 I2V 为实证最优。

## Verification And Learning

检查图片可读性、实际尺寸、SHA-256 与 S04 exact MP4 identity；无产品 source 改动，无 fresh isolated Harness receipt，无视频生成或质量 PASS。`record-ai-video-session` 稳定 checkpoint 已记录；`distill-ai-video-learning` 自动评估 `no_candidate`：单张未获人审的候选不满足重复实验或受控对照阈值，不创建 placeholder。其他 staged/dirty files 保留。
