# AI-VIDEO Provider Console Runs Integration Specification

## Status

Accepted for implementation。用户已明确要求现有中文 Provider Console 不再停留在静态 demo，
而是只读接入 repository `runs/` 中的真实 Project、Shot、Provider attempt、artifact 与 evidence。

本 Spec 不授权 Provider submit、poll、fetch、recovery、candidate activation、Manifest write、
QualityExperienceRecord capture、云端访问、secret lookup、自动选路或 fallback。

## Goal

把 `provider-console/` 从硬编码 Alice/Shot 12 的视觉原型升级为 local-only、no-network、
read-only observer：操作员可以选择 `runs/` 中的真实 Production workspace，查看其 canonical
Project、Shot、video generation attempt、Provider/profile/capability、输入首帧、输出媒体和 exact
evidence pointers。

## Problem Boundary

当前 UI 的 `LANES`、Project、Shot、时间、能力和 evidence 全部来自 `App.jsx` 常量；“查看证据”
只展示原型文本。因此 UI 即使视觉正确，也没有消费 `runs/` runtime truth。

需要替换的旧路径是这些静态 constants 与仅更新 React state 的“使用 Provider”行为。设计外壳、
中文信息架构和手动选择/不自动 fallback 的可视语义保留。

## Owners And Dependency Direction

- Production state owner 不变：`ProductionManifest` 与 `ProductionStateCommitter`。
- strict read owner 不变：`load_production_project(project.yaml)`；Legacy root manifest 使用
  `load_manifest(manifest.json)`。
- 新 `ai_video.provider_console` 只拥有 sanitized read projection；它不得写 `runs/`，不得调用
  committer、Provider、recovery、analyzer、Quality Intelligence store 或 Agent control plane。
- `provider-console/scripts/runs-api.mjs` 只把 loopback Vite `GET/HEAD` 请求桥接到 Python projector，
  并按 projector 生成的 opaque media token 提供已验证的 image/video bytes。
- Browser 只消费 sanitized JSON 与 media URLs，不读取任意 filesystem path。

## Discovery Contract

`runs/` discovery 必须 bounded、deterministic、no-follow：

- root 必须是 caller 显式提供、存在且可解析的 directory；默认只由 local Vite bridge 传入
  repository `runs/`。
- Production workspace 是 `runs/**/project.yaml` 且同目录存在 `state/manifest.json`；最多扫描
  256 个 workspaces、relative depth 最多 6。
- Legacy workspace 只接受 `runs/<run_id>/manifest.json`，不把 Production `state/manifest.json`
  当成 Legacy。
- symlink、absolute relative key、`..`、越界、非 regular file、重复 workspace key 全部拒绝或作为
  typed invalid entry 隔离，不能 follow。
- catalog 按 manifest/project mtime 降序，再按 workspace key 排序；列表阶段不声称 Project 已 strict
  reopen。

## Selected Workspace Contract

选择 Production workspace 后必须调用 `load_production_project()` 完成 selected Project、Manifest、
Registry、dependency、Provider evidence 与 registered bytes 的现有 strict reopen。失败时返回 sanitized
`invalid` 状态和稳定错误码/消息，不 fallback 到裸 YAML/JSON truth。

成功 projection 只允许：

- run/workspace relative identity、Project ID/title/revision、Manifest revision、updated time；
- Shot ID、intent、visual strategy、duration、Scene identity；
- ordered `video_generation` attempts 的 attempt ID/status/phase/timestamps；
- 通过 `load_video_request_receipt()` reopen 的 target Shot、Provider name/kind、model、profile、
  capability、execution/billing kind、mode、effective output、continuity role 与 hashes；
- Manifest pointer paths、file/content hashes、Registry asset identity、MIME、bytes、measured dimensions/
  fps/frame count/duration、egress remote bool；
- registered first-frame/image 与 generated video 的 opaque media token。

禁止把 raw prompt/negative prompt、Provider response、signed URL、credential、absolute path、raw error
traceback 或 arbitrary evidence JSON 返回 Browser。

## Local API Contract

- `GET /api/runs`：返回 bounded catalog 与 read-only/local-only boundary。
- `GET /api/runs/detail?workspace=<relative-key>`：返回一个 strict-selected workspace projection。
- `GET|HEAD /api/runs/media/<opaque-token>`：只返回本进程已缓存、已由 selected Registry 验证的
  `image/*` 或 `video/*` regular bytes；支持 video byte range。
- 其它 method 返回 `405`；unknown workspace/token 返回 `404`；invalid input 返回 `400`。
- API 必须发送 `Cache-Control: no-store`，不得监听或调用 remote Provider。Sites/static deployment 没有
  local filesystem 时显示“本地 runs 数据源不可用”，不得注入 build-time runtime snapshot。

## UI Contract

- 初始加载真实 catalog；默认选择最新可加载 workspace，而非静态 Alice record。
- 保留 Provider Console layout；增加 workspace selector 与 refresh。
- lane rail 展示 selected workspace 中真实 video generation attempts。没有 attempt 时显示明确 empty
  state；不得补造 Local H3/Hailuo/Seedance lanes。
- 选择 lane 后，header、Shot、Provider、capability、readiness/evidence、首帧和 output media 全部来自
  projection。
- 主 CTA 改为只读动作（查看输出/证据）；不得生成持久化意图或暗示已授权执行。
- loading、invalid workspace、API unavailable、empty attempts 和 media unavailable 都必须有中文状态。

## Unchanged Contracts

Legacy CLI、Manifest schema/layout、Production models、Registry、StateCommitter、Planner、Readiness、
Router、Provider、P6/P7、QualityExperienceRecord、ResolvedTimeline、HyperFrames、paid/cloud/secret gates
全部不变。`runs/` bytes 与 mtimes 在 catalog、detail、media 和 browser QA 前后必须保持不变。

## Acceptance Criteria

1. 页面能列出当前真实 `runs/` workspaces，并切换至少一个 Local H3 与一个 Seedance/Hailuo workspace。
2. selected detail 的 Project/Shot/Provider/output 与 exact Manifest/request/Registry evidence 一致。
3. 首帧或 registered image、generated video 可以从 local media endpoint 预览。
4. invalid historical workspace fail closed，不回退到 hard-coded demo data。
5. API 只接受 GET/HEAD；path traversal、symlink、unknown token、raw prompt/secret exposure tests 通过。
6. focused Python/Node tests、frontend build、Chrome integrated QA 与 exact Harness receipt 通过。
7. 验证前后 `runs/` tree snapshot无写入变化；无 Provider/network call。

## Out Of Scope

Provider selection mutation、submit/retry/recovery、Quality dataset UI、跨机器 run registry、database、queue、
authentication、remote deployment读取本机 `runs/`、编辑 evidence、删除/修复历史 run。
