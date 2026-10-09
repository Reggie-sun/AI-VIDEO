# Seedance Fictional Reference Admission

## Scope And Authority

用户明确要求“修改harness再上传”，并确认使用虚构角色、不走真人认证。此次只修改
`seedance_asset.py` 的本地写实虚构人物一律拒绝规则；不修改角色、原对白、参考图或生成参数。
2026-08-28 的真实拒绝与旧 receipt 继续保留，新授权不追认旧结果。

## Implementation And Evidence

删除 `_deny_photorealistic_person_like_egress` 及 authorizer/resolver 两处调用。
现有 human attestation、mode-specific permitted use、来源证据重开、Registry/bytes/hash、
task/preview/authorization、one-use permit 与 no-retry 保持不变；真人或受保护身份仍拒绝。
先运行四个修改后的正向测试，均被旧 blanket denial 阻断；删除该条件后 Seedance 全部
124 项测试通过。Fake transport 检查 I2V/R2V exact image bytes 与 permit 消费，不能证明
Ark 接受。当前 synthetic resolver 仍只支持 PNG 和 image-only 请求，不声称已补齐原画布
JPEG 或混合 video 参考的 Production materialization。

## Upload Observation

已准备并复核原画布三个角色、宿舍及已获批准的 2 秒参考视频，源证据位于
`runs/fanxiang-canvas-fidelity-20261009-002/`。通过已登录的方舟体验页尝试
Chrome MCP `upload_file`，工具在文件读取前返回 `Access denied`：项目路径不在该工具的
configured workspace roots 内。该操作没有得到上传结果，不属于 Ark 素材审核拒绝。
2026-10-10会话环境重新给出当前项目workspace root后，基于前次明确零上传结果检查一次，
工具仍在相同位置拒绝；两次均未进入平台上传。未转换原图、未尝试绕过工具的路径限制、
未真人认证、未生成；没有对未知平台结果重试。

## Verification Boundary

实现检查与独立审查证据放在 `runs/seedance-fictional-egress-20261009-001/`；
Harness 检查位于 `.agent/harness/runs/seedance-fictional-egress-20261009-001/`，全部通过，
提交前 receipt 的 exact staged snapshot、完整性和 freshness 均复核为 true。代码提交
`71d8df1`。Kimi invocation `e32ee1df-7635-4e56-ae05-e97ac609e73b` 为受管
`deep / k3 / max`、`PARSED`，无 blocking finding；其测试证据与旧字符串遗留问题由
Parent 用 fresh Harness receipt 和 `rg src tests .agent/harness` 无命中结果裁决。
此次是 standing nontrivial delegation 下的有界独立验证；Risk Gate 不要求额外审查：
没有引入credential、跨项目权限或durable-state写入，现有来源与授权负向检查保留。
审查和离线通过不等于上传或平台验收。
本地允许提交、浏览器上传、平台审核、生成成功与用户成片验收是不同结论。
需要修复浏览器工具的 workspace roots 配置或用户手动选取这些原文件才能继续上传；
生成仍需要完整输入接入和用户先前要求的最终 Claude 审查。

## Learning Evaluation

使用 `record-ai-video-session` 记录真实阻断；`distill-ai-video-learning` 评估为
`no_candidate`：本轮仅有确定性代码验证和上传工具路径错误，不形成模型或制作质量经验。
