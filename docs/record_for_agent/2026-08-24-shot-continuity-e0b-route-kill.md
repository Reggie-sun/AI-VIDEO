# Shot Continuity E0-B Route-Kill Record

Date: 2026-08-24

## Purpose

本文记录 Shot Continuity `E0-B` 的第一次真实 Local T8 empirical route-kill。它只回答当前 `ScenePlusIdentity + 22-frame latent context + Stock20` 路线是否值得继续生成完整 32 秒长镜头。

本轮分类为 `development_experiment`。本文不是 Production qualification evidence、active capability、winner evidence、P6 Final Acceptance、`C4_DESTINATION_READY`、replay proof 或 production validation snapshot。

## Experiment Classification

- execution：local ComfyUI / MiniMax H3 T8 only；没有 remote Provider、paid API、cloud egress、fallback 或 retry；
- intended output：`1344x768`、24 fps、770 frames、32.083333 seconds；
- actual route decision：`STOP`；
- accepted partial evidence：3 个连续 segments，共 328 frames；第 4 段在 6/20 steps 时按 route-kill stop condition targeted cancel；
- complete 770-frame output：不存在。

## Experiment-Only Reference Materialization

冻结的 beige-trench reference 在执行前仍没有 materialized bytes。为避免复用 mustard-raincoat E0-A bytes，本轮用本机 Qwen Image Edit 2511 对既有 rainy-station character reference 做一次 local-only materialization：保持 short black bob、人物身份和 red satchel，将 wardrobe/scene 改为 beige trench coat 与 indoor station concourse。

- source：`/home/reggie/ComfyUI/input/03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c.png`；
- single local Qwen prompt ID：`9e7a1dbe-4526-4f1f-aeaf-ba7e1534060c`；terminal status `success`；没有 retry；
- raw Qwen output：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0b_reference_20260824_00001_.png`，SHA-256 `fdea4378077eab3f6f00586260e496dd06121ff456b74991ee9ea3e6a34c6592`；
- full-scene input：`/home/reggie/ComfyUI/input/development_experiment_e0b_full_scene_20260824.png`，SHA-256 `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`；
- identity crop：`/home/reggie/ComfyUI/input/development_experiment_e0b_identity_crop_20260824.png`，SHA-256 `7e71030f3cad5e3049143be2169b5933711a80dbd277ea76025490b253dcafac`。

这两份输入是本轮 Agent 选择的 experiment-only reference candidate，不是用户明确批准的 Production canonical reference，也没有写入 Production Manifest / Registry。后续不得把它们升级为正式 reference truth。

## Exact Local Stack And Request

- ComfyUI `0.33.2`，commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- MiniMax H3 T8 plugin commit `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`；
- diffusion model `minimax_h3_fl2va_int8_convrot.safetensors`，SHA-256 `7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5`；
- CLIP `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`，SHA-256 `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6`；
- video VAE SHA-256 `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522`；
- audio VAE SHA-256 `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48`；
- Turbo LoRA off；20 steps；`dual_clock_euler/native_flow`；video/audio shifts `12/3`；native audio；CRF 17；
- `ScenePlusIdentity`，22-frame AV latent context，persistent identity interval 1；
- seed `320001`，fixed across continuation segments；
- frozen prompt SHA-256 `d65e4f9337c8f5b26854b3f413e61a6485ae1d2ab288bce3a87739fbcae1f22b`；
- API request SHA-256 `c3008cb8433ab38a48ed49c5d2b5b2f9ce0bb79fcb335a442021057e790271a8`；canonicalized prompt graph SHA-256 `2f300b87845969f15e8d490a4a30544bd2cb00e10363ce106540aca423bf2eb4`；
- background chain：`shot_continuity_e0b_seed320001_20260824`，`max_retries=0`，release policy `unload_all_models`。

完整 prompt 继续由 `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md` 拥有；本文只记录 hash，不复制第二份 prompt owner。

## Runtime Evidence And Early Stop

初始 local prompt ID 为 `c6627c82-c550-4e81-9a06-1e008fa6c7de`。Background controller 顺序提交 continuation；没有并发 segment、retry 或 fallback。Manifest 位于：

`/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0b_seed320001_20260824/manifest.json`

取消前 manifest revision 为 3：

| Segment | Frames | Timeline | MP4 SHA-256 | Motion MAD mean | Median-flow mean | Flow P90 |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| 0 | 124 | 0–123 | `b581e5e1f86cd95358f3d75a5108958d62b5cff4cd8a62e34e310d3bcbbf502d` | 7.0075 | 0.9780 | 1.5559 |
| 1 | 102 | 124–225 | `379d6a949fe045bda4c9bede3eac1663191d8485ae582e5a2d9d019f18f148ec` | 2.2827 | 0.1852 | 0.3071 |
| 2 | 102 | 226–327 | `4a6f06ba216c1aae3e5a8a3b806eead8c77b2691de524edebba8c224941938fe` | 0.6353 | 0.0348 | 0.0579 |

2 fps 与 1 fps strips 显示 identity、beige trench coat、red satchel、station scene 和 screen-right framing 基本稳定，没有明显 hard cut、teleport、gross anatomy collapse 或新 scene；但人物在第一个 continuation 已明显减速，第二个 continuation 几乎维持同一位置和步态。相对 segment 0，segment 2 的 median-flow mean 只剩约 3.6%，而 frozen Shot contract 要求 medium walking 直到 near-end 才自然停止。

这构成明确的 early motion-collapse route-kill。第 4 段 prompt ID `9efcfc27-58e4-4efb-bd6e-399dcaab4c7b` 在 6/20 steps 时通过 targeted background cancel 中断；它没有 candidate、没有 manifest acceptance。最终 background state 为 `cancelled`、accepted count 3、retry count 0、queue empty。

## Review Artifacts

- exact-frame partial preview：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0b_seed320001_STOP_partial_328f_exact.mp4`；SHA-256 `ad9202148c0da788cc147c0f7ce83339254984439e201192080f6f30ebbbdbe0`；
- video stream：H.264，1344x768，24 fps，328 frames，13.666667 seconds；
- audio stream：AAC，32 kHz stereo，13.673 seconds；
- 1 fps contact sheet：`/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0b_seed320001_STOP_partial_1fps_contact.jpg`；SHA-256 `555f5b78d12ee777353da9ac292920c387e3b4a28d4d98e4d8983257c4be401e`。

Partial preview 只拼接已接受 segments，未生成新画面。它用于观看 STOP 原因，不是完整 E0-B output、winner evidence 或 final delivery。

## Provider And Effect Accounting

- local reference materialization prompt count：1；
- E0-B local H3 prompt count：4（3 succeeded/accepted，1 targeted interrupted）；
- complete E0-B output count：0；
- retry count：0；
- fallback count：0；
- remote submit count：0；
- paid effect count：0。

## Assessment

E0-B verdict 为 `STOP`。当前 exact long-video route 在 identity 与 scene stability 上有希望，但 strong persistent scene/identity conditioning 与 frozen stop-oriented prompt 的组合在第一个 continuation 后迅速吞掉动作幅度。此次停止发生在 328/770 frames，避免继续生成已明显不满足 medium-motion rubric 的其余 442 frames。

该结果不证明 Local H3 的 normal 124-frame Shot 或 six-shot hard-cut baseline 不可行。它只否决当前 `ScenePlusIdentity + interval 1 + frozen stop prompt + Stock20` 的 32-second single-take route。E0-A motion-compatible endpoint 的短镜头改善证据仍然有效，两项实验回答不同问题。

## Production Impact And Next One Thing

现有 Production qualification gates 全部保持原状态。E0-B STOP 不关闭 materialization、permit、lifecycle、replay、recovery、qualification、P6 或 human acceptance，也不创建 active capability、winner、Production child 或 M1 artifact。

Next One Thing：重新评估 Local T8 long-video motion-conditioning strategy，在任何 seed `320002`、降分辨率、缩短时长、降低 motion、打开 Turbo 或 six-shot baseline 之前，先形成一个只改变单一 motion-preservation surface 的新实验合同。不得把本次 seed `320001` 以换参数方式补考。

## Agent Guardrails

- 不得把 328-frame partial preview 描述成 32-second output。
- 不得运行 seeds `320002`、`320003`、`320004`；first seed 已明确 `STOP`。
- 不得用 lower resolution、shorter duration、weaker motion、Turbo、different prompt 或 fallback 改写本次 verdict。
- 不得把 experiment-only Qwen reference 写入 Production Manifest / Registry 或称为 approved canonical reference。
- 不得把 stable identity/scene contact strips 替代完整主观视觉验收；本轮 verdict 只针对明显 early motion collapse。
