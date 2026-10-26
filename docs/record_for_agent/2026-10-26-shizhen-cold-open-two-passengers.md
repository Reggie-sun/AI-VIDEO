---
record_kind: session_summary
topic_id: shizhen-cold-open-two-passengers
learning_eligibility: ineligible
---

# Two Passengers Cold Open Review Checkpoint

## Scope And Outcome

用户授权执行已认可《两位》冷开场，指定Jimeng Seedance2.5、Suno v6原创器乐、保护现有S01；执行中明确2.5可一次最长30秒。已实际完成8秒前态、4秒后态、22秒单次完整事件，五次内置图像调用及一次Suno候选对。最终P4导演剪辑冷开场含片名20.167秒，随后接认可的名义16秒S01，1920×1080/24fps/868帧。

当前交片为`outputs/shizhen-episode01/cold-open-execution-20261026/失帧-两位冷开场加S01-1080p审看版.mp4`，SHA-256 `5ab3a929258db93606196ab537d89c795343899dba8616dbdd8905e55433e48a`。仅`REVIEW_READY`，human acceptance未评、未发布、未Production激活，不是整集完成。

## Actual Media And Repair

CO-A1原片`b42b27040a62c6c303079e9f582534ec5d7ff7dcf9fb6c88c781de53dcde02fd`，8秒，33帧MCP与真实音频观察后八项analyzer PASS。CO-A2原片`0dabb72c98edcc3550c91d2e23292740044a193bee7079f8751bb0fb43a2060c`，4秒，17帧与原声观察PASS。实际A1末帧由既有视频帧验证owner提取，并用于A2参考，未假称Production accepted-terminal。

用户提出单次30秒后，第三次预留调用改为22秒完整事件CO-A3，模型确实完成两位→遮挡→一位→平常回答。但高峥从开画缺挎包，raw identity为FAIL，声音独立观察未充分区分电话声及棚雨，记录NOT_EVALUATED；原片`750326c44ba58ecd0093c52ff8c7337cb8942f4e3efd9bd61634d3cfe3b119cf`及原判决完整保留，没有倒签PASS或新付费重试。

导演剪辑采用A1有包前态、A2后态及CO-A3实际近景回答选段，修复前述已知包状态。P4独占准确时钟、失帧片名、翌夜、配乐与原声。最终exact MP4盲声音观察能区分三名开场说话人及电话滤波，并确认四轮对白齐全、日常表演和湿街环境。此新证据属于最终组合范围，不改写旧raw判决。

## Music And Preservation

现有Music Director/SunoMusicService产生“缺席的应答”一对v6候选，选B仅用于3.5秒片名，进入S01前退出。同一录音的片尾再现交接已保存，最终整集入点未定。工具实际描述偏钢琴/弦乐/氛围合成器，未把指定乐器或冷峻审美标人工通过。

S01源SHA `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`再次核验未变；保留前次认可名义0–16秒区间与四组双语字幕。四段选中原声PCM与实际P4 canonical WAV窗口逐样本相同，S01没有BGM重叠；最终AAC正常有损，原文件endpoint/AAC空尾未被覆盖或删除。

## Minimal Runtime Change And Verification

`src/ai_video/production/_composition_visual.py`原布局条件要求所有Shot都有DIALOGUE且audio_tracks数量等于Shot数，导致合法“原声字幕+静态无对白片名+BGM”被拒。最小修复允许仅无对白/旁白且IMAGE的STATIC_IMAGE Shot省略捕获原声轨，并允许额外BGM/SFX/ambience。每条captured video仍有一条exact原声，来源、裁剪窗口、0gain/no-fade/no-duck、字幕归属、连续区间和Production activation fence保持。

`tests/test_caption_development_preview.py`新增有效组合与缺源、错源、增益变更、字幕串绑、标题视频/新增对白、额外旁白等负向验证。三份相关测试59项PASS，Junit与两个实际源码SHA见`qa/p4-verification-receipt.json`。HyperFrames实际lint/check均0错误，输出868帧；最终MCP、关键帧和原声保存验证均已落盘。未运行全量工程回归；film-first要求用户审片认可后再全量验证和owned-path commit/push，本checkpoint保持未提交，不夹带并行窗口的其他源码。

Risk Gate为Parent自审／`NATIVE_REVIEW_NOT_REQUIRED`：改动局部可回滚，不变凭据/授权/持久化/激活，实质失败路径有相关测试并有实际出片验证。没有把测试或工具成功当成人工审片。

## Accounting And Remaining Work

冷开场视频3次已知受理并下载；保留六次旧史及另一窗口独立S03一次，共10次。原9次bound由跨窗口addendum补足到合计10；冷开场3次、每次1500/本任务4500内部CRD不增加，内部总11000不是报价或实际账单。视频、图像实际费用未结算。

本次Suno真实10credits（2480→2470），音乐历史四次与两个UNKNOWN不动；本次为第5次逻辑音乐请求。音频理解6次独立exact unit已知完成，无旧UNKNOWN重试。所有凭据只走原有供应引用，未复制或外泄。

待用户审看音乐气质与整体效果；新开场认可后自动制作字幕。片尾主题由未来整集时间线放置。完整工程验证、commit/push、发布均未完成，不能把审看片标正式交付接受。

## Evidence Pointers

- 制作与原始素材：`outputs/shizhen-episode01/cold-open-execution-20261026/README.md`
- 最终核验：同目录`qa/final-editorial-review.json`、`final-v1-mcp.json`、`final-v1-original-audio-preservation.json`
- 唯一时间线／渲染：同目录`composition/resolved-timeline.json`、`render-receipt.json`
- 原始逐镜判决：同目录`qa/CO-A1-post-media-gate.json`、`CO-A2-post-media-gate.json`、`CO-A3-post-media-gate.json`
- 相关验证：同目录`qa/p4-verification-receipt.json`、`p4-related-tests.xml`
- 原运行根：`runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/`
- 继续计划：`docs/superpowers/plans/2026-10-26-shizhen-cold-open-production.md`

## Learning Evaluation

`no_candidate`。这是一轮作品制作：分段和整段的prompt、时长、输入mode与参考职责均不同，不能当作受控比较，也不能推出“分段总比单次好”或“30秒模型不会连续叙事”。P4组合修复已有精准测试与一次真实渲染，不据单例修改Skill/Policy/Gate或声称普遍模型结论。已做experience follow-up检索，结果仅advisory；无新增学习批准流程。
