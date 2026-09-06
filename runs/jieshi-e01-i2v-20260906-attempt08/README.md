# S01 Broadcast Timing Repair

Vidu Q3 Pro首尾帧，4秒、1080p、9:16、audio=true、is_rec=false。沿用已批准双图，仅修改广播起声和语速要求。

一次POST已完成并fetch；实际MP4位于`production-s01-v8/state/video-generation/fetch/files/cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e.mp4`，3,232,566 bytes。

project-local video-analysis及97帧检查已完成。广播segment结束约2.14秒；继续时核对封存请求，纠正整镜Gate为 **FAIL**：要求第2秒前达到末帧姿态，实际约3秒才转正。全速听感、约2cm间距、胸牌细节与最终字幕仍未完成验收。完整证据见[Gate](preparation-v1/shot-01-gate.md)。未激活、未提交S02。

本目录是已消费的一次attempt历史证据，不是可重新执行的授权。不得直接重跑live脚本或将profile续期视作新增submit额度。
