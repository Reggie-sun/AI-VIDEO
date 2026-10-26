---
record_kind: session_summary
topic_id: shizhen-s03-witness-and-live-action-override
learning_eligibility: ineligible
---

# Shizhen Witness Revision And Live-Action Override

## Duplicate Scan Trim

用户指出36.25秒版约21秒与24秒重复扫码并要求剪辑。已删除该版 `[20.875,23.25)` 的S02尾部2.375秒：S02源窗口改为 `[0.75,5.625)`，在取枪下移、尚未完成对瓶扫码时切至S03；完整保留S03放稳瓶、松手、一次扫码、消失/落枪和反应求证。声画同窗、原速，无新生成或字幕。新片 `outputs/shizhen-episode01/失帧-第一集-S01-S02-S03-去重复扫码-1080p-33.875秒-原声.mp4`，SHA `45fb4e45f815bbe00f42165429dd5f19335e2dbf60ef4206710e09755308f233`，31,241,451bytes，1080p/24fps/813帧/33.875秒，保留原声。旧版不覆盖。

仍用CompositionSpec→ResolvedTimeline→HyperFrames software，lint/check均零error，实际导出和MCP probe通过；新接点抽帧确认只保留后一组完整扫码，未把瓶子放稳过程剪没。完整原速自然度和人工接受仍待用户观看，未签全片PASS或发布。receipt为 `live-action-regeneration-01/join-S01-S02-S03-006-scan-trim/delivery-receipt.json`；仅run-local合成和记录变更，付费video新增0，累计17不变。学习评估no_candidate；film-first完整工程验证与owned commit/push仍等待成片认可。

## Authorized Assembly After 005

用户在收到005地址后明确要求“拼接”，当前已完成S01-007→S02-002→S03-005连续审看片，替代上节“尚未拼接”的当前状态；该授权不被扩大为字幕、发布或全片QA认可。输出 `outputs/shizhen-episode01/失帧-第一集-S01-S02-S03-真人连续版-1080p-36.25秒-原声.mp4`，SHA `fbc9b34f583dabb6d86b21a2f1412243ddfea717cb83cf98fd4afdfb5c2d3e9a`，32,876,494bytes；1920×1080、24fps CFR、870帧/36.25秒、AAC48k双声道。保留原前两镜558帧窗口（S01完整16秒、S02从0.75秒进入），追加S03原速13秒/312目标帧，声画同窗，无字幕/BGM/转场或新video调用。

沿qualification source capture→CompositionSpec2.3→ResolvedTimeline→HyperFrames0.7.103，adapter与isolated runner均明确software模式；lint/check零error，实际导出和输出媒体测量通过，Manifest未改变。receipt `live-action-regeneration-01/join-S01-S02-S03-005/delivery-receipt.json`，唯一timeline共1,740,000目标samples，解码1,740,800含800padding。查看exact输出23.25秒接点：店员左、林序右，瓶仍左手略倾、枪与手机仍分别在原持有者右手；近景切双人中景，枪与手机角度/高度存在源片差异，完整原速接点自然度及声音连续性未签PASS。原片与新连续片均保留，用户接受PENDING，未发布。仅run-local合成与本记录改动，无共享代码新改动；full工程验证与owned commit/push仍待成片认可。学习评估no_candidate，正常复用合成不构成新模型质量结论。

## Seedance 2.0 Remake 005 — Single-Shot Delivery

最新用户要求重做店员不自然、过慢的扫码与扫码枪掉落，并明确使用Seedance2.0；用户已指出未认可不得先拼接。当前交付仅单独Shot3原声，不把旧累计片自动更新。下方003/004及更早“尚未提交”描述均是历史检查点。

本次沿原 `trial-S03-v2`、原task提交attempt005，Project4→5、own4→5、全片known16→17，有限单元仅1次新video、零自动重试。实际使用 `seedance_2.0_vip`、multimodal、13秒、1080p、原声；入口承接S02手机与枪均已在手，不重复购买剧情。四张实际绑定参考依序为原 `S03-live-action-keyframe-01`、新 `S03-ref-02-ready`、`S03-ref-03-landed`、`S03-ref-04-reaction`；后三张由本会话imagegen实际生成，分别约束瓶已站稳且枪降低的中态、消失后枪落台的终态、同一次反应近景，不能冒充真实动作证据。参考职责、来源hash与限制见 `live-action-regeneration-01/S03-seedance20-005/reference-preparation-review.json`。

原声MP4：`outputs/shizhen-episode01/失帧-第一集-S03-Seedance2.0-重做005-原声-13秒.mp4`，SHA `51bf0aaea2deaa8f02fb2a8f3f4f2666a8cd6304e5f9f80f5598fd7eab87368f`，34,353,935bytes，与fetch逐字节相同。1920×1080，313帧，video13.016667秒/container13.057秒，AAC44.1kHz双声道；avg18780/781fps，r_frame_rate60标签不表示真实60fps，也未将原片称为24CFR累计片。未重编码、拼接、上字幕或发布。

显式project-local video-analysis MCP及密集实际PTS抽帧：约1秒瓶已直立，2秒左手退出、扫码，3秒枪降低；3.716667秒店员与持枪手仍在，3.75秒人缺席且枪已接触左侧空台面，无上一版持续数秒悬停；约3.833–4秒林序同框张嘴受惊，约6秒切近景，10–13秒探看。单帧间的重力轨迹、完整原速自然度和声音含义未被充分证明，不签PASS。八项canonical observation均NOT_EVALUATED并保留局部观察，用户接受PENDING。receipt为 `live-action-regeneration-01/S03-seedance20-005/delivery-receipt.json`，相邻 `post-media-gate-005.json`、`media-findings.json`、`disappearance-contact-sheet.png` 保留证据；没有下一镜提交。

新 `/5` authored retarget封存完整image/media输入、模型/模式/输出/能力与明确授权，保留旧 `/4`、QA、已知失败及全部付费历史。实际发现旧source validator错误地把004当前request与003 historical baseline比较，已修成精确匹配004 fetched evidence；删除重复未调用planner helper。P2A第一次knownFAILED是generated_video pending只接受单首帧role；最小补充显式非空image `reference` tuple支持，保留唯一pending video、first/last、重复/未知/非image拒绝。原sealed候选bytes保持，通过strict candidate reader后以新local commit ID正常恢复；没有重复supersession、budget、QA或生成POST。三轮独立xhigh审查最后findings empty；focused12+68及两组旧路径各2通过，实际canonical prepare/start/submit/fetch成功。详见 `focused-verification.json`，不代表full Harness或媒体接受；工程commit/push仍按film-first等待用户认可，保留并行dirty/staged改动。

本轮实际新增1次video与3张生成参考图。全部known video17/17：S01七、S02二、S03五、cold-open三，无已知UNKNOWN。原生只读报价429credits，实际视频扣费待结算，参考图费用未暴露；1500CRD/call仅内部guard，不是成交价。学习评估 `no_candidate`：模型、时长、提示与参考同时改变，局部改进不能证明哪个变量有效，也不能据此自动修改Skill/Policy或宣称2.0普遍更好。

## S03 Physics Regeneration And Approval Boundary

本节更新并覆盖下方旧checkpoint的“S03未提交/总known14”状态。真人S03-003已实际生成并fetch，exact SHA `fb70d66ac802ed1133afffae2b9f4af8b9be0be0493bc2b3119be9866f632c28`，20秒原声；瓶子支撑转换缺失、枪落台碰倒瓶子等观测为FAIL，其他未检查项保留NOT_EVALUATED。旧43.25秒累计片仅是错误提前合成的待修复审看文件，不是用户认可或可用完成版。用户已明确反对未点头先拼接：本次及后续S03先交单镜，得到明确认可后才合成，字幕仍待认可。

用户“重新生成shot3”授权一次有界修复，原S03 task/root不变，历史总15次（S01七/S02二/S03三/cold-open三）保留，总上限15→16，S03三→四，零自动重采样。真实扣费待结算，1500CRD/call仅内部guard。工作目录 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/S03-repair-004/`。Project4的/4 authored目标已封存，同一真人首帧、20秒2.5/1080p，保留原QA规则，只明确瓶底受力→松手退手→移枪隔开→消失后立即落到左侧空台面的完整过程，保留即时同框反应及近景求证。

提交前live回读全部15资源status1000有video，新节点空、账号身份与20秒1080p mode2一致；账本无UNKNOWN。旧003的exact负面经验已走canonical committer记录并supersede。未生成后续剧情、字幕或发布。

发现规划器对同rubric新作者goal误停EVIDENCE_GAP；最小修复为qualification下识别单次、同能力/输出/验收且实际intent变化的prospective goal，保留旧FAIL/NE和诊断，compiled admission与/4提交锁继续验证完整历史、封存目标、预算和permit。最终精准回归117项通过、关联契约回归53项通过（15个既有畸形对象测试的serialization warnings）；独立reviewer_xhigh一轮无finding，Parent核对关键锁仍在。具体源码hash及验证边界见该目录 `engineering-verification.json`。Harness需要exact staged/commit scope，本轮film-first尚未stage，不声称Harness/全工程PASS；本任务源码和记录待用户媒体认可后完整验证再owned commit/push。

### Attempt 004 Delivered With Known Failure

004真实一次POST成功，fetch原片SHA `4255225065ff4c9a34932d14f94472fb64719533a0cedf7a4f8143fa46b1c353`，61,038,628bytes，1918×1080，481帧、video20.016667秒/container20.065秒、原AAC44.1k双声道。平台native的r_frame_rate为60但平均为28860/1201，不能将其称60fps或已制成24fps累计片；仅exact复制交付。地址 `outputs/shizhen-episode01/失帧-第一集-S03-真人重生成004-原声-20秒.mp4`，完整解码PASS，未拼接、未字幕、未发布。

显式调用project-local video-analysis MCP，抽帧与5.25秒起4fps接触表证明：瓶子先被放稳，左手退出，约5.5秒正常在场后才消失，瓶纸饭团留位；主角同框立即受惊，后续近景承接。关键未满足：扫码枪在6.019和7.023秒仍无支撑悬停，至约7.75–8秒才落台。action与space-camera FAIL，其余未完整核验为NOT_EVALUATED，无全片声音理解或用户认可声明。明确提交文本已要求枪降低到隔开的左侧空台面上方、距台面很近、手消失同瞬间立即落下；提示词约束不等于实际落实。证据见 `S03-repair-004/media-findings.json`、`mcp-analysis-summary.json`、`disappearance-contact-sheet.png`、`delivery-receipt.json`。

本次实际新增1次、全部known累计16/16，真实扣费待结算，停止本单元无自动重试。用户未认可前不拼接。本轮工程改动未commit/push，按成片优先等待认可；定向117+关联53离线测试与代码review不替代媒体接受。学习评估no_candidate：一次复杂提示修订同时改变动作叙述/节奏，瓶子改善但枪仍失效，不能推出通用质量保证或因果结论；不继续修改Skill/Policy。

## Current Direction

用户明确将全剧改为所附照片同类的真人实拍感，并要求S01、S02也重做；其余剧情、对白、自然表演、物理连续性和字幕规则保持。旧CG认可只属历史，不批准新真人成片，也不能将新真人镜头与旧CG作为风格连续的完成版混拼。执行计划为 `docs/superpowers/plans/2026-10-26-shizhen-live-action-three-shot-rebuild.md`，当前资料归 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/`；另一窗口的宏观开场/字体目录仍由其owner负责。

## Latest Plan And Trim Revision

用户“旧方案修改了啊,然后继续拼接”后，实际重写 `docs/superpowers/plans/2026-10-26-shizhen-live-action-three-shot-rebuild.md`，明确退役固定三个生成单元、旧8秒与一直主用2.5的默认安排：先完整行动/回应分组，再决定摄影切镜和模型。G01保留现有16秒真人表演；未来G02评估补买咖啡到消失/即时反应/求证的一段约24–28秒多机位戏，因此候选2.5；独立简单不超过15秒的完整内容评估2.0。没有2.0实测质量/价格承诺，也未以文档冒充跨版本runtime接通。旧sealed数据及消费历史不改；新G02入口手机仍在口袋、枪仍在底座，旧S03候选图不能直接当其首帧。

本轮只剪已有源。对同exact S02 MP4做一次local Whisper局部定位，估计唯一语句约1.16–1.84秒，字面误识别不作语义通过；查看开头8fps画面后，从source0.75秒进入，去掉重复推纸、保留说话前停顿和整个后续动作。S01仍16秒，S02保留174帧，唯一ResolvedTimeline共558帧/23.25秒、1,116,000目标samples，声画同窗trim，不变速、不移声、不加字幕/BGM。

HyperFrames0.7.103硬件auto模式两次相同timeline的check都报sweep_static，未出片；保留两个FAIL及一次known-failure恢复边界。独立read-only软件模式诊断check对同source通过；尝试给canonical runner追加CLI flag在invocation前被argv白名单拒绝，保留拒绝且未绕guard。新增共享可选 `browser_gpu_mode=hardware|software` 参数，adapter/唯一isolated runner须以相同controlled environment绑定固定 `PRODUCER_BROWSER_GPU_MODE`；默认None保持旧环境字节，未知值/错配拒绝，不修改argv、网络隔离、renderer/version或lint/check/output验证。随后明确software模式在同canonical路径完成lint/check0error与实际导出，不是拿诊断JSON当成片接受。未修改其他窗口的 `_hyperframes_source.py` 图形变更；`tests/test_production_hyperframes.py` 只追加本任务GPU枚举/错配用例，保留其他dirty hunks。

当前实际交付：`outputs/shizhen-episode01/失帧-第一集-S01-S02-真人连续版-接点修正版-1080p-23.25秒.mp4`，SHA `689f019bfd018bf796e59429b03b4badf4320d660644b35cf65bb52bbecdecf7`，19,462,551bytes；1920×1080/24fps/558帧，AAC48k双声道，解码1,116,160samples含160padding。核对encoded接点样本，第二镜起于店员推纸后，原对白source窗口保留；没有全片声画人工接受声明。receipt `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/join-S01-S02-03/render-receipt.json`，focused验证 `focused-verification.json`；7PASS/208deselected，不是全工程回归。Parent Risk Gate为NATIVE_REVIEW_NOT_REQUIRED，原验收fences不变。S03未submit，本轮新增付费video0，总known14/上限15不变。未发布、未activation、用户接受PENDING；按film-first，完整工程验证与owned commit/push等待用户认可，不夹带其他窗口文件。

学习评估仍为no_candidate：旧24秒同类源硬件曾成功，当前23.25秒只有一组时间线/采样与一次canonical软件成功，无法将问题归因为普遍GPU能力；也没有模型2.0/2.5或人物表演的受控质量比较。只记录有界工程诊断，不自动改Skill/Policy/default或提出普遍配置推荐。

## Current Direct-Viewing Checkpoint

用户明确“别审核了,之前做过,直接给我看就好现在”，随后指出真人S01-006最后一秒头在前、躯干在后的肩颈错位。006 exact SHA `27b065ee05b87622265b76484f98cd4390110d375256f26fe304781993f83252` 已交原片，明确D-art FAIL；其他项目NE，不以免审签PASS。用户继续后，沿原S01 task/root6→7生成007，保留同一真人首帧、纸饭动作和三轮原声对白，只明确结尾自然直立胸像、完整肩颈、眼神嘴角短笑；Project6、node `node_nhmst901g4`、16秒1080p，已fetch并直接交用户，SHA `e65f369828e8e00a311157c7d60abb5f6b0a62e9a5b9245e1695a21e44799691`，59,181,815bytes。没有新全镜媒体审查或人工认可。

真人S02沿原task/root1→2，Project4、node `node_14t3vqh201`，8秒1080p，SHA `15d6d73ed9dfe01392d024ebeefddef30b5419766dce853b50575b2c8f264ff8`，21,993,680bytes，已fetch并直接交用户。首帧取007的13.4秒柜台实际画面，纸饭团和咖啡保持。准备阶段误将输出设10秒、sealed intent仍8秒，Planner在POST前拒绝；用normal committer的一次性 `correct_unsubmitted_authored_timing` 恢复原8秒，previous_supersession保留原不可执行target、原授权/意图/QA/Project/图片/计数/预算不变，存在任何successor request后禁止再校正。此错误没有额外POST。另修复authored predicate应允许保留正确首帧修表演，以及R2V转单首帧时移除旧media；目标仍禁止新media。相关新增精准测试分别2PASS、1PASS、1PASS；先前失败的fixture修正后才通过，不冒称完整工程回归。

当前known付费video共14次：S01七、S02二、S03二、cold-open三。保持旧总上限14并新增一次S01已知人体错误修复到15；不重置历史。真实金额/积分待结算，内部guard上限不作报价。S03真人未submit；已准备两张先后参考，后一张以actual S02尾部修正左手略倾持瓶，需先落稳再消失。用户质疑8秒为何仍用2.5及为何不组织多摄影镜头，Parent确认沿用了旧模型/分组，没有新的2.0/2.5比较证据；后继生成分组待Director重判，不继续机械沿旧切分。

用户进一步要求“shot拼接下”。当前exact真人007+S02002经qualification capture、CompositionSpec2.3、ResolvedTimeline及HyperFrames生成24秒审看版；未生成字幕、未新video POST。第一条native A/V映射试准备因原生VFR与delivery FPS不一致被resolver拒绝，未交片；相关临时shared扩展已撤销。最终使用既有normal-speed capture和从各exact MP4解码的48k原声WAV，明确dialogue provenance及同窗trim，无增益、伸缩、换声、BGM或虚构字幕。只移除captured-dialogue layout中错误的“必须有caption”条件，保留其他窗口的静态片名等既有hunks；新增 `test_captionless_native_join_preview.py` 1PASS，错source/错音频窗仍拒绝。没有改普通Production准入或签质量通过。

最终连续审看片 `outputs/shizhen-episode01/失帧-第一集-S01-S02-真人连续版-1080p-24秒-无字幕.mp4`，SHA `3bf9e46f0d64e890adf0c436faadc2a1a8136c6002964416f6372261647a138e`，20,116,365bytes；1920×1080、24fps CFR、576帧、AAC48k双声道1,152,000解码samples。HyperFrames lint/check均0error；唯一时间线/原声、source identity及Manifest不变检查通过，只证明所测技术行为。receipt `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/join-S01-S02-02/render-receipt.json`。约16秒接点：第二镜开头仍含店员推纸饭团余动作，已在展示时明确说明原片顺接；本版是用户要求的审看片，非连续性合格声明。未发布、未Production activation、用户接受PENDING，字幕仍待明确认可。共享工程尚未完整回归或提交；保留film-first用户认可后再验证/owned commit/push。

## Known CG Outcome

旧10秒S03延迟察觉被用户否决后，沿原task/root做过一次18秒Seedance2.5、first_frame、1080p的创作修订，旧调用和原判决未删除。新raw SHA `9e2bf4f22a797e9bb9caed12ab0beaf47cef6289940a96feb49ebbc17d837003`，49,852,836 bytes，1918×1080，433native帧，mux18.049秒；60fps标签不代表真实60帧，最终交付时基仍24fps。

精确帧中f121(5.050s)店员仍在、f122(5.083s)已缺席；枪在f122–129悬停，f130开始落下、f134附近落台；主角明显后缩约f132。独立媒体reviewer确认物理悬停为blocker，近景约f184能延续同一反应。显式MCP及canonical评价保留5PASS/2FAIL/1NE，原片没有被签成合格。合格注入的Gemini同bytes声音观察有非语言男性喘息、闷响/脚步和安静室内底噪；半截扫码音、环境抽空和精确声画同步未被证明，未假造人工听感。

曾沿正常P4/ResolvedTimeline/HyperFrames试剪：保留source0..122，删123..129，接130..431；最后一个不足24fps完整时钟的尾帧不纳入。新source窗口、原声同窗与独立capture均由canonical owner封存，没有新付费video调用。试剪连看共921帧/38.375秒，SHA `588d13ee6efdd406ca5e37c355f461cd520a2726a7bee74a3fd85dcb64b6dee1`；用户随后改真人风，故该CG试剪未做最终媒体接受，不能称悬枪修复已验收或作为当前交付。原片、失败观察与试剪全部保留。

## Shared Contract And Review

新增typed authored revision目标，复用原supersession `/4`、唯一committer、严格reader和submit锁；旧multimodal没有first_frame时诚实记录None。目标封存exact未来Project、首帧、QA、意图、输出与同Provider/model；后来用户改风格时，以精确旧/新requirement pair和closure授权引用声明五项视觉要求变化，其他ID、proof与未列内容保持，空新增字段从历史payload省略。

第二阶段允许已消费n→n+1的一次继承，全部旧评价原样保留，按唯一(attempt_id,request_hash)计费并与durable同task集合精确比对。真实S01有5次调用、7份评价，不能按评价条数计费；冲突request/Shot、未知结果、缺历史或binding仍拒绝。没有新root/task归零、旧permit复用、隐式fallback或Production qualification。

独立xhigh三轮历史保留在新旧review packets：SAR001首帧缺canonical role、SAR002误用Resolved.output_requirement、SAR004误计重复评价、SAR005缺GenerationIntent导入、SAR006纸动作字面lint不识别“离开台面”，均有具体复现及修复。中间曾错误冻结user_goal原文，导致旧S03真实binding无法重开；已删除两条新加的过严检查，三个旧root及旧`/4`均重新严格读取成功，未改历史bytes。最后一轮actual纯Planner→Router→compiler→binding、exacttarget validators及八项lint通过，unknown/缺史/冲突身份负例保持拒绝。

验证分层：首阶段175项相关回归通过；第二阶段authored-visual为139PASS及一项错误消息断言失败，修正断言后精准单测PASS，未假称整组重跑。quota25PASS、execution入口28PASS、goal兼容6PASS、最终多评价计数及真实锁5PASS。误扩大的约千项feedback组主动中止，仅113项中途PASS，不记suite通过。两个新leaf加入既有Harness映射；未运行full suite，不宣称工程release完成。

## Earlier Live-Action Checkpoint

真人参考两次调用：CG构图作强输入的第一图仍保留CG脸型，判FAIL、不投视频；第二次以用户真人照片为人物/摄影主参考重建便利店，得到 `S01-live-action-firstframe-02.png`。独立concept检查未见明确CG泄漏或纸饭穿插；确认右手只是轻扶台面咖啡，拍摄须先松开而非再次“放下”。这只是参考/概念证据，不是视频或人工接受。

新S01已沿原 `trial-S01-v3`、原task，从5→6计数，选择新node `node_5p3kzhcv9j`，16秒/1080p/first_frame。新目标Project5正常committer应用；截至本checkpoint，真人video新增1次且平台已accepted，仍在生成，S02/S03尚未提交真人video。全部known video累计12次（S01六、S02一、S03二、cold-open三）；当前有界合并上限14，后两镜必须各自实际handoff、preview、预算和新permit，不能消费本单元以外次数。

实际金额/积分尚未结算。1500CRD每call及合并17000CRD只是sealed内部上限，不是报价或实际消费；旧reservation与全部历史保留。未自动发布、未Production activation。新原片需显式MCP及实际声画/动作审片，用户认可后才生成中英双语字幕，末尾无标点；后继不能将技术PASS代替人工接受。

## Remaining Work

真人S03-005已单独交原声MP4，等待用户观看认可；未认可不拼接或上字幕。S01-007、S02-002及23.25秒接点修正版保留。当前有限video单元17/17已用完，不自动续跑。工程改动未完整回归或commit/push，遵film-first待效果认可后再验证并按owned paths/hunks提交，不夹带其他窗口改动。

## Learning Evaluation

`no_candidate`。本次人物风格迁移及未接受CG试剪不构成可推广的模型能力证明；输入、构图与脸型同时变化，不能当受控多arm结论。没有自动修改Skill/Policy/Gate学习规则或标ADOPTED；现有shared contract修改来自用户本任务直接授权。
