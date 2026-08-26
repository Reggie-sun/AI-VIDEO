# Qingyan V8 Underarm And Elder-Dialogue Continuity Repair Record

Date: 2026-08-26

> **SUPERSEDED / HUMAN FAIL:** 用户观看 exact v8 后明确指出开头仍静止、缺少真正的腋下
> `使用前 / 使用后`效果对比、约 14 秒处的 optical-retime 换镜诡异，并指出后段推销词只有
> 字幕没有声音。v8 的历史测量继续保留，但 current candidate 已由
> `docs/record_for_agent/2026-08-26-qingyan-v9-before-after-and-later-voice-repair.md` 替代。

## Purpose

本文记录用户对 exact v7 的 human `FAIL` 及其 replacement：把产品定位明确收敛为腋下止汗净味，
用 fully clothed、非低俗的 AI 腋下视角做夸张除味表现；加入苗家年轻女孩与老人三轮在镜对白；
移除人物段的重复 packshot/icon、white flash、静图抖动和长尾站桩。最后两张商业静图只出现一次，
合计 `5.000s`。

本轮只产生 local、repository-untracked media candidate，并更新 tracked session record。没有 remote / paid
Provider、Production Manifest mutation、candidate activation、P6、Final Acceptance、push、release 或上传。

## Authoring And Runtime Contract

authoring source：

```text
artifacts/qingyan-miao-ad-20260826-v8/authoring-contract.md
artifacts/qingyan-miao-ad-20260826-v8/prompts/01_underarm_deodorizing_repair.txt
artifacts/qingyan-miao-ad-20260826-v8/prompts/02_elder_dialogue_repair.txt
artifacts/qingyan-miao-ad-20260826-v8/prompts/03_leave_together.txt
artifacts/qingyan-miao-ad-20260826-v8/compose_t8_canvas_v8.sh
```

accepted source MP4 均由本机 MiniMax H3 T8 direct quality route 生成，canvas 为 `768x1344`、24fps、
20 steps、`res_multistep/simple`、无 Turbo/LoRA；最终 deterministic composition 输出 `1080x1920`。
accepted generation 使用 T8 checkout `28cb160827c245b2d6a37539df30c1d7c5e7aecd` 与 ComfyUI
checkout `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`。内建 `imagegen` 只用于 bounded first/last-frame
约束，不拥有 Product Truth、Shot lifecycle 或 acceptance。

## Generation And Per-Shot Gate

本轮共发生 `5` 次 local T8 submit，零 remote submit、零 fallback、零 blind retry：

1. initial Shot 01 成功落盘，但约 4 秒生成 floating box+bottle poster；exact Shot Gate `FAIL`，未进入下个
   submit。失败证据在 `review/01_underarm_deodorizing/gate.json`。
2. FL2VA Shot 01 replacement：`01_underarm_deodorizing_repair.mp4`，SHA-256
   `ced2f7e4739a9930b88fcf1e62479a55c8a59a9b04f0fb6a8d4cc84392784be0`，175 frames，Gate `PASS`。
3. 226-frame Shot 02 在 `SamplerCustomAdvanced` 发生 deterministic CUDA OOM，没有 MP4；错误封存在
   `runtime/t8_portrait_ad/02_elder_dialogue.failure.json`，未伪称 media Gate。
4. 缩为 175 frames 的 Shot 02 replacement：`02_elder_dialogue_repair.mp4`，SHA-256
   `4d28cd1f9ea588802d8028e5581fa421e33f3cd5154159971b7179e1226ba2aa`，Gate `PASS`。三轮对白为
   “姑娘，喷的什么？” / “青颜抑汗净味喷雾，清爽舒适。” / “难怪这么自在。”。
5. Shot 03：`03_leave_together.mp4`，SHA-256
   `5edda6a828c1fbbf392ccf5c49aec6e68dce4092ad6b64fbc4f9144257502eb8`，175 frames，Gate `PASS`。
   其 native audio 被最终 composition 明确丢弃，避免非对白音频触发的 Whisper 幻觉进入成片。

每个 accepted Shot 的 exact MP4 + SHA-256 均先经过 project-local `video-analysis` MCP 和 requirement-level
Gate，才提交下一 Shot。Gate 只证明当前 bytes 满足 sealed intent，不写 Manifest，也不授予 Final Acceptance。

## Final Composition

exact local candidate：

```text
artifacts/qingyan-miao-ad-20260826-v8/final/青颜_苗家双人腋下止汗对话广告_30s_9x16_v8.mp4
SHA-256 e534c4ac93da0b03a0ac3f028fb6c83bf50292716dfccc64f0a49ae4828e5bd8
```

final timeline：

| Segment | Time | Frames | Contract |
| --- | --- | ---: | --- |
| exaggerated underarm deodorizing | `0.000-7.292s` | 175 | fully clothed underarm POV；单一实物瓶；无 floating overlay |
| elder dialogue | `7.292-13.750s` | 155 | 保留三轮对白；删除长尾 static response |
| leave together | `13.750-25.000s` | 270 | 同一连续步行动作 optical retime；不新增 seam |
| golden-fluid benefit | `25.000-27.500s` | 60 | 固定静图，只出现一次 |
| exact product hero | `27.500-30.000s` | 60 | 固定 packshot，只出现一次 |

picture 使用 direct continuity cuts；没有 `white flash`、`xfade` 或 moving yellow band。character Shots 只出现
单一 physical bottle；没有手持产品与右下角 packshot 同屏。Shot 01/02 native audio 加连续 BGM；Shot 03
native audio不进入成片。

## Exact Verification

- SHA-256 sidecar可校验；H.264 High、`1080x1920`、24fps、720 frames；video/audio stream均
  `30.000s`，container `30.022s`；AAC 48kHz stereo。
- project-local `video_probe`绑定 exact final path；`video_review` 返回 `issues: []`，1437 sampled frames中
  unique ratio `0.999`。
- Whisper small按顺序检出老人提问 `7.20-9.04s`、女孩回答 `9.04-12.20s`、老人认可
  `12.20-13.68s`；ASR 对品牌/卖点出现同音误写，不能证明 exact spelling 或 human lip-sync。
- Shot 01→02 与 Shot 02→03 边界 SSIM 分别为 `0.951692`、`0.972581`；两个 character boundary
  均无 `>=0.35s` freeze。开场仍有 deliberate `0.917s` low-motion setup，而非 edit seam。
- integrated loudness `-19.2 LUFS`，true peak `-8.5 dBFS`。
- final two stills各 60 frames；decoded consecutive-frame YAVG difference最大仅 `0.0137948` 与
  `0.0092718`，支持无几何 jitter，仅保留 codec quantization。
- final Gate：`artifacts/qingyan-miao-ad-20260826-v8/review/final/final-gate.json`；contact sheet 与
  boundary montage位于同目录。

## Assessment And Remaining Boundary

current status 为 `TARGETED_AGENT_GATE_PASS / NEW_HUMAN_VERDICT_PENDING / LOCAL_CANDIDATE_ONLY`。
本轮修复了用户点名的重复产品静图、白闪 seam、老人对白缺失、对话尾部停滞和末两图时长问题；不代表
canonical Ecommerce Gate 2、P6、Final Acceptance、publication 或广告合规完成。

仍需用户以 1.0x uninterrupted playback 判断：开场夸张腋下气流是否合适、模型生成对白的口型与老人声线
是否自然、optical retime 的户外步态是否可接受。产品功效文案和包装上可读声明还需 Product Truth / 法务
复核。若 human verdict再次为 `FAIL`，本记录必须按 exact artifact继续 supersession，不能用本轮 Agent Gate
覆盖真人判断。

项目 Agent Memory初始 query用于既有对白、per-Shot Gate与 human-verdict边界；基于本轮 T8/FL2VA、
175/226-frame 与 product-overlay failure形态的 follow-up query返回 `[]`，仅排队 detached refresh，未做前台
index rebuild。Markdown record不会自动刷新 RAG。
