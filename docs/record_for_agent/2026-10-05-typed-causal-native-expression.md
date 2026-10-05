---
record_kind: architecture_implementation
topic_id: verified-causal-opening-native-expression
learning_eligibility: ineligible
---

# Verified Causal Opening Native Expression Record

Date: 2026-10-05

## Baseline And Scope

fetch后实测 `HEAD == origin/main == 4cc1b55d81c881711175c71fa18a1f4d7326c92f`，初始main clean。
仅 bounded architecture/implementation/offline proof；0真实Video Provider credential lookup、paid
consumption、POST、poll、fetch或媒体生成。临时fixture backend/permit/QA不代表真实effect或资格。
详见 [research](../research/2026-10-05-typed-causal-native-expression.md)、
[spec](../superpowers/specs/2026-10-05-typed-causal-native-expression.md)、
[plan](../superpowers/plans/2026-10-05-typed-causal-native-expression.md)。

## Root Cause And Chosen Seam

旧shared compiler只有requirement/voice route；bound request没有causal preimage。
事实唯一owner是 route binding → policy v2 → causal_state_changes。
Parent先研究源码和CodeGraph callers，再self-review spec/plan，后实现。
新seam是 `_sequence_source.build_verified_causal_opening_expression` 签发的 process-local
`VerifiedCausalOpeningExpression`：重开 current Project、accepted adjacent source/close PASS、
policy/binding、exact target/intent、完整两列hash、selection lineage、既有final Planner preimage
及authoring seal。`destination_planning_request`仅扩展保存到same-stack；无新durable schema。
weak issuance registry独立保存原始seal，拒绝construction/copy/原对象及nested facts重封冒充owner。
grammar每次检查payload与req/bound
seal、重新计算两列hash，仅确定性表达current `target_open`；adapter只传输入、不读policy编facts。
canonical preparation/current recompile重签发，caller自报hash control coverage必须再次重编译。
opening digest仅从verified临时recipe lexical projection移除，原recipe/QA seal和其他文本义务不变。

## Offline Verification

- 初次typed-expression suite：22 PASS；十维facts、determinism、HardCut/EXACT_TERMINAL、无证hash/
  TYPED_REF、target/intent/policy/binding/preimage mismatch、missing/duplicate/CARRY、resealed
  mismatch、issuer/copy tamper、current close拒绝、recipe seal保留、自报coverage拒绝。
- `TYPED_TEXT` 与 baseline compiler逐字节比较，golden prompt SHA-256
  `79551dcfe71dd0e72005c4c65cc38dea3bed5daf73cfcdd3dbe3cc05f4fba209`。
- METASO normal Ref2VA body SHA-256
  `4e78bc70637ffdba99da736288776f5529fdfc2dc6dcd2da11af32c6ef849cbc`；FULL soft Ref2VA gate不变。
- remote adapters/Vidu rich/subject/voice regression：519 PASS；sequence：55 PASS；
  execution/feedback/provider wiring/service：109 PASS。
- 原RED在有效source/Planner/Router fixture之后因新owner入口不存在而失败；同一语义路径修复后GREEN。
  test fixture输入、枚举、typed serialization问题均在tests修正。

METASO positive fixture使用标准Project/Manifest/committer；source backend/compiler/human-close
评价均明示scripted double。复用existing six-second audiovisual MP4，真实probe核对bytes和AV
metadata；512×288初始PNG经canonical project/Registry/dependency commit，C2经既有image lifecycle。
FULL/HARD_CUT/C2 first-frame Router SELECTED，真实METASO adapter compile/resolve/preview/native body
成功，base64还原exact Registry PNG，prompt无digest。recipe coverage也通过。credential/transport
均为会立即失败的sentinel；不证明真实 source acceptance或观看质量。

## Harness And Independent Evidence

`make harness-inspect`已运行，task Architecture Gate PASS。最初policy将本slice路由至full tests；
首轮policy audit因新路径未注册而STOP，随后补existing category/argv及full suite路由。
用户另行授权的Harness任务已细化最终选集；本任务按其最终policy重新验证，不刷新architecture baseline。
实际outcome由fresh canonical receipt证明，
本文不预签Harness/reviewer verdict。最终receipt与同snapshot双独立read-only review在交付报告列出。
首轮native review的TCNE-001/002由Parent在canonical fixture独立复现：grammar标记冒充subject
compiler以及原对象/nested facts重封；三项新增regression先RED。修正selected compiler例外及
独立original issuance seal registry，修正后重新验证与审查。首轮Kimi final review
`8be1d504-4836-4ac1-8dab-305f141e142f`在14次wire requests后connection failure，
receipt为OUTCOME_UNKNOWN且无terminal report；artifact hashes已核验，不采用partial output。
修正后typed-expression suite为24 PASS（103.27s）；包含原对象/nested facts重封及非subject
compiler冒报grammar拒绝。此前22项语义、TYPED_TEXT与Ref2VA golden全部保留。
修正后shared compiler/Vidu subject/voice focused regression为115 PASS（121.42s），
task Architecture Gate重新PASS；旧snapshot Harness结果不作为修正后的最终receipt。
两次Kimi final attempts均为CONNECTION_ERROR/RESPONSE_BODY且无terminal报告：第二次
`5ce7f138-c31c-4766-b945-aa93c3c92fd3`为3 requests/482.94s；两轮artifact hashes均核验。
按SUBAGENTS Repeated Kimi Failure Fallback转只读native `reviewer_xhigh`，
agent `/root/fallback_review`，替换失败Kimi reviewer；不冒称native具有Docker route proof。
同snapshot另一独立native `/root/final_review`已复核TCNE-001/002，无remaining finding。
fallback review只指出TCNE-FR-001 non-blocking canonical接线coverage gap；现新增standard
`.prepare()`、temporary Project request persist、effect前recompile exact equality及source/policy
bytes drift阻断测试。恢复任一旧接线的mutation分别2 FAIL；无effects的正向接线2 PASS。
fixture为target单独author新QA rubric，source旧close criterion/evaluation artifacts保持immutable。
首轮full Harness `final-2`在1800s约37%/约5.9k tests处timed_out；stdout有5个F失败标记。
`final-3`因新增coverage superseded而停止，stdout有4个F；保留原receipts/logs。
最终复审TCNE-003纠正此前只检查receipt/tail而遗漏失败信号的记录。旧summary未完成，
失败原因必须由完整结果及focused reproduction调查，不把timeout扩展当作测试修复。
full_tests有限timeout为7200s；不减检查、不改通过标准、不刷新baseline、无Provider预算变更。
Parent按旧progress/collection定位并focused重现：T10 import-boundary是真实task regression，
新final Planner reopen误放到exception之外；现移回既有`require_sequence_source`，不放宽guard。
另3个Agent Memory失败因旧shell interpreter的chromadb0.5.23不满足pyproject>=1.0,<2，
并恰好等于测试使用的stale-version sentinel。改用repo已有`.venv`/chromadb1.5.9，
无dependency安装或contract修改。兼容环境focused 4项failure repro全部PASS（3.72s）；
单独local calibration进程收到SIGTERM而未完成，原因未确认，不视为PASS，final full suite重新验证。
`final-4`因owner fix/environment correction被supersede，原receipt保留，不冒称green。
原native final-review已3轮；因新增真实T10修复，自主封存额外1轮exact-snapshot复核预算，
不重置历史轮次；fallback reviewer使用其第3轮，两个独立reviewer仍同snapshot。
修正后`.venv`中的typed-expression + sequence suite共81 PASS（558.47s），
T10 import-boundary及task Architecture Gate PASS。并行writer在本任务过程中另行提交
`d3cdc4cd708e72fd106d23a1477bca0b277648b0` research docs；paths与本任务完全不相交，
保留其commit，不将其diff当作本任务实现或额外编辑。
最终typed-expression suite为26 PASS（106.23s），task Architecture Gate PASS；
standard wiring mutation日志及两轮Kimi失败/fallback routing保存在上述ignored evidence目录。
Targeted logs：ignored `runs/typed-causal-native-expression-20261005-001/`。
`final-5`完整结束：5875 PASS、1 FAIL、5 SKIP，4327.66s；唯一失败是
`test_local_multilingual_project_corpus_answerability_calibration` 的负向query误命中旧record。
验证期间另一Harness任务修改共享policy及staged scope，receipt同时为workspace_stable=false；
该receipt不可作为最终验收。用户明确指定Harness任务先收尾、本任务随后重验并提交。
Parent只读归档 `4cc1b55` 的368个docs文件，以test-only plugin仅替换原测试的docs/corpus输入，
使用未改的测试body、真实本地embedding/Chroma index；baseline复现同一负向query、同一旧record
误命中：1 FAIL、496.83s。memory源码和测试相对baseline无diff；不修改memory阈值或掩盖FAIL。
JUnit、stdout及hash审计保存于ignored evidence目录的`baseline-calibration-audit.json`。
Harness任务最终冻结tree `fc6143a17a0c183685b9f4bdcacda6eb68000c69` 的选集receipt为
18 checks PASS、2由同run PASS覆盖，workspace_stable=true；其双独立native review及Parent裁决
完成、无remaining finding（两次Kimi failure后受管fallback）。这证明其owned Harness改动，
不代替本任务的final acceptance。其policy引用本任务未提交测试，publication仍有producer依赖。
本任务接续时24个owned paths均与原reviewed tree `06a1fa4f5feaf039478bf45812fdc20d191e04f9`
逐文件bytes一致；这里只补历史结果。共享policy由Harness任务owner接管，不夹带其文件提交。
`final-6`开始后，并发governance record提交和Harness最终record staging再次改变HEAD/scope；
Parent仅停止本run exact isolated pytest process group，保留failed receipt及非PASS历史。
Harness任务已完成审查与本地交付，仅publication等待本任务依赖；现基于其最终31-path index
启动`typed-causal-native-expression-20261005-final-7`，不编辑其owned paths；结果以实际receipt为准。
AOCI稳定维护评估返回 `stopped/blocked`、无候选/正式语义写入：6个managed stale对象及65个
跨历史observed pending；当前工具要求全scope review/ack，不能在本bounded task中猜签。
AOCI仍advisory stale，不宣称完整current-system cognition；source/code/tests验证独立有效。
受管Kimi research第一invocation `1d372f40-1e4b-4d73-b1ac-8ed40e9d0753` connection error/
OUTCOME_UNKNOWN，未用partial report；缩小三文件的新任务
`fcb8c955-43cd-42fc-bb1e-64d4498da667` receipt/Read/artifact hashes核验，Parent核对结论。
工程研究不属于Video Provider effect或Product acceptance。

## Final Checkpoint And Publication

`typed-causal-native-expression-20261005-final-7` 已结束为 `passed`：18 checks PASS，
2 checks由同run实际PASS覆盖；`workspace_stable=true`。receipt为
`.agent/harness/runs/typed-causal-native-expression-20261005-final-7/receipt.json`。
提交前scope/policy/artifact integrity、freshness、snapshot、coverage与cleanup核验全部true；
原receipt保持immutable，提交后的scope变化不冒称它仍是current staged freshness。
最终Provider 898 PASS、Vidu 194 PASS、voice routing 47 PASS；新typed-expression 26项
及sequence 55项的focused证据保持。旧full calibration FAIL与baseline复现未改判。

implementation commit `ecb4aa1ee2c7b08ccc7700037d8b978a28fb4f5b` 仅含本任务24 paths，
逐文件证明committed blobs等于verified staged snapshot中的owned blobs，已正常push main；
发布后实测HEAD与origin/main均为该commit。另7个Harness staged paths及其bytes完整保留，
不属于本任务提交。ignored `final-7-publication-proof.json`保存receipt hash及publication核验。
本节是之后的documentation-only checkpoint，不能将implementation发布状态冒充本节已发布。

本次hook `ai-video-record-684b2163295de9be` 复用并更新同一primary record，不创建重复记录。
automatic learning evaluation仍为`no_candidate`：本链是离线工程修复，没有独立real media
实验或controlled quality比较；不建Learning Claim、不修改adoption target、不刷新RAG。
记录阶段不触发Provider、media、network或新tests；仅检查owned diff并做本地record checkpoint。

## Changed Paths

production：`_remote_video_native_prompt.py`、`_causal_prompt_context.py`、`_sequence_source.py`、
`video_compiler.py`、`generation_feedback.py`、`video_generation.py`、`metaso_h3.py`、`minimax_h3.py`、
`minimax_hailuo.py`、`seedance.py`、`vidu.py`、`voice_routing.py`、`_vidu_prompt.py`、`_vidu_subjects.py`。
planning：`sequence_continuity.py`。tests：`test_typed_causal_native_expression.py`、
`test_planning_sequence_continuity.py`。docs：research/spec/plan、本record、runtime baseline、
primary contract matrix、前frame-capability record的有界supersession notice、Harness新路径注册。

## Remaining Limits And Historical Truth

previous close/current open/current close严格分离。pairwise facts不证明current-close hash；缺独立
authored owner继续unsupported，即使digest相等。既有sequence fixture current close仍hash、未改。
cross-stack prior无证hash seed仍unsupported；Vidu named-subject FULL/R2V仍缺frame conditioning。
Provider既有length/geometry/audio限制仍适用。普通hash/TYPED_REF继续fail closed。
因此fresh accepted source不能自动视为real A/B唯一blocker；还须核对真实target close及prior selection。
真实媒体质量/A-B均NOT_EVALUATED；旧S02/S03、FAIL、edited evidence未改。

## Learning Evaluation

按 `record-ai-video-session` 建stable工程record，并评估 `distill-ai-video-learning`：
`no_candidate`。离线contract regression不是独立real media experiment或controlled quality比较；
不创建Learning Claim、不修改Skill/Policy/Gate、不请求adoption。
