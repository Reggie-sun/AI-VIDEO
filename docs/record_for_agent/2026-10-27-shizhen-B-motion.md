# Shizhen B Motion Review Candidate

Date: 2026-10-27

Latest review candidate: **B3 / 6秒**，由用户“太快了”“应该慢一点，有个过程”触发；下方 B2 保留为被否决的历史候选。B3仍未获用户最终认可。

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
