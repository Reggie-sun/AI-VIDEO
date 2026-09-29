---
record_kind: session_summary
topic_id: reference-capabilities-and-local-canvas-method
learning_eligibility: ineligible
---

# Creative Goal Tests, Jimeng Canvas Comparison And Local Replication — Full Record

Date: 2026-09-28
Session window: 2026-09-27–2026-09-29, Asia/Hong_Kong
Original checkpoint: `dfb11626d9bab4f6c4c9a19db2ea2c5c5d102d7c`
Continuation implementation checkpoint: `17aca1057783a2fde6c442e9ebceb8acc010cef9`

## Current Continuation — Sixth Physical Submit Completed Sampling, Host OOM During Decode

2026-09-29 20:48 +08:00已完成本次actual failure恢复：`R10 = runs/coco-nosha-sync-offload-20260929-001/`的`coco-nosha-attempt-07` / prompt `8e0e92e6-3665-4895-990c-7ee873201c9b`完成4/4 GPU sampling，但在随后的video VAE decode阶段worker PID611184被kernel global OOM杀掉，MP4仍0。下方第五次失败和restricted-window记录保留历史，不再代表当前阻塞位置。Original refs/voice/model/LoRA/profile/prompt/17 s全部保持，canonical fresh seed1583761486，不声称same-seed媒体A/B。

`543f22c`实现exact第五grant，default cap2/ceiling3保留，10项fresh exact-staged direct policy checks全PASS（tree `ce8b7c1c57bad862b561fe47ce5331c208c508ba`）；用户禁止worktree，所以canonical Harness receipt为None。受管Kimi round1 `95d31f7f-16f9-49f7-818a-de11a85b1591`为response-body CONNECTION_ERROR/OUTCOME_UNKNOWN，8 wire/21 Reads，无完整report；收窄相同source snapshot的packet后round2 `ae185bcf-435a-4579-9285-c1d82bfadc73` PARSED / 304.521 s / 3 wire / 4 Reads，qualified Docker/deep route、response identity、receipt/report/source hashes经Parent核验。Report SHA `2f78a2e3f340ecfb86854576b1a1ee49881423799653279d4cf68024dc947516`无blocking findings；三个evidence questions由Parent检查local receipt必须绑定intent、旧runtime拒绝新5以及read-only telemetry/restore owner后关闭，见R10 `review-adjudication.json`、`review-acceptance.json`。PARSED只作为review证据，不是媒体通过。

新finite unit保留R9 budget/hash、actual used5→batch ceiling6、local total=None、paid0、new submit1、7200/5400 s bounds；第五grant由actual07 consumed，没有改名task或重置历史。`--disable-async-offload`保留CUDA运算，temporary unit `ai-video-comfyui-eb94d306f73a4f9c907e517071dd3a38.service`、InvocationID `9bb82621e77242c5a00b2868c2496a7c`。同Invocation/PID journal记录4/4 sampling、7:06采样时间及VideoVAE开始；GPU telemetry曾约30 GiB/100%，采样完成后约15 GiB。20:41:52 kernel明确记载global_oom杀掉PID611184、anon-rss60143584 kB（约57.4 GiB）；不是新CUDA OOM，也不把systemd的早期MemoryPeak或failure后free RAM当完整峰值。

进程和8188 endpoint消失，Comfy volatile history不再可取；exact output prefix `ai_video_h3_t8_native_3_bbaf736636abe9f6` inventory为空，没有fetch或AV文件。绑定证据在R10 `comfy-host-termination.jsonl`、`kernel-host-termination.log`、`host-termination-evidence.json`（SHA `be7cd0a6ad053aff2927dba3b7755b108879cf33263479ec6ddebc0da18201fa`）。核实own poll controller PID620985/argv后只SIGINT停止其无结果history poll，exit130，不杀未知任务。用existing canonical `record_video_provider_failure`显式记录known worker failure，再`record_attempt_evaluation`；没有合成Comfy history或Provider observation，没有裸写Manifest、remint或重试。

Public loader重开Manifest45、6个actual submitted全FAILED、5份grants全consumed、fetch0/MP4=0，prepared-only03不计submit。Actual07 binding `25ea6c94d581176bdd5481e7cd4e04e48d65858cffe1f3c0d0a90f6ddae47a98`。R10 `terminal-audit.json`保存canonical恢复依据和计数。OOM后的`--collect` unit已消失，旧restore要求active/idle的前置条件不成立；先证明exact worker死亡、supervisor无unit/无endpoint，再复用原serialized supervisor恢复正常Python3.13/Sage GPU服务，未stop任何unknown service。恢复unit `ai-video-comfyui-f03994349044422b97809ba255e283a2.service` / PID793442 / InvocationID `56a4d91f35f14dea892b75da443b7ece`，active/loopback healthy/queue empty，见R10 `service-before-restoration.json`、`restoration-health.json`。Jianji/未知任务保留。

下一候选见[host pin recovery spec](../superpowers/specs/2026-09-29-coco-nosha-host-pin-recovery.md)及[plan](../superpowers/plans/2026-09-29-coco-nosha-host-pin-recovery.md)：pinned H3 VAE已经内置空间/时间分块，`decode_tiled`为regular alias；针对RAM failure验证关闭额外host pinned-memory缓存，保留GPU推理/原算法和17 s。原单次slot已消耗，不能重跑R10 controller；新finite unit仍需runtime proof、canonical ceiling6实现/验证和适用review。Task默认授权覆盖，不再为同类工程调整请求批准。

真实delivery仍未完成。全部media/原声线/完整因果链/完整观看聆听为NOT_EVALUATED；本runtime完成4/4不等于最终成片能力或视觉验收。本模型输入接口无法实际聆听audio，原MP3 listening记录为NOT_EVALUATED（R10 `reference-listening-boundary.json`），不能把ASR当timbre或听觉证明。Automatic learning evaluation为`no_candidate`：这次是单一host OOM incident，局部配置对照不支持完整模型RAM或成片recipe；保留既有claim，无placeholder/adoption。没有仅为record增加测试/network/media，RAG未刷新，unrelated `.codex/config.toml`保留，无push/release。

## Historical Continuation — Fifth Physical Submit Failed At Vbar Prefetch

2026-09-29 19:41 +08:00实际执行已取代下方restricted namespace与cap4 pending状态。本窗口可以访问RTX 5090、user manager和strict-loopback ComfyUI；没有绕过平台权限，没有修改installed Comfy/model或停止Jianji/未知任务。共享实现`b25c2ac`保留默认cap2及旧ceiling3，只新增exact ceiling4与typed revalidation；15项fresh exact-staged direct policy checks全部PASS，staged tree `550f5a46bb6ee682aa52ba27f6e0440ee73bbdf1`。`R9= runs/coco-nosha-mlp-memory-20260929-001/`的`policy-verification.json`保存逐项log/hash；用户禁止worktree，所以没有canonical Harness receipt。

### Equivalent Local Kernel And Independent Review

完整MLP row-only分块最初在真实宽度65569-row LoRA组合出现max absolute error0.0001373291015625，已拒绝并保留历史；保留full-row LoRA down projection后，最终8项GPU对照全PASS。实际hidden5376/FFN14336的plain与LoRA各比较352498944个output elements、max error0、input unchanged，峰值stock→candidate比约0.186/0.181。最终candidate SHA `afdf3e9a2182b653ffa751c2c3858e2430b2cab670cee200db89107d5e4d4858`，原失败token rows未测量，100032-row stock曾OOM，不能把代表case当exact failure shape或完整模型通过。Metadata guard误读属性后的known验证失败及有限修订均保存于R9，无数值标准降级。

受管Kimi第一轮`51a1def5-f2ff-4a43-9603-ee677a39fd75`为TLS_ERROR/CONNECT、6.248 s/1 request/0 Reads，无report；有限无凭据握手证明间歇性TLS，未改变route/CA。第二轮`c360d2e1-da8e-424a-b783-456e009cdcb2`于888.480 s/5 wire requests后得到完整canonical report，20个Read覆盖exact source/spec/plan/packet。Docker image `8f399afdd9208aa6e6b37a6fd15ba3c0afdf1617c60fdc55dc11d3515d8bc720`、deep/k3[1m]/max和runtime/response identity及全部artifacts/source hashes均核验。Review report无blocking finding；Parent核对policy-result hash与policy-YAML hash属于不同文件、确认direct-check限制，另用read-only helper证明ceiling4对remote/metered仍拒绝。`R9/review-adjudication.json`与`review-acceptance.json`记录最终裁决及exact source snapshot，不把PARSED或kernel PASS当media acceptance。

### Actual Fifth Submit And Terminal Recovery

新R9有限unit保存R8 budget/hash为predecessor、actual used4→batch ceiling5、local total=None、paid0、new physical ceiling1、window7200 s/active5400 s。由sole committer登记第四份grant `752e0b808a0c4743ee0930684b2bfc2a16b138b8f5bebe232bc94d0a6efdb9aa`，实际由`coco-nosha-attempt-06`消耗。Frozen三图、COCO voice、prompt/model/LoRA/profile和17 s输出保持，canonical fresh seed1583761485；不声称same-seed A/B。

Owned task-only GPU unit `ai-video-comfyui-9d4ee16763954761a8bc213bfecb2682.service` / PID127208 / InvocationID `365e7c760aeb445ba5020b19606d24ff`加载原Triton、LoRA及MLP overlay。Actual prompt `2822aecf-549a-49b4-840f-3fdc931ed82f`运行41.46 s，于0/4采样阶段报`VRAM grow failed: 646288384 bytes`，stack为`model_prefetch.prefetch_queue_pop -> cast_modules_with_vbar -> get_cast_buffer -> VRAMBuffer.get`。这是新异步预取buffer failure，不能称旧MLP rotation已完成全模型证明，也不能从失败后free VRAM推断失败时峰值。

Public loader与Comfy history核对后，Manifest revision39、5个actual submitted attempts均FAILED、4份grants全consumed、fetch0/MP4=0，prepared-only03仍RUNNING但没有submit意图/receipt，不计物理提交。Actual06 binding `7b314cae21434c1e2d704dd01c2b6142bc08b9bd23fb0432976149252a8e0c19`；`R9/terminal-audit.json`、`attempt-06/observation.json`与`comfy-history.json`保存known outcome，controller exit0只表示已记录失败。新单次slot已消耗，禁止重跑R9 controller或复用grant/permit。

Known terminal/empty queue后经原supervisor恢复默认GPU ComfyUI：unit `ai-video-comfyui-b211c66af9174f28ba5b63c0681eed50.service` / PID207059 / InvocationID `e0555d522af44fbaacb520def14e6ae2`，loopback healthy、队列空，argv为正常Python3.13/Sage、不带临时overlay/Triton flags。`R9/restoration-health.json`保存恢复证明。新诊断是使用pinned Comfy现有`--disable-async-offload`避开预取/异步buffer；两个隔离CUDA进程在4.813 s内证实NUM_STREAMS2→0、queue/stream停用、小MLP16640 output elements bytes hash相同，但未执行dynamic全模型。新spec/plan见[synchronous offload repair](../superpowers/specs/2026-09-29-coco-nosha-synchronous-offload-repair.md)，后续仅一个新有限unit，不盲重试、不降低17 s成片要求。

### Delivery And Learning Boundary

目标仍未完成；COCO / Nosha MP4=0，完整观看/聆听、原声线与完整因果链均NOT_EVALUATED。这里记录工程/恢复与已知media failure，未新运行测试、网络或media仅为记录，未push/release，unrelated `.codex/config.toml`保留，RAG未刷新。Automatic learning evaluation为`no_candidate`：本记录不外推模型媒体能力；数学对照只约束exact task-local算子，新offload配置只证明dispatch，尚无足够full-model或成片证据支持新的media recipe/adoption。历史失败、反证及局部数值结果继续可检索，未创建placeholder claim。

## Historical Execution Blocker — Restricted Window Recheck

2026-09-29 18:28 +08:00用户要求继续生成后，本窗口重新验证：`/dev/nvidia*`为空，独立`nvidia-smi`退出9，`systemctl --user`不能连接bus，`127.0.0.1:8188/queue`不可达。当前受限namespace无法访问宿主机GPU/service/loopback，不能据此判断host driver损坏、显存不足或host ComfyUI停机；不得绕过平台权限。标准 `load_production_project`在现有Python3.13重开确认Manifest33、actual submits4全部FAILED、3份grant全consumed、fetch0；本轮新增submit/service mutation均0。误选的Python3.11环境缺少numpy，未安装dependency，改用已有Python3.13后loader成功。Evidence见 `runs/coco-nosha-sandbox-recheck-20260929-001/preflight.json`，Manifest bytes SHA-256 `78e097c82f23e918812e31a31d7e979bb53a9d8d8905aadb096b8088e6cfc545`。

继续条件是平台提供可访问本机GPU、用户service manager和ComfyUI loopback的执行窗口；届时先实测MLP mitigation并自主完成任务内cap4 contract/有限预算所需实现与验证，再经canonical seam生成。旧grant/window/permit不复用，不再请求同类规则变更批准。17 s、一镜到底、正常速度、完整因果链及原声线不变；目标仍未完成、MP4 0。该段是read-only preflight的真实blocker记录，不是新media experiment；learning评估`no_candidate`，未进行额外模型调用、RAG rebuild、GPU tests或服务操作。

## Authorization Supersession — 2026-09-29

用户已要求任务内 shared contract、有限预算和 recovery规则默认授权，见[规则变更记录](2026-09-29-default-task-contract-budget-recovery-authority.md)。下方旧 proposal中“须先获用户批准”的机械步骤不再是继续条件；Parent自主完成 scope/self-review、plan、实现、验证与适用审查。规则修改未修复MLP OOM或实现第四grant：上一已验证媒体 checkpoint仍为4个 known FAILED submits、0 MP4；旧计数、消耗、sealed evidence及 unknown-outcome停止要求保持。

## Current Continuation — Fourth Physical Submit Failed At MLP Rotation

2026-09-29 06:43 +08:00更新取代下方旧review/window/remaining-slot状态：**本目标实际local video submit4，全部known FAILED，MP4 0**。第7轮required targeted review已取得完整report并经Parent核验、裁决通过；一次已授权的window续期已执行，原第三grant由actual attempt-05消耗。现在的blocker是实际GPU MLP activation rotation OOM及本次唯一新增submit已用完，不再是review未完成、GPU不可见或local付费额度。没有attempt-06、第四grant、paid media、fetch、activation或Final Acceptance；prepared-only attempt-03的零side-effect历史保持。

### Accepted Review And One-Time Window Renewal

用户明确继续最多两轮review，第6轮`088c92aa-c8a9-4fb3-bec5-5de5be7aa92b`为TLS_ERROR/CONNECT、5.796 s、1 wire attempt、0 Reads、无report，保留其canonical receipt。两次连续无凭据TLS预检通过后，第7轮`ad2d2249-1979-45b0-9d60-1e13c4f8d095`最终**PARSED / 338.698 s / 2 wire requests**，实际authenticated endpoint identity为k3/max；qualified Docker route、seal `0d44bbe41b4b75ab42ec87543ef11edae3c403ad8a25e719c87f1fdc97dab991`、所有artifact hashes及三份完整Read均核验。Report SHA-256 `fc57bd3e131bc658a9fad9f00423764c82f7fd1663f409e5ef0c6fa7b0322609`未发现blocking candidate。Parent以原budget exact hash/fields、一次续期absence check和durable ordering关闭两项evidence questions；proposal中的historical additional_review_rounds=1不被当作第8轮权限，remaining review rounds记录为0。证据`R8/review-round-7-receipt.json`、`review-round-7-adjudication.json`、`review-acceptance.json`。Review只覆盖guard/recovery/window，初始共享实现与kernel审查独立保留，不产生media acceptance。

续期在`2026-09-28T22:40:04.960999+00:00`执行前，通过canonical loader确认Manifest28、actual submitted3均FAILED、第三grant未消耗及no attempt05。保存原budget exact bytes（SHA-256 `74c5efa98ee983ca8d1481f2da9054df9199951b4de5c51c5c6c25a00aaa0c42`），保持started_at `2026-09-28T18:40:58.266294+00:00`及其余所有fields，只将elapsed ceiling7200改为21546，对应操作时刻加7200 s。原/new hashes、review/report/Parent identity与count3先落`R8/continuation-window-renewal.json`，再same-directory atomic replace并核验；new budget SHA-256 `b7da06064d00ccb3bcbb3b94992360e2981ca60409aa07a9926927b74c592410`。没有reset/remint或重复续期；budget中的used3是sealed pre-submit历史，current count4以Manifest为准。

### Actual GPU Attempt And New Failure Boundary

Fresh RTX 5090预检总32607 MiB、free23366 MiB，own service/loopback/queue empty。通过supervisor只切换verified idle own unit，新temporary unit `ai-video-comfyui-e49df81101f744ac80ee693e00662bf1.service`、PID1585842、InvocationID `441a9b1ca2c94b76bce2cbf06b2d2975`，原Python3.13、NORMAL_VRAM、Sage及verified LoRA/Triton overlay；无lowvram/novram/cpu/gpu-only。完整runtime hashes与activation-PID验证后，调用原`recover_pre_submit.py`重开existing grant并沿canonical seam签发new exact intent/one-use permit；不运行会remint的main。

`coco-nosha-attempt-05`于**22:42:52.911690 UTC**实际submit，prompt **e5d7d03a-a1f7-47c9-b26e-6ceb7320ce48**，resolved hash **04e4e80b590f37c55b8aad0b32a298a02660e56869f3c1a632f1f45852b67989**。完整prompt、三图/voice bindings、17 s output、V3 profile均与actual attempt-04相同，canonical fresh repair seed1583761483→1583761484；`R8/attempt-05/control-comparison.json`保存对比。Comfy实际执行**38.69 s**后known OOM，canonical observation于22:43:32.998689 UTC记录FAILED；没有MP4，不能调用不存在素材的media Gate或声称观看/聆听。

本次trace落在`comfy/ldm/minimax/model.py:183`的`MLP.forward -> comfy.ops.linear_input_act -> comfy_kitchen.backends.triton.quantization.int8_linear -> tensor.int8_utils._rotate_activation:72 -> torch.matmul(x_grouped,h)`；与上次LoRA up-projection分配失败的位置不同。服务自身memory summary记录peak allocated19157 MiB、peak reserved21952 MiB、失败时allocated16424 MiB；不将reserved当actual allocated，也不凭该表推导全机同时peak、错误tensor实测shape或GPU utilization。源码显示fc1完整输出、SwiGLU和旋转物化属于MLP路径；仅给旋转分块但保留完整中间结果不自动证明整体peak可承受。候选下一方向是整个MLP按独立token rows处理，仍须独立验证数值和显存；当前未实施或验证，不把到达更后方OOM当完整LoRA/model equivalence。证据`R8/attempt-05/comfy-terminal-evidence.json`及`service-journal-tail.txt`。

### Canonical Terminal State And Restoration

标准loader重开Manifest **33**、actual submits4均FAILED、3份runtime-repair grants全部consumed、attempt05 latest observation存在且fetch receipt为空；experience `ad4688691d40dcea336dc2d9f4273d6c8c7ad24b9f905cac9a2a9a42b25f5a63`为runtime_failure。`R8/attempt-05/terminal-state-audit.json`保存remaining submit0/MP4 0；不用prepared-only03或sealed budget pre-count制造额外slot。

known terminal/empty queue及exact unit/InvocationID核验后恢复原GPU默认服务：`ai-video-comfyui-95d7a154556348f5831e2159ba7b887b.service`、PID **1643363**、InvocationID `b2e6779e2a0b4cb1a97706043653ca84`，active/loopback healthy/queue empty，原Python/Sage、无temporary overlay/Triton/lowvram/novram/cpu/gpu-only。旧ownership/restoration证据独立保留，见`R8/service-restoration-health.json`。Jianji/未知任务未停止；VLLM原本inactive，未停止且无需启动。用户新增Repeated Kimi Failure Fallback规则已读取；本轮7已有完整可用输出，无需追加重复native review，后续命中连续故障时按该规则接手。

下一最小条件见[pending第四runtime repair提案](../superpowers/specs/2026-09-29-coco-nosha-fourth-runtime-repair.md)：先验证完整MLP allocation mitigation，再按sole committer扩展exact local repair ceiling3→4及仅一个新增physical slot，保留default2、全部旧receipt/hash/history和17 s原要求。提案尚未批准/实现，不授权新submit、再次clock续期或绕过Gate。按`record-ai-video-session`记录此真实blocker；自动`distill-ai-video-learning`为`no_candidate`：新MLP failure只有一个完整model attempt，未形成isolated multi-arm/full-model mitigation或既有claim更新，kernel对照不外推media结论。未刷新RAG、未创建claim；记录过程无额外Provider/media/network动作。Git保持local-only，无push/release，unrelated `.codex/config.toml`保留。

## Current Continuation — Third Repair Implemented, Pre-Submit Recovery Review Blocked

以下为截至05:46 +08:00的历史checkpoint；当前状态由上节替代。

2026-09-29 continuation：用户批准第三份exact local runtime repair后，共享契约已实现并提交`c959456`，真实第三份grant已登记但未消耗；**累计local video submit仍3、MP4 0**。用户在解释review及expired window两个继续条件后回复“继续”，批准一轮新增review及review通过后一次同slot7200 s extension，已落在spec/plan amendment与`f9fde46`。第5轮现已执行，**TLS_ERROR / CONNECT / 5.946 s / 1 wire attempt / 0 Reads**，无terminal report；required review仍blocked、未启动第6轮。原budget未改、续期未激活，Manifest revision28、没有attempt-05或新intent。不是GPU不可用或local付费quota；新Kimi maximum policy已生效，但不能解决实测间歇性TLS失败。

本节`R8`为`runs/coco-nosha-lora-memory-20260929-001/`。traceback定位QKV `LoRAAdapter.h`的完整up output，在base output已存在时分配；原profile的518个converted LoRA tensors均2D，ranks16/64，QKV down64×5376/up21504×64。重hash文件与profile pinned SHA-256 `5b8ad6cb7ac206852006f4efa3ce2d679cd6ffb5d5b8a4edce8e981393289df5`一致。failure没有实测tensor shape，因此以下large case是代表性kernel验证，不冒充原失败的exact shape。

Parent编写task-local `R8/lora_chunk.py`，SHA-256 `0b438b1a259317c8ca26696167fa8bb841ed288f512979d3ef3f78a961b856b7`：保留全量down projection，up projection按64MiB delta分块，保持scale rounding后add的顺序，在plain linear inference的独立contiguous base中加回；training/conv/mid/DoRA/reshape/不兼容dtype/device/layout与输入storage alias保留stock path。没有修改安装的ComfyUI、模型、LoRA weights、workflow或17 s output contract。公开[H3 long-sequence源码](https://github.com/ByronLeeeee/ComfyUI-MiniMax-H3-Optimization-Suite/blob/main/plugins/ComfyUI-H3-Long-Sequence/nodes.py)提供LoRA row-chunking的prior art；本候选保留原stock scale rounding，不采用其fused alpha-add，也未引入其base-MLP量化/attention/solver优化。

`R8/verify_lora.py`一次有限GPU验证，55.360 s、8 checks全部PASS：6个FP16/BF16小case（None/noninteger/negative scale、多个chunks及非整除tail）exact equal；输入alias fallback不修改x且exact equal；BF16 `[100032,5376,21504,64]`large stock/chunked全部**2151088128**个输出元素比较，relative RMS/max absolute error均0。stock peak allocated **14007132160 bytes（13.05GiB）**，candidate **5469888512 bytes（5.09GiB）**。预设relative RMS≤0.005和peak<stock×0.6均满足；不是所有GEMM/layout、完整model或media equivalence证明，也不将kernel timing作为完整推理速度。证据为`R8/kernel-verification.json`、log、header inspection及candidate bytes。

受管Kimi deep诊断invocation `cd501bcb-e1b7-4b9d-a3b2-ab92398a8bcc`完成sealed packet Read后到达300s wall budget，classification `OUTCOME_UNKNOWN`、无terminal worker report；route/Read/artifact hashes已检查，不采纳partial conclusions、不自动retry。这是external diagnostic outcome，不改写原三次video的known failed状态，也不声称通过independent implementation review。Parent的kernel proof与该未完成诊断分开保存。

当前`MAX_RUNTIME_REPAIRS_PER_SHOT=2`、sole committer的count guard及`test_runtime_repair_budget_is_per_shot`已重开；Manifest保留attempt-01与attempt-02的两份consumed grants。用户明确选择“A：批准这 1 次任务内扩展并继续生成”，批准[task-scoped third repair spec](../superpowers/specs/2026-09-29-coco-nosha-third-runtime-repair.md)的exact local task/Shot有限repair（2→3）；[durable plan](../superpowers/plans/2026-09-29-coco-nosha-third-runtime-repair.md)已生成。Source candidate采用typed exact extension、`runtime-repair/2`与兼容旧`/1`的serializer，并将完整runtime-repair职责移入同一committer的private helper，保留原MRO与public methods；实现前checkpoint尚未签发真实grant/permit或新submit；下方更新保存后续真实grant与停止边界。RED为9 failed/14 passed（新接口尚不存在）；首轮GREEN 23 passed，补充paid/remote及unknown后继续完整policy验证和implementation review。初版增加MRO owner，引起structure assertion；补齐该test后新增全量Production contract检查在1800 s时约79% timeout、没有打印断言失败，不能称PASS。最终采用private helper保留原MRO并恢复原structure test exact HEAD bytes；据最终实际changed paths重新运行全部必需checks，不更改policy或豁免验证。

### Verified Implementation And Exact Review

`c959456`保留默认cap2，新增typed exact extension与兼容`runtime-repair/1` bytes/hash/read/replay的`/2`；完整事务由原committer委托private helper，同一lock/atomic writer、原MRO与Manifest pointer不变。最终focused **66 PASS**，fresh exact staged tree `1a2ea9878c06f77a316be8abd1f753806f2a909c`的**15项policy checks全PASS**，其中state **962 PASS / 432.04 s**、feedback **329 PASS**、voice **47 PASS**、final-output **63 PASS**。全部source/runtime/log hashes已核对，receipt路径`R8/policy-verification.json`；因用户禁止worktree，只有direct exact-staged policy evidence，`canonical_harness_receipt=null`，不冒充正式Harness receipt。

Implementation review round1 `723404a8-a5e8-4ea9-9a41-4c2820fec694`，qualified Kimi deep/k3/max、Docker sealed route，**PARSED / 353.175 s / 2 wire requests**，完整Read packet 1–2790；report/artifact/route/hash核验。Parent独立裁决无unresolved blocker；裸next lookup已有strict binding/candidate invariant，submit负测经`R8/review-submit-scope-trace.json`证明caller.start返回后在`service.submit_local_once`实际拒绝，文档diff与15项log由Parent核验。见`R8/review-adjudication.json`，不把PARSED单独作为acceptance。

### Known Pre-Submit Failure And Targeted Re-Review

经唯一supervisor切换verified owned、idle original GPU service，temporary unit `ai-video-comfyui-9c7568b9ca164a698b7ffc8667ea36cc.service` / PID9635 / InvocationID `a98dde135dca4b858e4b20a193632074`实际加载pinned LoRA/Triton overlay。`start`返回unit/InvocationID但无main_pid，task wrapper误读导致KeyError；read-only status + exact ownership/queue/activation-PID核验补齐观察，无重启、无媒体submit，见`R8/startup-record-recovery.json`。此处仅证明补丁加载，没有完整model运行。

随后创建原有限budget（local used3/bound4、total=None、new physical ceiling1、paid0、elapsed7200 s/active5400 s），由sole committer登记第三份grant **48342361f437b2f6e9276f008c50b5c0b8048faebbb0ca4b6f368a96367d19b4**，source attempt-04，当前Manifest revision **28**，**consumed=false**。旧ready的raw-all-attempts FAILED guard误将prepared-only attempt-03的RUNNING状态当submit失败边界，进入prepared_next即拒绝；未创建attempt-05、intent/permit或新submit。attempt-03保留原状态且无local/paid submit/observation/fetch receipts，不能写成真实FAILED或计入物理submit。

Parent将task wrapper guard限定为actual local intent/receipt，提交/fetch body抽到helper且AST逐statement相同，新增显式`R8/recover_pre_submit.py`，只重开原budget和exact unconsumed grant、核对revision/actor/source/count3及no attempt-05，不remint/reset。`R8/pre-submit-wrapper-verification.json`保存read-only exact-state guard、body AST等价与新hash证明。Shared code未变，但该semantic correction必须targeted re-review，尚未执行recovery。最初context preflight拒绝为0 requests，不计round。

Review round2 `f91b18c7-c058-4132-ab6c-4459d346df29` full Read，**UPSTREAM_GENERATION_LIMIT / 253.985 s / 2 requests**，8192 cap耗尽，无可采纳report；调查后最终round3采用已成功的16000 cap/480 s、同一小scope。Round3 `5c9507a8-5e67-4d5c-8573-4615f71cc9f6` full Read，**OUTCOME_UNKNOWN / 363.308 s / 2 requests**，第二个wire request `CONNECTION_ERROR / RESPONSE_BODY`、无terminal report。没有采纳partial输出或启动第四轮；`R8/review-acceptance.json`已设parent_accepted/required_review_complete=false，保存first acceptance单独历史。按`SUBAGENTS.md`三轮规则标`REVIEW_ESCALATION_REQUIRED`并请求明确追加1轮审查；此处external review unknown不改写三次local video known FAILED。

### Restored Runtime And Actual Delivery Boundary

#### Authorized Fifth Review And Task-Local Sandbox Recovery — 2026-09-29 05:46 +08:00

用户“继续”承接先前清楚说明的required review与window renewal；[spec](../superpowers/specs/2026-09-29-coco-nosha-third-runtime-repair.md)的Approved Continuation Window Amendment及[plan](../superpowers/plans/2026-09-29-coco-nosha-third-runtime-repair.md)已补齐，`f9fde46`提交。Fresh exact staged tree `a139ab1715cc7ea89b63547e339cf147688595c8`的4项documentation policy checks通过，`R8/round-5-scope-verification.json`保存direct check/log hashes，无canonical Harness receipt。`R8/continuation-window-renewal-proposal.json`封存同一task/Shot/grant、original budget hash和固定started_at；仅review通过后调整elapsed ceiling对应now+7200 s，原其他fields全保持，active5400 s、新physical ceiling1、paid0，无reset/remint。

首次round5 inspect为**零Provider request**的`SANDBOX_IMAGE_UNAVAILABLE`：global config指定原Docker image `08efb085...`，实际本地image已缺失，socket可访问。当前另一镜像entry hash不同，不能冒充原sandbox；未替换到未qualified的bubblewrap。Parent依据canonical `scripts/build_sandbox.py` recipe，用active installed package的pinned runtime/container-entry exact bytes和已有local base重建，`--network=none --pull=false`；仅recipe输出config target改到task-owned `R8/review-sandbox.json`，没有改global共享config或其他image。新image **8f399afdd9208aa6e6b37a6fd15ba3c0afdf1617c60fdc55dc11d3515d8bc720**，单独任务tag保留；full Docker/native adversarial doctor通过。Provenance、build log/config和doctor分别保存`R8/review-sandbox-build-provenance.json`、`review-sandbox-build.log`、`review-sandbox-doctor.json`。Pinned runtime SHA与原deep qualification不变，实际run仍重新核对qualification，不绕过containment。

Qualified round5 seal **b687f95db8942f14fc9d09ad39249b97ed78c47c77a05ab4b322edfa33f38421**，packet SHA-256 **60ae75bddff30b340fed8e6d67917faf892dc293be7d55af043a830812499e0b**；new maximum budgets/deep/max/1M实际封存，旧seal不改。Invocation **58d9100e-4d66-4037-be1e-799bfdab2184**在**5.946 s**结束：**OUTCOME_UNKNOWN / TLS_ERROR / CONNECT**，1 wire attempt、observed Reads0、无terminal report。Canonical receipt/artifacts/route hashes已核验，`R8/review-round-5-receipt.json`及`review-round-5-adjudication.json`保存边界。零request image preflight不计review round；随后有wire attempt的TLS失败计第5轮，不用“没有读到材料”抹除history或额度。

Parent以`debugging-network-issues`做有限无凭据诊断，未调用模型、修改route/selector/CA或禁用certificate validation。初始curl经TUN访问`api.kimi.ai`在约5 s报`SSL_ERROR_SYSCALL`；显式使用当前Mihomo mixed-port17897的HEAD完成TLS并收到HTTP404（path不是推理请求），只证明该次连通，不证明审查可用。错误的旧7897端口CONNECT timeout不作为当前mixed-port结论。OS解析为fake IP198.18.0.215、route经Mihomo table2022；canonical broker明确不消费环境proxy。随后同broker Python的一次direct TLS通过，进一步3次有界同路径握手为**FAIL/PASS/PASS**，失败`SSLEOFError / UNEXPECTED_EOF_WHILE_READING`、成功TLSv1.3，各约5.2 s，见`R8/unauthenticated-tls-probes.json`。该反证排除“始终是TUN而显式proxy才能成功”的断言，只能确认间歇性TLS连接故障；尚未定位具体坏hop或证明修复。Controller仅经已有Unix socket只读访问，未读取controller/raw Provider credentials，无global network mutation。

本轮重新核对Manifest28、3个actual submitted FAILED、no attempt05、original budget SHA仍**74c5efa98ee983ca8d1481f2da9054df9199951b4de5c51c5c6c25a00aaa0c42**；third grant未消耗，budget extension已授权但**未激活**，没有new grant/intent/permit或video submit。现有原GPU默认service保持active、own queue empty；没有切换ComfyUI、停止Jianji/VLLM/未知任务。GPU本轮观察free13584 MiB，不以此推断未来生成一定OOM或一定成功。需要先处理间歇性TLS并在适用明确追加round授权下取得terminal review，不能自动启动第6轮；review通过后原已授权的一次clock extension和同一physical slot可继续。媒体Gate、完整观看/聆听、17 s/因果/原声线仍全部NOT_EVALUATED，MP4 0。自动record/learning评估`no_candidate`：有限TLS诊断和sandbox恢复不证明新的model/media能力，record保持ineligible session_summary，不创建claim、不刷新RAG。

#### Active Maximum Policy Check — 2026-09-29 05:14 +08:00

用户“现在修复了,你看看”后，Parent只读核对global router安装、当前task文件和最近receipts，没有改动router工作树。Router source checkpoint `bb5f619`落实`kimi-maximum-v1`；其`223da83`记录中的installation blocked是历史状态，当前active entry关键source/Skill hashes已与新policy一致。Project-local原review acceptance仍false，未出现本目标新terminal report；其他任务的receipt不能替代本目标review。

本地`subagent doctor --backend kimi`的Docker/native containment检查通过，`live_identity=NOT_EVALUATED`。随后只执行`inspect`，没有`run`：`R8/resource-policy-inspection.json`保存seal **170dc72bc9594c6f8fc89e8afc60c086d0e234ea0a2434a9dac17b500bbd85e4**，effective route deep/k3[1m]/max、context1048576 tokens，generation32000、wall3600 s、idle1800 s、request_limit64、output16777216 bytes、context8388608 bytes；`resource_policy`明示原480/240/3/16000等低额度输入。CLI实测证明新seal采用最高有限资源，不修改旧seal、不消耗第5轮，也不证明先前`CONNECTION_ERROR / RESPONSE_BODY`已经修复或required review完成。新增真实Provider requests和video submits均0。

原`experiment-budget.json`的started_at `2026-09-28T18:40:58.266294+00:00`和elapsed ceiling7200 s未改；本轮首个时间观察为`2026-09-28T21:14:07.675611+00:00`，旧window已于`20:40:58.266294 UTC`到期。保留同一task/Shot、3次实际FAILED、原第三grant未消耗和remaining physical slot1。若继续，需适用授权下的新增有限review round及可审计window extension；不得重置started_at、旧history或grant、借新task逃避边界，也不得把maximum requests64视为64轮review。用户本次“看看”没有被解释为扩大review round或重置generation window。该检查仅确认安装/封存行为，无新的full-model或媒体证明；自动learning evaluation仍`no_candidate`。

#### Authorized Fourth Review — 2026-09-29 03:19 +08:00

用户明确允许追加一次targeted review并继续原17 s GPU生成。Parent封存`R8/review-round-4-snapshot.json`和546行packet（SHA-256 `0dfc77eb1a2d28100f50f1a3d39f8c151039ec0a30034831abb0ca0e3804713b`），核对corrected wrapper、shared implementation及kernel bytes未变；相对旧snapshot仅record/baseline更新状态。Qualified deep/k3/max invocation `a11a51b1-7794-40e5-8804-b2ce05ae67e7`，seal `658336d3212bc49746558c025ad07bd82f5350c81d01f9bb2e975804311ace23`，预算480 s/240 idle/3 requests/16000 generation tokens/8 MiB output。完整Read accepted Spec/Plan和packet已核验。

本轮在**361.067 s、2 wire requests**后以`OUTCOME_UNKNOWN`结束；第二请求`CONNECTION_ERROR / RESPONSE_BODY`，344.434 s、1495730 upstream bytes，不是wall预算耗尽。无terminal worker report，partial输出不采纳；canonical receipt和全部artifact hashes已核验，见`R8/review-round-4-receipt.json`及`R8/review-round-4-adjudication.json`。第4轮用户授权已消耗；required review仍未完成，没有第5轮授权或调用。此external transport failure不改变原3次video的known FAILED，也不证明代码存在review finding。

本轮宿主机实测RTX 5090，总32607 MiB、free22620 MiB；原GPU默认ComfyUI仍为下述PID240543，active/loopback、queue empty，见`R8/round-4-restored-runtime-preflight.json`及`R8/round-4-terminal-runtime-health.json`。没有重新启用overlay、切换服务、停止Jianji或其他任务。Canonical loader重新确认Manifest revision28、3个实际submitted attempts均FAILED、没有attempt-05、第三grant未消耗。原budget started_at `2026-09-28T18:40:58.266294+00:00`未重置；终态审计elapsed2405.927 s/7200 s，剩余窗口随时间递减，不是永久本地额度。

确认本目标没有新submit、own queue empty及unit/InvocationID后，经supervisor停止temporary overlay service并恢复原Python、GPU默认/sage配置，actual argv无lowvram/novram/cpu/gpu-only/Triton。本次restored unit `ai-video-comfyui-806e641e7c6347ccb727bd620ee9e9dc.service` / PID **240543** / InvocationID `23bc6cd693864ff49fc4a15b6b86e6cc`，active/loopback healthy、queue empty，见`R8/service-restoration-health.json`。Installed ComfyUI/weights未改，LoRA patch仅临时进程加载、恢复后不再激活；Jianji与未知任务保留。VLLM从本目标开始就inactive，未被停止、无需启动；Nomad Drive Demo先前自行退出，未发信号。

**本目标仍未完成：video submit3 / MP4 0 / remote-paid media0**。没有media Gate、完整观看/实际聆听、QA activation、P6或Final Acceptance，17 s/完整因果/原声线全部NOT_EVALUATED。旧广告/剧情片不作为本次成果。最小继续条件：先解决已重复两次的review报告传输失败，并在适用授权下完成exact corrected wrapper的required review；然后重新核对当前restored service/queue/GPU、finite elapsed window及同一existing grant，显式恢复task-local overlay后沿canonical seam执行唯一剩余slot。不能把当前“允许追加一轮”当作无限审查预算；不得直接重跑main、重建budget/grant、伪造attempt-03失败、blind submit或重用permit；expired window也不得静默重置。本轮自动learning evaluation为`no_candidate`：同一修正的未完成审查不产生新的媒体能力claim，record仍为ineligible session_summary，不创建placeholder、不刷新RAG。

Git publication保持local-only，`.codex/config.toml` unrelated dirty保留。Shared implementation已commit，task-local runtime/proof artifacts留在ignored `R8`，不提升为Production qualification。

按`record-ai-video-session`更新同一primary record，自动learning为`no_candidate`：此处是deterministic kernel equivalence/capacity验证链，尚无独立full-model/media mitigation pattern；既有learning family无匹配claim。Agent Memory仍沿用本任务既有library-incompatible failure，不retry/rebuild或刷新index，不制造adoption candidate。

## Current Runtime — GPU Encoding Default Applied

2026-09-28 用户明确要求“代码改成gpu”，本轮只修正既有 supervisor 的默认memory-mode参数：不再隐式传`--lowvram`，保留显式`--novram`；不使用当前ComfyUI不支持的`--normalvram`，也不使用`--gpu-only`固定全部模型驻留。`scripts/comfyui_supervisor.py`仍是唯一启动/停止owner，loopback、unique transient unit、ownership、health与generation gates不变。旧记录中的lowvram默认值与旧服务identity从此为历史；第三次known LoRA OOM终态仍成立。

本节`R7`为`runs/coco-nosha-gpu-encoding-20260928-004/`。本机原Python加载当前ComfyUI源码，实际device-selection检查返回`NORMAL_VRAM`、compute/text-encoder load device=`cuda:0`、offload device=`cpu`，见`R7/gpu-device-selection.json`。这是设备选择与CUDA初始化证明，**没有执行完整text encoder，也不证明17 s视频或LoRA显存峰值已通过**。source/tests RED为1 FAIL / 16 PASS；修正后supervisor与Harness focused共199 PASS，command assertions同时覆盖默认无强制VRAM flags和显式novram。

只有核实原unit/InvocationID/PID、loopback和queue empty后，才经既有supervisor显式stop/start应用新默认值。当前unit `ai-video-comfyui-2b389280edc64f3c94160ac9231670b8.service`、PID **2192367**、InvocationID `77eb01457c304a5e925ab972ca4a8615`；actual argv无lowvram/novram/gpu-only/cpu，保留sage-attention；health与empty queue已验证，见`R7/service-health.json`。这是用户要求持续采用的新配置，不是临时停止后应恢复的旧lowvram实验。没有停止Jianji或未知进程；本轮新增video submit **0**，累计仍 **3 / MP4 0**，remote/paid媒体0。

受管Kimi worker只读mapping invocation `265e0eba-5aa3-4dbd-acc5-8756a35d3b81`，两次authenticated `k3-256k/high`请求，sealed packet完整Read及route/artifact hashes已核验；建议去掉强制flag，指出FP16/dynamic-VRAM条件和无full-model证明。Parent以当前源码、device selection与实际服务补证，并加入默认flags排除断言；不把mapping当final implementation acceptance。packet/receipt/Parent adjudication位于`R7/`，未修改ComfyUI安装或模型。

同一记录按`record-ai-video-session`更新，自动learning evaluation为`no_candidate`：这是局部配置修正及device/lifecycle证明，没有新的独立成片对照；不创建claim，不刷新已有失败的Agent Memory索引。原17 s、一镜到底、正常速度、原声线与完整因果链目标不变；其媒体验证仍`NOT_EVALUATED`，下一次提交前仍须解决已知LoRA allocation及既有有限repair边界。unrelated `.codex/config.toml`保留，无push/release。

## Current Supersession — Local Quota Corrected, Third Submit Failed

2026-09-28 22:57 +08:00 terminal result：用户澄清“本地的额度应该是无限的”后，已撤回下节的未批准 renewal-ledger proposal，按当前授权修正现有 local/unmetered submit-limits owner。**累计真实 local video submit 3、MP4 0；第三个请求已知失败，在 GPU LoRA 运算发生 OOM。目标仍未完成。** 本节取代 22:31 的 RUNNING checkpoint；下节 quota blocker、需先批准新 ledger 和旧 restored-service identity 均为历史，不再是当前继续条件。

本节 `R6` 为 `runs/coco-nosha-local-unmetered-20260928-003/`，`R4` / `R5` 保持原 run identity。实现 commit `21fd766b56a571644efc80b885ad32ce6ca5af9b`，exact staged tree `8b17165477a85e331bad8225fad4a24e15f1f6c2`；只在 `_require_persisted_generation_limits` 取消当前 selected sealed `local/local_unmetered` 的 prior-local permanent-ceiling 单调限制。`local_total_limit=None` 表示无累计额度；finite current batch / 显式 total limit、same-task durable intent/receipt counters、paid/remote、runtime-repair cap、history/latest、unknown、one-use permit 和 QA 不变。无新 dependency/schema/ledger/CLI/Provider path；现有文件没有净行数增长。原 `.codex/config.toml` dirty work 保留。

### Correction Verification And Independent Review

先复现旧 blocker：focused RED 4 FAIL / 30 PASS；修复后 guards/runtime-repair/paid-quota focused 51 PASS。最终 stable source 的 **14 个适用 policy commands 全部 exit 0**，包含 generation-feedback 315、Provider 813、Production state 962、final-output/no-regression 63 项 PASS，以及 task-delta Architecture Gate PASS。`R6/policy-final-verification.json` 绑定八个 source hashes、exact staged tree、完整 argv/log hashes；最初增加六行的候选被 Architecture Gate 拒绝，已等价简化并完整重验，旧失败日志保留在 `R6/first-policy/`。用户禁止 worktree，所以仍**无 canonical Harness receipt**，直接验证报告不冒充该 receipt。

新增 quota-correction scope 的受管 Kimi deep review 三轮封存独立预算；前两轮完整 Reads 后触发 `UPSTREAM_GENERATION_LIMIT`，没有 terminal report 或 partial acceptance。第三轮缩小为 exact executable diff、changed owner 与 direct guards/tests、accepted spec/plan，invocation `a6becf82-0548-483b-9d47-79a794e5c0e5` 为 `PARSED`，两份 required Read 完整、route identity / artifact hashes 已核验。Reviewer 未提出 blocking code defect，但问到 pending-intent-only test 和无 Harness receipt。Parent 重开已通过的 `test_pending_submit_intent_on_another_shot_reserves_task_count`、unknown/fetched-history tests，并机械比较所有 packet source excerpts、current/staged hashes、tree 与 14 个 log hashes，关闭 evidence-visibility question；no-worktree 边界如实保留。详见 `R6/kimi-worker-report-03.json`、`parent-review-adjudication.json`、`review-acceptance.json`。这是新 scope 的第三轮，不是旧 duration review 的第四轮；不继续新增 review。

### Exact Third Submit And Historical Active Checkpoint

新 current batch 保持原 task `user-approved:coco-nosha-local-17s-20260928`、used=2、batch bound=3、total limit=None，仅一个新增 submit，active wall 5400 s / elapsed 7200 s。旧 budget 不改，两个 failed submits 保留；prepared-only `coco-nosha-attempt-03` 经 canonical evaluation 记录为 `not_submitted`，不伪造 runtime failure。使用原第二个 unconsumed runtime-repair grant、新 local intent / one-use permit，不 remint 旧 grant、不复用 permit。

`coco-nosha-attempt-04` / `coco-nosha-generation-04` 于 **14:21:17.349935 UTC** 真实提交，Provider prompt ID `768b1c3b-bedc-4099-9db2-19b3cdcb4879`，resolved hash `8b17840a3d705bc0f66b20dedef7e738319dcf186ba6ddbc951865557eff1035`。原 prompt、image/audio bindings、17 s output 和 V3 profile 均与实际 attempt-02 相同；canonical fresh runtime repair seed 1583761482→1583761483，不把准备但未提交的 attempt 当新 sample。`R6/attempt-04/control-comparison.json` 保存 held constants 和 attribution boundary；submit/decision/binding/preview 已落盘。

仅切换 exact owned、empty-queue ComfyUI，经既有 supervisor / R5 pinned launcher 启用 `--novram --use-sage-attention --enable-triton-backend`。该临时 unit 为 `ai-video-comfyui-ed2c7f860774467d863d2aad85653b10.service`、PID 1601951、InvocationID `37a28a62ada641478ef024f826131357`；提交时 loopback 健康，现已在 known terminal 后停止。现有 isolated kernel bytes/proof 和 installed package 未改。初始游戏/Jianji exports 保留；exports 自行结束后用户另明确允许结束 `Nomad Drive Demo`，14:26 实测该游戏已退出，**未发信号**，free VRAM 18754 MiB，见 `R6/authorized-game-release.json`。其他任务保留，VLLM 没有被停止；后续 Jianji 导出重新运行也未被本任务停止。

22:31 checkpoint 的 queue 仍只有本 prompt，elapsed 589 s，history 尚无 terminal result；reference/encoder logs 有执行活动，未报告 error，但不能把“仍在 running”当成功。`R6/execution.log` / `runtime-monitor.jsonl` 保存进度。请求运行期间**不得 stop/restart 服务、重提、remint permit 或恢复原服务参数**；继续观察现有 request，known terminal 后按原 seam fetch/record，unknown 必须显式恢复。正常结束且 queue empty 后恢复原 Python / lowvram/sage 配置并验证健康。

### Known GPU Failure And Completed Restoration

`R6/attempt-04/observation.json` 于 **14:57:12.031244 UTC** 记录 `failed`；ComfyUI history 为 `status_str=error`、node 10 `SamplerCustomAdvanced`、`torch.OutOfMemoryError`，queue empty。`completed=false` 不覆盖明确的 execution_error，也不被解释成 unknown。日志记录本次执行 **00:35:53**。canonical evaluation 已由既有 committer 完成：attempt-04 FAILED、一个 runtime-failure experience、local submit receipt 存在、fetch receipt 不存在，见 `R6/attempt-04/canonical-terminal.json`。prepared-only attempt-03 仍不计为真实 submit。

实际 journal 确认 Triton backend 启用；此前 eager INT8 conversion 失败点此次不再是终态失败点。新的 traceback 在 `comfy/weight_adapter/lora.py:366` 的 `out = op(hidden, up)`（linear 分支为 `F.linear`），上层 `bypass.py` 已先保留 `base_out`，随后还需 LoRA scale/add 的输出。全尺寸输出及并存 buffer 是源码支持的峰值风险；没有测得该失败调用的 exact tensor shape，不能从 isolated kernel shape 推导本次所需额外显存。OOM summary 为 current allocated 10973 MiB、peak allocated 13371 MiB、reserved 17952 MiB；这些是 Torch allocator 数字，不是全卡空闲显存。证据为 `R6/attempt-04/history.json`、`service-journal.log`。

用户问“为什么不用gpu”：本次 **GPU 确实用于视频采样**，但 `--novram` 把约 14960 MB 的 CLIP/text encoder 放在 CPU；journal 明确记录 load/offload/current device 均为 cpu，长编码期间 GPU 使用低。Parent 为保持此前 offload 模式、隔离 Triton mitigation 而沿用 novram，未充分考虑 CPU 编码延迟。当前源码 `model_management.text_encoder_device` 支持 NORMAL/HIGH 或 dynamic 条件下的 GPU encoder 和后续 offload；单纯 lowvram 并不在所有条件下保证 GPU encoder，`--gpu-only` 也不能解决大模型总显存需求。改善编码 placement 与修复采样 LoRA peak 是两个问题，前者不能证明后者已解决。

known error、empty queue 和 unit/PID/InvocationID 核验后，已通过既有 supervisor 恢复原 Python / `--lowvram --use-sage-attention`，不保留任务 Triton flag。restored unit `ai-video-comfyui-010309db15b040cca09837230ce0c3ae.service`、PID **1960989**、InvocationID `7311744cf8c545a4abdc9e04c937eeb4`；loopback health 与 empty queue 已验证，见 `R6/service-restoration-health.json`、`service-restoration.log`。VLLM 原本 inactive、未被停止，无需恢复；游戏未发信号；Jianji 与未知任务保留。

本 finite batch 的唯一新增 slot 已用完，既有两个 runtime-repair grants 已用于实际 repairs；未执行第四次 submit、重置 task/history 或 remint permit。这是当前自动修复边界，不是恢复永久本地累计 quota。继续出片需先找到可执行、保持原 model/profile/17 s/声线/因果链的 LoRA peak mitigation 或足够 headroom，再沿 canonical repair policy 封存下一有限实验；若确需改变已接受的 repair cap/contract，按其 owner 与 Decision Gates 处理。不能用仅切换编码 device 的重复提交冒充已定位修复。

尚无 MP4，因此未运行 `video-analysis`，未观看/聆听成片；17 s 一镜到底、正常速度、完整因果链、身份/声线与视觉质量全部 `NOT_EVALUATED`，无 activation/P6/Final Acceptance。自动 `distill-ai-video-learning` 判 `no_candidate`：这一个 full-model Triton attempt 的 LoRA OOM 未隔离成功 mitigation，旧 eager failures 与 kernel unit proof不能替代对照成片，不创建 placeholder，不刷新失败的 Agent Memory index。记录过程无额外 media/Provider/network call；source correction `21fd766` 的已通过验证与 review 不被此次模型 OOM 混为质量验收。

## Historical Snapshot — Sampler Mitigation Verified, Canonical Renewal Blocked

2026-09-28 20:47 +08:00 更新：用户“继续”后，本窗口已对 sampler allocation 路径完成源码诊断和真实 GPU kernel 验证。**本目标仍未完成，累计 local video submit 2、MP4 0；本窗口新增 video submit 0**。当前 blocker 是 `LOCAL_SUBMIT_CEILING_RENEWAL_UNIMPLEMENTED`，不是宿主机不可访问，也不是已确认 Triton 视频仍 OOM。下节保留此前两次失败及服务恢复的历史；其服务 PID、下一步条件与“未准备第三个 attempt”已被本节替代。

本节 `R5` 指 `runs/coco-nosha-sampler-recovery-20260928-002/`；`R4` 仍指原 host-recovery run。17 s creative scope、原素材和 implementation commit 不变；本窗口未改 tracked executable source、profile、model、installed package 或 user desktop tasks。

### Source Diagnosis And Isolated GPU Proof

Torch CUDA 12.8 下，ComfyUI 当前源码禁用 comfy-kitchen CUDA backend；未传已有 `--enable-triton-backend` 时 Triton 也禁用，所以先前两次实际使用 eager INT8。eager `int8_linear` 创建完整 INT32 输出，再以 float chunk scaling / conversion / concatenation 形成最终输出。仅卸载权重不能消除这些临时分配。安装的 `comfy_kitchen 0.2.31` 已有 fused Triton INT8 backend，但两种 GEMM 与逐行量化的 address arithmetic 使用 32 位 index。

任务独立复制完整 package，只在 `backends/triton/quantization.py` 增加 **5 处 int64 address casts**：两个 GEMM 的 row/column offsets 共四处，rowwise quantizer 的 row index 一处。原文件 SHA-256 `caa360f0ada87c639d45b7d31017444ca71f60905a198c60520ec809c0beaeae`；patched SHA-256 `860943a6d090ed05e9d554a8db978a17dba96136db7bde4373f590f7d3573c3f`。48-file manifest SHA-256 `513e81a94de358ecc24e0c7c261cfd3f9e6e0c5f5f13f2d1597d18634f00fa7c`，其他 files 与已安装源相同。既有 supervisor 的 explicit Python path 使用任务 launcher；它先 rehash manifest / package / GPU proof，再 exec 原 Python 与已有 Triton flag。没有 dependency installation 或新的 Provider seam。

`R5/kernel-verification.json` 为真实 RTX 5090 proof，所有 checks PASS：四组 BF16 / FP16 / F32、scalar/per-channel、bias/ConvRot/SwiGLU 小矩阵与原 Triton **exact equal**；与 eager 的 relative RMS 最大 0.002927，低于预设 0.02。大 QKV case `m=100032,n=21504,k=5376` 输出 2151088128 elements，跨 signed32 boundary，peak allocated 7385197568 bytes；大 quantizer case `m=400032,n=128,k=5376` 输入 2150572032 elements，peak allocated 11135618560 bytes。两者全行 finite，head/middle/tail 样本与 eager relative RMS=0。未运行会触发非法地址风险的原 kernel 大矩阵；样本检查不是全矩阵逐元素证明，也不是 actual 17 s model/quality acceptance。

官方 [comfy-kitchen issue 136](https://github.com/Comfy-Org/comfy-kitchen/issues/136) 提供 MiniMax H3 QKV 32-bit output-index overflow 的独立问题报告；本任务另核对 rowwise quantizer 的 input-index boundary。该外部报告不能证明本任务 17 s 请求成功。

受管 Kimi 本次是独立 kernel diagnosis，不是此前 implementation review 的第四轮。invocation `f0a1c36a-cbf7-4888-b0f5-fdeb9fa90542` 在 480 s wall budget 超时，classification `OUTCOME_UNKNOWN`，无可接受 terminal report；没有重试或采纳 partial output 为 review acceptance。sealed packet / route receipt 位于 `R5/kernel-packet/` 与 `kimi-kernel-run.json`。Parent 自行核对源码及 GPU proof，未把该诊断宣称为通过的独立 review。

### Canonical Preparation And Actual Blocker

新 caller-side finite budget提出两个新增 slots，其中仅一个 runtime repair，绑定旧 budget 与 unchanged approved executable bytes；不是有效的 durable quota extension。初次 `prepare` 被 `LOCAL_BATCH_REVIEW_REQUIRED` 拒绝。Parent 重开两次 terminal failure / experience / queue，补充 `R5/batch-review.json`，保留原 renewal budget started_at；没有新 media effects。之后 canonical decision 为 `GENERATE_ONCE`，compiled request hash `8d7f81290d092efec578df9aff4a411eda2de218b5d3b4c82cba451337758a4f`，canonical seed 1583761483；prompt、image/audio bindings、output 与 profile 均与前次一致。preflight PASS。

`service.start` 注册了 `coco-nosha-attempt-03` prepared state / execution binding，但 `submit_local_once` 在 `_require_persisted_generation_limits` 拒绝 **同 task local_total_limit 2→4**。尚未写 local submit intent 或签发 permit，也没有 Provider job / 第三次 submit。源码同时明确 bare batch review hash 不能 reset durable local batch count；即便只把 caller limit 改为 3，仍缺 canonical renewal relationship。Parent 不改 task ID、清 history、编辑已有 binding 或直接 POST。`R5/canonical-submit-blocker.json` 重开 Manifest 证明原两个 failed attempts 有 submit receipts，新 prepared attempt 没有 intent/receipt；无 unknown video outcome。

第二个 runtime-repair authorization 已在 sole committer 登记但未消费；Shot 最大 runtime repairs 仍为 2，其中旧 repair 已 consumed、新 grant unconsumed。后续不能 remint 同 evidence，不能把 prepared attempt 当 runtime failure；新执行必须遵循正式 recovery / renewal contract，不能复用旧 permit。

待批准 [local renewal proposal](../superpowers/specs/2026-09-28-local-generation-budget-renewal.md) 缩小为**累计 ceiling 2→3，仅 1 次新增 submit**，同 task / used=2，不 reset batch；sole committer strict reopen、content-addressed renewal、atomic one-use consume，保持 runtime-repair cap、unknown fail-closed、local-only 与原成片要求。它是 `PROPOSED / NOT APPROVED / NOT IMPLEMENTED`，不是已恢复的执行能力。原 17 s 批准不覆盖新 persistent quota contract；下一步须批准该 scope 后 plan / implementation / verification / 适用 T3 review，不能再仅封存 caller JSON 就 submit。

### Restoration, Acceptance And Learning

仅停止 verified task-owned Triton unit `ai-video-comfyui-65878e01e36b4ec0b8b2f8ae5772ca71.service` / PID 702372，核对 queue empty 和未提交 prepared state 后恢复原 Python / `--lowvram --use-sage-attention`。当前 restored unit `ai-video-comfyui-d179ad6088ff43e9bff08c2f268e6e82.service`，PID 771248，InvocationID `197f71220fd34ed9b0ac621ca741bf14`；20:47 loopback HTTP 200、queue empty。见 `R5/service-restoration-health.json`；R4 ownership file 已更新。VLLM 未被本任务停止，无需启动；未知 graphics / exports 保留，已安装 comfy-kitchen 全部原 bytes 保持。

没有 MP4，未调用 `video-analysis`、未观看/聆听成片，所有 creative / voice / full-watch findings 仍 `NOT_EVALUATED`；无 activation / P6 / Final Acceptance。隔离 kernel proof 只解决了一部分 deterministic uncertainty，实际模型显存、17 s 动作/声线质量仍未验证。

本稳定 blocker 由 `record-ai-video-session` 更新同一 primary record，自动 `distill-ai-video-learning` 判 `no_candidate`：一个 kernel unit-validation chain 和未提交 preparation，不证明真实长视频 mitigation，也不满足新的独立媒体 pattern；旧两次不同 seed/mode OOM 保留其边界。现有 learning family search 无匹配 claim；Agent Memory 本任务已有 library-incompatible failure，不重试或 rebuild。本文保持 `session_summary / ineligible`，不制造独立实验或学习 placeholder。

## Historical Snapshot — Host Recovery And Bounded Runtime Failure

2026-09-28 18:33 +08:00 更新：旧窗口的 sandbox、素材未取得、固定 5.167 s profile 与 `.git` 只读状态均已被本节的实际宿主机证据替代。下文 `Selected COCO / Nosha Target And Inputs`、`Verified Preflight And Blocker`、`Recovery And Continuation Conditions` 及原记录扩写验证保留旧窗口历史；其中 submit 0、没有 sealed attempt、无法控制服务和无法 commit **不再是当前状态**。

当前目标仍未完成：`LOCAL_GENERATION_BLOCKED_AFTER_BOUNDED_RUNTIME_REPAIR`，本目标 local submit **2**、remote/paid media submit **0**、MP4 **0**。两次均为已知 terminal GPU OOM，不是 unknown outcome；无媒体 quality findings、activation、P6 或 Final Acceptance。已恢复临时切换的服务配置并验证健康。当前最小继续条件是：保持 17 s / 一镜到底 / 正常速度 / 原三图与声线的前提下，验证能降低 sampler 临时分配或提供足够 GPU headroom 的方案，并封存新的有限执行额度；不能继续使用已经耗尽的本轮 1 initial + 1 repair。

### Authority, Environment And Exact Sources

用户明确批准“按 17 秒、一镜到底、正常速度扩展本地 Ref2VA；保留完整因果链和原声线”。该批准接通新增 local duration contract 的 spec / plan / implementation，不授权 paid 媒体替代、删动作、加速或切镜拼接。已按 [spec](../superpowers/specs/2026-09-28-local-ref2va-17s.md) 与 [plan](../superpowers/plans/2026-09-28-local-ref2va-17s.md) 执行，没有创建 worktree。

真实宿主机可见 NVIDIA devices；RTX 5090 为 32607 MiB，driver `580.178.04`。用户服务管理器和 `http://127.0.0.1:8188` 均可用，ComfyUI `0.33.2` / Torch `2.9` CUDA 12.8。实际 T8 为 `1.36.2` / commit `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`，ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，VideoHelperSuite commit `4ee72c065db22c9d96c2427954dc69e7b908444b`，SageAttention `2.2.0`。VLLM 原状态 inactive / MainPID 0，本任务没有停止它，也没有在收尾时擅自启动。18:25 实际 NVIDIA process view 中唯一 compute PID 为本次 ComfyUI；其余约 7 GiB 为 Xorg / desktop / application graphics，均保留。

沿用户指定的 gstack route 使用已有 Chrome `Profile 1` 登录态，取得画布原素材节点提供的 full-size PNG / MP3 response bytes。没有用 UI screenshot 或新生成图代替。实际三图均已 inspection：第一张为场景/比例，第二张 COCO 为小型轮式机器人，第三张 Nosha 为黑衣、透明圆柱容器头部角色。Registry / canonical Character / Scene 选择这些 exact bytes；voice reference 经同一 selected-input projection 进入 Ref2VA。

| Source under `runs/coco-nosha-host-recovery-20260928-001/reference-source/` | Measured bytes / shape | SHA-256 |
| --- | --- | --- |
| `reference-01.served.png` | 2583232 bytes；1672×941 | `66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62` |
| `reference-02.served.png` | 1622654 bytes；1672×941 | `5f3996fbe878d848d0ee6d71f689114f944677b9e739ab816a5e06b048e41920` |
| `reference-03.served.png` | 1461375 bytes；1448×1086 | `5d73df034a0b2a6637f29f8406fbd9f08a54f1636f34c03aea7a239239b134e6` |
| `coco-voice.served.mp3` | 208173 bytes；6.504 s，48 kHz stereo，256 kbps MP3 | `32b3e405b704bff738882fe433c9cb2aa984f08b991109541668170b5db15c7a` |

来源、source node/resource identity、MIME 和 response hash 见 `R4/reference-provenance.json`，没有保存 signed query 或登录凭据。这里证明 exact canvas-served full-size bytes；与用户上传前文件逐字节相同仍为 `NOT_EVALUATED`，不冒充 upload-original proof。当前模型运行环境不支持实际音频聆听，reference MP3 的视频转写工具返回 `no_video_stream`；没有据此伪造 transcript 或“已听过”。

点击旧 reference card 时 Parent 曾误插 composer chip；随后只删除该意外 chip，reload 后核对原文 6326 characters、SHA-256 `b066122f8a5c28ada6d78f27e86a8a710c5aec7589e2ca87b6c55e1a3459b028` 恢复，node / edge counts 为 296 / 162。`R4/composer-restored.json` 与 `composer-persisted.json` 保留恢复证据；不把中间误操作说成完全无编辑。没有点击画布生成。

### Implemented Long Profile And Verification Boundary

显式新 lane 为 `minimax_h3_t8_ref2va_turbo_native_17s_v3_local`，profile `minimax_h3_t8_ref2va_turbo_native_17s_v3.json` 的 content SHA-256 为 `12a94254dabb1ad8440b64fb49fb0549574823ecc25c06321c65426579d7c45b`。schema 3 / profile v3 只允许 Ref2VA；1344×768@24fps、native audio、4 steps、dual-clock Euler / native flow、pinned non-pruned weights。一次采样 413 frames，既有 `MiniMaxH3OutputTrimT8` 同步提供首 408 frames / 17 s audio，仅去掉 5 帧内部网格 padding，不改速、不切镜、不重复末帧。安装节点的 CPU executable proof 验证 ordered 413→408 和 32 kHz / 544000 audio samples；这不是生成成片。

V2 的 124-frame profile bytes、hashes 与 default six-child family fingerprint 保持原值。新 lane 必须显式选中，不产生默认升级或 Production quality qualification；413 frames 超出 T8 约 124–362 的常见训练区间，仍是经验风险，不能从 loader / schema PASS 推断质量或可执行显存需求。

V3 prompt 的 `<Picture 1..3>` / `<Audio 1>` ordinal 按真实 compiler 的 canonical asset order 与 upload binding 对齐；新 helper fail closed 拒绝缺 Shot marker，避免把 opaque Asset IDs 当模型角色名。修正既有 rich reference-only intent projection 错误要求 first/last frame anchors 的 deterministic preflight；下游 reference evidence、exact hashes 和 frame-mode gates 保留，没有新 schema、writer 或第二 timeline owner。

final focused suite 为 **265 PASS**；全部 **12 个**适用 mandatory policy commands exit 0，包括 813 项 Provider suite、voice routing、requirement/projection、workflow、Harness 和 docs/policy checks。精确 implementation tree `9de07bed4973db5fbd6b1c2370b0e63ef0190288` 已提交为上述 `17aca10`；详细 argv / logs / exit codes 见 `R4/policy-final-verification.json` 与 `final-candidate-tests.log`。

受管 Kimi implementation review 的三轮预算已用完：第一轮 generation-limit 无 terminal acceptance；第二轮 partial evidence 未放行；第三轮 `4779f065-1192-4d27-808e-887363768c8c` 为 `PARSED`，15 required Reads 完整，route receipt、upstream identity 与 artifact hashes 经 Parent 验证。Parent 调查并裁决 ordinal false positive / nonblocking caller-cardinality 与文档证据边界；最终 `R4/review-acceptance.json` 为 `parent_accepted=true`，blocking findings 为空。单独 `PARSED` 不构成 acceptance，也没有调用第四轮。准备过程中 `ready.json` / `resolved.json` 后来合法刷新；旧 snapshot hash 是审查时身份，不能当这些 mutable preparation files 当前 bytes 的证明。

用户禁止 worktree；canonical Harness 要求 detached verification worktree，故本轮只在已知 exact working-tree state 执行 policy commands，**没有 canonical Harness receipt**。`policy-final-verification.json` 是直接验证报告，不冒充 Harness receipt；该限制没有被旧 PASS、Kimi verdict 或 local commit 消除。

### Canonical Preparation, Execution And Known Failures

`R4/production/` 为本目标独立 development project；完整因果、三图职责、原文对白与唯一 COCO speaker / original voice、无 BGM / captions / readable phone UI、四宠物职责与持续 camera、末段 15–17 s D 咀嚼均冻结在 intent / rubric。提交走 `GenerationFeedbackOrchestrator` → selected adapter → `VideoGenerationService` → `ProductionStateCommitter` 的 local intent / one-use permit；不复用广告/剧情 projects 或旧 permit。无 activation。

Parent 初次 preparation 更新 intent 后未同步 graph，`service.start` 在 lineage validation、任何 VideoAttempt / intent / permit 或 submit 前拒绝。随后通过已有 `commit_project_registry` owner 刷新 graph，再验证 lineage。原 budget 的 started_at 和 ceiling 保留；preparation guard / unsupported metadata / invalid operation 等提交前错误均是 no-effect，不计为媒体尝试，也不被描述成 unknown retry。证据为 `R4/pre-submit-graph-recovery.json`、`pre-submit-preparation-recovery.json` 及 execution logs。

封存预算见 `R4/experiment-budget.json`：initial 1、repair 1、total 2、paid media 0、elapsed 7200 s、累计 active prompt wall 5400 s；started_at `2026-09-28T09:46:18.542959Z`。两次真实执行身份如下：

| Attempt | UTC submit → known failure observation | Request / prompt identity | Outcome |
| --- | --- | --- | --- |
| `coco-nosha-attempt-01` / lowvram | 09:52:34.237792 → 09:53:14.345884 | request `b4dea780e4d6e5bb478b705523af504844cef1ee1421bf52c743f9d9db2b6016`；prompt `5b237786-c2bf-4192-98fb-94cd5a3288b3` | node 10 `SamplerCustomAdvanced`，`torch.OutOfMemoryError`；MP4 0 |
| `coco-nosha-attempt-02` / novram | 10:02:14.077101 → 10:28:09.647744 | request `ac6088d93744de8af4a9e19e47241d1cb64f28a3be5b89880ee423e3943946be`；prompt `fdadae82-47b9-4806-a047-d88b80a548f5` | 同 node / 同 OOM kernel；MP4 0；prompt wall 25:54 |

首次已知失败后 queue empty，记录 canonical runtime-failure experience；仅停止 owned ComfyUI，再以 supervisor 显式 `--novram` 开启新 owned unit。`record_runtime_repair_authorization` 绑定 exact failure，one-use grant content hash `9b176ac11aa14c96d1b2ca1fad0689ae72d282a278e9c2a923a197f52b216f5a`，由 canonical decision / replacement submit 消耗。保留 prompt / image / audio bindings、profile 和 output；canonical repair seed 从 1583761481 前进到 1583761482，见 `repair-02/runtime-control-comparison.json`。这不是严格单变量模型质量 A/B；没有声称相同 seed 或已隔离所有内存因果。

第二次经历约 24 min 的 CPU/offload input processing 后进入主模型采样；主模型日志为 0 MB loaded / 32429.07 MB offloaded / 1241.97 MB buffer。仍在 `comfy_kitchen/backends/eager/quantization.py:1048` 的 `int8_linear` / `chunk_scaled.to(out_dtype)` 发生 GPU OOM；即时 memory summary 为 active / allocated 23824 MiB、reserved 24288 MiB。offload 权重未消除临时 activation/conversion allocation；不能据此保证只关闭几个桌面窗口或增加少量 headroom 即可成功。

`repair-02/comfy-history.json` SHA-256 为 `8ad3bbc38db87d2911f7d22494b1a80b331cca495cea5b42ea8a87040305eea7`。ComfyUI 对失败历史保留 `completed=false`，但 `status_str=error`、明确 `execution_error`、canonical observation / Manifest 为 failed、queue empty；这里的 false 不被误当作仍运行或 unknown。错误摘要、service log、两次 observation 和 canonical runtime-failure experiences 均落盘。标准 reader 重开确认两个 attempt FAILED、local submit receipts 存在、fetch receipts 不存在，task run 内 MP4 0，见 `R4/completion-state.json`。

由于没有 MP4，没有调用 project-local `video-analysis` 冒充媒体 Gate；时长/速度、身份、完整因果、声线和 full-speed watch/listen 全为 `NOT_EVALUATED`。两次都是 runtime failure，没有模型质量 FAIL / PASS，也没有用已有广告/剧情成片替代当前成果。budget 已耗尽，未提交第三次、付费 fallback 或降低目标。

### Restoration, Learning And Continuation

known error / empty queue / unit InvocationID / PID ownership 核验后，已停止临时 novram unit `ai-video-comfyui-a777d83e2f654ca7a831d72d9ba7ee02.service`，恢复默认 `--lowvram --use-sage-attention`。新 owned unit `ai-video-comfyui-fdb8ccb9bdab4229b22857be63e51a2a.service`、PID 124265、InvocationID `4bc393239e0d46938dfe1fc35da9267f`，18:31–18:33 loopback health PASS、queue empty。证据为 `repair-02/restore-preflight.json`、`novram-stop.json`、`lowvram-restored-start.json`、`service-restoration-health.json`。没有临时停止的 VLLM 需要恢复，未知桌面任务未动。

`record-ai-video-session` 更新同一综合记录、保留旧窗口历史；自动 `distill-ai-video-learning` 为 `no_candidate`。仅本目标的一次 mode repair，尚未隔离可采纳的 allocation mitigation，也没有成片可支持模型质量模式；现有 learning search 未发现直接匹配的 Ref2VA / novram / int8-linear claim。不能从重复日志或 proof layers 制造独立支持，也不据本案例修改已 adopted rule。Agent Memory 在本任务 preflight 返回 library-incompatible shard / exit 3，按 Skill 不重试、不做 foreground rebuild；继续重开本地原文及 exact runtime evidence，新记录是否已进入 RAG 未验证。

后续首先需要可验证的 local sampler memory mitigation 或满足峰值分配的执行条件，以及新的有限执行 ceiling；不需再批准已批准的 17 s / single-take creative scope。原三图/声线、canonical project、spec/plan、implementation commit 和 terminal receipts 均可复用为检查输入，但不得复用已消耗 permit。若确需修改 pinned runtime / Provider contract，仍按 owner 与适用 verification 处理。任务未完成与 engineering commit / environment closure 分开报告。无 push / release；unrelated `.codex/config.toml` 保持未 stage。

## Reading Guide

本文件按用户要求扩写此前 80 行的简版，保存从 creative-goal implementation、两轮广告/剧情真实测试、参考图纠错、即梦画布诊断，到 COCO/诺萨本地复刻准备的完整上下文。它是当前综合入口，不替换各实验的原始 receipts、immutable evidence 或历史记录，也不将扩写算作新的实验。

下文依次记录用户目标与授权、工程实现、此前八次视频尝试及本目标两次本地提交、参考素材及实际消费情况、失败归因、画布方法与完整目标、当前参数支持、本地映射、阻挡、验证和继续执行条件。原始 source / prompt / report 按 exact path 引用；不复制 raw Provider prompt、登录态、credential、signed media URL 或完整外部响应。

| Concern | State at this checkpoint |
| --- | --- |
| Creative-goal M1–M4 engineering | 已完成 offline implementation；不等于业务媒体质量通过 |
| 两轮广告/剧情视频 | 共 8 次 submit：4 local + 4 API；6 个 raw MP4 均未通过，2 次 local 剧情 OOM |
| 第二轮参考图 | 6 次 image generation，5 张最终可用新参考；错误广告尾帧已排除，修正图未提交 |
| 用户即梦画布 | 已取得 exact served 三图/声线；意外 composer chip 已恢复并 reload 验证；无画布生成 |
| 当前用户目标 | 本地复刻 COCO/诺萨片段，保留角色、声线、完整因果链、正常速度与一镜到底 |
| COCO/诺萨本地生成 | local submit 3，known OOM 3，MP4 0；attempt-03 为 prepared-only，attempt-04 为第三次实际提交 |
| 17 s engineering | `17aca10` local commit；265 focused PASS，12 policy commands PASS；无 canonical Harness receipt |
| 最新综合记录 | local/unmetered quota 已纠正；第三次在 GPU LoRA 运算 OOM，原服务已恢复；未交付视频 |
| Quality / Production / release | 未获 human full-speed acceptance、P6、Final Acceptance；无 push / release |

## Purpose And Scope

用户要求记录当前 API / local 对即梦画布参考方式的支持情况，然后本地按照画布方法生成，随后明确指出需要“一个非常完整的记录”。本文件承接 [implementation](2026-09-27-creative-goal-preservation-implementation.md)、[first-frame tests](2026-09-27-creative-goal-real-api-local-tests.md)、[first/last retests](2026-09-28-creative-goal-first-last-reference-retests.md) 与 [Jimeng canvas comparison](2026-09-28-jimeng-canvas-method-comparison.md)。本轮请求授权任务内 local generation，但不授权新的 remote / paid generation、自动 activation、P6 或发布。

本记录区分能力声明、当前封装、历史技术证据、本轮运行条件与实际媒体效果。用户已明确选择复刻画布里的 COCO/诺萨片段，不再做广告/剧情替代测试。旧窗口在环境/素材/时长上被阻断；本次 continuation 已恢复环境、取得素材并实现显式 17 s profile，但三次真实提交均 OOM，视频目标未完成。

## Request History And Authority

| Order | User instruction / decision | Execution meaning and result |
| --- | --- | --- |
| 1 | 实现 `docs/superpowers/plans/2026-09-27-creative-goal-preservation-and-completion.md` | 批准 M1–M4 offline engineering；工程阶段未据此提交业务媒体 |
| 2 | 使用 gstack browser | 实际验证开发报告显示；后续画布浏览也沿 gstack route |
| 3 | “真实测试”；选择“按 plan：真实广告、剧情各测一次” | 真实媒体验证与 offline fixtures 分开 |
| 4 | “分别用api和本地一起尝试” | 第一轮四个独立 video attempts：广告/剧情 × API/local |
| 5 | 明确允许停止占显存的 VLLM 服务再跑本地 | 仅处理该获准服务及 task-owned ComfyUI；不授权停止其他导出或清理未知进程 |
| 6 | 询问失败是否因为参考图片太少 | 需要核对真实输入、动作和资源证据，不能只按图片数量猜测 |
| 7 | “你先生成合适的参考图不要只有首帧,多一点再测试” | 新参考素材任务；第二轮另封存 finite task budget，不重用旧 permit |
| 8 | 访问指定即梦画布；用户完成登录 | 只读浏览已有作品/素材；无新生成、发布或画布编辑 |
| 9 | 明确比较对象为“你刚才生成的广告、剧情测试，比我的画布差” | 诊断 Parent 的制作方法与真实结果，而不是误把用户作品当作失败对象 |
| 10 | 询问 API / local 是否支持画布里的参数 | 区分实际使用的模式、仓库其他模式、prompt guidance 与 hard runtime parameters |
| 11 | 写记录，然后本地按画布模式生成 | 记录与 local preparation；不授权自动改成 paid API |
| 12 | 明确选择“复刻画布里的 COCO／诺萨片段” | 原广告/剧情不是当前生成目标；完整一镜到底要求必须保留 |
| 13 | 要求完整记录 | 扩写当前文件并核对既有证据；不为记录额外生成媒体、跑 Provider 或重做历史测试 |
| 14 | 续接真实宿主机恢复并继续 COCO/诺萨目标 | 重新验证 devices / resources / user services / loopback；保留未知任务、收尾恢复临时设置 |
| 15 | 批准 17 秒、一镜到底、正常速度扩展本地 Ref2VA，保留完整因果链和声线 | 新 local spec / plan / profile implementation 与 1 initial + 1 repair；两次 terminal OOM，MP4 0 |

原始 creative-goal 问题来自用户拒绝青颜全程单图方案：`runs/ecommerce-qingyan-packshot-20260927-001/final/青颜_10秒_原图品牌短片.mp4`，SHA-256 `25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6`。用户的拒绝针对实际创作方案，不是 formal Production ReviewReceipt；历史技术 PASS 不因此被改写，拒绝也没有因后续代码或局部动作片通过结构检查而解除。来源见 [spec record](2026-09-27-creative-goal-preservation-spec.md)。

## Evidence Locations And Identity Rules

为避免长路径掩盖内容，以下 aliases 只用于本记录：

| Alias | Exact repository-relative root | Evidence type |
| --- | --- | --- |
| R1 | `runs/creative-goal-real-test-20260927-001/` | 第一轮首帧-only，四次视频 submit |
| R2 | `runs/creative-goal-multi-reference-test-20260927-002/` | 第二轮首尾帧，四次视频 submit、六次参考图 generation |
| R3 | `runs/jimeng-canvas-diagnosis-20260928-001/` | UI capture、文字、截图、read-only comparison |
| R4 | `runs/coco-nosha-host-recovery-20260928-001/` | 当前 exact served sources、implementation/review proof、canonical local attempts 与 restoration |

`R1` / `R2` 的 attempt 名称会重复，例如 `advertising-local-attempt-01`。唯一身份必须同时包含 experiment/run namespace 和 exact request hash；不能按同名 attempt、图片数、报告数或 proof-layer 数重复计入独立实验。

每个成功 raw MP4 的实际路径为 `<R1或R2>/<advertising或drama>/<local或api>/production-v5/state/video-generation/fetch/files/<SHA-256>.mp4`。这些 `runs/` 产物在 Git 中被忽略；本记录提交也不会把媒体打包到其他 checkout。没有原文件、合法复制件及匹配 bytes 时，不应把本机路径当作跨机器可用素材。

## Engineering Implementation And Its Limits

### Implemented Milestones

| Milestone | Implemented owner / behavior | Evidence boundary |
| --- | --- | --- |
| M1 | `scripts/creative_goal_binding.py` 只读加载 creative input、Director v4 coverage、FinalOutputContract 与 binding；join explicit intent → constraints → units → requirements，校验 exact bytes、UTF-8、containment、symlink 与 IDs | 证明已提供 inventory 的引用关系；不能证明自然语言意图提取完整或 concept 好看 |
| M2 | `final_output_review.py::adjudicate_final_output_details` 产生 aggregate、有效逐项 verdict 与 global evidence gaps；旧 aggregate API 投影同一计算 | raw PASS 不等于有效 PASS；缺 human strength / 1.0x viewing 或身份不符保持 NOT_EVALUATED；有效 FAIL 优先 |
| M3 | `visual_quality_report.prepare(..., goal_binding=...)` / `--goal-binding`；新 packet `/3` 封存 validated binding 及三个 dependency bytes，reopen 只消费 packet snapshot | 原始目录移动可 reopen；snapshot 换 bytes/contract 不复用旧 PASS；`/1` / `/2` 保持原兼容边界 |
| M4 | 既有 creative-completion reference、routing、matrix、baseline 与 Harness routes 接通 | 保留跨轮目标、独立 concept 判断、实际观看和有限修复；不增加第二 QA / Manifest / activation owner |

现有源码仍包含上述入口；本次扩写只读取，没有再次运行工程 suites 或修改实现。既有 code/tests 是工程事实来源，计划和本记录均不能替代 executable verification。

### Historical Verification

M1 初始 40 tests、M2 focused 92 tests、M3 focused 111 tests 通过；Parent 后续发现 `Explicit User` normalization 漏检，新增两项 RED 后复用原 validator normalization 修正，相关 focused 合并 suite 为 314 PASS。最终 exact code checkpoint 为 `6019f3969cb49e68f30c5f29f85c284c747f7a0e`；关键 suites 包含 Production Review 664、Final-output / No-regression 63、visual quality 69、goal binding 161 PASS。

工程报告使用 2 s lavfi fixture 实际渲染。Chrome MCP 当时返回 `Missing X server`，随后以本机 headless Chrome / 用户指定 gstack 验证 raw PASS 与有效 NOT_EVALUATED 的区分、图片加载及移动端布局。fixture 证明报告显示，不证明广告/剧情动作、音频或用户满意。

T2 implementation 使用受管 read-only Kimi `deep`：第一轮 `ab33aa6b-f491-4dfe-88de-05c4d2e77dd5` 超时、15 wire requests、OUTCOME_UNKNOWN，无 terminal review；第二轮 `bf2be738-db45-4fc3-bf71-f091676d19d1` 正常 PARSED、7 wire requests、16 complete Reads，qualified route / authenticated identity 可核验。Parent 重开 source / baseline / receipt 后裁决 offline M1–M4 KEEP，没有把 transport verdict 当作创作 acceptance。详细 seals、uncertainties 和 AOCI 边界保留在 [implementation record](2026-09-27-creative-goal-preservation-implementation.md)。

工程成果是“目标和有效证据不丢失”，没有证明模型已经能演出正确因果、自动理解用户撤回拒绝，或已经完成合格成片。

## Preserved Advertising And Drama Goals

| Domain | Full target | Scope actually generated |
| --- | --- | --- |
| Advertising | 问题开场 → 老人推荐 → 使用 → 社会反应 → 原包装 hero / CTA；商品与衣着不变，使用过程可见 | 只生成使用动作候选；不包含整条广告链，不能替代完整商业 composition |
| Drama | 姐姐递钥匙 → 弟弟退避拒接 → 姐姐收回钥匙、放松等待 → 弟弟看见退让后主动接取 → 唯一钥匙最终归弟弟 | 一个固定轴线互动段；不能用字幕、旁白或仅改变末帧补齐等待触发 |

两轮均保存 `authoring/{advertising,drama}/` 的 creative-input / coverage / contract / direction / binding。`review-authoring/` 仅整理报告所需 visual requirement namespace，通过 lineage 指回原合同，没有修改 submit 前冻结的 Provider QA rubric 或降低用户目标。

## Round One — First-Frame-Only Real Tests

### Exact Requests And Results

R1 四次提交均为 `image_to_video`、一个 `first_frame`、零 reference audio/video bindings、native audio enabled。local 使用 stock `provider_kind=minimax_h3_fl2va` / `model_id=minimax-h3-fl2va`，不是 T8 native Turbo；API 使用 `provider_kind=vidu` / `model_id=viduq3-pro`。下表的 seed 从各 `resolved.json` 直接读取。

| Record ID | Domain / route | Effective seed | Requested output | Result / failed evidence |
| --- | --- | ---: | --- | --- |
| R1-ad-local | advertising / local | 1035261873 | 294 frames / 24fps，416×736 | FETCHED；10–12 s 左袖消失、衣着退化，identity FAIL |
| R1-ad-api | advertising / API | 905050387 | 12 s / 24fps，720p adaptive | FETCHED；1–4 s 泵头长出横向白管，随后消失，object FAIL |
| R1-drama-local | drama / local | 838889672 | 294 frames / 24fps，1344×768 | known CUDA OOM，无 MP4；没有媒体 quality verdict |
| R1-drama-api | drama / API | 2071971615 | 12 s / 24fps，720p adaptive | FETCHED；等待触发缺失，交接后钥匙回到姐姐手中，action / object FAIL |

### Measured Artifacts

| Record ID | Bytes | Measured duration / frames / size | Audio |
| --- | ---: | --- | --- |
| R1-ad-local | 2160466 | 12.250 s / 294 / 416×736 / 24fps H.264 | AAC stereo 32000 Hz |
| R1-ad-api | 6890098 | 12.042 s / 289 / 720×1280 / 24fps H.264 | AAC stereo 48000 Hz |
| R1-drama-api | 4512460 | 12.042 s / 289 / 1268×724 / 24fps H.264 | AAC stereo 48000 Hz |

R1-drama-api 的 1268×724 是历史 measured output，不把 nominal 720p 重写成 1280×720。音轨存在只关闭 stream-existence 条件；实际完整聆听、audibility、lip-sync 和人类完整原速 acceptance 未完成。

### Runtime And Repair Boundaries

三个 fetched MP4 在当时均调用 project-local `video-analysis`，逐秒抽样，剧情追加 0.5 s 核对钥匙：8–9 s 可见钥匙在弟弟掌上，10 s 又在姐姐指间、弟弟掌心空着。正式 analyzer evidence 走 public `review_generation_attempt` 和 `ControlledPresentationVerifier`；没有冒充 human proof。

API 剧情首次 polling transport failure 后，只查询、fetch 原 task；`resumed-observation.json` / `media.json` 记录 `resumed_existing_task=true`、`new_submit_count=0`，没有额外 submit 或换 permit。

local 剧情 OOM 的 runtime-failure evidence hash 为 `c2c0dde009f2d30de97c2d03ef0a3db666e2a699857a7d593ad13e3a529f6c3f`。环境 repair readiness 试图把初始 sealed batch ceiling 从 1 改为 2，committer 拒绝 `Generation submit ceilings cannot expand within one task.`；repair attempt 只有 pre-submit state，submit 0，当时没有 novram 成功证据。

Own ComfyUI queue 为空后停止 own service；当时恢复 `jianji-qwen3-vl.service`，readback active / MainPID 599082。服务恢复不代表 OOM 或创作缺陷解决。第一轮 API repair ceiling 为 0。

### Real Report UI Repair

真实长 hash/path 使报告在 390px viewport 横向溢出，article 约 666px；Parent 修复 `scripts/visual_quality_report.py` 的长词换行和 flex wrap，commit `8f684036512e1f0ef9752ce53c31cc106392ee7e`，focused UI tests 82 PASS。gstack 随后验证 local 广告和 API 剧情 report 在 390px / 1280px 无 overflow；广告 5 张帧图、剧情 7 张帧图加载。原 local MP4 muted 播放推进至 1.256906 s，仅证明解码/播放，不能当作完整观看或听音 acceptance。

## Round Two — Added References And First/Last Retests

### Generated References And Actual Consumption

用户要求增加参考图后，R2 使用 built-in `image_gen` 生成 6 张 PNG；错误广告 end 排除后，保留 5 张可用新参考。加上广告既有 first frame，相关输入列表如下。本次扩写重算六张新 PNG 的 SHA-256，均与 `references/manifest.json` 相符。

| Reference | SHA-256 | Use / current status |
| --- | --- | --- |
| Existing advertising first | `e3e305cab076ea151a6b3cff6ad13f9bbacb8776ccb63a029c2ef0a92384782d` | 两次广告 video submit 使用 |
| `references/advertising-end.png` | `7111a4f6d7295915dd2ceccc6092c3834ec261c9298cef169038224fee54857b` | 两次广告 video submit 使用；后发现持瓶手错误，已排除 |
| `references/advertising-end-corrected.png` | `066448edf98bddfe4f825e70e5e8449f544a56773130d6108f4febb503e6c1a4` | 已生成并检查；video submit 0 |
| `references/advertising-pump-detail.png` | `88abafb0da32a644198b77ba7850e0644b6f1aee5881668c6d737390f8560384` | authoring only；没有作为第三张参考输入模型 |
| `references/drama-start.png` | `dd653730e01a7f8e4400384efbcfecb60a89e22bfd895d73c398743fc4b93e0c` | 为首尾尺寸兼容生成；两次剧情 submit 使用 |
| `references/drama-waiting.png` | `ab76dda17ad3095aa39668acf467113052a95fd945bad3a2398682691c6e985f` | authoring only；没有成为模型可消费的中间状态输入 |
| `references/drama-end.png` | `43989d7fe967c130ea3b2ed5d2fae8a90d51b165014fcc635ee82303d07fbef2` | 两次剧情 submit 使用 |

图库为 `R2/reference-gallery.html`，整理后的 authoring inputs 为 `image-authoring-prompts.json`。后者不是逐字工具调用 transcript。原 packshot 盖子遮挡泵头，生成的细节图不证明商品隐藏几何真实，也不能替代 authentic product source admission。

R2 实际没有切换 Ref2VA / R2V：四个 `resolved.json` 都是一个 `first_frame` 加一个 `last_frame`，`media_bindings=[]`。`verified-two-frame-bindings.json` 保存 exact registered bytes 的断言。等待图/细节图虽然生成并展示，但没有进入此次 video conditioning。

### Parent Reference-Compatibility Error

初版广告 tail 把持瓶袖口手从画面右侧换成左侧；原 anatomical left/right 描述也与图像冲突。Parent 在 submit 前的静态 reference Gate 漏检，两次真实广告 submit 都使用了该错误尾帧。因此即便模型连续接到这个终态，也不满足原目标，不能把换手全部归因于模型。

`R2/reference-image-gate-correction.json` 明确 supersede 初版 compatible / accepted-endpoint 结论，保留旧 request 和图片。后续 corrected reference 保持原持瓶手，screen-relative wording 也已准备，但没有进入新的实际 video submit。修正图“看起来兼容”与“修正后模型效果已验证”必须分开。

### Exact Requests And Outcomes

R2 local 使用 stock H3 profile hash `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`，20 steps、294 frames / 24fps；不是 T8 native Turbo。API 为 Vidu `viduq3-pro`，回传 metadata 表示 `headtailimg2video`。

| Record ID | Domain / route | Effective seed | Requested output | Result / failed evidence |
| --- | --- | ---: | --- | --- |
| R2-ad-local | advertising / local | 788478632 | 294 frames / 24fps，416×736 | FETCHED；9–10 s 换手，1–7 s 镜头放大裁切头发/脸侧，action / space FAIL |
| R2-ad-api | advertising / API | 1717170643 | 12 s / 24fps，720p adaptive | FETCHED；9 s 瓶子在头侧持瓶手突然出现，缺少连续交接，action / object / motion FAIL |
| R2-drama-local | drama / local | 223189650 | 294 frames / 24fps，1344×768 | `--novram` 下 known CUDA OOM，无 MP4 |
| R2-drama-api | drama / API | 1732247789 | 12 s / 24fps，720p adaptive | FETCHED；末态钥匙归弟弟改善，但等待触发不完整，action FAIL；object NOT_EVALUATED |

| Record ID | Bytes | Measured duration / frames / size | Audio |
| --- | ---: | --- | --- |
| R2-ad-local | 2853879 | 12.250 s / 294 / 416×736 / 24fps H.264 | AAC stereo 32000 Hz |
| R2-ad-api | 7159095 | 12.042 s / 289 / 720×1280 / 24fps H.264 | AAC stereo 48000 Hz |
| R2-drama-api | 3657228 | 12.042 s / 289 / 1280×720 / 24fps H.264 | AAC stereo 48000 Hz |

两个广告候选抽样可见长袖保留，但这个局部改善不关闭换手、摄影机或整体目标缺口。剧情中弟弟 2–3 s 深弯腰，6 s 姐姐放低钥匙时弟弟已伸手，随后两次掌部接触；遮挡下不能确认两次实际钥匙转移，所以不能写成 object PASS 或两次转移已确证。

R2 local 剧情 OOM 发生在 H3 quantization `torch.cat`，错误为 `torch.OutOfMemoryError: Allocation on device`。历史 own journal 记录 allocated 20689 MiB、reserved 24448 MiB、prompt elapsed 00:13:56；provider request `9849a18e-304c-455c-b1af-a61cf291eec2`，observation fingerprint `a336dd126bb28bd22d8b809393a47fb98d9b1f9375600fbb0eae600ba08878d7`，public runtime-failure evidence hash `217bc1fa9c4f3cb0047a2eb3b4bc60a2385602deed82f9549e59395762466a1e`。没有 MP4 就没有本次动作、画面或音频的可比较成片。

### Budget-Setup Error And Unsubmitted Repair

R2 封存 initial video ceilings 为 local 2、API 2；local repair ceiling per domain 为 1、total ceiling 4，但第一个 local task 的 batch ceiling 只有 2。两个 local initial submits 后 batch 耗尽；total 4 不会自动重置 batch。当前 committer 没有可 reopen 的 typed batch-review receipt，bare hash 不能恢复计数或开启下一批。

因此 corrected advertising end 和 prompt 已准备，readiness 仍为 BLOCKED_EXECUTION、repair submit 0。证据为 `R2/local-corrected-repair-boundary.json`，并指向 `generation_decision.py`、`generation_feedback.py`、`_state_commit_video.py` 的既有 owner。这个阻挡是 Parent 的预算编排错误，不是用户没有允许修复，也不是 corrected reference 已被模型验证失败。

R2 封存 elapsed limit 90 min、GPU wall limit 60 min；后者没有独立仪表计量，不能把单条 prompt elapsed 当作 GPU 总时长。API paid repair ceiling 为 0。没有扩大 ceiling、重置 count、用新 task ID 绕过旧边界或降低 rubric。`experiment-budget.json` 的配置字段与 `service-restoration.json` 的 actual effect 必须分别读，不把单个配置 flag 当作服务状态。

### Historical Service Restoration

Own queue running / pending 均为空后，停止 task-owned `ai-video-comfyui-d543579794064c1fbfd6e17e47253b99.service` 并 readback inactive。VLLM 首次恢复只有短暂 active，随后因 free memory 20.62 GiB < desired 24.14 GiB、KV cache 6.46 / 6.73 GiB < required 6.75 GiB 退出；不能把早期 PID 当作稳定恢复。

未停止其他 Jianji FFmpeg 任务或改变配置，等待资源释放后原自动重启策略成功。历史最终 `jianji-qwen3-vl.service` 为 active/running、MainPID 2659509、InvocationID `8d0779c188af4e8d985709d42fb723bb`；`GET /health` HTTP 200、available KV cache 7.2 GiB。证据在 `R2/service-restoration.json`，没有 inference submit。这是该时刻的 runtime proof，不代表后续 sandbox 能访问同一宿主机服务。

## Artifact Index And Acceptance State

| Record ID | Exact raw MP4 SHA-256 |
| --- | --- |
| R1-ad-local | `376b5562701c119f6eada740dbede12964dd2a2fbdbd1aefed94d47e4fbb5a68` |
| R1-ad-api | `f29f434df0835df4b275056feb6c2dfce7ee98ce152e6cd07abd71ac7279f03a` |
| R1-drama-api | `270dbec018a5b7ab2bb312c8a11296c29572aa769606afbcd117b027d9de7bd6` |
| R2-ad-local | `ca595380cc932e9b7532c5d6541a1ed2b73d285a8582bb3cdfbebcabf23fe408` |
| R2-ad-api | `8d56ec4f5a33d049f24eef553f1d5d695ee51b03d9e6663bcae8fbad595bcbaf` |
| R2-drama-api | `9a91633aa4a4b4be360a31e823e2741be6cf2e412deb96e15ce7aa4c70b91668` |

R1-drama-local / R2-drama-local 均为 `NO_ARTIFACT:CUDA_OOM`。本次扩写读取六个既存 `review-packet/result.json`，均为 `review_scope=full_contract`、`goal_chain=verified`、`verdict=fail`、`production_acceptance=not_evaluated`。负向 `visual_quality_report check` exit 1 是预期验收结果，不是工具崩溃。

历史每个 fetched MP4 均有 exact-bytes project-local `video-analysis` 和 analyzer binding；R2 三个 muted 浏览器视频播放至 ended / readyState 4，无解码错误。浏览器播放完、抽帧、frame hashes、正式 analyzer proof 是不同层次；不能由程序播放完推导 Parent/用户完整原速观看、实际聆听或 human acceptance。R2 durable attempts 仍在 running / VALIDATE，不把负向 review 自动改成 canonical rejection 或 activation。

本任务没有将六个 raw clips 自动拼成“合格广告”，也没有新的 candidate activation、P6 / Final Acceptance。完整广告链、原包装 source admission、canonical composition 与最终音频进入 timeline 都仍有独立要求。

## Diagnosis — What Is Established And What Is Not

| Concern | Established evidence | Supported conclusion / limit |
| --- | --- | --- |
| Reference count | R1 一个图；R2 两个图；detail / waiting 图没有进入模型 | “多生成图片”不等于“模型消费了多参考”；没有检验 full-reference method |
| Reference compatibility | R2 广告 first/end 持瓶手相反，原左右描述冲突 | submit 前 authoring defect 已证实，Parent 应承担漏检责任；不能全归因模型 |
| Action causality | 剧情末态改善但等待触发仍缺失 | 端点正确不足以保证中间因果；需要对中间行为提供可消费指导并真实验证 |
| Candidate iteration | 每个 domain / route 只提交一个初始候选，repair 又被预算封死 | 现有结果不是充分迭代后的制作上限；不能据一次候选宣布模型整体不行 |
| Local resources | 两次剧情分别 OOM；第二次 novram 仍失败 | 是具体 request / resource path 的执行失败，不是“参考图少”或动作表演 FAIL |
| Picture quality / size | local 广告 416×736，用户画布预览 1280×720 | 尺寸、横竖构图及细节条件不同，不能当作等条件模型排名 |
| Same-content comparison | 测试广告/剧情与用户外星宠物片段题材不同；R1/R2 seeds 也不同 | 没有 controlled A/B，不能量化多图、模型或 prompt 的单独贡献 |
| Audio | 有 AAC stream；无完整听音/voice identity / lip-sync proof | 不能宣称声线、可听性或音画同步通过 |

因此最充分的解释是输入模式、参考职责、参考兼容性、动作组织、规格与迭代过程都有可见差异；现有证据不支持“只因图少”、Seedance 对全部任务必然更强、local H3 普遍不可用或改一个参数即可修好的结论。进一步归因必须隔离变量，完整任务则必须保留用户原目标。

## Jimeng Canvas Inspection

### Canvas Identity And Observed Scope

URL：`https://jimeng.jianying.com/ai-tool/ai-canvas/f0ed223b-090e-4ed6-b394-283f8b7dbd07?enter_from=project_list&from_page=create`；标题 `《零号档案》2资产+重置片段`。用户完成登录后，gstack 复用实际 Chrome profile 的即梦域登录态。未导出 cookie、secret 或 signed media URL。

R3 inventory 为 296 nodes：image 172、video 66、group 25、text 24、audio 8、timeline 1；edges 162。浏览前后总数不变。只选择节点、打开参考图/代表视频、preview/seek，没有编辑文字、重连节点、点击生成或发布。

查看范围为画布总览、四个文字模板、一个完整参考图及代表视频预览；不是逐项检查 296 nodes，也不是看完全部 generation history。四个文字节点为：

| Node | Observed method |
| --- | --- |
| `node_9sznptmnrz` | 分镜图素材按人物身份、服装道具、机位构图动作、场景光线分工；单图表达一个关键瞬间 |
| `node_qw4v1w4jnf` | 视频组织为整段概述、全局拍摄规则、时间轴动作、常见错误；动作有准备、发起、接触、受力和反馈 |
| `node_5d3v7f72da` | 锁定资产 → 压缩整段逻辑 → 统一拍摄规则 → 按时间执行 → 封堵模型常见错误 |
| `node_5tf55px00d` | 用户自己的版权 authoring policy；本记录不将它升级为项目规范或法律判断 |

### Selected Video And UI Parameters

选择 `node_bq6wajb5xe` / `视频 10 (17)` 后，current composer 为 Seedance 2.5、全能参考、17 s、16:9、720P，三个 image chips 加 `COCO声线` 7 s，文字 6326 characters。history viewer 显示 15 results；主预览实测 17.056009 s、1280×720、readyState 4。

current composer 不是 exact historical submit receipt：其文字与七段时间轴截止 15 s，但 control 为 17 s；历史主视频可能采用不同 revision / options。15 results 也不能推导 15 次付费 submit 或单一参数的成功率。

完整参考图可见高大黑外套/透明头部诺萨、较小 COCO、外星宠物、木质收容处与窗侧自然光；代表视频 8 s 的确认截图可见同类角色/空间互动。这些 observations 支持制作方法对照，不签发整片 identity / continuity / quality PASS。

### Capture Integrity And Limits

| R3 artifact | SHA-256 |
| --- | --- |
| `node-inventory.json` | `fe6ba7bdcb8932773c11b5a7df1ae8eeb45897c95a13327328eb142cc9069f92` |
| `selected-texts.json` | `4477d7081c9aa4ddb6db25984afedec33cc93c76afcc16d97a0f8e0741ee2a2f` |
| `selected-video-ui.json` | `780922a204ca5ea0f126b4fea4c074dc517e229f971119c6a8e098693dcd66a9` |
| `video10-confirmed-preview.png` | `4d7bccfb8e693292699e3bece14b9a1603f034c32ced7eea32470b54e9643458` |

本次扩写从实际 bytes 重算以上四项，与既有记录一致。早期 `video10-2s.png` / `video10-8s.png` / `video10-13s.png` 的文件名源于 seek target，compositor 有异步滞后，不能当作 exact timestamp；确认截图播放器实际显示 0:08 / 0:17。没有下载并 hash 用户原 MP4，没有完整原速观看或聆听，不能宣称已完成用户片段的完整验收。

## Method Comparison And Parent Responsibility

用户画布展示了明确的角色/场景/参考职责、连续摄影机路线、按时间展开的动作接触及后果，还有声线输入与多个结果的选择界面。Parent 的测试则是首帧或首尾模式，辅助图未接入、首尾兼容性漏检、动作等待链指导不足、仅一次初始候选、repair 预算不可执行，并且规格和内容不对等。

这说明上轮并没有在相同输入方式和制作条件下复现用户的方法。Parent 应先修正这些可定位的制作/编排问题；不能用模型、QA checks、technical PASS 或“已经交了 candidate”解释掉未达目标，也不能为了记录完整而越权重生成。

## Current Capability Matrix

| Path | Images | Reference audio | Reference video | Output duration |
| --- | --- | --- | --- | --- |
| 上轮实际 API：Vidu `viduq3-pro` I2V / start-end | first frame + optional last frame | 无 | 无 | 当前声明 1–16 s |
| 上轮实际 local：stock H3 `minimax_h3_fl2va` | first frame + optional last frame | 无 | 无 | 上轮 sealed profile 为 124–362 frames / 24 fps，约 5.167–15.083 s；遵守帧数网格 |
| 仓库已有 Vidu `viduq3` / `viduq3-turbo` R2V | 最多 7 张 reference images | 无 | 无 | 3–16 s |
| 仓库已有 local H3 `T8 Ref2VA` native Turbo V2 | 最多 9 张 reference images | 最多 3 段 | 最多 3 段 | 当前 sealed profile 固定 124 frames / 24 fps，约 5.167 s |
| 仓库已有 `doubao-seedance-2-5-260628` API | 最多 30 张 reference images | 最多 10 段 | 最多 10 段 | 4–30 s |

当前代码依据为 `src/ai_video/production/{vidu_profile.py,vidu.py,comfy_video.py,comfy_t8_native_turbo_profile.py,comfy_t8_native_turbo_video.py,seedance_capabilities.py,seedance.py}`。上轮 stock H3 的 exact profile 为 `runs/creative-goal-multi-reference-test-20260927-002/advertising/local/production-v5/provider-profiles/a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d.json`。本轮没有确认任何新的 API account access；不能把 adapter 实现说成账号已经可用。

Seedance 2.5 的图片/视频/音频上限也见 [official prompt guide](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh)：视频总时长和音频总时长分别不超过 30 s。Vidu 多参考模式是独立 model/mode，不会因给 `viduq3-pro` 多准备图片而自动启用；Vidu 视频延长也不等于通用动作视频参考。

原生生成音频不等于输入声线参考或可靠复刻声线。参考素材数量上限不保证身份、接触、动作或音画同步质量。当前 Vidu resolve 限制 I2V prompt 为 5000 characters，R2V / extend 为 2000 characters；画布当前 composer 的 6326 characters 不能原样传入该封装。

### Parameter-Level Support And Interpretation

| Canvas concern | Actual current support | Important limit |
| --- | --- | --- |
| 多图分别锁身份、场景、道具、姿态 | stock FL2VA / Vidu q3-pro 的两帧是端点；Vidu R2V / H3 Ref2VA / Seedance 2.5 有独立 reference bindings | 图片职责主要由 authoring / prompt 指定；数量和 ordinal 不自动建立身份、时间或因果 |
| 首尾精确状态 | stock FL2VA 和 q3-pro 可以声明 first / last | H3 Ref2VA 不能同时绑定 first / last roles；两张 reference 不自动等于硬端点 |
| COCO 声线素材 | H3 Ref2VA / Seedance 多模态 reference_audio 路径已有实现 | 上轮视频没有 reference audio；支持输入也不等于声音身份已通过 |
| 视频动作/摄影机参考 | H3 Ref2VA / Seedance 已有 reference_video 输入 | 当前 Vidu q3 R2V 没有此 binding；独立 Vidu extend 不能当作通用运动参考 |
| 17 s | 当前 Seedance 2.5 API duration declaration 可以覆盖 | 当前 q3-pro 最多 16 s，stock H3 上轮 profile 约 15.083 s，selected Ref2VA 固定 5.167 s；未验证其他新 local profile |
| 分辨率与比例 | Vidu 声明 540p / 720p / 1080p；Seedance 2.5 为 480p / 720p / 1080p；stock H3 exact dimensions 受 profile 限制 | 当前 native Ref2VA 固定 1344×768 横屏；不能将“接近 768p”说成用户原视频 exact 1280×720 |
| FPS | 上述 selected capability 均声明 24fps | 当前封装不支持任意改成 25/30/60fps；fixed output contract 和可调控制不是一回事 |
| Seed | Vidu 和 local H3 支持 sealed seed；Seedance 2.5 当前 capability 为 `seed_supported=False` | 同一个数值 seed 跨 model / sampler 不保证相同构图；本次八个 video seeds 也不同 |
| 24–28mm / 机位高度 / 光线方向 | 可进入适用 intent / prompt | 没有通用硬光学、轨迹或几何约束；模型是否执行必须看 exact media |
| 秒级动作、唯一说话人、无 BGM / 字幕 | intent / audio policy / prompt 可表达，并在适用 Gate 中核对 | 保留文字不等于实际表演、时间窗或声音已经成立 |
| `camera_fixed` / negative prompt | 当前 Vidu 和 local H3 声明 `negative_prompt_supported=False`；Seedance `camera_fixed` 只限 legacy T2V profile | 不能把 payload 中存在某字段误读为 Seedance 2.5 或所有模式都支持；locked camera 仍需适用 prompt / evidence |
| 长提示词 | Vidu 当前封装明确有 5000 / 2000 character limit；H3 `/4` 使用三字段 compiler | 不直接粘贴 6326 字画布全文；必须保存原目标、形成适用表达并回查 actual compiled bytes，不能截断要求求通过 |

当前 Seedance adapter 已把 image/media bindings 投影为 `image_url` / `video_url` / `audio_url` 及对应 roles，并输出 `duration`、`resolution`、`ratio`、`generate_audio` 等结构化字段。该事实来自当前源码，不是本轮 live Seedance submit 证明。API model/account access、选定 profile 和 cloud egress readiness 尚未复验，本地任务不能自动切换过去。

## Local Mapping Of The Canvas Method

选择 `workflows/profiles/minimax_h3_t8_ref2va_turbo_native_v2.json`，而不是继续用 stock FL2VA。该 profile 的 content hash 为 `0bb8ebf9688369f89d959d8273a81f73dcc6e02e96c1a20a52110583ace7db9d`，固定 `1344x768`、124 frames、24 fps、4 steps、`dual_clock_euler/native_flow`、native audio 与 CRF 17。

- Ref2VA 中 first/last roles 的 cardinality 均为 0，所有参考素材合计为 1–15 项；不可把它解释成首尾帧之外还能无条件加 9 张图。视频参考每段 2–15 s，音频参考每段最多 15 s；素材格式、bytes 与 identity 仍须按当前 capability 验证。
- 将人物身份/服装、场景光线、关键动作状态、道具细节分别指定参考职责。检查实际 resolved image/media bindings，确认素材确实进入 conditioning；生成或展示更多图片本身不构成输入证据。
- 总体描述、全局拍摄规则、动作时间轴及常见错误进入适用 Shot intent，再由当前 H3 compiler 表达。镜头焦段、角色职责、逐秒动作及接触/受力反馈主要是 prompt guidance，不是保证执行的硬参数。当前 `/4` H3 compiler 使用唯一三字段、单 `[Shot 1]` 与 primary camera motion，不能直接粘贴包含任意多镜头语法的画布全文。
- 当前 Ref2VA profile 不能直接生成画布的 17 s。用户已选择的 COCO/诺萨段明确要求一镜到底、正常实时速度，因此不能采用多 Shot 切镜、压缩全部动作进 5.167 s、快放、重复或插帧冒充完整复刻。需要有 current code / exact profile / runtime evidence 支持的本地长镜头能力；仅改 JSON 时长或复用旧 FL2VA 会改变已选 mode / contract，不能视为本次已验证路径。
- 使用 `load_production_project -> VideoGenerationService -> ProductionStateCommitter` 的既有 seam，fresh exact request / local intent / one-use permit。每个 exact MP4 后显式运行 project-local `video-analysis`，required findings 全 PASS 后才继续下一 Shot。known failure 按有界 local repair 处理，unknown outcome 禁止重复提交；不旁路直接 POST ComfyUI prompt。

## Selected COCO / Nosha Target And Inputs

本节保留旧窗口截至 14:54 +08:00 的 discovery 状态；素材、sealed attempt 和已批准 17 s 的当前事实见文件开头 `Current Supersession`。

用户选择复刻的目标为画布 `f0ed223b-090e-4ed6-b394-283f8b7dbd07` 的 `node_bq6wajb5xe` / `视频 10 (17)`。已保存 `runs/jimeng-canvas-diagnosis-20260928-001/selected-video-ui.json` 中的 current composer 显示三张图片及 `COCO声线` 7 s；图片显示名分别为 `ChatGPTImage2026年9月3日14_01_09`、`ChatGPT Image 2026年5月18日 04_44_48.png (2)`、`ChatGPT Image 2026年5月18日 16_13_13.png (2)`。角色与场景职责应在原图 inspection 后确定，不能仅凭文件名猜测对应关系。

保留目标包括：阳光充足的外星宠物收容处；COCO 明显小于诺萨、始终拿手机且为唯一说话者；继承 COCO 的参考男性声线；诺萨黑色长外套/黑色西装/透明圆柱形头部、不说话；四只外星宠物的功能不可互换；A 被 B 撞落并逃跑，惊动 C 扑上诺萨头部，诺萨失去视线后摇晃并经推车撞翻果篮，水果滚向 D 并被吞吃。摄影机连续沿同一路径跟随上述因果链，不切镜、不慢放、不定格，也不添加其他人物。

这是目标摘要，不是冻结后的 request 或验收证据。current composer 文字写 15 s、control 写 17 s，历史主预览 measured duration 为 17.056009 s；UI 组合不是 exact historical submit receipt。复刻准备必须保留此差异，不能自动降低时长或宣称已精确还原历史参数。

现有诊断目录和 `/tmp/jimeng-*.png` 为 UI screenshots / captures，并非三张原图与原始声线音频。它们不能替代 Asset Registry 的 exact source bytes。当前尚未获得/登记这些原始输入；不得从截图虚构完整角色资产、用新生成图片冒充用户原图，或用 native audio 代替参考声线。

### Character, Pet And Prop Requirements

下表是已保存 composer 的语义摘要，不另建 canonical Character / Scene / Shot owner。恢复实际 authoring 时必须对照原始 reference bytes；缺图不能仅凭文字声明身份已经锁定。

| Entity | Required visible / audible identity | Function and prohibited substitution |
| --- | --- | --- |
| COCO | 比诺萨明显小，拿手机，开心跑近；唯一说话者，参考男性声线 | 不是站桩播报；只能改变跑动气息/语气，不改声纹、性别感或音高中枢；台词一次、逐字、不重复 |
| Nosha / 诺萨 | 高大，黑色长外套和黑色西装，透明圆柱形头部容器 | 不开口、不做说话口型；被 C 吸附后失去视线，受冲力连续摇晃并撞动推车 |
| Pet A | 灰蓝短绒、非对称水滴软体，四颗琥珀小眼、花瓣软口、半透明扇形耳膜、六只短吸盘足、细长平衡尾 | 开场被摄影机跟随；被 B 撞落、翻滚逃跑、掠过 C / 碰落容器；不能替代 C 扑脸 |
| Pet B | 青紫鼓囊软体、湿润无甲壳、连续腹部肌肉褶、两侧柔软平衡鳍 | 只从侧面撞落 A，贴平台收缩滑走；不得变成甲虫、蜈蚣、蜘蛛、蟑螂或其他地球昆虫 |
| Pet C | 浅褐圆盘软体、中央吸盘口、六瓣短肉肢；无 A 的长尾或扇形耳膜 | 从开场在诺萨脚边活动；受 A 掠过/容器碰撞惊吓后立即扑上透明头部，接触后吸附 |
| Pet D | 拳头大小三角软壳、不规则透气孔、三根眼柄、横向柔软口器、五只细弯足 | 开场隐藏于低货架/木箱间，末段观察并吞吃水果；不得变成鼠、猫、狗或昆虫 |
| Alien fruit | 拳头大小、浅橙半透明纤维皮、六条螺旋果瓣围绕中央凹口，无包装/文字 | 滚出果篮并被 D 吃掉；不变成苹果、橘子、梨等地球水果 |
| Phone / cart / basket / container | 手机始终归 COCO；推车、果篮和轻型容器承担可见因果 | 不显示可读手机文字/数字/UI；不能靠突然出现、瞬移或切镜补事件 |

环境固定为阳光充足的外星宠物收容处，保持木质空间、窗侧自然光及原参考的角色比例。可辨识人物只有 COCO / 诺萨，无额外机器人、第三人、工作人员、路人或背景人影。当前文字存在用“她”指 COCO、同时要求男性声线的表述；正式冻结应以原参考身份和已明确的声音要求为准，不从代词猜测或改写角色资产。

### Authored Action Timeline

这是 current composer 的 15 s authoring timeline，各行都是同一长镜头的阶段，不是允许切镜的分镜列表。17 s control 与 17.056009 s 主预览的差异仍须处理，不能直接把此表当作已冻结的 17 s request。

| Authored interval | Visible action | Causal / continuity obligation |
| --- | --- | --- |
| 0.0–1.6 s | A 在高处活动、观察镜头；B 从侧面撞中 A | 有接触点，A 吸盘脱离后坠落；B 保持非虫形软体并离开 |
| 1.6–3.5 s | 摄影机连续下降跟随 A，A 落地翻正并逃跑 | 不切镜、不瞬移；持续保留落地、受力与恢复后的运动 |
| 3.5–7.8 s | 同一低位弧线带出 COCO，COCO 拿手机跑向诺萨并说话 | COCO 从后景自然入画，避开 A 后短暂并行；不是站立旁白 |
| 7.8–9.5 s | COCO 靠近诺萨，A 抵达诺萨脚边并掠过 C，尾部碰落容器 | 触发物和 C 的位置可见，动作顺序和同一空间可追踪 |
| 9.5–11.1 s | C 受惊、蹬地扑脸、接触吸附，诺萨直接失衡摇晃 | 无停顿的连续动作浪潮；C 不悬停/摆姿蓄力，诺萨不先站稳展示再摇晃 |
| 11.1–12.8 s | 诺萨连续踉跄，撞动推车，推车撞翻果篮 | 显示力的传递和可见后果；水果不能无因出现或凭空滚动 |
| 12.8–15.0 s | 摄影机沿原方向降低，跟随水果到货架下，D 确认周围后吞吃 | D 的动作不改给其他宠物；末帧仍在咀嚼/吞咽，不定格收尾 |

完整因果链为 A 观察 → B 撞落 A → A 落地逃跑 → 摄影机带出 COCO → COCO 跑近说话 → A 掠过 C / 碰落容器 → C 受惊扑脸 → 诺萨失衡 → 推车撞翻果篮 → 水果滚出 → D 吞吃。上一个事件应能解释下一个事件，不能只生成相似角色和几个孤立动作。

### Camera And Sound Requirements

摄影机初始在高处平台旁约 1.2 m；A 坠落时沿左前斜线降到约 40 cm；沿中央工作区外缘持续逆时针低位弧线，COCO 从后景进入并并行；到诺萨脚边后在继续前进时向上倾斜追随 C；果篮倾倒后沿原方向降到约 15 cm，跟随水果进入低货架下方。24–28mm 广角、足够景深，用距离、主体运动和连续对焦自然传递视觉重心。

禁止摄影机瞬移、跳轴、突然换到人物正面、另一组构图、硬切/隐藏切镜/黑场；也不能用人物、宠物、货架、阴影、景深或运动模糊遮掩切镜。第一帧 A 已活动，末帧 D 仍咀嚼；正常实时速度，无静止帧、慢动作、停滞或定格尾帧。当前 H3 compiler 只有一个 primary-camera-motion contract，具体连续路线如何完整表达必须回查实际 compiled prompt，没有专用数值轨迹槽或执行保证。

COCO 的原文台词与完整 reference expression 保留在 `R3/selected-video-ui.json`，语义为新一集千万播放、观众好奇制作方法；正式 authoring 必须消费原文，不能用本摘要重新创作台词。只有 COCO 说话，诺萨、宠物、背景及画外无可辨识人声。允许宠物叫声、软体落地、吸盘足拍地、脚步、衣物摩擦、推车/果篮碰撞、水果滚动、咀嚼吞咽与自然室内声。无 BGM、字幕、旁白、UI、台词转写、标识、水印或手机可读文字。声线 reference 是输入身份，native AAC stream 是输出存在，两者不能互相替代。

### Replication Is Not Yet A Sealed Attempt

目前没有这段 COCO/诺萨的 registered assets、approved Character/Scene/Shot artifacts、goal binding、request preview、local intent、one-use permit 或 fetch receipt。已保存的 UI composer 只能作为 authoring discovery source。既有广告/剧情 projects 不能重命名冒充本次新目标；原始 reference bytes 取得后，必须创建隔离的 development project 并沿标准 owners 处理。

若只做 5.167 s reference smoke，将是另一个较小目标，不能称完整复刻；用户没有选择这个替代结果。当前不通过切镜拼接、缩短动作、换 paid API 或悄悄改 sealed profile 来消除阻挡。

## Verified Preflight And Blocker

本节为旧 sandbox 窗口的历史检查；不可将其 device / bus / endpoint / Kimi / CodeGraph 不可用推断为当前宿主机状态。本次实际恢复和新的 terminal OOM 见文件开头 `Current Supersession`。

2026-09-28 14:48–14:54 +08:00，本地执行准备窗口的实际检查结果如下。本次记录扩写没有重跑 GPU、服务或 browser preflight；这些是该时段的 observed evidence，不是新的当前硬件健康结论。

| Check | Current evidence / limit |
| --- | --- |
| Standard profile loading | `load_t8_native_turbo_execution_profile(..., artifact_root=repo)` 成功；验证 selected workflow / binding bytes 与 profile 的 hashes，并执行 workflow validation |
| Capability projection | `t8_native_turbo_capabilities()` 确认 images 9 / videos 3 / audio 3、group 1–15 与 124 / 24 固定输出 |
| Installed model visibility | Ref2VA base 文件可读，stat size 为 34038894550 bytes；converted LoRA 为 779858632 bytes；本轮未重算完整模型 SHA-256，不冒充完整 preflight |
| GPU device access | `/dev/nvidia0`、`/dev/nvidiactl`、`/dev/nvidia-uvm` 均不可见；`nvidia-smi` exit 1，无法连接 NVIDIA driver |
| Host driver evidence | `/proc/driver/nvidia/version` 可读并显示 `580.178.04`；不能因沙箱设备不可见断言宿主机驱动未安装或显卡损坏 |
| Local endpoint | `curl --max-time 4 http://127.0.0.1:8188/system_stats` exit 7，无法连接当前环境的 loopback endpoint |
| Service control | `systemctl --user` 及 repository `comfyui_supervisor.py status` 均返回 `Failed to connect to bus: No medium found` |
| Authenticated canvas access | 按用户此前指定的 gstack `browse status` 尝试连接；daemon 启动无法绑定 localhost，exit 1。未清理用户浏览器或登录态，未下载新的画布素材 |
| Managed Kimi route | doctor 为 `BLOCKED_CAPABILITY` / `adversarial_containment_not_qualified` / `SANDBOX_IMAGE_UNAVAILABLE`；未发送 live Kimi request，不绕过 containment |
| CodeGraph | tool 返回 approval required，而 current approval policy 为 `never`；本轮未获得关系图证据，不声称已完成结构化 graph verification |

因此本轮状态为 `LOCAL_GENERATION_BLOCKED_BEFORE_SUBMIT`：新 local submit count = 0，remote / paid submit count = 0，没有新 MP4、Media Gate verdict 或 activation。没有停止/重启宿主机 VLLM、修改 ComfyUI 配置、安装依赖或绕过 sandbox。恢复执行环境需要访问本机 NVIDIA devices、user-systemd 与 selected loopback ComfyUI endpoint，然后重新运行 exact runtime preflight；只启动服务不能解决设备不可见问题。恢复完整复刻还需要原始三图/声线与能表达完整一镜到底时长的 selected local capability；不能仅恢复服务就认定这些条件已关闭。

`docs/record_for_agent/2026-08-22-t8-native-turbo-v2-gate-closure.md` 保存了该 Ref2VA lane 的历史技术 smoke；这不是当前环境的可运行证明，也不是本任务的新生成结果。

## Recovery And Continuation Conditions

本节为旧窗口的继续条件清单。环境、exact served references 与新 duration contract 的推进及当前 budget / sampler blocker，已由文件开头 `Current Supersession` 替代；以下保留原 chronology。

下面是继续任务的必要条件，不是已完成的动作，也不授权绕过 contracts：

1. **恢复真实执行环境。** 能访问本机 NVIDIA device nodes、user-systemd bus、task-selected loopback ComfyUI；核对现有 VLLM/其他任务 ownership 与 queue，不能从旧 PID 或上一轮 health 200 猜测当前状态。不要先改模型参数来掩盖设备或 namespace 不可见。
2. **取得原始输入。** 通过用户已登录画布合法取得三张原 PNG 与 COCO 声线 audio；保存 exact bytes / MIME / dimensions / duration / hash / source provenance，逐图确认职责，再由 Asset Registry owner 登记。不以 UI screenshot 或新生成近似图冒充原资产。
3. **关闭时长与能力差异。** 保留完整长镜头及正常速度，核对 15 s authoring / 17 s control / 17.056009 s 预览，形成一致的 exact target。选择已有、可验证满足该目标的 local capability；若需要新 profile / Provider contract，实现与验证必须走适用 approval / spec / plan，不仅编辑 literals 求过 Gate。
4. **冻结内容。** 形成符合 canonical owners 的 Character / Scene / Shot、角色/参考职责、完整因果与 camera/audio requirements；不删除难演动作。复核 raw source、coverage、contract、goal binding 及实际 compiled prompt，没有身份、声线、手持道具、timeline 或 reference-role 冲突。
5. **封存有界执行。** 在本次 scope 下明确 initial / repair / batch / total / elapsed / GPU limits，使必需 repair 在既有 public seam 上实际可执行；不要重复 R1/R2 的 batch setup 错误，不继承或改写已消耗的旧 permit/count。
6. **逐项实证。** 通过 `VideoGenerationService`、exact local intent、committer-issued permit、selected adapter submit/status/fetch；MP4 exact hash 后显式调用 project-local `video-analysis`，核对身份/宠物职责、接触与力的传递、完整连续 camera、时长/速度、原文对白/唯一说话者/声线与 audibility、禁字幕/BGM/额外人物及结尾持续动作。任何缺证为 NOT_EVALUATED，不凭总分代替。
7. **观看、修复和交付。** 完整 1.0x 观看并真实聆听；known local failure 在封存 budget 和可归因变量内 repair，evidence-only 问题先补证，unknown outcome 停止恢复。只在目标真正满足后交付；raw candidate、technical PASS 和当前文件名不自动产生 activation、P6 或用户 acceptance。

当前的三个独立阻挡为执行环境、原始 references、完整时长 capability。只恢复 localhost、只增加图片、只降低分辨率或只取得声音都不能关闭全部条件；也没有证据证明必须下载新的权重或重新实现整个生产系统。

## Verification Receipts And Publication History

| Historical checkpoint | Exact scope / purpose | Receipt |
| --- | --- | --- |
| `ce6ec9b..6019f39` | Creative-goal M1–M4 engineering；12 executed checks PASS，covered check 同 run closure | `.agent/harness/runs/creative-goal-implementation-20260927-01/receipt.json` |
| `fac1070..8f68403` | 真实 report mobile wrap 修复；7 checks PASS | `.agent/harness/runs/creative-real-report-wrap-commit-20260927-02/receipt.json` |
| `42cc1ef..0fc4bcb` | 首尾 retest 文档及真实 service restoration 记录 closure | `.agent/harness/runs/creative-first-last-record-20260928-02/receipt.json` |
| `0fc4bcb..dfb1162` | Jimeng canvas method comparison 文档 | `.agent/harness/runs/jimeng-canvas-method-comparison-20260928-01/receipt.json` |

本次扩写直接读取以上 receipts 的 stored `status=passed` 与 exact base/head；不是重跑 Harness、重新验证其所有 integrity 字段或宣称这些旧 receipts 覆盖当前 untracked 文件。历史 freshness 属于各自 checkpoint，当前新记录仍需要自身 exact-snapshot verification。

相关历史 local commits 为 `949a05a`（goal bindings）、`beb8112`（effective results）、`6019f39`（packet /3 和 completion practice）、`fac1070`（implementation evidence closure）、`8f68403`（mobile report）、`42cc1ef`（first real tests）、`1b5a5ff`（first/last retests）、`0fc4bcb`（stable VLLM restoration）、`dfb1162`（canvas comparison）。这些 local history 不代表 push / origin / release。当前 unrelated `.codex/config.toml` 的 7 行 dirty change 始终未 stage 或 commit。

## Record Expansion Verification

本节及下一节记录旧窗口扩写时的验证与 `.git` 只读阻挡，不覆盖本次 continuation。当前 local implementation commit、直接 policy 验证、真实失败和服务收尾见开头更新。

本次扩写只修改本文件；读到的 code / plans / prior records / media sidecars / JSON evidence 没有改写。核对八份 `resolved.json` 的 model / seed / effective output / image bindings / zero media bindings、六个 report results、六张 reference PNG hashes、四份 R3 capture hashes与四份历史 Harness scopes。Parent 又从实际 bytes 重算六个既存 raw MP4 SHA-256，全部与上方 index / content-addressed filenames 相符；没有重新解码、分析或生成视频，hash 匹配只证明这些文件身份。

Native read-only mapper 独立核对两轮六份 media sidecars 的路径/hash/bytes，并确认首轮 API drama 是恢复既有 task、两次 local drama 没有 MP4；其未重算 MP4 或运行 analyzer，不能补出新的 quality / human proof。

历史受管 Kimi 调查/审查 receipts 在对应 records 中保留。当前执行窗口 doctor 明确 BLOCKED_CAPABILITY，未绕过 containment；本次 docs expansion 没有再次运行 live Kimi。CodeGraph 当前 route 被 approval policy `never` 阻挡，记录不得声称新增结构图验证。Parent 拥有最终事实核对、diff 和完成判断，mapper 不拥有 acceptance。

完成检查使用 documentation contract / whitespace / local link 和既存 artifact bytes 核对，不追加业务 media、Provider、GPU、网络或整套 tests 来装饰记录。20 个一级内容 sections 无重复标题、6 个 local Markdown references 均可解析；没有 conflict markers 或 trailing whitespace。最新结果见下节；当前 `.git` read-only 的 checkpoint blocker 未解除。

## Verification, Learning And Publication

`record-ai-video-session` 在真实 blocker checkpoint 及本次完整记录请求下执行；`distill-ai-video-learning` outcome 为 `no_candidate`。此次汇总重新引用已有八次 video attempts，不新增独立媒体、controlled comparison 或 existing-claim material update；不能因为多个记录/表格重复引用同一失败就制造额外独立证据。原两个实验 records 的 eligible Evidence Index 保留；本综合记录为 `session_summary / ineligible`，不产生新的模型质量 claim，也不覆盖既有经验结论。

local execution 准备时 Agent Memory 返回 fresh run-summary 与 stale experience fragments；完整记录扩写时 focused query 返回 tagged stale 的两份实验记录，已重开原文和当前 files。stale refresh queue 因 `.git` read-only 失败，未重建索引；不保证本综合记录已进入 RAG。记录之外的 unrelated `.codex/config.toml` 保持不动。

简版与本次完整版均实际运行 `python -m scripts.docs_contract_gate check`，exit 0，输出 `Documentation contract gate passed.`；对新文件运行 `git diff --no-index --check /dev/null <record>` 无 whitespace diagnostics。此前对唯一 task-owned 文档执行 exact-path `git add` 返回 exit 128：无法创建 `.git/index.lock`，`Read-only file system`。权限未解除，因此文档保留为 untracked，未 commit，也没有本轮 exact-snapshot Harness receipt；不以历史 passing receipt 冒充本轮验证，不移动 Git metadata 绕过权限。记录完整性检查完成、生成 blocked、publication 未完成分别报告。无 push / release / P6 / Final Acceptance。

原 `capture_request_id=ai-video-record-26b95842b89fe19c` 已在 implementation checkpoint ACKED `recorded / no_candidate`，两份实验与画布记录均保留该事实。本次主动评估不重复 acknowledge 同一 ID，也不伪造新的 capture request。
