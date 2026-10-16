---
record_kind: architecture_implementation
topic_id: reusable-reference-control-preview
learning_eligibility: ineligible
---

# Reference Control Audit And Preview

Date: 2026-10-17

## Current Generic Control Capability

用户明确纠正目标为跨项目、跨镜头通用能力。此前 `473ed99` 的模式/参考预览和 `c8fefdd` 的单镜离线表达修订不足以证明逐目标控制契约；本轮在原共享 owners 内补齐输入声明、编译拒绝和逐目标投影，没有新增故事分支、控制目标清单、选路器、timeline、状态库或 renderer。旧付费单元与失败镜不延续，本轮视频/图片/音频 Provider POST 均0，没有读取凭据或改变真实 Production。

源码发布 `0fc8c05e7fd7c521047c11f162dcd221b6f5f8cf`，base `c8fefddec979f83ef5dd6b9e7056ae273021b4d8`。本节为当前工程工作；下方原审计、发布证据、媒体比较方案及计数保留为先前 checkpoint 历史，不构成本轮新许可或媒体质量证明。

### Confirmed Gaps And Shared Repair

- 原 `_expressions` 无条件从 `intent_paths` 派生 native text，同一整段 progression 会覆盖各目标独立片段，无法保留作者要求的具体动作时限。新 `RequirementExpression.input_control` 保留原 QA profile 的 authored fragments，`GenerationRecipe` 重开完整 inventory 并拒绝改写后重新封存的片段；legacy 字节/hash/派生行为保持。
- 原报告用固定六类控制描述代替逐项目标，还使用不存在的 `motion_intent` / `subject_endpoint` 路径。现按完整 recipe 输出 `objectives`，真实路径为 `motion_envelope`、`pacing`、`subject_action.endpoint`；固定部分明确为模式概览，不计目标覆盖。
- 新 `generation-input-control/1` 区分 prompt/reference guidance、first/last frame、native output。参考 duty 保留角色、id、SHA、显式 owner、用途及 exact scope；同一 common compiler 的纯 helper 校验声明，复用原 `PROMPT_EXPRESSION_UNSUPPORTED` 和目标 ID，不添加第二执行检查链。只要一项目标启用映射，全部 raw 非 diagnostic 目标须映射；缺片段、缺 scope、错 role/SHA/owner、端点不符或冒充独立人物输入均拒绝，不自动换模式或补原文。
- 新字段无需伪造 semantic marker；QA 封存 owner 对 opted-in inventory 解析 typed shape 与完整 unique IDs，未知机制/缺 scope 在持久化前拒绝。语义必要性、QA verdict、event measurement 与最终 timing 继续归原 owners；输入声明不自动产生语义或质量 PASS。
- `independent_identity=true` 必须有 identity owner；不同 binding/owner 复用同 SHA 不能宣称独立身份证据，同一参考供多个目标复用合法。不去重或改索引。白模只认明确 duty 与实际图像/视频绑定；静态布局图不替代动态视频，普通 video 不推断为白模，声明不代逐镜制作/观察/验收。
- Reporter 复用上述问题码，完整投影原验收要求、native fragments、参考职责、native path、原 Router assessments 与能力限制。未编译时保留 selected candidate 目标、失败 ID 及 `AUTHORED_NOT_COMPILED`，不编造 route/参数。另一个 RED 复现同 id/SHA 同时用于首尾帧时职责会串绑两个索引，现以 canonical native role 分开关联。

输入覆盖仅 `EXPRESSED_INPUT_ONLY` / `UNSUPPORTED_INPUT` / `NOT_EVALUATED`；所有模型质量与 human 验收均仍 `NOT_EVALUATED`。这些是可复现工程缺口，不是旧媒体人物缺失、手部幽影或动作落点失败的受控根因结论。没有新增自动理解目标、精确事件定时、区域 mask、模型服从保证或白模合格认证。Planner/Router 仍只按原候选/能力选择，未把词法校验说成自动选出质量最优模型。

### Transferable Offline Evidence

新 core 测试22项、report 测试25项通过。覆盖合法/非法 schema、unmarked QA seal、完整目标 inventory、missing fragment、错角色/id/SHA/owner、相同字节冒充独立人物、同 binding 复用、端点职责、静态/动态白模职责、旧 hash、改写片段、未编译报告和 JSON-safe preview。

六个临时项目沿正常 loader → Planner → Router → actual Provider compiler → execution binding prepare：Robot抬臂/atrium、Courier放包裹/station platform、Scientist转向窗/narrow cabin，各走 H3 Max 与 Seedance。每例独立保留 action-deadline、main-identity、aux-identity、space-layout、native-duration 五项目标。Seedance 实际选择 `doubao-seedance-2-0-fast-260128`，H3 为 `MiniMax-H3-Max`，六例均 `reference_to_video`；缺原生动作句时只返回 `action-deadline` unsupported，不生成 binding。临时 QA 激活归 canonical committer，没有真实项目或 video_generation attempt。

这些是占位 PNG 的工程 fixture，main/aux 是同一 Character 的两份身份参考，不能称为两个人物质量或独立模型尝试；六例没有真实白模制作或媒体质量证据。H3 Max / Seedance 2.0 / 2.5 的 first、first+last、reference_video 三路线另由既有 actual adapter resolver/native-parameter 9格矩阵验证，不能把该矩阵冒充每格都走过完整 Planner 或真实模型。

可审阅预览：`runs/reference-input-contract-preview-20261017-001/preview.md`；六份 JSON 及各 SHA 见同目录 `summary.json`。只存只读报告，不产生第二 Production state。完整共享使用方法归 [Per-Objective Input Contract](../canvas-production-harness.md#per-objective-input-contract)，官方互斥约束和社区正反例范围见本记录原审计及 [research](../research/2026-10-17-h3-action-timing-reflection-repair.md)。没有把本地 H3 社区经验升级为 H3 Max CN 或 Seedance 保证。

### Current Verification And Publication

源码 exact-range Harness：`.agent/harness/runs/generation-input-control-20261017-r1/receipt.json`，17项全部 PASS；源码发布点重验 integrity、fresh、complete_completion_proof、scope_worktree_clean 及隔离 workspace cleanup/stability 全 true。Architecture Gate 为0 error / 0 warning；Provider-neutral、原文保留、声音选路、QA review、输出回归及历史/恢复边界均实际执行。

feedback suite 523 PASS / 1 skip：隔离 checkout 不含历史 run archive，skip 明示该原因，self-contained fixture 仍执行；不将它计作当前真实媒体历史重验。Provider suite 975 PASS / 23 serializer warnings，warnings 来自预算/配额等负测构造的未类型化 dict，未屏蔽或改变其拒绝断言。其他 suite 结果保留在同一 receipt/JUnit，不把重复执行或测试数量当独立媒体证据。

Risk Gate：对上述 exact source candidate 为 `NATIVE_REVIEW_NOT_REQUIRED`。新增的是封存输入声明、纯校验及只读投影，失败在 submit 前关闭；许可、凭据、预算、lifecycle 和 QA acceptance 不变。normal/boundary/failure、完整 loader/Planner/compiler 路径和 legacy replay 已覆盖，没有剩余关键越权/难恢复状态损坏路径或重大未验证运行语义。模型理解/质量未知被明确保留为 NOT_EVALUATED，不是额外代码审查能够代签的缺证。Parent 自审裁决；前期只读调查和 Product review tests 都不冒充独立最终审查或真实验收。

源码已 push 到 origin/main，`ls-remote` 核验 exact SHA 为 `0fc8c05e7fd7c521047c11f162dcd221b6f5f8cf`。文档 checkpoint receipt：`.agent/harness/runs/generation-input-control-record-20261017-r1/receipt.json`；文档 publication 以该 receipt 和 Git remote SHA 为准。foreign files 的 bytes 及原 staged binary diff SHA 均与任务前基线一致；只提交本任务 owned paths，没有前台 RAG rebuild 或全局 memory 更新。

### Remaining Empirical Decision

工程验证、真实模型质量、单镜/连续镜、完整故事与 human 1.0x 验收分别计。旧失败 S01 的 STOP 与无 accepted state 不因本次代码变化解除；本轮不继续其离线修订、不挪用旧消费或未用臂。

下一最小质量单元建议从两个不同项目的合格镜头各比较首帧与全模态参考，共最多4条、零重抽，先固定一个已有 Provider 以减少混杂；它仍不能证明跨 Provider 普遍质量。新单元须先选定真实素材、逐镜白模或 exact-mode 有据例外、原目标和采用窗，准备完整 native preview，再集中取得当前有限 submit/upper-bound/egress 决定。当前六份 fixture 不可直接转为真实质检素材；没有为该建议创建预算、intent、permit、上传或 paid preview，也不自动授予4次调用。若要比较 Seedance，素材准入须另行满足其当前 exact route，不能默认已通过。

`record-ai-video-session` 本轮更新已有 primary record；`distill-ai-video-learning` 自动评估为 `no_candidate`：没有新增独立、受控真实媒体比较，不把工程 fixture、社区推荐或一份历史失败当通用质量规律。不建立 Learning placeholder，不修改 Skill/Policy/Gate 的经验采纳；本次 workflow 更新只描述已实现且已验证的输入契约。experience 检索返回 stale last-good advisory；本轮没有前台刷新 RAG 或全局 memory 写入。

## Historical Authorized Media Follow-Up

工程发布后，用户批准下述最多2次、零重抽单元。已执行一个此前尚无实证的 H3 Max CN first-frame 条件；15项为6 PASS / 2 FAIL / 7 NOT_EVALUATED，整镜仍STOP、无accepted state或S02提交。第二臂原样重做会重复旧 native `ratio=9:16` 请求，故未消耗；`effective_output.ratio=adaptive` 不能反推native比例。当前媒体、计数、canonical关闭与有界比较以 [Jieshi First-Frame Record](2026-10-13-jieshi-original-s01-s02-candidate.md#current-official-h3-max-first-frame-result--2026-10-17) 为准；下文的Manifest103/Project14、POST0和待授权状态保留为先前工程checkpoint历史。

## Goal And Scope

建设跨项目、跨镜头的控制目标→参考职责→所选路线→exact输入→验收证据说明，沿既有 Canvas、Planner、Router、compiler 与唯一 committer；《界蚀》是现有失败案例，不是特殊分支。前序 10-13 reference preflight 与 10-16 preserved-video spec/plan 只作历史依据，本轮没有把它们当新通用 spec 或付费许可。未新增 Provider、执行链、timeline、renderer、状态库、依赖或 QA 放宽。

## Audit Findings

| Control Goal | Existing Owner / Material Duty | Exact Route And Native Binding | Control Strength And Evidence |
| --- | --- | --- | --- |
| 首帧一致 | approved_keyframe / FIRST_FRAME；原图负责初始视觉 | Planner IMAGE_TO_VIDEO；H3 Max / Seedance `content.role=first_frame` | 显式 API 端点输入；不证明中段动作、人数或镜面合格，仍需 exact 输出逐项 QA |
| 生成末态 | LAST_FRAME 与原末态要求；采用切点另由 composition 声明 | 同一 I2V route 可选 `last_frame` | 生成末端输入，不等于原较早切出帧；不能拿5秒尾帧代3秒采用末态 |
| 人物身份 | Character 的 identity 引用与 Scene 参考分别有 owner | R2V 将 identity/scene 编为 native `reference_image`；exact semantic evidence 与 index 可在报告中对照 | 模型引导；同图多个 alias 不是多份独立人物证据；人数、身份及道具须实测 |
| 动作时序 | generation_intent.subject_action / motion_intent；视频负责明确声明的动作/几何预演 | R2V 实际 `reference_video` + 原文；frame route 不可混该 role | 模型引导；参考时长、生成时长及采用窗口分开；duration 参数不保证动作落点 |
| 空间/摄影 | scene_continuity / camera_intent / camera_endpoint 与原图/白模 | 端点图或 reference_image/video；无额外硬摄影保证 | 轴线、位置、遮挡、人数、反射、机位/焦段、输出画幅均需当前媒体观察 |
| 白模职责 | Director 既有逐镜说明、实测 Registry metadata 与白模 QA | 视频须实际成为 `reference_video`；普通 existing_video 仅是候选，不能推断合格白模 | 必须核对用途、几何、完整动作及采用接点；精确 frame mode 不支持并用视频时逐镜记录能力证据/例外，不静默丢弃 |

MiniMax 当前[官方 V2 API](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)与火山[创建接口](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)、[Seedance 2.5 提示词说明](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh)均区分端点与参考路线；两类 roles 互斥。Seedance reference 模式可在原文指定图片为首尾帧，但仍是参考引导，不获得端点模式约束。本轮公开文档 GET/搜索，无 API POST；MiniMax 国内页首次超时，已核对可访问的国际官方同接口，不外推网页端或第三方网关。

项目已有 H3 Max frame/reference、Seedance 2.0/2.5 frame/reference 能力，并非全部缺失。H3 Max sealed ratio 为 adaptive 才开放 `minimax-h3-max-fl2va-v1`，frame native 不发 ratio；Seedance 2.5 frame native 为 adaptive，R2V 明确 `omni_reference_task_type=reference`，2.0 不发送该值。unsupported 混用或 native hard control 继续沿原 capability/compiler 拒绝，没有为了预览扩大能力。

## Shared Changes

- `canvas_preflight` 保留显式 owner、媒体实测尺寸/时长/fps/帧数；显示 semantic binding 数、SHA/bytes/MIME 唯一组、重复组和原 composition / requested duration。selected route、独立人物证据、白模用途/时序仍为 NOT_EVALUATED；不运行 Router、自动去重或推断所有视频是白模。
- `production.video_reference_controls` 解释既有 PreparedGeneration，关联 requirement semantic evidence、native content 路径/媒体序号、原文 prompt、实际模式/profile/compiler、同字节组及原 QA 全部要求。H3/Seedance scalar native 参数复用实际 payload builder，不读 reference、credential、transport 或签 permit；materialization/admission/quality 仍独立。
- 共享 CLI prepare/prepare_repair 只序列化 immutable 输入、决策、编译、request/binding 与报告，不 deepcopy/序列化运行时 Provider。修复此前 dataclass 默认编码会触及 Provider 并产生不可序列化结果的实际路径，未改变 service 生命周期。
- 原文到媒体编号由既有 `seedance_source_expression._source_media_indices` 唯一推导，Canvas 和 actual compiler 复用；后者仍先做完整 evidence/role/bytes 校验。没有改 /1、/2 原文语义、旧 hash/native顺序，也未删除重复绑定。若未来按 bytes 合并上传，必须另验全部角色及 alias→index→compiler 输出；本轮没有证据支持静默合并。
- 已验证步骤写回 `docs/canvas-production-harness.md`、matrix 和官方 H3 Max provider owner。Harness policy 只把新测试加入既有 generation_feedback suite 与路径映射，没有削弱检查或质量 Gate。

## Current Jieshi Evidence

本节为源码发布前的只读工程基线；后续新授权媒体已由顶部notice取代其“当前”状态。

通过标准 `load_production_project`、`reopen_authoring_input` 及 author validation 重开 current sealed input，再运行只读 preflight：Manifest103 / Project14，source SHA `302772dd855b9ae60dd9b15b5c4319cae63c0b781f20b528c4cdad2adc908980`；10 个 semantic bindings、2 组 unique bytes。9 个 image aliases 均为原 PNG `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`；另一个是 v015 视频 `8b8d1e43d5295109fceda1755bc41e005f6e927ef2b8e657d0328f288aa50e33`，720×1280、24fps、96帧、4000ms。作者职责和每个 owner 保留。原 docs 初版定义直接 resume 当前修订项目被 source-selection guard 正确拒绝；不能把新项目的 position=None 当当前运行状态。

独立重开 CN unit 的 sealed execution-binding 文件 SHA `8b86179a31b94e04b0d9d241816d9dbdee3f5b520b2fa765cac8c4d101410c3b`，新报告给出 native `content[1]`–`content[9]` 为9份同PNG reference_image，`content[10]` 为白模 reference_video；保留 identity/scene/video_reference 各语义证据。resolved hash `821b422b878fa4a105eb4ba55dd417236f7f4c9d7bec1d7adb45d04a51fd662a`。这是历史 exact 请求的解释，不是新选路、调用或 accepted state。

当前 attempt `canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c` 仍 failed / validate；只读核对前后 project.yaml 与 state/manifest.json 的 SHA 未变。原15项、4 PASS/5 FAIL/6 NOT_EVALUATED、缺陈立/手部幽影/3秒动作不到位的 STOP 保留。历史累计17次视频调用、本轮新增视频/图片/音频 POST 均0，S02仍0；未读取凭据、重用额度/permit、激活或重生成。

## Verification

源码 commit `473ed99d7c449689baaf797dffd57546a8d140f2`，base `9917a28d60498fbe823794a29bf072fd25f20a59`。focused aggregate 325 PASS，覆盖新报告17项、Canvas/source 73项及既有 H3 Max/METASO/Seedance/feedback：不同人物、动作与空间；三模型族各首帧/首尾帧/视频参考；重复字节但保留语义职责与原native输入；actual payload 参数/role核对；错 requirement 拒绝、blocked无伪造route、CLI不copy Provider、preflight无runtime/写入及 immutable resume。

完整 exact-range 为17 PASS / 1同run覆盖后的适用性 skip，receipt核验的 integrity / fresh / complete_completion_proof / scope_worktree_clean 全true。完整 exact-range receipt：`.agent/harness/runs/reference-control-preview-20261016-r1/receipt.json`；验证结果、freshness/integrity/completion proof 以该机器证据为准。Architecture scoped check 有既有 Seedance adapter +6 effective LOC 的单一 WARN、0 error；这里只从原 payload 提取同一职责的参数 builder，并保留原 body 顺序/参数和回归，未扩入报告职责或刷新 baseline。

Risk Gate 对上述 exact source candidate 为 `NATIVE_REVIEW_NOT_REQUIRED`：修改只解释既有已选输入、统一纯编号与原 payload 参数，未改变许可、凭据、预算、持久化或状态推进；normal/boundary/failure 与历史 replay 已由 focused 和完整 Harness 覆盖，没有剩余重大运行语义缺口。Parent 自审并裁决；两次只读调查不冒充独立最终审查，旧任务已关闭的 review 历史不重开。

源码已 push 到 origin/main 并用 ls-remote 核验 exact SHA为上述源码 commit。

文档 checkpoint receipt：`.agent/harness/runs/reference-control-record-20261017-r1/receipt.json`。publication 以对应 Git 与 remote main SHA 核对为准；原 AGENTS/playbook 及旧记录/spec/plan/baseline 的 staged/dirty/untracked 工作全部保留。

## Empirical Boundary And Next Unit

以下为获批前的方案与授权边界；后续实际只执行A一次，B的重复性和最新Gate见顶部notice。原先“未执行/需新授权”的时态只适用于该工程checkpoint，不覆盖随后用户“可以”的新有限授权。

本轮完成通用工程表达与多场景离线行为验证，未证明任何模型的通用质量改善、单镜通过、连续镜通过、完整故事交付或 human 1.0x 验收。9份同图、4秒reference/5秒generation/3秒采用分别造成多大影响仍无受控因果结论。

最小下一实证问题是“同一严格目标下，端点输入与视频参考各保留/失去哪类控制”，不是再投旧失败请求碰运气。建议先封存一个最多2次、零重抽的 paired unit：官方 H3 Max CN / MiniMax-H3-Max / 768P / nominal5s；同一原PNG与全部15项/0–3秒采用保持。A为原PNG first_frame、adaptive、无reference视频，必须显式记录所选mode无法并用动态白模的逐镜例外；B为原PNG语义reference与已核验v015 reference_video，显式比例，记录失去端点输入。若保持旧9个语义alias，报告必须原样披露；不能将去重混进模式变量。两臂 binding cardinality 随模式改变且 seed 不受控，因此不是 isolated A/B；即使执行也只给有界观察，不足以证明因果或跨项目质量。

这是可审阅的外部决定方案，未执行、未创建授权/预算/intent/permit。恢复须用户新的有限付费授权，operator 新封存 exact profile/inputs/preview、内部 upper bound、egress、恢复 grant及当前剩余计数；不沿用已消费单元、预算或用户Key存在。每臂 exact MP4 后先逐项 MCP，FAIL/NOT_EVALUATED 停止 attempt；第二臂只有其独立授权与第一臂known/closed outcome齐备才执行；证据型 NOT_EVALUATED 先补证，不以缺证为第二臂重生理由。工程报告不解除旧S01 STOP。跨项目质量仍需另有当前授权、真实素材及代表性 holdout，不用本工程 fixture 或单《界蚀》结果代替。

## Record And Learning

`record-ai-video-session` 记录为共享工程工作，不是新媒体实验。`distill-ai-video-learning` 自动评估为 no_candidate：experience 检索及当前源码复核显示历史 Alice参考/编码比较、旧METASO frame能力和当前《界蚀》失败属于不同边界；没有新增可归因模型质量实证，不能把离线用例数量当 independent attempts。未创建 Learning placeholder、修改 Skill/Policy/Gate 的经验采纳或全局 memory。
