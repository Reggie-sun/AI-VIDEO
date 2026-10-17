---
record_kind: media_experiment
topic_id: generic-h3-reference-control
learning_eligibility: eligible
evidence_index_version: "1"
---

# Generic H3 Robot Reference Pilot

Date: 2026-10-17

## Current Result

用户对[实际输入准备](2026-10-17-reference-control-audit-and-preview.md)推荐的最小单元回复“确认”：
仅执行几何人物 `robot-reference`，官方 MiniMax H3 Max CN，5秒、768P、16:9、balanced，
最多1次视频POST、零重抽，无新图片或音频调用。实际只POST1次且HTTP200；任务succeeded并已fetch。
新单元内部总上界与单次上界均50,000,000 CNY microunits，仅为operator拒绝越界上限，不是价格或账单。
其余三条候选路线未提交，也未继续《界蚀》失败镜。

当前逐项裁决为 **0 PASS / 2 FAIL / 5 NOT_EVALUATED**。
`arm` 与 `turn` 的3.5秒时序要求有明确反例；其余五项保留抽帧/技术观察，但缺所选measurement要求的
完整正常速度观看，不能把局部相似或技术解码成功签为整项PASS。0 PASS不表示这五项均有可见失败。
canonical `abandon_video_generation` 已关闭此候选；标准loader重开Project1/Manifest14，attempt为
`failed`、phase为`validate`，candidate video asset IDs为空。没有activation、accepted state或最终交付。

本次真实单镜未通过，不能证明通用模型质量、跨场景迁移、连续镜、完整故事或human验收。
本单元1/1已消费，后续真实生成需要另有当前有效的有限授权；本记录、代码PASS或Key存在均不授权重试。

## Exact Identity And Input

证据根：`runs/generic-control-real-media-20261017-001/live-robot-r2v-001/`。
Project root：`runs/generic-control-real-media-20261017-001/candidates/robot-reference/production/`。
非Q0独立身份固定为 `canvas:generic-robot-reference:canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda`，
对应本Project、本attempt及本次`robot-reference-r2v` arm；多层证明只算一个独立尝试。

| Concern | Exact anchor |
| --- | --- |
| Attempt | `canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda` |
| Approved proposal SHA | `3713c0346bff23b3df52e653876bf7658e32f508e1938ec6bcc267c4da607a8e` |
| Native body SHA / bytes | `f8aa4be075b301046ad4e6afb8525de73491495f6a1364fc00726454f3f15519` / 1,055,134 |
| Resolved generation hash | `bb8a457b14be0825dd1e1a621b857fc4ff4945634a249359370b3a55ddad4132` |
| Paid submit receipt fingerprint | `5acc1ca174e3deacbc2e193c116cb1be4b99ebb59d72d889880f28b976f5c151` |
| Submission fingerprint | `4178a601eb0449a86cef305ed979bc5dcce3e14b8dd939a69928b5705650f0f6` |
| Selected QA content hash | `eb0fc3e471ce3a7def4c5ebe7e7c8b1aee1108b88c54dd5bc1b22881ef154a56` |
| Exact MP4 SHA / bytes | `0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9` / 1,734,383 |

同一共享数据入口、Planner/Router、实际compiler、paid guard、一用permit和committer执行；
未建立故事专属executor、第二timeline或状态库。native `model=MiniMax-H3-Max`、`duration=5`、
`resolution=768P`、`ratio=16:9`、`extra.prompt_expansion_mode=balanced`，API origin为`https://api.minimax.cn`。
`content[0]`为原封存text；`content[1]`一份PNG `reference_image`，SHA
`dea3ad07b19df83ab99779f6f061a0bff76b4e85f0d460a6f8e0db5aad05dd05`，负责外观/开场；
`content[2]`一份MP4 `reference_video`，SHA
`6d4fcd90b3069b799b351907efdf56810c28d3939986365e7d7865247403fe19`，负责动作、时序及固定全身摄影。
没有重复图片冒充独立人物参考；这是reference route，未发送`first_frame`，开场及动作均属模型引导。

本Project是独立通用样例的第一个获授权单元；旧《界蚀》的计数、消费、STOP和ledger保留在原Project，
未搬运、复用或清零。执行后核对旧`production/state/manifest.json` SHA仍为
`1ece69263041eb06d345e5673f010a2b209e67a1e2fea82c2002e12a2b982e60`，与授权前一致。
新单元仅1次POST，不据此推算整个账户账单或所有项目的累计调用数。

## Media Measurement And Findings

MP4位于本Project的
`state/video-generation/fetch/files/0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9.mp4`。
实际1344×768，**7:4**，不是精确16:9；24fps、124帧，video5.166667秒、container5.184秒，AAC32000Hz双声道。
qualified FFmpeg全视频解码exit0无error；完整PTS为0–5.125秒，最大间隔0.041667秒。
原采用窗仍0–5秒，最后采用frame119约4.958秒；frame120及后续额外尾部不替代原切点。
这些技术测量不证明声音语义、正常速度观感或可用质量。

Parent显式调用project-local `video_analyze`，`frame_interval=0.25`、21张0–5秒抽帧、单scene，
`transcribe_audio=false`、`understand_audio=false`；另看原分辨率关键帧及生成/白模frame119。
随后通过实际初始化的同一project-local stdio MCP session、`ControlledPresentationVerifier`、
canonical analyzer六项及technical一项分两次记录，第二次为同字节`repair_evidence=True`。
原生`ProjectAnalysisSession`的默认稀疏参数没有被宣称已自动补齐；本次由trusted operator显式配置dense调用。
没有伪造human authority、调用新音频模型或复用已消费audio unit。

| Requirement | Verdict | Evidence and limit |
| --- | --- | --- |
| appearance | NOT_EVALUATED | 21帧均见单白色几何人物，无采样可见额外人物/肢体；缺完整正常速度观看。 |
| arm | FAIL | 3.5秒/frame84仍低于肩水平，3.75秒仍在抬，约4秒/frame96才水平，错过3.5秒deadline。 |
| camera | NOT_EVALUATED | 抽帧见全身/地面/留边，单scene；不把抽帧或scene detector升为全段摄影PASS。 |
| duration | NOT_EVALUATED | nominal5、完整解码和PTS已核实；所选“可用连续画面”及完整正常速度观看尚未证明，保留整项NE。 |
| hold | NOT_EVALUATED | 0–2秒每0.25秒均见双臂垂下；缺所选全段正常速度观察。 |
| opening | NOT_EVALUATED | 静态外观/站姿/地面基本相似，构图端点未锁定且实际比例7:4；不以相似签整项PASS。 |
| turn | FAIL | 3.5–4秒仍抬臂，已违反3.5–5秒保持侧平举；后段转向大体正确，不无据判方向或精确末态角度失败。 |

`exact-media-observations.json`保留完整逐项依据，`explicit-exact-mcp.json`保留显式原回应；
`canonical-analyzer-mcp.json` / `canonical-technical-mcp.json`及受控presentation、diagnosis保留实际接线。
`canonical-closure.json`绑定Manifest14、FAIL/NE和rejection，content hash为
`9fab3bc612063d302d6d40c888d2ebbd8540cefc1fbe8c94fb9654b208469f4f`。
同字节dense分析、关键/采用帧和完整技术解码已做；无法制造缺失的正常速度human证据，额外稀疏分析不能修复已知失败，
故有据abandon并保留五项unresolved requirements。没有把正常速度看过、声音通过或通用能力成立写成事实。

## Shared Download Recovery

首次fetch在建立HTTP连接前被既有公网校验拒绝：系统DNS返回代理fake-IP `198.18.0.24`。
不是已观察到redirect；错误文案同时覆盖多种下载安全失败，不能仅凭文案判断根因。
现有物理网卡`enp132s0`的`systemd-resolved`查询返回真实公网地址；本机controller401后停止该路线，
没有读取代理secret、改系统DNS/代理规则、关闭TLS或接受fake/private IP。

源码`51228c4421d918dd40e994842fafeed98f52b3f7`在既有`vidu_download`增加可选
`download_resolver`，由继承的H3 transport显式转发；全部结果仍重验public/family/TCP/443，
数值地址固定连接，原hostname证书/SNI、无凭据GET和无redirect不变。默认系统DNS行为保留，没有自动fallback。
operator仅对当前结果hostname注入现有网卡解析，并沿原canonical fetch恢复**同一task**；没有第二次POST。
`download-dns-resolution.json`、原失败及恢复后的fetch receipt保留；签名URL仅在内存，未保存key/header/raw Provider response。
使用边界写回既有[Provider文档](../minimax-h3-max-provider.md)，不是新的媒体质量规则。

## Engineering Verification And Publication

TDD先复现不接受resolver参数，再实现；Parent增补畸形记录/端口/协议及错误信息不泄露的失败用例，
三个focused suites共166项PASS。exact commit-range Harness：
`.agent/harness/runs/public-video-download-resolver-20261017-r1/receipt.json`，9项全PASS，
Provider976、Vidu204、neutral requirement450项PASS，Architecture0 error/0 warning。
源码发布前receipt核验integrity/freshness/complete_completion_proof及snapshot/workspace均true；
已push origin/main并核验远端为`51228c4421d918dd40e994842fafeed98f52b3f7`。

Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`：显式trusted resolver没有授予新的凭据、预算、权限或lifecycle，
既有地址/TLS/隔离边界和新增normal/boundary/failure测试闭合，真实同task fetch成功；
没有识别到剩余关键越权/泄密/难恢复状态损坏路径或重大未验运行语义。Parent完成自审；writer不是独立最终reviewer。
本记录与上一准备记录的supersession notice只按owned paths独立验证/提交；保留全部foreign staged/dirty内容。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robot-r2v-fetch | canvas:generic-robot-reference:canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | generic-reference-control-20261017 | canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | robot-reference-r2v | 0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9 | PROVIDER_SUBMIT_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/generic-control-real-media-20261017-001/live-robot-r2v-001/fetch-recovered-result.json |
| robot-r2v-analyzer | canvas:generic-robot-reference:canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | generic-reference-control-20261017 | canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | robot-reference-r2v | 0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9 | ANALYZER | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | robot-r2v-fetch | runs/generic-control-real-media-20261017-001/live-robot-r2v-001/canonical-analyzer-diagnosis.json |
| robot-r2v-technical | canvas:generic-robot-reference:canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | generic-reference-control-20261017 | canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | robot-reference-r2v | 0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9 | TECHNICAL | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | robot-r2v-fetch | runs/generic-control-real-media-20261017-001/live-robot-r2v-001/canonical-technical-diagnosis.json |
| robot-r2v-human | canvas:generic-robot-reference:canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | generic-reference-control-20261017 | canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda | robot-reference-r2v | 0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9 | HUMAN | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | robot-r2v-fetch | runs/generic-control-real-media-20261017-001/live-robot-r2v-001/canonical-closure.json |

## Research Clarification

用户追问官方/社区是否已有答案后，补核官方full-reference rewrite指南、CN API扩写选项与第一手社区报告，
结论和链接写入原[研究owner](../research/2026-10-17-h3-action-timing-reflection-repair.md#generic-reference-timing-follow-up)。
已有职责组织、时长/FPS对齐及保留关系表达方法；同类动作延迟也已有本地H3用户报告。
本次白模已满足5秒/24fps，不能把重复该配置或机械切换video editing/扩写模式当成经验证修复。
官方rewrite格式不等同原始API强制格式，意图保留标记不等同硬控制；尚未找到当前H3 Max CN
精确动作deadline的可复核稳定修复证据。先应用适用资料并离线核对，真实验证只回答剩余具体问题。
本次只有文档资料GET，无新增Provider/media/凭据操作或Production状态变更；原独立尝试仍只计一个。

## Automatic Learning Evaluation

`record-ai-video-session`完成当前真实尝试与旧准备状态对账后，实际评估`distill-ai-video-learning`：
结果`no_candidate`，不创建placeholder，不修改Skill/Policy/Gate或标ADOPTED。
本样例只有一个新H3 Max CN R2V尝试，没有受控多臂、重复或经验证改善；不能从时序漂移归因于参考模式、
prompt expansion、长度、参考职责或Provider的一项因素，也不能声称某个修法通用有效。
已检索当前experience并重开相关原记录及现有H3 claims；旧本地H3 fl2va的首帧/可见context claims
不覆盖官方H3 Max remote reference route，本次没有material update。
旧Seedance Mini对白模迁移的局部PASS记录也不能变成本模型对照或证明所有模型都不能使用白模；
《界蚀》的不同人/空间/素材及旧时序失败没有控制混杂，不能拼成本修法的独立有效性证明。
本次只保留有界反例；逐目标输入解释、工程准入与实际模型效果、单镜与通用质量继续分开。
