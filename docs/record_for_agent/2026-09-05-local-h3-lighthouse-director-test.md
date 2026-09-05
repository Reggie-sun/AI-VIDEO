---
record_kind: media_experiment
topic_id: local-h3-lighthouse-director
learning_eligibility: eligible
evidence_index_version: "1"
---

# Local H3 Lighthouse Director Test

Date: 2026-09-05

## Purpose And Scope

用户先要求“换个场景再试一下”，随后指定“再试一下本地的h3”。本轮未继续 Mini，
原创场景改为雨夜灯塔：黄色雨衣守塔人转动黄铜手轮，齿轮启动、灯亮，光束扫过雨窗。
它与先前温室 Seedance 实片不是同题材、等时长或同 prompt 的 Provider comparison。

使用 `retrieve-ai-video-memory -> open-video -> approved Character/Scene/Shot -> h3-video`。
Director 根据同空间机械启动的因果链选择 `single_take`，两个内部 coverage units 连续衔接；
不因短时长或无 prompt 强制选择简单镜头。Raw kind=`direction`，两个用户约束均有 verbatim
inventory/binding，schema-v3 validator 两次均 PASS。初步构思中的环绕未进入最终请求；
最终唯一主运镜为 `crane_up/up/moderate amplitude/moderate speed/stationary-to-settled`。

## Canonical Runtime

- Selected provider `ComfyUIT8VideoProvider`，capability `minimax-h3-t8-t2va-quality-v1`；
  `workflows/profiles/minimax_h3_t8_t2va_quality.json`。
  Exact profile hash：`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`。
- 固定 T2VA、1344×768、124 frames、24fps、native audio、20steps、res_multistep/simple、CRF17。
  未用 Turbo 或 LoRA；exact MP4 embedded workflow 的节点与 sampler 设置已复核并保存精简 summary。
- 正式 `VideoPlanner -> require_current_video_plan -> pre-generation graph -> Router -> H3 compiler /3`
  保持 lineage。完整 typed camera 自动产生 requirement `/4`，并不需要参考图；没有把运镜偷塞
  locked-camera 字段，也没有编译后替换 prompt。`runtime_skill_calls=0`。
- 上游独立 PROMPT_GRAMMAR.md 未随安装提供，采用已读取的 Skill 三字段说明与当前正式 compiler。
  v4 compiler 的现有序列化格式保持原样；本轮没有产品实现或 Skill 修改。
- 实际 ComfyUI/T8/VHS commits 分别为 `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、
  `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`、`4ee72c065db22c9d96c2427954dc69e7b908444b`。
  T8 pyproject version=`1.36.2`，launch argv 含 `--use-sage-attention`，完整 preflight 验证
  四个模型 exact bytes、workflow/binding、节点 schema 与当前 runtime，未以 advisory 文档代替实查。
- 只用 `http://127.0.0.1:8188`，没有 cloud、paid call、credential、下载、安装或 runtime 更新。
  本轮以 supervisor 启动独立服务 `ai-video-comfyui-7f5d9a299fd64428b86461bccd7128cf.service`；
  最后确认 queue empty 后停止，status inactive、8188 无 listener。

## Attempts And Bounded Repair

Run roots：`runs/director-h3-lighthouse-20260905-001/` 与 `runs/director-h3-lighthouse-20260905-002/`。
各有 director coverage、authoring、typed intent、planning/projection/routing/compilation/resolved、
runtime/preflight preview、canonical submission/fetch receipts 与逐项 media gate。

| Fact | Initial 001 | Repair 002 |
| --- | --- | --- |
| Attempt | lighthouse-h3-video-001 | lighthouse-h3-video-002 |
| Resolved hash | 0a01ed6a16fc46f2bcf9cdaeca0f9381fee6e8edc9940627cc0dd97f5eb43123 | 1adb21ee3aeb06134086a67ef496abcf68b201196686852ca65380b981670d21 |
| Exact MP4 SHA-256 | c1cd4263f9c1c4a5f1e25bf1938b8a5fb9e66750b3e42d82359df213cabdf657 | 2cc1188fda2a0471e8677a8100a42ccc2d50b3d1174acdd5ded26a013e42528e |
| Bytes | 3,871,937 | 3,177,364 |
| Effective seed | 9031062904533376117 | 5137329031542248876 |
| Submit UTC | 08:29:53 | 08:41:16 |
| Observed succeeded UTC | 08:35:12 | 08:46:21 |
| ComfyUI measured execution | 318.47s | 303.87s |

MP4 均位于各自 `production/state/video-generation/fetch/files/<SHA-256>.mp4`，fetch receipt 和
现场 SHA-256 相符。每个 attempt 各一次 `VideoGenerationService.submit_local_once`，均经
唯一 committer 的 durable intent / one-use permit；无直接 transport submit、blind retry 或 activation。
native reviewer 对初次预提交 accept；发现并修正了 task-local fetch wrapper 对 dataclass 的错误
序列化，未涉及产品代码或媒体重做。第二次 scoped review 为 accept with concerns。

001 的灯起初背对镜头，后来转出亮着的灯面，不能证明由灭到亮。已保存 `NOT_EVALUATED` Gate，
再进入事先封存的 local bounded repair：唯一创作变量为“从开场就能看到未亮的前方灯面”。
002 保持原始亮灯要求、人物、动作、camera、输出与 recipe，source Gate hash 明确绑定。
但 canonical 未指定 seed 会从新 request 派生不同 effective seed，因此不是固定 seed 对照，
不能把效果差异全部归因于 prompt 的可见性修正。

初次之前已封存 max2 attempts、task3600s / GPU2400s。第二次提交前后重新检查原始 elapsed
预算，没有借新 run 重置额度。两次合计生成 622.34s；第二次后达到 attempt 上限，停止追加。

## Requirement-Level Results

两条 project-local `video-analysis` MCP probe 都测得 H264 High、5.167s、124frames、1344×768、
24fps、AAC32000Hz stereo。Agent 检查各11张0.5s间隔帧，并对002后段补充0.25s密集帧。
002完整 video/audio decode 实际 PASS。001/002音频 mean分别 -22.2/-28.4dBFS，peak -7.3/-14.6dBFS。

| Requirement | Initial 001 | Repair 002 | Evidence Boundary |
| --- | --- | --- | --- |
| Technical output | PASS | PASS | exact bytes、尺寸、帧数、fps、音轨与预检目标相符 |
| Keeper/room identity | PASS | PASS | 抽样保留雨衣、黑手套、手轮、灯与窗格；不承诺逐帧 anatomy |
| Handwheel action | PASS | PASS | 手转轮与齿轮运动可读 |
| Continuous crane-up | PASS | PASS | 从手轮近景连续上升至守塔人/灯中景；非简单静态首帧 |
| Lamp off-to-on | NOT_EVALUATED | PASS | 001灯面先被灯背挡住；002在0–1s可见未亮灯面，1.5s开始发暖光，2s后点亮 |
| Light sweep on wet windows | PASS | FAIL | 001可见移动暖色反射；002后段雨窗基本持续蓝色，缺少可读的大幅移动光束 |
| Exclusions | PASS | PASS | 抽样未发现额外人物或文字 |
| Audio intent/synchronization | NOT_EVALUATED | NOT_EVALUATED | 无法听验；非静音和ASR estimated speech=0不能证明音效贴合 |

整体 Gate：001 `NOT_EVALUATED`，002 `FAIL`。002解决亮灯可见性，但不代表整体质量胜出。
未推进下一 Shot，未自动激活、签发 P6、Final Acceptance 或质量全项通过。
002 canonical Manifest revision9、video phase=`validate`。本次交付是供用户观看的原始测试样片。
MCP scene_count=1 与单take相符；issues=[]不是语义验收。Raw MP4保留workflow/prompt metadata，
record不复制完整prompt/graph，sanitized probe sidecar已去掉该metadata字段。

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。初次 RAG 返回 stale-tagged advisory，已重开 native prompt
历史记录并以当前 compiler/runtime复核；因发现状态可见性问题又做了focused experience检索，
返回fresh fragments并重开M6/V13因果动作记录。这些旧案例涉及不同conditioning、prompt/compiler、
动作与场景，不借其PASS覆盖本次，亦不把当前T2V案例写成旧I2V结论的supersession。
没有同范围existing Learning Claim。两次本地样本的目标可见性结果不一致且seed变化，只有一个
修正后成功的off-to-on案例；不提出“文字修正必然有效”或H3/Seedance整体质量排序/adoption。

## Verification And Publication

两个 schema3 Director validator、正式编译/lineage、完整provider preflight、两次local submit/poll/fetch、
上述MCP媒体检查已执行。记录执行 evidence identity、docs contract、whitespace及documentation类别
exact-staged Harness mandatory checks；不为记录额外生成媒体、调用Provider或运行完整suite。
本次仅提交这一份记录；运行脚本/sidecars/MP4保留local ignored artifacts。未修改产品source、
未触碰unrelated staged/dirty工作，未push/release；没有手工刷新独立RAG index。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| h3-initial-technical | h3:0a01ed6a16fc46f2bcf9cdaeca0f9381fee6e8edc9940627cc0dd97f5eb43123 | lighthouse-h3-20260905 | lighthouse-h3-video-001 | N/A | c1cd4263f9c1c4a5f1e25bf1938b8a5fb9e66750b3e42d82359df213cabdf657 | PROVIDER_TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-20260905-001/fetched.json |
| h3-initial-media | h3:0a01ed6a16fc46f2bcf9cdaeca0f9381fee6e8edc9940627cc0dd97f5eb43123 | lighthouse-h3-20260905 | lighthouse-h3-video-001 | N/A | c1cd4263f9c1c4a5f1e25bf1938b8a5fb9e66750b3e42d82359df213cabdf657 | AGENT_VISUAL | NOT_EVALUATED | LAMP_OCCLUSION_AND_AUDIO_UNVERIFIED | SAME_EVIDENCE_NEW_PROOF_LAYER | h3-initial-technical | runs/director-h3-lighthouse-20260905-001/media-gate.json |
| h3-repair-technical | h3:1adb21ee3aeb06134086a67ef496abcf68b201196686852ca65380b981670d21 | lighthouse-h3-20260905 | lighthouse-h3-video-002 | N/A | 2cc1188fda2a0471e8677a8100a42ccc2d50b3d1174acdd5ded26a013e42528e | PROVIDER_TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-20260905-002/fetched.json |
| h3-repair-media | h3:1adb21ee3aeb06134086a67ef496abcf68b201196686852ca65380b981670d21 | lighthouse-h3-20260905 | lighthouse-h3-video-002 | N/A | 2cc1188fda2a0471e8677a8100a42ccc2d50b3d1174acdd5ded26a013e42528e | AGENT_VISUAL | FAIL | WINDOW_BEAM_NOT_READABLE | SAME_EVIDENCE_NEW_PROOF_LAYER | h3-repair-technical | runs/director-h3-lighthouse-20260905-002/media-gate.json |
