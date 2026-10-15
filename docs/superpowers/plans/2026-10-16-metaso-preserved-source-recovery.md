# METASO Preserved Source Recovery Plan

## Goal

完成对应 spec 的两个共享适配并恢复原 S01 的一次 METASO H3 真实生成。

## Ownership

- Source worker：既有 source-expression/编译/执行校验 owner、METASO adapter 和对应 focused tests；复用原文校验，不复制另一实现。
- Recovery worker：runtime repair schema、decision、committer/Canvas recovery consumers 和对应 focused tests；新增显式 exact 跨 Provider grant，旧许可不扩权。
- Parent：spec/plan、operator 接线、预算与凭据、项目数据适配、canonical matrix/记录、最终验证、一次原生审查、真实提交及 QA；不改 foreign dirty。

## Milestones

1. 两个 workers 各自先复现阻断并跑 focused red/green；保持 file ownership 不相交。
2. Parent 在当前原 S01 数据上运行无副作用 prepare/preview，逐项核对 exact source text、首帧 SHA、声音和输出契约；修复任何实际缺项。
3. Focused verification 后仅提交 owned paths，封存 exact commit range，再运行适用 Harness（保留现有 foreign index）；按 Risk Gate 由一名原生只读 reviewer 审查 paid/source authority，裁决并修复 blocker，通过后推送。
4. 通过 injected exact supplier 取得 METASO credential，封存当前有限单元与真实历史计数，经原 committer 新 intent/permit 提交一次 S01、poll/fetch；exact MP4 显式 MCP QA 后决定是否能继续 S02。

## Acceptance And Stop

原文未声明删改为零；旧失败证据保留；无旁路提交。FAIL/NOT_EVALUATED/UNKNOWN 依原 Gate 停止，不自动重抽或推进。未取得 exact MP4 与 QA 不宣称生成成功；human acceptance 保持 NOT_EVALUATED。

## Self Review

覆盖 source preservation、显式恢复、真实请求与媒体 Gate；无额外用户审批或 worktree。
