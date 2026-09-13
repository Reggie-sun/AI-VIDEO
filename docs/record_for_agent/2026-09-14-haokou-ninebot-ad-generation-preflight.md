---
record_kind: session_summary
topic_id: haokou-ninebot-ad-generation
learning_eligibility: ineligible
---

# Haokou Ninebot Ad Generation Preflight

Date: 2026-09-14

## Repair Delivery — 2026-09-14

用户随后明确要求“修正”。本节取代下方旧版“没有修正版”的当前状态；原始失败
attempt及DNS证据继续作为历史保留。新修正版已通过canonical HyperFrames render
verification，由committer激活render state；这不是原始Provider candidate activation，
也不是P6、用户验收或发布。

修正版：`runs/haokou-ninebot-ad-repair01-20260914/delivery/潜江市浩口9号电动车-修正版.mp4`。
SHA256：`9cdc9f00db62a17819d150a713116dfd55a9a2d73ab2ff30c916e3f92ef7562a`；
30,001,372 bytes，1080×1920，24fps，672frames，视频28秒，容器28.022秒，
H.264 + AAC 48kHz stereo。交付副本与canonical output逐字节SHA一致。

本次新的有限repair授权只执行一次Vidu `ad-one-click` generation POST，task
`996764199801622528`，request SHA256
`5973dd578374883f3a5b6f9bc30dc161a193cc2d730a7e4ea3f99e39eef9f176`。
保留1000 CNY本地safety allocation及submit ceiling=1，不是价格声明；未追加远程
variants。参考包括官方商品图及第一版6秒角色帧；新source candidate SHA256
`9c980b14730c300feb193daad52849737faee6129606f43768e7744f7f84fb39`。
修复后的系统DNS可正常完成canonical fetch，无本轮进程DNS override。

新source改善了人物白头盔、橙黑白外套连续性，但尾卡生成了“月990”及无关网址，
不能直接交付。通过独立真实import project登记静音visual及原始旁白/音乐混合PCM，
由唯一`ResolvedTimeline`及P4混音进入HyperFrames；未把旁白混合音轨伪称BGM，
未使用FFmpeg drawtext/direct mux替代final renderer。源预处理只做画幅、帧率和
末帧补齐到28秒，原声保留到28秒。

最终门店标题在4秒与22秒切换字号，骑行段避让头部，尾卡完整覆盖错误文字；
底栏保留“感应解锁 · 离车自动锁”、APP预先设置条件和“欢迎到店体验”。
`video_analyze`对最终exact MP4实际执行，抽查0–26秒每2秒共14帧，另查27.9秒；
人物头盔/服装、文字、尾卡覆盖及技术音视频检查通过。
证据位于同run的`review/final-analysis.json`、`final-review.json`、`final-last-frame.jpg`。
ASR同音错字不作为口播地点读错的证据；本片仍是生成式品牌广告，不声称精确SKU
实拍还原。用户主观认可和正式P6仍未评估。

## Repair Runtime Findings

- 缓存Chrome146在实际seek时出现`PIPELINE_ERROR_DISCONNECTED`，视频像素不变，
  HyperFrames正确报`sweep_static`。同一source改用既有`browser_path`指向本机
  Chrome149.0.7827.53后check通过；没有修改node_modules或禁用检查。
- 671帧输出的有效音频比timeline少16samples，严格audio verification拒绝；
  改为目标内的完整28秒/672帧后通过，没有放宽sample contract。
- Pydantic严格JSON重读`CompositionSpec`/`ResolvedTimeline`时，parent before-validator
  已将嵌套JSON数组物化为Python list，五类graphic tuple字段拒绝自己的序列化输出。
  唯一代码修复在`commercial_graphics.py::_StrictModel._json_reference_arrays`：
  仅JSON模式把这五类数组转tuple，继续检查元素类型，Python strict语义不变。
  未修改其他会话的`composition_contracts.py`、`models.py`或paid/voice writer。
- 回归测试先复现两个roundtrip失败；修复后composition/ad-creative focused tests
  105 passed，另有6个聚焦边界测试通过。`reviewer_xhigh`独立复现旧代码错误、
  验证真实封存对象及54个非法输入，verdict `accept`。代码commit：`e30e8fd`。
  exact-commit完整验证receipt：
  `.agent/harness/runs/haokou-graphics-json-fix-20260914/receipt.json`；
  各mandatory check状态由该receipt记录，focused tests不替代它。
- canonical成功attempt为`composed-production-28s`中的`haokou-28s-render-02`，
  render state hash `8f7f279e748d5cf318733f0776e137d65bf42afe6ab0dac99f93d2c9d279df0e`。
  旧本地失败attempt和未验收diagnostic render保留，不作为交付结果。

按`record-ai-video-session`更新本记录并执行`distill-ai-video-learning`评估：
`no_candidate`。当前是依赖原始角色帧的repair链，同时改变prompt/reference和本地
图文策略，未形成可隔离归因的新跨实验模型能力结论；局部兼容故障由代码、回归测试
及本次runtime证据记录，不自动扩大为Provider策略。未修改学习target或刷新RAG。
交付仅在本机；其他staged/dirty文件保持原状，无push/release。

## Supersession And Live Result — 2026-09-14

下方缺少 operator ceiling 的停止点及 `Next Action` 已成为历史。用户随后回复
“没有上限”，本次据其授权封存1000 CNY有限本地 safety allocation，明确不是官方报价
或账单预测；task submit ceiling仍为1。已实际调用一次 `ad-one-click`，不再处于
generation submit=0，也不再缺少 Production bundle 或 credential presence evidence。

官方 Fz2 系列说明书核实了APP/蓝牙设置后坐上解锁与预先开启的离车自动锁车；
依据在 `runs/haokou-ninebot-ad-20260914/preflight/product-fact-check.json`。
真实公开商品参考经 canonical bootstrap 登记，标准 loader通过，未使用测试fixture。
request SHA256：`f3560ea383805efc1d30bf41fdf5d538a800e29bf9185e5a6c1fce01a2941add`。
任务 `996756627904311296` 从accepted到success，generation POST=1，没有重提或variant。
`reviewer_xhigh` 对封存单次提交及后续fetch-only恢复分别给出accept。

视频已由committer下载为未验收source candidate：
`runs/haokou-ninebot-ad-20260914/production/state/ad-generation/candidates/7f1efbeb2da31ee635cf0a66e10fa03a59af72ac753d7b9b4df0c253ae9c3a93.mp4`。
SHA256即文件名；12,944,384 bytes，1080×1920，24fps，672frames，28.010秒，
H.264 + AAC 48kHz mono。project-local `video_analyze` 与 `video_extract_frames`
均实际执行；原始分析和抽帧在同run的 `review/`。

媒体判定 **FAIL**：6秒戴头盔角色与10秒未戴头盔骑行角色/服装变化；
24秒与26.5秒尾卡没有要求的“潜江市浩口9号电动车”文字。
ASR存在明显同音识别错误，不能据其单独认定旁白念错地点；音频口播精确性仍未验收。
有声可播放与Provider success不等于创意、质量或Production Final Acceptance。
未激活candidate，未进入P4最终合成，未发布。当前一次提交额度已使用，未自动新增调用。

## DNS Repair And Verification

初次canonical fetch因Mihomo把视频域名解析为`198.18.0.247`而触发公网IP guard。
fetch-only进程使用公共DNS恢复同一视频，保留canonical公网IP检查、TLS/SNI、禁止
redirect与无凭证media GET。用户随后明确要求“先修复dns”。

持久修复仅在本机 `~/.local/share/io.github.clash-verge-rev.clash-verge-rev/`
的 `dns_config.yaml` 与 `codex-mihomo-runtime.yaml` 各新增一条
`dns.fake-ip-filter`：`prod-ss-vidu.s3.oss-cn-beijing.aliyuncs.com`。
修改前后完整解析对象比较确认其他字段相同；Mihomo离线配置验证通过，热加载HTTP204。
私有原配置备份：`/home/reggie/proxy-config-backups/vidu-dns-20260914-003627/`。
没有修改VPN仓库已有dirty templates，也未修改AI-VIDEO运行时代码或全局DNS模式。

修复后system getaddrinfo返回`8.141.221.10`/`8.141.221.11`，canonical公网guard通过；
**不使用进程DNS override** 再经canonical downloader读取完整视频，SHA256与已落盘
candidate完全相同。证据：`preflight/system-dns-fix-verification.json`。
适用范围是本次视频下载域名；未宣称所有Provider/CDN均已修复。

## Checkpoint Assessment

本轮调用使用当前shared working tree，未接管其他会话的voice/runtime改动。
只更新本记录与任务run artifacts，并作上述已授权本机DNS配置修复；无push/release。
按 `record-ai-video-session` 记录后评估 `distill-ai-video-learning`：
`no_candidate`，本广告只有一个生成attempt，不足以提炼广告模型能力的跨实验规律。
DNS重复案例已有精确恢复记录，本轮仅落实主机配置，未提出新的advisory target adoption。
未刷新RAG索引。以下为保留的历史preflight证据。

## Scope And Result

用户明确要求生成广告，延续“潜江市浩口9号电动车”、抖音/快手竖屏和相对传统电动车
便利性的目标。计划28秒、9:16、中文，最小 task submit ceiling 为1。
这构成任务内生成授权，不需要再次询问是否允许付费调用。

当前停止于 `BLOCKED_MISSING_OPERATOR_CEILING`：检查 `runs/**/provider-profiles/*.json`
共191份，其中10份使用 Vidu 国内 endpoint，但没有 `service=ad-one-click` profile。
历史普通视频上限不构成整片广告服务的已配置上限，不能擅自沿用、从测试 fixture
取值、查官方价格或通过时间续期改变 service scope。

## Prepared Evidence

`runs/haokou-ninebot-ad-20260914/preflight/readiness.json` 保存规格、一次提交上限、
地点文案、拟定段落及配置检查结果。此前下载的 Fz2 30 图片复制为
`preflight/product-reference.png`，实测 SHA256 与字节数保存在同一 JSON。
参考图已经人工视觉检查；拟定功能镜头仍需绑定可靠车型资料，不标 authoring ready。

本轮没有创建 Production Project、durable submit intent 或 permit；generation submit=0。
未读取 credential；其可用性未知。没有 Provider 视频、没有成片或质量验收。
只进行了只读产品资料查询和本地准备，没有查询 Provider pricing。

## Next Action

由 operator 配置本次 `ad-one-click` 的有限人民币费用上限，或提供现有该服务 profile。
这属于 runtime Budget Guard 所需配置，不是官方单价查询，也不是重复申请生成授权。
取得配置后继续核实车型功能、封存素材与请求、走现有 committer/paid Gate 提交一次，
下载后执行真实媒体检查；不得根据本记录跳过任何 Gate。

记录与 automatic learning evaluation 已完成，结果 `no_candidate`：没有新的真实
生成实验可用于跨实验学习；未主动刷新 RAG 索引。
