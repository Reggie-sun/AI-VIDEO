# Native Audio Retime

## Goal And Authority

用户同意继续完善并验收既有几何人物剪辑版，保留此前跨项目复用目标。原authoring明确`audio_need=required`、`muted=false`；只交静音版不足。Parent在任务内共享契约授权下补必要能力，原静音实现及历史证据保留；不授权新图片、视频、音频Provider POST。

## Contract

- 保留原`video-time-map/1`只静音及所有旧序列化/hash；新`video-time-map/2`显式`audio_policy=retime_preserve_pitch`，只由`CompositionSpec/ResolvedTimeline 2.4`消费。画面仍按原整数映射采样。
- 原声绑定同一visual layer、同一VIDEO asset/hash、唯一原生audio stream0；不把失败视频提取成伪qualified WAV，不用普通import清洗来源。独立WAV P4不变；同镜/全局额外音轨、字幕和voice仍按原拒绝边界处理。
- `ResolvedTimeline`独占将各frame anchor解析为source/output sample区间；输出沿原`audio_spans`，不增加第二timeline、audio状态库或renderer。Native spans显式记录visual layer、map hash与连续sample segments；输出sample边界使用同一全局frame anchor后减Shot起点，避免非整除采样率下相对取整差一个sample。
- 普通imported VIDEO的Registry本地测量不是generation probe；按其真实来源解析预期sample map。新native render在begin前对held bytes检查音轨存在性/唯一性，缺轨/多轨不改Manifest、不调用renderer；materializer仍重读并验证exact bytes，已有attempt沿原replay且不重复预检。generated/captured源继续重开exact probe；repair provenance必须先于普通import分支核验，旧capture不得借IMPORTED标记进入A/V。
- HyperFrames source materializer使用已注入、hash绑定的FFmpeg/ffprobe从exact MP4 held snapshot解码。首版要求video起始时钟为0且唯一原生音轨；正向音轨起始偏移按PTS保留，负向或不可可靠解析的起始时钟拒绝，再按sample map运行`atempo`。倍率拆为0.5–2的乘积，避免大倍率直接跳采样。
- `atempo`输出可能与目标sample数略异；仅允许逐段不超过一个输出frame的尾部trim/pad并逐项记录，超限失败，不静默补长段静音。处理结果仍须音质/同步验收，不能把结构对齐当音义或自然度保证。
- Frame map独占精确`0.1–5`倍率验证；两轴sample窗口各有不到一个sample的floor差误差，sample层仅用该有限整数包络拒绝真实越界，不重拒合法端点。合法frame map仍须实际DSP输出通过尾部修正上限，不能把domain验证当作音频可处理/质量资格；超限保留明确失败，不回退静音或生成。
- 同源原声的节奏与时点跟随画面映射，保音高不保留原绝对时刻；额外音轨、字幕或voice时序尚无对应映射时仍拒绝，不能宣称原节奏或口型已通过。
- 既有RendererAudioBinding/bundle receipt绑定source VIDEO、stream、input/mapped PCM、map、每段实际sample修正及工具hash。旧无此字段的binding字节不变；reader拒绝proof缺失或映射/来源不一致。
- `development-repair-input/3`封存显式A/V用途及有音轨的exact probe；`/1`、`/2`含义不变。失败素材与新原声仍UNBOUND/NE、development_preview，activation的scope及alias保护保留，不制造accepted state。
- 普通Canvas同一time map选择retime时不再要求mute且不额外自动登记另一份native WAV；明确mute路线继续原样。通用Production策略材料化保留map版本并选2.4。

## Verification And Limits

用不同FPS/源trim/分段长度验证sample解析、旧hash、缺轨/错源/旧schema/metadata漂移/错误proof/失败素材activation拒绝；用真实本地FFmpeg合成可识别信号验证pitch与时点，再经pinned HyperFrames导出验证实际音轨、sample数与视觉帧不回归。
真实robot只复用已消费MP4，生成新的A/V development preview及完整逐项观察；原Manifest、消费及STOP不变。当前模型不支持直接audio input；缺真实听音、整段自然度或human证据时明确NE，不借旧Gemini unit或新付费调用补证。

官方机制参考：[FFmpeg atempo](https://ffmpeg.org/ffmpeg-filters.html#atempo)。本地可行性已测三段原声，原始输出相对目标分别+51/-947/-808 samples，故必须记录sample修正。
