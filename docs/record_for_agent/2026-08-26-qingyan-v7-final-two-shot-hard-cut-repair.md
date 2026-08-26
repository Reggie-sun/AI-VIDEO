# Qingyan V7 Final-Two-Shot Hard-Cut Repair Record

Date: 2026-08-26

## Purpose

本文记录用户对 exact v6 的第三轮 human correction。用户指出 product hero 背后移动浅黄色光带
没有必要；golden-fluid benefit 与 source packshot 应各自只出现一次，并位于最后两个 Shot；
每个 seam 使用 white flash 作为默认转场缺乏叙事理由，形成连续闪屏。

本轮责任层为 deterministic composition/post。没有新的 T8、ComfyUI、remote、paid、Provider
submit、retry 或 fallback，也没有写 Production Manifest、激活 candidate、签发 P6 / Final
Acceptance、push、release 或上传。

## V7 Composition Contract

current source：

```text
artifacts/qingyan-miao-ad-20260826-v7/authoring-contract.md
artifacts/qingyan-miao-ad-20260826-v7/compose_t8_canvas_v7.sh
```

主要 correction：

1. 八个 non-overlapping segments 直接组成 `720` frames；所有 picture boundary 都是 deliberate
   hard cut，没有 `xfade`、video `fade`、white endpoint、overlap 或 double exposure。
2. 移除全部 moving yellow band；compositor 不再创建 yellow color-source overlay。
3. golden-fluid image 只在 Shot 07 / frames `384..551` / `16.000-23.000s` 出现一次。
4. exact source packshot 只在 Shot 08 / frames `552..719` / `23.000-30.000s` 出现一次，
   同时承担 product hero、brand closure 与 CTA；没有第二个 text-only end card。
5. product、fluid 与 graphic background 不做平移、缩放、往复或 `zoompan`；只有 copy timing
   在同一固定画面内变化。
6. 口播 source 的前六个 still frames 与对应前 `0.250s` audio 被同步裁掉；social source 的
   前八个 still frames保持裁除。live-action window `0.000-13.583s` 不再有 `>=0.25s`
   freezedetect event。
7. BGM 连续跨越 hard cuts，只在 `16.000s` benefit 和 `23.000s` product hero 各使用一次
   低音量 cue；不再在每个 seam 添加视听转场。

## Exact Output And Verification

current local candidate：

```text
artifacts/qingyan-miao-ad-20260826-v7/final/青颜_苗家女孩T8硬切顺滑广告_30s_9x16_v7.mp4
SHA-256 4ac67c1c3193819befc5144e11c457a122c481d6bcbfd458963f7fe2028e63e5
```

measured facts：

- file size `15,963,027` bytes；container `30.022s`；video stream `30.000s`；
- H.264 High、`1080x1920`、24fps、720 decoded frames、`yuv420p`；AAC 48kHz stereo；
- SHA sidecar、full video decode 与 full audio decode均通过；
- integrated loudness `-18.3 LUFS`，true peak `-4.2 dBFS`，无 `>=0.35s` silence event；
- seven exact boundary windows共有零个 full-white frame；逐帧边界图未出现 fade 或 flash；
- compositor 静态检查：`xfade=0`、video `fade=0`、`zoompan=0`、`tpad=0`、`reverse=0`、
  `clone=0`、moving yellow source/overlay `=0`；packshot input count `1`，fluid input count `1`；
- product crop phase correlation 在 168 frames 中最大水平位移 `0.000400px`、最大垂直位移
  `0.000340px`、minimum response `0.999486`，支持 product geometry stable；fluid background
  没有 compositor transform，decoded phase estimate 受压缩影响出现最高 `0.4995px` vertical
  ambiguity，因此不将其夸大为 subpixel-zero empirical proof；
- project-local `video_review` 抽取 40 frames，generic result为`issues: []`；unique ratio `0.994`
  受 deliberate low-motion final graphic windows影响，不能替代 human viewing；
- Whisper medium 检出一条推广句，仍将 `青颜`、`抑汗净味`转写为同音/近音字；画面烧录 copy
  使用 approved exact Chinese。

targeted evidence：

```text
artifacts/qingyan-miao-ad-20260826-v7/review/final/all-boundaries-no-flash.jpg
artifacts/qingyan-miao-ad-20260826-v7/review/final/product-benefit-frequency-2fps.jpg
artifacts/qingyan-miao-ad-20260826-v7/review/final/boundary-white-scan.txt
artifacts/qingyan-miao-ad-20260826-v7/review/final/static-geometry-phase.txt
artifacts/qingyan-miao-ad-20260826-v7/review/final/targeted-human-failure-gate.json
```

## Assessment And Remaining Boundary

current status 为 `TARGETED_AGENT_GATE_PASS / NEW_HUMAN_VERDICT_PENDING`。本轮证明的是用户点名
的 composition failure paths 已从 v7 compositor 中删除，并有 exact final-media evidence；不证明
canonical Ecommerce Gate 2、P6、Final Acceptance、publication 或 market performance。

Shot 06、07、08 是 intentional low-motion graphics。它们不再抖动，也不再重复图片，但最后两镜
各 7 秒的 read time、hard-cut rhythm 与整体审美仍必须由用户在 1.0x uninterrupted playback 中判断。

media、contract、compositor 与 review derivatives保持 repository-untracked、local-only。项目 Agent
Memory 第一次 query 返回 tagged stale fragments并排队 detached refresh；基于最终修复形态的
follow-up query返回 `[]`。本轮没有前台重建 index。

## Agent Guardrails

- 不得把每个 seam 的 white flash 解释成 continuity；没有动作/光源动机时它只是闪屏。
- hard cut 是明确的 edit grammar，不等于连续动作；相邻 Shot必须按 action、location、audio bridge
  或商业 beat 给出切换理由。
- one presentation window 可以持续多帧；不得把同一 Shot 内的抽样帧数量误算为“图片出现多次”。
- targeted Agent `PASS` 不能覆盖新的用户 human verdict，也不是 canonical Ecommerce Gate 2、P6、
  Final Acceptance 或发布证明。
