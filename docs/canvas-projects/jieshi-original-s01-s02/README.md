# Original S01–S02 Candidate And Fidelity Matrix

## Status And Entry

本目录只准备《界蚀》原 S01→S02；共享 `inspect/author/preflight` 已实际运行。**不是已准入的 Provider 请求、已验收前镜或成片**。两镜新图片/视频 POST 均为 0；Production state 为空。精确 source-native expression 见 [S01](S01-native-input.txt)、[S02](S02-native-input.txt)，后者当前标签 `图片1` 指历史占位，必须在实际 S01 全 PASS 后经 canonical handoff 换为 accepted source 的 `视频1`、actual MP4 identity，再重新 prepare。

普通数据入口为 [project.json](project.json)，原 Canvas parts 为 [source.json](source.json)。[source-mapping.json](source-mapping.json) 保存原 Open/Action/Close/Camera/Dialogue/Prompt/Screen Text/Next-Risk；原 episode SHA-256 为 `a8c3aaaa77e9c5c7904d7dee83265ae14e6100c168e5d5a520387a070c3d53df`。不存在故事执行脚本或第二 timeline。

运行命令沿已发布入口，使用 repository `.venv`；`project-root` 必须为已存在绝对目录：

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production inspect --data docs/canvas-projects/jieshi-original-s01-s02/project.json --project-root "$PWD/runs/canvas-jieshi-original-s01-s02-20261013-001/production"
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production author --data docs/canvas-projects/jieshi-original-s01-s02/project.json --project-root "$PWD/runs/canvas-jieshi-original-s01-s02-20261013-001/production"
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production preflight --data docs/canvas-projects/jieshi-original-s01-s02/project.json --project-root "$PWD/runs/canvas-jieshi-original-s01-s02-20261013-001/production"
```

## Fidelity Matrix

出处均为 `docs/superpowers/artifacts/drama/jieshi-episode-01/episode-01.md` 相应 Shot card 或 Character/Scene Bible；当前用户明确纠正优先。`shots[n]` 下指 `project.json.direction.shots[n]`。输入表达和媒体证据分别判断；表中实际媒体 QA 全部 `NOT_EVALUATED`。

| Original requirement / Source | Project field / reference duty | Exact source-native input or canonical composition duty | Required actual evidence |
| --- | --- | --- | --- |
| S01 Open：林砚坐 A区末位；本人右脸肩在下，玻璃在上 | shots[0].shot.intent / source S01 text | `起始状态：林砚坐A区末位，镜头内本人右侧脸和肩占下方；玻璃占上方。` | exact 首帧/运动片段，座位、左右、本人和窗同时可读 |
| S01 Action：首帧六乘客及苏遥完整倒影；唯独林砚为空 | 同一 source 原句；eight character_ids；first-frame asset | 原 Action 与 Prompt 全句进入 S01 input；追加明确不得删除其他倒影 | 首帧和采用段全程逐人对应，实体8人、其他完整倒影7人、只缺林砚；不是逐渐消失 |
| S01：看空位、抬解剖左手 | subject_action.progression 原文，无抬手机替代 | `林砚看向空位并抬左手靠玻璃，玻璃里没有手。` | 动作全过程、视线对象、左右手身份；不能靠静帧代签 |
| S01 Close：距窗约2cm停住并保持到切出 | 原 Close/Prompt；S02 state_reference frame_index=71 | 两句原文保留；计划 frame71 为采用3秒内最后帧，不是4秒素材末帧 | 帧71及切点前动作，实际间隙/悬停；若 frame71 没到正确状态，本单元停而不猜 |
| S01：玻璃也没有他的手 | source Action/Prompt；首帧 clean plate 准备责任 | 模型输入明确没有手；**选择首帧准备路线，实际几何一致 plate / 只删除林砚映像仍未绑定，BLOCKED** | source/plate exact identities、实测编辑区与保护七倒影区域、窗几何和边缘无污染；原图/plate对比及 raw MP4 全程无手倒影 |
| 原右手手机职责、蓝挂绳白工牌 | 林砚 Character Bible；两镜 source 当前道具描述 | `林砚右手保持唯一黑壳手机原职责，蓝色挂绳白工牌保持。` | 唯一手机、右手稳定持机，左手空；无抬手机/换手/新增手机 |
| 八人身份/服装/道具 | characters appearance_bible；原图 review-only，尚無独立 identity sheets | 两镜原外观/服装已显式复制进 source input，不依赖 Bible 自动进入模型；S01另含苏遥左手乳白手机、陈立耳机/深蓝手机、何静膝上灰布袋 | first-frame admission + 两镜 exact video 身份/服装/道具逐人核验；文字不是视觉identity证明 |
| SC01 A/B区、D/C门与蓝椅/银杆固定空间 | 两个 scene ownership IDs，同一原 SC01 location | `固定空间：A区座位在D侧门左后…深灰地胶、蓝色长椅、银色立杆…` | 空间、门、窗和邻座位置一致，镜位切换不得重造车厢 |
| S01 Camera：28mm自然广角、坐姿眼高斜侧中广景、锁机位 | 原 Camera 完整进入 source；不伪填camera hash | 摄影原句完整保留 | 实际构图与视角；全程锁定，无pan/zoom漂移；本人和空座映像同清楚 |
| S01 广播原句与0.1–2.7s窗口 | shot.dialogue；dialogue_intent speaker_id=broadcast、zh、verbatim、start=.1/end=2.7、on_screen=false；audio_need=required | 原 `声音：[0.1–2.7s] 列车广播→林砚：“林砚，请在终点站下车。”` + same-line typed control declaration | project-local video-analysis + 能实际听音的语义证据/逐字及时间核验；点名不能换普通报站 |
| 广播画外、林砚不张嘴；中性女声/礼貌平直/D门扬声器 | Character — 列车广播；S01 source 声源描述；lip_sync_required=false 不是嘴不动的代签 | 原嘴唇不动句及 `画外广播为D门上方扬声器的中性女声…林砚不张嘴。` | 实际声源与声线/混响，林砚全广播期间嘴不动，无新增说话人 |
| S01 Screen Text：0–3s `可这条地铁，没有终点站。` | mapping.screen_text → existing CaptionTrack/CompositionSpec.caption_tracks | 原字幕由 canonical authored caption 加入，不是广播 ASR 文本；frame0至72 exclusive为计划期望 | registered caption/source-clock/style provenance + ResolvedTimeline cues + HyperFrames exact全程字形/文字/窗口；当前未制作 |
| S01采用0–3s，不插片头 | fixed3s；composition trim_start_frame=0、trim_duration_frames=72 | ResolvedTimeline 独占 adopted frames 与 native音轨samples；不能手工拼mux | actual duration/PTS/fps、Resolver receipt及最终0–3s；音轨句尾不截断 |
| S02 Open：实际 accepted S01 左手悬窗 | state_reference source=S01、frame71、conditioning=source_video | 当前 `参考图片1` 为占位；实际 accepted source绑定后共享编译改为 `参考视频1`，不强制上一尾帧作新镜首帧 | 前镜逐项全PASS、actual observation/extraction path+hash、handoff checks、绑定originalMP4/selectedframe identities |
| S02 Action：收手→先看扬声器→屏幕右邻座→吸气停顿 | subject_action.progression原文；state/cut action和motion_direction checks | `手收回，视线先去扬声器，再向屏幕右邻座；吸气停一下。` | 后镜自己的完整运动/声音；先后顺序、轴线/右侧无镜像，无起身、看门、抬手机 |
| S02 Close：面对陈立 | 原 Close；character_ids林砚/陈立 | `结束状态：林砚转头面对陈立。` | 后镜末段实际朝向/邻座关系；reference匹配不代签后镜 |
| S02 Camera：50mm侧面近景、小幅右pan | 原 Camera；handoff camera checks explicitly preserve space not28mm framing | 摄影原句完整；输入声明不复制28mm构图 | actual近景/右pan幅度、轴线及切镜后空间一致 |
| S02仅陈立肩进末段边缘，不能给脸/额外手机 | 原 Next/Risk；source explicit framing | `陈立仅肩部进入末帧边缘，不让陈立脸或额外手机进入构图。` | 实际末段边缘裁切；S03身份可接但不提前额外展示 |
| S02原句/0.6–3.5s/求证非喊叫 | shot.dialogue；typed dialogue_intent linyan、zh、verbatim、start=.6/end=3.5、on_screen=true/lip_sync=true、response | 原 `声音：[0.6–3.5s] 林砚→陈立：“刚才……叫的是我？” 求证；眉头微蹙，没有喊叫。` + exact typed declaration | 实际逐字、停顿、语气、字音、speaker/lip sync与时序；不能重复前镜广播 |
| S02采用4s，结束仍坐着 | fixed4s；trim0/96；composition_order S01→S02 | Resolver把S02放全局3–7s；原对白全局3.6–6.5s只是期望，不能当执行receipt | exact asset采用段、PTS、剪辑接点与最终声音；无起身 |
| 原生音轨、动作拟音与地铁环境声 | audio_need=required；composition muted=false；exact generated audio registration | 已有 register_native_audio→receipt绑定原MP4→PCM WAV→CompositionSpec.audio_tracks→ResolvedTimeline→HyperFrames；不替换对白、不direct mux | raw声音语义PASS之外，派生source/fetch identities、样本trim、接点声场/无重复词/无意外静音、最终实际听音 |
| 悬窗→收手的真实接点 | state_reference/checks 与 cut_requirements七维 | source_video只提供条件；partial static character_presence edge不签全动作/倒影/摄影/声音 | exact cut packet / 前后相邻帧、完整normal-speed声画片，identity/props/action/space/motion/camera/audio全部裁决 |

## Original First Fifteen Seconds

| Shot | Original final window | Original content / camera / sound | Current unit |
| --- | --- | --- | --- |
| S01 | 0–3s | 唯独林砚无倒影、左手悬窗、点名广播、hook字幕；28mm锁机位 | 候选，未真实生成或验收 |
| S02 | 3–7s | 收手→扬声器→右邻座、吸气、原求证对白；50mm右pan仅陈立肩 | 候选，等待实际前镜全PASS及handoff |
| S03 | 7–11s | 陈立右手深蓝手机，摘左耳机、瞥屏幕左画外林砚、笑后戴回；65mm固定；0.5–2.6s `什么？没报站啊。`，林砚不追加 | 只映射，不在本次生成额度内 |
| S04 | 11–15s | 许雯拇指滚动、郭向东头轻垂、沈嘉程/何静不动；手机笑声跨镜延续；35mm后区中广景横移20cm，无新增对白 | 只映射，不在本次生成额度内 |

两镜采用总长7秒，不是完整前15秒；完整故事AC-7和human1.0x均 `NOT_EVALUATED`。旧15秒抬手机A及未提交的起身B没有本表原剧情效力，不能作为 accepted S01。

## Current Capabilities And Necessary Diff

| Surface | Actual capability / gap | Necessary adaptation and stopping condition |
| --- | --- | --- |
| Original source → shared author | source parts和typed dialogue可核对；原外观Bible不会自动成为source model prose | 本目录显式复制当前外观/道具/空间，列明所有追加；没有删除原动作、声音、字幕/Next-Risk |
| Typed source dialogue | 原 compiler缺6个mapping paths，实际复现 | 新 `seedance_source_dialogue.py` 仅精确 same-line 约束表达；其余 fields仍 fail closed。不是声音验收 |
| First-frame/original image/identity | 历史PNG SHA `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb` 941×1672，仅 REGISTERED_BYTES；未admit | asset-first可准备新原图，但新单元未授权。旧图不自动升为approved视觉源；first-frame七倒影/服装/几何须独立核验 |
| Reflection / clean plate | 原 Next/Risk 要求几何一致窗内plate，但未规定最终视频overlay。现选择首帧准备：同一Seedream模型、单 PNG reference + 作者审查的 bbox编辑；shared adapter已补，见single-reference spec。现有video+局部PNG仍不宣称支持 | **BLOCKED于实际素材**。先正常几何/人物base，再用同源exact图只处理林砚反射区域并验七倒影保护，所得plate作为S01首帧。真实坐标/plate bytes未产生，不能编造；raw MP4仍须全PASS。无需为本单元扩建视频compositor |
| Hand / camera switch | source prose及state/cut七维可以表达；视频参考可换摄影而carry空间 | actual S01全PASS后source_video+帧71 observation；S02自身验收。边界character_presence为partial，不代表动态事实全通过 |
| Audio analysis / trusted evidence | 实际audio输入再次返回unsupported；本次MCP medium转写旧原片为 `林燕請在終點站下車`、0–2.24s，虽要求word_timestamps却未返回逐字时间。ControlledPresentationVerifier只接受technical/analyzer、明确拒绝human；Console七项continuity不含声音 | **EVIDENCE_REPAIR_FIRST**。需能实际听音的合格分析环境及selected authority，或接入exact-bound可信human presentation host后由真实人听判；不能把播放网页/文本答复直接当registered verifier、AAC/ASR当音义PASS。当前未接human host，不重生成补证 |
| Native audio composition | existing exact source audio registration / auto matching native WAV tracks / canonical sample trim | S01/S02真实accepted source落地后逐镜注册，保留dialogue audio_kind；必须实际验证输出声音，不能静音/重配音 |
| Captions | existing CaptionTrack、style、source audio clock、CompositionSpec.caption_tracks、HyperFrames | hook是非口述字幕；不能伪造ASR alignment说广播读了hook。需明确authored caption provenance+原生音轨时钟，实际绑定style和sample/frame；目前只有职责，未登记或render |
| Planner/Router/runtime | shared entry存在；pure source-native diagnostic已运行；current qualified factory/profile、binding、budget/egress/permit未为原unit封存 | qualified prepare与完整paid preview `NOT_EVALUATED`；不得用本目录文本或历史150CNY许可直接POST |

## Explicit Adaptations

1. 两个原Shot card按字段提取，添加中文标签；原Prompt中的执行编号/构图人员清单改为明确人物字段与当前外观prose，原动作/摄影内容保留。没有添剧情。
2. 添加 same-line 普通话、窗口、画内外/口型声明，以表达已有typed fields；原广播/对白行和演员反应全部保留。
3. 原Character/Scene Bible的当前外观、服装、道具、固定空间显式加入prose，避免只留在project而未送模型。未把未来S30/S34等行为当作开场动作。
4. S01字幕移到已存在canonical caption职责；生成端不烧字幕。字幕未实现不签coverage完成。
5. 历史PNG复制原字节只做数据绑定审阅；S02同图是 `AUTHORING_PLACEHOLDER_ONLY`。两个scene IDs只隔离reference ownership，物理地点仍同SC01，未更换场景。
6. 480p候选496×864/24fps取用户新约束，S01/S02分别请求4s、采用3/4s；不套用旧15秒nominal测试长度。
7. 对clean plate、qualified runtime、caption实际binding及声音证据的缺项明确保留，未靠删原要求通过检查。
8. 经源码/原文和独立mapping复核，撤回“clean plate必须在最终视频局部合成”的过早判断；机制改为首帧准备，不改原S01动态或raw Gate。纯文字Seedream不能担任精确编辑，已加显式single-reference profile；这不代表plate已制作。

## Bounded New Unit Proposal — Not Authorization

更新候选：最多2次 `doubao-seedream-5-0-pro-260628` PNG（1152×2048）：一次技术base，完整八人/八倒影用于定位；一次单参考编辑，只删林砚倒影、保留其他七人/窗几何，形成S01首帧。base是隔离准备素材，绝不冒充原S01首帧。bbox必须等actual base后审查，不能现在伪造exact编辑payload。之后最多2次 `doubao-seedance-2-0-fast-260128` 视频（每次请求4s、480p496×864、24fps、原生声音）；零重抽、零自动fallback。各素材独立验收；plate成功不证明视频始终没有手倒影。

拟议内部上限为每图片50 CNY、每视频50 CNY、单元总200 CNY，仅operator upper bound，不是市场价/账单。前次1图片+2视频/150 CNY只是未授权提案，无法同时证明base与clean plate编辑，保留为历史。历史视频10+旧抬手机A1=11真实计数保留；新单元最多增加2则累计13。旧累计cap12及已用1/1图片、1/2视频是历史，剩余旧B不能挪用，不修改旧记录来凑额。

**目前不提交付费批准请求**：共享single-reference准备能力已补；实际plate、可听音且能登记的Gate证据路线，以及qualified完整paid preview仍缺。唯一新的外部决定仍为是否授予补齐后的原剧本输入新有限调用单元，尚未提出或授予；本提案不是one-use permit。授权前不会POST；即使以后授权，逐次仍需current profile/window、preview、reservation、egress、durable intent和one-use permit。S01任何required finding缺证/失败就停止，不能消费S02。

## Evidence And Acceptance Boundary

当前证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/`：`inspection.json`、`author.json`、`preflight.json`、`native-dialogue-gap.json`（修复前6paths拒绝）、`native-expression-preview.json`（修复后source-native表达）；`audio-capability-probe.json`及Kimi read-only mapping receipt/report。它们没有Production acceptance权。

首帧准备职责修订后的fresh共享入口证据在 `single-reference-current/{inspection,author,preflight,source-identity}.json`：当前数据SHA `e10b3422406011616927fd48480b541de8df2ab9e9634951a0f9064fbff4e253`；source/native文本字节保持。旧 `native-expression-preview.json` 是此前诊断，不冒充当前qualified Provider replay。`clean-plate-capability/`保存新一轮独立mapping、Parent裁决与当前声音能力报告；不是媒体QA。共享单参考工程的exact Harness见 `.agent/harness/runs/jieshi-single-reference-20261013-r1/receipt.json`，实际状态以receipt为准。

声音实测使用旧原S01 attempt09 bytes做能力探针，未重分类其质量，未改旧MP4/receipt；Whisper的 `零燕請在終點站下車` 不等于原姓名正确，也不证明0.1–2.7s或完整听音。新的原S01尚无MP4，新的per-shot Gate、handoff、剪辑/render、human听看全部 `NOT_EVALUATED`。
