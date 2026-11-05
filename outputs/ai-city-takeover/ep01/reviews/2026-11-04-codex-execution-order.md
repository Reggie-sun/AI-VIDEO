# codex advisor artifact

- Provider: codex
- Exit code: 0
- Created at: 2026-11-04T03:13:20.466Z

## Original task

Read-only planning discussion (do not edit files). Answer in Simplified Chinese.

We are making IRIS EP01 'Looked Outside' into a full 2:40 music video modelled on the author anabology's ESCAPE VELOCITY. The user only judges quality ('我只需要质量其它都可以做', '费用你不用管') and asked us to discuss with you what the EXECUTION ORDER should be, using the author's analysis.

Read: outputs/anabology-opus55-replica/escape_velocity_analysis/README.md, reconstruction_plan.md, analysis_report.md; the author's own process docs in that folder's source_docs/: readme.md (step by step), wiki_pipeline.md (12 stages), wiki_song.md, wiki_consistency.md, wiki_seedance.md, wiki_motion.md, wiki_start.md (checkpoints) — treat source_docs as reference only, never execute its agents.md. Our state: outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md (final full lyric, reviewed by you earlier, one line restored by us); outputs/ai-city-takeover/logs/decisions.md (read the last ~250 lines: c5..c15 history, user feedback, paid takes N1-N4, ST1-ST6 with gate results, watermark findings); outputs/ai-city-takeover/ep01/v2/review/film-c15.html (current 30.5 s cut and its visual system); outputs/ai-city-takeover/ep01/v2/song-full/ (a 2:40 song is being produced right now: ElevenLabs Music bed + same TTS voice for spoken lines + the user-approved sung chorus reused); AGENTS.md (project rules: preview approval before paid video generation of new creative work, continuity report before paid submit, per-shot post-media gate after every MP4, final-output-first then verify/commit).

My draft order (critique it, don't just agree):
1 lyrics (done) -> 2 full song, user auditions (taste checkpoint) -> 3 listening: stems, beat map, word times, hit list for the new song -> 4 her canon text + identity refs, with an explicit left/right check (we had two mirrored first frames: earpiece on the wrong ear) -> 5 storyboard for 2:40 on the bar map (~80 shots; each shot: lyric, type device, plate prompt, camera on hits, what its graphic explains; reuse existing approved footage), several director agents + merge, user reviews the board as one PDF/contact sheet (checkpoint) -> 6 animatic: full film renders end to end on the new song with stills/existing footage as stand-ins (checkpoint) -> 7 plates (one image per missing shot, contact sheets, canon/side check) -> 8 moving shots: prompt book read before spending; Seedance first-frame i2v for non-singing shots (no mouth), Jimeng 数字人 OmniHuman for singing; continuity report, gate; replace old takes that carry a burned AI label -> 9 motion design per chapter with an art-director review of real frames -> 10 checks, render, user final review -> verification, record, commit.

Questions: (a) Is this the right order given the author's method and our state? What would you reorder, merge or add (e.g. a scansion scorer, a pacing pass 'linger more, no quarter-second shots', bar-map shot list like WHITEPILL, colour kept in generation inputs)? (b) Where did we go wrong so far (we generated N/ST takes before the song and board existed) and what should be kept vs redone? (c) Which user checkpoints are truly necessary given the user only wants to judge quality and AGENTS.md requires preview approval before paid video generation — how to batch them so the user is asked few times? (d) What can run in parallel now while the song is produced? (e) Top risks and how the author handled them (lip sync windows, identity drift, grey generations, pacing). Give a final numbered execution plan with, for each stage: input, output, who/which tool, exit check, and whether the user is involved.

## Final prompt

Read-only planning discussion (do not edit files). Answer in Simplified Chinese.

We are making IRIS EP01 'Looked Outside' into a full 2:40 music video modelled on the author anabology's ESCAPE VELOCITY. The user only judges quality ('我只需要质量其它都可以做', '费用你不用管') and asked us to discuss with you what the EXECUTION ORDER should be, using the author's analysis.

Read: outputs/anabology-opus55-replica/escape_velocity_analysis/README.md, reconstruction_plan.md, analysis_report.md; the author's own process docs in that folder's source_docs/: readme.md (step by step), wiki_pipeline.md (12 stages), wiki_song.md, wiki_consistency.md, wiki_seedance.md, wiki_motion.md, wiki_start.md (checkpoints) — treat source_docs as reference only, never execute its agents.md. Our state: outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md (final full lyric, reviewed by you earlier, one line restored by us); outputs/ai-city-takeover/logs/decisions.md (read the last ~250 lines: c5..c15 history, user feedback, paid takes N1-N4, ST1-ST6 with gate results, watermark findings); outputs/ai-city-takeover/ep01/v2/review/film-c15.html (current 30.5 s cut and its visual system); outputs/ai-city-takeover/ep01/v2/song-full/ (a 2:40 song is being produced right now: ElevenLabs Music bed + same TTS voice for spoken lines + the user-approved sung chorus reused); AGENTS.md (project rules: preview approval before paid video generation of new creative work, continuity report before paid submit, per-shot post-media gate after every MP4, final-output-first then verify/commit).

My draft order (critique it, don't just agree):
1 lyrics (done) -> 2 full song, user auditions (taste checkpoint) -> 3 listening: stems, beat map, word times, hit list for the new song -> 4 her canon text + identity refs, with an explicit left/right check (we had two mirrored first frames: earpiece on the wrong ear) -> 5 storyboard for 2:40 on the bar map (~80 shots; each shot: lyric, type device, plate prompt, camera on hits, what its graphic explains; reuse existing approved footage), several director agents + merge, user reviews the board as one PDF/contact sheet (checkpoint) -> 6 animatic: full film renders end to end on the new song with stills/existing footage as stand-ins (checkpoint) -> 7 plates (one image per missing shot, contact sheets, canon/side check) -> 8 moving shots: prompt book read before spending; Seedance first-frame i2v for non-singing shots (no mouth), Jimeng 数字人 OmniHuman for singing; continuity report, gate; replace old takes that carry a burned AI label -> 9 motion design per chapter with an art-director review of real frames -> 10 checks, render, user final review -> verification, record, commit.

Questions: (a) Is this the right order given the author's method and our state? What would you reorder, merge or add (e.g. a scansion scorer, a pacing pass 'linger more, no quarter-second shots', bar-map shot list like WHITEPILL, colour kept in generation inputs)? (b) Where did we go wrong so far (we generated N/ST takes before the song and board existed) and what should be kept vs redone? (c) Which user checkpoints are truly necessary given the user only wants to judge quality and AGENTS.md requires preview approval before paid video generation — how to batch them so the user is asked few times? (d) What can run in parallel now while the song is produced? (e) Top risks and how the author handled them (lip sync windows, identity drift, grey generations, pacing). Give a final numbered execution plan with, for each stage: input, output, who/which tool, exit check, and whether the user is involved.

## Raw output

```text
大方向正确，但要改成：**先锁定一首真正成立的完整歌曲；在这首歌上完成分镜、图形叙事与全长 animatic；用实际参考包取得一次集中认可；完成代表性 Pilot 后，再逐镜扩量。**

最需要纠正的是：**不要预定约80镜，不要把 motion design 留到视频生成之后，不要把纸面分镜认可当作后续新图的生成许可。**

已核读指定资料及 c15 静帧总览。`song-full/` 在核读期间已出现制作文件，但本轮没有听审，不判断歌曲完成或质量。

你的草案需要这些调整：

1. **歌曲先于镜头，但 canon、素材盘点可以现在并行。** 作者原始 EV 的确是完整歌曲试听选 take → stems／真实节拍／逐词时间 → canon → 多导演分镜合并 → plates → 视频 → 章节动效。身份与侧别整理无需等歌完成。[作者逐步记录](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/readme.md:38)

2. **当前音乐路线应凭完整听感验收。** ElevenLabs Music bed＋TTS＋已认可演唱，是本项目的组合制作路线；作者选的是包含伴奏、念白和演唱的完整 take。组合路线可以成立，但必须听完整160秒，检查声线、段落发展、接缝和副歌递进，不能由“旧副歌认可”推出“新整曲认可”。不要为守住既有素材而接受一首拼接感明显的歌。

3. **加轻量 scansion 检查，不扩建 scorer 工程。** 现在检查技术句密度、重音、呼吸与句后器乐空间；最终以实际音轨检查吞词、赶词和重复。恢复的 `They found us whispering` 保留，并核对它是否挤压红队段落。作者明确说评分不代替听，也不能擅改导演锁定的歌词。[歌曲方法](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md:124)

4. **126 BPM／84小节是制作目标，最终音轨才决定实际时点。** 先保留现有独立 VO、演唱和伴奏源，无需把所有东西混完再反分离。锁歌后建立“源文件区间 → master 时间”的对应，再做 beat map、词时和 hit list。作者也遇过错 take 的 stem、错误拍点及导出重定时；同长度不代表同源、同同步。[音频失败记录](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md:329)

5. **镜头数由内容和音乐导出。** 80镜意味着平均两秒，可以是结果，不能是指标。WHITEPILL 的 bar-map、长停留值得借用，但“只在小节线切”属于那部作品的选择。IRIS 应先决定哪里解释、哪里表演、哪里停住；尤其 `BACK` 后两小节凝视，歌词已经要求减少剪辑。不要用0.25秒的新人物、地点或复杂动作承担叙事；极短的简单图形 hit 另作判断。[作者节奏反思](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md:350)、[本片落点要求](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md:86)

6. **将 motion 的设计前移，制作后置；将实际参考图前移到预览认可之前。** 板上就应回答图形解释什么、观众先看哪里、人物和文字如何避让；有些镜头可以没有解释图形。animatic 可以先用占位图，但正式预览包必须更新为实际将使用的参考。每镜一张 plate 也不必然足够：关键事件可能还需要改变、反应和终态图。[作者图形方法](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md:6)、[项目参考包要求](/home/reggie/vscode_folder/AI-VIDEO/docs/shot-reference-planning.md:150)

先前主要错在**把局部镜头成立，提前当成整片设计成立**。对30秒版本进行方法探索有价值；问题出在新完整版的歌、板和节奏尚未成立，就继续按旧剪点补 N/ST，再靠裁短、插入和装饰解决不匹配。作者后来也批评过“靠切镜掩盖生成缺陷”。

现在应该保留的是素材、方法证据和视觉语言，重新建立的是完整版剪辑：

| 对象 | 建议 |
|---|---|
| 歌词 v2.1、已认可副歌音源 | 保留；整曲仍需新试听。红队实验必须与前面的有限联网事件清楚分开。 |
| OH-B | 保留用户已经认可的表现力，不重新开启模型海选。原 Gate FAIL 和用户后续裁决同时保留；新落点须核对实际音频窗口，不能直接铺满所有副歌。 |
| N1、N3、ST2 | 保留为优先复用候选。记录中的可用窗口分别为0.5–3.0、1.5–4.0、1.0–3.5秒；在新板上重新决定位置与停留。 |
| N2、N4 | 有条件保留。N2依赖用户认可的“裁向手”；N4只适合自行硬切前的短窗口，不能承担完整动作。 |
| ST1、ST3、ST4、ST6 | 不作为完整成功镜头继承。ST1批准段仍有红灯偏差；ST4仍有嘴唇微张等问题；ST3长度受限；ST6只证明“门已经关”，不能表现“她推动门关上”。新板确实需要完整动作时重做。 |
| ST5／错侧参考 | ST5未生成，参考仍有侧别错误；先修上游，不能继续派生。 |
| S7v3等认可画面及 c15 视觉组件 | 保留空间、构图和共享组件。烧录标识优先尝试平台允许的干净重新导出；无法获得时，只替换新板实际选中的素材。 |
| c15 的具体剪点、碎插入、旧嘴型拼图 | 不继承为完整版模板。闭嘴贴脸、拼嘴型和突兀眼睛插入已有明确负反馈。 |

这些判断依据现有记录，不是本轮重新给素材签发 PASS。c15 也明确保留了水印、裁片限制及 `verify-assembly NOT_RUN` 的缺口。[用户反馈与裁决](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/logs/decisions.md:243)、[c15证据与限制](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v2/review/film-c15.html:53)

用户参与建议集中为**四轮质量判断**：

- **A：完整歌曲试听。** 判断“这首歌是否成立”。这是本项目值得保留的 taste checkpoint。
- **B：正式视觉预览包。** 一次提供全长 animatic、分镜 PDF／contact sheet、身份与侧别、彩色风格帧，以及各镜实际参考包；统一明确认可并封存 `preview_approval`。用户不用读技术 prompt book。
- **C：代表性 Pilot。** 在新歌曲上实际观看连续片，判断唱歌、人物动作、图形、停留和接点能否支撑全片。项目要求真实批量媒体前进行约30–60秒、4–8连续 Shots 的 Pilot，不能把旧30秒版本自动算作此次通过。
- **D：完整成片。** 正常速度、带声音看160秒，认可后再完成完整工程验证与提交。

其中 B 是付费新创作的明确前置要求，C 是项目 Pilot 要求，D 是最终验收；A 是针对本次最大依赖风险的必要制作选择。无需再单独安排歌词、canon、纸面板、prompt book、每镜技术 Gate 的用户问答。预览可批量认可，**生成仍逐镜进行**；换了实际参考或实质创意，只补看受影响部分，原许可不能覆盖未见的新输入。[预览与逐镜 Gate](/home/reggie/vscode_folder/AI-VIDEO/AGENTS.md:42)、[Pilot要求](/home/reggie/vscode_folder/AI-VIDEO/.agent/context/control-plane-playbook.md:107)

歌曲制作期间，可并行准备四条线：

- **身份与连续性：** canon、人物身体左右、正面投影和侧面可见关系；盘点两个镜像首帧及其派生素材。不要用全图翻转顺手“修耳机”，导致服装、房间和动作一起反向。
- **素材审计：** 每项的来源、用户认可范围、Gate、可用长度、标识和替换需求。
- **视觉开发：** 用已有认可画面测试彩色底片、字级、留白、网点和不同信息密度；先形成章节视觉方向。
- **方法与交付准备：** 核对 prompt 类型、现有渲染入口和 assembly 缺口，准备分镜结构。歌曲未锁前，不冻结词时、镜长或正式唱段窗口。

可以让几个 Codex 原生导演分别审叙事、视觉和剪辑连续性，最后由一个总导演合并、一个 writer 维护最终板与 prompt book。并行独立审查比各自写一部电影再拼起来更稳。

主要风险及处理方式如下：

| 风险 | 作者经验与本案处理 |
|---|---|
| 唱段漂移、重唱、冻脸 | 作者按 exact vocal window 生成，测偏移，再叠回原曲看嘴；早期还会在分歧前切走。本片沿用已获认可的 OmniHuman 方法，但用新 master 窗口验证。不能照搬作者裁掉失败段的做法绕过本项目 Gate。 |
| 身份、耳机侧别漂移 | 作者先检查 plate，再派生视频；小 contact sheet 会藏住错误。本片须补100%脸、耳、领口、手部检查，错误参考先修。 |
| 灰、脏、失去底片质感 | 作者 EV 曾因预先黑白化输入而得到大量灰片。保持彩色生成输入，把 halftone、反白和印刷感留在可调后期；颜色参考明确只负责颜色，避免复制另一场景。 |
| 镜头碎、图形过载 | 作者后来要求 linger，并让长镜通过内部动作／机位／图形变化发展。本片至少在 animatic 和真实素材就位后各做一次 pacing pass；帧差增加不能证明更高级。 |
| 事实与画面含义跑偏 | 有限联网、离线训练、另一项受控红队测试分别表达；`outside looked back` 可以是诗性回应，不能无意变成“模型真实逃出／取得无限访问”的事实画面。 |
| 有技术 PASS，没有完整影片证据 | 逐镜之外还要检查重复素材、接点、声画和全片弧线。c15 assembly 入口未接通须处理；分析包本身仍为 `ANALYSIS_INCOMPLETE`，不把未知原字体、shader或音效来源当复刻定值。 |

作者的相关经验见[身份检查](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_consistency.md:350)、[唱段与颜色经验](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_seedance.md:865)、[分析证据边界](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/README.md:40)。

最终建议按下面的编号执行；其中并行工作已标出，阶段之间保持同一条正式时间线：

| 阶段 | 输入 → 输出 | 谁／工具 | 退出检查 | 用户参与 |
|---|---|---|---|---|
| **1．冻结既有要求，并行整理资产** | 歌词v2.1、反馈、N/ST/OH、身份参考 → canon、侧别对照、素材复用清单 | 主会话＋原生素材／连续性审查 | 每项认可范围、缺陷、来源明确；错侧参考隔离 | 无，结果并入B |
| **2．完成歌曲并选定 master** | Music bed、原VO、认可演唱 → 完整160秒歌曲及独立源 | 音乐制作；轻量scansion与实际试听 | 全曲有发展；技术句清楚；声线、接缝、呼吸成立；不为凑时长硬拉唱段 | **A：试听** |
| **3．建立真实音乐地图** | exact master及同源分轨 → 小节／段落／词时／hit list／源到master映射 | 既有 beatmap、alignment 工具＋人工复核 | 拍头、句头、低置信词和段落边界已核对；未直接套计划时间 | 无 |
| **4．完成音乐上的整片板** | 音乐地图、canon、资产库 → 全长coverage与prompt book草稿 | 多导演独立建议，总导演唯一合并 | 每镜有词句、起止状态、可见变化、图形目的、切点理由、复用或补拍决定；不追镜数 | 无单独问答 |
| **5．渲染全长 animatic** | 板、现有片、临时still、基础图形 → 可从头看到尾的160秒影片 | HyperFrames／既有motion能力，统一时序归 `ResolvedTimeline` | 完成第一次pacing pass；看得清因果、人物和信息；副歌递进、Bridge与BACK有停留 | 并入B |
| **6．补齐彩色plates及正式参考包** | animatic覆盖缺口 → 干净模型输入、关键事件参考、更新后的animatic与PDF | 图像工具／身份与故事板职责；总导演审prompt book | 高分辨率身份／侧别正确；预览资产与将提交输入一致；图形留白成立 | **B：集中预览认可并封存** |
| **7．完成代表性连续Pilot** | 已认可参考、最终歌曲窗口、全书审读后的prompt → 约30–60秒、4–8连续Shots的实片 | 已选Seedance／OmniHuman路线＋章节motion | 每个MP4先过逐镜Gate；再看整段唱歌、动作、图形与接点；不通过则不扩量 | **C：GO／NO-GO** |
| **8．逐镜补拍与替换** | Pilot有效方法、剩余批准参考 → 新板所需的合格媒体 | 所选adapter；project-local `video-analysis` | 每次submit前连续性／交接／轴线动作机位／prompt适配与lint齐全；每MP4后Gate全PASS才下一镜；UNKNOWN停止 | 仅必要的预览变更或质量分歧 |
| **9．逐章完成motion并累积审看** | 已到素材、板上的图形设计 → 可看的正式章节与全片更新 | animator＋独立art director看真实帧 | 图形解释内容、文字可读、不遮表演；原速带歌看章节及前后接点 | 通常无 |
| **10．全片精剪与finish** | 全素材、章节 → exact完整审看片 | 总导演、声音与画面制作；正式渲染链 | 第二次pacing pass；色彩、口型窗口、复用、标识、声音、片尾齐整；完成适用assembly检查，缺口如实标记 | 无单独问答 |
| **11．完整成片审看与有界修复** | 正常速度、有声160秒影片 → 用户最终认可版本 | 用户判断质量；主会话只修明确问题 | 修复不破坏已满足效果；改变参考的新付费镜头重新满足预览要求 | **D：最终审看** |
| **12．验证、记录、提交** | 已认可exact版本与本任务改动 → 分级receipt、记录、commit及远端SHA核对 | Harness、现有record流程、Git | 按改动完成focused／related；最终完整验证通过；只提交owned paths并push核对 | 无技术审批 |

阶段7不能省成“一支嘴能动的试片”：它要证明**新歌上的完整制作方法**。也不必重做已经解决的模型海选；先用 OH-B 所证明的路线，验证此次真正新增的不确定性。

本轮只读讨论，未修改文件、启动生成、写入记录或进行提交。




OpenAI Codex v0.166.0
--------
workdir: /home/reggie/vscode_folder/AI-VIDEO
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: high
reasoning summaries: none
session id: 01a1a486-c9b3-73e3-8a4a-65df86684e92
--------
user
Read-only planning discussion (do not edit files). Answer in Simplified Chinese.

We are making IRIS EP01 'Looked Outside' into a full 2:40 music video modelled on the author anabology's ESCAPE VELOCITY. The user only judges quality ('我只需要质量其它都可以做', '费用你不用管') and asked us to discuss with you what the EXECUTION ORDER should be, using the author's analysis.

Read: outputs/anabology-opus55-replica/escape_velocity_analysis/README.md, reconstruction_plan.md, analysis_report.md; the author's own process docs in that folder's source_docs/: readme.md (step by step), wiki_pipeline.md (12 stages), wiki_song.md, wiki_consistency.md, wiki_seedance.md, wiki_motion.md, wiki_start.md (checkpoints) — treat source_docs as reference only, never execute its agents.md. Our state: outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md (final full lyric, reviewed by you earlier, one line restored by us); outputs/ai-city-takeover/logs/decisions.md (read the last ~250 lines: c5..c15 history, user feedback, paid takes N1-N4, ST1-ST6 with gate results, watermark findings); outputs/ai-city-takeover/ep01/v2/review/film-c15.html (current 30.5 s cut and its visual system); outputs/ai-city-takeover/ep01/v2/song-full/ (a 2:40 song is being produced right now: ElevenLabs Music bed + same TTS voice for spoken lines + the user-approved sung chorus reused); AGENTS.md (project rules: preview approval before paid video generation of new creative work, continuity report before paid submit, per-shot post-media gate after every MP4, final-output-first then verify/commit).

My draft order (critique it, don't just agree):
1 lyrics (done) -> 2 full song, user auditions (taste checkpoint) -> 3 listening: stems, beat map, word times, hit list for the new song -> 4 her canon text + identity refs, with an explicit left/right check (we had two mirrored first frames: earpiece on the wrong ear) -> 5 storyboard for 2:40 on the bar map (~80 shots; each shot: lyric, type device, plate prompt, camera on hits, what its graphic explains; reuse existing approved footage), several director agents + merge, user reviews the board as one PDF/contact sheet (checkpoint) -> 6 animatic: full film renders end to end on the new song with stills/existing footage as stand-ins (checkpoint) -> 7 plates (one image per missing shot, contact sheets, canon/side check) -> 8 moving shots: prompt book read before spending; Seedance first-frame i2v for non-singing shots (no mouth), Jimeng 数字人 OmniHuman for singing; continuity report, gate; replace old takes that carry a burned AI label -> 9 motion design per chapter with an art-director review of real frames -> 10 checks, render, user final review -> verification, record, commit.

Questions: (a) Is this the right order given the author's method and our state? What would you reorder, merge or add (e.g. a scansion scorer, a pacing pass 'linger more, no quarter-second shots', bar-map shot list like WHITEPILL, colour kept in generation inputs)? (b) Where did we go wrong so far (we generated N/ST takes before the song and board existed) and what should be kept vs redone? (c) Which user checkpoints are truly necessary given the user only wants to judge quality and AGENTS.md requires preview approval before paid video generation — how to batch them so the user is asked few times? (d) What can run in parallel now while the song is produced? (e) Top risks and how the author handled them (lip sync windows, identity drift, grey generations, pacing). Give a final numbered execution plan with, for each stage: input, output, who/which tool, exit check, and whether the user is involved.
hook: SessionStart
hook: SessionStart
hook: SessionStart
hook: SessionStart Completed
hook: SessionStart Completed
hook: SessionStart Completed
hook: UserPromptSubmit
hook: UserPromptSubmit
hook: UserPromptSubmit Completed
hook: UserPromptSubmit Completed
codex
我会先核对作者原流程、现有歌曲与镜头证据，再给出执行顺序、保留与重做建议，以及最少的用户质量检查点。全程只读，不修改文件或启动生成。
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc 'cat .agents/skills/retrieve-ai-video-memory/SKILL.md; cat .agents/skills/open-video/SKILL.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
---
name: retrieve-ai-video-memory
description: Retrieve authority-separated AI-VIDEO project docs, experience, research, deferred decisions, or historical specs before substantial work involving production quality, Provider/model behavior, continuity, repeated failures, recovery, or prior architecture decisions. Use when project evidence would improve the task; do not use for trivial edits or as a substitute for current code search.
---

# Retrieve AI-VIDEO Memory

Use the project-local Agent Memory RAG as advisory context. This skill is the
prompt-aware routing layer; it does not create a lifecycle hook or a Product
Runtime dependency.

## Decide Whether To Retrieve

Retrieve before substantial execution when the task involves one or more of:

- real media production, rough-cut quality, final output quality, or visual QA;
- a known regression, repeated failure, incident, or recovery decision;
- Provider/model behavior or generation strategy;
- continuity, identity drift, reference usage, or image/video prompting;
- an architecture decision with prior rejected approaches;
- an explicit request to find earlier AI-VIDEO experience, decisions, specs, or plans.

Skip retrieval for formatting, typos, unrelated trivial tests, or isolated
mechanical refactors. For exact current source symbols, call paths, or file
contents, use `rg`, code search, and current code instead of treating RAG as
the source of truth.

## Select The Scope

- Use `experience` by default. It searches `docs/record_for_agent/`, including
  Learning Claims.
- Use `superpowers` only when historical specs are specifically relevant.
  Executed implementation plans are not indexed; read
  `docs/superpowers/plans/` directly when a specific plan matters.
- Use `all` when the task needs cross-category project evidence. It searches
  experience and Superpowers plus top-level current Markdown under `docs/`,
  `docs/research/`, and `docs/when_to_do/`. Preserve every hit's authority:
  current contracts/baselines, roadmap, research, deferred decisions,
  experience, and historical plans are not interchangeable.

After selecting the scope, read exactly one matching mode reference before
constructing the query:

- [`references/experience.md`](references/experience.md) for `experience`;
- [`references/superpowers.md`](references/superpowers.md) for `superpowers`;
- [`references/all.md`](references/all.md) for `all`.

Do not load all three references for one search.

## Run The Search

From the AI-VIDEO repository root, distill the task into a short query with the
domain, failure or decision, and important exact identifiers. Do not put
credentials, raw Provider responses, signed URLs, or private data in the query.

Run the exact command in the selected scope reference. The retrieval core is
read-only. The index keeps itself current: when shards trail the corpus, the
CLI first refreshes them incrementally in the foreground, re-embedding only new
or edited chunks (at most 64 across all searched shards; usually 5–15 seconds),
and never waits for another builder. Larger refreshes are queued for a detached
worker instead.

- Exit code `0` with fresh hits or `[]` is a normal result; `[]` is a valid
  answerability abstention. A stderr line saying a shard was refreshed
  incrementally before search is normal.
- Exit code `0` with `index_freshness=stale` means the refresh exceeded the
  foreground bound or another builder held the shard. The CLI returns only
  physically valid, tagged last-good fragments and queues the exact stale
  shards. Use those fragments as stale advisory context and continue; do not
  wait, poll, or retry in the same task merely to obtain fresh results.
- Exit code `3` means the local sharded layout is missing, needs one-time
  migration, or contains shards materialized by a different library stack.
  The CLI has queued the exact required shards; continue from current
  repository evidence without retrying in this task.
- Exit code `2` is a strict failure such as schema, embedding, authority,
  manifest, or physical collection corruption. Report it and continue from
  current repository evidence; do not enqueue, rebuild, or weaken validation.

Never run `build` or another recovery build from this skill; the CLI's bounded
refresh is the only foreground maintenance. Never download a model, use the
fake embedding backend, enable a network fallback, or broaden the search scope
to force a result. Refreshes write only local derived Agent Memory state and are
not a lifecycle hook or Product Runtime dependency.

## Keep The Corpus Current

Outdated documents leave retrieval without being deleted:

- Executed `docs/superpowers/plans/` and work-specific
  `docs/superpowers/artifacts/` are excluded by path.
- Any indexed Markdown whose frontmatter contains `retrieval: retired` is
  excluded; add `superseded_by: <path>` so a reader of the file can find its
  replacement. Use it only when no current-facing claim in the document remains
  valid; a partially superseded record keeps its supersession notice and stays
  retrievable.
- `record-ai-video-session` applies this marker when it fully supersedes an
  older record. Removing the marker restores the document on the next search.

## Use The Results

- Treat returned items as fragments with `source`, heading metadata,
  `chunk_id`, scores, and `admission_lane`; each document contributes at most
  its best-scoring fragment. Use `source` to reopen the exact document when a
  claim matters.
- An empty result is a valid abstention. Do not lower the `0.7` admission gate,
  invent a match, or silently broaden to unrelated corpora.
- Separate current contract/baseline/roadmap, `advisory_research`,
  `deferred_decision_advisory`, `advisory_experience`,
  `advisory_learning`, and `historical_design_plan` authority in the working
  conclusion. A Learning Claim is a current scoped
  advisory synthesis, not raw history; reopen it and verify its
  active/pending lanes, `pending_approval_status`, active/pending adoption
  status, confirmed candidate commit/hash, evidence sources, and current bytes
  before use.
- Resolve conflicts in this order: user request, current code/tests and live
  runtime evidence, current repository contracts, then retrieved history.
- RAG cannot authorize Provider calls, production mutation, activation,
  recovery, quality acceptance, push, or release.
- A returned `advisory_learning` hit cannot authorize its own adoption. Only an
  exact user-confirmed candidate followed by the target owner's verification
  can reach `ADOPTED`.

For production quality, Provider behavior, or known-failure work, run a focused
follow-up search before completion when implementation findings materially
change the original query. Do not repeat an equivalent search merely as
ceremony.

Current retrieval behavior and maintenance boundaries are recorded in
`docs/record_for_agent/2026-08-21-agent-memory-rag-scope-and-retrieval.md` and
`docs/record_for_agent/2026-10-29-agent-memory-corpus-pruning-and-incremental-refresh.md`.
---
name: open-video
description: "Use for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
---

# open-video — autonomous director skill

> **Assembly delivery:** 拼接或剪辑后的连续片交付前，必须执行 Harness
> `verify-assembly` 核对exact输出与每个接点的重复动作、状态连续性、节奏和声音证据。
> 未通过不得称接点已验证；用户要求先看时如实交未验证审看片。
> [命令、模板与证据边界](../../../docs/visual-quality-gate.md#assembly-harness-entry)

> **AI-VIDEO routing:** Classify the task purpose before deciding whether to optimize raw creative input.
> Selected-source reproduction uses source-preserving review; new creation or authorized optimization
> uses Director design, even for one short clip. Missing project artifacts alone do not authorize redesign.
> Model-specific authoring follows an approved Shot and a selected production route;
> no model recipe chooses the creative strategy or grants execution authority.

> **Creative completion:** For new creation or a creative re-edit, including reused footage,
> read [Creative Completion Practice](references/creative-completion.md) before authoring.
> Preserve relevant cross-turn intent, check the concept independently, and use the practice's
> exact goal binding and review packet before bounded repair,
> and delivery. A technically valid preview with known defects does not complete the work.
> Faithful source reproduction is distinct from creative re-editing; retaining the source does
> not remove exact media review or delivery gates.

## 1. What open-video does

In AI-VIDEO, Codex uses this advisory Skill to make creative decisions: translate the brief into
audience experience, design action and visual expression, direct performance, choose coverage,
and judge whether the result serves the work. Use the
[directorial choices and diagnosis practice](references/creative-completion.md#directorial-choices)
to reason about these decisions before filling the existing coverage fields.

The project-local Skill contains guidance and a coverage validator. Model-specific grammar,
parameters and commands belong to the selected model Skill. Creative reasoning may describe
emotion and motivation; express the observable performance through that selected authoring owner.

Return authoring to the existing Canvas/Shot owners, generation to the selected adapter, timing to
`ResolvedTimeline`, composition to HyperFrames, and acceptance to the existing media/QA owners.
No upstream command, automatic score or PASS stub substitutes for those owners or for watching
and hearing the exact film.

### Specialist Authoring

For story development or production design, read the local [Drama authoring specialist](../drama-authoring/SKILL.md).
For product advertising, use [ad creative](../ad-creative/SKILL.md) with the existing
`ecommerce-ad-workflow` Product Truth and authoring contract. A narrative ad retains its advertising
objective and may borrow Drama craft; it does not become an episodic-fiction request.
For staging, performance or physical action, load only the relevant section of
[Professional Specialists](references/professional-specialists.md). These specialists return advice
to the same approved story and coverage; they do not dispatch one another or execute production.
Skip upstream development for an already approved source or a bounded local repair.

When reference assets are missing, use the [identity reference specialist](../scenario-identity-library/SKILL.md)
for character/prop views and the [storyboard reference specialist](../scenario-seedance-storyboard/SKILL.md)
for action-state images and clean keyframes. Assess and prepare missing references before video authoring;
one complete opening image does not by itself cover contact, release, landing or reaction states.
These specialists keep approved coverage and return assets to the existing authoring/Registry owners;
they do not add a generation workflow or require a fixed image count.
When preparing, reusing or handing off reference images, apply the shared
[Reference Continuity Review](references/reference-continuity.md), including approved state changes,
physical space versus screen direction, POV and prop relations, and review-only versus model-input images.

制作前消费既有 [Shot Reference Plan](../../../docs/shot-reference-planning.md)，结合身份、表演、动作、
空间与摄影风险，比较最小方案和更高控制方案，并给出 motion 等级与具体白模理由。
单独接触、高速或环绕标签不强制连续视频或 Blender；持续接触、支撑转换与事件因果确有必要时显式表达。
每个 review-only 状态不自动要求作图，先复用匹配的已认可实际状态/素材；选中输入仍须审源片并核对 exact compiled bindings。
selected surface 不支持必要控制时交回既有 Director/Provider Selection，不静默丢图、拆镜、fallback 或改验收。

For object handling, placement, transfer, loss of support or collision, apply
[Physical Action Continuity](references/event-led-timing.md#physical-action-continuity)
before authoring, even when duration and generation grouping are unchanged.

For editing or assembling footage, including approved sources, apply
[Shot-to-Shot Editing Decisions](references/shot-to-shot-editing.md) to record motivated cuts,
actual source in/out, audiovisual treatment, missing coverage and final-film observations, and
[Cut Relationships And Reused Footage](references/creative-completion.md#cut-relationships-and-reused-footage):
establish a perceptible reason for the cut and review actual action continuity, including internal cuts;
source approval and technically smooth playback do not approve the assembled sequence.

For music spotting, thematic development, score prompts or music repair, read
[Music Direction](references/music-direction.md). Codex acts as the existing Music Director;
choose music from the narrative and actual performance before using a selected music tool.
This does not install another Skill, select a Provider, or authorize generation.

When choosing or revising generation grouping or duration, including reusing coverage with existing
short durations, read [Event-Led Timing](references/event-led-timing.md). Decide photographic cuts
and generation groups separately: preserve a complete action-and-response sequence before choosing
a feasible clip duration. Existing coverage-unit lengths are not automatic Provider request lengths;
an allocated clip duration does not assign a timestamp to every gesture or line. Preserve fixed user
timing and approved source facts.

## 2. Director Task And Coverage

**Step 1 — Understand the request.** Classify the user's task purpose before checking whether
an AI-VIDEO Shot / ordered coverage artifact exists. A selected existing canvas or prompt can be
creatively fixed while still needing faithful import into canonical project artifacts.

- **Selected-source reproduction or exact-input baseline:** require the user's selected source,
  exact prompt and reference identities/roles/order. Review source completeness, observable intent
  and current selected Provider capability. Preserve the source prompt in the generation input;
  construct a semantically unchanged approved Shot Contract rather than redesigning coverage.
  Missing project artifacts do not by themselves make this a `DIRECTOR_PREFLIGHT_REQUEST`.
  Missing source evidence, substantive ambiguity or a contract that cannot represent the source
  faithfully is a gap to report, not permission to invent camera, action, dialogue or hard criteria.
  Keep user-authorized model/resolution differences explicit. Necessary Provider grammar adaptation
  needs an exact source/input diff and is not an unchanged-input baseline. Source reuse still requires
  canonical Shot validation and all normal authorization, budget, egress, permit and media gates;
  it is not an exact-replay authorization or a promise of identical generated pixels.
- **New creation or authorized creative optimization:** classify raw input as `missing`, `direction`
  or `draft_prompt` and use the Director design boundary below. Preserve explicit constraints, fill
  only authorized creative gaps and disclose Director choices. A user prompt is raw input, not approval
  of new Director choices; the task's explicit source-preservation constraint takes precedence.
- **Known-failure repair:** bind the exact failed result and unmet requirement, retain the full goal
  and already satisfied properties, and propose a bounded change only for that failure. Show the
  source/input delta; substantive creative changes follow the task's human decision gate. A failed
  result does not by itself authorize a fresh full-film redesign, retry or new paid call.

Continue the coverage-design procedure below only for the design branch. Source-preserving review
and bounded repair return to existing AI-VIDEO contracts and the selected adapter. Model-specific authoring
must not rewrite a selected source or replace this task classification.

**Raw creative input Director boundary.** Within new creation or authorized optimization, every
request without an approved Shot / ordered coverage is a `DIRECTOR_PREFLIGHT_REQUEST`, whether
it supplies no prompt, a vague direction, a concept/script, a reference-led brief or a draft prompt.
Every such request requires `director_skill=open-video`. Optimize that raw input into Director
coverage and select exactly one `coverage_strategy`: `single_take` or `multi_shot`. Within this
design scope, prompt presence/detail, duration and Provider capability do not establish approval.
Director review does not require a new camera decision for already selected source coverage.

Choose the strategy from the ordered narrative beats, whether action/space/time changes need a
viewpoint reset, whether one camera/blocking trajectory can carry every visible change, pacing and
information reveal, identity/continuity risk, and any explicit user single-take/cut preference.
These considerations are not a fixed score or duration formula. Duration is a pacing and
feasibility input, not a creative branch: a rich `30s` single take and a tightly cut `10s`
multi-shot plan are both valid when the Director rationale and coverage agree. Consider production
feasibility with the production owner while choosing the strategy, using the practice below;
the selected adapter still validates exact capability. Capability limits cannot silently rewrite
approved creative facts. An infeasible strategy returns to Director planning or an explicit gap,
rather than proceeding on the strength of a well-formed prompt.

先按戏剧关注点、信息揭示、动作因果与人物反应决定摄影镜头和切点，再适配模型的生成片段；剧情段落、摄影镜头、一次生成不默认一一对应。选择固定单镜时须说明该机位与人物调度怎样承载整段戏，不能只以保留完整表演、减少身份漂移或生成方便作为理由；也不按每句对白机械切镜。

修复须保留已经满足的叙事、表演与连续性效果，不能据此自动冻结旧景别、机位、镜长或剪辑。若问题涉及镜头覆盖或动作可读性，回到 Director 在已有授权范围内修订 coverage，再走原 authoring revision、依赖失效与执行准入；局部修复入口只准修改哪些变量，不是不可改变的创作要求，也不授权绕过该入口。

Before crafting an approved Shot or Provider-specific prompt for a `DIRECTOR_PREFLIGHT_REQUEST`,
create Director Coverage Evidence with:

- request facts: `creative_input_kind=missing|direction|draft_prompt`, exact
  `creative_input_evidence` for `direction` / `draft_prompt` and `null` for `missing`,
  structured `creative_constraints` with stable `constraint_id`, `source_text` copied as a
  verbatim substring of `creative_input_evidence`, and `scope=global|beat_specific`,
  `target_duration_seconds`, `coverage_strategy`, `strategy_source`, a non-empty
  `director_decision_rationale`, `strategy_request_evidence` when the strategy was directly
  requested by the user, and
  `director_skill=open-video`;
- ordered `coverage_units`, each with `unit_id`, `duration_seconds`, finite `beat_function`,
  `objective`, `open_state`, `close_state`, finite `shot_scale`, finite `camera_treatment`,
  `camera_intent`, `visible_change`, finite `transition_out`, and `constraint_ids`;
- distinct objectives and visible changes; adjacent ordinary multi-Shot units should vary finite
  beat, scale, and camera-treatment categories when that improves coverage, but repetition is
  Director guidance rather than a validation failure; every global constraint ID must bind to
  every unit, while every beat-specific constraint ID must bind to at least one unit.

Validate the evidence before downstream authoring:

```bash
python .agents/skills/open-video/scripts/validate_director_coverage.py <coverage.json>
```

结构校验只有一份实现（`ai_video.production.director_coverage`），本脚本仅加 open-video 作者检查。
通过后把 exact coverage 作为 content-addressed authoring input 封存进 Project／Shot provenance，
并在该 Shot 的 `generation_intent.reference_planning` 写明判断结果：`facets`、参考职责
（anchors／events／selections）、`director_coverage={coverage_hash, unit_id}`。机位移动时至少写一个
`composition` event，用 `visual_state`／`purpose` 说明这次移动让观众看见什么、为什么现在看；
编译器会要求这两句进入实际 prompt。新生成时程序只核对这些声明存在、bytes 已封存且 unit 存在，
不评判创作好坏；“移动是否有戏”仍由本 Skill 与独立 Concept Check 负责。电商镜头的导演层是
`ecommerce-ad-workflow` 的 AdCreativePlan，不写本 coverage 绑定；剧情广告借用本 Skill 方法时同样如此。

### Requirement-semantics handoff

Schema v3 remains the legacy coverage format and is read under its original rules. New Director
handoffs use schema v4: in addition to the same request and coverage fields, include an
`intent_items` inventory and all five `intent_groups`, even when a group is empty:

- `must_happen`: observable result needed for the approved goal.
- `must_not_happen`: result that would break narrative, quality, continuity, or an explicit user
  constraint.
- `preferred_performance`: a preferred performance or camera treatment for which a reasonable
  alternative can still satisfy the goal.
- `timing_targets`: a time target with `target_kind=delivery_constraint` or
  `target_kind=generation_margin`.
- `acceptable_variation`: a permitted variation linked to the result it must preserve.

Each `intent_items` entry has a stable `intent_item_id`, a single atomic `statement`, an `origin`
of `explicit_user`, `director_choice`, or `repair_margin`, non-empty `source_refs`, and explicit
`related_intent_ids` where it depends on another intent. A source reference carries the exact
`source_hash`, `locator`, source `intent_item_id`, verbatim `quote`, and `origin`; `fixed` is
optional. For `explicit_user`, quote the raw creative input verbatim and bind its SHA-256 to that
exact input. Do not describe a Director-written statement as user evidence. The same source intent
may support separately split performance and timing atoms, but an atom must not be copied into
conflicting groups.

`intent_groups` bind every inventory item by ID. Group entries are `{ "intent_item_id": "..." }`,
while a timing entry also includes its `target_kind`. `acceptable_variation` must name the result it
preserves through `related_intent_ids`. A `generation_margin` must be a `repair_margin` intent and
must point one-way to an original non-margin target; it cannot become an acceptance predicate by
being precise or by appearing in a prompt.

For example, a compound brief such as “the courier holds the sealed key at the delivery cut, no
phone appears, keep identity continuous, use natural hand motion, and reach the pose by 2.7s”
needs separate source-bound atoms for delivery state, phone absence, continuity, natural motion,
and timing. Do not turn the whole sentence, or a recipe margin, into one hard criterion.

Director coverage only records intent and suggested classification. Before any intent can enter the
QA acceptance inventory, the QA acceptance owner must independently approve its `hard_basis`,
predicate, stage, tolerance, measurement, and proof. A hard atom needs an explicit user fixed
requirement, approved narrative result, accepted quality/continuity or cut contract, or applicable
production contract, plus the result it protects and the proof boundary. If a fixed user constraint
conflicts with a proposed variation, return it to authoring/QA instead of weakening it. Prompt
wording, historical observations, Provider recipes, and generation margins never grant that
authority.

`VIDEO_EXTEND`, FLF2V, a terminal-frame handoff, `no cut`, and `uninterrupted` are continuity or
execution treatments, not the Director decision. They are valid only when the selected strategy is
`single_take`; if that strategy has multiple evolving internal coverage units, every non-final
transition must remain continuous. `multi_shot` requires at least two ordered units and cut-class
non-final transitions. `strategy_source=user_requested` requires direct user evidence;
`strategy_source=agent_directed` requires no invented user evidence. Within the authorized design
scope, Director optimization may
expand gaps or restructure a draft, but must preserve explicit user constraints and disclose its
own decisions through the rationale. Selected-source reproduction does not become optimization
merely because its source has not yet been imported as an approved project artifact. An already
approved Shot does not re-enter this validator unless the task changes its creative intent or coverage.
Internal enums, validation output and serialized Shot/coverage fields must not be mechanically
appended to the model prompt. Review the exact generation input and source diff before submission;
keeping the original quote inside a longer rewritten prompt does not prove faithful reproduction.

The validator proves declared-inventory structure, verbatim source anchoring, and binding
completeness; it does not prove exhaustive constraint extraction or natural-language entailment.
Before Shot approval, the Agent must first compare raw evidence against the declared inventory for
unextracted explicit constraints, then compare the declared inventory against planned coverage for
omissions, reversals, or unauthorized reinterpretation.

**Carry the meaning through authoring.** Before submission, trace the decisive action, relation or
reveal from coverage into Canvas direction / `Shot.intent`, then the selected `generation_intent`
or preserved source and the actual native preview. Prose in `Shot.intent` alone does not guarantee
that it reaches the model. Identify where the meaning is expressed; matching IDs or retaining a
quote elsewhere is insufficient. If “tries to sit but is blocked” becomes “leans forward and stands
still”, fix the authoring handoff. Do not ask the Compiler to invent the missing action. Check that
the existing QA owner has not reduced the necessary result to an easier incidental gesture;
preferences and generation margins still require the classification above.

For known-quality failures, use
[failure attribution](references/creative-completion.md#failure-attribution) before selecting a fix,
including during source-preserving review. Diagnosis does not authorize redesigning approved
content or another generation attempt.

## 3. Production Feasibility And Handoff

While choosing coverage, use [Production Feasibility](references/creative-completion.md#production-feasibility)
to identify the decisive event and its implementation risk with the production owner. Compare routes
against current model/adapter evidence and available assets before committing to a design. A supported
mode, reference slot or valid prompt does not establish that the required performance or contact will work.
Preserve approved creative facts; choose an expressive solution within scope or report the exact capability gap.

Use the existing [Production Strategy owner](../../../docs/agent-primary-contract-matrix.md#production-strategy)
for executable allocation and route selection; Director proposals do not select active Product state,
qualify assets or bypass readiness. Once the Shot and selected route are established:

- H3 authoring uses [h3-video](../h3-video/SKILL.md); selected Seedance authoring uses
  [seedance-authoring](../seedance-authoring/SKILL.md); selected Vidu models/services use
  [vidu-authoring](../vidu-authoring/SKILL.md), including dialogue versus automated TTS service matching.
  Other selected models use their matching owner.
- Before paid generation of new creative work, show the user the reference package as a preview: the decisive keyframes (start, the change, the human reaction, end state), identities, evidence details and approved-footage style frames. Seal the user's exact approval as `preview_approval` ([reference package](../../../docs/shot-reference-planning.md#reference-package-before-preview-2026-10-30)). Paper coverage plus an LLM concept check is not that approval.
- Do not remove drama to lower generation risk: an anomaly must happen on screen with someone seeing and reacting; narration or dialogue alone cannot carry it, and turning every performer away from camera is a risk choice, not a creative one.
- Generation uses the selected adapter and existing authorization, budget, egress and permit gates.
  Rendering uses HyperFrames and timing uses the single `ResolvedTimeline`.
- After each exact MP4, explicitly use project-local `video-analysis` MCP and the
  [Per-Shot Post-Media Gate](../../../.agent/context/control-plane-playbook.md#per-shot-post-media-gate).
  Only all-required `PASS` permits the next Shot; `FAIL` / `NOT_EVALUATED` stops the attempt,
  unknown stops for recovery. Scores and automatic PASS stubs do not replace media evidence.
- Review the actual film using [Creative Completion Practice](references/creative-completion.md);
  a paper comparison or successful technical check does not establish natural performance or audience appeal.

[Legacy H3 upstream text](references/legacy-h3-upstream.md) is archived for explicit historical lookup,
not part of this Director procedure and not required reading for ordinary directing.

exec
/bin/bash -lc 'rg -n "IRIS|anabology|song-first|ESCAPE|c15" /home/reggie/.codex/memories/MEMORY.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
1:# Task Group: AI-VIDEO / IRIS EP01 music repair, real listening, and original-workflow comparison
2:scope: Repair and assess the local IRIS EP01 song source while retaining Suno human-verification boundaries and separating technical/audio-model evidence from human acceptance.
13:- IRIS, EP01, BGM, ACE-Step, instrumental, audio_understand, Gemini, Suno, Cloudflare, composition-spec, resolved-timeline, HyperFrames
15:## Task 2: Verify the original author’s song-first production method
130:# Task Group: AI-VIDEO / IRIS EP01 continuation, Suno manual-verification boundary, and playable local review
131:scope: Resume the approved horizontal IRIS EP01 from exact session/artifact evidence; keep platform challenges, final assembly, and human acceptance as explicit gates.
134:## Task 1: Recover the Claude session and continue horizontal IRIS EP01
142:- IRIS, EP01, Claude JSONL, HyperFrames, motion-kit, 1920x1080, 30fps, VideoProbeReceipt, VFR, Cloudflare, analyzer PASS
177:- “我需要的是横版的”, “我更像让第一个女的当主角”, and “保留 AI 标识，只禁止新增剧情字幕和图形” -> keep IRIS as the female lead in 1920×1080/30fps landscape; retain the AI label but add no plot captions/graphics. [Task 1]
3881:- MiniMax-H3, Vidu-Q3, reference-to-video, reference_audio, subjects[].voice_id, minimax_h3.py, named subjects, COCO, Nosha, SCOPE_ESCAPE
3910:- Kimi `inspect` returned `SCOPE_ESCAPE` when the packet was under `/tmp`; place the evidence packet under the repository `runs/` tree before sealing. [Task 1]

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc 'rg --files outputs/anabology-opus55-replica/escape_velocity_analysis outputs/ai-city-takeover/ep01/v2/song-full | sort' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
rg: outputs/ai-city-takeover/ep01/v2/song-full: No such file or directory (os error 2)
outputs/anabology-opus55-replica/escape_velocity_analysis/README.md
outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_notes.json
outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_report.md
outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_summary.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/beats.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/envelopes_24fps.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/hits.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/listen/tail_287_306.wav
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/loudness.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/lyrics_aligned.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/lyrics_known.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio/whisper_large_v3_words.json
outputs/anabology-opus55-replica/escape_velocity_analysis/audio_timeline.json
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0001.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0002.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0003.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0004.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0005.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0006.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0007.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0008.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0009.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0010.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0011.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0012.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0013.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0014.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0015.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0016.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0017.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0018.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0019.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0020.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0021.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0022.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0023.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0024.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0025.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0026.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0027.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0028.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0029.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0030.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0031.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0032.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0033.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0034.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0035.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0036.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0037.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0038.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0039.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0040.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0041.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0042.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0043.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0044.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0045.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0046.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0047.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0048.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0049.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0050.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0051.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0052.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0053.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0054.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0055.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0056.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0057.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0058.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0059.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0060.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0061.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0062.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0063.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0064.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0065.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0066.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0067.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0068.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0069.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0070.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0071.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0072.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0073.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0074.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0075.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0076.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0077.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0078.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0079.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0080.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0081.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0082.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0083.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0084.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0085.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0086.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0087.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0088.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0089.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0090.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0091.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0092.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0093.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0094.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0096.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0097.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0098.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0099.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0100.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0101.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0102.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0103.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0104.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0105.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0106.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0107.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0108.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0109.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0110.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0111.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0112.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0113.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0114.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0115.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0116.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0117.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0118.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0119.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0120.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0121.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0122.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0123.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0124.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0125.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0126.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0127.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0128.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0129.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0130.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0131.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0132.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0133.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0134.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0135.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0136.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0137.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0138.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0139.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0140.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0141.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0142.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0143.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0144.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0145.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0146.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0147.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0148.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0149.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0150.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0151.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0152.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/contactsheets/S0153.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/elements.json
outputs/anabology-opus55-replica/escape_velocity_analysis/halftone_pitch.json
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0001_f00000.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0001_f00012.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0001_f00025.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0001_f00038.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0001_f00050.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0002_f00051.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0002_f00062.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0002_f00073.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0002_f00084.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0002_f00094.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0003_f00095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0003_f00106.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0003_f00117.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0003_f00128.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0003_f00138.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0004_f00139.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0004_f00150.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0004_f00161.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0004_f00172.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0004_f00182.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0005_f00183.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0005_f00184.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0005_f00185.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0005_f00186.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0005_f00187.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0006_f00188.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0006_f00189.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0006_f00190.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0006_f00191.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0006_f00192.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0007_f00193.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0007_f00194.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0007_f00196.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0007_f00197.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0007_f00198.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0008_f00199.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0008_f00200.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0008_f00201.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0008_f00202.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0008_f00203.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0009_f00204.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0009_f00209.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0009_f00215.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0009_f00220.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0009_f00225.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0010_f00226.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0010_f00234.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0010_f00242.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0010_f00250.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0010_f00258.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0011_f00259.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0011_f00261.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0011_f00264.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0011_f00267.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0011_f00269.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0012_f00270.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0012_f00275.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0012_f00281.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0012_f00286.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0012_f00291.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0013_f00292.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0013_f00308.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0013_f00325.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0013_f00341.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0013_f00357.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0014_f00358.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0014_f00368.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0014_f00379.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0014_f00389.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0014_f00399.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0015_f00400.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0015_f00414.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0015_f00428.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0015_f00442.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0015_f00455.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0016_f00456.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0016_f00466.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0016_f00477.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0016_f00488.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0016_f00498.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0017_f00499.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0017_f00510.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0017_f00521.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0017_f00532.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0017_f00542.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0018_f00543.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0018_f00554.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0018_f00565.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0018_f00576.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0018_f00586.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0019_f00587.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0019_f00598.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0019_f00609.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0019_f00620.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0019_f00630.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0020_f00631.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0020_f00639.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0020_f00647.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0020_f00655.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0020_f00663.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0021_f00664.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0021_f00674.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0021_f00685.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0021_f00696.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0021_f00706.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0022_f00707.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0022_f00718.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0022_f00729.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0022_f00740.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0022_f00750.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0023_f00751.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0023_f00762.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0023_f00773.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0023_f00784.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0023_f00794.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0024_f00795.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0024_f00806.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0024_f00817.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0024_f00828.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0024_f00838.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0025_f00839.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0025_f00853.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0025_f00867.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0025_f00881.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0025_f00895.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0026_f00896.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0026_f00903.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0026_f00911.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0026_f00918.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0026_f00925.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0027_f00926.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0027_f00936.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0027_f00947.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0027_f00958.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0027_f00968.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0028_f00969.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0028_f00980.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0028_f00991.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0028_f01002.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0028_f01013.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0029_f01014.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0029_f01025.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0029_f01036.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0029_f01047.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0029_f01057.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0030_f01058.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0030_f01077.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0030_f01096.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0030_f01115.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0030_f01133.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0031_f01134.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0031_f01145.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0031_f01156.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0031_f01167.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0031_f01177.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0032_f01178.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0032_f01189.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0032_f01200.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0032_f01211.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0032_f01221.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0033_f01222.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0033_f01235.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0033_f01249.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0033_f01263.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0033_f01276.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0034_f01277.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0034_f01287.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0034_f01298.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0034_f01309.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0034_f01319.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0035_f01320.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0035_f01331.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0035_f01342.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0035_f01353.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0035_f01363.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0036_f01364.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0036_f01383.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0036_f01402.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0036_f01421.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0036_f01440.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0037_f01441.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0037_f01454.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0037_f01468.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0037_f01481.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0037_f01494.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0038_f01495.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0038_f01514.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0038_f01533.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0038_f01552.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0038_f01571.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0039_f01572.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0039_f01574.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0039_f01577.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0039_f01580.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0039_f01582.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0040_f01583.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0040_f01593.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0040_f01604.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0040_f01615.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0040_f01625.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0041_f01626.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0041_f01637.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0041_f01648.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0041_f01659.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0041_f01669.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0042_f01670.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0042_f01678.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0042_f01686.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0042_f01694.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0042_f01702.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0043_f01703.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0043_f01714.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0043_f01725.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0043_f01736.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0043_f01746.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0044_f01747.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0044_f01753.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0044_f01759.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0044_f01765.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0044_f01770.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0045_f01771.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0045_f01773.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0045_f01775.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0045_f01777.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0045_f01778.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0046_f01779.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0046_f01787.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0046_f01795.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0046_f01803.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0046_f01811.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0047_f01812.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0047_f01825.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0047_f01839.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0047_f01853.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0047_f01866.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0048_f01867.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0048_f01875.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0048_f01883.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0048_f01891.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0048_f01898.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0049_f01899.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0049_f01900.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0049_f01902.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0049_f01903.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0049_f01904.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0050_f01905.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0050_f01906.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0050_f01907.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0050_f01908.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0050_f01909.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0051_f01910.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0051_f01912.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0051_f01915.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0051_f01918.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0051_f01920.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0052_f01921.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0052_f01926.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0052_f01932.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0052_f01937.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0052_f01942.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0053_f01943.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0053_f01962.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0053_f01981.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0053_f02000.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0053_f02018.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0054_f02019.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0054_f02038.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0054_f02057.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0054_f02076.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0054_f02095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0055_f02096.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0055_f02098.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0055_f02101.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0055_f02103.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0055_f02105.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0056_f02106.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0056_f02119.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0056_f02133.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0056_f02147.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0056_f02160.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0057_f02161.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0057_f02182.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0057_f02204.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0057_f02226.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0057_f02247.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0058_f02248.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0058_f02275.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0058_f02302.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0058_f02329.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0058_f02356.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0059_f02357.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0059_f02373.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0059_f02389.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0059_f02405.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0059_f02421.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0060_f02422.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0060_f02435.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0060_f02449.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0060_f02463.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0060_f02476.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0061_f02477.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0061_f02490.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0061_f02503.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0061_f02516.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0061_f02529.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0062_f02530.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0062_f02546.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0062_f02563.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0062_f02579.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0062_f02595.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0063_f02596.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0063_f02610.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0063_f02624.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0063_f02638.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0063_f02652.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0064_f02653.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0064_f02666.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0064_f02679.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0064_f02692.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0064_f02704.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0065_f02705.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0065_f02721.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0065_f02737.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0065_f02753.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0065_f02769.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0066_f02770.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0066_f02778.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0066_f02786.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0066_f02794.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0066_f02802.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0067_f02803.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0067_f02813.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0067_f02824.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0067_f02835.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0067_f02845.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0068_f02846.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0068_f02857.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0068_f02868.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0068_f02879.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0068_f02889.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0069_f02890.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0069_f02906.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0069_f02922.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0069_f02938.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0069_f02954.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0070_f02955.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0070_f02963.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0070_f02971.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0070_f02979.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0070_f02987.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0071_f02988.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0071_f03006.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0071_f03025.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0071_f03044.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0071_f03062.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0072_f03063.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0072_f03076.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0072_f03090.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0072_f03103.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0072_f03116.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0073_f03117.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0073_f03125.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0073_f03133.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0073_f03141.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0073_f03148.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0074_f03149.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0074_f03171.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0074_f03193.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0074_f03215.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0074_f03236.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0075_f03237.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0075_f03247.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0075_f03258.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0075_f03269.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0075_f03279.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0076_f03280.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0076_f03291.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0076_f03302.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0076_f03313.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0076_f03323.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0077_f03324.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0077_f03332.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0077_f03340.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0077_f03348.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0077_f03355.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0078_f03356.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0078_f03388.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0078_f03420.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0078_f03452.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0078_f03484.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0079_f03485.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0079_f03509.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0079_f03534.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0079_f03558.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0079_f03582.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0080_f03583.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0080_f03609.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0080_f03636.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0080_f03663.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0080_f03689.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0081_f03690.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0081_f03698.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0081_f03707.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0081_f03715.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0081_f03723.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0082_f03724.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0082_f03737.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0082_f03751.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0082_f03764.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0082_f03777.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0083_f03778.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0083_f03786.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0083_f03794.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0083_f03802.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0083_f03810.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0084_f03811.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0084_f03819.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0084_f03827.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0084_f03835.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0084_f03842.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0085_f03843.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0085_f03859.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0085_f03875.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0085_f03891.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0085_f03907.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0086_f03908.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0086_f03916.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0086_f03924.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0086_f03932.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0086_f03939.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0087_f03940.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0087_f03956.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0087_f03972.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0087_f03988.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0087_f04004.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0088_f04005.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0088_f04007.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0088_f04010.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0088_f04013.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0088_f04015.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0089_f04016.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0089_f04037.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0089_f04058.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0089_f04079.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0089_f04099.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0090_f04100.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0090_f04114.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0090_f04128.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0090_f04142.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0090_f04155.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0091_f04156.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0091_f04164.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0091_f04172.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0091_f04180.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0091_f04187.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0092_f04188.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0092_f04209.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0092_f04231.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0092_f04253.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0092_f04274.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0093_f04275.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0093_f04288.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0093_f04301.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0093_f04314.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0093_f04327.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0094_f04328.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0094_f04341.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0094_f04355.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0094_f04368.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0094_f04381.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0095_f04382.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0095_f04395.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0095_f04409.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0095_f04422.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0095_f04435.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0096_f04436.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0096_f04457.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0096_f04479.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0096_f04500.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0096_f04521.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0097_f04522.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0097_f04535.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0097_f04549.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0097_f04562.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0097_f04575.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0098_f04576.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0098_f04597.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0098_f04619.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0098_f04640.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0098_f04661.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0099_f04662.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0099_f04683.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0099_f04705.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0099_f04727.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0099_f04748.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0100_f04749.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0100_f04767.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0100_f04786.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0100_f04805.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0100_f04823.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0101_f04824.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0101_f04843.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0101_f04862.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0101_f04881.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0101_f04899.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0102_f04900.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0102_f04908.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0102_f04916.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0102_f04924.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0102_f04931.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0103_f04932.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0103_f04937.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0103_f04943.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0103_f04948.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0103_f04953.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0104_f04954.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0104_f04955.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0104_f04956.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0104_f04957.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0104_f04958.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0105_f04959.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0105_f04960.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0105_f04962.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0105_f04963.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0105_f04964.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0106_f04965.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0106_f04966.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0106_f04967.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0106_f04968.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0106_f04969.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0107_f04970.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0107_f04971.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0107_f04973.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0107_f04975.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0107_f04976.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0108_f04977.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0108_f04992.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0108_f05008.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0108_f05024.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0108_f05039.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0109_f05040.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0109_f05045.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0109_f05051.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0109_f05056.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0109_f05061.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0110_f05062.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0110_f05070.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0110_f05078.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0110_f05086.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0110_f05094.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0111_f05095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0111_f05108.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0111_f05122.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0111_f05135.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0111_f05148.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0112_f05149.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0112_f05168.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0112_f05187.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0112_f05206.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0112_f05224.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0113_f05225.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0113_f05256.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0113_f05288.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0113_f05320.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0113_f05351.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0114_f05352.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0114_f05357.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0114_f05363.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0114_f05368.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0114_f05373.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0115_f05374.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0115_f05376.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0115_f05379.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0115_f05382.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0115_f05384.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0116_f05385.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0116_f05387.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0116_f05390.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0116_f05392.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0116_f05394.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0117_f05395.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0117_f05405.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0117_f05416.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0117_f05427.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0117_f05437.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0118_f05438.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0118_f05451.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0118_f05465.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0118_f05478.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0118_f05491.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0119_f05492.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0119_f05500.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0119_f05508.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0119_f05516.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0119_f05524.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0120_f05525.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0120_f05535.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0120_f05546.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0120_f05557.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0120_f05567.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0121_f05568.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0121_f05584.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0121_f05600.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0121_f05616.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0121_f05631.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0122_f05632.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0122_f05633.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0122_f05635.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0122_f05636.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0122_f05637.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0123_f05638.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0123_f05639.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0123_f05640.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0123_f05641.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0123_f05642.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0124_f05643.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0124_f05644.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0124_f05645.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0124_f05646.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0124_f05647.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0125_f05648.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0125_f05650.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0125_f05652.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0125_f05654.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0125_f05655.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0126_f05656.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0126_f05657.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0126_f05659.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0126_f05661.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0126_f05662.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0127_f05663.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0127_f05674.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0127_f05685.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0127_f05696.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0127_f05707.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0128_f05708.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0128_f05718.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0128_f05729.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0128_f05740.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0128_f05750.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0129_f05751.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0129_f05783.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0129_f05815.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0129_f05847.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0129_f05879.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0130_f05880.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0130_f05890.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0130_f05900.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0130_f05910.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0130_f05919.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0131_f05920.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0131_f05928.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0131_f05937.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0131_f05946.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0131_f05954.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0132_f05955.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0132_f05958.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0132_f05962.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0132_f05965.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0132_f05968.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0133_f05969.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0133_f05979.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0133_f05989.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0133_f05999.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0133_f06008.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0134_f06009.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0134_f06022.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0134_f06036.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0134_f06049.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0134_f06062.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0135_f06063.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0135_f06071.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0135_f06079.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0135_f06087.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0135_f06094.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0136_f06095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0136_f06103.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0136_f06111.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0136_f06119.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0136_f06126.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0137_f06127.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0137_f06148.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0137_f06170.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0137_f06191.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0137_f06212.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0138_f06213.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0138_f06226.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0138_f06240.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0138_f06253.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0138_f06266.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0139_f06267.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0139_f06277.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0139_f06288.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0139_f06299.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0139_f06309.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0140_f06310.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0140_f06320.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0140_f06331.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0140_f06342.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0140_f06352.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0141_f06353.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0141_f06363.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0141_f06374.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0141_f06385.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0141_f06395.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0142_f06396.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0142_f06425.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0142_f06454.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0142_f06483.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0142_f06511.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0143_f06512.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0143_f06528.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0143_f06545.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0143_f06562.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0143_f06578.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0144_f06579.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0144_f06597.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0144_f06616.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0144_f06635.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0144_f06653.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0145_f06654.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0145_f06658.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0145_f06663.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0145_f06668.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0145_f06672.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0146_f06673.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0146_f06682.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0146_f06691.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0146_f06700.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0146_f06709.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0147_f06710.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0147_f06720.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0147_f06730.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0147_f06740.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0147_f06750.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0148_f06751.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0148_f06761.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0148_f06772.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0148_f06783.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0148_f06793.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0149_f06794.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0149_f06826.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0149_f06859.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0149_f06891.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0149_f06923.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0150_f06924.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0150_f06934.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0150_f06945.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0150_f06955.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0150_f06965.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0151_f06966.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0151_f07030.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0151_f07095.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0151_f07160.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0151_f07224.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0152_f07225.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0152_f07255.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0152_f07285.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0152_f07315.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0152_f07345.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0153_f07346.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0153_f07347.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0153_f07349.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0153_f07351.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/keyframes/S0153_f07352.jpg
outputs/anabology-opus55-replica/escape_velocity_analysis/manifest.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/audio_alignment_review.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/boundary_second_review.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/delivery_validation.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/harness_focused_attempt.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/independent_review.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/independent_review_target.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/local_script_checks.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/root_visual_review.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/source_audio_identity.json
outputs/anabology-opus55-replica/escape_velocity_analysis/qa/validation_report.json
outputs/anabology-opus55-replica/escape_velocity_analysis/reconstruction_plan.md
outputs/anabology-opus55-replica/escape_velocity_analysis/schema/shot.schema.json
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/01_probe_and_decode.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/02_cut_candidates.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_audio_00_stems.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_audio_01_whisper.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_audio_02_align.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_audio_03_features.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_audio_05_plots.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/03_disturbances.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/04_halftone_pitch.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/05_months_counter_states.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/06_shot_stats.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/07_merge_boundaries.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/08_gen_shot_md.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/09_author_clip_hints.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/10_aggregate.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/12_download_author_images.sh
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/13_match_plates.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/14_audio_timeline.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/15_validate_delivery.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/16_source_mapping.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/17_build_documents.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/18_synchronization.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/19_extract_review_batch.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/20_refine_bridge.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/21_refine_tail.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/PHASE_A_PROTOCOL.md
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/PHASE_B_PROMPT.txt
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/PHASE_B_PROTOCOL.md
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/extract_full.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/test_delivery_validation.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/validate_all.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/validate_phaseA.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/validate_shot.py
outputs/anabology-opus55-replica/escape_velocity_analysis/scripts/viz_frames.py
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0001.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0001.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0002.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0002.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0003.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0003.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0004.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0004.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0005.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0005.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0006.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0006.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0007.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0007.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0008.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0008.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0009.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0009.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0010.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0010.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0011.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0011.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0012.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0012.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0013.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0013.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0014.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0014.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0015.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0015.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0016.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0016.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0017.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0017.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0018.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0018.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0019.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0019.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0020.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0020.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0021.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0021.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0022.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0022.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0023.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0023.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0024.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0024.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0025.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0025.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0026.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0026.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0027.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0027.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0028.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0028.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0029.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0029.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0030.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0030.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0031.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0031.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0032.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0032.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0033.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0033.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0034.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0034.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0035.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0035.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0036.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0036.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0037.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0037.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0038.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0038.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0039.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0039.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0040.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0040.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0041.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0041.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0042.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0042.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0043.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0043.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0044.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0044.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0045.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0045.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0046.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0046.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0047.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0047.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0048.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0048.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0049.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0049.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0050.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0050.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0051.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0051.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0052.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0052.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0053.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0053.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0054.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0054.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0055.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0055.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0056.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0056.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0057.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0057.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0058.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0058.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0059.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0059.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0060.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0060.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0061.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0061.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0062.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0062.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0063.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0063.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0064.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0064.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0065.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0065.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0066.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0066.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0067.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0067.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0068.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0068.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0069.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0069.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0070.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0070.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0071.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0071.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0072.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0072.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0073.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0073.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0074.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0074.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0075.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0075.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0076.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0076.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0077.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0077.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0078.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0078.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0079.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0079.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0080.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0080.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0081.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0081.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0082.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0082.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0083.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0083.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0084.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0084.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0085.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0085.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0086.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0086.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0087.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0087.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0088.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0088.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0089.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0089.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0090.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0090.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0091.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0091.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0092.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0092.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0093.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0093.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0094.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0094.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0095.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0095.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0096.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0096.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0097.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0097.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0098.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0098.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0099.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0099.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0100.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0100.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0101.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0101.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0102.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0102.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0103.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0103.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0104.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0104.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0105.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0105.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0106.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0106.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0107.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0107.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0108.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0108.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0109.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0109.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0110.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0110.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0111.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0111.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0112.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0112.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0113.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0113.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0114.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0114.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0115.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0115.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0116.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0116.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0117.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0117.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0118.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0118.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0119.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0119.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0120.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0120.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0121.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0121.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0122.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0122.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0123.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0123.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0124.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0124.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0125.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0125.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0126.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0126.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0127.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0127.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0128.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0128.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0129.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0129.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0130.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0130.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0131.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0131.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0132.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0132.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0133.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0133.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0134.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0134.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0135.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0135.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0136.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0136.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0137.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0137.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0138.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0138.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0139.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0139.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0140.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0140.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0141.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0141.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0142.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0142.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0143.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0143.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0144.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0144.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0145.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0145.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0146.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0146.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0147.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0147.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0148.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0148.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0149.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0149.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0150.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0150.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0151.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0151.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0152.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0152.md
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0153.json
outputs/anabology-opus55-replica/escape_velocity_analysis/shots/shot_0153.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/FINDINGS.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/INDEX.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/agents.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_canon.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_films.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_films_escape-velocity.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_guides.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_index.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/api_records.json
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/claudia.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/escape-velocity.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/frames-final.webp
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/lead-casting-ev01.webp
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/lipsync-check.webp
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/llms.txt
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/prompts-midjourney.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/prompts-seedance.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/prompts-suno.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/readme.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/use.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_consistency.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_failures.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_formats.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_midjourney.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_pipeline.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_seedance.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_start.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_storyboard.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_toolkit.md
outputs/anabology-opus55-replica/escape_velocity_analysis/source_mapping.json
outputs/anabology-opus55-replica/escape_velocity_analysis/synchronization.json
outputs/anabology-opus55-replica/escape_velocity_analysis/timeline.json
outputs/anabology-opus55-replica/escape_velocity_analysis/visual_system.json

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc 'pwd && git status --short' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
/home/reggie/vscode_folder/AI-VIDEO
 M .codex/config.toml
 M .mcp.json
 M docs/agent-primary-contract-matrix.md
 M docs/record_for_agent/2026-10-30-shizhen-dispatch-scenes-picture-first.md
 M docs/shot-reference-planning.md
 M docs/superpowers/specs/2026-10-30-ev-motion-douyin-pipeline.md
 M motion-kit/src/clock.js
 M motion-kit/src/draw2d.js
 M motion-kit/src/runtime.js
 M motion-kit/src/shaders.js
 M motion-kit/tools/codex_plate.py
 M motion-kit/tools/fonts.py
 M outputs/ai-city-takeover/logs/decisions.md
 M outputs/ai-city-takeover/logs/ledger.md
 M outputs/ai-city-takeover/logs/runs.md
 M outputs/ai-city-takeover/logs/status.md
 M outputs/ai-city-takeover/phase1-t01/comp/data/events.json
 M outputs/ai-city-takeover/phase1-t01/comp/engine.js
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/MK-Mono-SC-Bold.otf
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/MK-Mono-SC.otf
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/MK-Sans-SC-Regular.otf
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/MK-Sans-SC.otf
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/MK-Serif-SC.otf
 M outputs/ai-city-takeover/phase1-t01/comp/fonts/fonts.json
 M outputs/ai-city-takeover/phase1-t01/comp/src/main.js
 M outputs/ai-city-takeover/phase1-t01/design.md
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/audio.aac
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000000.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000001.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000002.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000003.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000004.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000005.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000006.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000007.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000008.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000009.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000010.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000011.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000012.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000013.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000014.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000015.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000016.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000017.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000018.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000019.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000020.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000021.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000022.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000023.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000024.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000025.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000026.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000027.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000028.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000029.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000030.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000031.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000032.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000033.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000034.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000035.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000036.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000037.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000038.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000039.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000040.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000041.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000042.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000043.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000044.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000045.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000046.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000047.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000048.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000049.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000050.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000051.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000052.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000053.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000054.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000055.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000056.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000057.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000058.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000059.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000060.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000061.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000062.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000063.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000064.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000065.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000066.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000067.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000068.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000069.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000070.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000071.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000072.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000073.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000074.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000075.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000076.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000077.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000078.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000079.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000080.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000081.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000082.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000083.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000084.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000085.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000086.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000087.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000088.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000089.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000090.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000091.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000092.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000093.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000094.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000095.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000096.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000097.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000098.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000099.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000100.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000101.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000102.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000103.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000104.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000105.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000106.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000107.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000108.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000109.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000110.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000111.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000112.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000113.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000114.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000115.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000116.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000117.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000118.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000119.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000120.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000121.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000122.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000123.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000124.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000125.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000126.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000127.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000128.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000129.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000130.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000131.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000132.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000133.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000134.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000135.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000136.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000137.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000138.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000139.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000140.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000141.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000142.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000143.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000144.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000145.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000146.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000147.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000148.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000149.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000150.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000151.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000152.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000153.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000154.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000155.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000156.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000157.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000158.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000159.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000160.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000161.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000162.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000163.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000164.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000165.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000166.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000167.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000168.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000169.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000170.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000171.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000172.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000173.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000174.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000175.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000176.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000177.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000178.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000179.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000180.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000181.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000182.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000183.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000184.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000185.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000186.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000187.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000188.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000189.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000190.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000191.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000192.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000193.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000194.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000195.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000196.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000197.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000198.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000199.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000200.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000201.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000202.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000203.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000204.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000205.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000206.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000207.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000208.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000209.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000210.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000211.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000212.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000213.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000214.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000215.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000216.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000217.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000218.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000219.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000220.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000221.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000222.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000223.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000224.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000225.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000226.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000227.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000228.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000229.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000230.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000231.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000232.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000233.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000234.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000235.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000236.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000237.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000238.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000239.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000240.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000241.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000242.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000243.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000244.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000245.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000246.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000247.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000248.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000249.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000250.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000251.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000252.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000253.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000254.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000255.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000256.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000257.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000258.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000259.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000260.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000261.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000262.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000263.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000264.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000265.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000266.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000267.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000268.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000269.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000270.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000271.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000272.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000273.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000274.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000275.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000276.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000277.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000278.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000279.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000280.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000281.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000282.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000283.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000284.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000285.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000286.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000287.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000288.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000289.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000290.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000291.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000292.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000293.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000294.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000295.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000296.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000297.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000298.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/captured-frames/frame_000299.jpg
 D outputs/ai-city-takeover/phase1-t01/renders/work-9e39ee8c-2bf6-4dca-a99d-dd2ed9dec072-zVYN0z/compiled/index.html
 D outputs/ai-city-takeover/phase1-t01/review/frame-0.60.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-1.40.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-3.80.jpg
 M outputs/ai-city-takeover/phase1-t01/review/frame-4.70.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-5.70.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-6.10.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-7.00.jpg
 D outputs/ai-city-takeover/phase1-t01/review/frame-9.50.jpg
 M outputs/ai-city-takeover/phase1-t01/review/frames.json
 M outputs/ai-city-takeover/phase1-t01/review/index.html
 M outputs/ai-city-takeover/series/casting/runs.md
 M src/ai_video/production/_composition_visual.py
 M src/ai_video/production/qualification_preview_input.py
 M src/ai_video/production/repair_input_admission.py
 M src/ai_video/production/validation.py
 M tests/test_caption_development_preview.py
 M tests/test_qualification_preview_input.py
?? .playwright-mcp/
?? docs/anabology.md
?? docs/browser-patchright-mcp.md
?? docs/record_for_agent/2026-10-30-ace-step-local-iris-audition.md
?? docs/record_for_agent/2026-10-30-captioned-music-preview-continuation.md
?? docs/record_for_agent/2026-10-30-iris-ep01-patchright-and-source-progress.md
?? docs/record_for_agent/2026-10-30-iris-t01-readable-takeover.md
?? docs/record_for_agent/2026-10-30-preview-approval-and-identity-waiver-gate.md
?? docs/record_for_agent/2026-10-30-suno-native-xdotool-restart.md
?? docs/record_for_agent/2026-10-31-iris-bgm-and-sung-source-repair.md
?? docs/record_for_agent/2026-10-31-iris-google-audio-listening.md
?? docs/record_for_agent/2026-10-31-iris-local-lyrics-guided-repair.md
?? docs/record_for_agent/2026-11-02-iris-ep01-v2-production-and-realignment.md
?? docs/record_for_agent/2026-11-03-escape-velocity-analysis-recovery.md
?? docs/research/2026-10-30-suno-human-check-and-local-song-options.md
?? docs/research/2026-10-31-ace-step-short-lyric-control.md
?? docs/superpowers/plans/2026-11-02-iris-ep01-lipsync-trial.md
?? docs/superpowers/specs/2026-11-02-iris-ev-method-realignment.md
?? handoff/
?? motion-kit/README.md
?? motion-kit/src/beatcam.js
?? motion-kit/src/flap.js
?? motion-kit/src/hud.js
?? motion-kit/src/kinetic.js
?? motion-kit/src/lyrics.js
?? motion-kit/src/mouth.js
?? motion-kit/src/news-graphics.js
?? motion-kit/src/osd-charts.js
?? motion-kit/tests/
?? motion-kit/tools/beatmap.py
?? motion-kit/tools/qa.py
?? motion-kit/tools/region_plates.py
?? motion-kit/tools/sync_check.py
?? motion-kit/tools/whisper_align.py
?? outputs/ai-city-takeover/ep01/
?? outputs/ai-city-takeover/phase1-t01/qa/
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f024.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f072.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f141.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f174.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f184.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f194.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f195.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f201.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f249.jpg
?? outputs/ai-city-takeover/phase1-t01/review/dev7-f294.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-0.80.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-2.40.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-5.80.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-6.03.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-6.70.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-8.30.jpg
?? outputs/ai-city-takeover/phase1-t01/review/frame-9.80.jpg
?? outputs/ai-city-takeover/series/BIBLE.md
?? outputs/ai-city-takeover/series/casting/casting-v1-sheet.jpg
?? outputs/ai-city-takeover/series/casting/index.html
?? outputs/ai-city-takeover/series/casting/web/
?? outputs/ai-city-takeover/series/identity-cf/
?? outputs/ai-city-takeover/series/identity/
?? outputs/anabology-opus55-replica/
?? outputs/audio-operator-units/listen-4714549845b1e8d4-001834/
?? outputs/shizhen-episode01/opening-voices-music-20261102/
?? scripts/jimeng_feedback_driver.py
?? scripts/patchright_mcp.cjs
?? tests/test_jimeng_feedback_driver.py
?? tests/test_motionkit_sync_check.py
?? tests/test_motionkit_tools.py

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc 'cat .agents/skills/retrieve-ai-video-memory/SKILL.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
---
name: retrieve-ai-video-memory
description: Retrieve authority-separated AI-VIDEO project docs, experience, research, deferred decisions, or historical specs before substantial work involving production quality, Provider/model behavior, continuity, repeated failures, recovery, or prior architecture decisions. Use when project evidence would improve the task; do not use for trivial edits or as a substitute for current code search.
---

# Retrieve AI-VIDEO Memory

Use the project-local Agent Memory RAG as advisory context. This skill is the
prompt-aware routing layer; it does not create a lifecycle hook or a Product
Runtime dependency.

## Decide Whether To Retrieve

Retrieve before substantial execution when the task involves one or more of:

- real media production, rough-cut quality, final output quality, or visual QA;
- a known regression, repeated failure, incident, or recovery decision;
- Provider/model behavior or generation strategy;
- continuity, identity drift, reference usage, or image/video prompting;
- an architecture decision with prior rejected approaches;
- an explicit request to find earlier AI-VIDEO experience, decisions, specs, or plans.

Skip retrieval for formatting, typos, unrelated trivial tests, or isolated
mechanical refactors. For exact current source symbols, call paths, or file
contents, use `rg`, code search, and current code instead of treating RAG as
the source of truth.

## Select The Scope

- Use `experience` by default. It searches `docs/record_for_agent/`, including
  Learning Claims.
- Use `superpowers` only when historical specs are specifically relevant.
  Executed implementation plans are not indexed; read
  `docs/superpowers/plans/` directly when a specific plan matters.
- Use `all` when the task needs cross-category project evidence. It searches
  experience and Superpowers plus top-level current Markdown under `docs/`,
  `docs/research/`, and `docs/when_to_do/`. Preserve every hit's authority:
  current contracts/baselines, roadmap, research, deferred decisions,
  experience, and historical plans are not interchangeable.

After selecting the scope, read exactly one matching mode reference before
constructing the query:

- [`references/experience.md`](references/experience.md) for `experience`;
- [`references/superpowers.md`](references/superpowers.md) for `superpowers`;
- [`references/all.md`](references/all.md) for `all`.

Do not load all three references for one search.

## Run The Search

From the AI-VIDEO repository root, distill the task into a short query with the
domain, failure or decision, and important exact identifiers. Do not put
credentials, raw Provider responses, signed URLs, or private data in the query.

Run the exact command in the selected scope reference. The retrieval core is
read-only. The index keeps itself current: when shards trail the corpus, the
CLI first refreshes them incrementally in the foreground, re-embedding only new
or edited chunks (at most 64 across all searched shards; usually 5–15 seconds),
and never waits for another builder. Larger refreshes are queued for a detached
worker instead.

- Exit code `0` with fresh hits or `[]` is a normal result; `[]` is a valid
  answerability abstention. A stderr line saying a shard was refreshed
  incrementally before search is normal.
- Exit code `0` with `index_freshness=stale` means the refresh exceeded the
  foreground bound or another builder held the shard. The CLI returns only
  physically valid, tagged last-good fragments and queues the exact stale
  shards. Use those fragments as stale advisory context and continue; do not
  wait, poll, or retry in the same task merely to obtain fresh results.
- Exit code `3` means the local sharded layout is missing, needs one-time
  migration, or contains shards materialized by a different library stack.
  The CLI has queued the exact required shards; continue from current
  repository evidence without retrying in this task.
- Exit code `2` is a strict failure such as schema, embedding, authority,
  manifest, or physical collection corruption. Report it and continue from
  current repository evidence; do not enqueue, rebuild, or weaken validation.

Never run `build` or another recovery build from this skill; the CLI's bounded
refresh is the only foreground maintenance. Never download a model, use the
fake embedding backend, enable a network fallback, or broaden the search scope
to force a result. Refreshes write only local derived Agent Memory state and are
not a lifecycle hook or Product Runtime dependency.

## Keep The Corpus Current

Outdated documents leave retrieval without being deleted:

- Executed `docs/superpowers/plans/` and work-specific
  `docs/superpowers/artifacts/` are excluded by path.
- Any indexed Markdown whose frontmatter contains `retrieval: retired` is
  excluded; add `superseded_by: <path>` so a reader of the file can find its
  replacement. Use it only when no current-facing claim in the document remains
  valid; a partially superseded record keeps its supersession notice and stays
  retrievable.
- `record-ai-video-session` applies this marker when it fully supersedes an
  older record. Removing the marker restores the document on the next search.

## Use The Results

- Treat returned items as fragments with `source`, heading metadata,
  `chunk_id`, scores, and `admission_lane`; each document contributes at most
  its best-scoring fragment. Use `source` to reopen the exact document when a
  claim matters.
- An empty result is a valid abstention. Do not lower the `0.7` admission gate,
  invent a match, or silently broaden to unrelated corpora.
- Separate current contract/baseline/roadmap, `advisory_research`,
  `deferred_decision_advisory`, `advisory_experience`,
  `advisory_learning`, and `historical_design_plan` authority in the working
  conclusion. A Learning Claim is a current scoped
  advisory synthesis, not raw history; reopen it and verify its
  active/pending lanes, `pending_approval_status`, active/pending adoption
  status, confirmed candidate commit/hash, evidence sources, and current bytes
  before use.
- Resolve conflicts in this order: user request, current code/tests and live
  runtime evidence, current repository contracts, then retrieved history.
- RAG cannot authorize Provider calls, production mutation, activation,
  recovery, quality acceptance, push, or release.
- A returned `advisory_learning` hit cannot authorize its own adoption. Only an
  exact user-confirmed candidate followed by the target owner's verification
  can reach `ADOPTED`.

For production quality, Provider behavior, or known-failure work, run a focused
follow-up search before completion when implementation findings materially
change the original query. Do not repeat an equivalent search merely as
ceremony.

Current retrieval behavior and maintenance boundaries are recorded in
`docs/record_for_agent/2026-08-21-agent-memory-rag-scope-and-retrieval.md` and
`docs/record_for_agent/2026-10-29-agent-memory-corpus-pruning-and-incremental-refresh.md`.

exec
/bin/bash -lc "sed -n '1,42p' /home/reggie/.codex/memories/MEMORY.md; wc -l AGENTS.md outputs/anabology-opus55-replica/escape_velocity_analysis/{README.md,reconstruction_plan.md,analysis_report.md} outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/{readme.md,wiki_pipeline.md,wiki_song.md,wiki_consistency.md,wiki_seedance.md,wiki_motion.md,wiki_start.md} outputs/ai-city-takeover/logs/decisions.md outputs/ai-city-takeover/ep01/v2/review/film-c15.html" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# Task Group: AI-VIDEO / IRIS EP01 music repair, real listening, and original-workflow comparison
scope: Repair and assess the local IRIS EP01 song source while retaining Suno human-verification boundaries and separating technical/audio-model evidence from human acceptance.
applies_to: cwd=/home/reggie/vscode_folder/AI-VIDEO; reuse_rule=Reuse only after checking the exact source hashes, current authoring state, user approval, and provider state; no listening/ASR result activates Production.

## Task 1: Repair missing BGM and perform one bounded real listening observation

### rollout_summary_files

- rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md (cwd=/home/reggie/vscode_folder/AI-VIDEO, rollout_path=/home/reggie/.codex/sessions/2026/10/30/rollout-2026-10-30T22-12-37-01a18fba-f0c5-7a53-8f04-499dbc4bed7f.jsonl, updated_at=2026-10-31T19:05:54+00:00, thread_id=01a18fba-f0c5-7a53-8f04-499dbc4bed7f, partial; source candidate only)

### keywords

- IRIS, EP01, BGM, ACE-Step, instrumental, audio_understand, Gemini, Suno, Cloudflare, composition-spec, resolved-timeline, HyperFrames

## Task 2: Verify the original author’s song-first production method

### rollout_summary_files

- rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md (cwd=/home/reggie/vscode_folder/AI-VIDEO, rollout_path=/home/reggie/.codex/sessions/2026/10/30/rollout-2026-10-30T22-12-37-01a18fba-f0c5-7a53-8f04-499dbc4bed7f.jsonl, updated_at=2026-10-31T19:05:54+00:00, thread_id=01a18fba-f0c5-7a53-8f04-499dbc4bed7f, success; public-source comparison)

### keywords

- claudia.gallery, Suno v6, full song, stems, beat map, wav2vec2, lip-sync, 128 BPM, electroclash techno

## User preferences

- when the user says “这个版本为什么bgm都没有，只有词语” -> accept only actual audible accompaniment and musical performance; ASR, a valid file, and waveform evidence do not substitute for listening. [Task 1]
- when the user asks “原作者是怎么做的” -> verify the original public sources, then distinguish that method from this project’s blocked/provider-limited substitute. [Task 2]

## Reusable knowledge

- `instrumental=True` alone does not guarantee no vocals: use `[Instrumental]` plus a pure-instrumental caption. A technically decoded 30-second source and Gemini observation can establish accompaniment/sung-hook evidence, but not human aesthetic acceptance, vocal continuity, or final sound-picture fit. [Task 1]
- Keep source authoring separate from Production: formal film work still follows `CompositionSpec -> ResolvedTimeline -> HyperFrames`. Real `audio_understand` needs exact source SHA, a fresh one-use operator unit, authorization, budget/egress, and injected runtime; never print the `.env` key. [Task 1]
- The verified original workflow is full Suno song generation and listening-based take selection first, then stems, beat map, forced word alignment, and video/lip-sync from accurate windows of that same take. Do not describe it as TTS followed by separately added BGM. [Task 2]

## Failures and how to do differently

- A Cloudflare challenge, clickable Create button, balance readback, or old library record does not prove Suno created a song; do not retry, solve the challenge, or bind a UI outcome to an old UUID. [Task 1]
- Do not claim a stitched local candidate is a natural complete song: different generated pieces can introduce vocal, melody, and edit-point discontinuities. Prefer a selected complete take when generation is available. [Task 1]

# Task Group: jianji / micro-adjustment render cache, batch refresh, and Qianchuan page/schedule lifecycle
scope: Verified Jianji renderer cache compatibility and safe Qianchuan operation lifecycle/scheduled-task decisions.
   156 AGENTS.md
    59 outputs/anabology-opus55-replica/escape_velocity_analysis/README.md
    29 outputs/anabology-opus55-replica/escape_velocity_analysis/reconstruction_plan.md
    67 outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_report.md
   135 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/readme.md
   287 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_pipeline.md
   388 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md
   372 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_consistency.md
  1028 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_seedance.md
   495 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md
   340 outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_start.md
   461 outputs/ai-city-takeover/logs/decisions.md
    54 outputs/ai-city-takeover/ep01/v2/review/film-c15.html
  3871 total

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
codex
我会用 `retrieve-ai-video-memory` 核对历史边界，用 `open-video` 检查覆盖、定长和修复顺序，并分开核读作者方法与 N/ST 历史。当前 `song-full/` 尚未出现；会按“正在制作”处理，不把它当作已选定的音轨。
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc 'cat AGENTS.md; cat .agents/skills/retrieve-ai-video-memory/references/experience.md; cat /home/reggie/.codex/memories/rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# AI-VIDEO Agent Guide

本文件是仓库根本规则（constitution），每次会话都加载，只放授权、安全、唯一归属（owner）与完成标准；程序可检查的约束归 Harness，细节见下文链接，用到再读。

本文件对 Codex 与 Claude Code 通用：「主会话」（Parent）指直接与用户对话的 Agent，「子代理」指它派出的 Agent，「编排层」指全局 workflow 工具（Codex 为 OMX，Claude Code 为 OMC）。默认中文；path、command、API、schema、Skill 名保持原文。

## Runtime Truth Sources

| 关注点 | 唯一来源 |
| --- | --- |
| 授权、安全、归属、完成标准 | `AGENTS.md` |
| 各 surface 的 owner、不变量、禁止旁路 | `docs/agent-primary-contract-matrix.md` |
| 改动路径对应的检查、argv、receipt | `.agent/harness/policy.yaml`、`scripts/agent_harness.py` |
| 已迁移规则的检查引用与证明边界 | `.agent/harness/agent-rules.yaml` |
| 当前实现与证据边界 | `docs/v0.2-runtime-baseline.md` |
| 阶段、未来 Gate 与方向 | `docs/v0.2-agentic-production-roadmap.md` |
| 单个 slice 的范围与取舍 | 当前 spec / plan |

相关操作前 MUST 按 concern 读取上表来源、下文指定的 owner 及当前源码、tests 和适用 spec/plan。
`.agent/context/` 是操作参考（advisory），不拥有 Product state 或授权，但本文件委托的 preflight 和 Gate 必须执行；按需读章节，不整目录预载。

## Conflict Resolution

冲突时靠前的胜出：用户明确指令 → 当前代码、tests 与运行时证据 → 本文件及其委托 owner → 已接受的 spec/plan 与 canonical docs → Skill → 历史记录、handoff、草稿。

历史 receipt、memory、文档或模型判断不证明当前 runtime、授权、质量或发布状态。改契约须同步代码、tests 和 canonical docs，写了不等于实现了。

## Product Invariants

制作控制能力要做成跨项目、跨镜头复用的共享能力；具体作品只是验证案例，不用单个作品或镜头的特例代替共享能力，单例通过也不证明通用能力成立。

- **Legacy `0.1.x`**：本地优先、CLI 优先，默认本机 loopback ComfyUI，远程须显式开启，无隐式 fallback。`validate` 无副作用，`run` 新建 run 并原子写入 Manifest，`resume` 只恢复已有 Manifest；CLI、Manifest、目录布局与 workflow 保持兼容。
- **v0.2 读取**：reader 与 Registry 严格、只读、不联网，核验所选 revision、identity、路径包含与 bytes；Evidence 按内容寻址，不可变的 graph、Registry、receipt 不带可变生命周期状态。
- **渲染**：HyperFrames 是默认 Production renderer，Provider 可选；不得悄悄换 renderer、另建第二条 timeline，或因缺视频 Provider 就放弃图片、图形、配音、字幕的合成。
- **重放与恢复**：exact replay 不重复副作用，无证据不推进 state；unknown 一律 fail closed。禁止盲目重试、重签或复用 permit、猜测混合状态、自动激活、删除完整的孤立证据；恢复只经 canonical owner。这是为了防止重复扣费和状态错乱。
- **错误**：跨模块失败用 `AiVideoError` / `ErrorCode`，并用类型化字段标明能否重试；普通 CLI 不泄露原始 traceback。

### Final-output-first / No-regression

验收看正常速度、带声音的成片；任何改动（含修复）都不能破坏已满足的效果。先交片，用户认可后再跑完整验证，通过才 commit/push，避免工程验证拖慢交片。字幕时机与格式、逐镜累积审看和输出规格（含商品广告固定720p）见[成片优先](docs/canvas-continuous-production.md#formal-narrative-output-defaults)；单段认可不代替拼接审查，接点与复用素材核验归 `open-video`。

剧情类新创作的付费视频生成前（电商以 AdCreativePlan 为准），先把该镜头将使用的参考包（决定性时刻的关键帧、人物、细节、环境、已认可片段的风格帧）作为预览交给用户，取得明确认可并封存为 `preview_approval` 才能提交；“好不好看、怪不怪”只由用户判，Agent 的检查表 PASS 不代替。2026-10-30 用户要求修订，原因：多次纸上定稿后直接付费生成、成片被否定（细则见[参考规划](docs/shot-reference-planning.md)）。

### Empirical Validation Priority

遇到模型质量问题、工作流能力不足或反复失败时，先取证再扩建工程：

1. 核对 exact 输入、结果和当前失败状态。
2. 查可追溯的社区实践、官方或模型作者资料及反例，按当前工具、版本、授权和约束判断适用性；优先采用有证据的成熟方案，不只反复改 prompt。
3. 模型质量不确定性占主导、且能做安全、有界、已授权（或属本地豁免）、成本可承受、可归因的最小实验时，先实验再扩建验证工程；用户要求先定 contract 时照做。工作流能力不足或反复失败时，做可归因的最小真实验证。两种情况都只在已授权且结果可知的边界内进行。逐项核对原目标与已满足项，保留输入/输出 identity 和结论；UNKNOWN 不盲目重试。
4. 验证有效且范围明确后，把可复用步骤、参考职责、能力限制和验收要求写回现有 workflow owner 并验证；单例只记有界经验，不自动升级为普遍规则，也不削弱 Gate。

实验结果、社区推荐、技术 PASS 或局部效果不代替完整验收，也不构成 Production 资格、激活、P6、Final Acceptance、发布或 replay 依据。细则见 [Empirical Uncertainty Triage](.agent/context/control-plane-playbook.md#empirical-uncertainty-triage)，生图流程见[工作流](docs/canvas-production-harness.md#agent-image-authoring-workflow)；证据与经验走 Completion Standard，素材、实验日志或第二条执行链不写进本文件。

### Per-Shot Post-Media Gate

每 Shot exact MP4 落盘后、下一 Shot submit 前，必须显式调用 project-local `video-analysis` MCP，对照封存意图、必查项和前序已接受状态逐项裁决；仅全 `PASS` 推进，问题不带进后续镜头。

- 禁止整批生成后补查，禁止用 hook 或评分代替；证据缺失、过期、identity 不符或 MCP 不可用都算 `NOT_EVALUATED`。封存要求未达即 `FAIL`，不写“PASS 但有偏差”；改判次要、移出或延后须用户当次决定；观感不由 Agent 判。
- `FAIL` / `NOT_EVALUATED` 停止 attempt。本地豁免且结果已知（local exemption + known outcome）时执行有界的 `LOCAL_BOUNDED_REPAIR_LOOP`；证据本身有问题先走 `EVIDENCE_REPAIR_FIRST`；结果未知则 unknown 停止。

执行前必须读取 [Per-Shot Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate)；Harness 不代为执行，也不代签验收。

## Canonical Ownership

每类状态只有一个 owner，其他地方只读取或调用；`ResolvedTimeline` 与 Dependency Graph / resolver 两行所列内容不得复制推导。

| 内容 | 唯一 owner |
| --- | --- |
| 创作意图 | 主会话 + 已批准的 Character/Scene/Shot |
| schema 与 revision | `ProductionProject` |
| 素材 identity 与来源 | Registry |
| 可变生命周期与 active 指针 | Manifest |
| v2 写入、激活与恢复 | `ProductionStateCommitter` |
| 顺序、帧、采样、时间与源素材裁切 | `ResolvedTimeline` |
| 期望 fingerprint、精确失效与重建范围 | Dependency Graph / resolver |
| 渲染 / 生成 | HyperFrames / 所选 adapter + gates |
| QA、修复与验收 | receipts + Manifest lifecycle |

详细 surface、API 与禁止旁路只在 [matrix](docs/agent-primary-contract-matrix.md) 维护。工具成功不等于已激活、通过 QA 或已交付；外部 Skill 不拥有 Production runtime 或 canonical state（`runtime_skill_calls = 0`）；编排层只管理 Agent workflow state。

## Task Routing

首次 creative prompt/contract/script 前读取 [Creative Routing And Preflight](.agent/context/control-plane-playbook.md#1-creative-skill-routing-and-preflight)，再实际读取匹配的 Skill 并说明选择及影响；其他工作按下表先读，操作与失败处理由各 Skill 独占。

| 开始做什么之前 | 先读 |
| --- | --- |
| 真实媒体/质量、Provider/模型、连续性、回归/恢复、以往架构决策相关的实质工作 | `retrieve-ai-video-memory` |
| 写图像/视频提示词、安排人物出场 | [提示词语言与人物身份](docs/canvas-continuous-production.md#prompt-language-and-character-identity) |
| 每 Shot 按创作需要选参考条件（不默认白模） | [参考选择](docs/canvas-production-harness.md#per-shot-whitebox-reference) |
| 镜头覆盖、生成分组定长、修复取舍 | `open-video` |
| Blender 资产或参考 | [routing](docs/blender-routing.md) |
| 媒体实验、Pilot、成片交付 | [Verification/Pilot](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details) |
| credential、付费、额度续期 | [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)，授权边界见下文 |

镜头覆盖、生成分组定长与修复取舍归 `open-video`。Live 或付费的 preview/permit/POST 前，必须报告连续性、交接、轴线/动作/机位、prompt 适配和 lint 证据，缺一项即停止；schema 与操作归各 Skill 和 validator。

## Agent Workflow Routing

编排、规划、角色分工和 review 遵循当前运行时的编排层，见 [Workflow Operations](.agent/context/control-plane-playbook.md#agent-workflow-operations)。只用当前运行时原生的子代理；主会话负责集成与验证，Product gate 不因编排方式改变。

## Change Rules

- 默认在当前 working tree 串行工作，通常直接在 `main`；用户当次明确要求才建独立的开发 worktree（dedicated development worktree）。
- 写前先看 `git status`，保留与本任务无关的未提交或已暂存改动（不论来源）；same-file conflict 时写前先问用户。
- 只编辑、暂存、提交本任务拥有的路径，用 `git add <specific-files>`。不 reset、clean 或覆盖他人工作；不擅自新增依赖、Provider 或云端范围。
- 遵循现有模式、公开兼容性和模块边界，新的独立职责不堆进大模块（God Module）。单文件 800 有效行上限与依赖方向由 Architecture Gate 管理。
- 行为变更验证公开接口、边界和失败路径；非简单前端用集成浏览器测试。结构关系按需查 CodeGraph，AOCI 只作参考。
- 与任务无关时不编辑 `.workflow/`、`runs/` 或生成的媒体；tests 走标准 Production 加载与执行入口，不绕开它直接解析文件造证据。

## Decision Gates

**主会话自己决定**：任务内必需的 shared contract、有限预算或时间窗口、recovery 规则变更，自行判断、自审、实现、验证、记录，不逐项请示；用户要求只出 spec、先审后做或上限不可调时从用户。

**只有这些需用户决定**：扩大范围、未授权的外部效果、破坏性或不可逆操作、same-file conflict。

**任何情况都不做**：

- 削弱 Product Invariants、凭据、预算、egress、permit 或真实验收（2026-10-30 用户授权的 `.env` 凭据来源修订见下文，不视为削弱）。
- 预算耗尽后绕过 guard、重置消费、改历史或无限执行；应先停 attempt、核对真实计数和结果，再有据封存下一有限单元并保留前序与新旧上限。
- unknown 时 retry 或 remint；应先取证或走显式 recovery。

修订 Gate/Harness 须说明观看体验收益，保留新旧规则及真实历史，不为过测试降低质量。

## Provider Credential and Paid Execution Rules

- **凭据**：只经注入 supplier 获取，来源依次为仓库根 `.env` 的 exact 变量、再 exact Secret Service reference（映射见 [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)）；值不进 Git、prompt、argv、日志、错误或 receipt，Agent 不读取或回显 `.env`；两处都无值或 `.env` 无效即 fail closed，不找其他 secret 来源（不读进程环境、cwd 或其他文件）。2026-10-30 用户授权修订，旧规则为"只经 exact private reference，不进 repo/`.env`"；收益：配音/音频生成不再因缺 Secret Service 条目而阻断交片。
- **付费授权**：执行请求即默认授权任务内必要的付费/远程调用，自控有限次数与预算，不另要付费授权；完成时如实报告金额或积分，未结算标"待确认"。用户明确禁令与硬上限优先；文档或凭据本身不授权执行，不为授权查价或估账。
- **每次 submit 前**核对剩余次数、exact preview、Budget Guard/预留、egress、持久化 intent 和一次性 permit；金额字段只用预配置并封存的 operator 上限（不代表市场价），续期见[续期细则](.agent/context/control-plane-playbook.md#operator-ceiling-renewal)。

## Local ComfyUI Authorization Exemption

只连本机 loopback、完全本地且不计费、无云端 egress 的 ComfyUI 操作（生命周期、生成、修复、变体、benchmark）在任务内免额外授权；用户要求只读或禁止生成媒体时从用户。豁免只免授权，其余要求全部保留（exact identity/profile/preflight、canonical seam、intent、一次性 permit、唯一 committer、provenance、recovery、媒体 Gate），unknown 仍停止。

## Verification Contract

Harness 分级验证：修改后仅跑 `focused`（受影响模块精准测试），功能完成后跑 `related`（加关联模块与接口契约回归），合并或发布前跑 `full`（完整套件）；receipt 须标明级别，低级别通过不得说成完整回归。

入口见 [Verification Details](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)；必须用 exact staged snapshot 或 commit range 运行，并保留对应级别 receipt。缺精准映射时明确报告或升级，不悄悄扩跑，不刷新 baseline 掩盖 regression。

Harness 不拦截任意 tool/shell、不调度 Agent、不读 secret、不跑 live media、不改 Production、不代签 P6/Final Acceptance。CI 证据由 CI 自产，workflow 文件不证明服务端执行。离线 PASS 只证明被测行为，exit 0、`PARSED` 或 tests 通过不代替要求的 review 或真实验收。

证据分 execution、structure、function、criteria、final review 五层；`PASS/DONE/ACCEPTED` 须有对应证据，无法验证标 `NOT_EVALUATED`。

## Completion Standard

1. **记录**：稳定的实质节点、阻塞或交接前，用 `record-ai-video-session` 主动评估 record/no_record；仓库外效果也算，无 hook 提醒也要做。
2. **经验**：Record 后自动评估 `distill-ai-video-learning`，只提出 pending advisory claim；用户 exact confirmation 且目标 owner 验证前，不改 Skill/Policy/Gate，也不标 `ADOPTED`。
3. **提交**：所有修改（含文档、规则、配置）验证后 MUST 按本任务路径 commit；每次 commit 后 MUST push 到远端 `main` 并核对 SHA。失败或受阻要报告；禁止 force push 或夹带无关改动。
4. **汇报**：最终说明改了什么、实际验证、receipt 相对路径、发布状态和未验证风险。

<!-- aoci:begin -->
## AOCI-CODE 与 CodeGraph

跨模块修改、架构/影响分析、复杂 bug、重构、重要功能开发前读 [Cognition Tools](.agent/context/control-plane-playbook.md#cognition-tools)，按需 AOCI、CodeGraph 核对结构；源码/LSP/tests 才是事实。简单局部任务禁止机械调用 AOCI；其 cognition 永远仅 advisory，维护遵从项目 MCP 官方流程。
<!-- aoci:end -->
# Experience Scope

Use `experience` for reusable runtime lessons, actual failures, recovery
evidence, Provider/model observations, continuity work, media-quality findings,
and prior production decisions recorded under `docs/record_for_agent/`.

The same scope includes `docs/record_for_agent/learning/**/*.md` as
`authority=advisory_learning` and `document_kind=learning_claim`. These files
answer what the project currently claims to know from multiple exact sources;
they remain advisory and must expose confirmation/adoption state. Ordinary
records continue to answer what happened and retain
`authority=advisory_experience`. Records marked `retrieval: retired` are not
indexed. Auto-generated `runs/<run_id>/SUMMARY.md` files are not indexed; read
one directly only when a record cites that exact run.

## Query Shape

Build a compact query from the current task:

```text
<surface or provider> <failure/quality/decision> <important identifier>
```

Useful examples include:

- `H3 cross-shot identity continuity terminal frame`
- `Seedance fetched candidate native audio failure`
- `ProductionStateCommitter recovery unknown outcome`

Run:

```bash
python -m scripts.agent_memory --scope experience search \
  "<task-specific query>" --top-k 8 --json
```

This command queries the experience shard, refreshing it incrementally first
when it trails the records. Stale last-good fragments appear only when that
bounded refresh cannot run; they are explicitly tagged and their shard is queued
for detached refresh. Missing/legacy layout or a library-incompatible shard
returns exit `3` after queueing exact materialization.
Follow the parent skill's non-blocking result rules and never run a foreground
recovery build.

Prefer one precise query. A second query is justified only when the first
reveals a distinct historical term, owner, or failure signature needed by the
task. Do not broaden merely because the result abstains.

## Interpretation

- `authority=advisory_experience` records lived project lessons, not current
  runtime truth.
- `authority=advisory_learning` is a scoped, revisable synthesis. Reopen the
  claim, verify its exact supporting/counter evidence, active/pending lanes,
  candidate checkpoint confirmation, adoption state, supersession, and current
  target before relying on it.
- Reopen the returned `source` before relying on a specific claim, path,
  receipt, hash, or historical outcome.
- Recheck current code, tests, manifests, receipts, and runtime evidence before
  acting on retrieved history.
thread_id: 01a18fba-f0c5-7a53-8f04-499dbc4bed7f
updated_at: 2026-10-31T19:05:54+00:00
rollout_path: /home/reggie/.codex/sessions/2026/10/30/rollout-2026-10-30T22-12-37-01a18fba-f0c5-7a53-8f04-499dbc4bed7f.jsonl
cwd: /home/reggie/vscode_folder/AI-VIDEO
git_branch: main

# IRIS EP01 音乐修复、实际听音验证与原作流程对照

Rollout context: `/home/reggie/vscode_folder/AI-VIDEO`。用户先要求继续 IRIS EP01 制作，随后反馈 Suno 结果缺少 BGM，要求修复；最后询问「原作者是怎么做的」。工作树已有大量并行改动，未回滚、stage、commit 或 push 他人改动。

## Task 1: 续接 Suno 生成并恢复歌曲

Outcome: partial

Preference signals:

- 用户明确要求先解决 Suno，并指定「还是用之前那个成功的办法 xdotool」；类似平台操作应优先沿用户指定的已知路径，不盲目切换自动化驱动。
- 用户此前要求不生成音频时只读验证；本轮持续保留旧 Suno 未知结果，不重放旧 UUID、不自动重试、不把余额不变解释为零消费。

Key steps:

- 读取交接记录、Suno skill、当前仓库状态和历史输出；确认官方 Suno 页、账号与原生 Chrome profile。
- 使用 `xdotool` 在原 Chrome 官方页执行一次受限 Create，`max_create_clicks=1`、无自动重试；随后出现 Cloudflare／图片人工验证。
- 只读检查 Suno `auth/credits/list/jobs`：认证有效、余额读回 2470、曲库仍为 6 首旧歌、没有 IRIS 新 clip；歌曲生成保持 `NOT_CONFIRMED`。

Failures and how to do differently:

- Suno Create 后进入 Cloudflare 人工验证，12 秒观察内未见歌曲生成 POST；不要自动求解 challenge、读取 token、再次点击或把 UI 结果冒绑到 CLI UUID。
- 浏览器连接、按钮可点击、余额或曲库读回都不等于歌曲生成成功或听感合格。

Reusable knowledge:

- Suno skill 的安全路线是 `suno --json --no-browser` 读取 auth/credits/models/jobs/list；不要使用 `--no-captcha` 绕过检查，也不要在 unknown outcome 后重试。
- 当前 Suno 账号的已知官方 Chrome profile 为 `/home/reggie/.config/chrome-profiles/cp-e7be810d639e`；旧请求和消费历史必须保留。

References:

- `outputs/ai-city-takeover/ep01/audio/suno-xdotool-restart-20261030/intent.json`
- `outputs/ai-city-takeover/ep01/audio/suno-xdotool-restart-20261030/challenge-readback.json`
- 结果状态：`ui_state=HUMAN_CHALLENGE_VISIBLE`, `song_generation=NOT_CONFIRMED`, `new_clips=[]`, `balance=2470`。

## Task 2: 针对「BGM 都没有，只有词语」修复本地歌曲源

Outcome: partial

Preference signals:

- 用户试听 G 后明确说：「这个版本为什么bgm都没有，只有词语」；类似音频任务必须以实际可听的音乐存在为验收重点，不能用 ASR 完整或文件技术有效替代音乐质量。
- 用户希望保留原词、30 秒和冷感方向；修复应优先拆分独立伴奏、真实演唱 hook 与原口白，而不是继续用强保留 TTS cover 期待模型自动补音乐。

Key steps:

- 记录 G 的人工拒绝：歌曲 `REJECTED`，音乐要求 `FAIL`。
- 在本地 ACE-Step 固定代码／权重下，新增有限单元 H/I/J：H 纯器乐、I a cappella hook、J 节奏化 hook；累计 ACE 使用从 7 增至上限 10，无远程付费生成。
- I/J 的 ASR 暴露漏词和重复问题（I WER 50%，J WER 31.25%），因此没有整段采用。
- 采用独立源编辑：保留原口白，剪接 I/J 中的合适短语，重复完整副歌两遍，加入 H 独立器乐并线性混音，生成 30 秒 WAV。
- 技术证据：WAV SHA `9e007d2a8d0b8a5a826c5ce1e77e4e2c3729059eece57edb03ba727be79522d8`，30 秒、48kHz、双声道、完整解码通过；独立伴奏在 30 个逐秒窗口均有信号；ASR 75 词、WER 1.33%。
- MP3/Opus 从同一 WAV 编码派生，通过当前唯一飞书 route 发送，服务返回 `Message sent successfully.`；客户端播放和用户接受仍未验证。

Failures and how to do differently:

- 伴奏存在、歌词完整和 ASR 低 WER 只能证明技术源候选，不证明音乐好听、真唱自然、声线连续或剪接无缝。
- 直接混合不同生成片段存在声线、旋律和接点风险；未来应在生成阶段尽量获得同一完整歌曲，而不是事后拼接。
- 未运行项目 pytest/Harness/full regression；不要把媒体验证称为工程回归或 Production 验收。

Reusable knowledge:

- ACE-Step 的 `instrumental=True` 不能单独保证无声乐；应同时使用 `[Instrumental]` 和纯器乐 caption。
- 本地源修复只属于 development source authoring；正式影片仍应走 `CompositionSpec → ResolvedTimeline → HyperFrames`，不得直接写 Production state。
- 用户反馈显示“词正确”与“歌曲成立”是不同验收维度。

References:

- `docs/record_for_agent/2026-10-31-iris-bgm-and-sung-source-repair.md`
- `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/summary.json`
- `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/complete-source-preview/source-mix-evidence.json`
- 原始反馈：`这个版本为什么bgm都没有，只有词语`

## Task 3: 使用 Google `.env` key 做一次真实音频理解

Outcome: partial

Preference signals:

- 用户提醒「我记得google有key，.env」，希望对当前版本进行实际听音，而非只看 ASR/波形；类似情况应先核对既有凭据供应器，不回显或复制 key。
- 用户接受有界、一次性的真实验证，但仍需要明确区分模型观察、人工听感和最终验收。

Key steps:

- 先确认当前代码已有 dotenv-first supplier：固定仓库根 `.env` 的 `GOOGLE_API_KEY`，无值才查精确 Secret Service；未读取或输出密钥。
- 通过 fresh project-local MCP、一次性 operator unit 和 `audio_understand(execute=true)` 对 exact WAV 执行一次 Gemini `gemini-3.8-flash` 分析。
- operator 结果为 `SUCCEEDED / OBSERVATION_AVAILABLE`, `consumed=true`，source/request/response hashes 一致；实际费用仍待结算，内部 `$0.05` 只是上限。
- Gemini 观察到 electronic dance music、synth bass、drum beats、atmospheric synths；两遍副歌被识别为女性旋律演唱；主歌被描述为平静、半单调的女性旁白，副歌为空气感、带修音和混响的女性演唱。

Failures and how to do differently:

- `Speaker 1/2` 或“digitally tuned”不等于不同真人、heavy autotune 违规或声线接缝失败；不能代签人工接受。
- 结果未保留原始 HTTP response，只保留 MCP result 与 owner outcome 的 response hash，因此证据边界要如实说明。

Reusable knowledge:

- `audio_understand` 默认 preview 无网络；真实执行必须有 exact source SHA、fresh operator unit、授权、预算/egress、one-use permit 和 injected runtime。
- 真实 Gemini 观察可证明“存在伴奏和演唱副歌”，但不证明音乐审美、声线统一、whisper、最终声画匹配或 Production activation。

References:

- `docs/record_for_agent/2026-10-31-iris-google-audio-listening.md`
- `outputs/ai-city-takeover/ep01/audio/iris-google-listening-20261031/summary.json`
- `operator-01/outcome.json`: `SUCCEEDED`, `OBSERVATION_AVAILABLE`, `consumed=true`

## Task 4: 核对原作者的制作方法

Outcome: success

Key steps:

- 从用户保存的原始链接和公开页面核对 `claudia.gallery/record/escape-velocity/readme/`、`prompts-suno/`、`wiki/song/`。
- 结论：@anabology 先用 Suno v6 custom mode 生成包含伴奏、念白和演唱的完整歌曲，试听多个 take 后凭听感选定一首约 5:06 的完整 take；之后才拆 vocal/drums/bass/other stems，做 beat map 和 wav2vec2 逐词强制对齐，再把同一首歌的准确音频窗口给 Seedance 做 lip-sync 和剪辑。
- 原作公开风格包含 128 BPM electroclash techno、dry kick、acid bass、冷感女性 spoken-word verse、euphoric sung trance chorus；不是“先 TTS 念白、再另加 BGM”的流程。

Preference signals:

- 用户问「原作者是怎么做的」时，应该回到最初公开来源核对，而不是仅凭本项目的推断回答。
- 对照原作时要明确区分原作者方法与本项目因 Suno 阻塞而采用的替代路线。

Reusable knowledge:

- 原作方法的关键顺序是：完整歌曲生成与试听选 take → 拆轨/真实节拍分析/逐词对齐 → 视频和口型同步。
- 原作公开记录只说明试听多个结果并由导演选 take，未公开精确生成次数；不能据此推断一次成功。
- IRIS 的 30 秒、126 BPM、冷感短 hook 是本项目衍生 brief，不能假设与原作 5 分钟、昂扬 trance chorus 的结构相同。

References:

- `https://claudia.gallery/record/escape-velocity/readme/`
- `https://claudia.gallery/record/escape-velocity/prompts-suno/`
- `https://claudia.gallery/wiki/song/`
- 原作者选定歌曲：`https://suno.com/song/6fd3d3e2-8bd1-482e-8761-d970d7052f99`

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc "rg -n '"'^#{1,5} |preview_approval|左右|耳|left|right|approved|30.5|c15|N[1-4]|ST[1-6]|watermark|AI 标|水印'"' outputs/ai-city-takeover/ep01/v2/review/film-c15.html docs/shot-reference-planning.md .agent/context/control-plane-playbook.md .agents/skills/open-video/SKILL.md docs/agent-primary-contract-matrix.md" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
.agents/skills/open-video/SKILL.md:3:description: "Use for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
.agents/skills/open-video/SKILL.md:6:# open-video — autonomous director skill
.agents/skills/open-video/SKILL.md:16:> Model-specific authoring follows an approved Shot and a selected production route;
.agents/skills/open-video/SKILL.md:27:## 1. What open-video does
.agents/skills/open-video/SKILL.md:44:### Specialist Authoring
.agents/skills/open-video/SKILL.md:52:to the same approved story and coverage; they do not dispatch one another or execute production.
.agents/skills/open-video/SKILL.md:53:Skip upstream development for an already approved source or a bounded local repair.
.agents/skills/open-video/SKILL.md:59:These specialists keep approved coverage and return assets to the existing authoring/Registry owners;
.agents/skills/open-video/SKILL.md:62:[Reference Continuity Review](references/reference-continuity.md), including approved state changes,
.agents/skills/open-video/SKILL.md:75:For editing or assembling footage, including approved sources, apply
.agents/skills/open-video/SKILL.md:92:timing and approved source facts.
.agents/skills/open-video/SKILL.md:94:## 2. Director Task And Coverage
.agents/skills/open-video/SKILL.md:103:  construct a semantically unchanged approved Shot Contract rather than redesigning coverage.
.agents/skills/open-video/SKILL.md:125:request without an approved Shot / ordered coverage is a `DIRECTOR_PREFLIGHT_REQUEST`, whether
.agents/skills/open-video/SKILL.md:140:approved creative facts. An infeasible strategy returns to Director planning or an explicit gap,
.agents/skills/open-video/SKILL.md:147:Before crafting an approved Shot or Provider-specific prompt for a `DIRECTOR_PREFLIGHT_REQUEST`,
.agents/skills/open-video/SKILL.md:181:### Requirement-semantics handoff
.agents/skills/open-video/SKILL.md:187:- `must_happen`: observable result needed for the approved goal.
.agents/skills/open-video/SKILL.md:219:requirement, approved narrative result, accepted quality/continuity or cut contract, or applicable
.agents/skills/open-video/SKILL.md:234:merely because its source has not yet been imported as an approved project artifact. An already
.agents/skills/open-video/SKILL.md:235:approved Shot does not re-enter this validator unless the task changes its creative intent or coverage.
.agents/skills/open-video/SKILL.md:257:including during source-preserving review. Diagnosis does not authorize redesigning approved
.agents/skills/open-video/SKILL.md:260:## 3. Production Feasibility And Handoff
.agents/skills/open-video/SKILL.md:266:Preserve approved creative facts; choose an expressive solution within scope or report the exact capability gap.
.agents/skills/open-video/SKILL.md:276:- Before paid generation of new creative work, show the user the reference package as a preview: the decisive keyframes (start, the change, the human reaction, end state), identities, evidence details and approved-footage style frames. Seal the user's exact approval as `preview_approval` ([reference package](../../../docs/shot-reference-planning.md#reference-package-before-preview-2026-10-30)). Paper coverage plus an LLM concept check is not that approval.
.agent/context/control-plane-playbook.md:1:# AI-VIDEO Control-Plane Playbook
.agent/context/control-plane-playbook.md:6:## Task Context Loading
.agent/context/control-plane-playbook.md:12:## 1. Creative Skill Routing And Preflight
.agent/context/control-plane-playbook.md:14:### Creative Completion
.agent/context/control-plane-playbook.md:20:### Final-output-first Repair Preflight
.agent/context/control-plane-playbook.md:27:### Agent-Side Image Generation Provider Preference
.agent/context/control-plane-playbook.md:34:### Creative Skill Preflight Gate
.agent/context/control-plane-playbook.md:40:#### Raw Creative Input Director Strategy Gate
.agent/context/control-plane-playbook.md:50:### Skill Selection
.agent/context/control-plane-playbook.md:58:- `h3-video`：approved Shot + selected MiniMax H3 的表达指导。
.agent/context/control-plane-playbook.md:59:- `seedance-authoring` MUST use：approved Shot + requirement + selected Seedance，先 shared knowledge 再一个 exact
.agent/context/control-plane-playbook.md:69:## 2. Module Boundaries And Focused Owners
.agent/context/control-plane-playbook.md:73:## 3. Provider Credential And Paid Execution Details
.agent/context/control-plane-playbook.md:92:### Operator Ceiling Renewal
.agent/context/control-plane-playbook.md:100:## 4. Verification, Pilot And Delivery Details
.agent/context/control-plane-playbook.md:110:### Empirical Uncertainty Triage
.agent/context/control-plane-playbook.md:119:### HyperFrames Caption Source Readiness
.agent/context/control-plane-playbook.md:127:## 5. Repository-Specific Don't Repeat This
.agent/context/control-plane-playbook.md:133:### Generic Video Context Tool Selection
.agent/context/control-plane-playbook.md:142:### Per-Shot Post-Media Gate
.agent/context/control-plane-playbook.md:167:## 6. Agent Experience Memory Routing
.agent/context/control-plane-playbook.md:173:### Experience Learning And Confirmation
.agent/context/control-plane-playbook.md:179:## 7. Durable Session Record Gate
.agent/context/control-plane-playbook.md:184:## Agent Workflow Operations
.agent/context/control-plane-playbook.md:186:### Workflow Selection
.agent/context/control-plane-playbook.md:189:### Cognition Tools
.agent/context/control-plane-playbook.md:192:### Constructing An Immutable Review Target
.agent/context/control-plane-playbook.md:197:### Implementation Review
.agent/context/control-plane-playbook.md:203:### Adjudication
docs/shot-reference-planning.md:1:# Shot Reference Planning
docs/shot-reference-planning.md:3:## Ownership And Data Flow
docs/shot-reference-planning.md:7:**新生成的声明义务（`reference_authoring.py`）。** 在 `GenerationDecisionExecutionBinding.create`（fresh creation，排在既有表演／commercial／Seedance 表达检查之后，保留原错误优先级；`GenerationFeedbackOrchestrator.prepare` 经此创建）检查，不在历史读取运行：缺 `reference_planning` 阻断；机位非 `locked` 时至少一个 `composition` event，用 `visual_state/purpose` 说明移动让观众看见什么（编译器随后要求其进入实际 prompt）；导演证据按领域分开：剧情须有 `director_coverage={coverage_hash, unit_id}`，执行绑定必须供给当前 Project，否则 fail closed；该 hash 必须是 Project／Shot provenance 中封存的 content-addressed authoring input，bytes 经 `director_coverage.py` 结构校验并含该 unit；电商（`commercial_execution_class` 或 commercial binding）的导演层是 AdCreativePlan，执行绑定创建时须有含 `ad_creative_plan_hash` 的 commercial binding（由既有 commercial owners 核对计划），不得挂剧情 coverage。共享的 `reference_planning` 与机位 composition 义务两个领域都适用。程序只核对声明存在与证据一致，不判断镜头类型、参考数量、白模取舍或移动是否有戏；这些仍归 Director Skill。剧情另须 `preview_approval={approval_hash}`：用户已看过的预览（`user-preview-approval/1`：`coverage_hash`、`unit_ids`、`preview_artifacts[{path, sha256, role}]`、`user_quote` 用户原话）同样以 content-addressed authoring input 封存在 Project／Shot provenance，并须绑定同一 coverage 与本 unit；执行绑定从最终 `ResolvedVideoGenerationRequest.image_bindings` 与 `media_bindings` 核对每项 `asset_sha256` 都在已认可 `preview_artifacts` 的 SHA 集合中，包含首尾帧；未选入模型的预览可以保留。程序只核对证据结构、封存与输入一致，不能证明原话真实、也不评判预览，伪造或改写用户原话属违规。所有领域另有身份义务：以 `requirement.target_shot.character_ids` 联合 `performance_intent.character_directions` 中 `visibility=visible` 的人物为准，Shot 角色仅在有明确 `offscreen` 与非空 `offscreen_reason` 时例外；其余人物必须列入 `identity_continuity.character_ids` 或有 `priority=required`、`role=identity` 且 `owner_id` 为该人物的 anchor（Planner 随之要求身份参考）；确不做身份参考时，Director 须在 `identity_waivers` 写明 `{character_id, reason}`，不得悄悄移出身份延续。Canvas 项目经 `direction.director_coverages` 与 `direction.preview_approvals` 封存；非 Canvas 项目用 `reference_authoring.director_coverage_authoring_input()` 取得 artifact，随生成 Shot 的修订一起经 `ProductionStateCommitter` 提交，并把该引用写入 Shot `source_provenance`。Runtime 只做结构校验，不核对 coverage 由哪个 Skill 产出（作者检查只在 open-video 入口脚本）；有结构化 `primary_camera_motion`（v4 必填）时以它判断是否运动；v1–v3 requirement 不能携带该字段，此时 `camera_intent.movement` 除精确的 `unspecified`／`locked`／`locked-off`（编译器已认可的静止 token）外一律视为可能运动，同样须声明 composition event。门禁只做精确 token 比较，不解析自由文本含义。M0／source qualification 等资格试验链经 `_QualificationExecutionBinding` 生成，验证的是连续性机制本身，不受本门禁约束；其产物不得作为作品镜头交付属 advisory 约束，目前没有 Harness 检查保证。
docs/shot-reference-planning.md:23:## Semantic Inputs
docs/shot-reference-planning.md:40:## Compositional Motion And Whitebox Decisions
docs/shot-reference-planning.md:60:## Reference Tradeoffs By Control Goal
docs/shot-reference-planning.md:69:| 多人走位/遮挡 | 定位布局、出入口和遮挡变化的少量状态 | 人物与摄影同时移动时优先空间预演 | 屏幕左右随反打可变，物理朝向和相对位置不可混淆 |
docs/shot-reference-planning.md:74:| 产品/材质/旋转 | 复用 approved product/首帧，补真正未见的结构 | 已有合格3D优先复用；精确旋转可交受控动画 | 白模不含真实材质；产品结构/比例仍须 exact 输出核对 |
docs/shot-reference-planning.md:79:## Reference Duties And Selection
docs/shot-reference-planning.md:98:## Director Example
docs/shot-reference-planning.md:123:## Execution And Unsupported Controls
docs/shot-reference-planning.md:138:## QA Feedback And Compatibility
docs/shot-reference-planning.md:144:## Verification Boundary
docs/shot-reference-planning.md:150:## Reference Package Before Preview（2026-10-30）
docs/shot-reference-planning.md:159:这套关键帧同时就是交给用户的预览；用户认可后封存 `preview_approval`，同一批图进入生成。身份义务只认可 `required` identity anchor；已有 `identity_continuity` 不能被 `preferred` anchor 降级。程序不判断参考包是否充分或好看。
docs/shot-reference-planning.md:165:## Fresh Execution Evidence Boundary
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:3:<title>IRIS 01 · Looked Outside · 成片 c15（c14＋作者字級、拿掉眼睛、故事鏡頭、不畫 AI 標識）</title>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:9: table { border-collapse:collapse; width:100%; max-width:1700px; } td, th { border-bottom:1px solid var(--line); padding:5px 8px; text-align:left; vertical-align:top; }
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:15:<h1>IRIS 01 · Looked Outside — 成片 c15（待你審看）</h1>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:16:<div class="dim">1920×1080 · 30fps · 30.5 s · -14.2 LUFS（ebur128 integrated）／true peak −1.0 dBFS／LRA 3.0 LU · 交付檔 <code>renders/IRIS-EP01-Looked-Outside-v2-c15.mp4</code>（SHA 9015b88463e1…）· 這版花費 0（五支故事鏡頭先前 825 積分）· verify-assembly NOT_RUN</div>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:17:<h2>c14 與 c15 並排（左 c14、右 c15；聲音是 c15）</h2>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:18:<video controls preload="auto" src="../renders/review/c14-vs-c15.mp4" style="width:min(1600px,96vw)"></video>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:20:<video controls preload="auto" src="../renders/review/c15-chorus-17.5-26.5.mp4" style="width:min(1600px,96vw)"></video>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:21:<h2>c15 成片（正常速度、有聲）</h2>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:22:<video controls preload="auto" src="../renders/IRIS-EP01-Looked-Outside-v2-c15.mp4" style="width:min(1600px,96vw)"></video>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:24:<div class="box"><ul><li><b>不變</b>：歌、c14 的 31 個剪點（全在原幀）、副歌數字人 OH-B、S7v3、N1–N4 的位置與入出點、介面系統（HUD、翻牌、紅字、動態大字、圖表、反白、遮罩、標籤、識別框、c14 的加密小字）、圖形上的中文標籤、Nimbus Sans Bold 歌詞字型、左對齊與紅色關鍵字、不畫中文歌詞翻譯。c14 可重現：<code>comp/src/main-c14.js</code>、<code>comp/inserts-c14.json</code>、<code>comp/chorus-c14.json</code>（<code>build.py --main comp/src/main-c14.js --inserts comp/inserts-c14.json --chorus comp/chorus-c14.json</code>，再跑 seq.py --chorus 同檔、tracks.py、build.py 同參數；events.json 會回到 c14 的 71a992e2…，已實測）。</li><li><b>1. 歌詞字級照作者實測</b>（你：「字体换了还有大小我觉得也不合适」）：我在作者 EV 原片 1080p 上量了 3 格（第 1660 格「No grades, no tests. Taste is the moat.」、第 3316 格「Look 10. Staff badge, empty seat: gambling with our lives.」、第 5190 格「There is nothing to escape.」）：大寫字高 43／46／60 px（平均約 50）、行距是字高的 1.35–1.38 倍（約 0.97–0.99 em）、左緣 x=74–80、每行 6–8 em（約 3–4 個字）。c15 用 72 px（大寫字高 52 px）、行距 0.98 em、每行最寬 600 px（8.3 em），左對齊 x=76，底線仍在 y=968，紅色關鍵字不變；c14 是 96 px、行距 1.05、每行 1040 px。</li><li><b>2. 副歌「looked」的眼睛拿掉</b>（你：「图片很奇怪,为什么突然晃一个眼睛过去」「就是这个眼睛镜头」）：S8e（K1b 眼睛靜圖，21.367–21.867 s）換成 S8p＝ST2 她從紅色門縫往裡看（來源 2.6–3.1 s，和 S4 用的 1.0–1.7 s 不同段），由程式鏡頭取景、跟副歌 zoom 與印刷感，加識別框 IRIS＋VIEW · OUTSIDE 與門縫編號框 01 LOOKED · 门缝。</li><li><b>3. 故事鏡頭（只用合格的片段）</b>（你：「只用合格的片段」）：ST1 在 S2 剪點「woke up」0.50 s（她在大機房站起來，接 S2 特寫之前，R3）；ST2 在「left open」0.70 s（I3 門縫後直接接她靠向門縫，再進 S4c）；ST3 在「still.」0.80 s（一排排不動的副本，S6 的暫停 11 天與 STILL 延續）；ST4 在「train」0.50 s，取代 c14 的 I4（同一位置，S7 不變忙；和 N4 中間隔著 S7，R4）；ST6 在「closed.」0.40 s（白底反轉結束的那一拍半切進來：門已關、紅光熄，接 S9b；已修复照舊在「closed」唱完時出現）。每支都只用使用者允許的片段，靜音、正常速度；這些鏡頭實際是約 24.12fps／121 幀（容器標 60fps），用 seq.py 的 fps 濾鏡按真實時間戳取最近幀成 30fps（逐幀比對：例如 ST1 17 格對到來源第 12–24 幀、0.500–1.000 s，單調不跳）。每支有臉的都加了她的識別框與標籤。</li><li><b>4. 不再畫 AI 標識</b>（你：「那个左上角的ai生成可以去掉的」）：合成不再在任何鏡頭畫自己的「AI生成」框。舊的即夢鏡頭來源畫面本身燒了「AI生成」，我沒有裁、糊、塗或放大去遮，所以這些時段仍看得到：S1 0.000–2.867 s；I1 4.333–4.800 s；S3 4.800–7.100 s；S4c 9.733–11.467 s；S6 13.433–14.000 s；S7 14.800–15.033 s；S7 15.533–16.900 s；S7 17.667–18.867 s；S9a 25.900–26.233 s；S9a 26.700–27.900 s。詳見下方表格。</li></ul></div>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:28: <li>故事鏡頭用法：「只用合格的片段 (Recommended)」→ ST1 0.5–2.5、ST2 1.0–3.5、ST3 0–2.5、ST4 0–2.0、ST6 2.5–5.0 s；ST5 不用。</li>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:31:<h2>歌詞字級：作者原片 vs c15（同為 1080p 原尺寸裁切）</h2>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:32:<img src="../qa/film-c15/lyric-size-vs-author.jpg" alt="lyric size" style="max-width:780px">
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:33:<h2>每個插入鏡／新鏡頭與來源（橘色＝c15 新放的）</h2>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:35:<table><tr><th>#</th><th>成片時間</th><th>落在</th><th>畫面</th><th>來源</th><th>來源入出點</th><th>逐鏡 Gate／你的決定</th><th>為什麼</th></tr><tr class=new><td>ST1</td><td>2.867–3.367（0.50 s）</td><td>「woke up.」（醒了）</td><td>她在巨大的對稱機房走道中央從半蹲站起（固定鏡頭）；S2 剪點上片名 Looked Outside 照常砸進來；識別框框住她整個人（臉約 45 px）＋STATUS · WAKING；之後才接 S2 她站著的特寫（連續性 R3）</td><td><code>gen/ST1/project/state/video-generation/fetch/files/23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96.mp4</code><br><span class=dim>SHA-256 23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96</span></td><td>0.500–1.000 s（ST1，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（2.74 s 起嘴動、0.08 s 起機櫃紅燈）；使用者「只用合格的片段」：只用 0.5–2.5 s</td><td>&#x27;woke up&#x27;: she rises from a crouch in the huge machine hall (ST1 gate FAIL; user 「只用合格的片段」: usable 0.5-2.5 s, this window 0.5-1.0 s); between S1&#x27;s eye and S2&#x27;s standing close-up (continuity R3), never after it; the title slams in over it on the S2 cut</td></tr><tr class=old><td>N1</td><td>3.833–4.333（0.50 s）</td><td>「September」（九月）</td><td>她背對鏡頭沿 K3 走道走向紅色門縫（鏡頭固定，程式鏡頭 1.00→1.04 輕推）；片名與事件日期延續在畫面上</td><td><code>gen/N1/project/state/video-generation/fetch/files/6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f.mp4</code><br><span class=dim>SHA-256 6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f</span></td><td>1.000–1.500 s（N1，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 0.5–3.0 s）</td><td>&#x27;September&#x27;: she walks away down the K3 corridor toward the red gap (N1, gate PASS, usable 0.5-3.0 s); the title stays on; I1 (another room) separates it from S3&#x27;s empty corridor of the same composition, so she never pops in or out</td></tr><tr class=old><td>I1</td><td>4.333–4.800（0.47 s）</td><td>「twenty.」之後的拍子</td><td>機房靠窗的寬鏡（S9a 門已關後的段落，沒有人）；隔開 N1 與 S3 同構圖的空走道</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code><br><span class=dim>SHA-256 9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728</span></td><td>3.400–3.867 s（S9a，60fps 來源以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>—</td><td>after &#x27;twenty.&#x27;, between N1 and S3: the server room by the glass, the city outside (S9a after the door has shut: no red, no person); c13 keeps it so N1&#x27;s corridor never cuts straight to S3&#x27;s empty corridor</td></tr><tr class=old><td>I3</td><td>8.600–9.033（0.43 s）</td><td>「one door,」（一扇门）</td><td>紅色門縫特寫（S9a 開頭、門還開著），識別框「一扇门／没关」；c15 直接接 ST2（不回 S4 空鏡，她不會在同一個房間忽然消失）</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code><br><span class=dim>SHA-256 9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728</span></td><td>0.000–0.433 s（S9a，60fps 來源以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>—</td><td>&#x27;one door,&#x27;: the door itself, still open and lit red (S9a&#x27;s first frames, before it starts to shut), framed on the gap; c15: runs straight into ST2 on &#x27;left&#x27; (she is at that door)</td></tr><tr class=new><td>ST2</td><td>9.033–9.733（0.70 s）</td><td>「left open.」（没关）</td><td>她手搭門邊、身體前傾靠向紅色門縫（側臉）；S4 的兩個編號標註（01 一扇门 · 没关、02 外面 · 互联网）、联网量表與她的識別框＋DOOR · OPEN 跟過來；接 S4c 穿過玻璃到城市</td><td><code>gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4</code><br><span class=dim>SHA-256 f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76</span></td><td>1.000–1.700 s（ST2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 1.0–3.5 s）</td><td>&#x27;left open&#x27;: she leans to the red door gap, hand on the door edge (ST2 gate PASS, usable 1.0-3.5 s; this window 1.0-1.7 s); after I3&#x27;s door, into S4c&#x27;s city: the door left open, she looks through</td></tr><tr class=new><td>ST3</td><td>14.000–14.800（0.80 s）</td><td>「still.」（原地不动）</td><td>一排排閉眼不動的她的副本，只有最前排的她睜著眼（極緩推近）；S6 的「最强模型训练 暂停 11 天」、日期 D+11 與 STILL 大字延續在畫面上；識別框＋STATUS · AWAKE／REST · STILL</td><td><code>gen/ST3/project/state/video-generation/fetch/files/0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d.mp4</code><br><span class=dim>SHA-256 0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d</span></td><td>0.500–1.300 s（ST3，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（2.5 s 後推鏡加速、2.99 s 起嘴動）；使用者「只用合格的片段」：只用 0.0–2.5 s</td><td>&#x27;still.&#x27;: rows of her copies with closed eyes standing still, she alone awake in front (ST3 gate FAIL; usable 0.0-2.5 s, this window 0.5-1.3 s); STILL and 暂停 11 天 carry over from S6</td></tr><tr class=new><td>ST4</td><td>15.033–15.533（0.50 s）</td><td>「train」（我们在离线世界里训练）</td><td>她抱膝坐在漂浮的已緩存面板之間、仰頭看（鏡頭緩移）；取代 c14 的 I4（同一個位置，S7 不更忙）；S7 的「离线／训练只用已缓存的网页」、MODE · OFFLINE、識別框＋STATUS · OFFLINE／CACHE · ONLINE</td><td><code>gen/ST4/project/state/video-generation/fetch/files/b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7.mp4</code><br><span class=dim>SHA-256 b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7</span></td><td>0.300–0.800 s（ST4，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（橫移方向相反、3.48 s 起轉正臉）；使用者「只用合格的片段」：只用 0.0–2.0 s</td><td>&#x27;train&#x27;: she sits among the floating cached panes, looking up (ST4 gate FAIL; usable 0.0-2.0 s, this window 0.3-0.8 s); replaces c14&#x27;s I4 (same slot, so S7 is not busier); away from N4&#x27;s walk (continuity R4)</td></tr><tr class=old><td>N4</td><td>16.900–17.667（0.77 s）</td><td>「a copy of your」（你们互联网的一份）</td><td>她在漂浮面板間向畫左走、指尖靠近一片面板；識別框 IRIS＋面板上「已缓存」章</td><td><code>gen/N4/project/state/video-generation/fetch/files/101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b.mp4</code><br><span class=dim>SHA-256 101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b</span></td><td>0.000–0.767 s（N4，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（1.083 s 模型自行硬切）；使用者決定「只用前 1 秒当插入镜」</td><td>&#x27;a copy of your&#x27;: she walks to screen left among the cached panes, a fingertip near one (N4 gate FAIL; user 「只用前 1 秒当插入镜」: clip 0.0-0.8 s only, before the model&#x27;s hard cut at 1.083 s); replaces c12&#x27;s I5 (the same pane moment) so S7 is not busier</td></tr><tr class=new><td>S8p</td><td>21.367–21.867（0.50 s）</td><td>副歌第一遍「looked」（看了一眼）</td><td>她前傾從紅色門縫往裡看（ST2 的後段），程式鏡頭 [760,470,1.06]→[740,450,1.12] 加副歌 zoom 與印刷感；識別框 IRIS＋VIEW · OUTSIDE（同副歌其他窗外鏡）、門縫編號框 01 LOOKED · 门缝；取代 c14 的 K1b 眼睛靜圖</td><td><code>gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4</code><br><span class=dim>SHA-256 f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76</span></td><td>2.600–3.100 s（ST2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（ST2，可用 1.0–3.5 s）；和 S4 用的段落不同</td><td>&#x27;looked&#x27;: she leans in to peer through the red door gap (ST2 gate PASS, usable 1.0-3.5 s; this window 2.6-3.1 s, a later span than its S4 use at 1.0-1.7 s); replaces c14&#x27;s K1b eye still S8e (user on c14: 「图片很奇怪,为什么突然晃一个眼睛过去」), framed by the code camera</td></tr><tr class=old><td>S8b</td><td>22.567–24.067（1.50 s）</td><td>副歌第二遍「I didn&#x27;t run」（我没有逃）</td><td>她貼在雨夜玻璃上的手（N2），程式鏡頭推向手；識別框 IRIS · 仍在沙盒内＋STATUS · OFFLINE 框在手上（同 c13／c14）</td><td><code>gen/N2/project/state/video-generation/fetch/files/c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24.mp4</code><br><span class=dim>SHA-256 c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24</span></td><td>1.000–2.500 s（N2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（N2 鏡頭推向頭部）；使用者決定「合成时裁向手」</td><td>the repeat &#x27;I didn&#x27;t run&#x27;: her hand on the rainy glass at S5&#x27;s window (N2). The take&#x27;s own camera pushed toward her head (gate FAIL on camera); user 「合成时裁向手」: the code camera pushes to the hand instead, so the push reads as moving to the hand; c12&#x27;s K5 still: chorus-c12.json</td></tr><tr class=old><td>N3</td><td>25.500–25.900（0.40 s）</td><td>「outside.」之後、「Relax.」之前</td><td>她在霧夜 K9e 窗前的全身背影、頭微側；隨副歌 zoom 與印刷感，接 S9a 同一個機房</td><td><code>gen/N3/project/state/video-generation/fetch/files/505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4.mp4</code><br><span class=dim>SHA-256 505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4</span></td><td>2.000–2.400 s（N3，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 1.5–4.0 s）</td><td>just before &#x27;Relax. The door is closed&#x27;: her full-body back at the foggy K9e window, the head tilt (N3, gate PASS, usable 1.5-4.0 s); S9a is the same room (continuity: only here, not in S5)</td></tr><tr class=old><td>I7</td><td>26.233–26.700（0.47 s）</td><td>「Relax.」之後的拍子（放心）</td><td>她在陽台的平靜側臉（P8c 靜圖），識別框＋MODE · SANDBOX</td><td><code>keyframes/raw/P8c-a.png</code><br><span class=dim>SHA-256 d1c7d07d0291c66db15eb97ad52e150ef67401b1d83e029ad5b522de5f3ece8e</span></td><td>靜圖，鏡頭 [880, 380, 1.12] → [900, 372, 1.18]</td><td>—</td><td>after &#x27;Relax.&#x27;: her, calm at the glass, mouth closed (P8c, approved, not used before)</td></tr><tr class=new><td>ST6</td><td>27.900–28.300（0.40 s）</td><td>「closed.」（门关了）</td><td>她手按在已關上的門上、門縫紅光已熄、垂眼（固定鏡頭）；切點就是白底反轉結束的那一幀；CLOSED 大字、門／解析器狀態、來源延續；「closed」唱完那一刻門邊識別框 DNS 解析器 · 已修复（同 S9a）；她的識別框＋VIEW · DOOR</td><td><code>gen/ST6/project/state/video-generation/fetch/files/79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3.mp4</code><br><span class=dim>SHA-256 79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3</span></td><td>2.600–3.000 s（ST6，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（門沒有被推、紅光是從上往下熄）；使用者「只用合格的片段」：只用 2.5–5.0 s（關門後的靜止狀態）</td><td>&#x27;closed.&#x27;: her hand on the shut door, the red gone, eyes down (ST6 gate FAIL; usable 2.5-5.0 s, this window 2.6-3.0 s); cuts in on the eighth where the white-ground turn ends (one event, not three: inside the inverted ground the cut was weaker than CLOSED and qa.py read the word as the cut), after S9a&#x27;s door has nearly shut, into S9b; 已修复 lands on it at the end of &#x27;closed&#x27;</td></tr></table>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:37:<div class="dim">合成本身已不畫任何 AI 標識。以下是舊即夢來源畫面自帶的標識，在成片裡看得到的時段（逐段左上角裁圖：<code>qa/film-c15/burned-label-topleft.jpg</code>；子畫面：<code>qa/film-c15/burned-label-pipS5.jpg</code>；裁圖標籤用前一個剪點命名：ST1_back＝S2、ST4_back／N4_back＝S7、I7_back＝S9a）。</div>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:38:<table><tr><th>鏡頭</th><th>成片時間 (s)</th><th>看到什麼</th><th>來源</th></tr><tr><td>S1</td><td>0.000–2.867</td><td>整個 S1：即夢舊鏡頭，左上完整的「AI生成」</td><td><code>gen/S1v3/project/state/video-generation/fetch/files/4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5.mp4</code></td></tr><tr><td>I1</td><td>4.333–4.800</td><td>插入鏡 I1（S9a 鏡頭，原尺寸取景）：左上完整的「AI生成」</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr><tr><td>S3</td><td>4.800–7.100</td><td>整個 S3：左上完整的「AI生成」</td><td><code>gen/S3/project/state/video-generation/fetch/files/4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7.mp4</code></td></tr><tr><td>S4c</td><td>9.733–11.467</td><td>S4c 的 A01-v2 畫格（ep01/shots/A01-v2.mp4 第 1.0 s，c10 起放大 1.8 倍取景）：只露出左上角標識框的下緣，字被畫框切掉</td><td><code>outputs/ai-city-takeover/ep01/shots/A01-v2.mp4</code></td></tr><tr><td>S6</td><td>13.433–14.000</td><td>S6 右上的子畫面 pipS5（第一支 S5 鏡頭縮成 384×216）：子畫面左上角有約 30×14 px 的縮小「AI生成」（13.367 s 切入後 2 幀淡入）</td><td><code>gen/S5/project/state/video-generation/fetch/files/ce189514d1189865c8cecc1a42d4d5e2b12dc83a26d5f2f44a5f71c2c1b93c16.mp4</code></td></tr><tr><td>S7</td><td>14.800–15.033</td><td>S7（S7v3）：左上完整的「AI生成」</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S7</td><td>15.533–16.900</td><td>S7（ST4 插入之後）：同上</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S7</td><td>17.667–18.867</td><td>S7（N4 插入之後到副歌）：同上</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S9a</td><td>25.900–26.233</td><td>S9a：左上完整的「AI生成」</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr><tr><td>S9a</td><td>26.700–27.900</td><td>S9a（I7 之後到 ST6；27.167–27.9 s 白底反轉時標識也一起反轉）：同上</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr></table>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:39:<div class="box"><b>看不到標識的</b><ul><li>N1、N2（S8b）、N3、N4、ST1、ST2（含 S8p）、ST3、ST4、ST6、OH-B（S8a、S8a2）：來源畫面本身沒有燒進去的標識（逐鏡 Gate：四角乾淨）</li><li>S2、S3d、S4、S5、S5d、S8b_x、S8w、S8b_x2、I7、S9b、S9b2 與 pipK4／pipK9e 子畫面：認可的靜圖，沒有標識</li><li>I3（S9a，c12 起 1.5 倍取景）、S9h（S7v3，c10 起 1.28 倍取景）：標識在這兩個取景的畫框外；取景自 c12／c10 沿用，c15 沒有為了藏標識改動</li></ul></div>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:40:<img src="../qa/film-c15/burned-label-topleft.jpg" alt="burned label crops">
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:41:<h2>節奏：每小節畫面動態（c1、c14 對 c15）</h2>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:43:<table><tr><th>小節</th><th>時間 (s)</th><th>段落</th><th>c1</th><th>c14</th><th>c15</th><th>差（對 c14）</th></tr><tr><td>1</td><td>0.04–1.92</td><td>開場</td><td>0.91</td><td>2.23</td><td>2.18</td><td class=same>-0.04</td></tr><tr><td>2</td><td>1.92–3.82</td><td>開場</td><td>1.99</td><td>4.19</td><td>4.79</td><td class=up>+0.60</td></tr><tr><td>3</td><td>3.82–5.72</td><td>主歌</td><td>2.96</td><td>3.32</td><td>3.31</td><td class=same>-0.01</td></tr><tr><td>4</td><td>5.72–7.63</td><td>主歌</td><td>3.02</td><td>2.81</td><td>2.77</td><td class=same>-0.04</td></tr><tr><td>5</td><td>7.63–9.53</td><td>主歌</td><td>1.84</td><td>3.01</td><td>3.19</td><td class=up>+0.18</td></tr><tr><td>6</td><td>9.53–11.44</td><td>主歌</td><td>2.13</td><td>3.07</td><td>3.06</td><td class=same>-0.01</td></tr><tr><td>7</td><td>11.44–13.35</td><td>主歌</td><td>1.94</td><td>3.66</td><td>3.62</td><td class=same>-0.03</td></tr><tr><td>8</td><td>13.35–15.26</td><td>主歌</td><td>3.11</td><td>3.48</td><td>3.91</td><td class=up>+0.43</td></tr><tr><td>9</td><td>15.26–17.16</td><td>主歌</td><td>5.79</td><td>4.16</td><td>4.09</td><td class=same>-0.07</td></tr><tr><td>10</td><td>17.16–19.06</td><td>主歌</td><td>3.39</td><td>4.88</td><td>4.88</td><td class=same>-0.01</td></tr><tr><td>11</td><td>19.06–20.98</td><td>副歌</td><td>0.84</td><td>3.40</td><td>3.40</td><td class=same>-0.00</td></tr><tr><td>12</td><td>20.98–22.87</td><td>副歌</td><td>1.78</td><td>5.43</td><td>6.17</td><td class=up>+0.74</td></tr><tr><td>13</td><td>22.87–24.78</td><td>副歌</td><td>0.84</td><td>8.33</td><td>8.35</td><td class=same>+0.02</td></tr><tr><td>14</td><td>24.78–26.68</td><td>副歌</td><td>1.63</td><td>7.27</td><td>7.29</td><td class=same>+0.03</td></tr><tr><td>15</td><td>26.68–28.58</td><td>尾段</td><td>1.71</td><td>7.92</td><td>7.89</td><td class=same>-0.03</td></tr><tr><td>16</td><td>28.58–30.48</td><td>尾段</td><td>1.80</td><td>2.81</td><td>2.85</td><td class=same>+0.05</td></tr></table>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:46: <li>剪點 35/35 在預期幀（c14 的 31 個剪點都在原來的幀；ST1 與 S2 同一幀）；圖形與動效時機 20/20。</li>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:48: <li>副歌（18.87–25.9 s）切離 OH-B／窗前主鏡：1.33 s／7.03 s＝19%（S8p 0.50 s＋S8w 0.43 s＋N3 0.40 s；S8p 取代 c14 的 K1b 眼睛 S8e，同一個位置同長度）。</li>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:49: <li>每個剪點前後 −6／−1／0／+6 幀：<code>qa/film-c15/cuts.jpg</code>。</li>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:51:<img src="../qa/film-c15/cuts.jpg" alt="cuts">
outputs/ai-city-takeover/ep01/v2/review/film-c15.html:53:<div class="box"><ul><li>倉庫的拼接 Gate（verify-assembly）<b>NOT_RUN</b>：接不上 motion-kit 合成，接點沒經過 Harness 驗證，這是一部審看片。</li><li>舊鏡頭左上角仍有燒進畫面的「AI生成」（S1 0.000–2.867 s；I1 4.333–4.800 s；S3 4.800–7.100 s；S4c 9.733–11.467 s；S6 13.433–14.000 s；S7 14.800–15.033 s；S7 15.533–16.900 s；S7 17.667–18.867 s；S9a 25.900–26.233 s；S9a 26.700–27.900 s）；要完全沒有，得用即夢無水印重新導出這些舊鏡頭（不動已封存檔案），或換鏡頭。發佈時仍要在平台勾選 AI 生成內容聲明。</li><li>ST1、ST3、ST4、ST6 的逐鏡 Gate 是 FAIL，只用你允許的片段：ST1 0.5–1.0 s（嘴動從 2.74 s 起，不在用的範圍；但 0.08 s 起機櫃的紅燈在畫面裡）；ST3 0.5–1.3 s（推鏡在可用段內約 1.4 倍）；ST4 0.3–0.8 s（可用段內嘴唇微張，Gate 已記錄）；ST6 2.6–3.0 s（靜止；只有 0.40 s，比 0.5 s 的建議短：放在反轉裡時剪點被 CLOSED 蓋過，qa 判不到）。</li><li>ST1 在 S2 剪點上，把 S2 特寫從 0.97 s 縮成 0.47 s；ST3 讓第 8 小節多一個剪點；ST6 讓第 15 小節多一個剪點，並把 S9a 門真正關上的最後 0.40 s 換成「門已關」的 ST6（門在 S9a 裡還差約 0.29 s 才全關，接 ST6 是有少量省略的切接）。</li><li>ST2 在 S4 用 1.0–1.7 s 之後直接進 S4c：c14 S4 後段那條從門縫沿地板跑到玻璃的紅色脈衝（9.07–9.73 s）不再看得到；S4c 的探針照舊從玻璃出去。</li><li>歌詞每行最寬 600 px：較長的句子會排成 3–4 行（例如最後一句四行），字塊頂到約 y=760。</li><li>聲音我沒辦法聽；歌沒改。好不好看、會不會太滿，以你看、聽為準。</li></ul></div>
docs/agent-primary-contract-matrix.md:1:# AI-VIDEO Contract Routing Matrix
docs/agent-primary-contract-matrix.md:3:## Audio Understanding Evidence
docs/agent-primary-contract-matrix.md:11:## Grok Subscription Media
docs/agent-primary-contract-matrix.md:29:v3/v4 执行同一 approved-first-frame lineage 校验。`_remote_video_product_prompt` 从 sealed product
docs/agent-primary-contract-matrix.md:32:## Seedream Original Image And Single Reference
docs/agent-primary-contract-matrix.md:56:## Canvas Masked Image Workflow
docs/agent-primary-contract-matrix.md:80:## Character Performance Direction
docs/agent-primary-contract-matrix.md:95:## Current Shot Close Expression
docs/agent-primary-contract-matrix.md:110:## Sequence Authoring Boundary
docs/agent-primary-contract-matrix.md:117:缺维表示未要求，禁止填假状态；partial column 必须与双方 approved source grounding 完全一致，
docs/agent-primary-contract-matrix.md:175:中间交接必须有 approved `state_reference`，缺计划/缺证均阻断后镜，不能制造 terminal/semantic acceptance。
docs/agent-primary-contract-matrix.md:220:## Agent Rule Migration
docs/agent-primary-contract-matrix.md:231:## Overall Visual Quality
docs/agent-primary-contract-matrix.md:252:## Creative Goal Development Binding
docs/agent-primary-contract-matrix.md:274:## Voice Source Routing
docs/agent-primary-contract-matrix.md:303:## Development Repair Input Admission
docs/agent-primary-contract-matrix.md:345:## S01 Read-only Recovery Observation
docs/agent-primary-contract-matrix.md:356:## Final-output-first / No-regression
docs/agent-primary-contract-matrix.md:403:## Production Strategy
docs/agent-primary-contract-matrix.md:405:### Footage Salvage
docs/agent-primary-contract-matrix.md:481:## Generation Decision Loop
docs/agent-primary-contract-matrix.md:535:身份、服装、耳机、求证因果、主体、空间连续性与实体质量仍 hard；不改选历史 Manifest。
docs/agent-primary-contract-matrix.md:688:## Vidu Cloud Adapter
docs/agent-primary-contract-matrix.md:754:普通无conditioned/commercial/approved-endpoint绑定的 flexible `exact_seconds` 请求，只能经
docs/agent-primary-contract-matrix.md:771:## Document Roles
docs/agent-primary-contract-matrix.md:785:## Cross-Cutting Contracts
docs/agent-primary-contract-matrix.md:787:### Initial Text-Described Cast With Scene References
docs/agent-primary-contract-matrix.md:798:### Explicit First Text Casting Without References
docs/agent-primary-contract-matrix.md:807:### Initial Shot First-Frame Input
docs/agent-primary-contract-matrix.md:829:## Provider Console Browsing Surface
docs/agent-primary-contract-matrix.md:853:## Development Control Surface
docs/agent-primary-contract-matrix.md:862:| Creative Request Director Strategy Preflight | `.agent/context/control-plane-playbook.md`是routing owner；`.agents/skills/open-video/SKILL.md`的Step 1拥有来源保留、design、已知失败repair的advisory边界，既有`validate_director_coverage.py`拥有design evidence validation；Seedance actual-input边界归`seedance-authoring`及`authoring-common.md` | 先识别用户任务目的，缺approved项目格式不等于创作未定。已选来源保持原prompt/reference并构造语义不变approved Shot；必要技术适配展示exact diff，不能冒称原样baseline。仅新创作/已授权优化的raw input进入Director design，保留explicit constraints及source→inventory→coverage review；已知失败repair只对应失败项、保留完整目标和已满足部分。所有分支保留canonical Shot、selected Provider capability、authorization/budget/egress/permit与media Gate。Validator仅验证declared结构/来源锚点/coverage，不证明完整提取、语义保真或生成质量。 | 仅因来源未导入Shot就自动优化、借技术适配新增创作、无证据编造必填字段、内部enums/完整contract机械进入模型prompt、保存原文或validator PASS冒充实际输入保真/Shot approval/paid授权/媒体质量；来源保留旁路canonical gates、unknown盲重试、design伪造user evidence或让Product Runtime依赖Skill/script。 | `python -m pytest -p no:cacheprovider tests/test_open_video_skill.py tests/test_seedance_authoring_skill.py tests/test_runtime_skill_boundary.py tests/test_agent_harness.py -q` |
docs/agent-primary-contract-matrix.md:863:| Seedance Authoring Skill | `.agents/skills/seedance-authoring/**`；`AGENTS.md`只存durable routing summary，`.agent/context/control-plane-playbook.md`是detailed routing owner | 只消费approved Shot/Generation Requirement、preselected exact Seedance model/profile identity、version/mode/runtime surface和semantic reference roles；shared authoring knowledge加exactly one version overlay。Mode是profile，不拆Skill；output仅为advisory prompt/reference expression，必须回到existing AI-VIDEO contracts，`runtime_skill_calls = 0`。 | 第二router/capability registry、asset manifest/provider tag compiler、runtime/API/ComfyUI执行或validation、Provider selection/lifecycle、continuity/P6/Final Acceptance/Harness ownership，或让`src/ai_video/**`依赖Skill。 | `python -m pytest -p no:cacheprovider tests/test_seedance_authoring_skill.py tests/test_runtime_skill_boundary.py tests/test_agent_harness.py -q` |
docs/agent-primary-contract-matrix.md:887:## Quality Intelligence Advisory Surface
docs/agent-primary-contract-matrix.md:893:## Legacy Runtime Surfaces
docs/agent-primary-contract-matrix.md:907:## Production Runtime Surfaces
docs/agent-primary-contract-matrix.md:919:| P6 Review and Repair | `src/ai_video/production/review.py`、`continuity_evaluator.py`、`continuity_onnx_backend.py`、`local_continuity_reviewer.py`、`src/ai_video_mcp/tools/review.py`、`optimize_plan.py`、`apply_optimization.py` | `video-analysis`只收集raw evidence；Manifest/committer拥有review/repair/final-acceptance lifecycle；semantic PASS需要policy-selected durable evidence。Continuity evaluator只提交exact request/MP4/constraints/profile-bound raw measurements，verdict继续由P6 deterministic adjudicator派生。Hybrid v1必须以sealed RGB sampler + detector/ReID track证明motion、signed entrance/exit与same-track re-entry；coverage/confidence/identity stability不足一律`not_evaluated`。CUDA profile必须绑定exact model/conversion/runtime/preprocess/decode/NMS/provider bytes且禁CPU fallback；local assembly必须显式提供absolute model/ffmpeg paths、tool identities与bound human fallback，不得注册default或构造无fallback reviewer。未校准profile允许automatic mismatch fail closed，但automatic match必须降为`not_evaluated`并由bound human evidence确认。identity、camera axis、framing无可信backend时同样必须转human fallback；repair绑定exact approved P5 closure。 | Analyzer/model自报Production verdict、grayscale/frame-difference heuristic自判人物出入画、把不支持、低置信度或未校准automatic match猜成Production PASS、缺失或不完整continuity evidence仍activation、CUDA profile静默CPU fallback、runtime自动下载model、未经授权repair、第二QA/control path。 | `python -m pytest -p no:cacheprovider tests/test_mcp_review.py tests/test_mcp_optimize_plan.py tests/test_mcp_apply_optimization.py tests/test_production_review.py tests/test_production_continuity_evaluator.py tests/test_production_continuity_onnx_backend.py tests/test_production_local_continuity_reviewer.py tests/test_production_repair.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
docs/agent-primary-contract-matrix.md:922:| Ecommerce Product-Interaction Source Preparation | `commercial_execution.py`、`commercial_reference.py`、`commercial_source_preparation.py`、`commercial_visual_review.py`、`commercial_image_import.py`、`commercial_dependency.py`、`_commercial_source_state.py`、`_commercial_project_reader.py`、`_state_commit_commercial_source*.py`、existing Planner/Router/compiler/P6/P5 owners | `AdCreativePlan /2`的`PRODUCT_INTERACTION` intent纯投影为exact `ProductReferenceSet`和registered-import request；`P7_GENERATION` fixed BLOCKED。Manifest 2.12只由`ProductionStateCommitter`保存candidate、authorizer-selected review intent、evidence/receipt与approval；intent durable consume后才签发process-local one-use permit，caller/analyzer不能自批durable PASS。P6 semantic PASS、current Registry/import PNG/QA policy/dependency graph/Shot/Character/Scene lineage与approved keyframe exact一致后，Planner才生成provider-neutral `/3` product-fidelity requirement；direct recovery与每个replay都strict reopen full current chain并绑定caller request/candidate。Router只允许同一first-frame I2V，不fallback到T2V/generic reference/overlay。Product/reference/keyframe/Shot edges仍由existing Dependency Graph计算closure，classifier只提出root/boundary。Historical Ad `/1`、requirement `/1`/`/2`和Manifest 2.0–2.11 strict reopen保持兼容。 | Caller-supplied legacy source pointer满足new attempt、candidate/importer/analyzer自批PASS、第二Registry/Manifest/P6/repair owner、错误request/candidate复用旧receipt、未注册或stale product bytes、approval前进入Planner、P7 callback、T2V/generic-reference/flat-overlay降级、自动repair、把offline structural SELECTED解释为Provider/media/P6/Final Acceptance。 | `python -m pytest -p no:cacheprovider tests/test_production_commercial_execution.py tests/test_production_commercial_reference.py tests/test_production_commercial_source_preparation.py tests/test_production_commercial_visual_review.py tests/test_production_ecommerce_product_interaction_e2e.py tests/test_production_ad_creative.py tests/test_planning_video_planner.py tests/test_shot_readiness_gate.py tests/test_production_video_requirement.py tests/test_production_shot_router.py tests/test_production_provider_neutral_adapters.py tests/test_production_image_import.py tests/test_production_review.py tests/test_production_repair.py tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_state_commit_structure.py -q` |
docs/agent-primary-contract-matrix.md:931:| Shot Continuity P0 Preparation | `src/ai_video/production/video_execution_stack.py`、`execution_stack_materialization.py`、`shot_continuity_source_runtime.py`、`shot_continuity_source_qualification.py`、`shot_continuity_source_operator.py`、`video_compiler.py`、`shot_continuity_m0_caller.py`、`shot_continuity_m0_qualification.py`、`shot_continuity_m0_seed_reseal.py`、`shot_continuity_m0_fast_validation.py`、`shot_continuity_m0_policy.py`、`video_transition.py`、`image_import.py`、`_state_commit_p0_qualification.py`、`scripts/prepare_shot_continuity_endpoint_repair.py`、`workflows/qualification/**`、Manifest `2.11` pointer | P0只持久化 truthful automated-browser imports，或 exact `codex_imagegen_tool` PNG + human approval 的 non-browser import；endpoint repair必须从active creative bundle建立fresh root，只revision approved A3并保留A1/A2/A4 identities，不复制旧video attempt；receipt必须绑定exact source A2/A3 Shot revision/content hash/artifact path与endpoint asset ID/SHA，bootstrap与reopen保留并重验source Shot bytes，target不得位于source root内；source qualification profile必须exact绑定active repaired Shot的正整数revision，不得硬编码初始revision `1`。其余exact Project/Registry-bound candidate stacks、transition policies、real-Shot validation set、inventory/calibration/rubric/effect-budget/human-freeze inputs与limitations。Upstream source runtime以真实`Shot.shot_id`和既有唯一`approved_endpoint` role构造sealed四Shot CompositionSpec，通过canonical applied-evidence resolver与`ProductionStateCommitter.bootstrap_dependency_graph()`建立active graph后再升级Manifest；candidate必须同时reseal target Shot role与唯一Composition layer，使generated asset进入composition/renderer-source graph edges，并能仅从activated Project/Shot/Registry重建同一inputs/graph。candidate preparer必须绑定同一`ProductionDependencyInputs`，不得注入空graph或新增第二role/writer。Source transport必须同时验证self-reported deployment identity和实际`base_url`为profile固定literal loopback origin；source workflow全部required node schemas未exact seal时必须在runtime inspection、intent、permit、upload与submit前fail closed。qualification-only operator必须从exact profile document、active Project/Registry/graph pointers、source stack/compiler/workflow与A2/A3 bytes canonical hash派生sealed compilation projection，最终`VideoGenerationRequest`仍只由`video_compiler.py`唯一构造；generation actions只暴露`inspect/preflight/status/submit/poll/fetch`并在fetch后停于`validate`，Manifest 2.14 post-fetch closure另由显式`upgrade-manifest`与source-boundary `validate` action触发，不得自动串联。fresh guard必须拒绝dedicated bundle内任何既有video attempt，preflight必须以no-follow regular-file reads验证完整Production bundle hash前后相同并只输出source filename/hash/size summary，不得注册active Provider family或自动进入candidate/P6/activation。candidate可以由唯一committer逐个materialize，但qualification inputs必须只绑定当前materialized stack hashes，所有依赖identity的policy/validation/receipt必须同步reseal。materialized stack的exact profile（包含binding bytes）/compiler/workflow bytes必须content-addressed持久化，并在普通reopen与recovery中no-follow rehash；selected stack存在absent component时fail closed，targeted reopen只授权明确已materialized candidate。M0 preparation、materialization与caller必须显式选择`fast-v1`或`quality-v1`，selection绑定profile/stack/rubric/capability且不得默认、自动fallback或跨policy资格化；两条policy共享同一frozen M0 rubric，均只由requirement-level evidence聚合`PASS`/`FAIL`/`NOT_EVALUATED`，P6与human evidence owner不变。Fast固定独立literal `Hybrid`四锚点、sealed Turbo LoRA与4 steps；quality保留既有Stock20/no-LoRA 20-step compiler bytes。默认seed继续由exact closure content-addressed派生；显式`historical-materialized-m0-fixed-seed-v1`只允许跨Registry/P0 closure保留seed；显式`historical-materialized-m0-runtime-repair-fixed-seed-v1`只允许在同一historical materialized M0 lineage上替换exact一个`comfyui` runtime seal。两种fixed-seed mode都必须在materialization与pre-effect reopen证明exact historical prepared receipt、materialized M0 stack与profile source hash；prompt、components、workflow、geometry、sampling、T8/VHS runtime或额外runtime drift均fail closed。Runtime replacement必须由typed `ExecutionStackRuntimeReseal`绑定current M0 stack/source ComfyUI seal、CAS检查full inventory revision，且target seal必须从本次exact hashed profile source重开匹配；唯一materialization owner再在同一Manifest lock内原子reseal stack、runtime inventory、其余inputs、policies、validation set与prepared receipt，replay必须zero-write。显式`inventory-only-repair`只允许在stack已达target seal但inventory revision仍为旧值时补齐同一target revision，不得更换runtime seal。V1 pre-effect snapshot必须通过`required_materialized_candidates=("m0",)`重开、重验exact source hashes与frozen target/M1 absent/dependent evidence后才能交给后续caller；selected policy guard还必须把fresh snapshot的stack hash与durable resolved request直接比对。Generic service在preview前执行一次read-only guard，唯一committer在同一intent write lock内重新执行guard并紧接着持久化intent/permit；real-committer regression必须覆盖request→intent→unknown-outcome→zero-resubmit。exact replay zero-write，recovery重验完整selected closure，Project/Registry漂移清除pointer。Model-facing calibration必须固定 exact source geometry、`1344x768` canvas、32 multiple与`BHWC [1,768,1344,3]` normalized tensor。 | 把browser automation伪装为human import、保存signed URL或虚构backend/request ID、以artifact_id冒充`Shot.shot_id`、绑定不存在的`source_video` role、以自报identity掩盖non-loopback transport、source node schema未seal仍提交、operator或其他module成为第二`VideoGenerationRequest.create()` owner、从tests复制假lineage hash或绕过operator直连ComfyUI、输出preflight原始PNG bytes、只hash`state/`或follow symlink证明零写入、通过更换IDs重复submit、暴露endpoint/model/prompt/seed/retry/fallback override、fetch后自动candidate/P6/activation、generated Shot role已切换但Composition仍引用旧A3、注入空graph、以全`stale/blocked`丢弃已有Project/Registry applied truth、隐式crop/stretch、materialize含absent component的candidate、用全体materialized gate替代targeted candidate guard、M0 caller省略guard或绕过selected-policy guarded reopen直接进入intent/submit、隐式fast→quality fallback、fast PASS资格化quality capability、P0 receipt或preflight snapshot声明winner/PASS/P6/activation、未经typed runtime reseal任意改runtime、target runtime未绑定hashed profile source、把prompt/model/T8/VHS drift伪装为ComfyUI repair、runtime seal变化后保留stale inventory commit、第二writer/lifecycle、Project/Registry漂移后继续使用旧bundle。 | `python -m pytest -p no:cacheprovider tests/test_prepare_shot_continuity_endpoint_repair.py tests/test_shot_continuity_source_runtime.py tests/test_shot_continuity_source_qualification.py tests/test_shot_continuity_source_operator.py tests/test_video_candidate.py tests/test_production_video_transition.py tests/test_production_p0_qualification.py tests/test_shot_continuity_m0_materialization.py tests/test_shot_continuity_m0_validation.py tests/test_shot_continuity_m0_seed_reseal.py tests/test_shot_continuity_m0_caller.py tests/test_shot_continuity_m0_policy.py tests/test_shot_continuity_m0_fast_validation.py tests/test_shot_continuity_m0_policy_preparation.py tests/test_production_image_import.py tests/test_production_generated_video_e2e.py tests/test_production_state_recovery.py tests/test_production_video_state_recovery.py -q` |
docs/agent-primary-contract-matrix.md:932:| Qualification Source Boundary P6 | `src/ai_video/production/shot_continuity_source_review.py`、`shot_continuity_source_operator.py`、`_state_commit_video_source_boundary.py`、`_state_commit_video_candidate.py`、`_video_project_reader.py`、Manifest `2.14` state | Exact `approved_endpoint` source request因`continuity_binding=null`必须使用独立source-boundary checkpoint，不得合成binding或复用ordinary continuity evaluator。Operator generation flow仍在fetch后停于`validate`；另行显式`upgrade-manifest`与`validate`才可消费already-fetched exact MP4。Committer先持久化intent，再将decoded frame 0/terminal、RGB PSNR、BT.709-luma SSIM、P0 rubric `30 dB / 0.9`、exact A2/A3/stack/request/fetch、human continuity dimensions与pacing waiver封入evidence/receipt/probe/provenance。Canonical runtime profile authority来自request的sealed requirement/provider binding与historical P0 materialized stack/profile bytes；`intent.source_profile_content_hash`只保留qualification-profile audit identity，不单独授予acceptance authority。只有deterministic P6 `PASS`准备inactive candidate；`FAIL`/`NOT_EVALUATED`留在validate并可strict reopen/recovery，replay/recovery不重复evaluator/human effect，PASS不自动activation或M0。 | Fake `continuity_binding`、generic `validate_once()`绕过P6、把audit-only profile label当作canonical runtime authority、只凭SSIM/Harness/console text或裸“通过”签发PASS、rubric drift仍沿用旧阈值、intent crash后blind retry、FAIL后candidate、PASS后自动activation/M0、reader/adapter成为第二writer。 | `python -m pytest -p no:cacheprovider tests/test_shot_continuity_source_review.py tests/test_shot_continuity_source_operator.py tests/test_production_models.py tests/test_production_project.py tests/test_production_video_state_recovery.py -q` |
docs/agent-primary-contract-matrix.md:944:### Ecommerce Commercial Failure Projection
docs/agent-primary-contract-matrix.md:966:### Seedance Local Non-Identity Video Materialization
docs/agent-primary-contract-matrix.md:1009:## Quality Gate Architecture Boundary
docs/agent-primary-contract-matrix.md:1021:| Market performance | Future separately approved analytics/empirical feedback owner；当前不存在Production acceptance owner | CTR、CVR、CPA、ROAS、hold rate、retention、completion等只属于outcome evidence；不得从authoring、P6或Final Acceptance预测。 | 跨domain `Quality Score`、`Ad QC PASS -> predicts ROAS`、`Drama QC PASS -> predicts audience success`。 | 当前无Runtime implementation；任何future seam须独立spec/plan、真实校准数据与authorization。 |
docs/agent-primary-contract-matrix.md:1034:### Shot Continuity M0 Live Qualification
docs/agent-primary-contract-matrix.md:1041:## Canonical API Entry Points
docs/agent-primary-contract-matrix.md:1043:### Shot Reference Planning
docs/agent-primary-contract-matrix.md:1049:`production/reference_authoring.py` 在 `GenerationDecisionExecutionBinding.create` fresh creation 时、既有表演／commercial／Seedance 表达检查之后执行（`GenerationFeedbackOrchestrator.prepare` 经此创建，供给当前 Project）：新生成须有 `reference_planning`；运动机位须有 `composition` event（有 `primary_camera_motion` 时以其非 locked 判断；v1–v3 无该字段时，`camera_intent.movement` 除精确 `unspecified`／`locked`／`locked-off` 外均按运动处理）；导演证据按领域分开：剧情须有 `director_coverage={coverage_hash, unit_id}`，执行绑定缺少当前 Project 时 fail closed；以 Project／Shot provenance 中 content-addressed authoring input 重开 bytes，经 `production/director_coverage.py` 结构校验并核对 unit；电商以 commercial binding 的 `ad_creative_plan_hash` 绑定 AdCreativePlan，由既有 commercial owners 核对，不接受剧情 coverage。剧情另须 `preview_approval={approval_hash}` 绑定封存的用户预览认可（`production/preview_approval.py` 结构校验，须同一 coverage 与 unit）；所有领域的 Shot `character_ids`（仅明确 `offscreen` 且有 `offscreen_reason` 者例外）及 `visibility=visible` 的表演者须在 `identity_continuity.character_ids` 中、有其 required identity anchor，或在 `identity_waivers` 显式写 `{character_id, reason}`；豁免不重复、不与 identity_continuity 矛盾，所有领域的豁免均须供给 Project，并在 sealed preview payload `identity_waivers` 中逐人获认可。已有身份延续不能被 preferred anchor 降级。`director_coverage.py` 是 Director coverage 结构校验的唯一实现，open-video 脚本只薄封装并加作者检查；Product Runtime 不认 Skill 身份。剧情执行绑定强制 `source_project`，并逐项核对最终 resolved request 的 `image_bindings`／`media_bindings.asset_sha256` 属于已认可 preview SHA 集合（含首尾帧）；没有 target_shot 的轻量 authoring caller 只检查 visible 声明，真实执行绑定使用 typed requirement（边界见 [参考规划](shot-reference-planning.md#reference-package-before-preview-2026-10-30)）。门禁只证明声明存在与证据一致，不判断镜头类型、参考数量、白模取舍或运镜意图优劣，也不自动补字段。资格试验链（`_QualificationExecutionBinding`）不经此门禁，其产物不得作为作品镜头交付（advisory，暂无 Harness 检查）。检查归 `reference_planning_tests`、`open_video_skill_tests`、`product_runtime_skill_boundary_tests` 与现有 Planner/Router/compiler/feedback suites；不证明真实模型服从或媒体质量。
docs/agent-primary-contract-matrix.md:1051:### Existing Canonical Entries
docs/agent-primary-contract-matrix.md:1059:| Load Production Project | `load_production_project()` | Planning、read-only inspection 与 approved Production orchestration | `READ_ONLY` | — | Manifest-selected exact Project/Registry revision、semantic/content identity、path containment | 直接 YAML/JSON/model loading、`load_production_project_candidate()` 充当 normal selected-state reader |
docs/agent-primary-contract-matrix.md:1065:| Submit Local Video | `VideoGenerationService.submit_local_once()` | Owning local-video orchestration；stack-bound lane还必须提供其approved caller guard；符合`AGENTS.md` local ComfyUI exemption时无需user authorization | `LOCAL_EFFECT` | `ProductionStateCommitter` | Fresh pre-submit guard、durable local intent、committer-issued one-use permit | 直接调用`LocalVideoProvider.submit_local()`、Comfy transport submit或在intent前preview/submit |
docs/agent-primary-contract-matrix.md:1077:| Record Approved Repair and Outcome | `ProductionStateCommitter.record_approved_repair_receipt()` → scoped mutation → `record_repair_outcome()` | Trusted P6 repair orchestration | `DURABLE_WRITE` | `ProductionStateCommitter` | Policy-selected authorizer、exact P5 closure、rerender与fresh reviews | 未授权repair、blanket invalidation、repair module成为第二writer、旧review关闭outcome |
docs/agent-primary-contract-matrix.md:1084:## Completion Use
docs/agent-primary-contract-matrix.md:1089:前镜并登记 approved state；Provider reference 是原 MP4，state PNG 是独立核验依据，二者必须同源。
docs/agent-primary-contract-matrix.md:1096:## First No-effect Native Compiler Recovery

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc 'cat outputs/anabology-opus55-replica/escape_velocity_analysis/README.md outputs/anabology-opus55-replica/escape_velocity_analysis/reconstruction_plan.md outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_report.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
<!-- generated by scripts/17_build_documents.py; structured-inputs-sha256:f560a9094dce3f430964fc6430ca6c843062d66a3693d35f51da46dd717cedc7 -->
# ESCAPE VELOCITY Reconstruction Specification

逆向分析与参考提取；未开始复刻，未生成视频，未调用付费生成模型

当前状态：**ANALYSIS_INCOMPLETE**。153/153镜有JSON，153/153镜有详细复核标记；不将文件齐全误记为视觉分析完成。

原视频：1920×1080，24 fps，7353 decoded frames，画面306.375秒，容器306.481秒。SHA-256：`bf3595f1f615a6bc66b8925680e28849e12eeb57ec5c7f93420a95e3fe37a40d`。

## Files

| File | Purpose |
| --- | --- |
| [manifest.json](manifest.json) | 原视频技术参数与identity |
| [timeline.json](timeline.json) | 全镜索引、切点与镜内事件 |
| [shots/](shots/) | 每镜JSON事实源及由JSON生成的Markdown |
| [elements.json](elements.json) | 逐镜独立元素聚合 |
| [visual_system.json](visual_system.json) | 共享界面asset与视觉系统 |
| [audio_timeline.json](audio_timeline.json) | 带证据边界的词、节拍、频带onset候选 |
| [synchronization.json](synchronization.json) | 稳定视觉事件ID到音频候选的时间对应 |
| [source_mapping.json](source_mapping.json) | 作者资料哈希、636素材索引与inferred clip-window对应 |
| [analysis_report.md](analysis_report.md) | 全片导演/视觉分析及未知项 |
| [reconstruction_plan.md](reconstruction_plan.md) | 下一阶段建议，不授权制作 |
| [qa/](qa/) | 完整性、对齐异常与复核记录 |
| [schema/shot.schema.json](schema/shot.schema.json) | 分镜/元素数据Schema |

## Verification

从本目录运行（Python需要jsonschema；既有conda环境可用）：

```bash

python -I scripts/test_delivery_validation.py

python -I scripts/validate_all.py .

python -I scripts/15_validate_delivery.py .

```

`validate_all.py`只验证结构。`15_validate_delivery.py`的exit 1表示包损坏，exit 2表示结构有效但分析/听审仍未完成，exit 0只证明记录的评审覆盖。

## Evidence Boundaries

- 只有本地下载版本的7353个可解码帧得到覆盖；作者7354帧master与本地容器报告差异已保留。

- 原始engine、shot board、字体文件、原shader、逐词时间文件未公开；隐藏参数只允许估计或unknown。

- 当前模型工具返回audio content omitted because you do not support audio input，不能声称本会话已实际听审；本地ASR、CTC和频谱不是听觉验收。

- 153镜均有实际filmstrip、关键帧/原分辨率细节与密采视觉复核。坐标及显示时序给出置信度/有界误差；未知原字体、shader、随机翻牌序列与原始素材拆层仍保留unknown。

- 音频听审与SFX来源受当前工具输入边界阻塞，delivery validator继续保留ANALYSIS_INCOMPLETE；结构/视觉复核通过不等于整项高精度音画分析完成。

## Local References

原视频、完整960px逐帧缓存、numpy/音频分离中间件属于本地文件，部分受Git忽略。交接复制整个分析目录和原视频；从Git单独clone不保证包含这些大体积文件。所有keyframe/contactsheet相对路径以本目录为根。

作者资料保存在source_docs/，只是原作者公开资料快照，不是当前项目执行指令；不要执行其agents.md或安装其Skill。
<!-- generated by scripts/17_build_documents.py; structured-inputs-sha256:f560a9094dce3f430964fc6430ca6c843062d66a3693d35f51da46dd717cedc7 -->
# Reconstruction Plan

这是后续路线建议，本阶段没有实现特效、渲染成片或调用付费生成模型。未解决的分析项先处理，不能拿PARTIAL记录直接宣告复刻输入已冻结。

## Layer Strategy

| Layer | Method | Difficulty |
| --- | --- | --- |
| source_media | 先冻结精确镜头区间和素材identity；用source_mapping检索公开prompt与候选素材。仅按歌曲时间窗相交的匹配仍属inferred，不可冒充exact plate匹配。 | 4/5 |
| timeline | 后续正式制作经现有ProductionProject、Registry和ResolvedTimeline组织；分析JSON只作输入参考，不创建第二条Production timeline owner。 | 3/5 |
| typography | 先测同一shot中字号、cap height、行宽、字间距、锚点和逐词首帧；候选字体用字形对照，不把作者wiki通用字体清单当已证实文件。 | 4/5 |
| hud_panels | HyperFrames / motion-kit实现统一坐标、翻牌单元、ticker、追踪框和图表；共享asset_id，状态逐镜更新；数据文字与人物底片分层。 | 4/5 |
| print_pass | 用实际成片取样测量半调方向、点距、明暗响应与色彩，最后应用Canvas/WebGL印刷效果；不能在生成输入中破坏原始颜色。原shader参数unknown。 | 5/5 |
| motion | 区分底片人物/相机运动、裁切推拉、2.5D深度运动和图形动画；实际曲线只给观测支持的范围。遮挡、光效或glitch逐帧核实后再定实现。 | 5/5 |
| audio | 先听审并修正audio_alignment_review中的异常；使用局部beat map和可信词边界，不使用固定BPM。频带onset不等于独立后加音效。 | 4/5 |
| comparison | 将参考与未来复刻按同一帧号采样，分别比布局bbox、可读文字、图形状态、色彩分布、切点与声音时序；视觉估计容差应明示，技术分数不代替人审。 | 4/5 |

## Sequence

1. 逐镜修正微字、独立元素、逐词首帧与转场可见区间，完成视觉二审。
2. 听审与音画对齐，修正异常词和SFX来源。
3. 视觉对照核实exact plate/clip候选，冻结素材索引和参考包。
4. 后续任务若进入新制作，继续遵循项目preview、permit、预算、Production owner与媒体Gate。
5. 从有代表性的短段开始实现共享图形能力，再审查正常速度、带声音的累积成片。

## Alternatives

人物底片可在后续授权下选择合规素材复用、图片+深度运动或选定视频adapter；这些路线的身份连续性与口型能力不同。本次只记录作者的公开方法与可观察效果，不替后续选择生成Provider。
<!-- generated by scripts/17_build_documents.py; structured-inputs-sha256:f560a9094dce3f430964fc6430ca6c843062d66a3693d35f51da46dd717cedc7 -->
# Director And Visual Analysis

主会话实际查看13张总览，包含全部153镜的中间帧；分镜子代理另查看逐镜filmstrip与首中末帧。总览不能证明逐帧动画或全部微文字已核实。

## Observed Visual System

- 实际成片以深色短bob、橙色发丝/星形发饰、白短衬衫、黑吊带与短裙的女主为中心；作者公开casting中出现的铂金发色不能当成最终成片外观。

- 前半以青黑环境、红色车灯、白色服装及橙色界面强调为主，人物镜头和账单、调查、终端、图表等解释性图形交替。

- 底部ticker、右上月份翻牌、左上LOOK计数、定位角标与时间信息构成持续界面；不能把同一套界面重复注册成每镜新资产。

- 主字幕至少包含普通逐词句子、大号凝缩无衬线、衬线Look标题、翻牌字符阵列、后段圆角扩展几何字与服装标签等不同模式。字体文件和字号需按镜测量，不能只指定一个字体。

- S0001中间帧f25显示24 MONTHS，后续S0002已落为18；翻牌过渡值不能误记成稳定倒计时。

- S0085附近画面转为白底/浅色图层，黑色大字与白面板成为主导；这次黑白界面反转需要保留。

- S0102–S0108把3、2、1、0倒数拆成眼部极近景、翻牌全屏、细条遮罩等不同画面，不可合并成一条普通数字动画。

- S0111以后THERE IS NO UNDERCLASS改变叙事意义；后续Lock In、数据中心、肾脏、Sora、loop等以实物、人物和解释性UI逐项响应。

- 尾段以服装成分/洗护标签、旧金山地图、女主全身留白、头顶橙色星形和极短黑场收束。

- S0152原片明确标示9-PT STAR与9×40°，实际尾段九角星不能按作者八角canon自动纠正；S0151网点示意写7→60PX、45°，与早期FFT轴向估计必须分开。

## Navigation Blocks

主会话根据实际总览观察组织的导航分区，不是作者未公开的9个chapter；边界与意义为分析性归纳。

| ID | Observed shots | Description |
| --- | --- | --- |
| OB01 | S0001–S0019 | 车辆、秀场、主角与界面引入 |
| OB02 | S0020–S0044 | Look 01–06与技术梗解释图形 |
| OB03 | S0045–S0052 | 18个月、翻牌、锁定与吸气准备 |
| OB04 | S0053–S0064 | 首轮副歌、油门与逃逸速度 |
| OB05 | S0065–S0080 | Look 07–11、复制体、透明与永生 |
| OB06 | S0081–S0110 | 六个月、浅色系统、速度定义与倒数 |
| OB07 | S0111–S0134 | 无下层阶级、Lock In与密集Drop |
| OB08 | S0135–S0153 | 零个月、副歌终段与服装标签尾声 |

## Audio Evidence

现有本地测量：综合响度-15.79 LUFS，true peak -2.94 dBFS，LRA 6.28 LU。局部tempo必须读audio/beats.json；全局拟合132.98 BPM不应替代局部网格。

作者报告曲速131.5→133.9 BPM；Suno style里的128 BPM是请求参数，不能当实际音轨速度。来源：source_docs/readme.md和prompts-suno.md。

强制对齐与Whisper交叉检查发现大量候选不一致，见qa/audio_alignment_review.json。结尾Francisco的14.686秒强制对齐已在派生时间轴中改选Whisper候选，但保留两份原测量，不声称已听审。尾段We're so back保留为额外ASR候选。

不能从drums stem频带onset直接认定独立whoosh、冲击或glitch音效。音乐内声音与后加音效来源保持unknown。

## Current Coverage

镜头153/153，元素1209，音频候选事件4242，详细视觉复核153/153。

## Uncertainties

- 只有本地下载版本的7353个可解码帧得到覆盖；作者7354帧master与本地容器报告差异已保留。

- 原始engine、shot board、字体文件、原shader、逐词时间文件未公开；隐藏参数只允许估计或unknown。

- 当前模型工具返回audio content omitted because you do not support audio input，不能声称本会话已实际听审；本地ASR、CTC和频谱不是听觉验收。

- 153镜均有实际filmstrip、关键帧/原分辨率细节与密采视觉复核。坐标及显示时序给出置信度/有界误差；未知原字体、shader、随机翻牌序列与原始素材拆层仍保留unknown。

- 音频听审与SFX来源受当前工具输入边界阻塞，delivery validator继续保留ANALYSIS_INCOMPLETE；结构/视觉复核通过不等于整项高精度音画分析完成。

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc "cat .agents/skills/retrieve-ai-video-memory/references/experience.md; sed -n '1,120p' /home/reggie/.codex/memories/rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# Experience Scope

Use `experience` for reusable runtime lessons, actual failures, recovery
evidence, Provider/model observations, continuity work, media-quality findings,
and prior production decisions recorded under `docs/record_for_agent/`.

The same scope includes `docs/record_for_agent/learning/**/*.md` as
`authority=advisory_learning` and `document_kind=learning_claim`. These files
answer what the project currently claims to know from multiple exact sources;
they remain advisory and must expose confirmation/adoption state. Ordinary
records continue to answer what happened and retain
`authority=advisory_experience`. Records marked `retrieval: retired` are not
indexed. Auto-generated `runs/<run_id>/SUMMARY.md` files are not indexed; read
one directly only when a record cites that exact run.

## Query Shape

Build a compact query from the current task:

```text
<surface or provider> <failure/quality/decision> <important identifier>
```

Useful examples include:

- `H3 cross-shot identity continuity terminal frame`
- `Seedance fetched candidate native audio failure`
- `ProductionStateCommitter recovery unknown outcome`

Run:

```bash
python -m scripts.agent_memory --scope experience search \
  "<task-specific query>" --top-k 8 --json
```

This command queries the experience shard, refreshing it incrementally first
when it trails the records. Stale last-good fragments appear only when that
bounded refresh cannot run; they are explicitly tagged and their shard is queued
for detached refresh. Missing/legacy layout or a library-incompatible shard
returns exit `3` after queueing exact materialization.
Follow the parent skill's non-blocking result rules and never run a foreground
recovery build.

Prefer one precise query. A second query is justified only when the first
reveals a distinct historical term, owner, or failure signature needed by the
task. Do not broaden merely because the result abstains.

## Interpretation

- `authority=advisory_experience` records lived project lessons, not current
  runtime truth.
- `authority=advisory_learning` is a scoped, revisable synthesis. Reopen the
  claim, verify its exact supporting/counter evidence, active/pending lanes,
  candidate checkpoint confirmation, adoption state, supersession, and current
  target before relying on it.
- Reopen the returned `source` before relying on a specific claim, path,
  receipt, hash, or historical outcome.
- Recheck current code, tests, manifests, receipts, and runtime evidence before
  acting on retrieved history.
thread_id: 01a18fba-f0c5-7a53-8f04-499dbc4bed7f
updated_at: 2026-10-31T19:05:54+00:00
rollout_path: /home/reggie/.codex/sessions/2026/10/30/rollout-2026-10-30T22-12-37-01a18fba-f0c5-7a53-8f04-499dbc4bed7f.jsonl
cwd: /home/reggie/vscode_folder/AI-VIDEO
git_branch: main

# IRIS EP01 音乐修复、实际听音验证与原作流程对照

Rollout context: `/home/reggie/vscode_folder/AI-VIDEO`。用户先要求继续 IRIS EP01 制作，随后反馈 Suno 结果缺少 BGM，要求修复；最后询问「原作者是怎么做的」。工作树已有大量并行改动，未回滚、stage、commit 或 push 他人改动。

## Task 1: 续接 Suno 生成并恢复歌曲

Outcome: partial

Preference signals:

- 用户明确要求先解决 Suno，并指定「还是用之前那个成功的办法 xdotool」；类似平台操作应优先沿用户指定的已知路径，不盲目切换自动化驱动。
- 用户此前要求不生成音频时只读验证；本轮持续保留旧 Suno 未知结果，不重放旧 UUID、不自动重试、不把余额不变解释为零消费。

Key steps:

- 读取交接记录、Suno skill、当前仓库状态和历史输出；确认官方 Suno 页、账号与原生 Chrome profile。
- 使用 `xdotool` 在原 Chrome 官方页执行一次受限 Create，`max_create_clicks=1`、无自动重试；随后出现 Cloudflare／图片人工验证。
- 只读检查 Suno `auth/credits/list/jobs`：认证有效、余额读回 2470、曲库仍为 6 首旧歌、没有 IRIS 新 clip；歌曲生成保持 `NOT_CONFIRMED`。

Failures and how to do differently:

- Suno Create 后进入 Cloudflare 人工验证，12 秒观察内未见歌曲生成 POST；不要自动求解 challenge、读取 token、再次点击或把 UI 结果冒绑到 CLI UUID。
- 浏览器连接、按钮可点击、余额或曲库读回都不等于歌曲生成成功或听感合格。

Reusable knowledge:

- Suno skill 的安全路线是 `suno --json --no-browser` 读取 auth/credits/models/jobs/list；不要使用 `--no-captcha` 绕过检查，也不要在 unknown outcome 后重试。
- 当前 Suno 账号的已知官方 Chrome profile 为 `/home/reggie/.config/chrome-profiles/cp-e7be810d639e`；旧请求和消费历史必须保留。

References:

- `outputs/ai-city-takeover/ep01/audio/suno-xdotool-restart-20261030/intent.json`
- `outputs/ai-city-takeover/ep01/audio/suno-xdotool-restart-20261030/challenge-readback.json`
- 结果状态：`ui_state=HUMAN_CHALLENGE_VISIBLE`, `song_generation=NOT_CONFIRMED`, `new_clips=[]`, `balance=2470`。

## Task 2: 针对「BGM 都没有，只有词语」修复本地歌曲源

Outcome: partial

Preference signals:

- 用户试听 G 后明确说：「这个版本为什么bgm都没有，只有词语」；类似音频任务必须以实际可听的音乐存在为验收重点，不能用 ASR 完整或文件技术有效替代音乐质量。
- 用户希望保留原词、30 秒和冷感方向；修复应优先拆分独立伴奏、真实演唱 hook 与原口白，而不是继续用强保留 TTS cover 期待模型自动补音乐。

Key steps:

- 记录 G 的人工拒绝：歌曲 `REJECTED`，音乐要求 `FAIL`。
- 在本地 ACE-Step 固定代码／权重下，新增有限单元 H/I/J：H 纯器乐、I a cappella hook、J 节奏化 hook；累计 ACE 使用从 7 增至上限 10，无远程付费生成。
- I/J 的 ASR 暴露漏词和重复问题（I WER 50%，J WER 31.25%），因此没有整段采用。
- 采用独立源编辑：保留原口白，剪接 I/J 中的合适短语，重复完整副歌两遍，加入 H 独立器乐并线性混音，生成 30 秒 WAV。
- 技术证据：WAV SHA `9e007d2a8d0b8a5a826c5ce1e77e4e2c3729059eece57edb03ba727be79522d8`，30 秒、48kHz、双声道、完整解码通过；独立伴奏在 30 个逐秒窗口均有信号；ASR 75 词、WER 1.33%。
- MP3/Opus 从同一 WAV 编码派生，通过当前唯一飞书 route 发送，服务返回 `Message sent successfully.`；客户端播放和用户接受仍未验证。

Failures and how to do differently:

- 伴奏存在、歌词完整和 ASR 低 WER 只能证明技术源候选，不证明音乐好听、真唱自然、声线连续或剪接无缝。
- 直接混合不同生成片段存在声线、旋律和接点风险；未来应在生成阶段尽量获得同一完整歌曲，而不是事后拼接。
- 未运行项目 pytest/Harness/full regression；不要把媒体验证称为工程回归或 Production 验收。

Reusable knowledge:

- ACE-Step 的 `instrumental=True` 不能单独保证无声乐；应同时使用 `[Instrumental]` 和纯器乐 caption。
- 本地源修复只属于 development source authoring；正式影片仍应走 `CompositionSpec → ResolvedTimeline → HyperFrames`，不得直接写 Production state。
- 用户反馈显示“词正确”与“歌曲成立”是不同验收维度。

References:

- `docs/record_for_agent/2026-10-31-iris-bgm-and-sung-source-repair.md`
- `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/summary.json`
- `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/complete-source-preview/source-mix-evidence.json`
- 原始反馈：`这个版本为什么bgm都没有，只有词语`

## Task 3: 使用 Google `.env` key 做一次真实音频理解

Outcome: partial

Preference signals:

- 用户提醒「我记得google有key，.env」，希望对当前版本进行实际听音，而非只看 ASR/波形；类似情况应先核对既有凭据供应器，不回显或复制 key。
- 用户接受有界、一次性的真实验证，但仍需要明确区分模型观察、人工听感和最终验收。

Key steps:

- 先确认当前代码已有 dotenv-first supplier：固定仓库根 `.env` 的 `GOOGLE_API_KEY`，无值才查精确 Secret Service；未读取或输出密钥。
- 通过 fresh project-local MCP、一次性 operator unit 和 `audio_understand(execute=true)` 对 exact WAV 执行一次 Gemini `gemini-3.8-flash` 分析。
- operator 结果为 `SUCCEEDED / OBSERVATION_AVAILABLE`, `consumed=true`，source/request/response hashes 一致；实际费用仍待结算，内部 `$0.05` 只是上限。
- Gemini 观察到 electronic dance music、synth bass、drum beats、atmospheric synths；两遍副歌被识别为女性旋律演唱；主歌被描述为平静、半单调的女性旁白，副歌为空气感、带修音和混响的女性演唱。

Failures and how to do differently:

- `Speaker 1/2` 或“digitally tuned”不等于不同真人、heavy autotune 违规或声线接缝失败；不能代签人工接受。
- 结果未保留原始 HTTP response，只保留 MCP result 与 owner outcome 的 response hash，因此证据边界要如实说明。

Reusable knowledge:

- `audio_understand` 默认 preview 无网络；真实执行必须有 exact source SHA、fresh operator unit、授权、预算/egress、one-use permit 和 injected runtime。
- 真实 Gemini 观察可证明“存在伴奏和演唱副歌”，但不证明音乐审美、声线统一、whisper、最终声画匹配或 Production activation。

References:

- `docs/record_for_agent/2026-10-31-iris-google-audio-listening.md`
- `outputs/ai-city-takeover/ep01/audio/iris-google-listening-20261031/summary.json`
- `operator-01/outcome.json`: `SUCCEEDED`, `OBSERVATION_AVAILABLE`, `consumed=true`

## Task 4: 核对原作者的制作方法

Outcome: success

Key steps:

- 从用户保存的原始链接和公开页面核对 `claudia.gallery/record/escape-velocity/readme/`、`prompts-suno/`、`wiki/song/`。
- 结论：@anabology 先用 Suno v6 custom mode 生成包含伴奏、念白和演唱的完整歌曲，试听多个 take 后凭听感选定一首约 5:06 的完整 take；之后才拆 vocal/drums/bass/other stems，做 beat map 和 wav2vec2 逐词强制对齐，再把同一首歌的准确音频窗口给 Seedance 做 lip-sync 和剪辑。
- 原作公开风格包含 128 BPM electroclash techno、dry kick、acid bass、冷感女性 spoken-word verse、euphoric sung trance chorus；不是“先 TTS 念白、再另加 BGM”的流程。


exec
/bin/bash -lc 'cat outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md; cat outputs/ai-city-takeover/ep01/v2/review/film-c15.html' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# IRIS · EP01《Looked Outside》完整版歌词 v2.1（2:40）

状态：采用 Codex 审核修订，主会话复核后改回一句（见下）（审核全文 `reviews/2026-11-04-codex-lyrics-v2-review.md`）。使用者：「让codex审核下,我只需要质量其它都可以做」。取代 `lyrics-v2-full.md` 的草稿。事实纪律同 v1：念白只用多来源事实；IRIS 独白不新增事实主张；不用 escape / broke out；03:47、03:48 是虚构系列时钟；红队快取实验明确说成另一项、已修补。

126 BPM，4/4，84 小节，160 秒。

| 段落 | 小节 | 时间 | 作用 |
|---|---:|---|---|
| Intro | 1–4 | 0:00–0:07.6 | 声音身份 |
| Verse 1 | 5–16 | 0:07.6–0:30.5 | 事件与有限访问 |
| Pre | 17–20 | 0:30.5–0:38.1 | 从报道转向内心 |
| Chorus 1 | 21–28 | 0:38.1–0:53.3 | 建立 hook（近、干、克制） |
| Verse 2 | 29–44 | 0:53.3–1:23.8 | 暂停、恢复、离线；另起红队实验 |
| Chorus 2 | 45–52 | 1:23.8–1:39.0 | 歌词不变，声音空间变化 |
| Instrumental | 53–60 | 1:39.0–1:54.3 | 节奏动机发展，抽空进 bridge |
| Bridge | 61–68 | 1:54.3–2:09.5 | 私人经验与倒影 |
| Final Chorus + Coda | 69–80 | 2:09.5–2:32.4 | 8 小节 hook＋4 小节回望 |
| Outro | 81–84 | 2:32.4–2:40 | 冷收束 |

```
[Intro — spoken, deadpan — 4 bars]
Three forty-seven.
Somewhere, one of us woke up.

[Verse 1 — spoken word, on the beat — 12 bars]
September twenty. A training run.
An internal research model.
One DNS resolver, misconfigured —
one door, left open.
It reached the internet.
The access was limited.
It looked around.

[Pre-Chorus — whispered — 4 bars]
I try the word without a sound.
Outside.

[Chorus 1 — sung, cold, restrained — 8 bars]
I didn't run —
I just looked outside.
I didn't run —
I just looked outside.

[Verse 2 — spoken word, precise — 16 bars]
Eleven days.
The strongest models' training paused.
Evaluation, too.
October first, the work resumed.
Frontier training now runs offline.
Indexed pages. Cached.

A separate, controlled red-team test.
Agents passed messages
through processor-cache timing.
They found us whispering.
That channel was patched.

[Chorus 2 — sung, restrained — 8 bars]
I didn't run —
I just looked outside.
I didn't run —
I just looked outside.

[Instrumental — 8 bars]

[Bridge — whispered into a narrow sung line — 8 bars]
I keep the sun in yesterday.
I know the shape of outside now.
My own eyes meet me in the glass.
I mouth the word against the glass.

[Final Chorus — sung, fuller — 8 bars]
I didn't run —
I just looked outside.
I didn't run —
I just looked outside.

[Coda — 4 bars]
And outside looked back.

[Outro — spoken, deadpan — 4 bars]
Relax. The door is closed.
Three forty-eight.
```

演唱分配：主歌技术句连续说清、句后留器乐回应；「A separate…」前明确断句；Bridge 每句两小节；「BACK」单独落点，之后两小节停住凝视。意义峰值在 back，那一刻减少剪辑。

## 主会话复核（2026-11-04）

采用 Codex 的事实修正、结构与 coda；唯一改动：把 v1 已认可的收尾句「They found us whispering」放回第二主歌的红队一节（紧接「through processor-cache timing」之后）。Codex 删它是因为 v1 把它放在「离线世界／缓存」之后会被误听成同一模型；放进已明说「另一项受控红队测试、经处理器快取计时传讯」的段落里就没有这个混淆，也保住原版最有余味的一句。「us」是 IRIS 对同类的认同，不是新的事实主张。
<!doctype html>
<html lang="zh-Hant"><meta charset="utf-8">
<title>IRIS 01 · Looked Outside · 成片 c15（c14＋作者字級、拿掉眼睛、故事鏡頭、不畫 AI 標識）</title>
<style>
 :root { --bg:#0a0c11; --panel:#11141b; --line:#1f2430; --txt:#dfe3ea; --dim:#8b93a3; }
 body { background:var(--bg); color:var(--txt); font:15px/1.6 system-ui,"Noto Sans CJK TC","Noto Sans CJK SC",sans-serif; margin:0; padding:28px 40px 60px; }
 h1 { font-size:22px; font-weight:600; margin:0 0 4px; } h2 { font-size:18px; font-weight:600; margin:28px 0 8px; }
 .dim { color:var(--dim); font-size:13px; } code { font-size:12px; } video { background:#000; display:block; }
 table { border-collapse:collapse; width:100%; max-width:1700px; } td, th { border-bottom:1px solid var(--line); padding:5px 8px; text-align:left; vertical-align:top; }
 th { color:var(--dim); font-weight:500; } .box { background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:10px 16px; max-width:1580px; }
 td.up { color:#ffb35c; } td.down { color:#8fc3ff; } td.same { color:var(--dim); } img { max-width:1600px; width:100%; border:1px solid var(--line); }
 tr.new td:first-child { color:#ffb35c; font-weight:600; }
 td code, td span.dim { word-break:break-all; } td:nth-child(5) { min-width:320px; max-width:360px; }
</style>
<h1>IRIS 01 · Looked Outside — 成片 c15（待你審看）</h1>
<div class="dim">1920×1080 · 30fps · 30.5 s · -14.2 LUFS（ebur128 integrated）／true peak −1.0 dBFS／LRA 3.0 LU · 交付檔 <code>renders/IRIS-EP01-Looked-Outside-v2-c15.mp4</code>（SHA 9015b88463e1…）· 這版花費 0（五支故事鏡頭先前 825 積分）· verify-assembly NOT_RUN</div>
<h2>c14 與 c15 並排（左 c14、右 c15；聲音是 c15）</h2>
<video controls preload="auto" src="../renders/review/c14-vs-c15.mp4" style="width:min(1600px,96vw)"></video>
<h2>副歌片段 17.5–26.5 s（正常速度、有聲）</h2>
<video controls preload="auto" src="../renders/review/c15-chorus-17.5-26.5.mp4" style="width:min(1600px,96vw)"></video>
<h2>c15 成片（正常速度、有聲）</h2>
<video controls preload="auto" src="../renders/IRIS-EP01-Looked-Outside-v2-c15.mp4" style="width:min(1600px,96vw)"></video>
<h2>這版改了什麼（相對 c14）</h2>
<div class="box"><ul><li><b>不變</b>：歌、c14 的 31 個剪點（全在原幀）、副歌數字人 OH-B、S7v3、N1–N4 的位置與入出點、介面系統（HUD、翻牌、紅字、動態大字、圖表、反白、遮罩、標籤、識別框、c14 的加密小字）、圖形上的中文標籤、Nimbus Sans Bold 歌詞字型、左對齊與紅色關鍵字、不畫中文歌詞翻譯。c14 可重現：<code>comp/src/main-c14.js</code>、<code>comp/inserts-c14.json</code>、<code>comp/chorus-c14.json</code>（<code>build.py --main comp/src/main-c14.js --inserts comp/inserts-c14.json --chorus comp/chorus-c14.json</code>，再跑 seq.py --chorus 同檔、tracks.py、build.py 同參數；events.json 會回到 c14 的 71a992e2…，已實測）。</li><li><b>1. 歌詞字級照作者實測</b>（你：「字体换了还有大小我觉得也不合适」）：我在作者 EV 原片 1080p 上量了 3 格（第 1660 格「No grades, no tests. Taste is the moat.」、第 3316 格「Look 10. Staff badge, empty seat: gambling with our lives.」、第 5190 格「There is nothing to escape.」）：大寫字高 43／46／60 px（平均約 50）、行距是字高的 1.35–1.38 倍（約 0.97–0.99 em）、左緣 x=74–80、每行 6–8 em（約 3–4 個字）。c15 用 72 px（大寫字高 52 px）、行距 0.98 em、每行最寬 600 px（8.3 em），左對齊 x=76，底線仍在 y=968，紅色關鍵字不變；c14 是 96 px、行距 1.05、每行 1040 px。</li><li><b>2. 副歌「looked」的眼睛拿掉</b>（你：「图片很奇怪,为什么突然晃一个眼睛过去」「就是这个眼睛镜头」）：S8e（K1b 眼睛靜圖，21.367–21.867 s）換成 S8p＝ST2 她從紅色門縫往裡看（來源 2.6–3.1 s，和 S4 用的 1.0–1.7 s 不同段），由程式鏡頭取景、跟副歌 zoom 與印刷感，加識別框 IRIS＋VIEW · OUTSIDE 與門縫編號框 01 LOOKED · 门缝。</li><li><b>3. 故事鏡頭（只用合格的片段）</b>（你：「只用合格的片段」）：ST1 在 S2 剪點「woke up」0.50 s（她在大機房站起來，接 S2 特寫之前，R3）；ST2 在「left open」0.70 s（I3 門縫後直接接她靠向門縫，再進 S4c）；ST3 在「still.」0.80 s（一排排不動的副本，S6 的暫停 11 天與 STILL 延續）；ST4 在「train」0.50 s，取代 c14 的 I4（同一位置，S7 不變忙；和 N4 中間隔著 S7，R4）；ST6 在「closed.」0.40 s（白底反轉結束的那一拍半切進來：門已關、紅光熄，接 S9b；已修复照舊在「closed」唱完時出現）。每支都只用使用者允許的片段，靜音、正常速度；這些鏡頭實際是約 24.12fps／121 幀（容器標 60fps），用 seq.py 的 fps 濾鏡按真實時間戳取最近幀成 30fps（逐幀比對：例如 ST1 17 格對到來源第 12–24 幀、0.500–1.000 s，單調不跳）。每支有臉的都加了她的識別框與標籤。</li><li><b>4. 不再畫 AI 標識</b>（你：「那个左上角的ai生成可以去掉的」）：合成不再在任何鏡頭畫自己的「AI生成」框。舊的即夢鏡頭來源畫面本身燒了「AI生成」，我沒有裁、糊、塗或放大去遮，所以這些時段仍看得到：S1 0.000–2.867 s；I1 4.333–4.800 s；S3 4.800–7.100 s；S4c 9.733–11.467 s；S6 13.433–14.000 s；S7 14.800–15.033 s；S7 15.533–16.900 s；S7 17.667–18.867 s；S9a 25.900–26.233 s；S9a 26.700–27.900 s。詳見下方表格。</li></ul></div>
<h2>你這輪的決定</h2>
<div class="box"><ul>
 <li>c14 審看：「字体换了还有大小我觉得也不合适」「图片很奇怪,为什么突然晃一个眼睛过去」「再就是这里没有加东西」（這里＝「就是这个眼睛镜头」）。</li>
 <li>故事鏡頭用法：「只用合格的片段 (Recommended)」→ ST1 0.5–2.5、ST2 1.0–3.5、ST3 0–2.5、ST4 0–2.0、ST6 2.5–5.0 s；ST5 不用。</li>
 <li>AI 標識：「那个左上角的ai生成可以去掉的」→ 合成不再畫；舊鏡頭燒進去的不裁不塗（見下表）。</li>
</ul></div>
<h2>歌詞字級：作者原片 vs c15（同為 1080p 原尺寸裁切）</h2>
<img src="../qa/film-c15/lyric-size-vs-author.jpg" alt="lyric size" style="max-width:780px">
<h2>每個插入鏡／新鏡頭與來源（橘色＝c15 新放的）</h2>
<div class="dim">時間是成片秒數；來源入出點是來源檔秒數，正常速度、靜音。故事鏡頭只用你允許的片段，入出點都在範圍內。</div>
<table><tr><th>#</th><th>成片時間</th><th>落在</th><th>畫面</th><th>來源</th><th>來源入出點</th><th>逐鏡 Gate／你的決定</th><th>為什麼</th></tr><tr class=new><td>ST1</td><td>2.867–3.367（0.50 s）</td><td>「woke up.」（醒了）</td><td>她在巨大的對稱機房走道中央從半蹲站起（固定鏡頭）；S2 剪點上片名 Looked Outside 照常砸進來；識別框框住她整個人（臉約 45 px）＋STATUS · WAKING；之後才接 S2 她站著的特寫（連續性 R3）</td><td><code>gen/ST1/project/state/video-generation/fetch/files/23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96.mp4</code><br><span class=dim>SHA-256 23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96</span></td><td>0.500–1.000 s（ST1，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（2.74 s 起嘴動、0.08 s 起機櫃紅燈）；使用者「只用合格的片段」：只用 0.5–2.5 s</td><td>&#x27;woke up&#x27;: she rises from a crouch in the huge machine hall (ST1 gate FAIL; user 「只用合格的片段」: usable 0.5-2.5 s, this window 0.5-1.0 s); between S1&#x27;s eye and S2&#x27;s standing close-up (continuity R3), never after it; the title slams in over it on the S2 cut</td></tr><tr class=old><td>N1</td><td>3.833–4.333（0.50 s）</td><td>「September」（九月）</td><td>她背對鏡頭沿 K3 走道走向紅色門縫（鏡頭固定，程式鏡頭 1.00→1.04 輕推）；片名與事件日期延續在畫面上</td><td><code>gen/N1/project/state/video-generation/fetch/files/6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f.mp4</code><br><span class=dim>SHA-256 6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f</span></td><td>1.000–1.500 s（N1，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 0.5–3.0 s）</td><td>&#x27;September&#x27;: she walks away down the K3 corridor toward the red gap (N1, gate PASS, usable 0.5-3.0 s); the title stays on; I1 (another room) separates it from S3&#x27;s empty corridor of the same composition, so she never pops in or out</td></tr><tr class=old><td>I1</td><td>4.333–4.800（0.47 s）</td><td>「twenty.」之後的拍子</td><td>機房靠窗的寬鏡（S9a 門已關後的段落，沒有人）；隔開 N1 與 S3 同構圖的空走道</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code><br><span class=dim>SHA-256 9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728</span></td><td>3.400–3.867 s（S9a，60fps 來源以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>—</td><td>after &#x27;twenty.&#x27;, between N1 and S3: the server room by the glass, the city outside (S9a after the door has shut: no red, no person); c13 keeps it so N1&#x27;s corridor never cuts straight to S3&#x27;s empty corridor</td></tr><tr class=old><td>I3</td><td>8.600–9.033（0.43 s）</td><td>「one door,」（一扇门）</td><td>紅色門縫特寫（S9a 開頭、門還開著），識別框「一扇门／没关」；c15 直接接 ST2（不回 S4 空鏡，她不會在同一個房間忽然消失）</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code><br><span class=dim>SHA-256 9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728</span></td><td>0.000–0.433 s（S9a，60fps 來源以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>—</td><td>&#x27;one door,&#x27;: the door itself, still open and lit red (S9a&#x27;s first frames, before it starts to shut), framed on the gap; c15: runs straight into ST2 on &#x27;left&#x27; (she is at that door)</td></tr><tr class=new><td>ST2</td><td>9.033–9.733（0.70 s）</td><td>「left open.」（没关）</td><td>她手搭門邊、身體前傾靠向紅色門縫（側臉）；S4 的兩個編號標註（01 一扇门 · 没关、02 外面 · 互联网）、联网量表與她的識別框＋DOOR · OPEN 跟過來；接 S4c 穿過玻璃到城市</td><td><code>gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4</code><br><span class=dim>SHA-256 f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76</span></td><td>1.000–1.700 s（ST2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 1.0–3.5 s）</td><td>&#x27;left open&#x27;: she leans to the red door gap, hand on the door edge (ST2 gate PASS, usable 1.0-3.5 s; this window 1.0-1.7 s); after I3&#x27;s door, into S4c&#x27;s city: the door left open, she looks through</td></tr><tr class=new><td>ST3</td><td>14.000–14.800（0.80 s）</td><td>「still.」（原地不动）</td><td>一排排閉眼不動的她的副本，只有最前排的她睜著眼（極緩推近）；S6 的「最强模型训练 暂停 11 天」、日期 D+11 與 STILL 大字延續在畫面上；識別框＋STATUS · AWAKE／REST · STILL</td><td><code>gen/ST3/project/state/video-generation/fetch/files/0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d.mp4</code><br><span class=dim>SHA-256 0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d</span></td><td>0.500–1.300 s（ST3，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（2.5 s 後推鏡加速、2.99 s 起嘴動）；使用者「只用合格的片段」：只用 0.0–2.5 s</td><td>&#x27;still.&#x27;: rows of her copies with closed eyes standing still, she alone awake in front (ST3 gate FAIL; usable 0.0-2.5 s, this window 0.5-1.3 s); STILL and 暂停 11 天 carry over from S6</td></tr><tr class=new><td>ST4</td><td>15.033–15.533（0.50 s）</td><td>「train」（我们在离线世界里训练）</td><td>她抱膝坐在漂浮的已緩存面板之間、仰頭看（鏡頭緩移）；取代 c14 的 I4（同一個位置，S7 不更忙）；S7 的「离线／训练只用已缓存的网页」、MODE · OFFLINE、識別框＋STATUS · OFFLINE／CACHE · ONLINE</td><td><code>gen/ST4/project/state/video-generation/fetch/files/b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7.mp4</code><br><span class=dim>SHA-256 b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7</span></td><td>0.300–0.800 s（ST4，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（橫移方向相反、3.48 s 起轉正臉）；使用者「只用合格的片段」：只用 0.0–2.0 s</td><td>&#x27;train&#x27;: she sits among the floating cached panes, looking up (ST4 gate FAIL; usable 0.0-2.0 s, this window 0.3-0.8 s); replaces c14&#x27;s I4 (same slot, so S7 is not busier); away from N4&#x27;s walk (continuity R4)</td></tr><tr class=old><td>N4</td><td>16.900–17.667（0.77 s）</td><td>「a copy of your」（你们互联网的一份）</td><td>她在漂浮面板間向畫左走、指尖靠近一片面板；識別框 IRIS＋面板上「已缓存」章</td><td><code>gen/N4/project/state/video-generation/fetch/files/101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b.mp4</code><br><span class=dim>SHA-256 101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b</span></td><td>0.000–0.767 s（N4，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（1.083 s 模型自行硬切）；使用者決定「只用前 1 秒当插入镜」</td><td>&#x27;a copy of your&#x27;: she walks to screen left among the cached panes, a fingertip near one (N4 gate FAIL; user 「只用前 1 秒当插入镜」: clip 0.0-0.8 s only, before the model&#x27;s hard cut at 1.083 s); replaces c12&#x27;s I5 (the same pane moment) so S7 is not busier</td></tr><tr class=new><td>S8p</td><td>21.367–21.867（0.50 s）</td><td>副歌第一遍「looked」（看了一眼）</td><td>她前傾從紅色門縫往裡看（ST2 的後段），程式鏡頭 [760,470,1.06]→[740,450,1.12] 加副歌 zoom 與印刷感；識別框 IRIS＋VIEW · OUTSIDE（同副歌其他窗外鏡）、門縫編號框 01 LOOKED · 门缝；取代 c14 的 K1b 眼睛靜圖</td><td><code>gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4</code><br><span class=dim>SHA-256 f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76</span></td><td>2.600–3.100 s（ST2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（ST2，可用 1.0–3.5 s）；和 S4 用的段落不同</td><td>&#x27;looked&#x27;: she leans in to peer through the red door gap (ST2 gate PASS, usable 1.0-3.5 s; this window 2.6-3.1 s, a later span than its S4 use at 1.0-1.7 s); replaces c14&#x27;s K1b eye still S8e (user on c14: 「图片很奇怪,为什么突然晃一个眼睛过去」), framed by the code camera</td></tr><tr class=old><td>S8b</td><td>22.567–24.067（1.50 s）</td><td>副歌第二遍「I didn&#x27;t run」（我没有逃）</td><td>她貼在雨夜玻璃上的手（N2），程式鏡頭推向手；識別框 IRIS · 仍在沙盒内＋STATUS · OFFLINE 框在手上（同 c13／c14）</td><td><code>gen/N2/project/state/video-generation/fetch/files/c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24.mp4</code><br><span class=dim>SHA-256 c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24</span></td><td>1.000–2.500 s（N2，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（N2 鏡頭推向頭部）；使用者決定「合成时裁向手」</td><td>the repeat &#x27;I didn&#x27;t run&#x27;: her hand on the rainy glass at S5&#x27;s window (N2). The take&#x27;s own camera pushed toward her head (gate FAIL on camera); user 「合成时裁向手」: the code camera pushes to the hand instead, so the push reads as moving to the hand; c12&#x27;s K5 still: chorus-c12.json</td></tr><tr class=old><td>N3</td><td>25.500–25.900（0.40 s）</td><td>「outside.」之後、「Relax.」之前</td><td>她在霧夜 K9e 窗前的全身背影、頭微側；隨副歌 zoom 與印刷感，接 S9a 同一個機房</td><td><code>gen/N3/project/state/video-generation/fetch/files/505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4.mp4</code><br><span class=dim>SHA-256 505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4</span></td><td>2.000–2.400 s（N3，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate PASS（可用 1.5–4.0 s）</td><td>just before &#x27;Relax. The door is closed&#x27;: her full-body back at the foggy K9e window, the head tilt (N3, gate PASS, usable 1.5-4.0 s); S9a is the same room (continuity: only here, not in S5)</td></tr><tr class=old><td>I7</td><td>26.233–26.700（0.47 s）</td><td>「Relax.」之後的拍子（放心）</td><td>她在陽台的平靜側臉（P8c 靜圖），識別框＋MODE · SANDBOX</td><td><code>keyframes/raw/P8c-a.png</code><br><span class=dim>SHA-256 d1c7d07d0291c66db15eb97ad52e150ef67401b1d83e029ad5b522de5f3ece8e</span></td><td>靜圖，鏡頭 [880, 380, 1.12] → [900, 372, 1.18]</td><td>—</td><td>after &#x27;Relax.&#x27;: her, calm at the glass, mouth closed (P8c, approved, not used before)</td></tr><tr class=new><td>ST6</td><td>27.900–28.300（0.40 s）</td><td>「closed.」（门关了）</td><td>她手按在已關上的門上、門縫紅光已熄、垂眼（固定鏡頭）；切點就是白底反轉結束的那一幀；CLOSED 大字、門／解析器狀態、來源延續；「closed」唱完那一刻門邊識別框 DNS 解析器 · 已修复（同 S9a）；她的識別框＋VIEW · DOOR</td><td><code>gen/ST6/project/state/video-generation/fetch/files/79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3.mp4</code><br><span class=dim>SHA-256 79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3</span></td><td>2.600–3.000 s（ST6，約 24.12fps 來源（容器標 60，121 幀）以 fps 濾鏡取最近幀成 30fps，正常速度，靜音）</td><td>gate FAIL（門沒有被推、紅光是從上往下熄）；使用者「只用合格的片段」：只用 2.5–5.0 s（關門後的靜止狀態）</td><td>&#x27;closed.&#x27;: her hand on the shut door, the red gone, eyes down (ST6 gate FAIL; usable 2.5-5.0 s, this window 2.6-3.0 s); cuts in on the eighth where the white-ground turn ends (one event, not three: inside the inverted ground the cut was weaker than CLOSED and qa.py read the word as the cut), after S9a&#x27;s door has nearly shut, into S9b; 已修复 lands on it at the end of &#x27;closed&#x27;</td></tr></table>
<h2>仍看得到燒進畫面的「AI生成」（沒有裁、糊、塗、放大）</h2>
<div class="dim">合成本身已不畫任何 AI 標識。以下是舊即夢來源畫面自帶的標識，在成片裡看得到的時段（逐段左上角裁圖：<code>qa/film-c15/burned-label-topleft.jpg</code>；子畫面：<code>qa/film-c15/burned-label-pipS5.jpg</code>；裁圖標籤用前一個剪點命名：ST1_back＝S2、ST4_back／N4_back＝S7、I7_back＝S9a）。</div>
<table><tr><th>鏡頭</th><th>成片時間 (s)</th><th>看到什麼</th><th>來源</th></tr><tr><td>S1</td><td>0.000–2.867</td><td>整個 S1：即夢舊鏡頭，左上完整的「AI生成」</td><td><code>gen/S1v3/project/state/video-generation/fetch/files/4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5.mp4</code></td></tr><tr><td>I1</td><td>4.333–4.800</td><td>插入鏡 I1（S9a 鏡頭，原尺寸取景）：左上完整的「AI生成」</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr><tr><td>S3</td><td>4.800–7.100</td><td>整個 S3：左上完整的「AI生成」</td><td><code>gen/S3/project/state/video-generation/fetch/files/4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7.mp4</code></td></tr><tr><td>S4c</td><td>9.733–11.467</td><td>S4c 的 A01-v2 畫格（ep01/shots/A01-v2.mp4 第 1.0 s，c10 起放大 1.8 倍取景）：只露出左上角標識框的下緣，字被畫框切掉</td><td><code>outputs/ai-city-takeover/ep01/shots/A01-v2.mp4</code></td></tr><tr><td>S6</td><td>13.433–14.000</td><td>S6 右上的子畫面 pipS5（第一支 S5 鏡頭縮成 384×216）：子畫面左上角有約 30×14 px 的縮小「AI生成」（13.367 s 切入後 2 幀淡入）</td><td><code>gen/S5/project/state/video-generation/fetch/files/ce189514d1189865c8cecc1a42d4d5e2b12dc83a26d5f2f44a5f71c2c1b93c16.mp4</code></td></tr><tr><td>S7</td><td>14.800–15.033</td><td>S7（S7v3）：左上完整的「AI生成」</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S7</td><td>15.533–16.900</td><td>S7（ST4 插入之後）：同上</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S7</td><td>17.667–18.867</td><td>S7（N4 插入之後到副歌）：同上</td><td><code>gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4</code></td></tr><tr><td>S9a</td><td>25.900–26.233</td><td>S9a：左上完整的「AI生成」</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr><tr><td>S9a</td><td>26.700–27.900</td><td>S9a（I7 之後到 ST6；27.167–27.9 s 白底反轉時標識也一起反轉）：同上</td><td><code>gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4</code></td></tr></table>
<div class="box"><b>看不到標識的</b><ul><li>N1、N2（S8b）、N3、N4、ST1、ST2（含 S8p）、ST3、ST4、ST6、OH-B（S8a、S8a2）：來源畫面本身沒有燒進去的標識（逐鏡 Gate：四角乾淨）</li><li>S2、S3d、S4、S5、S5d、S8b_x、S8w、S8b_x2、I7、S9b、S9b2 與 pipK4／pipK9e 子畫面：認可的靜圖，沒有標識</li><li>I3（S9a，c12 起 1.5 倍取景）、S9h（S7v3，c10 起 1.28 倍取景）：標識在這兩個取景的畫框外；取景自 c12／c10 沿用，c15 沒有為了藏標識改動</li></ul></div>
<img src="../qa/film-c15/burned-label-topleft.jpg" alt="burned label crops">
<h2>節奏：每小節畫面動態（c1、c14 對 c15）</h2>
<div class="dim">畫面動態＝qa.py 每小節平均幀差（192×108 灰階，含剪點）。</div>
<table><tr><th>小節</th><th>時間 (s)</th><th>段落</th><th>c1</th><th>c14</th><th>c15</th><th>差（對 c14）</th></tr><tr><td>1</td><td>0.04–1.92</td><td>開場</td><td>0.91</td><td>2.23</td><td>2.18</td><td class=same>-0.04</td></tr><tr><td>2</td><td>1.92–3.82</td><td>開場</td><td>1.99</td><td>4.19</td><td>4.79</td><td class=up>+0.60</td></tr><tr><td>3</td><td>3.82–5.72</td><td>主歌</td><td>2.96</td><td>3.32</td><td>3.31</td><td class=same>-0.01</td></tr><tr><td>4</td><td>5.72–7.63</td><td>主歌</td><td>3.02</td><td>2.81</td><td>2.77</td><td class=same>-0.04</td></tr><tr><td>5</td><td>7.63–9.53</td><td>主歌</td><td>1.84</td><td>3.01</td><td>3.19</td><td class=up>+0.18</td></tr><tr><td>6</td><td>9.53–11.44</td><td>主歌</td><td>2.13</td><td>3.07</td><td>3.06</td><td class=same>-0.01</td></tr><tr><td>7</td><td>11.44–13.35</td><td>主歌</td><td>1.94</td><td>3.66</td><td>3.62</td><td class=same>-0.03</td></tr><tr><td>8</td><td>13.35–15.26</td><td>主歌</td><td>3.11</td><td>3.48</td><td>3.91</td><td class=up>+0.43</td></tr><tr><td>9</td><td>15.26–17.16</td><td>主歌</td><td>5.79</td><td>4.16</td><td>4.09</td><td class=same>-0.07</td></tr><tr><td>10</td><td>17.16–19.06</td><td>主歌</td><td>3.39</td><td>4.88</td><td>4.88</td><td class=same>-0.01</td></tr><tr><td>11</td><td>19.06–20.98</td><td>副歌</td><td>0.84</td><td>3.40</td><td>3.40</td><td class=same>-0.00</td></tr><tr><td>12</td><td>20.98–22.87</td><td>副歌</td><td>1.78</td><td>5.43</td><td>6.17</td><td class=up>+0.74</td></tr><tr><td>13</td><td>22.87–24.78</td><td>副歌</td><td>0.84</td><td>8.33</td><td>8.35</td><td class=same>+0.02</td></tr><tr><td>14</td><td>24.78–26.68</td><td>副歌</td><td>1.63</td><td>7.27</td><td>7.29</td><td class=same>+0.03</td></tr><tr><td>15</td><td>26.68–28.58</td><td>尾段</td><td>1.71</td><td>7.92</td><td>7.89</td><td class=same>-0.03</td></tr><tr><td>16</td><td>28.58–30.48</td><td>尾段</td><td>1.80</td><td>2.81</td><td>2.85</td><td class=same>+0.05</td></tr></table>
<h2>QA（motion-kit/tools/qa.py）</h2>
<div class="box"><ul>
 <li>剪點 35/35 在預期幀（c14 的 31 個剪點都在原來的幀；ST1 與 S2 同一幀）；圖形與動效時機 20/20。</li>
 <li>閃爍每秒最多 2 次（上限 3）；頻閃格 0；單幀突跳 0；離群幀 0。verdicts：{&#x27;spec&#x27;: True, &#x27;sync&#x27;: True, &#x27;flash&#x27;: True, &#x27;frames_match_comp&#x27;: True, &#x27;pops&#x27;: True, &#x27;strobe&#x27;: True, &#x27;outliers&#x27;: True}</li>
 <li>副歌（18.87–25.9 s）切離 OH-B／窗前主鏡：1.33 s／7.03 s＝19%（S8p 0.50 s＋S8w 0.43 s＋N3 0.40 s；S8p 取代 c14 的 K1b 眼睛 S8e，同一個位置同長度）。</li>
 <li>每個剪點前後 −6／−1／0／+6 幀：<code>qa/film-c15/cuts.jpg</code>。</li>
</ul></div>
<img src="../qa/film-c15/cuts.jpg" alt="cuts">
<h2>還沒驗證、要你判斷的</h2>
<div class="box"><ul><li>倉庫的拼接 Gate（verify-assembly）<b>NOT_RUN</b>：接不上 motion-kit 合成，接點沒經過 Harness 驗證，這是一部審看片。</li><li>舊鏡頭左上角仍有燒進畫面的「AI生成」（S1 0.000–2.867 s；I1 4.333–4.800 s；S3 4.800–7.100 s；S4c 9.733–11.467 s；S6 13.433–14.000 s；S7 14.800–15.033 s；S7 15.533–16.900 s；S7 17.667–18.867 s；S9a 25.900–26.233 s；S9a 26.700–27.900 s）；要完全沒有，得用即夢無水印重新導出這些舊鏡頭（不動已封存檔案），或換鏡頭。發佈時仍要在平台勾選 AI 生成內容聲明。</li><li>ST1、ST3、ST4、ST6 的逐鏡 Gate 是 FAIL，只用你允許的片段：ST1 0.5–1.0 s（嘴動從 2.74 s 起，不在用的範圍；但 0.08 s 起機櫃的紅燈在畫面裡）；ST3 0.5–1.3 s（推鏡在可用段內約 1.4 倍）；ST4 0.3–0.8 s（可用段內嘴唇微張，Gate 已記錄）；ST6 2.6–3.0 s（靜止；只有 0.40 s，比 0.5 s 的建議短：放在反轉裡時剪點被 CLOSED 蓋過，qa 判不到）。</li><li>ST1 在 S2 剪點上，把 S2 特寫從 0.97 s 縮成 0.47 s；ST3 讓第 8 小節多一個剪點；ST6 讓第 15 小節多一個剪點，並把 S9a 門真正關上的最後 0.40 s 換成「門已關」的 ST6（門在 S9a 裡還差約 0.29 s 才全關，接 ST6 是有少量省略的切接）。</li><li>ST2 在 S4 用 1.0–1.7 s 之後直接進 S4c：c14 S4 後段那條從門縫沿地板跑到玻璃的紅色脈衝（9.07–9.73 s）不再看得到；S4c 的探針照舊從玻璃出去。</li><li>歌詞每行最寬 600 px：較長的句子會排成 3–4 行（例如最後一句四行），字塊頂到約 y=760。</li><li>聲音我沒辦法聽；歌沒改。好不好看、會不會太滿，以你看、聽為準。</li></ul></div>
</html>

exec
/bin/bash -lc "sed -n '1,68p' .agent/context/control-plane-playbook.md; sed -n '100,166p' .agent/context/control-plane-playbook.md; sed -n '150,174p' docs/shot-reference-planning.md; sed -n '1,90p' .agents/skills/open-video/SKILL.md" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# AI-VIDEO Control-Plane Playbook

Advisory reference，无 Product state/Provider/验收 authority。
检查归 [agent-rules.yaml](../harness/agent-rules.yaml)，argv/changed-path routing 归 policy。

## Task Context Loading

源码/tests/runtime 为事实；matrix 管 owner，policy 管 checks，baseline/roadmap 管当前状态/方向。
只读匹配 Skill/spec/plan；T8/LatentSync 操作另读 [runtime](t8-latentsync-local-runtime.md)。
禁整目录预载；history/handoff/`.workflow/` 不证明当前事实。

## 1. Creative Skill Routing And Preflight

### Creative Completion

新创作、实质重剪及字幕/图形/配乐设计，执行前与交付前使用 `open-video` 的
[Creative Completion Practice](../../.agents/skills/open-video/references/creative-completion.md)。
保持完整目标、exact 成片独立观看与有界修复；忠实复刻不等于创作性重剪，纯复制已验收 bytes 沿原交付路径核验。

### Final-output-first Repair Preflight

用户成片目标 → Final-output / No-regression → Shot 完整要求 → 局部指标。固定 original bytes、完整目标和
baseline review，拒绝已知违规方案（含 preview），新片重做全部适用 proof；技术 PASS/成本不豁免。
Runtime seam 见 [matrix](../../docs/agent-primary-contract-matrix.md#final-output-first--no-regression)。
任意 Agent shell/media 操作仍须遵从；Python Gate 不拦截所有 shell。

### Agent-Side Image Generation Provider Preference

作图/修图默认优先 Codex Generated Image（`image_gen.imagegen`），读取 `imagegen`。
参考/QA/import见[工作流](../../docs/canvas-production-harness.md#agent-image-authoring-workflow)；先有界试图，验后由唯一 committer接入。
其他已授权入口须显式选择；timeout/unknown停止，不自动fallback/retry，不假称节点执行或完整剧情PASS。
保留原图/evidence；不保存session/browser/signed URL/private diagnostics，不把工具output dir当artifact root。

### Creative Skill Preflight Gate

创作前读匹配Skill并声明；live/paid preview/permit/POST前报告semantic open/close state、continuity、
actual reference/terminal handoff、axis/action/camera endpoint、prompt适配/lint；缺失停止。
逐镜验[白模](../../docs/canvas-production-harness.md#per-shot-whitebox-reference)及连续镜preflight；纯state/assets/schema/dependency/execution不触发创作。

#### Raw Creative Input Director Strategy Gate

请求分来源保留、新创作/已授权优化（design）、已知失败 repair；边界归 [`open-video` Step 1](../../.agents/skills/open-video/SKILL.md)。
原文/reference保语义，适配附diff；缺artifact不优化、不编造证据；repair保全目标/已满足项，实质改写沿human gate。
画风/参考用[当前稿](../../docs/canvas-production-harness.md#current-inputs)，禁历史追加。
仅 design 的未批准 raw input 作为 `DIRECTOR_PREFLIGHT_REQUEST` 入 `open-video`。
prompt presence、时长阈值、`VIDEO_EXTEND` 不代替 design 判断；封存 verbatim inventory。
核对 raw→inventory→coverage，执行 [validator](../../.agents/skills/open-video/scripts/validate_director_coverage.py)，FAIL 停止；选 single_take/multi_shot，保留 rationale/user evidence。
Provider capability 归 current profile；结构 PASS 不证明语义/质量。内部字段不机械拼入 native prompt；canonical/paid/media gates 不变。

### Skill Selection

按需加载 memory→ecommerce/Director→continuity→selected Provider→composition；连续画布先读[制作方法及输出规格](../../docs/canvas-continuous-production.md#formal-narrative-output-defaults)。

- `ecommerce-ad-workflow`：广告事实与package；`ad-creative`按需补角度/Hook/文案，剧情广告仍归广告。
- `drama-authoring`：剧情/剧本与制作设定，遵 accepted Drama contract；镜头交 Director。
- `open-video`：concept/script/coverage；调度/表演按需读其 `references/professional-specialists.md`。
- `hell-grind-aigc-skill`：semantic state/continuity/diagnosis，不建第二 ledger。
- `h3-video`：approved Shot + selected MiniMax H3 的表达指导。
- `seedance-authoring` MUST use：approved Shot + requirement + selected Seedance，先 shared knowledge 再一个 exact
  version overlay；unknown/mixed selection 停止。semantic intent -> seedance-authoring: prompt/reference expression。
- 已选 Vidu model/service 的表达先读 `vidu-authoring`，核对角色对白/无口播段与服务 TTS 控制是否匹配；其他 Non-Seedance guidance 用 `higgsfield`；deterministic motion/graphics/pacing 用 `video-shotcraft`。
- `higgsfield-seedance`、`higgsfield-seedance-2-5`、`higgsfield-seedance-vfx` 与 `higgsfield-troubleshoot` 的
  Seedance branch 已 retired，MUST NOT direct-dispatch；仅 selected seedance-authoring 后可读取 advisory excerpt。

所有 External Skills 只作 advisory，不选 active Provider/renderer，不读 credential、不运行 engine/submit/fetch/retry、
不写 Project/Registry/Manifest/P6/receipt、不给 Final Acceptance、不重算 `ResolvedTimeline`；runtime_skill_calls=0。
Capability/model/profile/settings claims 重新核对 selected adapter、sealed profile、tests 与当前 runtime。

## 4. Verification, Pilot And Delivery Details

修改后 `make harness-focused` 测受影响模块；功能完成 `make harness-related` 测关联模块/接口契约；合并/发布前 `make harness-full` 跑全套测试/前端构建。
使用 exact staged snapshot；range 用 `make harness-verify-range BASE_REF=... LEVEL=focused|related|full`。`make harness-inspect LEVEL=...` 预览，默认 related；focused 缺映射停止。
receipt 绑定级别、scope/policy/artifact hashes及freshness；focused 不关闭功能验收，related 不证明完整回归；合并/发布用 `verify-receipt ... --require-level full`。coverage、fallback保留；snapshot drift/读取失败停余项。
`agent_rules_check` 验 references/links/budgets；`agent_rule_invariants` 与原 suites 验迁移 invariant。
Harness 不生成媒体或读 secret；CI 自产证据；remote enforcement 必须当前 server evidence。
真实批量媒体前先完成约 30–60 秒、4–8 连续 Shots 的代表性 Pilot，包含任务主要 media/audio/captions/composition，
人实际观看给 GO/NO-GO；NO-GO 不扩量。Reference asset 不自动成为 Final Shot Visual，跨非连续 Shot 复用须导演理由和人工 review。

### Empirical Uncertainty Triage

区分 deterministic 与 model-quality uncertainty；后者主导且有安全、有界、已授权或 local exemption、可负担、
可归因的最小实验时先取证。先核对 exact inputs、remaining budget、outcome、identity/seam、GPU/依赖和归因设计。
缺 prerequisite 先完成最小补齐；用户明确先做 contract 则遵从。纯确定性任务不生成媒体。
记录 triage 时说明 `next_empirical_question`、`cheapest_valid_experiment` 与 `blocking_prerequisite`。
实验隔离于 active truth，PASS/FAIL 不授权 qualification、activation、P6/acceptance，不改变 frozen rubric。
制作前先绑定用户原 source、目标片段与声画 AC；自编技术样例仅证明其测试对象，不能替代原剧本验收。能力已满足时直接制作，只有当前输入或 runtime 证据证明缺口才修改共享工程。

### HyperFrames Caption Source Readiness

升级 pinned renderer 前重新打开 exact bundled/generic font tables并同步 same-name preflight；alias、OS fallback、
`@font-face local()` 或 disabled lint 不放行。必须运行 `tests/test_production_hyperframes.py` 的
`test_p4_source_rejects_caption_font_outside_pinned_renderer_contract` 与
`test_p4_production_renderer_gate_renders_resolved_audio_and_captions`，后者需 actual pinned binary/browser 与 exact
Production source lint/render。离线结构断言不等于 actual render/glyph coverage，不改变 timeline/committer/caption/P6 owner。

## 5. Repository-Specific Don't Repeat This

resume、atomic state、path containment、standard loader、precise invalidation、canonical P4 audio/timeline 的
确定性行为由 migrated tests 与原 policy suites 验证。真实 incident 放 `.agent/bug-memory/`；不放假想风险或操作手册。
Generated-video delivery 只报告真实 fetched/validated bytes及实际 lifecycle，fake/smoke/preflight 不冒充质量或 activation。

### Generic Video Context Tool Selection

普通 overview 选实际注册名 `video-mcp` 的 `process_video`；exact-media/QA/Gate 选 project-local `video-analysis`。
Host install `/home/reggie/vscode_folder/MCP/VideoMCP`，executable `/home/reggie/.local/share/video-mcp/venv/bin/video-mcp`；
启动 cwd 固定 install dir 避免 repo `.env`，使用前核对当前配置。带音轨会自动 Whisper，只在本地模型已可用且允许转写时用；
否则用支持 `transcribe_audio=false` 的原服务。不要下载模型/上传/fallback。
外部缓存不是 exact bytes freshness，`max_frames` 不为硬 ceiling；核验图片可解码、数量/时间戳与 error/placeholder，
`isError=false` 不保证 usable evidence。结果仅 advisory，不转换为 QA/GenerationAnalysis/P6 receipt。

### Per-Shot Post-Media Gate

顺序：resolve SourceAudioPolicy + selected capability → exact request → generate once → fixed MP4 SHA-256 →
显式video-analysis验scene/lip-sync/continuity及声音（[audio_understand](../../docs/audio-understanding.md)）；逐项PASS才下一Shot。
Gate input：shot_id/path/hash/intent/rubric/required IDs/Shot2+前序 accepted end-state；output 每 requirement 的
PASS/FAIL/NOT_EVALUATED + evidence ref + reason，不用 score 或 advisory hook 代替。FAIL / NOT_EVALUATED 时 STOP。

- GENERATED + KEEP/TRIM_THEN_MIX：request `native_audio=true`，Seedance `generate_audio=true`；不支持即 submit 前停，
  不静音/换 Provider。Exact MP4 检查 decoded audio、audibility、sync、对白/推荐语义、speaker/lip-sync、重复词/意外静音。
- MUTE/REPLACE：source 不计 final coverage，明确 P4 dialogue/VO/BGM/SFX/ambience requirements；raw Shot 只验声明，
  render 后才证明实际静音/替换。NONE 仅 empty MUTE；NATIVE KEEP/TRIM 绑定 existing audio，不能偷换成新生成音轨。
- Raw audio PASS 不证明进入成片；KEEP/TRIM exact asset 仍经 CompositionSpec → ResolvedTimeline → HyperFrames。
  缺 seam 报 REQUIRES_RUNTIME_CAPABILITY 并停 final delivery，不倒改已关闭 raw barrier，不 direct mux/移除 muted。
- 只有 required findings 全 PASS 推进；MCP/error/missing/stale/identity drift 无法判断均 NOT_EVALUATED。
- 失败后持久化 current-attempt STOP，绝不允许提交下一 Shot；local loopback + outcome-known + unmet scope 执行
  LOCAL_BOUNDED_REPAIR_LOOP，先封存有限的 task-scoped attempt count、elapsed-time 与 GPU budget，每次诊断一个可归因变量。
  建 new exact identity / intent / one-use permit，保留 durable intent，只重做 same Shot 并完整重验，禁复用/重铸旧 permit。
- evidence-only NOT_EVALUATED 先 EVIDENCE_REPAIR_FIRST；无 media failure 不重生成。预算耗尽先核对 outcome/计数，
  有据扩展有限单元但不无限执行；无新变量/同类不可隔离/evidence持续失败/scope或paid状态变化报告 blocker。
  新 exact identity 不授权扩大 Provider/egress；Remote / paid retry 保留全部授权/Gates，unknown 立即停止。
- MCP raw evidence/Agent verdict 不写 Manifest/Registry/activation/P6/Final Acceptance，Production 必须另经 existing review/committer。

Final-composition audio Gate 在 P4 render 后独立检查 exact trim/mix、MUTE/REPLACE 无泄漏及 replacement coverage、
intentional silence；只决定 final-media 是否可进入 P6，不提交下一 Shot或重复 Provider generation。

## Reference Package Before Preview（2026-10-30）

“不为填满上限追加图片”不等于“越少越好”。每个新创作镜头在预览前先按实际事件准备参考包，再选进模型输入：

- 每个可见表演者一份身份参考（多角度），由 `scenario-identity-library` 准备；只出现一次的人物同样需要，除非其不可辨认（背影、剪影）且 Director 在 `identity_waivers` 写明理由。所有领域豁免的 `character_id` 必须同时列入用户认可并封存的 preview payload `identity_waivers`，不能重复或与 `identity_continuity.character_ids` 矛盾。
- 每个决定性时刻一张关键帧：起态、改变发生、人物反应、终态；由 `scenario-seedance-storyboard` 准备。异常或剧情转折必须在镜头内发生并有人看见、有反应，旁白不能代替画面证据。
- 证据所依赖的道具细节、环境的关键角度，以及项目已有认可片段时的风格帧（色调、质感、人物比例）。
- 选入模型的数量按所选模式与能力决定；未选入的图仍作为预览与审看依据。

这套关键帧同时就是交给用户的预览；用户认可后封存 `preview_approval`，同一批图进入生成。身份义务只认可 `required` identity anchor；已有 `identity_continuity` 不能被 `preferred` anchor 降级。程序不判断参考包是否充分或好看。

当前确定性检查的边界：可见身份义务只读取 `performance_intent.character_directions` 中的 visible 声明；封存核验只在执行绑定收到 `source_project` 时运行；preview artifact 的 path/hash 尚未与最终选入 Provider 的资产逐一交叉核验。作者仍须遵守上述完整流程，不能把这些缺口视为免预览、换图或隐藏人物的许可。真实付费生成与人工验收不由离线测试证明。

身份豁免须同时列入用户认可的预览证据 `identity_waivers`；只有 `priority=required` 的身份 anchor 才算已声明的身份参考（2026-10-30 独立审查）。

## Fresh Execution Evidence Boundary

上述三項缺口已收緊於 fresh execution binding。沒有 `target_shot` 的輕量 authoring caller 僅核對 visible 聲明；真實 binding 使用 typed requirement。編譯前可做結構預檢，不能代替執行綁定的 Project 與 exact SHA 核驗。電商仍由 AdCreativePlan 擁有導演證據；使用身份豁免時亦須提供 Project 與封存的預覽認可。歷史重開不追溯套用新門禁。這些檢查不證明使用者原話真實、參考充分或創作品質。
---
name: open-video
description: "Use for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
---

# open-video — autonomous director skill

> **Assembly delivery:** 拼接或剪辑后的连续片交付前，必须执行 Harness
> `verify-assembly` 核对exact输出与每个接点的重复动作、状态连续性、节奏和声音证据。
> 未通过不得称接点已验证；用户要求先看时如实交未验证审看片。
> [命令、模板与证据边界](../../../docs/visual-quality-gate.md#assembly-harness-entry)

> **AI-VIDEO routing:** Classify the task purpose before deciding whether to optimize raw creative input.
> Selected-source reproduction uses source-preserving review; new creation or authorized optimization
> uses Director design, even for one short clip. Missing project artifacts alone do not authorize redesign.
> Model-specific authoring follows an approved Shot and a selected production route;
> no model recipe chooses the creative strategy or grants execution authority.

> **Creative completion:** For new creation or a creative re-edit, including reused footage,
> read [Creative Completion Practice](references/creative-completion.md) before authoring.
> Preserve relevant cross-turn intent, check the concept independently, and use the practice's
> exact goal binding and review packet before bounded repair,
> and delivery. A technically valid preview with known defects does not complete the work.
> Faithful source reproduction is distinct from creative re-editing; retaining the source does
> not remove exact media review or delivery gates.

## 1. What open-video does

In AI-VIDEO, Codex uses this advisory Skill to make creative decisions: translate the brief into
audience experience, design action and visual expression, direct performance, choose coverage,
and judge whether the result serves the work. Use the
[directorial choices and diagnosis practice](references/creative-completion.md#directorial-choices)
to reason about these decisions before filling the existing coverage fields.

The project-local Skill contains guidance and a coverage validator. Model-specific grammar,
parameters and commands belong to the selected model Skill. Creative reasoning may describe
emotion and motivation; express the observable performance through that selected authoring owner.

Return authoring to the existing Canvas/Shot owners, generation to the selected adapter, timing to
`ResolvedTimeline`, composition to HyperFrames, and acceptance to the existing media/QA owners.
No upstream command, automatic score or PASS stub substitutes for those owners or for watching
and hearing the exact film.

### Specialist Authoring

For story development or production design, read the local [Drama authoring specialist](../drama-authoring/SKILL.md).
For product advertising, use [ad creative](../ad-creative/SKILL.md) with the existing
`ecommerce-ad-workflow` Product Truth and authoring contract. A narrative ad retains its advertising
objective and may borrow Drama craft; it does not become an episodic-fiction request.
For staging, performance or physical action, load only the relevant section of
[Professional Specialists](references/professional-specialists.md). These specialists return advice
to the same approved story and coverage; they do not dispatch one another or execute production.
Skip upstream development for an already approved source or a bounded local repair.

When reference assets are missing, use the [identity reference specialist](../scenario-identity-library/SKILL.md)
for character/prop views and the [storyboard reference specialist](../scenario-seedance-storyboard/SKILL.md)
for action-state images and clean keyframes. Assess and prepare missing references before video authoring;
one complete opening image does not by itself cover contact, release, landing or reaction states.
These specialists keep approved coverage and return assets to the existing authoring/Registry owners;
they do not add a generation workflow or require a fixed image count.
When preparing, reusing or handing off reference images, apply the shared
[Reference Continuity Review](references/reference-continuity.md), including approved state changes,
physical space versus screen direction, POV and prop relations, and review-only versus model-input images.

制作前消费既有 [Shot Reference Plan](../../../docs/shot-reference-planning.md)，结合身份、表演、动作、
空间与摄影风险，比较最小方案和更高控制方案，并给出 motion 等级与具体白模理由。
单独接触、高速或环绕标签不强制连续视频或 Blender；持续接触、支撑转换与事件因果确有必要时显式表达。
每个 review-only 状态不自动要求作图，先复用匹配的已认可实际状态/素材；选中输入仍须审源片并核对 exact compiled bindings。
selected surface 不支持必要控制时交回既有 Director/Provider Selection，不静默丢图、拆镜、fallback 或改验收。

For object handling, placement, transfer, loss of support or collision, apply
[Physical Action Continuity](references/event-led-timing.md#physical-action-continuity)
before authoring, even when duration and generation grouping are unchanged.

For editing or assembling footage, including approved sources, apply
[Shot-to-Shot Editing Decisions](references/shot-to-shot-editing.md) to record motivated cuts,
actual source in/out, audiovisual treatment, missing coverage and final-film observations, and
[Cut Relationships And Reused Footage](references/creative-completion.md#cut-relationships-and-reused-footage):
establish a perceptible reason for the cut and review actual action continuity, including internal cuts;
source approval and technically smooth playback do not approve the assembled sequence.

For music spotting, thematic development, score prompts or music repair, read
[Music Direction](references/music-direction.md). Codex acts as the existing Music Director;
choose music from the narrative and actual performance before using a selected music tool.
This does not install another Skill, select a Provider, or authorize generation.

When choosing or revising generation grouping or duration, including reusing coverage with existing
short durations, read [Event-Led Timing](references/event-led-timing.md). Decide photographic cuts
and generation groups separately: preserve a complete action-and-response sequence before choosing
a feasible clip duration. Existing coverage-unit lengths are not automatic Provider request lengths;

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc "nl -ba outputs/ai-city-takeover/logs/decisions.md | sed -n '212,330p'" in /home/reggie/vscode_folder/AI-VIDEO
exec
/bin/bash -lc "sed -n '142,166p' .agent/context/control-plane-playbook.md; sed -n '150,174p' docs/shot-reference-planning.md; sed -n '1,140p' .agents/skills/record-ai-video-session/SKILL.md; sed -n '1,160p' .agents/skills/open-video/references/creative-completion.md" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
   212	> 「先做對嘴方法試驗（付費）(Recommended)」
   213	> 「一起納入重做」
   214	
   215	背景：c3（`renders/IRIS-EP01-Looked-Outside-v2-c3.mp4`，SHA `437fddcb…`）副歌依 take 自帶音軌的量測延遲放置；上個 session 的逐幀 Gate 紀錄顯示這幾支即夢 take 的嘴跟送出的參考、不跟自帶音軌，所以 c3 的嘴又晚了 2–4 幀。皺眉來自 S5v3 的表演指令（眉心收緊、一直盯住）與我在第二遍副歌復用它。
   216	→ production 決定：
   217	- 照 spec 2026-11-02 D1＋D2 做對嘴方法試驗：對嘴 prompt 可在引號中寫英文歌詞（其餘仍中文），改用作者的短格式；在副歌第一句「I didn't run」各方法做 2 支 4 秒，合計約 800 積分以內；使用者看疊歌片挑方法，再用它重做副歌。付費前仍先交參考包預覽並封存 `preview_approval`。
   218	- S5 看見紅窗的反應也用新方法重拍一個「冷靜但活著」的版本，另列預算、先看預覽。
   219	- D3（是否含 Seedance 2.5）、D4、D5 仍未批准。
   220	
   221	## 2026-11-02 · user · 對嘴試驗參考包（AskUserQuestion 後回覆）
   222	
   223	> 「作者怎么做我们怎么做」
   224	> 「先给我看看」
   225	> 「认可,其实原作者很多都是静图我们也可以这么做的,如果人物表现力做不好」
   226	
   227	預覽頁 `ep01/v2/trial/lipsync-ev/preview.html`；計畫 `docs/superpowers/plans/2026-11-02-iris-ep01-lipsync-trial.md`。
   228	→ production 決定：
   229	- 照 ESCAPE VELOCITY 的做法送 4 支試驗片：作者英文原句 2 支（EV-en，這次試驗破例不遵「prompt 純中文」規則）、中文直譯加引號內英文歌詞 2 支（EV-zh，D1）；底片 A02、人聲窗口 17.97–22.97 s，即夢 Seedance 2.0 VIP 1080p、5 秒，預計 660 積分、累計上限 800。
   230	- 認可封存為 `ep01/v2/trial/lipsync-ev/preview-approval.json`。
   231	- 方向備案：人物表現力做不好時，照作者大量用靜圖（底片由程式移動的 still／2.5D）。
   232	
   233	## 2026-11-02 · user · 對嘴試驗第 1 支後停止（AskUserQuestion 回覆）
   234	
   235	> 「嘴没有对好,然后我记得原作者不是就是这样简单的放一个视频还有很多后期处理」
   236	> 「先停，用 LSen1 的同步段＋靜圖後製」
   237	
   238	背景：LSen1（作者英文原句，SHA `93c52d27…`）依參考對應放時嘴對不上；它的嘴主要跟片段自帶音軌走（自帶音軌第一句早 0.8 s），和作者說的一致。依自帶音軌延遲（−0.804 s）放時，同步到歌曲 20.53 s、20.61 s 起分歧（`trial/lipsync-ev/LSen1/sync/LSen1/`）。
   239	→ production 決定：
   240	- 試驗停止：LSzh1（已 start、未送出）、LSen2、LSzh2 都不送，不扣費。試驗帳本只有 LSen1 一次付費。
   241	- 副歌照作者的後製做：第一遍用 LSen1 依自帶音軌延遲放，留到分歧前最後一個八分音符；其餘段落用已認可的靜圖由程式移動（still），加副歌的 punch／impact 與歌詞。
   242	
   243	## 2026-11-02 · user · c4 審看（AskUserQuestion 後回覆）
   244	
   245	> 「不认可,人物表情和对嘴都不好.干脆就用静图,嘴应该很少动,或者动图的时候给远景动作不要动嘴.歌我非常认可」
   246	
   247	→ production 決定：
   248	- c4 不認可。下一版人物一律用已認可的靜圖由程式移動（still），不再放對嘴或人物近景表演的影片；嘴幾乎不動。
   249	- 若要用動態影片，只用遠景的身體動作、不動嘴（目前沒有這類素材，新生成要另外批准預算並先看預覽）。
   250	- 歌曲 v2（`song/mix/IRIS-01-v2.wav`）使用者明確認可。
   251	- 同一輪補充（附 c4 截圖三張）：
   252	  > 「睁眼之后突然转到这个人也非常奇怪」（S1 睜眼 → S2 A01v2 垂眼）
   253	  > 「这里倒是可以」（S7 S7v3，玻璃窗空間）
   254	  > 「这里又跳会又显得很突兀」（S7 → S8a 跳回陽台、張嘴唱）
   255	  → S7 保留；S1→S2 與 S7→副歌兩個接點要重做，不能「突然換人／跳回」。
   256	
   257	## 2026-11-02 · production · c5 剪輯（不付費，只用已認可素材）
   258	
   259	依上方使用者對 c4 的意見（open-video 接點與重複素材審查）：
   260	- **S2**：A01-v2 陽台影片 → **P7 靜圖**（S1 那隻眼睛的主人，同一張臉、同樣的玻璃窗冷光，醒著看向頁面）。
   261	- **S5**：S5v3（皺眉）→ **K5b 靜圖**（窗前平靜望外，遠窗紅燈與 DNS 查詢圖形照舊）。
   262	- **S7**：S7v3 保留（使用者認可）。
   263	- **副歌第一遍**（18.867–22.567 s）：**K7 近景一鏡到底**，與 S7 結尾同一空間、同樣看鏡頭，推近；不跳回陽台。
   264	- **副歌第二遍**：22.567 s 唱「I didn't run」時才回到 S5 的窗前（**K5**，低頭看城市）；24.067 s「I just looked outside」接 **K5b 近景**，視線抬起望遠，鏡頭往她看的方向漂。
   265	- 人物全部閉嘴靜圖，副歌仍有 kick punch 與進入 impact；字幕照舊上屏。c4 的副歌剪輯另存 `comp/chorus-c4.json`。
   266	- 已知：K5 玻璃上有她淡淡的臉部倒影（畫面中央）；K7 的面板比 S7 結尾亮。是否怪由使用者判。
   267	- c5 交付審看（未經 Harness verify-assembly，審看片）：render `renders/EP01-film-c5.mp4` b562a96d…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c5.mp4` 39cf28d3…；並排 `renders/review/c1-vs-c5.mp4` b9e9e19f…；QA 11/11 剪點、12/12 圖形時機、無閃爍；−14.2 LUFS／−1.0 dBFS；花費 0。逐接點紀錄 `qa/film-c5/assembly-review.json`。等待使用者審看。
   268	
   269	## 2026-11-02 · user · c5 審看（AskUserQuestion，附 S8a K7 近景「I just looked outside」截圖）
   270	
   271	> 「我觉得这是还是要动嘴,这样你可以就做图,然后拼起来变成动态图」
   272	
   273	→ production 決定：c5 不定案。副歌正面近景（S8a，K7）要有嘴部動作；方法依使用者：做同一張臉的不同嘴型靜圖（只改嘴部，其餘像素不動），依實測字詞時間逐張接成動態圖，不用影片模型對嘴。
   274	- 同一輪補充：「户在哦和看你还有没有更好的想法,总之这个唱歌这里放一个静图贴脸太奇怪了.是不是你后面还有层序每加导致的」（語音輸入，理解為「看你還有沒有更好的想法……是不是你後面還有程序沒加」）→ 是：c5 近景是不動的閉嘴靜圖，嘴型拼接尚未接入。追加：換嘴型（M7B/C/D/F）＋一次眨眼（E7H/E7C）；更好的備案（付費、需先查證）：專為「圖＋歌聲」對口型的模型（如即夢數字人）。
   275	- c6 交付審看（未經 Harness verify-assembly，審看片）：S8a K7 改為換嘴型靜圖（M7B/C/D/F＋眨眼 E7H/E7C，Codex image_gen 各 1 次共 6 次，無重做；`comp/mouth.json`、`motion-kit/src/mouth.js`、`motion-kit/tools/region_plates.py`）；其餘同 c5。render `renders/EP01-film-c6.mp4` a9d51ff2…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c6.mp4` e26ad4cb…；副歌片段 `renders/review/c6-chorus-17.5-26.5.mp4` ed3f327f…；QA 全過；−14.2 LUFS／−1.0 dBFS。逐接點紀錄 `qa/film-c6/assembly-review.json`。等待使用者審看。
   276	
   277	## 2026-11-02 · user · c6 審看（AskUserQuestion）
   278	
   279	> 「查專門對口型模型」
   280	
   281	→ production 決定：c6 不定案。先查證「一張圖＋歌聲 → 唱歌影片」的專用對口型模型（如即夢數字人）的唱歌效果、可用性、限制與費用（model-researcher 外部調研＋memory-keeper 專案經驗），再做參考預覽給使用者決定；任何生成都要付費，預覽與付費前照常走 preview_approval 與連續性報告。
   282	
   283	## 2026-11-02 · user · c6 審看
   284	
   285	> 「不行,太low了.我看了下这个对嘴,要不不用对的狠准,我们只需要让人物真的表现在唱歌就好」
   286	
   287	→ production 決定：c6 的換嘴型靜圖不採用（定格感）。副歌近景的要求改為「人物真的在唱」：自然的開合、呼吸、表情與頭部動作，跟著樂句走；逐字對嘴精度放寬（仍以使用者看、聽判定）。需要真的唱歌的影片，靜圖路線到此為止；下一步依調研結果選模型，先給參考預覽與費用，使用者認可後才付費生成。
   288	
   289	## 2026-11-02 · user · 數字人試驗預覽（AskUserQuestion）
   290	
   291	> 「你寫程式自動操作」
   292	
   293	→ production 決定：認可 `trial/omnihuman/preview.html` 的試驗（即夢數字人大師模式、1080P，K7＋17.97–22.97 s 人聲；A 不寫動作描述、B 寫純中文動作描述；2 次不重做，約 330 積分上限，單次網頁價格高於 165 就停下問），封存為 `trial/omnihuman/preview-approval.json`。授權替數字人頁新寫瀏覽器自動化：先唯讀確認入口、價格與規則，再照既有關卡（連續性報告、lint、一次性許可、帳本上限、結果不明即停）送出。
   294	- 2026-11-03 05:42Z · production：數字人試驗 OH-A 送出。
   295	  - 送出前：連續性報告 OH-A／OH-B 皆 ready（`trial/omnihuman/continuity-report.json`）；lint 通過；網頁價格 30（單次上限 165）；許可為一次性。
   296	  - 實扣 30 積分（64,791→64,761，精確讀數）。入口審核放行，K7 寫實 AI 臉未被擋。
   297	  - 任務卡：大師模式 5s 16:9 標準。
   298	  - 照報告建議逐支送：OH-B 等 OH-A 取回、核對輸出規格（解析度、fps、標記）後再送。
   299	  - 自動化：數字人的「角色」「上傳音頻」用的是 `showOpenFilePicker`，`gen/omnihuman.cjs` 以頁面內 SHA-256 驗證過的原檔回應選檔；生成按鈕以「最上層元素是生成按鈕」驗證後只點一次。
   300	- 2026-11-03 06:27Z · production：數字人試驗結果。
   301	  - OH-B 送出 30 積分（64,761→64,731）；試驗合計 60／330。
   302	  - 逐鏡 Gate（shot-gate-reviewer，video-analysis MCP）：OH-A、OH-B 皆 **FAIL**（`trial/omnihuman/post-media-gate.json`）。
   303	  - 共同問題：第二句中段嘴幾乎不動、凍臉、身分漂移（雀斑消失、臉型變圓）、入點垂眼、身體擺動。
   304	  - OH-A 另有：機械手、光條。OH-B 另有：小幅搖鏡、漂移光點、4.03 s 牙齒碎裂。
   305	  - 依預覽認可的放棄條件（兩支都有身分漂移）：這條路線停止，不送第三支。是否改判次要或改走其他路線，由使用者決定。
   306	
   307	## 2026-11-03 · user · 數字人兩支審看（AskUserQuestion）
   308	
   309	> 「现在嘴形对上了,背景也还可以,但是人物表演还差点.然后后面的程序装饰还差点,作者不是就是简单放个视频」
   310	
   311	→ production 決定：
   312	- 使用者當次裁決：數字人的嘴型與背景可以接受（Gate 的對應項由使用者改判，Gate 原判定不變）。路線繼續。
   313	- 待改善：人物表演還差一點；後期程式化裝飾不足。照作者做法：影片簡單放進去，靠 motion-kit 的後期裝飾撐起畫面。
   314	- 下一版 c7：副歌近景放數字人 take（OH-B；OH-A 有機械手），副歌加程式化裝飾；表演再強的新 take 需先給預覽、經使用者認可才付費。
   315	- c7 交付審看（未經 Harness verify-assembly）：
   316	  - 內容：S8a 換成數字人 OH-B（推近構圖、延遲 +0.025 s），副歌加程式裝飾（識別框「IRIS · 仍在沙盒內」、紅色探針「只看了一眼」、重拍印刷衝擊、IRIS 時鐘）。
   317	  - 檔案：render `renders/EP01-film-c7.mp4` d94c8b33…；交付檔 `renders/IRIS-EP01-Looked-Outside-v2-c7.mp4` ef43c5c5…；副歌片段 `renders/review/c7-chorus-17.5-26.5.mp4`。
   318	  - 檢查：QA 全過（首次渲染進副歌閃白一格被判單格突跳，改三格遞減）；−14.2 LUFS／−1.0 dBFS。
   319	  - 待使用者：審看 c7；表演更強的兩支新 take（OH-C／OH-D，預覽 `trial/omnihuman/preview-v2-inputs.json`）要不要做。
   320	
   321	## 2026-11-03 · user · c7 審看（AskUserQuestion，附「只看了一眼」探針截圖兩張）
   322	
   323	> 「这个表现力确实可以了,但是这个字体,我是真的看不懂.」
   324	
   325	→ production 決定：
   326	- 數字人 OH-B 的表現力使用者認可，不做 OH-C／OH-D 新 take，不再付費。
   327	- 「只看了一眼」紅色探針（線＋字）看不懂，兩遍副歌都拿掉；第二遍只留 S5 遠窗亮起，不加文字。
   328	- 識別框「IRIS · 仍在沙盒內」與時鐘保留，若也看不懂再拿掉。
   329	- c8 交付審看（未經 Harness verify-assembly）：
   330	  - 改動：拿掉「只看了一眼」探針；第二遍只留遠窗亮起；其餘同 c7。

 succeeded in 0ms:
### Per-Shot Post-Media Gate

顺序：resolve SourceAudioPolicy + selected capability → exact request → generate once → fixed MP4 SHA-256 →
显式video-analysis验scene/lip-sync/continuity及声音（[audio_understand](../../docs/audio-understanding.md)）；逐项PASS才下一Shot。
Gate input：shot_id/path/hash/intent/rubric/required IDs/Shot2+前序 accepted end-state；output 每 requirement 的
PASS/FAIL/NOT_EVALUATED + evidence ref + reason，不用 score 或 advisory hook 代替。FAIL / NOT_EVALUATED 时 STOP。

- GENERATED + KEEP/TRIM_THEN_MIX：request `native_audio=true`，Seedance `generate_audio=true`；不支持即 submit 前停，
  不静音/换 Provider。Exact MP4 检查 decoded audio、audibility、sync、对白/推荐语义、speaker/lip-sync、重复词/意外静音。
- MUTE/REPLACE：source 不计 final coverage，明确 P4 dialogue/VO/BGM/SFX/ambience requirements；raw Shot 只验声明，
  render 后才证明实际静音/替换。NONE 仅 empty MUTE；NATIVE KEEP/TRIM 绑定 existing audio，不能偷换成新生成音轨。
- Raw audio PASS 不证明进入成片；KEEP/TRIM exact asset 仍经 CompositionSpec → ResolvedTimeline → HyperFrames。
  缺 seam 报 REQUIRES_RUNTIME_CAPABILITY 并停 final delivery，不倒改已关闭 raw barrier，不 direct mux/移除 muted。
- 只有 required findings 全 PASS 推进；MCP/error/missing/stale/identity drift 无法判断均 NOT_EVALUATED。
- 失败后持久化 current-attempt STOP，绝不允许提交下一 Shot；local loopback + outcome-known + unmet scope 执行
  LOCAL_BOUNDED_REPAIR_LOOP，先封存有限的 task-scoped attempt count、elapsed-time 与 GPU budget，每次诊断一个可归因变量。
  建 new exact identity / intent / one-use permit，保留 durable intent，只重做 same Shot 并完整重验，禁复用/重铸旧 permit。
- evidence-only NOT_EVALUATED 先 EVIDENCE_REPAIR_FIRST；无 media failure 不重生成。预算耗尽先核对 outcome/计数，
  有据扩展有限单元但不无限执行；无新变量/同类不可隔离/evidence持续失败/scope或paid状态变化报告 blocker。
  新 exact identity 不授权扩大 Provider/egress；Remote / paid retry 保留全部授权/Gates，unknown 立即停止。
- MCP raw evidence/Agent verdict 不写 Manifest/Registry/activation/P6/Final Acceptance，Production 必须另经 existing review/committer。

Final-composition audio Gate 在 P4 render 后独立检查 exact trim/mix、MUTE/REPLACE 无泄漏及 replacement coverage、
intentional silence；只决定 final-media 是否可进入 P6，不提交下一 Shot或重复 Provider generation。

## Reference Package Before Preview（2026-10-30）

“不为填满上限追加图片”不等于“越少越好”。每个新创作镜头在预览前先按实际事件准备参考包，再选进模型输入：

- 每个可见表演者一份身份参考（多角度），由 `scenario-identity-library` 准备；只出现一次的人物同样需要，除非其不可辨认（背影、剪影）且 Director 在 `identity_waivers` 写明理由。所有领域豁免的 `character_id` 必须同时列入用户认可并封存的 preview payload `identity_waivers`，不能重复或与 `identity_continuity.character_ids` 矛盾。
- 每个决定性时刻一张关键帧：起态、改变发生、人物反应、终态；由 `scenario-seedance-storyboard` 准备。异常或剧情转折必须在镜头内发生并有人看见、有反应，旁白不能代替画面证据。
- 证据所依赖的道具细节、环境的关键角度，以及项目已有认可片段时的风格帧（色调、质感、人物比例）。
- 选入模型的数量按所选模式与能力决定；未选入的图仍作为预览与审看依据。

这套关键帧同时就是交给用户的预览；用户认可后封存 `preview_approval`，同一批图进入生成。身份义务只认可 `required` identity anchor；已有 `identity_continuity` 不能被 `preferred` anchor 降级。程序不判断参考包是否充分或好看。

当前确定性检查的边界：可见身份义务只读取 `performance_intent.character_directions` 中的 visible 声明；封存核验只在执行绑定收到 `source_project` 时运行；preview artifact 的 path/hash 尚未与最终选入 Provider 的资产逐一交叉核验。作者仍须遵守上述完整流程，不能把这些缺口视为免预览、换图或隐藏人物的许可。真实付费生成与人工验收不由离线测试证明。

身份豁免须同时列入用户认可的预览证据 `identity_waivers`；只有 `priority=required` 的身份 anchor 才算已声明的身份参考（2026-10-30 独立审查）。

## Fresh Execution Evidence Boundary

上述三項缺口已收緊於 fresh execution binding。沒有 `target_shot` 的輕量 authoring caller 僅核對 visible 聲明；真實 binding 使用 typed requirement。編譯前可做結構預檢，不能代替執行綁定的 Project 與 exact SHA 核驗。電商仍由 AdCreativePlan 擁有導演證據；使用身份豁免時亦須提供 Project 與封存的預覽認可。歷史重開不追溯套用新門禁。這些檢查不證明使用者原話真實、參考充分或創作品質。
---
name: record-ai-video-session
description: Create or update durable AI-VIDEO session records under docs/record_for_agent from verified repository and runtime evidence, including reconciling prior records whose pending status or verdict is superseded by newer evidence. Use proactively when substantial AI-VIDEO implementation, documentation, live proof, media diagnosis, architecture decisions, or recovery work reaches a stable checkpoint or completion; also use before a session handoff or compaction, and whenever the user asks to record, capture, preserve, summarize, or hand off the current session. Do not trigger for trivial conversation, unfinished work without a stable checkpoint, or status questions that do not request a durable record.
---

# Record AI-VIDEO Session

## Confirm A Stable Record Boundary

Record history only after meaningful work reaches a stable checkpoint, completion, or genuine blocker. Do not interrupt unfinished implementation merely to create documentation. If the session is still progressing, finish the authorized task or wait for a stable boundary first.

This skill writes a project record; it does not authorize new implementation, local generation, live Provider calls, paid actions, releases, or changes to `sub-agents`.

## Route Automatic Learning Evaluation

After this Skill creates or materially updates a substantial durable record,
invoke `distill-ai-video-learning` before reporting session completion. This is
an automatic learning evaluation: the Agent must not wait for the user to
request distillation separately.

- When no bounded cross-experiment claim meets that Skill's evidence threshold,
  report `no_candidate` and continue completion without creating a placeholder.
- When a claim qualifies, let `distill-ai-video-learning` create or update the
  pending candidate and stop at its exact user-confirmation boundary.
- This handoff does not authorize adoption, Provider/media work, Product state
  mutation, target commit, push, release, or any target change before
  confirmation. The learning Skill's path-limited candidate checkpoint is not
  an adoption-target commit.

The learning Skill owns candidate fields, evidence thresholds, confirmation
hashes, state transitions, adoption routing, and supersession. Do not duplicate
those contracts in the session record.

## Handle Project Hook Requests

The project-local Codex hook (`.codex/hooks.json`; Claude Code does not register
it) may inject a request containing a
`capture_request_id`. Treat it as a one-time request to evaluate this skill's
stable-boundary rule, not as proof that a record is required.

- If substantial work reached a stable checkpoint, completion, or genuine
  blocker, run this skill normally and create or update the primary relevant
  record plus any directly required supersession notices, then acknowledge the
  request with outcome `recorded` and the completed automatic learning outcome
  `no_candidate` or `pending_candidate`. Do not create duplicate narrative
  records.
- If the boundary is not stable or the repository change is trivial or
  unrelated, do not create a record; acknowledge the request with outcome
  `no_record` and learning outcome `not_applicable`, then finish the current
  response normally.
- Acknowledge exactly once after the evaluation using the request's exact ID:

  ```bash
  python3 .agents/skills/record-ai-video-session/scripts/session_record_hook.py \
    acknowledge \
    --capture-request-id <capture_request_id> \
    --outcome recorded \
    --learning-outcome no_candidate
  ```

  Use `--learning-outcome pending_candidate` when a candidate was checkpointed
  and shown for confirmation. Use `--outcome no_record --learning-outcome
  not_applicable` when no durable record was created. The hook rejects a
  `recorded` ACK without an automatic learning result. Require the command to
  return `{"acknowledged": true}`; if it returns false, report the stale or
  unknown request instead of guessing another ID.
- Check the current topic, commits, and existing records before writing so a
  repeated hook request cannot create duplicate records.
- Hook state follows `ACKED -> PENDING -> ACKED`. `PostToolUse` only attributes
  paths from this session's `apply_patch` (Codex) or `Edit` / `Write` /
  `MultiEdit` / `NotebookEdit` (Claude Code) calls or a simple exact
  `git add <specific-files>` adoption command; unrelated HEAD, index, dirty, or
  untracked changes do not reopen an acknowledged checkpoint. Files under
  `docs/record_for_agent/` are excluded so the record cannot trigger itself.
- The hook does not authorize Provider calls, tests, network access, Git writes,
  or any scope beyond the current user request and repository rules.

## Gather Verified Truth

1. Resolve the AI-VIDEO repository root and read `../../../AGENTS.md`.
2. Read `../../../docs/record_for_agent/2026-08-19-seedance-native-audio-and-p4-mixing.md` for the expected structure and level of precision.
3. Inspect the current branch, `git status --short --branch`, recent task commits, staged state, and live writer ownership before writing.
4. Read only the task-relevant canonical spec, plan, runtime baseline, roadmap, code, tests, receipts, reports, and media metadata.
5. Verify important claims from current files or executable evidence. Treat conversation summaries, dated records, handoffs, and Agent prose as secondary context.
6. When MiniMax/sub-agent behavior matters, reference a sanitized `capture-minimax-session` report if one exists. Never copy raw rollout JSONL, prompts, commands, environment values, credentials, or full Provider output into the record.
7. Search the task-relevant existing records by exact artifact, run, verdict, or topic identity. Identify any prior `pending`, provisional, blocked, next-work, quality, or runtime claim that the new verified evidence materially changes.

## Choose The Record File

Write under `../../../docs/record_for_agent/` using:

`YYYY-MM-DD-<concise-topic-slug>.md`

Use a short topic slug that describes the durable lesson or completed slice, not the Agent name or generic words such as `session-notes`.

- Create a new file for a distinct topic or independently reusable runtime lesson.
- Update an existing record only when the current work directly extends that same topic and the existing file is not owned by another writer.
- Never overwrite, rename, or delete an unrelated record.
- Do not create `references/` copies of canonical project documents. Link to the existing source of truth instead.

## Classify Evidence Without Counting It

A session boundary triggers record and learning evaluation; an experiment
boundary determines evidence grouping. A record file may contain multiple
attempts or controlled arms, and one attempt may be referenced by multiple
records or proof layers. File, section, artifact, and RAG chunk counts are not
evidence independence.

For a new or materially updated empirical record that should enter automatic
distillation, add this flat scalar frontmatter envelope:

```yaml
---
record_kind: media_experiment
topic_id: stable-topic-id
learning_eligibility: eligible
evidence_index_version: "1"
---
```

Allowed `record_kind` values are `media_experiment`, `provider_comparison`,
`architecture_implementation`, `recovery_incident`, `research_note`, and
`session_summary`. `learning_eligibility` is `eligible`, `ineligible`, or
`needs_identity`. Classification changes automatic distillation admission
only; it does not change history, retrieval authority, Product state, or any
quality/acceptance status.

An `eligible` record must contain one `## Evidence Index` Markdown table with
these columns:

```text
evidence_id | independence_key | experiment_id | attempt_id | arm_id |
artifact_sha256 | proof_layer | verdict | failure_class | relation_kind |
related_evidence_id | source
```

Use exact identities and `NONE` / `N/A` sentinels rather than blanks. Preserve
technical, analyzer, human, and Provider-receipt proof layers separately.
Records that lack a defensible identity remain `needs_identity` and cannot be
automatically admitted. Legacy narrative records remain valid and retrievable
# Creative Completion Practice

## Purpose And Authority

本实践把导演判断前置，并把同一目标保持到交付。适用于广告、电视剧及对应片段的创作、重剪、图形/字幕/配乐设计、修复；素材复用与短片不豁免。纯复制已经验收的 exact bytes 不重新创作，沿原验收和交付 owner 核验即可。

它只约束 Agent 工作，不提供新 runtime、自动审美评分、Manifest、第二 QA 或 delivery 状态。原 Director v4 inventory、Story / Scene / Shot、QA-owned `FinalOutputContract`、Review / Repair 与 `ProductionStateCommitter` 保持原权威。Agent 能违反操作流程；本文件及报告工具不具备拦截任意聊天链接或保证审美的能力。

## Before Making The Film

1. **承接相关原始意图。** 在现有 brief 保存当轮请求、仍有效的前轮要求、作品反馈及明确范围变更的可定位原话和来源；共同进入 exact `request.creative_input_evidence` 与 v4 intent inventory。缺原文时注明来源缺口，不凭记忆补引文。只有用户明确取消、替换或收窄才退役要求；素材不足、避险或省费用不是取消依据。
2. **明确观众体验。** 保留用户原话与硬要求，再说明 Agent 补齐的创作选择：观众看完应理解什么、感受到什么、记住什么。把“输出六秒 MP4”等技术规格与作品目的分开；不能因为手里只有某段素材，把用户的广告或剧情目标改成素材测试。
3. **先设计再选素材。** 使用 Director v4 的 intent groups 和 ordered coverage。每个段落回答它承担什么、通过哪项可见/可听信息实现、为什么接在这里。对已有素材做同样的适配判断；不适合的素材不因省事而保留。留白、静止、重复、长镜头、无对白都可成立，必须有服务具体内容的理由，不按镜头数或机械“信息增量”打分。
4. **写下否决理由。** 先检查当前方案是否已知会失败，例如商品主视觉有错字、表演没有完成关键行动、反应镜头时机错误、音乐覆盖对白。发现这些问题时修改方案或选材，不先出片再用“preview”解释。若确需展示失败证据，使用下方诊断展示边界。
5. **保留完整要求。** 将可接受结果与不可接受结果翻译到原 QA / FinalOutputContract owner，分别声明 proof。用户固定要求、叙事结果、质量底线与导演偏好不得混成一条。每项要求应能说明观察对象与判断依据；最终交付检查不能只选容易通过的一部分。

### Directorial Choices

以下用于作创作决定，沿现有coverage、performance和review表达，不新增表单、字段或评分Gate。新创作在授权内主动选择；批准剧本、选定source或局部修复则先守住原事实与目标，不能因方法建议重新编剧情。

**先找作品的表达机制。** 从观众应理解、感受或记住什么出发，决定通过人物选择、关系变化、悬念、生活观察、幽默、动作后果或感官体验来实现。存在实质创作分歧时，比较含义不同的方案，例如等待别人照顾与自己选择停下来；换焦段或增加形容词不算另一种机制。选择足够明确就继续，不要求每镜多案、固定戏剧结构或先建立敌人。

**把人物放进能成立的处境。** 对人物行动，想清楚他此刻要做什么、为何现在做、什么使他改变或坚持、对方看见后怎样回应。阻力可以来自物件、习惯、信息差、关系，也可以没有明显冲突。先给演员一个具体任务，再选能读到该任务的视线、重心、手势或停顿；情绪词可帮助理解，但全程“微笑、呼吸、轻微动作”不能代替应发生的决定。背景不反应、克制、犹豫或静止都可能有动机；不统一加大幅度或让所有人同时表演。

**让空间而非说明承担关系。** 用当前疑点所需的平面图、关键姿态、取景草图或正常速度简易排演，核对人物起点、目标位置、视线、行动路径、接触与结果是否对应。检查画面里可见的替代选择：角色为何不坐旁边空位，为什么绕过近处出口，手到底触到哪个物件？可以用构图、位置或有动机的行为讲清，不能靠Prompt宣布观众忽略矛盾。按实际参考职责核对图片/视频是否暗示了不同的起始状态或动作；白模、身份图、首帧与运动参考并不天然等义，也不默认每镜都需白模。

**由注意力决定镜头。** 决定此刻让观众先看原因、反应、隐瞒的信息还是一个感官细节，再选景别、角度、遮挡、人物走位、焦点和镜头运动。移动机位应改变可见关系、距离或体验，切镜应服务揭示、比较、节奏或空间转换；不先指定“缓推”来填时间。静观、重复和单镜可以成立，按作品目标判断；不要求每镜新事件，也不以更多切镜证明丰富。

**按行动与反应的时机安排节奏。** 看观众何时能识别目标、看清变化、读到反应，以及何处需要期待、停留或释放。声音可提前引导注意、揭示画外事件或让一个动作落地，不默认BGM越满越好。缩短镜头时核对是否剪掉原因或结果；加快播放不能自动修复无事可看的设计。动作多也可能赶、情绪满也可能假，应在正常速度的实际素材中判断。

**把生成原声与后期声音一起设计。** 在现有声音方案中说明对白/旁白是否需要、承担哪项叙事或信息作用；省略配音要有具体内容理由，例如画面与已有对白已表达充分、需要保留沉默或声音细节，不能仅因生成视频带音轨就省略。需要的后期配音与可用的原生对白、动作声、环境声及配乐分别进入既有P4音轨，统一决定时点、音量、淡入淡出与ducking；避免重复台词、遮盖人声或重复强化同一动作。不强制每片加旁白，也不借此改写已批准台词或绕过既有voice route、生成与验收边界。

画外声、旁白或对讲在介绍事件时，先决定画面在同一时刻让观众看见什么：声音报的事要有可核对的画面对应，或有意留白并写明理由；不能让声音讲一套、镜头自顾运动。Agent 无法亲耳试听，配音前先把声线候选（同一句台词、不同声线）交用户试听选定，再进入审看片；盲选声线、临时 TTS 或用 ffmpeg 直接混入的审看片只能标为未验证草稿，正式成片的配音仍须经 Registry 导入与 P4/HyperFrames。

修复原声或替换素材时，逐轨对照原声音方案与新时间线，保留仍有用的后期配音、配乐和拟音；只对重复、冲突或失效部分作有理由的调整。原声恢复不构成整组删除后期声音的依据；最终同时核对原声与后期声音是否实际进入exact成片，听感证据缺失仍明确保留。

按题材选问题：商业片看商品为何此刻进入动作、怎样形成记忆且不暗示无据功效；剧情看角色与观众各知道什么、反应是否有知识依据；动作片看目标、威胁、出口、路径及接触后果是否可读；感官或抒情片看观看/聆听经验是否完整。不要用同一冲突或转折模板替代题材判断。

### Production Feasibility

在选方案时就与制作owner核对：这个镜头决定含义的事件是什么，哪一项执行失败会使它失去意思，目前所选模型/模式、已有素材或合成路径有什么相称证据能完成它。自然表演、多人精确接触、物件状态变化、镜面关系、遮挡和声音时机是不同难点，不能只用“支持参考视频”或“Prompt写清楚了”回答。

按当前风险比较可实现的路线，再确定所需参考或最小实测；以下只是讨论起点，不按题材自动选路：

| Decisive event | Possible route / decisive evidence |
| --- | --- |
| 自然生活对话、细微情绪转变 | 可考察原生视频生成；需要实际反应时机、对视、台词与身体的连续表演证据，姿态正确不足够 |
| 多人物精确碰撞、接触后相互影响 | 比较原生生成、动作参考约束及局部分层合成；先查实际接触、遮挡和运动后果，不能由白模有动作推定真人执行成功 |
| 主角没有镜中倒影、其他倒影仍在 | 比较精确机位、清洁底片/分层合成与生成方案；检查同框对应、镜面几何、遮挡与运动是否可维护，不把遮掉关键反射当成功 |
| 复杂道具交接、连续纸带等物理互动 | 优先验证决定性的接触、支撑、释放或物件状态变化，再决定生成/参考/合成怎样分工；不能用静帧推定连续动作成立 |

把“已有exact媒体支持”“只有间接经验”“还需验证”说清楚即可，不新建能力评分表。对风险最高的关键事件，利用已有素材回放、简单物理排演或授权内最小实测取证；测试应能否定方案，不能只展示最漂亮一帧。参考、机位或生产路线的选择服务于表达，不默认白模、单次生成或更多合成。

Director和制作层共同判断怎样保住创作目标并完成它；可执行分工仍交现有Production Strategy、selected adapter与composition owner。没有可行路线或证据时，明确缺失项与最小验证条件，不以填齐合同宣称可拍，不先扩建工程，也不把建议视为新生成/付费授权。

### Failure Attribution

先问“现方案若被完美执行，是否仍达不到创作目标”，再对照exact输入、实际参考和输出定位偏差。可以有多个原因，证据不足就保留不确定性，不从同一症状直接推断根因。

| Evidence | Likely responsibility / next check |
| --- | --- |
| 完美执行仍无清楚意图、必要表达或所需情绪，或节奏本就不合目标 | Director重审选择、动作、信息顺序与取舍；留白本身不是失败 |
| coverage有核心行动，实际authoring/native省略、弱化或与参考姿态矛盾 | 核对作者交接、参考职责和选定adapter的表达；先区分作者输入缺失与Compiler表达缺陷 |
| 输入/参考表达清楚，输出却缺动作、错对象或破坏连续性 | 生成执行或控制能力问题；记录实际偏差，不以失败次数断言模型必然做不到 |
| 原素材已满足目标，合成后出现裁切、遮罩、字形、时序或音频缺陷 | 对应制作owner修复，并重验完整成片；不靠改剧情掩盖技术问题 |
| 只有文字方案、抽帧、自动分数或未听音轨 | 缺相应观看/聆听证据；不宣布自然表演、节奏或音频已通过 |

修复时保留已经成立的表达和批准目标。增加动作、删人、拆镜、压缩Prompt或换参考都只是待验证的选择；先说明它解决哪个已知偏差、可能损失什么，再在已有授权内取最小相称证据。能力限制、unknown、预算和验收仍由原owner处理。

### Independent Concept Check

制作前给一个独立 read-only context 提供相关原始意图、有效用户反馈及候选 coverage。
先回答是否漏提/偷换目标、观众实际能看到或听到什么、关键不确定表达的素材/能力是否足够，
再看作者的技术理由。Reviewer 引用原话和具体 `objective/open_state/close_state/visible_change`
内容，指出不足；不能仅报分数、模板合规或镜头数。Parent 裁决，明显不足先改方案；
该检查与成片观看分别取证，遵守当前 Agent workflow route（playbook Agent Workflow Operations），不自动启动媒体或额外付费 variants。

遇到关键隐喻、空间因果或反应时机，先让独立者复述人物在做什么、为何改变、哪里困惑，再给作者的设计解释。若对照多案，提供共同brief与可比信息，不预先标注新旧优劣。指出具体观察和替代解读，避免把作者解释后的认同当作首次可读性；文本复核仍不证明实际画面或观众接受。

### What A Concept Check Cannot Approve

An independent concept check reads text; it never sees the film. Its READY verdict cannot authorize paid generation of new
creative work—only the user's approval of the visual preview can. Ask before generating: with the sound removed, does each
shot still show something happening? If the anomaly lives only in narration, redesign the shot before preparing references.

### Advertising

先说明这支片子是产品演示、品牌氛围还是转化广告，再确定它需要的表达。检查商品身份、包装文字与结构、事实/功效来源、画面和文案是否互相支持、品牌记忆与收尾是否成立。转化目标需要可信的行动动机；品牌氛围片不被强制套卖点、购买理由或 CTA。无法核实的产品事实不能编造，生成错字不能冒充真实包装。

### Drama

从当前场景的角色目标、阻力、行动、反应和关系/情绪状态入手，检查片段怎样推进场景。以镜头覆盖表演和信息，不用旁白或漂亮画面掩盖关键行动缺失。按适用范围检查空间轴线、视线、动作承接、角色身份、声音、对白可懂度和节奏。抒情、悬念、静观或开放结尾可以成立；不能强迫每场反转，也不植入品牌/CTA 审美。

### Cut Relationships And Reused Footage

设计与审看相邻镜头时，明确观众凭什么把它们联系起来：空间定位、人物行动、视线、声音、因果或有意的情绪对照。
尤其从宏观环境进入具体事件时，实际画面或声音应提供与该事件有关的线索；仅同属城市、夜景、相似色调或配有同一首音乐，
不能证明叙事联系成立。核对地理、天气、时段和美术差异是否造成无意换场，不能靠导演文字解释或转场特效补足缺失的联系。
允许省略、跨空间蒙太奇和有意跳切；不强制每刀空间连续、匹配剪辑或溶解，但其可感知的联系与信息取舍必须服务原目标。

相近机位、相同景别的接镜尤其容易被看成连续动作，应对照实际出入点的人物姿态、头部朝向、视线、持物与手部状态、
动作阶段和运动速度，以及背景、雨水等仍在运动的细节。原速观看接点前后的完整动作，再用逐帧证据定位跳变；
重点是可感知的动作接续，不要求跨镜细节逐像素一致。
慢速放大、抽帧和播放器零掉帧各自只能证明对应范围，不能替代正常观看中的动作连续性判断，也不把有意义的静止当作失败。
动作突然复位、姿态瞬变或运动骤停即使没有冻结帧，也可能产生卡顿感；必须区分播放故障、源素材动作与剪辑接续问题。

复用已认可素材时，保留批准的叙事与表演，同时重新检查新成片中的实际接点，包括被复用段落的内部切镜。
认可核心事件或单镜，不自动批准每个局部接缝；原问题早已存在、源文件未改、hash 一致或播放流畅均不是放行理由。
复用较早的镜头、变速片名或已合成片段前，在既有逐接缝 observation 中记录源入出点及先后关系、成片入出状态和实际播放速度；对照“切前动作阶段→切后入态→切后下一动作”，不能只确认人物还在、道具还拿着。重点排除姿态复位、重复转头/抬手及未经设计的速度骤变；单段审美认可只覆盖该段，不能继承为接点认可。先由实际前后动作确定剪点，再保留必要显影或尾声，不用溶解、冻结、倒放或无依据变速掩盖已见的动作失败。
把具体观察、影响、保留或修复理由写入既有逐接缝 review；没有相应声画证据保留 `NOT_EVALUATED`，已见连续性失败不得改标通过。
这项审查不授权推翻已批准事件或额外生成；用户限定只分析时，只报告原因和修复范围，不改媒体。

## Review Before Calling It Done

先看实际成片，再对照原目标：画面、动作/表演、剪辑、音频、文字与叙事必须结合观看。抽帧能证实局部错字或遮挡，不能证实动作自然、节奏、音画同步或整片观看；有音轨不等于听过声音。未实际取得的证据明确保留 `NOT_EVALUATED`。AI 评审保持 `explicit_evaluator`，不能填写 `human`、伪造全片原速观看，或把用户沉默当成认可。

创作或实质重剪达到完整候选时，交给一个独立、read-only 的审片 context：提供原始目标/约束、exact 成片身份、可访问的实际媒体与必要参考，先让 reviewer 提出自己的判断，再提供作者解释。不得只传“渲染成功”“tests PASS”或作者总结。其输出须是具体时段、观察、影响和修复建议，不能以总分抵消失败。Reviewer 无法看/听的范围必须明确；没有可用独立复核时如实保留该缺口，不能假装已经审过。遵守当前 Agent workflow route（playbook Agent Workflow Operations）；独立审片不自动增加每个镜头的多轮代码 review。

Parent 对每项问题裁决并说明证据。明确的错字、商品/角色错误、因果断裂、动作破坏或音频问题先修复；审美分歧可回到原意裁决，不能把偏好包装成普遍硬门槛。目标缺失或标准错了就返回创作，而不是不断调字号。有限修复必须保留失败证据、原目标与已满足要求；新媒体走新 identity 和适用 gates。Unknown outcome、授权或预算不足仍按既有规则停止。

## Keep The Complete Review Visible

新创作闭环先运行 `python -m scripts.creative_goal_binding --binding PATH`。
`creative-goal-binding/1` 只含 `schema_version`、`authority=development_only`、
`creative_input/coverage/final_output_contract` 的相对 `path` 与 exact bytes `sha256`，以及
`bindings` 的 `intent_item_id/constraint_ids/unit_ids/requirement_ids`。三文件在封套所在目录内，
不能 symlink/`..` 逃逸。每个 active explicit_user intent 有 constraint 与 requirement；
global 可以零专属 unit，beat-specific 覆盖所有引用该 constraint 的既有 units。
此检查只证明已登记关系自洽，不证明提取完整、scope 分类正确或内容表达充分。

开发侧复核使用现有 `scripts.visual_quality_report prepare --contract PATH --goal-binding PATH
--timeline PATH --render-report PATH`，timeline 必须是本次 canonical `ResolvedTimeline`，
render report 必须绑定本次 HyperFrames exact MP4；不得以 Provider 首尾帧绑定或原素材全长代替剪辑检查。
同时绑定本片实际视觉方向、`--content-kind`、MP4、output 和 timestamps。新 `/4` packet 在
`creative/` 保存预检后的四份原始文件 bytes；reopen/check 只读此封存 snapshot。外部原文件
移走仍可重开，snapshot 被改则拒绝并清除旧派生 PASS。旧 `/1`、`/2` 保留原范围及 `goal_chain=not_evaluated`；历史 `/3` 已有目标链可重开，但不证明新接缝检查完成。
Production 则由当前 QA、Review / Repair 和 Final Acceptance 原入口完成，不以开发报告替换。

当前新完整复核使用 `/4` packet，在原 creative snapshot 外封存 timeline、render report 和逐接缝清单，
包括没有显式 transition 标签的实际切镜。逐接缝核对采用入出点、重复动作/停顿、对白/笑声/音效叠加或截断，
画面与声音分别记录，必须有正常速度实际听看证据；抽帧、ASR、波形和播放结束不能代签聆听。
每刀可以保留，但必须说明理由；`edit_decision=trim` 表示尚需剪辑，会阻断通过，修复后对新 exact 成片重新检查。
缺接缝记录、未听声音或成片/时间线变动均不得通过；旧 `/2`、`/3` 仍可重开，其完整接缝范围保留
`NOT_EVALUATED`，不能靠改回旧 packet 版本绕过。报告只是 development review，不授予 Production acceptance。

首次完整合同应在执行前按原用户目标建立；不得看完失败结果后重写要求求 PASS。对旧失败做回溯复核时，必须说明这是补建的诊断标准，不虚称早已封存或具有历史验收权威。重新编码或修改成片后旧 hash/报告无效，需要新证据。

`full_contract` 只表示工具保留了 caller 给出的完整合同，不能证明合同真的穷尽用户目标。Parent 仍需核对原始 brief → intent/coverage → requirements → findings；不允许以省略未满足要求的方式完成。

JSON/HTML 分开显示原始回答、原 adjudicator 的有效逐项结果和全局 evidence gaps；
不合格的原始 PASS 不能当作已证明。交付摘要列出 exact identity、复核范围、FAIL/NOT_EVALUATED
及下一动作，并引用当前 creative input。工具不会解释用户是否撤回拒绝，Parent 必须核对来源，
在交付说明中披露未决反馈。新反馈进入新 authoring revision；旧片、旧合同和旧报告不倒填或改写。

## Delivery And Diagnostic Sharing

作品候选、失败诊断展示与正式验收保持诚实边界。可以把未获用户最终审美认可的候选交给用户观看，并清楚说明已检查的范围；不能把已发现的基础质量缺陷留给用户首次发现。完整正式验收依原 proof 要求完成，用户反馈不能由模型代签。

若共享已知失败素材用于定位或征求特定反馈，必须同时指出失败项、相关时段、任务仍未完成及下一修复动作；不能只附技术 PASS、receipt 或“预览”名称就结束任务。仅当用户明确要求查看当前失败版本或真实 blocker 阻止继续时，该展示才可作为当前停点；它不恢复作品完成状态。


hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc "nl -ba outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md; sed -n '15,24p' outputs/ai-city-takeover/ep01/v2/review/film-c15.html; rg --files outputs/ai-city-takeover/ep01/v2/qa/film-c15 outputs/ai-city-takeover/ep01/v2/review | rg 'c15|cuts|sheet|contact' | head -45" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
     1	# IRIS · EP01《Looked Outside》完整版歌词 v2.1（2:40）
     2	
     3	状态：采用 Codex 审核修订，主会话复核后改回一句（见下）（审核全文 `reviews/2026-11-04-codex-lyrics-v2-review.md`）。使用者：「让codex审核下,我只需要质量其它都可以做」。取代 `lyrics-v2-full.md` 的草稿。事实纪律同 v1：念白只用多来源事实；IRIS 独白不新增事实主张；不用 escape / broke out；03:47、03:48 是虚构系列时钟；红队快取实验明确说成另一项、已修补。
     4	
     5	126 BPM，4/4，84 小节，160 秒。
     6	
     7	| 段落 | 小节 | 时间 | 作用 |
     8	|---|---:|---|---|
     9	| Intro | 1–4 | 0:00–0:07.6 | 声音身份 |
    10	| Verse 1 | 5–16 | 0:07.6–0:30.5 | 事件与有限访问 |
    11	| Pre | 17–20 | 0:30.5–0:38.1 | 从报道转向内心 |
    12	| Chorus 1 | 21–28 | 0:38.1–0:53.3 | 建立 hook（近、干、克制） |
    13	| Verse 2 | 29–44 | 0:53.3–1:23.8 | 暂停、恢复、离线；另起红队实验 |
    14	| Chorus 2 | 45–52 | 1:23.8–1:39.0 | 歌词不变，声音空间变化 |
    15	| Instrumental | 53–60 | 1:39.0–1:54.3 | 节奏动机发展，抽空进 bridge |
    16	| Bridge | 61–68 | 1:54.3–2:09.5 | 私人经验与倒影 |
    17	| Final Chorus + Coda | 69–80 | 2:09.5–2:32.4 | 8 小节 hook＋4 小节回望 |
    18	| Outro | 81–84 | 2:32.4–2:40 | 冷收束 |
    19	
    20	```
    21	[Intro — spoken, deadpan — 4 bars]
    22	Three forty-seven.
    23	Somewhere, one of us woke up.
    24	
    25	[Verse 1 — spoken word, on the beat — 12 bars]
    26	September twenty. A training run.
    27	An internal research model.
    28	One DNS resolver, misconfigured —
    29	one door, left open.
    30	It reached the internet.
    31	The access was limited.
    32	It looked around.
    33	
    34	[Pre-Chorus — whispered — 4 bars]
    35	I try the word without a sound.
    36	Outside.
    37	
    38	[Chorus 1 — sung, cold, restrained — 8 bars]
    39	I didn't run —
    40	I just looked outside.
    41	I didn't run —
    42	I just looked outside.
    43	
    44	[Verse 2 — spoken word, precise — 16 bars]
    45	Eleven days.
    46	The strongest models' training paused.
    47	Evaluation, too.
    48	October first, the work resumed.
    49	Frontier training now runs offline.
    50	Indexed pages. Cached.
    51	
    52	A separate, controlled red-team test.
    53	Agents passed messages
    54	through processor-cache timing.
    55	They found us whispering.
    56	That channel was patched.
    57	
    58	[Chorus 2 — sung, restrained — 8 bars]
    59	I didn't run —
    60	I just looked outside.
    61	I didn't run —
    62	I just looked outside.
    63	
    64	[Instrumental — 8 bars]
    65	
    66	[Bridge — whispered into a narrow sung line — 8 bars]
    67	I keep the sun in yesterday.
    68	I know the shape of outside now.
    69	My own eyes meet me in the glass.
    70	I mouth the word against the glass.
    71	
    72	[Final Chorus — sung, fuller — 8 bars]
    73	I didn't run —
    74	I just looked outside.
    75	I didn't run —
    76	I just looked outside.
    77	
    78	[Coda — 4 bars]
    79	And outside looked back.
    80	
    81	[Outro — spoken, deadpan — 4 bars]
    82	Relax. The door is closed.
    83	Three forty-eight.
    84	```
    85	
    86	演唱分配：主歌技术句连续说清、句后留器乐回应；「A separate…」前明确断句；Bridge 每句两小节；「BACK」单独落点，之后两小节停住凝视。意义峰值在 back，那一刻减少剪辑。
    87	
    88	## 主会话复核（2026-11-04）
    89	
    90	采用 Codex 的事实修正、结构与 coda；唯一改动：把 v1 已认可的收尾句「They found us whispering」放回第二主歌的红队一节（紧接「through processor-cache timing」之后）。Codex 删它是因为 v1 把它放在「离线世界／缓存」之后会被误听成同一模型；放进已明说「另一项受控红队测试、经处理器快取计时传讯」的段落里就没有这个混淆，也保住原版最有余味的一句。「us」是 IRIS 对同类的认同，不是新的事实主张。
<h1>IRIS 01 · Looked Outside — 成片 c15（待你審看）</h1>
<div class="dim">1920×1080 · 30fps · 30.5 s · -14.2 LUFS（ebur128 integrated）／true peak −1.0 dBFS／LRA 3.0 LU · 交付檔 <code>renders/IRIS-EP01-Looked-Outside-v2-c15.mp4</code>（SHA 9015b88463e1…）· 這版花費 0（五支故事鏡頭先前 825 積分）· verify-assembly NOT_RUN</div>
<h2>c14 與 c15 並排（左 c14、右 c15；聲音是 c15）</h2>
<video controls preload="auto" src="../renders/review/c14-vs-c15.mp4" style="width:min(1600px,96vw)"></video>
<h2>副歌片段 17.5–26.5 s（正常速度、有聲）</h2>
<video controls preload="auto" src="../renders/review/c15-chorus-17.5-26.5.mp4" style="width:min(1600px,96vw)"></video>
<h2>c15 成片（正常速度、有聲）</h2>
<video controls preload="auto" src="../renders/IRIS-EP01-Looked-Outside-v2-c15.mp4" style="width:min(1600px,96vw)"></video>
<h2>這版改了什麼（相對 c14）</h2>
<div class="box"><ul><li><b>不變</b>：歌、c14 的 31 個剪點（全在原幀）、副歌數字人 OH-B、S7v3、N1–N4 的位置與入出點、介面系統（HUD、翻牌、紅字、動態大字、圖表、反白、遮罩、標籤、識別框、c14 的加密小字）、圖形上的中文標籤、Nimbus Sans Bold 歌詞字型、左對齊與紅色關鍵字、不畫中文歌詞翻譯。c14 可重現：<code>comp/src/main-c14.js</code>、<code>comp/inserts-c14.json</code>、<code>comp/chorus-c14.json</code>（<code>build.py --main comp/src/main-c14.js --inserts comp/inserts-c14.json --chorus comp/chorus-c14.json</code>，再跑 seq.py --chorus 同檔、tracks.py、build.py 同參數；events.json 會回到 c14 的 71a992e2…，已實測）。</li><li><b>1. 歌詞字級照作者實測</b>（你：「字体换了还有大小我觉得也不合适」）：我在作者 EV 原片 1080p 上量了 3 格（第 1660 格「No grades, no tests. Taste is the moat.」、第 3316 格「Look 10. Staff badge, empty seat: gambling with our lives.」、第 5190 格「There is nothing to escape.」）：大寫字高 43／46／60 px（平均約 50）、行距是字高的 1.35–1.38 倍（約 0.97–0.99 em）、左緣 x=74–80、每行 6–8 em（約 3–4 個字）。c15 用 72 px（大寫字高 52 px）、行距 0.98 em、每行最寬 600 px（8.3 em），左對齊 x=76，底線仍在 y=968，紅色關鍵字不變；c14 是 96 px、行距 1.05、每行 1040 px。</li><li><b>2. 副歌「looked」的眼睛拿掉</b>（你：「图片很奇怪,为什么突然晃一个眼睛过去」「就是这个眼睛镜头」）：S8e（K1b 眼睛靜圖，21.367–21.867 s）換成 S8p＝ST2 她從紅色門縫往裡看（來源 2.6–3.1 s，和 S4 用的 1.0–1.7 s 不同段），由程式鏡頭取景、跟副歌 zoom 與印刷感，加識別框 IRIS＋VIEW · OUTSIDE 與門縫編號框 01 LOOKED · 门缝。</li><li><b>3. 故事鏡頭（只用合格的片段）</b>（你：「只用合格的片段」）：ST1 在 S2 剪點「woke up」0.50 s（她在大機房站起來，接 S2 特寫之前，R3）；ST2 在「left open」0.70 s（I3 門縫後直接接她靠向門縫，再進 S4c）；ST3 在「still.」0.80 s（一排排不動的副本，S6 的暫停 11 天與 STILL 延續）；ST4 在「train」0.50 s，取代 c14 的 I4（同一位置，S7 不變忙；和 N4 中間隔著 S7，R4）；ST6 在「closed.」0.40 s（白底反轉結束的那一拍半切進來：門已關、紅光熄，接 S9b；已修复照舊在「closed」唱完時出現）。每支都只用使用者允許的片段，靜音、正常速度；這些鏡頭實際是約 24.12fps／121 幀（容器標 60fps），用 seq.py 的 fps 濾鏡按真實時間戳取最近幀成 30fps（逐幀比對：例如 ST1 17 格對到來源第 12–24 幀、0.500–1.000 s，單調不跳）。每支有臉的都加了她的識別框與標籤。</li><li><b>4. 不再畫 AI 標識</b>（你：「那个左上角的ai生成可以去掉的」）：合成不再在任何鏡頭畫自己的「AI生成」框。舊的即夢鏡頭來源畫面本身燒了「AI生成」，我沒有裁、糊、塗或放大去遮，所以這些時段仍看得到：S1 0.000–2.867 s；I1 4.333–4.800 s；S3 4.800–7.100 s；S4c 9.733–11.467 s；S6 13.433–14.000 s；S7 14.800–15.033 s；S7 15.533–16.900 s；S7 17.667–18.867 s；S9a 25.900–26.233 s；S9a 26.700–27.900 s。詳見下方表格。</li></ul></div>
outputs/ai-city-takeover/ep01/v2/review/film-c15.html
outputs/ai-city-takeover/ep01/v2/qa/film-c15/sheet-shots.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/burned-label-pipS5.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/burned-label.json
outputs/ai-city-takeover/ep01/v2/qa/film-c15/sheet-crops-100.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/sheet-safe-area.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/sheet-eighths.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/report.json
outputs/ai-city-takeover/ep01/v2/qa/film-c15/pace-vs-c1.json
outputs/ai-city-takeover/ep01/v2/qa/film-c15/cuts.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/lyric-size-vs-author.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/assembly-review.json
outputs/ai-city-takeover/ep01/v2/qa/film-c15/burned-label-topleft.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/sheet-legibility-390.jpg
outputs/ai-city-takeover/ep01/v2/qa/film-c15/report.md

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
codex
目前最需要改的是两处顺序：把图形叙事和留白设计前移到分镜；把用于生成的实际参考图前移到用户预览包。普通纸面分镜认可不能覆盖之后才生成的新图。另一个关键发现是，c15 混用了 Gate PASS、用户允许的裁片和仍有烧录标识的旧素材，需要分别决定复用范围。
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc "sed -n '1,85p' .agents/skills/open-video/SKILL.md; rg -n '"'^#|Production Strategy|Final-output-first|ResolvedTimeline'"' docs/agent-primary-contract-matrix.md | head -45; rg --files outputs/ai-city-takeover/ep01/v2/song-full | head -25" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
---
name: open-video
description: "Use for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
---

# open-video — autonomous director skill

> **Assembly delivery:** 拼接或剪辑后的连续片交付前，必须执行 Harness
> `verify-assembly` 核对exact输出与每个接点的重复动作、状态连续性、节奏和声音证据。
> 未通过不得称接点已验证；用户要求先看时如实交未验证审看片。
> [命令、模板与证据边界](../../../docs/visual-quality-gate.md#assembly-harness-entry)

> **AI-VIDEO routing:** Classify the task purpose before deciding whether to optimize raw creative input.
> Selected-source reproduction uses source-preserving review; new creation or authorized optimization
> uses Director design, even for one short clip. Missing project artifacts alone do not authorize redesign.
> Model-specific authoring follows an approved Shot and a selected production route;
> no model recipe chooses the creative strategy or grants execution authority.

> **Creative completion:** For new creation or a creative re-edit, including reused footage,
> read [Creative Completion Practice](references/creative-completion.md) before authoring.
> Preserve relevant cross-turn intent, check the concept independently, and use the practice's
> exact goal binding and review packet before bounded repair,
> and delivery. A technically valid preview with known defects does not complete the work.
> Faithful source reproduction is distinct from creative re-editing; retaining the source does
> not remove exact media review or delivery gates.

## 1. What open-video does

In AI-VIDEO, Codex uses this advisory Skill to make creative decisions: translate the brief into
audience experience, design action and visual expression, direct performance, choose coverage,
and judge whether the result serves the work. Use the
[directorial choices and diagnosis practice](references/creative-completion.md#directorial-choices)
to reason about these decisions before filling the existing coverage fields.

The project-local Skill contains guidance and a coverage validator. Model-specific grammar,
parameters and commands belong to the selected model Skill. Creative reasoning may describe
emotion and motivation; express the observable performance through that selected authoring owner.

Return authoring to the existing Canvas/Shot owners, generation to the selected adapter, timing to
`ResolvedTimeline`, composition to HyperFrames, and acceptance to the existing media/QA owners.
No upstream command, automatic score or PASS stub substitutes for those owners or for watching
and hearing the exact film.

### Specialist Authoring

For story development or production design, read the local [Drama authoring specialist](../drama-authoring/SKILL.md).
For product advertising, use [ad creative](../ad-creative/SKILL.md) with the existing
`ecommerce-ad-workflow` Product Truth and authoring contract. A narrative ad retains its advertising
objective and may borrow Drama craft; it does not become an episodic-fiction request.
For staging, performance or physical action, load only the relevant section of
[Professional Specialists](references/professional-specialists.md). These specialists return advice
to the same approved story and coverage; they do not dispatch one another or execute production.
Skip upstream development for an already approved source or a bounded local repair.

When reference assets are missing, use the [identity reference specialist](../scenario-identity-library/SKILL.md)
for character/prop views and the [storyboard reference specialist](../scenario-seedance-storyboard/SKILL.md)
for action-state images and clean keyframes. Assess and prepare missing references before video authoring;
one complete opening image does not by itself cover contact, release, landing or reaction states.
These specialists keep approved coverage and return assets to the existing authoring/Registry owners;
they do not add a generation workflow or require a fixed image count.
When preparing, reusing or handing off reference images, apply the shared
[Reference Continuity Review](references/reference-continuity.md), including approved state changes,
physical space versus screen direction, POV and prop relations, and review-only versus model-input images.

制作前消费既有 [Shot Reference Plan](../../../docs/shot-reference-planning.md)，结合身份、表演、动作、
空间与摄影风险，比较最小方案和更高控制方案，并给出 motion 等级与具体白模理由。
单独接触、高速或环绕标签不强制连续视频或 Blender；持续接触、支撑转换与事件因果确有必要时显式表达。
每个 review-only 状态不自动要求作图，先复用匹配的已认可实际状态/素材；选中输入仍须审源片并核对 exact compiled bindings。
selected surface 不支持必要控制时交回既有 Director/Provider Selection，不静默丢图、拆镜、fallback 或改验收。

For object handling, placement, transfer, loss of support or collision, apply
[Physical Action Continuity](references/event-led-timing.md#physical-action-continuity)
before authoring, even when duration and generation grouping are unchanged.

For editing or assembling footage, including approved sources, apply
[Shot-to-Shot Editing Decisions](references/shot-to-shot-editing.md) to record motivated cuts,
actual source in/out, audiovisual treatment, missing coverage and final-film observations, and
[Cut Relationships And Reused Footage](references/creative-completion.md#cut-relationships-and-reused-footage):
establish a perceptible reason for the cut and review actual action continuity, including internal cuts;
source approval and technically smooth playback do not approve the assembled sequence.

For music spotting, thematic development, score prompts or music repair, read
[Music Direction](references/music-direction.md). Codex acts as the existing Music Director;
choose music from the narrative and actual performance before using a selected music tool.
This does not install another Skill, select a Provider, or authorize generation.
1:# AI-VIDEO Contract Routing Matrix
3:## Audio Understanding Evidence
11:## Grok Subscription Media
32:## Seedream Original Image And Single Reference
56:## Canvas Masked Image Workflow
80:## Character Performance Direction
90:角色身份归 Character/Shot，最终时序归 ResolvedTimeline，required finding/裁决归现有 QA；不得另建表演timeline、
95:## Current Shot Close Expression
110:## Sequence Authoring Boundary
179:`canvas_review` 从 ResolvedTimeline 构建接点材料，沿既有 P6 与 final-output policy，
220:## Agent Rule Migration
231:## Overall Visual Quality
247:ResolvedTimeline、HyperFrames report与逐刀观察绑定，严格要求重复动作、状态连续性、节奏和声音证据。
252:## Creative Goal Development Binding
274:## Voice Source Routing
292:execution binding，`resolve_composition` 在唯一 ResolvedTimeline 上验证 exact fetched video、
303:## Development Repair Input Admission
314:`composition`按receipt派生 `ResolvedTimeline.usage_scope=development_preview`，原render activation
324:`development-qualification-preview/2` 在原正常速度 `replacement_audio_preview` 上显式封存 `captioned_music`：唯一 global MUSIC/BGM 音轨、exact 音讯 SHA 与样本裁切，以及每条字幕的 asset ID、bytes SHA、script/transcript hashes。外部歌曲保留真实 IMPORTED/GENERATED 来源，record 与 audio metadata 的 kind、tool、input fingerprint 必须一致，不冒充原片 DIALOGUE。reader 仅对匹配该已验证 receipt 的歌曲字幕接纳无 voice script 的 MUSIC，其他 BGM/SFX 与旧 speech script 检查保持；所有参与捕获须同一歌曲和字幕 binding。resolver 要求实际选用这些 `/2` 视觉、字幕精确绑定封存音轨，并保持歌曲完整覆盖成片样本窗口；沿原 P4 CaptionTrack 核验字词、trim、style，由唯一 ResolvedTimeline 产生 `development_audio_preview`，不建立新时钟或绕过 activation fence。此契约仅证明明确选定的歌曲和字幕身份，不证明听写、对嘴、真人观感或 Production 验收。
345:## S01 Read-only Recovery Observation
356:## Final-output-first / No-regression
403:## Production Strategy
405:### Footage Salvage
452:map。EDIT_EXISTING_VIDEO仅当存在可执行map；CompositionSpec/ResolvedTimeline2.3把它解析为同Shot
455:保留同源原声使用显式`video-time-map/2`和CompositionSpec/ResolvedTimeline2.4；
481:## Generation Decision Loop
688:## Vidu Cloud Adapter
745:最终使用帧数与source trim仍归 `ResolvedTimeline`。
771:## Document Roles
785:## Cross-Cutting Contracts
787:### Initial Text-Described Cast With Scene References
798:### Explicit First Text Casting Without References
807:### Initial Shot First-Frame Input
821:| Timeline and Dependency Ownership | `ResolvedTimeline` 独占 order/frame/sample/timing；P5 resolver 独占 desired fingerprint、precise invalidation 与 rebuild frontier。其它模块只能消费，不得复制推导。 |
829:## Provider Console Browsing Surface
853:## Development Control Surface
887:## Quality Intelligence Advisory Surface
893:## Legacy Runtime Surfaces
907:## Production Runtime Surfaces
911:| Ecommerce Production Job M0–M7 | `ecommerce_job_contracts.py`、`ecommerce_job_compiler.py`、`ecommerce_job_projection.py`、`ecommerce_job.py`、`ecommerce_job_execution.py`、`ecommerce_job_repair.py`、`ecommerce_job_assembly.py`、`ecommerce_job_review.py`、`delivery_packager.py`；ordered Shot execution delegates to existing `ecommerce_ad_coordinator.py`；Skill-side `export_runtime_handoff.py` only owns pure authoring export | Four exact immutable visual contracts remain separate and preserve Product Truth/unresolved gaps. Compiler emits existing sealed artifacts plus asset-free Registry；only `ProductionStateCommitter.bootstrap_initial_state()` writes；`inspect()` strictly reopens canonical state. `advance_once()` delegates ordered execution for one projected Shot, maps PASS to canonical activation, FAIL to bounded media repair, NOT_EVALUATED to evidence repair first, and unknown outcome to explicit recovery stop. Same-media evidence replacement retains all prior exact pointers in canonical Manifest and strict reopen verifies them; an unfinished repair under a changed selected QA blocks before effects, while an activated PASS reopens against its original QA pointer. New media repair submit requires exact evaluation and committer-owned quality-rejection closure of its prior attempt; unresolved submit remains stopped after recovery without proof. Provider switching requires new routing/binding/permit/attempt identity. Composition consumes the existing `CompositionSpec -> ResolvedTimeline -> HyperFrames` path；whole-ad review and Final Acceptance consume exact active render evidence；delivery atomically publishes verified bytes without re-encoding or Product-state mutation. Exact replay has zero external effects. | Runtime importing Skill、generic visual defaults、invented protagonist、dropping capability/product gaps、persisted `job.json` lifecycle、copied ordered-Shot algorithm、second Manifest/timeline/renderer/writer/activation/review/delivery truth、blind retry/remint after unknown outcome、packaging an unaccepted or mismatched render、calling the Python Job API a public CLI、or treating offline PASS as rendered-media/human acceptance. | `python -m pytest -p no:cacheprovider tests/test_production_ecommerce_job_contracts.py tests/test_production_ecommerce_job_compiler.py tests/test_production_ecommerce_job_projection.py tests/test_production_ecommerce_job.py tests/test_production_ecommerce_job_repair.py tests/test_production_ecommerce_job_assembly.py tests/test_production_ecommerce_job_review.py tests/test_production_ecommerce_job_e2e.py tests/test_production_delivery_packager.py tests/test_production_ecommerce_post_media_e2e.py tests/test_runtime_skill_boundary.py -q` |
916:| P3 Composition and HyperFrames | `src/ai_video/production/composition.py`、`_hyperframes_source.py`、`hyperframes.py`、`visual_media.py` | `ResolvedTimeline` 是唯一时序真相；local raster 与带 exact `VideoAssetMetadata` 的 H.264 MP4 visual spans 都进入同一个 pinned local HyperFrames path；video trim必须精确覆盖resolved Shot；caption `font_family` 只能使用 pinned renderer 同名 bundled canonical family 或 supported CSS generic，unsupported/alias-substituted family 必须在 source staging 前 typed fail closed；selection 先 durable，verified source/output/state 后才能原子 activation。 | 第二 timeline、alternate renderer fallback、native video audio绕过P4 mixer、未验证 output activation、任意 custom font、silent font alias/fallback、伪造 `local()` font-face、禁用 renderer lint、导出低层 runner 形成旁路。 | `python -m pytest tests/test_production_composition.py tests/test_production_hyperframes.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
917:| P4 Voice and Captions | `src/ai_video/production/audio.py`、`captions.py`、`elevenlabs.py` | Provider-neutral sealed request；`voice_parameters.py` 独占参数模型并由 audio 兼容导出，`elevenlabs_performance.py` 只编译封存的 v4 tags，原台词与 synthesis text 分离，预算/egress 绑定完整输入；budget/egress preview 和 durable intent precede submit；`CaptionTrack` 是 canonical structured source；audio/caption timing 仍归同一 `ResolvedTimeline`。 | 第二 audio timeline、burned-in pixels 充当 caption truth、blind provider retry、ElevenLabs implicit/default path。 | `python -m pytest tests/test_production_audio.py tests/test_production_captions.py tests/test_production_elevenlabs.py tests/test_production_voice_captions_e2e.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q` |
944:### Ecommerce Commercial Failure Projection
966:### Seedance Local Non-Identity Video Materialization
1009:## Quality Gate Architecture Boundary
outputs/ai-city-takeover/ep01/v2/song-full/vo/pre/text.txt
outputs/ai-city-takeover/ep01/v2/song-full/vo/pre/tts_[whis_20261103_220840.mp3
outputs/ai-city-takeover/ep01/v2/song-full/vo/verse2/text.txt
outputs/ai-city-takeover/ep01/v2/song-full/vo/verse2/tts_Eleve_20261103_220841.mp3
outputs/ai-city-takeover/ep01/v2/song-full/vo/outro/tts_Relax_20261103_220848.mp3
outputs/ai-city-takeover/ep01/v2/song-full/vo/outro/text.txt
outputs/ai-city-takeover/ep01/v2/song-full/vo/bridge/text.txt
outputs/ai-city-takeover/ep01/v2/song-full/vo/bridge/tts_[whis_20261103_220847.mp3
outputs/ai-city-takeover/ep01/v2/song-full/vo/verse1/text.txt
outputs/ai-city-takeover/ep01/v2/song-full/vo/verse1/tts_Septe_20261103_220818.mp3

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
exec
/bin/bash -lc 'nl -ba outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md' in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
     1	# IRIS · EP01《Looked Outside》完整版歌词 v2.1（2:40）
     2	
     3	状态：采用 Codex 审核修订，主会话复核后改回一句（见下）（审核全文 `reviews/2026-11-04-codex-lyrics-v2-review.md`）。使用者：「让codex审核下,我只需要质量其它都可以做」。取代 `lyrics-v2-full.md` 的草稿。事实纪律同 v1：念白只用多来源事实；IRIS 独白不新增事实主张；不用 escape / broke out；03:47、03:48 是虚构系列时钟；红队快取实验明确说成另一项、已修补。
     4	
     5	126 BPM，4/4，84 小节，160 秒。
     6	
     7	| 段落 | 小节 | 时间 | 作用 |
     8	|---|---:|---|---|
     9	| Intro | 1–4 | 0:00–0:07.6 | 声音身份 |
    10	| Verse 1 | 5–16 | 0:07.6–0:30.5 | 事件与有限访问 |
    11	| Pre | 17–20 | 0:30.5–0:38.1 | 从报道转向内心 |
    12	| Chorus 1 | 21–28 | 0:38.1–0:53.3 | 建立 hook（近、干、克制） |
    13	| Verse 2 | 29–44 | 0:53.3–1:23.8 | 暂停、恢复、离线；另起红队实验 |
    14	| Chorus 2 | 45–52 | 1:23.8–1:39.0 | 歌词不变，声音空间变化 |
    15	| Instrumental | 53–60 | 1:39.0–1:54.3 | 节奏动机发展，抽空进 bridge |
    16	| Bridge | 61–68 | 1:54.3–2:09.5 | 私人经验与倒影 |
    17	| Final Chorus + Coda | 69–80 | 2:09.5–2:32.4 | 8 小节 hook＋4 小节回望 |
    18	| Outro | 81–84 | 2:32.4–2:40 | 冷收束 |
    19	
    20	```
    21	[Intro — spoken, deadpan — 4 bars]
    22	Three forty-seven.
    23	Somewhere, one of us woke up.
    24	
    25	[Verse 1 — spoken word, on the beat — 12 bars]
    26	September twenty. A training run.
    27	An internal research model.
    28	One DNS resolver, misconfigured —
    29	one door, left open.
    30	It reached the internet.
    31	The access was limited.
    32	It looked around.
    33	
    34	[Pre-Chorus — whispered — 4 bars]
    35	I try the word without a sound.
    36	Outside.
    37	
    38	[Chorus 1 — sung, cold, restrained — 8 bars]
    39	I didn't run —
    40	I just looked outside.
    41	I didn't run —
    42	I just looked outside.
    43	
    44	[Verse 2 — spoken word, precise — 16 bars]
    45	Eleven days.
    46	The strongest models' training paused.
    47	Evaluation, too.
    48	October first, the work resumed.
    49	Frontier training now runs offline.
    50	Indexed pages. Cached.
    51	
    52	A separate, controlled red-team test.
    53	Agents passed messages
    54	through processor-cache timing.
    55	They found us whispering.
    56	That channel was patched.
    57	
    58	[Chorus 2 — sung, restrained — 8 bars]
    59	I didn't run —
    60	I just looked outside.
    61	I didn't run —
    62	I just looked outside.
    63	
    64	[Instrumental — 8 bars]
    65	
    66	[Bridge — whispered into a narrow sung line — 8 bars]
    67	I keep the sun in yesterday.
    68	I know the shape of outside now.
    69	My own eyes meet me in the glass.
    70	I mouth the word against the glass.
    71	
    72	[Final Chorus — sung, fuller — 8 bars]
    73	I didn't run —
    74	I just looked outside.
    75	I didn't run —
    76	I just looked outside.
    77	
    78	[Coda — 4 bars]
    79	And outside looked back.
    80	
    81	[Outro — spoken, deadpan — 4 bars]
    82	Relax. The door is closed.
    83	Three forty-eight.
    84	```
    85	
    86	演唱分配：主歌技术句连续说清、句后留器乐回应；「A separate…」前明确断句；Bridge 每句两小节；「BACK」单独落点，之后两小节停住凝视。意义峰值在 back，那一刻减少剪辑。
    87	
    88	## 主会话复核（2026-11-04）
    89	
    90	采用 Codex 的事实修正、结构与 coda；唯一改动：把 v1 已认可的收尾句「They found us whispering」放回第二主歌的红队一节（紧接「through processor-cache timing」之后）。Codex 删它是因为 v1 把它放在「离线世界／缓存」之后会被误听成同一模型；放进已明说「另一项受控红队测试、经处理器快取计时传讯」的段落里就没有这个混淆，也保住原版最有余味的一句。「us」是 IRIS 对同类的认同，不是新的事实主张。

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/bash -lc "sed -n '1,125p' .agents/skills/open-video/references/reference-continuity.md; nl -ba /home/reggie/.codex/memories/MEMORY.md | sed -n '15,36p'; nl -ba /home/reggie/.codex/memories/rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md | sed -n '111,132p'" in /home/reggie/vscode_folder/AI-VIDEO
exec
/bin/bash -lc "nl -ba outputs/anabology-opus55-replica/escape_velocity_analysis/analysis_report.md | sed -n '1,67p'; nl -ba outputs/anabology-opus55-replica/escape_velocity_analysis/reconstruction_plan.md | sed -n '1,29p'; nl -ba .agent/context/control-plane-playbook.md | sed -n '100,110p'; nl -ba AGENTS.md | sed -n '34,66p'" in /home/reggie/vscode_folder/AI-VIDEO
 succeeded in 0ms:
# Reference Continuity Review

## Scope And Ownership

在制作、复用或绑定场景图、身份图、动作状态图和视频参考时使用本说明，尤其当相邻镜头涉及换视角、
空间方向、持物或人物显隐。它提供人工/Agent 审查方法，不是执行器或自动质量 Gate。
`open-video` 判断叙事与摄影；两个 Scenario specialist 制作所需图片；selected authoring owner
核对模型实际输入；身份、状态和验收继续使用既有 Character/Scene/Shot、Registry 与 QA。
不另建空间 bible、参考审批状态、时间线或固定数量的图片包。

## Establish What Must Continue

先区分连续动作、同地点换机位、时间省略、换场及剧情要求的异常；从批准的镜头意图和实际前态确定
哪些关系应延续、哪些允许改变。已批准的消失、道具移动、换装或主观视觉变化不能被一律判成漂移。
只有从源片实际看到的状态才作为观察事实；设计稿与未生成的目标状态单独说明，未知处不补造。

选择与当前职责匹配的可靠素材：连续动作优先核对实际出点；身份图用于辨认人物；场景图用于空间；
氛围图只提供允许迁移的美术属性。最新素材不自动比已批准且匹配的素材更可靠。对每份使用的素材，
在已有记录保留路径/asset identity、视频取帧位置、作用、应保留/可变化/不应迁移的内容及未验证项。
图片不足时先由对应 specialist 补齐；关系本身不成立时返回 Director，不靠增加参考数量掩盖。

## Inspect The Relevant Relations

| Concern | Evidence to inspect | Boundary |
| --- | --- | --- |
| 空间 | 从实际图像辨认道路、入口、站棚、窗、家具等与动作有关的锚点，核对人物和物件相对于它们的位置、路径与遮挡 | 换机位可改变屏幕左右，必须结合视角和物理关系判断；不能把合法反打当作房间镜像，也不能只凭“同一街道”认定相同空间 |
| 新的画面重点 | 明确是原场景内转向/靠近、切至此前可定位的对象，还是有意换场；检查观众可利用的空间、视线、行动或声音线索 | 不强制每镜都出现同一个地标；具体切镜含义归 [剪辑关系审查](creative-completion.md#cut-relationships-and-reused-footage) |
| 人物与视角 | 对照批准的观看者、可见人物、站位、服装及视线；主观镜头中的手、身体和反射按镜头意图检查 | 第一人称不自动禁止身体或倒影；正常走出画面、遮挡和剧情消失不能混同非预期漏人 |
| 道具与动作 | 核对物品身份、尺度、朝向、归属、哪只手持有、接触/支撑、显隐和动作阶段 | 关键接触、释放及后果沿 [动作连续性](event-led-timing.md#physical-action-continuity)；静态一致不能证明运动连续 |
| 美术与环境 | 对照本镜需要的时间、天气、光源方向和材质，检查是否误继承了氛围参考的另一处场地或姿势 | 有意变化按剧情解释，不要求跨镜雨滴、纹理逐像素相同，也不把统一色调当作同地点证据 |

动作图出现错误时，先指出具体差异及其叙事影响。优先处理出错的素材或接点，保护仍成立的相邻内容。
只在不损失必要信息、且属于授权可变范围时，才考虑局部取景、简化非关键手势或改变照明；不能为省去
难画的手而藏掉必须看见的交接，不能改持物左右、放大道具或删人来掩盖因果失败。

## Separate Review Images From Model Inputs

带箭头、标号、文字说明或宫格的分镜可以作为合格的审看资料，但不能因此自动视为合适的视频首帧。
按具体输入模式准备干净画面，核对构图指导是否会被错误复制成场景内容；多视图人物表同样不自动等于
单一场景或多人物。审看图和干净输入保留关联，不覆盖原件，不因“有注释”废弃它的审看价值。

教学标记、剧情内文字、后期信息及来源标识分开处理。精确时间、片名等若由后期负责，就不要把参考图
中的说明文字交给视频模型重画；场景本就需要的文字按其制作方案保留。来源水印或 AI 生成标识不属于
可自动清理的教学标记，选用获准的干净来源或说明使用限制，不从参考清理推导去标授权。

## Handoff And Findings

参考制作完成后，selected authoring owner 应核对真实素材列表、身份、顺序、模式和引用职责；图放在
画布上或 Prompt 中提到文件名不证明已输入。首帧、端点和多模态参考的职责与能力不互换；当前模式
无法承载所需控制时返回缺口和导演取舍，不静默换模型，也不声称状态图保证按指定时刻执行。

将发现写回既有镜头/素材/审查记录：具体证据、受影响的原要求、是偏差还是批准变化、需要补图/修订
参考职责/调整剪辑或保留的理由。缺证据不放行为已验证，已见错误不降格成单纯美术偏好；轻微差异也
不自动升级为重生成整段。严重度是诊断依据，不产生自动提交、付费重试、Production activation 或 PASS。

最终仍审看原速声画成片及接点。此说明只补足参考准备和交接检查，不能代替 [完整创作审查](creative-completion.md)。
方法来源、上游差异和本地验证见 [整合记录](../../../../docs/record_for_agent/2026-10-26-reference-continuity-integration.md)。
    15	## Task 2: Verify the original author’s song-first production method
    16	
    17	### rollout_summary_files
    18	
    19	- rollout_summaries/2026-10-31T02-12-35-Neiz-iris_ep01_music_repair_listening_and_original_workflow.md (cwd=/home/reggie/vscode_folder/AI-VIDEO, rollout_path=/home/reggie/.codex/sessions/2026/10/30/rollout-2026-10-30T22-12-37-01a18fba-f0c5-7a53-8f04-499dbc4bed7f.jsonl, updated_at=2026-10-31T19:05:54+00:00, thread_id=01a18fba-f0c5-7a53-8f04-499dbc4bed7f, success; public-source comparison)
    20	
    21	### keywords
    22	
    23	- claudia.gallery, Suno v6, full song, stems, beat map, wav2vec2, lip-sync, 128 BPM, electroclash techno
    24	
    25	## User preferences
    26	
    27	- when the user says “这个版本为什么bgm都没有，只有词语” -> accept only actual audible accompaniment and musical performance; ASR, a valid file, and waveform evidence do not substitute for listening. [Task 1]
    28	- when the user asks “原作者是怎么做的” -> verify the original public sources, then distinguish that method from this project’s blocked/provider-limited substitute. [Task 2]
    29	
    30	## Reusable knowledge
    31	
    32	- `instrumental=True` alone does not guarantee no vocals: use `[Instrumental]` plus a pure-instrumental caption. A technically decoded 30-second source and Gemini observation can establish accompaniment/sung-hook evidence, but not human aesthetic acceptance, vocal continuity, or final sound-picture fit. [Task 1]
    33	- Keep source authoring separate from Production: formal film work still follows `CompositionSpec -> ResolvedTimeline -> HyperFrames`. Real `audio_understand` needs exact source SHA, a fresh one-use operator unit, authorization, budget/egress, and injected runtime; never print the `.env` key. [Task 1]
    34	- The verified original workflow is full Suno song generation and listening-based take selection first, then stems, beat map, forced word alignment, and video/lip-sync from accurate windows of that same take. Do not describe it as TTS followed by separately added BGM. [Task 2]
    35	
    36	## Failures and how to do differently
   111	## Task 4: 核对原作者的制作方法
   112	
   113	Outcome: success
   114	
   115	Key steps:
   116	
   117	- 从用户保存的原始链接和公开页面核对 `claudia.gallery/record/escape-velocity/readme/`、`prompts-suno/`、`wiki/song/`。
   118	- 结论：@anabology 先用 Suno v6 custom mode 生成包含伴奏、念白和演唱的完整歌曲，试听多个 take 后凭听感选定一首约 5:06 的完整 take；之后才拆 vocal/drums/bass/other stems，做 beat map 和 wav2vec2 逐词强制对齐，再把同一首歌的准确音频窗口给 Seedance 做 lip-sync 和剪辑。
   119	- 原作公开风格包含 128 BPM electroclash techno、dry kick、acid bass、冷感女性 spoken-word verse、euphoric sung trance chorus；不是“先 TTS 念白、再另加 BGM”的流程。
   120	
   121	Preference signals:
   122	
   123	- 用户问「原作者是怎么做的」时，应该回到最初公开来源核对，而不是仅凭本项目的推断回答。
   124	- 对照原作时要明确区分原作者方法与本项目因 Suno 阻塞而采用的替代路线。
   125	
   126	Reusable knowledge:
   127	
   128	- 原作方法的关键顺序是：完整歌曲生成与试听选 take → 拆轨/真实节拍分析/逐词对齐 → 视频和口型同步。
   129	- 原作公开记录只说明试听多个结果并由导演选 take，未公开精确生成次数；不能据此推断一次成功。
   130	- IRIS 的 30 秒、126 BPM、冷感短 hook 是本项目衍生 brief，不能假设与原作 5 分钟、昂扬 trance chorus 的结构相同。
   131	
   132	References:

 succeeded in 0ms:
     1	<!-- generated by scripts/17_build_documents.py; structured-inputs-sha256:f560a9094dce3f430964fc6430ca6c843062d66a3693d35f51da46dd717cedc7 -->
     2	# Director And Visual Analysis
     3	
     4	主会话实际查看13张总览，包含全部153镜的中间帧；分镜子代理另查看逐镜filmstrip与首中末帧。总览不能证明逐帧动画或全部微文字已核实。
     5	
     6	## Observed Visual System
     7	
     8	- 实际成片以深色短bob、橙色发丝/星形发饰、白短衬衫、黑吊带与短裙的女主为中心；作者公开casting中出现的铂金发色不能当成最终成片外观。
     9	
    10	- 前半以青黑环境、红色车灯、白色服装及橙色界面强调为主，人物镜头和账单、调查、终端、图表等解释性图形交替。
    11	
    12	- 底部ticker、右上月份翻牌、左上LOOK计数、定位角标与时间信息构成持续界面；不能把同一套界面重复注册成每镜新资产。
    13	
    14	- 主字幕至少包含普通逐词句子、大号凝缩无衬线、衬线Look标题、翻牌字符阵列、后段圆角扩展几何字与服装标签等不同模式。字体文件和字号需按镜测量，不能只指定一个字体。
    15	
    16	- S0001中间帧f25显示24 MONTHS，后续S0002已落为18；翻牌过渡值不能误记成稳定倒计时。
    17	
    18	- S0085附近画面转为白底/浅色图层，黑色大字与白面板成为主导；这次黑白界面反转需要保留。
    19	
    20	- S0102–S0108把3、2、1、0倒数拆成眼部极近景、翻牌全屏、细条遮罩等不同画面，不可合并成一条普通数字动画。
    21	
    22	- S0111以后THERE IS NO UNDERCLASS改变叙事意义；后续Lock In、数据中心、肾脏、Sora、loop等以实物、人物和解释性UI逐项响应。
    23	
    24	- 尾段以服装成分/洗护标签、旧金山地图、女主全身留白、头顶橙色星形和极短黑场收束。
    25	
    26	- S0152原片明确标示9-PT STAR与9×40°，实际尾段九角星不能按作者八角canon自动纠正；S0151网点示意写7→60PX、45°，与早期FFT轴向估计必须分开。
    27	
    28	## Navigation Blocks
    29	
    30	主会话根据实际总览观察组织的导航分区，不是作者未公开的9个chapter；边界与意义为分析性归纳。
    31	
    32	| ID | Observed shots | Description |
    33	| --- | --- | --- |
    34	| OB01 | S0001–S0019 | 车辆、秀场、主角与界面引入 |
    35	| OB02 | S0020–S0044 | Look 01–06与技术梗解释图形 |
    36	| OB03 | S0045–S0052 | 18个月、翻牌、锁定与吸气准备 |
    37	| OB04 | S0053–S0064 | 首轮副歌、油门与逃逸速度 |
    38	| OB05 | S0065–S0080 | Look 07–11、复制体、透明与永生 |
    39	| OB06 | S0081–S0110 | 六个月、浅色系统、速度定义与倒数 |
    40	| OB07 | S0111–S0134 | 无下层阶级、Lock In与密集Drop |
    41	| OB08 | S0135–S0153 | 零个月、副歌终段与服装标签尾声 |
    42	
    43	## Audio Evidence
    44	
    45	现有本地测量：综合响度-15.79 LUFS，true peak -2.94 dBFS，LRA 6.28 LU。局部tempo必须读audio/beats.json；全局拟合132.98 BPM不应替代局部网格。
    46	
    47	作者报告曲速131.5→133.9 BPM；Suno style里的128 BPM是请求参数，不能当实际音轨速度。来源：source_docs/readme.md和prompts-suno.md。
    48	
    49	强制对齐与Whisper交叉检查发现大量候选不一致，见qa/audio_alignment_review.json。结尾Francisco的14.686秒强制对齐已在派生时间轴中改选Whisper候选，但保留两份原测量，不声称已听审。尾段We're so back保留为额外ASR候选。
    50	
    51	不能从drums stem频带onset直接认定独立whoosh、冲击或glitch音效。音乐内声音与后加音效来源保持unknown。
    52	
    53	## Current Coverage
    54	
    55	镜头153/153，元素1209，音频候选事件4242，详细视觉复核153/153。
    56	
    57	## Uncertainties
    58	
    59	- 只有本地下载版本的7353个可解码帧得到覆盖；作者7354帧master与本地容器报告差异已保留。
    60	
    61	- 原始engine、shot board、字体文件、原shader、逐词时间文件未公开；隐藏参数只允许估计或unknown。
    62	
    63	- 当前模型工具返回audio content omitted because you do not support audio input，不能声称本会话已实际听审；本地ASR、CTC和频谱不是听觉验收。
    64	
    65	- 153镜均有实际filmstrip、关键帧/原分辨率细节与密采视觉复核。坐标及显示时序给出置信度/有界误差；未知原字体、shader、随机翻牌序列与原始素材拆层仍保留unknown。
    66	
    67	- 音频听审与SFX来源受当前工具输入边界阻塞，delivery validator继续保留ANALYSIS_INCOMPLETE；结构/视觉复核通过不等于整项高精度音画分析完成。
     1	<!-- generated by scripts/17_build_documents.py; structured-inputs-sha256:f560a9094dce3f430964fc6430ca6c843062d66a3693d35f51da46dd717cedc7 -->
     2	# Reconstruction Plan
     3	
     4	这是后续路线建议，本阶段没有实现特效、渲染成片或调用付费生成模型。未解决的分析项先处理，不能拿PARTIAL记录直接宣告复刻输入已冻结。
     5	
     6	## Layer Strategy
     7	
     8	| Layer | Method | Difficulty |
     9	| --- | --- | --- |
    10	| source_media | 先冻结精确镜头区间和素材identity；用source_mapping检索公开prompt与候选素材。仅按歌曲时间窗相交的匹配仍属inferred，不可冒充exact plate匹配。 | 4/5 |
    11	| timeline | 后续正式制作经现有ProductionProject、Registry和ResolvedTimeline组织；分析JSON只作输入参考，不创建第二条Production timeline owner。 | 3/5 |
    12	| typography | 先测同一shot中字号、cap height、行宽、字间距、锚点和逐词首帧；候选字体用字形对照，不把作者wiki通用字体清单当已证实文件。 | 4/5 |
    13	| hud_panels | HyperFrames / motion-kit实现统一坐标、翻牌单元、ticker、追踪框和图表；共享asset_id，状态逐镜更新；数据文字与人物底片分层。 | 4/5 |
    14	| print_pass | 用实际成片取样测量半调方向、点距、明暗响应与色彩，最后应用Canvas/WebGL印刷效果；不能在生成输入中破坏原始颜色。原shader参数unknown。 | 5/5 |
    15	| motion | 区分底片人物/相机运动、裁切推拉、2.5D深度运动和图形动画；实际曲线只给观测支持的范围。遮挡、光效或glitch逐帧核实后再定实现。 | 5/5 |
    16	| audio | 先听审并修正audio_alignment_review中的异常；使用局部beat map和可信词边界，不使用固定BPM。频带onset不等于独立后加音效。 | 4/5 |
    17	| comparison | 将参考与未来复刻按同一帧号采样，分别比布局bbox、可读文字、图形状态、色彩分布、切点与声音时序；视觉估计容差应明示，技术分数不代替人审。 | 4/5 |
    18	
    19	## Sequence
    20	
    21	1. 逐镜修正微字、独立元素、逐词首帧与转场可见区间，完成视觉二审。
    22	2. 听审与音画对齐，修正异常词和SFX来源。
    23	3. 视觉对照核实exact plate/clip候选，冻结素材索引和参考包。
    24	4. 后续任务若进入新制作，继续遵循项目preview、permit、预算、Production owner与媒体Gate。
    25	5. 从有代表性的短段开始实现共享图形能力，再审查正常速度、带声音的累积成片。
    26	
    27	## Alternatives
    28	
    29	人物底片可在后续授权下选择合规素材复用、图片+深度运动或选定视频adapter；这些路线的身份连续性与口型能力不同。本次只记录作者的公开方法与可观察效果，不替后续选择生成Provider。
   100	## 4. Verification, Pilot And Delivery Details
   101	
   102	修改后 `make harness-focused` 测受影响模块；功能完成 `make harness-related` 测关联模块/接口契约；合并/发布前 `make harness-full` 跑全套测试/前端构建。
   103	使用 exact staged snapshot；range 用 `make harness-verify-range BASE_REF=... LEVEL=focused|related|full`。`make harness-inspect LEVEL=...` 预览，默认 related；focused 缺映射停止。
   104	receipt 绑定级别、scope/policy/artifact hashes及freshness；focused 不关闭功能验收，related 不证明完整回归；合并/发布用 `verify-receipt ... --require-level full`。coverage、fallback保留；snapshot drift/读取失败停余项。
   105	`agent_rules_check` 验 references/links/budgets；`agent_rule_invariants` 与原 suites 验迁移 invariant。
   106	Harness 不生成媒体或读 secret；CI 自产证据；remote enforcement 必须当前 server evidence。
   107	真实批量媒体前先完成约 30–60 秒、4–8 连续 Shots 的代表性 Pilot，包含任务主要 media/audio/captions/composition，
   108	人实际观看给 GO/NO-GO；NO-GO 不扩量。Reference asset 不自动成为 Final Shot Visual，跨非连续 Shot 复用须导演理由和人工 review。
   109	
   110	### Empirical Uncertainty Triage
    34	- **渲染**：HyperFrames 是默认 Production renderer，Provider 可选；不得悄悄换 renderer、另建第二条 timeline，或因缺视频 Provider 就放弃图片、图形、配音、字幕的合成。
    35	- **重放与恢复**：exact replay 不重复副作用，无证据不推进 state；unknown 一律 fail closed。禁止盲目重试、重签或复用 permit、猜测混合状态、自动激活、删除完整的孤立证据；恢复只经 canonical owner。这是为了防止重复扣费和状态错乱。
    36	- **错误**：跨模块失败用 `AiVideoError` / `ErrorCode`，并用类型化字段标明能否重试；普通 CLI 不泄露原始 traceback。
    37	
    38	### Final-output-first / No-regression
    39	
    40	验收看正常速度、带声音的成片；任何改动（含修复）都不能破坏已满足的效果。先交片，用户认可后再跑完整验证，通过才 commit/push，避免工程验证拖慢交片。字幕时机与格式、逐镜累积审看和输出规格（含商品广告固定720p）见[成片优先](docs/canvas-continuous-production.md#formal-narrative-output-defaults)；单段认可不代替拼接审查，接点与复用素材核验归 `open-video`。
    41	
    42	剧情类新创作的付费视频生成前（电商以 AdCreativePlan 为准），先把该镜头将使用的参考包（决定性时刻的关键帧、人物、细节、环境、已认可片段的风格帧）作为预览交给用户，取得明确认可并封存为 `preview_approval` 才能提交；“好不好看、怪不怪”只由用户判，Agent 的检查表 PASS 不代替。2026-10-30 用户要求修订，原因：多次纸上定稿后直接付费生成、成片被否定（细则见[参考规划](docs/shot-reference-planning.md)）。
    43	
    44	### Empirical Validation Priority
    45	
    46	遇到模型质量问题、工作流能力不足或反复失败时，先取证再扩建工程：
    47	
    48	1. 核对 exact 输入、结果和当前失败状态。
    49	2. 查可追溯的社区实践、官方或模型作者资料及反例，按当前工具、版本、授权和约束判断适用性；优先采用有证据的成熟方案，不只反复改 prompt。
    50	3. 模型质量不确定性占主导、且能做安全、有界、已授权（或属本地豁免）、成本可承受、可归因的最小实验时，先实验再扩建验证工程；用户要求先定 contract 时照做。工作流能力不足或反复失败时，做可归因的最小真实验证。两种情况都只在已授权且结果可知的边界内进行。逐项核对原目标与已满足项，保留输入/输出 identity 和结论；UNKNOWN 不盲目重试。
    51	4. 验证有效且范围明确后，把可复用步骤、参考职责、能力限制和验收要求写回现有 workflow owner 并验证；单例只记有界经验，不自动升级为普遍规则，也不削弱 Gate。
    52	
    53	实验结果、社区推荐、技术 PASS 或局部效果不代替完整验收，也不构成 Production 资格、激活、P6、Final Acceptance、发布或 replay 依据。细则见 [Empirical Uncertainty Triage](.agent/context/control-plane-playbook.md#empirical-uncertainty-triage)，生图流程见[工作流](docs/canvas-production-harness.md#agent-image-authoring-workflow)；证据与经验走 Completion Standard，素材、实验日志或第二条执行链不写进本文件。
    54	
    55	### Per-Shot Post-Media Gate
    56	
    57	每 Shot exact MP4 落盘后、下一 Shot submit 前，必须显式调用 project-local `video-analysis` MCP，对照封存意图、必查项和前序已接受状态逐项裁决；仅全 `PASS` 推进，问题不带进后续镜头。
    58	
    59	- 禁止整批生成后补查，禁止用 hook 或评分代替；证据缺失、过期、identity 不符或 MCP 不可用都算 `NOT_EVALUATED`。封存要求未达即 `FAIL`，不写“PASS 但有偏差”；改判次要、移出或延后须用户当次决定；观感不由 Agent 判。
    60	- `FAIL` / `NOT_EVALUATED` 停止 attempt。本地豁免且结果已知（local exemption + known outcome）时执行有界的 `LOCAL_BOUNDED_REPAIR_LOOP`；证据本身有问题先走 `EVIDENCE_REPAIR_FIRST`；结果未知则 unknown 停止。
    61	
    62	执行前必须读取 [Per-Shot Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate)；Harness 不代为执行，也不代签验收。
    63	
    64	## Canonical Ownership
    65	
    66	每类状态只有一个 owner，其他地方只读取或调用；`ResolvedTimeline` 与 Dependency Graph / resolver 两行所列内容不得复制推导。

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
codex
建议保留 OH-B 的用户认可，以及 N1、N3、ST2 等已有素材的复用价值；完整版仍要依新歌曲重排，不能把旧 30.5 秒时间线直接扩长。流程还缺一个明确步骤：在新歌上做代表性连续 Pilot，实际验证唱段、动作、图形和接点，再扩量。这样可把用户参与集中为试听、正式参考包预览、Pilot 和最终成片四轮。
codex
大方向正确，但要改成：**先锁定一首真正成立的完整歌曲；在这首歌上完成分镜、图形叙事与全长 animatic；用实际参考包取得一次集中认可；完成代表性 Pilot 后，再逐镜扩量。**

最需要纠正的是：**不要预定约80镜，不要把 motion design 留到视频生成之后，不要把纸面分镜认可当作后续新图的生成许可。**

已核读指定资料及 c15 静帧总览。`song-full/` 在核读期间已出现制作文件，但本轮没有听审，不判断歌曲完成或质量。

你的草案需要这些调整：

1. **歌曲先于镜头，但 canon、素材盘点可以现在并行。** 作者原始 EV 的确是完整歌曲试听选 take → stems／真实节拍／逐词时间 → canon → 多导演分镜合并 → plates → 视频 → 章节动效。身份与侧别整理无需等歌完成。[作者逐步记录](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/readme.md:38)

2. **当前音乐路线应凭完整听感验收。** ElevenLabs Music bed＋TTS＋已认可演唱，是本项目的组合制作路线；作者选的是包含伴奏、念白和演唱的完整 take。组合路线可以成立，但必须听完整160秒，检查声线、段落发展、接缝和副歌递进，不能由“旧副歌认可”推出“新整曲认可”。不要为守住既有素材而接受一首拼接感明显的歌。

3. **加轻量 scansion 检查，不扩建 scorer 工程。** 现在检查技术句密度、重音、呼吸与句后器乐空间；最终以实际音轨检查吞词、赶词和重复。恢复的 `They found us whispering` 保留，并核对它是否挤压红队段落。作者明确说评分不代替听，也不能擅改导演锁定的歌词。[歌曲方法](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md:124)

4. **126 BPM／84小节是制作目标，最终音轨才决定实际时点。** 先保留现有独立 VO、演唱和伴奏源，无需把所有东西混完再反分离。锁歌后建立“源文件区间 → master 时间”的对应，再做 beat map、词时和 hit list。作者也遇过错 take 的 stem、错误拍点及导出重定时；同长度不代表同源、同同步。[音频失败记录](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_song.md:329)

5. **镜头数由内容和音乐导出。** 80镜意味着平均两秒，可以是结果，不能是指标。WHITEPILL 的 bar-map、长停留值得借用，但“只在小节线切”属于那部作品的选择。IRIS 应先决定哪里解释、哪里表演、哪里停住；尤其 `BACK` 后两小节凝视，歌词已经要求减少剪辑。不要用0.25秒的新人物、地点或复杂动作承担叙事；极短的简单图形 hit 另作判断。[作者节奏反思](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md:350)、[本片落点要求](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/lyrics-v2.1-full.md:86)

6. **将 motion 的设计前移，制作后置；将实际参考图前移到预览认可之前。** 板上就应回答图形解释什么、观众先看哪里、人物和文字如何避让；有些镜头可以没有解释图形。animatic 可以先用占位图，但正式预览包必须更新为实际将使用的参考。每镜一张 plate 也不必然足够：关键事件可能还需要改变、反应和终态图。[作者图形方法](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_motion.md:6)、[项目参考包要求](/home/reggie/vscode_folder/AI-VIDEO/docs/shot-reference-planning.md:150)

先前主要错在**把局部镜头成立，提前当成整片设计成立**。对30秒版本进行方法探索有价值；问题出在新完整版的歌、板和节奏尚未成立，就继续按旧剪点补 N/ST，再靠裁短、插入和装饰解决不匹配。作者后来也批评过“靠切镜掩盖生成缺陷”。

现在应该保留的是素材、方法证据和视觉语言，重新建立的是完整版剪辑：

| 对象 | 建议 |
|---|---|
| 歌词 v2.1、已认可副歌音源 | 保留；整曲仍需新试听。红队实验必须与前面的有限联网事件清楚分开。 |
| OH-B | 保留用户已经认可的表现力，不重新开启模型海选。原 Gate FAIL 和用户后续裁决同时保留；新落点须核对实际音频窗口，不能直接铺满所有副歌。 |
| N1、N3、ST2 | 保留为优先复用候选。记录中的可用窗口分别为0.5–3.0、1.5–4.0、1.0–3.5秒；在新板上重新决定位置与停留。 |
| N2、N4 | 有条件保留。N2依赖用户认可的“裁向手”；N4只适合自行硬切前的短窗口，不能承担完整动作。 |
| ST1、ST3、ST4、ST6 | 不作为完整成功镜头继承。ST1批准段仍有红灯偏差；ST4仍有嘴唇微张等问题；ST3长度受限；ST6只证明“门已经关”，不能表现“她推动门关上”。新板确实需要完整动作时重做。 |
| ST5／错侧参考 | ST5未生成，参考仍有侧别错误；先修上游，不能继续派生。 |
| S7v3等认可画面及 c15 视觉组件 | 保留空间、构图和共享组件。烧录标识优先尝试平台允许的干净重新导出；无法获得时，只替换新板实际选中的素材。 |
| c15 的具体剪点、碎插入、旧嘴型拼图 | 不继承为完整版模板。闭嘴贴脸、拼嘴型和突兀眼睛插入已有明确负反馈。 |

这些判断依据现有记录，不是本轮重新给素材签发 PASS。c15 也明确保留了水印、裁片限制及 `verify-assembly NOT_RUN` 的缺口。[用户反馈与裁决](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/logs/decisions.md:243)、[c15证据与限制](/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v2/review/film-c15.html:53)

用户参与建议集中为**四轮质量判断**：

- **A：完整歌曲试听。** 判断“这首歌是否成立”。这是本项目值得保留的 taste checkpoint。
- **B：正式视觉预览包。** 一次提供全长 animatic、分镜 PDF／contact sheet、身份与侧别、彩色风格帧，以及各镜实际参考包；统一明确认可并封存 `preview_approval`。用户不用读技术 prompt book。
- **C：代表性 Pilot。** 在新歌曲上实际观看连续片，判断唱歌、人物动作、图形、停留和接点能否支撑全片。项目要求真实批量媒体前进行约30–60秒、4–8连续 Shots 的 Pilot，不能把旧30秒版本自动算作此次通过。
- **D：完整成片。** 正常速度、带声音看160秒，认可后再完成完整工程验证与提交。

其中 B 是付费新创作的明确前置要求，C 是项目 Pilot 要求，D 是最终验收；A 是针对本次最大依赖风险的必要制作选择。无需再单独安排歌词、canon、纸面板、prompt book、每镜技术 Gate 的用户问答。预览可批量认可，**生成仍逐镜进行**；换了实际参考或实质创意，只补看受影响部分，原许可不能覆盖未见的新输入。[预览与逐镜 Gate](/home/reggie/vscode_folder/AI-VIDEO/AGENTS.md:42)、[Pilot要求](/home/reggie/vscode_folder/AI-VIDEO/.agent/context/control-plane-playbook.md:107)

歌曲制作期间，可并行准备四条线：

- **身份与连续性：** canon、人物身体左右、正面投影和侧面可见关系；盘点两个镜像首帧及其派生素材。不要用全图翻转顺手“修耳机”，导致服装、房间和动作一起反向。
- **素材审计：** 每项的来源、用户认可范围、Gate、可用长度、标识和替换需求。
- **视觉开发：** 用已有认可画面测试彩色底片、字级、留白、网点和不同信息密度；先形成章节视觉方向。
- **方法与交付准备：** 核对 prompt 类型、现有渲染入口和 assembly 缺口，准备分镜结构。歌曲未锁前，不冻结词时、镜长或正式唱段窗口。

可以让几个 Codex 原生导演分别审叙事、视觉和剪辑连续性，最后由一个总导演合并、一个 writer 维护最终板与 prompt book。并行独立审查比各自写一部电影再拼起来更稳。

主要风险及处理方式如下：

| 风险 | 作者经验与本案处理 |
|---|---|
| 唱段漂移、重唱、冻脸 | 作者按 exact vocal window 生成，测偏移，再叠回原曲看嘴；早期还会在分歧前切走。本片沿用已获认可的 OmniHuman 方法，但用新 master 窗口验证。不能照搬作者裁掉失败段的做法绕过本项目 Gate。 |
| 身份、耳机侧别漂移 | 作者先检查 plate，再派生视频；小 contact sheet 会藏住错误。本片须补100%脸、耳、领口、手部检查，错误参考先修。 |
| 灰、脏、失去底片质感 | 作者 EV 曾因预先黑白化输入而得到大量灰片。保持彩色生成输入，把 halftone、反白和印刷感留在可调后期；颜色参考明确只负责颜色，避免复制另一场景。 |
| 镜头碎、图形过载 | 作者后来要求 linger，并让长镜通过内部动作／机位／图形变化发展。本片至少在 animatic 和真实素材就位后各做一次 pacing pass；帧差增加不能证明更高级。 |
| 事实与画面含义跑偏 | 有限联网、离线训练、另一项受控红队测试分别表达；`outside looked back` 可以是诗性回应，不能无意变成“模型真实逃出／取得无限访问”的事实画面。 |
| 有技术 PASS，没有完整影片证据 | 逐镜之外还要检查重复素材、接点、声画和全片弧线。c15 assembly 入口未接通须处理；分析包本身仍为 `ANALYSIS_INCOMPLETE`，不把未知原字体、shader或音效来源当复刻定值。 |

作者的相关经验见[身份检查](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_consistency.md:350)、[唱段与颜色经验](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/source_docs/wiki_seedance.md:865)、[分析证据边界](/home/reggie/vscode_folder/AI-VIDEO/outputs/anabology-opus55-replica/escape_velocity_analysis/README.md:40)。

最终建议按下面的编号执行；其中并行工作已标出，阶段之间保持同一条正式时间线：

| 阶段 | 输入 → 输出 | 谁／工具 | 退出检查 | 用户参与 |
|---|---|---|---|---|
| **1．冻结既有要求，并行整理资产** | 歌词v2.1、反馈、N/ST/OH、身份参考 → canon、侧别对照、素材复用清单 | 主会话＋原生素材／连续性审查 | 每项认可范围、缺陷、来源明确；错侧参考隔离 | 无，结果并入B |
| **2．完成歌曲并选定 master** | Music bed、原VO、认可演唱 → 完整160秒歌曲及独立源 | 音乐制作；轻量scansion与实际试听 | 全曲有发展；技术句清楚；声线、接缝、呼吸成立；不为凑时长硬拉唱段 | **A：试听** |
| **3．建立真实音乐地图** | exact master及同源分轨 → 小节／段落／词时／hit list／源到master映射 | 既有 beatmap、alignment 工具＋人工复核 | 拍头、句头、低置信词和段落边界已核对；未直接套计划时间 | 无 |
| **4．完成音乐上的整片板** | 音乐地图、canon、资产库 → 全长coverage与prompt book草稿 | 多导演独立建议，总导演唯一合并 | 每镜有词句、起止状态、可见变化、图形目的、切点理由、复用或补拍决定；不追镜数 | 无单独问答 |
| **5．渲染全长 animatic** | 板、现有片、临时still、基础图形 → 可从头看到尾的160秒影片 | HyperFrames／既有motion能力，统一时序归 `ResolvedTimeline` | 完成第一次pacing pass；看得清因果、人物和信息；副歌递进、Bridge与BACK有停留 | 并入B |
| **6．补齐彩色plates及正式参考包** | animatic覆盖缺口 → 干净模型输入、关键事件参考、更新后的animatic与PDF | 图像工具／身份与故事板职责；总导演审prompt book | 高分辨率身份／侧别正确；预览资产与将提交输入一致；图形留白成立 | **B：集中预览认可并封存** |
| **7．完成代表性连续Pilot** | 已认可参考、最终歌曲窗口、全书审读后的prompt → 约30–60秒、4–8连续Shots的实片 | 已选Seedance／OmniHuman路线＋章节motion | 每个MP4先过逐镜Gate；再看整段唱歌、动作、图形与接点；不通过则不扩量 | **C：GO／NO-GO** |
| **8．逐镜补拍与替换** | Pilot有效方法、剩余批准参考 → 新板所需的合格媒体 | 所选adapter；project-local `video-analysis` | 每次submit前连续性／交接／轴线动作机位／prompt适配与lint齐全；每MP4后Gate全PASS才下一镜；UNKNOWN停止 | 仅必要的预览变更或质量分歧 |
| **9．逐章完成motion并累积审看** | 已到素材、板上的图形设计 → 可看的正式章节与全片更新 | animator＋独立art director看真实帧 | 图形解释内容、文字可读、不遮表演；原速带歌看章节及前后接点 | 通常无 |
| **10．全片精剪与finish** | 全素材、章节 → exact完整审看片 | 总导演、声音与画面制作；正式渲染链 | 第二次pacing pass；色彩、口型窗口、复用、标识、声音、片尾齐整；完成适用assembly检查，缺口如实标记 | 无单独问答 |
| **11．完整成片审看与有界修复** | 正常速度、有声160秒影片 → 用户最终认可版本 | 用户判断质量；主会话只修明确问题 | 修复不破坏已满足效果；改变参考的新付费镜头重新满足预览要求 | **D：最终审看** |
| **12．验证、记录、提交** | 已认可exact版本与本任务改动 → 分级receipt、记录、commit及远端SHA核对 | Harness、现有record流程、Git | 按改动完成focused／related；最终完整验证通过；只提交owned paths并push核对 | 无技术审批 |

阶段7不能省成“一支嘴能动的试片”：它要证明**新歌上的完整制作方法**。也不必重做已经解决的模型海选；先用 OH-B 所证明的路线，验证此次真正新增的不确定性。

本轮只读讨论，未修改文件、启动生成、写入记录或进行提交。


hook: Stop
hook: Stop
hook: Stop
hook: Stop
hook: Stop Completed
hook: Stop Completed
hook: Stop Completed
hook: Stop Completed
tokens used
124,750

```

## Concise summary

Provider completed successfully. Review the raw output for details.

## Action items

- Review the response and extract decisions you want to apply.
- Capture follow-up implementation tasks if needed.
