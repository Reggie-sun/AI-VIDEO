# Shot Continuity E0-H Speaking Subtitle Quick Record

Date: 2026-08-25

## Purpose

本文记录一个独立的 Local MiniMax H3 T8 development experiment：在已验证的 beige-trench railway-station人物基础上生成 8 秒快速说话版，并把与实际生成语音一致的中文字幕确定性烧录到派生 MP4。

E0-H 不是 E0-G seed-only replication、retry或 Production continuation。它改变了 duration、resolution、Turbo、prompt、dialogue、conditioning task与subtitle composition，因此不能证明或推翻 E0-D/E0-G 的 replication verdict，也不产生 Production qualification、P6、Final Acceptance、active capability或 canonical reference。

## Experiment Contract

用户选择：

- 8 秒快速版，而不是完整 32 秒 continuity schedule；
- 固定普通话台词“我们快到了，再往前走一段。”；
- 中文字幕应与实际可听语音一致并烧录进交付视频。

Local generation surfaces：

- mode：`Hybrid`，以 full-scene image作为 exact first frame，并增加 identity crop reference；
- model：`minimax_h3_fl2va_int8_convrot.safetensors`；
- Turbo LoRA：`minimax_h3_turbo_4步加速ema_comfyui.safetensors`，strength `1.0`，SHA-256 `b07ab477437c6a525dfdaf11107722aad609975ac172f3b577a7a87b228ff7b3`；
- resolution：`736x416`；24 fps；192 frames；8.000 seconds；
- 4 steps；`dual_clock_euler/native_flow`；video/audio shift `12/3`；
- native audio；seed `320005`；CRF `18`；no remote Provider、no cloud fallback；
- corrected compact request SHA-256：`116bbb779fbfdf7627cb161d28408e6f7fc2cd4bb2d4a1e58b1f186433ce397a`；
- prompt UTF-8 bytes SHA-256：`caf249416456f360bbe42b9e4d752597edd6a0c3c32f1e97219be94643c60edf`。

Experiment-only inputs保持既有 bytes：

- full scene：`/home/reggie/ComfyUI/input/development_experiment_e0b_full_scene_20260824.png`，SHA-256 `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`；
- identity crop：`/home/reggie/ComfyUI/input/development_experiment_e0b_identity_crop_20260824.png`，SHA-256 `7e71030f3cad5e3049143be2169b5933711a80dbd277ea76025490b253dcafac`。

这些 references仍只属于 development experiment，不是 Production canonical assets。

## Runtime Result

第一次 local prompt POST（prompt ID `77395783-3a8a-4001-a3ab-795103d5c461`）在 node `MiniMaxH3AudioConditioningT8` 的 sampler 前验证阶段被拒绝：显式 `I2VA` 不允许同时携带 identity reference，必须使用 `Auto` 或 `Hybrid`。该 prompt没有进入 sampling、没有产生媒体或 GPU generation output。

随后只把 `task_type` 从 `I2VA` 修正为 `Hybrid`，其他 generation inputs保持；实际 sampling prompt ID为 `2630c1fd-1452-4f5c-9e3a-d0396d1fc314`，terminal status为 `success`。没有模型级 retry、fallback或额外 candidate。

Raw native-audio master：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0h_speaking_subtitle_quick_v1_seed320005_20260825_00001-audio.mp4
```

- SHA-256：`4a2b8ccbfc845e9e21ef5bffe0239b7cab1ab407207e15ba124daad4f108320c`；
- size：`1,436,394` bytes；
- H.264、`736x416`、24 fps、192 decoded frames、8.000-second video stream；
- AAC、32 kHz、stereo、8.000-second audio stream；
- full video decode与full audio decode均通过。

Burned-subtitle derivative：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0h_speaking_subtitle_quick_v1_seed320005_20260825_subtitled.mp4
```

- SHA-256：`7f3e066b30d98b026ba7111015d8e6fd328c459da4162b3147eadadc49243734`；
- size：`1,280,200` bytes；
- H.264、`736x416`、24 fps、192 decoded frames、8.000-second video stream；
- AAC、32 kHz、stereo、8.000-second audio stream；container duration `8.032` seconds；
- full video decode与full audio decode均通过；
- raw与subtitled MP4的decoded PCM SHA-256均为 `06fdafe94639ae72125db621af105f7fe587bf8d3bbab298b6da36f92726845f`，证明subtitle derivation未改变audio samples。

## Speech, Subtitle And Visual Evidence

T8 bundled faster-whisper model bytes存在，但当前 ComfyUI Python没有安装 `faster_whisper` package；本轮未联网安装dependency。改用本机已有 OpenAI Whisper `small` model进行单样本、local-only transcription：

```text
好,我们快到了,再往前走一段
```

ASR segment约为 `0.0--2.0` seconds，`no_speech_prob=0.0967`、`avg_logprob=-0.4254`。相对 requested exact words，模型在开头多生成一个“好”；因此 exact-dialogue prompt adherence不是严格 PASS。为了避免字幕与真实音频不一致，burned subtitle使用：

```text
好，我们快到了，再往前走一段。
```

字幕只覆盖开头人声段，后续画面不持续占屏。1 fps全片 contact inspection显示同一人物、short black bob、beige trench coat、red satchel、railway-station scene与screen-right行走方向保持；0--2 秒的4 fps face strip显示连续口型变化。以上是 sampled visual evidence，不等同于人工 full-speed lip-sync、voice naturalness或subtitle-timing acceptance。

## Assessment And Boundaries

Technical artifact verdict为 `PASS`：一个真实本地 H3 native-audio master和一个音频不变的burned-subtitle derivative均完成并通过完整解码。Exact spoken-text adherence有一项明确 concern：开头多出“好”。Human verdict仍为 pending，需要用户以正常速度、开启声音观看最终字幕版，并判断：

- 语音是否清晰、自然；
- 口型与人声是否主观同步；
- 字幕内容、出现时机与可读性是否合适；
- 人物步速、identity、wardrobe与场景是否可接受。

Provider/media effects：

- local prompt POST：2；其中1个pre-sampling validation error，1个successful sampling；
- local sampled candidate：1；raw MP4：1；deterministic subtitled derivative：1；
- model-level retry：0；fallback：0；remote submit：0；paid effect：0；
- Production code、Manifest、Registry、qualification、activation、P6与Final Acceptance effects：0。

完成后 ComfyUI queue为 `0/0`；本窗口 supervised loopback unit已停止，`127.0.0.1:8188`不再监听。

Next One Thing：由用户观看上述 subtitled MP4并给出human verdict。若用户接受，不再生成媒体；若不接受，必须根据明确的 voice、lip-sync、subtitle timing或walking-speed问题建立新的 bounded experiment，不能把本次结果自动升级为 Production evidence。

## Agent Guardrails

- 不得把 Whisper单样本 transcription当成稳定 Chinese speech capability claim。
- 不得把burned subtitle描述成 P4 canonical caption integration；它只是 development derivative。
- 不得隐去开头多生成的“好”，也不得宣称 exact spoken-text adherence PASS。
- 不得把本地 artifact success升级为 Production qualification、P6、Final Acceptance、active capability或 canonical reference。
