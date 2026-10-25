# Hotpatch Dayoff Editing Preview Record

Date: 2026-10-20

## Subtitle Execution Repair — 2026-10-21

用户否定旧 `c951…e6e3` 的字幕“太low了”，随后要求修复字幕执行问题，并明确选择“成片与执行规范一起修”。旧样帧检查确认：宽底条反复出现，接盒时叠泛化文案，结尾三根同形长条挤占商品与留白；未发现渲染器把合格设计画坏的证据。旧版仍保留作拒绝基线，原先抽帧finding为空不代表用户认可。

本轮只调整现有 G4 guidance 与本片图文数据，不修改共享 Python renderer/validator 或扩建新模块。现有 `ecommerce-ad-workflow` 入口明确本地审片、字幕修复、手工编排也适用；`references/advertising-copy-graphics.md#authoring-and-media-review` 补充表达/必要性先于样式、落实到真实输入、检查图层与原速阅读、用户拒绝后重审而不能以技术PASS关闭。该指导不具备自动拦截Agent或保证审美的能力，不新增状态或审美评分；这是用户直接要求的规范修复，不是将单次结果自动ADOPT为经验规则。

实际新编排位于 `runs/hotpatch-dayoff-20261020-001/author-subtitle-repair.py`，设计依据为同目录 `subtitle-repair-direction.md`。开场改为“下班了”与手机动作关联的“手机也歇会儿”，仅局部底衬；接盒/落座留白；商品名36px、结构示意34px、片尾主题50px及详情28px，商品段不加底条。安全区、避让对象、cue与既有beat事件绑定实际写入 `GraphicTreatment`。独立概念复核CC-10/11建议标签可读、去掉悬空逗号、时点关联，Parent采纳；不将这些具体字号/文案写成通用规范。

使用既有 `AdCreativePlan → CompositionSpec → ResolvedTimeline → HyperFrames 0.7.103 → ProductionStateCommitter` 完成本地 `hotpatch-subtitle-repair-006`。新MP4 SHA `82ad5125cf65a51a83f89ae6e243aaca48ade737e3aa1f5868bf282bf0306423`，3,971,940 bytes，768×1366、24fps、264帧/11秒、AAC48kHz stereo；canonical路径为 `runs/hotpatch-dayoff-20261020-001/production/state/render/outputs/82ad5125cf65a51a83f89ae6e243aaca48ade737e3aa1f5868bf282bf0306423.mp4`。同字节审片副本 `/home/reggie/电商/热敷贴/成片/今天_腰先下班_11秒_字幕重设计版.mp4`，不覆盖旧版。

局部验证：真实render完成，严格重开项目；对比新旧resolved visual/audio spans与Composition layers/audio tracks完全相同；新旧MP4实际解码PCM SHA均为 `2df9d19771a0f2343a6f9e5880985dfa93f0e0d7673ad077ecfaf28d3b770b6d`。新图文7层，非原8层。结果见同目录 `subtitle-repair-media-check.json`、`subtitle-repair-render-output.json`；canonical render receipt为 `production/state/render/render-receipts/c0aa4d786598023dcdfeede6b5e30dd06bd15f395db250c525a96a756e90b036.json`。实际调用project-local MCP取得22张半秒样帧，保存在 `subtitle-repair-006-visual-mcp.json`；Parent查看开场、放手机、接盒、落座、两商品段与收尾，未见文字压住脸/手/商品或明显裁字，但不能以此证明正常速度完整阅读与节奏。音频不重跑远程分析，复用原音轨且解码一致不新增聆听证据。

独立Native `concept_review`核验exact SHA并查看全22张实帧，未见文字遮住脸、手、橙盒；对两处现有规范变更finding为空，确认本地preview不能豁免设计且没有新增固定模板/自动审美批准。CC-12为non_blocking：7/8秒切入帧标签几乎不可见，7.5/8.5秒才清楚，淡入缩短一秒商品段的清晰停留。Parent确认阅读窗口风险，未宣称修复；保留现有0.25秒fade供用户原速审片，未为消除此切点现象使用历史已知会提前插值露出未来字幕的NONE entrance，避免布局回归或再扩建工程。具体边界见 `subtitle-repair-independent-review.json`；不把本轮实帧复核说成原速阅读通过。

用户审美、正常速度完整人工听看、P6/Final Acceptance仍NOT_EVALUATED。本轮无视频/音频Provider调用，历史计数保持视频3/3、音频4/4。遵从用户先审片后工程套件/commit的要求，未跑完整工程套件、未stage/commit/push；既有失败/中止Harness不被本轮局部证明替代。规范仅做局部diff核对与上述独立定向复核，待用户认可后按实际changed paths完成工程验证。其他dirty/index工作保留。

按 `record-ai-video-session` 稳定候选边界更新本记录；`distill-ai-video-learning`评估为 `no_candidate`：当前是一条受用户否定的基线及尚未获认可的字幕修复链，不能据此提出已证实的通用审美结论。历史检索返回exit3、library-incompatible，已按owner停止重试并依据当前文件处理，不为记录重建索引或新增测试/Provider调用。

## Full Film Review Copy — 2026-10-21

最新用户反馈“你在干什么这合理吗这么慢”后，Parent确认把剪辑扩成工程修改并等待宽泛回归拖延了交付，属于流程选择失当。已直接提供下述完整视频，并停止本任务独占的`production_contract_tests`进程；Harness正常保存中止结果；回传stdout在中止前已有7个F标记，但没有完整failure明细，因此工程验证未通过，不能把它仅解释为中止或声称整组检查通过。稳定receipt为`.agent/harness/runs/hotpatch-final-product-film-stable-20261021/receipt.json`：前9项完成，完整合同套件中止，后续未执行。用户随后明确顺序：先由用户审片并认可效果，才运行完整套件，验证通过后再commit/push；这条流程指令不是对当前视频的认可。后续套件、诊断修复与提交均等待该实际认可。工程修改保留本地、未提交/未推送；媒体文件及所有历史保留。本轮record/learning评价为`recorded/no_candidate`，没有为记录新增Provider、媒体或测试。以下本地focused48 passed、独立代码审查及媒体检查各保留自身证明范围，不代替未完成的最终policy验证。

用户对最后一次改为“放下手机—接盒—伴侣落座”、退役纸卷剧情的具体问题回答“我接受生成啊”。授权封存在 task `final-slot-authorization.json`，沿原 METASO / `MiniMax-H3` 执行第3次且最后一次视频提交；没有再次询问、自动重抽或切回 Seedance。以下2/3视频、3/4音频以及等待此回复的段落均为历史，现由本节取代。

新 source attempt `canvas-d5478cc0e117ff0e92a01a004121235590805518`，exact MP4 SHA `55857f1ae02d2e2be8d00a3c46030cfa2b14d35f029ade93afead44ab6c440ea`，6,146,483 bytes，768×1344、192帧、24fps、8秒、AAC32kHz。输入为实际核验过的原创人物/客厅图、真实中央橙盒及8秒粗动作白模；无竞品上传。exact request body SHA `5cfe93ad47cebbeef248d83a5fc318113f0e933336587be1b561b629610adbec`。HTTP200结果已知；同一输出经原 public-address pinning/TLS SNI/no-redirect downloader取得，没有重复POST。

显式 project-local MCP 每0.5秒观察全8秒：放下一部手机并释放、女子双手承接后男子释放单个橙盒、男子随后坐在右侧，人物身份和物件连续。`SP1-canonical-diagnosis.json` 六项要求全PASS，证据hash `5b4f146ef02d1995d47b6cf2be56a022b0ee3a01d45c15d0f93586489df558f4`；已沿 canonical validate/activate 准入。手机是否反扣未获证明，已披露导演朝向偏差；不将逐项PASS说成prompt逐字服从。sound项仅证明明确MUTE/P4责任，不能替代成片音频。

完整剪辑由 `CompositionSpec → ResolvedTimeline → HyperFrames 0.7.103 → ProductionStateCommitter` 完成：source0.5–7.5秒以1.0x保留7秒，接1秒真实包装、1秒贴片结构示意、2秒真实包装收尾，共264帧/11秒。文字从“再忙一下？”到“手机，下班了。”与放下手机动作关联；只借休息与关心建立关系，不演产品即时疗效。完整原始brief、七项explicit intents及九项原final requirements均保留；开发审片另补五项视觉方向，不回写或伪装成历史raw准入标准。

最终 canonical 文件：`runs/hotpatch-dayoff-20261020-001/production/state/render/outputs/c951788b2c107da8e7666eeb3bd810e9a5c519ccf59fc5b551216a487030e6e3.mp4`，SHA同文件名，4,042,084 bytes，768×1366、H.264、24fps、AAC48kHz stereo。已按相同SHA复制到用户素材目录 `成片/今天_腰先下班_11秒_有声审片版.mp4`，不重新编码、不覆盖异名旧片；这是本地审片副本，不是Production delivery package或公开发布。

P4三个登记音轨为实录手机落桌、低音量纸盒窸窣及钢琴。新手机声来源为 Vladislav_Sazonov 的 [Take the phone and put it on wooden table](https://freesound.org/people/Vladislav_Sazonov/sounds/859962/)，实际页面CC0与公开preview/完整PCM派生保留于 `input/licensed-audio/`；其他两项CC0来源见历史声音节。最终平均音量−21.8dBFS、峰值−5.4dBFS。第4次且最后一次 `gemini-3.8-flash` 分析exact完整11秒音轨，HTTP200，明确观察到 `piano music`、无可辨语音；未单独辨认短促动作声，故不能声称其存在感/同步听感通过。当前总消费为视频3/3、音频4/4，均known outcome，无剩余额度或UNKNOWN。

独立Native Codex审片查看完整半秒样帧，CC-08指出结构局部过紧、CC-09指出收尾字靠边。Parent确认并使用原像素重排留白、展示更多层次、内移文字；新版`c951…`定向复核finding set为空。`film-005-visual-mcp.json`为22帧exact证据。此复核不是正常速度完整播放或人工听音；finish、complete-av、holistic及最终商业审美/传播效果仍NOT_EVALUATED。未取得PackageReady、commercial I2V source handoff、P6或Final Acceptance，不以raw激活或渲染成功代签。

## Local Finishing Recovery

首次静帧接入时，来源AssetRecord元数据更新导致旧crop receipt身份不匹配；通过原candidate/authoring/committer入口创建`packaging-center-hero-v2`并退役仅该无效active派生记录，保留旧不可变证据。未直接编辑Manifest。后续本地render001–003已知check失败：对比度及不同时段图文提前插值重叠；调整为明确淡入淡出、保持独立primary层后render004成功。没有为此关掉lint或放行check错误，失败attempt均保留。

为修复CC-08/09，现有`production/image_preparation.py`新增有界`letterbox`操作，原始像素居中落在显式纯色画布，不缩放、不重绘；旧pad/crop/mask规则及历史receipt字节不变。真实结构图先裁掉上方功效标题和左侧标签，再保留轮廓/分层作示意；包装采用干净crop及暖色留白。两个派生SHA分别为`2db503fac337cad2845ca72c7b1b5a6d18d33ca17ea534f9de6de60ea2d8002e`和`450a8adc56c6135c4b2ba7659db27a94a54cc20852209d9a5ba3e481e70be107`。均经原Registry/committer登记、strict reader逐像素重验。

真实后编辑还暴露reader缺口：authoring已由P5合法退役旧render-domain，但旧last-render pointer仍保留历史，strict reader因此拒绝新修订。两个已知失败事务原样保留。修复仅允许无active render-domain且完整旧四节点SUPERSEDED的情况，并从SUCCEEDED历史attempt取得exact origin graph，核验四类节点、node/artifact/fingerprint和同一render pointer；旧render/source/output继续重验。部分历史、删一补一伪节点、不存在origin、改fingerprint均拒绝，旧输出不算新项目fresh。未删除历史pointer或绕过唯一committer。

工程TDD先复现render→authoring被拒绝，再验证修订、strict重开和新render；图像准备验证RGB/RGBA完整原像素、边界拒绝及receipt重开。最终focused验证48 passed。Risk Gate为`NATIVE_REVIEW_REQUIRED`，原生`reviewer_xhigh`独立审查指出LR-01“数量不足以证明完整unit”、LR-02“origin未与实际render成对绑定”；Parent均确认。修复沿同一成功render attempt绑定exact reopened state的attempt/project/registry/timeline与origin graph，再核验原节点；新增伪节点/伪origin/指纹、两次成功render交换pointer与篡改attempt配对的拒绝回归。关闭和最终policy证据见本轮保存的review材料及 `.agent/harness/runs/hotpatch-final-product-film-stable-20261021/receipt.json`；代码/记录只按owned paths提交，不夹带同时运行窗口的Skill与文档。第三轮固定快照finding set为空；其后首个最终Harness因project.py增长15 effective LOC而拒绝，故把同一退役历史判定移入既有`_project_dependency_evidence` owner，project.py不增长、不改判定条件；Parent对迁移差异自审并重验，不声称reviewer审过迁移后字节，也不为纯迁移启动第4轮。原失败receipt保留于`hotpatch-final-product-film-20261021`。

开发审片封套`film-005-review-packet/`保留exact原始brief、coverage、完整合同与五项视觉方向；`creative_goal_binding`核验成功，报告`goal_chain=verified`、`review_scope=full_contract`，整体`not_evaluated`，没有用partial proof生成最终PASS。当前保留的缺口为完整人工听看、holistic/finish及动作声音可辨/同步，未伪造human authority。

本节是当前稳定制作记录，以下声音失败与纸卷剧情继续作为历史证据保留，不因新片完成而改成PASS。最终完整人类听看仍由用户审片，不回写假human证据。

## Directed Redo Checkpoint — 2026-10-21 (Historical)

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

本记录最初记录首镜真实生成、声音失败及用户节奏反馈后的非生成剪辑预览。该历史阶段未交付完整成片；当前完整有声审片文件与仍缺的人类验收由顶部`Full Film Review Copy`节取代，不把旧预览改称Production接受。

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

## Remaining Boundary (Historical Before Product Revision)

后续镜头未提交，商品互动及包装收尾未制作；最终音乐、音效、完整剪辑、P6、Final Acceptance、独立成片审查及用户最终听看均未完成。当前 canonical contract 允许失败源进入 sealed 本地预览，明确禁止把它直接激活为 Production。不能通过倒改已关闭 raw barrier、伪造 SourceUseEvidence 或删除 sound FAIL 来继续。

最小恢复条件为既有 owner 支持对非生成修复的 exact 输出逐项完成新用途验收、保留完整 lineage 与原失败，或适用且明确授权的新有限生成修复；未知状态不得重试。现有剩余两次视频 quota 不自动授权首镜重抽。此记录不是新增 Provider 调用、发布或 Gate 修改授权。

## Learning Assessment

`distill-ai-video-learning`: `no_candidate`。这是一条实际生成链及其派生预览，不能把多个文件、检查层或修订当成多个独立实验；无成熟、可推广的节奏或模型质量结论，不修改 Skill/Policy/Gate。

2026-10-21第二次真实生成后重新评估仍为 `no_candidate`：第一镜主要为原声环境失败，第二镜为新调度下的因果/物件连续性失败，输入、动作与音频责任均改变，不能将两种不同失败归为同一已复现模型结论。独立复核、抽帧、canonical诊断属于同一新媒体的不同证明层，不增加实验独立数；不自动提出或采用Skill/Policy/Gate变更。

2026-10-21完整商品审片版后再次执行自动学习评估，仍为`no_candidate`：新source退役纸卷、改变人物起始姿态/动作/参考并替换声音责任，是一个新的有界成功素材，不能把两条不同失败与这次结果拼成受控A/B或普遍H3结论。工程回归和两轮布局媒体属于同一链的新证明层；修复作为任务内普通实现，不自动采纳经验为Skill/Policy/Gate。

Director-only JSON 与用户原文最初放在要求完整 `project.json` 的 `docs/canvas-projects` 数据目录，使首次 Harness 的 `canvas_project_data_check` 拒绝。现移至既有 `docs/superpowers/artifacts/ecommerce/hotpatch-dayoff/`，保持字节不变；README 留在原目录作入口。历史 QA 的原路径字符串与 content hash 保留，不回写旧 receipt。普通 Canvas project data 仍只位于 task run，未把 Director 覆盖冒充可执行 Canvas project。
