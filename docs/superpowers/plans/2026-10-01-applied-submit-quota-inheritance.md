# Applied Submit Quota Inheritance Plan

## Goal And Scope

落实同名spec，仅修复 retained task cap的读取和 admission，不改变quota publication、ledger、permit或media acceptance。

## Milestones

1. 在canonical fixture重现 successor不能继承已生效cap，覆盖不完整ancestor和计数边界。
2. 在quota owner实现read-only继承predicate，替换committer局部query；同步matrix。
3. targeted及changed-path检查、真实REQUEST只读guard、双独立review绑定稳定snapshot；必要修复后重验。
4. 通过后恢复同一未提交REQUEST，核对fresh profile/authorization和2/4 consumption；POST后按canonical状态poll/fetch并显式MCP逐镜gate。

## Stop Conditions

Unknown outcome、required review无法闭合、未授权输入/Provider/egress停止；profile过期须canonical explicit recovery，不能改旧request。工程checkpoint不等于影片完成。

## Self-Review

范围和spec一致；不创建worktree，不修改unrelated `.codex/config.toml`，不制造逐项批准步骤。
