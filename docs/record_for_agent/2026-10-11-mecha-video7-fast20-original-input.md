---
record_kind: architecture_implementation
topic_id: seedance-single-first-frame-canvas-source
learning_eligibility: ineligible
---

# Mecha Video7 Fast2.0 Original Input Record

Date: 2026-10-11

## Supersession Notice — Human Acceptance And Harness Readiness

用户在完整视听确认问题之后回复“可以通过下一个”，已接受本记录 exact 视频7原片；
`runs/canvas-mecha-fast20-video7-20261011-001/human-acceptance.json` 绑定原 MP4 SHA。
这取代下文“用户未回复/完整视听待确认”的当前状态，仅覆盖该原片的人工接受；
更强的核心紫光在问题中已明确展示。旧 analyzer 的2项PASS/4项NOT_EVALUATED保留，
human接受不倒填 immutable分析、不自动activation，也不变成完整spec或保留集声画交付。
用户随后允许在取证已足够时转向Harness；readiness与实际剩余Gate见
[Harness readiness checkpoint](2026-10-11-canvas-harness-readiness.md)。

## Goal And Current Outcome

用户接受上一份蚂蚁视频6的已知 POV 偏差，并明确继续下一个视频。本次选择《机魂觉醒》视频7，
按原文与图片5完整首帧使用 `doubao-seedance-2-0-fast-260128`、480p、15s 生成一次。
新增 physical POST 1，HTTP200，status queries 10，fetch 成功；没有自动重试或下一视频提交。
`review.html` 同页直接播放画布原片和新片，提供静音同步比较、独立有声播放和原始 PNG。

explicit project-local video-analysis 已核对新片 exact bytes。开场内容与悬空位置 PASS；
完整缓慢推进、烟雾漂移、“没有生机”和整体 source fidelity 仍为 `NOT_EVALUATED`。
新片核心在2s及后续样本出现明显紫色亮点，强于原片样本，不能未经人工判断宣称符合“没有生机”。
用户已收到绑定这份新片的完整视听确认问题，当前未取得回复。
技术生成与播放完成不等于媒体验收；完整 reusable canvas spec、AC-7 与 Final Acceptance 尚未完成。

## Previous Acceptance And Source Boundary

视频6的 `human-acceptance-with-pov-deviation.json` 独立保存用户新决定，绑定前一 MP4 SHA。
历史 POV/source_fidelity FAIL、human motion/audio PASS 保留。未修改其 immutable analyzer evaluation，
未 activation，不将该例外外推至视频7。

来源为既有 full canvas graph：
`runs/reusable-canvas-production-20261011-001/mecha-document.json`。
视频7节点 `node_dzjqb2reg0`，原输出 resource `247522b8-831a-43d4-a154-22ce354cdf8a`；
唯一首帧为图片5节点 `node_0vjb6ycb6g`、resource `47075ae1-df27-4a22-84bd-540eeca149a3`。
编号6→7是用户授权后的操作员选择，不推断 timeline 连续剧情，不消费蚂蚁片末帧。
原 PNG 与原片由已观察的 authenticated resource-read API 取得，来源审计不保存签名 URL 或 cookies。
原 PNG 是完整2560×1440素材，不重绘、不编码转换、不消除原有水印。

原 UI 为 `seedance_2.0_fast_vip`、`firstLastFrame`、单 FIRST_FRAME、无 LAST_FRAME、720p、15s、16:9。
API 请求为单首帧 I2V、用户指定480p；未证明 UI VIP 标识与 exact API backend revision 等同，
也不承诺随机生成的像素级重放。原片只用于比较，不作为请求中的视频参考。
该节点原文没有音频指令；保持批准的 native-audio 设置，不追加对白、配乐、字幕或音效文案。

## Necessary Runtime Change

两个有可靠 reproduction 的最小阻断已修复：来源 inspection 只以所选生成单元及其直接引用
形成执行闭包，不把已生成参考图的上游创作依赖误视为本次执行依赖；完整图和祖先 issue 仍保留。
直接引用的 resource、bytes/history 缺失仍阻断。

`SeedanceNativePromptBinding.compile_source` 增加原文单 FIRST_FRAME I2V。
只允许一个 first_frame asset，原文 intent/progression/hash 必须一致；仍拒绝 rich v4、
typed-hash continuity、conditioning compatibility、额外首末帧与 separate voice。
沿同一 recipe/compiler/Registry/execution binding、Budget Guard、egress、durable intent、one-use permit。
没有新增 transport、mutable-state writer 或 recovery owner，没有 Director prompt 扩写。
计划见 `docs/superpowers/plans/2026-10-11-canvas-source-first-frame.md`，契约归 matrix。

## Paid Execution And Exact Identity

证据根：`runs/canvas-mecha-fast20-video7-20261011-001/`。
attempt：`canvas-fe9a856729cf7f14ec99ea571d2b0deadfc48f4d`。
exact private supplier 沿已获授权的 injected reference，仅内存使用，不输出或持久化值。
sealed operator upper bound 沿前序配置，不查询市场价格或推测抵扣规则。

| Item | Verified evidence |
| --- | --- |
| Provider model | `doubao-seedance-2-0-fast-260128` |
| Mode / output | I2V，single `first_frame`，480p，16:9，15s，`generate_audio=true` |
| Request hash | `e2376c4c28501d276e191f480201fe35f8d645645ef5c1c13afecc3bbba9fa88` |
| Source prompt SHA | `8641b2946adb99f3d4e96c24b7fe4e1b4bb18a49c6d4fb27d39d417c73d95e7b` |
| Native body SHA | `d4a056ab5a641beb6bf8ff270e30ec290afc63a625fb8eda95ea660c1b7da801` |
| Original PNG SHA | `57226872ee1082812accc41bdb6e777c2d59ddb518714876f5366d99a18912f5` |
| Original video SHA | `15749cd597930878da6bcc4de3e8dae5cc76b3257894fb58ae73d0c98774dbb4` |
| New MP4 SHA | `8567bcf5f96dd63c240ac49400a7281be956241164e140caea0fd7c8ac4e09f7` |
| New MP4 measurement | 4406720bytes，15.104s，864×496，24fps，361frames，H264 High / AAC32000Hz stereo |
| Original measurement | 30816319bytes，约15.105s，1280×720，24fps，H264/AAC |
| Call budget | 前序4次 POST + 本单元1次 = 累计5次；remaining0；automatic resample0 |

`source-unit.json`、`pre-submit-preflight.json`、`seedance-authoring-lint.json`、
`sealed-native-body.json` 证明原文 UTF-8 完全相等、完整 PNG bytes 相等和 adaptation diff 为空。
observed transport 在 canonical submit 前比对 actual body SHA、sealed bytes 和 exact Ark endpoint；
`transport-submit-*.json` 只保存摘要及响应状态，不输出认证头或原响应。
permit/reservation/preview 由 canonical `CanvasProductionService` 执行，未直接 HTTP 提交绕过 gates。

## Media Proof And Stop Boundary

`exact-media.json` 和 exact SHA 命名的 fetched MP4 固定本次观察对象。
完整视频/音轨 ffmpeg decode exit0；浏览器两个播放器 readyState4、正确源/时长/尺寸、controls、
未静音，PNG2560×1440 decode 成功。新片实际1倍速有声播放至 ended，无播放器错误；
这证明播放功能，不证明 Agent 或用户已听过并接受声音。

显式 `video_analyze` 的0/2/4/6/8/10/12/14s样本在 `explicit-mcp-analysis.json`；
原片0/5/10/15s比较样本在 `original-mcp-samples.json`；没有 ASR。
canonical facade 的 MCP bridge 又绑定 request/rubric/QA/artifact identity，持久化
`canonical-mcp-analysis.json`、`generation-evaluation-source.json`、`generation-media-diagnosis.json`。

| Required finding | Current analyzer verdict |
| --- | --- |
| `first_frame_match` | PASS：0s保留原图菱形、损坏核心、废墟与天空，仅证明开场外观 |
| `monster_hover` | PASS：各样本显示主体悬于废墟上空，无地面接触 |
| `slow_push` | NOT_EVALUATED：样本主体逐渐变大，完整缓慢平滑推进尚待正常速度观看 |
| `smoke_drift` | NOT_EVALUATED：样本烟雾位置变化，完整缓慢连续漂移尚待观看 |
| `lifeless` | NOT_EVALUATED：更强的核心亮光与原文感觉的关系尚待人工判断 |
| `source_fidelity` | NOT_EVALUATED：输入忠实已证，完整输出忠实仍有上述缺证 |

AAC存在与正常播放不代替实际听感；不宣称无BGM、无对白或声音与原片一致。
`post-media-stop.json` 是 Agent STOP，不冒充 committer receipt。Manifest 仍在 `VALIDATE`，
next_action为`validate`；未执行 blocked validation、activation、composition/render 或下一 Shot。
先补完整视听证据，缺证不重生成。新增单元额度已用尽，不能自动再次 POST。

## Verification And Publication

相关 scoped tests 113 passed；聚焦原文入口/来源检查33 passed。
exact staged Harness：`.agent/harness/runs/canvas-source-first-frame-20261011-final/receipt.json`，
12 checks PASS，1 check由已通过 suite完整覆盖而SKIPPED；合计1990 test cases，含production918、
canvas115、Vidu194、provider-neutral442。Architecture Gate0errors/0warnings。
`make harness-receipt` 在提交前证明 exact snapshot/freshness/artifact integrity/completion proof。
index tree：`fdb0a76a428c45f10823a36b8d4ef6823089295e`。

Parent stable-candidate Risk Gate 为 `KIMI_REVIEW_NOT_REQUIRED`；具体三个条件及验证理由
见 `implementation-review-risk.json`。受管 Kimi 只读 deep/source mapping invocation
`bfa9d61b-e29f-4adf-b00e-b99518e95b8c` 已验证 sealed snapshot/route/artifact SHA，
机械观察4次 upstream wire requests、零 orchestration retry、内部 retry未知；不是 final implementation review。

代码 checkpoint `109707e8aba34d2ca0e4a77e5e0fd1cdb73e43e0` 已push至remote main并核对SHA。
只包含六个本任务 owned paths；paused retarget/spec/baseline dirty work未编辑、stage或commit，
其内容不属于 exact staged verification。本文与前一原文记录的 supersession notice 另执行
documentation-only staged Harness，receipt目标为
`.agent/harness/runs/canvas-video7-fast20-record-20261011-final/receipt.json`；最终publication以实测SHA为准。

## Learning Evaluation And Remaining Work

自动 `distill-ai-video-learning` 评估为 `no_candidate`。只有一次新增不受控生成；原片与新片
分辨率、后端版本确定性、seed等未控制，不能推出普遍模型能力、费用或 prompt扩写因果结论。
未修改/采用 Learning Claim、Skill、Policy或Gate。没有为记录额外调用Provider、生成媒体、网络研究或全套测试。
experience检索只作发现，结论来自重开的源文件/receipt；未手动刷新独立RAG index。

等待新片完整视听确认；整体spec仍需要后续真实媒体/production acceptance，不因技术PASS完成。
直接前一原文记录已加醒目supersession notice。更早旧记录仍有paused dirty hunks，保持原样，
不能宣称那些文件中的所有历史当前状态已全面协调；其已有pointer指向更新后的原文记录。
