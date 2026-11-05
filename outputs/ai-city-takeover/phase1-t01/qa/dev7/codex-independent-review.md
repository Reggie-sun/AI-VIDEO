# Codex Independent Review — T01 dev7

日期：2026-10-30。范围：dev6b→dev7 的 S3 有界修补、S1/S2 和时间码回归；只读检查，不签 Production 或人工验收。

## Verdict

**PASS（有界逐帧修补） / PARTIAL（完整声画体验）**。红1与HUMAN现有足够多帧的实际前态，f195同时切为白0与AI；dev6b中“计数已归零、标签仍是HUMAN”的可见矛盾已消除。未实际正常速度带声听看，不将本结论扩大为声音、节奏、运动自然或人类审美认可。

## Exact Identity

- 原片 `renders/T01-dev7.mp4`：SHA-256 `5e4601b0824b2cb82a42c9041178b0d3f06827f1d66de4e14755bf83b47a3697`。
- 审看衍生 `review/T01-dev7-review.mp4`：SHA-256 `f14a007a5ae6570336adc1edfb1b89d382247e00485be83f9f3c1e11e1009165`。
- 以下抽帧取自原片；未把衍生片当相同bytes。

## Evidence

1. 显式调用 project-local `video-analysis.video_review`，`frame_interval=0.5, max_frames=20, transcribe_audio=false`。返回1920×1080、30fps、10.022s、has_audio=true、issues=[]。与dev6b一样，自动工具仍返回scene_count=1，未完整检出真实的4/6s切镜；不据此签语义PASS。
2. 直接抽取并检查 **f180–195每一帧**的计数与标签裁切，再检查f196、f240、f241、f249的全景。f180（6.000s）红1处于入场淡显，未观察到可见HUMAN框；f181–194红1清晰且HUMAN稳定可见；f195（6.500s）同帧白0与AI。实际可见HUMAN前态为14帧（约0.467s），不能宣称从f180起有15帧/完整0.5s；已明显多于dev6b的两帧。
3. f194仍为红1/HUMAN，f195同时为白0/AI，f196仍白0/AI。没有旧片中0后再出现HUMAN的反向状态。
4. 当前S3逻辑用同一`takeoverAt`驱动计数、标签和hero的settle终点。hero `settle=takeoverAt-settleStart`，因此6.5s时`chaos=0`；其他光轨settle公式保持原值。静帧中hero笔画沿原路面分布。该数学检查证明参数同拍，不等于正常速度下“入相”观感已通过。
5. S1/S2回归：直接解码两版前180帧并缩为320×180灰度，逐帧平均绝对差的整体均值 **0.396/255**，最差帧均值 **0.730/255**。这是相似性证据，不能冒称像素相同；重新有损编码本身可产生小差异。现有QA中S1事件、S2切镜与禁用事件仍在±1帧内；未发现这一修补带来的明显S1/S2静态回归。
6. f240（8.000s）时间文字尚未显出，f241（8.033s）可见“·03:48”，f249（8.300s）清晰；与原先逐渐显入机制一致。QA对s3_time报告detected=240是自动ROI变化检测，不等于字形在该帧已可读。
7. 阅读`qa/dev7/report.md`：300帧、video_duration=10.0s；11/11事件±1帧，spec/sync/flash/frames_match_comp/pops/strobe/outliers均true。这些是对应技术范围证据。

## Gaps And Risks

- 正常速度带声音实际听看：`NOT_EVALUATED`；本次没有通过播放结束、抽帧或工具无issues来代签。
- S2前进感、扫描光在真实画面上的亮度峰值、hero入相的感知、末拍镜头停顿及全片节奏仍沿dev6b报告的证据边界；本次只修S3的状态顺序与可见时长。
- 临时guide audio不能证明Suno成曲、演唱、歌词逐字同步、对嘴或最终配乐完成。
- 本报告只新增自身；源代码、媒体、历史报告、接受状态均未修改。
