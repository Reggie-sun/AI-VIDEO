---
record_kind: architecture_implementation
topic_id: continuous-canvas-preparation
learning_eligibility: ineligible
---

# Continuous Canvas Workflow Extraction

## Supersession Notice — 2026-10-11 Implementation

下方Proposed/spec-only、未写plan/未实施是先前回合的历史状态，已由
[共享production入口的工程实现](2026-10-11-reusable-canvas-production-harness.md)取代。
当前工程commit为`a4eb0939a57daa370ecace209108a2fafeafdc43`；离线整链控制流已验证。
两份新holdout仅完成来源/素材/authoring验证，AC-2仍PARTIAL，AC-7未执行。
旧作品持物、转场和声画偏差、未验收结论均未改写，不从新代码测试推断旧素材通过。

## Generic Scope Correction And Spec — 2026-10-11

用户明确指出目标是通用 Harness，而不是适配两部作品。下方案例的持物冲突、转场及声画未评估状态仍保留，
但仅属于对应素材，不是通用 Harness 必须先修好的全局 blocker。上一轮 preparation/handoff 实现与测试
也不等于完整多故事制作流程已经完成；旧“先补两链所有边界”的建议不再作为新目标的默认推进方式。

本轮按“写一个specs”仅新增
[Reusable Canvas Production Harness](../superpowers/specs/2026-10-11-reusable-canvas-production-harness.md)，
状态 Proposed/spec-only，未实施、未写 plan、未生成或修改媒体。定义结构化来源与 MD/HTML 投影的区别、
多画布覆盖和保留集、连续性/参考职责、既有 Production owners 的整链衔接、人工听看与默认480p。
五个提取样本加两个保留样本是起步取证规模，不是硬编码数量或泛化保证；新画布仍未提供/读取。
独立新故事仅改项目数据、无需故事专属代码是工程验收；未来真实短片获用户完整听看认可另为制作验收。
旧案例无需重拍，训练模型不属于本 scope；未把规范设计写成模型经验结论。

Parent 重开当前 preparation/handoff/sequence owner 与 contract 文档，CodeGraph 核对后者的
accepted_sequence_source、Project reader、Planner/Router 关系；当前只读交接要求既有 Shot 和真实前序证据。
按 standing delegation 使用受管 Kimi 作现有能力调查，非 spec reviewer；spec 由 Parent self-review。
invocation `9831b93f-2d8f-4f8d-bda9-3e2c47d6a300` 已核验 canonical receipt，deep、exit0、未截断，
实际读三份入口源码及AGENTS。Parent采纳“已有准备/交接不等于完整AV流程”的有限结论；
“缺跨画布合并”超出用户目标，不新增fan-in系统；min尺寸断言也不足以证明“不支持任意宽高比”，不采纳此推论。
未读全库的gap不作为全仓缺失证据；spec明确多画布首先指跨作品复用，而非合并作品。
本轮只改 spec 和本记录，无实现变更，Implementation Review Risk Gate 不触发。
首轮文档检查通过；上述范围澄清后最终 receipt 入口：`.agent/harness/runs/reusable-canvas-spec-20261011-002/receipt.json`，
结果以实际 receipt 为准，不复用旧代码测试冒充本轮新行为验证。

record-ai-video-session 复用本主记录；distill-ai-video-learning 评估 `no_candidate`：本轮为需求边界和
spec，不增加独立制作实验。项目 RAG 返回 stale advisory，未以历史片段代替当前源码，也未前台重建索引。

## Corrective Implementation — 2026-10-10

用户在Team审查后授权继续。下方“代码缺陷尚未修复”是历史checkpoint；本次修复准备器并实现只读handoff，
没有生成/改动视频、上传素材或改变任何真实Production state。默认新准备480p，原720p参数/原声/失败记录保留。

### Source Extraction

`docs/canvas-sequences/fanxiang.json`与`baidaizi.json`保存既定4+8单元原文、引用职责、输出resource指针、
10条边界的逐侧原句/计划开闭状态/继承项/缺口；expected_source_snapshot_sha256绑定完整旧源快照。
Parent逐一重开源快照，验证12单元正文/hash/引用身份/输出指针与保存的evidence_units完全一致。
结果和核验记录在`runs/canvas-sequence-correction-20261010-001/`，旧run不覆盖。

当前6边为ANALYZED_PENDING_SHOT_AUTHORING，3边为BLOCKED_SOURCE_GAPS，1边为BLOCKED_SOURCE_CONFLICT。
6边有明确承接方法，但没有冒充已批准Shot状态列；真实accepted media仍须canonical owner重验。
反向25→26的持杆/空手冲突继续阻断，26→27不能因未提长杆就宣布道具消失。
白带子前两边分别缺终端身份/信号切换说明、深空信号到巨兽世界的切换说明；不补造复位或传送。
后五边原文支持生物实体遮挡与摄影机前冲，明确释放前世界身份，不强求同一物种/场景/光源；
遮挡速度、方向、透光及声音匹配保留为media_checks，不伪装成原文剧情冲突或实际媒体失败。
这些结论来自实际prompt/原timeline；本轮没有连续播放/听辨，resourceId也不是输出字节SHA或timeline variant验收。

### Implementation And Ownership

修复raw/rich混用覆盖原prompt、非法enum组合、carryover丢失、异常JSON traceback；引用chip之间插入文本边界，
防止拼出不存在的连续引文。边界组合规则从`ContinuityTransitionPolicy`抽出共用函数，仍归production唯一owner，
不构造假的Project/Shot/stack/hash来验证准备资料。缺证/冲突分析不会产生planning_arguments。
新`scripts/canvas_sequence_handoff.py`重开source/selection、核验occurrence→当前Shot identity与Storyboard连续顺序，
核对480p尺寸断言，并真实调用既有sequence adapter；采用时source revision与当前revision分别核验。
执行证据不得覆盖边界分类。此入口不自动批准/创建Shot、不提交、不替代Planner/Router/Registry/Manifest或真实验收。

### Verification And Review Boundary

Red阶段8个回归失败已复现；修复后相关49项通过。最终Harness `canvas-sequence-correction-20261010-002`
10项检查全通过：canvas准备/交接54 tests、生产连续性366 tests、Harness275、规则44、runtime boundary2及Architecture Gate。
实际committer/reader fixture覆盖正常交接、Production bytes不变、错序/陈旧身份/冲突/缺证/覆盖参数/分辨率不符，
缺真实source close评价由canonical owner拒绝；fake fixture不证明真实视频可用或连续成片。
首轮Harness `...-001`因新negative fixture选择了更早的QA失败路径而失败；改用缺失close verdict后验证准确拒绝路径，失败receipt保留。

Native `continuity_workflow_review`本次只读提取10边，Parent校正不连续摘录并逐字重验；
独立Kimi核对绑定staged tree `80d91e64ae3b383f0b140890c11887c824cc9c3c`与上述fresh Harness；
invocation `d007df25-15cc-40fc-91e0-8d498dc69d53`，deep/8份实际读取，PARSED/exit0，canonical receipt已核验。
Parent裁决：F-SEQ-1是中间状态测试缺口，补pending状态及handoff拒绝断言；F-SEQ-2裸KeyError已独立Red复现，
最小修复为缺source_shot显式ValueError；F-SEQ-3是有意的owner分层，不复制accepted identity验证，补陈旧采用身份的拒绝测试。
三个findings均non_blocking，没有发现错误accept；第一项所述自动提升会进入adapter的后果并不成立，缺planning_arguments也会先失败。
Kimi没有读取真实链JSON或fixture内部，不将其报告扩称源画布/真实媒体审查；这些由Parent与native提取核对。
主体实现`9501be1`已通过上述完整Harness并push，远端SHA一致；后续仅上述窄拒绝路径、测试和本记录，
按changed-path进行独立final receipt，不重复未改变的366项生产套件。此窄修复由Parent验证，不声称Kimi已审新bytes。
Risk Gate：无新的明确Kimi强制review指令、无关键凭据/authority/durable-state后果；入口read-only且无effect，
focused fixture与canonical回归覆盖主要失败路径，KIMI_REVIEW_NOT_REQUIRED。仍依standing delegation执行一次有界Kimi独立核对，
不增加native reviewer、不把PARSED当验收。Parent拥有最终finding裁决与diff review。
最终收尾验证入口为`.agent/harness/runs/canvas-sequence-correction-20261010-003/receipt.json`，实际状态以该receipt为准。

record-ai-video-session复用本记录；distill-ai-video-learning评估no_candidate：这是确定性提取/集成与工程修复，
不是新增模型质量实验或可归因的token节约证明。RAG stale advisory未作当前事实依据；未等待或强制刷新索引。

## Team Review Correction — 2026-10-10

用户要求独立Team复核commit `a658a7d9411245c8d2b46a3ea9635e643ddba8f1`。本次只读审查代码与原画布，未修复实现、未生成/改动媒体。
原27 tests及Harness通过仍是真实工程事实，但不足以完成“提取共同连续制作方法到Harness”的用户目标：
两份真实packet的10条边界均未编写具体planned open/close/carryover，且没有packet→Production实际consumer。
`next_owner`只是字符串；既有continuity adapter仍拒绝缺少真实accepted source的执行。不能将此入口称为连续工作流已接通。

### Confirmed Findings

- 制作证据：反向第25组小龙开场、末段都握长杆；第26组却写“没有拿到任何东西，双手仍然空着”。
  `docs/canvas-continuous-production.md`第34行直接归一为“空手”，遗漏原文矛盾。正确处理是显式标出待决定的状态变化，不能自行改写任一组。
- `canvas_sequence_packet.py`允许raw document混入自洽hash的`generation_nodes`覆盖真实`generationDraft`正文。
  Parent纯内存反例已确认导出替换正文；两份历史实际包未发现被这样篡改。
- `_boundary`仅验证单项enum，不验证canonical组合。现有test fixture把`scene_boundary + identity_style_carryover + scene_reset + []`
  当作正确authoring，实际`ContinuityTransitionPolicy v2`拒绝该组合。Parent亦复现continuous_take+scene_reset被准备器接受。
  这是准备契约缺陷；下游owner仍重验，不是生产授权或媒体验收绕过。
- `selection.boundaries[].required_carryover_dimensions`被静默丢弃，FULL进入既有adapter仍缺必需carryover声明；Parent已复现。
- 非object source JSON `[]`导致AttributeError/raw traceback/exit1，未走CLI的exit2错误封装；Parent通过临时输入复现，无输出文件。

### Scope Limits And Disagreement

白带子8段timeline顺序和clip选择未发现错误，共享素材与480p默认可以保留。
但unit没有保存所选输出resourceId/hash；完整source archive能回查当时指针，不等于packet冻结了输出bytes。
source quote只检子串不能自动证明开头/结尾语义，这属于需人工裁决的证据边界，不能要求字符串校验器冒充导演。
制作与架构成员交叉质疑后同意：首要工作是补出具体承接状态并揭示长杆冲突；单加bridge不够。
离线handoff接入既有Storyboard/sequence owner可以是后续窄范围工作，无需扩成无人值守driver。

### Independent Evidence And Parent Adjudication

Native `continuity_workflow_review`（context_search_agent）负责真实源文与连续制作；
`harness_integration_review`（architecture_auditor）负责调用链与canonical语义，两者完成一轮交叉质疑。
受管Kimi reviewer invocation `8a03bb3d-2754-4bf0-94f3-9760bc543cc5`，PARSED、5份实际读取，canonical receipt已核验；
其职责仅代码/测试反例，没有读完整画布，不冒充制作侧审片。Parent分别复现上述实现缺陷并逐字核对道具冲突。
Kimi的CLI与enum findings CONFIRMED；quote位置语义finding按当前spec裁为已知人工判断边界，不声称安全漏洞。
测试通过事实保留，当前用户目标状态修正为INCOMPLETE，代码缺陷尚未修复。无新Spec/Plan、无第二次实现review循环。
record-ai-video-session复用本记录；distill-ai-video-learning为no_candidate，不从审查结论创造模型质量规律。

## Scope And Evidence

用户要求把反向之地与白带子共用方法提入Harness，并明确包含整张画布的连续制作，默认480p。
本轮无Provider视频生成、无媒体改动。只读核对原始画布/正文和现有continuity owner。
反向之地沿用2026-10-09保存件：94节点、272边、39个生成节点，没有生成节点之间的直接reference边；
不将其称为本轮实时刷新。白带子从已登录画布只读获取：296节点、162边、66视频节点、1条8片段timeline。
原节点中的五段框架、六份导演合同、连续性锁定，以及前后生物遮挡/前冲连接都有直接文字证据。

## Implemented Boundary

新增`scripts/canvas_sequence_packet.py`，保留原始parts/参数/slot/node/resource、共享资产、
明确顺序、重复clip身份、timeline trim/speed/volume/mute原数据；新准备默认480p，原720p证据不改。
原rich packet对source_composers重建核对，raw draft对reference边/slot/resource核验。
逐边界复用现有BoundaryKind/ContinuityObligation/CausalEdgeSemantics/CausalStateChange，
full_continuity要求完整十维；两侧原文quote精确匹配，缺边界显式BLOCKED。
不从文字自动提取并签署实际状态，不按画布坐标/标题推断顺序，不另建生产timeline或writer。

共用制作步骤已进入[Continuous Canvas Production](../canvas-continuous-production.md)及现有playbook路由；
保留同空间连续、换场承接、单条内部一镜到底/切镜的区别。现有sequence adapter仍负责accepted source、
实际末态、QA与route，不声称本轮新增完整画布→ProductionProject自动编译或通用连续生成driver。

## Verification

Focused checks：`tests/test_canvas_sequence_packet.py`与`tests/test_canvas_reference_packet.py`共27 passed。
先记录缺模块失败，再实现；真实离线提取白带子8段/13份共享素材/7边界，反向24–27组4段/5份共享素材/3边界。
这些实际selection未新写承接状态，所以10个边界保持BLOCKED_MISSING_AUTHORING，不伪造accepted source。
证据目录：`runs/canvas-sequence-extraction-20261010-001/`，包含两份完整源快照、selection与sequence packet。
工程最终receipt：`.agent/harness/runs/canvas-sequence-extraction-20261010-003/receipt.json`；状态以该实际receipt为准。
前两次Harness在guide原有文档预算上停止，新增说明已压缩为现有行中的链接，未提高预算；失败receipt保留。

受管Kimi只读对照原prompt/原脚本：invocation 43425e2a-8cfc-4f78-b55f-06609fd7a614，
PARSED、六份实际读取、receipt已核验；它的任务封存早于用户强调整图，因此不冒充审过新增sequence实现。
Parent补查整图与现有sequence API，采用共享框架建议；音频由新raw-document入口保留身份，旧rich入口兼容不扩张。
CodeGraph确认旧build_packet的reader/测试关系，当前源码确认sequence adapter是既有唯一typed edge owner。

## Acceptance And Learning

用户此前对两条Seedance效果给出正面反馈：反向之地表情动作清楚，白带子效果可以；
这是人类观看意见，不能覆盖逐项造型/布局等已知偏差，也不把旧反击任务改为完成。
本轮没有重新审听视频，没有媒体质量结论。distill-ai-video-learning评估no_candidate：
沉淀的是用户明确要求的制作组织与确定性准备能力，不是经过受控对照证明的模型规律或token节省比例。
RAG返回stale advisory片段后直接查当前文件，未等待索引刷新。
