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

## Remaining P3 Polish

- 极长 evidence hashes 在窄右栏按字符换行，信息完整但视觉密度较高。
- 字体 rasterization 与 CJK weight 会随本机字体栈产生轻微差异。

final result: passed
