# Non-generative Video Cleanup Implementation Plan

## Goal And Authorization

用户明确要求“补上这个通用能力”。在现有素材准备、失败源诊断准入和Canvas入口中增加跨作品可复用的clean-plate局部修补；不调用生成模型，不修改原失败历史。此前两张静帧只证明局部可修性，本计划不把它当作完整视频或通用质量验收。

## Contract And Ownership

- `video_cleanup_contracts.py` / `video_cleanup_pixels.py`：显式frame index、同视频plate frame、多边形软遮罩、逐帧plate-to-output仿射变换及foreground保护区。无自动对象识别、自动跟踪或生成填补；显式跟踪数据由作者提供。每帧先保护原像素，再局部合成；缺帧、非法几何、非有限/奇异变换、越界采样拒绝。
- `video_cleanup_media.py`：注入的本地FFmpeg/ffprobe执行file-only解码与lossless RGB源素材准备。检查CFR、零视频起点、帧数/几何/PTS一致及输出重解码像素；保留0或1条原声音轨并比较PCM与声音时序。明确资源上限，不安装依赖、不隐式选择工具、不改变源顺序/trim/speed。该输出是派生源素材，最终renderer仍为HyperFrames。
- `video_cleanup_admission.py`及既有`repair_input_admission.py`：新增`development-repair-input/4`，保留原`/3`捕获资产/receipt、Provider probe和完整失败链；另封存派生MP4、local measurement、recipe、工具及像素/声音证明。不得用新probe冒充原Provider产物。标准Registry重开两份资产和exact provenance。
- 既有`ProductionStateCommitter.bootstrap_repair_input`增加显式cleanup参数；所有持久写仍经同一bootstrap。Canvas/CLI提供显式调用入口和可审阅结果，不创建第二Manifest、timeline、renderer或验收状态。
- 新派生资产继续是UNBOUND、qualification NOT_EVALUATED、development preview。原`/1–3`序列化/hash及原failed attempt不变；禁止绑定Production Shot、激活render或推动S02。

## Acceptance Criteria

1. 公共数据入口可以表达并执行任意同尺寸源视频的局部补片，不含故事名/人物名/坐标特例；故事坐标只在run内的作者计划。
2. 多种人物替身、图案和几何的fixture验证平移/仿射、羽化、保护区、未编辑帧及多个补片；正常/边界/失败路径不执行Provider。
3. 实际本地视频验证所有源帧顺序/时间不变、lossless输出重解码符合合成、保护像素零变化；原声PCM及时间不变。无法可靠保持的输入显式拒绝。
4. 标准loader重开v4派生及原捕获；篡改源、输出、plan、measure/proof或source Registry linkage拒绝，Production quarantine及旧版本回归保持。
5. 在真实S01完整素材上制作可播放的非生成修补候选，显式video-analysis及独立内容复核实际效果；局部修复不代签其余缺证/人工听看。没有新生成POST。

## Milestones And Verification

1. Parent定契约；唯一worker实现pixel contracts/kernel及`tests/test_video_cleanup_pixels.py`，先RED后GREEN。Parent负责其余文件，互不覆盖。
2. Parent实现bounded local media preparation、source-preserving receipt与synthetic真实视频验证；跨场景像素用例只证明工程行为。
3. Parent沿原repair bootstrap/Registry/Canvas入口集成v4，补canonical loader、replay、tamper、quarantine与CLI验证；不增加普通Production通过路径。
4. 使用同一公共入口处理S01，保留未处理原片与recipe/工具/输出SHA、源声音证明。先取实际效果，再做最终工程发布检查。
5. owned bytes稳定后跑适用Harness与Architecture Gate，根据SUBAGENTS Risk Gate判断独立代码审查；因新增派生源信任边界，需检查验证是否仍有重大缺口。记录、learning评估、owned paths commit/push main并核验远端，保留foreign index。

## Limits

首版支持显式逐帧对齐数据，不承诺自动光流/平面跟踪、任意遮挡重建或缺失背景恢复。无干净底片或无法保护真实前景时，保留失败而不是模糊/冻结全画面。真实修补是否自然与工程零变化证明分别验收。
