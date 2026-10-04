# METASO H3 Frame Conditioning Research

## Research Result

A. 当前 baseline `bf2c81d2bbd2d568a0da78d86b9d4184aacbd05d` 的
`metaso_h3.py` 只有 `metaso-h3-ref2va-v1`；resolve 固定 Ref2VA，native image
固定 `reference_image` 且总发送 ratio。缺口属于 adapter coverage。

B. 2026-10-05 重新读取 upstream main，exact commit
`0d1c72b1d80a54237b40adb111ae74d7fe38f4b4`。事实来自
[nodes.py](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API/blob/0d1c72b1d80a54237b40adb111ae74d7fe38f4b4/nodes.py#L128)
及 [api_client.py](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API/blob/0d1c72b1d80a54237b40adb111ae74d7fe38f4b4/api_client.py#L98)，不据此宣称 live 服务或媒体质量。

| Question | Exact upstream result |
| --- | --- |
| First frame | `image_url: {url: ...}`, `type=image_url`, `role=first_frame` |
| Last frame | 相同 schema，`role=last_frame`；optional，only first 合法 |
| Ordering | text → first → optional last |
| Model / endpoint | `MiniMax-H3` / `POST /v2/video_generation`；与 Ref2VA 同 endpoint，不同 roles |
| Duration / resolution | 节点整数 4–15 秒；`768P` / `2K` |
| Aspect ratio | 跟随输入图片；frame 节点传 `ratio=None`，client 省略该字段 |
| Seed | UI 接收，client 注释明确 v2 不发送；不得声明 seed support |
| Watermark | true 时发送 `aigc_watermark=true`；默认 false 时省略 |
| URL / data URI | URL 节点声明 public URL、`mm_file://`、data URI；本 adapter 保留 Registry exact bytes → data URI |
| Minimum / ratio | tensor 节点逐张验证宽高至少 256，ratio inclusive 0.4–2.5 |
| Pair geometry | 两张分别验证；未发现要求尺寸或比例相同。URL 节点也未声明 pair equality；server 更严格要求未经 live 验证 |

Snapshot 保存在 `runs/metaso-h3-frame-capability-20261005-001/upstream.json`；
`api_client.py` SHA256 `5f5343fd059a9d209984340b16f66870ff041a028800bdd0cce8fabdcd41748d`，
`nodes.py` SHA256 `c44321e21d6677586f94405d0299cf79139577f495a3afa7ba9a9b3493fb7d66`。
只读取公开源码，没有查询价格、凭据或发起 H3 effect。

C. 复用 `VideoCapabilityVariant.allowed_image_roles` / `required_first_frame`、
existing compiler 的 role ordering、`ResolvedVideoGenerationRequest.create`、Registry resolver、
remote prose compiler，以及现有 transport/preview/paid seam。一个 IMAGE_TO_VIDEO variant
即可覆盖 first-only 与 first+last，无需新增 mode、cardinality grammar 或 Provider。

D. 最小 implementation files：`production/metaso_h3.py`、
`tests/test_production_metaso_h3.py`；更新现有 Provider docs/runtime baseline，并新增本研究、
小 spec/plan 和独立 continuation record。

E. 不修改 sequence、policy、Planner、Router、source reopen、route authority、QA、
历史 S02/S03 及其 records；不修改 shared capability/helper，不新增 transport。

## Applicability

公开源码已证明 API input 表达方式，无需对 payload grammar 再做付费 A/B；
opening-state continuity 的 media-level 结论仍需要后续新的 accepted source 和真实实验。
新 variant 仅在 adaptive profile 下注册，保留旧固定 ratio Ref2VA 的全部 serialization。
既有 30 MiB、256–5760 bounds 继续作为 adapter 保守约束；frame bytes 不 crop/resize/transcode。

## Independent Compiler Boundary

集成检查发现 `_remote_video_native_prompt.py::_state_text` 仅表达 TYPED_TEXT，
TYPED_HASH/REFERENCE 返回 unsupported；而 sequence 的 accepted causal state 使用 TYPED_HASH。
这属于现有 native prose expression 的 fail-closed，不能把 opaque hash 伪装成 narrative truth。
本 slice 不修改 prompt architecture；Router fixture 使用完整 v4 text intent 验证 adapter coverage，
并单独验证 hash intent 在 compiler 前保持阻断。尚不能据此宣称 canonical typed sequence B 已可提交。

## Independent Mapping Receipt

受管 Kimi `e6b1bbb1-ccec-463a-a92b-f4437f6a7c74`，deep / `k3` / max，2 wire requests，
104.643 秒；canonical receipt、report hashes 与实际 Read hashes 已核验。
其结论支持 single optional-last variant 和未观察到 upstream pair equality。
Parent 根据源码采纳这两项，将 server pair behavior 保留为未验证，不新增 equality gate。
先前 `7d68d310-8520-427e-b52b-854476d153bf` 在 response body 断连，3 wire requests、
365.574 秒、OUTCOME_UNKNOWN；无 terminal report，partial 输出隔离，未用于结论。
