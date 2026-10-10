---
record_kind: media_experiment
topic_id: reusable-canvas-mecha-ant-production
learning_eligibility: eligible
evidence_index_version: "1"
---

# Mecha Ant Canvas Seedance 480p And MCP Gate

Date: 2026-10-11

## Goal And Current Outcome

用户选择现有机甲画布继续[spec](../superpowers/specs/2026-10-11-reusable-canvas-production-harness.md)，
保留《美丑》拒绝证据，并继续Seedance480p授权。一次实际生成取得完整15秒蚂蚁脱困单元的raw MP4。
它来自已读development样本《机魂觉醒》，不是holdout、完整机甲片或代表性Pilot。

已知视觉FAIL：受阻段显示主角完整头背和身体，是第三人称后方跟拍，违反封存的主角眼睛视点。
初次analyzer未实际听看声音/完整连续运动，保持NOT_EVALUATED；用户后续已确认声音，见下节独立human证据。
canonical experience仍为`EVIDENCE_GAP + QUALITY_FAILURE`，
`validate`实际被Gate拒绝，Manifest未变；没有activation、composition、render或下一Shot提交。
attempt仍`running`/phase`validate`，这是有证据的阻断，不伪造terminal failed、quality rejection或abandonment。
完整spec尚未完成，AC-2完整资格仍PARTIAL，AC-7尚未验收。

## Source And Creative Decisions

证据根：`runs/canvas-mecha-seedance480-20261011-001/`。source node`node_fgfrmwy9ss`，
引用`node_pftt2pa76z`/resource`ea03ccdb-4eaa-4d93-9ea9-60a737931582`。
完整source inspection保留93nodes/118edges及未支持subject/audio/timeline字段；只明确选择可执行的蚂蚁单元，
不根据名称或坐标拼整片。原文、source版本和adaptation分别保留。

一张场景参考用于破瓶、沙土、叶石、黑色蚂蚁及二维手绘风格，不当first_frame或独立角色portrait。
平台预览WebP720×408，85136bytes，SHA`56f746591db43cc9b501ce1d9dd45bb02b4c7f9054261d86144029887eb61733`；
同像素RGB PNG564238bytes，SHA`2713555c702c7269139ddbb09f446bfbbd11b3a6907a87aa892d91b09e5be617`。
原1920×1088仅为平台元信息，没有冒充取回原图/原generator receipt。一次尝试更高分辨率URL返回403，
随后从实际DOM预览导出；这个只读素材GET不计视频POST。signed URL不进入本记录。

Director三个内部摄影段落：3秒建立顺时针围瓶困境，8秒主角第一人称碰撞/穿叶/绕石并坚持，
4秒一次越出外缘并带领同伴。它们在一次15秒native generation中完成，未把Provider上限当导演依据。
群体场景没有独立主角portrait，取消Agent误加的Character身份锁；完整动作、主观视点与跟随结果仍保留。
无对白源文不被改成新增对白；保留音效、无BGM/字幕。完整15项raw QA要求没有在看到结果后删改。

独立concept调用`773cb6b3-6175-4214-b6f1-cde38eeca1b3`，qualified deep route
`4f2d5dc8-4234-4665-b382-e82f1ad6cc00`，receipt为PARSED/exit0、5个actualRead、2个wire requests。
report SHA`3d69b8daa08f8dce932d1395bd0a1b8ad27913fcc9ea93026322a521e9154346`。
Parent确认并修正POV自相矛盾、重复脱圈、顺时针绑定及动作/分镜/正面音效检查；
864×496疑问由当前Seedance2.0 capability raster反证，不采用2.5的854×480。
补充复核`a1e60f57-5978-4a1c-8649-7070e33bbb41`读5份文件、2wire requests，
终态`STRUCTURED_OUTPUT_EXHAUSTED`/exit1，无可采纳报告、不当PASS，也未自动重试。
Parent逐项裁决与Director/goal-binding/native compiler检查独立成立，不冒称补充调用审过当前bytes。

## Paid Execution And Exact Artifact

现有generic data-configured caller只调用`CanvasProductionService`与既有owners。
用户指定`.env`的exact private supplier继续使用，credential仅内存、不输出、不复制。
human素材使用权原声明与本次明确来源选择分别封存；场景无人物，实际分类为ordinary non-character image。
新profile消费既有operator内部定额`50_000_000`microCNY，非市场价或账单。
新单元submit上限1、auto resample0，前序《美丑》实际1保持，任务累计上限/实际均2。
exact preview、source/Registry bytes、egress、预算、durable intent和one-use permit实际重验。

| Item | Actual evidence |
| --- | --- |
| Attempt | `canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7` |
| Model / mode | `doubao-seedance-2-0-fast-260128` / `reference_to_video` |
| Request | 15秒、480p16:9、24fps、`generate_audio=true`、1张PNG |
| Request input SHA | `5b5a91a92b281fe3cd0b2b8eb3a9fbe2e6a1177f439d0ff3da2dedb8b63c5e2e` |
| Resolved SHA | `628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19` |
| Prompt SHA | `b2f7e2890c3bb023f8b19f7af62224e200121cb4a523e844343d740098cc856c` |
| POST | HTTP200；757282bytes；bodySHA`4cde6e04c5847829965039780c8e54217df3e693e2d054759538c99ea5ca585e` |
| Paid receipt | `production/state/paid-provider/submits/9cc4e4f43c705bb5365ab4913180f1012beec060a2052f7dc2922a56826efe51.json` |
| Paid receipt file SHA | `ed2f500fd2643c91da3e4476be29944846189787e6e776c025a60eef2295086b` |
| Raw MP4 | `production/state/video-generation/fetch/files/265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36.mp4` |
| MP4 identity | SHA`265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36`；5976142bytes |
| Probe | 15.104秒容器；361帧；864×496/24fps/H264；AAC32000Hz/stereo |
| Calls | 1物理POST；7成功状态GET；fetch前1重查GET；1媒体download；0生成重试/下一Shot |

两次poll helper缺少显式transport，均在本地抛错而未发网络请求。核对constructor后仅补现有transport注入，
同task继续查询；未重新POST。fetch成功后的helper JSON序列化错误从committer重开真实fetch receipt修复，
没有重复fetch。开发telemetry与Production权威状态分开，错误/消费历史不清零。

## Per-Shot Evidence And Gate

exact MP4落盘后首先显式project-local`video_analyze`，0.5秒间隔取31帧，不转写/下载Whisper。
抽查视点范围0–15秒，主角背部明确可见；抽帧不等于完整正常速度观看/听辨。
scene detector在threshold0.4报告1scene，不用它否定实际可见切镜或代签摄影要求。
修复下节调用路径后，normal`service.evaluate()`再次实际调用同MCP，保存0/5/10/15秒帧及原response。
第5/10秒本地证据足以反证literal POV；不把局部反证升级为全部运动/声音判定。

canonical分析`canonical-mcp-analysis.json`，source`generation-evaluation-source.json`，
diagnosis`generation-media-diagnosis.json`；experience pointer：
`production/state/video-generation/experience/00efcfc58d26514cc8eda1b22d2bf43be0f22332f189d8012e6f18c0f3c4c425.json`。
experience fileSHA`316642e05f6bf2a580b24221983f5d3a3410df65a4fe8158a579c817d66fa7e4`。

- `pov`、`identity_state_camera`、`source_fidelity`、`reasonable_coverage`：FAIL，均包含被实际局部反证的视点义务。
- `closeups`：PASS，仅证明大幅近景存在，不代签镜头合理性。
- `audio/sfx/no_music`、完整运动/障碍/跟随等其余10项：NOT_EVALUATED；音轨存在不证明已听或音画同步。

`canonical-gate-blocked.json`记录validate抛出`production_project_invalid`，非retryable且Manifest revision不变。
正常evaluate replay只重开已保存source/analysis，diagnosis相同、无新MCP/Provider调用或Manifest write。
这里保留待补证的validate状态，未调用terminal abandonment，未settle费用或签人类验收。

### Human Audio Confirmation

用户对exact诊断MP4完整声音核对回复“音效符合要求，无配乐或对白”。
`human-audio-confirmation.json`绑定同MP4 SHA/size、实际request item与回复，作为独立`HUMAN_AUDIO`证据。
它补齐声音反馈，不推出用户完整视觉认可；也不把真实human observation改称analyzer调用、覆盖旧source中的
NOT_EVALUATED或签Production/P6/Final Acceptance。已知POV失败和其余未完整运动取证保持。

## Shared MCP Invocation Repair

`ProjectAnalysisSession.__init__`原先把配置Python symlink`resolve(strict=True)`后作为executable调用。
配置venv能import`mcp`，真实resolved base Python不能；normal review因SDK缺失在MCP调用前失败。
修复先strict检查目标存在，再调用原配置路径的absolute形式；不安装SDK、不选新解释器、不fallback。
一个真实回归先红后绿，另一个保持missing executable拒绝；`test_generation_feedback_review.py`31项通过。
随后同bytes的真实MCP→evaluator→feedback与blocked validation/replay取证成功。

旧v2 source/authoring冻结21paths只有已发布spec/plan状态文字不同；本次新增共享QA调用修复在其外，
不能将旧工程receipt外推到这次代码或补签AC-2/AC-7。本次独立exact snapshot按policy验证。
Implementation Risk Gate：`KIMI_REVIEW_NOT_REQUIRED`，改变只保留已选executable路径；无新增secret/network/
Production authority或state writer，strict missing检查、public invocation seam回归与实际MCP都已验证。
concept审查不冒充code review，补充protocol失败也不构成已通过的required review。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mecha-provider-result | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/canvas-mecha-seedance480-20261011-001/fetch-result.json |
| mecha-pov-gate | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | ANALYZER | FAIL | POV_NOT_SATISFIED_WITH_EVIDENCE_GAPS | SAME_EVIDENCE_NEW_PROOF_LAYER | mecha-provider-result | runs/canvas-mecha-seedance480-20261011-001/generation-evaluation-source.json |
| mecha-human-audio | provider-request:628e66a4f86191ff5f1a46d0490e9ae3e2f70a94a3de7c61b8dae0f57ababa19 | canvas-mecha-ant-unit-20261011 | canvas-a69856aa5c2b934893fe53a1a5f28cbf94be0fc7 | N/A | 265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36 | HUMAN_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | mecha-provider-result | runs/canvas-mecha-seedance480-20261011-001/human-audio-confirmation.json |

同一attempt只有一个独立单元；31帧、四个失败requirement、两次MCP及两层proof不增加独立实验数。

## Remaining Work And Record Outcome

当前先`EVIDENCE_REPAIR_FIRST`：声音已获上述human确认，完整运动及formal选定QA proof仍须各自取证。
保留已知POV失败，缺连续运动证据不靠重复生成补齐。下一次repair需要明确不同的视点表达变量，
按同Shot历史、原recovery/planning和新的有限paid单元执行，不另开目录清零，不改成第三人称求PASS。
最终还需真正holdout短剧情单元、canonical原声composition/HyperFrames和用户完整听看认可。
当前媒体可用于失败诊断，不能以candidate/preview名称结束作品目标或签AC-7。

使用`record-ai-video-session`记录真实稳定阻断和共享修复，并对工程/Beauty记录作直接supersession。
`distill-ai-video-learning`评估`no_candidate`：一次机甲POV失败与Beauty输入拒绝涉及不同model、素材及
观察层，未隔离共同变量；SDK调用回归没有第二独立实验或controlled multi-arm，不制造通用学习规则。
record不改Skill/Policy/Gate，不重建RAG，也不为记录增加Provider/media或额外测试。
本次publication及verification以`.agent/harness/runs/reusable-canvas-production-20261011-mecha/receipt.json`
和实际main SHA为准；原11-check/1475-test receipt只保留原snapshot证明范围。
