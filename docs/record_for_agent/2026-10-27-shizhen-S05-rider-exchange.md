---
record_kind: media_experiment
topic_id: shizhen-S05-rider-exchange
learning_eligibility: needs_identity
evidence_index_version: "1"
---

# Shizhen S05 Rider Exchange

## Scope And Accepted Entry

用户“过关,开始shot5”接受S04原声接点修正版 `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`。实际末帧236@24fps已提取并查看：林序看向右侧骑手，右手手机垂右髋、左手自由；瓶直立、扫码枪卧瓶左、饭团在白纸。S05只执行原剧本五轮与指饭收手，不扩展至店长出场或S06、不发布。当前用户已认可的是S04，不是尚未取回的S05。旧S04 raw FAIL、assembly crop warning/NOT_EVALUATED和S03音频UNKNOWN仍保留。

## Complete Event And Selected Route

原文五轮依次为骑手“你找老板？后边呢。”、林序“不是。刚才这个小伙子。”、骑手“什么小伙子？”、林序“给我热饭那个。红围裙。”、骑手“你不是自己热的？”。骑手左掌稳托独立封闭餐盒，右手扣头盔，听到小伙子才停扣、看空柜台再看林序。林序右手手机全程垂髋，结尾用左手短指白纸上的饭团再收回，想笑未笑。头盔松带与餐盒各有真实支撑，不拿错三角饭团。

20秒容纳约四十字五轮、相互倾听、托稳餐盒、停扣、看柜台和短指收手。选现有Jimeng / Seedance2.5 / multimodal /1080p/native audio KEEP；不是为10秒的软件限制换版本，也不挤压2.0的15秒上限。沿原S05顾客侧稳定双人中景，同时看认知相反的听说反应；这个机位来自叙事和原coverage，不由时长默认一镜到底。原CG表现已按用户持续真人要求替换，原剧情与逐字对白不变、不加逐句时间戳。

## Exact Reference And Preflight Evidence

L/S05实际绑定4图：1是S04 actual terminal的林序身份/低持手机；2是新双人开场、同白头盔黑雨衣黑黄背包骑手的脸与造型；3是右手停扣/左掌托盒的中态；4是林序左手指饭团、右手手机仍垂髋的后段状态。2/3/4来自image_gen，已逐张实际查看；S01三人图仅用于制图时保留原骑手衣物，不进视频输入，避免旧店员和旧持物姿态回流。

本轮image调用4次、选用3张生成图。04-v1食指偏向手机，known outcome下封存一次有界gesture repair，04-v2纠正指示目标和眼神，保留原图且未盲重试UNKNOWN。费用未暴露。所有原PNG、完整prompt、input/output SHA与尺寸见 `S05/references/*.source.json`、`reference-evidence.json`。

封存前依次保留v1/v2/v3 intent及旧preview：v2把简写“黑有线枪”明确为“黑色有线扫码枪”；v3移除已消失店员的旧围裙材质，并把林序表演触发改为先询问、听否认后才不服。旧sealed数据不覆盖，时长、原话、参考与QA不变。最终 `prepare-v3.json` / `native-prompt-v3.txt`4083字符，四图顺序、五句原话、无台词时间戳、两人持物与支撑、KEEP、20秒/benefit/output和1080p lint全通过；2.5当前渠道上限15000，未套用2.0的4000。

## Real Submission And Finite Bounds

canonical `R/trial-S05-v1`，task `shizhen-S05-qualification`，attempt `shizhen-S05-qualification-attempt-001`。全部roots严格盘点得到此前18个唯一paid video，无video UNKNOWN；平台18个旧video资源均完成，新目标node为空，账号/project exact匹配。经现有ProductionStateCommitter、selected adapter、preview、budget/quota、durable intent和新one-use permit提交1次并被接收。历史消费不归零，合并有限上限18→19，自动resample/retry0。

native quote **1280credits**，1500CRD是内部每call guard，实际扣费待结算；图片费用未暴露，旧S03音频UNKNOWN未重试。本轮未新调远程声音理解。实际bindings、prompt SHA、原话、全计数归 `S05/actual-binding-receipt.json`；原平台/历史检查归 `platform-preflight.json`与`all-roots-before-submit.json`。

## Verification And Current Limit

当前已完成GenerationIntent模型校验、canonical reader/bootstrap/prepare/start、真实账户/平台只读核验和submit被接收；此处仍等待exact视频，不能把这些签成电影质量PASS。新run-local脚本已compileall，未扩建共享源码，未启动长全片/工程审核拖延交片。取回后须explicit project-local MCP，并区分逐字对白/口型、持物、自然度和用户接受；ASR或音轨存在不证明实际听感。

使用record-ai-video-session记录本稳定接收检查点，distill评估no_candidate：本次新单臂生成尚无媒体结果，参考修复也不是独立视频实验。S04原适配源码修改已通过此前277个关联用例但尚未完成完整工程验证；保留其他窗口dirty工作，不夹带commit。当前publication NOT_PUBLISHED，S05人工接受/媒体Gate NOT_EVALUATED。
