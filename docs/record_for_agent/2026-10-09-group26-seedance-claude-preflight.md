---
record_kind: session_summary
topic_id: fanxiang-group26-seedance-fidelity
learning_eligibility: ineligible
---

# Group26 Seedance Claude Preflight

Date: 2026-10-09

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
