---
record_kind: media_experiment
topic_id: shizhen-suno-live-pilot
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Shizhen Suno Live Pilot — Authentication Stop

## Authorization And Outcome

用户授权《失帧》EP01 有限真实测试，最多三次音乐生成，不购买积分；随后明确说
“预算不要设gate,告诉我到时候消耗多少就可以”。Parent 在本实验取消金额/积分 gate，
仅保留原请求次数、exact identity、one-use、账号/平台及 unknown 边界，不修改全局 Budget Guard。

实际只尝试一次 `generate`。2026-10-25T20:24:29Z（香港26日）得到 CLI exit 2 / `auth_expired`，
没有 clip ID。CLI jobs 后续只读查询：transaction `68ae0257-5b71-5871-8c49-10d03fc658f7`、
`state=rejected`、`ids=[]`；项目 ledger 保守保留 `submission_unknown`，不改写或删除历史。
任务 STOP 在后续消费及 CLI 调用之前阻断全部新请求。没有重试、换 UUID、自动登录/刷新、
验证码求解、token 注入、代理切换、积分购买或第2次真实生成。

账号 readback 前后均 Pro、v6 can_use=true、total_credits_left=2500、monthly_usage=0。
观察到积分变化0，独立账单 settlement 未取得；不把读取成功当生成权限有效，不以 auth error
本身证明 Provider 没有任何副作用。账户余额不是 gate，本次没有因费用估计阻断调用。

## Existing Media And Creative Choice

完整原剧本有六场，首镜实际视频五个版本；后续异常/妹妹/身份反转只有剧本分镜。
当前原片：`outputs/shizhen-episode01/失帧-第一集-S01-1080p高清版-Seedance2.5-16秒.mp4`，
SHA-256 `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，
51,142,682 bytes、1920×1080、16.065秒，H.264/AAC。原片已按相同 bytes 放入交付包，未转码。
同一首镜的字幕导出/原声不能冒充后续剧情素材。

Project-local `video_analyze` 关闭 ASR/remote audio，9帧采样；Parent 实际检查了0/4/8/12/14秒，
只证明可见构图和动作片段，不宣称完整动态观看。自动scene只报1，不能覆盖可见切镜；
nominal r_frame_rate60不证明恒定60fps，avg_frame_rate=23100/961。
完整native音轨解码到48k stereo PCM16（16.068229秒）；4秒探针经 filesystem MCP 实际省略为
`audio content omitted because you do not support audio input`。没有当前模型的听音证据。
未重试历史原声分析UNKNOWN，未新增识音模型或付费audio_understand调用。

导演选择：首镜不新增音乐，先让小程成为普通人；消失瞬间靠声音缺失而非惊吓重击；监控/修复台
设计同一录音中的稀疏动机；妹妹台词先让对白/呼吸成立，旧照片才考虑情绪主题；结尾音乐退出。
第2条只做offline准备，第3次保留给有实际偏差证据的修订。无后续视频和新音乐，所有配乐质量/
音画适配/主题旋律保持/最终听感仍NOT_EVALUATED。
具体设计和五层评估见[spotting report](../superpowers/artifacts/drama/shizhen-episode-01/music-pilot-20261026/spotting-and-evaluation.md)。

## Concrete Repair And Independent Review

执行前核对 pinned CLI `generation.rs` 的 `output::json::success(&clips)`，发现项目适配器只识别
对象data。新增 Clip[] 成功解析，保留旧对象、空/坏数组 fail-closed；先红1失败/3通过，再绿。
补充 auth_expired 缺少no-submit proof时保持UNKNOWN、双次调用不重提。当前音乐专项25 PASS。
该成功信封修复不是 live success，因为真实调用停在认证错误。

Native `reviewer_high` `/root/music_pilot_review` 只读完成三轮，不 nested delegation。
R1 MUSIC-PILOT-001：task-local summary先落盘再凭据检测，Parent CONFIRMED；
复用 `_envelope` 改为先检测整个响应后持久化白名单字段。Fake title/error-code 两例均不落敏感值，
保留UNKNOWN、两次submit仅一次fake call。R2无findings。实际失败后加入持久STOP，R3 targeted
无findings：STOP fake测试0调用/0消费。没有以 reviewer 意见代签音乐质量。

最终 runner SHA-256 `0f0840c2f6dafb632c425a09b4124c5dfc9f31ce40c2f748d9b261dfff777609`；
`suno_music.py` `def2c12bc94532b558829c73ee5a84a763571034f0b1a2db640f5b2b878e95bd`；
`test_suno_music.py` `73f7732598be39aca2bdece636669ce483e48229ab9c19bb24110c24c544a140`。
R1/R2旧候选与所有 findings/history 保留在本地 `execution-review.json`，没有重置轮次。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| suno-generate-01 | suno:68ae0257-5b71-5871-8c49-10d03fc658f7 | shizhen-suno-live-20261026 | request-01 | N/A | NO_ARTIFACT:AUTH_EXPIRED | execution | FAIL | auth_expired | NEW_ATTEMPT | NONE | outputs/shizhen-episode01/suno-v6-music-pilot-20261026/request-01/transport-summary.json |
| suno-recovery-01 | suno:68ae0257-5b71-5871-8c49-10d03fc658f7 | shizhen-suno-live-20261026 | request-01 | N/A | NO_ARTIFACT:AUTH_EXPIRED | technical | NOT_EVALUATED | submission_unknown_retained | SAME_EVIDENCE_NEW_PROOF_LAYER | suno-generate-01 | outputs/shizhen-episode01/suno-v6-music-pilot-20261026/recovery-observation.json |

## Verification And Delivery

工程源码仅修改Suno响应解析及其回归；没有Provider、依赖、renderer、预算政策或凭据变更。
25项音乐专项通过。真实执行前已完成相称局部验证；精确候选的 Harness 关联回执独立归
`.agent/harness/runs/shizhen-suno-live-response-related/receipt.json`，以其实际level/verdict为准；
不把上轮1552项历史PASS当本轮源码或脏工作区整体通过。

交付页：`outputs/shizhen-episode01/suno-v6-music-pilot-20261026/index.html`；
包：`outputs/shizhen-episode01/失帧-EP01-Suno验证包-认证受阻-20261026.zip`，53,895,379 bytes，
SHA-256 `f1d8e5e9dfd51f722dc54e5265c1272941fe9c1b7d2ce5ccebdbbcaaa5972cae`。
包含原片精确副本、原声、Prompt/config、offline结果、真实错误与recovery、STOP、审查/runner验证和SHA清单。
ZIP CRC、HTML本地链接与manifest hashes核对；文本扫描不含credential-like值。没有Suno音乐文件，
没有新配乐成片、音乐资产登记、Registry/Manifest/active pointers、P6或公开发布。

自动 `distill-ai-video-learning`：no_candidate。单次认证失败、无音乐结果，没有独立音乐质量对照，
不提炼为模型质量结论或推广为生产规则。此次使用的RAG结果部分stale，重要状态均重开当前文件/运行证据。
会话外global memory未修改。其他任务dirty/staged内容不stage、不rollback、不纳入本次提交。

## Minimum Recovery Conditions

已有账号通过正常支持流程恢复生成认证，先核对确切transaction的rejected/UNKNOWN并经原recovery
owner处置；不能删账本、改历史为未提交、伪装成功或绕过STOP。当前请求已停止，不自动恢复授权。
若从正常官方界面取得原始音乐及可追踪clip信息，可先继续本地文件有效性和人工审听，但那不证明
当前CLI自动生成路径已修复。本轮未证明专业影视配乐质量或生产使用条件。
