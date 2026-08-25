# Qingyan Miao T8 Motion Smoothness Record

Date: 2026-08-25

> **Supersession notice (2026-08-25):** The interrupted portrait attempt described
> below remains historical and still has unknown outcome. A later, separate
> seven-shot portrait batch is recorded in
> `2026-08-25-qingyan-miao-t8-portrait-batch-diagnosis.md`. That newer record
> supersedes only the next-work/status implication that no portrait clips had
> landed; it does not turn the new development clips into Production,
> P6, Final Acceptance, or a smoothness PASS.

## Purpose

本文记录青颜苗家女孩广告在继续制作前的 Local MiniMax H3 T8 `Stock20`
development experiments。前两次按当时 accepted scope 验证横屏单镜头行走；随后经用户纠正并由
当前 T8 节点源码确认，增加一次原生 portrait canvas 尝试。本文不生成产品喷洒镜头，也不把
任何结果扩展为完整广告、Production candidate、P6 或 Final Acceptance。

## Portrait Capability Correction

当前 T8/H3 backend 并未把 tensor shape 固定为 16:9：

- `MiniMaxH3AudioConditioningT8` 和 `MiniMaxH3PreflightT8` 的 `width` / `height` 均以
  `32` 为 step；
- `empty_av_latent()` 只要求两轴为 32 的倍数，并以
  `(height // 16, width // 16)` 动态构造 video latent；
- conditioning 会按传入 canvas resize first/last frame，并动态记录 `latent_h` / `latent_w`；
- 当前 Turbo README 同样声明 width / height 为 32 的倍数，short edge 通常为 768。

因此此前“底层 tensor 只能 16:9”的判断错误，应撤回。当前 AI-VIDEO sealed V2 profiles 固定
`1344x768` 只是现有 adapter/profile contract，不代表 T8/H3 backend 缺少 portrait 能力。
`768x1344` 可以作为原生 portrait generation canvas；它不是数学上 exact 9:16，最终可由
canonical composition 中心裁切为 `756x1344` 后再 resize 到 `1080x1920`。未经新的 sealed
profile、runtime preflight 与 live evidence，不把 development-side portrait 支持升级为当前
Production capability。

## Experiment Contract

两次实验均固定以下 generation surface：

- local loopback ComfyUI only；remote submit、paid call 与 Provider fallback 均为零；
- `MiniMaxH3AudioConditioningT8 -> MiniMaxH3DualClockSamplerT8 -> MiniMaxH3AVDecodeT8`；
- `minimax_h3_fl2va_pruned_int8_convrot.safetensors`，Turbo LoRA off；
- `1344x768`、24 fps、124 frames、约 5.167 seconds；
- `Stock20`、`res_multistep/simple`、native audio、CRF 17；
- exact ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- exact T8 checkout commit `28cb160827c245b2d6a37539df30c1d7c5e7aecd`。

第一次采用中景侧向跟拍，seed `8252026`，验证上半身、背景视差和连续行走。第二次是
新的隔离假设而非 blind retry：seed `8252027`，要求真正全身入镜、双脚可见、固定机位、
四步匀速行走，用来区分相机跟拍问题与人物步态/生成时序问题。

这两次 submission 通过 task-owned development caller 调用 loopback `ComfyClient`，没有进入
`VideoGenerationService.submit_local_once()`、Production Manifest、Registry、Dependency Graph、
candidate activation 或 recovery。因此它们只能作为 development media evidence，不能升级为
canonical Production Provider evidence。

## Runtime Evidence

第一条中景样片：

```text
artifacts/qingyan-miao-ad-20260825/runtime/t8_smoothness/qingyan-miao-t8-stock20-smoothness.mp4
```

- SHA-256 `28f558396bfb46d3e4c5a51859d542478417fff1c551c11423c391c41606d442`；
- `4,284,181` bytes；H.264 `1344x768@24fps`，124 frames；
- AAC 32 kHz stereo；container duration `5.167` seconds；
- unique local submit `1`，retry/fallback `0/0`，wall time `344.413` seconds。

第二条全身隔离样片：

```text
artifacts/qingyan-miao-ad-20260825/runtime/t8_smoothness/qingyan-miao-t8-stock20-fullbody-smoothness.mp4
```

- SHA-256 `5bfdac52405d7b56e940ddccd5bc47e38fffd4589733f892b95220ae33f5c496`；
- `2,393,681` bytes；H.264 `1344x768@24fps`，124 frames；
- AAC 32 kHz stereo；container duration `5.167` seconds；
- unique local submit `1`，retry/fallback `0/0`，wall time `348.406` seconds。

两条 MP4 的 video/audio full decode 均通过，逐帧 PTS 间隔保持
`0.041666–0.041667` seconds，各自 124 个 decoded frame hash 全部唯一。Project-local
`video-analysis` 对第一条报告 one scene、166/166 sampled frames unique、无 heuristic issue；
这些事实只证明容器时序和帧列完整，不证明内容运动流畅。

## Interrupted Portrait Attempt

第三次尝试只改变画幅和竖屏构图，保持 `Stock20`、124 frames、24 fps、
`res_multistep/simple` 与 T8-only graph 不变：

- requested canvas `768x1344`；seed `8252028`；
- intended submitted graph SHA-256
  `33dc0b553166e89e5c83925242e4624678f07bc37bad6f4b3f82cf413f558988`；
- prompt SHA-256 `af3fa8b99bd7f8bd005adc22da82b077536feec101bdca7a6c99eacf0da2fdba`；
- ComfyUI journal confirms the prompt was accepted at `2026-08-25 19:24:52 +08:00`；
- the shared supervised unit was stopped at `19:27:28` while this prompt was still executing；
- no `Prompt executed` event、final output、temp output 或 receipt exists for this attempt。

该 attempt 是“已提交、执行中被外部 stop、无 durable result”的 unknown outcome。runner 的
local polling process was interrupted only after the loopback listener disappeared；没有提交第二次
request。按 fail-closed contract，不把该 attempt 计为 portrait quality evidence，也不自动换 seed、
重新提交或声称 T8 portrait runtime 已通过。

## Motion Finding

独立逐帧检查拒绝第一条作为流畅性 PASS。Farneback optical-flow P90 与 consecutive-frame
MAD 在以下边界同时出现异常峰值：

| Boundary | Time | First clip flow P90 | First clip MAD |
| --- | ---: | ---: | ---: |
| `51 -> 52` | `2.125s` | `4.453` | `10.254` |
| `75 -> 76` | `3.125s` | `3.633` | `8.909` |
| `99 -> 100` | `4.125s` | `5.065` | `10.436` |

第一条常态 flow P90 median 为 `2.134`、MAD median 为 `6.731`。三个异常点严格间隔
24 frames，形成约一秒一次的周期性位移跳变；此外中景没有完整显示膝、踝和落脚，不能验证
完整步态。

第二条将人物完整纳入画面，脚、踝和膝在 sampled frames 中可见，且整体运动幅度降低；但
同一三组边界仍是全片前三大 flow P90 峰值：

| Boundary | Time | Full-body flow P90 | Full-body MAD |
| --- | ---: | ---: | ---: |
| `51 -> 52` | `2.125s` | `1.682` | `3.824` |
| `75 -> 76` | `3.125s` | `1.524` | `5.148` |
| `99 -> 100` | `4.125s` | `1.902` | `7.830` |

第二条常态 flow P90 median 为 `0.888`、MAD median 为 `2.744`。固定机位要求也没有完全
被模型遵守：人物大致保持画面位置，背景仍呈跟随位移。两次不同 seed、不同构图均复现相同
24-frame 周期边界，所以当前证据支持“问题不是单一跟拍 prompt 所致”；它仍不足以把根因
精确归入 T8 sampler、conditioning、decode 或其他内部 owner。

独立复核进一步只分析没有人物的画面上方背景 ROI：常态 P90 光流约 `0.41–0.65`，三个
边界升至 `1.003–1.286`；`99 -> 100` 的背景水平位移突然为 `-0.911px`，而相邻帧约为
`+0.1px`。因此异常不是正常迈步加速，而是人物与背景共同发生的 temporal discontinuity。

## Assessment

Technical container verdict 为 `PASS`，T8 motion-smoothness verdict 为 `REJECT`。人物脸部、
发饰、服装和可见肢体在 dense samples 中总体稳定，没有明显身份突变或严重解剖畸变；但
周期性内容跳变在两次独立实验中复现，当前 T8 Stock20 124-frame route 不应直接用于青颜广告
的真实行走、转身或社交镜头。

本结论来自 full-frame decode、dense samples、motion statistics 与 independent review；
真人 1.0x 正常速度播放验收仍由用户拥有。该缺口不会被 unique-frame ratio、constant FPS、
single-scene 或无 heuristic issue 替代。

## Remaining Risks Or Next Work

Next One Thing：在继续生成广告镜头前，对 current T8 124-frame graph 的 exact periodic
boundary 做独立 root-cause diagnosis，确认峰值是否来自 sampler/conditioning/decode 的固定
时序结构。没有新的 root-cause evidence 时，不继续更换 seed 或堆叠同类 Stock20 candidate，
也不通过补帧、变速或时间重映射隐藏原始运动缺陷。

若要补做 portrait flow check，必须把它作为新的明确 attempt：先由本 task 独占受管 ComfyUI
unit，再使用新的 output identity，并在用户确认 recovery direction 后单次提交；不得将已中断
attempt 视为未发生而 blind retry。

青颜包装真值、苗家女孩跨镜头 identity、产品拿出/开盖/喷洒、9:16 composition、口播、
Douyin UI safe area 与完整商业成片均未由本轮验证。

## Agent Guardrails

- 不把 124 个唯一帧、constant 24fps 或 one-scene 当作动作流畅 PASS。
- 不把这些 development `ComfyClient` submit 描述成 Production Provider lifecycle evidence。
- 不覆盖或删除失败样片；两次结果分别保留，供后续 root-cause 对比。
- 不把当前相关性证据升级为 T8 内部 root-cause 定论。
- 不在没有新假设时 blind retry、批量换 seed、fallback 或用后期时序处理掩盖跳变。
