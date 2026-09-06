# Jieshi S01 Local H3 Preview

Status: `FETCHED__MEDIA_GATE_NOT_EVALUATED__NO_S02`

## Result

已完成一次 local H3 native V2 I2VA：1344×768，124 frames / 24fps，5.167 秒，H.264 + AAC。生成约 104.17 秒。原生音频未替换，未制作正式竖屏成片。

- MP4：`production/state/video-generation/fetch/files/6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a.mp4`
- SHA-256：`6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a`
- Bytes：`1419435`
- 请求：`3a4ad6f82bc9ac67ae14220a1066647351b3e3564f1b930e6ab046781bc52367`

## Gate

`media-gate.json` 保存 exact MP4 的逐项判断。MCP 抽帧及原尺寸核对显示 2 站立 + 5 坐姿倒影，主角倒影缺席、左手抬起、右手手机和锁机位基本符合。

广播逐字内容与 0.1–2.7s 窗口未可靠验证；中文 base/medium 转写均不支持完整台词。原生音轨整体较低，mean -47.8dB，max -23.6dB。2cm 精确距离也无法由单一视角测量。因此整体 `NOT_EVALUATED`，不能推进下一 Shot 或宣称合格成片。

## Execution And Boundaries

实际代码路径为 `prepare_project.py` → canonical Planner/Router/compiler → `live_driver.py` → `VideoGenerationService` / `ProductionStateCommitter`。`submission.json`、`outcome.json`、`fetch-receipt.json` 为真实提交、观测与下载证据。不得再次执行固定 attempt 的 `submit`。

已执行 `EVIDENCE_REPAIR_FIRST`，没有隔离出可归因的 generation repair 变量，保留第二次预算而不随机重试。由本任务启动的 loopback ComfyUI 已停止。无 activation、S02、remote video 或 paid call。

代码修复提交 `6f5c0a1`；1184 项扩展检查通过，完整测试见 `verification.json`。用户限制未授权 worktree，标准 Harness 未运行。完整记录：`docs/record_for_agent/2026-09-06-jieshi-s01-local-h3-horizontal-preview.md`。
