---
record_kind: architecture_implementation
topic_id: iris-ep01-patchright-and-source-progress
learning_eligibility: ineligible
evidence_index_version: "1"
---

# IRIS EP01 Patchright And Source Progress

Date: 2026-10-30

## Supersession Notice — 2026-10-30 Continuation

后续接续已只读核对当前 Suno：官方页恢复为正常表单、截图未见实际 challenge，但 CLI 预检仍要求验证，曲库仍无 IRIS、余额 2470，旧请求保持未决，没有重试。外部歌曲及双语字幕的开发预览接线已新增显式 `/2` 契约；当前测试的混合依赖与隔离基线失败边界见 [continuation record](2026-10-30-captioned-music-preview-continuation.md)。下文 Cloudflare、费用和源片结论保留为原会话历史，不代替当前验证，也没有因此完成歌曲或成片。

## Current Runtime Truth

用户已明确认可三张 EP01 参考并要求继续镜头；随后明确「保留 AI 标识，只禁止新增剧情字幕和图形」。这取代前一记录中 EP01 尚无参考包、未获后续镜头认可、零 paid submit 的当前状态，不改变 T01 历史测试或工程验证结果。

用户另要求接入 Patchright 后继续 Suno。当前独立 runtime 已安装 `patchright@1.64.2` 和标准 MCP transport 的 `@modelcontextprotocol/sdk@1.32.2`。入口 `scripts/patchright_mcp.cjs` 通过公开 `createConnection(config, contextGetter)` 提供真实 Patchright context；项目两份 MCP 配置新增 `patchright`，未替换既有 Playwright/Jimeng。

## Browser Evidence

`outputs/ai-city-takeover/ep01/audio/patchright-integration-validation.json` 保存实际连接、账号、工具、版本、代码与截图 identity。原 Chrome 的 `sunruijie42` 可见；实际 MCP 标签、快照、表单读取/填写及一次 Create 通过。连接退出后 Chrome 与 Suno 页仍保留。独立 code review 修正初始化错误诊断后 `APPROVE`；Node 语法、配置语义保留和 task-path whitespace 检查通过。

本通道 Create 之后，实际截图是 Cloudflare “Verify you are human”。普通 DOM 检查未列出 captcha iframe，不能据此宣称没有验证码。歌曲仍 `NOT_CONFIRMED`，没有伪造成功 clip、读取 challenge token 或自动求解；已保留官方窗口并请求用户手动完成，不重复点 Create。本通道 Create 后重新只读查询余额仍为 2470，曲库未查到 IRIS；不能把浏览器接通或按钮点击当作已扣费、已生成音乐。

旧 Codex 成功网页操作已重开原 session `01a1748d-b86a-7610-ad87-bcfab8cbc67a` 核验：使用 `xdotool` 操作原 Chrome；另一条成功链为 `SunoMusicService → suno --json --no-browser`。这只证明当时的实际路径，不证明当前验证码由某一驱动导致。原 CLI/UI intent、未知及阻断历史保留，不用新 UI 结果替换旧 UUID。

## Video Sources

- A01 第一版 SHA `65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5`，6.061 秒、1920×1080。构图偏离已认可图；旧严格闭口及旧文字要求也未满足。经真实 MCP、same-bytes evidence repair 和 canonical feedback 正规 `reject_video_generation` 关闭，Manifest 34，`failed / video_quality_rejected`。原片、消费和旧评价完整保留。
- A01 第二版 SHA `850b3807757e570dc59c2a6af96fcf930d8689322408e11f1be81db2c5adae1c`，6.080 秒、1920×1080。真实 payload 为认可阳台图和正面 ID7b；侧身 CF-a 保留为 identity/provenance 资料但未上传。当前 exact QA 四项经 MCP、145 帧检查与正常 1× 播放后，canonical raw analyzer Gate `PASS`，Manifest 19。它不代表真人验收、Provider 资格晋升或 Production 激活。
- C 室内观察在 A01-v2 canonical Gate 全通过后，经现有 committer 建立独立源素材项目并完成 prepare；不改 active qualification 的 A2 state。输入是认可 A03 和 ID7b，显示器背面保持，无设备操作或新闻贴图。已取回 6.080 秒、1920×1080 原片，SHA `974e83c050dd7cc079e6dabdf2ea3b168629d02fffc02cf8163c7881c4968f15`。真实 MCP、145 帧观察和正常 1× 播放后，经 canonical feedback 四项 `PASS`，Manifest 12。仍无真人接受或 Production 激活。
- 四个新闻图形源片均已完成并分别检查，见 `ep01/graphics/source-assets.json`。它们是独立素材，最终顺序、裁切、声音及字幕仍须由 `CompositionSpec → ResolvedTimeline → HyperFrames` 决定。

Source profile 的 `r_frame_rate=60` 不能当作恒定 60fps：已取回人物源片是 145 帧的 VFR，正常播放及最终 30fps 时间线解析分别验证。

## Cost And Authority

前两个即梦视频均已取回，余额从 68189 降至 67793，与两次 198 积分 native quote 一致；未另取正式逐笔账单。C 取回后同账户余额为 67595，三个视频单元累计余额下降 594，与三次 198 积分 native quote 一致。C 是第三个明确有限单元，最多一次、250 operator credits，累计最多 3 次、750；旧两次消费和 FAIL/PASS Gate hash 均在新 bound 中保留，不重置旧计数。具体一次性 permit、dispatch 和 paid state 仍归原 owner。

查看 `ep01/live-binding/`、`ep01/a01-repair-binding/`、`ep01/c-binding/` 的 intent、prepared、lint、submit/fetch 结果，以及 `ep01/qa/A01/`、`ep01/qa/A01-v2/` 的 canonical diagnosis 和 Gate。新 C 完成后先显式调用 project-local video-analysis 再推进；不得提前提交下一镜。

## Verification And Pending Work

浏览器 runtime 与源码接线已实测，不等于歌曲生成成功。Suno 等人工 Cloudflare；B 演唱镜头、逐字字幕和最终声画时序等真实歌曲。C 已完成 raw analyzer Gate；整片正常速度带声音验收尚未完成。

HEAD 仍为 `43c330bc9509d4e14ff91411d9cdf1b190f61810`。他会话的 22 条 staged 路径未动；本任务未 commit/push，未运行新的 related/full Harness。依成片优先规则继续制作，后续完整验证与发布不能冒称已完成。配置原文备份只在本机隔离 runtime，未放入 Git。

开发预览的 metadata/admission 仍需沿现有 owner：人物源片真实视频时长约 6017ms，而当前 `nominal_seconds + fps=None` 的严格 Production output-contract 比较要求 6000ms，故严格检查保留 `REJECTED`。已只读验证现有 `VideoProbeReceipt.create` 可绑定 held-FD 的真实测量后供 development-only qualification preview 使用；这不改严格时间检查，不伪造30fps/180帧，也不代表 Production probe 通过。预览裁切仍受真实145帧和现有 admission约束，歌曲、B演唱和实际时序未就绪前不封存成片 timeline。 `assembly-preparation/` 已保存真实 measurement receipt 候选，六项精准测试通过、39 个 source state 文件字节不变；正常验证退出0，缺失输入的 preview-ready 验证正确退出2。没有写 admission state 或 timeline。

## Learning Assessment

自动评估结果 `no_candidate`。这是一次实际 browser integration 与受平台验证阻断的有界观察；两个 A01 版本还同时变更参考职责和提示词，不能据此推出一般模型质量或验证码因果规则。没有新增或采用 Skill/Policy/Gate 学习规则，没有手工重建检索索引。
