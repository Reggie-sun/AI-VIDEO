# Local H3 Blur Diagnosis And Quality Boundary Record

Date: 2026-08-20

## Purpose

本文记录 `h3-shot-router-generalization-20260820-v2` 两镜头 Alice 咖啡厅视频的模糊问题、已经排除的错误路径、当前可验证的画质限制，以及后续 Local MiniMax H3 quality-profile 修复边界。

本记录只保存 diagnosis checkpoint。它不表示高画质 workflow 已实现，不构成新的远程或付费 Provider 授权，也不把 Shot Router technical acceptance、exact terminal continuity 或可播放成片描述成 subjective quality acceptance。

## Repository And Implementation State

记录创建前，本地 `main` 为 `cff6c5b`，相对 `origin/main` ahead 14，working tree 与 index clean。Shot Router 实现位于独立、clean 的既有 worktree：

```text
/home/reggie/vscode_folder/AI-VIDEO-shot-router
branch: agent/shot-router
HEAD: 460528a
```

该 branch 的相关 checkpoint 为：

- `e18e5ce feat: add provider-neutral shot routing`
- `f94bfc9 fix: separate shot continuity modes`
- `460528a test: prove shot router input variation`

因此，Router 的四档 continuity 与 variation coverage 已存在于 branch-local implementation，但尚未 merge、push 或 release。当前 `main` runtime baseline 仍将 Router 记录为 pending；不得用 branch-local commit 改写 `main` truth。

## Verified Alice Two-Shot Evidence

本次检查的真实 local ComfyUI run：

```text
runs/h3-shot-router-generalization-20260820-v2/
```

`live-report.json` 记录 `provider=comfy-local-h3`、`provider_call_count=2`，两个 Shot 都为 `succeeded`。使用的 sealed profile content hash 为：

```text
456b59c7a907d4b07c7d951d63ec03cbd0fb5c64638dbc8dad870aca09e2b604
```

两段 source MP4 与最终拼接文件的实测 metadata：

| Artifact | SHA-256 | Frames / Duration | Resolution | Video bitrate | Size |
| --- | --- | --- | --- | --- | --- |
| `evidence/alice-cafe-shot-1.mp4` | `81e24ffc5169734397c14bc2d632aaf18894bf623c09d724383df336594def3d` | 124 / 5.167 s | 1024x512 | 558,726 bps | 451,946 bytes |
| `evidence/alice-cafe-shot-2.mp4` | `e919769fa8a4ee35c1a5315ed48e0e2ff9607539c6310f02e319dd46a0084bb3` | 124 / 5.167 s | 1024x512 | 797,541 bps | 607,334 bytes |
| `evidence/alice-cafe-exact-terminal.mp4` | `fea79de950fb44ea146abf85ddff6b2ad325b9012bcef4148f6cc9f62dac6ff8` | 248 / 10.400 s | 1024x512 | 1,007,718 bps | 1,550,170 bytes |

三者均为 H.264 High、24 fps、`yuv420p`；run report 还记录 source/final MP4 含 AAC。最终文件路径为：

```text
runs/h3-shot-router-generalization-20260820-v2/evidence/alice-cafe-exact-terminal.mp4
```

Continuity evidence 保持成立：Shot 1 terminal PNG 与 Shot 2 `first_frame` input 的 SHA-256 均为：

```text
38cbe1e5e5a206b9aa90aae7a8144c87059efc4141d7d754fad9e2b01ccca064
```

因此人物在边界断开、错误 first-frame binding 或 Router continuity mode 不是本次“整段画面偏软/模糊”的已知根因。Exact pixel continuity 只证明边界输入一致，不证明每段生成画质达到 subjective acceptance。

## Workflow Findings

当前 sealed technical profile 由以下 artifacts 组成：

- `workflows/profiles/minimax_h3_fl2va.json`
- `workflows/templates/minimax_h3_fl2va_api.json`
- `workflows/bindings/minimax_h3_fl2va_binding.yaml`

Derived workflow 与 binding SHA-256 分别为：

```text
workflow: c736a12f35fd89f10a8db86f0769a85ca7bceb80d16feab62a1666cfd078737b
binding:  e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c
```

Workflow topology 没有发现错接：`MiniMaxH3ImageToVideo -> res_multistep/simple/20 steps -> VAEDecode/VAEDecodeAudio -> CreateVideo -> SaveVideo`，并由 binding 注入 exact prompt、first/optional-last frame、seed、width、height、frame count、steps、sampler 与 output prefix。

但它是 technical acceptance profile，不是 high-quality tuned profile。当前可验证的限制包括：

1. Run request 在 `execute.py` 中显式固定为 `1024x512`，只有约 0.52 megapixel；sealed profile capability 实际允许最高 `1344x768`、尺寸为 32 的倍数。
2. `CreateVideo` 使用 8-bit output；`SaveVideo` 当前为 `codec: "auto"`，workflow 没有显式 CRF。
3. 当前 ComfyUI `SaveVideo` schema 的 H.264 explicit re-encode path支持 `crf`，默认为 23；更低 CRF 表示更高质量和更大文件。现有 workflow 没有选择该 explicit path。
4. 两个 Provider source clips 的视频码率只有约 0.56 Mbps 和 0.80 Mbps。最终 concat 在 `execute.py` 中再以 `libx264 -preset slow -crf 18` 编码；后续较高质量重编码不能恢复 source clips 已经丢失的纹理，并会形成第二次有损编码。
5. Sealed model components采用 `int8_convrot` diffusion、`nvfp4_awq` text encoder、20 steps、无 LoRA、无 remote refiner、无 cloud fallback。这些是潜在的细节上限，但本 session 没有受控 A/B 证明它们各自的因果权重。

Reference evidence 也需要诚实区分：canonical Alice reference：

```text
runs/c2-alice-shared-20260820-001/evidence/alice-character-reference-12s.png
608x352
SHA-256: 4c67ece5d44b2bee66024d6dc7c06f4e2395fd0e4f475beb4d03071191624a02
```

Router run 实际消费：

```text
runs/h3-shot-router-generalization-20260820-v2/inputs/alice-cafe-reference.png
1456x720
SHA-256: 7d0596f2bb24318915ab0831da2dcd022d4f8c53ef0089f6c683b96ae4c5c69b
```

当前 durable run report没有保存从 608x352 到 1456x720 的 exact transformation receipt，因此不能把后者自动声称为 native high-resolution source。输入缺少真实高频细节可能加重模糊，但在 controlled A/B 前也不能把它写成唯一根因。

## Assessment

当前最准确的结论是：本地 workflow 没有节点或 continuity binding 错误，但它仍是以 technical proof 为目标的低分辨率、implicit encoding profile；本次 source clips 已实测为低码率，随后又被二次编码。Reference resolution/lineage、量化模型、固定 20 steps 与无 refiner可能进一步限制细节。

这些证据足以拒绝“Router 导致模糊”或“最终 CRF 18 已经等于高画质”的说法，但还不足以通过因果排序宣称某一个参数单独解决问题。修复必须通过同输入、同 seed 的受控 A/B，而不能只比较不同人物、不同 prompt 或不同 reference。

## Next Authorized Work Boundary

下一步应在既有 `/home/reggie/vscode_folder/AI-VIDEO-shot-router` worktree 中新增 additive Local H3 quality profile，不覆盖或修改已经验收的 `minimax_h3_fl2va` sealed technical profile与历史 hash。

首轮受控修复只改变已确认的主要变量：

1. 使用 `1344x672`，保持尺寸为 32 的倍数且在既有 capability bounds 内。
2. 依据真实 `SaveVideo` schema选择 explicit H.264 re-encode，并测试 CRF 16-18；不能只在 prompt、文件名或文档中声称高质量。
3. 避免不必要的二次有损编码；若 canonical composition仍必须重编码，分别报告 source/final codec、bitrate 与原因。
4. 保持 Shot N terminal SHA 等于 Shot N+1 first-frame input SHA，不以提高画质破坏 `exact_terminal` contract。
5. Alice 最终 quality proof 不得把简单插值放大的 608x352 输入冒充 native high-resolution reference；若输入仍是瓶颈，应通过现有 local P7 image lane生成或导入具有 exact provenance 的原生高分辨率 reference。

Verification 必须包含 workflow/profile regression tests、旧 profile hash compatibility、真实 local two-Shot output、`ffprobe`、项目本地 `video-analysis`、source/final bitrate、sampled detail/sharpness、boundary evidence 与 fresh Harness receipt。只有文件体积变大、播放器可播放或主观一句“更清晰”均不足以通过。

## Remaining Risks And Guardrails

- 当前没有 additive quality profile、修复后 MP4、same-seed A/B 或 blinded subjective review；模糊问题仍未实现性解决。
- 不得为画质修复改写 Shot Router 四档 continuity contract、Manifest/schema、Registry layout、CLI、P5 dependency ownership、`ProductionStateCommitter` 或 canonical timeline。
- 不得因为本记录提出 A/B 就自动调用 remote/paid Provider、读取 secret、启用 cloud fallback或扩大 benchmark scope。
- Local live proof、Router technical acceptance、exact terminal equality 与 subjective image quality必须继续分开报告。
- 记录生成过程没有运行测试、媒体生成、ComfyUI submit、Provider call、网络请求、push 或 release。
