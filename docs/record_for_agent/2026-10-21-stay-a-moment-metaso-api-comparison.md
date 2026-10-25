---
record_kind: provider_comparison
topic_id: director-natural-performance
learning_eligibility: eligible
evidence_index_version: "1"
---

# Stay A Moment — METASO API Comparison

Date: 2026-10-21

## Outcome

按用户“你调用api再看看呢METASO /home/reggie/vscode_folder/AI-VIDEO/.env”，实际完成一次远端 `METASO / MiniMax-H3` 首帧生成。可直接观看 `runs/director-stay-metaso-20261021-001/stay-a-moment-metaso-8s.mp4`；它是 canonical fetched MP4 的逐字节副本，无剪辑、增益或配乐。SHA-256 `0fd4865747a9f65c10f88f452588b5d83bbb3772c0135469093b498c6e8b48e2`，6,631,508 bytes，1344×768、24fps、192帧、8.000秒，H264 High，AAC stereo 32kHz。

男子转向门口、离开再返回坐下的动作比[本地版](2026-10-21-stay-a-moment-local-acting-trial.md)完整。独立读图者能读成“原本准备离开的人接受挽留”；这是一项有边界的叙事可读性观察。自然表演、观看吸引力和完整声画尚无本片用户验收，不能宣布 API 更好或导演升级成功。

声音没有声学改善：全片解码成功，平均 `−57.2 dBFS`、峰值 `−35.0 dBFS`，低于本地版 `−49.1 / −28.7 dBFS`。这些数字不证明音义或实际可听度。当前 Agent host 无 audio input 支持，未假装听过原声；已请求用户正常速度听看 exact 原片，尚待反馈。没有再次放大噪声或调用付费识音。

## Comparison And Actual Images

沿用同一首帧 PNG，SHA `c8d593f77dbdec2e36f080420f59548dbde89062b9e95e9ec6a4510072d2b07c`。保持人物、场景、8秒目标、“离开—让出身旁位置—看见邀请—返回坐下”、克制表演及生活声目标；无新图片、白模或动作参考生成。

这不是严格 A/B。远端改用 `metaso-h3-fl2va-v1` / remote prose compiler，名义8秒、adaptive几何；API不提供可控seed，backend版本、量化和采样参数未知，Context IR开启。为适配现有5000字符上限，去除本地输入中重复的开闭状态、行为和三阶段表演描述，保留两个角色的动机、行为、视线、因果与声画要求；最终 native prompt 为3999字符。原/适配 authoring 和各次无副作用编译结果保留，不把“同一创作目标”冒充“同一输入”。实际返回几何/FPS恰与本地相同，也不消除其他混杂。

显式 project-local `video_analyze` 提取20帧，间隔0.4秒，检测到一个场景；关闭转写和远端识音。原始response、逐帧JPEG、联系表、完整解码与声学事实分别在 run 的 `video-analysis-response.json`、`review/` 中。

| Time | Sampled observation |
| --- | --- |
| 0–1.2s | 两人保持原位置，女子先准备撑手挪位。 |
| 1.6–2.8s | 男子转身面向门口并移动；女子左移，右侧空位出现，并朝他伸手/看去。 |
| 3.2–4.8s | 男子停下、转回走向沙发；女子抬头关注他。 |
| 5.2–6.4s | 男子转身落座，接近女子。 |
| 6.8–7.6s | 两人并肩、目光向下，未见强笑或产品摆拍；画面有轻微重构图，未完全遵守locked camera。 |

Parent区分了两个结论：相较本地版，“离开再回来”的动作存在；原要求中的严格先后仍未完全执行，女子较早开始挪位，不能把顺序目标判成全PASS。独立者无需作者解释便能读到接受挽留，说明不能仅因起动时机偏差就断言观众完全读不懂。人物反应与结尾情绪是否自然、有效仍需完整原速观看。

## Independent Review

`reviewer_high` `/root/stay_media_review` 先看实际采样和用户目标，没有先读本轮作者解释或原生Prompt。检查全部联系表、8张单帧，并校验20张JPEG与MCP response一致。

- `METASO-01`（non_blocking）：动作可读成接受挽留，冷窗暖灯与构图有吸引力；结尾她的情绪变化仍含蓄，须原速盲看。Parent保留此正向观察与限制，不扩大成表演验收。
- `METASO-02`（blocking_candidate）：声音目标缺实际听音。Parent `CONFIRMED`，声音语义、可感知度及同步保持 `NOT_EVALUATED`；不能据AAC或分贝判PASS。

Reviewer及Parent都只查看采样和技术证据，没有连续1x视听能力证据，不冒充human验收。Agent-side `media-gate.json` 为STOP，无下一Shot授权。

## Execution And Recovery Boundary

新任务授权限定一次视频提交、零自动重抽，不含新付费音频理解。实际只有一次POST，返回已接受并最终成功；既有护腰贴任务的三次remote消费没有重置或借用。内部 operator upper bound沿既有配置封存为本次单次/总上限，不是价格或实际账单；paid state仍为accepted，未编造费用结算。

原项目含P7生成图，直接复制Registry到新bootstrap被标准reader拒绝；失败bundle留在 `production/`，没有Provider效果。尝试修订原项目时因其fetched/VALIDATE未闭合而在写入前被拒；原Manifest没有新增该修订attempt，没有修改本地失败状态。最终通过现有 `prepare_canvas_png_assets` 导入exact既有PNG，明确标为本地素材导入，不伪称新P7生成或平台采用；来源project/Registry/原asset记录留在 `reference-import-source.json`。有效新Production root为 `production-reference-import/`，仍使用canonical Planner/Router/compiler、feedback execution binding、预算预留、durable intent、one-use permit及 `VideoGenerationService`。

首次fetch被本机Fake-IP DNS阻断：`files.metaso.cn`解析到`198.18.4.68`。这不是已确认的HTTP重定向。通过现有transport的injected resolver，仅为该host查询公网A记录，再由原下载器验证公网地址、pin连接和TLS，继续禁止redirect。随后仅重试同一已知成功任务的下载，未重试生成；sanitized DNS证据在 `download-public-dns.json`。没有修改全局DNS或源码。

视频停在fetched/VALIDATE，未activation、qualification、P6、Final Acceptance或发布。凭据只由用户指定文件的exact `METASO_API_KEY` supplier在内存读取，未输出、shell source或持久化secret；没有调用其他Provider。其他窗口dirty/index工作保持不动。

## Evidence Index

本轮独立实验单位为一次远端submit；同一视频的执行、抽帧和审片不重复计数。与本地版保持首帧与目标，但未隔离制作路线变量，不能登记为受控多臂实验。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| metaso-execution | metaso:stay-metaso-01:d3baa331674199292ed9d6d494e6d68770609876537f230c39fed10382279b2e | stay-metaso-20261021 | stay-metaso-01 | N/A | 0fd4865747a9f65c10f88f452588b5d83bbb3772c0135469093b498c6e8b48e2 | PROVIDER_EXECUTION | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-stay-metaso-20261021-001/fetch-receipt.json |
| metaso-action | metaso:stay-metaso-01:d3baa331674199292ed9d6d494e6d68770609876537f230c39fed10382279b2e | stay-metaso-20261021 | stay-metaso-01 | N/A | 0fd4865747a9f65c10f88f452588b5d83bbb3772c0135469093b498c6e8b48e2 | EXPLICIT_EVALUATOR_SAMPLED_FRAMES | FAIL | RESPONSE_ORDER_NOT_FULLY_EXECUTED | SAME_EVIDENCE_NEW_PROOF_LAYER | metaso-execution | runs/director-stay-metaso-20261021-001/media-gate.json |
| metaso-sound | metaso:stay-metaso-01:d3baa331674199292ed9d6d494e6d68770609876537f230c39fed10382279b2e | stay-metaso-20261021 | stay-metaso-01 | N/A | 0fd4865747a9f65c10f88f452588b5d83bbb3772c0135469093b498c6e8b48e2 | ACOUSTIC_FACTS_WITHOUT_LISTENING | NOT_EVALUATED | MISSING_LISTENING_EVIDENCE | SAME_EVIDENCE_NEW_PROOF_LAYER | metaso-execution | runs/director-stay-metaso-20261021-001/review/decode-and-acoustic-facts.json |

## Learning And Next Boundary

自动评估 `distill-ai-video-learning`：`no_candidate`。一个本地与一个remote输出存在prompt、Context IR及未知执行栈混杂，观看吸引力和本片声音缺用户结论；不足以形成“API优于本地”或普遍导演规则，也不把同一声源的增益诊断当重复实验。没有修改Skill、Policy、Gate或共享代码。

最小下一步是先正常速度完整听看本片，确认接受挽留是否自然、原声是否可用；不要再次生成来补听音证据。若原声依旧不可用，应保留可用画面，评估独立生活声制作及现有P4混音路线。若人物戏仍不吸引人，应验证更明确的表演参考或另一个具有不同表达机制的方案，而非无限重抽相同动作。当前没有证明可持续生产同等质量片段。

按当前 `AGENTS.md` 的视频制作“先交片审片，效果认可后完整工程验证再commit/push”顺序，先保留本地记录与媒体供审片；不为这次看片运行完整工程套件，不以工程receipt冒充作品验收。未发布。
