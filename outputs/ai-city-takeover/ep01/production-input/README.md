# IRIS EP01 Canonical Authoring Preparation

这里是可编辑导演输入，使用仓库现有 `ProductionBrief / Story / Character / Scene / Storyboard / Shot / DeliveryProfile / RendererPolicy`，不是新的项目协议、Registry、Manifest或时间线。八个叙事镜头复用四个摄影设置：A 阳台开场/回望，C 室内人物与暗屏，D 同设备图形近景，B 同阳台演唱近景。

## Edit And Validate

在仓库根执行：

```bash
python outputs/ai-city-takeover/ep01/production-input/build_draft.py
python outputs/ai-city-takeover/ep01/production-input/validate_draft.py
```

`build_draft.py`只写本目录的开发稿。直接编辑 JSON 后，内容哈希应由现有 `seal_artifact` 重算；重跑 builder 会从脚本中的导演文本重建本目录草案。验证使用真实 canonical 类型和哈希函数，核对所有现有参考字节与叙事对象关系；没有执行 bootstrap 或签发任何验收。

A开场与C室内观察使用主会话选定的6秒源片生成窗口；其余Shot使用 `DurationPolicy(mode="content_driven")`，故意没有 seconds。这不是基于真实歌曲测得的最终镜长，最后裁切仍交canonical resolver。它们是按歌词顺序的导演叙事稿，不是歌曲分秒时间线。主歌/耳语/结尾念白画外；仅 B 的副歌声明人物出镜演唱，须真实音频与口型验证。原已认可英文词全部保留在相应 Shot 的 narration/dialogue，中文译句仍由 `../lyrics-v1.md` 独占。

`reference_asset_ids`和`required_asset_roles`暂不填不存在的ID。参考图片只通过现有 `SourceReference` 绑定真实路径和SHA，已获参考图认可，但尚未注册、采用或证明动态身份；不得把它们冒充已采用的primary_visual。

## Final Composition Boundary

```bash
python outputs/ai-city-takeover/ep01/production-input/validate_draft.py --require-compose-ready
```

此命令输出准备状态并**退出2**；不是可运行的成片 compose 入口。三张参考已获用户原话「三张都认可，继续镜头制作」认可，该原话单独封存并进入SourceReference；尚未绑定runtime preview_approval。A03实际可见屏幕背面，因此C只拍人物反应，D承载独立图形，不向背面贴图。

缺少实际选定歌曲、逐字与镜头时序、最终 coverage、runtime preview_approval、Registry采用及实际镜头QA，不能凭现有静帧创建完整 ProductionProject 或 ResolvedTimeline。

歌曲和镜头到位后，应由现有 authoring/committer 完成真实登记与采用，再进入既有 `CompositionSpec → ResolvedTimeline → HyperFrames`。图形 source clip 仅作为各自独立源素材；最终剪点、裁切、歌曲和字幕归原resolver。禁止把整个开发预演片当作单一黑盒视频绕过最终时间线。

没有创建假的Canvas平台捕获、预览认可、音轨引用、逐字时间戳或QA PASS。此目录不含Provider调用，也不读取凭据。正常验证通过只证明已准备的数据，不证明能完成最终合成或用户已认可视频。
