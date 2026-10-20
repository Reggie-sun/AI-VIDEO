---
record_kind: research_note
topic_id: jimeng-current-canvas-interface-research
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Jimeng Interface Research And Existing Result Recovery

Date: 2026-10-21

## Assessment

当前登录账号下，已经通过直接 HTTP 请求完成图片、音频、视频各一次存储上传，并在两个独立客户端进程重连后读回同一已有结果，下载的 MP4 与历史 source provenance 的 SHA-256 一致。账号会话由原项目浏览器 profile 持有，操作没有依赖视觉点击，也没有导出登录 Cookie。

**这证明当前会话中的三类上传和已完成结果找回可行；尚未证明新生成闭环、三模态同次生成、运行中断线恢复、提交结果未知时的恢复或长期稳定性。** 新生成、充值、购买均为 0。用户随后确认一次三模态试验；当前在提交前因余额不足及尚缺数值积分上限而停止，详见下节。

没有安装或启动三个第三方服务，也没有接入新的 Production Provider、写入 Manifest / Registry、激活素材或签署 Shot QA。上传只到存储层，未调用 `resource/upload` 将新对象登记到画布，原画布仍为 296 nodes / 162 edges。新上传的三个对象保留，不以自动清理删除证据。

## Single Trial Preflight — 2026-10-21

用户确认了此前预览的最多一次试验：同一 `视频 10 (17)` 的 Seedance 2.5、720p、17 秒、单输出，保留三张图片与 COCO 声线，加入已经上传的同镜视频作为运镜参考。这次确认没有给出数值积分上限。新增视频材料在 `materials[4]`，使用上传后的 `vid=v02870g10004dbbu7dfog65m808fqmv0`；原四个材料的 index 和引用绑定保持。该视频仍是存储对象，没有画布 node/resource 映射；其服务端准入未验证。

实际下载并查看了三张 exact 参考图片：图片 0 为宠物店场景，图片 1 为 COCO 多视图设定，图片 2 为 Nosha 多视图设定。参数预览 v2 只追加视频用途说明：参考连续摄影机路径与动作节奏，人物和场景身份仍由图片约束，声线由音频约束，不从视频取对白或字幕。原叙事、动作因果与镜头文本均保留；原文本写 15 秒而已有控件/请求为 17 秒的差异显式记录，没有静默改写。预览 SHA-256 为 `05ff5ed428d22a594dde561f8409d343875f3d06309591692d206238a0831d43`，性质仍是 `LOCAL_PARAMETER_PREVIEW_NOT_A_PERMIT`，`execute_allowed=false`。

同一账号的原生余额请求成功返回 `vip_credit=725`、`gift_credit=40`、`purchase_credit=0`，合计 **765 积分**。只读调用当前客户端原生 commerce `quoteActions` 对上述 exact 选项核算，结果为 **884 积分**；随后 `getActionState` 返回 `status=blocked, reason=credit_insufficient, isFree=false`。会员 entitlement 为 `access=available`，没有免除本次费用。差额为 **119 积分**。这些是当前账号的客户端核算和准入状态，不是已扣费回执或官方市场价格。

核算输入与公开客户端的 action builder 一致：输出 17 秒，输入视频实际 17.056009 秒经 `Math.round(ms/1000)` 取 17 秒，`hasInputVideo=true`、`chargeInputVideoDuration=true`，`benefitAmount=34`。34 是该核算的用量参数，不能当作积分；884 来自原生 quote 返回，没有用历史扣分或自行估价代替。

该 quote 是从正常 React context 中取得已有 commerce client 的只读方法，依赖当前 UI 内部结构，不能视为稳定公开 SDK 或独立费用接口；未调用权限拒绝的 observability diagnostics，也未执行 commerce action、引导充值、领取或购买。独立 browser fetch 请求余额接口即使带原生公开 query 参数仍返回业务 `ret=1014`，因此也未证明 standalone 余额读取可用。可选 `commerce_selection.quote_precondition` 的源码字段不证明服务端承诺积分硬上限，不能充作 Budget Guard。

本次 continuation 新上传 0、生成 POST 0、购买/充值 0、Production mutation 0；没有消费 permit，没有提交后 outcome，也没有 `UNKNOWN` 重试。原画布仍为 296 nodes / 162 edges。素材 index、枚举、配置时长和原文保留的局部检查通过，服务端素材准入、三模态生成、运行中轮询、断线恢复及新 MP4 的逐 Shot Gate 均为 `NOT_EVALUATED`。

本机 continuation receipt：[`.codex/tmp/jimeng-single-trial/receipt.json`](../../.codex/tmp/jimeng-single-trial/receipt.json)，绑定 `native-account-read.json`、`native-quote.json`、`action-entitlement.json`、`preflight.json`、预览和实际参考图片的 hash。它独立于下方初次研究 receipt，保留两个 checkpoint 的历史。

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
| Canvas generation | `POST /octo_api/v1/node_generate` | 当前公开客户端源码确认；本轮未调用。 |
| Read output/reference resources | `POST /octo_api/v1/resource/batch_get`，body `{project_id, resource_ids}` | 实际返回素材参数、`resource_id` / `submit_id` / `task_id`、状态和媒体地址。 |
| Queue lookup | `POST /octo_api/v1/resource/generation/queue_status`，body `{project_id, resource_ids}` | 对已有完成资源实际返回 `ret=0, results=[]`；没有排队中样本。 |
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

本画布 66 个当前视频资源的实际回读中没有发现 `materials.type=3`；本轮没有伪称已有 Shot 同时使用三类参考。视频分支的真实证据是下方独立存储上传；三模态同次生成仍为 `NOT_EVALUATED`。

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

这只是接入条件和风险判断，本轮没有实现 Production adapter 或证明服务端幂等。已完成结果恢复为本次有界 `PASS`；运行中恢复、无响应提交恢复、三模态生成闭环和长期稳定性为 `NOT_EVALUATED`。

## Verification And Evidence

本机总 receipt： [`.codex/tmp/jimeng-interface-research-receipt.json`](../../.codex/tmp/jimeng-interface-research-receipt.json)。它绑定 source revisions、公开 bundle、probe scripts 和各本地回执的 SHA-256。媒体和本机回执位于 ignored 目录，不随 Git 发布。

REA 实际捕获 `resource/batch_get` 的请求/响应字段结构，Evidence ID 为 `ev_ddd646a5a2635861a4b296a45a8a3c718a4598b1198ac7d052cd6e3f88de80d2`。保留文件是删除 URL query values 的 derivative，明确标记不能当作原始 Evidence 的字节等同副本；原始 stdout hash 单独保存。其 coverage 是 `policy_filtered` / attach-limited，没有 prior network；没有将其他 Chrome/Playwright 输出称为 REA Evidence。

局部文档契约、owned-path whitespace 和 receipt artifact hash 验证按实际执行结果记入总 receipt；本次没有运行完整工程 Harness。没有 Product behavior 改动，Parent Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：交付是有边界的研究记录和局部真实读写证据，不改变授权判断、凭据 owner、Production writer 或恢复语义。

使用 `record-ai-video-session` 保存本 checkpoint；`distill-ai-video-learning` 自动评估为 `no_candidate`。这是协议/单会话研究及一次提交前检查，没有满足独立媒体实验门槛，也没有修改 Skill、Policy 或 Gate。初次 Agent Memory 检索返回 incompatible shard / exit 3；continuation 的 experience 检索返回标记为 stale 的 last-good 片段并提示后台 refresh。两次均按 retrieval owner 使用当前源码与运行证据，没有前台重建或重试索引，也没有用检索片段作为授权。

## Paid Continuation Boundary

尚未发出任何新生成请求。最多一次 exact 试验已获确认；当前停止条件是原生 `credit_insufficient` 和尚缺用户数值积分上限。恢复时应核验同一账号最新余额及 exact 选项的 fresh quote，确认额度足以覆盖且不超过用户上限，再完成适用 budget / durable intent / one-use permit 边界。一次试验授权不包含充值、购买、缩短时长、删参考、换模型或自动改用另一权益。

提交后保留同一任务 identity，验证排队、断开客户端、重连、下载及 exact 媒体 Gate；unknown 停止，不重交。原生 quote 和这份研究报告均不构成付费 permit，已完成旧结果的恢复证据也不构成新生成或长期稳定性证明。
