# Edit-First Temporal Control Implementation Plan

**Goal:** 在现有上层生产选择和唯一时间线中支持可验证分段变速，避免将可编辑问题直接送回生成。
**Spec:** `docs/superpowers/specs/2026-10-17-edit-first-temporal-control.md`。
**Approval:** 用户最新明确方向及任务内共享契约授权；Parent self-review，无新增媒体付费许可。
**Invariants:** 原历史/消费/QA保留；ResolvedTimeline唯一时间owner；HyperFrames唯一renderer；用途证据不跨map复用；显式音频边界。

## Milestone 1: Canonical Frame Mapping And Renderer

**Files:** 新`production/video_retime.py`；原`composition_contracts.py`、`composition.py`、`visual_media.py`、`_composition_source_duration.py`；相关composition/HyperFrames tests。
**Contract:** 可选VideoTimeMap的严格整数锚点与倍率；2.3版解析为顺序source/output spans，旧字节不变；非一比一段解析为每输出帧一个一比一source window，避免pinned导出忽略data-playback-rate。源帧、样本与输出起止只解析一次；不添加依赖。
**Verification:** TDD复现缺字段；normal/piecewise/bounds/version/legacy hash/audio负例及actual pinned render的可识别源帧验证。

## Milestone 2: Editing Candidates And Exact Use Evidence

**Files:** 原`production_strategy_contracts.py`、`source_use_evidence.py`、`planning/production_strategy.py`、strategy reader/materialization/composition及原tests。
**Contract:** EDIT_EXISTING_VIDEO只在有可执行time map时可行；map完整进入用途、lineage和composition校验。policy `/2`默认等待更少生成次数候选的NE用途证据；明确FAIL可排除，其他可行生成仍须原授权。显式 `/1`兼容。
**Verification:** source未评估不自动fallback生成、FAIL区别、篡改map/复用旧PASS拒绝、标准loader/materialize/compose正常与回放路径、多场景迁移。

## Milestone 3: Canvas Reassessment And Retained-Media Preview

**Files:** 原Canvas application/data/CLI seams；必要的现有failed-media admission/Registry owner；原tests与workflow docs。
**Contract:** 质量失败修复先上层评估；薄CLI调用现有planning；来源保留原失败证明，不清除STOP或越过known/unknown guard。显式muted编辑preview不构成Production qualification。
**Verification:** 无Provider/noPOST准备与拦截，known-no-effect/runtime兼容；同一已消费MP4的本地preview、原/编辑关键帧对比、原Manifest/hash不变；human与声音缺证明示。

## Completion

源码稳定后运行owned exact snapshot适用Harness；按SUBAGENTS Risk Gate处理用途证据/准入的独立审查需求，修复确认finding。
记录工程证明、编辑预览与未验质量，评估record/learning；仅owned paths commit/push main并核验remote SHA，foreign index/dirty保持。

## Verified Progress

分段源帧映射、exact用途证据、上层编辑优先及静音开发预览已实现；实际pinned导出11/11抽样帧匹配，机器人原4秒姿势映射到3.5秒样帧，新增Provider POST0，完整质量与human仍NE。
基线Harness r2为21 PASS/1 covered SKIP；旧格式None trim兼容增量r3为7 PASS，分别在其exact源码点核验fresh完整证明。
首次native reviewer_xhigh在8470611发现EF-001完整P4校验遗漏与EF-002材料化后Canvas续接缺口；Parent确认并修复，补公开compose/render、正反切点及未知结果STOP用例。修复快照43b58d6的r4为14/14 PASS，fresh/integrity/complete证明已核验；同一reviewer第二轮full re-review finding set为空，Parent结合公开回归关闭两项问题。
源码已push main并核验remote43b58d62e55fbcba8021002667f3042be584a6c2。收尾文档只明确既有source-backed自动续接范围、减速重复采样限制及上述实证，不增加运行语义。文档checkpoint的receipt归`edit-first-temporal-control-record-20261017-r1`；工程证明、静音单源局部观察、原Shot STOP与human未验分别保留，记录及learning评估见`docs/record_for_agent/2026-10-17-edit-first-temporal-control.md`。
