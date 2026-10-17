# Native Audio Retime Implementation Plan

**Goal:** 让已有视频的画面与原声沿同一映射完成剪辑，无新生成。
**Spec:** `docs/superpowers/specs/2026-10-17-native-audio-retime.md`，Parent self-review；用户已同意继续完善当前剪辑版，必要共享修复归原任务授权。
**Invariants:** 旧map/2.0–2.3字节及行为保持；唯一ResolvedTimeline、P4 mixer、HyperFrames和committer；failed media不qualified/activate；外来index/dirty保持。

## Milestone 1: Sample Mapping And Failed-Source Admission

**Owner:** bounded writer A；Parent拥有共享`audio_retime_contracts.py`初始接口。
**Files:** `video_retime.py`、`composition_contracts.py`、`composition.py`、新`_composition_native_audio.py`、`repair_input_admission.py`及相应tests。
**Contract:** V2非静音map只允许2.4；resolver从同一VIDEO layer产生原P4 `ResolvedAudioSpan.native_audio_retime`；不信任caller自造sample时间。NativeAudioRetime连续覆盖exact trim与输出；捕获v3唯一有声源，旧v2不能携带A/V范围；development_preview只放行同源native spans，字幕及任意外加音轨仍拒绝。
**Acceptance:** 标准loader/committer的正常、错map/错源/旧schema/缺轨/alias activation失败路径与旧hash回归通过。

## Milestone 2: Native Audio Processing And Renderer Proof

**Owner:** bounded writer B；依赖共享typed接口，独占`hyperframes.py`、`models.py`、`project.py`、新`_hyperframes_native_audio.py`及相应tests。
**Contract:** 现有explicit FFmpeg/ffprobe接线传入source materializer；no-follow/hash验证后的MP4 snapshot解码，pitch-preserving分段tempo，严格sample补齐上界及逐段proof。P4仍只混合canonical samples，mixed WAV沿原source bundle和HF renderer输出；多次复用同一asset的不同map按track分别处理，不能覆盖缓存。
**Acceptance:** fixture正常/边界/失败与真实FFmpeg音调、时点证明；source receipt拒绝missing/tampered proof，旧WAV路径字节不变。

Architecture范围核验发现既有`hyperframes.py`、`models.py`、`project.py`均已超过800 effective LOC，
不能为新增能力继续增长。完成职责迁移：P4 mixer/WAV校验归`_hyperframes_audio.py`，
RendererAudioBinding归`renderer_audio_contracts.py`并由models兼容re-export，
完整source/timeline track校验归`_render_source_validation.py`并由project导入；旧API与唯一执行路径保持。

## Milestone 3: Public Integration And Actual Reused-Media Candidate

**Owner:** Parent；`canvas_composition.py`、`production_strategy_materialization.py`、policy及workflow/matrix、公开测试与记录。
**Contract:** Canvas/策略只在显式V2选2.4，跳过重复native WAV注册；实际robot从原failed source新封存v3并经原HyperFrames导出。画面采用窗和anchors保持，无direct mux、无Provider/凭据调用、无activation；所有要求和声音缺证保留。
**Verification:** focused公开用例→稳定exact-range适用Harness→Risk Gate及一名native reviewer审查（保留此前两轮历史）→owned commit/push main和remote SHA核验。真实导出显式project-local video-analysis、全部frame/PCM/时钟证据及独立可访问媒体复核；无法真实听看不代签human。

公开导入用例确认普通VIDEO使用local measurement而非generation probe；resolver按真实Registry来源
解析预期映射，materializer才对held bytes核验唯一音轨。测试覆盖同素材不同map复用、缺轨/双轨失败及
repair v2/v3先于普通IMPORTED分支的准入边界；不增加另一种导入凭证或修改失败素材资格。

## Completion

round3独立审查确认NA-001公开render缺轨/双轨在begin后才失败、NA-002非整除采样率下相对取整偏差。
必要修复沿共享held-source预检与既有global shot_start_frames；先RED再GREEN，适用Harness后只增加
一次同profile round4完整复审，保留已执行三轮及finding历史，不自动增加第五轮。
round4另发现NA-003：整数sample比值误拒合法frame倍率端点。Parent以实际44.1kHz/24fps fixture
复现后，修复有限量化包络；同例实际DSP短缺8967 samples超过1838上限，保持拒绝且不改算法/guard。
此后仅为该已调查的局部修复增加一次targeted round5，保留四轮历史；不自动增加第六轮。

更新原edit-first/robot进度与必要supersession，record/learning评估；工程能力、单源A/V preview、完整QA、Production/human分别报告。实现困难不构成结束理由；真实授权、unknown或不可取得的验收证据缺口才报告最小恢复条件。
