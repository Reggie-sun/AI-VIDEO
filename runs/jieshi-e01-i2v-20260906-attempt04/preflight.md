# S01 Compiler V2 Live Attempt

## Scope

用户本次“继续生成”授权一次新的 S01 Vidu Q3 Pro I2V，4 秒、1080p、原生声音。
沿用已登记首帧 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，
2,064,319 bytes、941×1672；使用既有 import receipt，不伪造 human visual approval。
仅改变 Provider prompt 编译（v2 prose）及 `is_rec=false`，创作意图保持 attempt03。
随机种子仍未固定，不能将结果差异单独归因于一个参数。

## Exact Request

- Request: `b66d3b87c97390eacddd01140785d1702d6f566e82881908123ac576700f55c3`
- Paid preview: `8a1f17e7042660356d8e44e4e8f16f680f3bd4a6ece327e489d9e81380c81538`
- Actual POST body: `d504b3aefe6d3f1ac8d8b50c4c53df76d73fb31c6a9c94ca006e834bed13c1d6`
- Prompt: 974 chars; SHA `5d5a5fc5f60807318b066fa7566b6d26da00cbd704457ea8b3460244e1a6767a`
- Endpoint: `img2video`; `audio=true`, `is_rec=false`.
- New task quota: 1; new authorization/reservation04/intent/one-use permit.

原 attempt03 strict reopen 为 fetched/validate，Gate FAIL，额度已消费。
本次新 independent project 由 canonical bootstrap 建立，没有复制旧 Manifest。
原 profile 定额 operator ceiling 依仓库已有续期流程保留原金额/配置，真实决定时间起一小时；
新旧 identity 见 `operator-ceiling-renewal.json`，不代表官方报价。

## Verification Boundary

Planner/readiness → Router → compiler2 → resolve → paid preview 完成，
native reviewer_xhigh 提交前核查 `accept`；AST 与输入 bytes 核对通过。
本地 core compiler 提交 `e568122` 已有离线测试及独立 review。
本 run 脚本 Harness inspect 落入 fallback；用户禁止 worktree，因此没有 fresh isolated receipt，
不声称已完成该完整检查组合。无 push、无 S02 submit、无自动 activation。

实际提交于 2026-09-06 08:32:55 UTC 开始，HTTP 200 且 task accepted；
本次 submit quota 已消费。后续仅恢复同一 task，exact MP4 落盘后立即调用 project-local video-analysis。
