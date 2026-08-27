# Qingyan Seedance Mini Handoff Live Rejection Record

Date: 2026-08-27

## Purpose

本文记录用户否决 v12 后，为缺失的“老人推荐产品并交给苗家少女”因果桥设计的一次 Seedance Mini 单 Shot 实验，以及唯一一次 remote submit 的 known-no-effect rejection。

本记录是 development experiment failure evidence，不是 Provider 成功、生成视频、Production candidate、P6、Final Acceptance 或 v12 修复完成的证据。

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

## Post-Media Gate

本次没有得到 MP4，因此没有调用 `video-analysis` MCP，所有媒体 requirements 保持 `NOT_EVALUATED`。若未来另有明确授权的新 submit 得到 exact MP4，必须先绑定其 SHA-256 并立即调用 project-local `video-analysis` MCP。以下 requirements 全部为 `PASS` 才能结束实验：

1. `IDENTITY_AND_COUNT`
2. `INITIAL_OWNERSHIP`
3. `DIALOGUE_AND_SPEAKER`
4. `HANDOFF_CAUSALITY`
5. `END_OWNERSHIP`
6. `NO_PREMATURE_TREATMENT`
7. `CAMERA_CONTINUITY`

任何 `FAIL` 或 `NOT_EVALUATED` 都立即停止；不得自动重试、生成 variant、插入 v12 或升级成 quality acceptance。

## Remaining Risks

1. 当前没有 Provider MP4，因此还无法判断双人 identity、手部交接、产品一致性、中文对白和口型是否满足要求。
2. 两次 permit 均已消费且均为 known-no-effect；第二次已确认是 remote real-person classifier rejection。任何新 submit、风格化 reference 或 Provider 变化都是新 scope，必须获得新的明确 authorization。
3. 即使未来单 Shot PASS，也只证明桥接镜头本身；首 Shot 问题建立、后续喷雾/效果因果、`11s` / `22s` 节奏与最终收口仍需独立 human review gates。
4. Seedance native audio 是否进入最终 composition 受现有 P4 contract 限制；raw MP4 有音轨不等于最终成片采用该音轨。
5. run evidence 为 local generated/untracked runtime artifact；本记录 commit 不会把它变成 Production state、remote publication 或 release truth。

## Agent Guardrails

- 不得把 offline adapter preview 或 prompt lint PASS 描述成 Seedance 生成成功。
- 不得绕过 exact Secret Service reference，或把一次 task authorization解释成无限调用额度。
- 不得在 missing/stale/unknown exact MP4 上调用或伪造 post-media PASS。
- 当前 `HTTP 400` 是 `known_no_effect`，不是 unknown outcome；但它同样不授权自动重试或 permit remint。
- local provenance 证明“虚构人物”不代表 Ark classifier 必须接受；不得伪造真人 consent、改写 classification 或重复提交相同 photorealistic bytes 绕过远端 safety gate。
- 不得自动重试或把新桥接 Shot 插入 v12；下一次 remote submit 与任何 composition change 必须保持各自 authorization 和 gate boundary。
