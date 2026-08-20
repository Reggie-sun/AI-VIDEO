# Local MiniMax H3 Quality Profile And Alice A/B Record

Date: 2026-08-20

## Purpose

本文记录 Local MiniMax H3 `fl2va` 画质修复 slice 的稳定 checkpoint：独立 quality profile、同一 Alice 两镜头受控 A/B、原生高分 reference provenance、真实媒体测量和 exact-terminal continuity。它是 durable runtime note，不是新的 Provider/live/paid 授权；代码、测试、Harness receipt 与 live artifacts 仍是 source of truth。

## Current Runtime Truth

- Repository: `/home/reggie/vscode_folder/AI-VIDEO-shot-router`；branch `agent/shot-router`；implementation checkpoint commit `06674cbac02acc92901de92c4c6dc8d245427114`（parent `460528a99854d691d767c940aa3a69eb20d9fe9f`）。该 commit 已在本地，未 push、merge 或 release。
- 本次新增的是 additive `minimax_h3_fl2va_quality_local`，不替换 sealed technical profile。旧文件 SHA-256 保持不变：
  - `workflows/profiles/minimax_h3_fl2va.json`: `efca71d54bdd9f8a935c1911429d00b38e351e497df35db630b4bdab320f1d1c`
  - `workflows/templates/minimax_h3_fl2va_api.json`: `c736a12f35fd89f10a8db86f0769a85ca7bceb80d16feab62a1666cfd078737b`
  - `workflows/bindings/minimax_h3_fl2va_binding.yaml`: `e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c`
  - sealed old profile content hash: `456b59c7a907d4b07c7d951d63ec03cbd0fb5c64638dbc8dad870aca09e2b604`
- Quality lane files and seals：`workflows/profiles/minimax_h3_fl2va_quality.json`（file SHA `fad986fddb39ff1a3769c92b7a62350761bbf45414a52b9ee1b0961b9a609bbf`，content hash `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`）、`workflows/templates/minimax_h3_fl2va_quality_api.json`（SHA `8b6c338279d8af768fae8106034f9f26e8e9d59583e95a8ca8b16d36a930ad65`）和 `workflows/bindings/minimax_h3_fl2va_quality_binding.yaml`（SHA 与旧 binding 相同）。
- Quality profile 本次 A/B 固定 `1344x672`、`24 fps`、`124 frames`、H.264 `re-encode`、CRF `17`；保持 `minimax_h3_fl2va_pruned_int8_convrot`、`res_multistep`、`simple`、`20 steps`、VAE 和 prompt/reference binding 不变。ComfyUI `SaveVideo` 的真实 API 动态字段是 flat dotted keys：`codec=h264`、`codec.encoding=re-encode`、`codec.encoding.crf=17`。
- Router 四档 continuity contract、exact-terminal binding、Manifest/schema、Registry layout、CLI、P5 dependency owner 和 `ProductionStateCommitter`/state writer 没有改变。相关实现变更只涉及 quality profile/template/binding、`comfy_video` quality validation、回归测试和 canonical research/baseline 更新。

## Session Work And Decisions

- 官方 H3 资料把约 `1.0 MP` 的 `1344x768`（32 的倍数）作为 16:9 full-quality canvas；本片保持既有 `2:1` 构图，因此首轮选择合法但不是官方 16:9 native canvas 的 `1344x672`。社区关于 BF16、CRF、VAE 和 upscaler 的信号只作为假设，不把 int8、steps 或 refiner 写成已证实根因。完整来源和 schema 记录在 `docs/research/2026-08-20-minimax-h3-local-quality-parameters.md`。
- 旧 technical control 的源片已经只有约 `559/798 kbps`，最终片又发生二次有损编码；quality lane 让 H3 source encoder 显式使用 CRF 17，并把两个兼容 source clip 用 concat demuxer stream copy 连接，避免 final composition 再次重编码。旧片与新片的 codec、pixel format、码率和原因必须按下面的实测值解释，不能用文件大小代替质量证据。
- Alice 的 `608x352` 插值 reference 只作为首轮受控 A/B 的相同输入，不能称为 high-resolution reference。人物细节仍受 reference 限制，因此随后使用现有 loopback-only P7 Qwen Image Edit 2511 lane 生成一次原生 `1344x672` reference，并保存 exact provenance；没有调用 remote/paid Provider。
- P7 reference 的 local result 是 `succeeded`，但 materialize 后 P5 candidate scope validation 拒绝 activation，状态为 `outcome_unknown`。已执行 explicit recovery、没有 blind retry，并把 exact bytes 诚实作为 H3 conditioning reference 导入；不把它描述成 activated P7 candidate。

## Verification And Evidence

### Controlled A/B With The Same Interpolated Reference

| Measurement | Old technical control | Quality profile, same reference | Delta/meaning |
| --- | --- | --- | --- |
| final artifact | `/home/reggie/vscode_folder/AI-VIDEO/runs/h3-shot-router-generalization-20260820-v2/evidence/alice-cafe-exact-terminal.mp4` | `runs/h3-shot-router-quality-20260820-v1/evidence/alice-cafe-exact-terminal.mp4` | both are two-Shot evidence outputs |
| final SHA-256 | `fea79de950fb44ea146abf85ddff6b2ad325b9012bcef4148f6cc9f62dac6ff8` | `da5cb85f52a2998588c5fbdd2d7c9941b92d8c65fab4e40e45d1d6a424bbb4e1` | exact bytes recorded |
| resolution / frames | `1024x512`, 248 | `1344x672`, 248 | quality lane is +72.3% pixels |
| source video bitrate (Shot 1 / Shot 2) | `558726 / 797541 bps` | `2993933 / 2957600 bps` | source detail loss is substantially reduced |
| final video bitrate | `1007718 bps` | `2975733 bps` | final old output was re-encoded; quality final uses stream copy |
| codec / pixel format | H.264 High / `yuv420p` | H.264 High / `yuv420p` | codec family is comparable |
| sampled detail, same-scale 16 frames | Laplacian `109.154`; Tenengrad `9170.554` | Laplacian `112.647`; Tenengrad `9701.114` | `+3.20%` / `+5.79%` |
| decoded boundary SSIM | `0.928515` | `0.936091` | boundary remains exact-terminal and improves |
| project-local `video-analysis` | old output flagged `low_resolution` | `issues: []`, one scene, `336/336` unique sampled frames | technical evidence only |

The same-reference A/B therefore confirms output resolution and encoder settings as contribution factors, but does not isolate which of the two is responsible for each gain and does not explain all original softness.

### Native P7 Reference Follow-up

- P7 report: `runs/h3-shot-router-quality-20260820-v1/p7-reference-report.json`。
- Native reference: `runs/h3-shot-router-quality-20260820-v1/inputs/alice-cafe-reference-p7-native.png`，`1344x672` RGB，SHA-256 `99253a9dc5a705487a35b016e18e5fb5b693d78f444a959054c1fbce0c73ed6d`。
- Provenance：one local loopback call to `http://127.0.0.1:8188`；provider request id `d87841c6-24aa-481a-9183-8e2984aa489d`；profile `local-image-profile:sha256:3871ae162aabe70ff3217ea6a9dbc4e83194b70a1d00e2ca249da202d4d8c6df`；workflow SHA `34f1d2a67d049b646eef1c8f0c51aa8c1ad6b9eb5ef176c9ec422c3ff384a85f`；ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；`provider_calls=1`、`remote_used=false`。
- Final artifact：`runs/h3-shot-router-quality-p7-20260820-v1/evidence/alice-cafe-exact-terminal.mp4`，SHA-256 `05c00691a7a04d8e0864f018073ea746ccba3e0cba38aa0c9f651180d30bae9e`，`1344x672`、H.264 High、`yuv420p`、248 frames、video bitrate `2653350 bps`、format bitrate `2780985 bps`、AAC audio。两个 source clip 的 video bitrate 为 `2547971` 和 `2758776 bps`；final `video_reencoded=false`，为 concat demuxer stream copy。
- Native-reference final 的同尺度 Laplacian mean `244.187`（相对旧片 `+123.71%`）、Tenengrad mean `11032.689`（`+20.31%`）、decoded boundary SSIM `0.937613`；project-local `video-analysis` 报告 one scene、`336/336` unique sampled frames、`issues: []`。这支持“低输出/弱编码 + 低原生 reference 的共同作用”，不能外推为通用 H3 或 P7 M8 quality acceptance。
- P7 recovery 保留完整 orphan evidence；active project/registry/graph 回到 recovery 后的 exact tuple。这个 reference 是 H3 conditioning provenance，不是 P7 candidate activation proof。

### Exact-Terminal Continuity

- Same-reference quality run：Shot 1 terminal SHA 与 Shot 2 `first_frame` input SHA 都为 `894db2c9ded146a26c6cfaf50230708750af4e8386929926c06bfe3aec1f2893`，`exact_terminal_to_first_frame=true`。
- Native-reference quality run：Shot 1 terminal SHA 与 Shot 2 `first_frame` input SHA 都为 `2dd12cac1381fd2cbc35067fc1d6f76b4e190135f5edc535172d94270f9ff27b`，`exact_terminal_to_first_frame=true`。
- 这证明 continuity technical contract 仍成立；它不等价于 C2 derived-keyframe、blinded subjective continuity 或通用 shot quality acceptance。

### Tests And Harness

- Implementation regression tests previously passed：`pytest -q tests/test_production_comfy_video.py` 为 `21 passed`；相关 workflow tests 为 `9 passed`；focused production/comfy suite 合计 `63 passed`。
- Fresh Harness receipt：`.agent/harness/runs/20260820T052956542992Z/receipt.json`。`make harness-verify` 的 workflow tests、task-delta Architecture Gate 和 production video-provider checks 全部 passed（production provider `818 passed`）；`make harness-receipt RECEIPT=.agent/harness/runs/20260820T052956542992Z/receipt.json` 返回 `artifact_integrity=true`、`closure_eligible=true`、`fresh=true`、`integrity=true`、`passed=true`、`policy_matches=true`、`schema_supported=true`、`scope_worktree_clean=true`、`snapshot_matches=true`、`workspace_cleanup_confirmed=true`。
- 本次 record 操作没有重新运行 tests、Harness、ComfyUI、`video-analysis`、Provider 或媒体生成；上述数字来自 implementation checkpoint 的 fresh receipt 与已存在的 live reports。record 本身只需要文档 diff check。

## Assessment

受控 A/B 已证实：显式 H.264 CRF 17、较高输出 canvas 和避免 final 二次有损编码能显著提高 source bitrate，并带来可测的 sharpness、SSIM 和 resolution 改善；换成真正原生 `1344x672` Alice reference 后，细节指标进一步大幅提升。因此当前 Alice 模糊的最佳证据解释是“输出分辨率/编码损失 + reference 分辨率瓶颈”的组合，而不是已证明的 int8、20 steps、sampler、VAE 或无 refiner 单一根因。

这两个变量在首轮是一起变化的，所以不能声称已经把 resolution 与 CRF 的独立贡献完全分离。当前证据足以冻结 `minimax_h3_fl2va_quality_local` 作为 Alice/Shot Router 的更高质量本地基线，但还不足以称为通用 H3 quality benchmark、P7 M8 acceptance 或 subjective editorial acceptance。

## Remaining Risks Or Next Work

- 建议下一步先用当前 quality profile 和 native reference 做约 5 分钟的代表性 rough cut，再按全片暴露的失败类型决定是否继续调 shot 参数。这样能先验证质量基线在不同景别、运动、光线和 continuity 压力下是否稳定，避免只在 Alice 两镜头上过拟合。
- 暂不把 BF16/int8、steps、refiner、VAE 或 sampler 作为确定根因；如果 rough cut 仍有稳定的 temporal/detail failure，再做一次只改变单变量的短 A/B，并沿用相同 ffprobe、video-analysis、sharpness、SSIM 和 continuity 证据。
- `1344x672` 保持当前 `2:1` 构图，但不是官方 16:9 `1344x768` full-quality canvas；后续若改 aspect ratio 必须重新确认 creative contract 和 downstream composition。
- P7 native reference 的 candidate activation scope failure 已 recovery，但当前 record 不把它升级为 activated P7 state；任何未来 reference regeneration 仍需 exact local provenance 和相同 writer/recovery 边界。
- 本轮没有 remote/paid Provider call、cloud fallback、secret lookup 或新 benchmark；没有新的 live evidence 被本 record 创建。

## Agent Guardrails

- 不覆盖、不重 seal、不改写已验收的 `minimax_h3_fl2va` technical profile、workflow、binding 或历史 hashes。
- 不把 `codec=auto`、低 bitrate、插值 reference、文件变大或肉眼印象单独当作 quality proof；必须保留 source/final codec、CRF/bitrate、pixel format、resolution、sampled detail、boundary SSIM 与 exact SHA。
- 不把 P7 result `succeeded` 或 H3 local fetch 当成 activated candidate；`outcome_unknown` 必须走 explicit recovery，不能 blind retry。
- 不把 exact-terminal continuity technical proof、stream-copy final artifact 或 AAC stream 当作 P4 audio ownership、subjective quality 或 full-production acceptance。
- 后续任何 H3 parameter exploration、new live generation、benchmark、remote/paid call、C2 quality acceptance 或 schema/Manifest/writer 变化都需要独立 scope、授权和验证。
