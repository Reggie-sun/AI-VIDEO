# Lost Frames Cold Open — Composition And S01 Handoff

## Protected Sources

S01采用`outputs/shizhen-episode01/失帧-第一集-S01-1080p高清版-Seedance2.5-16秒.mp4`，SHA-256 `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，51,142,682 bytes，1920×1080，16.065秒，385帧，内嵌44.1kHz stereo AAC。MCP的nominal fps读60不证明CFR60；最终timeline按实际PTS与24fps规则处理，不直接按60fps算trim，不用补帧重生保护源。

原文件不改、不裁头、不覆盖。默认从首帧进入，保留全部人物、饭团／垫纸、黑金瓶咖啡、动作、对白与原音。不要为做“从街外推进便利店”的过门再生成S01头部，也不在雨站安排林序路过或偷听，避免无证据地使他已经知道异常。

当前双语字幕审看副本SHA-256 `3bbf15995bac0e91033be3689b12f16ad1e09f9eb8a78d53a80cb2724a0d16a1`，16秒，其user review仍PENDING。字幕源与原片保持各自identity。不可将其视为16.065秒无损替代，也不从烧录字幕版再OCR或二次烧字。后续选择原有字幕轨路径时重新检查原音时基；37秒只是方案预算，不能直接给所有字幕固定加37秒。

## Assembly Order And Timing

顺序由这版coverage交给唯一Composition owner：CO01 → CO02 → CO03 → CO04 → CO-TITLE → **S01完整源** → 原后续故事。`ResolvedTimeline`独占帧、sample、trim及字幕offset；本包没有可执行的第二条剪辑时间线。

片名与S01是明确的**翌夜场景边界**，不是从雨站连续走到便利店。片名尾部完整收掉配乐与雨站声，再在S01首帧进入S01原音；默认不做覆盖S01的J-cut或音乐尾音，避免双份车流和对白遮盖。先用这个保护性接法听看，若需要跨界声桥，也只能在新开场的尾端调整，不截掉S01。

输出沿正式规格1920×1080、24fps、MP4/H.264、约15–20Mbps、AAC 48kHz 256–320kbps。源44.1kHz音频须经现有派生owner解码／重采样登记后进入P4；不把内嵌AAC默认当作自动进入成片。视觉素材在现有renderer里muted，S01显式原声轨必须存在且只存在一份。

## Exact Text And Graphics

| Item | Text | Placement / responsibility |
| --- | --- | --- |
| 开场定位 | 临江 · 前一夜 | CO01画面下部安全区域，避开人物与未来对白；轻量，不做说明旁白 |
| 时钟前态 | 03:16:59 | CO03遮挡前，实际站牌平面，后期准确合成；要可读但不做倒计时特写 |
| 时钟后态 | 03:17:11 | 同一站牌位置与字宽，遮挡后；之后按实际叙事时间自然走字，不永久冻结11 |
| 主片名 | 失帧 | 透明矢量字形`assets/title-shizhen.paths.svg`，由P4摆在冷黑底；不让视频模型生成文字 |
| 场景时间转接 | 翌夜 | 片名末段小字；先告知转场再进S01，S01本身不叠新字 |
| 原终场片名 | 失帧 | 保留原剧本结尾；当end slate处理，不再复演完整片头 |

片名字体源为本机`NotoSansCJK-Regular.ttc`的SC字形；资产将“失帧”转成真实path，没有运行时字体fallback依赖。保留静态完整字形，只在P4对两字间距作一次轻微、不改变可读性的空隙变化。无数据瀑布、RGB错位、闪白、血字或三枚符号Logo；字体轮廓资产不是已渲染片名，也不证明动态效果通过。

## Dialogue Caption Preparation

首轮先审新原片；用户认可后再自动做字幕，沿当前中英双语选择、句尾无符号。下表是逐字文本准备，不含伪造时间码；实际speaker／发声窗口由最终原声裁定，电话声同样由该owner对齐。

| Speaker | Chinese | English |
| --- | --- | --- |
| 罗敏 | 师傅，我们在站里，两位 | We're at the shelter. Two of us |
| 高峥 | 让他别急，路滑 | Tell him to take it easy. The road's slick |
| 罗敏 | 听见没，慢点开 | Hear that? Take it slow |
| 司机／电话 | 就你一位 | Just you |
| 罗敏 | 嗯，就我一个 | Yeah, just me |

不要用字幕补写“高峥消失了”“所有人忘了他”或“十一秒”。中文内部标点可以保留，句尾不加符号；英文句内句号／问号不等于句尾标点。正式字幕遵已选排版规范，不能把这个准备表当作timing证据。

## Sound Allocation

| Existing track kind | Source / obligation | Avoid |
| --- | --- | --- |
| dialogue | 新镜实际原声中两人的台词＋司机电话声；必要后期修复仍按同一voice route | 偷用林序／妹妹声线、把高峥的声线配给司机、重复台词 |
| ambience | 雨棚近雨、远车流；跨CO01–04保持同一世界 | 异常时所有轨道数字静音、每个切镜重启一遍雨 |
| sfx | 货车经过／声尾、镜片衣料等实际动作 | 雷击、怪物低吼、刺耳频闪音、双份货车 |
| bgm | 已采用actual Suno cue，事件后进入、片名接续、S01前退尽 | 原生模型随机配乐与新配乐同时存在 |
| S01 dialogue/ambience | 受保护S01原音由既有合法派生路径明确绑定到P4 | 只加muted visual MP4造成无声S01、重复混入或强降噪 |

各轨gain、duck、fade由现有`AudioTrackSpec`等owner在actual samples上决定；本包不凭空给音乐分配精确起点或声压验收数。雨站新原声如含随机音乐，先标出与目标冲突，不能一键删掉整条音频而丢对白／动作声；回原音频owner选择能保留必要声音的修复。

## Acceptance Allocation

下表仅是交给现有QA author的要求提案，不是已经封存的`FinalOutputContract`或可签PASS的rubric；hard basis、stage、measurement、tolerance与proof须由原owner独立批准。

| ID | Observable result | Evidence owner / boundary |
| --- | --- | --- |
| CO-RELATION | 两名普通人可辨，接车目的、听说因果自然 | 每个raw Shot的身份／表演；exact原速声画，不靠人数检测分数 |
| CO-EVENT | 同构图两人→遮挡→一人，无走开／上车／残影／遗物 | CO03 exact连续视频＋出口／地面／道具核验；若allocation改变，保留raw与assembly各职责 |
| CO-FORGET | “两位→就我一个”，罗敏无保留记忆行为 | CO02与CO04的exact对白和完整反应，结合整段语义观看 |
| CO-RULE | 前一夜、既定03:17缺口、不新增触发法则、不泄底 | 文字审读＋最终片头图形与整集上下文；不是单镜CV可裁决 |
| CO-ART | 成年D版CG语言贯穿背景与两名新角色、空间不漂移 | 实际参考局部查看＋每镜／整段原速审片；S01风格正确不自动证明新镜 |
| CO-SCORE | 原创器乐、无突发惊吓、空位先成立、主动留白 | Suno来源／权利边界＋实际音乐审听＋exact混音；无音乐保持NE |
| CO-TEXT | 片名正确、时间准确、字幕无句尾符号且可读 | P4 actual encoded MP4按边界帧核验，不用SVG或SRT单独证明 |
| CO-S01 | 原片与记录未改、首字／全动作／原音保留、字幕路径清楚 | 源SHA保持、source-use/trim/sample readback、S01全段声画对照与exact输出 |
| CO-ENDING | 片头不含终场答案，片尾原雨声／反转保留 | 全集剧本和未来actual整集审看；当前后续场面未制，媒体结论NE |

最终交用户审看的应是正常速度的**冷开场＋片名＋完整S01**，同时保留新开场独立原片；方案、音乐dry-run、静态片名与抽帧都不能替代它。当前仅准备完成，不宣称完成新开场、音乐、混音、P6或Final Acceptance。
