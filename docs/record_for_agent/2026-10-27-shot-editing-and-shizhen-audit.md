---
record_kind: architecture_implementation
topic_id: shot-to-shot-editing
learning_eligibility: ineligible
evidence_index_version: "1"
---
# Shot-to-Shot Editing And Shizhen Audit

Date: 2026-10-27

## Outcome And Scope

本次先审计当前 skills/code/tests，再研究两个指定上游仓库，最后在原有导演/时间线/QA seam
实现结构化逐接点决策。《失帧》完成现存主叙事素材的完整抽帧扫描与接点审计，给出有界修复方案；
没有重剪交付新版，没有付费生成/补拍，没有 Product activation 或人工声画验收。此次“改善”是剪辑决策
可表达、可进入成片QA、可被错源/缺证据阻断；不能宣称现有MP4已更有电影感。

证据目录：`docs/research/evidence/2026-10-27-shot-editing-audit/`。`media-identity.json`
绑定三份现存媒体的SHA与实测metadata；10页 contact sheets 覆盖全片每0.5秒及已知接点附近抽帧。
S05 使用时间/PTS，不将标称fps换成源帧。此目录不改写任何旧素材、timeline、report或QA。

## Current Capability Audit

| Surface | Already implemented | Gap and bounded change |
| --- | --- | --- |
| Director / Shot Planning | `open-video` 的 coverage、shot_scale、camera、transition_out；`event-led-timing` 已按完整事件分配时长；已有对白/动作/反应和 source-preserving repair | 原则已存在，不能再造导演系统；补参考页，将原则转成逐接点可观察意图 |
| Continuity | `reference-continuity`、hell-grind 的 axis/eyeline/state/action/space guidance；Canvas前后状态参考 | 单镜合格不证明接缝；新增动作匹配、轴线视线空间、景别反应、节奏揭示及声音桥的独立观察 |
| Timeline / Editing | CompositionSpec 的 video source trim、音轨 start/trim/fades；唯一 `resolve_composition()`→ResolvedTimeline→HyperFrames；cut packet已有源帧/SHA/audio evidence | TransitionSpec 仅表示cut/dissolve，不需扩展特效；新增动机/效果/风险与声桥意图，裁切/混音仍写原spec |
| QA | `junction_review`投影真实Shot边界、隐式hard cut和±1s音轨；exact MP4/report/timeline绑定；原速human/实际声音与动作重复/状态/节奏Gate；Canvas P6 | 原 `edit_reason`自由文本不足；新增typed intent、源入出点绑定、五项观察和补拍反馈；旧记录仍可读 |
| Internal cuts | 现有文档要求审看，但Shot inventory不会发现同一生成片内摄影切镜 | 本次实片人工抽帧扫描结合FFmpeg候选；仍不声称自动语义识别能力 |

当前相关 skill 以 `open-video` 为导演/剪辑owner，`hell-grind`为连续性建议，`drama-authoring`、
`ad-creative`与`ecommerce-ad-workflow`为题材/事实约束，selected-model skills 为提示词表达。
新增方法留在 `open-video/references/shot-to-shot-editing.md`，未安装或调度上游Skill。

## Research And Reuse

完整primary-source研究、exact SHA和许可见 [research](../research/2026-10-27-shot-to-shot-editing-reuse.md)。
`narrative-film-direction@4ee8b42484cb57407f4a7772216aa79e20b0971f`主要是导演方法，
适合吸收场景基准→coverage、轴线/视线与动作切点；文档许可存在路径/署名歧义，本次只综合方法，未复制原文。
`agent-video-editor@8e32c0aff64c445ef1e2b87bc04408a34d68c973`适合吸收按题材判断目的、声音桥和成片检查；
其可执行引擎针对屏幕教程，不能直接验证剧情表演。未引入其依赖、素材库、固定镜长或第二执行链。

## Implementation Boundary

- `ShotEditingIntent` 沿已有 junction owner 定义：题材、切型、原因、效果、出入动作阶段、空间/视线、
  景别/反应、节奏/揭示、风险、声音策略/轨道、补拍需求。不存在统一切镜频率或自动秒数分配。
- Canvas 的 `cut_requirements[].editing_intent` 为向后兼容的可选字段。选择后展开为原有
  FinalOutputRequirements；cut packet同时保留原intent和canonical源帧/音轨/输出SHA。
  改意图会改变goal identity；原有P6和whole-playback human证据要求保留。
- 新 assembly 模板为 `/2`，既有 `/1` 可读；当前Gate不允许旧版本缺字段绕过新要求。
  `source_selection` 复制resolved span并核对源入点、排他出点与素材SHA；多层/多segment不猜主画面。
  J/L/声音桥必须有指定轨道实际跨cut sample，之后仍需听验来源、方向、口型和自然度。
  缺新观察为NOT_EVALUATED；错源/未解析声桥/显式失败/未补足coverage为FAIL。自动模板不会签PASS。
- 没有修改resolver/renderer/state committer，也未宣称支持原source-audio合同禁止的对白覆盖。
  拟议修剪需回原CompositionSpec→resolve→render→新exact-media QA；补拍反馈不授权生成。

## Selected Media And Real Evidence

| Selected bytes | Measured identity / timeline | Current boundary |
| --- | --- | --- |
| `失帧-第一集-S01-S02-S03-去重复扫码-1080p-33.875秒-原声.mp4` | SHA `45fb4e45f815bbe00f42165429dd5f19335e2dbf60ef4206710e09755308f233`；813帧/24fps；主timeline `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/join-S01-S02-S03-006-scan-trim/resolved-timeline.json` | S01源[0,384)，S02源[18,135)，S03源[0,312)；外部切点f384/16.000s与f501/20.875s。实际assembly verdict FAIL，含已见动作不匹配；人工原速听看仍NE |
| `失帧-第一集-S04-接点剪辑修正版-1080p-9.875秒-原声.mp4` | SHA `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`；237帧/24fps；`.../S04-edit-005/resolved-timeline.json` | 用户此前认可保持。当前strict assembly输入拒绝：历史render report中check warning_count=1；保留原报告，不伪造新PASS |
| `失帧-第一集-S05-Seedance2.5-005-接点连续性修复-原声-20秒.mp4` | SHA `89497e155e872792dece88eb44db1e165bf44e0213bf04dc6c43dffe6c34b02b`；481帧；视频20.016667s/容器20.065s，r_frame_rate=60，avg=28860/1201；逐帧PTS见`S05-frame-pts.json` | 烧录字幕明确可见，整体FAIL素材；无S04→S05累计timeline；不把后续UNKNOWN当作此片成功 |

project-local MCP实际调用了video_analyze、video_scene_detect及video_review；结果保存在证据目录。
MCP在threshold0.1仍把三片各报1个scene；S05 review报issues=[]，但画面明确有禁用字幕。
这直接证明该工具返回与heuristic分数不能替代语义QA。独立FFmpeg `select='gt(scene,0.08)',showinfo`
得到候选，再按实际抽帧区分摄影切镜、消失事件和移动误报；未改动MCP实现。
S05的MCP fps=60以及unique-frame数量也不能用于canonical timing，采用ffprobe原始PTS。

## Complete Junction Audit

以下时间均来自选中exact输出或源PTS。24fps成片中显示入镜frame，源窗口采用排他出点。
“保留候选”表示叙事方法合理，不能当作正常速声画PASS。全片声音、呼吸、口型、表演速度与最终节奏
没有本次human实际听看证据，一律NOT_EVALUATED。

| Boundary | Cut reason and observed state | Narrative effect / risk | Executable decision |
| --- | --- | --- | --- |
| S01内部4.541667s/f109 | 双人中景→林序近景，抬眼/回应 | 将关注点转到顾客，不需加转场；对白入点未听验 | 保留当前source[0,109)→[109,163)作baseline；听核触发、完整原句与反应 |
| S01内部6.791667s/f163 | 林序→店员反打 | 接收顾客回应再转包装行动；背景/柜台大体相容，不能仅以反打判过轴 | 保留候选source[109,163)→[163,331)，核对机位工作侧/视线对象与反应起点 |
| S01内部13.791667s/f331 | 店员包装/放物→林序低头反应 | 行动结果→反应；包装动作末态与完整声音须保护 | 保留候选source[163,331)→[331,384)，不为缩时删掉支撑/放稳过程 |
| S01→S02 16.000s/f384 | 林序微笑低头→店员抬眼/继续交易 | 从情绪回应转回交易；不是同一主体运动匹配 | 当前S01源out384，S02源in18，Hard Cut保留候选；原声同窗直切尚未听验 |
| S02内部18.541667s/f445 | 店员正面→柜台侧向手部/扫码准备 | 明确取枪/商品的行动；需保留瓶与枪的相对位置 | 该点对应S02源f79，先核源[18,79)→[79,135)；不得当成多生成一次扫码的理由 |
| S02→S03 20.875s/f501 | f500仍高举扫码枪，f501枪已到台面瓶旁 | 高位→低位跳阶段；去重扫码修复没有自动保证动作连续 | **FAIL；修剪候选见下节**，不能继续称Cut on Action已匹配，也不用dissolve遮盖 |
| S03约24.625s/f591 | 店员在同一机位消失 | 这是叙事事件，非普通摄影切镜；需要观众先认识空间再看见异常 | 保留消失前后完整状态；场景检测候选不能自动当作应删除的jump cut |
| S03内部26.583333s/f638 | 无店员的柜台关系→林序近景看向原位置 | 异常→人物反应，动机成立；前面消失的可读停顿与后面惊疑反应须保留 | 对应S03源f137，保留source[0,137)→[137,312)作baseline，完整声画确认后才调整停顿 |
| 拟议S03→S04 | S03末俯身→S04开头近似姿态继续找人 | 空间相容线索存在，但重复俯身/停顿或对白尚未听核 | 尚无累计timeline；baseline候选S03 out312→S04-edit in0，禁止直接宣称已拼接合格 |
| S04内部3.500s/f84 | 林序俯身寻找→枪/瓶静置插入 | 人不在、物还在；有信息职责，不是空镜补时 | 保留已认可剪法：edit源[0,84)→[84,135)，对应原片前源out84、后源in87；核对POV与道具关系 |
| S04内部5.625s/f135 | 道具插入→林序中景反应 | 证据→困惑、再转向骑手；动作reset风险不能靠插入遮掩 | 保留已认可剪法：edit源[84,135)→[135,237)，原片前out138/后in138；维持手机右手及counter关系 |
| 拟议S04→S05-005 | S04末看画右→S05双人镜骑手位于画右 | 视线引导到对象，换景别有动机；骑手由背景到身旁的省略及声场需交代 | 尚未拼接；候选S04-edit out237→S05 PTS0，原声Hard Cut先作baseline；005整体FAIL不得入合格累计片 |
| S05源PTS3.050s/decoded ordinal73 | 双人镜→林序近景，回答骑手 | 从提问到人物说明；需保护开口前接收反应与完整“不是” | 保留candidate [PTS0,3.05)→[3.05,6.216667)，字幕违例独立阻断 |
| S05源PTS6.216667s/ordinal149 | 林序→骑手反打 | 骑手的疑惑/回答才有切镜价值，不按说话者列表机械切 | 保留candidate→PTS9.216667，核对同侧空间、目光对象与听/说时机 |
| S05源PTS9.216667s/ordinal221 | 骑手→林序近景 | 揭示红围裙店员的信息；怀疑应逐步形成 | 保留candidate→PTS13.05，不将台词字幕当作实际听见/口型证据 |
| S05源PTS13.050s/ordinal313 | 近景→双人较宽镜 | 让指向柜台/店员原位置的动作可读并带骑手反应 | 尾段到视频20.016667s；检查指向动作约16s后是否有冗余停留，只有完整原声/反应明确后才裁尾 |

## Bounded Repair Plan

1. **优先修20.875s接点，仅使用现有素材。** 当前S02源[18,135)、S03源[0,312)。
   候选A将S02排他out改为120（5.000s），S03保持in0：在高举枪动作之前切到低位扫码，明确为有意省略的
   Hard Cut，而不伪称动作匹配；候选B在S02源out120–124范围逐帧找与S03源in0的手/枪方向最相容点。
   此为未执行的源裁切候选，不是新timeline或已改善证据。先核S02源5.0s附近原句/呼吸是否完整；
   截断台词或丢必要动作则拒绝该候选。S03扫码、放瓶、消失与反应完整保留。
2. **声音先保留，再有依据桥接。** 当前各段原声同窗直切，没有J/L轨道。可从现有来源选择连续room tone，
   或在完整原句确实跨视觉切点时使用L-Cut；若S04末 gaze→S05开头骑手声音可提前引出其对象，可考虑J-Cut。
   在获得exact音频源区间与聆听证据前不指定假声学sample、不混入额外配乐、不把同期对白伪装为ambience。
   所有实施须现有source-audio准入、AudioTrackSpec和resolver允许，声桥不是默认修复。
3. **累计版先接S03→已认可S04，再评S04→合格S05。** 对S03末俯身与S04首段比较完整动作与台词，
   决定是否有重复。S04现有两处插入剪法保留，先补齐历史renderer warning的当前证据，不能直接改旧report。
   S05-005含字幕且整体FAIL，仅作覆盖参考；后续UNKNOWN保持停止，不重试、不生成代替它的素材。
4. **补拍反馈只在原素材不足时提出。** 若候选A/B都破坏原句或动作阶段不可接，反馈原Director：
   缺“低位取枪→接近瓶”的可连续覆盖，或能承接当时视线/持物状态的真实反应镜；应保持柜台地理、
   手别/枪瓶状态、原有事件和声场。另一缺口可能是骑手接收林序视线的反应/空间建立。补拍请求不等于
   已授权新尝试，不默认付费重生成，也不能用不相关产品特写或闪切反应蒙混。
5. **复核新片。** 修改原spec后重新resolve/render，按新exact SHA重做每个接点与内部摄影切镜检查，
   用project-local MCP取证，逐项检查动作、空间、景别、揭示及声音，最后原速连续听看。
   不把本次图片审计、测试PASS或历史单镜认可当作新片质量接受。

## Verification And Publication

已先复现旧模板缺决策能力的测试FAIL，再实现；相关正反例覆盖缺意图/旧版本绕过、错源入出点/SHA、
声音桥无实际跨点轨道、显式轴线失败、补拍阻断、未听/抽帧不能PASS。Canvas测试通过真实loaded project、
authoring/QA policy/renderer seam，将intent送入cut packet与P6，缺human proof仍NOT_EVALUATED且replay无副作用。
测试中的renderer/provider/evaluator为受控离线fixture，不证明《失帧》的艺术效果。

当前工作树精准回归132项通过；JUnit与participating source hashes保存在证据目录。工作树治理检查另发现既有AGENTS.md超出14000-byte预算，未改该并行文件。

最终工程receipt及publication结果由本次交付列出；receipt绑定task-only commit range，不能夹带其他窗口dirty。
Parent Risk Gate：本改动只增加可回滚的意图与开发Gate、复用现有P6，未新增durable-state writer；
主要结构/失效路径有可执行验证，人工创作质量不由代码或reviewer签署。故NATIVE_REVIEW_NOT_REQUIRED，Parent自审；
前期只读mapper/inventory不是最终独立review。

Record evaluation=record（共享QA契约与实片失败具持久价值）；learning evaluation=no_candidate：
本次是同一素材链的审计，不是独立多次实片实验或受控改善对照，不升级普遍质量规则。
Skill改动来自用户本次明确的剪辑能力请求，不是将未确认Learning Claim自动ADOPTED。
