# S01 First/Last Frame Repair Preparation

## Status

最终更新：已执行一次真实首尾帧生成并下载，MP4 SHA256 `292aae3a02357a96e129879af07b19ff6340c37f801d8bc7833d82fa7b2588cb`，3,689,055 bytes。逐镜 **FAIL**：左手目标姿态约3.5–4秒才达到；准确广播等仍NOT_EVALUATED。详见 `preparation-v1/shot-01-gate.md`。一次submit额度已消费，无activation、无S02。以下准备状态保留为历史。

更新：用户已回复“同意”；新末帧 canonical import 已完成，receipt content hash 为 `c1ffc3e43f26f4f29c7ad276e67ab1429f9e909f30bd5c01413e37b8d5ac8bb4`。首尾帧请求 `83680c436cf3694be09a2982e1ac8d110ef5aafe2b5bdc41fd39e1a812649f68` 和 paid preview 已封存。以下“待确认”描述保留为前一检查点历史；当前尚未 submit，提交前审查进行中。

2026-09-06：仅完成新末帧候选、离线接入修复和 independent canonical bootstrap。没有新的视频 POST、MP4 或逐镜 PASS；S02 仍阻断。

- 输入首帧 SHA256：`4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
- 新末帧：`shot-01-last-frame-v1.png`，SHA256 `059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330`，941×1672、1,998,073 bytes。
- 新末帧由 `codex_imagegen_tool` 生成；agent 观察为左手手背朝镜头、掌心朝玻璃。该观察不是 human input-use approval 或视频质量验收。
- 用户对新末帧 exact bytes 的使用确认仍待回复，未创建 `endpoint-import-receipt.json`。

## Canonical Preparation

`bootstrap_project.py` 已成功执行并 strict reopen。Bootstrap 中 `last_frame` 暂时绑定原已注册首帧，仅用于建立可导入目标角色；它不是新末帧验收证据。`planning()` 检查新末帧的 exact SHA，在 canonical import 前拒绝继续。

确认新末帧后，沿 `HumanImageImportReceipt` → `import_endpoint.py` → `prepare_i2v.py` 继续。Receipt 必须使用真实用户批准事实和时间；不得把 agent 观察伪造成 human approval。

`live_i2v.py` 的 `EXPECTED` 故意为 `PENDING_CANONICAL_PREPARATION`；尚无新 profile、exact request、preview、intent 或 permit。完成导入后才可封存这些输入并执行有界单次调用。预期 Provider 是现有 Vidu Q3 Pro、4 秒、1080p、native audio、`is_rec=false`，两张实际图片通过 `/start-end2video` 传入。

本目录中的脚本是待完成准备，不构成 live-ready 声明。历史 attempt04 仍为已 fetched、逐镜 Gate FAIL，不能作为已接受连续性来源。

## Verification

- Planner/validation/import/Router/Vidu：386 passed。
- Reader/neutral requirement/runtime boundary/readiness 等补充检查：711 passed。
- 六个脚本 AST parse、`git diff --check`：PASS。
- 无 isolated Harness receipt：用户禁止 worktree；相关测试在当前 working tree 中执行。
