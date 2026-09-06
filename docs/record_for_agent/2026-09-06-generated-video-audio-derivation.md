---
record_kind: architecture_implementation
topic_id: generated-video-native-audio-derivation
learning_eligibility: ineligible
---

# Generated Video Audio Derivation

Date: 2026-09-06

## Scope And Current Truth

用户明确批准有界原生音轨派生入口，目标是后续组合《界蚀》S01的attempt07视觉与attempt08广播。本轮完成能力实现，不重新编剧、不增加Provider调用、不改变源视频Gate结论。

`ProductionStateCommitter.register_generated_video_audio()`消费已结算、successful fetch、尚处于`VALIDATE`的remote/metered源，通过seekable临时WAV与既有probe生成独立P4语音素材。目标只支持Manifest2.0–2.2、Registry2.1，语音种类只支持dialogue/narration；更高版本在提取前拒绝。完整契约见[generated-video-audio.md](../generated-video-audio.md)。

登记复用`audio_import`事务；没有新Manifest字段、第二writer、第二timeline或direct mux。独立reader验证source submission/task、settlement budget、probe、工具、metadata、base project及Registry历史关联；TTS与派生claims独立且不得重叠。相同attempt由target内POSIX锁串行化，exact replay校验本次语义参数且不重复提取或Manifest写入。

## Review And Verification

首次独立review拒绝了参数漂移、source/probe闭包、历史snapshot关联、单进程锁、晚版本拒绝及异常路径缺失import。逐项修复并补充重新封存后的语义篡改测试；同一native `reviewer_xhigh`最终`accept`。没有用早期passing tests代替这些修复。

- 新功能及committer结构测试：30 passed，含真实本地临时MP4→PCM WAV→登记→strict reopen。
- 相关project/state-commit/generated-video-e2e组合：417 passed。
- Harness、CLI、runtime Skill边界组合：223 passed。
- Documentation contract、policy audit与task architecture delta：PASS；policy无unmapped/unverified paths。
- 完整Production suite：`python -m pytest -p no:cacheprovider tests -k 'production or video_candidate or video_generation' -q`，3147 passed、3 skipped、1353 deselected，736.61秒。最终focused+structure由parent另行复跑30 passed（9.30秒）。

用户明确禁止worktree，因此未执行会创建detached worktree的Harness verify，也没有签发fresh isolated Harness receipt。以上是已知working-tree上的实际验证，不冒称隔离receipt。保留七个原有staged runs文件；不push。

## Live Blocker And Next Action

attempt07 MP4：`88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e`，3,350,152 bytes。

attempt08 MP4：`cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e`，3,232,566 bytes。

两源paid state均为`ACCEPTED`、reservation仍`reserved`、`actual_cost_microunits=null`。已检查的fetch evidence无实际扣费字段。原生音轨入口与既有video candidate登记均要求真实settlement；不能把operator upper bound当实际费用，也不能伪造结算。已向用户请求各任务实际人民币扣费及账单依据，尚未收到。

本轮未对07/08提取、登记、activation或合成；没有新S01成片或逐镜PASS。只读mapping还确认：`validate_once()`只登记原request的inactive candidate，并不提供另一repair composition的通用视觉输入登记。音轨能力不能替代这一缺口。取得真实结算证据后，先沿既有committer完成合法结算，再处理视觉repair输入登记与原生音轨登记，构建新composition并调用project-local video-analysis。不得激活失败源或推进S02。

## Record And Learning

`record-ai-video-session`用于保存实现checkpoint及真实live blocker，并对旧记录添加有界supersession。`distill-ai-video-learning`评估为`no_candidate`：这是一次实现与回归验证，不构成独立媒体实验或跨实验质量结论；不创建占位claim、不修改Skill/Gate、不刷新RAG索引。
