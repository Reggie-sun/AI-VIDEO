---
record_kind: architecture_implementation
topic_id: seedance-verbatim-canvas-source
learning_eligibility: ineligible
---

# Mecha Fast 2.0 Original Input And Media Gate

Date: 2026-10-11

## Supersession Notice — Video7 Human Acceptance

下方 Video7 notice 当时的“视听验收待确认”已由用户“可以通过下一个”取代，
视频7原片当前 human ACCEPTED；见[Video7当前记录](2026-10-11-mecha-video7-fast20-original-input.md)。
原视频6 POV测量及完整spec尚未验收的边界保持，不把两份同画布单镜当作完整保留故事链。

## Supersession Notice — 2026-10-11 Video7

用户随后明确“那不管这种也算过继续下一个视频”，已对本记录视频6的 exact MP4
作出 `ACCEPTED_WITH_KNOWN_DEVIATION`；这取代下文当时的 Agent 禁止进入下一镜结论，
仅限该蚂蚁片的已知 POV 偏差。历史 analyzer POV/source_fidelity FAIL 保留，未倒填 PASS、
未 activation，也不推导合成连续性或未来镜头的质量豁免。证据为原 run 的
`human-acceptance-with-pov-deviation.json`。

独立选择的原画布视频7已经一次 Fast2.0 / 480p 生成，新增单首帧原文 I2V 入口已实现并验证。
旧 T2V/R2V-only 能力说明及四次累计提交上限属于历史单元；新单元继承历史4次、新增1次、累计5次。
视频7视听验收仍待确认，完整 spec 仍未完成。当前证据见
[Video7 record](2026-10-11-mecha-video7-fast20-original-input.md)。

## Goal And Current Outcome

用户购买同账号资源后明确要求“再复刻用fast 2.0”，继续 480p。此次只执行《机魂觉醒》
`node_fgfrmwy9ss` 蚂蚁单元的原文与一张来源 PNG，没有 Director 扩写。
一次新物理 POST 已成功生成原片；用户完整听看后分别确认“只有音效，无配乐或对白”及
“这些动作清楚且连贯”。第一人称仍 FAIL：2s/4s 样本从外部显示主角头背和身体。
输入忠实成立不等于输出复刻成功；完整 spec、AC-7 与 Final Acceptance 尚未完成。

本次 Fast2.0 来自新的明确指令，不能解释为用户永久禁止 2.5。
旧扩写视频、旧 HTTP403 / `AccountOverdueError` 与所有历史结论保留；这次成功请求只证明该请求
未再次遭计费拒绝，不证明账号余额、抵扣顺序或套餐归因。

## Runtime Change And Ownership

离线先复现：来源可原文导入，但旧 remote prose compiler 强制不存在的表演、灯光、运镜字段，
`PROMPT_EXPRESSION_UNSUPPORTED` 且无 execution binding。必要修复已实现于
`SeedanceNativePromptBinding.source_preservation` 与同 owner 的纯 `compile_seedance_request`，
adapter 继续通过唯一 `compile_request` 调用；未新建 transport、Product state 或 recovery owner。

显式原文声明只接受 approved Shot.intent、原文 progression、prompt/source SHA 完全匹配的
非 v4 T2V/R2V 输入。拒绝增删原文、v4 替代、typed-hash continuity、不相等时长及未表达的已批准 controls。
普通新创作仍走原 rich compiler；共同的 recipe lexical coverage、reference/output/profile checks、
execution binding、Budget Guard、egress、durable intent、one-use permit 和未知结果停止规则仍运行。
不以补齐内部 enum 伪造来源摄影意图。契约见 `docs/agent-primary-contract-matrix.md`，
计划见 `docs/superpowers/plans/2026-10-11-seedance-verbatim-source-input.md`。

## Paid Execution And Exact Identity

证据根为 `runs/canvas-mecha-fast20-original-20261011-001/`，attempt 为
`canvas-cad4584de7de3544064bf3d9f76f64a2babb6445`。
现有用户指定的 exact private supplier 保持 injected lookup，不复制或输出凭据。
sealed operator 定额沿用既存配置，不查市场价格，不推算账单。

| Item | Verified evidence |
| --- | --- |
| Provider / model | Ark / `doubao-seedance-2-0-fast-260128` |
| Requested output | R2V、15s、16:9、480p、native audio true |
| Native endpoint | `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks` |
| Source prompt SHA | `8154f5471620976ac328181ef2ef2bd752dd77455d9c06e871dd613f40870e26` |
| Native body SHA | `fbb46c8b8b3f23ce7f16a54ca7e56ffc67babaa1ba8ce6b48950548093deaaf5` |
| Reference PNG SHA | `2713555c702c7269139ddbb09f446bfbbd11b3a6907a87aa892d91b09e5be617` |
| Reference role | 一张原画布场景参考；`reference_image`，不当 first frame |
| Actual MP4 SHA | `8f02e04ff10e82e2d0be6a3de79d63b80fd3865fea6bcb3f7e70fdb94e28a622` |
| Decoded output | 5680938bytes、15.104s、864×496、24fps、361frames、H264 High / AAC 32000Hz stereo |
| Calls | 本单元 POST 1、status queries 10、automatic resample 0 |
| Historical total | Beauty 1 + 旧扩写 1 + 旧计费拒绝 1 + 新原文 1 = 4；ceiling 4，remaining 0 |

原文 UTF-8 与实际 request.prompt_text 相同，adaptation/authoring diff 为空；原文输入与实际 body
分别有 seal。参考是此前实际取回的 720×408 预览所导 PNG，不冒称平台完整尺寸原图。
UI 显示的 `seedance_2.0_fast_vip` 与 API exact backend revision 未独立证明等同；
原 UI 720p/outputCount 2 与此次明确授权的 480p/单次输出亦不同，不承诺像素级重放。
预检、当前 recompile 和 fetch 证据分别在 `pre-submit-preflight.json`、
`execution-binding-current-recheck.json`、`fetch-result.json` 与 `exact-media.json`。

## Media Proof And Stop Boundary

exact raw MP4 位于上述根的 `production/state/video-generation/fetch/files/`，filename 为其完整 SHA 加 `.mp4`。
`review.html` 直接播放该原片并显示原文/原图；浏览器核对 controls、未静音、readyState 4、
实际时长/尺寸及 PNG decode，无后期拼接或静音替换。

显式 project-local `video_analyze` 已调用，`explicit-mcp-analysis.json` 保留 0/2/4/6/8/10/12/14s
样本和 probe；canonical facade 另保存 `canonical-mcp-analysis.json`、
`generation-evaluation-source.json` 与 `generation-media-diagnosis.json`。没有 ASR。

| Proof layer | Verdict and boundary |
| --- | --- |
| Input / execution binding | PASS：原文、原 PNG identity、Fast2.0 与请求输出参数一致 |
| Exact-media analyzer | POV 与 source_fidelity FAIL；close-up 存在 PASS；完整运动/声音当时 NOT_EVALUATED |
| New human audio | PASS：新片只有音效，无配乐或对白；`human-audio-confirmation.json`；未另断言精确声画同步 |
| New human motion | PASS：顺时针围瓶、碰撞后继续、穿叶绕石、带同伴离圈清楚连贯；`human-motion-confirmation.json` |
| Production / full spec | NOT_EVALUATED / 未验收；第一人称已知 FAIL，禁止采用或进入下一镜 |

两份 human 回复均绑定新 MP4 SHA 与本次 question identity，不沿用旧视频确认。
所选 canonical proof 为 analyzer；human 观察独立保存，不倒填 immutable analyzer 的 gaps。
Manifest 仍处于 `VALIDATE`、next action `validate`，未谎称 canonical failed/abandoned；已有失败 evaluation
不允许 validation/activation 推进。`post-media-stop.json` 只记录 Agent STOP 与零剩余 POST，
不冒充 committer receipt。没有 activation、composition、render 或下一 Shot submit。

## Verification And Publication

最终 scoped tests 188 passed，含九项原文入口/失败边界测试。exact staged Harness
`.agent/harness/runs/seedance-verbatim-source-20261011-final/receipt.json`：12 checks PASS，
Seedance local check 因被已通过的 production suite 完整覆盖而 SKIPPED；production suite 915 passed，
Vidu 194 passed，provider-neutral 442 passed。Architecture Gate 0 errors/0 warnings；
`make harness-receipt` 的 snapshot、freshness、artifact integrity 与 completion proof 全部成立。
snapshot index tree 为 `474d8c1f55c503b718f041d7eae3775415ea309b`。

Parent stable-candidate Risk Gate 为 `KIMI_REVIEW_NOT_REQUIRED`，exact snapshot、三个条件的
具体不触发依据和验证证据保存在 `implementation-review-risk.json`。原有 read-only Kimi 调查
`c6678be9-8a6d-44db-a093-92c037741d34` 有 qualified containment/route receipt；
机械观察三次 wire requests、零 orchestration retries，内部 retry 未知，不冒称 final implementation review。

代码 checkpoint 为 `9d6300682ac7db77e7679f22b176ada91ee58eb6`，只包含本轮六个 owned paths。
暂停的 paid-retarget code/tests/spec/plan 与旧记录未提交 hunks 不属于此验证 snapshot，也未被夹带。
本记录与直接 supersession notices 另走 documentation-only staged Harness 和 publication；
旧文档仍有保留的 paused dirty hunks，因此文档验证使用隔离 checkout 的 exact staged tree，
严格核对其 tree 与本窗口 index 一致；不把未提交 hunks 混入验证或 publication。
最终 publication SHA 以交付时实际 remote 核验为准。

## Learning Evaluation And Remaining Work

自动 `distill-ai-video-learning` 评估为 `no_candidate`：原文与旧扩写片之间 seed/输入契约等条件
未控制，不能据此认定扩写导致 POV 失败、Fast2.0 无法第一人称，或提出新模型通用规则。
多个 proof layers 仍只有一个新 attempt；现有逐镜 Gate 继续适用。未自动修改 Skill/Policy/Gate 或采用 claim。
本记录的工程与单次 live proof 不作为新的受控多臂实验。

本次已授权的单次原文验证结束；若继续修第一人称，须定义新的有界验证单元，保留原文/失败证据和
完整历史计数，不能自动扩写或重抽。记录未调用 Provider/媒体、未新增测试取证或手动刷新独立 RAG index。
experience 检索返回 stale，并按检索 owner 自动排队维护；未等待或宣称刷新完成，结论来自重开的 exact evidence。
