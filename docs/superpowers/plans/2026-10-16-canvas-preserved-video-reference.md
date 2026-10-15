# Canvas Preserved Video Reference Plan

## Goal And Scope

执行同名spec：准备S01本地白模，给当前共享入口补齐exact视频参考准入，完成一次METASO H3生成及QA。

## Ownership And Invariants

Parent负责Blender资产、spec/plan、canonical数据/恢复/预算/调用/QA与记录。bounded worker只修改 `src/ai_video/canvas_source_expression.py`、新 `src/ai_video/canvas_video_assets.py`、`tests/test_canvas_source_expression.py` 和 `tests/test_canvas_assets.py`；新helper独占本地MP4测量/selection receipt准备，不复制Provider生成receipt；其他source/renderer/state owner保持。保留foreign dirty，不建development worktree。

## Milestones

1. 白模按原S01 28mm锁机位、24fps、左手至2cm/右手手机/七名反射替身制作；查看渲染及几何证据，导出无对白干净reference MP4及可编辑blend。白模不代最终素材验收。
2. 复现普通video reference准入失败，在现有source owner验证exact slot/resource/role/type/provenance/metadata，保留image/subject/state replacement回归。新source snapshot保留原文并显式新增用户授权参考，不伪造旧snapshot。
3. focused tests及exact Harness通过后按Risk Gate判断review；经唯一committer封存旧失败、准入新参考、生成新的exact input/preview/intent/permit，最多提交一次S01。逐项MCP QA后保存视频和真实证明边界；不自动扩S02/重抽。

## Self Review

已覆盖原文保留、输入差异、旧证据保留、有限调用及媒体验收；没有额外用户审批步骤或新执行链。
