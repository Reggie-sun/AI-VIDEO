# Vidu Video Provider

## Scope

`ai_video.production.vidu.ViduVideoProvider` 是显式注入的 optional video Provider，
通过既有 `VideoProviderRegistry` / `VideoGenerationService` 使用。
支持 `viduq3-pro`、`viduq3-turbo` 的 T2V、单 `first_frame` I2V，以及
`first_frame + last_frame` 首尾帧模式。其他模型、参考生视频、视频延长、主体库和
自动选路不属于本次接入。

## Configuration

创建 `ViduProviderProfile` 时必须提供 official `origin`（`https://api.vidu.cn`
或 `https://api.vidu.com`）、实际结果 CDN 的 exact `result_origins`、
`cost_upper_bound_microunits`、timezone-aware `pricing_observed_at` 与
`pricing_expires_at`。费用字段是覆盖所使用 Q3 请求的 operator per-call ceiling，
不是内置报价；国内站使用 CNY，国际站使用 USD。过期 ceiling 在 preview 阶段拒绝。
不要把测试 CDN、示例费用或历史报价直接用于真实调用。

```python
from ai_video.production.vidu import HttpxViduTransport, ViduVideoProvider
from ai_video.production.video import VideoProviderRegistry

# profile contains verified pricing and CDN origins.
# credential_supplier resolves VIDU_API_KEY without logging its value.
transport = HttpxViduTransport()
provider = ViduVideoProvider(
    profile=profile,
    transport=transport,
    credential=credential_supplier,
    image_resolver=registered_image_bytes,
)
registry = VideoProviderRegistry((("vidu", provider),))
```

请求使用 `profile.pointer()` 绑定 exact profile hash；profile bytes 按既有
production preparation seam 持久化。`credential` 是 injected supplier，
paid preview 的 `SecretReference` 必须为 `secret_store / VIDU_API_KEY`。
不要将 raw key 写入 repository、命令参数、日志或 profile。
调用方拥有 transport 生命周期，使用结束后调用 `transport.close()`。

## Output And Inputs

Q3 接入范围为 1–16 秒 `exact_seconds` / `nominal_seconds`、540p/720p/1080p、24 fps MP4，
`native_audio` 必须显式选择。T2V 使用明确 ratio 和匹配短边 resolution 的 exact
width/height；I2V 使用 `dimension_mode=adaptive / ratio=adaptive`。
最终尺寸、帧率、时长和音轨仍需既有 artifact validation 实测，API 参数不能证明产物
满足要求。显式 seed 接受 1–2147483647；0 的 Provider 随机语义不冒充固定 seed。
Generic Router 当前使用 `exact_seconds`，其时长要求由 downstream artifact gate 实测；
`nominal_seconds` 只用于现有直接 request seam，不改变 neutral requirement timing contract。

Image resolver 必须返回绑定的 exact registered bytes。Adapter 核对 SHA-256、size、
MIME 与比例，然后在内存编码 data URI；完整 JSON body 不得超过 20 MiB。
首尾帧模式固定 first/last 次序。所有 prompt/image bytes 必须进入 paid egress preview。
与既有 cloud adapter 一致，generic compiler 对没有 native prompt 表达的 `/4`
requirement 返回 typed unsupported；本次不扩展 Director/native-prompt authoring。

## Lifecycle And Verification

`submit` 只在 durable paid permit 消费后执行一次 POST。超时、无法解释的响应和
非明确拒绝均为 unknown outcome，必须沿既有 explicit recovery 处理。
查询通过 exact task URL，若响应带 task/model 字段则复核；下载时重新查询同一 task，
要求同一 creation ID，仅在 sealed HTTPS result origin 上 GET，且不发送 API credential。
URL 仅在进程内存中使用；receipt 不保存完整 signed URL。

离线测试：`python -m pytest -p no:cacheprovider tests/test_production_vidu.py -q`。
本次实现不表示 credential/access、live submit、真实媒体质量或 P6 / Final Acceptance
已验证；也不自动 activation、retry、切换其他 Provider。

## Official References

核对日期：2026-09-05。

- [Text to Video](https://platform.vidu.cn/docs/text-to-video)
- [Image to Video](https://platform.vidu.com/docs/image-to-video)
- [Start End to Video](https://platform.vidu.com/docs/start-end-to-video)
- [Get Creation](https://platform.vidu.com/docs/get-generation)
- [Model Map](https://platform.vidu.com/docs/model-map)
- [Pricing](https://platform.vidu.com/docs/pricing)
