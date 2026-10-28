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

## Current Inputs

用户更换画风、参考或修复已知输入问题时，Agent先整理**完整当前稿**，重新inspection；历史提示与修订说明留在既有immutable authoring input和主记录，不追加进新的模型提示词。旧source/compiler仍逐字保留当前批准稿，不负责理解“后文覆盖前文”、删重复或自动改写原剧情。先对照原目标和已满足项审核差异，再走既有`author`/`revise`；不写作品专用执行脚本。

已有Canvas Shot修改原始prompt、实际`Shot.intent`或`preserved_source_expression`时，`direction.shots[]`必须使用`source_revision`，包括移除已有原文保留表达；不因未声明画风字段或observed packet没有parts而豁免。新Shot初稿和未改稿的legacy重开保持兼容。baseline按canonical Shot ID关联，改Canvas节点名不重置控制历史：

- `contract_version: canvas-source-revision/1`、非空`reason`。
- `baseline_source_snapshot_sha256`绑定重开的上一版Canvas packet；`baseline_prompt_parts_sha256`是`canonical_sha256({"parts": baseline_parts})`。
- `baseline_effective_prompt_sha256`由`canvas_source_revision.effective_prompt_sha256(baseline_row)`计算：绑定上一版`Shot.intent`、`preserved_source_expression`；没有保留表达式的legacy编译路线另纳入typed、规范序列化的`generation.generation_intent`，覆盖动作、表演等实际编入native prompt的指导。output/reference等执行配置不混入该payload；不是本版intent的hash。
- `sections: [{section_id, parts}]`只列当前有效段落；section ID唯一，其`parts`依序展开必须等于本版inspection的`prompt_source.parts`。替换同一职责时更新当前section，不保留另一份历史指令。
- `dispositions: [{part_index, part_sha256, disposition, reason}]`逐项覆盖上一版parts；part hash用`canonical_sha256(part)`，`disposition`为`retained`或`superseded`。保留项不能消失，被替代的完整旧文字不能继续混在新提示中。

没有结构化parts的observed prompt按一个`{"type":"text","text": source_text}`part进入同一inventory，observed prompt须与source_text一致；保留逐字原文，不自动拆段。只改导演intent而保留原始source时，仍列出全部原始parts为retained，并填写明确改稿理由。

既有accepted-state handoff由原owner调用`retained_source_revision`，在Registry注册前为机械材料替换生成canonical baseline及逐项retained声明；该helper拒绝原始parts/source_text变化，不自动审核画风或其他创意改稿。完整参考仍须沿既有accepted-source与exact replay校验，不借新声明绕过媒体Gate。换图使画风review失效时在Registry注册前停止，需Agent重新查看并显式建稿，不能自动继承审美结论。

`canvas_source_revision`从标准loader取得的上一版Project重开canonical director input，拒绝stale baseline、漏项、重复section、当前parts漂移或历史回流。声明随现有director provenance封存；已批准修订可重开和exact replay，有效intent或原文表达变更不能冒用旧声明的replay快捷路径，也不能在后续改稿中静默丢弃。检查只验证显式处置与字节，语义等价、原剧情/动作/声音保全仍需Agent按完整目标审核；把旧词换成近义词不构成已验证修复。

全镜换画风的每个Shot必须声明`visual_style`，不因legacy字段可选而省略：

```json
{
  "contract_version": "canvas-visual-style/1",
  "scope": "whole_shot",
  "source": {"asset_id": "current-style-character", "asset_sha256": "<exact-selected-PNG-SHA256>"},
  "reviews": [{
    "asset_id": "current-style-character", "asset_sha256": "<exact-selected-PNG-SHA256>",
    "role": "character_reference", "owner_id": "character-id",
    "current_style_sha256": "<same-style-anchor-SHA256>",
    "disposition": "current_style", "observation": "实际查看该exact图后记录的画风检查"
  }]
}
```

示例仅展示一条review的结构，实际须覆盖全部选中的图片，包括辅助图、场景和端点图；人物/场景引用的`owner_id`须匹配对应Character/Scene。完整端点图由当前Shot拥有，review可用`covered_owner_ids`明确列出已实际看图检查的可见角色和Scene；前镜terminal仍沿canonical前镜owner。这样允许已审核完整首帧覆盖多人构图，不强制改成九图参考路线，也不从图片自动推断人物是否齐全。style anchor本身必须是实际选择的Registry图片，不用任意字符串冒充已传给模型的原上传图。每条review绑定本图SHA与当前anchor SHA；漏图、换图未重审、旧画风review、漏角色或场景均阻断authoring。显式offscreen角色沿既有表演契约说明，不伪造可见参考。

`whole_shot`为默认范围，不能用仍为旧风格的`identity_layout_only`参考冒充全量换风格。确实采用混合参考时显式选`scope: mixed_reference_guidance`并填写`mixed_reference_reason`，每个例外另填`reason`及最终native prompt逐字包含的`scope_text`；预检报告`PARTIAL_REFERENCE_STYLE`，不声称全镜风格统一。图片实际是否同风格由观察者判断，确定性校验器不能从SHA推断审美。

`canvas_visual_style`在authoring、当前service重开、prepare及start前使用同一契约；prepare/start还对照实际requirement evidence、resolved image bindings和native scope，阻止声明中的图被漏传、替换或新增未审图。`preflight.shots[].visual_style_control`区分覆盖、例外与`aesthetic_acceptance/source_consumption: NOT_EVALUATED`；编译绑定检查不代表Provider已经执行或画风已通过。legacy未声明的输入保持原序列化/编译行为，报告`NOT_DECLARED`；旧失败片与付费历史不因工程修复而改变。

全场风格判断另由 Agent 实际查看本次 exact 参考：分别记录主要人物、背景人物的头身比例、肤质、发丝、衣物材质与环境光照是否协调、是否符合用户方向与时代设定。给出局部观察与未确定项；主角像 CG、人数正确、SHA 相符或 coverage 完整均不能证明全场统一。区分已观察不符、缺证和显式合法例外；换图沿既有 Registry/source revision/review 重新绑定，不改历史裁决，也不默认追加白模、图片或生成调用。

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
若本镜选用动态白模但首帧路线不能同时消费，必须逐镜记录 exact mode 的能力证据及输入取舍，保留全部原要求；
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
frame/reference 互斥及逐镜参考选择继续沿现有模型能力和上文/下文 authoring 规则处理。

`reference_control.objectives` 从同一完整 recipe 投影要求、输入片段、机制、duty、native path 与验收要求，
区分输入已表达、输入不支持及未评估；`decision.assessments` 只解释原候选选择。
compiler 失败时仍保留 selected candidate 的目标和失败 ID，片段标为 authored、未编译，不虚构实际 request。
模式概览不计作目标覆盖；所有输入检查和离线 fixture 的模型质量、human 验收仍 `NOT_EVALUATED`。

### Character Performance Authoring

Agent 制作有人物的镜头时，必须在 `generation.generation_intent.performance_intent.character_directions`
明确填写当前 Shot 每个 `character_id` 的表演方向，再准备新生成；不能仅写“自然”“害怕”等情绪词、
复制角色外观或依赖旧六字段。该字段沿现有 intent、Planner、recipe、compiler 和 execution binding
封存，不建立另一份人物状态库。`prepare` 与新 binding creation 会阻断缺失的角色、阶段或原片验收映射；
历史 reader/replay 不要求补写，不修改旧 bytes/hash、消费或验收状态。

每个人物填写 `screen_identity`（画面可辨认的外观/位置身份）、`role=principal/supporting/background`
以及 `visibility=visible/offscreen`。可见人物的 `beats` 按 `opening/response/settle` 顺序填写需要的阶段，
或只用 `throughout` 表达持续状态；逐阶段填写 `trigger`、`emotion`、
`intensity=none/subtle/moderate/strong`、`facial_expression`、`gaze_target`、`breathing`、`body_behavior`。
不可见人物必须写 `offscreen_reason` 且不填写可见表演；不得用此项隐藏应当入镜的人物。
没有可见人脸、机械角色或遮挡时，应按真实可观察部位说明限制，不编造眉眼或呼吸。

主角的情绪应落到可观察的面部/视线/身体变化，路人保持符合场景的日常状态；对异常不反应不等于整段冻结。
`throughout` 不等于 freeze，`none` 强度不等于无生命。眨眼、呼吸和小动作按景别、角色与叙事需要编排，
不自动为所有人添加相同动作，不强制每镜出现情绪转折。相对阶段是作者表演次序，不是硬定时参数，
实际采用 trim/frame/sample/timing 仍由 `ResolvedTimeline` 独占。

作者先区分用户硬约束、已批准叙事、导演选择与旧 repair margin，再检查主动作的动机、反应和终态。保留身份、道具、视线、剧情及已满足条件；保留构图或坐姿不能无据扩大成不许移动头身。按景别核对脸部、目光、呼吸、身体平衡与主动作的联系，不强制转头、换重心或新增事件。`subtle`、`none`、`throughout` 及有叙事来源的静止均可成立；遮挡和不可辨认的微表演须说明限制，不能靠统一眨眼/摆动制造全员自然的声明。

既有 coarse `PerformanceIntent` 六字段继续明确镜头整体反应；逐人物字段补足各人的职责，不从人物Bible
自动填值。新参数必须由 Agent 在 author/revise 输入中显式编写并查看适配 diff；不允许执行器根据空值猜表演。
对应 selected QA 的 required `acceptance/raw_generation` 条目，使用 `analyzer` 或 `human` 观察原片表演，
`intent_paths` 绑定整个 `generation_intent.performance_intent.character_directions`，或覆盖相关人物的全部阶段字段。
technical probe、recipe hint、diagnostic 或只覆盖视线的条目不能代替完整表演验收。
按组件生成时，表演映射必须进入所选组件的 generation acceptance；顶层 QA 清单不能替代该组件的验收。
电商商业 Shot（`commercial_binding`）的表演验收由电商 profile 的 `shot.performance.character_direction` 承担：
有人物时该 ID 必须列入 `applicable_requirement_ids`（`project_generated_commercial_shot_binding` 拒绝缺项），
selected QA 中同 ID 的 raw 条目 `intent_paths` 绑定 `generation_intent.performance_intent`，proof 与商业评审一致；
放在 `shot.*` 之外的表演条目虽可通过新生成检查，但商业失败评审无法给出其结论，修复会停止。

rich remote/local H3 编译器将同一表演方向机械转为原生文字。preserved-source 路线必须先在新作者版本中
显式写入完整确定性表演段落，并保留 coarse 六字段的原句；pure
`performance_direction.render_performance_direction(performance)` 和 preflight 的 `native_text_required`
提供待核对段落。编译器只核对原文已有内容，不自动追加或重写保留原文；缺表达返回输入不支持。
原始用户要求与新增导演表演指令的来源分别保留，输入修订不沿用已消费的旧调用授权。
表演文本计入所选 model/mode 的提示词长度上限；作者须核对 exact 预览并精炼表达，不能为适配长度静默删除人物或控制目标。

普通 Seedance authored binding 与 preserved-source 独立：新普通 binding 预先选择 `seedance-video-compiler/4` 的 target/stack，保留最终正文原字节；v1/v2 自动 prose 与既有 v2/v3 source 路线不被偷偷升级。对每个当前人物及 beat，在 selected QA 的 `RequirementExpression.intent_paths`、`native_text` 中编写精简职责；需要消除多路径/多片段歧义时填写可选 `native_text_mapping={contract_version: "native-text-mapping/1", intent_sha256, bindings: [{intent_path, fragment_indices}]}`。`intent_sha256` 由 QA 作者取当前 `canonical_sha256(generation_intent.model_dump(mode="json"))`；intent 修订后重新审查并封存 QA，runtime 不自动刷新。每条映射只指向同一条 QA 的非空片段和具体 canonical intent 叶子；片段可共同承担明确列出的相关字段。完整 deterministic 表演段落实际存在时仍可使用，但普通精简 binding 不要求整块模板文字。

author/revise 后实际对照 canonical directions → selected QA → 最终 native 正文，检查人物区别、动机、阶段、反应与终态有无丢失。旧 prose 的 `expressed_control_paths`、笼统父路径或“自然一些”不能免除这些职责。映射核验 request/intent/QA identity、叶子和 exact 片段；等义是否成立、有无正反矛盾由作者语义审查，程序不做 NLP 判断。不得以删人物、改 offscreen、移除 required finding 或降为 diagnostic 补覆盖；缺口回到输入层修订，不让编译器补写、截断或塞回长模板。500 字等建议不构成新的硬上限。

`preflight.performance_control` 与 `prepare.reference_control.performance_control` 展示逐人物参数、缺项、
所需原生段落、输入字面表达和原片验收映射。`LEXICALLY_EXPRESSED` / `DECLARED` 只说明输入/映射存在，
机制始终是 model prompt guidance；所有表情、强度、阶段与背景自然度都需看实际输出，不能当作 API 硬控制。
未进行新的真实媒体验证时，actual quality 与 human acceptance 保持 `NOT_EVALUATED`。

`final_native_prompt`、`final_text_mapping_issues`、`missing_final_text_paths` 显示本次最终输入；`MAPPED_FRAGMENTS_PRESENT` 仅说明具体片段存在。原片仍沿 Per-Shot Gate 显式调用 project-local `video-analysis`，自然表演还须正常速度观看，声音语义/反应时机须同 bytes 声画观察。分别汇报基础连续性、表演/观感、完整剧情与声音，说明时间/帧、遮挡与缺证；检查动作动机、身体/手部协调、脸部/目光状态、背景生活状态、全场美术及原叙事目标。抽样截图不能独自证明全部表演，背景安静也不能直接判成冻结。FAIL/NOT_EVALUATED 停止推进，证据不足先同 bytes 补证；用户负反馈记录为审片事实，正式 HUMAN receipt 仍归既有受信 owner。

方法参考：[Seedance官方提示指南](https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide)
强调将抽象情绪落实到可见动作/表情；[MiniMax H3模型作者指南](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)
区分主体身份与动作/表情等参考职责。后者是开放模型 full-reference 指南，不证明 H3 Max CN API 的同等能力。
[社区旧MiniMax表情演示](https://www.reddit.com/r/aivideo/comments/1g6shqk/)只作有界实践线索，
不作为当前 model/mode 的质量证据或必成功规则。普通作者输入示例见
[`subject-reference/project.json`](canvas-projects/subject-reference/project.json)，对应 source 保留显式表演段落。

### Production Responsibility Allocation

分工沿既有 QA inventory 的 `level/stage/semantics`、`ProductionRequirementAllocation` 与 Shot 的
`production_intent` 声明，不另建可编辑控制表。固定原文、人物和叙事结果保持 acceptance；
`directional_preference/acceptable_variation` 只能表达其明确范围内的自由度，不计 required finding。
未提供语义的旧目标标为未评估，不自动解释成可放宽。

| Existing owner | Responsibility | Evidence boundary |
| --- | --- | --- |
| Component `generation_acceptance` | 原片必须存在的人物、动作、状态及其他 raw 结果 | 输入/参考仅作引导，需原片逐项验收 |
| `assembly_requirement_ids` + `FinalOutputContract` | 剪辑或合成后才成立的硬结果 | 已声明 hard goal 须保持 ID、observable；post proof 保持原映射，不能仅写“后期处理” |
| `ProductionIntent` + Planner | 选择实际复用、变速、声音、生成等操作 | exact source-use 证据、能力与范围均满足才可选 |
| `ResolvedTimeline` + HyperFrames | 采用窗口、帧/样本、实际成片 | 分工报告不另算时间线，也不证明成片通过 |

新 QA publication 和当前策略使用共用 `production_allocation_issues`：有 generation rubric 的组件，
其 raw 目标及未分给 assembly 的 hard IDs 必须全部由该 rubric 的 `acceptance/raw_generation` 覆盖；
声明 raw 的目标必须有 component 承担，assembly 重叠不会豁免；raw 的 observable/proof/tolerance/measurement
也不能被组件改写。rubric required IDs 不能用 hint 或后期条目冒充。相同 ID 不能换成另一结果。
post 目标的 final proof 映射须一致，technical 无映射时要求显式修订，不静默降为 human/evaluator；
raw 原证明继续由 component/source-use 承担，额外 final proof 可不同，例如技术检查加成片人工验收。
多组件或原片/成片重叠验收合法；source-only
组件继续走 exact source-use，不强造生成 rubric。历史 bytes/hash、反序列化和 lineage 重开保持兼容，
不完整旧合同的新发布/使用仍会阻断。未实现的遮罩、跟踪、口型等操作仍为 capability blocker。

生成组件需要逐字保留已选输入时，由 `ProductionUnit.preserved_source_expression` 显式声明，
materialization 原样交给 child Shot，再由既有 compiler 核对 actual reference 绑定；不自动继承父镜整段表达。
该字段省略时保留旧序列化/hash，source-backed 组件不得携带生成表达，声明本身不代表 Provider 准入或质量通过。
生成组件失败后，原 quality-rejection owner 使用 lineage 对应的 component rubric 核对 recipe 并关闭；历史 receipt 保留其当时 QA，不能借父镜或新 QA 改写旧裁决。
QA inventory 可保留作者的条目顺序；recipe 按唯一 requirement ID 对齐完整字段，不重封 QA 或更改其 hash，缺项、改义和重复项仍拒绝。
对已物化项目再次 author 时，Storyboard 只有在 beats 仍匹配 director input 时才能复用；父 Shot revision 沿 retained canonical parent 递增，其余未变 Shot 的采用角色继续保留。

`author/preflight.production_control` 展示 QA inventory、固定来源、允许变化与已声明分工。
新项目可在 `--arguments` 提供普通 `qa_policy` 文件（限 data 目录内）预览，标为
`candidate_not_approved`；已批准项目的 preflight 默认读取 selected policy。全局 rubric 只展示一次，
没有匹配 Shot intent/allocation 时不把它自动套给每镜。`prepare_production` 的 CLI 和 Python API
默认仍返回原 immutable decision；需要报告时在普通 `--arguments` 中显式指定
`"include_control_report": true`（Python 为 `include_control_report=True`），返回
`{decision, production_control}`，materialize 仍消费其中原始 `decision`。
原生输入预览的每项目标同步展示上述语义；后期/诊断条目不再从 intent paths 派生出模型文本。
用户原 prompt 不被自动删改，已有 explicit input-control fragments 保持原合同。
这些入口无 POST、permit 或验收效果；旧失败不会因分工预览而通过，编辑用途与最终 A/V 仍需新 exact 证据。

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
该自动续接首版仅处理source-backed组件；`source=None`的动态生成组件仍归原ProductionPlanningService/
generation owner，本入口尚不自动续接。unknown优先STOP。最终完整P4重新校验，
`cut_packet`按实际首/末子镜的resolved spans描述原occurrence外部切点，不复制帧或样本推导。

`ProductionSourceOption.source_time_map`、`SourceUseEvidence.source_time_map` 和
`CompositionLayerSpec.source_time_map` 共用 `video-time-map/1`：相对所选trim的整数锚点
`points: [{source_frame:0, output_frame:0}, ...]`，`audio_policy: mute`。两轴严格递增，末点分别等于
源帧数和输出帧数；每段源/输出比为0.1–5。不反转、冻结、跳过区间或补造动作；加速会减少输出采样帧，
减速会重复采样源帧，不做光流补帧，动作自然度必须另验。
`CompositionSpec/ResolvedTimeline 2.3` 解析为同Shot连续spans，由唯一时间线拥有source trim及输出
frame/sample。固定版本0.7.103导出忽略 `data-playback-rate`，因此非一比一段按每个输出帧取
源坐标floor展开为一帧span；HyperFrames消费这些既有一比一窗口，不新增timeline或renderer。旧2.0–2.2字节/hash保持且拒绝time map。
Canvas composition使用上述V1时必须显式 `muted:true`。保留原声采用显式
`video-time-map/2` + `audio_policy:retime_preserve_pitch` + `muted:false`，并进入
`CompositionSpec/ResolvedTimeline 2.4`：resolver从同一VIDEO身份和同一帧映射派生
sample segments及内部 `native_video` P4 span；不另注册WAV、不把原生整轨冒充单独对白或环境声。
generated/captured源重开exact probe；普通imported源使用Registry实测metadata，不伪造generation probe。
compose只解析预期音轨；新native render在begin前对held MP4预检音轨存在性/唯一性，缺轨/多轨不写attempt，
materializer仍重读并验证exact bytes。已有attempt沿canonical replay且不重复预检，compose成功不证明已取得可用声音。
输出sample区间使用全局帧锚点减Shot起始sample，与画面共用取整边界。
源必须只有一条音轨、视频时间原点为零；正向音频起始偏移保留为空白，前置音频或不能可靠对齐时拒绝。
原声经显式注入的FFmpeg/ffprobe处理，逐段保音高变速；每段尾部补齐/裁切最多一个输出帧的samples，
proof记录输入/输出PCM、source/map/tool hashes及修正量，超界拒绝。画面仍沿原帧窗口解析，
`0.1–5`是帧映射倍率边界；两轴sample窗口各有不到一个sample的取整误差，不能据此重拒合法帧映射。
原声还须通过实际DSP样本修正检查；合法map不保证每份原声都能安全处理，超限明确失败，不自动静音或转生成。
原P4 mixer和HyperFrames消费同一时间线。原声节奏与时点随画面映射改变；保音高不保留原绝对时刻，
也不保证音色、接缝或口型质量，必须检查实际A/V。
同镜/全局额外音轨、字幕或voice来源尚无对应sample mapping时明确拒绝，不能静默丢掉所需声音。
独立其他Shot的声音不受影响，旧2.0–2.3及V1序列化保持兼容。

每次用途评估必须绑定exact map、bytes、role/window/transform及原要求；未编辑PASS不资格化编辑用途。
已失败媒体仅经原 `bootstrap_repair_input` 的sealed `/2` exact用途进入静音本地预览；
同源A/V用途需独立 `/3` capture及 `retimed_av_preview` scope，不能复用旧静音capture。资产保持UNBOUND、
qualification为NOT_EVALUATED，timeline标记 `development_preview` 并禁止render activation。
这一路线保留原request/fetch/rejection/QA及消费，不是普通import或Production许可。
需要检查独立替换声音时，显式使用`development-repair-input/6`的`replacement_audio_preview`：
sealed source window仅支持正常速度，receipt内V1 map的source/output锚点必须逐点相等；
Composition layer不携带retime map，仍严格匹配receipt的Shot/role/trim/transform。
P4必须显式提供已登记的BGM/SFX/ambience，不允许对白、旁白、caption或voice source；
原MP4音轨不会进入混音。resolver沿同一帧/样本时间线产生`development_audio_preview`，
HyperFrames实际导出AAC；旧`/2`静音与`/3`原生保音高预览的行为保持。
新scope仍保持UNBOUND/NOT_EVALUATED，原activation owner拒绝所有非Production scope，
且即使改写scope，captured bytes检查仍拒绝Production激活；有声预览不修复原raw Gate。
先观察编辑实际效果，仍有无法达成的缺口时才提交明确、有限的新生成方案。

### Non-generative Local Cleanup

局部影子、穿帮或脏点先评估clean plate与遮罩合成，不因trim/retime修不了就直接重生成。
`production_control.source_preparation`显示本地修补入口、前置条件和边界，不选择新Provider或自动放宽QA。
公共像素核使用同一视频的干净帧，`video-clean-plate/1`包含exact `source_sha256`及严格排序的`frames`：
每项声明`frame_index`、`patches`（`plate_frame`、plate坐标多边形、`feather_px`、正向`plate_to_output_affine`）
与output坐标的`protected_polygons`。仿射数组表示`x'=a*x+b*y+c, y'=d*x+e*y+f`。
这是显式逐帧对齐数据，不是自动平面/光流跟踪；空背景、前景遮挡与素材变化仍由作者核对。
非法/越界/自交几何、非有限或奇异变换、越界采样拒绝，不静默裁掉失败区域。

保护区优先于补片羽化：核会将保护像素的alpha强制置零，因此保护线切过补片内部时仍可产生硬边，
扩大保护矩形也可能把待去除残影一起保留下来。先核对真实前景轮廓与残影的空间关系，再调整作者的逐帧保护多边形/补片，
不以保护像素零变化证明遮罩内容正确。对贴近前景边缘的修补，检查实际最后一帧及动作边界附近的连续帧，
并以正常速度完整观看衔接；稀疏抽帧可能遗漏不足一个采样间隔的缺陷。
用户反馈先对齐exact观看文件、实际手势/画面区域及既有source/use/time-map；口语“最后”不能直接映射为文件末帧，
采用切点与源片尾段分别核对，时间映射仍归`ResolvedTimeline`。覆盖检查要包含整块待去除物与真实前景，
不能仅检查局部接缝，或让固定保护baseline盖过已写出的动态轮廓。

`prepare_video_cleanup(source_bytes=..., plan=..., tools=VideoCleanupTools(...))`只做有界本地素材准备：
支持8-bit、零视频起点的CFR MP4、0或1条原声音轨；默认最多600帧/60秒、source200MiB、解码RGB1GiB及PCM64MiB。
保持每个源帧及其PTS，用`libx264rgb` lossless保存并重解码比对，未选帧和保护像素不得变化；原声音频不重编码，
另比较PCM及stream start/duration/time base。不能可靠保持的输入显式失败。编码结果是派生源，不是新的timeline或最终成片renderer。

面向正常浏览器播放时，`CanvasProductionService.bootstrap_video_cleanup`默认同时生成独立的观看代理（`viewing_proxy=True`）；
可显式关闭。低层`ProductionStateCommitter.bootstrap_repair_input(cleanup_viewing_proxy=False)`默认仍不生成代理。
此扩展沿用原捕获资产及`development-repair-input/4`无损RGB母版，再以`development-repair-input/5`
登记母版派生的独立H.264 `yuv420p`、BT.709 limited-range有损代理；原`video-clean-plate/1`计划、`video-cleanup/1`母版及`/4`准入契约不变。
代理保留测得的画面尺寸、帧率、逐帧PTS、时长、原音轨和PCM，但不拥有母版的逐像素保护证明；母版仍是像素证明对象，代理只用于观看。
输出像素格式与实际色彩标签经ffprobe复核，不能由编码参数声明代替实测。两份派生物都保持UNBOUND/`NOT_EVALUATED`，
播放或技术证明不自动成为模型质量、人工验收或Production通过。

本地视频库明确标记`source_kind=viewing_proxy`并关联`source_master_sha256`；`cleanup_master`默认隐藏，
可在“高级证据筛选”中显式显示。使用观看代理做实际画面判断前，仍须以正常速度检查肤色、灰阶、主色、局部修补、声音和整体效果；
用户看到的代理是有损编码，不能代替母版核验。工作区目录保留扫描上限；受限relative workspace与exact SHA深链
可通过既有strict detail读取目录遗漏的目标，文件权限边界不变，能定位一个准确素材不等于索引完整。

对已关闭remote质量失败，使用现有独立开发bundle的`bootstrap_repair_input`及`/4`准入。
Canvas普通`--data`指定该开发bundle；`bootstrap_video_cleanup --arguments ... --ffmpeg ABS --ffprobe ABS`
要求原`source_root/source_attempt_id/source_sha256`、新`asset_id`、`usage_license`、sealed `preview_use`、
原实际`preview_probe`及`cleanup_plan`（内联或同data root内JSON路径）。工具显式注入，不加载generation runtime或凭据。
公共service也支持同样参数；所有持久化仍由唯一committer完成，CLI返回已落盘派生路径和exact SHA供观看。
原捕获`asset_id-source`与新派生资产同时保留；Registry reader复验recipe/proof、原失败链和关联，不把local measurement伪装成Provider probe。

派生仍UNBOUND、qualification NOT_EVALUATED，禁止Production Shot绑定或render activation；不自动修复原raw Gate，
也不推进下一镜。正常速度观看要检查补片漂移、接缝、被覆盖背景运动及真实前景；局部像素/声音证明不代替整段质量。
最终剪辑、变速和声音混合继续归`ResolvedTimeline`/HyperFrames。原片及其质量失败、消费和其余全部要求保留。

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

白模是可选的空间、动作与摄影预演手段，不是所有题材或Shot的默认生成路线；按`AGENTS.md`逐镜选择参考条件。选用白模时，沿[Blender routing](blender-routing.md)使用现有Skills与共享资产入口，核验后实际绑定；不新建故事执行链。白模、参考图及长Prompt均不保证模型服从；输入组织修复与工程PASS也不证明画面质量改善，仍须exact新成片证据。

### Reference Selection

在既有Director适配说明/preflight证据中逐镜说明参考职责与选择依据，结合题材、表演/动作/空间/摄影目标、所选exact model/profile/mode/role及已有成片证据，不以题材标签或工具可用性代替判断：

| 结论 | 必须具备的依据 |
| --- | --- |
| 制作或复用白模参考 | 说明需要引导的具体空间关系、动作或摄影目标，以及当前输入模式能消费哪些参考；复用仍核对本镜全部适用条件，不假定模型原样继承动作时序。 |
| 使用其他参考条件或文字 | 说明所选原图、人物/表演/动作参考、首尾帧或文字分别承担什么职责及其局限；有空间或动作要求也不自动强制白模，不使用白模无需申请例外。 |
| 所需输入能力不支持或未知 | 核对当前adapter/capability证据；上传、素材准入、配额或runtime暂缺不能谎报模型不支持。未知先查明，再明确选择可行路线，不默默删掉原要求或退回纯prompt。 |

选定的必要参考未核验或未实际绑定时，在付费preview/permit/POST前停止并补齐。参考选择不豁免原剧情、引用准入、预算或逐镜QA，也不授权换模型、额外调用或上传；以下制作步骤仅适用于选用白模的Shot。

### Author, Bind And Verify

1. **Preserve the Shot.** 从原文/approved Shot列出开场、完整动作、结束状态、人物/道具/空间、镜头与采用接点。白模只负责明确指定的动作、几何、节奏和摄影；人物身份、服装、写实质感继续由原图/Character/Scene参考负责，声音/对白/字幕继续归原合同。不得为了方便白模删剧情、加动作、改镜头或拆镜。
2. **Match format and timing first.** 锁定原Shot画幅/比例、镜头焦段/机位/高度/轴线、fps、原采用窗口及所选Provider的nominal生成时长。生成时长与reference可接受时长不同则显式说明hold/padding及动作落点；最终frame/sample/trim仍只归`ResolvedTimeline`。不要继承Skill的通用1080p/35mm/时长默认值；已有竖屏不能在reference模式中无说明变横屏。封存actual native ratio设置，`adaptive`不保证保留原图比例。
3. **Build the smallest faithful guide.** 复用同场景的可编辑`.blend`、相机及角色/道具proxy；每镜分别核对人数、解剖左右、持物手、肩肘腕链、行进方向、接触/间距、遮挡和全动作极值。需要完整倒影或异常几何时显式建模并说明替身/光学模拟的实际范围。只做足以判断目标的白模，不扩成精模工程；动态镜头输出连续动作MP4，静态布局可在模型/role支持时使用白模静帧，不以静帧代动态控制。
4. **Review the exact reference.** 先实际看渲染，核对首帧、动作起点/极值/接触、采用接点及末态；有动作时完整正常速度查看白模，并显式用project-local `video-analysis`核对exact MP4、帧与时间。画面裁切、人体/道具穿插、错误手或错镜位先修。保存clean参考、`.blend`、作者来源/几何审计及实际观察；burn-in/注释只放独立review版本，不进入默认模型参考。白模QA与模型输出QA分别记录。
5. **Import and bind through existing owners.** 视频用`prepare_canvas_video_assets`及Registry 2.2；静帧沿既有PNG/generated-source入口。经`author`/`revise_authoring`保留旧记录与来源，再由Planner/Router/selected adapter编译。新参考须在新的inspected source中显式增加职责，原text parts逐字保留并展示适配diff。普通白模不能冒充前镜accepted state；连续后镜仍只从actual accepted source提取并绑定真实状态，白模按该状态适配。
6. **Prove actual consumption before submit.** 每镜展示白模path/SHA、实测规格、参考职责、原图identity、actual camera/aspect设置、生成/采用时序及实际编译后的image/media bindings与native请求预览。检查所选输入路线确实送入白模，不能只在prompt提到它或只把文件放进Registry。输入数量、role、人物/场景owner或素材准入不匹配时指出具体缺项，做必要共享适配；不要无依据复制参考、猜参数、绕过guard或悄悄省略白模。
7. **Recheck the generated Shot.** exact输出后仍显式调用project-local `video-analysis`，按全部原要求逐项验身份、动作、道具、人数、空间、摄影、画幅/裁切、声音和接点。白模/绑定/工程PASS不代模型服从或成片PASS；原图里的手机/工牌等不能因新画幅出画而直接继承通过。仅全PASS才推进下一镜；FAIL/NOT_EVALUATED/UNKNOWN沿原Gate停止与恢复，human 1.0x听看仍另验。

选用白模后的制作、核验、导入和绑定是Agent的执行责任；以上逐镜说明复用已有Director/preflight/evidence owner，不增加Product schema、状态库或第二timeline。本规则本身不证明程序已自动拦截所有工具调用，亦不提供新付费或重抽许可。

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

### Verification Responsibilities

制作顺序由本 workflow 编排，工程验证、提交准入和媒体验收分别沿原 owner 执行；以下不是新增的 Product phase、状态库或许可。

| Point | Required work | Evidence boundary |
| --- | --- | --- |
| Before a bounded media trial | 先判断已有素材/剪辑是否可用；只补齐当前输入或运行证据确认的确定性缺口，运行相关 focused regression 并关闭阻断；核验 exact 输入、当前授权、真实计数、预算、egress 和一次性 permit | 完整 Harness receipt 不是模型取材前置条件；关键正确性/安全阻断不能因“试拍”略过 |
| After the exact source exists | 显式 project-local MCP 核验所选 raw rubric；原片可用但节奏偏差时，先用现有剪辑及原声映射形成 exact 成片 | raw 时序余量不替代成片切点；FAIL/NOT_EVALUATED 不推进下一 Shot，也不授予 activation/accepted state |
| Before engineering completion or final delivery | 共享源码稳定后完成 exact scope 的全部适用 Harness checks 和必要 Risk Gate；成片按原 P6/final-output/human 要求独立验收 | 工程 proof、媒体质量与人工接受分别报告；模型路线未成立时可以继续有界取证，不能宣称工程或交付完整完成 |

`harness-inspect` 的 `verification_purpose=engineering_completion` 只列工程完成检查；
`media_submit_authority=false`、`media_acceptance_authority=false` 不产生运行时例外。
纯数据准备、普通查询或每镜生成不重复全仓工程验证。源码变化后的相关回归不能用旧 receipt 代替；
完整工程发布验证在稳定候选执行，后续仅因新变化、失败或未解决问题补做适用检查。

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
当前调用次数、outcome 与剩余有限授权只从 canonical attempt/paid state 和当前授权核对，历史消费不重置；具体实验状态保留在对应 record，不在通用 workflow 固定某一项目或 Provider 的当轮计数。
