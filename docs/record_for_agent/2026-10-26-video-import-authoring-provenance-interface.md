---
record_kind: architecture_implementation
topic_id: video-import-authoring-provenance-interface
learning_eligibility: ineligible
---

# Video Import Authoring Provenance Interface

Date: 2026-10-26

## Human Review Update — 2026-10-26

用户先表示“可以过关”，经明确询问认可范围后回复“6.5秒诊断片的画面和声音”。本次人审认可绑定 `sharp-repair-720-001/post/review/cumulative-review-003/` 的6.5秒720p累计诊断片，MP4 SHA-256 `0dc52da4df8211f56687e4ca7d27dab6aa014971c08ee06c3d532d52a8ce3e6a`；已重新核对用户目录中同名副本的实际hash。画面与声音的人审状态更新为认可，取代下文“未取得本版正常速度人审”的当前解释；保留旧拒绝与当时的NE历史。

认可仅限该6.5秒版本的画面和声音，不扩展为40–60秒整片验收。此前MC-01包装容量/品名比对、原片Gate FAIL及canonical封存状态保持原证据，不把人审认可改写成这些技术或商品真实性检查PASS。后续保留这版已认可的剪辑与声画效果；广告生成和交付固定720p，规格规则已由 `16390fd` 提交推送。

当前18次/A12硬上限已耗尽（A12/B3/C3），本次认可不续期或提高预算，后续付费生成仍停止。完整广告未完成、未发布；本次仅更新人审证据，无Provider/媒体调用、无新工程验证或Production状态变更。自动learning评估为 `no_candidate`：这是同一制品新增人审证明层，不构成独立实验或新的通用方法。

## Problem And Scope

用户要求先修代码再重新生成浮夸版颜生源广告。本次实际错误出在新写的任务适配器，不能归因为即梦不支持视频参考：错误引用未导出的 `measure_png_bytes`；带入视频导入凭证却漏接 Project provenance；合并带显式视频元数据的记录时沿用 Registry 2.0。原共享作者入口已有正确的凭证收集及 Registry 2.2 合并行为。

## Code Changes

`production/authoring_input.py` 新增 `prepared_authoring_input_references()`，从 PreparedArtifact 收集、验证并按原顺序去重内容寻址的导入凭证引用。`canvas_authoring.py` 改用同一接口，保留原有 canonical bytes/path 校验，避免任务适配器再次复制并漏接这段逻辑。新测试进入现有 Harness check 与路径映射；没有放宽 bootstrap、reader 或媒体验收。

任务适配器修正测量函数导入，使用该接口将视频凭证加入 Project provenance，按 Registry 2.2 合并并重新封存；读取两个 authoring-input 时逐个核验，并精确区分主创作包和视频导入凭证。失败中间产物保留在同一 runtime 的 archive，未删除凭证、伪造 AssetRecord 或重置历史计数。

## Verification

- 新接口缺失先复现失败；新增顺序去重、错路径、非规范字节三个回归测试。
- 新接口和既有视频导入→作者→bootstrap→不可变重开测试：4 PASS。
- `test_authoring_input.py`、`test_canvas_authoring.py`、`test_canvas_assets.py`、`test_canvas_project_data.py`、`test_production_bootstrap.py`：89 PASS。此为相关定向验证，不是完整仓库 Harness PASS。
- Harness focused inspect 识别全部四个工程路径，无 fallback/unfocused path；新测试已登记。
- Exact staged focused Harness 另行执行，receipt 为 `.agent/harness/runs/video-import-interface-20261026-001/receipt.json`，结果 FAILED：docs contract PASS，harness tests 为319 PASS/2 FAIL，随后停止。失败涉及 `full_tests.covers_check_ids` 漏列 `authored_visual_revision_tests`，以及7个非本次 owned 的未映射源码/测试。只读检查当前 HEAD policy 已存在前一遗漏；7个文件分别属于 qualification quality repair、preview source clock/input 和 watermark preset。没有为此修改其他窗口文件、隐藏失败或宣称 Harness PASS；本记录更新后旧 receipt 仅作为该次失败快照的历史证据。
- 父级审查结论：现有收集逻辑提取复用，严格存储/读取与 side-effect owner 未改变，相关成功和拒绝路径已验证；`NATIVE_REVIEW_NOT_REQUIRED`。Worker 实现不冒充独立审查。

## Exact Task Evidence

下列路径相对 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/`：

- `hyperbole-001/motion-repair-001/runtime/A/H01-bootstrap-output.json`：真实 bootstrap PASS，project SHA `1b4be1a4393dcfe7b2a85b191dc759bd933881ea392a96b3030b6463c621393d`，Registry SHA `2e288fc3eb0ac67a98207aaa09b78079122b06f4edde588a289adf4e8fc9e207`。
- `hyperbole-001/motion-repair-001/runtime/A/H01-prepare-output.json`：SHA `5f14babb5b3d38622d1172eacded4f6a8ae4b3510d88486d3c29abc548548423`，request `c26ff5f91632c28e18de854ed6d9008068049ef04ac6d983394d267aab2a59fb`，3809/4000 UTF-16，4 PNG + 1 reference_video，native audio enabled。
- 视频参考 SHA `ea8a0664116d9bacd7f8307199082a57a31df528b732b099d0e570ae7d3ff80d`，6秒、360×640、24fps；只约束运动和布局，不转移白模外观、无声状态或表演。
- `hyperbole-001/motion-repair-001/native-readiness/A-H01-c26ff5f91632c28e.json`：2026-10-26T00:08:39Z 实际页面只读预检 PASS，账户、空目标节点、已上传 guide 节点/资源、三层 request 的媒体身份均核验。

本 checkpoint 尚无新 generation attempt/start/submit，历史 durable paid 槽位仍15/A9/B3/C3。旧 H01 空间 FAIL 与 sound/performance NOT_EVALUATED 均保留；技术预检不证明新片动态附着、浮夸表演或声音已通过。新片实际费用未发生；旧已发生费用仍待结算。

## Post-Fix Media Checkpoint

上述零付费接口验证 checkpoint 之后，Parent 于00:11Z执行一次 start/submit，平台 accepted；00:18:48Z poll SUCCEEDED，随后只 fetch 一次。当前 durable paid 槽位16/A10/B3/C3，历史未清零；本次新增1次视频生成，实际积分尚未结算，不把500CRD内部单次上界当成交价。没有新增音义云调用或未知结果重试。

实际 source MP4 SHA `f11aad0d4164edc9b61306ee0e672fac513e6fb97a61bff0aa96e9c2eb6246ef`，21,022,495 bytes，720×1280，241帧，平均帧率14460/601，视频10.016667秒、AAC stereo 44.1kHz/容器10.08秒。MCP展示的60fps是流字段，不能代替平均播放帧率。

Parent 显式调用 project-local video-analysis MCP，按0.25秒检查41帧；独立只读 native reviewer 另按0.5秒检查21帧。新结果的瞪眼、张嘴、抬手、大幅转头明显增强，且未再明显跨鼻换颊；但房屋立面在4.75–7秒头转近侧面时仍缺相应转向、透视压缩及遮挡变化，不能把随平移当动态附着PASS。1.25–1.75秒大助手与新小助手同时出现，存在短暂复制；6.5秒开始裁瓶底，后段标签/瓶身进一步出画。整体 Gate FAIL，action/performance/sound 保留 NOT_EVALUATED，未推进任何后镜。

精确证据位于 `hyperbole-001/motion-repair-001/source-acceptance/H01/`：`mcp-analysis-metadata.json`、`independent-review.json`、`post-media-gate.json`。Gate SHA `5b1ca3504d34e8092cc76ca6018a123f2e8251fee28bbaa862c4eed6dafd7a60`。预观测 rubric 的检查项未变，`sealed-rubric-identity-r2.json` 仅明确区分 request_input_hash 与 resolved_generation_hash，保留原文件及身份纠正说明，不因观察结果改判定标准。原因仍为 UNDETERMINED；此试验不能隔离中文空间澄清、Prompt压缩与视频参考各自的效果。

P4 只制作诊断审片，保留 FAIL，不签验收或激活。任务脚本修正了不受当前 `FixedTransform` 支持的 `contain` 参数；720×1280 到1080×1920同为9:16，使用 `cover` 等比放大，不额外裁切。失败的首个准备项目保留，r2实际 HyperFrames lint/check/render PASS。视频为240帧/24fps/10秒，原生声音1x且仅一次，商户水印“栖澜百货商贸”沿50秒全片轨迹的前10秒缓慢移动，原AI披露保留。实际编码文件0/5/9.75秒另经MCP查看；源片自身的裁瓶等缺陷仍在，没有包装成合格片。

P4报告：`hyperbole-001/post/review/H01/r2/H01-render-report.json`；审片 SHA `035cb943dcbc24631888e1448bce4523a9265e17eb3a02e1bb44178819a7cec1`，15,183,351 bytes。用户可访问副本：`/home/reggie/电商/颜生源/广告试片/2026-10-26-浮夸重做/01-脸上盖别墅-10秒诊断待审.mp4`，复制后SHA实测一致。用户按正常速度看听要求明确反馈“语气和表情都够浮夸”；只接受这两个方向，不覆盖已确认的画面FAIL，也不自动签完整字词/口型专项验收。精确人审记录为 `motion-repair-001/source-acceptance/H01/user-performance-review-001.json`，SHA `a9c7c2fd383c9fe934ecb40c74eeffea5860d6b0982a8049c301ce33eefc6cf1`。

后续改用剪辑保护已认可表演：原生 generation Gate FAIL 保留，暂不 abandon，不再生成新的声音或人物表演。新用途意图 `motion-repair-001/source-use/H01-edit-intent-001.json` 计划选取原片2–4.5秒和7.5–10秒的正面反应，中间用1.5秒真实产品特写替换坏转头，并以原声6–10秒保留完整问句。目标6.5秒，后续15+15+4秒使全片约40.5秒；具体 frame/sample/trim 仍由 ResolvedTimeline 独占。此为新的有限 editorial source use，不能把原片所有角度改判PASS；新编码片、全部剪切边界及听审通过前仍禁止后镜 submit。当前全片未完成，publication=`NOT_PUBLISHED`。

## Learning And Publication

自动学习评估为 `no_candidate`：这是单次适配器实现修复，测试与 bootstrap 不是多个独立媒体实验，不产生模型效果或通用生成保证。没有新建或采纳 Learning Claim，也未刷新 RAG。本记录不代表媒体发布或 Production activation；成片尚待生成和真实审片。

## Window Handoff — 2026-10-26

本节取代上文及 active plan 的6.5秒商品卡方案作为当前下一步；历史方案保留。用户明确要求 `$next-window`，当前窗口停止实施，只准备续接。Overall goal 仍为先做好一条40–60秒颜生源广告，前三秒产品在场、钩子及人物声音/表情浮夸，完整口播“颜生源美白祛斑精华液”，剧情包含环境、问题、主动护理、受支持的功效表达与回扣。商户水印“栖澜百货商贸”低存在感、全片连续缓慢移动。

### Accepted And Rejected Evidence

- 用户只认可10秒诊断片 SHA `035cb943dcbc24631888e1448bce4523a9265e17eb3a02e1bb44178819a7cec1` 的语气和表情方向；不得推广为全部画面、字词、口型或新剪辑已验收。
- 已实际编码6.5秒 r6，SHA `00e50cdcb0f1330c1726ed6608ae51a1c6ecee10265ab7c489dd8432836bf5b9`。用户明确拒绝中途突然插入白底产品卡，精确记录 `motion-repair-001/source-use/H01-edited-r6-user-rejection.json`，SHA `62d7f59c214dda7452df1289e408412bcd949a08da076dcb6c68fddabc3f0634`。r6为叙事/剪辑 FAIL，不能拿 provisional Gate 的旧 NOT_EVALUATED 绕过此拒绝。
- raw 原生 Gate 仍 FAIL；原始 source、paid、fetch、失败历史不变。新 source trial 未执行 abandon 或 experience evaluation，最后已核对 Manifest rev14 / RUNNING / VALIDATE，paid ACCEPTED，不能为剪辑用途伪造原片 PASS。

### Uncommitted Renderer Fix

实际 r5 编码及 Chromium 检查发现，未来片段的 AI 标签提前渐入，造成两个 AI 标签重叠。原因是 `_graphic_keyframes` / `_graphic_layer_keyframes` 在 CSS 重复 offset 合并后，默认 linear 将片段之前的 opacity 0 插值到片段起点1。Parent 已在 `src/ai_video/production/_hyperframes_source.py` 添加窗口外 step-end、窗口内恢复 linear，保留指定入出动画。测试在 `tests/test_production_hyperframes.py`：真实 Chromium 五种入出组合 RED 5 FAIL → GREEN 5 PASS；相关 source/graphic 测试65 PASS、147 deselected，`git diff --check` PASS。新测试需显式 `P4_BROWSER_PATH`；未设置时 SKIP，不能声称 CI 自动执行。

r6实际编码已核查标签不再提前显示，但这不抵销用户的叙事拒绝。上述两个共享文件及本记录、active plan 的本轮追加仍未提交；接口修复 commit `a2cd778097e959b8d16d52391f9663c30bc7d463` 已在此前 push 并核验远端。当前 index 为空，其他窗口大量 dirty 保留，尤其 `.agent/harness/policy.yaml` 在该 commit 后又有他人改动，不能整文件 stage。尚无新完整工程验证或 renderer fix 的独立 Risk Gate 裁决；用户成片认可前不扩跑完整套件。

### Next One Thing And Remaining Work

首个可执行动作：只读打开 `hyperbole-001/post/edited-opener-001/work/r7/b-start-scale2-xm500-ym700.png` 和对应 `b-end-scale2-xm500-ym700.png`，结合 r6 拒绝记录确定新的同场景反应切法，再封存新意图后制作审片。

当前 `motion-repair-001/source-use/H01-edit-intent-003.json` SHA `523934d670a846b59c2fffd3b962fa43fa59195695c37c4df46efae0972ad39e` 计划 A原片2–4.5秒、B原片7–7.5秒租客特写、C原片7.5–10秒人物质问，共5.5秒。Parent 实际查看 B 的 scale2/x−500/y−700 静态起止预检，仍清楚露出侧脸转正脸及错误房屋透视，因此该裁切未通过，不能直接照此渲染。worker 已最终交回 ownership 并确认停止，无 r7 project/report/MP4 或活动渲染进程；review目录当前只有 r1–r6。`render_edited_opener.py` 的 r7 builder 已改为读取003但尚未执行，B crop 仍是不合格候选。`work/r7/` 保留 ASR、源帧及静态预览；runs 被 Git 忽略，不能因 status 不显示便认为这些文件未改动。

本地 Whisper 对照发现原片7.5–10秒缺“不是”，7–10秒保留完整“不是！你们在我脸上盖别墅啊？！”；整片 ASR 时间不是 canonical source clock。不能为遮坏画面删词或改变已认可语气。可探索女主画外音对应同场景正面租客反应，但这是未验证建议；如换 B 视频来源，须新意图 revision，不静默改003。产品继续前三秒现场可见，后续商品特写由主动拿瓶/护理动作引出，禁止再硬插商品卡。

开场 exact MP4 按新用途逐项检查、全 PASS 并交正常速度看听后，继续既有 H02/H03/hero：`motion-repair-001/continuation-prep-001/creative/H02-H03-draft.json` SHA `0b41f7251e9c5da370031bbecf3e4ec92adbb9d3e15cc7b2c5e7c1a4e81f55a0`。合同续住→主动拿瓶及完整品名→护理→多次日常护理与租客收拾→同合同“不续了”回扣；不暗示一滴即白、见效天数或百分比。每镜按实际末态选择硬首尾帧或 soft reference，不能把多模态参考冒充硬首尾帧。H02/H03尚未 submit，预算不得重置。

### Execution Boundaries

所有相对 run 路径前缀为 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/`。新 source 完整路径为 `hyperbole-001/motion-repair-001/runtime/A/trial-H01-motion/state/video-generation/fetch/files/f11aad0d4164edc9b61306ee0e672fac513e6fb97a61bff0aa96e9c2eb6246ef.mp4`；P4 worker 脚本为 `hyperbole-001/post/edited-opener-001/render_edited_opener.py`。Parent 拥有 source-use 文件与上述两个共享 renderer/test 文件；其他未知 dirty 需重新协调 ownership。

当前 durable paid16/A10/B3/C3，actual accepted generation15/A9/B3/C3，差额是历史 known-no-effect。总体18/A12及既有内部金额上界不重置，实际积分待结算。当前 `motion-repair-001/operator-window.json` 于2026-10-26T01:14:55.505033Z到期，新 submit 须先读 Provider Details 并按真实 baseline 有界续期。旧音义 UNKNOWN 保持停止，新 H01 的 audio_understand 为 runtime_required / KNOWN_NO_EFFECT / no POST；不为赶片重试未知请求。

仍由 CompositionSpec → ResolvedTimeline → HyperFrames 编排，禁止另造 timeline 或用 ffmpeg 直出成片。每镜 exact MP4 显式 project-local video-analysis Gate，不能以 lint/check/ASR 或别的片段人审替代。通过后继续已授权未完工作，不做完开场就结束；仅在真实阻断、审批边界或全片真实验收完成时停止。用户认可效果后完成适用工程验证、按 owned paths commit/push 并核验 SHA。

此 handoff 更新自动学习评估 `no_candidate`：CSS 问题为可复现实现缺陷，媒体参考试验有混杂变量，不能升级模型通用结论。没有新 paid/Provider/media 操作、额外测试或 RAG 刷新；publication=`NOT_PUBLISHED`，全片及新开场均未完成。

## R8 Editorial Execution — 2026-10-26

本节取代前述Window Handoff的“尚无新开场”当前状态；历史003及r6拒绝原样保留。用户明确要求继续实施，Parent核对AGENTS/SUBAGENTS、Git/远端main=`a2cd778097e959b8d16d52391f9663c30bc7d463`，确认原writer已交回，未触及其他窗口dirty或index。实际打开r7两张B首尾图后否决003的坏转头裁切。

Parent封存 `hyperbole-001/motion-repair-001/source-use/H01-edit-intent-004.json`，SHA `f4a9111bfe680a927059aa7599b2f998999fbdbbc7d942ccf2e6f67759f3d297`：A源2–4秒，B源4–4.5秒正面租客近景（scale3/x−1500/y−1650）承接原声7–7.5秒“不是”，C源7.5–10秒承接原问句余段；B排除女主口形，不露坏侧转、不定格、不硬插商品卡。原片FAIL、仅语气/表情的人审认可和旧UNKNOWN均不变。Builder运行前先保存原r7脚本，运行后保存r8脚本snapshot；均在 `post/edited-opener-001/work/r8/`，不依赖Git status记录ignored runs变更。

已实际执行 CompositionSpec → ResolvedTimeline → HyperFrames 0.7.103，生成exact r8：5.000秒/120帧/24fps/1080×1920/H.264/AAC48k双声道；7,904,766 bytes，SHA `97ec05544ec59bb88052663fde70ca33480a97ceeb2f7cd8c17cbe8968dd5a19`。报告 `hyperbole-001/post/edited-opener-001/review/r8/edited-opener-render-report.json`，lint/check零error/零warning；这是出片技术证据，不是完整Harness或人审。按50秒轨迹切前5秒，商户水印24px/opacity260连续慢移；AI标签未见提前重复。

显式project-local `video-analysis.video_analyze`核对exact编码，20帧/0.25秒采样、metadata和base/zh转写；原问句“不是”存在，转写“盖别墅”的同音错字不当作错读结论，ASR时间戳不是canonical clock。另查两刀47/48、59/60相邻帧与118/119末帧。Native只读 `reviewer_high` `/root/opener_concept_check`独立核对46–49/58–61/118–119及A末瓶体ROI15ml，sampled finding set为空；其连续动态、原速节奏、声音未实际听看，均保留NOT_EVALUATED。其OC-01确认旧5+15+15+4只有39秒，计划收束6秒暂排41秒；最终剪后仍须40–60秒。

`work/r8/mcp-analysis-metadata.json` 保存去base64的实际MCP metadata及无网audio_understand preview（network_calls=0）；`independent-limited-review.json`保留范围，`post-media-gate-provisional.json`诚实保留动态/听感/口型/原速接缝NOT_EVALUATED，next_shot_submit_allowed=false。没有重新执行旧UNKNOWN或为剪辑生成新表演。未以旧版局部人审批准本版。

用户可访问副本 `/home/reggie/电商/颜生源/广告试片/2026-10-26-浮夸重做/03-脸上盖别墅-5秒同场景反应-r8-待听看.mp4` 已复制并回读SHA一致，`work/r8/delivery-readback.json`绑定。已交本版正常速度带声审看并异步征询完整问句/口型/两刀自然度；截至记录没有该版人审回复，不能签收或提交后镜。后续 `motion-repair-001/continuation-prep-001/creative/H02-H03-draft-r2.json` 保留旧draft及SHA，指向004与r8候选frame119；候选末态未标accepted，不假称hard first-frame或已绑定生成。合同→主动拿瓶/完整品名→护理→多次日常护理/收拾→“不续了”→真实商品收束仍待制作。

实扫16个paid submit receipt：A10/B3/C3，accepted15/known_no_effect1，18/A12总上限下剩2；`work/r8/paid-count-readback.json`保存exact receipt列表/hash。此轮零新generation submit、零音义POST；实际历史积分待结算。旧operator window过期，新submit须按真实baseline有限续期，禁止复用旧permit/window/node假称新准入。

本轮仅出片必要编译/渲染/MCP与diff检查，没有扩跑工程套件。共享renderer/test的旧未提交修复保留；用户效果认可前不commit/push。record自动learning评估 `no_candidate`：这是同源剪辑的单次有界尝试，非独立模型效果对照；未新增Learning Claim/Policy/Gate采用或RAG刷新。全片仍未完成，publication=`NOT_PUBLISHED`。

## R8 Rejection And R10 Cut Repair — 2026-10-26

用户对r8明确反馈“3s这里突然切镜头是什么意思,一瞬间又切回来”，故r8叙事/节奏FAIL，取代上节“只待人审”的状态；最新原话绑定 `hyperbole-001/motion-repair-001/source-use/H01-edited-r8-user-rejection.json`，另有superseding user Gate，未倒改旧技术证据。Parent归因：为避开坏转头设计的0.5秒租客插镜未给足阅读时间，不能用几何/抽帧通过抵销用户拒绝。

新006 SHA `4f27d0d3bed3b173b300f9117cdc88aca871a2bfa460129a9f6a1220cf422d83` 采用A源2–3.5秒(1.5秒)、B源3.5–4.5秒(1秒)、C源7.5–10秒(2.5秒)，保留吃惊爆发与台面商品，再给租客完整近景承接“不是”，后续女主质问不切。原拟A1/B1.5的005未执行；只读concept reviewer提出其削弱A爆发的OC-02，Parent采纳1.5/1.0/2.5。OC-03“延长本身不证明节奏成立”仍须exact原速人审，不签PASS。005输入预览路径已被006预检替换，独立disposition诚实记其closure失效及3秒原图保留位置。

r9只做到project准备，没有render/MP4：现有REPLACE guard要求一条音轨覆盖B全窗口，两个相邻span不足。Parent未修改共享guard或另造混音时间线；r10经standard AudioImportRequest/Registry/bootstrap导入r8原canonical ResolvedTimeline/HyperFrames mixed PCM，完整5秒拆在新视觉切点，每段各一条连续音轨。原r9准备失败保留。

实际r10由CompositionSpec→ResolvedTimeline→HyperFrames0.7.103编码5秒/120帧/24fps/1080×1920，SHA `009bf5c48c83ad96d3ca8d94089d9a116824882df85084f489e5f0684abb524d`，7,880,526 bytes。报告 `hyperbole-001/post/edited-opener-001/review/r10/edited-opener-render-report.json` lint/check零error/零warning。显式video-analysis对exact MP4作20帧/0.25秒及ASR，另看35/36和59/60实际cut两侧。新旧MP4实际解码音频SHA均 `75e7b5def82446b5237f1666eb3ac3db8f889e3903064f6f6ec8d985e297535f`；只证明声音没有改变，不签聆听。证据归 `work/r10/mcp-analysis-metadata.json`、`audio-identity-check.json`、`post-media-gate-provisional.json`，原速节奏/口型/听审仍NOT_EVALUATED，后镜submit关闭。

副本 `/home/reggie/电商/颜生源/广告试片/2026-10-26-浮夸重做/04-脸上盖别墅-5秒反应停留-r10-待听看.mp4` 回读SHA一致。此轮零新paid generation/音义POST，不重试历史UNKNOWN，计数上限不变。用户效果认可前未commit/push；全片未完成、NOT_PUBLISHED。按record-ai-video-session更新原记录，distill-ai-video-learning=`no_candidate`，同源剪辑迭代不升级通用模型经验。

## Sharp Closeup And Resolution Correction — 2026-10-26

用户明确拒绝r10：“但是这个切近了之后也太模糊了”。延长三倍720p裁切并未修复清晰度。Parent最初自行选1080p，用户随后明确“不需要1080啊 720就可以”“你为什么会默认1080”；当前生成和交付改用720p，靠近景构图与对焦修复，不提高像素代替修复。r10的待审状态由最新拒绝取代，原10秒片仅语气/表情的局部认可不扩大。

原motion源已沿 `record_attempt_evaluation → abandon_video_generation` 封存FAIL；闭合凭证 `hyperbole-001/motion-repair-001/runtime/A/H01-motion-abandonment-closure.json` SHA `78933753b706ce14be384f124e476af3b1572e924a95e75aeeec55cd90971e2d`。paid/fetch/原片/声音保留，不补签未评项目。新增7.125/7.25/7.375边界证据确认，单靠切点无法同时保住“不是”及避开坏侧转；改为新租客近景承接原声，再接raw7.5–10安全正面段。独立概念复核OC-04要求C保留已检查的去半瓶构图，Parent采纳；其他文字概念未见新finding，实际媒体仍待验。

新15秒素材计划：同侧脸颊两租客清晰近景→同卧室中景才展开续租合同→女主浮夸挑眉、主动拿唯一棕瓶并说“还想续住？颜生源美白祛斑精华液，淡斑焕亮，匀净肤色。”→拿瓶引出的手部一滴护理。不开白底商品卡，不改真人肤色雀斑。完整方案仍包含多次日常护理/租客收拾/同合同“不续了”/真实商品收束，文本预算42秒。五张已实看图片分别约束场景、女主、boss、助手和商品，全部soft reference，无硬首尾帧承诺。

1080p scope `hyperbole-001/sharp-repair-001/` 没有submit、参考上传或付费消费。已start的REQUEST先记录not_submitted evaluation，再由 `close_unsubmitted_video_generation(reason=superseded_before_submit)` 在Manifest rev8关闭；`user-720-correction-closure.json`绑定，旧适配器另有STOP阻止提交。初次STOP中对closure seam缺口的误诊由该后续凭证纠正。零付费prepare失败及Project快照保留，不伪装Provider失败、不删历史。

当前执行 `hyperbole-001/sharp-repair-720-001/`：720p/15秒Seedance2.0 VIP五图R2V，profile SHA `d8d7530fc38c389dee713e7e1df3f708b2db421d4f5491830b80f5fa39b4da6b`；`operator-window-r2.json` SHA `3eef087a05f621931d41c8845be9662e74b1fe4ed4a08a07a85162a69ac378fc`，保留baseline16/A10/B3/C3、18/A12、9000/A6000与单次500CRD上界，零自动retry。窗口到04:22:28Z，expiry不阻断既有accepted的poll/fetch。

Goal binding verified；实际编译3751/4000 UTF-16、5PNG、无参考视频/音频、native audio。实际页面核对账户/项目/空节点PASS，request `bd450e850f85fd7a3c89443ae6e5b51e252369f462302866232f7753f2c27f8b`，只读报价210积分，非最终实扣。已沿canonical start/submit_once得到accepted，submission fingerprint `7d40599461a73e3fe704df55a76bb7acb2574c9c1dbf24aec2e884bfb943c939`。当前paid17/A11/B3/C3，accepted16/known_no_effect1；18/A12下剩1，实际积分待结算。

本checkpoint新MP4尚未fetch，媒体Gate、声音/口型/动态附着均NOT_EVALUATED，禁止H03 submit。旧音义UNKNOWN不重试。落盘后显式project-local video-analysis并交原速看听，不能用本次预检签验收。本轮未修改共享generation/state/reader，其他窗口dirty/index保留；用户效果认可前不扩跑工程套件或commit/push。全片未完成、NOT_PUBLISHED。自动learning=`no_candidate`：同源裁切及一个尚无媒体结果的新输入不支持通用质量结论。

## Final Bounded Media Results And Blocker — 2026-10-26

本节取代前节“未fetch/17次”当前状态。720p/15秒source已实际fetch，SHA `af5a06db82a97ebf30546eab5915f7281d77866fe08e42990046d64f423f1c31`。显式project-local video-analysis取61帧/0.25秒与本地base/zh转写：租客近景细节清楚，但嘴入画；合同到了女主手中，拿瓶后又举空手；护理前景与镜中持合同状态不一致。Gate FAIL，performance/sound NE；canonical evaluation/abandonment保留paid/fetch，`sharp-repair-720-001/raw15-abandonment-closure.json`，Manifest rev13。

Parent在同一失败主体分组内封存一次有界完整主体修复，而非在FAIL后另提交下一H03：Seedance2.5/720p/25秒、相同五张参考、两个无逐句时间戳的女主turn，合同始终给boss持有，护理要求离镜，晨夜两次护理之后才收拾/“不续了”。独立概念复核OC-05/06要求可辨不同使用场合及有信息职责的可调整产品收束，均写入新coverage，文本40.5秒。30秒原生报价600超单次500上界，未执行；25秒报价500在旧上界内。版本/时长选择同时核对current code/native quote及[官方2.5说明](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)，不把官方宣传当实际质量证明。

执行scope `hyperbole-001/body-repair-25s720-001/`；profile SHA `2179af9b669220e32b534e91c42696306f2931ca344259155832a1ba516d1beb`；window SHA `ef5a92ef6dcc487dcc9a7f61885e88b1e5f42e1329149e4647d6a4a802c0b420`，保留17/A11/B3/C3 baseline及18/A12、9000/A6000、单次500，零retry。实际request `43a9ff8d33baa7fe9c5e6a43573d387e35ae55c9b89ade743a75f00eddbeaa9d`，4679/15000 UTF16；native页面预检PASS。模型默认字段由canonical JimengProfile serializer省略，任务preflight显式恢复其已知2.5默认并核验三层request，不改profile bytes或隐式换模型。

唯一canonical submit accepted，fingerprint `bf9e5ff5d63fee13840b698345f1fa33f2b7e761719f0e3570344c7ac7ef6c71`；已fetch SHA `9b1b6c987463bfface25c0464218924079314b1deedb3efb6bfe3559ccb91880`，720×1280、容器25.057秒、601帧。显式MCP51帧/0.5秒及ASR发现仍有包装失真；raw Gate FAIL，performance/truth/sound NE。护理仍见模糊镜面，未满足sealed离镜构图；ASR提示“不续了”在10–11秒、19–24秒有重复文本，但可能含ASR幻觉，未听审不当作已确认的额外对白。已沿canonical evaluation/abandonment封存，`raw25-abandonment-closure.json`、Manifest rev13，quality rejection `e8cea48d80559a420e4ea9298ddaee5f46a689ddd9b080b60994055db494ae8a`；未补签或激活。

有限剪辑已实际得到6.5秒720p/24fps P4诊断版：`sharp-repair-720-001/post/review/cumulative-review-003/cumulative-review-render-report.json`，MP4 SHA `0dc52da4df8211f56687e4ca7d27dab6aa014971c08ee06c3d532d52a8ce3e6a`、5,599,755 bytes。CompositionSpec→ResolvedTimeline→HyperFrames0.7.103实际lint/check/render；MCP26帧/0.25秒与ASR、两刀59/60和95/96及154/155末帧另查，原“不是”和问句保留。原生macro0–1.5秒轻度构图排除嘴，非旧三倍模糊裁切；旧C去半瓶构图保留。时钟由mapper代码及exact ffprobe验证：开发预览使用delivery24fps wall-clock seek，旧源48/108/180/240帧PTS恰为2/4.5/7.5/10秒，不以avg14460/601猜时间；新macro第36帧PTS1.5秒。原声全为标准48k音频导入，A2–4.5、B6–7.5、C7.5–10，无新声音生成。技术证据不签正常速度听审。

独立read-only媒体复核新增MC-01：exact诊断片frame30/59的瓶签出现10ml及中文品名异常，真实商品PNG为15ml。Parent CONFIRMED，因此该剪辑也为FAIL，不因整瓶可见或近景清楚而通过。MC-01在新25秒首帧/0.5秒复现。MC-02指出25秒合同近景实际约19.5–21秒且已含卷回/收椅，不可前移到护理前冒充续租反应；Parent否决该候选重排。13–19秒日夜片段仍见雀斑，但不同光线不足以签肤色纹理不变，亦未认定明确一滴即白。原片仅语气/表情的认可仍不扩大。

已核验真实product.png本身为RGBA透明图；尝试用其在原房间局部修正包装，未新增图像生成或付费。仅task-local准备：r1缺目标root、r2 storyboard路径不符、r4/r5分别被pending-generated与repair-source绑定规则拒绝、r6未声明graphic layer而类型不符、r7缺exact AdCreativePlan identity；r3是上段唯一完成编码的版本，r4–r7没有新MP4。所有失败项目/脚本保留，未弱化guard、伪造AdCreativePlan或以“只改metadata”绕过物理跟踪/遮挡/光照能力边界。当前builder是阻断快照，不能当作可直接执行的通过方案；快照在 `post/review/current-builder-blocked-snapshot.py`。这些失败不证明HyperFrames一般不能叠图，只证明本次准备未满足当前canonical合同；完整的正确商品修复尚未完成。

用户可访问的诊断副本已明确更名 `/home/reggie/电商/颜生源/广告试片/2026-10-26-浮夸重做/05-720p清晰近景-6.5秒诊断-瓶签错误未通过.mp4`，SHA回读与原MP4一致，`delivery-rejection-update.json`保存MC-01及旧copy receipt。没有交作合格广告，也未取得本版正常速度人审。

当前真正停止边界：实扫18个durable paid receipts，A12/B3/C3，accepted17/历史known_no_effect1；总18/A12上限已耗尽，禁止新submit、重试或重置历史。`body-repair-25s720-001/final-budget-readback.json`保存全部path/hash与计数，`STOP-budget-exhausted.json`明确停止。本轮2次accepted视频原生报价210+500=710积分，非实际结算价；实扣仍UNKNOWN_PENDING_BILLING，1080p零submit/零费用。没有历史UNKNOWN重试或新audio_understand POST。

本轮只修改task-owned ignored run适配器/素材证据及本记录/计划，没有改共享generation/state/reader或其他窗口dirty。另一窗口在写generation_visual_revision时出现短暂SyntaxError，已通过工具直接协调其owner修复稳定后再prepare，未擅改他人文件。新增适配器py_compile、creative goal binding、真实P4与MCP只证明上述范围；没有新完整Harness PASS。用户效果尚未认可，故未commit/push；既有renderer/test修复仍未提交、其旧5 Chromium/65相关测试不是新完整验证。全片40–60秒尚未完成、未发布、未通过；原始失败、拒绝、费用及未验证项全部保留。record后自动learning评估仍 `no_candidate`：当前同项目未收敛修复没有已验证的可复用新方法，不创建或采用Skill/Policy/Gate claim。
