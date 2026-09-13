# Vidu Whole-Ad Source API

## Scope

接入 Vidu 官方 `POST https://api.vidu.cn/ent/v2/ad-one-click` 的创建、查询和下载。
这是 whole-ad 服务，不是可选择底层 Q3 模型的接口，也不是 WaveSpeedAI `vidu/q3-ad`。
官方请求没有 `model`；内部 `model_id=ad-one-click` 仅用于绑定服务与付费证据。
参考：[官方接口文档](https://platform.vidu.cn/docs/one-click-ad-film)。

输入为 1–7 张已注册图片、最多 2000 字提示词、8–60 秒、`1:1/16:9/9:16`、
`zh/en` 和显式 `creative`。输入图片顺序保持不变，首图应为商品图；无图片 URL
抓取旁路，只发送验证后的原始 bytes 的 data URI。完整请求不超过 20 MiB。

输出为 `AdSourceCandidate`，只有 content-addressed bytes 和下载来源证据。
`acceptance=not_evaluated` 不可变。没有自动 Registry import、Shot activation、
timeline、render 或 P6/Final Acceptance；不会把服务端内部镜头伪装为已通过逐镜 Gate。
该服务内的批量镜头不能用于宣称完成现有 sequential Shot workflow。
媒体 probe、功能真实性、车辆一致性、中文文字与 whole-ad 质量仍需后续标准流程验证。
本次不包含编辑、重新合成、自动重试、第三方 Provider、CLI 或 live generation。

## API

`ViduAdProviderProfile` 复用 Vidu 的 operator ceiling 和下载信任配置，但具有独立
`service=ad-one-click` identity，只允许国内官方 endpoint。须由 operator 配置一个
覆盖整次 create 的有限上限；本实现不查询价格、不用积分数猜测货币金额，也不自动结算。
凭证继续由 injected supplier 读取 `secret_store / VIDU_API_KEY`，不得写入输入或文件。

调用流程（`loaded` 必须来自 `load_production_project`，图片必须来自该 Registry）：

```python
from ai_video.production.vidu import ViduVideoProvider
from ai_video.production.vidu_ad_contracts import AdGenerationRequest, AdImageBinding

# profile is a sealed ViduAdProviderProfile supplied by the operator.
# transport is the existing HttpxViduTransport; supplier returns a secret in memory.
provider = ViduVideoProvider(
    profile=profile, transport=transport, credential=credential_supplier,
    image_resolver=registered_image_bytes,
)
request = AdGenerationRequest.create(
    task_id="haokou-ad", submit_limit=1,
    project_id=loaded.manifest.project_id,
    project_hash=loaded.manifest.active_project.content_hash,
    registry_hash=loaded.manifest.active_registry.content_hash,
    profile_hash=profile.pointer().profile_sha256,
    images=tuple(AdImageBinding(
        asset_id=a.asset_id, sha256=a.sha256, size_bytes=a.size_bytes,
        mime_type=a.mime_type, width=a.width, height=a.height,
    ) for a in selected_registered_images),
    prompt=approved_ad_prompt, duration=28, aspect_ratio="9:16",
    language="zh", creative=False, policy_id="haokou-ad-policy",
    expires_at=task_expiry,
)
committer.prepare_ad_generation(attempt_id="haokou-ad-01", request=request, provider=provider)
# The committer must have a task-specific paid_provider_authorizer and clock.
task_id = committer.submit_ad_generation(attempt_id="haokou-ad-01", provider=provider)
state = committer.query_ad_generation(attempt_id="haokou-ad-01", provider=provider)
# Query again explicitly later if not complete; no internal polling or retry.
if state.observation == "success":
    candidate = committer.fetch_ad_generation(attempt_id="haokou-ad-01", provider=provider)
    source_path = loaded.root / candidate.path
```

## Ownership And Recovery

所有 durable writes 都经过 `ProductionStateCommitter`。准备阶段无网络；提交前重新验证
selected project/Registry、图片 bytes、profile、task ceiling、request expiry、预算和 egress。
授权中的 actor、exact preview 与凭证 reference 继续由现有 paid Gate 保存。
首次 task scope 固定 `submit_limit` 和 policy；不能用新 attempt 改高上限。每个已签发
submit intent 保守计入一次尝试，明确拒绝也不自动回收次数；新 task 需要新的显式授权。

提交返回已知 task ID 后，重启再次调用 `submit_ad_generation` 只返回原 ID，不再 POST。
超时、畸形响应或中断后遗留 intent 必须 fail closed；`recover()` 使用现有 paid recovery
记录 `outcome_unknown`，不会重新签 permit。已接受但服务端失败的请求保留消费证据。
durable intent 之后的 credential lookup 等异常也保守记为 `outcome_unknown`，即使
本地没有观察到 POST；预算保留且禁止自动重提。当前广告路径没有受支持的
reconciliation 或恢复提交入口，unknown 只能封存并保持阻断；既有 paid video
reconciliation 不适用于广告，不能仅恢复 credential 就重试。
query/fetch 只使用已持久保存的 task ID，验证唯一 creation；下载前后确认同一 creation。
签名 URL 只留在内存，原始 URL 和凭证不写文件。下载沿现有 pinned public HTTPS transport。
fetch 失败后允许显式重试取回同一已知 task，不重新生成；完整未选中 bytes 保留为孤立证据。

## Compatibility And Verification

Manifest 2.16 增加可选 `StateCommitAttempt.ad_generation_state`，仅新 ad prepare 升级。
旧 manifests 不含该字段时保持原版本和序列化，旧版本显式传该字段（含 null）拒绝。
没有默认 Provider、单 Shot 路径、Registry、timeline、renderer 或 acceptance owner 变更。

Focused tests：

```bash
python -m pytest -p no:cacheprovider tests/test_production_vidu_ad_wire.py tests/test_production_vidu_ad_generation.py tests/test_production_vidu_ad_lifecycle.py -q
```

Harness `vidu_ad_source` 按真实 changed paths 路由这些测试及既有 Provider、paid/state、
Architecture 验证。Fake transport 证明协议及状态处理，不证明真实账户或成片质量。
