# Shot Reference Risk Assessment Plan

**Goal:** 在现有 Reference Plan 内按组合风险选择最小充分参考，减少简单动作的误阻断，并具体解释白模取舍。

**Scope:** 审查现有规划、Provider capability、上游 Scenario 方法及真实历史；增强派生规划、报告、失败诊断与现有 specialist 交接。

**Contract Surfaces:** `ReferencePlanningIntent` / `ShotReferencePlan`、VideoPlanner、`reference_strategy_report()`、Canvas preflight 与 prepared-generation report。

**Invariants:** 不另建 Planner/Router/Registry/持久状态；不改 Manifest、Budget、Permit、committer 或 QA 接受权限；不生成媒体、不重试 UNKNOWN、不改历史验收。时长不决定图数，输入容量不等于控制能力。

**Compatibility:** 保留既有 intent 字段及缺省序列化；只扩展现有 facets 和派生报告。新规则显式版本化；旧记录与已封存请求不迁移，当前重规划须重新核验。

## Milestones

### 1. Audit And Evidence

Parent 核对 canonical contracts、规划/选择/编译/QA 调用链及 Scenario 上游 pinned revision；只读 native investigator 核对 selected capability 与 exact 历史请求/QA/媒体。区分观察与未隔离因果，不把单例变成最优图数。

### 2. Risk Decisions And Reports

修改 `reference_planning.py`、`reference_planning_contracts.py`、`reference_strategy.py`；更新 `tests/test_reference_planning.py` 与 integration tests。沿同一 needs/selection seam 将 motion 分为 none、recommended、previs_priority、required；简单接触不强制视频，耦合受力/支撑转换/多人遮挡不得漏检。白模给出静态/连续预演或无需制作的具体理由，优先核对可复用素材。报告分开审看状态、待准备图片、已选图片/视频、能力与质量边界；补充输入用途冲突与已满足项保留检查。

### 3. Handoff And Verification

更新 `docs/shot-reference-planning.md`、`docs/blender-routing.md`、open-video、Storyboard specialist、Seedance authoring 的现有入口；仅必要时修改 identity/blockout 入口以纠正保证式表述。持久评估归本任务 `docs/record_for_agent/` record，不修改并发历史。先 red/green focused tests，再 Harness focused/related/full；精确 stage owned paths，记录实际失败和风险，按 Risk Gate 判断独立审查，验证后 commit/push main 并回读 SHA。

## Acceptance

- 稳定对白/简单接触/单一高速或运镜标签不因缺 motion reference 自动阻断。
- 因果受力结合支撑转换、多体遮挡或高速碰撞要求适合的连续参考；静态图不能充数。
- motion recommendation 不被误当 hard gate；选中的可选输入仍须通过原 Provider role/count/format guards。
- 每个状态与素材职责可追溯，不把 review board 当干净端点，不默认所有 review states 均须作图。
- Provider 上限/时序/模式边界及历史效果的未验证部分清楚报告；没有新增付费调用。
