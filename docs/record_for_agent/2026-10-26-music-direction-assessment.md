---
record_kind: architecture_implementation
topic_id: music-direction-assessment
learning_eligibility: ineligible
---

# Music Direction Assessment And Enhancement

## Purpose And Decision

2026-10-26：用户要求研究 Suno CLI 与 v6 Songwriter，增强现有音乐导演，禁止未经授权的新付费生成。
使用 `retrieve-ai-video-memory`、现有 `suno` 操作 Skill、`open-video` 和本 record Skill；
没有安装新 Skill。研究与许可证据见[assessment](../research/2026-10-26-suno-music-direction.md)。

CLI 已有丰富操作与 offline composer；Songwriter 是 CC BY 4.0 的纯文字方法，不能替代执行器或
证明音画审听。选择增强现有 Director 的音乐判断、结构/配器表达与修订方法，保留独立 Suno CLI。
没有照搬七段输出、三次实验、主副歌模板或固定乐器数。

## Current Runtime Truth

原 Music Director 的类型与决策移到 `production/music_direction.py`，Suno model 与传输仍在
`suno_music.py`；原 imports 与 `MusicDirection(model=v6)` 兼容。`SceneMusicBrief.musical_design`
可由 Codex 显式填写叙事功能、音乐语言、配器、脉冲、发展、混音、延续、排除项与听音检查。
它不是自动理解剧本并作曲的模型。显式选择不再被情绪关键词覆盖；无设计调用保留原启发式。

QA 问题进入原 `qa_findings`/`MusicQaRequirement`，不创建审美评分或 acceptance state。
Suno adapter 继续产出候选与交接参数，不拥有完整 Production 的预算/permit/committer 编排。
真实文本 submit、下载恢复、主题源约束、音画听感和 activation 均未在本次执行。

用户明确允许在已脏的 `.agent/harness/policy.yaml` 只追加音乐映射；仅本次新增检查和类别进入
index，其他改动保留在工作区。未修改脏的 contract matrix；当前音乐边界由
[Suno contract](../suno-music.md) 指向源码 owner，不声称 matrix 已补登记。

## Verification

- Red：新增测试在没有 `music_direction` 模块时按预期导入失败；实现后音乐专项 20 PASS。
- Direct related：483 PASS、20 SKIP、2 个既有 Pydantic serializer warnings；
  JUnit：`.agent/harness/runs/suno-music-direction/direct-related.xml`。
  涵盖原 Suno、音频、composition、HyperFrames、原声/变速、Director Skill 和 runtime Skill 边界。
  后新增的两项音乐检查计入上述 20 PASS，不倒写为该次 483 的一部分。
- 对比实施前 `HEAD:suno_music.py`：六种 edit_need 的输出 dict、生成 hash、request ID 全相同；
  悬疑关键词 fallback 输出也相同。未改变原 Suno ledger、验证码、credential 或 submit/recovery 逻辑。
- 实际已安装 `suno` 的 authored-design dry-run 返回 `submitted=false`、`charged=false`、
  `model_verified_live=false`、`chirp-hawk`；这是离线协议验证，不证明账户资格或媒体质量。
- Documentation contract 与 owned diff whitespace 检查通过。
- Harness 拒绝 partly staged policy 的 staged scope（同文件保留其他任务的 unstaged 改动），
  因此在已通过上述验证的 owned checkpoint commit 上使用 commit range，隔离其他工作区改动。
  精确 commit-range 的 Harness 结果单独归
  `.agent/harness/runs/suno-music-direction-related-r3/receipt.json`；以 receipt 实际 verdict/level 为准。
  首轮 `suno-music-direction-related/receipt.json` 保留失败：新增测试组漏记 `full_tests.covers_check_ids`，
  harness 自测发现（320 PASS、1 FAIL），已补登记并重新验证；未降低测试或验收要求。
  第二轮 Harness 自测 321 PASS、音乐 20 PASS、架构/规则/policy audit PASS；音频合成组
  1042 PASS、18 SKIP、1 FAIL。失败为本机 Conda/native `libass` 链接的系统 harfbuzz
  找不到 `FT_Get_Transform`，同一错误在独立 `ctypes.CDLL` 与单测重现；该字幕源码未被本次修改。
  单次命令预加载现有系统 `/lib/x86_64-linux-gnu/libfreetype.so.6` 后，原失败单测 PASS。
  第三轮沿同一测试/源码与原 Harness no-network guard，仅使用这个命令级 `LD_PRELOAD`；
  没有安装依赖、改系统配置、跳过测试或修改字幕实现。此前失败 receipt 均保留。
  Direct JUnit 不冒充 Harness receipt 或全量回归。

## Review And Learning Decision

按 `/home/reggie/.codex/SUBAGENTS.md`：`NATIVE_REVIEW_NOT_REQUIRED`。本次是纯导演输入表达与
既有代码拆分，付费/凭据/状态写入逻辑未改，兼容和异常路径由相称测试覆盖；没有已知的重大
不可恢复失败路径或剩余语义缺口需要 reviewer 补证。由 Parent 检查最终 owned diff。

自动评估 `distill-ai-video-learning` 为 `no_candidate`：这是工程与来源研究，没有两次独立
音乐生成、对照实验或可升级的真实听感证据，不创建经验採纳/用户确认流程。

## Remaining Limits

成片音乐质量、实际叙事效果、主题旋律延续、专业混音与人工审听仍 `NOT_EVALUATED`。
现有 `audio_understand` 是观察工具，不提供剧情/音乐匹配裁决；不新增付费识音调用。
本次音乐生成/积分消耗为零，没有 credential/config 改动、媒体上传、Manifest/Registry/P6 写入。
现有账号历史核验见[原记录](2026-10-26-suno-music-adapter.md)，不当作当前余额。

稳定源码/文档 checkpoint 按本项目规则 commit/push；不是音乐 publication、Provider qualification
或成片 Final Acceptance。其他工作区改动不属于本次交付。
