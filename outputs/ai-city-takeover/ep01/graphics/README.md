# IRIS Explanation Source Assets

这些素材只包含本地图形动画：`dns`、`pause`、`web-cache`、`cpu-cache`，各4秒、1920×1080、30fps、静音。范围为 `development_source_asset`，供之后经既有 Registry/CompositionSpec/ResolvedTimeline/HyperFrames 采用，不是整片、正式字幕、音乐时间线或 Production 验收。

## Build And Render

在仓库根执行：

```bash
uv run python outputs/ai-city-takeover/ep01/graphics/build.py
npx --no-install hyperframes render outputs/ai-city-takeover/ep01/graphics/dns -o outputs/ai-city-takeover/ep01/graphics/renders/dns.mp4 -f 30 -w 4 --browser-gpu --quality high
uv run python outputs/ai-city-takeover/ep01/graphics/inspect.py dns
```

每片渲染后，显式调用 project-local `video-analysis.video_review`，再查看 `qa/<kind>/contact-sheet.jpg` 与 `legibility-390.jpg` 逐项裁决并保存 `review.md`；工具不可用或局部要求不满足时不进入下一片。联系图与自动issues=[]不代替人类整体观看与最终接受。

## Editable Source

- `src/main.js`：通过 `hf-seek` 与 `waitUntil` 驱动的局部时间纯函数；前三秒推进、一秒完整停留。没有音轨，没有全片拍点或歌词。
- `build.py`：复用 `fonts.py` 做精确用字子集，再 esbuild bundle；各composition保留 `index.html`、`config.json`、`engine.js` 与实际字体。
- `motion-kit/src/news-graphics.js`：可复用Canvas2D绘制；可传 `transparent:true` 画入其他caller持有的局部图层。
- `inspect.py`：ffprobe、exact SHA、首中尾与390px联系图，不生成接受状态。

## Fact Boundaries

DNS图只说明有限路径；暂停日历只说相关最强研究工作，不暗示所有AI或ChatGPT停运。网页缓存方案早于事件；CPU缓存片明确标为另一项受控红队测试并与网页缓存分开。详细一手来源见 `../fact-check.md`。

没有图像模型、视频Provider、付费调用或云端egress；没有写Project/Manifest/Registry、激活或最终接受。正常速度观感仍需独立实际观看。
