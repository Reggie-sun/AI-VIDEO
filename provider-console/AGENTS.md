# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

Provider Console 的 runtime 数据必须来自本机 `runs/` 的只读 canonical projection；不得以 Alice、Shot 12 或静态 Provider lanes 作为 runtime fallback。Sites/static 环境无法访问 repository filesystem 时，必须显示“本地 runs 数据源不可用”，不得把 build-time snapshot 嵌入部署产物。Console 只允许观察已存在的 Project、Shot、attempt、registered media 与 evidence；不得写 Manifest、创建 intent、调用 Provider、读取 secret 或暗示已获得执行授权。

合法 workspace 即使没有 `video_generation` attempt，也必须保持可检查：明确标记 strict reopen 已通过，并展示已存在的 Shots、Manifest operation summary 与 bounded canonical Registry media。不得把“没有 video attempt”渲染成 workspace 读取失败；真正 strict invalid 的 workspace 仍须 fail closed。

Selected video attempt 的生成类型与输入必须来自 strict request receipt：`T2V` 显示 sealed prompt；`I2V` / `R2V` 显示 prompt 与 exact input bindings；`FL2V` 仅由 `image_to_video + first_frame + last_frame` 推导并同时显示首尾帧。不得按 Provider/model 名称猜测 mode；effective negative prompt、Provider raw response、signed URL、secret 与 absolute path 不得进入 Browser projection。
