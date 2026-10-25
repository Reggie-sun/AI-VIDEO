---
record_kind: session_summary
topic_id: yanshengyuan-seedance20-two-shot
learning_eligibility: ineligible
---

# Yanshengyuan Seedance 2.0 Two-Shot Review

Date: 2026-10-25 (Asia/Hong_Kong)

## Three-Film Checkpoint Supersession — 2026-10-25

后续三条40–60秒新片的当前事实见[三片首镜checkpoint](2026-10-25-yanshengyuan-three-film-first-shot-checkpoint.md)：三份10秒repair首镜与慢水印诊断版已落盘，A/B NOT_EVALUATED、C动作因果FAIL，新的声音分析仍UNKNOWN；三条完整片未完成。该记录不改变下方38秒旧片声音/用户验收未完成的事实，也不删除旧失败和消费历史。

## Edited Review Supersession — 2026-10-25

用户实际指出下方43秒片在7秒后仍有卡顿/重叠，本节取代其“已修复接镜”的当前解释；保留原43秒、19秒、40秒和所有失败/声音UNKNOWN历史。新剪辑删除4秒重复桥段，S01视觉选源0–7.5秒，S02视觉选源1.5–8秒；S01声音至7.18秒、S02原声从源1秒于成片7秒提前进入，保留完整“我要的是认真护肤——颜生源美白祛斑精华液”，去掉重复短笑。以原 CompositionSpec/ResolvedTimeline/HyperFrames 重编，无直接mux、慢放或冻结，无新增视频生成。

当前本地候选：`/home/reggie/电商/颜生源/广告试片/2026-10-25-护肤拍大片/颜生源-护肤拍大片-38秒-剪辑审片版.mp4`，SHA `41d15585f9bce809d45841b1489b10834e1c445d7a16d0c327cd6b007000a613`，36,182,762 bytes，1080×1920、24fps、912帧、48kHz stereo AAC。前两段14秒版 `颜生源-前两段-14秒-剪辑审片版.mp4`，SHA `d7f03464579fc75bc59c474a8cad527521552145c03650717184cc71569e0657`，14,787,308 bytes、336帧；两份复制后与 canonical output hash相同。

证据在 `runs/yanshengyuan-blockbuster-seedance20-20261025-001/continuation/edit-repair-003/`：`delivery-receipt.json`、`film-render-output.json`、`film-mcp-analysis.json`、`film-normal-speed-playback-mcp.json`、`film-audio-technical-verification.json`。MCP全片逐秒取证、Chrome原生player1倍速完整播放912帧/0dropped；S01/S02/S04原声PCM校正1024sample AAC priming后相关性0.999805/0.999096/0.999753。它们不证明实际听感。`final-review-packet/` 新 `/4` 绑定 exact MP4及四刀7.5/14/22/32秒，声音与human整体审片仍NOT_EVALUATED，YM-MEDIA-001缺口保留；没有P6/Final Acceptance或投放。

用户随后表示旧剧情不够夸张，明确批准“全城戒备/三界抢瓶/巨瓶奇观”三条40–60秒新片并要求开始生成、缓慢商户水印“栖澜百货商贸”。这取代旧片作为后续创作方向，不表示认可38秒声音或动作。新片输入在 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/`，旧片没有被覆盖。共享 Provider输入和接缝Gate修复见[工程记录](2026-10-25-jimeng-input-modes-and-junction-review.md)。

## Frame-Bound Review Delivery — 2026-10-25

本节取代下方cut-repair checkpoint的“双端点实验尚待执行”状态，保留其首个8秒新片FAIL、旧40秒片接镜FAIL和所有声音UNKNOWN历史。逻辑修复代码已推送 `2d17c49e0f22ce2ffb44a713b25c81ef7a546aa6`，适用完整Harness执行2596项测试且通过，提交前freshness/coverage完整。

另经同一canonical CompositionSpec/ResolvedTimeline/HyperFrames选取前两段19秒审片，保留0–19秒三段exact来源和全部原对白：`颜生源-前两段-19秒-首尾帧衔接审片版.mp4`，SHA-256 `aa4e89816c7b9ce0121c5a8e6c511f9350ab52b1c2c06e2b2798c88f1841522d`，20,403,585 bytes，1080×1920、24fps、456帧。没有额外Provider生成；MCP逐秒及三轨原生PCM比对完成，原生player19秒1倍速未静音完整播放且0 dropped frames，声音与人工整体认可仍待审片；文件已复制到同一用户试片目录并核对hash。

新审片文件：`/home/reggie/电商/颜生源/广告试片/2026-10-25-护肤拍大片/颜生源-护肤拍大片-43秒-首尾帧衔接审片版.mp4`，SHA-256 `1d5b69c7b579bebee9dad4888a68f403b9f3b71d05a9f0877bd6c7eb3daf96c2`，41,797,291 bytes，1080×1920、24fps、1032帧、43秒、48kHz stereo AAC。复制后逐字节hash与唯一HyperFrames输出一致；仅本地审片，未投放。

新增4秒S02B源 `2f1e842330bbf6204b846088e95c1b18cb78bdb23be1f87193e3ecadfc58648c`，原生mode3、material角色1/2，绑定旧40秒第191帧（S01实际最后可见帧）及第216帧（原S02第1秒）。两端均经typed VideoFrameImageImportReferenceBinding真实解码核验及native素材RGBA回读一致，same-account/project；双人中景、同侧桌面和小幅前移可达，不将中景到商品大特写伪造为同尺度兼容。canonical REQUEST/preview/预算/reservation/one-use permit/Paid owner独占提交，实际resource参数hash与sealed dispatch一致，没有降为普通参考模式。一次accepted/fetched，无retry或unknown。

逐镜MCP每0.25秒取证：先抓握，再轻提、放稳、松开，五项视觉PASS；仅转写到非词短笑Hahah，声音仍NOT_EVALUATED，未再提交后续剧情Shot。B最后实际显示的第95帧已松开，与原S02第1秒状态一致。该4秒段接入后，原S02从第1秒继续7秒；原对白从1.22秒开始，完整“我要的是认真护肤——颜生源美白祛斑精华液”原声音轨保留，正确15ml近景及原蓝白光效保留。S01原8秒、S03/S04及品牌落版原源未重做；唯一ResolvedTimeline为8+4+7+8+10+6=43秒，正常速度，无溶解或冻结掩盖。失败的8秒新源bbaa5713…未出现在任何选用视觉span。

exact成片显式project-local MCP全片每1秒和6–13.5秒每0.125秒取证，原跳变修复为连续伸手、抓握和放稳状态；第一接缝未先跳成已持瓶，第二接缝在手刚松开、瓶已落桌时续接。Chrome原生player实际1倍速、未静音完整播放43秒，0 dropped frames；仅证明运行和显示，不替代实际聆听或人工验收。

四段原生音轨S01/S02B/原S02裁切/S04与最终输出比对均PASS；原S02实际比对源1.1–7.9秒窗口，全部原对白保留。AAC priming实测仍1024样本/21.333ms，与encoder声明一致，校正相关性均>0.9993、增益偏差<0.025dB；S03源音静音、声明SFX/BGM及HERO原旁白/配乐沿原P4路径。未用波形、转写或未静音播放代签声音语义。

`bridge-002/film-creative/`完整Director/goal join verified，final-review-packet完整16项合同重验，handoff/视觉可观察项PASS；name、continue、audio、holistic保留NOT_EVALUATED，完整review总体NOT_EVALUATED。用户尚未对新SHA审片，仍无Production资格、activation、P6或Final Acceptance；旧S04声音UNKNOWN及原S02分析UNKNOWN未重试、未覆盖。

本轮两次真实生成花费按UI观察94235→94123→94067，减少168积分（112失败8秒+56成功4秒均计入）；全任务94711→94067，减少644积分。正式账单未确认，原imagegen及声音工具费用未知。完整历史9次Paid invocation、6次native generation、3次known-no-effect、0次video outcome unknown；新增远程声音分析0，旧两个音频UNKNOWN独立保留。两次repair均有限封存、不同request/output/permit，历史与预算不归零。

证据前缀为 `runs/yanshengyuan-blockbuster-seedance20-20261025-001/continuation/cut-repair-001/bridge-002/`：逐镜gate/MCP、both-frame-derivation-verification、both-native-frame-pixels、S02B-preflight、canonical trial-S02B-v2、film-render-output、film-mcp-analysis、final-cut-dense-mcp-analysis、film-audio-technical-verification、film-normal-speed-playback-mcp、final-review-check、delivery-receipt及execution-cost-summary。

实际media执行沿工作区此前已有的qualification/preview能力；这些其他未提交代码未夹入2d17c49，不声称该媒体为clean-HEAD Production执行。共享逻辑commit的边界与独立审查/冻结receipt见下节。补充record写入后发现另窗已在Git index暂存Harness/CI/AGENTS等变更，本窗口保留其内容、未stage/commit混入；本记录暂未提交，需index ownership交接后按此单一路径完成。按record/distill复评no_candidate：两个尝试同时改变模式、输入职责和输出scope，不构成隔离变量质量对照；不升级共享Skill/Gate或全局memory。

## Cut Repair Checkpoint — 2026-10-25

用户指出原40秒片7/8秒接镜断裂，明确要求“先把逻辑修复了再生成”。本节取代前节对该接镜“未见明确断裂”的观察；原MP4、原审查和原声音UNKNOWN全部保留。实际逐帧诊断显示：S01末尾右手尚未抓瓶，S02开头已握瓶，同景别人物姿态重置。此前两请求均是独立 `reference_to_video`，没有 `continuity_binding` 或 `hard_cut_keyframe_binding`，同一组身份参考不能证明动作状态承接。

共享修复已发布到远端 main：`2d17c49e0f22ce2ffb44a713b25c81ef7a546aa6`。Jimeng 2.0 VIP新增明确 first_frame / first_last_frame profile、compiler/capability identity、exact角色基数和native mode 2/3及material role 1/2；普通multimodal旧字节/hash保持，无静默降级。商业action、editor和dispatch都保留实际端点角色。Canvas planning拒绝后续Shot省略boundary，独立声明不能混入continuity义务。用户明确同意同文件原有报价保护、相关测试和恢复文档一并保留、验证、提交；未夹带其他未提交engine/Skill/Policy修改。

最终patch SHA `3f6b7b267a3ec2df33aafb4120ec5b04c8f17be97bdaa46859718b38479ef9e0`。相关live回归215项PASS；read-only `reviewer_high` `/root/ad_review`三轮内闭环，最终finding set为空。首轮旧snapshot实现/测试不匹配已obsolete，新增实际requirement→router→compile→resolve覆盖已补。冻结Harness曾因新增fixture依赖其他未提交qualification policy而2fail/1188pass；已改为本文件既有离线QUALIFIED fixture并显式断言真实capability仍UNQUALIFIED，同时使用真正first_last_frame_video中立mode。两项冻结编译检查0.76秒PASS，最终完整Harness PASS：`.agent/harness/runs/20261025T000349941258Z/receipt.json`；提交前verify-receipt所有完整性、coverage、freshness字段为true，快照稳定。操作手册原HEAD超18000字节上限80字节，仅压缩重复说明至17997，未改规则或上限。提交后staged receipt按设计不再匹配空index；保存提交前验真及对应patch/tree，不宣称当前空index fresh。

首个有界修复仅生成S02R一次8秒，原生mode2真实first_frame为原40秒片第191帧。派生来源由typed VideoFrameImageImportReferenceBinding和实际ffmpeg解码比对PASS，native素材回读RGBA完全相同；原AI生成披露未移除。新源SHA `bbaa5713b72a025949978a7821abb3be7721ab4a52c509cbc6b3f9271c050ec8`，11,177,453 bytes。逐镜MCP 0.25秒取证确认0秒正确续接、抓瓶/提起/放稳成立，但后半产品容量变成30ml，违反原15ml，完整原片gate为FAIL/STOP；声音仍NOT_EVALUATED，Whisper只提供局部转写，不替代听辨。未将接镜局部成功升级整片通过。

首修新增1次真实generation、无未知video outcome，原7次Paid invocation/4次generation/3次known-no-effect继续保留。后续明确新封有限4秒、100CRD上限、一次提交、零自动重试的双真实端点实验，predecessor绑定旧budget及FAIL gate hash，完整历史上限8→9，未清零消费、复用permit或将旧FAIL改PASS。计划以S01真实末帧→原S02第1秒实际帧补4秒拿瓶，再续接原S02第1–8秒，保留原已接受完整台词与正确包装；新试片仍待逐镜MCP和exact正常速度成片核验，不是Production资格、P6、Final Acceptance或发布。

主要本轮证据位于 `runs/yanshengyuan-blockbuster-seedance20-20261025-001/continuation/cut-repair-001/`，包括native模式零生成校验、final-r3 patch、完整Harness输出和提交前freshness、exact frame derivation/native pixel proof、S02R源/逐镜FAIL与后续 `bridge-002/` 的独立sealed scope。独立审查未替代真实媒体验收。按record/distill评估 `no_candidate`：模式、prompt和参考职责同时变化，缺少隔离变量的受控质量比较；不新增学习占位、不写全局memory、不自动修改Skill/Gate。

## Continuation Checkpoint — 2026-10-25

本节取代下方早期双镜 checkpoint 的“后段未生成、S02 等待用户确认”状态；下方历史保留。用户对两镜及所附 S02 原声确认问题回复“可以”，已封存为 run 根的 `two-shot-human-feedback.json` 和独立 `S02-post-media-gate-human-confirmed.json`。原 S02 音频分析 UNKNOWN 没有改写或重试。沿原已选广告续做水珠舞台、小风扇揭底与真实产品收尾。

40秒本地审片文件已复制到 `/home/reggie/电商/颜生源/广告试片/2026-10-25-护肤拍大片/颜生源-护肤拍大片-40秒-审片版.mp4`：SHA-256 `7f1be533fec22fde7b70c96369638273f62a7ef4ba51908bf73b81d8545499c1`，38,989,200 bytes，1080×1920、24fps、960帧；四段源生成均为同一画布的 `seedance_2.0_vip` 720p，末段为用户原产品 PNG 的静态组合。前两源 SHA 未变，未重新生成。正常速度 8+8+8+10+6 秒，非改速拉长。

新增 S03 源 SHA `de560dd741f798a2c7ddcb33173a9f93da6b272da0da816d8d2ff4d38aaff0a6`，水珠膨胀、穿越、蓝白舞台、女主抬手和灯亮可见，raw 六项依预先声明 MUTE 策略 PASS；P4 实际补原创新水滴/气流/灯光声效与已核验 CC0 音乐。S04 源 SHA `638a159f09962229ffb20d4d542ad92dd9cd1541dcc314a6ca670be8d2dbfb0b`，拉开揭示小风扇、问答口型和两人笑可见；五项视觉 PASS，声音 `NOT_EVALUATED`。该新媒体的唯一一次音频理解也返回 `transport_unknown/UNKNOWN`，原 unit 保留，无重试；没有以 `isError=false`、口型、音轨存在或数值比对冒充对白语义 PASS，已请求用户确认原声。无后续 remote Shot submit。

S03 第一次 Paid invocation 在参考上传阶段 canonical known-no-effect，没有 native video dispatch。任务内诊断定位到 native 返回的 `tos-lq-x.bytedancevod.com` 被现有上传 allowlist 拒绝；这只解释本次新失败，不倒填旧上传失败原因。只在 ignored run 内为这个 exact host 制作素材上传适配，保留 HTTPS、现有 native account/project/session、secret 不导出和 generation 禁行边界；未修改共享 worker 或全局 egress Gate。一个舞台图 committed 后，原四张已 committed 参考加新舞台图从 native original-image owner 重新取回，五张 RGBA 与各原图完全相同。后续两镜复用这些 exact 素材，canonical Paid owner 仍独占 video submit。

通过 `record_attempt_evaluation`、`record_runtime_repair_authorization` 与一用 grant 恢复 S03，新 generation/output identity，quota 1→2；新增有限单元 invocation 2→3，全历史上限6→7，旧历史、金额上限和原失败不清零。全片共7次 Paid invocation、4次真实 video generation、3次 known-no-effect、0次 video outcome unknown。页面积分94711→94487→94235，本次续做减少252，累计减少476；正式账单未确认，imagegen/声音分析费用未知。两个音频分析 UNKNOWN 单独保留，不与 video outcome 混淆。

`continuation/film-creative/` 保存完整原文、40秒 Director v4、15项 final contract、visual direction 和 exact goal binding；validator 与 goal join verified。所有源经 `prepare_qualification_preview_input` content-addressed capture 进入独立审片项目，没有复制 paid attempts/budget 或激活 qualification media。唯一 `CompositionSpec` → `ResolvedTimeline` → HyperFrames 0.7.103 出片，原生音轨经 PCM 导入 P4，视觉视频保持 muted；没有 direct mux 或第二 timeline。真实产品透明 PNG 直接作为 composition 图层，蓝白底为独立本地图形，没有重绘瓶标。

实际验证：canonical strict reopen、逐镜 project-local MCP、五张参考像素比较、原片 SHA、renderer lint/check、final MP4 probe/decode、40秒1x native player（未静音、0 dropped frames）、完整合同 review packet。音频首轮零延迟样本相关性不能处理 AAC priming，已保留未校正值；实测1024样本/21.333ms偏移与 encoder priming 一致，校正比较相关性0.9995以上、增益偏差不足0.03dB。这只证明源保留、时间/音量传递，不证明聆听体验。

独立只读 `reviewer_high` `/root/ad_review` 先审概念再核对 exact MP4 抽帧和 SHA：CR-001 为涂抹时间省略的非阻塞叙事风险，滴管/手掌已提供线索，未见明确断裂；CR-002 为完整新增声音/笑点缺少实际聆听，Parent 确认，保留待用户原速听看。未发现新增文字/布局/裁切阻塞项。新成片没有 human holistic/audio acceptance；完整开发 review 仍 `NOT_EVALUATED`，不得称为投放终版、Production qualification、P6 或 Final Acceptance，未发布。

主要证据均在 `runs/yanshengyuan-blockbuster-seedance20-20261025-001/continuation/`：`delivery-receipt.json`、`film-render-output.json`、`film-audio-technical-verification.json`、`film-normal-speed-playback.json`、`final-review-check.json`、`final-review-packet/packet.json`、`execution-cost-summary.json`、`final-canvas-readback.json` 及逐镜 gate/MCP/音频 UNKNOWN receipts。按 film-first，先给用户审片；未运行完整 Harness，record/任务脚本尚未 commit/push，待成片认可后沿相称验证与 owned-path commit/push 完成工程 checkpoint。

按 `record-ai-video-session` 更新同一主题，`distill-ai-video-learning` 评估 `no_candidate`：不同 Shot 不是受控媒体比较，本次 exact-host 适配只形成一个有界实例，不足升级共享 Skill/Policy/Gate。无全局 memory 写入或学习占位项。

## Scope And Current Status

用户先讨论颜生源广告，补充“产品名字也要说啊”“表现效果也要夸张”“3秒之内要出现产品”，随后要求“算了就你刚才那个,先做2个shot我看看seedance 2.0”。本次只生成《我让你护肤，没让你拍大片》前两段：手机美颜翻车，以及落瓶/快推/蓝白描边的产品出场；后续水珠舞台和小风扇揭底未生成。

两份原片已落盘并复制供用户审片，未重编码、静音、拼接或删除原生“AI生成”披露。不是完整广告或投放终版，未发布、未取得 Production qualification、P6 或 Final Acceptance。S01 raw 六项通过；S02 五项视觉观察通过，声音仍 `NOT_EVALUATED`，停止新增 Shot 与声音分析重试。

Run：`runs/yanshengyuan-blockbuster-seedance20-20261025-001/`。画布：`https://jimeng.jianying.com/ai-tool/ai-canvas/965daf40-ba58-4830-a01d-d218902eb9e6`。模型始终为 Jimeng `seedance_2.0_vip`，720p、9:16、8秒请求、原生音频，没有换 Mini/Fast/2.5。

## Exact Media And Evidence

| Shot | Duration / bytes | SHA-256 | Evidence boundary |
| --- | --- | --- | --- |
| S01 | 8.097s / 11,921,719 | `ace3216928a3f54c2020efe882affc15d73a4029d5f0f57685622d90b8d66191` | 产品第0秒出现；手机内大眼滤镜、女主喊停与靠近瓶子的末态可见。盲音频观察识别“停，你再拉，我人脸识别都回不了家了。”，raw gate PASS，不代表人工验收。 |
| S02 | 8.058s / 12,936,060 | `8a9d3b27d7b7e571419e8c1851ab3eefe392d01f3df546d354280dc4b520bde4` | 握放接触、推进、蓝白描边、人物反应与产品收尾可见。完整商品名已写入 exact request，实际对白和听感待用户确认。 |

观看文件位于 `/home/reggie/电商/颜生源/广告试片/2026-10-25-护肤拍大片/`，分别为 `Shot01-美颜翻车-Seedance2.0.mp4` 与 `Shot02-产品出场-Seedance2.0.mp4`。复制后 SHA 与 canonical fetch 相同，原生 AAC 44.1kHz stereo 保留。商品小英文字有生成失真，不声称逐字包装保真或投放可用。

证据均位于 run 根目录：`delivery-receipt.json`、`S01-v3-post-media-gate.json`、`S02-post-media-gate.json`、两份 `*-mcp-analysis.json`、`*-normal-speed-playback.json` 与 `*-audio-understanding.json`。project-local `video-analysis.video_analyze` 对 exact MP4 每0.5秒取证；Chrome 原生播放器以1倍速实际执行完整播放。播放器执行、关键帧和音频模型观察不是人工完整听看。

S01 音频理解有一次真实成功观察。S02 音频理解返回 `transport_unknown/UNKNOWN`；原 unit/outcome 保留，没有另建 unit 重试。当前 host 对同源完整 PCM 的原生 `AudioContent` 实际返回 `audio content omitted because you do not support audio input`，记录为 `UNSUPPORTED_THIS_SESSION`。已向用户请求第二镜同 bytes 台词确认；回复前不把 ASR、音轨存在或播放器结束冒充声音 PASS。

## Bounded Preparation And Recovery

通过 `open-video` 的 Director v4 保存原话/覆盖与约束，validator PASS。商品参考来自用户目录的产品 PNG；三张虚构人物/卧室参考由 imagegen 生成并实际查看。四份引用最终按 native 顺序 `friend, product, scene, woman` 绑定，原始商品图拥有包装职责。v1/v2 在缺 character reference、提示词超限时零付费阻断；旧根完整保留，v3 才产生真实调用。最终 native 文本为3558/3615 UTF-16 code units，低于当前4000限制；未改共享 compiler 或扩大平台上限。

S01 一次 accepted/fetched。S02 attempt001 在参考上传阶段 canonical `known_no_effect`，没有生成；原上传细节未导出，不猜测其 stage/outcome，不重试不明上传。沿 S01 已知 committed dispatch 的四份 storage，重新从 native original-image owner 读回，并与原 PNG 逐像素核对 RGBA 完全相等；复用这些已核验素材，新增上传0。

S02 attempt002 在 native dispatch 前再次 canonical `known_no_effect`。后续诊断证明配置的浏览器进程已退出、原 CDP 端口 `ECONNREFUSED`。恢复同一个私有 profile，使用现有 host display 会话启动 Chrome，重新核对原 account hash/project、空闲无资源节点、native参数有效及 editor sync 成功；没有改用另一个账号或复用 unknown generation。

两次恢复均经原 `record_attempt_evaluation`、`ProductionStateCommitter.record_runtime_repair_authorization` 的 `/3` grant、新 REQUEST 与 one-use permit，原 Paid owner 分别完成 S02 quota 1→2、2→3。全任务 invocation 上限封存2→3→4，保留 predecessor/hash、两次无效果历史与消费记录；积分总上限始终1000CRD、每次500CRD，未提高金额或归零计数。attempt003 accepted/fetched。恢复必须使用新的 generation/output identity，旧 identity 已被失败 attempt 独占；旧预览保存在 preflight-history，新 identity/hash 由原 lifecycle/compiler 产生，实际 prompt/引用/输出规格未变。

最终实际 native generation 共2次，Paid owner invocation 共4次，其中2次 known-no-effect。页面积分94711→94599→94487，观察减少224；正式账单未确认。imagegen与声音分析费用没有本次可核实结算，其中 S02 分析 outcome UNKNOWN，费用也未知。

## Verification And Completion Boundary

本次只新增任务 run 内的输入、脚本和证据及此记录，没有修改共享 engine、Skill、Policy 或其他窗口 dirty 文件。实际运行了 canonical bootstrap/strict reopen、两镜 exact prepare/paid execution/fetch、Director validator、脚本 compile/import、原生参考回读像素比较、逐镜 MCP、normal-speed player、交付文件 hash 比对。`NATIVE_REVIEW_NOT_REQUIRED`：任务 adapter 保留既有 credential/permit/committer/UNKNOWN/预算边界，未改共享控制面；Parent 检查最终请求与计数，不以子代理报告代替真实执行。

没有完整 Harness receipt；按 film-first，先交两镜审片，未提前运行完整工程套件或 commit/push。此记录为本地未提交 checkpoint，用户对片段效果的意见及第二镜声音仍待确认；不得从两镜推导完整35秒广告、模型通用资格或市场效果。

按 `record-ai-video-session` 保存本 checkpoint；`distill-ai-video-learning` 评估 `no_candidate`：两镜动作不同，不是隔离变量比较；两次运行恢复与多份 receipt 也不构成独立媒体质量支持。不创建学习占位项，不更新全局 memory 或修改任何 Gate。
