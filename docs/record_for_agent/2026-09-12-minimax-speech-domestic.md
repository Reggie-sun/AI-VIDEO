---
record_kind: architecture_implementation
topic_id: minimax-speech-domestic
learning_eligibility: ineligible
---

# MiniMax Speech Domestic Integration

Date: 2026-09-12

## Scope And Runtime Truth

用户明确要求接入国内 MiniMax Speech。本轮只扩展现有 adapter、voice preview 与语音 batch paid gate 的 exact origin 白名单，并让既有脚本默认选择国内站。没有新 Provider/lifecycle owner，没有修改视频路径、原 S03 或旧 unknown run，没有 commit/push/worktree。

官方国内 HTTP endpoint 为 `https://api.minimaxi.com/v1/t2a_v2`，参考 [API 文档](https://platform.minimaxi.com/docs/api-reference/speech-t2a-http)。现有两个 speech-2.8 模型、Chinese/English 和 WAV 合同保持不变。不跟随 redirect，不自动切换站点。

`MiniMaxSpeechProviderPolicy.origin` 默认仍是历史国际站。`MiniMaxSpeechTestBatch.region="cn"` 明确封存国内 batch identity，CNY 仅为账本币种标签，不代表已查价或已知费用；缺失 region 的历史 batch 保留国际语义，序列化省略该字段，旧 policy hash 不变。CLI `python -m scripts.minimax_speech_batch` 默认 `--region cn`；旧国际 root 需显式 `--region international`。跨 region 重开同 root 在 submit 前拒绝，不迁移账本。

国内凭证引用是 `MINIMAX_SPEECH_CN_API_KEY`，独立于旧 `MINIMAX_SPEECH_API_KEY`；操作引用见 [playbook](../../.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)。metadata-only `Secret.Service.SearchItems` 查国内 exact attributes 返回 unlocked/locked 两者均空。没有 GetSecret、读取旧 key、复制 key 或发起国内 Provider 请求。真实国内账户权限、余额与语音效果仍未验证。

## Verification

- RED：新 policy.origin 测试在未实现时失败；接通 adapter 后国内 batch 仍被 `audio.py::build_voice_generation_preview()` 的原 origin guard 拒绝。只将该 MiniMax-specific guard 扩展到国内站后 GREEN。
- `python -m pytest -p no:cacheprovider tests/test_production_minimax_speech.py tests/test_production_minimax_speech_batch.py -q`：53 passed；1 个既有 enum serializer warning。包括真实 CLI/committer/reader/candidate 路径，只有外部 transport 和 secret-tool process 用测试替身；不冒充 live。
- audio、paid_provider/state/e2e、ElevenLabs、voice captions e2e、voice candidate：202 passed。
- MiniMax Hailuo、provider-neutral adapters、Vidu、runtime-skill boundary：194 passed。
- `ruff check` 所有本轮代码/测试通过；`python -m ruff` 不可用后使用已安装 ruff executable，没有安装依赖。
- Documentation contract gate 与 `git diff --check` 通过；Architecture Gate `--base-ref HEAD` 为 PASS，保留此前 audio.py +25 LOC 和其他任务 image_import.py +18 LOC 的两项 WARN。本轮国内切换没有增加 audio.py 行数。
- native reviewer_xhigh：accept，无 blocking issues。主线程复核 strict reopen：旧 `runs/minimax-speech-zh-test-20260911-01` 的 batch JSON exact，region 缺省，Manifest SHA 仍为 `532db122627ffb58227485632743deb485070c4c5c027c33c6c0a6794e705dbb`，voice 仍 `OUTCOME_UNKNOWN`。
- Harness inspection 将未映射 batch helper/script 路由到 full tests；policy audit 仍报告已有 image_import_video_frame.py、paid_provider_no_effect_reconciliation.py 及对应 test 未映射。未改其他任务拥有的 policy/matrix。用户禁止 worktree/commit，未生成 exact-snapshot passing receipt，不把 working-tree tests 等同 Harness closure。

## Remaining Boundaries

国内接入代码和离线回归已验证，live 因国内凭证未配置而未执行；没有新增 WAV。国内 key 必须通过本机安全输入保存，不在聊天传递。旧 unknown 的具体 Provider 错误在此前代码中未保留，本轮不声称找回原因，也不以切站或新 root 自动重试。音质、口型与 S03 正式配音仍未验收。

使用 retrieve-ai-video-memory、focused test-driven-development、record-ai-video-session 与 distill-ai-video-learning；历史检索带 stale 标记，只作 advisory。Learning evaluation 为 `no_candidate`，没有可推广的独立真实实验。原 staged/其他 dirty changes 保留。
