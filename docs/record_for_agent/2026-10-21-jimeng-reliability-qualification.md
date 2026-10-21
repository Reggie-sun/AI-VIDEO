---
record_kind: architecture_implementation
topic_id: jimeng-provider-p0-reliability-qualification
learning_eligibility: ineligible
---

# Jimeng Reliability And Qualification Record

Date: 2026-10-21

## Scope And Current Verdict

本轮接管用户确认的 Jimeng dirty/staged 前序成果，继续加固既有 Provider。未新增付费生成、充值或购买，历史授权未复用。未更改其他任务的 dirty 文件、预算历史、Manifest/Registry authority、Director 或 Shot QA。工程候选已完成局部验证、独立审查及最终 exact snapshot Harness；源码提交 `9615517d1092bef3febb7dd44f16f651bcbeced8` 已 push `main` 并核验远端 SHA 一致，tree 与最终审查的 `8ac5f2a8944c326d4f958803f5c92b8c33619d32` 一致。

结论：**受控 Production Qualification readiness 有条件 GO；正式生产 NO-GO。** 本轮不为 Seedance 2.5 或 Mini 签发 Production qualification。可在新的明确授权、封存预算及已验证环境内进入单执行端、有限提交的受控资格实验；这不是本轮执行该实验的授权。正式生产仍缺当前 Provider 成功付费提交、后续完整交付及真实中断恢复证据。

## Confirmed Defects And Changes

- 原 Worker 只在连接时检查账号，随后独立 Fiber 扫描可能选择不同 owner。现在每个操作使用独立 JSHandle，反复核验当前 URL、唯一账号/project、canvas、commerce client 和 HTTP identity；页面刷新、身份/owner 漂移或多个相同画布页面均拒绝。
- 原 fence 到期后会恢复旧 HTTP 方法，尚未结束的原生 continuation 可以迟到发送；单独保留 prototype wrapper 仍会被替换后的 HTTP owner 绕过。现在在同步编辑器前独占页面，未结束的 promise 受关闭 fence 约束；同一 fence 还核对当前原生客户端所用页面 `fetch` 的完整 approved body，限制一次实际发送，覆盖 CDP 路由消失后的延迟 continuation。该边界依赖当前客户端使用页面 `fetch` 的源码事实，不证明未来任意客户端重写。
- 原宿主用 selector 后调用阻塞 `readline()`，半行消息可绕过 deadline；同时统一包装明确的提交前失败为 UNKNOWN。现在增量读取、检查帧及尾随消息，仅对可证明未启动原生提交且正常结束的 Worker 使用 `JimengSubmitNotDispatched`，沿既有 Paid Owner 记 `KNOWN_NO_EFFECT`。启动后、dispatch 后、异常退出和响应丢失继续 UNKNOWN，不重交或释放预算。
- 独立 Reviewer 用真实 subprocess 复现取消异常遗漏清理。`_single` 与 `submit_native` 的 `finally` 现在都终止/回收子进程并关闭管道，保留 `KeyboardInterrupt` / `SystemExit`，不静默修改持久意图或预算。
- 发送的 `quote_precondition` 现在核对 sealed benefit amount、即时原生 quote 和积分上限；ACK 还要求请求实际通过网络 fence，并匹配服务端 resource/submit/task 与生成参数 hash。报价仍不是服务端硬积分上限证明。
- 真实 Chromium 合成提交暴露了 Mock 未发现的 API 错误：Playwright 没有 `page.removeExposedFunction`。现在保存 `exposeFunction` 返回的公共 Disposable 并清理，不支持该能力的环境在原生提交前拒绝。正常清理只移除自身路由、binding 和仍属于自身的 hook，不覆盖其他逻辑替换的方法。
- Playwright 默认按 Node 模块名解析，保留显式 module path、Node binary、profile directory 和 timeout 注入；移除特定用户的默认绝对路径。保留前序 Mini 显式映射、纯图片商业 context、EOF 修复和已证实失败状态，不新增模型或平台状态枚举。

## Evidence Levels

| Evidence | Verified result | Boundary |
| --- | --- | --- |
| 真实平台只读，两个独立并发 Worker | 历史 2.5 resource `71949d15-dac1-4642-b83c-24f238650876`、submit `cedcb4bc-5bb5-4c8e-9c10-278f4f388518`、task `23681081680140` 均一致，`status=1000`；五项素材的完整 `video.gen` hash 为 `e31fc7ee6bc8f9be5985b4a7f76b86b10822e76c72a6c88e571773c3ea725bd7` | 只读重连，浏览器和登录会话始终运行 |
| 真实历史 MP4 再下载 | 29,222,147 bytes；SHA-256 `4cf66fe02005279b987f7d06fcc66f11adba7a63efc5785833adcfcf83720e5c`；H.264 1280×720/60 fps、AAC 44.1 kHz stereo、17.056009 秒 | 同一历史成片，不是新 Provider 成功生成或创作验收 |
| 真实服务端画布读回 | 历史目标 node/resource 精确匹配，draft/head 为 5/5，draft SHA-256 `1bd2b396353773caf73c3d023191b058c9b51068347006e81b48b0ddfcd05ece` | 不证明新提交的实时自动保存时序 |
| 真实 Mini 失败资源回读、标准 Reader 重开 | task `23694928965388`、`status=1001`、参数 hash `be5bcb1944462337ae71f2a9d0d7f2647e83fbbb9cad4182c199651e2157f814` 与 sealed dispatch 一致；Manifest16 仍 failed，Paid accepted | 原独立进程 UNKNOWN 恢复见 Mini 历史记录；本轮没有重交或改状态，历史实际结算仍未证明 |
| 真实 Chromium + 合成页面/runtime/wire | 一个 admission、一个 wire send、外部生成 POST=0；fetch/binding 清理及刷新后无遗留 binding；另验证账号漂移、owner 替换、旧 handle 随刷新失效、新 handle 可用、浏览器退出 | 浏览器与 Playwright 行为真实；平台业务、权限、收费及服务端均为合成，不能冒充付费提交 |
| 当前原生 HTTP 源码 | `postEnvelope` → `request` → 页面 `fetch`，没有据此扩展未知平台状态 | 源码事实/适用性推断，不是长期服务保证 |

还核对了本地已有的后续成功 Mini 资源 `cc23913c-b829-4cdc-8577-02154e945220`，task `23689514841868`。本轮真实只读查询确认 `status=1000`，模型/720p/16:9/5 秒及参数 hash 与原 Mini 请求一致，submit ID 同为 `b33f42f7-bd93-4a5b-b48c-108704aacce6`，但 resource/task 与原 sealed dispatch 不同。已有 MP4 为 9,582,069 bytes，SHA-256 `8c0fcc5319bc88bf50f1779b9dbdf6dffdbfbb11c261593690267091e3cc4e3d`，本轮核验了本地字节。其创建、提交与费用 lineage 不属于本轮已验证的正式 Provider attempt，不能仅凭相同 submit ID 和参数接管、替换原任务或结算原预留。原 Manifest16 的失败状态、原 dispatch/画布证据与预算均保留。这补充了 Mini 平台成功输出的历史证据，仍不证明当前正式 Provider 的完整成功生产链路。

## Tests And Independent Review

接管前 Jimeng 专项为 57 PASS；最终专项为 **97 PASS**，本轮新增 40 个参数化案例。覆盖完整 Worker 正常/故障路径、审批拒绝、重复 dispatch/wire、报价和参数变化、延迟发送与 HTTP 替换、半行/超时/异常退出、六种取消组合、明确 no-effect、两模型的并发与重复恢复、未知状态及完成缺失 `vid`。并发恢复只允许一次协调，重复恢复不修改 Manifest 或预算。均为离线、子进程或合成 runtime 证据，不把 Mock 恢复描述为真实平台 PASS。

独立审查仅使用一名 native `/root/final_review`，实际 profile `reviewer_xhigh`，read-only、无 nested delegation、无付费调用：

| Round | Candidate tree | Findings and closure |
| --- | --- | --- |
| 1 | `7285376a6b2c7f0f6ec4a7429ec3f7a0aea72f6f` | `JIMENG-R1` 取消未回收、`JIMENG-R2` 替换 HTTP 方法可绕过关闭 fence，Parent 均 CONFIRMED 并修复 |
| 2 | `9e93932d0ada4f4b8d1188568ccbcb4833fcb677` | 运行 22 项专项，finding set 为空 |
| 3 | `8ac5f2a8944c326d4f958803f5c92b8c33619d32` | 核对真实 Playwright Disposable 契约，运行 23 项专项，finding set 为空 |

最后一轮后源码保持冻结。Parent 的真实 Chromium 验证独立于 reviewer 静态意见；额外文档由 Parent 自审。

最终 exact staged Harness **PASS**：共 **2,740 tests passed、0 failure/error**，包含 State 962、Provider/Paid 1,081、Vidu 191、广告 54、Provider-neutral requirement 450、runtime Skill boundary 2；`seedance_local_video_tests` 由本次已通过的 covering check 覆盖而跳过。文档、规则、policy audit 和 Architecture Gate 也通过。提交前 `verify-receipt` 确认 integrity、freshness、完整 check records、coverage、scope/bytes 与 cleanup 全部成立。前序记录中的全仓 12 项基线失败不由本轮选定范围 PASS 消除；未扩成全仓回归、未改无关测试或 baseline。

## Deployment And Qualification Limits

已从审查 tree 构建 sdist、wheel 并安装到临时目录，三处 Worker 字节与源码一致，SHA-256 `aea33d1261890a87c00d78aead5effe8b36f45990083116d8a75a9f56eb1caec`。项目 venv 缺少 setuptools，隔离依赖安装不可用；随后使用本机既有 build/setuptools/wheel 完成构建，未改项目依赖。分发检查不等于独立新机器部署验证。

当前实测 Node 22.21.0、Playwright 1.64.0-alpha-1790635538000、Linux Chrome、显式私有 profile/CDP。其他版本/系统、真实登录过期恢复与即梦浏览器进程整体重启均未实测。部署必须独占该账号/project/node 的执行端：页面锁不跨浏览器实例共享，不代替 Paid permit 或 committer。

已确认的 blocker 已闭环，但不能保证未实测平台中断路径、未来网页内部变化或跨浏览器实例并发没有风险。无 dispatch 的 UNKNOWN 仍无法自动找回，保留预留并阻断；不猜测未扣费、不重置历史或重交。原生 promise 永不结束时可保留关闭 fence，需在只读核对后刷新页面再按 canonical 状态恢复。历史 `1001` 不是新提交许可或费用结算证明。

正式生产前仍需新授权下的当前 Provider 成功提交、完整状态查询/结果下载/画布保存/标准 Reader 重开，以及有界的真实响应丢失、进程中断、浏览器重启和会话过期恢复证据；必要的真实费用协调须保留原账本。Provider 技术资格与 Director/Shot 声画质量验收继续分离。

## Evidence Locations

- 工程验证最终 run：`.agent/harness/runs/jimeng-reliability-delivery-20261021/receipt.json`。旧候选因实际修复而变更 scope，保留其失败/中断/跳过状态，不冒充最终 PASS。
- 本地综合 hash/审查索引：`.codex/tmp/jimeng-reliability/evidence.json`。
- 额外成功资源的独立只读 identity：`.codex/tmp/jimeng-reliability/existing-other-resource.json`；它没有被写入原 Production attempt。
- 专项 JUnit：`.codex/tmp/jimeng-reliability/final-97.xml`；平台回读 `live-history.json`、`live-final.json`；浏览器证明 `browser-lifecycle.json`、`browser-submit.json`；分发证明 `package-proof.json` 均在同目录。
- 上述本地 receipts、源码研究缓存及历史 MP4 位于忽略目录，不随 Git 发布；本记录保留关键 identity 与 hash，支持重新验证。

Automatic learning evaluation：`no_candidate`。这是技术故障修复与既有任务的新证明层，不构成跨媒体实验质量规则；未修改 Skill/Policy/Gate、未写入全局 memory 或标记 ADOPTED，未主动重建 RAG 索引。
