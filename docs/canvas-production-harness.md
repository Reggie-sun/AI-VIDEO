# Reusable Canvas Production Harness

## Entry And Data

共用 CLI 为 `scripts.canvas_production`，API 为 `canvas_project_data.open_canvas_project`，执行服务为
`CanvasProductionService`。换故事只换 source、project JSON 与所选素材，不新写故事执行脚本。

```bash
mkdir -p /tmp/canvas-example
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production inspect \
  --data docs/canvas-projects/subject-reference/project.json --project-root /tmp/canvas-example
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production author \
  --data docs/canvas-projects/subject-reference/project.json --project-root /tmp/canvas-example
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production preflight \
  --data docs/canvas-projects/subject-reference/project.json --project-root /tmp/canvas-example
```

`inspect` 保留完整原始快照、版本指针、引用职责、主体主/辅图、timeline 与重复 occurrence，定位缺项。
`author` 无 Production 写入，展示原文、适配文本与 unified diff，并附带全序列 `preflight`。
`preflight` 忽略 `--runtime`，不实例化 Provider、不调用凭据或媒体生成工具；已存在项目时重开 immutable
Director input。它同时列出全部镜头的角色/场景/道具参考职责、exact bytes 与来源、普通状态提取依赖、
generation/composition order、声音表达及 cut requirements，供首镜付费前审核后镜路线。
待替换图片明确标为 authoring placeholder，不能作为 accepted 状态。`REGISTERED_BYTES` 只说明
Registry 中有该记录；synthetic 来源、同模型生成或本地抽帧都不自动证明 Provider admission。
报告中的 `NOT_EVALUATED` 必须由对应 owner 的真实证据补足，不能据此宣称禁止所有中间帧或已经可提交。
未来状态未产生时先核对路线，不要求伪造未来 bytes；若准入只能实测，明确 uncertainty 与有界实验，
不因离线报告齐全而投原失败请求碰运气。
Provider 返回尾帧、原始视频与普通中间 PNG 保持不同输入；改变路线须明确表达差异，不能自动替代。
示例是 development 测试数据：

- [text-reproduction](canvas-projects/text-reproduction/project.json)：原文 T2V、480p、15秒 nominal 输出。
- [subject-reference](canvas-projects/subject-reference/project.json)：主体主/辅图、场景参考、实际中间帧计划。

示例 PNG 无真实人物/动作资格，两个示例不算 holdout。`images` 默认只填
`asset_id/node_id/resource_id/path/usage_license`；入口测量目录内的 PNG 并计算内部 hash/receipt。
已有外部生成图可额外填 `generated_source`：`record_path`（data目录内的生成记录JSON）、
`record_sha256`（记录原bytes）、`tool`（明确声明的generator ToolIdentity）。记录的
`sha256/size_bytes/width/height`必须与实测PNG逐项相符；入口封存原记录和exact copy派生证据，
不接受source_kind标签代替来源。默认仍为imported。来源记录不证明Provider qualification、
human fictional identity attestation或媒体acceptance；这些由各自gate独立检查。
显式Registry元数据修订可在Director原文不变时经 `revise_authoring` 提交，旧snapshot保留。
preserved-source引用重开该派生copy的sealed observation和原record，对齐原snapshot、node/resource、
asset及image事实；不只比较新的receipt标签。后续修订保留原immutable source evidence。
平台 URL 和资源 ID 不等于已验证 bytes。重启读取 canonical Project 指向的 immutable authoring input，
不需要再次下载初始素材；修改输入使用显式 `revise`，状态读取不会批准新数据。
示例 generation raster 使用 Seedance 2.0 的 480p `864x496`；换模型时按已封存 capability
明确适配 raster，不能把不同模型的 480p 当成相同像素契约。

## Preservation And Orders

项目数据可用可选 `videos` 声明本地白模 MP4，字段复用下述 helper 的 selection：
`asset_id/node_id/resource_id/path/usage_license/tool`，可选 `input_artifact_ids`。
源快照必须有对应 video node/resource，Shot 的 `generation.references` 明确填
`{"role":"existing_video","asset_id":"..."}`；preserved-source 对应 `video_reference`。
视频与 PNG 一起导入现有 Registry 2.2，asset ID 不得跨类型重名。视频 path 必须在项目数据目录内，
不接受外链或 symlink。首次导入显式提供 qualified absolute ffprobe，例如：

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production preflight \
  --data /absolute/case/project.json --project-root /absolute/case/production \
  --ffprobe /absolute/qualified/ffprobe
```

API 使用 `open_canvas_project(..., ffprobe_executable=...)`；工具路径由 operator 注入，
不放进项目 JSON。该步骤只运行既有 file-only 本地测量，不调用 Provider、上传、凭据或付费 preview。
已批准项目重开 immutable Registry/authoring evidence，不重新读取或测量原导入目录的 MP4；
新增或替换素材仍显式 `author` / `revise`，不借 resume 批准改变的 bytes。
未声明 `videos` 的历史数据保留原有导入和 hash 行为。

显式新增本地视频参考的既有 helper 为 `canvas_video_assets.prepare_canvas_video_assets`，传入已 inspection 的
packet、`asset_id/node_id/resource_id/path/usage_license/tool`、allowed local root 和 exact absolute
`ffprobe_executable`；`input_artifact_ids` 只填写项目中真实存在的 artifact ID，外部作者源文件的
hash 另存 authoring evidence，不能伪装成 Registry dependency。helper 只准备 exact MP4 与
local-selection/measurement receipt，限制 2–15 秒、整数 FPS、50 MiB、file-only MP4 probe；
不调用 Provider 或写 Production。与当前 Registry 合并时显式保留全部旧记录并使用 Registry 2.2，
经既有 `author` / `revise_authoring` 导入；后续 source-expression 重开 sealed evidence。
原文中新增的 reference slot 必须进入新的 inspected source snapshot，并标明新增职责，不能冒充
原剧本已有素材。普通视频参考使用 `video_reference` / `existing_video`；它不等于 accepted source
或状态交接，不复用后者的资格。Planner/adapter 是否支持、exact native inputs 和全部原 QA 另验。

复刻保留原文 text part、chip slot、主体主图及全部辅图顺序和职责。只按 common compiler 的素材顺序
将 chip 换成 `图片N`。`Shot.intent` 与 `subject_action.progression` 自动生成，已有不同文本直接拒绝；
对白/旁白必须引用原文。`source_grounding` 仍经 source owner 验证，不制造原文未表达的动态事实。
不支持的音频引用或未知素材须明确补齐 supported route，不能删除后继续。
新数据入口封存 `seedance-preserved-source/2`，保留同一 chip 的每次文本出现与 tray-only 普通参考；
同一 selected asset 只形成一次 native input；不同 asset alias 的相同字节不自动合并，见下方控制预览。
重复 slot 的材料或同 asset 的 role/bytes 冲突直接拒绝。
历史 `/1` 的唯一 slot/asset 与 implicit first-frame 限制、hash/serialization 保持。
历史图片的 `type=image/uri/history-material` 参考保留原 descriptor；inspection 提供稳定素材 handle，
不虚构 canvas node 或 reference edge。`images.node_id` 使用该 inventory handle，`resource_id` 保留 URI；
用户只选择实际 PNG，入口计算内部身份。无本地 bytes、损坏 URI/history identity 仍阻断。
原文中的普通文字 `图1`/`图一`/`图片1` 不一定对应 native input 的索引；需要适配时在项目数据
`reference_aliases` 中按 occurrence 填 `[{"label":"图1","slot_id":"原 tray slot"}]`。
入口绑定原 slot 的全部材料，由同一 compiler 重编号并展示 diff，不凭标签猜角色或参考职责。

`direction.shots` / Storyboard 是生成顺序；`composition_order` 是最终 occurrence 的精确排列。
插入例：生成 `A → B → insert`，剪辑 `A → insert → B`。生成依赖仍走 sequence owner；
frame/sample/trim 仍只由 `ResolvedTimeline` 派生。重复节点使用独立 occurrence 和 Shot ID。
未知源 tick timebase 或 speed 不会被猜成执行时间。

## Operator Runtime

Provider、private credential supplier、paid authorizer、routing/decision policy、limits、MCP evaluator 和
HyperFrames toolchain 由当前 qualified operator runtime 注入一次，供所有故事共用。
API：`open_canvas_project(..., committer=..., targets=..., routing_policy=..., decision_policy=...)`。
CLI：`--runtime trusted_operator_module:function` 返回 `committer` 和 service configuration；可提供
`action_arguments(action, service, ordinary_arguments)` 注入 limits/session/adjudicator/toolchain 等对象。
这是共用运行环境接线，不能承载故事执行逻辑、自动扩大预算、换 Provider 或 fallback。
未配置 runtime 时 inspect/author/preflight 可用；prepare/execute 必须补齐当前 canonical runtime。
凭据不得进入项目 JSON、`--arguments` 或 CLI argv，只沿现有 injected supplier。

原声音证据不齐时使用[project-local音频理解工具](audio-understanding.md)补证，默认无网络preview；qualified operator就绪后可在原`evaluate`显式传`understand_audio=true`，观察进入原exact MP4分析证据。它不代selected QA/presentation、精确时序或human听看，缺证不重生成。

## Reference Control Preview

制作前先把控制目标分到已有职责：人物外观归 Character/identity，场景与道具外观归 Scene/原图，
开场/生成末态归显式 first/last frame，动作/空间/摄影预演归经核验的白模；声音沿原音频合同。
一份素材可以承担多项声明职责，但多个 alias 不产生多份独立人物证据。
`preflight.reference_inventory` 保留每份 asset/role/显式 owner，并按 SHA/bytes/MIME 披露相同字节组；
`measurements` 展示参考规格，`requested_duration_seconds` 与原 `composition` 并列。
普通视频仅列为白模候选，职责、逐镜核验、时序对齐及例外仍需作者证据，报告保持 `NOT_EVALUATED`。
不自动去重、重编号、推断白模合格或运行 Router；最终选择以既有 `prepare` 结果为准。

共享 CLI 的 `prepare` / `prepare_repair` 现在输出 JSON-safe 的 `reference_control`；API 调用者可用
`production.video_reference_controls.prepared_generation_report(prepared)` 读取同一投影。
它列出实际 provider/model/profile/capability/mode、原 compiler 结果、semantic evidence 到
`content[N]` / 每种媒体序号的映射、同字节组、exact prompt、参考时长、所选 QA 全部要求及控制限制。
MiniMax H3 Max/METASO 与 Seedance 的 `native_parameters` 复用实际 payload 的标量 builder；
不物化 reference URL、不调用 credential/transport/paid preview、不创建 intent/permit 或 Production state。
其他 adapter 的 native 参数明确 `NOT_EVALUATED`，没有选中 request 时不推测路线。
CLI 只序列化 immutable inputs/decision/compilation/binding，不复制或输出运行时 Provider。
当前失败镜的 STOP 仍生效，不能为查看报告绕过 `prepare` 或自动发起修复。

| Control | Frame Route | Multimodal Reference Route | Required Evidence |
| --- | --- | --- | --- |
| 开场一致 | `content.role=first_frame` 是显式端点输入 | `reference_image` 与提示词是模型引导 | exact 输出开场、人数/身份/道具/构图逐项观察 |
| 生成末态 | 可选 `last_frame` 绑定生成末端 | 末态文字/参考仍为引导 | 生成末端与原采用切点分别核验，不用长片尾帧冒充切出帧 |
| 人物身份 | 由端点图及原文表达，不能同时追加人物 reference | 原图/人物参考保留语义 owner 和 native index | 多人同图不计作独立人像；完整逐镜身份 QA |
| 动作时序 | 原文引导，端点不约束全部中间动作 | 原文 + 实际绑定视频引导 | 起点/极值/接触/结束及采用切点；duration 不证明动作落点 |
| 空间/摄影 | 端点提供布局，摄影仍需实测 | 场景图/白模视频提供引导 | 轴线、人数、遮挡、反射、镜头和画幅分别检查 |

官方 MiniMax H3 Max、Seedance 2.0/2.5 API 的 frame 与 reference roles 互斥。
H3 Max 当前 frame capability 只在 sealed `aspect_ratio=adaptive` profile 中开放，native 不发 ratio；
Seedance 2.5 frame route 发 `ratio=adaptive`，R2V 发 `omni_reference_task_type=reference`。
Seedance 官方允许在 reference 模式的原文中指定某图片为首/尾帧，但这不获得端点模式的约束；
使用已有 `reference_aliases` 绑定原 slot 并展示适配 diff，不凭中文数字猜素材、自动插入新创作要求。
若首帧路线不能同时消费动态白模，必须逐镜记录 exact mode 的能力证据及例外，保留全部原要求；
或经明确选择改用视频参考并接受首帧控制减弱，不能静默删除其中一项。
实测参考长度、标称生成长度与采用窗口分别说明 hold/padding/动作落点，最终 trim/frame/sample/timing
仍归 `ResolvedTimeline`。参数/绑定正确只证明输入，不证明模型服从或验收。

### Per-Objective Input Contract

逐目标的输入映射归已有 selected QA profile 的 `generation_requirements`，不另建目标清单。
每条 `RequirementExpression` 可选 `input_control`（`generation-input-control/1`），沿原
`_expressions` → `GenerationRecipe` → common compiler → execution binding 使用同一份封存数据。
`observable`、`proof`、`measurement`、`tolerance` 及 required IDs 仍由原 QA owner 决定；
`EventTimeWindow` 是输出测量条件，不会自动变成提示词或剪辑时间。

例：动作时限条目沿 `generation_intent.subject_action.progression`，保留作者已经写入 intent/源文的
确切 `native_text`，另声明 `input_control: {"mechanism":"prompt_guidance"}`。
它不会再被整段 progression 覆盖，也不会自动把验收时限追加到原文。参考条目则声明
`mechanism=reference_guidance` 及 `references`：每份 duty 包含 `asset_id`、`asset_sha256`、
现有 semantic `role`、`purpose` 和确切 `scope_text`；必要时包含 `canonical_owner_id`。
先由原 Planner/Router 选择 registered variant，再核对 actual native index 与 scope 原句中的素材指代；
字面匹配只证明表达存在，不证明自然语言语义、人物或事件一定正确。

| Mechanism | Input Obligation | Meaning And Limit |
| --- | --- | --- |
| `prompt_guidance` | 独立 `native_text` 与 generation intent 路径 | 原生文本引导，无精确动作定时保证 |
| `reference_guidance` | 上述文本与 exact duty、scope、role/id/SHA/owner | 实际参考输入；不等于模型服从 |
| `first_frame` / `last_frame` | 一个 opening/closing duty，原 binder 对应端点 role | API 端点输入；不保证中段或较早采用切点 |
| `native_output` | 仅既有 `output_need.*` / `audio_need` 路径 | 原 compiler 校验输出参数，不代表动作时间 |

任一条目启用映射时，全部 raw、非 diagnostic 目标必须逐项映射。缺映射、缺原生片段、
scope 未表达、参考身份或端点角色不符，经原 `PROMPT_EXPRESSION_UNSUPPORTED` 返回目标 ID；
不会自动改模式、补 prompt、删目标或重抽。完整 recipe 投影与新 authored fragments 均须匹配原 QA profile。
legacy profile 无此字段时保留旧 bytes/hash 与投影行为，逐目标输入覆盖明确 `NOT_EVALUATED`，
不能将旧报告整体“绑定成功”升级成逐目标覆盖。

`purpose` 区分 identity、appearance、layout、motion、camera、whitebox、audio、opening、closing。
人物参考声明 `independent_identity=true` 时必须有显式身份 owner；同一 SHA 的不同 binding/owner
不能冒充多份独立身份输入，同一 binding 被多个目标复用合法。只拒绝错误声明，不自动合并 alias 或改编号。
白模 duty 仅核对实际图像/视频绑定；静帧只适用于已说明的静态布局，动态控制仍须视频及逐镜 QA。
普通视频没有 whitebox duty 时不得推断其用途；declared duty 也不证明白模制作、时序或质量已核验。
frame/reference 互斥及逐镜白模例外继续沿现有模型能力和上文/下文 authoring 规则处理。

`reference_control.objectives` 从同一完整 recipe 投影要求、输入片段、机制、duty、native path 与验收要求，
区分输入已表达、输入不支持及未评估；`decision.assessments` 只解释原候选选择。
compiler 失败时仍保留 selected candidate 的目标和失败 ID，片段标为 authored、未编译，不虚构实际 request。
模式概览不计作目标覆盖；所有输入检查和离线 fixture 的模型质量、human 验收仍 `NOT_EVALUATED`。

### Edit-First Temporal Control

最终采用时点偏差首先是制作手段选择问题。先确认源素材是否已经包含要求的状态、动作顺序与可用画面，
再比较裁切、分段变速或现有coverage剪辑与新生成。缺人物、错误动作方向或不存在的末态不能靠变速补造；
变速也必须重验动作自然度、摄影、原有满足项及声音。原生成FAIL和编辑后用途评估分别保留。

上层选择沿 `ProductionPlanningService`，Canvas提供 `prepare_production` → `materialize_production`
→ `compose_production` 薄入口。作者在Shot既有 `production_intent.coverage_options` 中声明素材选项，
保留所有protected requirements。默认policy `production-strategy/2` 在qualified_reuse下先要求评估
更少生成次数、且仅缺用途证据的候选；明确FAIL可排除，但不会授权生成。显式旧policy `/1` 仅供兼容。
闭合质量失败的 `prepare_repair/start_repair` 返回上层重评；缺ProductionIntent会明确要求补authoring，
不会直接再生成。未提交关闭、known-no-effect、runtime retarget及unknown恢复仍归原owner。
材料化后，已取得当前用途资格的source-backed组件由原materialization builder重开lineage，接回标准
`position` → `compose/render`，并保留普通镜头及approved composition order；不重造原Decision/hash。
未完成的动态组件仍回原ProductionPlanningService，unknown优先STOP。最终完整P4重新校验，
`cut_packet`按实际首/末子镜的resolved spans描述原occurrence外部切点，不复制帧或样本推导。

`ProductionSourceOption.source_time_map`、`SourceUseEvidence.source_time_map` 和
`CompositionLayerSpec.source_time_map` 共用 `video-time-map/1`：相对所选trim的整数锚点
`points: [{source_frame:0, output_frame:0}, ...]`，`audio_policy: mute`。两轴严格递增，末点分别等于
源帧数和输出帧数；每段源/输出比为0.1–5。不反转、冻结、跳过区间或补造动作；加速会减少输出采样帧。
`CompositionSpec/ResolvedTimeline 2.3` 解析为同Shot连续spans，由唯一时间线拥有source trim及输出
frame/sample。固定版本0.7.103导出忽略 `data-playback-rate`，因此非一比一段按每个输出帧取
源坐标floor展开为一帧span；HyperFrames消费这些既有一比一窗口，不新增timeline或renderer。旧2.0–2.2字节/hash保持且拒绝time map。
Canvas composition填 `source_time_map` 时必须显式 `muted:true`；同镜/全局音轨、字幕或voice来源尚无
相应sample mapping时明确拒绝，不能静默丢掉所需声音。独立其他Shot的声音不受影响。

每次用途评估必须绑定exact map、bytes、role/window/transform及原要求；未编辑PASS不资格化编辑用途。
已失败媒体仅经原 `bootstrap_repair_input` 的sealed `/2` exact用途进入静音本地预览，资产保持UNBOUND、
qualification为NOT_EVALUATED，timeline标记 `development_preview` 并禁止render activation。
这一路线保留原request/fetch/rejection/QA及消费，不是普通import或Production许可。
先观察编辑实际效果，仍有无法达成的缺口时才提交明确、有限的新生成方案。

### Action Timing And Selective Effects

修复动作不到位时，先并排核对 actual native text、标称生成时长、原采用窗口和 QA observable。
`duration`、Shot 时长或 QA 中的切点不会自动成为 native prompt 的动作时限；已有“保持到切出”也可能
没有说明何时到位。作者应在既有 prose 内明确起始状态、连续动作、减速/落定及保持阶段，再逐字核对
compiler 输出。为切点预留的提前落定时间属于生成余量，必须与原验收条件分别记录，不自动加入或收紧 QA。
不得用长片末态代替较早的采用状态，也不把模型指南中的后续镜头切点语法当作单镜动作定时器。

保留源路径追加技术说明时，先保留旧 snapshot/hash 和原 parts，在新的 source draft 追加明确归属 Agent
的 text part，再重新 `inspect` → `author` → `preflight`；记录旧原文与新增段的 diff、来源和保持项。
它是新的 inspected authoring input，不能冒充历史用户逐字原文。仅修改 direction 的 expression/intent
会被原 preservation validator 拒绝；不得 patch compiled/resolved request 绕过。纯 author bundle/preflight
所需的本地/生成图 selection 证据也绑定 snapshot；新快照须沿原 import owner 重开同一 bytes/原生成记录，
准备新的 selection identity，保留旧 Registry 记录并明确重绑 asset roles，不能只改 receipt 的 hash。
这不需要重新生成图片，也不产生新的独立身份参考。纯 author bundle/preflight
不包含新候选的 Provider 编译或执行许可；完整 `prepare` 仍重开 canonical project、QA、history 和当前 limits，
没有新有限授权时不伪造 quota、decision binding 或执行就绪结论。

修复反射等局部异常时，分别说明正常保留区域与发生异常的区域、主体、可见背景和持续时段；避免全局
“无倒影”覆盖其他角色必须保留的映像。当前 H3 Max frame API 的首帧输入不提供逐帧区域遮罩或动作时刻
参数；这些 prose 仍是模型引导，不能声称执行了 mask、物理光学或中间帧硬约束。官方 H3 Base 指南与
社区原始实例的适用范围、失败反例及本次未验证假设见[研究记录](research/2026-10-17-h3-action-timing-reflection-repair.md)。
上述步骤用于核验输入表达；选择性反射、动作落点及其余已满足项仍须在 exact 新输出上重验。

## Per-Shot Whitebox Reference

这是用户明确指定的默认制作要求，适用于所有项目、Provider与每一个Shot：**先做白模参考，验后实际作为模型输入，再生成该镜头**。沿[Blender routing](blender-routing.md)使用现有Skills与共享资产入口；不新建故事执行链。此前单个白模实验不构成效果保证，新增规则也不追认历史失败为成功。

### Coverage And Exceptions

在既有Director适配说明/preflight证据中逐镜写明结论，不能整段或整个项目默认豁免：

| 结论 | 必须具备的依据 |
| --- | --- |
| 制作或复用白模参考 | 动作、人物/道具接触、走位、人数、空间、反射、运镜或接点等需保留的原要求；复用仍核对本镜全部适用条件。 |
| 模型不支持 | 所选exact model/profile/mode/role及当前adapter/capability证据，说明不支持所需视频/静态白模输入。上传、素材准入、配额或runtime暂缺属于待补能力，不能谎报模型不支持。未知先查明，不默默退回纯prompt。 |
| 确无必要 | 具体说明本镜没有需要几何/动作/摄影预演控制的信息，例如单纯静态风景/环境、纯图形，或直接复用已验收素材。环境镜有复杂运镜、关键空间关系或事件变化时仍做白模；制作麻烦、赶时间、已有文字/美术图都不是跳过理由。 |

只有上述两类有依据的例外允许不使用白模。未完成且无有效例外时，在付费preview/permit/POST前停止并补齐。例外不豁免原剧情、引用准入、预算或逐镜QA，也不授权换模型、额外调用或上传。

### Author, Bind And Verify

1. **Preserve the Shot.** 从原文/approved Shot列出开场、完整动作、结束状态、人物/道具/空间、镜头与采用接点。白模只负责明确指定的动作、几何、节奏和摄影；人物身份、服装、写实质感继续由原图/Character/Scene参考负责，声音/对白/字幕继续归原合同。不得为了方便白模删剧情、加动作、改镜头或拆镜。
2. **Match format and timing first.** 锁定原Shot画幅/比例、镜头焦段/机位/高度/轴线、fps、原采用窗口及所选Provider的nominal生成时长。生成时长与reference可接受时长不同则显式说明hold/padding及动作落点；最终frame/sample/trim仍只归`ResolvedTimeline`。不要继承Skill的通用1080p/35mm/时长默认值；已有竖屏不能在reference模式中无说明变横屏。封存actual native ratio设置，`adaptive`不保证保留原图比例。
3. **Build the smallest faithful guide.** 复用同场景的可编辑`.blend`、相机及角色/道具proxy；每镜分别核对人数、解剖左右、持物手、肩肘腕链、行进方向、接触/间距、遮挡和全动作极值。需要完整倒影或异常几何时显式建模并说明替身/光学模拟的实际范围。只做足以判断目标的白模，不扩成精模工程；动态镜头输出连续动作MP4，静态布局可在模型/role支持时使用白模静帧，不以静帧代动态控制。
4. **Review the exact reference.** 先实际看渲染，核对首帧、动作起点/极值/接触、采用接点及末态；有动作时完整正常速度查看白模，并显式用project-local `video-analysis`核对exact MP4、帧与时间。画面裁切、人体/道具穿插、错误手或错镜位先修。保存clean参考、`.blend`、作者来源/几何审计及实际观察；burn-in/注释只放独立review版本，不进入默认模型参考。白模QA与模型输出QA分别记录。
5. **Import and bind through existing owners.** 视频用`prepare_canvas_video_assets`及Registry 2.2；静帧沿既有PNG/generated-source入口。经`author`/`revise_authoring`保留旧记录与来源，再由Planner/Router/selected adapter编译。新参考须在新的inspected source中显式增加职责，原text parts逐字保留并展示适配diff。普通白模不能冒充前镜accepted state；连续后镜仍只从actual accepted source提取并绑定真实状态，白模按该状态适配。
6. **Prove actual consumption before submit.** 每镜展示白模path/SHA、实测规格、参考职责、原图identity、actual camera/aspect设置、生成/采用时序及实际编译后的image/media bindings与native请求预览。检查所选输入路线确实送入白模，不能只在prompt提到它或只把文件放进Registry。输入数量、role、人物/场景owner或素材准入不匹配时指出具体缺项，做必要共享适配；不要无依据复制参考、猜参数、绕过guard或悄悄省略白模。
7. **Recheck the generated Shot.** exact输出后仍显式调用project-local `video-analysis`，按全部原要求逐项验身份、动作、道具、人数、空间、摄影、画幅/裁切、声音和接点。白模/绑定/工程PASS不代模型服从或成片PASS；原图里的手机/工牌等不能因新画幅出画而直接继承通过。仅全PASS才推进下一镜；FAIL/NOT_EVALUATED/UNKNOWN沿原Gate停止与恢复，human 1.0x听看仍另验。

白模制作、核验、导入和绑定是Agent的执行责任；以上逐镜说明复用已有Director/preflight/evidence owner，不增加Product schema、状态库或第二timeline。本规则本身不证明程序已自动拦截所有工具调用，亦不提供新付费或重抽许可。

## Agent Image Authoring Workflow

用户要求原图、首帧或局部修图时，默认由 Codex 直接使用自带 Generated Image（`image_gen.imagegen`）；先做最小有界尝试，验实际图片后再接入现有项目。Qwen/ComfyUI 是可选的已封存执行路线，不是这套制作流程的前提。此处是 Agent authoring 指导，不是新的 Product Provider adapter、CLI 生图入口或 runtime Skill invocation。

1. **Bind intent and references.** 保留原文及已满足项，明确唯一编辑对象和目标状态；分别指定原图为编辑底图、人物图为身份参考、姿态/布局图为几何参考。先核对所选下游Provider的实际输入准入、原始产物/编辑产物要求，再投入长修图链；编辑前实际看图，核对 bytes/SHA、输入顺序、机位与邻座空间。不要用头像代替完整身体姿态，也不把参考图的背景或示意线要求生成进照片。
2. **Adapt supported inputs.** 内置工具接收 `prompt`、`referenced_image_paths` 或 `num_last_images_to_include`、`transparent_background`；两种参考机制不能同时传。prompt表达动作/坐姿、身份、构图、保留区域与禁止改动。它不接收 ComfyUI workflow JSON、`seed`、`steps`、`CFG`、sampler、latent mask 或 ControlNet 参数；骨架/区域示意只能作为可见参考，不能冒充对应节点或硬约束已执行。未暴露的模型身份/采样设置不猜测。
3. **Generate a bounded candidate.** 核验当前任务授权、明确新单元次数与时间边界、封存 exact 输入/引用和一次调用意图；不借默认路线自动扩大 paid/remote scope。以最少次数取证，保留每次原始输出与失败；timeout/UNKNOWN停止当前单元，不自动重抽、切工具或remint。用户以后明确变更路线也不关闭旧UNKNOWN、退回旧消费或授权盲目重试。
4. **Review actual media before integration.** 输出以 exact copy 保存进工作目录，实测 SHA、尺寸、通道；逐项检查目标姿态/手脚、身份、道具、空间、机位、非目标人物和额外文字。正常坐姿等语义成功与蒙版外像素零变化分开报告；尺寸变化不能经隐式resize/crop伪装匹配。所选合同需要精确保护区或mask时，必须另有匹配的已验证合成/执行证据，内置生图成功不能代签；缺项/FAIL仍阻断相应使用。
5. **Import through existing owners.** 仅在实际结果满足相应用途后，沿上文 [Entry And Data](#entry-and-data) 的 `generated_source` exact record/copy入口与 `revise_authoring`，保留完整旧Registry记录和原始 provenance。不能把内置生成图标成human/web import、Qwen输出或已qualified Provider；登记不等于素材验收/activation。原Shot视频、project-local逐镜MCP、声音/字幕、`ResolvedTimeline`和HyperFrames及human1.0x验收继续由原owner执行。

### Bounded Repair Practices

这些是已有入口内的Agent作图步骤，不是新的Provider或节点执行链。当前实证范围见[原S01修复记录](record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md#original-first-frame-static-admission-and-canonical-import--2026-10-16)；单条渐进链不能证明通用成功率。

- **Local detail → full frame.** 多人整图中的小对象持续不服从时，可显式裁出并放大目标作参考，记录原图SHA/crop/scale及新图身份；先验局部，再以原整图为唯一编辑对象、局部成功图只负责对应细节，调用原生生图转移。不能把局部PASS或放大的视图当最终构图，不能手工粘贴绕过合成/来源owner；每次转移都重验整图已满足项。
- **Pose before identity detail.** 镜面/背面左右臂难以用文字稳定表达时，先用实际姿态或几何参考明确肩→肘→腕→道具连接，再以单独照片只负责身份。几何参考可作为主输入，成功后再转移回场景。画面左/右不能代替解剖左/右；示意、Blender局部镜面与最终全景分别验，不把失败全景或参考输入声称为硬几何执行。
- **Original requirements before extra restrictions.** 修复前重开原文及后续相关状态，不自行要求空白证件、全部人物同排或零正常遮挡。撤回Agent附加条件要留原文证据和旧失败历史；原人数、身体范围、身份、动作、空间、声音、文字与叙事要求仍完整保留。
- **Prove the consumer binding.** 静态全项通过后，核对实际Scene/reference、`generation.references`、Shot的`required_asset_roles`及preserved-source的引用都指向该exact图；保留原Registry顺序和旧记录。沿共享preflight及无副作用Planner/Router prepare验证，旧mask/旧首帧槽未替换仍须修正，不能因登记成功就宣称视频可提交。Provider人像准入、人类来源声明、声音路线与逐次paid gates继续独立核验。
- **Keep Provider admission separate.** 2026-10-16原S01图静态PASS后，实际一次Seedance提交仍被`InputImageSensitiveContentDetected.PrivacyInformation`拒绝；人类虚构来源声明和本地Registry不会替平台放行。[方舟肖像指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh)列出的信任路线要求同账号、有效期内的指定模型原始产物，不能把Codex跨平台图或编辑图冒充该来源。规则须重新核对；失败后不靠降画质/遮脸/改标签/反复修prompt重发，先明确合法素材准入或已授权Provider路线，保留已通过图片和全部失败历史。该次拒绝不证明所有外部AI图永久不可用，也不自动授权入库、购买、换Provider或重抽。

### Portrait Input Admission

写实AI人物图被`InputImageSensitiveContentDetected.PrivacyInformation`拒绝时，先按输入准入问题调查。
该错误不证明人物是真人，也不定位到某张脸、工牌或具体像素；本地原创声明、静态QA、平台素材准入分别取证。
官方来源、社区原始失败报告、作者自报实测与本项目exact请求须分开，详见
[肖像准入研究](research/2026-10-13-seedance-ai-portrait-input-admission.md)。

1. **Identify the rejected input.** 重开实际model/endpoint/region、首帧或参考图role、native payload及解码后的SHA，保存error code、task有无及known/unknown outcome。格式错误、输入审核、输出审核分别诊断；没有MP4不伪造逐镜QA，也不因相同错误反复重发。
2. **Check the complete route before image repair.** 官方受信产物路线须核对账号、指定model、有效期、文生图/编辑来源及原始bytes；私域AIGC路线须核对实际权益、审核后`Active`、asset身份及所选role支持。官方API支持image URL字段的`asset://`和首帧role，但语法支持、单人`reference_image`示例均不能证明多人整张首帧审核放行。生图后再裁切、局部重绘或跨平台转移，仍要重验下游准入。
3. **Respect the current cost constraint.** 用户要求不找付费途径时，不推荐购买权益、充值、收费中转或新增付费Provider。不能由“高级创作权益”推断必须付费；[免费Entry及企业资格](research/2026-10-13-seedance-ai-portrait-input-admission.md#latest-correction--free-entry-and-account-eligibility--2026-10-16)须分别核对。文档存在、旧账号quota和当前已开通是三个不同事实，不把真人入口用于虚构图。Agent不代签人类声明或认证；用户拒绝开通时不自动开通。免费入库不等于免费视频生成，重新生成受信原图也不是免费复用当前图。未核验的当前权限、素材审核及免费额度标`NOT_EVALUATED`；本地profile存在不证明当前runtime就绪或原剧本质量通过。不自动下载模型、上传、提交工单或恢复调用。
4. **Preserve the accepted picture and story.** 保留已通过图片、source/generation lineage与旧计数；不靠换人物、改画风、隐藏人脸或删原文要求解决准入。社区换渠道成功、裁图/转码成功、同模型旧成功都只在其原条件下成立；不能给当前bytes或后镜状态代签。无符合当前授权、费用约束和完整声画要求的路线时，报告具体缺项并停止当前单元。

只有用户明确选择其他工具，或内置工具在submit前已确认不可用并且另一入口已获授权，才评估既有 `chatgpt-web`、本地ComfyUI或已选择Provider；失败后不能自动fallback。明确选择 `chatgpt-web` 时先核对 `backend_status` ready，保持exact backend，不切 `api/auto`。需要严格局部像素保护时，可选择下文已实现的 [Masked Image Workflow](#masked-image-workflow)，并完整保留其mask/permit/保护复验合同。

## Original Asset Preparation

已明确选择 Ark 原图路线时，`SeedreamImageProvider` 通过现有
`ProductionStateCommitter.generate_remote_image_asset` 执行单张 PNG；
`canvas_image_candidate_preparer` 注入既有 image activation 和 P5 owner。
model、纯文字 prompt、exact geometry、PNG/watermark、内部预算有效期进入 preview；
凭据仍由 private supplier 注入。生成次数和预算不会由 Canvas 自动增加。
原始 PNG 同时保留 Provider wire 与 Registry 身份。要在批准的 source 中选择该图，
resource ID 明确指向当前 canonical image output asset ID，保留原始 generation/paid 证据。
原图完成只提供下一镜的输入；仍须核验构图与引用职责，不能视为视频准入或连续性 PASS。

首帧需要基于已有场景图做局部准备时，同一 adapter 可显式选择
`SeedreamProfile(allow_single_png_reference=True, ...)` 和 injected `image_resolver(binding)`。
request 只接受一个 exact `scene` PNG reference；preview 列出该图的 SHA/bytes/MIME，
native payload 使用同一原图的 inline PNG。默认纯文字 profile 不接受参考，旧 hash 不变。
实际编辑区域由作者依据当前图片审核后放入 prompt；不自动计算坐标、遮罩或保护区。
原图、准备后的 clean plate 和影片须分别核验；首帧编辑不能代签 raw MP4 或下一镜质量。
该 shared capability 不授权新的图片/视频调用，也不启用图层拆分或新的 renderer。

## Masked Image Workflow

本地局部作图使用新profile `workflows/profiles/p7_1_qwen_masked_edit.json`，对应API图为
`workflows/templates/p7_1_qwen_masked_edit_api.json`。复用现有Qwen模型，不接入新的云Provider。
先通过现有Registry/authoring revision选择人物PNG、场景构图PNG和同尺寸黑白mask；mask归同一Scene，
白色为允许编辑区、黑色为保护区。mask不是新的角色图，也不伪造为原剧本中的canvas节点。

新mask/crop/padding由 `CanvasProductionService.prepare_image_assets(operations=...)` 无副作用准备。
每项操作显式给current Registry的source ID/SHA、新asset ID、license和像素参数；仅支持不缩放的
最小8倍数补边、identity crop与binary region mask。返回merged Registry、PreparedArtifacts和
content-addressed preparation receipts，保留旧assets；通过既有 `revise_authoring` 提交并绑定
Character/Scene后再prepare request。Production reader重放操作并复验source/output，不能假称原
canvas resource、human/web import或accepted Shot。源图不合剧情时，补边和crop不会解除质量失败。

API `CanvasProductionService.prepare_image_workflow` 或共用CLI同名action接收普通参数：
`attempt_id/shot_id/target_asset_role/character_id/character_asset_id/source_asset_id/mask_asset_id/seed/prompt_text`
与`profile_path/artifact_root`，可选`negative_prompt_text`。它沿标准loader重开当前项目，输出sealed
request/preview/profile及输入校验；忽略CLI `--runtime`，不提交Provider、不写state。
source/mask必须已被current approved Character/Scene选择，不能直接传任意文件路径或自动猜mask。

真实生成用注入的 `ComfyLocalImageProvider` 与 authorization，经已配置
`canvas_image_candidate_preparer()` 的 `ProductionStateCommitter.generate_image_asset` 执行；
现有local profile preflight、durable intent、一用permit和unknown停止规则保持。
新图以Scene为编辑底图，Character为身份参考，mask控制latent噪声及最终合成；输出、activation和
标准reader均核验保护区RGB像素不变。Mask内模型质量、clean plate几何和剧情要求仍须实际逐项QA。
Input PASS不证明runtime readiness；runtime readiness也不证明成功生成。原S01逐镜MP4、原生声音、
实际handoff、后镜QA、canonical字幕/trim与human1.0x不由作图工作流代签。

本地核心图的runtime核验沿既有 `scripts/comfyui_supervisor.py start --core-only`：
仅在新启动unit中禁用custom/API nodes并启用HF/Transformers offline；不下载模型。
旧默认启动参数保持，现有unit/占用端口不接管，失败/停止仍由同一supervisor管理。

## Production Flow

| Stage | Operation | Required evidence |
| --- | --- | --- |
| Inspect | `inspect` | exact snapshot、明确 selection、无 selected closure blocker |
| Author | `author` → `approve` / `revise` | diff、显式 approved 数据与 selected QaPolicy |
| Preflight | `preflight` | 全镜头参考职责/来源、后镜输入准入路线、占位与实际状态分离；不代替 paid preview |
| Means | `prepare_production` → `materialize_production` | 已有素材/剪辑与生成比较、exact用途证据、原目标覆盖；无新POST |
| Prepare | `prepare` → `start` | current Planner/Router、exact inputs、真实累计 limits |
| Execute | `execute(submit/poll/fetch)` → `evaluate` → `execute(validate/activate)` | paid/local gates、显式 project-local `video_analyze`、逐项 PASS |
| Handoff | `handoff_reference` 或既有 terminal/C2/C4 | accepted source、实测提取与所选实际状态检查 |
| Compose | `register_native_audio` → `compose` → `render` | exact request WAV、ResolvedTimeline、HyperFrames |
| Deliver | `cut_packet` → `review_delivery` → canonical acceptance → `deliver` | 剪辑接点、current P6、完整1.0x听看 |

每次 CLI 调用只做一个显式动作，`status` 给出 durable next action。`--arguments` 指向普通动作参数 JSON；
runtime 注入不能 JSON 化的对象。`approve` 需要 `attempt_id` 与 selected `qa_policy`：
共用 runtime 可注入已批准的 typed policy，或传入 canonical sealed policy 文件路径；用户无需手算内部 hash。
`prepare_repair/start_repair` 是显式已知失败恢复入口，`generate_voice` 接通既有 selected voice route。
准备阶段REQUEST尚无任何外部效果时，先经原feedback owner记录 `not_submitted`，再由committer
以 `superseded_before_submit` 或 `expired_execution_window` 关闭；同task的shared repair入口可接续
该核验通过的历史。不能把未关闭REQUEST当失败，也不能用此路径释放reservation或恢复unknown。
旧request/Registry/evidence与submit计数全部保留，唯一successor从canonical binding选择。
`execute` 的 action 必须等于当前 next action；resume 不重复已完成提交，unknown 不重试或改 ID。

## Shot Continuity

`state_reference` 填 `source_shot_id/frame_index/replace_asset_id/usage_license/checks`；
checks 只选实际需保持的 `identity/props/action/space/motion_direction/camera/audio`。
此计划使流程先停在交接，所选检查缺证/FAIL/陈旧时后镜不能 prepare 或 submit。

交接读取 accepted exact MP4，提取 presentation frame PNG，验证像素 derivation，再显式调用 MCP。
selected evaluator 的 `adjudicate(context, analysis, selected_reference)` 接收实际 frame PNG
PreparedArtifact 与 source/frame 绑定，返回每个所选 dimension 的 `ContinuityCheckMeasurement`：
expected、observed、confidence、rationale、match/mismatch/not_evaluated。全部 match 才经
Registry/committer 保存 immutable evidence 并绑定后镜。共用图片与提取本身不会制造状态 PASS。

普通中间状态替换一个明确的 scene chip，不伪装成 terminal。目标 Scene 需要独立 reference owner，
避免改写前镜共享的 Scene；可保留完全相同 location/time/mood，ID 分离不表示故事换场。
主体身份主/辅图不能悄悄换成动作参考。直接尾态、C2/C4 与有意 reset 沿既有 typed sequence contract。
每个后镜仍必须通过 exact post-media Gate 后才能推进。
中间状态交接必须先在 approved 数据中声明 `state_reference`；临时传入 checks 不代替计划。
缺计划会在提取、MCP 与 Registry/Manifest 写入前停止，避免后镜缺少对应 QA requirement。
`canvas_target_gate.target_state_qa_rules(direction=..., row=...)` 从已批准的 checks 产生普通 QA rows，
由共用 operator 加入该后镜的既有 selected generation inventory / allocation，并正常批准 policy；
不自动 activation。criterion IDs、source hash 由入口计算。prepare 检查 exact observable/dimension/
raw acceptance coverage；后镜的 canonical generation observations 必须全部 PASS。
source-frame 的 match 不代签后镜。实际比较所用的 frame/source evidence 由 selected evaluator 从
当前 canonical project 读取；marked QA 使用 `evaluate(..., presentation_verifier=...)` 的既有受控问答。

最终 `cut_requirements` 覆盖成片所有相邻 occurrence，声明 `continuous/insert/scene_reset` 与实际 checks。
`cut_packet` 绑定采用素材 SHA、源 trim、接点 frame 与重叠音轨；`review_delivery` 在 canonical P6
一次性 permit 下分析 final MP4。selected QaPolicy.final_output 必须等于
`canvas_review.canvas_cut_contract(direction)`，evaluator 必须是其 selected authority。
用 `seal_artifact` 与既有 `activate_qa_policy` 批准新版本，不自行制造 hash。
缺任何 requirement 或用户完整听看保持 NOT_EVALUATED，明确失败为 FAIL；原片认可不移给新片。
receipt/final acceptance 沿 P6 owners。`deliver` 只读 exact render，不签人类验收。

## Original Video Conditioning And Known Failure Recovery

`state_reference.conditioning` 默认 `extracted_frame`，显式 `source_video` 才将 Provider 输入改为
accepted 前镜的原始 Registry MP4。两种模式都先对 approved frame_index 的实际中间状态执行 Gate；
帧证据继续独立登记，视频参考绑定原始 SHA、source Shot 与 request identity。Scene 的 image ownership
不变，Seedance source-expression 的视频采用独立 `视频N` 编号。后镜自身 QA 不能由参考匹配代签。

已被 Provider 接受、随后 exact normalized observation 为 FAILED 且无输出媒体的 paid task，
仅可经 `runtime-repair/4` 的 `PaidKnownFailureRetarget` 显式恢复。grant 绑定旧 submit receipt、
FAILED observation、runtime-failure evidence 和新 candidate scope，one-use；必须保留同 task/Shot、
Provider/model、完整 final-output goal 及质量要求。T2V 到 I2V 的输入变更不等于 known_no_effect，
不释放旧 reservation、不重置消费，unknown/已有输出/错身份拒绝。新 POST 仍经全部 paid gates。

原文保留可由同一 source owner 为 Seedance/3 或 METASO H3/1 生成各自 grammar，重编校验原文、exact 引用及状态 grounding；不删除 preserved source 来换模型。
已知 paid no-effect 后显式换 Provider 使用 `runtime-repair/5` 的 exact 跨 Provider scope；旧同 Provider `/3`、已接受后 FAILED 的 `/4` 不因此扩权。
scope 冻结同 task/Shot、原文/首帧/剧情/声音与完整验收，只允许已声明的原生480p→768P输出 token 和几何适配，保留新旧 QA/goal、失败及消费历史；fresh preview/budget/egress/intent/permit 和逐镜 MCP Gate 仍不可省略。

## Audio And Verification

原生 WAV 只登记当前真正接受且有真实 cost coverage 的 request，旧 failed attempt 不阻碍正确版本。
未 mute 视频必须有 exact 来源 WAV；未指定音轨且只有一个精确匹配 WAV 时自动建轨，
使用 canonical frame/sample mapping 同步 source trim。显式轨道仍支持既有 L/J cut、gain、fade、ducking；
对白/旁白不能缺失。HyperFrames muted visual + canonical mixer 保持，禁止 direct mux 与第二 timeline。
普通15秒复刻使用 neutral `output_need.timing_mode=content_driven`，selected Provider output 采用
已实现的 `nominal_seconds` 有界末帧规则；显式 neutral fixed/frame_count 与精确 Provider 契约仍严格。
剪辑使用 `duration_policy.mode=content_driven`，`seconds` 是生成的标称提示；采用视频的实际帧数
或显式 source trim 决定 resolved 区间，仍检查 min/max、帧率、原生音频覆盖。`fixed` 保持精确覆盖。

离线 scripted Provider/evaluator/renderer 只证明控制流。冻结后以未参与设计的独立画布仅换数据验证复用；
来源表达、引用职责与对白改写错误通过 typed error 标明 occurrence 和数据字段；CLI 不回显原始输入或 traceback。
若修改共享代码，应将失败画布转为 development。真实完整声画与用户听看单独记录。
本轮 Seedance 新提交为零，历史7/7不重置。后续最小实测单元、授权和预算缺口见 completion record。
