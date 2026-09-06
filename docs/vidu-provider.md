# Vidu Video Provider

## Scope

`ai_video.production.vidu.ViduVideoProvider` 是显式注入的 optional video Provider，
通过既有 `VideoProviderRegistry` / `VideoGenerationService` 使用。
支持 `viduq3-pro`、`viduq3-turbo` 的 T2V、单 `first_frame` I2V，以及
`first_frame + last_frame` 首尾帧模式。另外支持 `viduq3`、`viduq3-turbo` 的
R2V／多主体图片参考，以及 `viduq2-pro`、`viduq2-turbo` 的 `VIDEO_EXTEND`。
R2V 的官方模型 ID 是 `viduq3`，不将 `viduq3-pro` 静默改名；Q3 不声明延长能力。
主体库管理、命名 `subjects`、视频参考编辑和自动选路不属于本次接入。

## Configuration

创建 `ViduProviderProfile` 时必须提供 official `origin`（`https://api.vidu.cn`
或 `https://api.vidu.com`）、显式下载信任配置、
`cost_upper_bound_microunits`、timezone-aware `pricing_observed_at` 与
`pricing_expires_at`。费用字段是覆盖所使用模型和请求的 operator per-call ceiling，
不是内置报价；国内站使用 CNY，国际站使用 USD。过期 ceiling 在 preview 阶段拒绝。
不要把测试 CDN、示例费用或历史报价直接用于真实调用。

已授权任务可以按 [Operator Ceiling Renewal](../.agent/context/control-plane-playbook.md#operator-ceiling-renewal)
重新确认既有内部上限，创建新 profile 与新请求。这里的 `pricing_observed_at` /
`pricing_expires_at` 是 dated operator ceiling 的有效窗口，不要求在线取得官方报价。
续期须保存真实决定及旧/新 hash 的证据，不能覆盖历史 profile 或改变旧提交的恢复绑定。
Runtime 仍拒绝过期 profile；该流程没有改变 schema 或取消 freshness 校验。

首次接入可显式设置 `result_trust="authenticated_task"`，此时 `result_origins` 必须为空
（可以省略）。下载 URL 只来自 official API 对 exact task 的认证查询，并在 fetch 时
重新验证同一 creation；无需先生成历史任务来发现 CDN。该模式进入 profile hash。
默认 `result_trust="fixed_origins"` 继续要求非空 exact `result_origins`；旧 profile 的
序列化 bytes/hash 保持兼容。两种模式不可混用，切换模式需新的 profile/request，不能
替换历史 submission 的 profile 来恢复下载。

```python
from ai_video.production.vidu import HttpxViduTransport, ViduVideoProvider
from ai_video.production.video import VideoProviderRegistry

# profile contains a dated operator ceiling and an explicit result trust policy.
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

## Reference To Video

`mode=REFERENCE_TO_VIDEO` 使用 `/ent/v2/reference2video` 的非主体调用 `images` 路径。
支持 1–7 张 `role=reference` 的图片，按 request 的 canonical asset ID 顺序发送，
多个角色／主体可以各有参考图；不把两张参考图误发到首尾帧 endpoint。
图片至少 128×128，单张保守限制为 10,000,000 bytes（兼容两站限制），
比例严格介于 1:4 与 4:1，prompt 最多 2000 字符；
Q3 R2V 时长为 3–16 秒，ratio 为 16:9、9:16、1:1，使用 exact geometry。
`native_audio` 显式选择，视频／音频 reference 不会被静默丢弃或改为图片。

## Video Extension

`mode=VIDEO_EXTEND` 使用 `/ent/v2/extend`。当前接入已下载、测量并注册的 Vidu
无声视频，绑定一个 `VideoMediaReferenceBinding(kind=video, role=reference_video)`；
原视频为 4–60 秒的整秒、24 fps MP4，可额外绑定一张 `last_frame`，prompt 最多 2000 字符。
Output 使用 adaptive geometry、540p/720p/1080p、`native_audio=False`，不支持 seed。
这里 `output_requirement.duration_seconds` 表示期望完整输出长度，HTTP `duration`
表示新增长度：完整长度减去 source measured duration，必须为 1–7 秒。
例如 5 秒原片延长 4 秒，output 写 9，HTTP 写 4；adapter 不做剪切或第二套 timeline。
实际服务是否返回符合这一完整输出约定的媒体，仍需 live probe 验证，不能由离线 payload
测试证明；若产物长度、音轨或其他测量不符，既有 artifact gate 拒绝，不自动修剪或接受。

调用方注入 `extension_source(binding) -> ViduExtensionSource`，从 canonical state
重开同一 profile 下的 `submission`、`submit_receipt`、`fetch_receipt`、`probe_receipt`。
`vidu_source.py` 只验证这些 receipts 的 seal、相互绑定及 source SHA/size/duration/
geometry/FPS，不写 state，也不替代 Registry loader 或证明 candidate activation。
Adapter 在付费 POST 前查询原 task，要求当前成功 creation 仍对应 fetch receipt 的
opaque file ID，再通过现有受限 fetch 流式重验远端完整 SHA/size，丢弃字节而不落盘，
全部一致后发送 `video_creation_id`。普通 reference 不自动等于连续镜头验收；
顺序连续生成仍必须由现有 continuity、Registry、Per-Shot Gate owners 验证。
Source video 的 exact SHA/size/MIME 也必须包含在 paid egress preview 中，purpose 为
`reference`，即使该素材由 Provider 内部复用；未知／变更 source 在 POST 和 permit 消费前拒绝。
Source 查询与素材/secret supplier 返回后、permit 消费前，重新核验 authorization 和报价有效期。
本次不实现任意外部 `video_url` 上传、无凭证 creation ID 或有声源视频延长。
历史 profile ID/version 保持兼容，新增能力使用独立 capability ID，不重写旧 receipt。

## Lifecycle And Verification

`submit` 只在 durable paid permit 消费后执行一次 POST。超时、无法解释的响应和
非明确拒绝均为 unknown outcome，必须沿既有 explicit recovery 处理。
查询通过 exact task URL，若响应带 task/model 字段则复核；下载时重新查询同一 task，
要求同一 creation ID。`fixed_origins` 额外验证 sealed origin；`authenticated_task`
信任此次 official task response 的 locator，不接受外部传入的任意下载链接。

`vidu_download.py` 独占结果 HTTPS transport：解析后的所有 DNS 地址必须是 public
unicast，拒绝内网、loopback、link-local、CGNAT、保留地址与 IPv6 transition 地址。
直接连接已验证的数值 IP，TLS SNI 与证书核验使用原域名，不再次解析域名，不走环境
proxy、不继承 API client 的 auth/cookie/header，不跟随重定向、不自动解压或重试。
固定白名单模式也使用同一安全下载路径。部署网络须支持直接访问真实 public 地址；
返回 Fake-IP 的 DNS 会被拒绝，不能通过关闭地址校验处理。
字节上限、HTTP/MIME/MP4 header、完整长度与 SHA-256 检查仍由 adapter 负责，媒体
测量和 acceptance 仍由既有 downstream owners 负责。
URL 仅在内存中使用；新模式的 fetch receipt 嵌入既有 `RemoteMediaMaterializationReceipt`，
绑定 origin、locator SHA-256、task/file identity 与实际下载 SHA/size，不保存完整 signed URL。

离线测试：`python -m pytest -p no:cacheprovider tests/test_production_vidu.py tests/test_production_vidu_download.py -q`。
本次实现不表示 credential/access、live submit、真实媒体质量或 P6 / Final Acceptance
已验证；也不自动 activation、retry、切换其他 Provider。

## Official References

核对日期：2026-09-05。

- [Text to Video](https://platform.vidu.cn/docs/text-to-video)
- [Image to Video](https://platform.vidu.com/docs/image-to-video)
- [Start End to Video](https://platform.vidu.com/docs/start-end-to-video)
- [Reference to Video](https://platform.vidu.cn/docs/reference-to-video)
- [Video Extension](https://platform.vidu.cn/docs/video-extension)
- [Get Creation](https://platform.vidu.com/docs/get-generation)
- [Model Map](https://platform.vidu.com/docs/model-map)
- [Pricing](https://platform.vidu.com/docs/pricing)
