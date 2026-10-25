---
record_kind: architecture_implementation
topic_id: suno-music-adapter
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Suno Music Adapter Record

Date: 2026-10-26

## Purpose

记录把 `paperfoot/suno-cli` v0.10.1 接到 AI-VIDEO 配乐流程的边界：已安装的 CLI 与 Skill、离线 dry-run，以及 2026-10-26 对指定 Chrome 配置文件完成的登录核验。付费生成仍未授权。

## Current Runtime Truth

`src/ai_video/production/suno_music.py` 提供音乐导演、生成参数、本地恢复回执、WAV 资产候选和 P4 `AudioTrackSpec` 绑定。它不写 Manifest，不激活 Registry，也不求解验证码。`ProductionStateCommitter` 仍是唯一 v2 写入者，`ResolvedTimeline` 仍拥有 sample 时钟。

Suno 没有官方生成 API。CLI 走网站私有接口，许可证为 MIT。Terms of Service（修订 2026-08-10，2026-09-03 生效）禁止以服务未提供的方式获取内容，也禁止 robots / scraping。账号限制是真实风险。适配器拒绝 `--token`、`--force`、`--max-mode` 和凭证参数。

## Session Work And Decisions

- 二进制安装在 `~/.local/bin/suno`，版本 `0.10.1`，安装前核对了 release checksum。
- Skill 安装到 Codex、Claude、Gemini 和既有 `~/.agents/skills/suno`。这些路径在仓库外。
- 本地配置 `default_model=v6`。离线 dry-run 把 `v6` 映射为 `chirp-hawk`，并返回 `submitted=false`、`model_verified_live=false`。
- 早先 `suno auth --login` 只扫描标准浏览器目录，报告没有 Suno 会话。该结论已被同日稍后的登录核验取代，见 Evidence Index 的 `suno-auth-missing` 与 `suno-auth-pro`。
- 用户指定的 Google 账号出现在 Chrome 头像菜单：`ruijie • reggie`，`sunruijie42@gmail.com`。对应正在运行的配置是 `--user-data-dir=/home/reggie/.config/chrome-profiles/cp-e7be810d639e`、`--profile-directory=Profile 1`。该配置里的 suno.com 已经登录为 `sunruijie42`。
- `suno auth --login` 不读取 `chrome-profiles`。本次让 CLI 的标准 Chrome 查找指向这个 user-data-dir 后，登录成功。凭证只写在仓库外的 `~/.config/suno-cli/auth.json`，模式 `0600`。
- 登录结果：`Pro Plan`，剩余 `2500` credits。`suno --json --no-browser models` 列出 `v6` / `chirp-hawk`、`v6-wild` / `chirp-hawk-wild`、`v6-mini` / `chirp-goose`，三者 `can_use` 均为 true。没有运行去掉 `--dry-run` 的 `generate`。
- 导演按留白、底乐、角色主题、悬疑气氛或画面内歌曲决定，不把编辑窗口写进生成命令。
- 同一请求编号在未知结果或内容变化时拒绝再提交。回执不含歌词和凭证。
- `docs/agent-primary-contract-matrix.md` 当时已有其他未提交改动，所以没有追加 matrix 行。说明写在 `docs/suno-music.md`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| suno-dry-run-cli | suno-cli-0.10.1-offline-dry-run | suno-music-adapter-20261026 | dry-run-1 | N/A | NO_ARTIFACT:OFFLINE_CLI_ENVELOPE | technical | PASS | N/A | NEW_ATTEMPT | NONE | tests/test_suno_music.py::test_installed_cli_dry_run_does_not_submit |
| suno-auth-missing | suno-account-probe-20261026 | suno-music-adapter-20261026 | auth-probe-1 | N/A | NO_ARTIFACT:AUTH_MISSING | technical | NOT_EVALUATED | auth_missing | NEW_ATTEMPT | NONE | suno --json --no-browser credits |
| suno-auth-pro | suno-account-probe-20261026-login | suno-music-adapter-20261026 | auth-probe-2 | N/A | NO_ARTIFACT:AUTH_JSON_PLAN_CREDITS | technical | PASS | N/A | CONCLUSION_SUPERSEDED | suno-auth-missing | suno auth --login --json |

## Verification And Evidence

`python -m pytest -p no:cacheprovider tests/test_suno_music.py -q`：8 passed。其中包含对已安装 CLI 的一次离线 dry-run。没有 `generate` 去掉 `--dry-run` 的调用，没有下载，没有扣费。

## Assessment

适配器可以离线决定配乐并拒绝未授权提交。指定账号的网页会话已经换成 CLI 本地认证：Pro Plan，2500 credits，v6 可用。这仍不是付费生成、听感验收或 Manifest 激活。

## Remaining Risks Or Next Work

用户明确授权后，才可以做一次付费生成。提交前若返回 `captcha_required`，停止，不自动解题。下载 WAV 后仍要测量响度，再由 `ProductionStateCommitter` 激活，并由时间线给出 `start_sample`。Matrix 与 Harness changed-path 映射尚未纳入这次改动。标准 `suno auth --login` 以后若只扫 `~/.config/google-chrome`，会再次看不到这个自定义配置文件里的会话。

## Agent Guardrails

- dry-run 和 `jobs` 不证明账号余额。余额和 v6 资格只以当次 `suno auth --login` / `credits` / `models` 的结果为准。
- CLI 成功或本地回执不是 P6、混音验收或 Manifest 激活。
- 不把 Cookie、JWT、Authorization 或浏览器库内容写入仓库、日志和回执。
- 不使用验证码求解器，也不把一次技术 PASS 当成听感验收。
