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

## External Media Library Follow-up — 2026-08-28

同一用户判断目标后来扩展到 `runs/` 之外的三类历史视频位置：repository `artifacts/`、本机
ComfyUI output 与 repository 外青颜项目目录。实现没有把这些异构目录伪装成额外 `runs` root，也没有
导入、移动、删除或激活媒体；`/api/runs*` 的 canonical projection 保持不变，新增的是平行的 local-only
External Media Library。

当前实现边界：

- `provider-console/scripts/external-media.mjs` 对 server allowlist root 做 bounded、no-follow 扫描，
  只接受 regular video，重新测量 exact SHA-256，并把相同 bytes 聚合为一个 group，同时保留所有
  source-relative physical locations。
- `provider-console/scripts/runs-api.mjs` 使用 source-qualified opaque token；Browser 不能提交 arbitrary
  filesystem root，也收不到 absolute path。media 与 JSON sidecar 均通过 `O_NOFOLLOW` fd、realpath、
  root containment 和 file identity 检查；播放前还会重验 exact media SHA/size，支持 `HEAD` 与 byte range。
- Generic metadata 只有声明 `ai-video-external-media-metadata/1` 且直接绑定 exact path/SHA 时才解释。
  未知 schema 即使绑定 exact bytes，也只保留 evidence ref，不解释通用 `type`、`state`、`status` 或
  `prompt`。
- 青颜历史证据使用独立 cross-fingerprint adapter：`result.json` 的 exact media SHA 必须与
  `fetch_receipt.json` 一致，observation/submit fingerprints、resolved hash、generation ID、Shot、seed、
  Prompt、mode 与 state 必须全部存在并相互匹配。任一 linkage 缺失都 fail closed。
- External `reported_status` 与 canonical `status`、`generation_status`、`lifecycle_status` 分离；后三者固定
  `NOT_EVALUATED`。External `succeeded` 不产生 candidate、QA、P6、Final Acceptance 或 activation truth。

本机 live catalog 证据：

- 3 个 allowlisted sources 全部 available；485 个 physical video locations 聚合为 392 个 unique SHA groups。
- 7 个青颜 groups 通过完整 evidence chain，显示 full Prompt、Shot ID、`text_to_video` 与 external
  `succeeded`；其 canonical lifecycle 仍为 `NOT_EVALUATED`。
- 其它没有受支持 schema/完整 chain 的视频仍可按 exact bytes 播放、搜索、查看 duplicate locations，
  但 Prompt、Shot type 与成功/失败保持 `NOT_EVALUATED`，不从文件名或目录邻近关系猜测。
- Chrome fresh reload 验证 source filters、搜索、video preview、non-canonical boundary 与 runs/external
  切换；console 无 warning/error/issue，observed requests 均为本机 `200` 或合法 `206`，public payload
  不含 `/home/reggie`。

Implementation commit：`792d8a88bbe3658eea66b638f7a80b86d8e36dd8`。

Exact commit-range Harness：

- range：`63113d3cb19200172540476ff4941b8befedb7b1..792d8a88bbe3658eea66b638f7a80b86d8e36dd8`；
- receipt：`.agent/harness/runs/provider-console-external-media-20260828/receipt.json`；
- receipt verification：`passed=true`、`fresh=true`、`snapshot_matches=true`、
  `scope_worktree_clean=true`、`complete_completion_proof=true`；
- Harness 内 `193` tests、Provider Console Python `32` tests、Node `29` tests、Vite/Sites builds 与
  Sites `5` tests 全部通过；Architecture Gate 为 PASS。

四个媒体 root 在一次完整 live catalog scan 前后的 file type/path/size/mtime tree digests 分别一致；
该检查证明本次 observer scan 没有改变这些 trees，不等于重新验收其中历史媒体的质量或 lifecycle。

Independent native `reviewer_xhigh` 首轮指出 cross-fingerprint 字段双方同时缺失时可能因
`undefined === undefined` 错误通过，以及 generic JSON 字段存在语义误读风险。实现改为所有 chain
identity 非空且相等，并为 generic metadata 增加 schema gate；scoped re-review verdict 为 `accept`，
无 blocking issue。

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
- External catalog 当前每次 refresh 都重新 hash 视频，并以 media × bounded sidecar 方式读取证据；本机
  485 个 locations 实测约 3.3–3.5 秒。未来若规模增长，应建立单次 sidecar index 与 in-flight scan
  合并，但缓存不得降低 exact-byte revalidation。
- 达到 scan limits 或遇到不可读子目录时，目前不会向 UI 投影精确 `truncated/skipped` count；当前三个
  source 未触发已知限制，但后续要声称“完整覆盖”前应补该可观察性。

## Agent Guardrails

- `shot_snapshot_status=unavailable` 必须 fail closed；不得用 current active Shot 补齐历史分镜。
- `fetched_media`、`candidate_media`、lifecycle success、QA acceptance 与 activation 必须保持独立。
- `error_code` 只允许已知 stable identifier 或 `unclassified_failure`；不得暴露 raw message、path、
  traceback、Provider payload 或 secret。
- Provider Console 保持 loopback、read-only、local-only；任何 mutation、Provider submit 或自动重试均
  属于新的授权范围。
- External `reported_status` 只能来自受支持 schema 或完整 verified chain；不得从文件存在、filename、
  unknown JSON schema 或 review/gate state 推导生成成功/失败。
- 本记录与实现仅形成 local Git checkpoint；没有 push、deploy 或 release。
