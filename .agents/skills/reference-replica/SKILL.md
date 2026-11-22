---
name: reference-replica
description: Use when the user supplies a reference video and asks for a standalone Agentcut edit based on its structure, especially a screen-recorded tutorial for a client or a reference-led news roundup. Covers narration, timing, redaction, local edit and delivery. Production Shots and compositions follow their existing owners.
---

# Reference Replica

先确认参考原片、用户授权使用的素材、交付对象和要保留的口播或画面要点。向用户出示完整口播，集中确认待定项。用户确认整稿并回答待定项后直接锁定文案，再按任务授权执行配音。对着原声写口播，作者的上屏补充文字留在字幕。逐字保留用户指定句子，句中时长与实测不一致时在汇报指出。保留原片的口语，禁止添加原片没有的招呼、过渡和点评。按原片的句长和节奏安排内容。每个镜头要解释对应的话。将用户反馈应用到全片每个同类镜头。

本 Skill 负责独立的 Agentcut 剪辑工程。用户输入属于 Production Shot 或 Composition 时，从已有 owner 读取资产和要求，并沿 [Contract Routing Matrix](../../../docs/agent-primary-contract-matrix.md#production-runtime-surfaces) 进入同一条 `ResolvedTimeline` 和 HyperFrames 路径。

## Local Inputs

从仓库根以 `python -m scripts.replica.<tool>` 调用工具。FFmpeg 和 FFprobe 通过相应的 `--ffmpeg`、`--ffprobe` 或 `PATH` 选择。涉及 Agentcut 的操作使用工具接收的明确项目目录，或者用 `--projects-root` / `AGENTCUT_WORKSPACE` 指定工作区。`AGENTCUT_WORKSPACE` 对应已登记 MCP 配置的同名变量，项目位于其 `projects/` 下。先选择本次拥有的独立工程，复制 `scripts/replica/agentcut-scenes/news/` 或 `tutorial/` 到工程的 `scenes/`，保留 `lib/` 相对路径。

用已安装的本地 Whisper checkpoint 转写原片和有音轨的素材。静默录屏出现订阅口号等幻听时，回到原音轨核实；无音轨的录屏按画面取证。Whisper 输出逐字时序和转写文本。语义、语气、声音与背景声的审听按 [Audio Understanding](../../../docs/audio-understanding.md#agent-procedure) 使用项目 `audio_understand`，先锁定实际文件与 SHA-256 后运行 `execute=false` 预览。真实执行依赖可信 operator；UNKNOWN 进入原恢复流程。只送审变化的音轨。复用过往审听时核对本次 exact 音轨与已审音轨一致。

```bash
python -m scripts.replica.transcribe transcripts ref=reference.mp4 A=recording-a.mp4 \
  --whisper-checkpoint /local/models/large-v3.pt
```

## Narration And Timing

按语义段保存 `groups`。每段保存稳定 `id`、逐句上屏 `lines`、实际读法 `say` 和可选 `gap`（帧）。数字、缩写等读法只进 `say`。选择明确的 MiniMax `voice` 配置，提供 `region`、`voice_id`，按需设置 `model_id`、`language`、`speed_milli`、`sample_rate_hz`。每期设定稳定的 `episode_id` 和专用配音目录。把表演提醒保留在 `direction` 供剪辑、回听参考，当前 MiniMax 合成使用 `say` 与选定声音参数。

`tts_run` 缺省只报告待做组和完整计划的 `plan_sha256`。有整稿确认后，显式 `--execute --approved-plan-sha256 <hash> --runtime <module:function>` 进入 [MiniMax 客户口播接线](../../../docs/minimax-speech.md#standalone-client-narration)。保留该期 `voice-state/`，为改稿指定变化过的组。当前组已成功则重开 canonical WAV；欠缺成功 WAV、处理中或结果未知时找回原证据并沿原 owner 恢复。

```bash
python -m scripts.replica.tts_run vo-groups.json voice g02
python -m scripts.replica.normalize_vo vo-groups.json voice g02
python -m scripts.replica.align_lines vo-groups.json voice line-timings.json \
  --whisper-checkpoint /local/models/large-v3.pt
python -m scripts.replica.make_timeline vo-groups.json line-timings.json voice timeline.json assets/voice/v2/
```

配音后用当前 exact take 做响度处理和逐句听查。对齐采用无提示词的 Whisper，`condition_on_previous_text=False`、`temperature=0`。上屏文字和实际读法各匹配一次，取匹配度较高者。任一句低于八成时先听并修复。旧 `timeline` 留作重映射基准。用 `layers_kit.make_mapper` 按句子的首末帧映射到新轴，共享边界以后一行起点为准。句数变化的段落重新编排，区段内录屏保持原始源时间范围，再算速度。将 `normalize_vo` 输出的 WAV 按组号放进时间轴所指的版本化 `assets/voice/` 目录，实际触发变更时使用新目录以刷新 Agentcut 缓存。画面文字与最新口播核对一致。

## Screen-Recording Tutorial

1. 按秒抽帧找到操作，再以更密的帧核对点击和页面状态。`gridshot <out.png> <media>@<seconds> ...` 绘制原分辨率坐标网格。口播只出现画面能证明的数字和步骤。
2. `redact <spec.json> --source-root <录屏目录> --output-root <打码输出目录>` 在源坐标和源秒数上打码。覆盖手机号、验证码、卡密、订单和支付流水、账号名、邮箱、照片及无关记录。键盘起落、弹窗位移和页面过渡各自量坐标，短过渡用覆盖整个敏感区的大框。旧打码文件留存，修复后使用有新文件名的版本。剪辑和封面都从已打码素材取图。
3. 手机录屏和 `Phone` 覆盖层共享 `from`、`duration` 和屏幕区域。对应状态下才显示红框，框在页面跳转或弹窗消失前收掉。核对快进、停留、外借镜头和返回前后的画面。字幕避开章节栏，章名、步骤和当前动作与录屏一致。
4. 客户片的开尾按参考片和交付 brief，去除栏目角标、关注动画和账号 CTA。上下集在有效章节边界切开，配相应总结。末句致谢可从主片已确认口播裁切。对需要在同一页面导出的临时主工程，用 `swap_layers <主工程> <拆条工程>` 切换，保留 `.full-backup`；完成后 `swap_layers <主工程> --restore` 并核对主工程时长和轨道。

## News Cut

按原片说法核实每条新闻的时间、官方表述和来源。使用官方未二次剪辑的演示，按完整片段取区间。方形和竖屏画面铺满，在允许的取景范围内裁掉烧录字幕和水印，保留主体可读区域。非官方示例在右上角标明来源。

跑分最多用三到四次整张动画柱状图，快速带过。每句配能说明内容的实际演示。禁止推近表格、网页或论文来展示数字或句子。禁止静止标题卡、推近后立刻切走以及抖动的伪视频。参考中有音乐时平衡口播与音乐。片尾 CTA 的语气和语速与全篇保持一致，品牌和发布以该次明确目的为准，客户交付止于本地文件。

## Final Media And Delivery

1. 核对实际导出的 MP4 可完整解码，检查黑场、字幕、点击框、声画、音量和结尾。正常速度带声音完整审看。对打码后的实际成片按每秒 4 帧逐段检查手机区域，重点看弹窗、键盘、切页、短暂过渡，主会话核对。发现露码后更新素材及输出复查，确认每个拆条和封面也已覆盖。
2. `deliver transcode <Agentcut-export.mp4> <delivery.mp4>` 生成 H.264、yuv420p、faststart 版，保留源色彩标签与可直接复制的 AAC。用 `deliver package <recipe.json> <交付目录> --projects-root <项目根目录> --font <本地中文字体>` 生成封面和字幕。已有 MP4 留在交付目录，SRT 放 `另附字幕文件/`，避免播放器自动加载出双层字幕。封面取本版获复查的画面，分辨率为 1920×1080。
3. 按完整版、上集和下集核对 MP4、封面、SRT 与版本。汇报已交付路径、修正内容、实测边界及有据的费用。用户的成片确认与技术检查分别取证。

## Offline Example

礼品卡范例位于 `examples/reference-replica/giftcard-jp/`。`build_layers.py parts --projects-root <临时工程根>` 重建三份层文件；主工程 `giftcard-jp-replica` 需已有 `project.json` 与 `assets/`。历史配音分组和镜头数据供回归使用，新任务按本 Skill 选择新项目、素材和声音配置。
