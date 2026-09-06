# Generated Video Audio Derivation

## Contract

此入口用于把已结算生成视频的原生音轨派生为独立P4音频素材，供既有`ResolvedTimeline`和HyperFrames组合。它不接受任意MP4冒充Provider结果，不重新调用Provider，不改变源视频的QA结论，也不证明派生语音符合台词或音质要求。

本次范围为`DIALOGUE`或`NARRATION`语音轨，不扩展远程音乐、SFX或local ComfyUI来源。源attempt限定为已fetch、尚处于`VALIDATE`且已结算的远程生成结果；不是任意生命周期阶段的通用导出器。

目标沿用现有无dependency transition的`audio_import`：仅支持Manifest `2.0`–`2.2`、Registry `2.1`。Manifest `2.3`及以后版本或Registry `2.2`在ffmpeg前拒绝，不能降级snapshot或绕过Dependency Graph来登记。

`ProductionStateCommitter`继续独占durable registration。生成音频保留`GENERATED`来源与原始request/task/fetch identity；`AudioImportRequest`对生成音频的拒绝保持不变。视觉MP4继续静音，最终声音只能来自显式P4 audio tracks。

登记复用现有`audio_import`原子事务，不伪造`voice_generation`或增加Manifest字段。严格读取器分别核验既有TTS与派生音频的来源证明；只有经过完整派生receipt、source evidence和事务base→candidate Registry核验的音频，才能进入派生claims集合。仅匹配文件名前缀、tool名称或`GENERATED`标记不构成认可依据；两类claims不得冲突或重复。

## Required Source Evidence

源project通过strict loader重新打开；源attempt必须拥有一致的sealed request、successful status、fetch receipt及exact MP4。远程付费素材必须保留既有settlement gate：`SETTLED` paid state、同attempt/request/submit的已结算reservation以及真实`actual_cost_microunits`。内部operator upper bound不是实际账单。

派生绑定源文件SHA/bytes、request/task/fetch、提取与probe工具身份及派生WAV身份。speech metadata中的voice identity只标识本段派生音频，不承诺Provider可以重用该声线。错误来源、变更字节、缺少音轨或不完整结算必须在登记前fail closed。

## Replay And Acceptance

重复调用必须校验原来源、参数、工具与已登记音频，再复用精确证据；不得重复ffmpeg/probe或Manifest写入。未完成或unknown transaction通过既有explicit recovery处理，不能重做派生掩盖状态。

登记不等于逐镜通过、源视频激活或最终验收。组合07画面与08广播需要合法登记的视觉输入、新的composition输出和完整逐镜Gate。不得用本能力绕过未接受源的适用质量门禁。

## Verification Boundary

focused tests：`tests/test_production_generated_video_audio.py`。Harness路由位于`.agent/harness/policy.yaml`；通用state/reader/audio契约继续运行相应既有组合。

《界蚀》attempt07/08当前付费状态为`ACCEPTED`，reservation实际金额缺失；即使本入口的离线测试通过，也不能把这两份素材描述为已完成派生、登记或成片。
