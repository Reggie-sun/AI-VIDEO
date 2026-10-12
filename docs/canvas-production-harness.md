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
```

`inspect` 保留完整原始快照、版本指针、引用职责、主体主/辅图、timeline 与重复 occurrence，定位缺项。
`author` 无 Production 写入，展示原文、适配文本与 unified diff。示例是 development 测试数据：

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
未配置 runtime 时 inspect/author 可用；prepare/execute 必须补齐当前 canonical runtime。
凭据不得进入项目 JSON、`--arguments` 或 CLI argv，只沿现有 injected supplier。

## Production Flow

| Stage | Operation | Required evidence |
| --- | --- | --- |
| Inspect | `inspect` | exact snapshot、明确 selection、无 selected closure blocker |
| Author | `author` → `approve` / `revise` | diff、显式 approved 数据与 selected QaPolicy |
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
