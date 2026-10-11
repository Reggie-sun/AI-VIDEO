# Original Canvas Multi-Shot Implementation Plan

Date: 2026-10-12

## Goal And Authorization

用户选择 A：补齐《机魂觉醒》选段所需接入口，然后用 Seedance 2.0 Fast、480p 实际制作供观看。
本计划是 [Reusable Canvas Production Harness spec](../specs/2026-10-11-reusable-canvas-production-harness.md)
的有界补齐，由 Native Codex 串行持有最终契约、实现和验收；不重新启动 Director 创作。

## Scope And Source

选择 `node_dzjqb2reg0`（视频7，怪物悬浮）和 `node_44chrfmntz`（视频2，机甲托举），
顺序来自 `node_v79w4jnbrv` 的实际前五个 occurrence 的父生成来源。
制作两份完整15秒生成单元；保留原修剪节点、具体 resource、clipId 和 sourceRange，
但不把父节点当前 draft 冒充修剪产物的历史输入，不猜 ticks timebase，不声称原裁切复刻。
保留集因补共享能力转为开发案例，不能继续用它自证冻结后的 holdout 泛化。

主体包的 main/auxiliaries 都保留，映射既有 Character reference/IDENTITY，不能丢辅图或当一般场景图。
来源文本 parts、原 slot、每份 resource snapshot 及实际 API 图片序号分别保存。
仅允许引用芯片到 Provider reference expression 的显式技术适配，不增加机位、动作、故事或声音设计。

## Contract Surfaces And Invariants

- Inspect/packet 只读离线；精确声明支持的 subject resource_snapshot 格式，未知格式继续拒绝。
- `post_edit_provenance` 只表达产物来源，不作为生成 reference、故事顺序或已证明历史输入。
- 来源保持与已批准 Shot、实际 image bindings 和 native prompt 机械核对；不能只有保存原文却提交扩写版。
- typed continuity 经现有 sequence owner 重新打开 exact accepted predecessor；不新增 accepted-state owner。
  本选段显式使用新的 `ContinuityTransitionPolicy/3` source-grounded identity/style hard cut：
  只封存双方 approved Shot 原文/引用支持的非空状态子集，缺少的维度表示无承接要求，
  不制造十维事实或 sentinel。既有 v2 完整十维与 FULL_CONTINUITY 路径保持原约束。
- 原文表达与跨镜状态事实分开。允许原引用表达其已有身份/静态外观；动态状态必须有原文表达，
  不能用任意 reference 覆盖所有 intent paths，也不能把封存 hash 或内部字段拼入模型文本。
- 新的原文连续性编译入口必须在 common compiler 重验 exact selected compiler/grammar、
  requirement、bound request 和 owner-issued opening evidence。旧 standalone guard 保留，
  v4 完整创作、voice、未表达 rich intent、错误/伪造/陈旧 lineage 仍拒绝。
- Registry、Manifest、ProductionStateCommitter、ResolvedTimeline、HyperFrames 及 paid/egress/permit owners 不变。
- 每镜 exact MP4 显式 MCP Gate；required FAIL/NOT_EVALUATED 不推进；全片正常速度听看另行验收。

## Ownership And Compatibility

当前 `main`，保留本次开始时13条 paused dirty/untracked 工作，不编辑、stage 或夹带。
本轮目标是 clean source-inspection/sequence-packet、Seedance source compilation 及其 focused tests，
新 helper 按职责拆分；不修改 paused `canvas_production.py`、recovery、spec、旧 plan 或 baseline。
既有格式和 standalone 单镜保持兼容；只在显式选中、精确支持的来源形状启用新增能力。

## Major Milestones

### Milestone 1: Preserve Subject And Edited-Source Facts

**Files:** `scripts/canvas_production_source.py`、`scripts/canvas_sequence_packet.py`、
新的 focused source helper、`tests/test_canvas_production_source.py`、`tests/test_canvas_sequence_packet.py`。

**Contract:** 支持含 main/auxiliary `resource_snapshot` 的主体，保留分组与 provenance；
芯片只能绑定 exact declared slot，reference edge 集合与 draft 必须一致。
识别合法 post-edit provenance，但未保存生成 draft 的 trim 仍不得直接当生成单元。
选定父生成 pilot 只消费原参考的 exact 当前素材，不宣称重建其上游历史生成。

**Acceptance:** 实际完整来源选择两父生成节点通过 source 能力检查；缺 main、坏辅图、错 slot、
未知 extension、非法/循环 post-edit 边、错误资源身份均有明确拒绝，原 source bytes 不变。

**Verification:** Canvas source/packet/reference tests；实际原快照无副作用 inspection。

### Milestone 2: Compile Preserved References And Evidence-Bound State

**Files:** `seedance_native_prompt.py`、新 `seedance_source_expression.py`、Shot optional field、
`production_strategy_contracts.ProductionShotMixin` 的 optional field、common `video_compiler.py` 的 explicit grammar validation seam，以及既有 sequence/transition/
intent-routing owners 的显式 v3 投影；新增 focused source/sequence compiler tests。

**Contract:** 原文与技术引用适配分开封存；最终图片序号按 actual native binding 顺序核对，
主/辅图都保留 exact SHA 与 Character owner。状态子集由 Shot 的
`preserved_source_expression` 封存，quote 字面来自原 text，reference 只支持明确绑定的静态身份。
opening 必须有 sequence-issued evidence，closing 必须匹配当前 approved column。
v3 仅用于 `identity_style_carryover` 的 `causal_ellipsis` 叙事切镜，禁止 FULL、连续 take、
v4/voice/conditioned rich intent；原文未描述的 gaze、holder、axis 等不填造作事实。
不能凭调用方提供的 expressed-control 标签或 grammar 字符串绕过重编译。
I2V 与 R2V 的 stack 不同；跨 stack 的 Router seed 只签发当前 accepted predecessor
静态身份子集的 selection expression。它必须绑定 canonical target、当前 snapshot 和 exact bytes，
不能执行；只有已有 sequence owner 物化实际 edge 后才能进入 Production start/submit。

**Acceptance:** 原文连续镜实际到达 canonical Planner/Router/compiler 的准备接缝，
且 native prose 未增加创作内容；tampered source、遗漏辅图、陈旧 opening、跨 Shot、
未表达动态事实、未知 rich intent 均拒绝。测试必须覆盖 common compiler direct-call bypass。

**Verification:** Seedance/source/typed-causal/compiler 与 Canvas planning/handoff 集成 tests；
project Harness、Architecture Gate；在 stable candidate 上按 Risk Gate 判定独立 Kimi review。

### Milestone 3: Bounded Live Reproduction And Review

**Files:** task-owned 新 run 数据、source exports、preflight/paid/media receipts、review 页面及 session record。

**Contract:** exact `doubao-seedance-2-0-fast-260128`、480p、两镜各15秒、原 native audio。
此前5次物理 POST 保留；新单元最多2次 submit，累计上限7，不自动重抽或重用旧 permit。
凭据沿已明确的私密 `.env` supplier，仅驻内存；封存 operator upper bound 不解释为市场价。
完整图片 bytes/角色职责、reference grammar diff、handoff/axis/action/camera、lint、
预算、egress、exact preview、durable intent 和一次 permit 均在新 POST 前核对。

**Acceptance:** 两镜经过逐镜 Gate 和 canonical adoption 后由既有 composition/HyperFrames 形成
exact 可观看片段，完整听看判断怪物身份、场景、悬浮→托举动作和剪接连续性。
若任何真正前提/QA阻断，保留 exact evidence 并停止相应 attempt，不能两次独立调用后假称交接通过。

**Verification:** exact fetched media SHA/probe、project-local video-analysis、正常速度完整播放/人工听看；
代码与记录按 owned paths commit、push `main` 并核验 SHA，分别报告工程与媒体结果。

## Self-Review

### Source Boundary Corrections

独立原生只读审查后，以实际 inspected/imported PNG、canonical authoring/bootstrap、
Planner/common compiler 和 committer start 复现三项边界问题。Binding 创建与 start 前
重开同一封存数据，重验 source prose 和完整图片/metadata；不因调用方重新计算 hashes
接受扩写或漏辅图。Source helper 复用 common compiler 的 native 图片顺序投影，
不签发 opening authority；sequence owner 对 accepted predecessor 的检查保持独占。
subject main/aux 的 material role 必须为 IDENTITY，选中 Character/Scene 仍与当前 artifacts 核对。
现有项目 title-only revision 先解析 current Registry 再验证原引用，输入资产和历史保持不变。
正常请求仍能进入 canonical start；恶意重封请求必须在持久化 attempt 前拒绝。
上述是原计划的失败路径补齐，不新增创作内容、Provider effect 或提交预算。

第二轮只读审查补齐了原文和图片完全正确、但 typed endpoint 或 camera intent 未表达的失败路径。
执行 binding 复用 source compiler 的 endpoint facts/hash 约束和 common compiler 的原有
recipe coverage 算法；当前项目的 opening authority 只由现有 sequence owner 重开，
不另签凭证或建立第二 issuer。构造、canonical start 和实际 pre-submit guard 均拒绝四类
自洽重封请求，并验证拒绝前后 durable state 不变；正常第二镜准备继续通过。
Guard 测试不冒充实际付费 submit，真实 Provider effect 仍待完整工程验证和最终复核后执行。

### Nominal Endpoint Recovery

第一镜已实际返回361帧、视频流15.041667秒；此前封存 `exact_seconds` 要求360帧，
属于本任务配置过严。画布原文只要求15秒，不要求生成原片精确终止在第360帧。
用户随后明确要求修改过严规则。Source-preserving Canvas未明确timing mode时，
Planner默认使用既有 `content_driven` timing need，使标称时长可选择 `nominal_seconds`；
显式 `fixed`、`frame_count` 及legacy非source路径保持原语义。
本选段后续新请求在提交前明确使用既有 `nominal_seconds`；旧请求、hash、paid reservation、
permit、fetch及原失败记录保持不变，不为这一帧重新生成。
Fast 2.0 的能力目录新增 `nominal_seconds` admission，并保留 `exact_seconds`；
两者发送相同整数 `duration=15`，差别仅是落盘后有界末帧验收，不新增 Provider 参数。
旧 exact-only profile 仍以原 bytes/hash 重开；后续请求创建新的 immutable profile，
不改写已提交请求所引用的能力配置。该修订由实际361帧返回及用户放宽普通复刻时长规则支持，
不表示 Provider-wide quality qualification。

旧原片通过 `ProductionStateCommitter.recover_nominal_video_endpoint` 显式准备 inactive candidate。
新增不可变 `VideoNominalEndpointRecovery` 嵌入既有 canonical probe receipt，
绑定 original exact output、request/fetch、完整真实测量 hash、actor、reason及原 exact timing mismatch。
只允许已有 nominal 算法的一至两帧有界额外末帧；既有 exact 请求的严格语义、尺寸/fps/audio及paid链不放宽。
本恢复只支持无conditioned/commercial/approved-endpoint绑定的普通 flexible exact请求；
未知 outcome、其他时长误差或媒体失败拒绝。Probe、provenance与candidate artifacts继续由原owner持久化，
reader/activation/recovery/replay重开同一receipt，没有第二state pointer或独立accepted-state store。
此收据不替代逐镜QA，不自动activation，不授权新的POST；时间线仍独占最终使用帧数与trim。

验证新增probe边界、保留旧hash/bytes、恢复→candidate→recovery→activation→read-only replay
以及零新增Provider调用；适用Harness和stable-candidate Risk Gate覆盖本修订。

覆盖本次 A 的最小接缝及实际观看目标；原 spec 全集、holdout 完整验收不由本小样替代。
没有新增 Provider、上云存储、模型训练、development worktree、第二 timeline 或自动质量接受。
当前主要风险是原文/引用对状态事实的可表达范围和真实模型的身份连续性，
先解决 deterministic 入口，再用有限实测判断；不以程序 PASS 自签成片合格。
