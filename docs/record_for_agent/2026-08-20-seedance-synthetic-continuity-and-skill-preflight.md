# Seedance Synthetic Continuity And Creative Skill Preflight Record

Date: 2026-08-20

## Purpose

本文记录一次明确授权的 Ark-native Seedance synthetic/illustrated I2V 两镜 continuity proof，以及由此固化的 Creative Skill authoring gate。它是 verified runtime evidence 与 Agent workflow guardrail 的 durable note，不是新的 Provider implementation authorization，也不把本次 fetched output 描述成 Production-activated 或通用 quality acceptance。

## Current Runtime Truth

本次 run 使用 `doubao-seedance-2-0-mini-260615`，每镜请求 5 秒、`864x496`、24 fps、16:9、`generate_audio=false`。Provider 实际返回每镜 121 帧 / 5.042 秒、H.264、无音轨；因此 exact output validator 保持 fail-closed，两个候选均为 fetched/validate 状态，未 activation。

Run scope：

```text
runs/seedance-anime-grand-action-continuity-20260820-001/
```

两个付费 POST 均在同一 task-scoped authorization 内完成：

- `submit_posts`: `2`
- `fetched_outputs`: `2`
- `activations`: `0`
- `blind_retries`: `0`
- `permit_remints`: `0`
- per-call upper bound: `1.5 CNY`
- aggregate upper bound: `3 CNY`

第二镜的唯一 `first_frame` egress bytes 与第一镜实际 decoded terminal PNG 完全绑定：

```text
5d52378e3eb92605ff33ab74e53fb6b9214429c6280603f0f3d27b296bc53f25
```

这不是预选 bridge frame；拓扑是 `shot1_actual_terminal -> shot2_first_frame`。

## Session Work And Decisions

### Creative Skill Authoring

本次 prompt/continuity authoring 按以下顺序使用了匹配 Skill：

1. `hell-grind-aigc-skill`：定义 Shot 1 的 terminal/open handoff、Shot 2 的 immediate continuation、动作与空间 continuity invariants。
2. `higgsfield-prompt`：采用单一主动作链和清晰的镜头 endpoint，避免多重相互冲突的 camera instruction。
3. `higgsfield-seedance`：把已批准的 continuity intent 适配为 Seedance I2V continuation 表达。
4. `higgsfield-camera`：固定正面 tracking、恒定人物尺度与单一 `Dolly Out` 方向。

这次 authoring 的关键修正是：Shot 2 不再从预先挑选的 bridge image 开始，而是从 Shot 1 的真实末帧继续；角色保持正面、中心轴与全身尺度，动作由腾空顶点接到下落、双脚着地、起身举臂和天空光环。

### Repository Guardrail

此前遗漏 Skill 的根因是 `AGENTS.md` 只写了 `SHOULD proactively use`，没有在付费 preview 前设置 evidence gate。本次已在本地 `main` 的 commit `ac5119a` 中将其固化为 `Creative Skill Preflight Gate`：

- 相关创作任务必须在首次 prompt/continuity/script authoring 前实际读取匹配 Skill，并在 commentary 声明选择和约束；
- 进入 live/paid exact preview、permit mint/consume 或 POST 前，必须报告 open/close state、terminal handoff、axis/action/camera endpoint、prompt adaptation 和 lint/preflight evidence；
- evidence 不完整时必须 fail closed；
- run script、Provider adapter、Manifest、receipt、timeline 与 renderer 不得 import 或调用 Skill；`runtime_skill_calls = 0` 是正确 runtime boundary。

## Verification And Evidence

### Media And Boundary

最终 stream-copy 文件：

```text
runs/seedance-anime-grand-action-continuity-20260820-001/output/two-shot-continuity.mp4
SHA-256: 0fc124c6dee72fd120a0d394cd911e1dba3295027002455953929747fb967330
```

已测量为 H.264 `864x496`、24 fps、242 帧、10.084 秒、无音轨，文件大小 `3,338,880` bytes。两个输入片段 hash：

```text
shot-1.mp4: 4e72d0e5946a4ac0361c84d2b7c5a6863e8bbfcf612610c8ed00f8dbee909ef8
shot-2.mp4: ed91af8af236f8530dca0d4a54517af0bc0a8d8aa7d2135f2b6fd99a43e02606
```

边界检查结果：

- Shot 1 terminal PNG 与 Shot 2 egress first-frame input SHA-256 相同；
- decoded boundary SSIM：`0.964020`；
- decoded boundary PSNR：`36.524616 dB`；
- boundary mean absolute luma change：`2.876813`；
- neighboring-frame change median：`2.276634`；
- boundary / neighbor median：`1.263625`；
- 上一轮预选 bridge-frame run 的 boundary SSIM：`0.338311`。

这支持“本次没有上一轮的尺度/位置 teleport”；视觉 review 将 action、axis、environment、light、space 与 state 判为 pass，identity 为 pass with minor concern。480p 与顶点处短暂 hold 仍是 minor concerns。

### Technical Inspection

Project-local `video-analysis` 对最终文件报告单一 scene、11 个抽帧、无音轨；这只是 raw technical evidence，不替代 semantic continuity 或 subjective quality acceptance。边界 contact sheet：

```text
runs/seedance-anime-grand-action-continuity-20260820-001/evidence/boundary-frames-116-127.png
SHA-256: e8eeccc4225140ffa18179379398370dde7e819a7c93b4d9566a8e3079436825
```

完整 continuity analysis：

```text
runs/seedance-anime-grand-action-continuity-20260820-001/evidence/continuity-analysis.json
SHA-256: 4aa889f137220328be31abe12077d7a312a6e4738f8d21fe105c6ab841f51274
```

Live report：

```text
runs/seedance-anime-grand-action-continuity-20260820-001/evidence/live-report.json
SHA-256: 694f667a1d365256c733b99b37143700e168404a1ad2ff22de6937cbe8ddcabf
```

### Control-Plane Verification

`AGENTS.md` 的 control-plane diff 通过了 exact staged snapshot 与 exact commit-range Harness：

```text
.agent/harness/runs/creative-skill-preflight-gate-commit-ac5119a/receipt.json
```

Harness result：`51 passed`；receipt `fresh=true`、`policy_matches=true`、`scope_worktree_clean=true`。Native named `reviewer` 对最终 gate 给出 `accept`，确认 authoring preflight 与 runtime no-Skill-dependency 边界没有冲突。

本窗口另执行了 `capture-minimax-session`；其 sanitized report 记录当前 Codex session 未检测到 MiniMax invocation、activity 或 structured terminal result：

```text
/home/reggie/.codex/session-diagnostics/minimax/01a01d7e-b64d-7780-8e0e-46727c1f2899-ab15b013b04d6116.md
```

该诊断只说明 runner activity，不说明应用代码或 Provider 媒体质量。

## Assessment

本次 continuity proof 解决了上一轮的主要失败模式：上一轮 Shot 1 末帧与 Shot 2 预选 bridge frame 的 subject scale、position 和 state 不一致；本次直接绑定真实 terminal，边界 similarity 从 `0.338311` 提升到 `0.964020`，并通过正面恒尺度动作链保持空间连续。

但本次仍只能称为 bounded paid/cloud diagnostic 与 technical/human continuity review pass with minor concerns：

- Provider 返回时长/帧数与 exact 5-second requirement 不一致，因此没有 activation；
- 480p 低于 preferred iteration-review resolution；
- 无音轨，且没有把任何 Provider audio 带入 P4 composition；
- 没有声称 Production QA acceptance、final delivery acceptance 或通用 Seedance quality benchmark。

## Remaining Risks Or Next Work

1. 若要把 synthetic/illustrated inline input lane 提升为正式 Provider runtime contract，仍需沿 P8 spec/plan 完成 exact transport、provenance、egress、typed failure 与 offline tests；本次 run script 不是该 runtime implementation。
2. 若要 Production-activate 该类输出，必须先解决 Ark 返回的 `121 frames / 5.042 seconds` 与 exact requirement 的 compatibility，不能通过放宽 validator 或猜测 trim 解决。
3. 若要声称更高主观质量，需要独立的 blinded review、目标分辨率和更长动作/多 Shot 验证；当前 video-analysis 单 scene 结果不能替代这些 gate。

## Agent Guardrails

- `first_frame` 必须绑定实际上一个 Shot 的 terminal bytes；不得用预选 bridge 或“看起来相似”的图片替代。
- synthetic/illustrated 角色 lane 不等于真人/identity-bearing lane；分类、来源、权利和 bytes identity 仍需明确 evidence，ambiguous input 必须 fail closed。
- `fetched`、`validated`、`activated`、`continuity reviewed` 与 `quality accepted` 是不同状态；不得互相冒充。
- Skill 只在 Agent authoring 阶段提供 advisory guidance；不得让 Skill 成为 Provider selector、Manifest writer、timeline owner、renderer 或 lifecycle owner。
- 付费调用计数、egress、permit、activation 和 unknown-outcome recovery 必须继续由 AI-VIDEO gates 管理；不得 blind retry、permit remint 或自动 fallback。
- 本次 record 只新增本文件；运行目录、媒体与外部 sanitized diagnostic 均保持各自 local-only ownership，未 push/release。
