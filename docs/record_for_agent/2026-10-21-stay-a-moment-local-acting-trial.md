---
record_kind: media_experiment
topic_id: director-natural-performance
learning_eligibility: eligible
evidence_index_version: "1"
---

# Stay A Moment — Local Acting Trial

Date: 2026-10-21

## Outcome

本轮实际生成了《再坐一会儿》8秒原生视频。用户观看后的原话是：**“自然到是还好,但是没有声音,然后你是用本地h3做的?”**。自然度获得有限的正向反馈，不能继续把“仍然生硬”当作已确认结论；声音没有形成可听体验。人物关系表达、观看吸引力和完整声画成片尚未获认可，不能宣布导演升级成功或可以稳定批量制作。

可观看原片：`runs/director-stay-a-moment-20261021-001/stay-a-moment-8s.mp4`。这是原生输出的逐字节副本，未加速、重剪或另配声音。SHA-256：`d57c6ef7b06d42876e743a84264e11283c863a076fbb13e02012e41c9ede75eb`。

本记录不撤销护腰贴旧8秒片“动作能读懂，但仍像摆拍或缺少吸引力”的反馈。新片更换了故事、首帧和制作路线，不是隔离导演变量的同条件 A/B。

## Creative Choice And Actual Route

阅读当前 Director、Creative Completion Practice、[Capability Study](2026-10-21-director-capability-study.md)、[现有素材复核](2026-10-21-director-feasibility-shot-check.md)及本地模型记录后，选择不含商品的私人场景：男子准备离开，女子挪出身旁的位置，他看见后决定留下。希望由距离、视线和选择传达关系，保留普通速度、固定双人中景及短暂停留，不要求微笑或配乐。

已有虚构人物/房间原图仅用于身份和环境参考，不直接当新场景首帧。没有白模：本镜空间可在实际开场图中检查，主要未知是表演，白模不能证明真人反应自然。概念阶段的独立意见要求先看见离开、再看见邀请，不能靠导演解释补出反应。

实际全部使用本地 loopback ComfyUI，没有外部生图、外部视频生成或付费音频分析：

| Stage | Actual execution |
| --- | --- |
| 首帧 | `p7_1_flux2_klein_4b.json`，本地 FLUX.2 Klein 4B，1344×768，4步；两次输出 |
| 视频 | `minimax_h3_fl2va_quality.json`，本地 native H3 I2V，192帧/24fps/8秒，1344×768，20步，单首帧，无尾帧/动作视频 |
| 原生声音 | AAC stereo 32kHz；未使用 P4 替换音轨 |

首张图多出一位女性，拒绝用于视频；第二张保留一男一女、女子在沙发右端、男子靠近右侧门口。修图同时改变了文字与 seed，不能证明重复参考或任何单一措辞就是重复人物的根因。对应图片 SHA 分别为 `ace6c19a6d13e3ba81ea9c90b2e0b409dc275c4191e7e8496cf41605af554a8a`、`c8d593f77dbdec2e36f080420f59548dbde89062b9e95e9ec6a4510072d2b07c`。

选 native H3 是因为现有 profile 已支持192帧；没有为了8秒修改固定124帧的 T8 profile。模型/工作流及源码身份保存在 run 的 `production-source-snapshot.json`，实际 request、compiled prompt、preview 和执行 binding 均留在 run。

## Observed Film

显式调用 project-local `video_analyze`，取得20张每0.4秒的帧；另查看每0.25秒联系表及较大单帧。工具没有执行音频理解或转写。观察范围不能冒充连续1x观看与聆听。

| Time | Actual observation and implication |
| --- | --- |
| 0–1.6s | 女子开始撑手挪位；男子没有先明确朝右侧门口离开。原设计的触发事件缺失。 |
| 1.6–4s | 女子继续左移，男子跟向左侧；约3秒后她抬头看他，但未清楚呈现他读到邀请后改变主意。 |
| 4–6s | 男子弯腰坐下。动作结果可读，不能据此推断人物选择已被表现。 |
| 6–8s | 两人并肩，女子低头、男子看前方。距离缩短成立，情绪落点与观看吸引力仍需实际观众判断。 |

采样中保留了蓝窗/暖灯的光线层次、同一房间和两个人；没有持续微笑或刻意展示商品。这些是可见事实，不等于自然表演或专业影视观感已整体通过。

独立 `reviewer_high` `/root/stay_media_review` 先看实际媒体及用户目标，未先读作者情节解释。它指出：距离变化可读，但接受陪伴与安排座位仍难区分；1–6秒主要用于挪位、站位调整和坐下。它只查看联系表与八张较大帧，明确没有完成完整1x听看。Parent 保留其叙事风险判断，不把采样中的节奏推测升级为“表演生硬”的事实；用户随后对自然度的正向反馈优先保留。

## Sound Finding And Bounded Diagnostic

完整声画解码退出0；原音轨平均 `−49.1 dBFS`、峰值 `−28.7 dBFS`。用户报告“没有声音”，因此声音项为 **FAIL**，不是因为有 AAC 就 PASS。测量提示电平很低，但不能单凭数字判定音轨语义或播放器设置。

当前会话的 `filesystem.read_media_file` 实际返回 `audio content omitted because you do not support audio input`。未绕过输入限制、调用付费识音或把声学统计当成听音。

保留原 MP4，另制作同一原声的 **audio-only +20dB 试听**：`review/native-audio-plus20dB-listen.wav`，SHA `bdae0ce64d750b1f15f8c49b1f27c481a67f79588f6fb763a75dcddd21756af0`，实测平均 `−29.1 dBFS`、峰值 `−8.7 dBFS`。用户试听后明确反馈 **“噪声更多”**，见 `review/user-feedback-audio-diagnostic.json`。因此这条原声不适合作为当前片段的声音，继续放大不能补出可用的环境/动作内容。这只评价本次输出，不外推所有 H3 原声。诊断没有新增音效或完成视频混音，原 MP4 的声音问题没有被修复。

现有 `register_generated_video_audio` 的来源检查要求 remote/metered 的 fetched evidence；当前 development repair-input 也明确不接收 local fetch。不得把本地原声伪装成远端生成、普通独立录音或已验收素材，也不得为嵌回声音 direct mux 或手造 timeline。本轮没有为此修改代码、Policy 或 Gate；若继续做完整声音修复，先由现有 P4 owner 确定有据可用的路径，保留这项实际接入限制。

## Attribution And Next Small Test

**导演/参考选择也有责任。** 放行的首帧中男子仍面朝女子，画面容易暗示“他在等位置”。导演寄望模型随后自行补出离开意图，未取得相称的制作可行性证据。画面漂亮、没有商品和没有笑，并不自动形成有吸引力的人物戏。

**存在明确执行偏差。** 原生 Prompt 确实保留了“转向出口、开始离开、看见新座位、再决定返回”，输出缺少这条链。不能归因为 Compiler 把动作删掉；也不能用一次结果断言所有 H3、I2V 或单镜头都做不到。

**目前不需要再次生成画面来处理声音。** 用户认为自然度还好，但已否定放大后原声的可用性。保留画面，下一步应单独制作房间环境、脚步以及挪位/坐下时的布料和坐垫声，再经相称的 P4 路径合成、原速复核。没有把提高响度当成修复，也没有用配乐覆盖噪声后声称声音完成。

若继续验证原导演命题，先取一段正常速度、真正包含“察觉邀请才改变行动”的表演参考，验证关系本身能否独立读懂，再选择能保留其表演时机的制作路线。若只修改首帧朝向或再次抽样，仍不能假定情绪层次会随动作补齐。本轮不再无限微调同一 Prompt。

## Execution And State Boundary

真实 ComfyUI 调用共两次图像生成、一次视频生成。视频 prompt ID `12ea2097-fab2-4e7e-bfdd-fa06b7db1f65`，执行约11分32秒。此前 `stay-video-01` 因任务脚本图像 resolver 的参数绑定错误，在上传/permit消费/prompt effect之前失败；经明确调用路径证明、唯一 committer 和一次性 runtime-repair grant 恢复。`stay-video-02` 因计数投影不一致在 submit intent 前被拒并正式关闭；未用 advisory hash 重置消费。`stay-video-03` 保留旧计数、原 Prompt/seed/profile/QA 后完成唯一实际视频生成。诊断与恢复证据均在 run，未手改 Manifest 或重复消费旧 permit。

`runtime-repair2-video-fetched.json`、`runtime-repair2-video-fetch-receipt.json`、`review/video-analysis-response.json`、`review/decode-and-acoustic-facts.json`、`review/user-feedback.json`、`review/audio-diagnostic.json`、`review/user-feedback-audio-diagnostic.json`、`media-gate.json` 保存当前证据。`media-gate.json` 为 Agent-side STOP，不冒充 Production QA receipt；本 run 的视频仍停在 fetched/VALIDATE，未激活、未提交后镜、未签 P6/Final Acceptance 或发布。

本轮启动的 supervisor unit `ai-video-comfyui-4b5b4f74841d4621ac343791bbe6fb1d.service` 已在确认 ownership 与空队列后停止，未终止其他 FFmpeg 工作。工作区存在其他窗口的源码、文档和 index 变化；本轮没有将其纳入提交，也不能以本实验声称 clean main 的完整可复现性。

## Evidence Index

非Q0 independence key 绑定本地 H3、该实际 attempt 及 sealed request input hash；同一视频的执行、采样和用户反馈是同一个实验单元，不按文档/帧数/审片人数重复计数。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stay-execution | local-h3:2868c4d5181b316791a84d735be4a432a66f530b9b82576dfbccffa6e2ce5b8c | stay-local-acting-20261021 | stay-video-03 | N/A | d57c6ef7b06d42876e743a84264e11283c863a076fbb13e02012e41c9ede75eb | PROVIDER_EXECUTION | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-stay-a-moment-20261021-001/runtime-repair2-video-fetch-receipt.json |
| stay-action | local-h3:2868c4d5181b316791a84d735be4a432a66f530b9b82576dfbccffa6e2ce5b8c | stay-local-acting-20261021 | stay-video-03 | N/A | d57c6ef7b06d42876e743a84264e11283c863a076fbb13e02012e41c9ede75eb | EXPLICIT_EVALUATOR_SAMPLED_FRAMES | FAIL | MISSING_DEPARTURE_AND_DECISION | SAME_EVIDENCE_NEW_PROOF_LAYER | stay-execution | runs/director-stay-a-moment-20261021-001/media-gate.json |
| stay-user-naturalness | local-h3:2868c4d5181b316791a84d735be4a432a66f530b9b82576dfbccffa6e2ce5b8c | stay-local-acting-20261021 | stay-video-03 | N/A | d57c6ef7b06d42876e743a84264e11283c863a076fbb13e02012e41c9ede75eb | USER_NATURALNESS_IMPRESSION_ONLY | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | stay-execution | runs/director-stay-a-moment-20261021-001/review/user-feedback.json |
| stay-user-sound | local-h3:2868c4d5181b316791a84d735be4a432a66f530b9b82576dfbccffa6e2ce5b8c | stay-local-acting-20261021 | stay-video-03 | N/A | d57c6ef7b06d42876e743a84264e11283c863a076fbb13e02012e41c9ede75eb | USER_AUDIBILITY_REPORT | FAIL | NO_AUDIBLE_SOUND | SAME_EVIDENCE_NEW_PROOF_LAYER | stay-execution | runs/director-stay-a-moment-20261021-001/review/user-feedback.json |

## Verification And Learning Boundary

实际验证包括本地生成、标准 Production loader 重开、Director coverage/goal binding 校验、显式 MCP 抽帧、完整解码、声学电平测量、独立采样审片和用户反馈。没有用代码测试、reviewer 意见或工程 receipt 证明作品成功。

自动评估 `distill-ai-video-learning`：**no_candidate**。只有一个实际视频实验，图片变体有混杂变量；没有隔离导演变量的受控比较或足够独立重复支撑新通用导演规则，原声增益试听也是同一声源的诊断。没有创建学习占位文档或修改 Skill。Agent Memory 后续检索报告 shard incompatible 并排队刷新，未等待/重建索引，也未将 RAG 当证据。

唯一跟踪改动是本记录；媒体和任务脚本保留在 ignored run，未作为 Production release 发布。最终文档验证与提交身份由对应 exact-range Harness receipt、Git 及交付说明给出。
