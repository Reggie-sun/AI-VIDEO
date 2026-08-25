# Shot Continuity E0-I High-Quality Speaking Record

Date: 2026-08-25

## Purpose

本文记录一个独立的 Local MiniMax H3 T8 development experiment。E0-I直接回应E0-H的人审问题：人物在后段出现倒步/方向不稳，且`736x416` Turbo4画面过于模糊。E0-I保留同一人物、station scene、seed `320005`与普通话台词，删除转头和画外同伴动作，改用高画质Stock20短镜头验证稳定screen-right行走、说话与字幕。

E0-I不是E0-H retry、E0-G replication或Production qualification。它同时改变prompt、duration、resolution、sampling profile、conditioning mode与subtitle treatment，因此只能作为新的development evidence。

## Contract And Prompt Correction

E0-H prompt虽然语义可读，但同时要求行走、转头看画外同伴、说话、口型与侧向跟拍，也没有明确禁止pivot/backpedal。E0-I删除画外同伴与转头，并明确冻结：

- face、chest、hips、knees与toes始终朝screen right；
- 每次foot plant都落在比前一次更靠screen right的位置；
- 禁止pivot、turn around、step backward、backpedal、sideways slide与walk in place；
- camera只向screen right同速跟拍，不得reverse；
- 说话时不得转头或转身，只允许自然lip/jaw motion。

Generation surfaces：

- local ComfyUI / MiniMax H3 only；no remote Provider、no paid call、no fallback；
- model：`minimax_h3_fl2va_pruned_int8_convrot.safetensors`，SHA-256 `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a`；
- first-frame I2V；experiment-only input `/home/reggie/ComfyUI/input/development_experiment_e0b_full_scene_20260824.png`，SHA-256 `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`；
- `1344x768`、24 fps、124 frames、target约5.1667 seconds；
- Stock20、Turbo LoRA off、`res_multistep/simple`、seed `320005`；
- raw output CRF `17`；native audio；fixed requested dialogue“我们快到了，再往前走一段。”；
- prompt UTF-8 bytes SHA-256：`d8c342fac50bafbae28fad2bdd8b66cb52803a7226be7c201e9549fe4bd8a04d`；
- compact request SHA-256：`bfc5d36d85f9f32637498de4edd62ce6880c57c8ea1ee3c5e0e91df3b8515fbd`。

此前focused `retrieve-ai-video-memory`已严格失败为`index embedding identity mismatch`。本轮按既有fail-closed合同不rebuild、不降低validation、不重复检索；所有结论只使用当前exact request、runtime history与真实媒体证据。

## Runtime Result

唯一local submit的prompt ID为`637cdcd5-87a4-41f1-a719-19754fd5a703`，`node_errors={}`，terminal status为`success`。从`execution_start`到`execution_success`约`380.554` seconds。没有第二个submit、模型级retry、fallback或额外candidate。

Raw high-quality native-audio master：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0i_speaking_direction_quality_v1_seed320005_20260825_00001_.mp4
```

- SHA-256：`9399a1c357462102868050cff84e72d1b83680647ce34ca8156955a2b8b9fa41`；
- size：`2,131,016` bytes；
- H.264、`1344x768`、24 fps、124 decoded frames、5.166667-second video stream；
- AAC、32 kHz、stereo、5.167-second audio stream；
- full video decode与full audio decode均通过。

High-quality burned-subtitle derivative：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0i_speaking_direction_quality_v1_seed320005_20260825_burned_subtitles.mp4
```

- SHA-256：`5dcd53252015f128ae5357f0c5c1d29301bc4fe1c66a60c45db1790c68002ab7`；
- size：`4,009,864` bytes；
- video bitrate约`6.07 Mbps`，CRF `12`；H.264、`1344x768`、24 fps、124 decoded frames；
- AAC stream直接copy；container duration `5.199` seconds；
- 3秒后无字幕区相对raw的SSIM为`0.994889`。

Selectable subtitle-track derivative：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0i_speaking_direction_quality_v1_seed320005_20260825_subtitle_track.mp4
```

- SHA-256：`da2c271d5eafe76aed8a9c0a9f6bcbf956b9731f54f52f923e909f5d6708c4ac`；
- size：`2,127,408` bytes；
- raw与subtitle-track MP4的extracted H.264 packet SHA-256均为`1bc437698aa40ff93f59f928714c9530cad51ce7eb70c6948aca9d73683f04f0`，因此该派生没有重编码video；
- `mov_text` subtitle stream为language `chi`，duration `2.500` seconds，需要播放器启用subtitle track。

raw、burned与subtitle-track三份MP4的decoded PCM SHA-256均为`7e463e43435cd2b0fb3bfde98e0cb6e4a06e470e5f39707dfdffc8f9c0f3fce3`，证明两种subtitle derivation均未改变audio samples。

## Direction, Sharpness And Speech Evidence

4 fps全片strip与最后1.4秒的8 fps strip显示人物保持side profile和screen-right gait，没有观察到E0-H式回身、倒步或camera reversal。该结论是bounded sampled visual evidence；完整full-speed human motion verdict仍由用户拥有。

将E0-H与E0-I raw frames统一resize到`736x416`后计算grayscale Laplacian variance：

| Artifact | Mean | Median | P10 |
| --- | ---: | ---: | ---: |
| E0-H `736x416` Turbo4 raw | `86.30` | `85.34` | `76.91` |
| E0-I `1344x768` Stock20 raw | `133.55` | `136.59` | `116.29` |

E0-I same-scale median约比E0-H高`60%`，与contact sheet中更清楚的hair、face edge、coat、satchel与station detail一致。该metric只证明相对spatial sharpness改善，不等同于human watchability或identity acceptance。

本机OpenAI Whisper对同一native audio的转写存在模型差异：

- `base`：`我们快到了 再往前走一段`；
- `small`：`只有我们快到了再往前走一段`；
- `tiny`：`因為我們快到了 再往前走一段`。

因此burned与selectable字幕都使用用户批准的固定文本“我们快到了，再往前走一段。”，但不能宣称exact spoken-text adherence已自动PASS。开头音节、voice naturalness、audibility与lip sync仍需人工开启声音观看。

## Assessment And Boundaries

Technical artifact verdict为`PASS`：raw、burned与selectable-subtitle三份MP4均存在，video/audio完整解码通过，direction sampled evidence通过，清晰度相对E0-H显著改善，subtitle derivation保持exact audio samples。Human verdict仍为pending。

Provider/media effects：

- local submit：1；successful sampled candidate：1；
- model-level retry：0；fallback：0；remote submit：0；paid effect：0；
- raw MP4：1；deterministic subtitle derivatives：2；
- Production code、Manifest、Registry、qualification、activation、P6与Final Acceptance effects：0。

完成后ComfyUI queue为`0/0`；本窗口supervised loopback unit已停止，`127.0.0.1:8188`不再监听。

Next One Thing：用户以正常速度、开启声音观看burned-subtitle MP4，并判断screen direction、sharpness、voice、lip sync与subtitle timing。没有新的明确缺陷和授权时，不再生成development media。

## Agent Guardrails

- 不得把sampled direction strip替代human full-speed gait acceptance。
- 不得把ASR模型分歧隐藏为exact dialogue PASS。
- 不得把burned subtitle或`mov_text` derivative描述成P4 canonical caption integration。
- 不得把本地technical PASS升级为Production qualification、P6、Final Acceptance、active capability或canonical reference。
