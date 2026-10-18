# Canvas Prompt Control and Acceptance

Date: 2026-10-18

## Finding

现有证据不支持“画布整体提示写得松、模型因此自由发挥”这个结论。本地 S01 authoring 文本为 1151 字符（SHA-256 `f9e21d1fe7ea7c752a061bfc3a48b3a40f8aa93df7ec1334104f92b6823f5833`），明确要求左手停在距窗约 2 cm、玻璃中不出现对应手，并保留其他乘客倒影；资源映射将其标为 `candidate_preparation_only`，不是外部画布提交凭证。[本地 authoring 输入](../canvas-projects/jieshi-original-s01-s02/source.json)；[来源映射](../canvas-projects/jieshi-original-s01-s02/source-mapping.json)；[S01 原镜头卡](../superpowers/artifacts/drama/jieshi-episode-01/episode-01.md#s01)

可追溯的本地 H3 Max A native preview 为 1202 字符、SHA-256 `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`、`prompt_expansion_mode=balanced`；[QA presentation](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-mode-pair-20261017-001/A-qa-presentation.actual.json) 对采用点的要求是 3 秒、frame 71。[Native preview](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-mode-pair-20261017-001/A-native-preview.json) 写了“保持到切出”，却没有把手部到位绑定到 3.000 秒；镜头卡则规定生成 4 秒、只采用前 3 秒。这里有可直接确认的**截止时点表达缺口**，但不能据单例认定它是唯一根因。倒影禁令已经写入输入而仍失败，因此不能把幽影归因于“没有写严格约束”。当前拿到的是本地候选准备和 native preview；外部 Canvas 的实际请求、服务端扩写文本与其改写行为仍未知。

## Official Guidance

MiniMax [H3 Max CN 创建接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)要求非空文本，允许 `extra.prompt_expansion_mode`，省略时为 `balanced`；该接口说明没有定义 `balanced` 的保真程度，也没有逐动作时间字段。MiniMax [H3 模型说明](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/README.md)称独立的 H3-Context-IR 会解析文本与多模态素材关系，在不偏离用户原意的前提下补充缺失或欠明确的语义，并建议复杂输入使用此处理或遵循 prompting guidance。这证明官方 H3 体系存在语义扩写路线，**不证明本次 H3 Max CN 请求或外部 Canvas 调用了同一 Context-IR**。

模型方 [基础提示指南](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)建议按首帧、动作起始、连续发展、结果来写 I2VA；无参考的 T2VA 可以加入与用户意图一致的细节。[Full-reference 指南](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)的生成描述通常为 350–500 英文词，属于该重写格式建议，不是 CN API 的强制格式或长度保证。因此官方资料不支持“短提示必然更可靠”的通用结论，也不把提示当逐帧硬约束。

## Community Evidence and Scope

一位本地 H3 用户按指南把后续镜头写为 `[Shot 2] At 00:03.000`、不为 Shot 1 加时间戳，随后自述场景时序改善。[原始讨论](https://www.reddit.com/r/StableDiffusion/comments/1vff69w/minimax_h3_ignoring_time_stamps_in_prompts/) 这只验证过该用户的镜头切点语法；它不等于同一镜头内手部动作的精确截止控制。另一条本地 ComfyUI H3 Ref2VA 讨论中，有用户称简单提示和长而反复强调的提示都未能可靠替换视频人物；其他用户对提示与参考图的主次也有相反观察。[原始讨论](https://www.reddit.com/r/StableDiffusion/comments/1vg20lv/some_tips_for_feeding_videos_in_to_minimax_h3/) 这些经验没有统一模型版本或 CN Max API 条件，不能推出普遍的提示长度规则。

## Bounded Conclusion

本案例显示“动作终点写清但未绑定采用切点”与“明确禁止的局部倒影仍出现”是两个不同证据：前者是输入表达缺口，后者是模型未满足既有要求。它们不能合并成“画布默认放任模型发挥”，也不能证明提示改写造成失败。通用流程应把验收要求映射到可观察的提示内容和实际采用时点，保留全部原目标与 QA Gate；若扩写文本可取回，应与原文一并核对。单例失败不授权放宽反射或动作要求，也不证明另一种提示长度会通过。

上层控制的职责是为各项目判断自由度与实现手段：原批准的剧情结果、身份和连续性需保持，未固定的表演细节可以交给模型补足；切点、采用时长与可通过剪辑达成的节奏沿既有[edit-first workflow](../canvas-production-harness.md#edit-first-temporal-control)处理。只有实际声画可用才说明后期解决了目标，不能把单次原素材的3秒落点失败当成所有编辑用途失败，也不能用变速声称已修好局部倒影。该判断不新增 schema、不改本镜 QA、不授权新的生成或质量放行。
