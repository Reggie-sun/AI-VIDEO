# Qingyan Seedance Mini Illustrated Handoff Experiment Record

Date: 2026-08-27

## Purpose

本文记录用户否决 v12 后，为缺失的“老人推荐产品并交给苗家少女”因果桥设计的 Seedance Mini 单 Shot 实验：两次 remote safety rejection，以及用户选择 `B` 后使用 clearly illustrated reference 获得的一个 exact MP4 和逐 requirement Gate 结果。

本记录包含一次 Provider fetch 成功，但仍只是 development experiment evidence，不是 Production candidate、P6、Final Acceptance 或 v12 修复完成的证据。

## Human Verdict And Problem Boundary

用户正常观看后确认 v12 仍不合理：老人推荐之后，没有一个可见的产品交接使少女取得喷雾，后续直接喷用仍然依赖观众脑补。用户也指出首 Shot 的问题声画建立、`11s` 后运镜、`22s` 切镜与转场、最后静图和重复广告语都属于应由独立 gates 约束的问题。

本次只隔离一个最大变量：

```text
推荐 -> 递出 -> 双手短暂共同接触 -> 少女接住 -> 老人松手
```

本 Shot 禁止开盖、喷洒和效果表现；成功后才允许把它放在后续“喷用”镜头之前。它不宣称同时修复首 Shot 或成片其他节奏问题。

旧记录 `docs/record_for_agent/2026-08-27-qingyan-v12-causal-recut-and-single-close.md` 已增加 supersession notice：其技术测量仍为历史事实，但当前 human verdict 为 `NEEDS_REVISION`。

## Routing And Decision

project Agent Experience Memory 使用真实 CLI 检索：

```text
python -m scripts.agent_memory --scope experience search \
  "qingyan elder recommendation product handoff Seedance Mini continuity experiment" \
  --top-k 8 --json
```

返回的当前相关 evidence 指向：

- `runs/t8-h3-seedance-3shot-continuity-20260822-v8/SUMMARY.md`
- `docs/record_for_agent/2026-08-22-t8-h3-seedance-mixed-shot-continuity-handoff.md`

历史结果表明 Seedance Mini I2V 只有首帧/尾帧锚点，且曾出现用户否决的身份漂移；Mini R2V 支持多个 image references，更适合同时绑定两位虚构角色与产品。因此本次选择：

- model: `doubao-seedance-2-0-mini-260615`
- mode: `REFERENCE_TO_VIDEO`
- three image references
- `5s`, `720x1280`, `9:16`, `24fps`
- `native_audio=true`
- exactly one submit ceiling; no retry, fallback, variant, auto-compose or activation

对白只保留一句自然建议“姑娘，试试这个，清爽些。”，不重复品牌或广告口号。完整 Shot contract 与 provider prompt 分别位于：

- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/shot-contract.md`
- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/prompt.txt`

## Sealed Inputs

preflight 绑定三张 project-owned development references：

| Role | Path | SHA-256 | Geometry |
| --- | --- | --- | --- |
| 白衣角色 | `runs/qingyan-seedance-mini-elder-handoff-20260827-001/references/01-white-blouse-woman.png` | `1eaa31af848b7895d76a28df29d4fe5e1d5e1497f4bc03375ea3c14e79d6b672` | `700x1200` |
| 深蓝服饰角色 | `runs/qingyan-seedance-mini-elder-handoff-20260827-001/references/02-navy-dress-woman-v3.png` | `6cadb70398e477da7927852714036076541307508f1c2bbe406f9978a1fa1b41` | `360x900` |
| 带盖黄色产品 | `runs/qingyan-seedance-mini-elder-handoff-20260827-001/references/03-qingyan-product.png` | `795d52d94a98470696b3a80d21367a2894f80ab8aad0bb7cc0f8cb9d4cdaa418` | `480x1200` |

exact source paths、source hashes、crop times、usage boundary 与 product rights status 记录在：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-001/source-evidence.json
```

两位人物均来自本项目既有本地生成媒体，声明为虚构人物 reference；没有 real/protected identity claim。产品 source packshot 的 rights status 来自 v12 ecommerce input 的 `CONFIRMED`，不是本次 preflight 自行推断。

## Offline Verification And Paid Preview

执行：

```text
PYTHONPATH=src python \
  runs/qingyan-seedance-mini-elder-handoff-20260827-001/preflight.py
```

连接真实 desktop session bus 后的最终输出：

```json
{"credential_present":true,"estimated_cost_upper_bound_cny":2.484,"mode":"reference_to_video","model_id":"doubao-seedance-2-0-mini-260615","prompt_lint":"PASS","reference_count":3,"status":"ready_for_paid_gates","submit_posts":0}
```

verified evidence：

- prompt lint: `PASS`, `177` words，prompt SHA-256 `0ba40e45dc6434cde079c63fca24ba61f0ea207a65537a6b55e7208707839ec9`
- adapter resolve / preview: local `NoNetworkTransport` 下通过
- estimated tokens upper bound: `108000`
- current unit price snapshot: `23 CNY / million tokens`
- estimated cost upper bound: `2.484 CNY`
- finite task ceiling: `3.0 CNY`
- `submit_posts=0`, `poll_queries=0`, `fetches=0`, `activations=0`
- durable submit intent: not created
- one-use permit: not minted
- cloud egress: not performed
- cost incurred by this task: `0 CNY`

machine-readable evidence：

- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/evidence/preflight-report.json`
- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/evidence/paid-preview.json`
- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/evidence/resolved-request.json`
- `runs/qingyan-seedance-mini-elder-handoff-20260827-001/evidence/prompt-lint.txt`

## Credential Recovery And Live Attempt

规定的 Secret Service lookup：

```text
application ai-video
provider seedance
credential ARK_API_KEY
```

历史脱敏记录确认此前使用过 `Secret Service injected ARK_API_KEY supplier`。最初的 lookup exit `1` 不是 item absent evidence；当时 Codex shell 未继承 `DBUS_SESSION_BUS_ADDRESS` 与 `XDG_RUNTIME_DIR`，实际没有连接 desktop Secret Service。连接当前用户 `/run/user/1000/bus` 后：

- `org.freedesktop.secrets` 由 `gnome-keyring-daemon` 提供；
- exact lookup 与 exact search 均成功；
- 没有读取 repo、shell history、raw rollout、MiniMax credential 或替代 secret source；
- credential value 没有写入 stdout、log、record 或 artifact。

重新通过 offline preflight 后，runtime 创建 exact paid preview、`3 CNY` ceiling、durable submit intent 与 one-use permit，并于 `2026-08-27T13:12:40Z` 执行唯一一次 POST。sealed request：

- request fingerprint: `a5e7fe755d725f17e34ec03fa78e30b228585c0f0ac7520e8f47ac75b1ef8ae5`
- preview fingerprint: `965d20fba91f7d8b565c37125ed5dd6df82634ee3ad31be1c7c6a526bdfa091d`
- body SHA-256: `899012c53fe1bec87c46733963afb1d6c77ec55f4b4f60849668321040280c9c`
- exact refs: three sealed PNGs listed above
- `720p`, `9:16`, `5s`, `generate_audio=true`

Ark 明确返回 `HTTP 400`。canonical runtime 将其落为：

```text
attempt status: failed
error_code: paid_provider_known_no_effect
paid_provider phase: known_no_effect
external_effect_id: null
actual_cost_microunits: 0
submit_posts: 1
```

submit receipt：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-001/production/state/paid-provider/submits/cfa6e83ecb4d1df3d155ed139ba88637daade942bc338c9574b54e15c675a2cc.json
```

budget reservation 已释放，费用为 `0 CNY`。没有 task ID、poll、fetch、MP4、activation、retry、permit remint 或 Provider fallback。当前 driver 没有持久化 Ark 400 response body，因此不能从现有 evidence 精确判断是 multi-reference、native audio、output geometry、prompt 还是其他 request constraint；不得猜测 root cause 后自动改参重提。

fresh 官方 `CreateContentsGenerationsTasks` 文档列出了多 image `reference_image` 输入示例，并说明 Seedance 2.0 支持 `generate_audio`；但它没有证明本账号、exact Mini model 与本次全部参数组合一定接受，也无法替代丢失的 400 structured response body。因此当前只可排除“通用 API 完全不支持 reference images / audio”这一过宽解释，不能进一步判定 exact rejection cause。文档：`https://api.volcengine.com/api-docs/view?action=CreateContentsGenerationsTasks&serviceCode=ark&version=2024-01-01`。

## Second Authorized Diagnostic And Exact Cause

用户随后明确授权新的生成。为最大化成功概率并隔离 first attempt 的多个变量，第二次请求回到历史已成功的 Mini R2V 形态：

- 新 run: `runs/qingyan-seedance-mini-elder-handoff-20260827-002/`
- one reference image: 同一画面内包含两位虚构角色、房间和产品
- `480p`, `9:16`, `5s`, `generate_audio=false`
- prompt lint: `PASS`, `155` words
- estimated cost upper bound: `1.155060 CNY`
- exactly one new submit; no retry or fallback

本次 transport 在不保存 credential、raw image bytes 或完整 response 的前提下，持久化了 Ark structured error：

```text
HTTP 400
code: InputImageSensitiveContentDetected.PrivacyInformation
type: BadRequest
message summary: input image content[1] may contain real person
```

evidence：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-002/evidence/provider-error.json
```

这证明 exact failure 是远端 Provider safety classifier 将本项目本地生成视频提取的虚构人物参考图判定为“可能包含真人”。它不证明素材实际包含真人，也不推翻 local source provenance；但 local `synthetic_photorealistic_person` attestation 不能覆盖 Ark remote rejection。

第二次 canonical outcome 同样为 `paid_provider_known_no_effect`：`external_effect_id=null`、实际费用 `0 CNY`、无 task ID、poll、fetch、MP4、activation、retry、permit remint 或 fallback。该 permit 已消费。不得继续提交相同或其他 photorealistic character bytes 试探 classifier。

## Third Authorized Illustrated Experiment

用户选择 route `B`：不伪造真人 consent，也不继续试探 photorealistic classifier，而是先把同一双人交接首帧改为明显的手绘二维插画，再进行一次 Seedance Mini 视觉动作实验。

使用 built-in `image_gen` 以 run 002 的双人构图和 run 001 的黄色产品 crop 为输入，生成并人工检查了 clearly illustrated reference：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-003/references/01-illustrated-elder-holds-product.png
SHA-256: b211bb0cc2c46b9f2296a2fb647cba1f4d737068fef9d9d598769630f94b5152
geometry: 950x1655
```

reference 中恰好两位虚构插画角色；开头只有深蓝服饰老人持有唯一一瓶带盖黄色产品，白衣少女双手空着。machine-readable provenance 位于：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-003/source-evidence.json
```

第三次 request 保持单变量、单提交边界：

- model: `doubao-seedance-2-0-mini-260615`
- mode: `REFERENCE_TO_VIDEO`
- one clearly illustrated reference
- `480p`, `9:16`, `5s`, `generate_audio=false`
- prompt lint: `PASS`, `161` words
- estimated cost upper bound: `1.155060 CNY`；task ceiling: `3 CNY`
- exactly one POST；无 retry、fallback、variant、permit remint 或 activation

Provider 接受任务并在第 `9` 次状态查询后成功返回，runtime 只执行一次 download。exact output：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-003/output/seedance-mini-handoff.mp4
SHA-256: 3b143e6311006d3540d78d2b5b286df246cc8f83b78b5f8ce5c671a0a944824a
size: 1881828 bytes
probe: 5.042s, 496x864, 24fps, H.264 High, 121 frames, no audio stream
```

`1.155060 CNY` 是预提交上界，不是 Provider invoice 或已确认实际扣费。live counters 与 sanitized request evidence 位于：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-003/evidence/live-report.json
```

## Post-Media Gate

exact MP4 落盘后已立即调用 project-local `video-analysis` MCP；`video_analyze` 和 `video_review` 均绑定上述 absolute path，使用 `0.5s` sampling、最多 `12` 帧、scene threshold `0.4`。MCP 报告：单一 scene、无 cut、无音轨；随后基于 exact bytes 生成 contact sheet 进行逐帧人工检查。

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| `IDENTITY_AND_COUNT` | `PASS` | 始终只有同一两位插画角色，服饰、发型与银饰可接受。 |
| `INITIAL_OWNERSHIP` | `PASS` | 开头只有深蓝服饰老人持瓶，白衣少女双手空着。 |
| `DIALOGUE_AND_SPEAKER` | `FAIL` | 原 Shot Contract 要求老人只说一次推荐语；exact MP4 没有音轨，视觉口型与手势不能替代对白。 |
| `HANDOFF_CAUSALITY` | `PASS` | 推荐姿态、递出、共同接触、少女接住、老人松手的顺序清楚。 |
| `END_OWNERSHIP` | `PASS` | 结尾只有白衣少女在胸前持有带盖产品。 |
| `NO_PREMATURE_TREATMENT` | `PASS` | 没有开盖、喷洒、湿润或效果展示。 |
| `CAMERA_CONTINUITY` | `PASS` | 单一稳定 medium two-shot，无推拉摇移、切镜或转场。 |

overall Gate 为 `FAIL`。视觉因果桥本身成立，但不能把无音轨结果描述成完整通过；而且本实验为绕开 remote classifier 故意采用插画风，`STYLE_COMPATIBILITY` 对直接插入 photorealistic v12 同样为 `FAIL`。完整 evidence：

```text
runs/qingyan-seedance-mini-elder-handoff-20260827-003/evidence/post-media-gate.md
runs/qingyan-seedance-mini-elder-handoff-20260827-003/evidence/handoff-contact-sheet.png
```

因此当前停止：没有自动重试、下一次 Provider submit、composition change、v12 插入、Production activation、P6 或 Final Acceptance。

## 2026-08-28 Runtime Path Retirement

用户明确要求后续不再遇到同类Ark“可能包含真人”远端拒绝。current code evidence显示，原`SeedanceSyntheticImageReferenceReceipt`允许`synthetic_photorealistic_person`在project-owned provenance与human attestation成立后进入inline PNG egress；这只能证明本地来源，不代表Ark像素分类器会接受，因此与本次live evidence冲突。

本轮退役该execution path，同时保持历史receipt读取兼容：

- `src/ai_video/production/seedance_asset.py`新增统一photorealistic person-like egress denial。
- `SeedanceSyntheticImageAuthorizer`在返回Ark egress authorization前拒绝该classification。
- `SeedanceSyntheticImageReferenceResolver.validate_submit()`在POST body、credential lookup和one-use permit消费前再次拒绝。
- 返回typed `PAID_PROVIDER_EGRESS_NOT_AUTHORIZED`；不调用Ark，不自动动漫化，也不fallback到其他Provider。
- `clearly_illustrated_anime_non_real_character`与`ordinary_non_character_image`保持原行为。

回归测试证明I2V与R2V的valid project-owned photorealistic fictional provenance都会在本地停止，`transport.requests == []`、credential supplier未调用且permit仍有效未消费；clearly illustrated与ordinary non-character两种允许分类均有authorizer、I2V和R2V正向覆盖。focused Seedance为`117 passed`，完整Seedance/Paid Provider/recovery组合为`527 passed`，Architecture Gate为`PASS`。`reviewer_xhigh`初审的测试计数与ordinary正向coverage concerns均已修复，同tier scoped re-review verdict为`accept`。本轮没有新的Provider submit、credential读取、媒体生成、activation或费用。

该Gate保证known inline synthetic photorealistic path不再把person-like bytes送到Ark classifier；它不声称能控制Ark服务端分类器，也不把本地BLOCKED解释成生成成功。若未来仍需要写实虚构人物视频，必须显式选择并验证另一条Provider/local-model路线，禁止silent fallback。

## Remaining Risks

1. 已有 Provider MP4 证明插画风下的双人交接动作可成立，但无音轨使原 `DIALOGUE_AND_SPEAKER` contract 明确失败。
2. 插画风与 photorealistic v12 不兼容；这条视频只能作为动作与镜头语言 evidence，不能直接拼入成片。
3. 前两次 permit 均为 known-no-effect；第三次 permit 已消费并返回 MP4。Ark inline写实合成人物现会在本地BLOCKED；任何替代Provider、local model、音频版本或写实风恢复都是新scope，必须获得新的明确authorization。
4. 即使未来桥接 Shot 全部 PASS，也只证明桥接镜头本身；首 Shot 问题建立、后续喷雾/效果因果、`11s` / `22s` 节奏与最终收口仍需独立 human review gates。
5. run evidence 为 local generated/untracked runtime artifact；本记录 commit 不会把它变成 Production state、remote publication 或 release truth。

## Agent Guardrails

- 不得把 offline adapter preview 或 prompt lint PASS 描述成 Seedance 生成成功。
- 不得绕过 exact Secret Service reference，或把一次 task authorization解释成无限调用额度。
- 不得在 missing/stale/unknown exact MP4 上调用或伪造 post-media PASS。
- 当前 `HTTP 400` 是 `known_no_effect`，不是 unknown outcome；但它同样不授权自动重试或 permit remint。
- local provenance 证明“虚构人物”不代表 Ark classifier 必须接受；不得伪造真人 consent、改写 classification 或重复提交相同 photorealistic bytes 绕过远端 safety gate。
- 不得自动重试或把新桥接 Shot 插入 v12；下一次 remote submit 与任何 composition change 必须保持各自 authorization 和 gate boundary。
