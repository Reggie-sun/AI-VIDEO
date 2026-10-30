---
record_kind: session_summary
topic_id: elevenlabs-direct-mcp
learning_eligibility: ineligible
---

# ElevenLabs Direct MCP Installation

## Result

本机 Codex CLI 0.166.0 新建短生命周期会话通过 `elevenlabs-direct` 成功调用
`search_voices({})` 与 `list_models({})`，两者均 completed、error=null，Codex exit 0。
前者返回默认页 10 条音色（不是全部账户音色），后者返回 11 个模型。
独立 MCP 握手与 tools/list 返回 27 个工具，直接音色查询 HTTP 200。
没有生成音频、克隆声音或执行付费操作；不证明配音质量改善。

## Installation And Credentials

官方仓库 https://github.com/elevenlabs/elevenlabs-mcp ，固定 commit
`c6dc1688ead5e0e67cdcaa5e336bed647019340c`，包版本 0.12.2，Python >=3.11。
本机使用 Python 3.13.5 独立 venv；上游已归档并停止维护，官方推荐 hosted MCP。

安装目录 `/home/reggie/.local/share/elevenlabs-direct/`；入口 `launch.sh`；
依赖清单 `requirements.lock`；操作说明 `README.md`；完整工具 schema `tools.json`。
用户配置 `/home/reggie/.codex/config.toml` 新增独立 stdio 名称且已启用，备份为
`/home/reggie/.codex/config.toml.elevenlabs-direct-20261029.bak`。
现有插件保留；没有重启共享 daemon。当前聊天不热加载新增工具，新会话加载。

凭据通过项目指定 Secret Service 精确引用
`application ai-video / provider elevenlabs / credential ELEVENLABS_API_KEY` 注入进程环境。
原查询因缺失 D-Bus 地址失败，连接当前用户 `/run/user/1000/bus` 后查询成功。
未读取用户指定的 `.env`，未把密钥写入配置、argv 或日志；启动关闭 dotenv 自动加载。

## Evidence And Limits

本机证据（相对安装目录）：`verification-summary.json`、`tools.json`、
`voice-query.json`、`codex-verification.jsonl`、`codex-verification.stderr`。
summary 内封存入口、依赖、schema 和 Codex JSONL 的 SHA-256。
首次直接探针误用不存在的 `get_voices` 返回 Unknown tool，随后按实际 schema 改用
`search_voices` 成功；该失败没有触发 API 请求。依赖下载曾被中止，续行安装最终成功。
Codex 验证仅在该次调用中禁用其他 MCP/插件，并限制三个已核实查询工具。

模型查询返回 eleven_v4、eleven_v4_turbo、eleven_v3、eleven_v3_conversational、
eleven_multilingual_v2、eleven_flash_v2_5、eleven_turbo_v2_5、eleven_turbo_v2、
eleven_flash_v2、eleven_english_sts_v2、eleven_multilingual_sts_v2。
模型可查询不证明每个模型与每个生成工具兼容，本次没有生成验证。

TTS schema 暴露 voice_id/voice_name、model_id、stability、similarity_boost、style、
use_speaker_boost、speed、language、output_format 等；无独立 emotion/tone/seed 参数。
此版本 language 只参与默认模型选择，不传给 API language_code。
上游 TTS readOnlyHint 标注不可靠，不能用它决定是否收费。
任何 Production 生成仍遵守项目预算、permit、egress 和媒体 Gate。

现有插件走 OAuth hosted 路由，本配置走固定本地代码/API key/stdio。
未成功枚举插件实际工具，不能宣称全量工具差异或已定位其 Unknown tool 根因。
其他窗口的 staged/dirty 业务改动保留；备份后其他配置项也发生变化，来源未归因，
因此回滚仅移除本项，不能无条件整份恢复旧配置。

## Operations

Codex 自动启动 stdio server；新会话指定调用 elevenlabs-direct 的 search_voices。
禁用：本项 enabled=false；启用：enabled=true，随后新开会话。
回滚注册：`codex mcp remove elevenlabs-direct`，保留安装目录与插件。
恢复注册：`codex mcp add elevenlabs-direct -- /home/reggie/.local/share/elevenlabs-direct/launch.sh`。
升级先核验完整 commit，在另一 venv 安装并冻结依赖，通过只读验证后备份入口并切换
exec 路径；保留旧 venv，回滚时恢复旧入口路径。详见本机操作说明。

`record-ai-video-session` 已评估并记录；`distill-ai-video-learning`：no_candidate。
这是一次连接与安装验证，没有独立媒体对照或质量证据，不产生通用制作规则。
