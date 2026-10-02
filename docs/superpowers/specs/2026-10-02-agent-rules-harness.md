# Agent Rules Harness Migration Spec

## Goal And Authority

用户要求精简 `AGENTS.md` 与 `.agent/context/`，把适合机械验证的规则做成 Harness。
Parent 在该任务授权内 self-review 并接受此迁移；不修改 Product、paid/recovery 或媒体验收语义。

## Contract

- `AGENTS.md` 保留 authority、canonical ownership、安全与授权边界、真实验收和 completion。
- `.agent/context/` 保留精简 advisory 操作入口与仍需 Agent 判断的规则；不迁入重复的 Skill/schema/catalog。
- `.agent/harness/agent-rules.yaml` 只登记 rule → existing check IDs、证据层级与文档体量。
  argv、changed-path routing 与 receipt 仍只属于 `policy.yaml` 与现有 Harness。
- 新只读 `scripts/agent_rules_gate.py` 检查 registry schema、非空/有效 check references、
  引用检查已被 policy 路由、context 覆盖/体量与本地 Markdown links/anchors。
- `agent_rule_invariants` 复用真实现有 tests 的 node IDs 验证 validate、resume、严格 reader、
  single timeline、precise invalidation、unknown-outcome 与 replay；不是 prose keyword PASS。
- 内容体量按 UTF-8 bytes 和 lines 双重约束，context 新文件必须显式登记，防止简单改为超长行或拆文件。
- authoring、external authorization、主观成片质量与逐 Shot MCP Gate 保留 manual/runtime 边界；
  离线 PASS 不证明 Agent 任意 shell/tool 操作受拦截，不产生 Production acceptance。

## Verification And Compatibility

RED mutation tests 证明 malformed/empty registry、unknown/unrouted check、oversize/new context、
broken links/anchors 和路径逃逸 fail closed；真实 policy 路由必须选择新 gate 和 invariants。
保留现有 Markdown anchors 与 Skill routing。只修改干净 task-owned paths，保留 staged
`.codex/config.toml`。exact staged snapshot Harness 与 T3 双独立 review 后 Parent 裁决。

## Self-Review

新增 rule index 不复制 surface mapping 或 argv，不替代 runtime checks；本次授权只覆盖 Development
Governance。Host runtime 文档的历史版本/实验数据回指 existing records，仍保留可用操作 recipe。
不改 historical evidence、不启用 Provider/media、不增加 runtime dependency、不 push/release。
