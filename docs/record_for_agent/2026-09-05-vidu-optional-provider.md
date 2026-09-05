---
record_kind: architecture_implementation
topic_id: vidu-optional-provider
learning_eligibility: ineligible
---

# Vidu Optional Provider Record

Date: 2026-09-05

## Result Trust Follow-up

用户明确批准调整首次下载的 CDN 信任方式。新增显式
`result_trust="authenticated_task"`，只消费 official authenticated exact-task 查询返回的
同一 creation URL；不再要求该模式在首次生成前已知 CDN。默认 `fixed_origins` 保留
旧 profile bytes/hash；新模式进入 sealed profile，不能替换旧任务 profile 绕过绑定。

`vidu_download.py` 是唯一 Vidu 结果网络连接实现，两个模式均检查所有 DNS answers，
仅连接已验证 public 数值 IP，并以原 hostname 执行 TLS SNI/证书验证。API client 与
media socket 分离，无 inherited credentials/cookies、环境 proxy、redirect 或 retry。
新模式复用 `RemoteMediaMaterializationReceipt` 绑定 exact locator hash 与下载 bytes；
不持久化 signed URL，不新增 lifecycle owner 或放宽 paid/media acceptance gates。

离线 Red：首次无 CDN 的显式 profile 测试在修改前失败；Green：Vidu focused suite
144 passed，包括旧 hash/roundtrip、wire headers、public IPv4/IPv6、混合 DNS、TLS
失败、redirect、超时参数、资源清理与 task/model/creation/profile drift。独立 review
发现全局 `http.client` debuglevel 会打印 signed URL；新增 failing stdout regression
复现后，强制 per-connection debuglevel=0，相关 regression 与完整 focused suite 通过。Fake socket
测试执行真实 `http.client` framing，但没有真实 CDN/TLS/live media 证明。
Independent review 与 exact-commit Harness 是额外 completion evidence，按最终 receipt
核验；不能由该 focused count 推导。此次没有读取 credential、Provider calls、上传或
生成媒体；其他窗口 staged `runs/` 保持原样。配置详情由 [Vidu Provider](../vidu-provider.md)
独占；历史 CDN blocker 见 [superseded preflight](2026-09-05-vidu-live-preflight.md)。
`distill-ai-video-learning`：`no_candidate`；本次是单个 offline implementation，
没有独立生成实验或满足 admission threshold 的 controlled comparison。

## Capability Follow-up

同日用户要求补齐 R2V 和 `VIDEO_EXTEND`。本 follow-up 已在原 adapter 上增加
`viduq3`／`viduq3-turbo` 的 1–7 张图片参考，以及 `viduq2-pro`／`viduq2-turbo`
的无声 Vidu 视频延长。下方三模式与 37 tests 描述原 checkpoint，不再代表完整能力清单。

新增 `vidu_source.py` 的 `ViduExtensionSource` 只验证 canonical submit/fetch/probe
链及 exact source bytes/measurement。注入 source supplier 后，adapter 重查原 task，
只复用与 fetch opaque file ID 一致的 creation，随后通过既有 fetch 流式重验远端完整
SHA/size；丢弃校验字节，不落盘。该 source proof 不替代 Registry/continuity/activation owner。
无 raw URL input、upload、第二 writer 或 fallback。
Source video 也纳入 exact paid egress。`output_requirement` 表示完整成片长度，HTTP
`duration` 为减去 source measured duration 后新增的 1–7 秒。
官方文档只明确新增时长，没有明确返回媒体是否包含原片；当前完整输出约定仍需 live probe
验证，产物不符时原 artifact gate 拒绝，不自动裁剪。尾帧可选；外部 URL、有声源、
命名主体库、视频参考编辑和 `/4` native authoring 保持未接入。

Focused `tests/test_production_vidu.py`：80 passed；新增证据包括 1/2/7 图 payload、
R2V 与 extend 的 Router/compiler、真实 committer/service permit 与 restart 拒绝重复 POST、
来源变更/损坏/跨站与 exact egress mismatch、源时长/FPS/输出/角色/model 边界。
Independent review 发现 source GET 期间授权/报价过期后仍可 POST 的窗口；先以 3 个
failing tests 复现，再增加消费 permit 前的授权/报价重验和 extension prompt 2000 字符限制。
官方 [R2V](https://platform.vidu.cn/docs/reference-to-video) 和
[extension](https://platform.vidu.cn/docs/video-extension) 本轮公开文档 HTTP 200。
没有读取 key、付费 POST、上传或生成媒体；其他窗口的 staged `runs/` files 保持原样。
独立 review 与 exact-range Harness receipt 作为完成证据另行核验，不由本记录提前证明。
`distill-ai-video-learning`：`no_candidate`，没有新独立媒体实验。

## Credential Follow-up

同日后续 [live preflight](2026-09-05-vidu-live-preflight.md) 已验证国内站
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
