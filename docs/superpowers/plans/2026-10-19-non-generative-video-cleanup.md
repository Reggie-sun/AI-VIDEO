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

## Human Playback And Frontend Follow-up

用户实际播放第二版后报告严重绿紫偏色，并指出前端没有视频。FFmpeg重解码与静态MCP图均正常，不能代替实际播放器显示；第二版因此不构成合格观看交付。先停止旧候选的最终Harness，保留失败/中止证明，再修复实际观看结果，最后验证稳定源码。

- 保留`video-cleanup/1`与`development-repair-input/4`的RGB制作母版及历史bytes。新增独立`video-cleanup-viewing-proxy/1`，用显式本地工具生成H264/yuv420p、BT.709 limited-range、faststart观看版；实际核验色彩tag、源帧/PTS、原声PCM和时间。不把lossy观看版的像素与母版逐像素保护证明混用。
- Additive`development-repair-input/5`保留原捕获、`/4`母版和观看版三个身份；viewing.source必须等于master的exact local measurement，Registry同时保留完整父链。仍由同一bootstrap持久化、标准reader重开、UNBOUND/NOT_EVALUATED，Production activation fence不变。旧committer调用默认不加proxy以保留replay；Canvas面向观看的新入口默认提供观看版，同时返回master路径和SHA。
- 既有Provider Console catalog改进有界发现顺序，保留depth/entry/no-symlink上限；现有detail投影严格重开的`/5`观看角色与`/4`母版角色。媒体库默认展示观看版，母版在高级入口保留；支持受限relative workspace与exact媒体SHA的直接链接，截断catalog时仍能经既有strict detail读取显式目标。不新增index、状态库、Provider或renderer。
- 验证增加正常肤色/灰色/原色的真实转码测试，v5来源/篡改/失败不写入与前端投影测试，以及深证据/未注册frame dump的扫描回归、URL路径拒绝和观看角色筛选。实际新视频先经MCP与真实Chrome DOM/video/canvas/截图验证，再请求完整1×听看；人工与工程结论保持分开。

## Reopened Foreground-edge Repair

用户指出最后手到玻璃前仍有痕迹，重新打开此前局部观感接受，颜色接受保留。先用exact raw/master/viewing尾段逐帧定位，区分作者遮罩内容与kernel语义；保护矩形留下残影不等于合成算法缺陷。

本次限定一条本地完整候选：仅调整普通run计划中frame56–123的前景保护轮廓，plate0、补片、仿射与羽化参数保持，frame0–55计划不变；经同一公共bootstrap制作无损母版和正常观看版，不截尾、冻结、变速或生成。核验全部124帧PTS、原声PCM和保护像素，检查实际尾帧、动作边界及完整1×播放。此前三轮媒体复核的历史保留；因新反馈和已定位原因，允许一轮仅针对新候选的内容复核，出现blocking缺陷则由Parent继续调查能力边界，不机械开启下一轮。源码无已证实缺口时不改kernel、不重跑全仓工程；稳定文档scope按Harness验证并发布。

用户新截图重新否决该39da候选：所指姿势约在source2.5秒，主体残影在固定保护baseline内，上一轮并未处理整块残影。保留前述已消费单元与四轮历史；新有限单元最多四次局部静帧作者调整、一次完整本地候选及一次针对截图区域的复核，不重置历史或自动续第六轮。仅在普通run计划补充frame40–123扶杆左侧的plate0小补片与局部真实前景轮廓，保留原补片、源顺序/时间和原声；先检查截图匹配位置的native放大对照和手/袖口保护，再输出同一公共入口的完整观看版。无共享源码缺口不扩建runtime或追加全仓工程验证，原S01所有要求与STOP保持。
