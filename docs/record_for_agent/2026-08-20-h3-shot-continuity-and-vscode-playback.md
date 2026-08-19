# H3 Shot Continuity And VS Code Playback Record

Date: 2026-08-20

## Purpose

本文记录本 session 对 AI-VIDEO Local MiniMax H3 `fl2va` Shot Continuity lane、最小 two-Shot proof、VS Code 播放路径和 MiniMax session capture 的实际结论，供后续 Agent 继续实现或审查时复用。

本记录是 architecture/runtime note，不是新的 Provider/live/付费授权，也不把 playback workaround 描述成 continuity quality acceptance。代码、测试、sealed profile 和 durable evidence 仍是最终 source of truth。

## Canonical Continuity Contract

Shot N 的 exact activated terminal-frame evidence 可作为 Shot N+1 的 `first_frame` continuity input。该依赖继续沿现有 Manifest 2.8、`ProductionStateCommitter`、Asset Registry 和 P5 typed dependency edge 实现：

- terminal extraction、candidate activation、reopen/recovery 与 downstream invalidation 不创建第二 writer、第二 resolver 或第二 timeline；
- exact terminal PNG bytes 必须进入下一 Shot 的 `first_frame`，仅同名或路径相同不算证明；
- `last_frame` 只有 request/profile 显式要求时才绑定，不得由 adapter 静默增加、删除或降级；
- `fl2va` 与 `ref2va` 是不同 profile identity，不能混用 checkpoint、workflow 或 capability；
- Local H3 是低边际成本 draft/筛选 lane，只有显式选中的 Shot 才能进入付费 Provider lane。

## Official Upstream Workflow Baseline

Local H3 `fl2va` 使用 reviewed upstream baseline，而不是 ad-hoc raw smoke JSON：

- repository：`Comfy-Org/workflow_templates`；
- pinned commit：`0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416`；
- path：`templates/video_minimax_h3_i2v.json`；
- pinned URL：`https://github.com/Comfy-Org/workflow_templates/blob/0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416/templates/video_minimax_h3_i2v.json`；
- raw JSON SHA-256：`313b029321a8be303e827dad471bff3022ca564c8bf8c6198a3e70b65c599671`；
- upstream license：MIT；
- official core node：`MiniMaxH3ImageToVideo`，支持必需 `first_frame` 与 optional `last_frame`；
- model components：`minimax_h3_fl2va_pruned_int8_convrot.safetensors`、`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`minimax_h3_video_vae_fp16.safetensors`、`minimax_h3_audio_vae_fp32.safetensors`。

官方文件是 UI/subgraph workflow，只证明节点图与 model compatibility。AI-VIDEO 派生 profile 还必须保留 upstream provenance，记录所有有意修改，并转换为 deterministic API-format JSON：删除 UI-only notes、demo input asset 和非必需 UI/subgraph metadata；默认关闭 LoRA、remote refiner 与 cloud fallback；保留 native H3 conditioning、sampling、video/audio decode 和 MP4 output contract。upstream 更新不会自动改变 sealed production profile；升级必须重新 review、重新 seal hashes 并重新验收。

当前 derived artifacts：

- `workflows/templates/minimax_h3_fl2va_api.json`；
- `workflows/bindings/minimax_h3_fl2va_binding.yaml`，绑定 `prompt`、`first_frame`、optional `last_frame`、`seed`、`width`、`height`、`length/frame_count`、`steps/sampler`、`output_prefix`；
- `workflows/profiles/minimax_h3_fl2va.json`，seal upstream provenance、derived workflow/binding hashes、ComfyUI commit、四个 model hashes、native node inventory、loopback endpoint、frame-grid/duration/native-audio/output bounds。

## Local Proof And Artifact Truth

Canonical local proof 位于 `runs/h3-shot-continuity-live-20260819-v3/`；它在 loopback ComfyUI 上验证两次 local proof submit、exact terminal hash 进入下一 Shot `first_frame`、candidate/terminal activation、Manifest reopen 和 zero-call replay。该 technical proof 不等于 blinded subjective quality acceptance，也不证明 `ref2va` 或 cloud continuity live。

本 session 重点检查的最小 proof run 位于：

`runs/h3-minimal-shot-continuity-proof-20260819-v1/`

可用于人工审片的 playback-safe evidence：

- `evidence/continuity-review-playback-safe.mp4`；
- `evidence/shot-1-playback-safe.mp4`；
- `evidence/shot-2-playback-safe.mp4`。

原始项目资产在 `project/assets/files/`。其中两份 H3 raw MP4 的实测音量很低：

- `58248d72859293e164a94eb11f72276bf6e64e63a440f36b9c0479b251dd6828.mp4`：mean `-49.8 dB`，max `-30.2 dB`；
- `d721ffbd7756ea8e284648221f40abda4b559778b3bbbe8fa8b47462434d87c7.mp4`：mean `-54.2 dB`，max `-33.1 dB`。

因此 raw assets 在系统播放器中也可能听起来像无声；这不是 evidence path 错误。`evidence/*-playback-safe.mp4` 是面向人工审片的派生副本，编码为 `H.264 Main + AAC LC`，不应替代 raw provenance 或被误写成新的 generation output。

## VS Code Playback Path

为使 VS Code 直接打开正确的 review artifact，用户级配置已写入：

`/home/reggie/.config/Code/User/settings.json`

配置内容为：

```json
{
  "unmuteVideo.ffmpegPath": "/home/reggie/miniconda3/bin/ffmpeg",
  "workbench.editorAssociations": {
    "*.mp4": "unmuteVideo.viewer",
    "*.webm": "unmuteVideo.viewer"
  }
}
```

推荐打开：

`runs/h3-minimal-shot-continuity-proof-20260819-v1/evidence/continuity-review-playback-safe.mp4`

另一个稳定 review 文件是 `runs/continuity-review-vscode.webm`。该文件本身为 `VP8 + Opus + yuv420p`，系统文件播放器可以正常播放；当前 VS Code/Electron WebView 仍显示 `Video format is not supported`。因此 VS Code 的 `Open in external player` 是当前可靠的降级路径：它播放原文件，不复制、不转码、不改变 evidence。这个现象属于编辑器/WebView codec compatibility，不是 H3 continuity proof 失败。

## MiniMax Session Capture

新版 `capture-minimax-session` 已对本 session 捕获脱敏诊断：

`/home/reggie/.codex/session-diagnostics/minimax/01a01979-f2da-7c00-80b2-65ee2aea9ade-a9b5d57b307c42e1.md`

报告 schema 为 `3`，fingerprint 为 `a9b5d57b307c42e1`，同一 session 的重复捕获返回同一路径。Terminal truth 保持字段分离：`status=success`、`transport_exit_code=0`、`cli_exit_code=0`、`termination_reason=cli_exit`、`agent_status=DONE_WITH_CONCERNS`。报告还记录了 `tool_error_event`、`explorer_tool_mismatch`、`long_activity_gap`、`zero_terminal_evidence` 和 `read_heavy_exploration`，这些只是 runner/skill optimization signals，不是 AI-VIDEO application failure proof。

报告权限为 `600`，没有保存 raw prompt、精确 command、credential、environment value 或完整 Provider result。

## Boundaries And Next Work

- 本 session 的 VS Code 配置修改在用户配置目录，不改变 AI-VIDEO workflow、Manifest、Registry、profile 或 artifact layout。
- 不得把 playback-safe 副本、external player 成功或 system player 可播放写成新的 Provider quality acceptance。
- 不得因为 raw H3 MP4 的低音量而修改 continuity contract、自动抽取 source audio，或绕过 P4 `ResolvedTimeline -> HyperFrames` audio path。
- `ref2va`、three-lane comparison、blinded subjective acceptance 与 cloud continuity live 仍是后续独立 scope；任何新的付费/live Provider 调用仍需当前任务授权与现有 Paid Provider Gate。
- 当前 workspace 另有其他窗口的 staged modifications；本记录只新增本文件，不应把其他 staged files 一并提交。

## Agent Guardrails

后续 Agent 处理本 lane 时必须保持以下区分：

- `raw H3 MP4`、`playback-safe evidence` 与 `final production render` 是三个不同 artifact 层级；
- `system player can play` 不等于 `VS Code WebView can decode`；
- `external player fallback` 不等于 workflow、adapter 或 continuity runtime 已改变；
- `technical two-Shot proof` 不等于 subjective continuity quality acceptance；
- `official upstream update` 不得绕过 derived workflow/profile review、hash resealing 和 re-acceptance。
