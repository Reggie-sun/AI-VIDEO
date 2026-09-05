---
record_kind: media_experiment
topic_id: jieshi-s01-vidu-first-frame
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi S01 Vidu I2V Live Gate

Date: 2026-09-06

## Scope And Result

用户“修复然后执行”，限定既有《界蚀》第一集S01首帧I2V。`80b5ffe` 完成有界修复，
首次真实首图输入、一次Vidu生成、canonical fetch及project-local video-analysis全部执行。
**媒体Gate FAIL，未激活、未提交S02；全集未完成。**

运行根目录：`runs/jieshi-e01-i2v-20260906-attempt01/`。
最新封装在 `preparation-v7/`，前序v3–v6保留离线诊断，不是新增Provider调用。
本记录取代[readiness blocker记录](2026-09-06-jieshi-s01-first-frame-readiness-block.md)的当前阻塞结论。

## Canonical Input And Fix

已登记PNG `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`
通过 `prepare_project_registry_commit` → `ProductionStateCommitter.commit` 绑定到S01 r3的
`first_frame` IMAGE位，保留pending `final_visual` VIDEO，Registry原记录不变，strict loader重开。
没有重复导入、直接写YAML、假造前镜terminal、human attestation或商业审批。

`validation.py` 允许恰当的输入/输出组合；`_asset_readiness.py` 校验exact Shot身份和绑定；
`video_planner.py` 只对非商业 `/3`、无前镜、`AUTO + FIRST_FRAME` 派生I2V。
独立review发现旧R2V的final_visual读取回归后，已用共享精确predicate修复，并补回归；
`reviewer_xhigh` scoped re-review accept。人物T2V guard、R2V、连续镜头和writer契约保留。

旧准备包未批准remote，v3 Router正确BLOCKED；依据用户本次请求新封装授权。
旧 `quality_need.minimum_raster` 是compiler未支持字段，v4 compilation正确拒绝；
最终1080p由既有 `output_requirement.resolution_label` 明确封装并下载后实测，
未放宽compiler，未声称内部原生生成分辨率已证明。v5/v6本地封装类型错误无外部提交。

## Paid Execution And Download

Exact request `7db8e13b87b2cea7fe5f961ee8aeb633c98f2d4f68c922c3635018c77bd552cc`。
Vidu `viduq3-pro-i2v-v1`、4秒、1080p、24fps、adaptive geometry、当时无原生声音。
Profile `0874e2ddd61044561b49d3cb74ef9598f83aa9b2a44bf019cf30184aad00c1b4`
使用已有未过期operator upper bound；`authenticated_task`，未查询或写死历史CDN允许列表。
新task submit ceiling=1，新的preview/authorization/reservation/intent/permit；旧85元授权未复用。

`live_i2v.py` 通过 `VideoGenerationService.start/submit_once` 提交。
唯一generation POST HTTP200，payload哈希
`f5888476c2e603f9ba37fef7821339ac20a66ec14c6db710d563b6a9c08a6350`；
出站base64解码核验2,064,319字节PNG/hash，证明真实图片进入请求。
状态queued→running→succeeded。没有额外variant或重试submit，没有根据推算账单settle reservation。

首次fetch失败：URL本身是合法HTTPS，但本机DNS将
`prod-ss-vidu.s3.oss-cn-beijing.aliyuncs.com` 返回为 `198.18.1.227`，触发公网IP guard。
`fetch_i2v.py` 只对这个hostname使用HTTPS公共DNS，得到公共IPv4，并仅在本进程替换该
hostname的getaddrinfo；canonical `_resolve` 公网检查、数值IP固定连接、原hostname TLS/SNI、
禁止redirect和credential-free media GET均保留。独立 `reviewer_xhigh` accept后恢复同一FETCH。
未改全局DNS、未改Provider代码、未开第二次submit、未改变sealed result trust。

## Exact Media Gate

MP4 SHA-256 `b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a`，
3,724,674 bytes。canonical路径：
`production-s01-v1/state/video-generation/fetch/files/b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a.mp4`。

落盘后立即调用project-local `video-analysis.video_analyze`，随后
`video_extract_frames`放大复核；逐项判定见 `preparation-v7/shot-01-gate.md`。
实测1080×1920、24fps、97frames、4.042s、无音轨、一场景。
林砚从膝部连续抬解剖左手，右手保留手机，证明是实际生成动作。
0.898/1.0s玻璃出现对应手影，0.449/0.5s有多余白数字，机位拉远/构图变化：required FAIL。
两厘米终点、完整身份/工牌及最终广播字幕尚未证实：NOT_EVALUATED。
ProduceID含720p而container为1080p，内部生成分辨率未知；不推断为已证实放大或原生1080p。
无human full-speed verdict，无Production QA/Final Acceptance。

## User Audio Policy Update

用户询问原生音频价格并明确要求改掉统一后期声音的解释。此次显式价格问题才查询
同参数audio开/关报价，两个HTTP200均96积分；没有刷新执行profile、没有新增生成。
官方Q2音频加价条款不适用于Q3；报价相同不伪造actual settlement。

[episode-01.md](../superpowers/artifacts/drama/jieshi-episode-01/episode-01.md#audio-production-policy)
已记录本集后续新请求默认原生声音优先：支持时 `AudioNeed.REQUIRED` / `native_audio=True`，
环境、拟音及已有台词进入生成，逐字/时序/声线/适用口型经过Gate，后期仅必要替换与统一混音。
字幕和最终音频仍走canonical timeline，不把原始音轨存在等同最终自动保留。
已消费的无声请求不改写；后续新请求必须重新绑定策略和授权。

## Verification And Publication

- 修复前7个focused failures复现；修复后四组focused287 PASS。
- `80b5ffe` exact `git archive` 临时目录中相关suite去重合并 **1151 PASS**，docs contract PASS。
  未创建git worktree；没有在archive中混入其他会话dirty changes。
- 共享工作目录policy audit PASS；Architecture Gate PASS，含planner effective LOC 782→801的WARN，
  未通过架构扩张消除警告。共享目录其他session的retrieval WARN不归本任务。
- 标准Harness verify需要detached worktree，用户禁止worktree，因此没有fresh Harness receipt；
  archive测试和独立review不冒充Harness。archive不含Git metadata，policy audit在archive不可运行。
- task code/script已commit，无push。旧7个staged runs diff SHA-256仍为
  `5e6c24dd5a82a3e9f66a79781d234e63491b97293e28716ddbda3f7db611a639`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-vidu-media | vidu:7db8e13b87b2cea7fe5f961ee8aeb633c98f2d4f68c922c3635018c77bd552cc | jieshi-s01-initial-i2v | jieshi-e01-s01-vidu-i2v-attempt01 | N/A | b4b4def02532232b3c910999af483604bd677ed0bd9606a2b378951b81e27f8a | AGENT_POST_MEDIA_GATE | FAIL | REFLECTION_TEXT_CAMERA | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt01/preparation-v7/shot-01-gate.md |

## Learning And Next Action

按 `record-ai-video-session` 达到有界生成与真实Gate阻塞的stable checkpoint，自动执行
`distill-ai-video-learning` evaluation：**no_candidate**。本次只有一个I2V媒体attempt；
submit/download/两次抽帧属于同一证据链，不是独立支持。历史T2V和本次模型、输入模式、
prompt均不同，不据此推出跨模型优劣或普遍修复结论。

Next One Thing：准备S01新repair请求，保留真实first-frame I2V并使用新原生声音策略，
聚焦消除对应手影、多余文字和机位变化。当前一次submit已消费；不得blind retry、复用
permit或越过失败Gate进入S02。仅代码/接入完成，整集和S01视觉/音频成片均未完成。
