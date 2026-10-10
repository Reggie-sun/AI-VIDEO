---
record_kind: architecture_implementation
topic_id: reusable-canvas-production-harness
learning_eligibility: ineligible
---

# Reusable Canvas Production Harness Implementation

Date: 2026-10-11

## Supersession Notice — Authorized Live Unit

下方“没有新Provider submit/没有已授权媒体单元”描述初始工程checkpoint，现已被
[《美丑》480p输入拒绝记录](2026-10-11-beauty-seedance480-input-rejection.md)部分取代。
用户后续授权后，同一入口已实际提交1次Seedance2.0 R2V；上游HTTP400，canonical `KNOWN_NO_EFFECT`，
没有task ID或MP4，resume为`stop`，零重试。凭据与授权前提已补齐；当前阻断是人物参考被上游拒绝。
工程验证与v2冻结仍有效；AC-2完整生产资格仍PARTIAL，AC-7完整成片/听看仍NOT_EVALUATED，
没有逐镜媒体或最终采用结论。以下初始计数与历史边界保留，不将Provider拒绝变成媒体FAIL。

## Purpose And Completion Boundary

用户授权完成[spec](../superpowers/specs/2026-10-11-reusable-canvas-production-harness.md)，并提供已登录的即梦画布。
本轮实现共享工程入口，完成只读来源取证及离线控制流验证；不是又一个导出包。
工程已发布，完整spec尚未验收：AC-2真实保留集仅验证到source/assets/authoring，AC-7未执行。
没有新Video/Voice Provider媒体submit，没有真实逐镜MCP或用户完整听看验收。
本轮新增的Production状态仅在task-owned隔离source probes/test roots，未改变旧作品的采用或偏差结论。

## Current Runtime Truth

`CanvasProductionService`连接inspection、author/approve/revise、Planner/Router、一步execute、显式MCP evaluate、
accepted-source handoff、voice/native-audio、composition、HyperFrames及exact delivery读回。
六个`canvas_*.py`模块各自保持来源素材、创作、planning、dependency调用、composition和application职责。
Product不import开发scripts；Manifest/Registry/Graph/Timeline/committer/Provider/gates仍由现有owners独占。
source pointer是导演声明，不从resourceId、源prompt、当前节点或scripted PASS推出原平台采用和媒体质量。

新项目默认480像素短边、24fps，保持显式来源aspectRatio；16:9为854×480，9:16为480×854。
未声明比例时640×480；混合或未知格式要求显式delivery_profile，不静默改变构图或换档。
本地PNG导入计算hash/测量值并检查node/resource、containment及no-follow；其他素材走原qualified Registry owners。
源tick timebase、非1 speed/gain、unsupported subject/edge/track不猜译。cross-stack handoff没有implicit fallback。

每个步骤重开canonical状态；未完成显式exact MP4 Gate不validate/activate/推进下一镜，unknown保持STOP。
修改导演数据经现有P5 rebase，未修改的已adopted Shot与历史bytes保留。重验不自动重生成。
native音频从实际accepted source经原owner派生WAV，再进入同一P4/ResolvedTimeline mixer，不direct mux。
旧native-audio target白名单改为现有video-generation Manifest capability，保留Registry/source/budget/graph guards。
无Video Provider的静态含声组合、render exact replay及final-media target读回亦有离线集成证据。

## Source Corpus And Holdout History

来源保存于`runs/reusable-canvas-production-20261011-001/`，均为development evidence。
前两份使用既存exact捕获；另外七份为登录后的只读document snapshot。

| Source | Nodes / edges | Observed gap or boundary |
| --- | --- | --- |
| fanxiang | 94 / 见source-preservation-results.json | 原长杆→空手冲突保持 |
| baidaizi | 296 / 见source-preservation-results.json | 原转场与未验收状态保持 |
| 搜山 | 206 / 103 | 使用/弃用分组不是采用证据，没有显式timeline |
| 校园短片 | 53 / 83 | 三条timeline，tick timebase未证明 |
| 机魂觉醒 | 93 / 118 | subject、非reference edge和audio track字段有unsupported项 |
| PuzzleMystiHAPI | 97 / 221 | 一个missing reference位于其他单元；选中链保留三occurrences |
| 任务编号0924 | 276 / 177 | timeline包含uploaded `6.mp4`且缺generation draft，完整链明确BLOCKED |
| STORMII 复刻 | 12 / 11 | 新v2 holdout；selected unit可检查，角色/动作reference职责须导演核对 |
| 美丑 | 113 / 308 | 新v2 holdout；15-occurrence timeline可检查，其他未选单元有不支持part/slot mismatch |

`source-preservation-results.json`逐份重开并断言完整source_snapshot与输入JSON相等，保留所有data/parts/slots/
参数/引用/版本/关系；并不证明全部media bytes已获取、输出版本被采用或原画布质量好。

`corpus-allocation-v1.json`、`shared-freeze-v1.json`保留初始5 development + 2 holdout分配。
v1冻结hash为`2860573f2363287ca00f0f0177dac0592d2a86a5988896e006146279357f3b05`。
默认尺寸会将16:9改成4:3的问题在Parent复核发现并修复，因此两份已读取holdout转为development，不能再算盲测。
`corpus.json` allocation_version=2在读取前固定另外两份holdout，没有持续换样本求PASS。
v2 freeze hash为`3f352ccf79b113705a3681b50fe58a442e95d53716fdf8bc7ded947876fc1a27`。
新增holds之后没有共享source、authoring、planning、execution或acceptance语义改动；本记录/status更新属于非语义收尾。

两个新holdout各用同一data-only probe进入`from_inspection -> author -> bundle.bootstrap -> strict reader -> position`，
Source intent原文不变，默认854×480，无故事分支或Provider effects。
另从已观察的resource response只读获取`download_url`返回PNG：STORM1张、美丑3张；signed URL/headers不进record或repo。
同一PNG选择接口实际测量并导入隔离Registry，结果见`holdout-source-assets-results-v2.json`：
STORM Registry `e79327109f667b0c9a40e2a94c58fe93203c7b25cd09dff705073933f500c29a`，
美丑Registry `d7219e6686262c440addb3745323ed805a72075824ba215be2b0ffc1e32c9d46`。
平台download transport和本地测量是两层事实；不声明release license、采用版本、完整reference ownership或Generation资格。
机械source mapping不等于approved Director coverage；真实创作/后续媒体仍须既有Director/preflight/gates。

## Verification And Review Decision

工程commit：`a4eb0939a57daa370ecace209108a2fafeafdc43`，remote main已核验同SHA。
其tree `3a87d674553b46cfd4c52c0d0f460481f78bbb8c`对应exact staged candidate。
Receipt：`.agent/harness/runs/reusable-canvas-production-20261011-engineering-v2/receipt.json`。
11个policy checks全部通过；canvas107、composition/audio1000、voice47、Harness275、agent invariants44、
runtime Skill boundary2，共1475 tests通过，3项显式live-renderer tests跳过。
`make harness-receipt`返回integrity/fresh/snapshot_matches/complete_completion_proof全部true。
跳过项分别是P4 raw audio/caption、P4 production audio/caption及Task6 live-render state gates；不作为actual renderer证明。
test runner/Provider/MCP observation是scripted seam，真实ffmpeg decode/提取仅证明技术bytes/音频事实，不签剧情/自然度/听感。

初轮engineering-v1 receipt为FAILED：新增check漏登full_tests reverse coverage catalog。
补齐catalog后原guard测试通过，再完整验证v2；失败receipt与真实历史未删除，未放宽AC或Gate。

按SUBAGENTS Risk Gate在v2 tests/Harness之后作`KIMI_REVIEW_NOT_REQUIRED`，
decision与exact snapshot在`implementation-review-risk-v2.json`。用户未要求该snapshot的Kimi review；
Parent未发现具体critical credential/cross-project authority/unrecoverable corruption path。
新caller不直接写state或发transport；canonical exact route/budget/permit/unknown/containment checks保持。
剩余真实素材职责、Provider及人工观看缺口是显式阻断的资格/验收前提，代码review不能代供这些证据。
tests PASS不是不触发理由，实际owner边界及failure/replay/局部rebase证据才是依据。

受管Kimi先前做read-only跨模块mapping：invocation `ca1aca9f-8601-4c91-a369-fb928cbda838`，
qualified deep route `4f2d5dc8-4234-4665-b382-e82f1ad6cc00`，canonical receipt已核验PARSED/exit0。
封存manifest `6c5c34b3-967d-4136-923e-e78789416eb7`，Source bytes核验并release后才修改原owners。
它不是final implementation review或media验收。Native worker仅写source inspector/tests及静态render测试；Parent拥有集成/裁决。
CodeGraph关系和AOCI仅advisory；AOCI index stale/不完整attestation没有作为当前实现证明。

## Acceptance Assessment

| Criterion | Status and actual boundary |
| --- | --- |
| AC-1 | 来源metadata忠实性PASS；全量输出bytes/采用映射仍PARTIAL |
| AC-2 | PARTIAL：冻结后的两份真实来源/实际PNG/authoring同入口；完整生产资格未验证 |
| AC-3 | 离线PASS：real canonical accepted-source的直接/C2/换场seams；未声称真实影片连续性 |
| AC-4 | 离线PASS：两镜生成→显式Gate→采用→composition→scripted render→exact delivery |
| AC-5 | 离线PASS：restart/replay不重提、unknown STOP、canonical局部失效、未相关adopted Shot与历史bytes保持 |
| AC-6 | PASS所测拒绝路径及真实来源缺口；不把原案例失败封成全局禁止 |
| AC-7 | NOT_EVALUATED：没有新的已授权媒体单元、完整成片或用户听看认可 |

最小后续条件：明确完整短剧情单元的参考职责/实际采用版本，qualify所需素材及exact Provider/model/能力；
封存有限submit count、真实inputs/preview及既有预算/permit后执行，再逐镜MCP和整片用户听看。
画布数量不是当前缺口；不需要继续泛化扩样来替代这些具体事实。

## Record And Learning Outcome

`record-ai-video-session`主动判定recorded；给上一份canvas record添加supersession notice，保留旧失败历史。
`distill-ai-video-learning`评估`no_candidate`：本轮是一个工程实现和来源探查，scripted cases/source文件数量
不是独立真实制作实验；没有达到跨实验admission或改变已有媒体结论，不创建placeholder或改Skill/Policy/Gate。
没有新capture_request_id，不伪造hook ACK；项目RAG未重建，旧advisory索引不证明本记录已被收录。
文档收尾的exact staged receipt入口为`.agent/harness/runs/reusable-canvas-production-20261011-docs/receipt.json`，
最终判定由实际receipt及remote SHA提供，本记录不自签未来publication或整片验收。
