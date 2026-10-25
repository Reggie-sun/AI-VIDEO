# Suno Music Adapter

## Decision

AI-VIDEO 把 Suno 当作可选、默认关闭的配乐 Provider。音乐导演只决定角色、情绪、器乐或唱词，以及是否在对白下让路；成片时间线仍归 `ResolvedTimeline` 和 HyperFrames P4 mixer。生成音频要成为已激活资产，仍必须经过 `ProductionStateCommitter`。本模块只产出未提交的候选、恢复回执和混音绑定参数。

接入没有复制 `suno-cli` 的作曲器、验证码求解或浏览器登录。外部二进制只作为传输层。

## Unofficial API And Account Risk

Suno 没有面向这段生成流程的官方 API。`paperfoot/suno-cli` 是 MIT 许可证的第三方客户端，直接调用 Suno 网站使用的接口。Suno Terms of Service（最后修订 2026-08-10，2026-09-03 生效）禁止用服务未提供的方式获取内容，并禁止 data mining、robots、scraping 或同类提取。账号因此可能被限制或终止。本适配器不绕过验证码、不提交 `--token`、不使用 `--force`，也不把 Cookie、JWT 或 Authorization 写入代码、日志、回执和 Git。

订阅等级决定商用权利和下载配额。这里的许可证字段固定为 `suno-account-terms-unverified`，不声称已经获得商用授权。Suno 文档把标准 v6 生成记为两首 10 积分，Max Mode 更贵；未对当前账号复核前，这只是公开说明，不是报价。

## What This Slice Verifies

- 安装的 CLI 是 GitHub release `v0.10.1`，并核对了 Linux x86_64 校验和。
- `suno skill install` 已把 Skill 写到 Codex、Claude、Gemini 和既有 `~/.agents/skills/suno`。
- 本地配置的默认模型是 `v6`。离线 `generate --dry-run` 把 `v6` 显示为 `chirp-hawk`，并明确 `submitted=false`、`model_verified_live=false`。
- 当前机器没有浏览器里的 Suno 会话。`credits`、`models` 和订阅资格因此是 `NOT_EVALUATED`，没有执行登录抓取以外的认证，也没有消耗积分。
- 导演会在留白、纯音乐底乐、角色主题、悬疑气氛和画面内歌曲之间选择。编辑窗口只作为提示，不进入生成参数。
- 同一请求编号在未知结果或内容变化时拒绝再次提交。回执模式为 `0600`，不含歌词和凭证。
- 测量后的 PCM WAV 可以形成 `AssetType.MUSIC` / `AudioKind.BGM` 记录，并由调用方给出的 sample 起点生成现有 `AudioTrackSpec`。QA 结论保持 `NOT_EVALUATED`。

## Not Activated

没有真实生成、下载、Manifest 指针切换、Registry 激活或成片混音。Captcha、余额、v6 是否对当前订阅开放，都要在用户明确授权并且浏览器会话已经存在之后，先跑 `suno credits` 和 `suno models`，再决定是否允许一次付费提交。
