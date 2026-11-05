---
record_kind: architecture_implementation
topic_id: captioned-music-development-preview
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Captioned Music Preview Continuation

Date: 2026-10-30

## Supersession Notice — Native UI Follow-up

本文 Suno「正常表单、尚未新增 Create」是该次接续的历史观察。用户随后要求改回 `xdotool`；已在原 Chrome 实际单击一次并进入 Cloudflare／图片人工验证，尚未有新歌。最新请求、次数和真实截图见 [native UI record](2026-10-30-suno-native-xdotool-restart.md)。下述代码、审查、基线失败与原 index 保留结论仍有效，后续没有因此新增工程实现或完成成片。

## Purpose

接续用户指定 session `01a18ea5-cafe-7c73-a5b9-75c95b39f5e0`，目标仍为 IRIS EP01《Looked Outside》25–30 秒横版带声成片。三张参考已获认可；保留 AI 标识，人物生成片内不新增剧情字幕和图形，后期英文逐字字幕、简中译句与独立新闻图形仍在范围内。renderer 继续使用 HyperFrames。

## Current Media And Suno State

当前六段源素材及八个无虚构剪点的 Shot 候选仍通过原准备 validator；六项准备测试通过。`validate --require-preview-ready` 正确退出 2，整片仍缺歌曲、B 演唱/对嘴、实际字幕时序与歌曲驱动的剪点。審看服务 `http://127.0.0.1:8767/ep01/` 及 A01-v2/C-v1 MP4 的 HEAD 均为 200，不代表本轮重新执行逐镜或人工验收。

当前 Suno 官方页为账号 `sunruijie42` 的正常表单，截图未见实际 challenge；CLI doctor 的 `captcha_preflight` 仍为 `required:true`。曲库重新读取仍只有六首 2026-10-25 旧歌、没有 IRIS，余额仍为 2470。历史至少四次 UI Create 保留 `outcome_not_proven` / `NOT_CONFIRMED`；余额未变、无新歌和 challenge 暂不可见都不足以改判 `KNOWN_NO_EFFECT`。本轮没有 Create、重试、付费 submit、challenge 求解或 token 读取。仍需用户验证结果或实际 clip identity，不能通过换 route 重开未知请求。

只读观察与原 intent anchors 见 `outputs/ai-city-takeover/ep01/audio/continuation-readback-20261030.json`。原即梦三次/594 积分历史和原片 Gate 均保留，本轮没有新增媒体或花费；未结算的历史 Suno 结果不被写成零消费证明。

## Shared Runtime Change

公开接线测试揭示两个确定性缺口：replacement preview 原来只允许同源 captured DIALOGUE 字幕；reader 又无条件比较来源 script hash，而 MUSIC/BGM metadata 按契约不能带 voice script identity。

新增显式 `development-qualification-preview/2`，保留原 `/1` 字节语义及 captured DIALOGUE 检查。`captioned_music` 封存唯一 global MUSIC/BGM track、音讯 SHA、真实样本窗口及各字幕 asset ID、bytes SHA、script/transcript hashes；生成来源保留 GENERATED，两层 kind/tool/input fingerprint 必须一致。英文与中文可分别具有不同 script/transcript identity。

reader 仅对 exact `/2` 歌曲字幕开放该有界例外，仍拒绝一般 BGM/SFX、旧 `/1`、冲突 binding 和改变后的字幕。resolver 要求实际选用对应的 `/2` 视觉、所有捕获具有相同 binding、原片显式静音、歌曲完整覆盖输出样本窗口；保留单一 `ResolvedTimeline` 和 `development_audio_preview`，Production activation 双重 fence 保留。此 binding 是作者选定的字幕身份，不是 ASR、演唱或对嘴质量证明。

只读 preparation 可使用含歌曲/字幕候选的 Registry；目标先经 committer bootstrap 尚未消费的捕获 receipt，标准 loader 可以重开。之后一次 `prepare_audio_registry_commit` 同时接入真实音讯、canonical captions 和 style，重新加载后才能 resolve。没有绕过 committer 写文件或持久化无效中间 Registry。

修改 owner 为 `qualification_preview_input.py`、`repair_input_admission.py`、`_composition_visual.py`、`validation.py`，回归在现有两份 qualification/caption 测试；canonical contract 已同步 `docs/agent-primary-contract-matrix.md`。未改 audio/CaptionTrack/CompositionSpec/ResolvedTimeline schema、renderer、Provider 或依赖。

## Verification And Evidence

证据目录：`outputs/ai-city-takeover/ep01/assembly-preparation/captioned-music-verification/`。

- 当前混合工作树公开接线测试：`python -m pytest -p no:cacheprovider tests/test_qualification_preview_input.py tests/test_caption_development_preview.py -q`，53 passed。正例含 IMPORTED、GENERATED、双语、bootstrap/reopen/单次 audio+caption commit/公开 resolve；负例含未导入、无 opt-in、冲突 receipt、未选原片的 Production 旁路、错 SHA、额外音轨、错字幕绑定、native KEEP、retime 和短音讯。
- 独立 code review：`APPROVE`，0 findings；7 条路径的 hashes、6 份 Python AST 和 whitespace 检查通过，11 项独立 unit cases 通过。固定目标 tree 为 `d8f257613d350a0235fbc09bbca64f7852605962`，见 `review-target.json` 和 `code-review.json`。
- 仅本任务 7 路径投影的 focused Harness：37 failed / 1 passed，错误都在既有 generation fixture 的 `identity_continuity.character_ids[hero]`，尚未进入新 preview 接线。未修改 HEAD 的单项既有 qualification 测试也以同一错误失败，见 `head-baseline.json`；失败 receipt 原样保留在 `owned-projection-focused-failed/`。
- 原工作树 53 项通过依赖另一会话已有的 reference-authoring/fixture 改动；不得把它称作 7 路径隔离通过。另建的 28 路径混合依赖快照由 `mixed-target.json` 固定，明确包含原 22 条 staged 路径的当前 working bytes，其中 `tests/reference_authoring_fixture.py` 还带既有 unstaged delta。这些依赖不属于本任务修改归属。
- 混合依赖快照的 focused Harness `FAIL`：`generation_feedback_tests` 为 654 passed、1 skipped、3 failed（726.222 秒），其余依赖检查按 Harness 规则跳过。三项均为已有 fixture fingerprint golden 不符；在完全不含本次六个 source/test 改动的 dependency-only tree `2b95b504a9991af74a1efc4c882934e9c929afe9` 中，三项再次以相同实际/预期 hash 失败（5.63 秒）。对应 `mixed-focused-failed/receipt.json`、`dependencies-only-failures.json` 和 JUnit 保留原结果，没有修改 golden 或认领他会话修复。
- 本任务两份精准测试随后在固定混合 tree `75116eccba6e2f49a426585aaba574f372ff8a79`、使用 Harness 的隔离环境与禁网 pytest guard 重跑，53 passed（29.03 秒），见 `mixed-targeted-tests.json`、`.junit.xml` 和 stdout。该证据仍明确属于混合依赖快照。
- focused Harness 尚未通过，related/full 未运行；没有真实 EP01 render、歌曲 ASR、对嘴或人工成片验收。2026-10-31 00:54:38 UTC 最后只读 Suno 仍是六首旧歌、无近期 clip、余额 2470。

CodeGraph 未取得可用返回，结构判断使用当前源码、公开加载/committer/resolver 测试与独立审查，不把索引当当前结构证明。Agent Memory experience shard 返回 library-incompatible、已由 CLI 排队，未手动重建或重复检索。

## Ownership And Publishing

原工作区 index 保持 tree `8d3bfcd181c529fc8dedfd2082a463e0becf65e5`，staged patch SHA `784f0f5729b5e1ff650f092cad703ce4c4ce1dbfe5bd172080318e0a3c3ed5a9`，见 `preserved-main-index.json`。没有替他会话 stage、commit、回滚或认领其依赖；matrix 的原 staged 改动与本任务新增段落分开保留。只创建临时验证快照，没有开发分支或 dedicated development worktree。

本任务未 commit/push；遵循成片优先，实际歌曲与正常速度带声成片验收尚缺。当前 HEAD 仍为 `43c330bc9509d4e14ff91411d9cdf1b190f61810`，不声称已发布或完成全片。

## Remaining Work

先解决现有 Suno 请求的真实结果；取得确切歌曲后保留 UI/CLI 各自 provenance，不能将 browser 产物冒绑失败 CLI UUID。再测实际全词时长、节拍、字幕时序与 30 秒约束，使用已认可 A02 参考制作 B 演唱并完成逐镜 Gate；实际字幕 binding 和 source windows 经原 committer/resolver/HyperFrames 合成，执行 assembly review 及正常速度带声人工验收。前三次即梦单元已消耗，后续必要有限单元保留旧消费和 Gate 历史，不重置计数。

## Learning Assessment

已按 `distill-ai-video-learning` 自动评估：`no_candidate`。这是有界确定性契约接线与平台未决状态观察，不构成模型质量、Suno challenge 因果或跨实验经验；没有新增或采用 Skill/Policy/Gate 学习规则。
