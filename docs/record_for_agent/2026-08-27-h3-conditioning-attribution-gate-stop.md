# MiniMax H3 / T8 Conditioning Attribution Experiment Record

## Status

- Date: 2026-08-27
- Classification: `development_experiment`
- Checkpoint: `COMPLETED_FIXED_FOUR_ARMS_AFTER_USER_OVERRIDE`
- Attribution result: `INCOMPATIBLE_LAST_ANCHOR` is the primary supported cause
- Human verdict: A `HUMAN_FAIL`; B/C/D `NOT_EVALUATED`
- Production effect: none

## Purpose

本次实验原计划用固定四臂区分 `incompatible last anchor`、FL2VA endpoint constraint / lane mismatch、当前 AI-VIDEO T8 workflow recipe/pin bundle，以及尚未排除的 H3 model limitation。执行纪律要求每一臂的 exact MP4 落盘后，在下一次 submit 前完成 project-local `video-analysis` requirement-level Gate。

A 臂最初在 required Gate 中出现多个 `FAIL` 并停止。用户随后确认 A 的 forced transition 不可接受、动作与镜头突兀停止但人物保持，并明确要求自主完成原先固定的 B/C/D。该 continuation 只执行预先定义的实验臂，不是 repair retry，也没有扩展 seed 或 variants。

## Authorization And Guardrails

- 仅使用本机现有 ComfyUI / MiniMax H3 T8 runtime。
- Remote / paid submit count: `0`。
- Local submit count: `4`；retry count: `0`；fallback count: `0`。
- 未下载 model，未修改、升级或覆盖 ComfyUI/T8 checkout。
- 未修改 AI-VIDEO code、tests、workflow profile、plan、spec 或 production state。
- 未执行 retime、xfade、dissolve、interpolation 或其他视频后处理；contact sheet 和 frame metrics 仅用于分析。
- 未 commit、未 push。

## Runtime And Exact Inputs

- Experiment root: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr`
- ComfyUI: `0.33.0`, commit `e01fb4c56b7a88149d469b99cbbfe3223d715054`
- T8: `1.36.2`, commit `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`
- Seed: `6623081611478359059`
- Frame contract: `1344x768`, `124` frames, `24 fps`, expected `5.166666666666667s`
- Exact first frame: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/inputs/first_e0a_c50517a1.png`, SHA-256 `c50517a17313402ef271694ea058d6c92b0b750c4b854e39858bdaf5d73c5768`
- Problematic/current last frame: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/inputs/current_last_e0a_03f4c5eb.png`, SHA-256 `03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c`
- Motion-compatible last frame: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/inputs/compatible_last_frame096_c970d519.png`, SHA-256 `c970d51917dd828b33f875d6980a013c748886d64708e057cdef0970ebf5317d`
- FL2VA sealed prompt SHA-256: `f9d0f7492af21bbfd52e6affa8e1f93bc8b73982152ed046a38c0011d12e9e7a`
- I2VA deterministic adaptation prompt SHA-256: `b42e0bff352f3281fbfbd07d3e27c0aeac9be3c6bac926bdfd7749f3702b7d5f`

当前 AI-VIDEO profile 声明的 ComfyUI pin 为 `7cee3ceb`，实际 live runtime 为 `e01fb4c`。本实验同时固定 exact submitted workflow 与 live runtime identity，不把 profile 声明误当成当前 runtime truth，也没有为消除漂移而修改环境。

## Fixed Arms And Exact Workflow Bundles

| Arm | Conditioning / assets | Recipe bundle | Exact workflow |
| --- | --- | --- | --- |
| A `FL2VA_CURRENT_LAST` | first + problematic/current last | `minimax_h3_fl2va_pruned_int8_convrot.safetensors`; SHA-256 `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a`; no LoRA; `20` steps; `res_multistep`; `simple` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/workflows/A_FL2VA_CURRENT_LAST.submitted_workflow.json`; SHA-256 `dc6fcab269cc6723ec0fccf6afc339cc1666d45f5722e6c09fbef363183c0195` |
| B `FL2VA_COMPATIBLE_LAST` | same first + compatible last | same Stock20 bundle as A | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/workflows/B_FL2VA_COMPATIBLE_LAST.submitted_workflow.json`; SHA-256 `3264e4d35ebae353a98b57ad27441de4b586bab7de44935f3427f1b629014922` |
| C `I2VA_FIRST_ONLY` | same first; no last frame | same Stock20 core with only deterministic conditioning graph/prompt adaptation | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/workflows/C_I2VA_FIRST_ONLY.submitted_workflow.json`; SHA-256 `68d4d5722a44ff1df7f9f1337a7876056d386759c4dc6c1f2010c04b4bbd2425` |
| D `FL2VA_COMPATIBLE_UPSTREAM_RECIPE` | same first/last as B | upstream-current stable 4V4A bundle: `minimax_h3_fl2va_int8_convrot.safetensors`, SHA-256 `7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5`; LoRA `minimax_h3_turbo_4步加速ema_comfyui.safetensors`, SHA-256 `b07ab477437c6a525dfdaf11107722aad609975ac172f3b577a7a87b228ff7b3`, strength `1.0`; `4` steps; `dual_clock_euler`; `native_flow` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/workflows/D_FL2VA_COMPATIBLE_UPSTREAM_RECIPE.submitted_workflow.json`; SHA-256 `048089c95d966a237ed0fdfee1244d8014e0386b61d77f6ef3923e6333c637ef` |

D 的 exact upstream source 固定在 upstream commit `fb5d227ae38860d9c9438c72a2657944cd79e09d`，source workflow SHA-256 为 `86978f79fa786f1a6d160cf884330f82825205eed9f776d6b8f9848bd609f0c2`。当前已安装 nodes/models 的静态与 live schema 预检均通过，D 已按该 exact recipe bundle 完成。

## Arm A Execution Evidence

- Comfy prompt ID: `1f3d4307-614d-44b2-a921-a836e95952c6`
- Exact MP4: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/outputs/A_FL2VA_CURRENT_LAST.mp4`
- MP4 SHA-256: `182aef02cde3f7db24cc75d3b9612c6188e352fbb7977caee30bcee49b4ff81e`
- File size: `3493225` bytes
- Probe: H.264 High, `1344x768`, `24 fps`, `124` frames, `5.167s`; AAC stereo `32000 Hz`
- Full video decode: `PASS`
- Full audio decode: `PASS`
- Project-local `video-analysis` calls: `video_probe`, `video_review`, `video_extract_frames`, all bound to the exact absolute MP4 path after SHA-256 fixation
- MCP sampling summary: `167` sampled frames, `167` unique frames, `1` detected scene, audio present, tool-level `issues=[]`
- Exact evaluation sidecar: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/sidecars/A_FL2VA_CURRENT_LAST.evaluation.json`, SHA-256 `2281b3261872083cdc11f0214b3c34cac3c238891c98159a0d9eb5703a2eb1bc`

Tool success and a one-scene summary are not acceptance. Requirement-level findings control the per-Shot Gate.

## Requirement-Level Findings

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| forced scene/scale transition | `FAIL` | 约 frame `101 -> 102`（`4.25s`）从侧向 tracking composition 被迫替换为 clock/column endpoint composition。 |
| terminal snap | `FAIL` | 最大 luma MAD 为 `29.559415`，发生在 frame `101 -> 102`；sampled visual review 确认 terminal composition snap。 |
| tail velocity collapse / near-static tail | `FAIL` | frames `105-118` median-flow mean `0.005945`；frames `119-122` 为 `0.002851`；两个窗口中低于 `0.07` 的 transition 均为 `100%`。 |
| camera motion | `FAIL` | snap 后原本的 parallel tracking 被 near-locked terminal composition 替代。 |
| subject / identity stability | `PASS` | sampled frames 中同一短黑色 bob、芥末黄 raincoat、黑裤和红色 satchel 的女性保持可识别；仅为 technical finding，不是 HUMAN PASS。 |
| action endpoint adherence | `FAIL` | 画面接近 endpoint image，但没有保持到结尾的向右步行与 satchel motion。 |

分析 artifacts 位于 `analysis/A_contact_sheet_4fps.jpg`、`analysis/A_tail_contact_sheet_12fps.jpg` 和 `analysis/A_frame_metrics.json`，均相对于 experiment root。

## Four-Arm Results

| Arm | Technical result | Tail median-flow mean (`105-118` / `119-122`) | Exact MP4 |
| --- | --- | --- | --- |
| A | `FAIL`; forced terminal replacement, snap, tail collapse, camera stop and endpoint-action failure | `0.005945` / `0.002851` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/outputs/A_FL2VA_CURRENT_LAST.mp4`; SHA-256 `182aef02cde3f7db24cc75d3b9612c6188e352fbb7977caee30bcee49b4ff81e` |
| B | `PASS`; compatible anchor preserves continuous FL2VA tracking, gait and endpoint motion | `0.332924` / `0.338028` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/outputs/B_FL2VA_COMPATIBLE_LAST.mp4`; SHA-256 `be84342b8091da6cbb668270d21c01206f7479a6ef2f8f2ed7b297dde4346076` |
| C | `PASS`; first-only I2VA has no forced endpoint lock or tail collapse | `0.348433` / `0.305755` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/outputs/C_I2VA_FIRST_ONLY.mp4`; SHA-256 `d48952f5e718c0fca527e44b1b2cf8bf6f56a0664b8f708fc8bf8d0ade6d30ea` |
| D | `PASS`; upstream-current recipe bundle also preserves compatible-anchor motion | `0.326365` / `0.389043` | `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/outputs/D_FL2VA_COMPATIBLE_UPSTREAM_RECIPE.mp4`; SHA-256 `eba6c6de704795935362ee6f03c30213b78e7ff196d94af2fe72e028756d8c4f` |

四臂均为 H.264 `1344x768`、`24 fps`、`124` frames、`5.167s`，包含 AAC stereo audio，并通过 full video/audio decode。每个 exact MP4 在下一次 submit 前均调用 project-local `video-analysis` 的 `video_probe`、`video_review` 和 `video_extract_frames`。

## Attribution Assessment

| Candidate cause | Assessment | Evidence boundary |
| --- | --- | --- |
| incompatible last anchor | `SUPPORTED_AS_PRIMARY_CAUSE` | A 与 B 的 Stock20 recipe、seed、first frame、尺寸和 semantic intent 相同，仅 last anchor 不同；A FAIL、B PASS。 |
| FL2VA endpoint constraint / lane mismatch | `NOT_SUPPORTED_AS_GENERAL_CAUSE` | B 在 FL2VA + compatible last 下通过全部 technical findings；C 的 I2VA PASS 进一步说明移除 endpoint constraint 也安全，但不能把所有 FL2VA 使用一概判错。 |
| current AI-VIDEO T8 workflow recipe/pin bundle | `NOT_SUPPORTED_AS_PRIMARY_CAUSE` | B 使用 Stock20 PASS；D 使用不同的 upstream-current recipe bundle 也 PASS。因为 B 本身已通过，不能把 A 归因于 Stock20 bundle。 |
| H3 model limitation | `NOT_SUPPORTED` | B/C/D 在同一 seed 和高动作密度 intent 下均通过 required technical findings。单 seed 不能证明普遍能力，但当前没有 model-wide failure evidence。 |

结论只支持强的一阶 conditioning 效应：historical problematic/current last anchor 与当前运动状态不兼容，FL2VA 为满足该终点而在尾部执行突兀 composition replacement 并冻结动作。compatible same-scale/motion anchor 消除了该失败；I2VA first-only 和 upstream-current bundle 也都正常。该结果不否定或解决 v12 的跨 Shot semantic/causal continuity 问题。

## Human Verdict Boundary

- A: `HUMAN_FAIL`。用户确认 forced transition 不可接受；动作和镜头确实停止，而且非常突兀、没有缓冲；人物保持。
- B/C/D: 仅为 requirement-level technical `PASS`，没有被声明为 `HUMAN PASS`。
- 本实验没有修改 continuity/H3 plan、production state 或 acceptance truth。

## Durable Evidence And Publication State

- Experiment contract: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/sidecars/experiment_contract.json`
- Checkpoint summary: `/home/reggie/ai-video-experiments/h3-conditioning-attribution-20260827-vyhlrr/sidecars/checkpoint_summary.json`, SHA-256 `eecc5d5202ba8c0797f38416026f0a390987a91972b37c6bf1de37399646d92f`
- ComfyUI input copies: `/home/reggie/ComfyUI/input/h3_conditioning_attribution_20260827_vyhlrr/`; three files preserve the input SHA-256 values listed above.
- ComfyUI raw outputs: `/home/reggie/ComfyUI/output/development_experiment/h3_conditioning_attribution_20260827_vyhlrr/`; exact copied MP4 identities are listed in `Four-Arm Results`.
- Media and sidecars remain outside the repository.
- ComfyUI was stopped after confirming the queue was empty.
- No commit or push was performed; remote publication state is unchanged.
