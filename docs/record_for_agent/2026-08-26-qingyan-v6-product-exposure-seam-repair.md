# Qingyan V6 Product Exposure And Seam Repair Record

Date: 2026-08-26

> Human supersession (2026-08-26): 用户播放 exact v6 后继续判定为 human `FAIL`。新的 blocking
> findings 是：product hero 背后移动的浅黄色光带没有必要；golden-fluid benefit 与 source
> packshot 应各自只出现一次并固定为最后两个 Shot；把 fade-to-white / fade-from-white 用作几乎
> 每个 seam 的默认处理形成连续白光闪屏。V6 的历史测量仍保留，但不再是 current delivery
> candidate。替代 local development candidate 是
> `2026-08-26-qingyan-v7-final-two-shot-hard-cut-repair.md` 记录的 v7；其 targeted Agent Gate
> 为 `PASS`，新的用户 human verdict 仍为 `PENDING`。

## Purpose

本文记录用户对 exact v5 进行 human playback 后的第二轮 correction。用户指出：开局约 2 秒从空手状态
突兀出现产品，约 4 秒再次明显 seam；人物手持产品时右下角又叠加 packshot；产品图在多个段落反复出现；
静态商品图被往复运动处理成抖动。V5 因此保持 human `FAIL`，其 requirement-level Agent `PASS` 不再是
current-facing delivery verdict。

本轮只修 composition，没有新的 T8/ComfyUI/Provider submit、retry、fallback、remote 或 paid effect。
没有修改 Production Manifest、激活 candidate、生成 P6/Final Acceptance、push、release 或上传。

## Failure Diagnosis

v5 证据位于：

```text
artifacts/qingyan-miao-ad-20260826-v5/review/human-fail-2/opening-0-5s-8fps.jpg
artifacts/qingyan-miao-ad-20260826-v5/review/human-fail-2/seams-2s-4s.jpg
artifacts/qingyan-miao-ad-20260826-v5/review/human-fail-2/product-frequency-2fps.jpg
```

责任层不是 T8 tensor 或 dialogue generation，而是后期 Shot contract：

- `F-CONTINUITY`：`01_concern` 的空手 close state 与 `02_product_lift` 的持瓶 open state 被直接
  cross-dissolve，双重人脸、手与道具状态同时可见；随后又从一个持瓶姿态 dissolve 到另一个持瓶姿态。
- `F-PROP-DUP`：人物已经手持 generated bottle，同一画面右下角仍叠 source packshot，形成两个商品主体。
- product-presentation repetition：packshot 同时承担 presenter overlay、scenario card、hero 与 end card，
  不再是清晰分工的 `IN_SCENE_GENERATED` 与 `DEDICATED_HERO_SHOT`。
- `F-JITTER`：still assets 使用 sinusoidal `zoompan`；虽然目标是“持续运动”，实际观感是静图往复抖动。

## V6 Composition Contract

current source：

```text
artifacts/qingyan-miao-ad-20260826-v6/authoring-contract.md
artifacts/qingyan-miao-ad-20260826-v6/compose_t8_canvas_v6.sh
```

主要修复：

1. 完全删除旧 `02_product_lift` segment；0–2 秒顾虑镜头先退到 white endpoint，2–3 秒使用无产品
   neutral bridge，3–8.167 秒进入一条连续 native-audio presenter Shot。4 秒位于同一个 Shot 内，不再换镜。
2. presenter Shot 只保留人物手中的 generated bottle，不再叠加右下角 packshot。
3. source packshot 只有一次输入，只在 19.833–25.833 秒独立 hero window 出现；scenario bridge 与
   end card 均不显示 product image，end card 为 text-only。
4. compositor 中 `xfade`、`zoompan`、`tpad`、clone、reverse 和 duplicated-frame extension 全部为 0。
   不同状态通过 3-frame fade-to-white / fade-from-white endpoint 连接，不再双重曝光人物或产品。
5. `01_concern` 与 `05_social_turn` 均删除源开头 8 个 still-hold frames；全部 live-action windows 中
   不再存在 `>=0.25s` freeze event。
6. 十个 non-overlapping segments 直接相加为 `720` frames；没有 overlap duration 或隐藏补帧。

## Exact Output And Verification

current local candidate：

```text
artifacts/qingyan-miao-ad-20260826-v6/final/青颜_苗家女孩T8自然转场广告_30s_9x16_v6.mp4
SHA-256 cdac1d5c78f0a40735220ad643f1d8ab9f5b6d8bd2bd41d7b9ef2d124432258d
```

measured facts：

- file size `17,341,950` bytes；container `30.022s`；video/audio stream均为 `30.000s`；
- H.264 High、`1080x1920`、24fps、720 frames、`yuv420p`；AAC 48kHz stereo；
- full video/audio decode `PASS`；integrated loudness `-20.8 LUFS`；true peak `-7.1 dBFS`；
- project `video_review`：40 frames extracted，1437/1437 sampled unique ratio `1.0`，`issues: []`；
- Whisper medium 在 3.30–8.24 秒检出单一推广句；`青颜/清盐` 与 `抑汗/易汗` 仍是同音字
  orthography ambiguity，画面烧录 exact correct Chinese；
- source-packshot input count `1`；presenter/live-action packshot overlay count `0`；
- product hero 21.0–24.5 秒 crop 的 85 帧 phase correlation：最大水平漂移 `0.000544px`、垂直漂移
  `0.000516px`、minimum response `0.999814`，支持“产品几何固定、无静图抖动”；产品与文字固定，
  只有背后的大面积浅金光带单向匀速通过，不使用往复、正弦或缩放；
- FFmpeg `freezedetect=-45dB:d=0.25` 的剩余事件全部落在 deliberate low-motion graphic/hero/end-card
  windows；所有 live-action windows 为 0 events。

targeted evidence：

```text
artifacts/qingyan-miao-ad-20260826-v6/review/final/opening-0-5s-8fps.jpg
artifacts/qingyan-miao-ad-20260826-v6/review/final/opening-boundaries.jpg
artifacts/qingyan-miao-ad-20260826-v6/review/final/product-frequency-2fps.jpg
artifacts/qingyan-miao-ad-20260826-v6/review/final/targeted-human-failure-gate.json
```

targeted Agent Gate 对 opening 2s/4s seam、same-frame product duplication、source-packshot frequency、
still geometry、live-action motion、hidden motion constructs、dialogue 与 technical delivery 均为 `PASS`。

## Assessment And Remaining Boundary

v6 已在可验证的 composition 层删除 v5 的错误路径，而不是通过更长 dissolve 或更多 negative copy 掩盖。
current status 为 `TARGETED_AGENT_GATE_PASS / NEW_HUMAN_VERDICT_PENDING`。只有用户重新播放 exact v6
SHA 后，才能决定这些主观 blocker 是否真正关闭。

intentional graphic windows 为 neutral bridge、benefit card、scenario bridge、dedicated product hero 与
text end card。商品与文字像素保持稳定，后四类卡的背景使用单向线性 light pass；它们不属于
live-action freeze，但其停留节奏是否符合用户口味仍属于
human acceptance，不由 freeze metric 或 MCP `issues: []` 替代。

artifacts 保持 repository-untracked、local-only。项目 Agent Memory 第一次 focused query 返回 stale corpus
且排队 detached refresh，第二次 follow-up query返回 `[]`；RAG 没有提供用于改变 current code/media
evidence 的命中，也没有前台重建 index。

## Agent Guardrails

- 不得把白场 endpoint 描述成动作匹配切；它明确承认中间状态被省略。
- 同一 live-action frame 不得同时出现 generated hand-held product 与 source-packshot overlay。
- source packshot 只承担 dedicated hero；若未来要求再次出现在 CTA，必须先获得新的 creative approval，
  不能静默恢复重复露出。
- static card 的 freeze 与 live-action clone/stutter 必须分层报告；不能用一个 unique-frame ratio混为总分。
- targeted Agent `PASS` 不是新的人类 `PASS`、canonical Ecommerce Gate 2、P6、Final Acceptance 或发布证明。
