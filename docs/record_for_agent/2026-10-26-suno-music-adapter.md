---
record_kind: architecture_implementation
topic_id: suno-music-adapter
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Suno Music Adapter Record

Date: 2026-10-26

## Purpose

记录把 `paperfoot/suno-cli` v0.10.1 接到 AI-VIDEO 配乐流程的边界：已安装的 CLI 与 Skill、离线 dry-run，以及未获得浏览器会话和付费授权时没有做的事。

## Current Runtime Truth

`src/ai_video/production/suno_music.py` 提供音乐导演、生成参数、本地恢复回执、WAV 资产候选和 P4 `AudioTrackSpec` 绑定。它不写 Manifest，不激活 Registry，也不求解验证码。`ProductionStateCommitter` 仍是唯一 v2 写入者，`ResolvedTimeline` 仍拥有 sample 时钟。

Suno 没有官方生成 API。CLI 走网站私有接口，许可证为 MIT。Terms of Service（修订 2026-08-10，2026-09-03 生效）禁止以服务未提供的方式获取内容，也禁止 robots / scraping。账号限制是真实风险。适配器拒绝 `--token`、`--force`、`--max-mode` 和凭证参数。

## Session Work And Decisions

- 二进制安装在 `~/.local/bin/suno`，版本 `0.10.1`，安装前核对了 release checksum。
- Skill 安装到 Codex、Claude、Gemini 和既有 `~/.agents/skills/suno`。这些路径在仓库外。
- 本地配置 `default_model=v6`。离线 dry-run 把 `v6` 映射为 `chirp-hawk`，并返回 `submitted=false`、`model_verified_live=false`。
- `suno auth --login` 报告浏览器中没有 Suno 会话。`credits` 和 `models` 因此返回 `auth_missing`。订阅、积分和 v6 资格是 `NOT_EVALUATED`。
- 导演按留白、底乐、角色主题、悬疑气氛或画面内歌曲决定，不把编辑窗口写进生成命令。
- 同一请求编号在未知结果或内容变化时拒绝再提交。回执不含歌词和凭证。
- `docs/agent-primary-contract-matrix.md` 当时已有其他未提交改动，所以没有追加 matrix 行。说明写在 `docs/suno-music.md`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| suno-dry-run-cli | suno-cli-0.10.1-offline-dry-run | suno-music-adapter-20261026 | dry-run-1 | N/A | NO_ARTIFACT:OFFLINE_CLI_ENVELOPE | technical | PASS | N/A | NEW_ATTEMPT | NONE | tests/test_suno_music.py::test_installed_cli_dry_run_does_not_submit |
| suno-auth-missing | suno-account-probe-20261026 | suno-music-adapter-20261026 | auth-probe-1 | N/A | NO_ARTIFACT:AUTH_MISSING | technical | NOT_EVALUATED | auth_missing | NEW_ATTEMPT | NONE | suno --json --no-browser credits |

## Verification And Evidence

`python -m pytest -p no:cacheprovider tests/test_suno_music.py -q`：8 passed。其中包含对已安装 CLI 的一次离线 dry-run。没有 `generate` 去掉 `--dry-run` 的调用，没有下载，没有扣费。

## Assessment

适配器可以离线决定配乐并拒绝未授权提交。它还不能证明当前订阅能使用 v6，也不能把音乐放进已激活成片。

## Remaining Risks Or Next Work

有浏览器会话后，先运行 `suno credits` 和 `suno models`，确认 v6 与剩余积分。用户明确授权后，才可以做一次付费生成。提交前若返回 `captcha_required`，停止，不自动解题。下载 WAV 后仍要测量响度，再由 `ProductionStateCommitter` 激活，并由时间线给出 `start_sample`。Matrix 与 Harness changed-path 映射尚未纳入这次改动。

## Agent Guardrails

- dry-run、`jobs` 和认证失败不证明账号余额或 v6 可用。
- CLI 成功或本地回执不是 P6、混音验收或 Manifest 激活。
- 不把 Cookie、JWT、Authorization 或浏览器库内容写入仓库、日志和回执。
- 不使用验证码求解器，也不把一次技术 PASS 当成听感验收。
