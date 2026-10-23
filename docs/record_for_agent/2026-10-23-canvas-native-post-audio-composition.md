---
record_kind: architecture_implementation
topic_id: canvas-native-post-audio-composition
learning_eligibility: ineligible
---

# Canvas Native And Post Audio Composition

## Problem And Behavior

用户明确要求由subagent实现：配音与生成视频应按成片需要结合，没必要时才省略。此前e6798d5已加公共原声保留检查，但Canvas普通原声WAV自动绑定仍把“已有任意同Shot后期音轨”误当作“不再自动接入原声”的条件。因而已有旁白或音乐且另有唯一可用同源WAV时，compose会错误拒绝，虽然原P4 mixer本来支持共同混音。

现仅按精确source匹配判断是否已有原声绑定：已有则保留，不重复建轨；没有则自动补入唯一匹配WAV，与已有后期轨一起解析。零个或多个未选择来源仍拒绝，无关旁白/音乐不能充当原声。显式MUTE/REPLACE、所有原source/trim/coverage检查、native变速约束、VoiceRouting/Registry/accepted-sequence资格及唯一ResolvedTimeline/HyperFrames mixer不变。没有增加Provider、schema、状态、选择器或渲染路径。

将创作判断写回现有open-video Creative Completion与电商G4音频reference：在声音方案说明旁白作用，省略要有内容理由，不能因原片有音轨就省略；恢复原声时逐轨保留仍有用的配音、音乐和拟音，只调整重复/冲突。它约束Agent选择，不声称validator能自动理解配音必要性，不强制每片旁白，不以此取消voice能力/预算/授权检查。

## Verification And Evidence

原生code_mapper只读定位，bounded_worker独占canvas_composition.py及既有test_canvas_native_audio_retime.py；Parent维护上述reference与source-audio-composition.md，并在交接后核对候选。Worker先新增公开compose回归复现RED：两类已有后期轨均被原条件错误拒绝；修改后13项通过，补PCM后14项通过。测试涵盖旁白/音乐组合、原声不重复、主动静音仍保留后期配音、缺失/歧义不能冒充来源。

PCM测试沿compose_canvas→materialize_hyperframes_source读取实际48kHz stereo WAV，以440/880/220Hz确定信号分别核验原声、-6dB且淡入的旁白、以及由旁白ducking -12dB的音乐均存在。仅generated-audio owner lookup使用脚本化fixture；公共composition/source guard及实际mixer保持真实执行。该证据证明所测路由/采样混合，不证明完整accepted-sequence receipt链、真人对白或成片听感。未生成新配音或改写原17秒成片。

正式Harness在exact staged tree `3b0f7faa10979844fd9a0994d2ffda2a6e01f928`中隔离其他未提交工作，原声音频73项、Canvas workflow 354项及前置文档/规则/架构检查通过。随后电商Skill组94 passed、1 failed：既有文档测试仍断言历史AGENTS的outcome known、旧链接文案与长句，当前HEAD已使用known outcome及精简表达。Parent只同步该测试对当前已有MCP时点、PASS barrier、FAIL/NOT_EVALUATED STOP、unknown STOP及local known-outcome条件的断言，不修改或削弱AGENTS/执行Guard；单项复验通过。原FAILED receipt保留，不重签完整Harness PASS。

最终候选仅增加该测试兼容修正与本记录补充；运行实现与前述73/354项验证完全相同。其余未运行/失败组在最终exact staged隔离快照中进行有界补验，不因文档断言修正重复73/354项。证据目录为runs/canvas-native-post-audio-20261023-001；原正式Harness为.agent/harness/runs/canvas-native-post-audio-20261023-001/receipt.json，最终补验、范围映射、提交及其限制见前者completion-receipt.json。当前dirty working tree的agent_rules_check曾因非本任务AGENTS.md超预算而失败；该文件未修改，不将其与隔离快照混淆。

本修复适用于普通Canvas中已登记原声WAV与既有P4配音的组合；VoiceRouting SEPARATE仍要求生成视频native_audio=false，不外推为新资格化的routed TTS + 同源生成原声路线。现有native time-map与音轨映射要求同样保留。

Parent Risk Gate：NATIVE_REVIEW_NOT_REQUIRED。实现为只读authoring自动组合条件修复，既有source资格与公共拒绝边界保留，无凭据/付费/Production持久化效果；针对缺失、歧义、重复与实际PCM的验证覆盖具体风险。worker参与不冒称独立审查。

## Completion And Learning

只提交本任务文件，保留其他会话dirty/index工作；按项目要求在稳定验证后提交推送并核验远端SHA。此任务不调用Provider、不消费积分、不发布视频，不重跑真实影片或听音。工程证明不代签人工作品认可。

record-ai-video-session评估recorded；distill-ai-video-learning评估no_candidate：这是确定性修复与脚本化回归，不以多个测试、信号或同一媒体链版本冒充独立质量实验，不创建学习占位或修改其他Policy/Gate。
