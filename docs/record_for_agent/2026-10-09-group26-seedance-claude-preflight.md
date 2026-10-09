---
record_kind: session_summary
topic_id: fanxiang-group26-seedance-fidelity
learning_eligibility: ineligible
---

# Group26 Seedance Claude Preflight

Date: 2026-10-09

## Supersession Notice — Live Canvas Recovery

同日后续已连接登录中的画布并取回正确场景，下面“场景bytes未取回/浏览器不可连接”只描述首次检查。旧720p视频和720×405图片是画布预览版本，不是本轮下载入口提供的高分辨率文件；原上传文件bytes仍未知。参考时长冲突和Ark人物素材接入仍未解除，新增生成POST仍为0。后续实证见本文末节。

## Scope And Status

用户要求改用已充值的火山方舟 API、原样复刻原画布，并在生成前让 Claude 审查。沿当前话题解释为《门挡不住？》对应视频15第26组完整五镜，已向用户说明；不是整集39节点或此前单独潘子一镜。原文、四句对白、15秒、16:9、720P、四图一视频参考保持，不新增改戏、架构或Spec/Plan。当前生成 POST **0次**，没有可提交的最终payload、生成结果或采用判定。

用户明确指定 `.env` 的已有密钥为本次来源，此明确指令覆盖旧的密钥环来源约定；只在内存读取并进行一次官方 `GET /api/v3/models`，返回HTTP200且列出 `doubao-seedance-2-5-260628`。不记录密钥、复制到其他配置或推断余额与生成权限。

## Exact Evidence And Blockers

本次run：`runs/fanxiang-group26-seedance25-20261009-001/`，`canvas-node.json`、`canvas-prompt.txt`保留2026-10-02画布捕获节点 `node_jxawv40nkz`，`preflight-facts.json`列明未决项。当前composer并非历史成功生成请求的证明。

- 原场景图为 `node_6qsfrhkdye` / resource `db7ee5ef-909a-4d18-824f-8717c63a22c6`；旧流程 `dormitory.webp` 来自 `node_29px8wry7c` / resource `916f9662-3e6c-40c4-be9d-ca55dc8e2daa`，不能替代。原观察浏览器的已知CDP端点当前不可连接，默认浏览器仅about:blank，本轮未取回正确场景bytes。潘子两个重复节点的resource相同，不能仅因node不同就判素材不同。
- 原视频 `runs/fanxiang-exact-canvas-h3-20261002-002/reference-11-copy.mp4` SHA-256 `db5091240ea83db2fee4939205ca48188bd84391508b21b2a1d706d5627ee15d`，原捕获实测1.880816秒。当前 `default_seedance_capabilities()` 的2.5 R2V视频下限为2000ms。旧H3衍生版补3帧到2秒，不能冒充原件。
- Parent实际查看三张角色板，均为写实人物外观。当前 `seedance_asset.py` 对 `synthetic_photorealistic_person` inline egress明确拒绝；直接离线调用现有判定得到 `paid_provider_egress_not_authorized`，无credential或网络。已验证的Active Ark asset lane另有契约；本次未取得这些参考的有效物化身份。此为当前项目输入接入限制，不宣称Seedance模型本身无法生成这些角色。

## Claude Review And Decision

用户指定的Claude审查经已安装 `discussion-with-claude` 的只读CLI relay执行，返回 `ok=true`；结论保存为 `claude-review.json` / `claude-review.txt`。Claude确认原文五镜、四句对白完整，但没有最终payload，参考接入与1881/2000ms冲突未解决，因此仅为准备审查、未放行。其结尾误写“四镜”由Parent纠正为五镜；其建议删视频参考不由本任务授权，不执行。Claude未审阅媒体或听辨声音，不能代签成片质量。

Parent保留原文与原参考，不删图、不补帧、不改时长、不改人物分类、不绕过egress gate，不提交已知不保真的替代请求。恢复条件是取回原场景bytes、建立有效Ark参考接入身份，并解决原短参考与接口下限冲突；任何实质参考调整须明确区分于1:1输入。

## Verification And Learning

已核对当前源码、实例化能力配置、原画布inventory/resource身份和历史视频bytes证据；密钥仅作一次只读模型列表查询，无上传或生成。未修改代码、旧媒体、音轨或采用状态。按 `record-ai-video-session` 保存，自动学习评估 `no_candidate`：这是零生成的输入准备阻断，不形成模型质量经验或新的Skill/Policy。

## Live Capture And Reference Binding Follow-up

用户明确授权读取后再交Claude检查，并写代码补足缺失节点表达。本轮run为 `runs/fanxiang-canvas-fidelity-20261009-002/`。已读取94节点（54图/40视频）、272条reference边、39个生成composer和227处富文本引用；与10月2日捕获相比node/resource身份、39份prompt/parameters均无变化。上传视频没有生成composer，不是漏读。整画布读取不授权39次付费生成，当前生成目标仍为Group26。

`scripts/canvas_reference_packet.py` 新增离线准备：完整保留观察graph/composer，校验覆盖、连线和资源身份；按slot/node/resource绑定，保留重复出现的chip，保留只在素材栏而未写入正文的视频。真实Group26正文引用顺序是小龙/曾亮/潘子/宿舍，素材栏为小龙/潘子/曾亮/宿舍/视频；不可按位置配对，亦不能据UI推断浏览器后端实际排列。`canvas-packet.json`保留全量，`group26-input-packet.json`保留当前单元。两者是准备数据，不是Production导入或已接入的Seedance提交payload。

正确场景现已取回：resource `db7ee5ef-909a-4d18-824f-8717c63a22c6`，5632×3168 PNG，27,256,502 bytes，SHA `10ffcabd9487528ba9734d5335480896b58d163bf0e47f1dbd756687c9e86467`。三角色分别为小龙3840×2160 JPEG、曾亮2048×1152 PNG、潘子3840×2160 PNG，绑定见`current-image-identities.json`。这些是画布当前full-size服务文件，不能保证等于最初上传bytes，JPEG格式本身也不能证明发生再编码。

同视频resource的当前`downloadUrl`文件保存为`original-guide.mp4`：1920×1080、45帧、24fps、H.264/AAC，视频1.875秒/音频1.880816秒/容器1.881秒；84,871 bytes，SHA `4217e17b7de90e326dd5952ae0c0f6e5993b7294fd8b3274dfdc2e10c1a6b78b`。旧1280×720版本的测量与历史使用保留，但不能继续称为与下载文件完全相同。未补帧或变更对白/时长。

Claude首次新审查确认Group26五镜四句及参数、光照要求内部一致，身份绑定避开顺序陷阱；其未独立审阅全39组剧情，全量保留/相等性由Parent程序验证。Kimi只读检查 invocation `fa6fb436-6565-44fb-a3f8-bbe85d0f287b` 为PARSED，报告与Parent裁决保存于run；其“只能标题匹配”的建议已由随后取得的rich document精确ID证据取代，不采纳。两者均未审片或听辨。

新增10项回归测试覆盖角色引用不同序、重复引用、缺节点/边/资源冲突、正文外视频、歧义停止；policy只增加该工具的测试路由及full-suite覆盖声明，不降低原检查。首次Harness因新增check未登记full-suite覆盖而失败，已补齐，保留失败receipt。实现Risk Gate为`KIMI_REVIEW_NOT_REQUIRED`：纯离线准备工具，无凭据/网络/Production写入，测试后无关键损坏或越权风险缺口；用户明确要求的Claude审查另行完成。学习评估仍为`no_candidate`，不形成模型效果定律。

Claude补充复核已返回`ok=true`，`claude-supplement.txt`核对旧Group26基线、当前packet和全部五份素材身份，确认原文/参数及resource/storageKey对应；撤回“JPEG即可证明再编码”和未存在下游的KeyError担忧。视频与图片仅为当前画布服务文件，原上传bytes、历史提交参数/seed、Ark提交等价性与成片表现仍未证明。最终验证receipt为`.agent/harness/runs/canvas-fidelity-20261009-004/receipt.json`；无生成、上传、改戏、画布节点增删或Production状态变更。
