# Source Audio Composition

## Intent And Enforcement

`CompositionLayerSpec.source_audio_policy` 表达 `KEEP`、`MUTE` 或 `REPLACE`，`source_audio_reason` 记录主动静音/替换的原因。新 Canvas 视频层默认封存 `KEEP`；显式 `muted=true` 封存 `MUTE`。`MUTE`/`REPLACE` 缺少非空原因、或与保留原声的 time map 矛盾时拒绝。仅有 `native_audio=true` 的生成请求不代表最终音轨已接入。

`resolve_composition` 是 Canvas 与直接 `CompositionSpec` 共用的执行边界。`composition_source_audio.require_source_audio` 只读核验已解析时间线，不创建音轨、派生文件、第二时间线或 Provider 调用：已验证有原声的视频默认 `KEEP`，必须有同一视频来源、正确 trim、覆盖所用画面区间的 P4/native 音轨。无关配乐、拟音、错误来源、缺段或错位不能代替。缺失时在渲染之前返回 `AUDIO_TIMELINE_INVALID`，而不是继续输出丢原声的成片。

显式 `REPLACE` 仍须有覆盖该层时段的替换音轨；显式 `MUTE` 不要求原声音轨。v2原生音频继续通过原VIDEO/sample映射、原stream预检与HyperFrames mixer；注册WAV仍遵循原来源和登记资格，不能用此检查绕过结算、原片验收或Registry owner。开发预览的来源不得升级为Production acceptance。

## Native And Post Audio Together

原声保留与后期配音不是二选一。普通Canvas视频层在同Shot已有旁白、对白或音乐轨时，仍应自动接入唯一精确匹配的已登记原声WAV；已显式绑定该原声时不重复建轨。缺少或存在多个未选定原声候选时，不能以任意后期音轨代替来源检查。显式MUTE/REPLACE仍遵守原意图与覆盖约束，后期轨的trim、gain、fade和ducking保持。

所有选定音轨由同一个`ResolvedTimeline`与HyperFrames mixer组合；是否需要旁白由现有导演/广告声音方案判断，省略须有内容理由，不由stream存在与否推断。听感、对白可懂度及是否重复仍需exact成片审听，配置与测试不代签。

## Compatibility And Proof Boundary

新增字段缺席时不进入旧序列化，历史Spec及hash不被补写。旧素材没有可重开的源音轨证据时，缺省policy不能作为“存在音轨”或“没有音轨”的证明；显式KEEP必须提供可验证的同源音轨路线。实际已验证原声不再因字段缺省而静默丢弃。

检查只核验源身份、时间和接线，不能证明语义、音质、对白正确或听感通过；这些仍由exact成片及适用用户/媒体验收决定。无副作用解析不自动取得提取/激活/发布权限。

## Regression Coverage

`tests/test_production_composition_source_audio.py` 覆盖直接Spec漏接原声、任意BGM误充原声、来源/trim/覆盖、显式静音与替换、旧字段缺席兼容；既有native time-map与Canvas测试保留。Harness复用 `native_audio_retime_tests`，不新增执行链。
