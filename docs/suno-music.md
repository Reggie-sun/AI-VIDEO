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

后续《失帧》实测已通过官方网页生成，并经 CLI 查询/下载；这不证明纯 CLI 生成恢复。
尚未执行 Manifest 指针切换、Registry 激活或成片混音。新提交仍需任务授权与剩余次数，
模型资格及认证/人机验证前检必须核实；余额仅按用户要求报告，不额外设置预算 gate。

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

## Live Pilot — 2026-10-26

《失帧》第一集的有界实测已尝试一次 `generate`，CLI 返回 `auth_expired`、没有 clip ID。
账号读取仍显示 Pro / v6 可用；前后余额均 2500 credits、monthly usage 均 0，读取成功不证明
生成认证有效。CLI jobs 的 `rejected` 与项目 `submission_unknown` 分别保留，不改历史、不重提。
用户本轮明确关闭金额/积分 budget gate，只据实报告消耗；原最多三次请求、one-use、unknown、
账号与平台边界保持。实验没有创建音乐资产、激活或改写全局付费策略。

执行前修复了真实 CLI `data: Clip[]` 成功信封的识别；旧对象形式仍兼容，空/坏数组仍 UNKNOWN。
该兼容有离线契约回归，尚未由成功 live generation 验证。具体素材、Prompt、错误/恢复、
当前音频输入受阻与生产限制见[本轮记录](record_for_agent/2026-10-26-shizhen-suno-live-pilot.md)
及[配乐方案与评估](superpowers/artifacts/drama/shizhen-episode-01/music-pilot-20261026/spotting-and-evaluation.md)。


## Generation Readiness Repair

doctor的success/pass不等于可生成，captcha_preflight.detail仍可能required:true。
SunoMusicService现在先只读核验jwt、studio_api、captcha_preflight；要求验证或检查不明确时，
在generate与UNKNOWN写入前停止。不用积分检查设置预算gate；submitted回放及UNKNOWN拒绝先执行。
官方网页的实际challenge仍由用户处理，适配器不求解/搬运token。当前36项精准回归通过。
《失帧》第3次通过原登录官方网页生成一对v6，CLI查询/下载MP3、WAV成功，消耗10 credits。
此证据不证明纯CLI生成认证恢复；候选未登记激活，音乐/声画待审听。最新状态见配乐报告的
Official UI Recovery节，旧认证受阻ZIP保持历史，当前盘满导致commit/push受阻。

### CLI Skill And Argument Repair

后续修复取代上一段的代码验证数量及磁盘阻塞状态。已同步修订现有
`~/.agents/skills/suno/SKILL.md` 和 `~/.codex/skills/suno/SKILL.md`，保留更新前备份。
不新增 Skill、不安装求解器、不改账号凭据或已消费请求。

在上游 [main.rs 的 resolve_captcha](https://github.com/paperfoot/suno-cli/blob/6d28c67a733b32183a80d81306bf0013f46b00b7/src/main.rs)
中，`--no-captcha` 会直接返回空 token，跳过平台前检，不能当作安全的“禁用求解器”。
项目现在不生成该参数，并拒绝向 transport 传入它；统一通过 `--json --no-browser` 调用 CLI，
保留原生检查，同时禁止浏览器求解。doctor 到实际调用之间平台要求若变化，CLI 仍可在 POST
之前返回 `captcha_required`，项目记录 `known_no_effect`，不把它误当成功。

Skill 还修正了 doctor 的 pass/detail 语义、`list` 命令、已有自定义 Chrome profile 的选择、
认证错误的歧义、官方网页与 CLI 事务的区别和下载/审听证据边界。不会再让用户重复登录错误窗口，
也不会因为刷新认证就重提 UNKNOWN。`auth_expired` 不能单独证明 JWT 失效或 captcha 是唯一根因。

当前精准回归37项通过；真实安装 CLI 的新 argv dry-run 已执行，submitted=false；
live 仅运行只读前检，没有第4次生成。REA 的 browser target 读取返回 invalid_endpoint_response，
所以本次未获得网页协议捕获；源码给出的是确定参数语义，不冒充完整根因逆向。
证据及当前平台阻塞见[修复记录](record_for_agent/2026-10-26-suno-cli-skill-preflight-repair.md)。

随后用户新增一次真实生成授权，修复后的 `SunoMusicService → CLI` 已获得两首complete/v6，
并完成MP3/WAV下载、完整解码、标准音频测量与未提交候选资产记录。真实提交ledger回放0网络调用。
新增10 credits、累计20，余额2480；不再追加。本次已证明纯CLI实际接入，但没有Scene04声画
审听或canonical Registry激活，仍不代表专业配乐质量或成片生产验收。详见同一记录的Live CLI Recovery。
