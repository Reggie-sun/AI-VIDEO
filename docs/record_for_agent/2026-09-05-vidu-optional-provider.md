---
record_kind: architecture_implementation
topic_id: vidu-optional-provider
learning_eligibility: ineligible
---

# Vidu Optional Provider Record

Date: 2026-09-05

## Credential Follow-up

同日后续 [live preflight](2026-09-05-vidu-credential-live-preflight.md) 已验证国内站
credential 与账户查询 HTTP 200，并安全保存 `VIDU_API_KEY`。下方“没有读取真实 credential”
描述原 implementation checkpoint；生成 POST、媒体质量及 P6 仍未验证，后续未提交生成。

## Scope And Runtime Truth

用户要求将 Vidu API 作为 Provider 之一接入。新增 `vidu.py` 与 `vidu_profile.py`，
使用既有 explicit `VideoProviderRegistry`、generic compiler、`VideoGenerationService`
和唯一 writer `ProductionStateCommitter`。没有 schema migration、默认选路或 fallback。
支持 Q3 Pro/Turbo T2V、单首帧 I2V、首尾帧；具体 profile、凭据引用、cost ceiling、
output/input 和 authoring 限制由 [Vidu Provider](../vidu-provider.md) 维护。

## Verified Decisions

- Submit 消费 exact durable permit 后只有一次 POST；unknown outcome 不自动重试。
- Task binding 包含 exact profile hash，防止后续更换 CDN allowlist 或其他 profile 字段。
- Preview 从 activation scope 重新 resolve，不能凭同名 capability ID 提交其他模型。
- HTTP transport 使用 exact request，API 使用 injected supplier credential，CDN 不继承
  client defaults/auth/cookies。下载重查同一 task，绑定同一 creation ID；signed URL 不落盘。
- Generic Router 当前不接受 nominal timing；`exact_seconds` 已实测走通
  Router→compiler→adapter。真实输出由原有 artifact gate 判断，`/4` native authoring
  没有表达器时继续 typed unsupported。

## Verification

- `tests/test_production_vidu.py`：37 passed，包含真实 committer/service durable permit、
  restart 后重复 submit 拒绝、Router/compiler、profile/model drift、HTTP auth 隔离等。
- 与 `tests/test_production_provider_neutral_adapters.py`、`tests/test_video_generation.py`
  的组合：81 passed。
- Native `reviewer_xhigh`：`accept`。Parent 复核并增加了三处边界修复的回归测试。
- `git diff --check`、policy audit、documentation contract gate：通过。
- Exact-range Harness 是独立 completion proof；本记录不提前替代其 receipt。

## Remaining Boundaries

没有读取真实 Vidu credential，没有付费 POST、上传、生成媒体、activation 或质量验收。
官方文档核对与离线测试不能证明账号可用、当前 billing 结算或 Provider 输出质量。
本地实现提交不表示 push/release。其他窗口的剧情素材及其提交不属于本任务。

Memory retrieval 命中部分 stale advisory history，未将其作为 Vidu 当前事实或授权。
`distill-ai-video-learning` evaluation：`no_candidate`；只有一个 offline implementation，
不存在满足 admission threshold 的独立媒体实验或 controlled comparison。
