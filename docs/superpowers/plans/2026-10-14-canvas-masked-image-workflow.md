# Canvas Masked Image Workflow Implementation Plan

## Goal And Scope

实现[spec](../specs/2026-10-14-canvas-masked-image-workflow.md)的本地三引用遮罩编辑路线，并接回已有 Canvas/image/committer/readback。用户要求原生 subagent，Parent继续拥有判断、集成、verification与completion。

## Ownership

| Owner | Files / responsibility |
| --- | --- |
| Native `image_mask_contract` | 新 `production/image_edit_mask.py`、`tests/test_image_edit_mask.py`；request/PNG/mask/保护像素校验 |
| Native `comfy_masked_workflow` | `production/comfy_image.py`、新 `comfy_image_workflow_contract.py`、三个新 `p7_1_qwen_masked_edit` artifacts、`tests/test_production_comfy_masked_image.py`；sealed图与adapter |
| Native `image_mask_contract` follow-up | `scripts/comfyui_supervisor.py`、`tests/test_comfyui_supervisor.py`；opt-in核心节点/offline模型启动，旧默认不变 |
| Parent | image request/intent/activation/reader消费者、helper Registry复验、共享Canvas preparation/API/CLI、集成tests、policy/matrix/docs/record |

各writer集合不重叠；worker完成并归还ownership后Parent才修改其文件。foreign dirty、旧profiles/templates/bindings与原剧本文件不动。

## Milestone 1 — Exact Mask Contract

新 role 复用 Scene creative + Registry bytes。仅mask请求采用 `/6`，其余hash不变。白编辑黑保护，opaque PNG、binary/geometry/SHA严格检查。input预核验与output像素复验共用helper；Registry复验由同一helper在intent和reader消费，无第二状态。

Verification：`PYTHONPATH=src:. .venv/bin/python -m pytest -q tests/test_image_edit_mask.py tests/test_production_image.py tests/test_seedream_remote_image.py`。新增typed请求、未selected mask、corrupt bytes及standard loader读回测试放在 `tests/test_canvas_masked_image_workflow.py`。

## Milestone 2 — Sealed Local Node Workflow

新增masked lane/profile，复用旧Qwen权重和exact ComfyUI commit；Scene→latent/Qwen image1，Character→image2，mask→noise mask与最终composite；三槽位按request顺序绑定。拓扑验证独占新module，旧ordinary两路线保持原验证语义与public imports。preflight/submit前重开source/mask，output保护像素验证失败停止。

Verification：`PYTHONPATH=src:. .venv/bin/python -m pytest -q tests/test_production_comfy_masked_image.py tests/test_production_comfy_image.py`；验证核心边篡改、mask遗漏/角色颠倒、尺寸错误、保护区变化和旧profile字节。

## Milestone 3 — Shared Canvas Entry And Standard Readback

新 `canvas_image_workflow.py` 只构造已有 ImageGenerationRequest/Preview，重开当前approved Character/Scene与注册mask。`CanvasProductionService`薄delegation，既有CLI增加只读 `prepare_image_workflow`；禁止该action加载operator runtime产生副作用。真实生成沿注入provider/authorization和唯一committer，canonical candidate setup复用 `canvas_image_candidate_preparer`。

Verification：标准Production loader/committer集成测试，三引用lineage、byte accounting、current/stale pointers、exact replay和mask外保护；CLI preparation禁runtime/no-network。技术fixture不代表原S01。

## Milestone 4 — Runtime And Publication

核验exact本机checkout/已有模型/节点。当前服务未启动；沿已有ComfyUI supervisor新增explicit `--core-only`，关闭custom/API nodes并设置HF/Transformers offline；旧默认启动保持。只做read-only profile readiness，不为缺合格剧情source/mask生成原S01。工程完成后跑mapped suites、Architecture Gate与exact staged Harness，receipt fresh且commit tree相等；按SUBAGENTS Risk Gate判断一次，owned commit/push并核验remote main。

## Completion Boundary

交付可运行的共享作图工作流、接口和实际工程验证。候选画面/七倒影质量、S01/S02 MP4、声音语义和human1.0x未实际验证时仍为NOT_EVALUATED；不以工程checkpoint标记原连续单元完成。记录沿既有原S01–S02主record更新，learning默认不从未实测workflow推导普遍结论。

## Continuation — Input Preparation And One Local Attempt

已发布工程与只读runtime checkpoint后用户要求继续。Native `image_workflow_seam`核对现有Manifest19 resume/revise路径，确认原node selection与human/web import不能真实表示新mask/crop/padding。Native `image_mask_contract`仅拥有新 `production/image_preparation.py` 与对应tests；Parent拥有service薄API、reader消费者、集成tests、policy/docs与原候选数据，workers不写原Production/执行媒体。准备receipt复验留在Production leaf，reader不反向依赖Canvas模块。

先实现无副作用、当前Registry来源的显式像素准备，标准reader重开同一receipt；通过relevant tests/Harness和Risk Gate后owned commit/push。随后固定原bytes和七反射/左右手/机位的完整准备要求，明确padding/crop/mask与模型文字的适配；经已有canonical authoring revision、exact prepare/preflight/intent/one-use permit提交一个strict-loopback本地candidate。有限单元最多1次、20分钟模型执行观察、无cloud/重抽；unknown停止，超时不重铸permit或另发请求。

输出保护像素验证与原S01完整静态QA分开。局部图FAIL/缺证停止镜头推进；素材通过也不能解除声音 `EVIDENCE_REPAIR_FIRST` 或代签视频Gate。下一真实视频仍沿原授权单元逐次核验，绝不消费旧B或改历史计数。

## Known Failure Extension

首个local unit已用1/1，exact PNG落盘/技术准入但广域窗面编辑破坏他人身份与空间；保护区1,096,780像素变化0。该attempt STOP/QA FAIL保留。新local unit有明确输入差异：恢复原始布局，选择实际被编辑角色自己的identity crop，仅改Zhou站姿；target-specific检查与非目标保护通过后，仅改He右缘完整性。最多2新submit、每次1200秒、本地累计cap3、paid0、blind retry0；不是重抽旧单元或无条件追加预算。

完整七倒影/身份/道具/摄影/缺席要求持续追踪，单个人物修复的中间图不冒充合格S01。Z target FAIL/NOT_EVALUATED不提交H，unknown立即停止；新unit预算或可归因变量耗尽时报告原剧情缺项，不再扩量。原Scene/Shot/Gate不简化，没有第二timeline、renderer或故事执行脚本。
