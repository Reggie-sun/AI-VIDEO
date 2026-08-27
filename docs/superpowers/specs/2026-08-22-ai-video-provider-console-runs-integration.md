# AI-VIDEO Provider Console Runs Integration Specification

## Status

Accepted for implementation。用户已明确要求现有中文 Provider Console 不再停留在静态 demo，
而是只读接入 repository `runs/` 中的真实 Project、Shot、Provider attempt、artifact 与 evidence。

本 Spec 不授权 Provider submit、poll、fetch、recovery、candidate activation、Manifest write、
QualityExperienceRecord capture、云端访问、secret lookup、自动选路或 fallback。

2026-08-28 detail follow-up：用户要求每个真实生成视频都能直接看到生成当时的 Shot 分镜、
sealed prompt、生成类型与成功/失败状态，以便人工判断。该 follow-up 只扩展 strict read projection
和 Browser 展示；不改变 Production lifecycle、candidate、QA acceptance 或 activation truth。

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
- Legacy workspace 接受 canonical `runs/<run_id>/manifest.json`，并兼容已存在的
  `runs/<capture>/output/<attempt>/manifest.json` 历史布局；不得把 Production
  `state/manifest.json` 当成 Legacy。
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
  capability、execution/billing kind、mode、sealed `prompt_text`、effective output、continuity role 与 hashes；
- attempt 必须投影 sealed `target_shot_revision` 与 `target_shot_content_hash`。只有 current active Shot
  已与 sealed ID/revision/content hash 完全匹配，或从该 attempt 的 canonical base Project 严格重开并
  完全匹配时，才能作为 `shot_snapshot`；不匹配的 current active Shot 不能代替生成当时的 Shot。
  无法严格重开时必须显式返回 unavailable binding；
- verified `shot_snapshot` 可以白名单投影 `storyboard_beat_id`、`dialogue`、`narration`、
  `character_ids`、`continuity_constraints`、`motion_directives` 与 `generated_video_rationale`；
- ordered image/media bindings 的 role、registered asset identity 与 opaque media token；Browser 显示的
  `T2V / I2V / R2V / FL2V` 必须由 canonical mode + binding roles 推导，其中 FL2V 是
  `image_to_video + first_frame + last_frame`，不得按 Provider/model 名称猜测；
- Manifest pointer paths、file/content hashes、Registry asset identity、MIME、bytes、measured dimensions/
  fps/frame count/duration、egress remote bool；
- registered first-frame/image 与 generated video 的 opaque media token。
- 若 attempt 已经有 strict remote/local fetch receipt，但还没有 Registry candidate，允许单独投影
  `fetched_media` opaque token。它只证明 exact fetched bytes 可播放，不表示 candidate、QA acceptance、
  activation 或 delivery；不得把它合并或改名为 `candidate_media`；
- attempt failure 只允许投影稳定的 `error_code`；raw `error_message`、traceback 与 Provider payload
  继续禁止返回 Browser。
- bounded Manifest operation counts，以及最多 32 个 canonical Registry 中已验证的
  `image/*` / `video/*` workspace media；它们只表示 workspace 内容，不得暗示绑定到某个 attempt。

禁止把 effective negative prompt、Provider response、signed URL、credential、absolute path、raw error
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
- lane rail 展示 selected workspace 中真实 video generation attempts。没有 attempt 时必须明确显示
  “工作区已读取”，并继续展示 Project、Shots、Manifest operations 与 Registry media；不得补造
  Local H3/Hailuo/Seedance lanes，也不得把合法的非视频 workspace 表述为读取失败。
- 选择 lane 后，header、Shot、Provider、capability、readiness/evidence、首帧和 output media 全部来自
  projection。
- Shot header 与 attempt rail 必须显示 `T2V / I2V / R2V / FL2V`。T2V 显示 sealed prompt；I2V 与
  R2V 显示 prompt 和全部已投影输入图片；FL2V 显示 prompt、首帧和尾帧。若 R2V 包含 registered
  reference video，则按其 exact binding role 显示，不得伪装成 image。
- attempt rail 必须同时显示 target Shot、normalized lifecycle outcome、raw phase、生成类型、媒体状态与
  prompt 摘要；`phase` 不能遮住 `succeeded / failed / interrupted / outcome_unknown / running`。
- selected attempt 必须把“生成当时的 Shot 分镜”和“实际提交的 sealed Prompt”分开显示，并显式展示
  Scene、Storyboard beat、visual strategy、duration、intent、对白/旁白、角色、continuity 与 motion
  directives（存在时）。一个 Prompt 可以包含多个文本镜头描述，Browser 不得解析 Prompt 来伪造新的
  structured Shots；当前 schema 没有通用 cinematic `shot_type` 时，也不得猜测景别或运镜类型。
- lifecycle outcome、可播放 fetched bytes、registered candidate、QA acceptance 与 activation 是不同
  proof layer，必须分别表达。尤其 `failed + fetched_media` 仍应允许人工播放，但不能显示为成功或已验收。
- 主 CTA 改为只读动作（查看输出/证据）；不得生成持久化意图或暗示已授权执行。
- loading、invalid workspace、API unavailable、empty attempts 和 media unavailable 都必须有中文状态。

## Unchanged Contracts

Legacy CLI、Manifest schema/layout、Production models、Registry、StateCommitter、Planner、Readiness、
Router、Provider、P6/P7、QualityExperienceRecord、ResolvedTimeline、HyperFrames、paid/cloud/secret gates
全部不变。`runs/` bytes 与 mtimes 在 catalog、detail、media 和 browser QA 前后必须保持不变。

## Acceptance Criteria

1. 页面能列出当前真实 `runs/` workspaces，并切换至少一个 Local H3 与一个 Seedance/Hailuo workspace。
2. selected detail 的 Project/Shot/Provider/output 与 exact Manifest/request/Registry evidence 一致。
3. 首帧或 registered image、candidate video，以及严格验证但尚未成为 candidate 的 fetched video，
   可以从 local media endpoint 预览，并保持各自 proof boundary。
4. invalid historical workspace fail closed，不回退到 hard-coded demo data。
5. API 只接受 GET/HEAD；path traversal、symlink、unknown token、negative prompt/secret exposure tests
   通过；sealed prompt 仅在 selected local detail 中按白名单返回。
6. focused Python/Node tests、frontend build、Chrome integrated QA 与 exact Harness receipt 通过。
7. 验证前后 `runs/` tree snapshot无写入变化；无 Provider/network call。
8. selected attempt 显示 exact-at-time Shot snapshot、完整 sealed prompt、generation type、normalized
   outcome、raw phase 与安全 `error_code`；历史 Shot 无法 strict reopen 时明确 unavailable，绝不回退
   到 current active Shot。

## Out Of Scope

Provider selection mutation、submit/retry/recovery、Quality dataset UI、跨机器 run registry、database、queue、
authentication、remote deployment读取本机 `runs/`、编辑 evidence、删除/修复历史 run。
