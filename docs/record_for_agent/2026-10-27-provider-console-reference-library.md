---
record_kind: architecture_implementation
topic_id: provider-console-reference-library
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Provider Console Reference Library

## Scope

用户明确要求把 repository 的 `referces/` 接入前端。新增左侧“素材”和顶部“参考素材”入口，
深链为 `http://127.0.0.1:5174/?view=references`；图片按文件更新时间排序，每页 12 张，
支持文件名／相对目录搜索、完整比例缩略图、点击放大和目录变更实时刷新。保留目录原拼写。
本次真实扫描为 81 张图片，查询 `lin-xu` 为 18 张。后续制作可能继续增加图片。

`provider_console_preparation.py` 复用已有有界图片读取，新增固定 archive 的分页投影；
最多扫描 4096 个目录项、深度 12，每页读取最多 64 MiB、单图 16 MiB。读取失败的条目仍显示
不可用，不静默从当前页消失。只读 PNG/JPEG/WebP，不解析或发布任意 JSON、Prompt、HTML。
`runs-api.mjs` 的 GET `/api/reference-library` 固定 repository `referces/`，只接受有限
query/offset，不接受客户端 root；沿用 loopback、exact SHA/bytes、no-follow、containment、
opaque token 和 no-store。原始资产、索引、Registry、Manifest 均不修改。

已有 library SSE 增加 references 来源；参考库的更新不触发无关外部视频重扫。
前端保留失败前结果并明确提示过期，新的查询／分页取消旧请求，缺失目录和空查询结果可见。
目录收录不代表选中用于 Shot、已提交生成或已通过质量验收；原目录与归档的同步仍遵循
`referces/README.md`，前端只观察该归档目录的实际文件。

## Verification

- Python：递归发现、跨页不重复、大小写无关搜索、offset 边界、缺失目录、root/file/目录链接、
  内容变化 token、超限图片可见但不可预览。
- Node：固定 root 的图片 GET、跨 root descriptor 拒绝、路径隐藏、query/offset 限制、GET-only、
  非 loopback 拒绝；SSE ready 和 references 事件路由；入口 SSR。
- Chrome MCP 与 Playwright MCP 配置被其他浏览器占用，未终止其进程；改用现有 Playwright
  和 Chromium，在独立临时 headless browser 对真实 5174 服务验证。1440×1000 首屏 12 图、
  `lin-xu` 第 2 页 6 图、放大／Escape／焦点恢复、503 后保留旧图并刷新恢复、空搜索、左侧
  素材入口均通过；390×844 页面宽度 390px，无横向溢出，浏览器 pageerror 为空。
  临时截图 `/tmp/reference-library-desktop.png`、`/tmp/reference-library-mobile.png`；
  浏览器日志 `/tmp/reference-library-browser.log`。
- Harness receipts：`.agent/harness/runs/20261027-reference-library-focused/receipt.json`、
  `.agent/harness/runs/20261027-reference-library-related/receipt.json`、
  `.agent/harness/runs/20261027-reference-library-full/receipt.json`，以对应级别结果为准。

## Review Boundary

Parent self-review：`NATIVE_REVIEW_NOT_REQUIRED`。固定用户指定的本地图片目录，沿用已有传输
校验，具备跨 root、链接、变化和刷新失败验证，无 Production 或付费路径。
`record-ai-video-session=record`；`distill-ai-video-learning=no_candidate`，不产生媒体实验学习。
