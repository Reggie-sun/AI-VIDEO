# T8 / MiniMax H3 Upstream Experiment Lessons

Date: 2026-08-24

## Purpose

本文是长期可复用的 **Development Knowledge / Experiment Evidence** 索引，用于未来设计 MiniMax H3 / T8 Shot Continuity、Long Video、identity、motion、camera、multi-segment 与 C4 实验时先核对作者已经运行过的 case、失败边界与 default-off 原因。

本文不是 Product Runtime contract、canonical spec、Harness / Gate、Provider qualification、active capability、P6 verdict 或 Final Acceptance owner。当前 runtime truth 仍由 code、tests、Manifest、sealed profiles、`docs/v0.2-runtime-baseline.md` 和 exact receipts 拥有。本文只引用 `AGENTS.md` 的 `Empirical Validation Priority`，不重述或扩张该治理规则。

## Source Snapshot

| Source | Snapshot | Reviewed scope |
| --- | --- | --- |
| `T8mars/comfyui-minimax-h3-audio-T8` | commit [`52ebb0d1f9786ad567e5b6379a92a0d011044ec5`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/tree/52ebb0d1f9786ad567e5b6379a92a0d011044ec5), package `1.45.0` | `README.md`, `docs/README_ComfyUI.md`, `features.json`, Long Video / Hybrid / MultiKeyframe reports and workflows, directly relevant source |
| `Larryvrh/ComfyUI-MiniMax-H3-Turbo` | commit [`4274783a23afcfdbea3b4876cb79effd6c510785`](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/tree/4274783a23afcfdbea3b4876cb79effd6c510785), package `1.2.3` | Turbo checkpoint/steps/base compatibility/audio guidance |
| `MiniMax-AI/MiniMax-H3` | commit [`d21241f0a4b3acbb34c97dae47fa417b7065e438`](https://github.com/MiniMax-AI/MiniMax-H3/tree/d21241f0a4b3acbb34c97dae47fa417b7065e438) | Official task/checkpoint and architecture boundary only |
| AI-VIDEO repository | HEAD at investigation start `aa2e8ce2615cb7b14a27e0842caf909737a525a7` | Existing governance, Shot Continuity spec/plan, runtime baseline and relevant records |

Primary upstream evidence anchors:

- T8 Long Video overview and warnings: [`examples/workflows/04-long-video/README.md`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md).
- T8 detailed author report: [`docs/README_ComfyUI.md`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md).
- T8 machine-readable experiment ledger: [`features.json`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json).
- Larry Turbo guidance: [`README.md`](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md).
- Official H3 task/architecture boundary: [`README.md`](https://github.com/MiniMax-AI/MiniMax-H3/blob/d21241f0a4b3acbb34c97dae47fa417b7065e438/README.md).

The snapshot is intentional. Future upstream changes do not silently update these conclusions.

## Evidence Classification

- `UPSTREAM_VERIFIED`: 上游作者明确记录了真实运行、受控对照、人工检查或报告结果。它仍只适用于记录的 exact material/profile/seed/hardware/conditions。
- `UPSTREAM_LIMITATION`: 上游作者明确记录失败、default-off、未验证、scope boundary 或不可宣传的结论。
- `AI_VIDEO_OBSERVED`: AI-VIDEO 自己已有的真实本地实验观察；不是上游作者结论。
- `AI_VIDEO_INFERENCE`: AI-VIDEO 根据上游与本地证据作出的 experiment-design 推论；不得改写成上游事实。

本文所有经验性结论均以前缀标记分类。`HEURISTIC` 只表示 advisory design hint，不是 Product invariant。

## Long Video Evidence

### 30–32 Seconds

- **UPSTREAM_VERIFIED** — T8 的 Long Video route 会把 segment 0 生成为 124 frames；22-frame context 的 continuation 通常贡献 102 new frames。作者实际完成过八段、exact 768-frame / 32.000-second AV chains，而不是只画出 workflow。[T8 detailed report lines 1107–1140](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1107-L1140)
- **UPSTREAM_VERIFIED** — 22-frame direct sampler latent 在一个受控 case 中优于只携带一张 last frame；video-VAE re-encode 没有优于 direct latent route，且耗时更长。这是单 case 的 context-route evidence，不是通用 quality ranking。[T8 detailed report lines 1080–1089](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1080-L1089)
- **UPSTREAM_VERIFIED** — `scene_plus_identity` 的 fixed 32-second / eight-segment chain完成 8/8 prompts，无 OOM/retry/cache reuse；continuation identity medians为 `0.699/0.639/0.644/0.609/0.737/0.601/0.574`，last/first retention ratio `0.821`。相对 legacy 与 full-scene persistent reference，identity proxy 均明显改善。[T8 `features.json` lines 2350–2357](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2350-L2357)
- **UPSTREAM_LIMITATION** — 同一 32-second `scene_plus_identity` chain 的预声明 relative-motion floor 失败：若干 continuation 的 flow-P90 ratio 低至约 `0.546/0.538`，temporal-MAD ratio 低至 `0.647`。两 fps strips 仍有球、手臂、姿态变化，所以不是 literal freeze，但 motion amplitude/trajectory regression 真实存在；feature 继续 `Experimental/default-off`。[T8 detailed report lines 1130–1140](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1130-L1140)
- **UPSTREAM_VERIFIED** — 两个未用于策略选择的新 32-second sources 也各完成 8/8 prompts。旗袍鼓舞 case 保持人物/服装/庭院与 active fan dance，但请求 120 BPM 的 descriptive estimate 约 104.17 BPM；two-women dialogue case 在 80 个 sampled frames 中同时检测到两个 source identities。[T8 `features.json` lines 2366–2370](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2366-L2370)
- **UPSTREAM_LIMITATION** — 未见过的 multi-person case 在 segment 6→7 从 full-body 跳到 close framing；ASR 找到目标短语但大量重复，mouth/audio proxy 不是 trained SyncNet evidence，不能证明 lip sync。两条 unseen source 的 mechanical completion 不关闭 rhythm、framing、dialogue 或 lip-sync gate。[T8 `features.json` lines 2368–2372](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2368-L2372)

### 60 Seconds

- **UPSTREAM_VERIFIED** — 作者完成过一条 uninterrupted 14-segment chain：`124 + 12*102 + 92 = 1440` frames，24 fps，exact 60.000-second video/audio/container。accepted-state、total-duration resume、atomic manifest、parent hash、explicit replacement/invalidation 与 composition route 有真实 execution evidence。[T8 detailed report lines 1315–1335](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1315-L1335)
- **UPSTREAM_VERIFIED** — Conservative Stock + DynamicVRAM headroom 2.0 profile又完成三个 independent cold-start base seeds，共 42/42 segments，无 OOM/retry/candidate reuse，并核对 manifest/parent/revision、accepted video/context hashes、1440 frames 与 1,920,000 samples。[T8 detailed report lines 1390–1406](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1390-L1406)
- **UPSTREAM_LIMITATION** — 三个 60-second timelines 全部积累 facial-age / identity drift，seed `2608083101` 最严重。Worst-seam contact 可没有 obvious hard cut，而人物仍然长期漂移；这直接证明 seam-local metric 与 long-term identity 是不同问题。[T8 detailed report lines 1407–1415](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1407-L1415)
- **UPSTREAM_LIMITATION** — 一个 60-second run 的 13 seams 可达到 MAD median/max `0.01618/0.01906` 与 SSIM median/min `0.96374/0.92868`，同时 14-segment timeline 仍出现 gradual appearance/exposure drift。Seam metric pass 不是 identity pass。[T8 detailed report lines 1325–1333](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1325-L1333)
- **UPSTREAM_LIMITATION** — `scene_plus_identity` 的 fixed 32-second chain虽然 identity proxy 显著改善，却因 motion floor 失败而拒绝进入 planned three-seed 60-second matrix。没有上游 evidence 表明该策略在 60 seconds 同时保持 identity 与 motion。[T8 `features.json` lines 2350–2357](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2350-L2357)

### Latent Tail, Accepted/Resume And Repair

- **UPSTREAM_VERIFIED** — 原生 latent concat 的低负载真实 probe 将 22+22 frames 合为一次 decode 的 39 frames，正确去除 overlap audio latent/sample；same-seed rerun byte-identical，并改善局部 video MAD 与 single-sample audio jump。[Long Video README lines 23–27](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md#L23-L27)
- **UPSTREAM_LIMITATION** — 上述 latent-concat segments 使用相关 prompts、不同 seeds，却没有把上一段画面/音频作为 continuation condition；它只证明 clocks、lossless PCM、single decode 与局部 smoothness signal，不证明 seamless long video、视觉连续性或省显存。[Long Video README lines 27–27](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md#L27)
- **UPSTREAM_VERIFIED** — `Accepted`/`Auto Resume` 是明确 review-first route；替换 segment N 会 invalidate N 之后所有 accepted segments，因为它们消费旧 parent context。NFE resume 只对 exact `dual_clock_euler + native_flow`、model/conditioning/seed/sigma/layout contract 证明逐位恢复。[Long Video README lines 35–52](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md#L35-L52)
- **UPSTREAM_VERIFIED** — Selective Repair 的 14-segment / 60-second chain survived six forced process exits；one real segment-7 repair generated 102 frames / 136,000 stereo samples and recomposed exact 1440-frame / 1,920,000-sample outputs。[T8 `features.json` lines 1733–1745](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L1733-L1745)
- **UPSTREAM_LIMITATION** — Selective repair 的 outgoing context continuity 仍 unresolved；mechanical repair/rollback 不等于修补后的 downstream identity/motion context 已重验。[T8 `features.json` lines 1752–1756](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L1752-L1756)

## Identity Lessons

- **UPSTREAM_LIMITATION** — Legacy 60-second multi-seed long video 已实证 long-term identity drift；不能以“segment seams 没硬切”否认这一失败。
- **UPSTREAM_VERIFIED** — Persistent full-scene first-frame reference 是 continuation-only reference；segment 0 仍由 exact `first_frame` 控制。它能在短链对部分 seeds 带来方向性 identity 改善，但 32-second identity depth 从 continuation 1 cosine `0.613` 下降到 continuation 7 `0.134`，没有解决深链漂移。[T8 detailed report lines 1107–1124](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1107-L1124)
- **UPSTREAM_VERIFIED** — Dedicated identity crop 在三 seed motion-rich short probes 中相对 legacy pooled cosine mean/median提高 `+0.08272/+0.09845`，54/59 paired detections更高；但一个 seed 相对 full-scene strategy回退，因此 crop不是无条件 winner。[T8 `features.json` lines 2335–2342](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2335-L2342)
- **UPSTREAM_VERIFIED** — `scene_plus_identity` 把 full scene 与 crop 作为两个独立 non-timeline references，与 motion keyframes 和 continuation-audio window 同时进入 continuation；短链三 seed 对 legacy/full-scene 的 identity proxy 都更好。[T8 `features.json` lines 2304–2308](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2304-L2308)
- **UPSTREAM_LIMITATION** — Reference blocks 会增加 sequence length/runtime/VRAM，并可能与 motion context 竞争；identity improvement 未满足 motion non-regression，所以 persistent strategies 保持 default-off。[T8 detailed report lines 1114–1140](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1114-L1140)

## Motion Lessons

- **UPSTREAM_VERIFIED** — 22-frame continuation context 是作者当前 balanced default candidate；5 frames有可重复 runtime/sampler-pool savings，但 absolute device-peak advantage不稳定，且较高 SSIM 可能只是 motion suppression。39 frames增加约 303–304 MiB sampler pool并出现一例 pose/framing jump与一例 severe identity/shot discontinuity。[T8 detailed report lines 1339–1388](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1339-L1388)
- **UPSTREAM_LIMITATION** — More context ≠ more continuity。5/22/39 frame choices都依赖 exact resolution/model/plugin/motion class；39-frame route为 `high_risk_experimental`，不是质量层级。
- **UPSTREAM_LIMITATION** — `scene_plus_identity` 不是 literal freeze，但低于预声明 motion floor。未来 experiment必须测量 action amplitude、trajectory、subject/camera velocity与 full-speed watchability，而不只做 frame uniqueness或 seam SSIM。
- **AI_VIDEO_INFERENCE** — Identity reference、motion tail、last-frame endpoint与 prompt 都在争夺有限 conditioning freedom。每增加一种约束，都应被当成新的 combination treatment，而不是把已有单项 PASS 相加。

## Camera / Framing Lessons

- **UPSTREAM_VERIFIED** — 22/39-frame context matrix 的人工检查记录过 visible pose/framing jump 与 severe identity/shot discontinuity；two-women 32-second chain也在 segment 6→7发生 full-body→close framing jump。[T8 `features.json` lines 2388–2399](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2388-L2399)
- **UPSTREAM_LIMITATION** — 上游证据没有独立校准 camera axis、camera path/velocity、FOV、subject scale或 framing retention。Latent seam、face cosine或检测到两个人，都不能证明 camera continuity。
- **AI_VIDEO_INFERENCE** — Camera continuity 的 evidence strength 明显弱于 mechanical segment completion和局部 identity proxy。AI-VIDEO C4必须自己用 full-speed review与专门 rubric检查 camera endpoint/path，而不能复用 identity或seam结论。

## Multi-Person / Dialogue / Lip-Sync Lessons

- **UPSTREAM_VERIFIED** — Two-women 32-second chain中两个 source identities在 80 sampled frames同时被检测到；ASR对两个目标 phrases可到 best WER 0。
- **UPSTREAM_LIMITATION** — 同一 case 出现 material framing jump、短语重复；mouth/audio proxy correlation `0.042/-0.008` 且 coverage不完整，不是 trained SyncNet，不能称为多角色稳定、dialogue fidelity或lip-sync PASS。[T8 `features.json` lines 2368–2372](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2368-L2372)
- **UPSTREAM_LIMITATION** — Same-scene single-character evidence不得外推到 multi-character blocking、speaker attribution、shot/reverse-shot、overlap speech或口型同步。

## Audio Lessons

- **UPSTREAM_VERIFIED** — H3 joint AV 使用 separate video/audio flow schedules；Larry记录 recent ComfyUI由 `ModelSamplingAV` 原生处理，而旧 ComfyUI 的单时钟 4-step sampler会过度推进 audio，造成失真。[Larry README lines 109–123](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md#L109-L123)
- **UPSTREAM_VERIFIED** — T8 Long Video保留 absolute sample accounting与可选短 bridge；bridge能大幅降低单采样 jump。
- **UPSTREAM_LIMITATION** — Bridge不能修复 adjacent-window level、timbre、speech semantics、rhythm或 lip sync。60-second three-seed chains 的最大相邻半秒 level gaps为 `23.59–48.06 dB`，descriptive NCC median仅 `0.127–0.206`，高频能量随链显著下降。[T8 detailed report lines 1407–1415](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/docs/README_ComfyUI.md#L1407-L1415)
- **UPSTREAM_LIMITATION** — Exact duration、dual-clock correctness、AAC presence和boundary jump改善不等于 speech intelligibility、speaker identity、music rhythm、perceptual continuity或lip sync。

## Hybrid / C4 Lessons

- **UPSTREAM_VERIFIED** — T8有两种易混淆的 `Hybrid`：task-Hybrid conditioning（例如 exact first frame + independent reference）与 model-Hybrid artifact（把 selected Ref2VA AdaLN rows作为小型patch施加到 FL2VA base）。两者不是同一概念。[T8 `features.json` lines 967–975](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L967-L975), [lines 2670–2715](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2670-L2715)
- **UPSTREAM_VERIFIED** — Model-Hybrid exact pruned FL2VA/Ref2VA pair的curve-aware artifact construction、fingerprints、100 offset-set operations、Stock20 mechanical runs和单 material/seed mixed-reference signal已通过。该 mixed case 的 face cosine `0.523`高于 FL/Ref controls `0.449/0.443`，WavLM `0.868`位于 controls `0.467/0.945`之间。[T8 `features.json` lines 2733–2744](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2733-L2744)
- **UPSTREAM_LIMITATION** — 这是单 material/seed Pareto signal，最低 headroom仅 `41.337 MiB`，没有完成 broad blind panel；不能称为 `best of both`、best-quality、max-reference、de-wax或 16GiB-safe。
- **UPSTREAM_LIMITATION** — Static video/audio AdaLN row replacement也会改变 target-stream modulation，不是“只增加 reference ability”。Hybrid必须在 LoRA前应用；full/pruned不可混用；selected AdaLN tensor若已有patch必须拒绝。[T8 `features.json` lines 2706–2715](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2706-L2715)
- **UPSTREAM_LIMITATION** — 官方 release本身提供两个 task-specific checkpoints：FL2VA支持 text/first/last-frame，Ref2VA支持 image/video/audio references；官方没有声明两者可以无条件合并成一个更强模型。[Official README lines 180–190](https://github.com/MiniMax-AI/MiniMax-H3/blob/d21241f0a4b3acbb34c97dae47fa417b7065e438/README.md#L180-L190)
- **AI_VIDEO_INFERENCE** — T8 task-Hybrid或model-Hybrid的 mechanical compatibility不是 AI-VIDEO `C4_MULTI_ANCHOR_MOTION_CONTINUITY` quality evidence。C4 exact first + last + identity image + motion video必须作为一个独立 treatment验证 cardinality、role semantics、identity、motion、camera和endpoint behavior。

## MultiKeyframe Lessons

- **UPSTREAM_VERIFIED** — T8 MultiKeyframe route机械支持 first/last之外 1–7 middle images，总 keyframe上限9；真实 probes覆盖 24-run memory/media matrix、最大七 middle anchors与有限 Stock20 position proxy。[T8 `features.json` lines 2572–2624](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2572-L2624)
- **UPSTREAM_LIMITATION** — 每帧 `visual_noise_aug`不是校准后的线性 similarity/strength；单变量 pilot只有 Spearman `rho=0.70`，未达到预声明 `rho>=0.8` gate。独立 keyframe strength calibration未关闭。
- **UPSTREAM_LIMITATION** — MultiKeyframe明确拒绝与 Long Video experimental model patch直接堆叠；必须有专门 compatibility path，不能叠两层未知 patch。[MultiKeyframe README lines 11–15](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/08-multi-keyframe/README.md#L11-L15)
- **UPSTREAM_LIMITATION** — MultiKeyframe 的 inspected FL2V four-step Turbo sample出现 melted/smeared；作者因此保留 Stock20为该 Advanced route的推荐质量路线，并明确拒绝把当前4-step result称为stable Turbo quality。[T8 `features.json` lines 2620–2632](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L2620-L2632)

## Prompt Relay / EAV / Selective Repair Lessons

- **UPSTREAM_VERIFIED** — Prompt Relay有针对 Long Video render window的独立 route；segment 0必须先真实保存 AV tail，再按 segment index继续。其 long-video coordinate projection与 patch order是mechanical contract，不是 prompt adherence或motion improvement proof。[Long Video README lines 54–63](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md#L54-L63)
- **UPSTREAM_LIMITATION** — Prompt Relay六种视觉任务的 same-input mechanical/media comparisons只证明 route与anchors未明显回退；不证明动作、identity、画质或音频改善。`joint_av_exp`是实验扩展，不是论文已验证能力。[T8 README lines 187–193](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/README.md#L187-L193)
- **UPSTREAM_VERIFIED** — EAV Long Video composer保持 Long Video为唯一 layout/context owner，EAV只拥有每 segment diffusion/attention route并验证 motion-keyframe offsets。
- **UPSTREAM_LIMITATION** — EAV + Long Video当前只完成 low-load deterministic contract与registration/import wiring；没有stress evidence，也不证明seam improvement、audio non-inferiority、speed、VRAM saving或通用16GiB safety。[T8 `features.json` lines 918–920](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/features.json#L918-L920), [Long Video README lines 62–67](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/52ebb0d1f9786ad567e5b6379a92a0d011044ec5/examples/workflows/04-long-video/README.md#L62-L67)
- **UPSTREAM_LIMITATION** — EAV + Long Video、Prompt Relay、Selective Repair各自存在不代表任意三者组合已通过；未知 patch owner、runtime state与outgoing context必须显式重验。

## Turbo Lessons

- **UPSTREAM_VERIFIED** — Larry推荐多数任务使用 `v4-600`；相对 `v1-850`，作者报告 static/small-motion、faces/fingers/texture micro-detail更好，早期 over-sharpen/plastic look得到修正。[Larry README lines 16–29](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md#L16-L29)
- **UPSTREAM_LIMITATION** — `v4` 的 static-frame enhancement 在 **4 steps + large/fast motion** 下可产生 motion smear/trailing ghosting；6–8 steps通常明显改善。狭窄的 4-step heavy-motion case，旧 `v1-850`可能更友好。
- **UPSTREAM_VERIFIED** — 推荐范围是 4–8 steps；4是 minimum，6–8通常优于4，超过8可能出现 over-sharp artifacts。Strength默认1.0；只对具体 smear/oversharp clip做小幅调整。[Larry README lines 75–85](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md#L75-L85)
- **UPSTREAM_VERIFIED** — Larry node声明支持 full `bf16/int8_convrot` 与 pruned/curve `pruned_int8/pruned_fp8` bases；`low_vram=on`在量化/pruned base上会因merge rounding变软。[Larry README lines 87–107](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md#L87-L107)
- **UPSTREAM_LIMITATION** — “conditioning graph unchanged”只说明 Turbo node能插入official T2V/I2V route；不证明每一种reference组合、Long Video、Hybrid C4或MultiKeyframe在Turbo下quality-compatible。作者仍把 audio 与 fast/intense motion列为 preview caveats。[Larry README lines 41–42](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo/blob/4274783a23afcfdbea3b4876cb79effd6c510785/README.md#L41-L42)
- **AI_VIDEO_INFERENCE** — 用4-step Turbo做 motion/continuity实验会把 checkpoint static enhancement、低NFE smear与conditioning strategy混在一起。若目标是判断 motion continuity，应优先冻结 Stock20或至少6–8-step control；否则“motion差”不能归因给 reference/C4策略。

## Non-Extrapolation Rules

- **AI_VIDEO_INFERENCE** — `A works` + `B works` ≠ `A+B works`。
- **AI_VIDEO_INFERENCE** — 5-second stable ≠ 32-second stable。
- **AI_VIDEO_INFERENCE** — Seam metric pass ≠ identity pass。
- **AI_VIDEO_INFERENCE** — Identity improvement ≠ motion non-regression。
- **AI_VIDEO_INFERENCE** — One seed ≠ robust capability。
- **AI_VIDEO_INFERENCE** — One source/prompt ≠ general capability。
- **AI_VIDEO_INFERENCE** — Same-scene single-character ≠ multi-character/dialogue。
- **AI_VIDEO_INFERENCE** — Long-video mechanical completion ≠ production-quality long video。
- **AI_VIDEO_INFERENCE** — First-frame persistent-reference evidence ≠ strong last-frame endpoint evidence。
- **AI_VIDEO_INFERENCE** — FL2VA evidence ≠ Hybrid C4 evidence。
- **AI_VIDEO_INFERENCE** — Reference support ≠ exact endpoint semantics。
- **AI_VIDEO_INFERENCE** — 32-second experimental success ≠ Production capability。
- **AI_VIDEO_INFERENCE** — Upstream workflow evidence ≠ AI-VIDEO exact stack qualification。
- **AI_VIDEO_INFERENCE** — Audio stream/duration/dual-clock correctness ≠ speech, speaker, rhythm or lip-sync acceptance。
- **AI_VIDEO_INFERENCE** — Detection of two identities in sampled frames ≠ stable multi-person blocking/framing。
- **AI_VIDEO_INFERENCE** — Accepted/resume/replay correctness ≠ perceptual continuity after repair or resume。

特别边界：

- **UPSTREAM_VERIFIED** — T8 `scene_plus_identity` 32-second evidence以 segment-0 exact `first_frame`、continuation full-scene/crop references、22-frame AV/motion context构成长链；该记录没有把 strong `last_frame` endpoint作为每段 long-video evidence的约束输入。
- **AI_VIDEO_INFERENCE** — 因此它不能外推到 `first_frame + last_frame + identity reference + motion reference + terminal-stop intent` 的 exact AI-VIDEO C4 regime。
- **AI_VIDEO_INFERENCE** — 更严格地说，AI-VIDEO E0-A本身只是 simpler FL2VA first+last treatment；它已显示 strong endpoint会压低terminal motion。未来 full four-anchor C4比E0-A约束更多，风险不会因为上游分别支持各个role而自动消失。

## AI-VIDEO E0-A Observation

Source: [`2026-08-24-shot-continuity-e0a-development-experiment.md`](./2026-08-24-shot-continuity-e0a-development-experiment.md).

- **AI_VIDEO_OBSERVED** — Exact baseline使用 strong A3 `last_frame`、`1344x768`、124 frames、24 fps、20 steps、Turbo off；technical execution成功，124 decoded frame hashes全部不同，所以不是padding/static duplication。
- **AI_VIDEO_OBSERVED** — 约 frames 102–107 已提前收敛到A3 endpoint pose；frames 107–123仍被真实采样，但 visible motion近乎collapse。Frames 105–119的 consecutive-frame MAD mean为 `0.248160`、median optical-flow mean为 `0.008383`；frames 120–123进一步降到 `0.069485` / `0.002880`。
- **AI_VIDEO_OBSERVED** — 当前定性是 technical execution `PASS`、motion quality `BORDERLINE`；不能据此进入长路线或Production qualification。
- **AI_VIDEO_OBSERVED** — 为避免篡改当前 record：baseline exact prompt **没有**“gradually slows down / comes to a stop”，而是要求 continuing gait。本文不纳入随后已执行的 prompt/endpoint A/B结果，因为本次知识文档的用户指定 E0-A scope只要求记录原 baseline observation。
- **AI_VIDEO_INFERENCE** — 原因尚不能仅由 baseline归结为 sampler、endpoint bytes、prompt interaction或多条件竞争；但它已经证明“technical sampling完成”不等于“terminal temporal block保留motion freedom”。

### Why Upstream Work Did Not Prevent E0-A

- **UPSTREAM_VERIFIED** — 上游 Long Video `scene_plus_identity` 证据主要连接 segment-0 `first_frame`、continuation identity references和22-frame motion/AV context；没有对应的强 `last_frame` endpoint treatment。
- **UPSTREAM_VERIFIED** — 上游已经发现更强 identity conditioning会压低 motion，并以预声明 motion floor失败保持 default-off。
- **AI_VIDEO_OBSERVED** — AI-VIDEO E0-A在更简单的 first+last FL2VA route中观察到 strong endpoint附近motion collapse。
- **AI_VIDEO_INFERENCE** — 所以这不是简单重复“作者已经解决的bug”，而是超出上游 treatment boundary 的 extrapolation failure。更完整的 first+last+identity+motion+terminal-stop C4组合仍必须由AI-VIDEO自己做最小empirical experiment。

## Practical Design Heuristics

以下均为 advisory only，不是 Product Runtime invariant：

- **AI_VIDEO_INFERENCE / HEURISTIC** — 若主要目标是long-term identity，可优先试 dedicated identity crop 或 `scene_plus_identity`，但必须同时冻结并检查 motion non-regression floor。
- **AI_VIDEO_INFERENCE / HEURISTIC** — Ordinary hard cut不要默认携带 latent/motion tail；只有 match-action 或 high-coupling boundary才值得承担强 motion continuation 的额外约束与成本。
- **AI_VIDEO_INFERENCE / HEURISTIC** — Strong `last_frame` endpoint必须单独检查terminal temporal window，不只看最后一帧是否命中。
- **AI_VIDEO_INFERENCE / HEURISTIC** — Prompt不要与endpoint contract重复施加强同方向约束；若需要stop，分别验证 endpoint、prompt与二者组合，避免把overconstraint误判为模型固有能力。
- **AI_VIDEO_INFERENCE / HEURISTIC** — 新 conditioning组合先做5-second / one-seed cheap falsification；只有没有fatal collapse时再进入32-second chain或multi-seed。
- **AI_VIDEO_INFERENCE / HEURISTIC** — Motion研究优先使用 Stock20或明确的6–8-step Turbo control；4-step heavy-motion preview容易污染归因。
- **AI_VIDEO_INFERENCE / HEURISTIC** — 只有便宜实验通过后再进入Production qualification、lifecycle/replay/recovery closure或promotion。
- **AI_VIDEO_INFERENCE / HEURISTIC** — Automatic seam/SSIM、unique frames、face detection与ASR不能替代identity、camera、motion、lip-sync和human watchability。
- **AI_VIDEO_INFERENCE / HEURISTIC** — MultiKeyframe、Long Video、Hybrid、EAV与Prompt Relay每增加一个patch owner，都应先做pairwise compatibility与single-variable falsification，不直接堆栈。

## Open Empirical Questions

- **AI_VIDEO_INFERENCE** — Strong `last_frame` 对terminal temporal block的因果影响多大，是否随endpoint pose、distance与duration变化？
- **AI_VIDEO_INFERENCE** — Motion-compatible endpoint是否普遍优于static/settled endpoint，还是只适用于当前walking material？
- **AI_VIDEO_INFERENCE** — Terminal-stop prompt何时放大collapse，何时只是无效；它与strong endpoint是否有interaction？
- **AI_VIDEO_INFERENCE** — Full four-anchor C4在32-second chain中的identity/motion trade-off是什么？
- **AI_VIDEO_INFERENCE** — Multi-character identity、blocking、composition与framing能否跨segments稳定？
- **AI_VIDEO_INFERENCE** — Dialogue语义、speaker attribution与trained lip-sync evidence能否同时通过？
- **AI_VIDEO_INFERENCE** — Camera axis/path/velocity、FOV和framing是否能在22-frame context与references竞争时保持？
- **AI_VIDEO_INFERENCE** — Cross-provider hard-cut boundary能否在same frozen rubric下保留identity、motion与camera，而非只命中first frame？

## When Future Agents Must Re-Experiment

下列任一 surface变化时，不得直接复用旧 PASS/FAIL；至少重跑能回答当前最大不确定性的最小实验：

- **AI_VIDEO_INFERENCE** — checkpoint/model bytes、FL2VA/Ref2VA/Hybrid recipe或AdaLN rows变化；
- **AI_VIDEO_INFERENCE** — workflow、node graph、patch order、plugin/ComfyUI version变化；
- **AI_VIDEO_INFERENCE** — sampler、scheduler、steps、LoRA/Turbo version/strength或DynamicVRAM policy变化；
- **AI_VIDEO_INFERENCE** — reference strategy、identity crop、reference count/order或motion-tail length变化；
- **AI_VIDEO_INFERENCE** — resolution、frame count、duration、context size或segment count变化；
- **AI_VIDEO_INFERENCE** — prompt contract、action/motion class、dialogue/rhythm要求或camera language变化；
- **AI_VIDEO_INFERENCE** — first/last-frame semantics、endpoint pose、terminal-stop intent或C4 anchor cardinality变化；
- **AI_VIDEO_INFERENCE** — single→multi-person、same-scene→scene change、low→heavy motion或static→moving camera变化；
- **AI_VIDEO_INFERENCE** — GPU/runtime/memory envelope或source material/seed population变化。

## Bottom Line

- **UPSTREAM_VERIFIED** — T8作者已经证明多段AV执行、22-frame context、accepted/resume、若干crash recovery、60-second mechanical completion，以及 `scene_plus_identity` 对特定32-second material的identity改善。
- **UPSTREAM_LIMITATION** — 同一证据也明确记录60-second multi-seed identity drift、identity-conditioning motion regression、multi-person framing jump、audio degradation、lip-sync未证明、Hybrid/MultiKeyframe/Turbo组合边界与多项default-off状态。
- **AI_VIDEO_INFERENCE** — “T8 long video已验证”只能表示这些 exact treatments 的 bounded evidence，不能推出新的 C4 conditioning组合成立。
- **AI_VIDEO_INFERENCE** — Future Agent必须先匹配 exact checkpoint/workflow/sampler/reference/duration/prompt/motion/camera profile；只要 treatment不等价，就回到最小 empirical falsification，而不是把 upstream workflow presence升级为AI-VIDEO capability或Production truth。
