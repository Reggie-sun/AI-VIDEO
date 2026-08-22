# Design QA

## Current Target

- Source visual truth：`design/provider-console-source.png`。
- Current runtime target：保留 source 的深色三栏 Provider Console anatomy，同时以本机 `runs/` 的真实 Project、Shot、attempt、registered media 与 evidence 替换静态 Alice / Shot 12 demo。
- Historical `design/implementation-*.png` 和 `design/qa-comparison-final.png` 只记录旧 demo 的视觉验收，不再作为当前 runtime-data acceptance evidence。

## Chrome Integrated QA

2026-08-22 使用 Google Chrome + `chrome-devtools` CLI 对 `http://127.0.0.1:4173` 做了 fresh integrated pass。

- Catalog：页面列出 69 个当时可发现的真实 Production / Legacy workspaces；重复 `run_id` 使用相对 workspace suffix 区分。
- Default latest workspace：`t8-h3-seedance-3shot-continuity-20260822-v7/projects/shot-01-take-01/project.yaml` strict reopen 成功，显示真实 `comfy-local-h3` running attempt 和已注册首帧。
- Local H3：切换到 `c2-alice-local-h3-t10-regression-20260821-001/project/project.yaml`，显示 3 个真实 attempts、真实 request evidence 和可播放的 registered `video/mp4`。
- Hailuo：切换到 `c2-hailuo23-live-20260820-001/production-recovered/project.yaml`，再选择 `minimax_hailuo`，显示真实 `MiniMax-Hailuo-2.3` capability、remote execution identity、registered output 和可播放媒体。
- Seedance：切换到 `seedance-anime-grand-action-continuity-20260820-001/production-shot1/project.yaml`，显示真实 `seedance` / `volcengine_ark_seedance` attempt；没有补造 output 或 fallback lane。
- Evidence dialog：打开后具有 `role=dialog`、modal label 和初始 close focus；`Escape` 关闭成功并恢复页面状态。
- Responsive：`1180 × 820` 下 `scrollWidth = clientWidth = 1180`、`scrollHeight = clientHeight = 820`，无 page-level overflow。
- Console：0 条 error message。
- Network：所有 37 个 observed requests 均为 `127.0.0.1`、Vite `data:` controls 或 `/api/runs*`；HTTP 状态均为 `200` / `206`，无 external request、failed response 或 Provider call。
- Media：opaque token endpoint 对真实 output 返回 `video/mp4`，byte-range 返回 `206` 和正确 `Content-Range`。

## Visual Findings

- 三栏层级、compact density、深墨色 surfaces、violet selection、green recorded-success tone 和 source 的 desktop composition 保持一致。
- workspace selector 进入 Provider rail 顶部，attempt rail 不再展示 invented lanes；相同 `run_id` 的多个 nested projects 可清楚区分。
- Header、record chain、registered media、Provider identity、effective output、evidence 与 read-only action bar 均从 selected projection 更新。
- 主 CTA 为“查看已注册输出”，不再生成 prototype intent；无 output 时为 disabled read-only state。
- 中文 UI 保持一致，Provider / model / API / evidence identifier 保持原始名称。
- 本地边界始终可见：不写 Manifest、不创建 intent、不调用 Provider、不访问云端、不自动回退。

## Accessibility

- workspace 使用原生 labeled `select`；attempts 使用 `button` + `aria-pressed`。
- dialog 有 label、Escape close、focus containment 和 opener focus restoration。
- 所有 interactive controls 保留 visible focus；motion 遵守 `prefers-reduced-motion`。
- registered image/video 有 accessible name；原生 video controls 可键盘访问。

## Mode-Specific Input QA — 2026-08-22

- Visual source：用户提供的 `Provider Console` 原图；本轮以同一深色三栏 anatomy、compact density、violet selection 与 green verified state 为视觉 truth。
- Browser states：在真实 `runs/` 上分别检查 `T2V`、`I2V` 与 `FL2V`。T2V 显示 sealed prompt 和 text-only 说明；I2V 显示 prompt 与首帧；FL2V 显示 prompt、首帧、尾帧和 registered output。
- R2V：当前 `runs/` catalog 没有可用于浏览器检查的 R2V workspace；projection contract 由 parameterized executable test 覆盖，不伪造 browser fixture。
- Full-view comparison：将用户原图与 `/tmp/provider-console-mode-input-fl2v-responsive-final.png` 放入同一视觉比较输入；三栏 hierarchy、typography scale、border density、colors、CTA placement 和中文 copy 保持一致。
- Focused input region：mode badge、raw mode、scrollable prompt、role-labeled binding cards 和 output card 均位于记录链 step 3；没有新增平行 panel 或假 Provider lane。
- Responsive：`1180 × 820` 下 `documentScrollWidth = documentClientWidth = 1180`，console `scrollWidth = clientWidth = 858`；修复 header status 在窄列溢入更新时间的问题。
- Console / network：0 条 console error；observed requests 仅为本机 Vite、`/api/runs*` 和 browser `data:` media controls，无 external request 或 Provider call。
- Evidence boundary：selected detail 显示 sealed prompt；effective negative prompt、Provider raw response、signed URL、secret、absolute path 与 raw error 不进入 Browser projection。
- Screenshots：`/tmp/provider-console-mode-input-t2v.png`、`/tmp/provider-console-mode-input-i2v.png`、`/tmp/provider-console-mode-input-fl2v.png`、`/tmp/provider-console-mode-input-fl2v-responsive-final.png`。

## Fresh Real-Runs + R2V Closure — 2026-08-22

- Visual source：`design/provider-console-source.png`（`1487 × 1058`）；implementation screenshot：`/tmp/provider-console-r2v-source-viewport-final.png`（Chrome viewport `1488 × 1057`，device scale factor `1`）。比较时只对 source 做 1px padding，不缩放页面。
- Combined comparison：`/tmp/provider-console-qa-source-viewport.png` 将 source 与同 viewport implementation 放在同一输入中复核；三栏 anatomy、compact spacing、深墨 surfaces、violet selected lane、green status、top summary、right evidence rail 与 bottom action bar 均保持一致。
- Catalog：fresh `/api/runs` 返回 `99` 个真实 workspaces、`truncated = false`；默认 strict reopen 最新可读 workspace `seedance-mini-r2v-live-20260822-002/production/project.yaml`，未回退到 demo。
- Mode states：在真实 workspaces 上逐一检查 `T2V`、`I2V`、`R2V`、`FL2V`。T2V 显示 prompt；I2V 显示 prompt + 首帧；R2V 显示 prompt + 参考图；FL2V 显示 prompt + 首帧 + 尾帧。没有补造不存在的 registered output。
- Strict error state：选择 rejected preflight workspace 时稳定显示 `PRODUCTION_PROJECT_INVALID` 对应的“工作区不可用”状态；刷新后回到最新可读 R2V workspace。
- Interaction：workspace selection、attempt selection、refresh、evidence dialog 与 registered media preview 均沿真实 `/api/runs*` seam 工作；页面级 `scrollWidth = clientWidth = 1488`、`scrollHeight = clientHeight = 1057`。
- Typography：中文 UI 与原始 Provider / model / API identifiers 的层级清楚；与 source 的字号比例和紧凑信息密度一致。仅保留本机 CJK font rasterization 差异。
- Spacing / layout：rail、main record chain、right identity/evidence 区与 action bar 的间距、边框和对齐无可见破损；长 fingerprint 只在右栏按字符换行。
- Colors / tokens：dark background、surface contrast、violet selection、green verified/read-only tone 与 source 匹配，没有引入新的高饱和视觉系统。
- Image quality / assets：R2V 使用 Registry 中真实 reference image，经 opaque local media token 加载；没有 placeholder、假缩略图或 external asset。
- Copy / content：主 CTA 明确为“查看已注册输出”，并持续展示“不提交、不重试、不自动回退”和“不写 Manifest、不创建 intent、不调用 Provider、不访问云端”的当前 slice 边界。
- Console / network：fresh reload 后 console `0` errors；20 个 observed requests 全部为 `127.0.0.1`、Vite module 或 `/api/runs*`，HTTP `200`，无 external request、Provider call 或 Alice demo asset request。
- Comparison history：首次 fresh reload 发现 `index.html` 仍将 Alice demo 图作为 favicon 请求，记为 P2 runtime demo leak。移除该引用、使用空 favicon declaration，并添加 `sites-worker.test.mjs` regression assertion；post-fix reload 不再请求 Alice，且不再产生 favicon `404`。

## Remaining P3 Polish

- 极长 evidence hashes 在窄右栏按字符换行，信息完整但视觉密度较高。
- 字体 rasterization 与 CJK weight 会随本机字体栈产生轻微差异。

final result: passed
