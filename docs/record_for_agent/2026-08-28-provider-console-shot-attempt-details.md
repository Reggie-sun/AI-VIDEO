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

前一 checkpoint 的本机 live catalog 证据（historical；后续数量由下方
`All-Video Shot And Audio Follow-up` 的新扫描取代）：

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

## All-Video Shot And Audio Follow-up — 2026-08-28

后续实现把“只看到一个视频或一个 attempt”的操作面扩展为完整 Shot 判断面，同时处理浏览器与主机
输出设备两层声音问题。该 follow-up 没有改变 Production lifecycle、`ResolvedTimeline`、activation、
Provider 或媒体 bytes。

当前界面行为：

- 启动后默认进入 External Media Library；来源改为一个可展开的 `<select>`，默认
  `全部外部来源`。`runs/` 继续作为独立 canonical Project 工作区入口，external selector 覆盖
  repository `artifacts/`、`/home/reggie/ComfyUI/output` 与 `/home/reggie/电商图片/青颜`。
- canonical Project 视图按 Project 当前 Shot 数组顺序展示全部 Shots；每个 Shot 下保留所有 attempts，
  并展示画面脚本、对白、旁白、`visual_strategy`、实际提交 Prompt、generation type、lifecycle
  outcome、phase 与媒体状态。找不到当前 Project Shot 的 attempt 会进入显式 unmatched 区域，不会丢弃。
- 每个 attempt 的脚本继续使用 exact-attempt snapshot；Project Shot 顺序明确不是最终成片的
  `ResolvedTimeline`，前端也不自动选择 winning attempt。
- External Media Library 只在受支持 schema 且 exact path/SHA evidence 完整时展示 Prompt、Shot、类型与
  external reported status；无法绑定的字段继续显示 `NOT_EVALUATED`。
- exact final SHA
  `94c6b7fc92202f6c7e979bb94b31ecd58aab40e3652113f1e78d66c3535a16a4` 可显示同目录
  `ecommerce-ad-workflow/package/2` 声明的 6 个 Shots。它只证明 final checksum 与同项目目录声明存在，
  因缺少 structured composition receipt，不证明 6 个 Shots 构成 exact MP4，也不升级 canonical
  timeline、candidate、QA、P6 或 Final Acceptance；每个 Shot 状态为
  `DECLARED_NOT_EVALUATED`。
- `AudibleVideo` 统一覆盖 external preview、candidate/fetched output、input video、Registry video 与
  Continuity Review；每个入口都有显式 `开启声音并播放`，在同一 user gesture 中设置
  `defaultMuted=false`、`muted=false`、`volume=1` 并调用 `play()`。独立媒体 HTML wrapper 同样执行该
  行为。若 exact 文件没有音轨，界面会明确提示，不能由输出设备绑定制造不存在的声音。

主机声音 runtime evidence：

- PipeWire default sink 当前解析为 node `56`：`HDA NVidia Digital Stereo (HDMI 2)`，对应桌面设置中的
  `HDMI / DisplayPort 2 - HDA Nvidia`；ALSA route 为 `hdmi-stereo-extra1`，设备 nick 为 `GX271UR`。
- 本轮重新执行 default-sink binding 与 unmute；当前 read-only observation 为 `Volume: 0.61` 且没有
  `[MUTED]`。短时 `speaker-test` 与系统测试音已送往该 sink；这证明 routing/action 已执行，不代替用户
  对显示器实际出声的听觉确认。

当前 live catalog 新扫描：

- `393` 个 unique SHA groups、`486` 个 physical locations；source locations 分别为 repository
  artifacts `192`、ComfyUI output `251`、青颜目录 `43`。
- `27` 个 groups 为 `verified_artifact_receipt`，`7` 个为 `verified_evidence_chain`，合计 `34` 个
  exact-bound structured evidence groups；其余 `359` 个保持 `not_evaluated`。
- public projection 未发现 absolute `/home/reggie`、`source_path` 或 `source_root` 泄露。

Verification：

- Node contract/API/UI tests：`35 passed`。
- Provider Console Python tests：`32 passed`。
- Vite production build 与 Sites packaging：通过。
- Chrome integrated QA：默认 all-sources selector、canonical multi-Shot/multi-attempt、external 6-Shot
  declaration、主视图与 HTML wrapper 的 user-gesture unmute/play 均验证通过；主页面无 console
  error/warning/issue。
- Implementation commit：`8d0282f3528b9101741ff23d78c965982e767f35`。
- Exact commit-range Harness：
  `49638b4d103ab0251bdcce5a052855a2bd315e91..8d0282f3528b9101741ff23d78c965982e767f35`；
  receipt：`.agent/harness/runs/provider-console-all-video-details-code-20260828/receipt.json`；
  receipt verification 为 `passed=true`、`fresh=true`、`scope_paths_match=true`、
  `snapshot_matches=true`、`complete_completion_proof=true`。

Independent native `reviewer_xhigh` scoped re-review verdict 为 `accept with concerns`，无 blocking issue。
其非阻断风险是：未来同一 SHA 若出现多条合法但语义不同的 verified Shot evidence，当前 grouping 只选择
首条 metadata association，可能隐藏 ambiguity；当前 393 groups 实扫未发现该冲突。

## Live Refresh, Unified Sources, And Prompt Recovery Follow-up — 2026-08-28

用户继续验证时确认了三个仍未满足的操作目标：新视频不会自动出现、浏览器没有可确认的声音，以及默认
判断面仍看不到 Shot 分镜与 Prompt。本 follow-up 取代上方“默认进入 External Media Library”和“依赖
手动 refresh”的界面描述；历史 implementation/runtime evidence 仍保留为当时 checkpoint，不代表当前
默认交互。

当前界面与数据行为：

- 旧的 runs/external mode switch 已退休。来源现在只有一个可展开 selector，默认
  `全部视频来源`；同一 selector 可切换 `Runs 工作区`、`AI-VIDEO Artifacts`、`ComfyUI Output` 与
  `青颜项目目录`。默认主判断面优先展示 canonical Runs Shot/attempt 详情，同时列出全部 external groups。
- `runs/`、repository `artifacts/`、`/home/reggie/ComfyUI/output` 与
  `/home/reggie/电商图片/青颜` 由 loopback server 的 bounded filesystem watcher 监听。变更经 `750 ms`
  debounce 后通过 GET-only、`no-store` 的 `/api/library-events` SSE 通知 Browser；页面无需 reload 或点击
  refresh 即重新取得 catalog/detail。
- live coverage 显式区分 `live`、`partial`、`unavailable`、`reconnecting` 与 `stale`。watcher runtime
  error 会关闭对应 source 并降级状态；scan 失败时保留最后一次成功 catalog，但 rail 与主视图同时显示
  stale warning，直到一次后续成功 scan 才清除，避免把旧列表显示成当前 truth。
- refresh 请求串行化，并分别使用 workspace-selection epoch 与 latest-detail-request epoch；旧 workspace、
  旧 manual request 或较早 live refresh response 都不能覆盖更新的用户选择/detail。
- canonical Runs 继续直接展示 Project Shot 顺序、exact-attempt Shot snapshot、完整 sealed Prompt、generation
  type、outcome/phase 与 fetched/candidate media。`全部视频来源` 中的 Runs 部分目前只展开当前选中的
  workspace；其它 workspaces 仍通过 workspace selector 访问，不声称已一次性展开全部历史 workspace。
- Artifact Prompt binding 与 producer 的 `read_text(...).strip()` 语义对齐后，storage whitespace 或尾随
  newline 不再导致合法 receipt Prompt 失联。没有 exact-bound evidence 的 raw external file 仍保持
  `NOT_EVALUATED`，不从 filename、邻近文件或 Prompt 文本猜测 lifecycle。
- exact-bound single-Shot artifact 在 `composition.ordered_shots` 为空时，会展示一个明确标记为
  `分镜脚本参考（来自 exact Prompt）` 的 Shot；该 fallback 不把 Prompt 段落解析成多个 structured Shots，
  也不产生 canonical composition/timeline truth。

本轮 live scan 的后续 observation：

- `395` 个 unique SHA groups、`488` 个 physical locations；source locations 分别为 repository artifacts
  `192`、ComfyUI output `253`、青颜目录 `43`。
- `34` 个 groups 绑定 Shot，`15` 个 groups 绑定 exact Prompt；此前 storage-whitespace mismatch 下只有
  `7` 个 Prompt-bound groups。
- Chrome integrated QA 期间，ComfyUI source count 无 reload、无 manual refresh 地从 `209` 更新到 `210`，
  随后到 `211`，总来源计数同步变化。该 observation 来自目录中其他进程产生的文件；本任务没有生成、
  修改或删除媒体。

声音分层证据：

- 选中的 exact MP4 经测量含 AAC、`32 kHz`、stereo 音轨，duration `5.166667s`；不是无 audio stream 的
  文件。
- `AudibleVideo` 与 standalone media wrapper 的 user-gesture handler 现在会在媒体已经 ended 时先把
  `currentTime` 重置为 `0`，再设置 `muted=false`、`volume=1` 并调用 `play()`。Chrome QA 在点击后观测到
  `paused=false`、`ended=false`、`muted=false`、`volume=1`、`error=null`，播放时间实际前进。
- 主机 default sink 重新绑定为 node `56`：`HDA NVidia Digital Stereo (HDMI 2)` / `GX271UR`，并执行
  unmute 与 `Volume: 1.00`。这与用户指定的 `HDMI / DisplayPort 2 - HDA Nvidia` 一致。
- 隔离的 DevTools Chromium 没有创建可观察的 PipeWire output stream，因此上述证据证明文件有音轨、
  应用已播放且主机默认 sink 配置正确，但不能替代用户实际 Chrome stream routing、显示器 OSD/硬件音频
  能力或实体听觉确认；不得声称显示器已经实际出声。

Verification：

- Node contract/API/UI tests：`43 passed`。
- Provider Console Python tests：`32 passed`。
- Vite production build：`4580 modules transformed`，通过。
- `git diff --check`：通过。
- Chrome integrated QA：默认 `全部视频来源`、canonical Shot/Prompt、exact Artifact Shot/Prompt、SSE 自动
  更新、scan failure stale retention/recovery、ended-media replay/unmute 均通过；console 无
  warning/error。
- Implementation commit：`669289fb6716d7b80076d857e4b8daeeeb9c620e`。
- Exact commit-range Harness：
  `a4a1cf104f40f17be1e70acc6e84b390eb090002..669289fb6716d7b80076d857e4b8daeeeb9c620e`；
  receipt：`.agent/harness/runs/provider-console-live-details-20260828-v1/receipt.json`；receipt verification
  包括 `passed=true`、`fresh=true`、`snapshot_matches=true`、`scope_paths_match=true`、
  `scope_worktree_clean=true` 与 `complete_completion_proof=true`。

Independent native `reviewer_xhigh` 最终 verdict 为 `accept with concerns`，无 blocking issue。剩余两个
非阻断 concern 是缺少 mounted App controller concurrency test，以及 `全部视频来源` 的 Runs 区域只展开
当前 workspace；request guards、deferred-refresh primitives 与 caller wiring 已由 focused tests/review 覆盖。

本 follow-up 没有执行 Provider submit、paid/cloud call、媒体生成、Manifest mutation、activation、P6、
Final Acceptance、push、deploy 或 release。实现与本记录均只形成 local Git checkpoint。

## Unified Source Selector Correction — 2026-08-28

用户通过当前页面截图指出“来源”与 `runs 工作区` 两个下拉控件表达重复。上方
`Live Refresh, Unified Sources, And Prompt Recovery Follow-up` 记录了“来源现在只有一个可展开
selector”的目标状态，但当时实际 DOM 仍同时渲染 `video-source-select` 与 `workspace-select`；该描述在
本修复前并不准确。本节以当前 code、tests 与 live browser evidence 修正该界面事实，历史实现证据继续
保留。

当前实现行为：

- `provider-console/src/video-library-rail.jsx` 现在只渲染一个 `video-source-select`。Runs workspaces 作为
  `Runs 工作区` `optgroup` 的 exact catalog options，与 `外部视频来源` 分组共同进入同一 selector；旧
  `WorkspaceSelector`、`workspace-select`、第二个 refresh button 及对应 CSS 已退休。
- 选择 exact Runs workspace 会同时把 `selectedSource` 切换为 `runs` 并通过既有
  `selectWorkspace()` strict reopen path 加载 detail；没有引入第二 reader、缓存、lifecycle owner 或
  mutation path。
- 唯一 refresh button 的 disabled/spinner 状态与实际 refresh scope 对齐：Runs 只受 `runsLoading`
  约束，external source 只受 `externalLoading` 约束，`all` 才受二者共同约束。无关 source scan 不再阻止
  当前来源的 manual refresh。
- `runs-workspace:*` selector value 只在当前 catalog exact match 时解析为 workspace。保留前缀但未匹配
  catalog 的值 fail closed 在 Runs 域；已选 workspace 若在 refresh 后消失，selector 显示 disabled
  `当前不可用` option，而不是空白或误判为 external source。

Verification：

- Focused Node test：`provider-console/tests/runs-api.test.mjs`，`33 passed`；包含 helper/state assertions、
  SSR component regression（rail 只有一个 `<select>`、两个 `optgroup`、无 `workspace-select` /
  `workspace-picker`）及 stale catalog display coverage。
- Full Provider Console Node suite：`59 passed`；Provider Console Python suite：`32 passed`。
- Vite production build：`4582 modules transformed`，通过。
- Isolated Chrome live QA：默认 `all` 与切换真实 Runs workspace 后 rail 均只有一个 selector，旧 picker 为
  `0`；workspace strict reopen 后展示 `1 attempts`，console 无 warning/error。
- Independent native `reviewer_high` scoped re-review：`accept`，无 blocking 或 non-blocking concern。
- Implementation commit：`749be6ceeedd428f418aeaa70eb38343c84275b9`。
- Exact commit-range Harness：
  `b9d972bebe6a1180cf6dbab134bb17eabf4c0dfc..749be6ceeedd428f418aeaa70eb38343c84275b9`；
  receipt：`.agent/harness/runs/provider-console-source-selector-20260828-v1/receipt.json`。Receipt verifier
  确认 `passed`、`fresh`、`snapshot_matches`、`scope_paths_match`、`scope_worktree_clean`、artifact integrity
  与 `complete_completion_proof` 均为 true。

本修复没有执行 Provider submit、paid/cloud call、媒体生成、Manifest mutation、activation、P6、
Final Acceptance、push、deploy 或 release；只形成 local Git checkpoint 与 read-only browser evidence。

## AI-VIDEO Experiments Source Follow-up — 2026-08-28

用户随后补充 repository 外历史实验目录 `/home/reggie/ai-video-experiments`。本节取代本记录上方将
external allowlist 描述为三类来源、将 watcher roots 描述为 `runs/` 加三个 external roots 的
current-facing 枚举；当时的计数继续只作为 historical observation。

当前实现边界：

- `provider-console/vite.config.mjs` 的唯一 external source configuration 新增固定
  `homedir()/ai-video-experiments` root，source id 为 `ai-video-experiments`，label 为
  `AI-VIDEO Experiments`，kind 为 `development_artifact`。Browser 不能提交或改变该 root。
- 新来源与既有 `artifacts`、ComfyUI、青颜目录走同一个 catalog、recursive watcher/SSE、opaque token、
  no-follow containment、exact-byte revalidation 与 public path sanitization；没有增加第二条 scanner、
  media service 或 lifecycle owner。
- selector、source count 与实时状态继续由 server projection 动态生成。当前 watcher roots 为 `runs/`
  加四个 external roots；external API source count 为 `4`。
- 该实验目录中的 `shot-*-result.json`、`exact-preview.json` 与 Prompt text 当前没有受支持且完整的
  metadata schema linkage。UI 可以保留安全 evidence refs，但 Shot、Prompt、generation type 与成功/失败
  继续显示 `NOT_EVALUATED`；不得因为文件名、`output_path`、相邻 Prompt 或实验结果文件存在就自动推导。

Live Browser/API evidence：

- `/api/external-media` 返回 `4/4` sources available、`400` unique SHA groups、`509` physical locations；
  `AI-VIDEO Experiments` source 有 `21` 个 physical locations，按 SHA 去重后在 selector 中显示 `15`。
- 选择该来源后 rail 显示 `15 / 15 unique SHA` 与 `15 videos`；选中的 exact group 可播放，并按 SHA 显示
  experiment/ComfyUI 重复位置，同时保持 `non_canonical` 与 `NOT_EVALUATED`。
- public catalog JSON 不包含 `/home/reggie`；SSE `/api/library-events` 为 `200`，页面显示
  `实时更新已连接`，Chrome console 无 error、warning 或 issue。

Verification：

- Node contract/API/UI tests：`44 passed`。
- Provider Console Python tests：`32 passed`。
- Vite/Sites build：`4580 modules transformed`，Sites packaging 通过；Sites tests：`5 passed`。
- Architecture Gate：PASS；policy inspection 没有 fallback 或 unmapped path。
- Implementation commit：`29219c90a7bb10a8d35067f697245cc06a968e1e`。
- Exact commit-range Harness：
  `e6caec40d36fc69de1d243bd86f33e7649f293ba..29219c90a7bb10a8d35067f697245cc06a968e1e`；
  receipt：`.agent/harness/runs/provider-console-experiments-source-20260828-v1/receipt.json`；receipt
  verification 包括 `passed=true`、`fresh=true`、`snapshot_matches=true`、
  `scope_worktree_clean=true` 与 `complete_completion_proof=true`。

Independent native `reviewer_xhigh` verdict 为 `accept`，无 blocking issue。其唯一建议是未来若
`vite.config.mjs` 出现启动 side effect，再把 pure configuration helper 移入已有 mapped script；当前不应
为抽象新增 unmapped module。

本 follow-up 没有执行 Provider submit、paid/cloud call、媒体生成、媒体修改、Manifest mutation、
activation、P6、Final Acceptance、push、deploy 或 release。

## Exact Experiment References And Verdicts Follow-up — 2026-08-28

本节取代上方 `AI-VIDEO Experiments Source Follow-up` 中“该实验目录尚无受支持 metadata linkage，
Shot、Prompt、generation type 与成功/失败全部保持 `NOT_EVALUATED`”这一 current-facing 限制；该段仍
保留为当时的 historical checkpoint。实现继续把 `/home/reggie/ai-video-experiments` 作为只读、
non-canonical external source，不把实验 evidence 提升为 Production lifecycle truth。

当前关联行为：

- 新的 experiment evidence adapter 支持三条已经真实存在的结构化链：M6 per-Shot result / requirement /
  resolved request / Prompt / Gate、causal handoff summary / exact preview / Prompt / Shot Gate，以及 H3
  conditioning evaluation / experiment contract / exact submitted workflow。
- 每个通过 exact MP4 identity 与完整 linkage 的记录在同一 detail card 展示 Shot 或 experiment arm、
  分镜脚本、sealed Prompt、generation type、`OUTPUT_RECORDED`、Technical Gate、Human Verdict、逐项
  findings 与可验证 Reference。`OUTPUT_RECORDED` 不等于 lifecycle success、candidate、QA、P6、
  Final Acceptance 或 activation。
- Reference 只有被 content hash / receipt 绑定到 exact submitted input 时才显示为实际生成输入。历史
  conditioning workflow 只有 `LoadImage` 名称而没有 upload receipt，因此仍显示 Arm、Prompt、输出与
  Gate，但 Reference binding 明确为 `NOT_EVALUATED` 并说明缺少 receipt；不再按 basename 猜测输入。
- 同一视频若出现语义不同的 verified evidence，包括 requirement-level findings 冲突，会标记
  `ambiguous_verified_experiment_evidence` 并隐藏 Shot、Prompt、Reference 与 verdict。未知 schema、链路
  缺失或 stale identity 继续 fail closed。
- Browser projection 对 absolute POSIX/Windows/UNC path、signed URL、secret-like text 与 traceback 做
  adapter gate 加 API 递归 redaction；source path、root 与 private media descriptors 只保留在 loopback
  service 内。Reference token 仍在读取时重验 allowlist containment、identity、SHA 与 size。

本机 read-only observation：

- external catalog 当时为 `4/4` sources available、`401` unique SHA groups、`512` physical locations；
  selector 的 `全部视频来源` 另加当前一个 Runs workspace，显示 `402`。
- `AI-VIDEO Experiments` 有 `16` 个 unique videos：`11` 个关联 exact experiment detail，其中 `7` 个有
  exact Reference，`4` 个 conditioning arms 的 Reference binding 为 `NOT_EVALUATED`；另外 `5` 个缺少
  structured composition/output receipt，继续 unbound。没有 ambiguity。
- Chrome integrated QA 在 M6 Shot C v4 同屏确认 exact first/last Reference、脚本、Prompt、
  `OUTPUT_RECORDED`、Technical `FAIL`、Human `NOT_EVALUATED` 与逐项 findings；conditioning Arm A 同屏
  确认 Prompt、`FAIL_STOP_BEFORE_NEXT_ARM`、`HUMAN_FAIL` 和 Reference `NOT_EVALUATED` 原因。页面不含
  `/home/reggie`，console 无 error/warning/issue，所列 local requests 无 `4xx/5xx`。
- catalog 从前一 checkpoint 的 `15` 个 experiment videos 增长到 `16` 来自目录中其它进程的新文件；
  本任务没有生成、修改或删除媒体。

Verification：

- Provider Console Node contracts：`56 passed`；Python projection：`32 passed`；Sites tests：`5 passed`；
  Vite production build：`4580 modules transformed`。
- Independent native `reviewer_xhigh` 对 evidence linkage、安全投影、ambiguity 与 Reference fail-closed 做了
  scoped review；最终无 blocking issue。Harness route follow-up verdict 为 `accept`。
- Implementation commits：`53002ac33e51c5f2f90176827f1ec9468cb24db4` 与
  `59e9860f84adf2f63bc2e6ee56266b7e4a411364`。
- Exact commit range：
  `8d616e07b7c949bc502065845a2b8675e01874bd..59e9860f84adf2f63bc2e6ee56266b7e4a411364`；
  receipt：`.agent/harness/runs/provider-console-experiment-details-20260828-v2/receipt.json`。
- Receipt 内 Architecture Gate PASS、Harness `193 passed`、Provider Console Python `32 passed`、Node
  `56 passed`、Vite build 通过；freshness verification 为 `passed=true`、`fresh=true`、
  `snapshot_matches=true`、`scope_paths_match=true`、`scope_worktree_clean=true` 与
  `complete_completion_proof=true`。先前 v1 receipt 因新 module 未映射而在 policy audit fail closed；补入
  唯一既有 `provider_console` route 并增加 route test 后，由 v2 receipt supersede，没有放宽 unknown-path
  fallback。

本 follow-up 没有执行 Provider submit、paid/cloud call、媒体生成、Manifest mutation、activation、P6、
Final Acceptance、push、deploy 或 release；两个 implementation commits 与本记录均为 local checkpoint。

## Shot Timing And Closable Reference Follow-up — 2026-08-28

用户在关联判断面继续提出两个操作要求：每个 Shot 必须看到对应时间，点击 Reference 图片后必须能退出。
本 follow-up 保持 `ResolvedTimeline` 的唯一 timing ownership，不从 Shot 顺序或 Prompt 文本猜测成片时间。

当前时间语义：

- Project Shot 有 fixed/ranged `duration_policy` 时显示计划时长，同时明确标记
  `成片位置 NOT_EVALUATED`；没有 `ResolvedTimeline` 时不累加前序 Shot 时长补造 timeline。
- 同目录 ecommerce package 有 explicit `start_seconds/end_seconds` 时显示 `声明时间`，但仍受原有
  `co_located_declared_package` 边界约束，不把 package 声明升级为 exact composition receipt。
- M6 result、causal handoff summary 与 conditioning evaluation 只有在原有 exact MP4 identity chain
  已成立时才投影单 Shot clip 时间。M6 使用绑定 result 的 measured duration；causal handoff 在 exact
  summary 只有 `frame_count/fps` 时计算 clip duration；conditioning 使用 exact evaluation probe。
- 单 Shot clip 时间显示为 `00:00.000 – end · duration`，并明确不是最终成片的
  `ResolvedTimeline`。duration 与 `frame_count/fps` 相互矛盾超过 `0.05s` 时，只隐藏 timing，保留其它
  已验证 Shot evidence；UI 显示 `NOT_EVALUATED`。

Reference 预览行为：

- exact-bound Reference 卡片不再打开无站内退出路径的 raw-image tab，而是在当前判断面打开 modal
  lightbox。
- lightbox 支持可见关闭按钮、点击遮罩和 `Escape` 三种退出方式；打开时 focus 进入关闭按钮，关闭后
  回到原 Reference 触发按钮，`Tab` 不会逃到 modal 背后的控制项。

Verification：

- focused Node contracts：`53 passed`；Continuity/Sites：`9 passed`；Vite production build：
  `4581 modules transformed`。
- Chrome integrated QA：Runs Project 两个 Shots 都显示 `2s · 成片位置 NOT_EVALUATED`；M6、causal
  handoff 与 conditioning Arm A 均显示 `00:00.000 – 00:05.167 · 5.167s` 和 `124 frames · 24 fps`；
  六个 ecommerce declared Shots 分别显示从 `00:00.000 – 00:04.500` 到
  `00:24.333 – 00:30.000` 的声明区间。
- Chrome 对 Reference 关闭按钮、遮罩与 `Escape` 逐一验证，关闭后 focus 回到原 Reference button；
  console 无 error/warning/issue，所列 local requests 均为 `200/206`。
- Implementation commit：`52755696342ac2ba116d54b2f782ad18305cd46d`。
- Exact commit range：
  `d6b2d13d0b64ee7d99da831fc37bbd42d079549a..52755696342ac2ba116d54b2f782ad18305cd46d`；
  receipt：`.agent/harness/runs/provider-console-shot-timing-lightbox-20260828-v1/receipt.json`。
- Receipt 内 Architecture Gate PASS、Provider Console Python `32 passed`、Node `57 passed`、Vite build
  通过；receipt verification 为 `passed=true`、`fresh=true`、`snapshot_matches=true`、
  `scope_paths_match=true`、`scope_worktree_clean=true` 与 `complete_completion_proof=true`。

本 follow-up 没有执行 Provider submit、paid/cloud call、媒体生成、Manifest mutation、activation、P6、
Final Acceptance、push、deploy 或 release；implementation 与记录均为 local checkpoint。

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
- `全部视频来源` 当前不会一次展开所有 Runs workspaces；操作员需要通过统一来源 selector 中的
  `Runs 工作区` 分组切换。若未来要建立跨 workspace history index，必须继续从 canonical read-only
  projection 汇总，不能另建 lifecycle owner。
- 应用层音轨、播放状态与 default HDMI sink 已验证，但实体显示器出声仍需要用户实际 Chrome playback
  stream 与硬件侧确认。若用户仍听不到，应先观察真实 Chrome PipeWire stream 和显示器 OSD，而不是改写
  媒体或引入第二套 audio path。

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
