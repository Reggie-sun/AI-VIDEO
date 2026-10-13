# Asset First Continuity Implementation Plan

## Goal And Scope

按同名 accepted/self-reviewed spec 完成共享 capability 后执行已批准的一图两镜有限单元。
Native Codex primary，当前 main；保留 foreign dirty files。两个 read-only mapper 分别核对 image owner
和 Canvas original-video seam；Parent 负责图片共享能力、服务整合、验证和最终裁决。
受管 Kimi 已完成共享边界调查；两个不相交的 native bounded workers 分别承担 paid recovery
和 original-video handoff/source compiler，缩短独立模块实现时间。service 同文件由 recovery worker
完成后串行交回 Parent；不允许两位 writer 同时写入。

## Implementation Ownership

- 图片：`seedream.py`、`image_candidate.py`、`canvas_image.py` 与原 image request/intent/reader/Registry
  validation owner；新增 `test_seedream_remote_image.py`。PNG wire 不转换，保留旧 Grok wire 路径。
- 接续：`canvas_handoff`、`canvas_source_expression`、`seedance_source_expression` 及对应 tests；
  approved state 与 conditioning input 分离但保留同一 canonical evidence chain。
- 恢复：`generation_runtime_repair`、`_state_commit_video_runtime_repair`、`generation_decision`、
  `canvas_recovery`、既有 `_state_commit_paid_provider` intent/grant 消费入口及 service recovery branch；
  typed version 保持旧序列化与历史 outcome。同版本 operator profile 可续期，仍绑定新 exact scope/preview。
- Parent 最后整合 `CanvasProductionService` 和 policy/matrix/Harness doc，先纯准备和离线验证，
  再执行已经批准的有限单元，不以任何 fixture 替代实际 Provider/MCP 验证。

## Contract Milestones

1. Seedream：沿既有 image service/paid/Registry seam 添加 exact Ark image adapter与严格 reader lineage，
   原图 PNG bytes 不转换，测试成功、拒绝、unknown、malformed/错模型/错身份、one-use及无隐式重试。
2. Canvas 原始视频参考：显式输入类型与职责，原 prompt机械映射，accepted A +所选实际状态 gate后绑定；
   测试未接受/错hash/错前镜/未审批状态/把尾帧冒充原视频等拒绝，并保持 B own Gate。
3. 已知 accepted FAILED 恢复：既有 runtime repair receipt 的窄版本扩展，精确前驱与新scope，
   同task/Shot和累计预算、保留goal/音频/时长、一用即消耗。拒绝unknown/运行中/有媒体/错链/重放。
4. 各 owner focused tests → exact staged Harness →适用独立 review → owned commit/push及远端SHA。
5. 生成前封存新单元、exact previews与运行资格；沿共享调用执行一图两镜及真实 MCP/Gate。
   通过后做canonical声画trim/HyperFrames及用户完整听看；实际失败/unknown按边界停止并记录。

## Verification Boundary

实际运行暴露的 P7 authoring successor 缺口由 `_image_video_lineage` reader owner 补齐；
验证生成→两次 authoring commit→standard reopen，并拒绝缺失提交边和变更 snapshot bytes。
实际项目只用 canonical committer 修复追加顺序，保留错误 Registry 版本，不新增图片或视频调用。

工程PASS不证明模型准入或连续性；不重复旧失败任务，不挪用旧 B 剩余额度，无自动重抽。
每个稳定变更包的文件归属由 Parent 在修改前精确列出；同文件冲突必须用户决定，read-only mapping不写文件。
