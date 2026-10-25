---
record_kind: recovery_incident
topic_id: jieshi-jimeng-mini-reference-upload
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Jieshi Jimeng Mini Reference Upload Stop

Date: 2026-10-26

## Root Cause Update — 2026-10-26

用户随后要求定位是否与旧 API 失败相同。当前有界上传诊断已复现本地 `upload destination invalid`：ImageX 实际返回的 `tos-lq-x.bytedancevod.com` 不匹配 `jimeng_browser.cjs` 的 `safeUpload` 域名白名单，因此在 binary POST 前被拒；其他返回的 `*.snssdk.com` 节点匹配并可上传，解释了间歇性成功/失败。此更新取代下文 checkpoint 的“根因仍未确证”，原两次 paid receipt、计数和未出片事实保持。

旧 API exact body 的 SHA 与 wire audit 一致，包含 `image_url / first_frame` 和 SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923` 的完整图片；方舟返回 HTTP400 / `InputImageSensitiveContentDetected.PrivacyInformation`。本次图片为 `93c4…7d9`、`reference / mode 4`，当前复现的故障是本地上传地址准入，不能将它归因为同一隐私审核。

新增证据为 `R/upload-diagnosis-results.json`（两次 upload 成功、一次 local host 拒绝）、`R/upload-host-format-results.json`（前七个 host 允许，第八个 delegated host 被当前规则拒绝；只执行 Apply，不发 binary/commit）和 `R/root-cause-comparison.json`。已从当前源码提取同一 regex 离线重放，确认 `snssdk.com` 为 true、上述 `bytedancevod.com` host 为 false；排除本次观察中的重复协议拼接，失败 host 的 `upload_host_has_scheme=false`。完整诊断 canonical Manifest hash 未变，新增生成请求 0。

原两次 opaque 异常没有保存被拒 host，不能逐次断言当时具体分配了哪个节点；本轮确证的是相同输入/当前实现可重复出现的上传准入缺陷。共享实现尚未修改，真实生成仍为 0，修复后端审核或 Mini 出片能力未得到验证。可复用定位归 [bug memory](../../.agent/bug-memory/jimeng-imagex-upload-host-allowlist.md)，不扩成模型质量 Learning Claim；自动 learning evaluation 仍为 `no_candidate`。

## Scope And Exact Inputs

用户要求自主复用《界蚀》旧素材，经正式 `JimengVideoProvider` 做最低成本真实图片参考测试，最后指定 720p，并允许新开页面。目标为 `seedance_2.0_mini`、`multimodal`、720p、9:16、4 秒、一个实际生成请求，内部积分上界 30；不使用 Ark API key。

Agent 已自行创建并保存独立[即梦画布](https://jimeng.jianying.com/ai-tool/ai-canvas/ba3fe23b-dee8-437c-ab89-d8a382a8998a)，节点 `node_kx6hab7jrd`。原有两个画布页面保持打开，未操作其节点。Browser 插件启动失败，Playwright MCP 又因共享 profile 已被占用而不能启动第二实例；随后使用项目既有 CDP/Playwright 连接创建新页面及节点，付费执行仍经正式 Provider、Service、committer 和一次性 permit。

证据根 `R = .codex/tmp/jieshi-jimeng-mini-20261026/`。从旧实际 `2.0/resolved-request.json` 提取 447 字原文，SHA `28934483d7c8fb62f10b0415608929d6a8df9bea5c97e7c7044fb853701547e0`；未将后来变化的同目录 `prompt.txt` 冒充旧请求。原图实际字节 SHA `93c4d6bc6d3467bc444a61ba492293ad9e98a5f8b123589cd7afb3476b0fe7d9`，2,301,611 bytes、941×1672，已实际查看。源资料与历史质量边界见[原对照记录](2026-10-21-jieshi-seedance-20-fast-comparison.md)。

新试验通过 canonical authoring/Registry/QA 和 qualification routing 创建隔离项目。图片实际编译为 `role=reference`，正文含唯一 `{{image:0}}`。Provider 文法将原人物、抬手、倒影、固定机位及广播内容结构化，并将首帧措辞适配为全能图片参考；最终 native prompt 为 2180 字符，不宣称逐字 baseline。两条封存请求的正文、参考 SHA 和规格一致。原作品的历史 Manifest、计数与媒体均未修改。

## Actual Execution And Recovery

原生只读 preflight 返回 Mini 720p/4 秒图片参考 `quote.status=available`、`credits=24`、`permission=allowed`，目标节点为空；这是报价，不是已扣费。`R/native-preflight.json`、`prompt-lint.json` 和 `sealed-media-rubric.json` 保存输入与逐项观察要求。

| Attempt | Canonical paid outcome | Actual generation POST | Result |
| --- | --- | --- | --- |
| `canvas-f45839f25a966a0e29719445f061dc139e829486` | `known_no_effect` | 0 | 图片上传阶段抛出 `Jimeng reference upload did not complete; generation was not submitted.` |
| `jieshi-mini-upload-recovered-one-actual-submit` | `known_no_effect` | 0 | 同阶段失败，没有 dispatch、resource/task 或 MP4 |

两条均从标准 `VideoGenerationService.submit_once` 进入，由 committer 保存 paid intent、budget 与终态回执。首次失败后，未改上传函数的隔离诊断成功返回已提交的 storage identity；随后独立调用当前 `JimengBrowserTransport.upload` 也成功。诊断副本只增加安全错误阶段投影，上传函数 SHA 与当前源码相同：`2481b1626ac2e77e531006bb8674ca1ea3973cf6a63520064c89f5971d9c0ae6`。这些成功不证明完整 Provider submit 路径已修复，原失败的具体异常被适配器折叠，根因仍未确证。

恢复保持旧 paid intent，canonical quota 从 1 扩为 2，实际生成请求上限仍为 1，积分上界仍为 30，未重置历史。Operator 最初登记了不适用于 qualification 的普通 runtime grant；其后将新增上传诊断通过 canonical experience owner 追加，并登记精确 paid-no-effect retarget grant。旧普通 grant 保留为未消费，typed grant 被第二 intent 消费。当前两条已知 no-effect 与两条 repair grant 全部保留；没有通过移除旧 grant、改历史、另建 scope 或新增 permit 继续执行。

## Verified State And Limits

标准 project reader 最终重开成功；`R/final-receipt.json` 保存两条 paid submit receipt、request hash、grant 消费状态和 Manifest SHA `3e9215e869f82d4c8578fb083107ee7ae6f45113cc5818fb3ecea404952d6756`。`R/final-canvas.png` 为同一画布最终读回，节点仍无资源。页面仍显示默认 VIP 编辑器设置，因为失败发生在 Provider 同步 Mini 编辑器之前；默认 UI 不是一次实际生成的参数证据。

真实生成 POST 总数为 0，未发生生成计费效果，两条账本均 `KNOWN_NO_EFFECT`。24 积分只是本次 Mini 原生报价。没有新 MP4，未调用逐 Shot 媒体 Gate，保持 `NOT_EVALUATED`；无 activation、P6、Final Acceptance 或完整作品交付。当前不能宣称 Mini 图片参考真实出片成功。

本轮未改共享实现或运行软件测试。验证为实际页面创建/保存、原图字节及编译绑定、原生报价/权限、真实上传、正式 Provider 前置失败、canonical recovery 与标准 reader 重开。文档仅做路径、数据一致性和 whitespace 检查，不冒充 Harness 或模型质量证据。

`record-ai-video-session`: record。`distill-ai-video-learning`: `no_candidate`；同一有界试验中的上传成功与 Provider 前置失败尚未隔离根因，没有新的媒体质量结论，不修改 Skill/Policy/Gate 或全局 memory。后续首先需要定位完整调用与独立上传的差异，并经 canonical owner 处理未消费普通 grant；不得直接再次 submit。
