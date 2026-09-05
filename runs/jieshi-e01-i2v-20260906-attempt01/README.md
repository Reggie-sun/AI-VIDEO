# Jieshi S01 First-Frame Preparation

## Current Result — 2026-09-06

I2V 接入修复提交 `80b5ffe`；已完成一次 Vidu q3-pro 4秒1080p真实首帧调用和 exact MP4 Gate。
最新请求与证据为 `preparation-v7/`；`preparation-v3` 至 `v6` 是保留的离线诊断，不是额外生成。
下载成功，但[逐镜 Gate](preparation-v7/shot-01-gate.md)为 **FAIL**：短暂手影、多余数字和机位变化。
MP4 SHA-256：`b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a`。
素材有真实抬手、实测1080×1920/24fps/4.042s；未激活、没有S02提交。

初次下载因本机 fake-IP DNS 被公共地址 guard 拒绝。`fetch_i2v.py` 在同一 durable FETCH
阶段用仅本进程的真实公共DNS解析恢复，原域名 TLS/SNI、公网IP校验、禁止redirect和
无凭据下载保持；无第二次 generation POST。两个 scoped `reviewer_xhigh` reviews 均 accept。

用户随后明确改为原生声音优先，见[本集声音策略](../../docs/superpowers/artifacts/drama/jieshi-episode-01/episode-01.md#audio-production-policy)。
本次已提交无声请求保持历史身份。应用户价格问题，只读查询同参数audio开/关均96积分；
没有刷新旧profile或另发生成。旧85元授权未使用；本次新的一次submit已消费，reservation未因推算账单而结算。

## Historical Preparation Status

`STOP_AT_READINESS`。未生成新视频，未创建新 paid intent/permit。没有可供逐镜 Gate 分析的新 MP4，不能推进 S02。

## Imported Source

`production-s01-v1/project.yaml` 经 `ProductionStateCommitter.bootstrap_initial_state()` 创建，随后通过 `prepare_human_image_import_commit()` → `ProductionStateCommitter.commit()` 导入 SC01 场景参考，strict loader 已重开。

- 原图：`../jieshi-e01-seedance20-20260905-001/preparation/shot-01-first-frame-v1.png`。
- SHA-256：`4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
- 实测 941×1672、2,064,319 bytes；未放大、未改变像素。
- Import receipt：`89318576d4eed1eafaaba834f57b832f8376168d25ac735125791966ad9109b1`；Registry revision：`ccc4125408d9be5141eee3e4d804ec6ebb8215f2da5c5678c71b45637b477a19`。
- Approval 只记录本次用户指定该 exact PNG 并要求检查后 import 的指令；不声称用户亲自完成视觉验收、Ark Active 观察或 Seedance human egress attestation。
- Agent 看到林砚本人、七个他人倒影及空的林砚倒影位置。白工牌缺少可读姓名/头像，仍是后续制作要处理的细节；不是已完成全片人物素材验收。

初次尝试在 pending video Shot 同时声明空 `first_frame` 图片 role，被 strict bootstrap 拒绝；`production/` 保留该未完成准备目录，不是有效 project。唯一当前 project 是 `production-s01-v1/project.yaml`。没有使用 tests fixture。

## Current Readiness Evidence

以 `planning-request-v2.json`、`video-plan-v2.json`、`readiness-v2.json` 和 `preflight-summary.json` 为准。首版 `planning-request.json` 将 scene-owned 图片投影为 `approved_keyframe`，该诊断不成立；v2 保留真实 `scene_reference`，没有伪造 S01 图片绑定。

`VideoPlanner._dynamic_decision()` 对 S01 的人物声明和 `AUTO + FIRST_FRAME` 追加 `IDENTITY + SCENE` 并选择 R2V；现有初始 I2V 分支只用于商业投影，另一分支需要真实前镜终帧。`GenerationOperation` 没有显式 I2V 值。普通 `approved_keyframe` 又要求 Shot `final_visual` 已绑定 IMAGE，与 pending generated-video Shot 只能保留一个空 VIDEO role 的契约不兼容。

v2 的 request/plan binding 和已声明场景参考 readiness 通过，但 `plan_eligibility` 阻塞；`verified_generation_requirement=null`。没有绕过 readiness 去构造 ProviderBound request、没有直接提交 Provider，也没有伪造 prior terminal。

## Provider And Quote

Seedance 当前虽能读取写实虚构人物 receipt，但 `SeedanceSyntheticImageAuthorizer` 和 `SeedanceSyntheticImageReferenceResolver.validate_submit()` 仍调用 `_deny_photorealistic_person_like_egress()` 拒绝该分类。不能用“项目虚构人物”声明使本图通过；也没有笼统要求真人 Ark 入库。

Vidu `authenticated_task` 已可用，不需要预知 CDN。`provider-profile.json` 是新 proposed profile，旧 profile 未修改。候选参数为 `viduq3-pro` / I2V / 4 秒 / 1080p / 24fps / 无原生音轨；I2V 的 geometry/ratio 为 adaptive，最终 1080×1920 仍需实测。当前 API 请求并未编译完成，profile 静态支持不等于 live 可用。

`pricing-query.json` 记录一次 `POST https://api.vidu.cn/ent/v2/pricing` 报价查询 HTTP 200：同参数 96 积分。按官方公开 1 积分 ¥0.03125，约 ¥3.00；两处静态价表不一致，采用该接口观察。`budget-proposal.json` 仅提出新一次调用最高 ¥3.00，尚非授权。此前 85 元 scope 已消费，不复用余额或 permit。

## Next Action

需要先对非商业首镜 first-frame I2V 的 Planner/readiness/source binding 做有界契约修复，然后沿现有 Router/compiler/Provider owner 重新生成准确预览。不得删除人物声明、伪造商业投影、把首图当成前镜已接受末帧，或转回 T2V。接入通过后再落实新一次有限预算及 exact egress、intent、permit，生成后对 exact MP4 调用 project-local `video-analysis`。

本次无 runtime code 修改、无 worktree、无 push；既有 staged runs 保留。动态 JSON 和 Production state 为本机 run evidence，不当作 Harness 或视频质量 PASS。
