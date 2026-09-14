# Commercial Graphic Typography

`GraphicTreatment` 拥有广告文案的外观与 Shot 相对时间；
`resolve_commercial_graphics()` 将其投影到 `ResolvedCommercialGraphic`，
HyperFrames 从与视频和 P4 音频相同的 `ResolvedTimeline` 渲染。
本契约不改变 renderer、timeline、源视频音频策略或 candidate activation owner。

`font_weight` 是可选的 CSS 数值字重，范围 100–900、步长 100，默认 700；
`letter_spacing_px` 是可选整数，范围 0–16，默认 0。两者继续使用 renderer
已有的 `sans-serif` 字体选择，不授权任意字体文件、font-family 代换或
caption style 覆盖。`GraphicTreatment` 与 `ResolvedCommercialGraphic`
序列化时省略两个默认值，保持旧版 sealed artifact identity 稳定。
默认值也不新增 CSS 声明，保持原有 render source 外观与审计结果；
只有非默认值才覆盖既有 `.commercial-graphic` 字重。

几何序列化必须把 `width_milli=600` 保留为 `width:60%`，包括以零结尾的整数百分比；
错误缩窄的文字框会把单行广告语挤成竖排。HyperFrames layout check 与
最终媒体验收仍需执行；CSS 序列化正确本身不证明观感或广告验收。
历史 render source 若由旧版零尾格式生成，仅在审计既有 source 且文字样式均为
默认值时接受该精确旧格式；新 materialization 始终输出修正后的百分比。
