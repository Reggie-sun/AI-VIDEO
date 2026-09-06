# S01 First/Last Frame Repair Preparation

## Status

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
