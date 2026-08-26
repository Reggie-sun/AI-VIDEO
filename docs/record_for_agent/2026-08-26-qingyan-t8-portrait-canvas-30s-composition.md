# Qingyan T8 Portrait Canvas 30s Composition Record

Date: 2026-08-26

> Current-facing quality correction (2026-08-26): this exact 30-second artifact
> has a user human visual verdict of `FAIL`. The three blocking findings are no
> dialogue/product recommendation, severe freeze/seam stutter, and visual
> discontinuity. The earlier project-local `video_review issues: []` remains a
> valid generic technical-tool result, but it did not run the canonical
> Ecommerce Gate 2 and cannot override the human verdict. Current status is
> `HUMAN_VISUAL_FAIL / CANONICAL_GATE_NOT_RUN`; the artifact is blocked from
> P6, Final Acceptance, publication, or reuse as the current delivery candidate.

> Superseded delivery routing (2026-08-26): the v4 artifact and its human `FAIL`
> remain immutable historical evidence. The current local development candidate
> is the repaired v5 recorded in
> `2026-08-26-qingyan-v5-dialogue-seam-continuity-repair.md`. V5 has a new audible
> product-recommendation Shot, no live-action clone padding, and requirement-level
> development Gate `PASS`; it has not yet received the user's uninterrupted 1.0x
> human acceptance and is not P6 or Final Acceptance.

## Purpose

本文记录青颜苗家女孩广告从 28 秒候选修订为 8 个 Shot、30 秒、9:16 开发候选的稳定 checkpoint。
本轮澄清 T8/H3 的 canvas contract：节点链路接收动态 `width` / `height`，人物素材使用原生
`768x1344` portrait canvas；最终交付再由 Composition 规范化为 `1080x1920`。不得把 shipped
profile 的某个默认或封存分辨率，误写成底层 tensor 只能生成 16:9。

本轮没有新的 ComfyUI/T8 submit、remote call、paid call、retry 或 fallback。它复用已绑定 exact
bytes 并通过逐 Shot Gate 的人物素材，增加 deterministic copy、source packshot 和 final composition。
该成片是 local development candidate，不是 Production Manifest candidate、P6、Final Acceptance、
`PACKAGE_READY` 或发布证明。

## Revised Authoring Contract

authoring input 与 8-Shot contract 位于：

```text
artifacts/qingyan-miao-ad-20260826-v4/ecommerce-input.json
artifacts/qingyan-miao-ad-20260826-v4/authoring-contract.md
```

`ecommerce-input.json` 已由 `ecommerce-ad-workflow/input/1` validator 判定为 valid。修订保持的 claim
边界为：

- 允许 `抑汗净味 清爽舒适`、`帮助减少汗湿困扰`；
- 不使用医疗、汗腺机理、量化功效、永久/绝对保证或 `清爽一整天`；
- 将旧开场的 `异味尴尬？` 改为较克制的 `靠近不自在？`；
- T8 手持产品只作为拿取/使用前动作提示，可读包装与产品 hero 必须使用用户源 packshot；
- Shot 03 不伪造本轮没有取得 evidence 的喷头、雾化微距或 literal spray。

精确时间轴为：0-3 秒痛点、3-6 秒拿取、6-9 秒使用前提示、9-13 秒抽象卖点、13-18 秒状态
转变、18-22 秒场景扩展、22-26 秒产品 hero、26-30 秒品牌落版，共 `720` frames at `24fps`。

## Human Quality Failure Diagnosis

本 artifact 没有进入 canonical `Universal Gate 1 -> Ecommerce Gate 2 -> P6`。本轮复核确认，上一轮
只调用了 generic project-local `video_review`；其 `issues: []` 与 unique-frame metric 不能证明
commercial audio、edit seam 或跨镜头 continuity。

若把当前 exact candidate 交给现有 Qingyan Ecommerce profile，至少以下 whole-ad findings 必须为
`FAIL`，因此 Gate 2 不得 PASS：

- `ad.audio.product_recommendation`：音轨只有 BGM/SFX，generic review 测得 speaking duration `0.0s`，
  没有对话或口播推广；
- `ad.audio.voice_continuity`：不存在可评估的推广 voice，不能标记 PASS；
- `ad.motion.required_windows`：compositor 主动插入多段 clone-frame padding；
- `ad.edit.pacing`：冻结尾帧与硬切形成明显 seam/stutter；
- continuity 相关 acceptance：用户已明确报告画面不连贯，当前 evidence 不支持 PASS。

直接代码证据位于 `artifacts/qingyan-miao-ad-20260826-v4/compose_t8_canvas_v4.sh`：Shot 01–03
各插入约 `0.667s` clone padding，Shot 05 插入 8 frames，Shot 06 与 Shot 08 各插入约
`1.667s` clone padding，合计约 `5.67s` 的 deterministic clone padding。FFmpeg
`freezedetect=n=-45dB:d=0.25` 对 exact final MP4 实测包括：

```text
2.29167-3.00000s   0.70833s
5.16667-6.00000s   0.83333s
8.20833-9.00000s   0.79167s
20.2500-22.0000s   1.75000s
```

Shot 05 又在 final timestamp `15.3333s` 将 `04_walk_forward` 与 `05_walk_smile` 直接 concat。
相邻 frames 中人物尺度、身体姿态、脚步与构图位置发生瞬间跳变；scene-difference scan 也将
`15.3333s` 识别为 change point。这不是跨镜头 state continuity，也不是可接受的自然运动衔接。

当前 profile 已包含 `ad.audio.product_recommendation`、`ad.audio.voice_continuity`、
`ad.motion.required_windows`、`ad.edit.pacing` 与 `ad.continuity.character`，但 Runtime Gate 只验证
evaluator 返回的 sealed requirement findings；它不会自行从 MP4 推导这些 finding。现有 deterministic
test fixture 甚至用 `has_audio=False` / `expects_audio=False` 并让 fake evaluator 对全部 requirement
返回 PASS。因此 Gate envelope 的 identity/freshness 能力已经实现，但真实 evaluator coverage 仍是
经验质量的关键缺口。

## Portrait Canvas And Source Evidence

人物输入保持 T8/H3 已生成的 `768x1344` portrait canvas。Composition 只在最终输出层执行中央
`756x1344` 的精确 9:16 取景，再以 Lanczos 规范化到 `1080x1920`；这属于 delivery sizing，
不构成横屏生成或 16:9 tensor fallback。

复用的 exact clips：

| Clip | SHA-256 | Evidence boundary |
| --- | --- | --- |
| `01_concern.mp4` | `9e3d64b6fa85e4eba47fcbae09c55e10d0b6897b663da65ff1708acf71619a0f` | 原 sequential Gate PASS |
| `02_product_lift.mp4` | `6d7f12ed2d9f7ec4e4346893aac667c57fe578c1330ceab75423fe35aa08f499` | 原 sequential Gate PASS；只作 coarse identity |
| `03_preuse_hint.mp4` | `ef4e6ae65181eff913a1e3086510c7e70125f05815e6066523023745f69ad3e8` | 原 sequential Gate PASS；无 literal spray |
| `04_walk_forward.mp4` | `423c9c5483ed691e2611a225bc0a80572b6be2d1f2c87fc3f44fea1d72b4c8a0` | 原 sequential Gate PASS |
| `05_social_turn.mp4` | `92222b20f055b32ddad48a2da2da8dd63e0f5a049adeaa53c4d0d0ea05ebb7f7` | 原 sequential Gate PASS |
| `05_walk_smile.mp4` | `66cc9a0983bebef138fbc15deeb2c502a0f4a1bfb714ff849b0ecbf459036e4a` | 本轮重新调用 project-local `video_review`；74/74 sampled unique frames，无内容 issue；工具只给出 landscape-oriented width heuristic |

可读产品真值来自：

```text
artifacts/qingyan-miao-ad-20260826-v4/assets/product-packshot.jpg
SHA-256 03d27bd46be48082b6d5ac737fbbb1f6cdca68b891d6c7d7c58eaa2c1c14f078
```

该 source packshot 保持黄色盒装、黄色瓶身标签、白色瓶盖、青颜和 `60ml` 的可读视觉证据；不得把
source packshot 的小字真值外推到 generated hand-held bottle。

## Composition Output

deterministic compositor：

```text
artifacts/qingyan-miao-ad-20260826-v4/compose_t8_canvas_v4.sh
```

当前 local output：

```text
artifacts/qingyan-miao-ad-20260826-v4/final/青颜_苗家女孩T8动态广告_30s_9x16_v4.mp4
SHA-256 bb688a688cf799e1e1c5302381d5b98dfb67ea83f79dce0162b8572af186b1e0
```

measured facts：

- container duration `30.022s`；video/audio stream duration 均为 `30.000s`；
- H.264 High、`1080x1920`、`24fps`、`720` frames、`yuv420p`；
- AAC、48 kHz、stereo；
- file size `19,493,262` bytes；
- `volumedetect` mean `-21.2 dB`、max `-1.6 dB`，未将该值误称为 integrated LUFS；
- video 与 audio full decode 均返回 success。

第一次 render 暴露 Shot 05 只输出 112 frames，导致整片 video track 为 712 frames / 29.667 秒。
根因是 concat 后的 duration-based `tpad` 没有实际产出尾帧。修订为对第二段源镜头执行
`tpad=stop_mode=clone:stop=8` 后，Shot 05 为精确 120 frames，最终视频为精确 720 frames。

## Review Evidence

project-local `video_probe` 实测 `1080x1920`、24 fps、720 frames 与 AAC 48 kHz stereo。
project-local whole-video `video_review` 提取 30 frames，报告 `issues: []`、1437/1437 sampled unique
frames。Agent 另外检查：

```text
artifacts/qingyan-miao-ad-20260826-v4/review/final/contact.jpg
artifacts/qingyan-miao-ad-20260826-v4/review/final/boundaries.jpg
```

逐秒联系表与各 Shot 边界前后采样未见字幕越出画面、产品卡覆盖人物面部、明显额外肢体或错误
包装 hero。该结果只属于 technical/media development review，不能替代用户在目标手机上的 1.0x
主观观看、平台 UI safe-area 验收、P6 或 Final Acceptance。

## Publication And Ownership State

- media、input、authoring contract、compositor 与 review derivatives 位于 repository-untracked
  `artifacts/qingyan-miao-ad-20260826-v4/`，保持 local-only；
- 本记录与旧 28 秒记录的 supersession notice 是唯一 task-owned tracked changes；
- 没有激活 Production candidate、写 Manifest、调用 `ProductionStateCommitter`、push、release 或上传；
- 旧 28 秒 artifact 与五条 sequential Shot Gate evidence 保留为历史 evidence，没有覆盖或删除。

## Remaining Risks Or Next Work

- 尚缺用户在目标手机上的 uninterrupted 1.0x 观看与 subjective verdict；
- 尚未在真实 Douyin UI overlay 下做 device/account-specific safe-area preview；
- BGM/SFX 继续复用现有本地资产，本轮没有闭合商业投放 license provenance；
- 没有取得可信 literal spray 微距，Shot 03 只交付使用前动作提示；
- T8 `768x1344` 到 delivery `1080x1920` 的放大会有细节损失，但不代表 T8 只能生成横屏；
- 本轮没有创建 `package/2`，因此不能声明 Ecommerce `PACKAGE_READY`。

## Agent Guardrails

- `T8 default canvas`、shipped profile 固定值与 node/tensor 可接受的动态 portrait canvas 是不同层；
  不得互相替代。
- 不得把已复用 Shot 的历史 Gate PASS 描述成新的 submit 或新的 Production acceptance。
- 不得把 source packshot 的 readable label 真值外推到 generated hand-held bottle。
- 不得把 `video_review issues: []` 或 full decode 推断成 human acceptance、P6、Final Acceptance 或投放表现。
- Development FFmpeg composition 不得描述成 canonical HyperFrames render 或 Production activation。
