# Alice C2 Cloud Provider Comparison Record

Date: 2026-08-20

## Purpose

本文记录 Alice 咖啡厅 C2 hard-cut representative input、MiniMax Hailuo 2.3 canonical live proof，以及 Seedance 2.0 Mini 在 remote submit 前遇到的 Ark private AIGC asset gate。目标是让后续 Agent 能准确区分：

- shared continuity prerequisite 与各 Provider 的独立 execution identity；
- Hailuo technical live acceptance 与尚未完成的 two-Provider subjective comparison；
- Seedance model access、private asset write access 与一次真实 video submit；
- Ark direct API、ComfyUI/BytePlus proxy 和第三方 aggregator 的不同 Provider surface。

本记录不授权新的 Provider 调用、素材上传、企业认证、第三方 fallback、Shot Router implementation、push 或 release。Canonical runtime truth 仍以 `docs/v0.2-runtime-baseline.md`、active specs/plans、source、tests 与 exact run evidence 为准。

## Shared Alice C2 Input

Representative prerequisite 位于 `runs/c2-alice-shared-20260820-001/`。Alice 与咖啡厅 anchors 为：清晰正脸、稳定发型、黑色外套、红色围巾；明亮日间咖啡厅、玻璃门、靠窗木桌、绿色椅子和右侧暖色吊灯。

Shared activated assets：

- Shot 1 terminal PNG SHA-256：`52596511bbea4314e39f0065559f6c01665303c4139a6c28326a8ee90b57e19b`。
- Shot 2 hard-cut keyframe asset ID：`image-5f2c1dfd702bf5079b87519ae443a73b2b8f62ec80a2bd72dac7c6e24fccb0b5`。
- Shot 2 hard-cut keyframe PNG SHA-256：`5072a65b0e13a7fae2b809d3dc0afb24dc6980c75b0ce9342559b60801c158fc`。
- Keyframe measurements：PNG、608x352、266569 bytes。
- Terminal 与 keyframe bytes 不同；它们表达 deliberate independent medium-framing hard cut，而不是 C1 direct terminal-frame reuse。

Hailuo 与 Seedance lane 必须消费上述同一个 activated hard-cut keyframe。不得为另一个 Provider 另造 keyframe，也不得用公共虚拟人像替换 Alice 后仍声称是同输入比较。

## Hailuo 2.3 Canonical Live Truth

Canonical run 位于 `runs/c2-hailuo23-adaptive-live-20260820-001/`，使用：

- provider：`minimax_hailuo`；
- model：`MiniMax-Hailuo-2.3`；
- profile：`minimax-hailuo-default` / `hailuo-2.3-v1`；
- capability：`minimax-hailuo-2.3-v1-i2v-768p-6s-first_frame`；
- provider task ID：`432581080539416`。

Exact input lineage 已证明 `first_frame_consumed_sha256` 等于 shared hard-cut keyframe SHA-256 `5072a65b0e13a7fae2b809d3dc0afb24dc6980c75b0ce9342559b60801c158fc`。

Bounded external effects：

- submit POST：1；
- poll：8；
- fetch：1；
- canonical activation：1；
- exact replay 新增 submit/fetch/activation：`0/0/0`；
- local recovery network calls：0。

Fetched live artifact：

```text
runs/c2-hailuo23-adaptive-live-20260820-001/output/alice-c2-hailuo23-adaptive-live.mp4
```

Measured facts：

- SHA-256：`90b4fc1842b4a74332ebcae7e20c1e0cc1cdd7166037702e4dd1b37d2ed0bdca`；
- size：588737 bytes；
- H.264 MP4，1326x768，24 fps，141 frames，5.875 seconds；
- Provider native audio：false；实际只有 video stream；
- 7 个定点抽帧 hashes 全部不同；
- black/near-black segments：0；
- frozen segments over 0.5 seconds：0；
- first frame 与 resized shared keyframe SSIM：`0.941854`；
- project-local `video-analysis`：single scene、6 frames extracted、no audio。

Candidate 已完成 canonical activation、project reopen、explicit recovery 与 P5 precise closure。Changed contribution nodes 只有：

- `asset:video-alice-c2-hailuo23-adaptive-live`；
- `asset:video-alice-c2-hailuo23-adaptive-live:terminal-frame`；
- `creative:shot:shot-2:visual`。

人工 review verdict 为 `pass_with_minor_concerns`。Scene identity、camera direction、motion direction、lighting/color、spatial relationships 与拉椅坐下并抬眼的 action completion 均通过；唯一 concern 是轻微 facial variation。

`MiniMax-Hailuo-2.3` live output 证明该 I2V `768P` lane 对 accepted first-frame aspect 使用 adaptive `1326x768` geometry，不是历史假设的固定 `1366x768 / 16:9`。相关 implementation/docs checkpoints 包括 `6547c17` 与 `7e7bde7`。

## Seedance 2.0 Mini Pre-Submit Truth

Target lane 保持：

- provider：`seedance` / `volcengine_ark_seedance`；
- model：`doubao-seedance-2-0-mini-260615`；
- capability：`seedance-2-0-mini-260615-image_to_video`；
- profile：`seedance-2-0-mini-260615-i2v-first-frame-v1`；
- credential reference：Secret Service injected `ARK_API_KEY` supplier。

Preflight 已完成 exact capability resolution、`generate_audio=false` request sealing 与 numeric preview：

- dated list-price basis：23 CNY / million tokens；
- conservative token upper bound：108000；
- estimated upper bound：2.484 CNY；
- sealed budget ceiling：3 CNY。

Chrome MCP 将 exact Alice keyframe 上传到 Ark experience surface，但该操作只产生 temporary experience object，没有生成 `Active asset-...` identity、asset group 或可验证 confirmation evidence。Sanitized gate evidence 位于：

- `runs/c2-seedance2mini-live-20260820-002/evidence/pre-submit-blocker.json`；
- `runs/c2-seedance2mini-live-20260820-002/evidence/ark-asset-quota.json`；
- `runs/c2-seedance2mini-live-20260820-002/evidence/ark-asset-manager.png`。

Exact Ark quota observation：

- `aigc_readable=true`；
- `aigc_writable=false`；
- `liveness_readable=true`；
- `liveness_writable=true`；
- private AIGC assets/groups used：0。

这表示当前账号可以读取公共 AIGC assets，并具有真人授权 surface，但不能把 fictional Alice 写成 private AIGC asset。真人活体/肖像授权不能用于虚构 Alice；企业主体认证也不能由 Agent 代填、伪造或自动提交。

Paid Provider Gate 在 Cloud Egress 后、durable submit intent 前 fail closed：

- durable submit intent：未创建；
- one-use permit：未签发；
- submit/poll/fetch/activation：`0/0/0/0`；
- outcome：`not_submitted`，不是 `outcome_unknown`；
- retry：0；
- automatic fallback：未使用；
- persisted secret material：false。

`597fcc5` 增加的 `SeedanceAssetMaterializationReceipt` 与 `SeedanceAssetReferenceResolver` 只导入已经由 Ark Console materialize 且人工观察为 `Active` 的 provider identity，并绑定 exact local ID/SHA-256/MIME/size 与 confirmation evidence SHA-256。它不是 uploader，不猜测 Assets API，也不允许 local Registry ID 冒充 `asset://`。

## Community And Proxy Route Assessment

社区中“个人上传图片即可生成”的常见路径不能直接外推为 Ark direct API capability：

1. ComfyUI official Partner Node 先把 local image 上传到 Comfy Cloud，再调用 `/proxy/seedance/virtual-library/assets`，等待 `Active` 后返回 `asset://...`。该 surface 使用 Comfy/BytePlus proxy 和 `dreamina-seedance-*` identity，不是本项目的 `ARK_API_KEY + doubao-seedance-2-0-mini-260615` lane。
2. Pika、CoreSync、KIE 等 aggregator 接受 public HTTPS 或提供自己的 media upload，但 Provider、credential、billing、asset owner 与 receipt 都属于第三方。
3. 即梦或 Ark experience UI 的手工上传可以完成交互式创作，但 temporary upload 或 UI result 不能自动成为本项目 durable Ark Provider receipt。

因此，Comfy proxy、第三方 aggregator、公共虚拟人像或真人授权素材都不能作为当前 exact Alice Ark lane 的 silent fallback。若未来选择这些路线，必须作为新的 Provider/model/credential/egress scope 单独批准和实现；不得只替换 `input_reference` 或复用当前 Provider receipt。

## Verification And Repository State

Relevant implementation checkpoint：`597fcc516eeb4234a8a8889a6a34ce0b453df1ee` (`fix: bind Seedance inputs to sealed Ark assets`)。Native named `reviewer` verdict 为 `accept`，blocking issues 与 non-blocking concerns 均为 none。

Current-HEAD code/control-plane verification receipt：

```text
.agent/harness/runs/20260819T204958227393Z/receipt.json
```

该 receipt 对 `c9a03d0..b2a3921` exact range 为 `passed`，包含 `scope_diff_check`、`harness_tests`、`production_contract_tests`、`cli_config_tests`、`task_architecture_gate`、`production_video_provider_tests` 与 `full_tests`。其运行结果包括 production `2124 passed, 3 skipped, 164 deselected`、provider `818 passed`、full suite `2287 passed, 4 skipped`。

记录创建前，repository 为 local `main`，HEAD `b2a3921`，相对 `origin/main` ahead 13，working tree/index clean。上述 changes 和 runtime evidence 均未 push 或 release。

## Assessment

Technical acceptance 必须分开报告：

- C2 hard-cut contract 与 shared Alice terminal/keyframe：accepted technical prerequisite；
- Hailuo 2.3 adaptive lane：canonical technical live accepted，subjective review `pass_with_minor_concerns`；
- Seedance 2.0 Mini adapter/import owner：offline accepted；
- Seedance Alice lane：blocked pre-submit，no live MP4；
- Hailuo vs Seedance comparison：not evaluable；
- overall two-Provider subjective gate：blocked；
- Shot Router：仍 blocked，不得因为 Hailuo success 或 Seedance offline tests 宣称 gate 已通过。

此前 `runs/seedance-mini-5s-live-20260819-r4/` 的 diagnostic MP4 只证明一次 Seedance cloud connectivity。它省略 tracked `generate_audio=false`、产生 AAC，并未完成当前 Alice first-frame lineage、billing settlement或candidate activation，不能替代本次 blocked lane。

## Remaining Risks Or Next Work

1. 若保持 exact Ark direct lane，必须先取得当前账号对 fictional/private AIGC asset 的合法 write entitlement，并 materialize 同一个 Alice keyframe 为真实 `Active asset-...`；随后创建 sealed materialization receipt，重新执行 pricing/budget/egress/intent/one-use permit，再进行最多一次 submit。
2. 任何 account entitlement 变化都必须重新读取 live quota；历史 console screenshot 不证明当前仍 writable。
3. 若改走 Comfy/BytePlus 或 aggregator，必须先明确这是 Provider scope expansion，并独立处理 credential、pricing、egress、durable identity、one-submit limit 与 activation/recovery；不得冒充 Ark live proof。
4. Seedance 成功前不能完成 shared-keyframe-vs-Seedance initial-frame review，也不能完成 Hailuo-vs-Seedance subjective comparison。
5. Router implementation、Local H3 C2 Shot 2、third candidate、blind retry、push 与 release 均不在当前 accepted result 中。

## Agent Guardrails

后续 Agent 必须保持以下区分：

- `Seedance model access works` 不等于 `private AIGC asset write is enabled`。
- `temporary experience upload exists` 不等于 `Active asset-... exists`。
- `aigc_readable=true` 不等于 `aigc_writable=true`。
- `ComfyUI can upload an image` 不等于 `Ark direct API can use the same credential/provider receipt`。
- `one historical Seedance MP4 exists` 不等于 `tracked Alice continuity payload live accepted`。
- `Hailuo technical pass` 不等于 `two-Provider comparison accepted` 或 `Shot Router gate passed`。
- 未取得真实 Seedance fetched/validated/activated MP4 前，不得向用户交付 fake、preflight、temporary upload 或失败 artifact 作为 Seedance output。
