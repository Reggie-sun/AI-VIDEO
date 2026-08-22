# Shot Continuity P0 Preflight And Image Set Record

Date: 2026-08-23

## Purpose

本文记录 `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md` 最新版本下的当前执行边界：
Seedance 2.0 model-isolation 草稿、Local T8 fresh inventory、独立 4-Shot 雨夜车站项目的 GPT Image 2
候选图，以及尚未关闭的 P0 freeze gate。

本记录不是 runtime implementation、Provider readiness、P0 closure、媒体质量通过、candidate activation、
Final Acceptance、push 或 release authorization。当前 code/tests、active spec/plan、Production records 与
fresh runtime evidence 仍是 source of truth。

## Governing Contract

当前 canonical artifacts 是：

- `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`；
- `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`。

计划在 `cbeae2b` 后明确把 Milestone 3 / Phase P0 设为所有 qualification 与 implementation lane 的共同
前置条件。P0 必须先冻结 fresh inventory、exact 3–4 Shot `RealShotValidationSet`、至少两个 continuity
edges、每个 edge 的 `ContinuityTransitionPolicy`、四锚点来源、prompt、output contract、Stock20 baseline、
rubric，以及 M0/M1 candidate `GenerationExecutionStackIdentity` payloads。P0 关闭前不得开始 M0，也不得把
任何 candidate 描述为 active Production identity。

## Current Repository Truth

记录前 checkout 为 `main`，HEAD 为 `cbeae2b`，相对 `origin/main` ahead 10。以下 Seedance files 存在
uncommitted draft：

- `src/ai_video/production/seedance_capabilities.py`；
- `src/ai_video/production/seedance_profile.py`；
- `tests/test_production_seedance.py`。

草稿实现了 exact official subset ordering、base/Fast/Mini mode isolation、pricing exact-set validation、
single-deployment consistency 与 base-only active profile construction。focused test 当前 evidence 是
`109 passed`，更早的相关 combined selection 是 `270 passed`；`git diff --check` 通过。native reviewer
verdict 是 `accept with concerns`，没有 blocking issue；其两个 non-blocking concerns 是缺少显式 Mini
identity 参数化断言，以及 Fast/Mini invalid resolution 尚未覆盖完整 cross product。

这些结果只证明当前 working-tree draft 的离线行为。上述 files 尚未 commit，也没有 exact staged/commit-range
Harness receipt，因此不得描述为已完成的 Milestone 2 runtime truth。

`index.json` 与 `.workflow/.scratchpad/` 也处于 dirty/untracked 状态。本记录没有覆盖、stage 或 commit这些
paths。

## Local T8 Fresh Inventory

本轮在 loopback `127.0.0.1:8188` 对当前可启动的 local ComfyUI environment 做过 fresh inventory preflight。
已确认：

- ComfyUI `0.33.2`，commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- Python `3.12.13`，PyTorch `2.11.0+cu130`，GPU `RTX 5090`；
- ComfyUI-MiniMax-H3-Turbo version `1.36.2`，commit
  `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`；
- VideoHelperSuite commit `4ee72c065db22c9d96c2427954dc69e7b908444b`；
- stock Ref2VA checkpoint SHA-256 `9eef934046...76a9`；
- pruned FL2VA checkpoint SHA-256 `e889202c41...c47a`；
- pruned Ref2VA checkpoint SHA-256 `9255f52b66...5779`；
- Qwen CLIP SHA-256 `35a88d5104...f2c6`；
- video VAE SHA-256 `7c1f131492...e522`；
- audio VAE SHA-256 `8e505d95dd...db48`。

object schema 同时确认 `MiniMaxH3AudioConditioningT8` 暴露 literal `Hybrid`、first/last anchor 与
reference image/video/audio inputs；pair inspector 绑定 exact pruned pair，loader 区分 `base_only` 与
`apply_artifact`。inventory 时没有可用 Hybrid artifact/sidecar，因此 M1 尚未 ready。没有执行 M0/M1 媒体
generation，也没有形成 P0 freeze receipt。

## New GPT Image 2 Candidate Set

用户指定使用 GPT Image 2 MCP，并选择建立新的 canonical visual direction，而不是把历史 V8 guide/imagegen
endpoint 升格为新项目 truth。当前独立候选图仍位于 repository 之外的 MCP output root，尚未复制到项目、
注册 Asset Registry、绑定 Project revision 或形成 materialization receipt。

已确认四张独立候选图均为 `1659x948`：

| Candidate | Output directory basename | SHA-256 |
| --- | --- | --- |
| A1 | `20260823-005833-create-continuity-anchor-a1-earlier-in-the` | `61ee0609f3c7aae86ca78ed02e4080b35a59608b7c3a7aff0f2389a47f57f9cb` |
| A2 | `20260823-005643-now-create-continuity-anchor-a2-one-shot-e` | `38725a3aacbaab0536f26cb24b7e50fe8617b79cfc984ada0efab7f9b144f614` |
| A3 | `20260823-005509-create-the-immediately-preceding-continuit` | `03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c` |
| A4 | `20260823-005119-generate-one-photorealistic-cinematic-cont` | `ac6b83a8c2abc2f21d50d29a4aa4c377d6044bb297e58d2d4c9ae56e4468f377` |

稍后出现的 A0 retry output：

```text
20260823-010517-the-previous-a0-request-timed-out-and-save/image-01.png
```

其 SHA-256 同样是 `61ee0609f3c7aae86ca78ed02e4080b35a59608b7c3a7aff0f2389a47f57f9cb`，
与 A1 字节级相同，不是第五张独立 anchor。A1–A4 可以构成四张图、三个相邻 edges 的候选顺序，但当前仍
缺少 exact-set human freeze；A2 的人物 scale/FOV drift 也必须保留为 visual concern。不得由图像生成成功、
hash 或 agent inspection 推导 P6/human PASS。

用户已要求暂停继续生图。本记录动作没有再次调用 GPT Image 2、ComfyUI、remote Provider 或 media tooling。

## Historical Evidence Boundary

历史 V7/V8 只可作为 failure evidence 与 workflow scaffolding：

- V7 已被用户以 identity 与 camera continuity 失败否决；Seedance result 为 fetched-unactivated；
- V8 raw H3 Shot 2 camera motion 被否决；corrected review derivative 不是 activated source；
- V8 guide terminal 与 image-generation endpoint 也被否决；
- 历史 creative hashes、generic fixtures、rejected endpoints 与 paid permits 不得升格或复用到新项目。

可复用内容只包括 proven workflow shape、exact terminal extraction方法、camera measurement recipe 与 schema
scaffolding。新的 Project revision、Character/Scene/Shot artifacts、Registry identities、policies、prompts、
materialization receipts 与 human review必须重新建立。

## MiniMax Delegation Evidence

MiniMax read-only explorer 的 Role 是 `explorer`，Scope 是 current continuity spec/plan 与 exact V7/V8 evidence
roots；runner model 为 `MiniMax-M3`，transport 为 MiniMax CLI/Claude runner bridge，最终 status 是
`DONE_WITH_CONCERNS`。其原始结论是：只有历史 T8 AV、V8 raw H3/exact terminal、camera measurement recipe
与 project schema 可复用为 scaffolding；V7 Seedance、V8 rejected guide/imagegen endpoint 与旧 creative hashes
不得 promotion，新 4-Shot 雨夜车站项目仍需独立 creative、materialization、policies 与 human receipts。

该 explorer 首次较长 invocation 曾因 structured-output retry exhaustion 终止；缩短 output 后做了一次 bounded
fresh retry并得到上述结果。另两个 bounded MiniMax writer attempts 因 command grant mismatch 结束为
`BLOCKED`，没有获得可依赖的完成 receipt；parent 保留了当前 working-tree draft并以 native tests/review复核。

sanitized automatic diagnostic 位于：

```text
/home/reggie/.codex/session-diagnostics/minimax/01a02a0e-f757-76e3-8a48-00cae28a0d95-e82349bc2a2a7596.md
```

该 diagnostic 的 terminal truth 同样记录 explorer `DONE_WITH_CONCERNS`，以及两个 writer 因
`permission_or_grant` / `tool_error_loop` 而 `BLOCKED`。diagnostic 是 developer workflow evidence，不是 Product
Runtime state。

## Verification Boundary

本 checkpoint 已有的执行证据：

- Seedance focused test：`109 passed`；
- related combined test selection：`270 passed`；
- Seedance draft `git diff --check`：pass；
- native reviewer：`accept with concerns`，无 blocking issue；
- GPT Image 2 output dimensions与 SHA-256：已本地复核；
- A0 retry 与 A1：SHA-256 identical。

本记录没有为已有代码补跑测试，也没有执行新的 Provider/media/network validation。record 自身只运行
documentation category的 mandatory Harness checks，并且该 receipt不能替代后续 code exact-range Harness、
真实 Shot generation、full-speed human review或P6 adjudication。

## Continuation Boundary

下一窗口必须从以下顺序继续：

1. 由 human 明确冻结 A1–A4，或先处理 A2 scale/FOV drift；不得把 duplicate A0当新 anchor。
2. 将 approved images复制到 task-owned project path，计算 exact bytes并建立新的 Project/Character/Scene/Shot
   revision、Asset Registry identities与materialization receipts。
3. 冻结 exact 4-Shot `RealShotValidationSet`、至少三个 adjacent edges、每个 edge 的
   `ContinuityTransitionPolicy`、四锚点来源、prompts、Stock20 baseline、rubric与M0/M1 stack payloads。
4. 生成并验证 content-addressed P0 freeze receipt。只能在此之后开始 I1/V1、M0 或任何 winner selection。
5. 单独处理并 commit Seedance draft，针对 exact staged/commit range运行 policy-required Harness；当前 record
   commit不能证明该草稿已完成。

## Agent Guardrails

- 不把 GPT Image 2 output当作已注册 Reference Asset或Final Shot Visual。
- 不把四张候选图或其 hashes 当作 P0 closure、creative PASS或P6 acceptance。
- 不把 A0 duplicate计为新的 Shot anchor。
- 不从 V7/V8 复制 rejected endpoints、creative hashes、permits或activation truth。
- P0 关闭前不执行 M0/M1，不创建 active Production stack identity。
- continuous take 不允许 cross-stack；hard cut与scene boundary继续服从最新
  `ContinuityTransitionPolicy` contract。
- 不 blind retry、fallback Provider、自动 activation或从 unknown outcome推断 success。
- 不覆盖、stage或commit unrelated dirty files；继续前重新检查 live-agent ownership与exact target overlap。
