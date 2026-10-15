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
`preflight` 忽略 `--runtime`，不实例化 Provider、不调用凭据或媒体工具；已存在项目时重开 immutable
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

复刻保留原文 text part、chip slot、主体主图及全部辅图顺序和职责。只按 common compiler 的素材顺序
将 chip 换成 `图片N`。`Shot.intent` 与 `subject_action.progression` 自动生成，已有不同文本直接拒绝；
对白/旁白必须引用原文。`source_grounding` 仍经 source owner 验证，不制造原文未表达的动态事实。
不支持的音频引用或未知素材须明确补齐 supported route，不能删除后继续。
新数据入口封存 `seedance-preserved-source/2`，保留同一 chip 的每次文本出现与 tray-only 普通参考；
同一实际素材只形成一次 native input。重复 slot 的材料或同 asset 的 role/bytes 冲突直接拒绝。
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
