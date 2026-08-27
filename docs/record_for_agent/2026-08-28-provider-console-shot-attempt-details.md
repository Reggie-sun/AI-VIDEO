# Provider Console Shot Attempt Details Record

Date: 2026-08-28

## Purpose

本记录保存 Provider Console “每个生成视频可查看生成当时的 Shot 分镜、sealed Prompt、生成类型、
lifecycle 成功/失败与可播放媒体”这一 slice 的 durable implementation boundary 与验证证据。

它记录的是本机只读 observer 已实现并验证的行为，不授权 Provider submit、poll、retry、recovery、
Manifest mutation、candidate activation、QA acceptance、publish 或 release。

## Current Runtime Truth

- `src/ai_video/provider_console.py` 继续通过 canonical Project、Manifest、Registry 与 request receipt
  readers 投影本机 `runs/`，不成为新的 Production state owner。
- 每个 Production `video_generation` attempt 现在独立投影 sealed Prompt、`T2V` / `I2V` / `R2V` /
  `FL2V`、target Shot identity、normalized lifecycle outcome、raw phase 与安全 `error_code`。
- “生成当时的 Shot”只在 sealed request 的 `base_project` / `base_registry` 与 Manifest attempt
  pointers 相等，且 ID、revision、content hash 与 snapshot bytes 全部严格匹配时标记为
  `verified`。显式 `unavailable` 不得回退到当前 active Shot。
- Shot storyboard 白名单包含 Scene、Storyboard beat、intent、dialogue、narration、characters、
  continuity constraints、visual strategy、duration、motion directives 与 generated-video rationale。
- strict fetched video 与 Registry candidate 分层展示。`failed + fetched_media` 可以播放供人工判断，
  但仍显示为失败且不表示 candidate、QA acceptance、activation 或 delivery。
- 当前 schema 没有通用 cinematic `shot_type`。界面分别显示结构化 `visual_strategy` 与
  request-derived generation type，不从 Prompt 猜测景别或运镜，也不把一个 Prompt 内的文本段落
  伪造为新的 structured Shots。

## Session Work And Decisions

- `provider-console/src/App.jsx` 与 `provider-console/src/styles.css` 增加 attempt rail、Shot storyboard、
  Prompt/input、fetched/candidate media 和 lifecycle proof-layer 展示，同时保持既有中文 Provider
  Console layout。
- `provider-console/src/run-detail-contract.js` 集中处理 outcome、generation type、Shot snapshot
  fail-closed fallback 与媒体状态文案；显式 `failed`、`interrupted`、`outcome_unknown`、`running`
  不再由 phase 模糊推断。
- `src/ai_video/provider_console.py` 从 `ResolvedVideoGenerationRequest.activation_scope.request`
  读取 original sealed request，并在 active Shot fast path 之前校验 sealed base pointers。
- Browser 只接收已知 `ErrorCode`；其它 Manifest string 统一投影为 `unclassified_failure`，raw
  `error_message` 与潜在路径/secret 文本继续禁止进入 public JSON。
- 对 validate 后失败但已 fetch 的 MP4，local API 只在 canonical receipt、canonical artifact path、
  no-follow containment、SHA-256、size 与 MIME 全部匹配时签发 opaque media token。

## Verification And Evidence

Executable verification：

- `PYTHONPATH=src python -m pytest -p no:cacheprovider tests/test_provider_console.py -q`：
  `32 passed`。
- `node --test provider-console/tests/runs-api.test.mjs`：`11 passed`。
- `npm --prefix provider-console run test:continuity`：`15 passed`。
- `npm --prefix provider-console run test:sites`：`5 passed`。
- `npm --prefix provider-console run build`：Vite production build 与 Sites packaging 通过。
- `git diff --check`：通过。

真实本机 read-only projection：

- workspace：`runs/shot-continuity-rainy-station-p0-20260826-v9/production/project.yaml`。
- 7 个 video-generation attempts 均投影为 `shot_snapshot_status=verified`；其中历史
  `rainy-station-3` revision 2 与 `rainy-station-4` revision 1 均由 sealed base snapshots 严格重开。
- 3 个 `failed / polling` attempt 没有媒体；3 个 `failed / validate` attempt 显示 strict
  `fetched_media` 且没有 `candidate_media`；1 个 `succeeded / activate` attempt 显示 Registry
  candidate。proof layers 未合并。
- Chrome integrated QA 在失败的
  `rainy-station-m0-quality-v1-layout-repair-20260827-v6` 上确认 historical Shot、完整 sealed Prompt、
  FL2V inputs、`video_provider_failed` 与 fetched video 同屏；MP4 `readyState=4`、duration
  `5.166667s`，实际播放时间从 `0` 前进到 `0.482655s`，无 media error。
- Chrome console 没有 warning/error/issue；该回归涉及的 43 个 local requests 均为 `200` 或合法
  byte-range `206`。
- `runs/` exact file-content digest 在浏览器 QA 前后保持
  `01f09f4c876a5be887d6b085f0e74f631cc47fde0e223771e13205a86c734931`；本轮没有生成媒体、
  Provider call、云端请求或 Production state write。

Independent native `reviewer_xhigh` 首轮发现 historical base-pointer、explicit-unavailable fallback 与
unsafe `error_code` 三个 blocking defects；修复并补 regression tests 后 scoped re-review verdict 为
`accept`，无 remaining material concern。

## Assessment

该 slice 已满足“逐生成视频查看用于判断的详细信息”这一工程目标：操作员能在一个真实 attempt 视图中
同时看到生成时的 structured Shot、exact request Prompt、输入素材、生成类型、成功/失败、phase、
安全错误码与实际可播放视频，并能区分 fetched bytes 与 registered candidate。

这仍是 evidence observer，不是质量裁决系统。lifecycle `succeeded` 不等于 P6、Final Acceptance 或
human visual PASS；同样，`failed` 但存在 fetched video 只表示已有 exact bytes 可供判断。

## Remaining Risks Or Next Work

- Legacy `0.1.x` Manifest 没有封存可严格恢复的 historical Prompt/Shot snapshot；本 slice 不通过读取
  当前 ShotList 或解析文本来冒充历史 truth。
- 一个 Provider Prompt 可以包含多个文本镜头描述，但当前 request 只绑定一个 canonical target Shot。
  若产品未来需要内部多镜头结构化拆分，应先新增 provider-neutral sealed schema 与 migration，而不是
  在前端启发式解析 Prompt。
- 本轮未执行新的 Provider、paid/cloud、media generation、P6 或 Final Acceptance；也未发布或部署。

## Agent Guardrails

- `shot_snapshot_status=unavailable` 必须 fail closed；不得用 current active Shot 补齐历史分镜。
- `fetched_media`、`candidate_media`、lifecycle success、QA acceptance 与 activation 必须保持独立。
- `error_code` 只允许已知 stable identifier 或 `unclassified_failure`；不得暴露 raw message、path、
  traceback、Provider payload 或 secret。
- Provider Console 保持 loopback、read-only、local-only；任何 mutation、Provider submit 或自动重试均
  属于新的授权范围。
- 本记录与实现仅形成 local Git checkpoint；没有 push、deploy 或 release。
