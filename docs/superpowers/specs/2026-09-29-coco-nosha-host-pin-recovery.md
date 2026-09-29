# COCO / Nosha Host Pin Recovery

## Goal And Authority

`SCOPE AUTHORIZED / SELF-REVIEWED`。依用户的任务内默认授权继续原17 s、一镜到底、正常速度、完整因果链和原声线。仅关闭当前Comfy支持的host pinned-memory缓存，保留GPU计算和已经验证的同步offload / MLP / LoRA / Triton；增加第六份exact local repair及最多一次新physical submit。无新的用户批准步骤、worktree或paid media fallback。

## Execution Result — 2026-09-29

本spec的第六grant已由`df90028`实现、验证和独立review；actual attempt08沿canonical seam在00:11:24后生成并fetch17.000 s/408帧/24 fps/1344×768 MP4，SHA `ee9a20d880bb82bbeb0bdd019c78f9f5a5c8f3f477e988363a708eec0b99752f`。Host pin关闭后的这一完整attempt未发生host OOM；不同seed的后续单次quality resample却在rms_rope eager fallback发生GPU OOM，不能推出稳定可重复能力或pin是全部failure的唯一cause。

MP4实际MCP/帧/ASR检查确认形态/果实偏差、约9.25 s切镜、重复且错时对白；canonical mixed quality/evidence rejection已关闭，原声线、完整观看/聆听仍NOT_EVALUATED，没有activation或Final Acceptance。当前Manifest59、8次physical submits、6 consumed grants、1个保留MP4，正常GPU服务已恢复。完整evidence与review/direct-policy/Harness边界见[当前记录](../../record_for_agent/2026-09-28-reference-capabilities-and-local-canvas-method.md#current-continuation--actual-17-second-gpu-video-quality-rejected-and-resample-oom)。以下诊断/计数是本spec实施前的历史依据；accepted scope与质量要求没有降低。

## Historical Pre-Execution Evidence And Diagnosis

实现`543f22c`、10项fresh exact-staged direct policy checks与受管Kimi第二轮`ae185bcf-435a-4579-9285-c1d82bfadc73`的完整report已由Parent核验。`runs/coco-nosha-sync-offload-20260929-001/`实际attempt07/prompt `8e0e92e6-3665-4895-990c-7ee873201c9b`于2026-09-29 20:41 +08:00完成4/4 GPU sampling，之后进入VAE decode时worker PID611184被kernel global OOM杀掉。Kernel记载anon-rss60143584 kB，systemd journal的4/4与termination绑定同InvocationID；进程和endpoint消失，exact output-prefix为空。由existing canonical `record_video_provider_failure`和`record_attempt_evaluation`显式记录known runtime failure，没有伪造Comfy history/observation或重置permit。当前Manifest45、6个actual submitted FAILED、5份consumed grants、fetch0/MP4=0；prepared-only03不计submit。原默认GPU服务已恢复健康、队列空，Jianji/未知任务保留。

Pinned Comfy源码的H3 VAE已内置空间/时间分块和CPU output-buffer streaming；`decode_tiled`只是regular decode alias，不声称开启tiling可修复这次RAM OOM。Dynamic model加载为weights/patches创建host buffers，ops首次搬运可以复制并注册host pins。`--disable-pinned-memory`保持`MAX_PINNED_MEMORY`为非正sentinel（当前-1）、host-buffer capacity为0，并在原生pin函数提前返回；同步GPU传输继续使用原权重。候选假设是避免额外驻留host副本、允许file-backed页回收，给VAE decode留RAM。此路径有source evidence，完整模型RAM峰值能否降低仍需一次真实取证；不改变OOM score或牺牲未知任务。

## Contract And Compatibility

`LocalRuntimeRepairExtension.ceiling`从`Literal[3,4,5]`增加6，default3与默认cap2保持。Sole committer仍要求typed revalidation、`granted == ceiling - 1`、prior grants全部consumed、same actor/task/Shot/local-unmetered、latest known FAILED及exact binding/evidence/revision，并在submit intent的同一atomic write consume。旧`/1`和`/2`ceiling3/4/5序列化/hash/read/replay保持；新6在旧runtime fail closed，7及copied-model tamper仍拒绝。没有新Manifest writer、恢复owner或激活权限。

## Runtime And Finite Execution

新unit目录`runs/coco-nosha-host-pin-recovery-20260929-001/`，不修改installed Comfy、模型、原sealed profile/workflow或旧run evidence。两个隔离进程在≤120 s核对当前native pin dispatch、host capacity及真实CUDA输出，保持同期`--disable-async-offload`；仅关闭pin为新变量。验证只证明配置/局部transfer，不冒充full-model/RAM或媒体证明。

验证和适用review完成后封存R10 budget/hash predecessor、actual used6→batch ceiling7、local total=None、paid0、new physical ceiling1、window7200 s/active5400 s。原服务必须exact PID/InvocationID且队列空才切换。Canonical generation seam准备fresh attempt08、local intent和one-use permit；canonical fresh seed变化明确记录，不能称same-seed媒体A/B。GPU/RAM/RSS telemetry只观察本prompt；如果MemAvailable低于4 GiB且该prompt仍是当前running job，最多一次exact-job cancellation防止重演host OOM，等待known terminal；unknown仍停止补证。Known failure或unknown结束本unit，不重复submit。

正常terminal/empty owned queue后复用原supervisor恢复正常GPU服务；如果worker被杀掉，则先以exact journal/kernel/PID/output证据和canonical owner封存known terminal，再在supervisor证明无service/无endpoint后恢复，不杀未知unit、不删除完整orphan。保留三图/voice exact bytes、prompt/model/LoRA/profile、1344×768@24fps、408 output/413 sampler frames，只trim尾部grid padding。MP4落盘后显式video-analysis、完整观看/聆听和逐项Gate；无法聆听必须NOT_EVALUATED。

## Verification And Self Review

Public orchestrator/service/committer tests新增6的登记/replay/history/one-use/耗尽、unknown、premature、identity/revision拒绝和旧5 bytes兼容。按真实changed paths完成fresh exact-staged policy；用户禁止worktree，所以direct checks与canonical Harness receipt明确区分。Stable candidate的共享授权/host恢复/runtime校验缺口按T2由一次受管read-only Kimi review独立检查，Parent核验route/snapshot/artifact及裁决；连续两次运行故障按SUBAGENTS native fallback，不追加同类故障调用。

本方案直接针对kernel证实的RAM failure，不把failure后显存余量当运行峰值。原VAE算法已经分块，无需引入新的视觉算法。Pin关闭影响搬运性能，无法保证完整媒体；一次finite真实执行给出结果，全部historical counts和质量要求保留，无push/release。
