---
record_kind: session_summary
topic_id: elevenlabs-shared-context-claude
learning_eligibility: ineligible
---

# Shared ElevenLabs Context Entry And Claude Registration

> 当前状态更新：用户指定项目根 `.mcp.json` 后已迁移为 project-scope，先前新增的 user-scope 项已移除。见下文 Project Scope Correction；旧 user 配置部分保留为操作历史。

## Scope And Result

用户明确要求把上下文接入共享入口，并注册到 Claude。本次接入工程与只读 MCP 验证，
不恢复前序 UNKNOWN、不生成音频或增加媒体消费。
共享 CLI 新增 `--performance-context FILE --line-id ID --preview-context`。
Codex/Claude 均可调用相同入口，不必复制台词和 tags，不把作品内容硬编码进业务模块。
完整导演说明供 Agent 创作/审听，实际模型输入是经过校验的所选行 tags+台词，
没有宣称已接通整场 Text to Dialogue 或将未朗读说明混入对白。

## Shared Input Contract

`scripts/elevenlabs_performance_context.py` 只读128KiB以内普通 JSON，目录与文件均 no-follow。
校验 source plan SHA、重复 JSON key/ID、路径包含及选中行 id/text/role/unit/shot_s 的精确类型和值，
验证模型与 tags 并重新编译 synthesis text，不信任包内候选字符串。
包 SHA 和 line ID 封存进既有 batch source_reference；旧 --text 默认路径保持兼容。
preview 不读凭据、不加载 Production、不写 root、不联网，不是 canonical paid preview。

当前真实包 BLOCKED 且保留 unresolved attempt 指针，实际执行在读取凭据/Production 与
transport 之前 typed error 停止。READY_FOR_CANONICAL_PREFLIGHT 仅表示输入无该项额外限制，
不授予任何权限；canonical permit/budget/egress/root exact replay 与 UNKNOWN recovery 不变。
无 force 参数。上下文包字段不能用来证明外部结果或覆盖 canonical state。

CLI exact Secret Service supplier 只在 D-Bus 地址缺失时配置当前 UID 的确定 user bus；
已有地址保留，不改变全局环境，不在 lookup 失败后切换来源、不读 .env、不 retry。
实际只读 lookup 成功，未输出 key。

## Claude Configuration

本机 Claude Code 2.1.311 的 `claude` 命令使用隔离包装器。实际 user 配置为
`/home/reggie/.local/share/claude-browser-only/state/home/.claude/.claude.json`，
不是 `/home/reggie/.claude.json`。先前普通 home 配置备份保留但未在其内注册。
CLI 注册时自动保存写前备份，已核对备份中没有该 entry，再另存同目录
`.claude.json.elevenlabs-direct-20261030-pre-registration.bak`（mode600）。
注册命令为 `claude mcp add --scope user elevenlabs-direct -- /home/reggie/.local/share/elevenlabs-direct/launch.sh`。
同名 server 与现有 Codex 指向同一固定commit安装，认证仍只经精确 Secret Service 引用。
原有配置未移除；CLI 同时刷新 oauthAccount.profileFetchedAt 元数据，未输出其内容。
未重启共享 daemon、卸载插件、复制密钥或写入 credential env/argv。

`claude mcp get elevenlabs-direct` 返回 Connected。随后读取该实际配置，经同一 launcher
做 MCP SDK initialize/list_tools/search_voices：27 tools，10条音色，HTTP200、isError=false。
这是 Claude CLI 连接检查与 SDK 查询的分开证据，未冒充 Claude 模型会话已调用生成。
本机摘要 `/home/reggie/.local/share/elevenlabs-direct/claude-registration-verification.json`。
新会话加载注册；旧会话热加载未验证。
禁用/回滚仅移除本项：`claude mcp remove elevenlabs-direct -s user`，不要整份恢复覆盖后续配置。

## Verification And Limits

context 接入新增21个测试；参数/existing context suite 198 passed，后续 user-bus 两个
边界用例加入后完整 batch suite 44 passed。覆盖无I/O preview、阻塞先于副作用、输入冲突、
source drift/类型/路径/symlink/重复/大小限制、canonical fake transport、context hash 与 replay。
独立 reviewer 两轮无问题，AST/whitespace 通过；真实 L3 preview 为 network_calls=0、
authoring_blocked=true、authorization_granted=false。真实包仅做离线读取，不新增 provider POST。
对应 exact commit-range Harness receipt 与远端 SHA 以本次最终验证输出为准。

此前表演控制代码的“未提交”检查点由本工程接入任务的提交更新；旧媒体 UNKNOWN、
历史候选身份缺口、女声未提交及无最终听感接受仍保持，不混成配音已修好。
voice-routing、audio-understanding 和 lockfile 的其他窗口 dirty/staged 工作不归本次提交。
`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
本次是输入接线与连接证据，没有新的模型表演实验或质量结论。

## Project Scope Correction

用户明确指定 `/home/reggie/vscode_folder/AI-VIDEO/.mcp.json`，注册已改为该项目文件。
写前备份 `/home/reggie/.local/share/elevenlabs-direct/backups/AI-VIDEO-mcp-before-20261030T061412Z.json`
mode600；只新增 elevenlabs-direct，原有7个服务器内容和格式保留。
移除本次 user-scope 同名项，避免两个配置 owner。仅对这个 server 做项目定向 approval，
没有 reset 其他 MCP 决策或重启 daemon。
`claude mcp get elevenlabs-direct` 已连续两次读回 Project config (shared via .mcp.json)、Connected。
实际 user 配置虽不再注册 server，仍承载该 Claude 客户端的 project trust；不把它当项目 MCP owner。
本机当前证据 `claude-project-health.txt` 与 `claude-project-registration-verification.json`
位于 `/home/reggie/.local/share/elevenlabs-direct/`。原 user-scope 证据只作为历史保留。
后续移除项目项使用 `claude mcp remove elevenlabs-direct -s project`。
