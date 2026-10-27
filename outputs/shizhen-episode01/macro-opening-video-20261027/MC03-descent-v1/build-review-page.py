from pathlib import Path
import json
V=Path(__file__).resolve().parent
fetch=json.loads((V/'fetch-result.json').read_text())
assert (V.parent/'失帧-下楼到达-1080p-2.0-试片01.mp4').exists()
page='<!doctype html><html lang="zh"><meta charset="utf-8"><title>失帧 · 下楼到达 · 试片01</title><style>body{background:#151719;color:#eee;max-width:1200px;margin:32px auto;font:18px sans-serif}video{width:100%}a{color:#a9d1ff}p{line-height:1.6}</style><h1>失帧 · 楼梯事件 · 下楼到达源</h1><p>Seedance 2.0 · 8秒 · 1080p · 原始声画 · MC03下楼到达，不含推门显露</p><video controls playsinline preload="metadata" src="失帧-下楼到达-1080p-2.0-试片01.mp4"></video><p id="review-note">当前版本待完整声画审查；使用三张下楼状态参考，实际动作尚未评定。完整楼梯事件仍需后续推门与反应源。</p><p><a href="失帧-下楼到达-1080p-2.0-试片01.mp4">打开／下载本段</a> · <a href="index-edit-v4.html">已认可市政剪辑段</a> · <a href="index-stairs-v1.html">保留的上一版失败原片</a></p></html>'
(V.parent/'index-descent-v1.html').write_text(page)
print('Review page built; quality NOT_EVALUATED')
