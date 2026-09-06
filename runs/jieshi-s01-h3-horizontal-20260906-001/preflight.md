# Scope

用户要求本地 H3 试做《界蚀》，并批准 S01 横屏试片。复用既有 S01 叙事，raw source 为封装 profile 的 124 frames / 24fps / 1344×768 / native audio。正式 300 秒竖屏全集不在本次试片交付内。

# Ownership

使用现有 `ComfyUIT8NativeTurboVideoProvider` 与 `VideoGenerationService`；所有 Production 写入归 `ProductionStateCommitter`。新增 run 使用独立 Production root；不替换或激活原 Vidu/Seedance 项目。准备阶段发现 native V2 未接入完整 `/4` prompt，随后进行了四文件有界修复及独立审查，详见本次 session record。当前 staged 的七个旧 run 文件不属于本任务。

# Creative Preflight

已读取 `retrieve-ai-video-memory`、`h3-video`、`hell-grind-aigc-skill` 及 imagegen 指导。RAG 返回 fresh run summaries 与 tagged stale experience，仅供参考；当前环境由本轮读取核验。既有 approved S01 已有明确单镜头，不新增 coverage。

- Open：林砚坐在画面左侧看向车窗，解剖右手持黑手机，左手置膝；窗内七个其他人物的倒影存在，林砚对应位置为空。
- Close：左手一次连续抬向车窗，在约 2cm 外停止；右手手机、座位、七个倒影、缺席的本人倒影不变。
- Camera：坐姿眼高斜侧中广景，锁机位；人物面向屏幕右侧，左手向窗抬起，无轴线跨越或剪切。
- Audio：画外列车广播 0.1–2.7s 说“林砚，请在终点站下车。”，屏内所有人物闭口，保留列车底噪及轻微衣料声，无音乐。
- 字幕由原有合成路径负责，raw source 不生成字幕或 UI。Raw test 不宣称字幕成片完成。
- 横屏首帧通过 imagegen 对原图作横屏改构图；reference/input/output identity 见 `provenance.json`，exact prompt 见 `first-frame-prompt.txt`。已查看原图与新图；图片不是 H3 视频输出。
- H3 guidance 将运动、摄影机、可见状态和音频分开声明；使用 adapter compiler，不手工修改 resolved payload。`GenerationIntent` 实际验证通过；Skill 没有可替代 Provider preflight 的可执行 lint。

# Verification

本轮 read-only runtime checks：ComfyUI、T8、VHS commits 与 profile 相同；T8 1.36.2 相同；loopback 127.0.0.1:8188，启动包含 `--use-sage-attention`，观测 queue empty。完整模型字节及节点 schema 仍须 Provider preflight 验证。

`PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_production_comfy_t8_native_turbo_video.py -q`：32 passed。

# Media Gate Rubric

输出后绑定 exact MP4/path/SHA-256，显式调用 project-local video-analysis。逐项检查：几何/时长/完整解码、人物与七个倒影、林砚及其手影缺席、左手动作与悬停、右手手机、锁机位、无杂字、原生声音可听、逐字台词和窗口、画外声源与屏内闭口。未可靠判定为 NOT_EVALUATED；任何 required FAIL/NOT_EVALUATED 均不进入下一镜。

首次已知失败仅在有单一可归因修复变量且 `budget.json` 允许时进行一个新 attempt；不重复提交，不复用 permit，不自动 activation。纯证据问题优先修复分析，不重新生成。
