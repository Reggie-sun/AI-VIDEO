# Hotpatch Dayoff Editing Preview Record

Date: 2026-10-20

## Directed Redo Checkpoint — 2026-10-21

用户对“剩余两次分别重做6秒腾座开场、8秒商品互动；总提交仍不超过3次、零自动重抽、原声MUTE/P4、最后一次Gemini留给整片”的具体问题回答“允许按此方案重做”。授权与前序消费封存在 task `redo-authorization-20261021.json`；它不是新增额度。以下旧段落的一次视频消费与待授权描述均为历史状态。

实际执行第二次 METASO / `MiniMax-H3` 提交，attempt `canvas-65eb4dda1ce1b7f168e1ad7fe5b82e4b2a45acb2`。新原创双人参考图 SHA `6f75d09150ce708891476d9a4045b78078afabc09f402f0cc3195410b254332d`，新6秒动作白模 SHA `e9a73a8a0e87389171a40513d559465d3382b915ad94b66ec948f81094ee6e97`；均实际检查，明确各自只负责身份/场景或粗略动作空间，不证明真实动作完成。新 Shot `S01R`、QA revision 2 和原声明确 MUTE 由原 authoring/committer owner 接入同一 Production root，旧 S01 的 KEEP sound FAIL、消费与 immutable QA 均保留。

exact native body SHA `1716e6df49c788e15e1002250f306adfe292a35484324d7244d68fc60a630b57`，8,544,757 bytes，参数6秒、768P、9:16、context IR enabled。HTTP 200 后 canonical poll 得到 succeeded；同一已接收结果的下载再次遇到 fake-IP DNS 拒绝，沿原 public-address pinning/TLS SNI/no-redirect downloader 注入当前 exact-host 公开解析后获取，未再 POST。一次 CLI 参数类型错误发生于 submit intent 前，无 POST；一次 fetch 返回后仅诊断 JSON 序列化失败，已从 Manifest 确认下载成功，没有重复 fetch 或提交。

新 raw MP4 为 `production/state/video-generation/fetch/files/db324a0e4f2f89702739208b085891de27631a1077e69428c01b063c83feaf63.mp4`，4,352,935 bytes，768×1344，158帧、24fps、6.583秒，含32kHz AAC。显式 project-local `video_analyze` 每0.5秒取得14帧，证据 `S01R-visual-mcp.json`。实际动作失败：0秒女子已经坐在无纸的左侧位置，0.5–1秒起身指向另一坐垫，5–6.5秒又坐回左侧；没有呈现同一座位受阻到腾空的因果。约3.5秒纸带出现明显断口，前景尾段留在地上，违反单条连续纸带要求。不能以人物、光线稳定抵消这些缺陷。

`S01R-canonical-diagnosis.json` 已经通过实际 MCP → selected evaluator → generation feedback owner 持久化：`QUALITY_FAILURE`，`action/performance/space-camera` FAIL，`identity/truth/sound-allocation` 保留，`all_required_observed_pass=false`。随后由 `reject_video_generation` 关闭本镜。声音 PASS 仅指明确MUTE/P4责任，未分析原生音轨、未声称替换音轨已完成。证据接入过程中先后因 legacy policy 与 `/2` evaluation 版本不匹配、`/1` 携带新版字段而在持久化前拒绝；改为该既有 unmarked QA 对应的 `/1` 后成功，未改变QA或减弱失败项，未调用额外Gemini。

独立 Native Codex 概念/媒体复核确认 CC-05、CC-06 均阻断：裁切、字幕、正常速度剪辑无法补出缺失的空间因果；遮掉地面会失去长纸与动作反馈，提前切走会丢失落座结果。Parent 不采用已知降质修复，不把本镜称为合格广告，不在当前失败镜后提交商品镜。原8秒商品计划另有 CC-03 衔接修正：若女子已坐，后镜不能让她重复坐下，男子持纸的去向须明确。

当前已消费2/3次视频提交、3/4次Gemini音频分析；两次视频结果均已知，未发出第3次提交，最后音频次数也未使用。完整成片仍未完成、未发布、无P6或Final Acceptance。已向用户提出将最后一次改为8秒“放下手机—接盒—伴侣落座”、真实商品画面收尾并退役纸卷剧情的范围调整，尚需实际答复；不能将 pending 问题当作同意或自动重抽。

本轮也重新打开三张原始商品图，纠正压缩上下文里文件名与内容的错配：`png_m_1a4…` 是橙盒包装，`jpeg_m_48ec…` 是贴片结构插画，`jpeg_m_f2e3…` 是实际使用示意。未据错误映射提交商品参考、建立新商品功效或输出商品镜头。后续必须以实际字节与画面为准。

## Supersession Notice — 2026-10-21

用户明确指出旧 3 秒预览“很奇怪”且没有声音，旧版本不能作为已满足节奏或审美的候选。后续仅制作正常速度的 2.25 秒局部动作/声音检查片段，未恢复整镜末尾对视，也未将它用作原完整 Shot 的替代。原完整目标与 sound FAIL 保留；完整成片、自然度与商业完成度仍未通过。

当前局部文件为 `runs/hotpatch-dayoff-20261020-001/natural-sound-render-v2/output/opening-natural-with-sound.mp4`，SHA `9fc167e0d6adb0ff61c96ccec35c2d3b7cad1f7fa96e91575c9ef47b97bbcd17`。实测 54 帧、24fps、768×1366、2.25 秒、AAC stereo 48kHz，HyperFrames lint/check 零错误。显式 MCP 视频检查取得五帧；完整音轨 Gemini 观察识别 paper rustling / pages turning，无可辨认语音。音乐轨已进入 P4 混音，但此次模型观察没有单独辨认音乐，不声称配乐听感通过或人工完整听看。

视频仍只提交一次；Gemini 已实际分析三次，剩余一次。第二次针对自制正弦拨弦/噪声混音，识别为高频吱响与擦拭声，被拒绝；第三次改用实际纸张录音及低音量钢琴，识别到纸张声。每次输入与结果保留，不重试旧 unit、不删除失败历史。

当前声音来源为 keweldog 的 [rustling paper.wav](https://freesound.org/people/keweldog/sounds/181774/) 与 Jadis0x 的 [Piano + Crystal Keys](https://freesound.org/people/Jadis0x/sounds/677275/)，两页当前均声明 CC0。下载公开 HQ MP3 preview，保留原文件及 SHA，以注入的 Jianji FFmpeg 转为完整 PCM WAV，再经 `AudioImportRequest`、committer、P4 tracks、同一 ResolvedTimeline 与 HyperFrames 混音；未绕过登录获取原下载、未 direct mux。声明、公开 URL、原/派生 SHA 见 task `input/licensed-audio/*.provenance.json`，完整录音不会作为本片原创录制署名。

## Replacement Audio Preview Capability

实际运行证实旧 `/2` admission、composition guard 与 resolved timeline 都禁止预览加入独立 P4 声音。为完成已授权的声音检查，增加有限、可复用的 `development-repair-input/6` / `replacement_audio_preview`，而非修改旧 `/2,/3` 或放宽 Production 资格。

新用途只支持正常速度：receipt 的 V1 map 必须逐点 identity，composition layer 不携带 retime map，仍精确绑定 Shot/role/window/transform/bytes；必须有登记的 BGM/SFX/ambience，拒绝对白、旁白、caption 和 voice source。resolver 输出单一 `development_audio_preview` 时间线，旧 activation owner 对所有非Production scope拒绝，captured-bytes fence 也拒绝把 scope 改成 Production 后的激活。原失败素材保持 UNBOUND/NOT_EVALUATED，不推进后镜 barrier。

TDD 先观察新 scope 被旧 admission 拒绝，再完成 bootstrap/strict reader/P4 registry import/resolve/relabel fence 的集成验证；旧 scopes 仍拒绝独立音轨，新 scope 拒绝 retime/native audio、缺轨与 speech。局部完整检查曾 42 passed；最终候选的实际 policy checks 以本次 fresh Harness receipt 为准。Parent Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：本次无新 Provider/凭据入口，无 Production activation 扩权；现有 mutation owner、原失败链与 activation/captured-bytes fence 保持，相关失败路径有 executable coverage。CodeGraph 查询报告 source changed during indexing，未将它当作当前结构证据；以源码和实际运行核对调用关系。

上述工程变更 commit `af77125a00512972874e985b453438ccfb699ddc` 的 exact range Harness 全部通过，receipt 为 `.agent/harness/runs/hotpatch-replacement-audio-20261021/receipt.json`；在匹配的已提交文件快照上 `make harness-receipt` 返回 `fresh=true` 与 `complete_completion_proof=true`。已 push `origin/main`，`git ls-remote` 核对同一SHA。后续本记录/README的诊断更新单独验证，不把工程测试证明当作媒体质量通过。

开发过程中一次音轨 import 将 recipe hash 误放入 `input_artifact_ids`，writer 已提交而 strict reader 随后拒绝未知引用。保留该开发 bundle 与失败证据，另建正常预览 bundle，使用空 dependency IDs、exact source fingerprint/provenance；未直接改 Manifest、未重置原 Production 消费。后续 audio import 成功、旧 preview 禁止音轨的已知失败均保留；新 scope 使用独立 capture，没有重解释旧 receipt。

## Purpose

记录《今天，腰先下班》首镜真实生成、声音失败及用户节奏反馈后的非生成剪辑预览。完整原创商业成片目标保留；未交付完整成片，也未把预览标为 Production 接受。

## Verified Media

任务目录 `runs/hotpatch-dayoff-20261020-001/`。输入、商品事实及 Director 覆盖见 [project README](../canvas-projects/hotpatch-dayoff/README.md)。竞品只用于本地风格分析，没有上传至视频 Provider。

用户先允许三个 5–8 秒镜头、零自动重抽及四次 Gemini 音频分析，后明确改用 METASO / `MiniMax-H3` 和指定私密文件。仅读取指定字段而不输出凭据。当前 METASO 实际提交一次，Gemini 实际分析一次；Seedance 和 MiniMax 官方接口均零提交。消费不因失败、预览或恢复重新计数。

首镜 attempt `canvas-45a6b2b6d8f31e425af27ec43909e11d008fda28`，exact MP4 SHA `2df69a622b9cf0e869e028b5cf4882ce5539915f22e6bb9b1bfc95904516a10f`。实测 4,825,867 bytes、768×1344、175 帧、24fps、含 AAC。`S01-canonical-diagnosis.json` 为五项画面 PASS、sound FAIL；Gemini exact observations 为 continuous rushing water / water splashing and spraying。Parent 没有声称亲自听音。原动作左右手与 source prose 的差异在评估中披露；不能从总体画面 PASS 推断提示词逐字服从。

下载首次被安全 downloader 拒绝，当前系统 DNS 将文件域名解析为 Mihomo fake-IP。对同一已接受结果使用当前 exact host 的公开 DNS 解析，经原 downloader 注入 resolver 后安全获取；TLS host、pinned-IP、安全地址与无重定向规则保留，没有重新提交。证据为 `download-DNS-selection.json` 和 `S01-fetch-public-DNS.json`。

## Editing Feedback And Output

用户指出慢动作感。原素材是正常 24fps，未后期降速；动作和对视到达得晚造成节奏松散，属于导演与剪辑问题。原 24 秒总长及 7 秒首镜是导演选择，不是用户固定要求。

经 committer 的 `reject_video_generation` 明确关闭原失败，再经独立开发 bundle 的 `bootstrap_repair_input` `/2` 捕获 exact failed source。原生成 `probe_generated_video_candidate` 拒绝输出契约匹配；预览使用实际 ffprobe 测得的 metadata 创建 preview probe，未把它称作原生成契约通过。首次开发 bundle 使用 content-driven 时因素材保持 UNBOUND 而无法解析；保留该 bundle，另封存 fixed 3 秒预览，不修改原历史。

`video-time-map/1` 的锚点为 `(0,0),(120,24),(175,72)`，`audio_policy=mute`，`video_fit=cover`。唯一时序由 resolver 展开，HyperFrames 0.7.103 实际渲染；未直接 FFmpeg 拼接、未创造第二 timeline、未对失败源进行普通 import 或 Production adoption。

输出 `opening-render-checked/output/opening-3s.mp4`，SHA `99fe8efd53d345174fc0938ce0d0e320ac9249c56834653003dad9ca76e6e115`，1,817,191 bytes，72 帧、768×1366、24fps，无音轨。原片严格保留在原 Production project；预览 `usage_scope=development_preview`，qualification `NOT_EVALUATED`，素材 UNBOUND。

`S01-edit-render-report.json` 保存实测及 HyperFrames lint/check receipts，均零 error / warning。显式 `video-analysis.video_analyze(frame_interval=0.25)` 获取 12 帧并实际检查，证据 `S01-edit-visual-mcp.json`；纸卷动作、女子转向与对视仍可见。抽帧不代替正常速度完整观看，也不能验证自然节奏或审美接受。没有音轨只证明明确静音，不证明替换音效已完成。

## Remaining Boundary

后续镜头未提交，商品互动及包装收尾未制作；最终音乐、音效、完整剪辑、P6、Final Acceptance、独立成片审查及用户最终听看均未完成。当前 canonical contract 允许失败源进入 sealed 本地预览，明确禁止把它直接激活为 Production。不能通过倒改已关闭 raw barrier、伪造 SourceUseEvidence 或删除 sound FAIL 来继续。

最小恢复条件为既有 owner 支持对非生成修复的 exact 输出逐项完成新用途验收、保留完整 lineage 与原失败，或适用且明确授权的新有限生成修复；未知状态不得重试。现有剩余两次视频 quota 不自动授权首镜重抽。此记录不是新增 Provider 调用、发布或 Gate 修改授权。

## Learning Assessment

`distill-ai-video-learning`: `no_candidate`。这是一条实际生成链及其派生预览，不能把多个文件、检查层或修订当成多个独立实验；无成熟、可推广的节奏或模型质量结论，不修改 Skill/Policy/Gate。

2026-10-21第二次真实生成后重新评估仍为 `no_candidate`：第一镜主要为原声环境失败，第二镜为新调度下的因果/物件连续性失败，输入、动作与音频责任均改变，不能将两种不同失败归为同一已复现模型结论。独立复核、抽帧、canonical诊断属于同一新媒体的不同证明层，不增加实验独立数；不自动提出或采用Skill/Policy/Gate变更。

Director-only JSON 与用户原文最初放在要求完整 `project.json` 的 `docs/canvas-projects` 数据目录，使首次 Harness 的 `canvas_project_data_check` 拒绝。现移至既有 `docs/superpowers/artifacts/ecommerce/hotpatch-dayoff/`，保持字节不变；README 留在原目录作入口。历史 QA 的原路径字符串与 content hash 保留，不回写旧 receipt。普通 Canvas project data 仍只位于 task run，未把 Director 覆盖冒充可执行 Canvas project。
