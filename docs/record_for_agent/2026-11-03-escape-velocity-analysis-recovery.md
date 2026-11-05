---
record_kind: research_note
topic_id: escape-velocity-reconstruction-analysis
learning_eligibility: ineligible
evidence_index_version: "1"
---

# ESCAPE VELOCITY Analysis Recovery

Date: 2026-11-03

## Scope And Status

用户要求读取 Claude session `7ba6b3ef-4ca7-482a-ae07-ede0dd151135` 并继续。已读取 exact JSONL：原任务最后明确限定完整逆向分析、结构化记录与参考帧提取，**不开始复刻，不生成视频，不调用付费生成模型**。先前 Claude 额度中断，Phase A 有153镜边界，Phase B没有落盘。

本次继续使用 Codex 原生子代理按S0001–S0051、S0052–S0102、S0103–S0153分配唯一writer。已完成153镜JSON与逐镜Markdown、1209元素的详细视觉复核及聚合；S0095–S0102、S0144–S0153由主会话接回完成，其他分镜writer已释放写入。主会话另审全片总览及29个低置信度边界。当前不能宣称高精度音画分析全部完成：直接音频听审仍为NOT_EVALUATED；最新数量和状态由下列JSON及QA报告提供。

分析根目录：`outputs/anabology-opus55-replica/escape_velocity_analysis/`。

## Verified Source

- 本地原视频：`outputs/anabology-opus55-replica/source/2103533196721704960.mp4`。
- fresh SHA-256：`bf3595f1f615a6bc66b8925680e28849e12eeb57ec5c7f93420a95e3fe37a40d`。
- fresh ffprobe count：1920×1080，24fps nominal，7353 decoded frames，画面306.375秒；容器306.481秒，AAC stereo 44100Hz音频306.480181秒。容器报告7354帧与实际可解码数量不同，原作者master也报告7354，不能抹平差异。
- `work/frame_pts.json`有7353条，帧PTS与`frame_index/24`的最大偏差约0.333微秒。
- `qa/source_audio_identity.json`：fresh原MP4解码的stereo44100 PCM与现有mix.wav样本字节哈希相同；只证明分析底稿identity，不证明听觉质量。

## Current Artifacts

- `manifest.json`、`timeline.json`、`shots/shot_NNNN.json`为技术参数、分镜和独立元素事实；`elements.json`聚合分镜，不另编事实。
- `audio_timeline.json`保留CTC与Whisper候选、节拍、频带onset与来源/时序不确定性。`qa/audio_alignment_review.json`列出交叉检查异常；结尾Francisco的强制对齐长度约14.686秒，派生记录改选Whisper候选，保留原测量。
- `source_mapping.json`核验30份公开资料快照哈希，索引636条作者素材元数据，153镜到Seedance公开歌曲时间窗相交的关系只标inferred，不宣称exact plate/clip identity。作者141镜storyboard与本地153段不能按ID等同。
- `synchronization.json`给视觉事件稳定ID和音频候选的时间对应，不能当作可听同步或因果锁拍证据。
- `qa/root_visual_review.json`：主会话实际查看13张总览，覆盖每镜中帧；另有分镜writer的filmstrip、首中末与detail证据。
- `qa/boundary_second_review.json`：主会话实际检查29个低置信度切点的前后帧；保留原take切换与合成内跳切/重构图分类歧义，未任意重编号。
- `work/full_batch/`含单次FFmpeg解码提取的1594张1920×1080参考，`index.json`绑定原视频sha。覆盖每镜首中末、首末附近每2帧及<=12帧短镜全部帧。原有960px逐帧缓存继续用于密采。
- `README.md`、`analysis_report.md`、`reconstruction_plan.md`由`scripts/17_build_documents.py`从JSON生成，附输入哈希；分镜Markdown由既有`08_gen_shot_md.py`生成并校验JSON哈希。

## Verification Boundaries

`validate_phaseA.py`五个chunk均0 errors。逐镜schema、引用、聚合与Markdown一致性由`validate_all.py`检查；不能用schema PASS代替内容完整。

新增`15_validate_delivery.py`调用原完整性检查，并区分INVALID_PACKAGE、ANALYSIS_INCOMPLETE与REVIEW_COVERAGE_COMPLETE。fresh结果为153/153 detailed、1209元素、4242音频候选、4080视觉/音频时间对应；结构错误0，唯一unfinished为音频听审/SFX identity，exit 2 = ANALYSIS_INCOMPLETE。验证器失败路径测试覆盖必需文件缺失、重复聚合元素、悬空音频引用、PARTIAL误报完成和基础validator失败；独立review后新增同ID元素payload漂移、timeline派生字段、镜内事件与音频章节漂移测试，8 tests PASS，30个Python脚本AST解析PASS。记录见`qa/local_script_checks.json`。

已对仅本任务owned paths的exact staged snapshot运行Harness focused verify，exit 2：`focused verification requires a module mapping`。失败记录在`qa/harness_focused_attempt.json`，绑定staged tree `26b2553ec96e99e58f2f3a5696e860a702e82e14`；Harness在映射检查前置失败，没有生成完成receipt。未扩大运行整仓测试，未修改Harness映射，不能把本地数据验证报告称为Harness工程完成receipt。

## Independent Review

原生只读review绑定16个文件的SHA，发现并修正：聚合payload漂移漏检、S0151诊断框坐标、S0152独立角度标签、S0100来源footer和S0152 leader转录。逐帧补正so出现于7289、back开始7300、全黑字7311；修正片尾标签bbox与文字。修正后独立review确认原3项findings全部解决，目标SHA未漂移，153个Markdown哈希匹配。见`qa/independent_review_target.json`与`qa/independent_review.json`。该scoped approval不证明全部153镜内容绝对准确，也不补音频听审。

## Audio Evidence Gap

native media reader返回`audio content omitted because you do not support audio input`。project-local `audio_understand`只做离线preview，因原文件不在该工具允许的媒体根目录而返回`invalid_media / EVIDENCE_GAP / retryable:false`；没有execute、外传、付费或重试。未移动文件来绕过边界。

因此没有直接听审证明；ASR、forced alignment、频谱和stem onsets不能签署音频语义、独立SFX来源或人的听觉验收。未知项保留unknown；逐镜详细视觉观察完成不抹平音频证据缺口。后续优先补真实听审与可定位的逐镜遗漏，不能用更多空泛模板代替。

## Learning Evaluation

`no_candidate`。本次是一个参考片的恢复与分析链，没有两个独立制作尝试或受控多臂比较，不提出通用制作能力结论，不修改Skill、Policy或Gate。

## Publication

当前为视觉分析完成、音频证据受阻的checkpoint。未开始复刻或生成，未付费。exact staged Harness检查因focused缺映射阻断；依仓库规则停止提交/推送，不改policy或扩跑完整套件来掩盖缺口。仅本任务stage用于验证，随后恢复为未暂存，文件仍完整保留本地。保留其他并行dirty/staged工作。精确媒体和部分大型cache受Git忽略，Git存在性不等于本地参考包完整性。
