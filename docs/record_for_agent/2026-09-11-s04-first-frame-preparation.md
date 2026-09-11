---
record_kind: session_summary
topic_id: jieshi-s04-first-frame-preparation
learning_eligibility: ineligible
---

# S04 First-Frame Preparation

## Outcome

2026-09-12 人审更新：用户回答“可以”，明确回应“你已看过 S04，确认画面和原生声音可以保留吗？”。重新核对 exact MP4 SHA-256 后，保存 `preparation-s04-v1/s04-attempt01-human-confirmation.json` 与 `s04-attempt01-human-next-shot-gate.json`：raw-generation required findings 依据该人审为 PASS，holistic KEEP，允许准备下一镜。P4 跨镜音频仍 NOT_EVALUATED，无 candidate activation 或最终验收。下文生成 checkpoint 的待人审状态保留为历史。

2026-09-12 更新：用户以“那就用这个先生成,把模型的声音也打开”确认首帧与声音。本次已完成一次 `viduq3-pro` I2V 提交并下载带原生音轨的 S04。下文首帧待确认、尚无 Router/Provider 结果与 used=0 均为先前 checkpoint 的历史状态，已由本节及 `Native Audio Generation` 取代。实际提交 quota 为 1/1；成片人审仍为 `UNDECIDED`，没有 activation 或 S05 submit。

## Native Audio Generation

- Exact MP4：`runs/jieshi-e01-i2v-20260907-attempt10/production-s04-v1/state/video-generation/fetch/files/a2a0251715de19e52d5ba80c335db06afb89f083c0c546cf5cd7c246b64aee4e.mp4`；SHA-256 同文件名；6,159,895 bytes。
- 请求为单张已批准首帧、4 秒、1080p、`native_audio=true`。实际 POST body SHA-256 为 `8437b7c6ab3f1b480e09c2c4cf3f0afb86e175ecd69c1157de8b93a68b91fbf4`；2026-09-11 16:03:57 UTC 提交，16:06:24 UTC success，16:07:03 UTC fetch 完成。
- project-local `video-analysis` MCP 已对 exact MP4 执行 probe、review 与 0.5 秒间隔抽帧。实际容器为 4.042 秒、1080×1920、24fps、97 帧；AAC 48kHz 双声道。FFmpeg 完整音轨解码成功，mean -38.1 dB、peak -21.8 dB，确认非静音；不推导声音内容或音量适宜性。
- 0/2 秒采样可见四人原有相邻座位；4 秒横移后最右人物部分出画。采样不证明整段动作自然、身份连续性或手机笑声语义。required findings 逐项为 `NOT_EVALUATED`，holistic `UNDECIDED`；P4 跨镜音频亦未验收。结果保存在 preparation 目录的 `s04-attempt01-post-media-gate.json`、`s04-attempt01-mcp-probe.json` 和 `s04-attempt01-mcp-review.json`。这是 orchestration evidence，未写入 Manifest acceptance。
- 第一次 fetch 因下载域名的本机 DNS 地址不满足 public HTTPS 检查而失败。复用 S03 的进程内 GET-only public-DNS helper，保留地址校验、TLS 与 canonical fetch；没有第二次 POST、全局网络修改或媒体重生成。`fetch-dns-evidence.json` 保存证据。
- 准备阶段 QA admission 发现 necessity/observable 重复与 source locator 被用作 intent path；在 Provider 调用前修正，并将精确 35mm/20cm 保留为偏好、跨镜音频留在 P4。经 canonical graph/QA transitions 达到 pre-submit r7，未重建 root 或删除旧 evidence。最终 QA hash `19c1ff19f44158f9f7ca7ecb650b94e4d91598c9c18655637db430e89abdee80`。
- 独立 `reviewer_xhigh` 为 `accept with concerns`，确认 exact request、audio、authorization、S03 前置 Gate 与 canonical execution seam；本次运行 `sys.flags.optimize=0`。相关 Vidu/guards 测试 98 passed，image-import/recovery 测试 42 passed。无 fresh isolated Harness receipt，不声称工程 Harness closure；未修改产品 source，保留其他 staged/dirty changes。
- 按 `record-ai-video-session` 更新本记录并按 `distill-ai-video-learning` 评估：`no_candidate`。仅一个未有人审结论的生成 attempt，不构成重复支持或受控对照，不提出自动采用的模型结论。

## Historical First-Frame Checkpoint

用户要求“生成shot4”。本轮完成《界蚀》S04 的首帧候选；尚未生成视频、提交 Vidu、导入首帧或修改 Production state。待用户对 exact PNG 确认输入用途后继续既有 Planner/Router/Provider 路径。

目录：`runs/jieshi-e01-i2v-20260907-attempt10/preparation-s04-v1/`。`image-generation-prompt.txt` 保存实际图片 prompt；`source-and-scope.json` 保存 S04 内容、参考范围及尚未 sealed 的视频意图；`first-frame-result.json` 保存测量结果。

- 实际调用内置 `image_gen.imagegen` 一次，不声称具体 backend model。
- 候选：`s04-first-frame-candidate-v1.png`；SHA-256 `8178b0206e58b02f22cc99f9f16e5567db08952972f5eb3fe45ad9ba50219bbc`；2,026,503 bytes；941×1672，未上采样。
- 参考是 S03 root 中已注册的开场图，SHA-256 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。继承四位乘客身份、服装、相邻座位及车厢材质；改为直接拍摄四人的机位，不继承前景林砚和镜面观察构图。
- 静态查看可见四人及其相邻顺序、许雯黑手机、何静膝上的灰包；不宣称视频连续性、人审或成片 PASS。

## Current Evidence

通过 `load_production_project()` strict reopen 当前 `production-s03-v1/project.yaml`，并实际重新计算 S03 MP4、人审确认与 next-Shot Gate hashes，均匹配 `s03-attempt01-human-checkpoint-state.json`。S03 raw visual 的用户 KEEP 记录仍有效；不是 typed activation 或 P4 音频验收。本轮未修改原 S03 文件。

S04 采用已存在的 4 秒分镜：许雯滚动手机，郭向东轻垂头，沈嘉程与何静安静；未新增对白。创作包 `Audio Production Policy` 要求后续新请求优先原生声音，因此后续准备应明确表达 native audio，而不能机械复制 S03 的 `native_audio=false`。跨镜笑声与最终混音仍由 P4 验证；尚无 sealed request 或音频结果。本任务准备 ceiling=1、used=0；没有 permit 或 Provider POST。

## Approval Boundary

`src/ai_video/production/image_import.py::HumanImageImportReceipt` 要求 `human_actor`、`approved=True`，并拒绝早于图片 import 的 approval timestamp。当前用户尚未看过并批准本轮新 PNG；不伪造这项人审。下一步仅请用户确认 exact 候选作为 S04 首帧，随后继续本次已要求的生成任务。

## Verification

Harness inspection 将本记录映射为 documentation。当前 working tree 的 docs contract check PASS，runtime Skill boundary tests 为 2 passed。Policy audit FAIL：既有 `image_import_video_frame.py`、`paid_provider_no_effect_reconciliation.py` 及对应 reconciliation test 未映射；本轮未修改这些文件或 policy。没有 fresh isolated Harness receipt，不声称正式 Harness closure。仅记录本轮证据，不处理其他 staged/dirty work。

## Router Selection Audit

用户随后追问为何持续使用同一路线。本轮只读核对实际 S02/S03 DecisionInputs、Decision 与当前 source，纠正“Router 判断 I2V 更优”的潜在误解：

- S03 `preparation-s03-v1/orchestration/s03_common.py::s03_planning_request()` 显式构造 `ConditioningLane.I2VA`、`SemanticReferenceRole.FIRST_FRAME`，并只提供 approved keyframe。模式在 Router 前已受输入约束。
- `preparation-s03-v1/prepare_s03.py` 只注册 Vidu target，并按 `model_id == viduq3-pro` 构造 `allowed_remote_candidates`；实际名单为 Q3 Pro T2V/I2V。
- S03 8 个 assessments 中，Q3 Pro I2V 是唯一 compatible 且 executable 的候选；Turbo I2V compatible 但被 remote scope 排除；T2V、R2V、extend 均不兼容当前固定 requirement，其中 R2V/extend 还不在调用范围内。这不是这些模式一般不受支持。
- S03 选中项 `fit=unknown`、`sample_count=0`、decision 输入 evidence 为空；`allow_bounded_exploration=True` 允许一次尝试。保存的 rationale 明确不保证质量。Parent 对候选数、唯一可执行项、selection 与 unknown 状态执行只读 assertions，PASS。
- S02 attempt04 的 8 个 assessments 同样只剩 Q3 Pro I2V compatible+executable，allowed 名单更窄，仅该 candidate。虽然输入有 4 项 evidence，选中 scope 的 sample_count 仍为 0，不能称为实证优胜。
- 通用 `generation_decision.py` 先筛兼容性、执行范围与 evidence fit；未知仅在 bounded exploration 允许时入选；多个 eligible 候选同 rank 返回 `UNRESOLVED_TIE`。并非固定按名字取首个。
- S04 当前只有图片、prompt、scope 与 image result，没有 DecisionInputs、Decision 或 execution binding。因此本轮准备首帧是 Agent 上游路线选择，不能归因于已运行的 Router。

上述核查不授权扩大 Provider/model 范围、放宽 Gates 或改写原请求。后续需要先依据 S04 的动作、连续性与真实参考用途判断适用输入路线，再经现有 owners 封装；不能仅删除白名单或改 mode 字段冒充同等条件的路线比较。RAG 返回 stale advisory fragments；结论来自本轮文件与代码核查。

## Learning Evaluation

按 `distill-ai-video-learning` 自动评估为 `no_candidate`：仅一个未获人审的静态候选，没有独立重复支持、受控多臂对照或现有 claim 的实质更新。
