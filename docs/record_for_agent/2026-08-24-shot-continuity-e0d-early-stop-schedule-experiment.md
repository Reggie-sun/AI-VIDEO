# Shot Continuity E0-D Early Stop Schedule Experiment Record

Date: 2026-08-24

## Purpose

本文记录 E0-C `HUMAN_REJECT / STOP` 后的一次 bounded Local T8 development experiment。实验只改变 `prompt_temporal_allocation`：把减速、停步与站定保持的 conditioning 提前；seed、reference strategy、interval、latent context、steps、sampler、resolution、时长与音视频拼接策略全部冻结。

本记录不是 Production qualification、P6、Final Acceptance、Provider capability activation 或 release evidence。E0-D 的 automated motion / prompt-adherence evidence 不能代替用户对 full-speed watchability、seam 与声音的最终判断。

## Frozen Contract

实验 identity：

- classification: `development_experiment`
- chain ID: `shot_continuity_e0d_early_stop_schedule_v1_seed320001_20260824`
- request SHA-256: `e3572fe61715da82449337e5398c51e7cf3633b31b9fde1e64e575e36f857161`
- background prompt SHA-256: `cca6c1ba5c9b053a2d3fa3a3ca372fc5dc4b50d0e02d9c2f9a31bfd515cd7eac`
- background job ID: `9280c1a9-9e75-40fa-839b-3017ce07d853`

Frozen generation surfaces：

- Local ComfyUI / MiniMax H3 T8 only；remote / paid Provider 未使用。
- `1344x768`、24 fps、target `770` frames / `32.083333 s`。
- Stock20、20 steps、`dual_clock_euler/native_flow`、video/audio shift `12/3`。
- Turbo LoRA off；model ID `minimax_h3_fl2va_int8_convrot_stock20_no_lora`。
- fixed seed `320001`。
- `ScenePlusIdentity` / `scene_plus_identity`、interval `1`。
- 22-frame video-and-audio latent context。
- `max_retries=0`、`replace_policy=reject_existing`、`compose_when_complete=true`。
- H.264 CRF `17`；audio seam policy `cosine_bridge`、bridge `5 ms`。

唯一变量 `prompt_temporal_allocation` 的 schedule：

| Segment | Timeline | Scheduled state |
| ---: | ---: | --- |
| 0--4 | `0--532` frames / `0--22.1667 s` | `steady` |
| 5 | `532--634` / `22.1667--26.4167 s` | `decelerate_early` |
| 6 | `634--736` / `26.4167--30.6667 s` | `stop_and_hold`；要求第一 third 完成减速、中点前双脚落地并停住，后半段保持 |
| 7 | `736--770` / `30.6667--32.0833 s` | `settled_hold`；不再迈步、滑移、漂移或重启步态 |

E0-C 的 segments 0--4 与 E0-D segments 0--4 的 accepted video SHA-256 逐段完全一致。context SHA 因新 chain provenance 不同。这把可归因变化严格限制在 frame `532` 之后的 schedule surface。

## Runtime Result

后台任务完成状态：

- state: `completed`
- accepted segments: `8`
- accepted frames: `124 + 102 + 102 + 102 + 102 + 102 + 102 + 34 = 770`
- retry: `0`
- fallback: `0`
- remote submit: `0`
- paid effect: `0`
- last error: empty
- completion 后 ComfyUI queue running / pending 均为 `0`；本次 supervised ComfyUI unit 已停止，`127.0.0.1:8188` 不再监听。

Exact assembled development artifact：

```text
/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0d_early_stop_schedule_v1_seed320001_20260824/assembled/development_experiment_shot_continuity_e0d_early_stop_schedule_v_e2686946d9af_r0008_cosine_bridge.mp4
```

- file SHA-256: `246dff16575421bbf1ab702ff1989d1c7de265935fb3a4ceeefe2903593dd480`
- file size: `17,468,639` bytes
- H.264 High、`1344x768`、24 fps、exact `770` frames、video duration `32.083333 s`
- AAC LC、32 kHz、stereo、audio/container duration `32.084 s`
- Manifest SHA-256: `417728bde77aea12717ead5a32756a60d7f98e1ff034a55661f16545bd883249`

Manifest 中全部 8 个 accepted MP4 与 7 个 non-final context artifact 均按记录的 SHA-256 重新校验通过。`ffmpeg` 对 final video 与 audio 的完整 decode 通过。Project-local `video-analysis` 确认 `770` frames、audio present、17 个 2 秒间隔采样帧和单一 scene；没有检测到 hard cut。这些属于 technical raw evidence，不拥有 human acceptance。

## Motion And Stop Assessment

沿用 E0-B / E0-C measurement：逐帧 resize 到 `336x192` grayscale；相邻帧计算 mean absolute difference 与 Farneback optical flow，记录每对帧 magnitude median 的 segment mean。

| Segment | Frames | MAD mean | Median-flow mean | P90 | Third means | Scheduled state |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0 | 124 | `8.7722` | `1.2523` | `1.5623` | `1.3851 / 1.2451 / 1.1265` | steady |
| 1 | 102 | `13.2205` | `1.5312` | `2.1291` | `1.2796 / 1.5682 / 1.7385` | steady |
| 2 | 102 | `13.0761` | `1.3217` | `1.8740` | `1.6125 / 1.2988 / 1.0622` | steady |
| 3 | 102 | `10.0921` | `0.9854` | `1.3383` | `0.9316 / 1.0402 / 0.9828` | steady |
| 4 | 102 | `10.1038` | `0.8787` | `1.1840` | `0.8956 / 0.8850 / 0.8561` | steady |
| 5 | 102 | `10.1949` | `0.7948` | `1.0570` | `0.7901 / 0.7963 / 0.7979` | decelerate early |
| 6 | 102 | `5.8375` | `0.3462` | `0.7606` | `0.6511 / 0.3439 / 0.0525` | stop and hold |
| 7 | 34 | `0.5056` | `0.0082` | `0.0174` | `0.0119 / 0.0079 / 0.0049` | settled hold |

segment 5 的三 thirds 没有形成可量化的 flow 下降，2 fps strip 也仍显示连续跨步，所以不能单独声称该段已明显减速。决定性变化发生在 segment 6：后半段 flow mean 为 `0.1134`，最后 10 frame-pairs 为 `0.0097`；4 fps strip 显示人物在中段完成最后一步，后段双脚站定。segment 7 flow mean 进一步降到 `0.0082`，最后 10 frame-pairs 为 `0.0051`，没有 gait restart。

24--32 秒的 0.5 秒 strip 显示人物完成最后一步后保持 exact screen-right standing pose 到 final frame；identity、short black bob、beige trench coat、red satchel、station scene 与 screen direction 保持。基于当前 automated / bounded visual evidence：

- motion preservation through the walking portion: `PASS` for this single-seed development experiment；
- final-stop and settled-hold adherence: `PASS` for automated evidence；
- human full-speed watchability / seam / audio verdict: pending；
- Production qualification、P6、Final Acceptance: not evaluated and not authorized。

## Seam And Audio Evidence

七个 boundary frame-pairs 相对各自局部 median 的 flow / MAD ratio：

| Seam time | Flow ratio | MAD ratio |
| ---: | ---: | ---: |
| `5.1667 s` | `1.2525x` | `1.3323x` |
| `9.4167 s` | `1.4075x` | `1.4417x` |
| `13.6667 s` | `1.3351x` | `1.3574x` |
| `17.9167 s` | `1.3983x` | `1.4741x` |
| `22.1667 s` | `1.4041x` | `1.3986x` |
| `26.4167 s` | `1.5001x` | `1.4019x` |
| `30.6667 s` | `6.3401x` | `4.5662x` |

最后一条 ratio 被已接近零的局部 hold motion 放大；其 absolute boundary flow / MAD 只有 `0.0593 / 3.1266`。逐 seam pairs 没有 hard cut、identity reset、wardrobe / satchel / scene replacement 或 screen-direction reversal，但 motion pulse 仍可量化，不得描述为 seamless。

Decoded audio 的七个 boundary single-sample step 均低于局部 derivative median，percentile 为约 `0.44--25.34`。20 ms seam 前后 RMS ratio 依次为 `1.1910x / 1.2168x / 1.3492x / 1.4395x / 1.2095x / 1.0262x / 1.0930x`。`cosine_bridge` 没有产生 click-like single-sample discontinuity，但 ambience texture / loudness 是否仍可听出分段必须由用户全速试听判断。

## Why E0-C STOP Is Unchanged

E0-C exact 770-frame bytes、final-step failure evidence 与用户 `HUMAN_REJECT / STOP` verdict 均未修改。E0-D 使用新的 chain ID、Manifest、accepted artifacts 与 final MP4；它是冻结单一 `prompt_temporal_allocation` surface 后的新反事实实验，不是对 E0-C artifact 的修补、重命名或重新解释。

E0-D 的结果支持“更早分配 stop conditioning 可以让本 seed 在 segment 6 中段自然停住并在 segment 7 保持”，但不能把这个 single-seed finding 扩写成普遍模型能力，也不能追认 E0-B / E0-C 为合格输出。

## Repository And Provider Effects

Repository effect：只新增本 experiment record。没有修改 Production code、qualification contract、Manifest / Registry、canonical reference、Harness policy、RAG implementation、push 或 release state。记录创建时其他窗口的 RAG / Seedance dirty work 保持未修改、未 stage、未纳入本记录 commit。

Provider / media effect：一次 unique Local ComfyUI submit，生成 8 个 accepted segments 与一个完整 770-frame development MP4；retry `0`、fallback `0`、remote `0`、paid `0`。E0-D bytes 未写入 Production Manifest / Registry，未激活为 Production candidate，也没有获得 P6 或 human Final Acceptance。

## Next One Thing

用户以支持硬解与 display-resample 的播放器按原速完整观看 exact E0-D MP4，重点检查：

1. 26.4--30.7 秒最后一步是否自然，而不是突然刹停或滑停；
2. 30.7--32.08 秒是否确实保持站定且没有姿态冻结感；
3. 17.9167、22.1667、26.4167 与 30.6667 秒 visual pulse 是否可接受；
4. 七个 seam 的 ambience 是否仍能被听出。

在用户给出 full-speed human verdict 前，不自动运行新 seed、retry、fallback、six-shot baseline、remote Provider 或 Production qualification，也不称 E0-D 为最终可交付成片。
