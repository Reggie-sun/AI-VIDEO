# Shizhen B Motion Review Candidate

Date: 2026-10-27

Latest review candidate: **B4 / 6秒**，由用户“太快了”“应该慢一点，有个过程”触发；下方 B2 保留为被否决的历史候选。B3/B4均未获用户最终艺术认可；B4为当前影像分层修订，下方保留历史。

## Scope And Status

用户选定 B 黑白负片方向，要求多个过渡态，否决左右擦除，允许调整终态并授权制作。本次完成可观看的局部片名审看片，不包含 S01，不宣称完整独立冷开场、宏观新镜头或真人重制已经完成。旧 F2 曾被用户否决，保留历史，B2也未获用户艺术认可。

## Actual Work

使用原 A3 连续帧 288..359，72帧、24fps、原速。四态参考来自 `outputs/shizhen-episode01/fusion-title-trial-20261026/image-directions/B-states-depth/`，不把参考图逐张叠化。生成的透明字标单独进入 Fusion，原运动底片经局部负片密度、亮度驱动字标显影、固定立柱遮挡合成。原源 AI 标识仍可见，未消除来源标识或改变使用限制。

实际 Fusion 内部 Lua Console 执行。首次 build_B.lua 在不存在的 DeleteTool 方法处停止，无视频输出；移除无必要的诊断节点清理后，检查六帧，再针对灰度过平、AI标识矩形补丁做B2修订。完整72帧由Fusion Saver输出。所有脚本和 B1/B2.comp 保存在本次输出目录，没有修改共享渲染器。

通过既有 ProductionStateCommitter 建立隔离审看项目 `runs/shizhen-fusion-B-motion-20261027/project-r1/`。HyperFrames/ResolvedTimeline负责准确时钟、原环境声、原Suno B配乐与最终输出；没有直接复用原片内嵌音频旁路混音，没有激活素材或发布。

## Exact Output And Verification

- 视频：`outputs/shizhen-episode01/fusion-B-motion-20261027/variant-B2/失帧-Fusion片名试片-B2.mp4`
- SHA256：`2def03b0b76dc9397bff2949086e68d3ed9184f3d3ef824fe217b751845bf31b`
- 实测3秒、1920×1080、24fps、72帧、H264/AAC、48kHz双声道，3065233字节。
- 渲染凭证：同目录 `variant-B2/render-receipt.json`；显式 project-local video-analysis：`qa/video-analysis-B2.json`。
- 实际浏览器1倍速完整播放：`qa/playback-B2.json`，72总帧、0掉帧、无播放器错误；页面重播操作通过。此证据不等于人工完整听看或艺术通过。
- `qa/audio-preservation.json`：解码PCM与旧F2同三秒的原环境声/配乐混音完全相同；未重做音乐，未宣称人工听感验收。
- `qa/parent-review.json` 保留艺术限制：负片高光边缘、立柱遮字仍待审，未标最终通过。
- 观看页已通过 xdg-open 打开：`http://127.0.0.1:8876/outputs/shizhen-episode01/fusion-B-motion-20261027/index.html`。

## Limits And Publication

当前只交动态片名候选供用户审看，不等于整段开场完成。真人质感仍受原生成底片限制，正式素材权利/标识限制仍继承原记录。无新增付费视频或音乐调用；透明字标参考由先前内置 imagegen调用生成，计费信息未暴露，不推定免费。

按成片优先规则，用户效果认可前未做完整工程回归、commit或push；文件为local-only/untracked。无无关文件stage/commit，无其他工作覆盖。

自动 learning evaluation：`no_candidate`，本次仅一个合成链的两轮调整，不能作为独立重复实验或普遍制作规则。

## Independent Review

同一 read-only reviewer `/root/opening_concept_check` 检查 exact 候选与抽帧，发现 B2-01 负片色阶断层、B2-02 立柱切中识字骨架，均 blocking_candidate；B2-03 固定左右分区为 non_blocking。Parent 全部 CONFIRMED，保留 OPEN，不以技术播放通过关闭。证据 `qa/independent-review.json`。本次两轮局部视觉修订已用完，先按用户“视频呢”交当前真实诊断候选，明确艺术未通过；后续修正须围绕这三个具体问题，不能继续泛化技术方案或宣称已交最终片。

## B3 Slower Process Revision

用户反馈后追加一个有界B3候选，旧B1/B2消耗与失败未重置。检查原始视频发现wide随后切近景，不能用其后六秒冒充同构图连续素材。已向用户明确片名段使用光流慢镜：原288..359共72帧，经本地运动补偿插值为144帧6秒；原始片不变，核心事件及四句对白未改。重新安排色彩退层、密度显现、字形可读与终态停留，非单纯把B2成片以0.5播放。图形未左右扫动；字组缩小左移，主识字骨架避开立柱。取消硬阈值，固定局部椭圆区并保护地面。静帧发现遮罩侵入人物后缩窄，修订存为B3-final.comp；最终实际帧中人物保持在变化区之外。

最终：`variant-B3/失帧-Fusion片名试片-B3.mp4`（相对于本次输出目录）；SHA256 `c35cc24125963c4a0015d514cb8f66ca4e97c55709290a9bf3add5f15218435e`，4442700字节、6秒、144帧、24fps、1080p、H264/AAC。渲染凭证 `variant-B3/render-receipt.json`，显式MCP `qa/video-analysis-B3.json`，实际浏览器 `qa/playback-B3.json`：1倍速、144总帧、0掉帧、无错误。已打开 `index-B3.html` 供用户观看。

声音经原P4编排：Suno B从已有源延续到六秒，仍原速；原无对白雨声段以0.2秒交叉接续到六秒，不对音频降速。此版不再声称与B2解码PCM相同。测得峰值-16.2dBFS、平均-31.9dBFS，非人工听感证明。准确时钟按视觉慢镜的source-time关系延展，未当成新灵异规则。

本地准备失败保留：第一次把原VOICE类别的环境声窗口声明为ambience，既有contract拒绝；恢复原登记类型dialogue，仍明确窗口无新增对白。第二次继承旧shot三秒duration_policy，六秒trim被拒绝；经同一ProductionStateCommitter在新的project-r3准确封存六秒Shot，未修改既有合同。project-r2失败准备证据保留，最终仅project-r3参与输出。没有绕过renderer、直接mux或覆盖旧项目。

B3的阶段展开和局部问题修订已可见，整体灰化仍有调色滤镜感，艺术效果待用户审看；不等于完整独立开场通过。无新增付费视频/音乐调用，暂未完整工程回归、commit/push。自动学习评估仍为no_candidate：一个合成链的迭代不足以推广成通用规则。

B3独立复核：同一reviewer确认阶段在实际截帧中展开，B2硬色阶和主识字骨架遮挡明显减轻；保留B3-01灰幕感、B3-02右侧笔画与柱子竞争，两项non_blocking，Parent CONFIRMED。记录 `qa/independent-review-B3.json`；未据抽帧宣布光流、音轨或整片艺术通过。

## B4 Image-Layer Refinement

用户“可以”批准继续解决B3的平灰覆盖与贴字感。本轮保留六秒节奏、原B3光流底片、B3声音结构和字幕/时钟安排，只修订Fusion影像层次及字形显现。借鉴[Blackmagic论坛的frequency separation说明](https://forum.blackmagicdesign.com/viewtopic.php?f=22&t=70621)，原图细节与模糊层分开：只改变远景大块明暗密度，并加回原运动雨痕/高光。这个技术是影像频率近似，不等于真实深度分割，也不自动证明电影质感。文字先随同一底片局部亮度/细节形成淡纹，再逐渐压实；没有新增随机噪点或左右擦除。

本轮实际一次六态静帧检查、一次144帧Fusion完整渲染、一次HyperFrames最终渲染，未新增任何付费生成。当前commit基线846b464由其他工作区提交并包含先前历史，本任务未把它当作本轮验收/发布。

- 文件：`outputs/shizhen-episode01/fusion-B-motion-20261027/variant-B4/失帧-Fusion片名试片-B4.mp4`
- SHA256：`e00963afc77ac0501243657bf1a60afe1ac16482b70d6911e1cb2a9c59f206a8`
- 实测：4715858字节，6秒，1920×1080，24fps/144帧，H264/AAC，48kHz双声道。
- 隔离项目：`runs/shizhen-fusion-B-motion-20261027/project-r4/`；Fusion图 `B4.comp`，既有committer和HyperFrames负责import与最终输出，没有激活/发布。
- 凭证相对本次输出目录：`variant-B4/render-receipt.json`、`qa/video-analysis-B4.json`、`qa/playback-B4.json`。实际浏览器1倍速全片144帧、0掉帧、无错误；B3对照/B4重播按钮验证。
- `qa/preservation-B4.json`：7个抽查PNG帧中，人物及右街ROI像素与B3完全相同；解码PCM与B3完全相同。仅证明对应区域/音轨保留，不代签运动自然或人工听感。
- 观看页 `index-B4.html` 已打开，保留B3对照；`qa/parent-review-B4.json`仍将艺术验收保留为待用户。

中间态在实测帧中比B3保留更多雨痕与建筑明暗，字形在第72/96/120帧逐步形成；局部平面化程度与终态构图仍须用户判断。完整宏观独立开场、真人重制和正式素材使用限制未因本轮片名修订关闭。按成片优先未运行完整工程回归或commit/push；本轮新增文件保持local-only。自动学习评估no_candidate，仍为同一合成链的连续迭代，不推广成通用制作规则。

B4独立复核确认灰膜感减轻、3.4秒零散字形与原雨夜明暗的关系更可见；保留B4-01立柱与失右侧笔画竞争、B4-02终态仍有实墨字层感，两项non_blocking均由Parent CONFIRMED，详见 `qa/independent-review-B4.json`。不把抽帧和播放记录升级为人工完整听看或最终艺术通过。

## B5 Pillar And Title Composition

用户要求继续优化立柱与文字构图。保留B4底片、六秒显影、原速音轨，仅在Fusion分离同一透明字标中的两个字并独立等比定位：“失”位于粗柱与细柱之间左上玻璃，“帧”位于细柱右侧下方玻璃。细柱作为两字间隔，不抹柱、不重画字形，也不重做音乐。四个检查帧确认可见字形完整后，完成一次144帧Fusion与一次HyperFrames输出。

- 视频：`outputs/shizhen-episode01/fusion-B-motion-20261027/variant-B5/失帧-Fusion片名试片-B5.mp4`
- SHA256：`f8b3b65e3554ba19a19ce0d5e818445acd21ef98cb29be06f39a7baaa1018067`；4710563字节，6秒，1080p，24fps/144帧，H264/AAC双声道48kHz。
- 隔离项目 `runs/shizhen-fusion-B-motion-20261027/project-r5/`；Fusion图 `B5.comp`；未激活或发布。
- 输出目录内凭证：`variant-B5/render-receipt.json`、`qa/video-analysis-B5.json`、`qa/playback-B5.json`、`qa/preservation-B5.json`。
- 浏览器实际1倍速播放完成，144帧、0掉帧、无错误；B4对照/B5重播验证。人物及右街7个抽样PNG帧ROI与B4像素一致；最终音轨解码PCM与B4一致。这不是人工听感或光流质量证明。
- `index-B5.html` 已通过xdg-open打开；B4及其creative材料保留在 `variant-B4/creative/`，当前creative binding更新为B5。

Parent审看实际MP4抽帧及正常速度播放截图：柱子没有再截断两字主要骨架，人物右侧避让保留；淡显过程仍有阶段性低对比，终态字层感仍是既有艺术限制。源AI生成标识保留；仅片名候选完成，非完整独立开场或正式素材验收。新增付费调用0；按成片优先未做完整工程回归、commit/push。学习评估no_candidate，仍是同一合成链的用户导向迭代。

B5独立限定复核finding set为空，Parent CONFIRMED：字形完整、未见拆字残片或柱字相切，3.4秒巾旁较淡但4.6至5.8秒可辨认；证据 `qa/independent-review-B5.json`。此结论不替代完整人工听看与用户艺术验收。

## B5 Existing-Film Assembly

用户“可以就先这样,拼接起来我看下”暂定B5局部视觉，要求独立开场连看。新文件 `variant-ASSEMBLY-B5/失帧-独立开场-ASSEMBLY-B5.mp4`，SHA256 `edeacc78b2fd85fb33565aee742a6c5745a106962b5a86efc06b8a5d5e0a87fb`，25509958字节，561帧/23.375秒，1080p/24fps。R3前417帧（已修动作接缝）加B5全部144帧；旧三秒片名退出本版，源文件不变。不含S01，四句对白、原音乐、原字幕和AI标识保留。观看页 `index-assembly-B5.html` 已打开，完整播放及切点跳转/重播通过。

实际走已有成片资产→ProductionStateCommitter隔离导入→CompositionSpec→ResolvedTimeline→HyperFrames。R3/B5既有混音解码为PCM，同窗、0增益、无新淡化进入P4，source_audio_policy=REPLACE明确指以相同来源PCM作为成片原声，不伪造generated-source KEEP证据。`usage_scope=production`是普通导入资产的resolver分类，不代表真实Production qualification/activation/acceptance；本次一律本地审看，继承原始raw QA失败/使用限制。

准备中的确定性失败均发生在渲染前且无付费副作用：原始qualification三镜与两条尾声原声混合，因captured-dialogue每Shot一条原声合同被拒；未改共享合同，改为装配已完成的审看成片。首次导入使用不存在的input artifact ID被严格reader拒绝，修为真实project artifact，失败目录保留；首版浮点秒数被上取整多一帧，重新封存原有的安全帧长表达。最终项目 `runs/shizhen-fusion-B-motion-20261027/project-assembly-rendered-B5-r3/`，失败准备不充当通过记录。

凭证相对本次输出目录：`variant-ASSEMBLY-B5/render-receipt.json`、`qa/video-analysis-assembly-B5.json`、`qa/playback-assembly-B5.json`、`qa/preservation-assembly-B5.json`。实际浏览器1倍速561帧/0掉帧；exact抽帧确认事件、回答、空位、B5序列。P4混合PCM与两源相同窗口拼接完全一致；有损输出缩图平均8bit误差约2.51（事件）/2.36（片名）。最终AAC波形相对输入PCM测得1024样本/21.33ms滞后，对齐后相关0.99960；不宣称最终PCM相同或完整人工听感通过。

`prepare-assembly-review`及`verify-assembly`已执行；`qa/assembly-B5-observations.json`逐刀绑定exact输出，`qa/assembly-B5-verdict.json`保留NOT_EVALUATED：抽帧/播放器/波形均不能代签正常速度人工听看。按用户先看要求交未最终验收的拼接审看片。此轮为既有素材保留式装配，无新的创作重剪，Parent完成相称核对，无新增独立Agent轮次。无新增付费生成/远程声音分析；此前UNKNOWN未重试。新整段仍待用户审看，未完整工程回归、commit/push；他人dirty文件不动。

用户随后提醒宏观部分：核对 `opening-A-revision-20261026/production-inputs/README.md`、`CO-WORLD.director.zh.txt`、`preparation.json`，推荐同一道路夜班流动→可定位站棚→事件→空位片名的方向仍有效，宏观有效剪辑预估4–6秒但不锁长。旧干街库存已弃用，同街雨夜真人宏观参考/视频未制作，execute_ready=false；本次23.375秒只有事件+B5，不能称宏观目标完成。已向用户明确承认这一缺口，未将旧方案悄悄删除。学习评估no_candidate：同一制作链，无新的独立实验。

### Assembly User Rejection And Exact Diagnosis

用户“等下刚才拼接之后16s之后切镜头很不自然”后暂停媒体改动，检查17.375秒切点。实际播放截图16.8秒近景头/视线朝右，17.45秒全景回到偏正面，18.5秒再次向右，动作回接。B5底片来源288..359早于紧前近景361..527，加上原速近景→局部半速全景及大景别变化，造成明显脱节。原“女人仍持电话”的局部说明不足以证明姿态连续；已更新逐刀state_continuity/repetition为FAIL，重新verify-assembly，保留同一MP4不修改。B5单段暂定不等于拼接通过；本版是被用户指出接点问题的诊断片，不能作为完成版推荐。下一修复需保护四句对白和显影过程，先解决实际出入点状态，不用溶解掩盖。此刻只诊断，未擅自缩短B5或新增生成。

## Explicit Rule Update And B6 Repair

用户“修改规则继续”直接授权本轮规则修改及接点修复。`AGENTS.md`增加一句单段认可不豁免拼接审查的原则；`open-video/references/creative-completion.md`和`docs/visual-quality-gate.md`细化同一既有owner的源时序/入出点/速度及“切前→切后入态→随后动作”核对。没有新增schema、自动检测器或第二时间线；也没有把一次经验自动推广成已学习采用的模型规律。

本轮最小修复保留R3事件前417帧，把片名视觉入点从B5第0帧改为第36帧，保留36..143共108帧原速度。片名段由6秒变4.5秒，只删除已见的回正再转头前导；不加速显影、不倒放、不冻结补时。声音从B5第0样本连续取216000样本，保持音乐与前段接续，最后48000样本淡出；声画不同源窗有意明确，不声称same-window或最终音轨字节不变。所有四句对白及其对应事件原PCM保留。

实际成片 `variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4`：SHA256 `d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`，24390940字节，525帧/21.875秒，1080p/24fps。隔离项目 `runs/shizhen-fusion-B-motion-20261027/project-assembly-rendered-B6/`；原B5/B5拼接FAIL及raw历史均保留，不激活/发布。只有一次新完整候选，无新增付费/远程调用。

相对本输出目录的当前证据：`variant-ASSEMBLY-B6/render-receipt.json`、`qa/video-analysis-assembly-B6.json`、`qa/playback-assembly-B6.json`、`qa/preservation-assembly-B6.json`。浏览器实际1倍速525帧、0掉帧，完整播放、切点定位和重播检查完成；新页面 `index-assembly-B6.html` 已打开。16.8/17.45/17.9/18.5秒实际截图显示切前后均右向持电话，不再出现旧版回正前导；此局部观察不代签完整动态自然度。P4混音中事件834000样本与原事件完全一致；视频缩图平均8bit差值约2.51（事件）/2.34（保留的B5窗口），属于有损重新编码比较，不是字节同一证明。

`qa/assembly-B6-verdict.json`由既有verify-assembly产出NOT_EVALUATED：缺正常速度人工完整听看，不能把抽帧和播放器报告签成PASS；目前可交用户的是修订审看候选。新原声比较仍须注意既有编码链1024样本滞后与有意片尾淡出，未在本轮改共享音频引擎。规则精准验证72项通过（open-video Skill及assembly证据入口），`qa/rules-focused-B6.json`明确focused、不代表完整工程回归；diff检查通过。

用户此次暂定的是B5局部，B5拼接又被否定；本轮新整段仍待用户效果审看，故按成片优先尚未完整工程回归、commit/push。宏观同街雨夜段依旧只有生产准备、不在B6内，不以本轮剪接修复宣称完整开场目标完成。自动学习评估no_candidate；规则变化源于用户明确指令而非自动学习采用。

B6独立复核由原read-only reviewer在用户新修复指令下追加一次限定轮次，历史不重置：所审截图中未见回正/重复转头，字形显影未见受损，finding set为空；Parent CONFIRMED局部范围。`qa/independent-review-assembly-B6.json`明确主观顺畅度、速度感与实际听音仍不能由抽帧判定，不升级assembly总判决。

## B6 User Acceptance And Macro Handoff

用户后续回复“可以,宏观的准备怎么做,我准备开新的窗口”，记录为认可当前B6局部连看结果、转入宏观准备。此新的人类反馈不改写此前机器NOT_EVALUATED记录，也不代表宏观/真人统一/正式发布完成。制作与授权状态交接至 `outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/MACRO-HANDOFF-20261027.md`，含exact B6身份、当前切点修复、同街宏观/中间/末态参考职责与未新增付费授权边界。本轮只整理交接、核验源文件及引用，不新增生成；完整工程验证与owned commit/push仍未执行，显式交接待办，不夹带其他窗口改动。学习评估no_candidate，用户反馈与同链制作不充作独立实验。
