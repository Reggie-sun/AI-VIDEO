# r2 本地有界合成（comp.py，羽化 24 px，只向框内羽化；框外逐像素等于原图）

框是 Codex 编辑件与原图差异图里左臂与外套垂布那一块（`/tmp` 差异图：高斯 6 px、阈值 18），避开脸、嘴、耳挂（p048 耳挂在 1289,204；p047 在 888,180）、工牌、隔板与纸条指尖。

- p048-arm-a|b-comp：`comp.py board/plates/p048-w1.png CONT1124/p048-arm-<x>.png CONT1124/p048-arm-<x>-comp.png 24 1236 392 1478 682 1366 682 1478 884`（a 接缝环均差 5.53，b 5.17；outside_identical True）
- p047-rc-a|b-comp：`comp.py CONT1124/p047-rb-b.png CONT1124/p047-rc-<x>.png CONT1124/p047-rc-<x>-comp.png 24 826 298 1142 812 950 640 1246 896`（a 4.35，b 5.34；outside_identical True）。第一次的框（826 298 1142 650 + 950 640 1246 896）在左下留了旧袖子的残影，删掉重合。
- 推荐：p048 取 b → `board/plates/p048-w2.png`（逐字节相同）；p047 取 a → `CONT1124/p047-rb-c.png`（逐字节相同），`tools/upscale_lanczos.py` 出 `p047-rb-c-2944.png`。
- 检查：`tools/check.py`（全图、240 px、开场脸 face-P016b / face-F1a 对照、红色）→ `check/CONT1124-p048-arm-*-comp.jpg`、`check/CONT1124-p047-rc-*-comp.jpg` 与同名 .json；四张的红色像素与原图完全一致（只有耳挂灯和唇色的几颗松阈值像素，都在框外）；左臂原尺寸对照 `check/r2-arm-zoom.jpg`。
