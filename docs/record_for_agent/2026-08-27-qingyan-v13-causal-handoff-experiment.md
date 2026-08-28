# Qingyan V13 Causal Handoff Experiment Record

> **2026-08-28 M6 empirical supersession:**
> `2026-08-28-h3-m6-causal-micro-sequence-gate-stop.md` 已在新的 task-scoped authorization 下执行 M6。
> Shot A technical Gate 六类均 PASS；Shot B 的 handoff/release/exit causal state PASS，但 conditioning 与 camera
> FAIL，故 Shot C 未提交。下方“仍未执行、未授权”的 M6 状态仅是 superseded historical context；v13 自身的
> media verdict 与 HUMAN/Production 边界没有改变。

> **2026-08-28 implementation update:** 本记录提出的最小 typed intent、pairwise readiness 与 exact H3
> compiler 已由 `2026-08-28-h3-causal-readiness-phase-a.md` 记录为 Phase A M1–M5 offline implementation。
> v13 的媒体 verdict 与本记录中的 HUMAN/Production 边界保持不变；M6 causal micro-sequence 仍未执行、未授权。

## Status

- Date: `2026-08-27`
- Classification: `development_experiment`
- Checkpoint: `COMPLETED_ONE_SHOT_AND_30S_RECONNAISSANCE`
- Single generated Shot technical Gate: `PASS`
- 30s causal continuity: `FAIL`
- Human verdict: `NOT_EVALUATED`
- Production qualification / activation / P6 / Final Acceptance: none

## Purpose

本实验在四臂 conditioning attribution 已支持 `incompatible last anchor` 为 forced transition、terminal snap
与 tail freeze 的主要原因后，继续隔离另一个问题：明确写出
`elder sole holder -> shared touch -> girl sole holder` 并使用 compatible same-scale first/last anchors，能否让
H3 生成一个可见、连续、可嵌入 30s 广告的产品交接动作；以及该局部修复是否足以关闭 v12 的跨 Shot
causal continuity FAIL。

本实验不验证 `GenerationIntent -> deterministic H3 compiler`，因为 exact H3 prompt 仍为手工 sealed prompt；
也不验证 Production input Registry lineage，因为实验 anchors 位于 repo-external development root，request 虽绑定
exact SHA-256，但 sidecar 明确记录 `registered_input_lineage=false`。

## Authorization And Guardrails

- 用户在当前 task 中明确授权直接执行本地实验并随后修改 plan。
- Local ComfyUI submit count: `1`。
- Retry count: `0`；fallback count: `0`；remote / paid call count: `0`。
- 使用 AI-VIDEO `VideoGenerationService`、`ProductionStateCommitter`、durable local intent / one-use permit 与
  sealed experiment profile；未直接调用 ComfyUI submit endpoint。
- 每次 submit 前验证 queue 为空；exact MP4 落盘后先调用 project-local `video-analysis`，再进行 30s
  deterministic composition。
- 未修改 Production profile、workflow、ComfyUI/T8 checkout 或 capability activation state。
- 30s recut 只使用 hard cuts、frame-exact trim/crop/scale、deterministic packshot 与既有 v12 audio/SFX；未使用
  xfade、dissolve、interpolation 或 seam-masking transition。
- ComfyUI 在 experiment 完成后已停止，queue 为空。

## Runtime And Exact Inputs

- Experiment root: `/home/reggie/ai-video-experiments/h3-causal-handoff-20260827-sLHhf1`
- ComfyUI commit: `e01fb4c56b7a88149d469b99cbbfe3223d715054`
- Profile source: `workflows/profiles/minimax_h3_fl2va_quality.json`
- Experiment profile SHA-256 identity: `ccdfd54991eac1462e8796afa3a26e1bd70a484edfdb9731e3bf647c6585e8cf`
- Workflow SHA-256: `8b6c338279d8af768fae8106034f9f26e8e9d59583e95a8ca8b16d36a930ad65`
- Recipe: Stock20, `res_multistep` / `simple`, no LoRA
- Seed: `6623081611478359059`
- Output contract: `768x768`, `124` frames, `24 fps`, `5.167s`, native audio present
- First anchor: elder sole holder, younger hands empty；normalized SHA-256
  `b408d98a99e354e9e34ca81cbce3106ea548e378e47e95a80ff8ef5e3f930f45`
- Last anchor: younger sole holder, elder hand empty；normalized SHA-256
  `f9ec7dd417c8bd4a7119a1bda6b1614a632ced28b7dc9cd01ad9552e286d167c`
- Prompt SHA-256: `27bc46ba30a446a3828f61f6916421385b62d308b81672665a6db6f53e1cbc74`
- Resolved generation hash: `52bd1bed21cc8fab6a9e228817eb37b997442b48349c376f7cf8801fad8ffc66`
- Provider request ID: `8c278e85-d2cd-4af0-b607-ad2f2841ce18`

Canonical Production profile currently seals ComfyUI commit `7cee3ceb...` while the live checkout was
`e01fb4c...`。本实验创建 repo-external versioned experiment profile 绑定 live commit；该行为只消除 attribution
中的 profile/runtime drift，不授权原地 reseal Production profile，也不证明 upstream recipe/pin 是质量根因。

## Single-Shot Result

Exact raw output:

```text
/home/reggie/ai-video-experiments/h3-causal-handoff-20260827-sLHhf1/outputs/h3-causal-handoff-square.mp4
SHA-256 30117ab8c80cbbc47df9e3779dd2a2ea28c9780fff384ad4c2c40ea4603220d9
843,583 bytes; H.264; 768x768; 24 fps; 124 frames; AAC 32kHz stereo
```

Project-local `video-analysis` 对 exact absolute MP4 执行 metadata、frame extraction 与 scene detection；technical
Gate 逐项结果：

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| initial holder | `PASS` | 老人为唯一 holder，少女双手空。 |
| visible transfer chain | `PASS` | 递出、少女伸手、短暂共持、少女抓稳、老人放手均可见。 |
| final holder | `PASS` | 结尾少女唯一持有，老人展示手为空。 |
| product functional state | `PASS` | 产品保持 closed/capped，无提前开盖、喷用或效果。 |
| identity/count/space | `PASS` | 两人、单产品、同房间、同 screen order 与近似 subject scale。 |
| camera/transition | `PASS` | 单场景、locked framing，无 forced scale transition、cut 或 compound motion。 |
| endpoint behavior | `PASS` | 因果动作完成；约 `4.54s` 起为 deliberate endpoint hold，无 incompatible-anchor snap。 |
| `1.0x` hand naturalness | `NOT_EVALUATED` | 必须由 human 正常速度观看，technical sampling 不代判。 |

Sidecar：

- `sidecars/exact-preview.json`, SHA-256
  `b4b5a4041c145317039dc7ac65a90d23c27cb20f690d5c05215ea6aefb0e5e7a`
- `sidecars/run-summary.json`, SHA-256
  `901873b45de7a3de6e03f0357ee3e7e0a0535a77a3ad0a98869ae6103ab8877f`
- `sidecars/shot-gate.json`, SHA-256
  `00896ccf2f30f6ea4748086485b62c9a226e7e8b1565f2f933fd7e86f03e66f7`

该 Shot 支持“compatible anchors + explicit visible state change 可以生成可见 handoff”的局部假设。它不支持
“任意 FL2VA 都会失败”，也不支持“Stock20 recipe、T8 pin 或 H3 model limitation 是本次主要原因”。

## Exact 30s Candidate And Findings

Primary:

```text
/home/reggie/ai-video-experiments/h3-causal-handoff-20260827-sLHhf1/outputs/final/qingyan-v13-causal-handoff-30s.mp4
SHA-256 d3dbfbed3c57d3474d20b4ccd7f9950fb382c97fc11f3664feb787091e89df6d
31,299,021 bytes; H.264; 1080x1920; 24 fps; 720 video frames;
video/audio stream duration 30.000s; AAC 48kHz stereo
```

No-BGM review master:

```text
/home/reggie/ai-video-experiments/h3-causal-handoff-20260827-sLHhf1/outputs/final/qingyan-v13-causal-handoff-30s-no-bgm.mp4
SHA-256 a0b728237fe30f86babe39b89e7154031eb275aac4c97ebf09e88a640721c33f
```

Frame-exact timeline：

| Frames | Time | Beat |
| --- | --- | --- |
| `0-107` | `0.000-4.500s` | v12 problem |
| `108-231` | `4.500-9.667s` | new causal recommend/handoff Shot |
| `232-375` | `9.667-15.667s` | v12 open/use |
| `376-466` | `15.667-19.458s` | v12 effect |
| `467-641` | `19.458-26.750s` | v12 walk |
| `642-719` | `26.750-30.000s` | shortened deterministic packshot |

The new Shot closes the missing product transfer，但 exact boundary contact sheets still show：

| Boundary | Verdict | Evidence |
| --- | --- | --- |
| `4.500s` problem -> handoff | `FAIL` | 少女独处直接切到老人已在场并持产品；character entrance 不可见。 |
| within handoff Shot | `PASS` | 推荐/递出/共持/接过/放手连续可读。 |
| `9.667s` handoff -> use | `FAIL` | 老人仍在场直接切到少女单人使用；elder exit/release of presence 未表达。 |
| `15.667s` use -> effect | `PASS_CAUSAL_ORDER` | 喷用先于效果；performance naturalness 仍为 human-first。 |
| `19.458s` effect -> walk | `FAIL` | 单人效果 Shot 后老人重新出现；presence re-entry 未表达。 |
| `26.750s` walk -> packshot | `PASS_AS_COMMERCIAL_CUT` | product close 可作为明确 commercial cut；whole-ad pacing 未评估。 |

Whisper 只识别一段约 `4.20-7.08s` 的老人推荐；ASR 同音字错误不改变 exact audio bytes，也不替代 copy
truth 或 lip-sync verdict。Scene detector 返回单 scene，和已知的 deterministic hard cuts 不一致，因此该工具
结果不能代替 frame-boundary review。

## Attribution And Plan Impact

1. 四臂实验已经把 forced scale transition / terminal snap 的主要原因收敛到 incompatible last anchor；本实验
   的 compatible anchors 再次没有产生该 failure class。
2. 精确 causal wording + compatible anchors 可以在一个 Shot 内完成 holder transfer，但没有证明 deterministic
   compiler，因为 prompt 仍是 manual authoring。
3. `holder` 修复不等于 30s continuity 修复。Character presence/entrance/exit 必须与 prop holder、hand contact、
   action phase 同级成为 pre-generation pairwise contract。
4. Intentional endpoint hold 与 forced terminal freeze 不能只用低 motion threshold 区分；必须结合 requested
   close state、anchor compatibility、snap 与 human/semantic evidence。
5. 当前没有 evidence 支持优先升级 Stock20 recipe/pin、把 FL2VA 视为普遍 lane mismatch，或继续扩 generic
   post-media Gate。下一步应先完成最小 typed intent / pairwise readiness / exact H3 compiler，再测试包含
   visible entrance、handoff、exit/release 和 use start 的最小 multi-Shot sequence。
6. H3 current minimum `124` frames at `24 fps` means each generated Shot is `5.167s`；`8-12s / 3-4 generated
   Shots` 不是可执行的最小 experiment。下一轮应使用 `2-3` generated Shots (`10.333-15.500s`) 或明确固定
   surrounding context，而不是靠 post trim 隐藏不可达状态。

## Human Review Boundary

本记录没有将 v13 升级为 HUMAN FAIL 或 HUMAN PASS；`30s causal continuity=FAIL` 来自 exact frame-boundary
evidence，足以阻止 plan 将其作为首条 30s PASS。用户仍可用正常速度观看 primary / no-BGM master，独立判断
hand naturalness、performance、dialogue/lip-sync、Hook Readability 与整体 pacing。任何重编码或修改都会产生
新 SHA，并需要新的 whole-video verdict。
