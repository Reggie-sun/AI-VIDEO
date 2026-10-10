# Reusable Canvas Production Harness Implementation Plan

Date: 2026-10-11
Status: Engineering published; mecha480p raw generation succeeded, per-ShotGate blocked by POV failure/evidence gaps; AC-7 not accepted.

## Goal And Scope

落实[spec](../specs/2026-10-11-reusable-canvas-production-harness.md)的可重复多故事生产入口。
当前请求取代 spec 当时的 spec-only 限制，授权工程实现与只读画布取证；不因此授权付费视频生成。
默认 Native Codex 在 current `main` 串行拥有集成与最终裁决，独立 source inspection 单元可委托。

## Authorized Live Continuation

后续用户明确授权 Seedance 480p，确认虚构角色与素材使用权，选择保留原对白/音效、无配乐/字幕。
本次 credential supplier 只读用户指定的 repository `.env` 中 `SEEDANCE_API_KEY`，值不输出、不持久化；
不把当前明确来源例外扩散为新默认。原 Secret Service exact lookup 未得到可用值、零 Provider 请求。

候选 Pilot 为《美丑》原 timeline 的 indices 1–4：醉酒进门→初次揭盖→再次确认→苹果堵嘴，共60秒。
正常导演选择保持原引用职责和剧情；前三段原观察为Seedance2.0，第四段为2.5，不能隐藏此差异。
先封存首段15秒、`doubao-seedance-2-0-260128` / R2V / `480p` / native audio 的最小实测，
仅1次物理 submit，0次自动重抽，bounded polling ≤120次/20分钟；不以此冒充完整 Pilot 或 AC-7。
首段有两个原始摄影段落，先以Director v4核对coverage与原文，再沿现有CanvasProductionService/paid owner执行。
现有operator内部upper bound仅作为守门定额，非市场价/账单；profile与完整授权在POST前单独封存。
首段exact MP4落盘后立即显式project-local video-analysis，完整视觉/声音与逐项Gate未PASS前不提交后镜。
后续连续性、跨model执行和真实renderer必须从实际accepted source准备，不能预填PASS、降为独立镜头或直接mux。

Parent self-review：新授权限于本目标内Seedance480p与用户提供的确切凭据来源；未放宽reference admission、
one-use permit、unknown STOP、canonical写入或真实听看要求。一次最小实测先回答平台是否接收这组虚构人物参考，
随后才评估表演/声音，避免在输入被拒或未验收时扩量。共享运行代码与v2 holdout冻结保持不变。

### First Live Outcome

《美丑》首段通过同一入口完成真实素材Registry、Director批准、完整intent、Router/Compiler、
exact preview、human来源声明、egress admission、budget与durable intent/one-use permit。
实际POST仅1次：`doubao-seedance-2-0-260128`、R2V、15秒、480p、`generate_audio=true`、5张原参考图。
API返回HTTP400 / `InputImageSensitiveContentDetected.PrivacyInformation`；没有task ID或MP4。
canonical paid outcome为`KNOWN_NO_EFFECT`，failure experience已保存，重开返回`stop`；零重试、零后镜提交。
原文720p仅是保留观察值，实际wire为480p。未删角色、换模型、换入口或将拒绝改称质量失败。
完整60秒Pilot、逐镜媒体Gate、renderer与人类听看仍`NOT_EVALUATED`。
来源数量充足；当前阻断为人物参考的上游接收，而非凭据缺失。
细节与最小后续选择见[live record](../../record_for_agent/2026-10-11-beauty-seedance480-input-rejection.md)。

### User-Selected Mecha Continuation

用户明确改用现有机甲画布，保留《美丑》失败。选择《机魂觉醒》`node_fgfrmwy9ss`的完整15秒蚂蚁
脱困单元：围破瓶顺时针循环→受撞后坚持穿叶绕石→一次逃脱并带出同伴。它是原development样本，
不补标holdout、完整机甲影片或30–60秒代表性Pilot。原文无对白，保留原生音效、不新增BGM/字幕。
来源只有一张群体场景参考，不虚构独立Character portrait或精确身份锁；主角动作、视点和逃脱义务仍完整保留。
720×408平台预览WebP以同像素RGB PNG导入Registry，原1920×1088仅为来源观察值，不冒充已取得的原图。

按原画布Fast2.0观察映射选定`doubao-seedance-2-0-fast-260128` / R2V / 15秒 / 480p / native audio，
本新单元只增加1次submit、0自动重抽；《美丑》历史1次不清零，累计上限与实际数均为2。
新immutable operator profile、授权、preview、egress、durable intent和permit独立封存；未查市场价/账单。
受管独立concept审查指出POV/双重逃脱等歧义，Parent修正为字面主角眼睛视点、只在末段脱圈，
补齐全程顺时针与动作/分镜/音效检查。补充复核因`STRUCTURED_OUTPUT_EXHAUSTED`没有可采纳报告，
不冒称新bytes已独立通过；原意见逐项裁决、结构与正常compiler检查实际通过。

实际POST一次被接收，同task经7次成功状态GET及1次fetch前重查落盘原MP4。
实测15.104秒、864×496、24fps、H264/AAC。直接逐镜MCP抽31帧，canonical bridge另分析同bytes并保存experience。
第5/10秒可见主角完整背部，POV明确FAIL；声音/连续运动的未取证部分保持NOT_EVALUATED。
canonical诊断为`EVIDENCE_GAP + QUALITY_FAILURE`；validate实际拒绝、Manifest未变，未activate/render或提交后镜。
durable next action仍为`validate`，是被Gate阻断的状态，不伪造terminal failed/已abandon。

### Live QA Client Repair

实测复现`ProjectAnalysisSession`对Python symlink使用`resolve()`后绕过配置venv、找不到`mcp`SDK。
修复只保留配置executable的absolute调用路径，仍strict验证目标存在；没有新增依赖/解释器fallback或改QA标准。
回归先失败后通过，相关suite31项通过，随后同一MP4的真实MCP/feedback持久化与无副作用replay通过。
两次本地poll客户端缺transport、fetch后辅助JSON序列化失败分别记录；均从canonical状态重开，未重复POST/fetch。
当前共享QA调用修复独立于原v2 source/authoring byte-proof；旧冻结和receipt保存，未补签保留集完整生产资格。

剩余先走`EVIDENCE_REPAIR_FIRST`：取得同bytes的声音与连续运动证据，再为已知POV失败设计有明确变量的
有限repair，经原history/recovery/planning/paid owners执行；不能用新目录或改名隐藏旧失败、清零次数。
AC-7仍需真正holdout完整单元、canonical final render和用户完整听看认可。详见
[current media record](../../record_for_agent/2026-10-11-mecha-ant-seedance480-canvas.md)。

用户随后完整声音核对回复“音效符合要求，无配乐或对白”，已绑定exact MP4保存为独立`HUMAN_AUDIO`证据。
此human observation补齐声音反馈，不改写较早analyzer source中的NOT_EVALUATED，也不代签视觉、adoption或最终验收。

## Current Evidence

工程commit `a4eb0939a57daa370ecace209108a2fafeafdc43`已push到main并核对远端SHA。
exact staged engineering receipt为`.agent/harness/runs/reusable-canvas-production-20261011-engineering-v2/receipt.json`：
全部11个policy checks通过、1475 tests通过、3个显式live-renderer tests跳过；fresh receipt核验通过。
初轮coverage catalog缺项已修复，失败receipt保留；没有降低验证或媒体验收规则。

以下初始样本分配为历史v1。默认480p修复为保持显式来源比例后，原两份holdout转为development；
v2在读取前固定`STORMII 复刻`和《美丑》为新holdout。共享代码/语义冻结后没有再改动。
两份新来源通过同一入口完成inspection、实际PNG选择/Registry、authoring与严格重开；
完整Reference ownership、Generation、连续性与声画交付仍未在这些真实来源上qualify，AC-2为PARTIAL。
详见[record](../../record_for_agent/2026-10-11-reusable-canvas-production-harness.md)。

`runs/reusable-canvas-production-20261011-001/corpus.json`登记分配。
现有开发样本为反向之地和白带子；新增开发样本为搜山、校园短片和机魂觉醒。
`PuzzleMystiHAPI`、任务编号0924只登记列表身份，冻结前禁止详细提取；同作品不同版本不计独立样本。
样本分配不证明代表性，制作特征、完整性与用户评价须分别取证。

三份新 `*-document.json` 已通过登录后的画布只读 `getSnapshot()` 保存：
搜山206 nodes/103 edges，校园53 nodes/83 edges，机魂93 nodes。
搜山存在使用/弃用分组但没有显式timeline；校园存在三条timeline；机魂存在独立audio track和subject引用。
来源已保存不表示所有media bytes、采用版本或生成历史已保存。
现有 canvas focused suite 本轮57项通过，只证明当前准备/只读交接行为。

## Contract Surfaces And Owners

| Surface | Owner and change boundary |
| --- | --- |
| 来源与显式选择检查 | 新 `scripts/canvas_production_source.py`，纯只读；复用现有 packet，不推断故事顺序或采用版本 |
| 可审查创作 bundle | 新 application authoring helper，以既有 Production artifact types 创建/seal；不新增Production schema |
| 同一流程入口 | 新 `src/ai_video/canvas_production.py` application service；调用既有 Planner/Router/Generation/sequence/composition APIs |
| durable state与恢复 | 保持 `ProductionStateCommitter` 和 Manifest 独占；workflow只从canonical reader重开 |
| 连续性 | 保持 `planning/sequence_continuity.py` / `_sequence_source.py`；拒绝来源原文代替真实accepted output |
| 时序、音轨、渲染 | 保持 CompositionSpec / ResolvedTimeline / HyperFrames；unsupported source speed或音轨设置显式阻断 |
| 验证与证明边界 | 新 source/workflow tests及现有生成、连续性、composition suites；开发Harness不代签媒体PASS |

开发脚本不能成为Product runtime的反向依赖：source adapter输出资料，application service消费既有typed artifacts
及显式导演决定；source import、authoring、execution、adoption保持独立事实。
Configured Provider、evaluator和renderer使用现有注入seam，不引入新插件系统或故事专属运行脚本。

## Invariants And Compatibility

不变更Legacy CLI；不增加第二timeline、Registry、Manifest、resolver或committer。
原prompt/parts/slot/参数/输出版本/occurrence与adaptation分开；非支持类型以定位信息阻断。
480p是新生成默认，旧720p仅观察值；不换模型或静默升档。
每个执行步骤重开真实持久状态，完成副作用不重放；unknown保持STOP，不remint、不blind retry。
真实末态/媒体Gate不由parser、score、ASR或scripted Provider产生。
更换输入的影响由canonical dependency owner推导，重验不授权重新生成。

## Major Milestones

### M0: Source Qualification And Fixed Corpus

保存少量完整开发来源，登记生成/引用/音轨/版本/顺序能力；缺media bytes、采用评价与未支持字段逐项报告。
原始全图保持immutable，只缓存相同hash来源。需要人工选链时呈现候选，不按坐标/名称猜测。
保留集冻结后才开详细数据；若共享语义为其修改则转为开发样本并如实记录。

### M1: Faithful Inspection And Authoring

Create `scripts/canvas_production_source.py` and `tests/test_canvas_production_source.py`.
检查显式来源、节点/边/slot身份、输出版本与timeline occurrence；展示missing/unsupported，MD/HTML仅为资料。
source inspection无网络、提交或Production写入。准备与authoring消费完整source并保留原文/适配差异，
existing artifact identity/hash由helper计算，不要求用户补造。
创作歧义与实际选用仍由导演数据表达，不能由parser封为已批准事实。

### M2: Reusable Canonical Workflow

Create `src/ai_video/canvas_production.py` and focused workflow tests.
同一application入口接通author/prepare/execute/handoff/compose/deliver；显式runtime注入复用既有Provider配置。
逐镜从canonical Project/Manifest/Registry重开，Planner/Router独占请求和能力决定。
source边界只在前镜exact MP4与既有Gate、adoption证据齐全后materialize。
重启通过现有resume action裁决，不用聊天状态；unknown返回明确停点。
composition与native source audio衔接既有owners，exact render和完整听看采用分别报告。

### M3: Executable Integration And Holdouts

新增scripted离线集成，通过实际committer/reader/sealed Planner/Router执行；覆盖直接承接、换场、
错序、陈旧输出、缺证、非法释放、unknown与重复启动，以及含声音的composition。
从canonical graph验证局部依赖失效，历史bytes及不相关项目保持。
冻结共享代码/规则hash后读取两份保留画布；同格式新故事只填数据和正常导演决定，不修改共享代码。
任一不足按导入、流程、能力或质量分类，不伪造AC通过。

### M4: Publication And Separate Media Acceptance

同步操作说明、matrix、baseline与精确Harness路由；运行完整changed-path checks与fresh receipt。
在稳定candidate按Risk Gate判断是否需要唯一受管read-only adversarial review，Parent裁决。
record-ai-video-session记录实际证据，distill-ai-video-learning评估，无合格独立实验则no_candidate。
仅owned paths commit、push main、核对远端SHA。
AC-7继续要求后续明确的Provider/inputs/有限submit授权与用户完整听看；未执行只能报告工程与制作证据分开。

## Verification

Source unit tests要求离线无副作用，原文/slot/输出版本/重复occurrence不丢失，损坏来源可定位。
Workflow integration要求从标准Production loading/execution seam起步，不裸解析造已采用状态。
Focused baseline command:

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_canvas_reference_packet.py tests/test_canvas_sequence_packet.py tests/test_canvas_sequence_handoff.py -q
```

最终使用仓库`.venv`执行`make harness-inspect`、nonempty exact staged `make harness-verify`与`make harness-receipt`。
actual renderer/Gate/听看不可用时对应项为NOT_EVALUATED，不能从离线PASS外推。

## Self-Review

AC-1/6对应M0/M1，AC-3/4/5对应M2/M3，AC-2对应冻结后的独立保留集，AC-7对应M4单独媒体验收。
source与Production ownership分离；无故事专属实现、自动副作用重放、内部identity手工补造要求或第二状态源。
真实调用预算和未支持节点仍显式；sample capture与工程测试不会改写旧作品偏差/采用结论。
