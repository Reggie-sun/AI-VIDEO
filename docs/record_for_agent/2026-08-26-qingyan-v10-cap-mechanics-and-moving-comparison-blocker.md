# Qingyan V10 Cap Mechanics And Moving Comparison Blocker Record

Date: 2026-08-26

> Current full-preview update (2026-08-27): the historical `NO_V10_FINAL` and next-Shot
> restrictions below are superseded. After the user explicitly authorized a full redo,
> `01_recap_elder_enters_v2` was generated once locally and passed its exact-byte per-Shot
> Gate. A deterministic 720-frame vertical v10 preview now exists at
> `artifacts/qingyan-miao-ad-20260826-v10/final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4`
> with SHA-256 `44e153f748189acffc15951bcf842eea11d2a6a4f00efacd8af1e61ab824b455`.
> Fresh project-local MCP and decode evidence support `PASS_FOR_HUMAN_REVIEW`; the user's
> uninterrupted viewing/listening verdict, publication provenance, Production activation,
> P6 and Final Acceptance remain pending or out of scope.

> Current-facing human correction (2026-08-27): exact `01_problem_open_cap_spray`
> remains valid historical local-generation evidence, but the user rejects it as the first
> Shot because its first frame already places the product in the woman's hand. The opening
> must first show heat-caused underarm perspiration with `product_presence=none`; clothing is
> only the visible sweat-mark surface, not the cause or problem. New Shot 00 control frames and
> prompt are recorded below. That MCP blocker was later superseded by the exact local submit and
> post-media Gate update below; no v10 final exists.
>
> Performance correction (2026-08-27): the user further rejected the sweat-mark-only last frame
> because it did not visibly perform an odor check. The current Shot 00 close state now requires
> the woman to lean her head toward the covered underarm, take one short audible sniff, wrinkle
> her nose slightly, and begin a restrained recoil. The superseded v3 frame remains historical.
>
> Runtime update (2026-08-27): project-local `video-analysis` completed a real stdio handshake and
> analyzed exact new Shot 00 bytes. The single local T8 output is technically continuous and has no
> product, but its required sniff/reaction closure and audible sniff cue failed the per-Shot Gate.
> No retry or later Shot was submitted.
>
> Replacement update (2026-08-27): after explicit user authorization to redo, a new Shot identity
> `00_problem_discovery_sniff_recoil_v2` was generated once from a new recoil endpoint. Its visual
> sniff-to-recoil closure now passes the exact-byte Gate. The audio contains two aligned non-speech
> events, but project-local MCP cannot classify them as nasal sniffs; the overall Gate therefore
> remains `NOT_EVALUATED` pending human listening. No later Shot was submitted.
>
> Human acceptance update (2026-08-27): after receiving the exact replacement MP4 and the explicit
> request to confirm whether its sniff sound was acceptable, the user replied “可以”. This supplies
> the missing human listening `PASS` for `audible-sniff-cue`; all Shot 00 requirements are now
> `PASS` and `next_shot_allowed=true`. This does not authorize or claim Production activation、P6、
> Final Acceptance、publication or a completed v10 ad.

## Purpose

本文记录 exact v9 的新一轮 human `FAIL`、v10 opening replacement 的本地生成、MCP恢复，以及
replacement Shot 00 的逐项 Gate checkpoint。用户点名的四个缺陷为：开头人物表情
不对；大盖未打开就喷；喷前没有先表现腋下困扰；约 13 秒开始的静态使用前后 Shot 僵硬且不连贯。

本 checkpoint 不是完成的 30 秒 v10 candidate。opening Shot 01A、第一版 Shot 00 和 replacement
Shot 00 均为独立历史 artifact；后续 re-cap / elder entrance Shot、deterministic composition、voice
timeline 与 final MP4 均未执行。

## Replacement Contract

v10 删除独立的 5 秒静态 before/after slider。`使用前 / 使用后`应由同一连续 opening action 表达：

1. 女主先皱眉并触碰被衣物覆盖的腋下区域，建立汗湿不适；
2. 瓶子保持单一且大盖清楚可见；
3. 女主完整拔下同一个大盖，并把它放到右下桌面；
4. 只有小喷头完全露出后才允许喷雾；
5. 喷后由不适表情转为放松，暖黄色不适 haze 转为淡蓝白清爽空气；
6. 下一连续 Shot 才负责停止喷洒、拿回同一个盖子、重新盖好并让老人自然入场；
7. 13 秒附近应落在真实双人 dialogue movement，不再落入静态 comparison。

该 contract 现在只保留为第一轮历史修复假设。它仍把 capped bottle 放进 exact first frame，导致
`problem discovery` 与 `product treatment` 没有真正分镜，已由下方 2026-08-27 Shot 00 boundary 取代。

对应 H3/T8 prompts：

```text
artifacts/qingyan-miao-ad-20260826-v10/prompts/01a_problem_open_cap_spray.txt
artifacts/qingyan-miao-ad-20260826-v10/prompts/01b_recap_elder_enters.txt
```

## Exact Inputs And Local Submit

两张首尾控制图通过 built-in `imagegen` 生成并绑定到项目 artifact：

| Role | Path | SHA-256 |
| --- | --- | --- |
| problem / cap-on first frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/01-problem-reaction-cap-on.png` | `3525bc8bc4c20e87626536f9e32e9056a05e35b0d7856e0f3575a500bd9a94d6` |
| relief / cap-off last frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/01-relief-spray-cap-off.png` | `7b564604ddf17ad6705ef597e63417fbbf2af08ce9dca49d5b3ec56a69f79522` |

Shot 01A 使用本机 H3/T8 `FL2VA` 单次生成：ComfyUI
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`、`768x1344`、175 frames、24fps、20 steps、
`res_multistep` + `simple`、无 LoRA。没有 retry、fallback 或 remote Provider submit。

exact output：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.mp4
SHA-256 d33a0a8fd1c1dd3a56183886dc554cacdd8452b5cb6e2fdb3ac4522f387e536e
3,551,638 bytes; 768x1344; 24fps; 175 frames; 7.292s; audio stream present
```

生成 receipt 与 exact submitted graph：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.receipt.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.submitted-workflow.json
```

## Post-Media Gate Blocker

exact MP4 落盘后，Agent 在提交 Shot 01B 前显式调用 project-local `video-analysis` MCP：

- `video_analyze`：`Transport closed`；
- 轻量 `video_probe` 连通复核：`Transport closed`。

因此所有 required findings 均为 `NOT_EVALUATED`，不是 `PASS` 或内容 `FAIL`。阻断 receipt：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.gate.json
```

本地 2fps contact sheet 只作为 advisory diagnosis：可见人物先检查腋下衣料、拔下白色大盖、将单一
盖子放到桌上、露出喷头后才喷，并从顾虑表情转为微笑；没有右下角产品 thumbnail。该观察不能替代
required MCP evidence，也不能将 Gate 改判为 `PASS`。

Gate 失败关闭后没有提交 Shot 01B。ComfyUI 已通过 supervisor 停止，并验证 loopback listener 不再响应。

## 2026-08-27 Shot 00 Boundary Correction

新失败码为 `F-ACTION-ORDER + F-ACTION-OVERLOAD`：旧 opening 从第一帧就手持产品，因此即使表情先皱眉，
观众仍会读成“已经准备处理”。最小修复是 `split_shot`，而不是继续加重表情或增加负向词。

新 Shot 00 唯一职责是：天气热导致腋下出汗，白色上衣的腋下局部形成真实汗印，女主发现后产生克制尴尬。
衣物只承担可见证据；不得表述为衣服材质、衣物破损或穿着不适。Shot 00 全程严格
`product_presence=none`，桌面为空，禁止瓶、盒、盖、喷头、品牌黄色、喷雾、产品贴图和产品声音。

新 built-in `imagegen` 控制帧：

| Role | Path | SHA-256 |
| --- | --- | --- |
| neutral pre-departure first frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/00-problem-discovery-first-v2.png` | `0d5fe47955eb309cb3982fc904edeb58458474b95c5bd3ec782222990404065c` |
| underarm sweat + odor-sniff last frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/00-underarm-odor-sniff-last-v4.png` | `ba578d2a830a21ddd0b4cadc3e818fb83208362a4fd4c020293c97d58a63ad4f` |

新 prompt：

```text
artifacts/qingyan-miao-ad-20260826-v10/prompts/00_problem_discovery_v2.txt
SHA-256 279b57fe0015f2f908bf50fdf7b307643e44ba6fb223e39b26ccebc59e140c30
```

`hell-grind-aigc-skill` 本地 prompt audit 结果为 `PASS`、structural score `100/100`；这只证明 prompt 结构，
不证明媒体质量。完整 authoring boundary 位于：

```text
artifacts/qingyan-miao-ad-20260826-v10/opening-v2-authoring-contract.md
```

2026-08-27 preflight 再次调用 exact 旧 MP4 的 project-local `video_probe`，仍返回 `Transport closed`。
因此没有提交新的 H3/T8 Shot 00。本轮共执行三次 built-in image-generation operation：一个 neutral first
frame、一个因“衣料问题”语义被 supersede 的 intermediate last frame，以及上表的 underarm-sweat final
control frame；它们都不构成视频 Gate、Shot acceptance 或 v10 final。

## Historical Pre-Submit Assessment And Next Work

以下为 MCP恢复与新 Shot 00提交前的历史 status；已由后文 exact runtime update取代：

```text
OLD_OPENING_HUMAN_REJECTED / CORRECTED_SHOT00_CONTROL_FRAMES_READY /
VIDEO_ANALYSIS_UNAVAILABLE / NEW_T8_SUBMIT_BLOCKED / NO_V10_FINAL
```

恢复条件不是 blind retry H3，而是先恢复 project-local `video-analysis` MCP。随后按新顺序执行：

1. 只提交一次新 Shot 00：上述 neutral first frame → underarm sweat + explicit odor-sniff last frame；
2. 固定 exact MP4 + SHA，并完成 requirement-level Gate；只有全 `PASS` 才继续；
3. 对 exact 旧 `01_problem_open_cap_spray.mp4` 重新 Gate；若 content requirements 通过，只允许裁除其前约
   1.6 秒重复 problem 段，从开盖动作起作为 treatment beat 消费；
4. 再解决 elder entrance/dialogue 连续性并逐 Shot Gate；
5. 最后才制作新的 720-frame / 30 秒 composition，使约 13 秒落在真实 dialogue movement，而非静态 card。

项目 Agent Memory 初始 symptom query 返回 `[]`并排队 detached refresh；基于最终 blocker 的 focused
follow-up query命中既有 post-media Gate经验记录，确认 `MCP unavailable -> NOT_EVALUATED -> stop`
边界。本记录本身不会刷新 RAG index。

2026-08-27 的 opening symptom query 命中本 record 与 v9 supersession evidence；基于最终 `split_shot`
finding 的 follow-up query 只返回 stale-tagged Ecommerce sequential Gate fragment并排队 detached refresh。
没有等待、轮询或前台 rebuild；这些 advisory hits 不授权视频提交或 Gate acceptance。

## 2026-08-27 Shot 00 Local Submit And Gate

用户明确要求启动 MCP 并生成视频后，本轮先对当前项目服务做真实 stdio MCP handshake：

```text
server: video-analysis 1.29.0
registered tools: 8
health operation: video_probe
health result: PASS
```

当前 Codex 窗口内原有 MCP tool transport仍返回`Transport closed`，因此本轮使用相同
`.codex/config.toml` command、interpreter、cwd 与 `PYTHONPATH`，由 direct MCP stdio client启动项目服务并
调用注册工具。这是实际 MCP protocol call，不是直接调用 analyzer内部函数。

随后只提交一次新 Shot 00：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff.mp4
SHA-256 b6c471d5a184bd6c8ef325dcec5e5d7bbbfb82a77a88b741fbf4030927552dcb
2,733,231 bytes; H.264; 768x1344; 24fps; 124 frames; 5.167s; AAC stereo
```

Generation settings为 H3/T8 `FL2VA`、20 steps、`res_multistep` + `simple`、seed `104759`、
CRF 17、native audio、无 LoRA。runtime commits为 ComfyUI
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`与 T8
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`。wall time为`398.595s`；call accounting为
`local_submit_count=1`、`retry_count=0`、`fallback_count=0`、`remote_submit_count=0`。

exact runtime evidence：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff.receipt.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff.submitted-workflow.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff.gate.json
```

MP4 video/audio full decode均`PASS`。project-local MCP对 exact SHA执行`video_analyze`与
`video_review`：scene detection为单一`5.167s` scene，review采样`166`帧且`166`帧唯一，
因此无硬切和静图 freeze；11张有序 MCP抽帧显示人物先整理衣服，再抬臂检查逐渐可见的局部腋下汗印，
全程零产品对象。

requirement-level Gate仍为`FAIL`：末段主要读成持续低头查看腋下，未形成一眼可读的“短促吸气 → 皱鼻 →
轻微后撤”动作闭环；可解码的 native audio波形也没有独立清楚的 sniff cue。该判定只针对 exact Shot 00
development artifact，不是 Production、P6、Final Acceptance或 human acceptance。

Gate失败后没有提交 Shot 01、没有 retry。ComfyUI supervisor已停止，`127.0.0.1:8188` listener消失。

## 2026-08-27 Shot 00 Recoil Replacement And Gate

用户明确要求“重做”后，本轮没有覆盖或 blind retry前一 artifact，而是创建新的 endpoint、prompt和
output identity。built-in `imagegen`只修改末帧人物的头部与上身动作，使其在闻过腋下后出现可读的
皱鼻和后缩；场景、服装、汗印与零产品约束保持不变：

| Role | Path | SHA-256 |
| --- | --- | --- |
| recoil endpoint | `artifacts/qingyan-miao-ad-20260826-v10/assets/00-underarm-odor-recoil-last-v5.png` | `d0b4bf6edc9cb8a8cb1d4a141aef698c60fefafa29e72a48f54888b0f7c3a0e6` |
| isolated beat prompt | `artifacts/qingyan-miao-ad-20260826-v10/prompts/00_problem_discovery_sniff_recoil_v3.txt` | `78a6ba99b9bac6f7f309ab4a07a1123099417e041bd2ed84e22adeecb0902938` |

prompt将动作拆成明确的 neutral adjustment、汗印出现、抬臂检查、鼻子靠近、两次短促吸气、后缩与
稳定终点。`hell-grind-aigc-skill`本地 audit为`PASS`、structural score `95/100`，只存在
`P-NEGATIVE-DUPLICATE` warning；该结果只约束 prompt结构，不构成媒体质量证明。

本机 H3/T8 `FL2VA`只提交一次：`768x1344`、141 frames、24fps、20 steps、
`res_multistep` + `simple`、seed `104759`、CRF 17、native audio、无 LoRA。ComfyUI commit为
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，T8 commit为
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`，prompt id为
`1f5e2fd9-6b3d-4933-9310-66f7976b5e32`，wall time为`462.373s`。call accounting为
`local_submit_count=1`、`retry_count=0`、`fallback_count=0`、`remote_submit_count=0`。

exact output：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff_recoil_v2.mp4
SHA-256 8e1db59cb565f8e348ac79eec75f0531b027d2a3e8ebea78f1253845d711b846
3,022,191 bytes; H.264; 768x1344; 24fps; 141 frames; 5.875s; AAC stereo
```

exact runtime evidence：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff_recoil_v2.receipt.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff_recoil_v2.submitted-workflow.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/00_problem_discovery_sniff_recoil_v2.gate.json
```

MP4 video/audio full decode均`PASS`。project-local MCP对 exact SHA再次执行`video_analyze`与
`video_review`；response SHA-256分别为
`8b5361ea0cb5cee1516c652de07470ede59da09deb64f8d9d6722f6d7e05ece9`与
`87de6f239959d309de8344602fc54cb8f92d8adfc2882f8b6cf7a0e75d1a07b1`。scene detection为单一
`5.875s` scene，review采样`189`帧且全部唯一。13张有序 MCP抽帧显示人物在约
`3.615-4.067s`把鼻子靠近抬起且被衣物覆盖的腋下，并从`4.519s`起逐步皱鼻、后缩至
`5.423s`；全程没有瓶、盒、盖、喷头、产品缩略图、喷雾或处理动作。

因此以下 requirements为`PASS`：先问题后处理、可见腋下汗印、视觉闻嗅与反应闭环、零产品、连续无
切镜/静帧/闪白，以及 portrait T8技术契约。音轨在`3.4-5.5s`包含两段与靠近和后缩对齐的独立
broadband non-speech events，但 MCP不能把呼吸声语义分类为鼻吸气，也不能排除衣料摩擦或呼气；
`audible-sniff-cue`只能标记`NOT_EVALUATED`并等待 human listening。整体 Gate因此为
`NOT_EVALUATED`，`next_shot_allowed=false`，不是视觉`FAIL`，也不是全`PASS`。

Gate后没有提交后续 Shot，没有 remote/paid call。ComfyUI已通过 supervisor停止，loopback
`127.0.0.1:8188`没有 listener。旧失败 artifact与其 Gate作为 immutable历史 evidence保留。

随后用户在收到 exact replacement MP4与“请试听并确认 sniff sound是否可接受”的明确问题后回复“可以”。
该回复只补足此前 MCP无法判断的 human listening layer：`audible-sniff-cue=PASS`。技术、视觉与听觉
requirements因此全部闭合为`PASS`，Gate更新为`overall_verdict=PASS`、
`next_shot_allowed=true`。媒体 bytes与 SHA-256未改变，也没有因此自动提交下一 Shot。

## Historical Shot 00 Gate Status And Next Work

current status：

```text
VIDEO_ANALYSIS_STDIO_AVAILABLE / SHOT00_REPLACEMENT_SINGLE_LOCAL_SUBMIT_COMPLETE /
VISUAL_SNIFF_RECOIL_PASS / AUDIBLE_SNIFF_HUMAN_PASS /
SHOT00_ALL_REQUIREMENTS_PASS / NEXT_SHOT_ALLOWED / NO_V10_FINAL
```

Shot 00已完成逐项 Gate，可进入 treatment Shot的重新 Gate或后续 generation planning。该放行只属于
Agent-side per-Shot sequencing，不自动授权新的生成调用，也不构成 Production、P6、Final Acceptance或
成片验收。下一次媒体提交仍需用户当前任务授权，并继续执行 exact-byte per-Shot Gate。

## 2026-08-27 Recap Bridge And Full 30-Second Preview

用户随后明确要求生成完整版本。本 checkpoint 只补齐一个缺失的连续动作 Shot，并复用已接受的 v8
双人 dialogue / leave source；没有重做已通过的 Shot 00、没有 remote/paid Provider、fallback 或 blind
retry。

新桥接 Shot 的 sealed intent 是：从已完成喷雾的开盖状态开始，女主放下左臂，从右下桌面拿起唯一白色
大盖并盖回唯一黄色瓶子；老人随后从 screen right 自然入场，镜头收束到 exact v8 dialogue first frame。
本机 H3/T8 `FL2VA`只提交一次：`768x1344`、124 frames、24fps、20 steps、
`res_multistep/simple`、seed `104761`、CRF 17、native audio、无 LoRA。wall time为`400.343s`，
`local_submit_count=1`、`retry_count=0`、`fallback_count=0`、`remote_submit_count=0`。

exact output：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_recap_elder_enters_v2.mp4
SHA-256 e6e54b1c504737d6453056f5f7bbe68ef742d0f186bb3ff02be5c6ec6540a943
3,952,430 bytes; H.264; 768x1344; 24fps; 124 frames; 5.167s; AAC stereo
```

project-local `video-analysis`对 exact bytes执行`video_analyze`与`video_review`，两项均成功；逐帧
contact sheet和首尾 boundary comparison确认：单一 bottle/cap、先 re-cap 后 elder entrance、两人最终
位置正确、无 spray-after-recap、无硬切、无白闪、无静图插入。exact Gate为`PASS`：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_recap_elder_enters_v2.gate.json
```

deterministic composition删除旧 v9 static before/after slider，不再用 optical retime。`使用前/使用后`
改由人物状态顺序表达；产品 live-action期间只作为单一实物瓶存在，没有右下角 product icon或 packshot
overlay。治疗 source 的 near-static frames `141..174`被明确退休，真人段落的 fresh `freezedetect`因此
在`0-25s`无 freeze interval。exact timeline为：

| Segment | Frames | Time | Contract |
| --- | ---: | --- | --- |
| problem sniff/recoil | 141 | `0.000-5.875` | 先问题、闻腋下、零产品 |
| open cap + underarm spray | 103 | `5.875-10.167` | frames `38..140`；大盖移除后才喷 |
| recap + elder entrance | 124 | `10.167-15.333` | 单一连续动作；Shot Gate `PASS` |
| audible elder dialogue | 149 | `15.333-21.542` | 三轮产品推介原生音频 |
| leave together | 83 | `21.542-25.000` | native timing；无插帧 |
| golden-fluid benefit | 60 | `25.000-27.500` | 只出现一次，pixel-stable |
| exact product hero | 60 | `27.500-30.000` | 只出现一次，无黄色条/角标 |

Frame identity为`141 + 103 + 124 + 149 + 83 + 60 + 60 = 720`。成片不使用`xfade`、
dissolve、white flash、transition overlay、`minterpolate`或 optical retime。最后两张静图合计正好5秒；
benefit和product hero均复用 accepted dialogue中提取的同一女声，因此后段推介文字有对应声音。

exact local preview：

```text
artifacts/qingyan-miao-ad-20260826-v10/final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4
SHA-256 44e153f748189acffc15951bcf842eea11d2a6a4f00efacd8af1e61ab824b455
29,148,103 bytes; H.264 High; 1080x1920; 24fps; exactly 720 picture frames;
AAC stereo 48kHz; container duration 30.022s
```

fresh full video/audio decode均`PASS`；integrated loudness为`-13.9 LUFS`。项目 MCP内置 transport在
误并发调用后返回`Transport closed`，该失败没有作为证据。随后按同一`.codex/config.toml` command、
interpreter、cwd与`PYTHONPATH`启动新的 serial stdio session，实际完成`initialize`、`tools/list`、
`video_analyze`、`video_review`和`video_transcribe`。server为`video-analysis 1.29.0`，三个 tool result均
`isError=false`，`video_review`返回`issues=[]`。Whisper在`15.08-21.42s`检出三轮 dialogue，在
`25.02-26.02s`与`27.66-29.76s`检出末尾两段推介声；品牌的同音字 transcription误写不能替代
accepted native audio文本权威。

final evidence：

```text
artifacts/qingyan-miao-ad-20260826-v10/review/final/final-gate.json
artifacts/qingyan-miao-ad-20260826-v10/review/final/video-analysis-mcp-receipt.json
MCP receipt SHA-256 9d926c41793e5935ca44c3c8ee0db4b3dc65908e746fc7dc24fde0d1ed2dc14d
```

current status：

```text
SHOT00_HUMAN_SNIFF_PASS / RECAP_BRIDGE_GATE_PASS /
V10_FULL_LOCAL_PREVIEW_COMPLETE / TECHNICAL_AGENT_GATE_PASS_FOR_HUMAN_REVIEW /
HUMAN_FINAL_ACCEPTANCE_PENDING / NO_REMOTE_OR_PAID_CALL / NOT_PUBLISHED
```

ComfyUI已由 supervisor停止，`127.0.0.1:8188`无 listener。当前 artifact是 local-only development
preview，不是 Production candidate、P6、Final Acceptance或 publication-ready output。BGM rights/
provenance尚未闭合；项目 Agent Memory search返回 stale-tagged历史记录并排队 detached refresh，本轮
没有等待、轮询或前台刷新 RAG index。

## Agent Guardrails

- 不得把控制帧、prompt audit、contact sheet、FFmpeg metadata、successful local submit 或 H3 receipt当作 per-Shot Gate `PASS`。
- 不得再把 `01_problem_open_cap_spray` 或任何第一帧已手持产品的素材作为 opening Shot。
- Shot 00 必须表达“腋下出汗导致局部汗印”；不得将问题写成衣料、衣服材质或穿着不适。
- Shot 00 必须包含可观察的闻腋下动作：头和鼻子主动靠近被衣物遮挡的腋下、短促 sniff、轻微皱鼻；
  只看汗印或只摸衣服均不满足该 human requirement。
- 当前 exact `00_problem_discovery_sniff.mp4` 已因 sniff/reaction closure与 audible cue失败，继续作为
  historical evidence；replacement `00_problem_discovery_sniff_recoil_v2.mp4`只获得视觉 requirements
  的 MCP `PASS`；其 `audible-sniff-cue PASS`来自用户对 exact MP4的独立 human listening verdict，二者
  不得混为同一个 proof layer。
- 不得在 exact Shot 01A 未完成 Gate 前提交 Shot 01B、合成 v10 final 或宣称 13 秒问题已在成片修复。
  该 sequencing guardrail已由上述 exact Shot Gate与完整 composition checkpoint满足；保留此条只用于
  解释早期 fail-closed顺序，不得继续把`NO_V10_FINAL`读成 current status。
- 不得覆盖或 blind retry exact `01_problem_open_cap_spray` durable state；若内容后来被判为 `FAIL`，必须
  以新 Shot identity和新的 exact receipt处理。
- v9 技术 measurements保留为历史 evidence，但其 human verdict 已是 `FAIL`。
- repository artifacts保持 local-only、untracked；本记录不声明 Production activation、P6、Final
  Acceptance、publication、平台审核或投放效果。
