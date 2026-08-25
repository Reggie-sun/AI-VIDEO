# E0-L Cadence-Only LatentSync Experiment Record

Date: 2026-08-25

## Purpose

本文记录 T8 speaking source 的 E0-L cadence-only A/B development experiment。E0-K 的
SyncNet 虽然得到 `offset=0`、`confidence=4.34`，但用户已在正常速度观看后明确判定
“口形完全没有对上”。该 human verdict 为 `FAIL`，取代旧记录中的 `human verdict pending`；
不得继续把 E0-K 称为主观 lip-sync PASS。

本记录只属于 `Local development media experiment`，不是 Production qualification、P6、
Final Acceptance、active capability、canonical reference 或 runtime authorization。

## Frozen Contract And Single Variable

E0-L 冻结以下内容：

- E0-J video frames 与 visual source；
- exact dialogue `我们快到了，再往前走一段。` 与 voice identity；
- LatentSync checkout commit `a229c3948406bc2cf6eaf4873e662e70c6a04746`、v1.6 UNet、
  20 steps、guidance `1.5`、seed `1247`、512 resolution；
- InsightFace `detection + landmark_2d_106`、512 detector size、largest valid face route；
- subtitle text、font、position、display window 与 encode settings。

唯一主要变量是 dialogue cadence。只对 E0-J 实测发声区间应用 pitch-preserving
`atempo=0.83`，保留台词前停顿和台词后静默尾拍；没有慢放视频、重跑 T8、换 seed、换台词、
安装 dependency、调用 remote/paid Provider 或使用 fallback。

## Official Runtime Constraint

LatentSync v1.6 README要求 inference 前把视频规范为 25 fps、音频规范为 16 kHz，并说明
`inference_steps` 的公开范围为 20--50、`guidance_scale` 为 1.0--3.0。当前 checkout 的
`latentsync/pipelines/lipsync_pipeline.py::loop_video()` 明确在 audio chunks 长于 video
frames 时交替使用正序与逆序 frames。因此 E0-L 把“派生音频必须实测不长于视频”设为硬门槛，
而不是接受官方 ping-pong loop。

Official references：

- <https://github.com/bytedance/LatentSync/tree/a229c3948406bc2cf6eaf4873e662e70c6a04746>
- <https://github.com/bytedance/LatentSync/blob/a229c3948406bc2cf6eaf4873e662e70c6a04746/latentsync/pipelines/lipsync_pipeline.py>
- <https://ffmpeg.org/ffmpeg-filters.html#atempo>

`0.83` cadence 是本项目的 bounded hypothesis，不是 LatentSync 官方宣称的中文嘴型修复方案。

## Run Identity And Immutable Inputs

Run ID：

```text
shot-continuity-e0l-cadence083-latentsync16-20260825-v1
```

完整归档目录：

```text
/home/reggie/vscode_folder/AI-VIDEO/runs/shot-continuity-e0l-cadence083-latentsync16-20260825-v1/
```

关键输入 identity：

- E0-J source SHA-256：`be73b86125623a31e3a62c6e1c11eef40e211017cc3edde23e310f740c251f4e`；
- E0-K A baseline SHA-256：`26574a4285c25baa7747862e0f682a9c607656851931c71d03d2572c1f794bf3`；
- dialogue UTF-8 no-newline SHA-256：`7c3acebeb8e6c08830c1be5ea759780c8336bfe72b3ebe0ec02ad8e258f26a21`；
- request raw-file SHA-256：`8c813019c52b6164853ca0f0be884083265074c1684244ee84e544c1a2b41bd9`；
- canonical sorted request JSON SHA-256：`a9274045720170b51e40c0243d30b70b02a41efb158a4b8d92684a3d7634a71c`；
- derived WAV SHA-256：`8c7c8fb1b6a3cc58bb6db5979c2e04ea0c2e47992ed849d76d2c6b2645e43be9`；
- derived decoded PCM SHA-256：`91f130e8c4c2e06cca5aa5c39425c7d838254b9316b247768cd40e6754c60989`。

完整 request、commands、model/detector hashes、artifacts 与 checksums 在 run directory 中。

## Hard Gate Evidence

### Gate 1: No Audio-Longer-Than-Video Loop

- source VAD window：`1.8758125--3.7775625s`；
- derived VAD window：`1.87581--4.14425s`；
- derived audio：16 kHz mono PCM，`82432` samples，`5.152s`；
- LatentSync normalized video stream：25 fps，130 frames，`5.200s`；
- measured margin：`0.048s`。

Verdict：`PASS`。派生音频短于可用视频窗口，不应进入 official ping-pong branch。

### Gate 2: Post-`atempo` Remeasurement

- requested tempo factor：`0.83`；observed VAD-envelope factor：`0.8383514662`；
- post-stretch silent tail：`1.00775s`；
- median F0：source `209.3126Hz`，derived `206.1374Hz`，差 `-26.46 cents`；
- DTW-aligned MFCC-12 cosine mean：`0.9971601`，p10 `0.9970803`；
- spectral centroid ratio：`0.989882`；bandwidth ratio：`0.973758`；
- full WAV decode：`PASS`。

Verdict：technical audio `PASS`，因此才进入 LatentSync。该 verdict 不替代人工 voice identity
或 voice naturalness；二者仍为 pending。

## LatentSync And Decode Result

LatentSync 一次完成 `9/9` inference chunks，并完成 `130/130` face restoration。输出：

```text
runs/shot-continuity-e0l-cadence083-latentsync16-20260825-v1/media/e0l-latentsync16-cadence083.mp4
runs/shot-continuity-e0l-cadence083-latentsync16-20260825-v1/media/e0l-latentsync16-cadence083-burned-subtitles.mp4
```

- unburned SHA-256：`dcb8610d34d266261b33cc7d42d3bc8829d9e4261959679c61f24401df5c639d`；
- burned SHA-256：`3e8d1258e92ee5dba931e12cb7d0a480eb1d12fd020757dc3dd8b9d77a1784c2`；
- H.264，`1344x768`，25 fps，130 frames，video duration `5.200s`；
- AAC，16 kHz mono，audio duration `5.152s`；
- 两个主结果的 full video/audio decode 均为 `PASS`；
- burned/unburned decoded audio SHA-256 均为
  `89b55a72149e228d477c1bae611fc5b035bae954adee78554601d000cbc1a410`。

## SyncNet, Face Retention, And Mouth Shapes

| Evidence | A: E0-K | B: E0-L |
| --- | ---: | ---: |
| SyncNet AV offset | `0` | `0` |
| SyncNet confidence | `4.34` | `4.56` |
| Face retention | `130/130` | `130/130` |
| Human lip-sync verdict | `FAIL` | pending |

使用同一 LatentSync FaceDetector / InsightFace `landmark_2d_106` 对 A 与 B 全帧检测，并按
derived-audio VAD 内的 ordered RMS/spectral-onset anchors 对齐；A 的时间锚点通过 exact
`atempo` transform 反向映射，不使用字幕时间。Contact sheet：

```text
runs/shot-continuity-e0l-cadence083-latentsync16-20260825-v1/evaluation/mouth-shape-ab-contact-sheet.png
```

逐项证据：

- `们` `/m/`：B frames 47--49（`1.88--1.96s`）出现近闭合/收拢，随后 frames 50--51 release；
  inner aperture / mouth width 为 `0.0717`。支持双唇过渡，但非自动 phoneme classifier，保留
  alignment uncertainty。
- `我`：frames 47--49 有可见 pursing/narrowing，`SUPPORTED`。
- `往`：frames 83--87 有较弱 narrowing/rounding，`SUPPORTED_BUT_WEAK`。
- `到`：frames 55--59 明显开口，normalized inner aperture 从约 `0.1452` 到 `0.1884`，
  `SUPPORTED`。
- `段`：frames 100--104 的 normalized inner aperture 约 `0.0384--0.0555`，只有小幅开口变化，
  `MARGINAL`。
- final stop：最后声学 offset 为 `4.14425s`；frame 106 / `4.24s` 已闭口，约 `95.75ms`、
  2.4 frames 内停止持续 articulation，`PASS`。

Technical verdict：`MIXED_NOT_SUFFICIENT_FOR_LIP_SYNC_PASS`。SyncNet confidence 比 A 增加
`0.22`，但 `段` evidence 偏弱且 landmarks 不能代替语音音素分类，因此不得宣称技术或主观
lip-sync PASS。

## Human A/B Contract

正常速度串联评估片：

```text
runs/shot-continuity-e0l-cadence083-latentsync16-20260825-v1/evaluation/e0k-A_then_e0l-B-normal-speed.mp4
```

第一次不暂停、不逐帧，选择 A、B 或 TIE；第二次分别把 `们`闭唇、`我/往`收圆、`到/段`
开口、末字后及时停嘴、identity/face/voice naturalness 标为 `PASS`、`MARGINAL` 或 `FAIL`。
只有 required checks 无 `FAIL` 且正常速度总体令人信服，才可给 human lip-sync PASS。
Technical verdict 与 human verdict 必须保持独立。

## ComfyUI Queue-Race Incident

在 E0-L 提交前等待 GPU 独占时，ComfyUI queue 的只读检查显示一个既有任务完成；停止 service
前后的 race window 中又出现了新的 unrelated prompt。service stop 于新 prompt 开始约 55 秒后
中断该任务。日志没有提供足够安全重建的 exact request/prompt identity，也未发现对应完成媒体。

本轮没有猜测、恢复、重新提交或删除该 unrelated task。E0-L 只在 ComfyUI 已停止、GPU 空闲且
两条 audio hard gates 都通过后运行。该 incident 是明确的 remaining operational risk，不能被
E0-L 成功或任何 SyncNet 指标冲销。

## Final Boundary And Next One Thing

Provider/media effects：local FFmpeg audio derivative `1`；LatentSync derivative `1`；burned
subtitle derivative `1`；A→B evaluation derivative `1`；remote/paid submit `0`；fallback `0`；
T8 rerun `0`。Production code、Manifest、Registry、runtime baseline、spec、plan、qualification、
activation、P6 与 Final Acceptance effects 全部为 `0`。

Next One Thing：用户观看正常速度 A→B 评估片，为 E0-L B 提供 human lip-sync 与 voice
naturalness verdict。没有新的明确授权时，不生成 E0-M、不改变 cadence/model/settings，也不把
本次 development evidence 升级为 Production truth。
