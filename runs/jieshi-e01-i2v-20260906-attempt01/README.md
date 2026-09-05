# Jieshi S01 First-Frame Preparation

## Status

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
