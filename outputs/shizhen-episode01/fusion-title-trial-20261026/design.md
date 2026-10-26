# Fusion Title Trial

## Scope

用户“那你先尝试做下”，在现有独立开场基础上试用已接通 Fusion。仅尾段合成，原有核心事件、四句对白、音乐、20.375 秒节奏不改，不含 S01，不产生付费生成。既有全目标宏观视觉和真人质感缺口继续保留，不以本次片名试片代替完成。

## Direction

只使用原 A3 帧 288..359。文字占左侧原人物缺席区域，女人在右继续通话。与旧版大块黑色图形相比，本次保持雨夜空间可见，错落的宋体字由底片雨玻璃的亮暗调制，无额外头灯、闪屏和新异常。完整标题在后半段稳定可读。细立框遮挡只限实际位置，不切断关键字形。原素材 AI 标识保留，时钟沿旧 ResolvedTimeline 从 03:17:18 续至 21。

## Bounded Execution

Fusion 负责单镜头层与图形，既有 HyperFrames 保持最终声音与输出责任。最多两轮局部视觉修订、每轮 72 帧；先检查实际静帧及运动，不以 API 成功代替观感。所有输出留在本目录及独立 run，不覆盖 R3。无外部脚本服务、网络脚本或无限重试。

## Known Runtime Incident

开始时 Resolve 已崩溃，日志明确 `collate_byname<char>::collate_byname failed to construct for en_US.UTF-8`，堆栈在 Fusion GetKeyMap；本机 locale 列表无 en_US.UTF-8。使用 localedef 在 `~/.local/share/ai-video/resolve-runtime/locale/` 创建独立 locale，并以 LOCPATH、LC_ALL=en_US.UTF-8 启动本次进程，不改系统默认语言。参考为 Blackmagic 官方论坛用户实际报告 https://forum.blackmagicdesign.com/viewtopic.php?f=40&t=221161；当前版本须以实际复测为准。

## Concept Review

独立 reviewer 指出空钟牌会成为额外异常：采纳，继续原后期时钟。指出任意扫光缺动机：采纳，取消新增灯带。指出立框遮挡须匹配实际几何：采纳，只使用真实立框窄区。字体试验不是新灵异机制，也不伪装成正式完成版本。
