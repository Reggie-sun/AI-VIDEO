# Canvas Masked Image Workflow

## Goal

把作图中的人物参考、场景构图和明确的局部编辑区送入真实节点工作流，替代全幅纯文本重抽。目标是为《界蚀》原开场保留已正确的车厢/人物/倒影提供输入控制；不宣称模型已经能生成正确 clean plate。

## Authority And Scope

用户明确要求原生 subagent 实现。当前 main 串行集成，两个原生 bounded workers 分别负责遮罩校验与 ComfyUI 节点路线，Parent 负责 canonical consumers、共享 Canvas 入口及验收。任务内必要共享变更由 Parent self-review 后实施，无 development worktree。保留 foreign dirty。

新增 `qwen_image_edit_2511_masked_local` lane，复用已装 Qwen-Image-Edit-2511、text encoder、VAE 和 ComfyUI core nodes。旧 Qwen/FLUX profiles、templates、bindings 原字节不变。无新增权重、依赖、Provider/云范围、故事脚本或 renderer。

本机read-only runtime核验沿既有ComfyUI supervisor的explicit `--core-only`新选项：不加载custom/API nodes，HF/Transformers offline；旧默认不变，不绕生命周期owner或自动下载模型。

## Request And Ownership Contract

- `ImageReferenceBinding.role=edit_mask` 仍绑定 Scene revision/hash 和 `visual_reference_asset_ids` 中的 Registry IMAGE。它是区域控制输入，不是新增人物。
- 新 request `/6` 只用于 `comfyui_local`，恰有按 canonical order 排列的 `character,scene,edit_mask` 三引用。Scene/mask 同 creative owner、不同 asset ID；source/mask/output geometry 相同，宽高为8倍数。
- 既有 request `/1–5` hash payload、preview、provenance 与序列化保持。新引用自然进入现有 preview bytes/IDs、provenance references、P5 input_artifact_ids，不另建 ledger。
- 共享 Canvas preparation 只读 current project/Registry，返回 sealed request/preview/profile 与输入核验结果。生成只调用现有 `ProductionStateCommitter.generate_image_asset`，注入 provider 和 authorization，重开 current pointers；未知停止、不重试。

## Mask And Graph Contract

Source 为8-bit opaque RGB/RGBA PNG；mask 为8-bit L/等RGB通道 PNG，只有0与255且二者都出现。白色编辑、黑色保护，无alpha/soft mask、EXIF旋转、自动缩放或全幅遮罩。按 SHA、Registry MIME/type/dimensions/bytes 严格核验。

新增 sealed graph：Scene 为 Qwen image1/latent source，Character 为 image2，mask 经 `ImageToMask(red)` → `SetLatentNoiseMask`；输出经 `ImageCompositeMasked` 与原 Scene 以 `x=y=0,resize_source=false` 合成后进入唯一 `SaveImage`。全部控制边和固定参数由同一 topology owner 核验，不能靠重算hash放行绕过mask的图。

在输入 preflight、submit 前重开并检查相同 bytes；fetched PNG及标准 Production reader均验证 mask=0 的每个 RGB 像素等于原 source。不静默修复输出，不声称整份 PNG bytes 未改变。mask 内是否达到剧情要求仍需实际视觉 QA。

## Invariants And Boundaries

Canonical Registry/Manifest/committer/P5/ResolvedTimeline/HyperFrames owners不变。新 workflow 不签 Shot acceptance；S01 MP4 → 显式 project-local video-analysis 全PASS → actual state → S02 自身QA保持。原对白、动作、摄影、七倒影异常、字幕和0–7/0–15秒边界不删改。声音 `EVIDENCE_REPAIR_FIRST` 独立保留。

原两个失败base不重分类，不挪用旧edit或B额度。工程验证不发 paid POST；严格local/unmetered runtime核验按既有豁免进行。真实图片生成前另核对task有限单元、exact输入、qualified runtime及一用permit。

## Acceptance Criteria

1. 共享请求、Canvas preparation、committer intent/activation与标准reader均可识别同一mask lineage；未选中/stale/错误SHA的mask在副作用前拒绝。
2. sealed masked profile/template/binding可加载并投影exact三引用，不能交换Scene/Character或绕过最终保护合成。
3. binary mask/geometry/channel/identity校验有执行证据；保护像素任一改变均被拒绝。
4. exact replay不重复调用；标准loader读回result/provenance/Registry边，fake工程证明明确区分真实媒体。
5. 旧profiles和旧request hashes不变；相关tests及exact Harness通过后按Risk Gate裁决、owned commit/push并核验远端。

## Parent Self-Review

本方案直接补足上轮确认的区域保护缺口；复用已存在的模型/节点和三引用lineage，减少全图重抽破坏已正确内容。遮罩不决定应画什么，不能保证七倒影或身份质量。当前8188未运行，runtime readiness在实际核验前为NOT_EVALUATED；不存在“装了节点即验收成功”的前提。

输入条件与图像编辑职责保持在新小模块；既有 oversized `comfy_image.py` 的拓扑实现移至唯一专用owner，public exports兼容。计划见[implementation plan](../plans/2026-10-14-canvas-masked-image-workflow.md)。
