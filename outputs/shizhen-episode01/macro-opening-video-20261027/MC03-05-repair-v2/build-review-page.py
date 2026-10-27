from pathlib import Path
import json
V=Path(__file__).resolve().parent
fetch=json.loads((V/'fetch-result.json').read_text())
assert (V.parent/'失帧-楼梯异常-1080p-2.0-修订02.mp4').exists()
page='<!doctype html><html lang="zh"><meta charset="utf-8"><title>失帧 · 楼梯异常 · 修订02</title><style>body{background:#151719;color:#eee;max-width:1200px;margin:32px auto;font:18px sans-serif}video{width:100%}a{color:#a9d1ff}p{line-height:1.6}</style><h1>失帧 · 第二段 · 楼梯异常修订02</h1><p>Seedance 2.0 · 12秒 · 1080p · 原始声画 · MC03–MC05</p><video controls playsinline preload="metadata" src="失帧-楼梯异常-1080p-2.0-修订02.mp4"></video><p id="review-note">当前版本待完整声画审查，静态首尾帧和生成成功均不等于视频通过。</p><p><a href="失帧-楼梯异常-1080p-2.0-修订02.mp4">打开／下载本段</a> · <a href="index-edit-v4.html">已认可市政剪辑段</a> · <a href="index-stairs-v1.html">保留的上一版失败原片</a></p></html>'
(V.parent/'index-stairs-v2.html').write_text(page)
print('Review page built; quality NOT_EVALUATED')
