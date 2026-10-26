---
record_kind: architecture_implementation
topic_id: provider-console-shot-references
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Provider Console Shot References

Date: 2026-10-27

## Current Behavior

修复 Registry 图片固定高度配合 `object-fit: cover` 导致主体被裁切的问题；媒体网格随容器
宽度换列，图片完整显示，文件标识换行。Registry、请求输入、创作参考复用站内图片放大预览，
支持关闭按钮、遮罩与 Escape，关闭后恢复触发按钮焦点；dialog portal 避免继承卡片的缩略图尺寸。

每个当前 Shot 新增 `authored_references` / `authored_references_truncated` 只读投影：
从 strict loaded Shot 的 `required_asset_roles`、匹配角色的 `reference_asset_ids`、
匹配场景的 `visual_reference_asset_ids` 读取，按现有 containment/media-token owner 生成预览。
每 Shot 最多 32 项，保留角色、场景和 Shot 素材的来源，不用文件名或邻近 Registry asset 猜关联。
即使没有生成 attempt，也能在 Project Shot 面板看到已登记创作参考。

视频预览页直接展示本次请求参考及当前创作参考，分别使用 exact attempt input bindings 和
当前 Project revision；当前参考不冒充历史提交输入，request binding 本身也不证明已远程提交。
未登记或不能严格重开的参考不会从 Agent 聊天、任意目录或失效证据中补造。

## Verification

- 新增真实 `write_production_project` / two-Shot factory → strict reader 测试，覆盖没有 attempt
  时仍展示参考、逐 Shot 素材归属、exact bytes 损坏 fail closed、只读及路径不泄漏；另覆盖 32 项上限。
- `focused-02`：79 项 Python、112 项 Node tests 通过；初轮发现旧 test double 未提供 Scene
  模型已有的默认参考字段，补齐 fixture 后通过，未放宽生产 reader。
- 前端 offline Vite build 通过。
- Chrome MCP 在真实 `shizhen-fusion-title-trial-20261026/project-r6/project.yaml` 验证：
  无 video generation attempt 的 CO-TAIL 展示角色/场景参考 `co-before-image` 和明确标为
  Shot 素材的 `fusion-title-composite`。Registry 原截图中的 1672×941 图片完整显示；1440px
  与 390px viewport 无页面横向溢出，实测放大、Escape/按钮关闭及焦点恢复。
- Receipts：`.agent/harness/runs/20261027-console-references-focused-02/receipt.json`（PASS），
  `.agent/harness/runs/20261027-console-references-related/receipt.json` 与
  `.agent/harness/runs/20261027-console-references-full/receipt.json`（FAILED）。后两者仍被
  既有根 `AGENTS.md` 14,185 bytes 超出 14,000 bytes 挡住；没有修改该规则，完整回归未通过。

## Boundaries

`NATIVE_REVIEW_NOT_REQUIRED`：仅扩展 strict reader 后的只读投影及可回滚 UI，沿用既有媒体
identity/containment/transport，关键关联和失效路径有测试。没有 Provider 请求或 Production
state mutation。保留其他窗口未提交改动；`distill-ai-video-learning=no_candidate`，本次不形成
独立媒体实验结论，不修改 Skill/Policy/Gate。

## Layout And Duplicate References Follow-up

用户补充截图后复现：扫描状态内容高 228px，却被 110px 上限裁切；S04 的 4 个 asset
同时绑定角色／场景和 Shot，旧 UI 按 8 条来源逐条画图。扫描区改为默认收起的原生 details，
展开后按内容撑高；取消动态卡片的垂直裁切，并让矮窗口主区域可滚动、侧栏不撑破 viewport。
生成记录摘要和操作按钮按容器宽度换行，修复手机端 692px 横向溢出。

创作参考按相同 asset ID 和 media SHA/token 合并卡片，保留所有去重后的来源用途；不同 asset、
不同媒体 identity、未知 identity 不合并。仅改变展示，不修改 Production references 或请求绑定。

- 边界测试覆盖同图多用途、重复用途、不同 identity、未知 identity，以及来源数组保持不变。
- `20261027-console-layout-focused`：79 项 Python、112 项 Node tests 通过；offline Vite build 通过。
- Chrome MCP 实测真实 `trial-S04-v1/project.yaml`：8 条绑定显示为 4 张图，全部加载，
  每张保留角色／场景及 Shot 用途；放大完整显示，Escape 关闭并恢复按钮焦点。
- 1440×1000、1280×600、390×844 viewport 检查：展开扫描详情内容不裁切、按钮完整、
  与 Shot 动态无重叠；矮窗口可滚动，手机无页面横向溢出。期间观察到真实 S04 从
  `running/polling` 更新为 `running/validate`，没有发起或修改 Provider 任务。
- 本轮 related/full receipts 位于 `.agent/harness/runs/20261027-console-layout-related/receipt.json`
  和 `.agent/harness/runs/20261027-console-layout-full/receipt.json`；仍在既有 AGENTS.md
  14,185/14,000 bytes 检查失败，完整回归未完成。最终包含记录的 focused receipt：
  `.agent/harness/runs/20261027-console-layout-final-focused/receipt.json`。

Parent 对以上五个前端源码／测试文件自审：`NATIVE_REVIEW_NOT_REQUIRED`，只读展示、局部可逆，
无新增 durable-state 或授权路径；`distill-ai-video-learning=no_candidate`。
