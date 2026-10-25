# Suno Music Adapter

## Decision

AI-VIDEO 把 Suno 当作可选、默认关闭的配乐 Provider。音乐决策由 `music_direction.py` 独占，Suno 适配器负责模型与 CLI 传输；旧 `suno_music` imports 保持兼容。Codex 通过现有 Director 的 [Music Direction](../.agents/skills/open-video/references/music-direction.md) 根据剧情、人物与实际画面作音乐选择。成片时间线仍归 `ResolvedTimeline` 和 HyperFrames P4 mixer。生成音频要成为已激活资产，仍必须经过 `ProductionStateCommitter`。本模块只产出未提交的候选、恢复回执和混音绑定参数。

接入没有复制 `suno-cli` 的作曲器、验证码求解或浏览器登录。外部二进制只作为传输层。

## Unofficial API And Account Risk

Suno 没有面向这段生成流程的官方 API。`paperfoot/suno-cli` 是 MIT 许可证的第三方客户端，直接调用 Suno 网站使用的接口。Suno Terms of Service（最后修订 2026-08-10，2026-09-03 生效）禁止用服务未提供的方式获取内容，并禁止 data mining、robots、scraping 或同类提取。账号因此可能被限制或终止。本适配器不绕过验证码、不提交 `--token`、不使用 `--force`，也不把 Cookie、JWT 或 Authorization 写入代码、日志、回执和 Git。

订阅等级决定商用权利和下载配额。这里的许可证字段固定为 `suno-account-terms-unverified`，不声称已经获得商用授权。Suno 文档把标准 v6 生成记为两首 10 积分，Max Mode 更贵；未对当前账号复核前，这只是公开说明，不是报价。

## What This Slice Verifies

- 安装的 CLI 是 GitHub release `v0.10.1`，并核对了 Linux x86_64 校验和。
- `suno skill install` 已把 Skill 写到 Codex、Claude、Gemini 和既有 `~/.agents/skills/suno`。
- 本地配置的默认模型是 `v6`。离线 `generate --dry-run` 把 `v6` 显示为 `chirp-hawk`，并明确 `submitted=false`、`model_verified_live=false`。
- 初次接入时没有检测到会话；同日后续登录核验已取代此结论，见[原接入记录](record_for_agent/2026-10-26-suno-music-adapter.md)。本次增强没有刷新认证/余额/模型资格，历史余额不代表当前可用额度。
- 导演会在留白、纯音乐底乐、角色主题、悬疑气氛和画面内歌曲之间选择。编辑窗口只作为提示，不进入生成参数。
- 同一请求编号在未知结果或内容变化时拒绝再次提交。回执模式为 `0600`，不含歌词和凭证。
- 测量后的 PCM WAV 可以形成 `AssetType.MUSIC` / `AudioKind.BGM` 记录，并由调用方给出的 sample 起点生成现有 `AudioTrackSpec`。QA 结论保持 `NOT_EVALUATED`。

## Not Activated

没有真实生成、下载、Manifest 指针切换、Registry 激活或成片混音。Captcha、余额、v6 是否对当前订阅开放，都要在用户明确授权并且浏览器会话已经存在之后，先跑 `suno credits` 和 `suno models`，再决定是否允许一次付费提交。

## Authored Music Design

原 `direct_music(SceneMusicBrief)` 仍兼容简单启发式。专业制作由 Codex 在同一 brief 的
`musical_design` 作出叙事、音乐语言、配器分工、脉冲、发展、混音与延续选择；不新增导演模块。
显式设计不会被“紧张”等关键词替换，也不规定固定歌曲结构、BPM 或成片秒数。

```python
from ai_video.production.music_direction import (
    MusicalDesign, MusicEditNeed, MusicRole, SceneMusicBrief, direct_music,
)
from ai_video.production.suno_music import build_generation_argv

direction = direct_music(SceneMusicBrief(
    cue_id="departure", scene_id="corridor",
    script_excerpt="她把钥匙放下，关门离开。", emotion="不舍但确定",
    scene_facts="门边的停顿与钥匙落地声需要保留。",
    edit_need=MusicEditNeed.UNDERSCORE, dialogue_present=False,
    musical_design=MusicalDesign(
        role=MusicRole.INSTRUMENTAL_BED,
        narrative_function="让决定保持开放，不替人物提前宣告悲伤",
        style="稀疏室内乐",
        instrumentation="中提琴延长音承接呼吸，钢琴单音回应视线",
        pulse="自由速度，跟随呼吸",
        development="先稀疏陈述，离开后减少音符，开放尾音",
        mix_intent="近而干的音色，让钥匙落地声清晰可辨",
        exclusions="trailer impact, drum fill",
        listening_checks=("音乐不抢先替人物哭泣",),
    ),
))
argv = build_generation_argv(direction, dry_run=True)  # 仅构造，不执行/付费
```

此 API 是导演选择的可执行表达，不是从剧本自动推理作曲的独立模型。旧 `suno_music.MusicDirection`
保留 `model=v6` 的输入兼容；provider-neutral `MusicDirection` 不含 Suno model。
新音乐结构改变生成身份；编辑窗口移动不改变身份。`qa_findings` 带入叙事、发展、混音、延续和
自定义听音问题，`music_qa_requirement` 仍为 `NOT_EVALUATED`，没有新增自动质量分数。

Suno 的网页多模态/局部编辑不等于本适配器已接通。独立 CLI 的 extend/cover/stems 仍可作为
独立工具能力研究，本适配器当前只封装文本生成；它没有整个 Production 的 paid Budget Guard /
permit / committer 执行编排，不能把 `paid_generation_authorized=True` 当作这些 Gate 的替代。
真实生成、下载恢复、主题旋律延续、混音与听感闭环仍须在各自授权和 canonical owners 下验证。

研究、许可证、已有覆盖和未引入项见[评估报告](research/2026-10-26-suno-music-direction.md)。
