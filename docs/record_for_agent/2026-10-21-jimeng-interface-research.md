---
record_kind: research_note
topic_id: jimeng-current-canvas-interface-research
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Jimeng Interface Research, Direct Generation And Task Recovery

Date: 2026-10-21

## Assessment

当前登录账号下，已经通过直接 HTTP 请求完成图片、音频、视频各一次存储上传，并在两个独立客户端进程重连后读回同一已有结果，下载的 MP4 与历史 source provenance 的 SHA-256 一致。账号会话由原项目浏览器 profile 持有，操作没有依赖视觉点击，也没有导出登录 Cookie。

**最新进展：三模态新生成已经完成并下载，运行中任务也通过独立客户端重连及页面刷新找回。** 本轮唯一生成实际扣除 442 积分，服务端已同步结算；新 MP4 完整解码通过。project-local `video-analysis` 已显式执行，但对白、声线、完整动作与运镜连续性缺少足够验收证据，媒体 Gate 为 `NOT_EVALUATED`。下方 765 积分 / 884 报价与提交前阻断保留为初次检查历史，不再代表最新账号状态。提交无响应的恢复、浏览器整体重启、登录失效和长期稳定性仍未验证。

没有安装或启动三个第三方服务，也没有接入新的 Production Provider、写入 Manifest / Registry、激活 Production 素材或签署 Shot QA。上传只到存储层，未调用 `resource/upload` 登记新上传对象；本轮通过原生生成 owner 更新了该画布节点的输出资源，仍为 296 nodes / 162 edges。新上传的三个对象保留，不以自动清理删除证据。

## Authorized Live Trial — 2026-10-21

用户在已知 884 积分报价、已确认最多一次 exact 试验后要求“现在有积分了你继续”；Parent 将这次知情续行限定为原模型、参数和输入、最多一次、884 积分上限，没有把整笔余额当预算。最新同账号状态为 `vipLevel=ultra`，可用积分 96825；原生 quote 返回 `credits=442, originalCredits=884, discountLabel=积分5折`，action 为 `allowed`。前述基础会员快照不能代表升级后的折扣。

提交仍为 Seedance 2.5 / `multi_modal` / 720p / 16:9 / 17000 ms / 单输出，材料类型顺序 `2,2,2,4,3`，`meta_list` 引用顺序 `1,2,3,0,4`。图片、声线、视频用途与预览 v2 完全一致，原提示词只保留既有视频参考用途适配。当前原生参数 validator 为 `valid`。

实际通过正常 React canvas context 的 `generationRuntime.actions.submitVideo` 调用原生 creation authority → commercial execute → generator owner，没有视觉点击，没有绕过其权限判断或导出登录凭据。该入口是当前 UI 内部方法，不是稳定公开 SDK，也不证明无浏览器会话的独立客户端生成可用。native owner 分配新的 submit/resource identity；本地 probe 在放行网络前 fsync 保存 exact request、任务 identity 和单次消费记录。预览中先前占位的 ID 没有用于另一次提交。

一次性研究 probe 不是 Production adapter 或 Production permit，不写 Product 状态。它对 exact 提示词/材料/绑定、账号、442 报价、884 上限和单次请求做限制，并在正常 HTTP 方法外增加只收紧权限的页面内检查；保留原生 HTTP 的请求策略、凭据、project scope 与商业流程。请求附加源码允许的 `quote_precondition={expected_benefit_amount:34,expected_credits_amount:442}`，服务端接受了该 body，但这不是已证明的服务端硬上限保证。

独立审查采用一名 native `reviewer_xhigh`，共两轮。第一轮确认延迟操作可能在调用端退出后继续提交，以及响应未绑定 exact Request 的问题；修正为页面内单次检查必须等本地持久化放行，断连不能取得新的放行，退出前关闭检查，响应绑定 admitted Request / resource ID。第二轮审查 exact probe SHA-256 `730581edeedeecf7ed296c7cdac287049f156b897a6304a57286f3b949c2d72e` 无剩余 finding。12 项离线边界检查、Node syntax 与真实原生只读 preflight 通过；没有运行完整工程 Harness。

唯一 POST 时间为 `2026-10-21T09:41:43Z`，HTTP 200 / `ret=0`，结果 `state=1,error_code=0`。服务器任务身份：

| Identity | Value |
| --- | --- |
| submit_id | `cedcb4bc-5bb5-4c8e-9c10-278f4f388518` |
| resource_id | `71949d15-dac1-4642-b83c-24f238650876` |
| task_id | `23681081680140` |
| canonical request SHA-256 | `64ec20d6e0fd9131dafc66f50a99d853a9f4c867bfdf8ef163276fd68344d447` |

独立进程通过资源接口读回新任务 `status=200`（生成中），队列返回 `stage=3`、无前序排队。实际服务端资源的提示词 hash、五个 materials 与四个既有 `reference_sources` 均匹配请求，`meta_list` 类型/index 顺序一致；本地脱敏记录省略 type-1 条目的明文，不能称整份参数逐字节一致。保存后刷新画布，再以持久 ID 查询，仍为同一任务；没有额外生成或购买尝试。刷新触发的原生余额响应为 `vip_credit=55325,gift_credit=41058,purchase_credit=0`，合计 96383，比提交前减少 442。

`2026-10-21T09:51:21Z` 首次读到 `status=1000`，距唯一 POST 约 9 分 38 秒；最终资源为 `vid=v02870g10004dbc8lta7dld3p49ej2i0`，并返回 `consumption_synced=true, consumed_credits=442`。随后直接 GET 新返回的媒体地址并落盘，29222147 bytes，SHA-256 `4cf66fe02005279b987f7d06fcc66f11adba7a63efc5785833adcfcf83720e5c`。没有重用旧 MP4 冒充本次输出。

本地文件为 [`.codex/tmp/jimeng-single-trial/resume/generated.mp4`](../../.codex/tmp/jimeng-single-trial/resume/generated.mp4)，H.264、1280×720、409 帧，容器/音轨时长 17.056009 秒，AAC stereo / 44100 Hz。完整解码 exit 0，音轨 mean/max 为 -26.5/-5.2 dB；这只证明可解码且非全静音，不证明对白正确或听感。FFprobe `r_frame_rate=60/1`、`avg_frame_rate=24540/1021`，与资源声明 24 fps 有显示口径差异，因此不把 MCP 的 60 fps 摘要当作恒定帧率证明。

project-local `video_probe` / `video_analyze` 对 exact MP4 执行成功，提取 0–16 秒九帧，场景阈值检测返回一个 scene。抽帧可见场景、COCO/Nosha、掉落宠物、推车/果物和结尾宠物，但不足以核验全速连续动作及完整摄影机路径。`audio_understand(execute=false)` 仅产生离线预览，network calls 为 0；没有为修补证据追加远程付费分析。因此媒体 Gate 为 `NOT_EVALUATED`，没有签署 Shot QA、人工观看/听觉验收或提交下一镜。

下载最初被研究脚本的静态域名白名单拦住，核对为 fresh 资源响应返回的第一方 CDN 后完成下载。用户随后明确要求去掉下载检查；本地只读下载 probe 已移除域名/端口、大小和 MP4 magic 准入限制，并允许跟随 CDN redirect。仍从 exact 已完成资源取地址、检查 HTTP 结果、避免覆盖已有文件，并在下载后做 hash/解码验证；没有把该局部调整改成 Product/Provider policy，也没有为此再次下载或提交生成。

本机证据目录为 `.codex/tmp/jimeng-single-trial/resume/`，含单次 intent / exact request / admission / network dispatch / acceptance、查询、页面刷新、费用回读、下载、媒体检查和审查历史。最终回执为 [`receipt.json`](../../.codex/tmp/jimeng-single-trial/resume/receipt.json)；媒体 Gate 明细为 [`media-gate.json`](../../.codex/tmp/jimeng-single-trial/resume/media-gate.json)。历史 admission 的 `ADMITTED_OUTCOME_UNKNOWN` 保持不改，由 acceptance / terminal 回读确定最新结果；单次额度已消费，不因质量未验收或等待异常重交。

## Single Trial Preflight — 2026-10-21

本节为首次余额不足时的历史 checkpoint；其未提交/未准入结论已由上方唯一真实试验补证，保留原检查范围与当时数值。

用户确认了此前预览的最多一次试验：同一 `视频 10 (17)` 的 Seedance 2.5、720p、17 秒、单输出，保留三张图片与 COCO 声线，加入已经上传的同镜视频作为运镜参考。这次确认没有给出数值积分上限。新增视频材料在 `materials[4]`，使用上传后的 `vid=v02870g10004dbbu7dfog65m808fqmv0`；原四个材料的 index 和引用绑定保持。该视频仍是存储对象，没有画布 node/resource 映射；其服务端准入未验证。

实际下载并查看了三张 exact 参考图片：图片 0 为宠物店场景，图片 1 为 COCO 多视图设定，图片 2 为 Nosha 多视图设定。参数预览 v2 只追加视频用途说明：参考连续摄影机路径与动作节奏，人物和场景身份仍由图片约束，声线由音频约束，不从视频取对白或字幕。原叙事、动作因果与镜头文本均保留；原文本写 15 秒而已有控件/请求为 17 秒的差异显式记录，没有静默改写。预览 SHA-256 为 `05ff5ed428d22a594dde561f8409d343875f3d06309591692d206238a0831d43`，性质仍是 `LOCAL_PARAMETER_PREVIEW_NOT_A_PERMIT`，`execute_allowed=false`。

同一账号的原生余额请求成功返回 `vip_credit=725`、`gift_credit=40`、`purchase_credit=0`，合计 **765 积分**。只读调用当前客户端原生 commerce `quoteActions` 对上述 exact 选项核算，结果为 **884 积分**；随后 `getActionState` 返回 `status=blocked, reason=credit_insufficient, isFree=false`。会员 entitlement 为 `access=available`，没有免除本次费用。差额为 **119 积分**。这些是当前账号的客户端核算和准入状态，不是已扣费回执或官方市场价格。

核算输入与公开客户端的 action builder 一致：输出 17 秒，输入视频实际 17.056009 秒经 `Math.round(ms/1000)` 取 17 秒，`hasInputVideo=true`、`chargeInputVideoDuration=true`，`benefitAmount=34`。34 是该核算的用量参数，不能当作积分；884 来自原生 quote 返回，没有用历史扣分或自行估价代替。

该 quote 是从正常 React context 中取得已有 commerce client 的只读方法，依赖当前 UI 内部结构，不能视为稳定公开 SDK 或独立费用接口；未调用权限拒绝的 observability diagnostics，也未执行 commerce action、引导充值、领取或购买。独立 browser fetch 请求余额接口即使带原生公开 query 参数仍返回业务 `ret=1014`，因此也未证明 standalone 余额读取可用。可选 `commerce_selection.quote_precondition` 的源码字段不证明服务端承诺积分硬上限，不能充作 Budget Guard。

本次 continuation 新上传 0、生成 POST 0、购买/充值 0、Production mutation 0；没有消费 permit，没有提交后 outcome，也没有 `UNKNOWN` 重试。原画布仍为 296 nodes / 162 edges。素材 index、枚举、配置时长和原文保留的局部检查通过，服务端素材准入、三模态生成、运行中轮询、断线恢复及新 MP4 的逐 Shot Gate 均为 `NOT_EVALUATED`。

本机 continuation receipt：[`.codex/tmp/jimeng-single-trial/receipt.json`](../../.codex/tmp/jimeng-single-trial/receipt.json)，绑定 `native-account-read.json`、`native-quote.json`、`action-entitlement.json`、`preflight.json`、预览和实际参考图片的 hash。它独立于下方初次研究 receipt，保留两个 checkpoint 的历史。

## Promotion Scope And VIP Label — 2026-10-21

本节为账号升级前的优惠范围核对；最新 `ultra` 账号的本 action 原生五折报价与实际 442 积分结算见上方真实试验。

用户随后指出 Seedance 2.5 活动横幅，并询问 2.0 的 VIP 标签。重新读取同一账号的原生 metadata、benefit strategy 与 fresh quote 后，**884 仅适用于本次当前画布 action，不能概括所有即梦入口的优惠情况**。之前向用户说明余额不足时缺少这个范围限定。

| Native benefit triple (`resource_type=aigc`) | Current unit credits / original | Read-only quote for amount 34 |
| --- | --- | --- |
| `generate_video` / `seedance_25_720p_output`，本次 `video.generate` action 的实际解析结果 | 26 / 26 | 884 |
| `dreamina_video_novel_video_generate_seedance2_5` / `dreamina_video_novel_video_generate_seedance2_5_720p_with_ref`，另一个视频生成计费项 | 12 / 26 | 408 |

两个单价均来自账号原生成功响应的 `credit_pricing_info`；`quoteBatch` 对两个 exact benefit triple 的只读核算分别返回上述积分。第二行证明另一个计费项存在优惠，不证明原 `/octo_api/v1/node_generate` 请求能选择该项或按 408 结算，也未定位它的实际生成提交入口。没有替换 `commerce_selection`、修改策略、切换生成入口、追加提交或购买。第一行在 reload 后仍由 `computeStrategyBenefit({scene,sceneOptions})` 解析，原生 action state 仍为 `credit_insufficient`。源码的报价函数会使用 exact strategy 的现价字段，不能用另一 resource 的现价覆盖本 action。

官方[活动页](https://jimeng.jianying.com/tools/jimeng-seedance-price)明确将横幅的 ¥0.19/秒“低至”条件写为超级会员连续包年，并另列活动对象和适用套餐；未将该人民币宣传价折算为本账号积分。官方[会员权益表](https://jimeng.jianying.com/)将 `Seedance 2.0 VIP专属通道` 列为基础会员包含的权益，VIP 标签表示会员通道资格，本身不证明积分免费。当前 `generation_specs` 另有 `seedance_2.0_vip` / `dreamina_seedance_40_pro_vision` 与 `seedance_2.0_fast_vip` / `dreamina_seedance_40_vision`。一次独立的 2.0 VIP 五秒只读示例 action 在当前 commerce wrapper 返回 `unsupported`，因此没有以该示例宣称具体 2.0 报价或成功准入，也没有把这次已确认的 2.5 试验换成 2.0。

本次补核生成 POST / 上传 / 充值 / 购买均为 0；本机回执为 [`.codex/tmp/jimeng-discount-check/receipt.json`](../../.codex/tmp/jimeng-discount-check/receipt.json)。本 checkpoint 仍为研究记录，自动 learning 结果 `no_candidate`，不改变 Skill、Policy、Gate 或 Production 状态。

## Pinned Sources

用户最终指定的三个项目如下；更早讨论中的其他即梦 MCP 不属于本次比较结论。以下是源码事实，不能单独证明账号可用。

| Source | Exact revision | Findings |
| --- | --- | --- |
| [Algovate/jimeng-cli](https://github.com/Algovate/jimeng-cli/tree/fdff6f8e21f88acd83a3213a18cf6e4663c1f8d2) | `fdff6f8e21f88acd83a3213a18cf6e4663c1f8d2` | GPL-3.0；Omni 的图片、视频上传与引用、任务查询/等待工具已有实现；本快照没有音频引用和 Seedance 2.5 路径。 |
| [zhizinan1997/jimeng-free-api-all](https://github.com/zhizinan1997/jimeng-free-api-all/tree/176e6f7280ccbb2508b8dc0427d11108127153a6) | `176e6f7280ccbb2508b8dc0427d11108127153a6` | GPL-3.0；检查到的视频入口将上传图片映射为首尾帧，没有视频/音频引用 schema；同步返回 URL，不提供持久任务恢复链。 |
| [hedashuaiii/jimeng-api](https://github.com/hedashuaiii/jimeng-api/tree/e82acff7848a96a2e4d0f13ce8ed518f8e6f506f) | `e82acff7848a96a2e4d0f13ce8ed518f8e6f506f` | GPL-3.0；三类素材上传、`material_list` / `meta_list`、异步任务持久化及重启后继续轮询均有源码；仍存在下述凭据、持久化和引用完整性问题。 |
| Local REA | `d13c9f840d36a321a56917e75c48afcb8d72920e`，读取时 clean | `rea@6.4.0` 已有构建产物；本轮实际运行了 target discovery 与 passive page observation。 |

关键代码定位：

- `jimeng-cli`：[references / request builder](https://github.com/Algovate/jimeng-cli/blob/fdff6f8e21f88acd83a3213a18cf6e4663c1f8d2/src/api/services/videos.ts#L640)、[task lookup](https://github.com/Algovate/jimeng-cli/blob/fdff6f8e21f88acd83a3213a18cf6e4663c1f8d2/src/api/services/tasks.ts#L104)、[transport retry](https://github.com/Algovate/jimeng-cli/blob/fdff6f8e21f88acd83a3213a18cf6e4663c1f8d2/src/api/services/core.ts#L536)。
- `jimeng-free-api-all`：[video request and polling](https://github.com/zhizinan1997/jimeng-free-api-all/blob/176e6f7280ccbb2508b8dc0427d11108127153a6/src/api/controllers/videos.ts#L511)、[automatic generation fallback](https://github.com/zhizinan1997/jimeng-free-api-all/blob/176e6f7280ccbb2508b8dc0427d11108127153a6/src/api/controllers/videos.ts#L700)。
- `jimeng-api`：[three material types](https://github.com/hedashuaiii/jimeng-api/blob/e82acff7848a96a2e4d0f13ce8ed518f8e6f506f/src/api/controllers/videos.ts#L1749)、[index binding](https://github.com/hedashuaiii/jimeng-api/blob/e82acff7848a96a2e4d0f13ce8ed518f8e6f506f/src/api/controllers/videos.ts#L2749)、[async persistence and startup recovery](https://github.com/hedashuaiii/jimeng-api/blob/e82acff7848a96a2e4d0f13ce8ed518f8e6f506f/src/api/controllers/videos.ts#L3010)。

## Current Request Surfaces

第三方仓库主要生成入口是 `POST /mweb/v1/aigc_draft/generate`，以 `history_record_id` 查询 `POST /mweb/v1/get_history_by_ids`。当前画布客户端使用另一组 generation/resource API，不能直接套用旧入口的 ID 和状态值。

| Operation | Current request | Evidence |
| --- | --- | --- |
| Account projects | `POST /octo_api/v1/project/list`，body `{}` | 实际返回 14 个已有项目；匹配目标画布。 |
| Upload ticket | `POST /mweb/v1/get_upload_token`，image `scene=2`，video/audio `scene=1` | 当前公开客户端与真实请求一致；只记录字段名及非秘密配置。 |
| Image storage upload | ImageX `ApplyImageUpload` → binary POST → `CommitImageUpload` | 三个阶段实际成功；最终 `UriStatus=2000`。 |
| Video/audio storage upload | VOD `ApplyUploadInner` → binary POST → `CommitUploadInner` | 两类素材均完成三阶段并取得 `Vid`。 |
| Canvas generation | `POST /octo_api/v1/node_generate` | exact 三模态试验唯一 POST 接受并完成；使用正常原生 owner，没有视觉点击。 |
| Read output/reference resources | `POST /octo_api/v1/resource/batch_get`，body `{project_id, resource_ids}` | 实际返回素材参数、`resource_id` / `submit_id` / `task_id`、状态和媒体地址。 |
| Queue lookup | `POST /octo_api/v1/resource/generation/queue_status`，body `{project_id, resource_ids}` | 旧完成资源与新任务完成后 `results=[]`；新任务生成中实际返回 `stage=3`，不是等待队列阶段的证明。 |
| Download | 对本次资源响应提供的媒体地址直接 GET | HTTP 200，落盘并核对 SHA-256；不持久化签名 URL。 |

公开客户端 `canvas-core.15e0f05e55.js` 的 module `73375` 构造 initial video body：`project_id`、`op=1`、`initial.{node_id,submit_id,items}`，每 item 包含 `resource_id`、`type=2`、`params.video_params` 以及适用的 `reference_sources`。`3717.4cfa44b033.js` module `85481` 负责 `nodeGenerate`；它支持 initial / retry / post-edit / detached，并检查返回资源的顺序及结果状态。这个方法会执行 POST，没有观察到可安全调用的 validate-only 模式。

`3717` module `99697` 拥有上述资源和队列读接口。module `94491` 的 `director_stage/motion_generation` 是另一套 Director motion task API，不能拿来替代普通节点生成的恢复。

当前公开 bundle 的 SHA-256：

| File | SHA-256 |
| --- | --- |
| `main.5336b4dea7.js` | `3c7b005eff4ef524d43bdc5f60f89b0aa56064e3d97eb358b3da7131746b2f56` |
| `canvas-data.3d75fe0568.js` | `f586fc0ef4b6a891e56f96d14804f6748d08dee6c20097ca83b30861c087375b` |
| `3717.4cfa44b033.js` | `eba27064379def21e00c7eb9d4c5ff81d600ee3cbfed465c55c633bad4470c27` |

这些文件取自当前页面实际引用的官方静态资源目录；下载和分析没有携带账号凭据。

## Complex Shot Reference Readback

本次选用已有画布《零号档案》2资产+重置片段，`project_id=f0ed223b-090e-4ed6-b394-283f8b7dbd07`，节点 `node_bq6wajb5xe` / `视频 10 (17)`。当前 draft 与存储资源均显示 `seedance_2.5`、全能参考、16:9、720p、17 秒。资源回读中的 `duration_ms=17000`；实际 MP4 时长是 17.056009 秒。

| Index | Reference | Wire fields | Verified binding |
| --- | --- | --- | --- |
| 0 | 图片 1 | `materials[0].type=2, image_uri` | `reference_sources[0]` 指向 `node_fy65r3arvg` 及其 exact resource。 |
| 1 | 图片 2 | `materials[1].type=2, image_uri` | 指向 `node_dnbfsjd7f9`；`meta_list` 使用 `material_idx=1`。 |
| 2 | 图片 3 | `materials[2].type=2, image_uri` | 指向 `node_yhk7aqyx8a`；`meta_list` 使用 `material_idx=2`。 |
| 3 | COCO 声线 | `materials[3].type=4, vid` | 指向 `node_9npw9qk4np`，服务器音频时长 `6.504` 秒；`meta_list` 使用 `material_idx=3`。 |

当前资源的 `meta_list` 中引用出现顺序为 `1,2,3,0`，与素材数组顺序不同；必须按 index 关联，不能按提示词出现顺序重新编号。资源类型枚举和 material 类型枚举也不同：resource 的 image/video/audio 为 `1/2/3`，此处 material 的 image/video/audio 为 `2/3/4`。

初次扫描本画布 66 个视频资源时没有发现 `materials.type=3`；没有将原有 Shot 伪称为三模态。后续唯一试验已回读三张图片、音频和视频材料，完成生成并下载新 MP4。这证明三模态参数被接受并保存，不证明每类参考都按导演意图影响结果。

此外实际读取 `GET /octo_api/v1/generation_specs`：本账号返回 `seedance_2.5`、`model_req_key=dreamina_seedance_45_pro`，`multi_modal` 支持 image/video/audio，数量上限分别 30/10/10，总量上限 50，视频/音频总时长各 30200 ms。返回的分辨率枚举包含 480p/720p/1080p，普通生成时长范围 4000–30000 ms。它说明当前 schema 宣告的边界，不替代实际素材准入、同次生成或费用核验；不能把旧仓库的 2.0/15 秒约束套到当前 2.5 上。

## Live Upload And Download Evidence

所有测试复用本账号已有资源服务的 bytes；source 标记为 canvas-served bytes，不冒充上传前原文件。STS、上传 Authorization、登录凭据始终留在浏览器内部的单次函数作用域，记录仅保留类型、状态、内容 hash 和非秘密对象 identity。没有把账号 session 交给第三方仓库代码。

| Kind | Source bytes | Source SHA-256 | Committed identity |
| --- | ---: | --- | --- |
| image | 2583232 | `66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62` | `tos-cn-i-tb4s082cfz/615844960f274e6b8dcbaf901e574d3f` |
| audio | 208173 | `32b3e405b704bff738882fe433c9cb2aa984f08b991109541668170b5db15c7a` | `v03870g10004dbbu7afog65h2qgmhlu0` |
| video | 33841254 | `0ed3948ce0d4c4c2049c447c9d9ee7548ace40f28bf0bc0258f24a2e00a0cab3` | `v02870g10004dbbu7dfog65m808fqmv0` |

图片第一轮在 Apply 响应之后、binary POST 之前停止，未取得足够诊断以确认具体原因。保留该回执后增加非秘密结构诊断，再进行一次有界尝试才完成上传；没有宣称修复了已定位的根因，也没有抹去历史。实际图片 Apply 2 次、binary 1 次、commit 1 次；音频和视频各 Apply/binary/commit 1 次。没有生成 retry，也没有 unknown outcome 后重新上传。

已有结果通过 `resource_id=91935bbb-590d-49b5-956c-f4aa14264425` 找回，读回 `task_id=21136179920140`、`submit_id=08a54b08-ac36-46a2-b909-d525436d3533`、`status=1000` 和原 `vid`。两个独立 Node 客户端仅凭保存的 resource identity 发起查询，返回身份均相同；查询没有依赖节点当前选中状态。浏览器进程和登录会话在这两次查询间保持运行，因此这不是浏览器重启或登录过期恢复测试。

下载文件为 `.codex/tmp/jimeng-existing-task-recovered.mp4`，33841254 bytes，H.264、1280×720、AAC stereo / 44100 Hz。SHA-256 与 `runs/coco-nosha-vidu-voice-recovery-20260930-001/source-provenance.json` 的历史源视频一致。FFprobe 与 project-local `video_probe` 均能打开；两者时长显示存在毫秒级舍入差异，未作视觉/听觉质量或逐 Shot acceptance 判定。

对照请求也实际执行：旧 `get_history_by_ids` 使用上述当前 `task_id` 时返回 HTTP 200 / `ret=0` 但 `data={}`；旧 `get_asset_list` 的视频查询也返回空列表。这些返回不证明历史结果不存在，本次已经由新资源接口找回同一结果。不能将 `task_id`、`history_record_id`、asset ID、resource ID、item ID 混用，也不能把 HTTP 200 当作已找回任务。

## Reuse And Recovery Decision

三个仓库适合作为协议研究参考，当前没有一个可直接认定为本项目的稳定接入：

- `jimeng-cli` 的显式查询/等待工具有复用价值，但保留 ID 主要依赖调用方；`list_tasks` 的视频/ID 映射仍需验证，缺少音频及当前画布协议。
- `jimeng-free-api-all` 的通用 transport 可重试 POST，视频层还可能降低规格重新提交；本项目不能继承这种 unknown 后重交或静默降级行为。
- `jimeng-api` 对自身 async route 的任务可落盘并在 `historyId` 已保存时恢复轮询；源码却把 refresh token 明文放入 `tmp/async-tasks`，写入失败只记日志，且得到远端 ID 到可靠保存之间存在崩溃窗口。这个实现不能原样用于本项目。部分素材上传失败后跳过并压缩 material 数组，还会使原 `@N` 指向错误素材。

如实施后续接入，应沿项目现有 Generation / paid / state owner，在发出唯一提交前持久封存账号范围、project/node/resource/submit identity、素材 bytes/hash 与 index 映射，并核实平台是否提供幂等和可查找的 durable receipt。提交后断线时先按已知资源身份读队列和资源；空查询不等于已证明未提交。缺少可归因结果时保留 `UNKNOWN`，不因复用 submit ID 或源码有 retry 就再次生成。签名下载地址应从 fresh 资源读响应重新取得，不作为持久任务标识。

本轮没有实现 Production adapter 或证明服务端幂等。已有完成结果恢复、当前登录会话中已接受新任务的客户端重连 / 页面刷新恢复、三模态新结果生成到下载闭环为本次有界 `PASS`。上传/查询/下载使用直接 HTTP；生成通过网页原生内部 owner 发出真实请求，因此“无需视觉点击”已验证，“完全脱离浏览器会话的独立 HTTP 生成客户端”仍未验证。无响应提交恢复、浏览器整体重启、登录失效和长期稳定性仍为 `NOT_EVALUATED`。

## Verification And Evidence

本机总 receipt： [`.codex/tmp/jimeng-interface-research-receipt.json`](../../.codex/tmp/jimeng-interface-research-receipt.json)。它绑定 source revisions、公开 bundle、probe scripts 和各本地回执的 SHA-256。媒体和本机回执位于 ignored 目录，不随 Git 发布。

REA 实际捕获 `resource/batch_get` 的请求/响应字段结构，Evidence ID 为 `ev_ddd646a5a2635861a4b296a45a8a3c718a4598b1198ac7d052cd6e3f88de80d2`。保留文件是删除 URL query values 的 derivative，明确标记不能当作原始 Evidence 的字节等同副本；原始 stdout hash 单独保存。其 coverage 是 `policy_filtered` / attach-limited，没有 prior network；没有将其他 Chrome/Playwright 输出称为 REA Evidence。

局部文档契约、owned-path whitespace 和 receipt artifact hash 验证按实际执行结果记入相应 receipt；本次没有运行完整工程 Harness。初始 docs/recovery checkpoint 没有 Product behavior 改动，Parent 判定 `NATIVE_REVIEW_NOT_REQUIRED`。后续单次付费 probe 存在调用端退出后仍可能提交的具体风险，判定 `NATIVE_REVIEW_REQUIRED` 并完成上述两轮独立审查。下载限制的后续移除和事实记录由 Parent 验证；不能称为 reviewer 审过的新内容。

使用 `record-ai-video-session` 保存本 checkpoint；`distill-ai-video-learning` 自动评估为 `no_candidate`。这是协议/单会话研究及一次真实三模态生成；同一次任务的多次轮询、刷新和检查不算多个独立实验，也没有足够已验收媒体支持新规则。没有修改 Skill、Policy 或 Gate。初次 Agent Memory 检索返回 incompatible shard / exit 3；continuation 的 experience 检索返回标记为 stale 的 last-good 片段并提示后台 refresh。均按 retrieval owner 使用当前源码与运行证据，没有前台重建或重试索引，也没有用检索片段作为授权。

## Paid Continuation Boundary

初次提交前阻断已被上方知情续行和 fresh 442 积分报价取代。最多一次 exact 试验已接受并完成，剩余新增提交数为 0；只查询、下载同一 task/resource 并检查 exact 媒体，不因超时、失败或质量问题自动重交。一次试验授权不包含本 Agent 充值、购买、缩短时长、删参考、换模型或自动改用另一权益。

提交后保留同一任务 identity，验证排队、断开客户端、重连、下载及 exact 媒体 Gate；unknown 停止，不重交。原生 quote 和这份研究报告均不构成付费 permit，已完成旧结果的恢复证据也不构成新生成或长期稳定性证明。
