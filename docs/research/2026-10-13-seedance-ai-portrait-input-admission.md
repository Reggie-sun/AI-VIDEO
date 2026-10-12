# Seedance AI Portrait Input Admission Audit

Date: 2026-10-13

Status: `advisory_research`

## Finding

本次《界蚀》HTTP400的公开错误码是`InputImageSensitiveContentDetected.PrivacyInformation`。
没有发现当前请求的endpoint/model/role/JSON/Base64构造错误；存在明确的接入准备缺口：
本地fictional identity/egress声明被用于inline提交，未取得Provider认可的受信素材身份。
此前只解释“AI图也可能被拦截”，没有查全自有虚拟人像入库路径，结论不完整。
应优先保留原人物、原图与写实风格，核验私域AIGC素材路线，不因拒绝而改画风或降低逐镜验收。
准入错误不证明PNG是真人，也不证明Harness或模型连续性已通过。

## Official And Community Sources

| Source | Verified Claim | Limit |
| --- | --- | --- |
| [方舟私域虚拟人像库指南](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview?lang=zh) | 自有虚拟人像可创建AIGC素材组、上传并审核；只有`Active`资产可用于推理，以`asset://<asset_ID>`引用。需高级创作权益；Assets API用AK/SK及IAM；素材与推理key的`ProjectName`须一致。 | 未核验当前账号权益、AK/SK或实际入库。没有查询价格、购买权益或调用Assets API。 |
| [方舟肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh) | 同账号30天内指定Seedream 5.0文生图原始产物、Seedance原始视频及其返回尾帧可走信任产物路径；跨平台产物不在这条路径。另有预置虚拟人像、授权真人素材。 | 不是“所有AI图都可以直传”；也不是“自有跨平台AI图永远无法使用”，私域AIGC入库是另一条路线。 |
| [方舟Create Video API](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh) | 图片可用标准Base64或素材URI；2.0参考图1–9张、`reference_image`；Fast支持480p，2.0 duration4–15秒；显式原生声音字段。 | 格式支持不等于人像准入，不等于账号可调用或输出质量。 |
| [ArcReel Issue #2249](https://github.com/ArcReel/ArcReel/issues/2249) | 2026-08-31 reporter提供同错误码：AI生成的人像作为图片输入被拒，提出asset库接入需求。 | issue仍为enhancement/needs-info；triage回复注明AI生成。只使用reporter的拒绝事实，不能将建议或bot回复视为已验证修复。 |
| [ComfyUI官方Seedance节点源码](https://github.com/Comfy-Org/ComfyUI/blob/14c553159994b626738c392eb99d295ea3d683c1/comfy_api_nodes/nodes_bytedance.py) | image helper上传虚拟库、等待`Active`、返回`asset://`；first/last-frame及reference-image调用点实际使用该helper。 | 经ComfyAPI proxy，是其平台/账号的素材处理链；不能把proxy权限移植到我们的ARK_API_KEY，也没有执行该外部源码。 |
| [社区Seedream使用反馈](https://www.reddit.com/r/generativeAI/comments/1se1e69/anyone_else_getting_reference_images_rejected_in/) | 有用户报告AI写实参考被拦，也有用户报告在平台内先用Seedream生图再做视频。 | anecdotal、自报参数不完整且渠道不同；不外推为本账号、所有图或所有平台的成功保证。 |

别人能制作写实AI人物视频，可能使用已入库人物、受信模型原始产物、预置虚拟人像或不同平台包装的
素材处理链。仅看到成片无法判断其模型版本、时间、账号权益或实际传输，不能据展示片判定我们的准入条件。

## Exact Local Request Audit

当前源码snapshot为`cb79ef2a95052f614e63931075a4f090b886367c`。通过共享reader重开failed新attempt
`canvas-293bebb27dd2322c484e104df678ac97ff5bbd4f`及exact sealed request，重新核对execution binding。
纯重建请求并构造HTTPX request，未send、未lookup credential，Manifest仍revision29。

| Surface | Actual Value / Evidence |
| --- | --- |
| URL / method | `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks` / POST |
| Settings | `doubao-seedance-2-0-fast-260128`、480p、16:9、duration15、generate_audio=true |
| Images | 两个`reference_image`，分别为`door-layout`和`linyan-reference`，均为`data:image/png;base64,...` |
| Decoded image | 两项均解码到原SHA `1a21ac10047cab19b441bfefd84ab91fef8de4b6787b7a5c558794903ff18b55`，941×1672、1,801,377 bytes |
| Body | 4,804,956 bytes；SHA `845b3a3cb825334e086a8a804acced5ea36f06546352cc796882fd14b052e2ad`，低于64 MB；HTTPX保持body原bytes |
| Prompt | 原950 UTF8 bytes，SHA `f0bea858c193c474299df4314f31f7d3b59054ba90807b9f7695753b01a51748` |
| Projection | `seedance_rejection.py`只读取server `error.code`的known literal，不根据图片或prompt自行分类 |

同PNG被两个职责引用有冗余，但没有找到官方SHA唯一性规则或重复图片导致PrivacyInformation的证据。
不得仅为“修复”在adapter去重、删除scene/identity职责或重写已批准prompt。
这份audit是当前exact request的deterministic reconstruction，不是当时network wire capture；
历史raw server body未保留，所以不能声称排除了所有可能的代码问题。

本机证据位于`runs/canvas-jieshi-two-shot-20261013-001/input-admission-audit/`：
`exact-request-audit.json`、`comfyui-reference-identity.json`、`kimi-receipt.json`、`kimi-report.json`、
`parent-adjudication.json`。ComfyUI pin `14c553159994b626738c392eb99d295ea3d683c1`的源码SHA为
`e277456ff9cc959c52ce05b440d4368cffef3e4e411f208b826b8fce2011c7da`；只下载文本作分析。

focused既有tests：active Ark receipt、hash/evidence mismatch、inline I2V/R2V、Fast nominal payload，
8 PASS / 117 deselected。受管Kimi只读调用`97b75bad-471d-4a89-9495-838549ef4fe6`为PARSED，
deep/k3/max/Docker、2 wire requests、124.010秒；report SHA
`8a39ad23f837be6cf62e88329596ae03fee681691010e1716bcb9327d829b416`已核验。
Parent用官方资料及actual decoder裁决：重复图强制去重建议无因果证据；唯一真人路径说法不适用于本虚构图。
不自动采用其patch建议，不将PARSED/离线tests当成Provider准入或视频质量验收。

## Existing Owner And Minimum Recovery

`SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> SeedanceVideoProvider`已有
exact source PNG/confirmation/Active identity绑定与`asset://`输出，不需要第二生成链。
它导入的是已实际入库的human-observed素材；没有自动CreateAssetGroup/CreateAsset owner。
`ARK_API_KEY`不替代Assets API的AK/SK权限；账号高级权益、素材ProjectName与入库结果目前NOT_EVALUATED。

最小方向是把原exact PNG入AIGC组，取得actual Active asset/确认，再通过原共享入口绑定已有resolver。
本次同图两个local aliases对应同一provider asset时还需核对既有resolver的唯一ID约束；可先在source/data owner
表达真实alias与职责，不伪造第二Provider资产或Active receipt，不宣称当前已prepare成功。
后镜仍只在新前镜MP4全PASS后提取approved实际状态；若该中间帧需要入库，按其自己的exact bytes办理，
不机械改为尾帧。官方受信尾帧路线只能在actual状态及原单元契约匹配时作为候选。

本轮无新增视频Provider POST/poll/fetch、无Assets调用/云发布/购买，无Production mutation。
项目POST实际2、历史7、累计9保留；当前剩余一次不能覆盖fresh A+B。
后续调用须保留历史并明确下一有限单元、exact inputs、上限与permit，不能把本次研究当作新执行许可。
两镜视频、MCP、状态绑定、声音/trim/HyperFrames、human完整听看及完整故事AC-7仍未完成。
