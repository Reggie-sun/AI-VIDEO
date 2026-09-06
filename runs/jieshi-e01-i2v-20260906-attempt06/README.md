# S01 Timing And Broadcast Repair

## Outcome

已完成一次Vidu Q3 Pro首尾帧生成，4.042秒、1080×1920、native audio。MP4位于 `production-s01-v6/state/video-generation/fetch/files/041de54a023082c24cb2d4cced4ba8d068569aebdf3330496f40615eaa9ae2a4.mp4`，4,111,052 bytes。

逐镜 **FAIL**：抬手约2.5秒达到目标，ASR广播内容/时长改善，但中段机位漂移、右侧乘客裁切。完整findings见 `preparation-v1/shot-01-gate.md`。未activation，未S02；一次submit已消费。

## Inputs And Execution

沿用05两张已批准、已登记的exact PNG及原HumanImageImportReceipt，没有新增human approval声明。
唯一实验变化是提示词表达：前2秒完成动作、后2秒保持，广播原句简洁独立表达；保留compiler2、model、duration、1080p、native audio和`is_rec=false`。

Bootstrap经canonical writer新建独立项目，包含末帧receipt引用的历史Shot文件；首次因缺此引用在durable write前拒绝，补齐exact bundle后成功。新profile仅续期内部上限时间；请求/preview/authorization由native reviewer_xhigh独立核验accept。首次下载被public HTTPS guard阻断，沿既有GET-only DNS恢复，未重复POST。

## Verification

四个脚本AST parse、diff check和canonical bootstrap/strict reopen通过。真实POST双图字节/sha断言通过，exact MP4立即调用project-local video-analysis。未改产品core，未运行额外测试或isolated Harness（用户禁止worktree）；live preparation review不等于媒体验收。
