# Jimeng Seedance Production Provider

## Scope and Owners

`JimengVideoProvider` 接入现有 `VideoGenerationService`。`ProductionStateCommitter` 独占 Manifest 状态、Paid Provider 意图、预算预留与回执；Registry 和现有视频获取、验证流程负责输入及输出资产。Provider 只映射素材、调用即梦画布原生运行时、查询任务并下载结果，不选择 Shot、不判断创作质量、不激活媒体、不决定修复或再次付费。

浏览器 transport 必须显式注入正在运行的 Chrome/CDP profile 目录，每次操作检查账号 hash 和画布 project。提交依赖内部 `generationRuntime.actions.submitVideo`，属于可能随网页版本变化的 UI 依赖，并非独立 HTTP 提交 API。profile 的 `node_id` 必须指向空闲且无既有引用来源的画布节点；如请求带入旧节点引用，提交前拒绝，避免素材关系混淆。凭据只留在网页上下文；桥接层返回技术 ID、参数和临时下载地址，后者不写 Product 状态。

## Selected Models

四个型号复用同一个 `JimengVideoProvider` 类及 `JimengBrowserTransport` / Worker，`JimengProfile.model_id` 精确选择原生 ID，不自动切换。每个 profile 封存一个输出规格；上层按 Shot 要求检查其 capability，Provider 不代选模型。旧 2.5 profile 的序列化和 identity 保持原样；各型号具有独立 capability、compiler 与 profile identity。

| Model | Native ID | Output duration | Resolutions | Production qualification |
| --- | --- | --- | --- | --- |
| Seedance 2.5 | `seedance_2.5` | 4–30 秒 | 480p / 720p / 1080p | `UNQUALIFIED` |
| Seedance 2.0 Mini | `seedance_2.0_mini` | 4–15 秒 | 720p | `UNQUALIFIED` |
| Seedance 2.0 | `seedance_2.0_vip` | 4–15 秒 | 720p / 1080p / 4k | `UNQUALIFIED` |
| Seedance 2.0 Fast | `seedance_2.0_fast_vip` | 4–15 秒 | 720p | `UNQUALIFIED` |

所有型号当前仅声明 reference-to-video / mode 4、单输出、原生音轨、整数秒及既有五种宽高比；不代表网页全部功能。2.0 / Fast / Mini 各自声明最多 12 项素材（图片 9、视频 3、音频 3），至少包含图片或视频；图片与视频各最多 50 MiB，音频 15 MiB，图片每边最多 8192，视频每边 200–2160。视频单段及总长 2–15.4 秒 / 最多 15.4 秒，音频 2–15 秒 / 总长最多 15 秒。2.5 最多 50 项（图片 30、视频 10、音频 10），支持纯音频参考；图片每边 300–8192、比例 0.4–2.5，视频每边 300–6000；视频和音频最短 1.8 秒、单段及各自总长最多 30.2 秒，音频 15 MiB。2.5 图片 40 MiB / 视频 100 MiB 继续使用已有较窄上限。Prompt 按 native JavaScript UTF-16 长度限制：2.5 为 15000，其余 4000；所有限制在上传前核验，不截断或丢弃素材。

`jimeng_models.py` 是各型号有界映射声明；2026-10-22 原生已加载 config、reference constraints 和只读 validator / commerce 查询的脱敏投影见 `tests/fixtures/generated_video/jimeng-native-models-20261022.json`。直接 `generation_specs` 读取当时不可用，实际证据来自网页初始化的 native stores；只读准入仅代表该时点账号状态，报价不代替下一次提交时的 fresh quote 或 operator bound。

`VideoCapabilityVariant.production_qualification` 为 hash-bound 静态准入声明；四型号均 `UNQUALIFIED`，正式 `VideoGenerationResolver` 返回 `BLOCKED_CAPABILITY / MODEL_UNQUALIFIED`，不会尝试其他型号。没有 profile 开关、自动晋级或新的资格生命周期。未声明该字段的既有其他 Provider 及旧 snapshot 保持兼容。技术 resolve / 只读历史恢复仍可用；测试中模拟 `QUALIFIED` 只验证原有 Paid / State 链，不赋予真实资格。本轮没有真实生成，2.0 / Fast 及四型号的正式成功出片链仍未获生产资格证明。

纯图片输入使用不含参考视频计时字段的原生 commercial action/context；只有存在视频素材才传入其时长。即使 `inputVideoDurationMs=0`，原生 owner 也会拒绝“无视频却带视频时长”的 context，不能将其等同于省略该字段。

## Exact Input and Paid Contract

`JimengProfile` 封存账号、project/node、输出规格、原生 benefit 类型与金额，以及操作人设置的积分上限。adapter 仅接受匹配的 `VideoGenerationRequest`，要求每项素材在提示词中以 `{{image:N}}`、`{{audio:N}}` 或 `{{video:N}}` 精确绑定。原生 index 按 canonical 图片、音频、视频绑定顺序排列；缺失、类型错误或越界在上传前失败。原生参数 validator 还须接受精确映射后的请求。

P0 的 `compile_request` 支持普通 Shot requirement 的显式素材绑定。带 `preserved_source_expression` 的 Shot 会明确返回 unsupported；该源文法尚未建立与即梦 index marker 一致的精确保真映射，不把原文静默改写后提交。

上传前核验 Registry 绑定素材的大小与 SHA-256。生成 POST 发出前，`JimengDispatchIntent` 已持久封存存储 ID、素材顺序与 hash、原生参数 hash、submit/resource ID；浏览器和 host 各守一道单次请求 fence。提交使用 `VideoGenerationService.submit_once` 的一次性 permit、Paid Gate 回执、预算预留和持久意图。原生 quote、action 权限及余额在启动和发送前核对上限。`CRD` 中 1 积分按 1,000,000 内部微单位表示；这是操作人封存的上限，不是市场价或已证实的服务端硬限额。代码不将 `quote_precondition` 当作硬上限证明。

每次提交后，Provider 只读轮询服务端已保存的画布草稿，要求本次节点精确绑定封存的 `resource_id`，再将完整草稿、版本和 SHA-256 按内容寻址保存为项目内 `artifacts/provider-canvas/jimeng/` 的不可变快照。accepted 的标准付费回执锚定 dispatch 和画布快照 hash；标准项目 reader 重开时还将有序素材 tuple 与原生成请求核对，缺失、替换或不一致即拒绝加载。服务端草稿保存未获确认时，付费结果保持 `OUTCOME_UNKNOWN`，只允许读回恢复，不能再次付费提交。此机制以草稿读取证明保存，不另行调用未经验证的画布写入接口。

提交响应丢失时，Paid attempt 保持 `OUTCOME_UNKNOWN`，预算保持未结算，UNKNOWN 回执锚定已落盘的 dispatch 与画布快照 hash。若进程在写提交回执前退出，标准 `ProductionStateCommitter.recover()` 或 `recover_jimeng_unknown_once` 都将遗留 `SUBMIT_INTENT` 锁定为 UNKNOWN，并封存当时已有的 Jimeng 证据；之后只查询已封存的 resource ID，核对账号/project、submit/task、素材及参数身份，并将原预算预留协调为 accepted；不重新提交或签发 permit。没有封存 resource ID、读回不可用或无法证明资源时继续保持 UNKNOWN。恢复回执嵌入带内容 hash 的读回证据。正常轮询和获取使用 accepted 的 `resource_id:task_id`；完成后从新鲜 resource 响应取下载地址，允许正常重定向，落盘时计算 hash。接受前仍须经过现有视频 artifact probe 与 QA。

## Integration

创建 `JimengProfile`，将 `JimengBrowserTransport(profile_dir=<私有配置的登录 CDP 目录>)`、Registry 精确字节 resolver 和当前项目的 `ProductionStateCommitter` 注入 `JimengVideoProvider`，在现有 Generation target 中注册选定 profile/Provider。`playwright_module` 默认通过 Node 的 `playwright` 模块解析，也可显式注入安装目录；`node_binary`、`timeout_seconds` 同样可注入，不依赖某个用户的安装路径。Playwright 的 `exposeFunction` 必须返回可 `dispose()` 的 binding；不支持该公共 API 的版本在原生提交前拒绝，不调用其他浏览器库的清理 API。本机已验证 Node 22.21.0 和 Playwright 1.64.0-alpha-1790635538000，其他版本不自动视为合格。浏览器须预先登录、开启本机 CDP，并且目标画布 URL 在所有 context 中恰有一个页面；Worker 不创建登录会话或选择重复页面。

沿用 `VideoGenerationService.start`、`submit_once`、`refresh_once`、`fetch_once` 和标准验证/验收；仅已有 Jimeng unknown attempt 可调用 `recover_jimeng_unknown_once`，不得再次调用 `submit_once`。Paid preview 使用 `billing_mode=remote_metered`、`currency=CRD`、profile 上限及 `SecretReference(kind="secret_store", reference_id="JIMENG_BROWSER_SESSION")` 作为浏览器会话元数据。账号/profile 由私有配置注入；Cookie、Token 不写入仓库、prompt、argv、日志或 receipt。

## Worker Reliability Boundary

每个操作保存独立的页面 JSHandle，并在上传、查询、同步编辑器、提交及发送前重新扫描当前 React context，核验唯一账号/project 和 owner identity；等待 host admission 后再次验证账号、owner、编辑器及原生商业准入。刷新使旧 handle 失效，必须建立新连接，只能按既有 Paid 状态决定后续动作。缺少/歧义/漂移均拒绝，不猜测新对象。

提交前先取得页面内独占 fence，再同步原生编辑器，避免其他 Worker 先改同一页面。超时或宿主失联时，未结束的原生异步动作仍受关闭的 fence 约束；只有原生 promise 结束后才恢复原方法，避免延迟 POST 穿透。同一个 fence 还保护当前原生 HTTP client 使用的页面 `fetch`，核对经过 admission 的完整 body 并限一次发送；即使 CDP 路由随 Worker 退出而消失、HTTP owner 被替换，延迟请求仍须经过该发送边界。此实现依赖当前客户端使用页面 `fetch` 的源码事实，不宣称覆盖未来任意客户端重写。正常清理仅移除自身路由与 exposed function，不覆盖已被其他逻辑替换的方法。若原生 promise 永不结束，该页面会保持阻断；保持原 attempt UNKNOWN，只读核对后再刷新页面，不重交。不同浏览器实例之间不共享页面锁，部署须独占该账号/project/node 的执行端；不能用此锁替代 Paid permit 或 committer。

`JimengSubmitNotDispatched` 仅代表可证明原生提交尚未启动（例如进程未创建、依赖/连接/编辑器 preflight 失败，且 Worker 明确返回、干净结束），由既有 Paid Owner 记录 `KNOWN_NO_EFFECT`。异常退出、无完整消息、启动后失败、dispatch 后拒绝/失联一律 UNKNOWN；不按“没看到请求”释放预算。宿主使用增量协议读取，半行、超时、重复 dispatch 与尾随消息均 fail closed；UNKNOWN 不携带重交授权。`KeyboardInterrupt` / `SystemExit` 等取消也在 `finally` 中终止并回收本次子进程及管道，保留原取消异常；已持久化的意图仍须经现有 committer 恢复，不因取消自动归零。

已证实的平台状态仅 `200`（运行中）、`1000` + `vid`（完成）、`1001`（任务失败）；未知状态和缺失 `vid` 不产生 FAILED 观察、不重置任务或预算。发送后的 ACK 要求实际通过网络 fence，且 resource/submit/task 和服务端参数 hash 精确匹配。素材上传失败停止，不跳过或替换；源字节、canonical index、storage identity、native params、dispatch、画布快照和 Paid 回执沿既有 owner 串联。

## Verification Boundary

当前可靠性候选源码为 `9615517d1092bef3febb7dd44f16f651bcbeced8`：97 项 Jimeng 专项、2,740 项 exact scoped Harness 和最终 native 独立审查通过；真实 Chromium 的合成提交流程验证了发送及清理，真实平台验证仅使用历史资源只读回读。结论为“可在新授权及已验证环境内开展受控资格实验”，正式生产仍 NO-GO。后续历史 Mini 成功资源与原失败 attempt 的 resource/task 不同，不能仅凭相同 submit ID 接管。完整证据分级、receipt、部署限制与剩余条件见 [reliability qualification record](record_for_agent/2026-10-21-jimeng-reliability-qualification.md)；下文保留前序验证的历史边界。

2026-10-21 的 Mini 验证使用独立画布，不继续往历史作品画布添加试验。原生报价 30 积分，实际生成请求最多一次。正式 Provider 已提交 Mini / 720p / 16:9 / 5 秒图片参考任务；服务端返回 `status=1001`、`error_code=20010` 和“生成失败，本次不消耗积分”。这不是成功出片证明，未取得新 MP4，失败原因不能从错误码自行推断。任务身份、画布保存、账本恢复与最终验证边界见 [Mini validation record](record_for_agent/2026-10-21-jimeng-mini-provider-validation.md)。

此前 P0 工程化的只读复查已通过本 transport 找回 2026-10-21 的三模态历史任务，resource、submit、task 身份、完成状态和新鲜下载地址均匹配；服务端保存的生成参数与原请求逐字段一致。用本 Provider 的下载路径再次取得同一历史 MP4，29,222,147 字节及 SHA-256 与先前保留的原片一致。服务端历史画布草稿只读获取成功，目标节点精确包含历史 `resource_id`；该阶段未通过新提交验证实时自动保存时序。离线测试覆盖参数映射、身份漂移、一次性 permit、响应丢失、读回不可用、画布快照缺失及替换、进程重开及遗留提交意图、预算协调、轮询和获取。构建验证确认浏览器 worker 存在于 sdist、wheel 及安装目标。该历史阶段未新增付费生成，也未实测浏览器整体重启、登录过期恢复或真实提交响应丢失。网页内部对象、quote 结构、上传签名与节点行为可能变化；完整 Production qualification 和最终成片验收需要相应真实证据，不能由离线测试推出。
