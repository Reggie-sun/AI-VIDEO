---
record_kind: session_summary
topic_id: haokou-ninebot-ad-generation
learning_eligibility: ineligible
---

# Haokou Ninebot Ad Generation Preflight

Date: 2026-09-14

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

媒体判定 **FAIL**：4秒戴头盔角色与8秒未戴头盔骑行角色/服装变化；
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
