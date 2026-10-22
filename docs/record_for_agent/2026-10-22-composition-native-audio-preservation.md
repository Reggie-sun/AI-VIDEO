---
record_kind: session_summary
topic_id: composition-native-audio-preservation
learning_eligibility: ineligible
---

# Composition Native Audio Preservation

## Problem And Final Behavior

用户指出即梦原片有音效、后期成片却丢失，随后明确要求修改模块防止再次发生。根因是visual MP4按既有架构静音，直接CompositionSpec可以只携带外加P4声而没有同源音轨；Canvas层的muted决定又未封存在layer。现将KEEP/MUTE/REPLACE及原因保存在CompositionLayerSpec；Canvas新视频层默认KEEP，主动muted封存MUTE，替换须明确声明。旧字段缺席仍省略序列化，既有hash不补写。

共同入口resolve_composition在返回前调用只读composition_source_audio守卫，重开精确source probe或开发捕获证据并核验已解析P4/native spans。已验证有原声默认KEEP：同源身份、时间覆盖和trim须吻合，无关BGM不能充数；漏接在渲染前AUDIO_TIMELINE_INVALID。MUTE/REPLACE要有原因，model_copy不能跳过验证；REPLACE须有覆盖画面时段的替换轨。普通进口/旧无probe资料不伪造stream事实；显式KEEP缺证且无合法同源轨则阻断。既有mapped native与canonical generated-WAV登记边界保持，清理后的/4、/5捕获按其本地输出证据判断，不拿原Provider probe冒充派生文件probe。原HyperFrames muted visual/P4 mixer、唯一timeline/writer及Paid/QA/activation边界不变。

## Verification

真实R2/R3开发项目只读对照：修复前二者均能resolve；修复后R2漏接原声被阻断，R3保留原声可通过，证据为runs/source-audio-composition-guard-20261022-001/actual-source-before.json与actual-source-after.json。这是共用入口验证，不把源码测试当听感或Production acceptance。原17秒修正版文件未被本工程改动重写，用户听音结论仍待确认。

新增15个policy/source/coverage/trim/旧hash/model_copy回归，另补3个Canvas入口用例；原replacement-preview用例改为显式REPLACE。最终目标复验36项通过；使用明确指定的本地FFmpeg工具验证native音轨处理22项、Canvas导入/渲染11项通过。清理后/4、/5开发来源与普通P4组合的局部验证也通过。所有检查均无Provider调用。

exact staged tree `93080109f96394aa38db9bb4fff4215c9ab95baa`复制至临时验证repository（仅验证副本，不是开发worktree），保留当前working tree其他未提交改动。正式全范围Harness run004状态为FAILED：其他13组检查通过；composition/audio组1040 passed、18 skipped、1 failed，失败为本机libass依赖FreeType缺符号，原异常保留。进程显式预载系统FreeType后，字幕组17项全部通过，未修改项目依赖或跳过断言。随后运行原被阻断的native组49 passed、17因缺显式测试工具而skipped；显式指定FFmpeg后上述22项和11项实际媒体检查均通过。

补跑Canvas workflow原组353 passed、1 failed：既有纯adapter测试把无关voice-dialogue mock成原声。修正测试夹具提供独立、同源WAV身份，保留公共守卫；最终tree `4c2b182b8fd0e3c470c82178bffb0f423cf2128c`仅此测试改变，implementation与run004完全相同。复验该文件及公共守卫/Canvas音频入口共36项通过，无skip。不会将历史失败receipt重签为PASS，也不声称最终完整Harness全绿；用原范围运行和有归因的局部补验完成工程验证。证据与完整映射见completion-receipt.json。

Parent Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：本改动只增加只读合成拒绝和显式意图，不产生Provider、凭据、预算或Production状态效果；来源/trim/缺轨与旧序列化均有边界测试及真实旧/新方案对照，未发现关键后果且仍未验证的语义缺口。委派仅有native code_mapper与有界worker，worker参与不冒称独立审查。

## Evidence And Learning

主receipt：runs/source-audio-composition-guard-20261022-001/completion-receipt.json；契约：[Source Audio Composition](../source-audio-composition.md)。本轮不再生成媒体、不增加付费调用、不发布；Git只提交本任务owned paths/hunks，影片制作的未审工程与其他会话改动保留。

按record owner记录，自动distill评估no_candidate：原失声输出与修正版是一条媒体链，单元测试/重复receipt不增加独立质量实验数。本修复直接执行用户明确要求，不借学习候选修改其他Skill/Policy/Gate，不写全局memory。
