# Canvas Reference Workflow Preflight Plan

## Goal And Ownership

按同名 spec 实现共享只读准备报告，并尝试沿真实项目继续。Parent 串行，当前 main；
保留旧 spec/plan/baseline/record 的 foreign dirty work。受管 Kimi 仅调查现有准入/恢复 owner。

## Files And Milestones

1. `src/ai_video/canvas_preflight.py` 负责纯报告；`scripts/canvas_production.py` 在现有 service author
   validation 后提供无 runtime 副作用的 CLI 和 author 输出；service lifecycle 无需修改。
2. `tests/test_canvas_project_data.py` 增加完整链路、来源、占位、immutable resume 与无副作用的回归；
   `docs/canvas-production-harness.md` 说明用法和证明边界；matrix 记录投影 owner，playbook 的既有
   Creative Preflight 要求在首镜前运行全序列报告，允许明确有界的准入实测而不制造禁止规则。
3. 运行 focused Canvas tests、exact staged Harness，Parent 风险裁决，owned commit/push 核验 SHA。
4. 对当前数据运行共享 preflight/status；缺凭据前不 lookup，缺材料/恢复证据前不提交。
   实际成功生成后才进入逐镜 MCP、状态交接和 HyperFrames；实际 blocker 落 record。

## Invariants And Verification

不新增 Provider/故事执行器，不替换普通中间帧，不修改既有 Gate、计数、失败历史或准入事实。
Report 保持 `NOT_EVALUATED` 与实际资产身份分别呈现；无 side effect 由失败型 runtime factory 回归证明。
Spec/Plan Parent self-review completed；验证失败先修，新的实测许可不能从工程 PASS 推导。
