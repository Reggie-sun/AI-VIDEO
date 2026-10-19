---
record_kind: architecture_implementation
topic_id: non-generative-video-cleanup
learning_eligibility: ineligible
---

# Non-generative Video Cleanup Record

Date: 2026-10-19

## Reopened Tail Repair

用户在先前接受后补充“最后那个瞬间还是明显的有痕迹”，定位为“手放在玻璃上”。旧`58dee01c...`观看版的修补观感验收重新打开；颜色正常的反馈与此前接受的历史保留，不再将该版局部修补写为当前已完成。

证据根为`runs/non-generative-cleanup-tail-20261019-001/`。原raw、旧无损母版和旧观看版的frame96–123逐帧对照，确认旧保护矩形将扶杆旁、真实手缘右侧的一条暗褐残影保留下来。只读原生`code_mapper`核对当前kernel：先计算补片羽化，后将保护区alpha置零；旧x<=570保护线切入x535..680补片内部，在570/571间可从0跃至255。保护像素零变化符合实现，但不能证明作者的保护区包含了正确内容。它解释了本次几何缺口，不推出全部痕迹都由此造成或模型/编码具有同一根因。

本次仅修改普通run计划的frame56–123保护多边形，使其随真实手轮廓变化；plate0、补片、identity affine、feather8与frame0–55计划保持。run-local轮廓作者辅助不进入共享代码，不声称自动识别/跟踪能力；简化共线点前后68份栅格保护mask逐字节一致，最多35个顶点。`bounded-repair-unit.json`封存一条本地候选、生成POST0及一次有限tail review扩展；独立intent check认为目标对齐，同时保留动态边缘和编码后保全的不确定性。原15项、36项、原Manifest与S01 STOP未放宽。

同一公共`bootstrap_video_cleanup`完成并经标准`load_production_project`及`verify_repair_input`重开`/5`：新观看版为`production/assets/files/39da73d103ab0c6c2b46976d6b31cc2b3417c6f1b3ba08e4a820b5b79d4e2a1b.mp4`，2,154,794 bytes；RGB母版为`0e6740df07b704580b51de7f6ae98d3d6914de7ade950c6b9e674851f5e84bd0`，52,734,783 bytes。768×1344、24fps、124帧、5.184秒，实际4:7；观看版为yuv420p/BT709 limited。准入hash为`545e7b74ea0f79383d6c6c8d245081804d13af1f13bba54041a7a30301421092`。新旧母版frame0–55的RGB hash全部相同；每帧源/母版/代理PTS相同，显式保护区像素变化0。四份PCM hash均为原`c9d52680fb853d64b89b3b1350e050811c36af2ff8095fc68901580a5eaefa85`，声音时序相同。见`cleanup.actual.json`、`reopen-proof.json`；代理有损，不继承母版逐像素证明。

显式project-local `video-analysis` MCP提取42帧，0.125秒间隔覆盖到实际末帧5.125秒；未转写、未调用audio_understand。`mcp-call.json`、`mcp-response-metadata.json`及`mcp-tail-39..41.jpg`保留调用/元数据/末三张采样，原工具返回42份JPEG；另以qualified FFmpeg解码新代理全部124帧，`new-tail-dense.jpg`覆盖末28帧、`new-transition-dense.jpg`覆盖52–95，解决旧0.25秒采样停在5.0秒而漏掉末三帧的证据缺口。

既有`reviewer_high`在已消耗三轮后完成一次有据的有限第四轮（不重置历史）：旧`MEDIA-04`尾段拖影在新候选末28帧和native末帧未复现，过渡及原片2.625/3.292/5.125秒对照未见新增指尖缺失、明确轮廓跳变、鞋靴断裂或偏色；新静态blocker finding set为空。Parent在相同图及MCP末帧中确认此有限结果，判为`OBSOLETE_AFTER_CHANGE_IN_INSPECTED_STATIC_SCOPE`。`MEDIA-02`保持：reviewer未播放或听音，不据静帧代签动态体验。见`media-review-r4.json`；没有机械第五轮。

实际Chrome DevTools MCP打开新relative workspace/exact SHA链接，通过HTTP读取bytes重算SHA确认选中39da新片；完整1×、unmuted/volume1自动播放至5.184秒，无错误，再seek5.125秒查看正常颜色与手缘。见`browser-full-playback.json`、`browser-final-frame.png`。MCP写截图文件被其workspace根限制拒绝，返回image由Parent保存；resize失败后保留实际viewport，这些失败不冒充产品通过证据。自动播放不是human听看；已向用户提供新absolute MP4并请求完整1×判断，当前新候选人工观感仍`PENDING`。新开发project/Manifest1、attempts空、qualification `NOT_EVALUATED`，原Manifest hash仍`06b50a94afcbc6d130b24db609dde4513172db8b83447dd0d6392ee04c3bd80a`，S02 POST0。

本次无已证实共享源码缺口，kernel/committer/codec均未改变；只同步既有workflow的保护区/羽化语义和实际尾帧检查说明。源码旧Harness证明保留，不为普通作者计划重跑全仓工程。文档scope完成证明归`.agent/harness/runs/cleanup-tail-followup-20261019-r1/receipt.json`；Parent `NATIVE_REVIEW_NOT_REQUIRED`，独立媒体有限复核另列。`record-ai-video-session`更新本记录和直接S01 notice；自动`distill-ai-video-learning=no_candidate`：同一raw派生链、局部作者修正与实现合同说明不构成新的独立模型质量结论，不创建claim或改Skill/Policy/Gate。检索仍返回stale last-good advisory并排队refresh，未主动重建或宣称fresh index。

## Historical Human-viewing Follow-up

用户实际播放下方第二版RGB母版后报告严重绿紫偏色，并指出前端没有视频。失败截图保存在`runs/non-generative-video-cleanup-20261019-001/user-color-failure.png`；FFmpeg重解码正常和MCP静帧正常均未证明实际播放器显示正确。旧母版不再作为正常观看交付，其原bytes和像素证明保留。已停止旧候选的最终Harness r3，保留`parent-abort.json`；该轮不是完成证明。

当时供人观看的文件为`runs/non-generative-cleanup-viewing-20261019-001/production/assets/files/58dee01c3fb9ad82b2b43e39f80c3ae85d6a1988c1f7e8b687f66b0d6dfd838f.mp4`，2,159,577 bytes；H264 High/yuv420p、BT.709 limited-range、768×1344、24fps、124帧、5.184秒、原AAC stereo/32000Hz。它是独立有损代理，不是修改或替换旧母版。标准loader及严格`/5`验证重开，确认raw→master→viewing三份身份、全部PTS与原声PCM/声音时序一致；见同根`cleanup.actual.json`、`reopen-proof.json`。

原前端catalog实际扫描16,384 entries并截断，遗漏目标；strict detail本身可以读取旧`/4`。共享修复保留原扫描上限，先发现常规primary locator并浅层优先遍历；显式relative workspace/exact SHA深链经既有strict detail读取遗漏目标，无新索引或文件权限扩张。视频库明确显示“修补观看版”，RGB母版默认隐藏于高级筛选。

用户后续确认普通入口为`http://127.0.0.1:5174/`且仍找不到视频，推翻了“直达链接能播放即默认入口可发现”的完成判断。Parent在无query首页复现：645个视频、每页12个，当前观看版已加载但Registry media没有排序时间，落在有文件时间的旧external视频之后。共享修复从既有安全`lstat`投影`modified_at`，列表将其明确标为`timeKind=file`并作为无attempt时的排序依据；不借Manifest时间冒充视频时间，也不覆盖已知生成时间。回归先RED再GREEN。此根页修复作为`3134bdc`之后的窄范围follow-up验证，不重跑无改动的生成/持久化大套件。

根页修复后真实Chrome无query加载651条时，观看版位于首屏第一张；普通点击选择exact token，读取768×1344/5.184秒且无错误。见`browser-default-fixed-loaded.json`、`browser-default-select.json`、`browser-default-final.png`；未通过减少外部来源、隐藏旧失败片或假造attempt时间来置顶本镜。49项Python console回归及19项Node library/browser回归通过。新root诊断首次误选了Chrome自动扩展页，已保存为`browser-default-target-mismatch.json`并固定task page ID重新验证；该误选不作Product失败或通过证明。

实际Chrome已显示正常肤色、灰色和蓝色，1×自动播放完整5.184秒，无解码错误；HEAD200、Range206及advanced母版开关/观看版固定选择均验证。证据为同根`browser-color.png`、`browser-full-playback.json`、`browser-seek-and-media.json`、`browser-controls.json`。Chrome MCP因其共享profile被占用不可用，本次使用任务独立headless Chrome的CDP，未终止或改变用户浏览器、代理或账户。

随后用户对该exact前端链接的完整1×听看问题明确回复“颜色正常，修补效果可以接受”；见`human-viewing-feedback.json`，question item `call_94c03f1c359b410ca39debd491c03990`。这是当时的人工接受，局部修补部分现被顶部尾段反馈重新打开，颜色接受仍保留；不推断用户已逐项确认原台词、道具、具名人物关系或交接终态，不代写canonical QA/activation。

## Current Capability And Limits

用户明确要求“补上这个通用能力”：已有视频出现局部手影时，可以先使用干净底片、遮罩和局部合成修补，不必重新生成。实现位于共享素材准备与既有开发修复准入 owner，源码不包含《界蚀》、人物名或本镜坐标分支。实现计划见 [plan](../superpowers/plans/2026-10-19-non-generative-video-cleanup.md)，操作合同见 [workflow](../canvas-production-harness.md#non-generative-local-cleanup)，职责见 [matrix](../agent-primary-contract-matrix.md)。

首版支持 `video-clean-plate/1`：同视频 plate frame、逐帧多边形、羽化、显式正向仿射数据与前景保护区。它不做自动识别、自动跟踪或生成填补；缺少干净背景、遮罩覆盖不全或遮挡关系不正确时，仍需作者修正计划。静态 capability report 已进入既有 `production_control.source_preparation`，不会自动选择 Provider 或签质量通过。

`prepare_video_cleanup` 使用显式注入的本地 FFmpeg/ffprobe，限定8-bit、零视频起点的 CFR MP4、0或1条原声音轨，保留源帧、PTS、帧率、尺寸和时长；用 lossless RGB 编码后重解码验证每帧。原声音轨 packet copy，另比较解码 PCM 与声音 stream timing。默认600帧/60秒、source200MiB、RGB1GiB、PCM64MiB及有限执行时间；不支持或不能保持的输入拒绝。输出是中间源素材；最终 trim、retime 和声音混合继续由 `ResolvedTimeline` / HyperFrames 所有。

`CanvasProductionService.bootstrap_video_cleanup` 与同名 CLI action 经现有唯一 committer 写入独立开发 bundle。`development-repair-input/4` 同时保留原始失败 MP4、原 Provider probe/失败链及派生 MP4、recipe、local measurement、工具和像素/声音证明。原捕获与派生资产分别登记，标准 reader 复验；不得把派生物冒充 Provider 原片或把 local measurement 当新 Provider probe。派生资产仍 UNBOUND、qualification `NOT_EVALUATED`，Production Shot 绑定和 render activation 拒绝，未新增 timeline、状态 owner 或生成执行链。

观看扩展沿用`video-cleanup/1`与`/4`，新增独立`video-cleanup-viewing-proxy/1`及`development-repair-input/5`：保留原捕获、无损RGB母版及有损YUV观看版，严格验证母版bytes/receipt与Registry父链。实际pixel format/color tags由ffprobe测量，逐帧PTS、几何、时长和原声PCM/时间保持；不将代理当作逐像素保护证明。Canvas新入口默认`viewing_proxy=True`并同时返回master身份，底层committer默认False保持旧replay。原Production quarantine和唯一writer不变。

## Historical S01 Master Preparation

证据根：`runs/non-generative-video-cleanup-20261019-001/`。原片 SHA 为 `c49403ca2a9491647fbe12ab4c277c42611cd866f85bb826697cf1dc1bf6fbc9`，5,248,370 bytes，768×1344、24fps、124帧、5.184秒、AAC stereo /32000Hz，实际4:7。原失败 attempt `canvas-ab20b88226f1308d4695a5a6589fd7c3c092b2b5`、Manifest143 /Project20及原15项/36项要求不变；本轮生成/付费理解 POST0，S02 POST0。

初次 target preflight 在任何目标 durable write 前发现历史 director data 引用了未选入该开发 Registry 的图片。仅修正独立诊断 bundle 的 Scene 引用，移除其中不存在的 Character reference 声明；人物 bible 和原 Production 全部要求保留，未声称诊断图具备人物参考 qualification。见 `cleanup.initial-preflight-failure.json`、`target-reference-correction.json`、`diagnostic-context-boundary.json`。这次已知失败没有写原项目、调用 Provider 或推进旧 attempt。

第一条完整本地候选 SHA `cb230088d4c9a319f3291aac512cb1210403d8c8684983ee73e9b5514c598f6c` 保留。独立静态复核发现约1.0–1.25秒玻璃右下仍有弯曲手指幽影，`MEDIA-01=blocking_candidate`，Parent `CONFIRMED`；初版遮罩从 frame25 开始，早段覆盖不足。拒绝将该版当作完成修补，没有把正确执行了不完整计划归咎模型或像素核。

第二版只调整 frame1–31 的遮罩；frame32–123 计划与首版完全一致，source、plate0、算法、工具、动作源帧及声音不变。经同一公共 CLI、canonical bootstrap、标准 loader 重开，生成以下派生源：

| Identity / measurement | Verified value |
| --- | --- |
| MP4 | `runs/non-generative-video-cleanup-20261019-001/repair-v2/production/assets/files/86eb56c7e2dab3f8aae27cd1c8073d0d6dabd8fcfad3f0d4dadbdf995ecdd9ff.mp4` |
| SHA / bytes | `86eb56c7e2dab3f8aae27cd1c8073d0d6dabd8fcfad3f0d4dadbdf995ecdd9ff` /52,848,315 |
| Video | H264 High 4:4:4 Predictive /gbrp；768×1344、24fps、124帧、5.184秒；lossless 中间源，不声称交付编码兼容性 |
| Source timing / pixels | 全部124帧 PTS 相同；frame0未编辑，123帧局部改变；显式保护区像素变化0 |
| Native audio | 原 AAC stereo /32000Hz；input/output PCM SHA 均 `c9d52680fb853d64b89b3b1350e050811c36af2ff8095fc68901580a5eaefa85`，stream timing 相同 |
| Admission / cleanup receipt | `6de045a9f4d5f8c77727d529f3f0fd7dd9bbc27ee5d14300c9e7cd2068cd3c1f` / `2ccda838db5ed4f66a837c998d93612060eddad1907f2add3489f97090e64b87` |
| Development state | project `non-generative-cleanup-s01-20261019-002`、Manifest1、attempts空、paid budget空、QaPolicy空、qualification `NOT_EVALUATED` |
| Original state | 原 Manifest SHA 仍 `06b50a94afcbc6d130b24db609dde4513172db8b83447dd0d6392ee04c3bd80a`；没有修改/激活原 S01 或提交 S02 |

`repair-v2/arguments.json`、`cleanup-plan.json`、`cleanup.actual.json` 与 `reopen-proof.json` 保留输入、执行及重开证明。故事特定遮罩只存在普通 run JSON，不进入共享代码。

## Media Evidence And Acceptance Boundary

显式 project-local `video-analysis` MCP 对第二版 exact MP4 提取0–5秒、间隔0.25秒的21张图，未转写或调用 `audio_understand`；见 `repair-v2/mcp-call.json`、`mcp-response.json`、`mcp-contact-sheet.jpg`。MCP 的 metadata/scene success 不是内容 PASS。

此前同一只读原生 `/root/cleanup_media_review`、实际 profile `reviewer_high` 完成三轮内容复核。第二轮母版采样与第三轮观看代理21张图中，1.0/1.25秒未再辨识旧手影，0.75–1.75秒未发现新增明确前景截断、鞋靴损坏或接缝；Parent将`MEDIA-01`在此采样范围内判为`OBSOLETE_AFTER_CHANGE`。`MEDIA-03`确认旧RGB母版用户偏色失败，该代理采样及Chrome截图未复现，范围仅限此exact文件/路径；当时未机械开启第四轮，后续新反馈引发的有限扩展见顶部。`MEDIA-02`限制仍`CONFIRMED`：静态图和自动播放不证明完整人工观看/听音。见旧根`media-review-r1.json`、`repair-v2/media-review-r2.json`与旧观看根`media-review-r3.json`。这是媒体样本复核，不冒充源码implementation review或人工验收。

已发布可复用修补入口；旧58dee观看版的颜色接受保留，局部修补观感因顶部尾段反馈重新打开，新39da候选人工观感待确认。`MEDIA-02`中的人工观看反馈保留其原范围，不抵消最新缺陷；原S01声音语义、badge/道具/座位与可采用终态等仍为`NOT_EVALUATED`。原raw的5 PASS /1 FAIL /8 NOT_EVALUATED与abandon历史保留，不因派生物改善改写旧verdict。没有accepted end-state、S02 handoff、连续镜、15秒或完整故事交付。

## Engineering Verification And Publication

源码checkpoint为`3a79de3`、无语义结尾修正`e97beda`、覆盖清单修正`8ce6b62`、观看/发现扩展`3134bdcef3e2e1b99b8c70131359ff4c23d3ea7e`及根页排序修复`955431bbcf07f330c1ea0678a54da7e99b6aa684`，基线`7aed5ae1a53af65f6cc08aa9e9b5c7814e6d069d`。早期聚焦组合64 PASS、资源边界1 PASS与母版真实媒体7/7 PASS保留。观看扩展后显式注入qualified FFmpeg/ffprobe的完整cleanup及旧repair admission组合为59 PASS，其中11项真实本地媒体测试均实际执行；另有console/职责预览63 PASS、Canvas data入口32 PASS和Node library/browser18 PASS。根页新增回归后Python console49 PASS、Node library/browser19 PASS。证据为新观看根`focused-cleanup-tests.junit.xml`、`console-preview-tests.junit.xml`、`canvas-entry-tests.junit.xml`及`default-entry-tests.junit.xml`。像素fixture覆盖不同尺寸、颜色/图案、平移/缩放/剪切、多补片、羽化与前景保护；观看fixture覆盖肤色、灰色、原色及有声/无声转换。这些证明工程迁移，不证明任意真实场景自动修补质量。

准入测试只替身 media adapter，实际使用 canonical writer/reader，覆盖双资产重开、exact replay、源/输出/recipe/proof篡改、source Registry丢失、Production绑定/render拒绝、预处理/目标验证失败不写入及不加载generation runtime。真实 S01 路线则没有替身 media adapter。

源码 Harness r2已通过生成回归551项、旧修复准入17项、reader569项、state962项、新修补离线26项及strategy/router等检查，但在 `harness_tests` 发现新专项漏登记到 `full_tests.covers_check_ids`，该轮整体失败，不能冒充完整证明。`8ce6b62` 只补这项覆盖声明；失败用例针对性复测 PASS，不改算法或媒体候选。新修补的7项真实FFmpeg测试在默认Harness中因未注入工具而skip，由上方7/7稳定实测补充。r1的文件尾空行与r2的覆盖声明失败证据均保留。

r3在用户报告偏色后中止，不报通过；其自封存receipt未手工改成完成。只清理了该轮干净的Harness验证checkout，其余worktree保留。

| Exact implementation scope | Receipt / result |
| --- | --- |
| `7aed5ae..3134bdc` | `.agent/harness/runs/non-generative-video-cleanup-20261019-r4/receipt.json`，24项全部通过；source/range/artifact完整性及`complete_completion_proof`重开通过。新根页修复在main中进行时，使用既有Harness隔离验证owner于干净的immutable3134 snapshot核验freshness；见`source-snapshot-verification.json`，不将历史source receipt声称为后续HEAD的fresh证明 |
| `3134bdc..955431b` | `.agent/harness/runs/cleanup-default-library-20261019-r1/receipt.json`，11项全部通过，包括55项Python console、106项Node与offline client build；在实际main/955431b核验integrity、artifact integrity、freshness及`complete_completion_proof`全部为true，见`ui-snapshot-verification.json` |

Harness中未注入工具的11项cleanup媒体测试保留SKIP，已由上述显式工具59项组合内的11项实测补齐；其他renderer/native-audio可选SKIP保留原适用性边界。两轮Architecture Gate均0 error、1 warning：`provider_console.py`在既有catalog/media projection职责内增加26及1 effective LOC至816；新增pixel/media/admission职责已拆到各自模块，本轮不顺手重构该历史owner。Node测试关闭SSR临时server时的dep-scan/HMR诊断保留，105/106项均PASS；最终又在真实5174根页核验选择/seek及正常颜色，见`publication-browser-select.json`、`publication-browser-seek.json`、`publication-browser-color-settled.png`。

Parent在上述实现验证后对exact候选955431b裁决`NATIVE_REVIEW_NOT_REQUIRED`，见`implementation-risk-gate.json`：无额外独立源码审查硬要求；source/permit/budget/accepted pointer与Production activation未放宽，新增写入只经既有bootstrap且开发quarantine、canonical reader/replay/tamper/失败不写入和实际声画证明已覆盖本范围。未发现具备重大后果且仍需独立审查增益的具体缺口。三轮独立媒体复核另有其scope，不冒充源码审查。显式作者遮罩、单场景真实质量及S01剩余语义/交接限制仍保留。

源码已push远端main，`git ls-remote origin refs/heads/main`独立读回`955431bbcf07f330c1ea0678a54da7e99b6aa684`。本记录及直接S01 supersession notice的完成证明归`.agent/harness/runs/non-generative-cleanup-record-20261019-r2/receipt.json`，后续仅文档checkpoint不重跑全仓工程。各scope独立保存，不把不同run的coverage合并冒充same-run证明。

## Record And Learning Evaluation

本记录由`record-ai-video-session`在共享修补、正常观看、无query根页验证及用户接受的稳定checkpoint写入并更新，同时修正原S01记录的直接supersession notice。`distill-ai-video-learning=no_candidate`：已有成熟方法的实现、synthetic工程fixture、同一原片的多个派生版本及不同proof layer不构成独立模型尝试，也没有隔离用户旧播放器/当前Chrome差异的通用模型质量结论。未创建占位claim、修改Skill或采纳经验Gate；workflow变更属于用户直接授权的工程合同同步。

保留 foreign staged/dirty 与原失败历史；记录不触发额外 Provider、媒体、网络或测试。检索此前返回带 stale 标签的 last-good advisory，并排队 derived refresh；本次不等待/重建 RAG，不声称记录已经进入 fresh index。
