---
record_kind: architecture_implementation
topic_id: drama-m6-d-shot-01-request-readiness
learning_eligibility: ineligible
---

# Drama M6-D Shot 01 Request Readiness Gate Stop Record

Date: 2026-08-29

## Current First-Submit V2 Source Drift Stop — 2026-09-05

用户明确要求运行同一canonical Shot 01。本窗口完成新的versioned invocation接线与封存，但在消费invocation前
发现unrelated Product source变化；当前仍为`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`，没有生成媒体。
本节取代下方V9之后“立即执行new invocation”的current next action；V9及全部旧evidence bytes保持不变。

- `0df8b5a4a507427872c3a2942ccd54cb962d0e5a`只新增`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_first_submit_v2.py`，
  SHA `71d4d4ed13a563333ce62220cd55cc6880bd533148264207ef8d1d146de3738e`。唯一Product effect owner仍为
  `VideoGenerationService + ProductionStateCommitter`；formal v3 reopen、current graph/request、source/audio、
  runtime/supervisor、creative lineage与queue在start、intent和exact POST前重验。旧v1 driver未重放或修改。
- `aa730c8d096b4d915dc559c7d4977cf26eff2385`封存`docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v2.accepted.json`，
  SHA `c4f256e30df40b0e158476a3ae74c27de0c6f1158d98c3c7974da39919dcb979`。预算为1 submit、1 GPU job、
  3600s、0 retry、0 remote egress；这是orchestration acceptance，不是permit、media或HUMAN acceptance。
- 新GET-only capture v6为`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-source-binding-preflight-v6.json`，
  SHA `373fee5c3f2f66f361d25e4fb92310cbf480e2e58e3677c39705acdc34282b6a`，exact source固定为`0df8b5a`。
  Capture时runtime `MATCH`、supervisor与V9相同、queue empty，request `87c98a1f...`、prompt `e6cc7411...`与
  `GENERATED + KEEP`未变。完整capture嵌入tracked invocation seal，canonical re-encode与raw bytes完全相同。
- Parent首次GET-only启动漏设`PYTHONPATH=src`，v4在Product import前`ModuleNotFoundError`退出；没有Provider访问。
  v4失败SHA `5432d6271050cdb27d41c2c9fd34fc7b86ba33bf299548dc96d456e56ce4fc52`保留。修正launch环境后，
  新v5/v6分别通过3次GET检查；这些read-only captures不是generation retry。

### Verification And Actual Stop

Native `reviewer_xhigh`分别对最终driver和exact invocation seal给出`accept`。Parent的`--validate-only`、
actual approval validator与embedded capture对比通过；1项positive及7项prompt/graph/audio/profile/runtime/
Production/status drift拒绝检查通过。固定snapshot中focused tests为`66 passed in 13.72s`。

Executable Harness exact range为`886c86d092fa8d1c6188d6c4161d4c55ddb66651..0df8b5a4a507427872c3a2942ccd54cb962d0e5a`：
`4318 passed, 4 skipped`，`1428.88s`；Architecture `0 errors / 0 warnings / 0 info`，mandatory checks全部PASS。
Receipt `.agent/harness/runs/drama-shot01-first-v2-executable-20260905/receipt.json`，SHA
`96374e6854b8139d234ca835fcc7424572b40b25696e12e040072be00d31057b`。在固定temporary checkout中
`verify-receipt`全部true；完整receipt已归档。该proof只覆盖exact snapshot，不覆盖后续unrelated source/policy edits。
Invocation seal独立docs Harness `.agent/harness/runs/drama-shot01-first-v2-seal-20260905/receipt.json`为PASS，
SHA `8f9c698ac7573776b2310aaa89159aaf346d550798c1b03136776bd42b56180c`，当时freshness校验全部true。

等待full Harness期间，其他会话修改`src/ai_video/production/vidu.py`和`vidu_profile.py`，随后新增
`vidu_source.py`。Parent只读调用现有`shot01_source_binding_preflight_v1._inventory(0df8b5a...)`，精确失败为
`pinned source drift: src/ai_video/production/vidu.py`。没有因为它不是H3模块就排除full source inventory，
也没有接管、删除、stage或commit这些unrelated bytes。

Blocker envelope：`docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v2.blocked.json`，
SHA `a0a22dfe0fa9c5e3e295cf54ca4258c8828bea29e0b26ad645055b2aef81146d`；blocker为
`CANONICAL_COMMITTED_SOURCE_INVENTORY_DRIFT`。这次停止发生在v2 `invoked` marker之前；invocation仍未消费。
16-file Production tree仍为`3abfb1c08a7de162220d46bbf1813115100db8f651b810a362e8bce55edb6731`，
request persistence、intent/permit、submit、runtime lifecycle、media、video-analysis与activation均为零。

随后source owner以`6b34537424841eafa45d632791e7aa7a7dac2820`提交Vidu changes，当前source不再dirty，
但仍不同于v2 pinned inventory；这不使旧v2 seal自动适用于新source。
Next One Thing：沿既有formal source-binding/preflight seam显式选择新committed source并封存新的exact
invocation，不改旧accepted v2或manual request。
目标仍是同一Shot 01及逐Shot Gate；不是重复授权问题，也不进入Shot 02、retry、P6或Final Acceptance。

按`record-ai-video-session`更新本primary record；自动`distill-ai-video-learning=no_candidate`：这仍是同一
deterministic repair/source-drift链，没有新独立媒体实验、controlled comparison或匹配existing Learning Claim。
Experience retrieval仍strict失败`index library version mismatch; rebuild required`，未rebuild或fallback。
记录阶段没有额外Provider/media/network调用；unrelated dirty/index work保留，未push/release。

## Historical Pre-Submit Prerequisite Acceptance — 2026-09-05

本窗口授权的独立source-binding repair与pre-submit prerequisite已完成；本节取代下方V8 source inventory stop。
M6-D仍为`NOT_EVALUATED / STOP_BEFORE_SUBMIT`，没有Shot 01生成或media Gate结果。

在等待最终Harness时，unrelated owner提交`272b17d5dae5b566d27f883c0414439176d053a3`。
相比`ee1b8d1`，`src/`与`workflows/`仅增加Vidu两个模块，原H3 source/workflow与本task drivers未变。
因此继续执行新versioned GET-only capture，而没有删除、忽略或接管其他任务文件：
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-source-binding-preflight-v3.json`，
SHA `f2988ac213f9f27c2e1d77b0adbc93a880ea5effc40ab0c11da3f61800fca726`，source固定为`272b17d`。

Current accepted seal为`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v9.accepted.json`。
它内嵌raw capture的完整JSON值；按driver的canonical serialization恢复后，bytes SHA与run-local raw sidecar一致。
Raw sidecar保留在canonical run且不另作Git source文件；tracked seal保存同一exact evidence内容，不建立第二Product owner。

- Canonical graph `a95a916...`、resolved request `87c98a1f...`、preview `a9b79ed8...`和prompt `e6cc7411...`均不变；
  strict reopen在GET前后再次完成，audio显式绑定同一accepted `GENERATED + KEEP` identity。
- Profile/runtime `MATCH`且checkouts clean：ComfyUI `7cee3ceb...`、T8 `977df788...` / `1.36.2`、
  VideoHelperSuite `4ee72c06...`、SageAttention `2.2.0`，required launch capability为`sage_attention`。
  Unit `ai-video-comfyui-d78eb1859328489996c9d5160cfdb63d.service`、PID `1039472`、invocation
  `5b59be0ad54f4485a5a791f7593e1197`及interpreter/cwd/listener归属通过前后核验。
- 仅发生`queue -> object_info -> queue`三次loopback GET，均HTTP 200，前后queue为空；Provider component/profile
  preflight通过。16-file Production tree前后仍为`3abfb1c...6731`；submit、request persistence、permit、activation、
  runtime lifecycle、media与video-analysis均为零。上述MATCH只适用于exact capture，不保证future runtime仍不变。
- `reviewer_xhigh`独立重算source inventories并核对capture/Git/profile/lineage，最终`accept`，只接受read-only facts。

Final executable Harness已自然完成：`4281 passed, 4 skipped`，耗时`1385.22s`，Architecture 0 errors，mandatory checks通过。
Receipt `.agent/harness/runs/drama-shot01-binding-final-20260905/receipt.json`，SHA
`bd76007da11ddf5e1b631c906ca7a719c2a84a81ebc417d681052fd1cbabe818`，exact range为`4ea0e328...0bc212d`。
在固定detached snapshot中`verify-receipt`全部true，包括fresh、artifact integrity与complete completion proof；原receipt已归档。
该receipt覆盖最终task executable bytes，不声称覆盖之后的Vidu实现、raw capture或V9 docs-only封存；后者单独按docs policy验证。
早期慢ONNX smoke并未证明hang；未跳过或改变tests，最终正常PASS。旧superseded Harness SIGINT仍保留为历史失败receipt。

Next One Thing：以新的versioned first-submit invocation消费V9 exact prerequisite，重新核对live source/runtime/queue，
再由既有`VideoGenerationService.start -> submit_local_once -> refresh_local_once -> fetch_local_once`执行已授权的同一Shot 01，
MP4落盘后立即进入该Shot的完整Agent Gate。不得复用已消费v1 invocation/permit，不得默认推进Shot 02、retry/variant、
activation、P6或Final Acceptance。本checkpoint完成的是独立pre-submit prerequisite，不是生成/质量接受；没有新增授权要求。

本primary record按`record-ai-video-session`更新；自动`distill-ai-video-learning=no_candidate`，理由仍为同一deterministic
修复链而非独立媒体实验。Experience retrieval的strict version-mismatch未修复或降级；无push/release，unrelated工作保留。

## Historical Source-Binding Repair And Source Inventory Stop — 2026-09-05

用户明确授权metadata-only source-binding与formal loader，以及相关document/test contract repair。
本节取代下方历史graph-binding stop：旧binding问题已修复，但后续GET-only capture在首次Product import前遇到新的
unrelated uncommitted source blocker。状态保持`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`，不是缺少同一Shot授权。

### Completed Repair

- `75e88e0f1934a2829838f1f28cc6f90d66def0c3`封存execution-intent source-binding v3 proposal，SHA
  `3c8b1305812c921ebf7166c01111eed8c90714a15839026797e83dfddde19188`；v3 accepted SHA
  `70dc023257863683157a12b0849f2fd3c6d8fe2d9c9dacf70c95d8ce38797276`。
- `39833755eb38b2172ddf8073032687b73171ff96`新增formal v3 loader；`2649f5f391f9422c8c9bba004f7910f11d182a8c`
  补齐final audio reread与exact metadata Harness routing。v3只替换active graph binding为`a95a916...`；原v1 semantic
  与v2 timing artifacts、historical drivers和graph evidence均未修改。没有Product/runtime/profile代码变更。
- Loader复用original `_assert_source_binding`、Planner、Router、compiler与current lineage validator；显式source commit
  inventory在imports前及收尾核验，并再次重开accepted references、audio policy、graph与semantic parents。
- 旧documentation test误要求已下沉至playbook的细节仍出现在AGENTS；修复测试的owner assertions，保留全部fail-closed
  audio/permit/budget/next-Shot语义，没有修改AGENTS/Skill/playbook来制造通过。

### Verification And New Blocker

Final pure proof：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-source-binding-v3-pure-proof-v1.json`，
SHA `2c8ad90c8d4c0400884486b86c26c967256ad640dba3abce97182507fd2aeca8`。Fresh process在禁止socket、文件写入
及非只读Git subprocess的audit boundary下通过完整canonical reopen；275-entry source inventory固定于`2649f5f`。
Resolved request为`87c98a1f...88f1d`、preview为`a9b79ed8...b820a`；prompt `e6cc7411...139b47`仍为3行、exact dialogue一次；
完整source-audio identity保持`GENERATED + KEEP`。16-file Production tree前后均为`3abfb1c...6731`。

Metadata/loader final exact-range Harness覆盖`4ea0e328...2649f5f`，8项mandatory checks全部PASS：Architecture 0 errors，
loader 7 tests、Harness 206 tests、ecommerce 94 tests、runtime boundary 2 tests。Receipt：
`.agent/harness/runs/drama-shot01-source-binding-20260905/receipt.json`，SHA
`3152f6cd61b16638a4c1da09e3ac992b71029ff505b8ead610f9259be42c0c51`；在固定detached snapshot中
`verify-receipt`全部true，包括fresh与complete completion proof。Native `reviewer_xhigh`最终`accept`。
此receipt只覆盖该stage，不覆盖后续GET-only driver。

新GET-only driver于`fa669da31cdf2f1eea2449b82c6d7898057d71bb`进入checkpoint，审查后以
`ee1b8d1490f1988901af0e07d19dffec43ebc1b4`修复最终Production snapshot、精确check-stage及runtime evidence标签。
真实Provider.preflight调用面已静态复核，parent的no-network canonical request assertions通过，`reviewer_xhigh=accept`；
没有POST/lifecycle/permit路径。旧`fa669da` full Harness在driver已superseded后由parent中止：198 passed，SIGINT，
不是fresh PASS。最终全部task delta verification使用
`.agent/harness/runs/drama-shot01-binding-final-20260905/receipt.json`的实际结果；未完成前不能称完整executable closure。

首次capture v1因parent误填不存在的source commit，在`source_inventory_before_import`被拒绝；错误证据保留。
改为真实`ee1b8d1`的capture v2仍在相同阶段正确拒绝：`uncommitted Product module supplements source commit`。
随后只读Git确认新untracked `src/ai_video/production/vidu_profile.py`来自本task之外，观察SHA
`55b9656d664c58fac1ac986d5ee672ad31fd2d0ce942d38df4b6b6b9dbf1edc9`。这个hash只是观察，不是接受其为新contract；
未删除、忽略、修改、stage或commit该文件，也未触碰concurrent `jieshi-episode-01` artifacts/record或其index。
两次capture均未进入runtime/Provider GET，request persistence、intent/permit、Provider submit、media、video-analysis及
Production writes为零。当前runtime是否仍满足profile、queue是否空闲在这次capture中均未验证。

Exact stop envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v8.blocked.json`。
Next One Thing：待source owner完成其committed state后，显式选择并验证新的exact source commit，沿v3 loader完成新的
immutable GET-only capture；不得以删除/忽略unrelated module、临时切换graph、重写旧request或重放已消费attempt绕过检查。
不进入Shot 02、retry/variant、activation、P6或Final Acceptance。

`retrieve-ai-video-memory --scope experience`仍strict failure：`index library version mismatch; rebuild required`，
未rebuild/retry/fallback。`record-ai-video-session`在真实blocker边界更新本primary record；自动
`distill-ai-video-learning=no_candidate`：这是同一deterministic修复链，没有独立媒体实验/controlled comparison，
existing learning claims未发现匹配source-binding/graph-rebind claim。无placeholder、adoption、push或release。

## Historical Graph Rebind And Authoring Reopen Stop — 2026-09-05

用户的“修复然后继续”授权本轮通过既有canonical graph/committer owner修复lineage，再继续检查Shot 01。
Graph-only transition已成功，但fresh authoring reopen出现新的source-binding blocker；本节取代下方历史current状态。
当前仍为`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`，不是缺少同一Shot的生成授权，也不是已确认runtime失配。

Checkpoint `665736cae9f462d065cc3c4d9d73324059b8672d`封存graph driver、rehearsal v7及graph-only approval。
唯一live transition `drama-shot01-graph-lineage-20260905-v1`通过
`ProductionStateCommitter.commit(StateCommitRequest(operation="commit_project_registry"))`完成：
Manifest revision `4 -> 6`、schema保持`2.7`，只改变Manifest与新增content-addressed graph。
Project/Registry pointers及exact bytes不变，旧graph、旧attempt、accepted creative/audio/overlay全部保留。

| Identity | Current verified value |
| --- | --- |
| active graph | `a95a916f26b53f4a2437d90860a13910fa458e33735507963148360062e8742a` |
| graph-bound resolved request | `87c98a1f8b834cd56d8fcbc163dd3a73526545e51edff202ad3fdf0ce3c88f1d` |
| graph-bound preview | `a9b79ed8cd91e3e3718187bda22eceeaf59b7ea5a70c5587ffb44379c80b820a` |
| unchanged prompt | `e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47` |
| Production tree after transition | `3abfb1c08a7de162220d46bbf1813115100db8f651b810a362e8bce55edb6731` |

Transition中的standard reload、canonical `verify_current_video_generation_lineage`通过，旧graph-bound request被拒绝。
但这些新request hashes只是transition时重新route得到的evidence，不是一次fresh完整execution preflight acceptance。
下一次从头reopen在`authoring_to_request_driver._assert_source_binding`停止：accepted overlay仍封存旧graph
`761c92a0...a47ff1`，此断言读取current Manifest后发现`a95a916f...62e8742a`，因而拒绝。
现有authoring loader没有消费graph-transition envelope来supersede该binding；不能手工跳过断言、改旧overlay、
手写request或把旧graph暂时切回去制造通过。Native `reviewer_xhigh`独立确认该边界，拒绝readiness acceptance。
未完成的success preflight代码已移除，仅保留严格复现exact rejection、验证Production零变更的blocked probe。

Exact evidence位于同一run的`evidence/`：

- `drama-shot01-graph-lineage-20260905-v1-committed.json`，SHA `2021fa28f0df82fde878f4316c879aa2486a33797f49300702e7092f53730b1c`。
- `drama-shot01-graph-bound-preflight-v1.blocked.json`，SHA `38036cb46ffe871464ebdbcfe97d2fa66aaac07e62549c14937b4b5eafd0d7b4`。
- Final stop envelope：`docs/superpowers/artifacts/drama/b-d0/pre-generation-rebind/key-at-the-waiting-room-shot-01-v1.blocked.json`。

Focused graph/committer tests `211 passed`；isolated exact-copy transition、replay零byte变化、canonical start的request
persistence-only proof与4项fault/replay checks通过。所有scratch persistence仅在隔离copy；canonical run没有
VideoGenerationRequest persistence、intent、permit、Provider submit、media或video-analysis。Fresh post-transition
probe在runtime/Provider GET之前停止；本轮graph-only commit不能写成Production零变更。

Graph checkpoint exact-range Harness：`.agent/harness/runs/drama-shot01-graph-rebind-20260905/receipt.json`，
SHA `0b8f8c775b4a2432d5379e31fdf68d691d1dd333d703c33933552151bf74c7e7`，固定detached `665736c`。
Docs contract、policy audit、runtime/Skill boundary与task Architecture Gate通过（Architecture 0 errors）。
Full suite再次遇到已知`test_native_audio_gate_documents_provider_capability_branch`的`outcome-known`字面量断言失败；
同commit focused复测同样FAIL。原计划的`PYTEST_ADDOPTS=-x`被Harness的environment sanitization清除，未生效；
parent对已知失败suite发送SIGINT，最终`1 failed, 882 passed, 1 skipped`，full check不完整且receipt为FAILED。
没有修改AGENTS/Skill/tests或隐藏该失败；不能宣称fresh passing executable receipt或execution ready。
Negative-only probe与live graph sidecars已在`74262c8b870ab9debd48e779d82b5097b7c8090f`单独checkpoint；
该commit的exact-parent Architecture Gate亦为PASS（0 errors），immutable probe重复调用在入口拒绝、没有重取或覆盖evidence。
上述graph Harness不覆盖这个后续driver commit；后者同样没有fresh passing full-suite receipt，不重复运行已知失败suite。
Final `reviewer_xhigh`对blocked probe、stop envelope、record与plan为`accept with concerns`，无artifact blocking issue；
concerns是两个已明确保留的operational blockers，不构成execution readiness。Final docs-only receipt单独位于
`.agent/harness/runs/drama-shot01-graph-rebind-stop-20260905/receipt.json`，以其实际结果为准，不代替executable verification。

Next One Thing：由execution-intent/authoring owner正式提供新的versioned source binding及current loader selection，
仅将旧graph binding沿已验证graph commit lineage更新，保持generation-intent semantic bytes不变；同时需要独立处理
既有documentation/test contract drift。当前“不修改accepted binding/code/tests”的边界未覆盖这些owner changes，
故停止并报告scope expansion。不得重跑已消费的graph transition/first-submit invocation，不得进入Shot 02或activation。

`retrieve-ai-video-memory --scope experience`仍为strict failure：`index library version mismatch; rebuild required`，
未rebuild/retry/fallback。`record-ai-video-session`在这个真实blocker边界更新本记录；自动
`distill-ai-video-learning`结果`no_candidate`：多次rehearsal/fault proof是同一deterministic修复链，没有独立媒体实验或
新controlled empirical comparison，未发现适用existing Learning Claim，未创建placeholder。未push/release，unrelated工作保留。

## Historical Canonical Start Rejection — 2026-09-05

此前source/queue blocker已在本轮fresh capture中解除，但真正的canonical `start()`暴露了更后面的graph lineage
blocker。本节取代下方历史current-facing结论；`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`仍然成立，原因不再是授权、
runtime checkout或queue不可用。用户已授权Shot 01首次真实生成及Agent-side单Shot Gate；没有授权重建pre-generation graph。

本轮在source commit `7148b548f08b036bdd0d59dd25e0c829ee1573b4`下完成strict reopen，profile-required ComfyUI
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8 `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`及其余runtime identity
为MATCH，canonical Provider preflight通过，queue为空。Exact current prompt仍为`e6cc7411...139b47`，音频策略为
已封存的`GENERATED + KEEP`。未修改accepted fixture、baseline、Story/Scene/Character/Shot、execution-intent或profile。

Driver与preflight checkpoint：`eb902f3`。唯一调用`drama-shot01-first-20260905-v1`在2026-09-05T11:21:57Z进入
`VideoGenerationService.start -> ProductionStateCommitter.begin_video_generation`，在request persistence之前被
`verify_current_video_generation_lineage`拒绝：`video request does not match the active generation target`。
Parent通过同一read-only validator独立复现，不重跑service.start、不retry、不改代码。

| Binding | Active graph | Exact current request |
| --- | --- | --- |
| requirement | `d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81` | `735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924` |
| planning request | `92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f` | `6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047` |
| verified projection | `9481519d2b4929e6abd9b0826cc5731ea54f60526ec414ffa07279d32f0a57fb` | `e201aebeb90a324549138163c0d0f4f93405ad7755f3645b1a9bd99c5413ea21` |

Active graph仍为`761c92a0...a47ff1`。15-file Production tree的前后SHA均为
`105168d84dfd9f1405b5bea548e7af1c0d6497696ec9256a29ba4700ac24a4f2`；Manifest仍只有bootstrap attempt。
Request persistence、durable intent、permit、Provider submit、media、video-analysis和Production byte changes均为零。
Orchestration的`invoked`、`started`、`stopped`sidecars保留；`started`只是进入canonical start前的记录，不表示已提交。
该invocation已消费，不能再次执行同一attempt。

Exact tracked evidence：

- `docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v1.accepted.json`：只封存单次执行范围，不是permit或media acceptance。
- `runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-first-submit-preflight-v3.json`：SHA `28b320b076297cbf553345eba585d20801088b94d91d02e6184eb3655639a624`。
- `docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v1.blocked.json`：封存exact lineage差异、validator结果、effects与三份run-local event sidecar SHA。Sidecars和早期preflight v1/v2保留为ignored本地证据，不覆盖旧版本。

Focused canonical state/service/T8/Router/prompt tests：`153 passed`；临时目录中exclusive invocation/replay guard检查
通过。Native `reviewer_xhigh`对driver为`accept with concerns`：无blocking safety defect，但共享外部runtime在最后guard
到POST之间仍有TOCTOU残余风险；本轮实际未到POST。该静态review不能代替committer lineage验证，更不能证明media quality。
Final blocker evidence经同一native `reviewer_xhigh`独立复核为`accept`。Driver exact-range Harness（FAILED）：
`.agent/harness/runs/drama-shot01-first-submit-boundary-20260905/receipt.json`；
最终stop documentation exact-range receipt：`.agent/harness/runs/drama-shot01-first-submit-stop-20260905/receipt.json`。
以receipt实际status为准，未完成的check不计PASS。
初次Harness run `drama-shot01-first-submit-boundary-20260905`期间共享HEAD被unrelated工作推进，已中止其full suite并保留
不完整receipt；不计作fresh completion evidence。中止输出为`1 failed, 1494 passed, 1 skipped`，失败项是
`tests/test_ecommerce_ad_workflow_skill.py::test_native_audio_gate_documents_provider_capability_branch`：
`AGENTS.md`缺少test要求的字面量`outcome-known`。在固定`eb902f3`及其parent的detached验证目录分别复测均为同一FAIL；
两者相关source/test文件无diff，确认是本轮之前已有的verification blocker。未修改AGENTS、Skill或tests，也未忽略该test。
Driver缺少fresh passing full-suite receipt，不能宣称全部verification完成或执行ready；无需重复整套测试来制造相同失败。

`retrieve-ai-video-memory`的experience查询仍为strict failure：`index library version mismatch; rebuild required`；
未重建、重试或fallback。`record-ai-video-session`在这个真实blocker边界更新本记录；`distill-ai-video-learning`为
`no_candidate`：无新媒体实验、无controlled comparison，不把同一链的多版本或多proof层计为独立evidence。

Next One Thing：单独扩展到canonical Dependency Graph / committer owner的lineage reconciliation，保持creative bytes
不变，更新graph后重新解析并封存graph-bound exact request，之后才评估新attempt。不能手改graph/Manifest、复用旧request、
重跑本invocation或修改runtime/code/tests绕过验证。Shot 02、retry、activation、P6、Final Acceptance仍不在本轮范围内。
现有`pre_generation_graph_driver.py`只支持bootstrap/exact replay，不能直接重跑；general graph transition owner虽存在，
本轮尚未验证exact graph-only transition。Future scope必须先验证该seam及unchanged Project/Registry语义，不能凭静态mapping
执行Manifest写入，也不能用旧bootstrap路径刷新当前schema。Readiness漏验点是没有在start前调用
`verify_current_video_generation_lineage()`；不能通过放宽这个canonical Gate来消除blocker。
本轮没有push/release，unrelated record写入保持原样；没有创建或刷新RAG index。

## Historical Scope Expansion And Pre-Submit Stop — 2026-09-05

用户已将范围扩展为canonical Shot 01首次真实生成及Agent-side单Shot媒体验收，包含必要的canonical request
persistence、durable intent与one-use permit；不包含Shot 02、activation、P6、Final Acceptance或runtime/code/tests修改。
授权已明确，当前停止原因不是缺少授权。

V6仍是有效的historical exact-capture evidence，但本轮fresh reopen在首次Product import前发现
`src/ai_video/production/comfy_video.py`相对其pinned source commit发生已提交漂移。随后只读diagnostic在新committed
source `767270b97f7060a246b53533f9ff98bf183bdd83`下验证既有exact request，并完成canonical Provider preflight；
但其post-preflight queue check失败：外部prompt `60f24a89-df16-4e73-94ec-2d0763372dd3`开始运行。
Diagnostic仅在内存中为新observation显式重绑sealed driver的source commit，没有修改旧driver、旧OUTPUT或v6 envelope，
也不构成新的accepted readiness。后续GET再次观察到同一running prompt，pending为空；该prompt不归本轮所有，
不得interrupt、clear、recover、adopt或把它计为本轮Shot 01。

Blocker evidence：
`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v7.blocked.json`，
SHA-256 `b5df618b7cd7d0d91daea50d2f9d9a7dbcd6e577314da0a0a88efc76ecf9577a`。
2026-09-05T08:54:26Z capture绑定HEAD `ec6f4f22b57a8c2efb5a4498f54d7c04e9e5bee5`、三项已提交source变化、
unit `ai-video-comfyui-94bf2350c7684bdfa0faf7f8f7db6384.service` / PID `875740`及queue response SHA。
独立Git检查显示ComfyUI仍为`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8仍为
`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`，两者checkout clean；没有重新接受完整runtime readiness。
15-file Production tree SHA-256仍为`105168d84dfd9f1405b5bea548e7af1c0d6497696ec9256a29ba4700ac24a4f2`，
与v6 capture一致。Request persistence、intent、permit、submit、media、video-analysis与Production writes全部为零。

Current blockers：`CURRENT_SOURCE_REVALIDATION_INCOMPLETE`与
`SHARED_COMFYUI_QUEUE_OCCUPIED_BY_UNATTRIBUTED_TASK`；`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`。
待共享runtime空闲后，沿已授权的同一Shot 01范围重新封存fresh source/runtime/exact-request readiness，再通过
`VideoGenerationService.start -> submit_local_once -> refresh_local_once -> fetch_local_once`进入真实媒体。
Native read-only explorer已核对该调用链、committer-owned intent/permit与fetch后`VALIDATE`停止点；不能将offline
Router family中的`transport=object()`用于live执行，也不能把blocking `poll_job()`的timeout当作轻量poll tick。
实际generation与media Gate尚未开始，不能从static mapping推出成功。Focused canonical local state / service / T8 tests：
`59 passed`。Repository baseline Architecture Gate为PASS（0 errors、21 warnings、11 info），这些是既有baseline debt，
不是本轮documentation delta的新增问题；exact task-delta verification另随checkpoint执行。

`retrieve-ai-video-memory --scope experience`本轮exit `2`，报`index library version mismatch; rebuild required`；
未重建、重试或降级。`distill-ai-video-learning`评估为`no_candidate`：单次operational source/queue observation不满足
独立媒体实验或controlled comparison threshold，未创建Learning Claim。Verification receipt以
`.agent/harness/runs/drama-m6d-shot01-expanded-scope-stop-20260905/receipt.json`的exact checkpoint结果为准。

## Historical Prerequisite Acceptance — 2026-09-05

Current Shot 01 pre-submit prerequisite已在committed source `3bd41443ab295289fe61a26846bfaab1a327622b`
上重新验证：exact Planner/Router/compiler/resolver/preview hashes保持不变，runtime identity `MATCH`，
canonical read-only Provider preflight通过。V6 envelope只接受这个prerequisite；下方v5 source-instability stop
保留为历史观察。当前仍为`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`，durable submit intent和one-use permit未创建。
详见末尾`Committed Source Reopen And Read-Only Preflight — 2026-09-05`及v6 envelope；future effect必须重新核对live identity。

## Historical Supersession Notice — 2026-08-29

本文原始`CANONICAL_SHOT_01_EXECUTION_INTENT_INCOMPLETE` stop及13-path diagnostics保留为commit
`71fc4e7ddc3174150283088030b3039fe32d963c`时的historical executable truth。新的versioned execution-intent overlay
已在不修改accepted semantic bytes或旧request/requirement evidence的前提下accepted/sealed，并经current canonical
Planner/requirement seam生成完整typed requirement与exact three-line H3 prompt。

Current state仍是`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`。2026-08-30 versioned timing repair已把canonical
requirement改为selected profile可表达的exact `124 frames @ 24fps`，并贯通Router、adapter compiler、resolver与
non-persisted exact request preview；current user显式选择的`GENERATED + KEEP` SourceAudioPolicy也已绑定并封存。
随后current user明确授权runtime切换，canonical supervisor已把clean ComfyUI checkout切换到profile-required
`7cee3ceb...`，原`SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH`已清除。Independent review拒绝了最初unsealed preflight
observation的dependency provenance；修复后strict hash-before-import又发现current request seam有uncommitted source
identity drift，且两次exact observation证明这些bytes仍在变化。Current唯一blocker因此是
`CANONICAL_REQUEST_SEAM_DEPENDENCY_IDENTITY_UNSTABLE`；durable submit intent与
one-use permit仍未创建，本记录不授权submit、media或进入per-Shot media Gate。

## Purpose

本文固定 canonical M6-D Shot 01 从 accepted Drama package 到 H3 exact non-persisted request preview之间的
executable boundary，并保存后续versioned prerequisite chronology。Current pre-submit prerequisite已通过；停止边界仍在
request persistence、durable intent、permit与任何submit之前，未进入M6-D empirical evaluation。

本文不修改 accepted fixture、baseline、Project、Registry、Manifest、historical request 或媒体 evidence，也不授权手写 prompt、默认值补全、Provider submit、retry、`video-analysis`、candidate activation、P6 或 Final Acceptance。

## Historical Materialization Identity

- canonical run root：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/`。
- materialization evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-canonical-materialization.json`，SHA-256 `75be2e494e44b5b253d730f9c9daca366806e09209c7e5e5e231c014a1b09f71`。
- planning request hash：`92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f`。
- target Shot：`drama.shot.waiting-room.001@1`，content hash `4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b`。
- requirement hash：`d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81`。
- active pre-generation graph：`761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1`。

Independent xhigh re-review 对 accepted fixture Shot 01 的 14 个核心 source fields 逐项比较为 exact match，包括 visible key presentation、exact dialogue、blocking、performance、emotion、prop close 与 camera intent。Canonical Shot identity 与 authoring lineage 没有 drift。

## Historical Executable Stop

Strict reopen exact canonical requirement 后，`compile_h3_prompt()` 返回：

- outcome：`unsupported`；
- `prompt_text=null`；
- no native prompt bytes or SHA；
- no persisted `VideoGenerationRequest`；
- no Provider selection、permit、submit、poll、fetch 或 media effect。

Exact unsupported paths：

1. `generation_intent.subject_action.endpoint`
2. `generation_intent.space_continuity.screen_direction`
3. `generation_intent.axis_continuity.camera_axis`
4. `generation_intent.axis_continuity.framing_continuity`
5. `generation_intent.performance_intent`
6. `generation_intent.visual_treatment`
7. `generation_intent.lighting_intent`
8. `generation_intent.ambience_intent`
9. `generation_intent.dialogue_intent`
10. `generation_intent.music_intent`
11. `generation_intent.camera_endpoint.start_framing`
12. `generation_intent.camera_endpoint.end_framing`
13. `generation_intent.pacing.shot_duration_seconds`

这些 diagnostics 不是可机械照填的完整 checklist。Current sparse intent 还保留 `unspecified` camera、motion、pacing、space/axis values；仅让上述 13 项消失仍可能产生不满足 visible/audible H3 grammar 的 prompt。

## Compiler Guardrail Repair

Legacy `/1` T2VA compiler 不再直接投影 `target_shot.intent`。Production Project 中的 `Shot.intent` 可以合法保存 canonical structured authoring JSON，但 Provider-native prompt 只能消费已验证的 typed current-Shot execution fields。此 guardrail 防止未来完整 intent 在 compile 时重新泄漏 `dramatic_function`、`next_shot_obligation` 或 raw JSON；它不补造 canonical M6-D 当前缺失的 execution facts，也不把 unsupported requirement升级为 ready。

Historical 6-Shot Development preview `runs/drama-h3-t8-30s-preview-20260829-v1/` 是不同 Shot identity、不同 requirement 与不同 empirical attempt。其 exact Shot 1 Gate `FAIL` 保持有效，但不得借给 canonical M6-D；同样不得把 preview request 借来绕过本 stop。

## Verification And Review

- strict reopen canonical materialization与 exact requirement：PASS。
- canonical compile outcome：稳定复现 exact 13-path `H3PromptUnsupported`。
- regression：structured `target_shot.intent` 不进入 legacy H3 prompt；三字段 grammar 与 raw-JSON exclusion保持。
- focused H3/requirement/provider adapter suite：`86 passed`。
- broader H3/T8/planner/video suite：`325 passed`。
- native `reviewer_xhigh` revised verdict：`reject` pre-submit readiness；canonical source binding正确，executable intent不完整。

## Historical Remaining Repair Boundary (Resolved)

以下内容解释为什么`71fc4e7` checkpoint必须停止，以及本轮overlay必须显式拥有哪些facts；它不再是current blocker。

继续 M6-D 前需要 separately sealed authoring-to-request repair。它可以保持 fixture/baseline bytes 不变，但必须由 canonical owner明确新增当前缺失的 execution-intent facts，并生成新的 projection/request/requirement hashes。

已 sealed facts能够支持部分机械 projection，例如 Shot 内钥匙展示与 close prop state、left/right axis、no-crossing、locked framing、steady rain、no music、5.0s target与 exact dialogue。Current accepted truth不能完整决定 visual treatment、lighting、supported dialogue language、dialogue timing/lip-sync policy、motion amplitude及cadence/tempo；Project、Story与Characters language仍为 `und`，不得根据中文字形猜 `zh-CN`，baseline也不是 prompt fact owner。

在新的 exact requirement 通过完整 typed validation、native compile、three-field visible/audible audit、profile/runtime identity preflight 与 canonical lifecycle readiness前：

- `M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；
- `next_shot_submit_allowed=false`；
- 不得手写 prompt、使用默认值、fallback、修补历史 requirement或复用 preview request；
- 不得调用 Provider、ComfyUI或`video-analysis`。

## Accepted Authoring-To-Request Repair

Accepted overlay：

- payload：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v1.proposed.json`；
- payload commit：`68863c9a34c0b7d20063d80dce07bc311aba3846`；
- payload SHA-256：`4d8fa775ba9cf51d0b0d82637cc13c0f689657559b0f08447c2f6e9a868ac0db`；
- acceptance envelope：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v1.accepted.json`；
- acceptance envelope SHA-256：`8b50b61b152b59542fc4521c870cc060b9b6469fc18db5e3a14248cf05de7efd`。

Overlay显式而非推断地拥有action endpoint/prop close、space/axis/no-crossing/locked framing、visible
performance/gaze/body/hand、visual treatment、lighting、steady-rain/no-music、exact dialogue、`zh-Hans`、
`1.700s–3.900s` timing、on-screen lip sync、camera endpoint、motion direction/amplitude、cadence/tempo与`5.0s` target。
`zh-Hans`由overlay直接author，不是从中文字形猜测locale；accepted fixture、baseline、Story、Scene、Character与Shot
semantic bytes均未改变。

Canonical accepted evidence：

- path：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-authoring-to-request-accepted-v1.json`；
- SHA-256：`1e38b731b31b4866720d5b80bfb2dd40da04ebe56dea8656f3d7219d15298cb6`；
- new request hash：`01c329aa22b898521d0611bd4fbcfcbba912babb81b4ce85a88582985704fe7c`；
- generation-intent projection hash：`9c1b1c633bef7cf9d2c26343e3f5dc84b0399269ecc4770cc879b6806fead419`；
- plan hash：`50af2a2b5df126ded8958f7d09d587a90c108a34567c15d093a9f649e88e8e24`；
- verified projection hash：`f2292b67f3616a5b4757c6c3e45301b971230bb59a3b683207d8a6d6cb412b1d`；
- new requirement hash：`d234cd95b712ca8d966132d28c6ee15a49831b412305b795c8c8eb9a2491b34d`；
- prompt SHA-256：`3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d`。

Strict request、requirement与verified projection reopen全部PASS。`compile_h3_prompt()`生成exactly three lines；exact
dialogue只出现一次，`<d>[Chinese]`与`non_diegetic_music: none`均为executable assertions。Audit确认无raw JSON、
Story/Scene/future bookkeeping、opaque canonical identity ID、abstract objective或`unspecified`。

Historical candidate evidence SHA-256 `747ec812a35eff69dc2cc20580c562cfe87165094d43127aa21712facb6d3977`与
accepted candidate-v2 SHA-256 `8d3256ab3d081820e67f727e8842fffe474a1f606ef074fa5ea09759118d13f2`在accepted rerun前后不变；
accepted-v1使用独立immutable path。Project tree before/after均为15 files，写入计数、Provider submit、媒体生成、
`video-analysis`、Manifest/Registry mutation与candidate activation全部为0。

## Current Verification And Stop

- focused Planner/requirement/H3 suite：`230 passed`；
- native `reviewer_xhigh` scoped re-review：`accept`，无blocking或non-blocking concern；
- detached exact-range Harness：`.agent/harness/runs/drama-m6-d-shot01-execution-intent-driver-v2-detached-20260829/receipt.json`；
- receipt SHA-256：`b9fff5a11907769bbc3c36fe16cf9136f65593675df60ec0f395e77cd01e2379`；
- Architecture Gate：PASS；full suite：`4206 passed, 4 skipped`；receipt status：`passed`。

该receipt在detached checkpoint上fresh且workspace stable；主checkout随后推进，因此current generic freshness不被写成true，
但immutable receipt与artifact integrity已重验。

### Provider/Profile/Runtime/Exact-Request Readiness — Current

Current canonical seam显式检查了唯一quality-first candidate，不运行ranking或fallback：

- Provider：`comfy-local-h3-t8`；model：`minimax-h3-t8-t2va-quality`；capability：`minimax-h3-t8-t2va-quality-v1`；
- profile：`minimax-h3-t8-t2va-quality@v1`，content hash `4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`；
- workflow SHA-256：`6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5`；binding SHA-256：`3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564`；
- compiler：`comfy-local-h3-t8-video-compiler@3`；family capabilities fingerprint：`d3b8e5cc31570763aae6f7454ca794737634c345ec3ea6bbbcaadc36196381dd`。

Read-only checkout/package inspection确认required与current ComfyUI commit
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8 commit
`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` / version `1.36.2`、VideoHelperSuite commit
`4ee72c065db22c9d96c2427954dc69e7b908444b`与SageAttention `2.2.0`全部exact match，三个checkout均clean。
Inspection还经systemd `ExecStart` read-only identity观察到current process包含required `sage_attention` launch capability。
期间既有ComfyUI supervisor为active；本driver没有start、stop、transport或generation调用，也没有把既有进程状态当成request readiness。

Canonical Router重新打开accepted overlay、Project/Registry、Shot revision/content hash、active pre-generation graph、new request/
projection/requirement lineage与prompt `3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d`。Prompt保持exactly
three lines且未改写。Router随后按exact output contracts比较：sealed requirement是fixed `5.0s` / `24fps`，selected
profile是`124` frames / `24fps`。`requirement_output_matches=false`，decision为
`blocked_capability / PROVIDER_CAPABILITY_DENIED`，因此没有`ProviderBoundVideoRequest`。

这也使current canonical seam无法产生或封存exact non-persisted request preview。Accepted requirement只拥有
`audio_need=required`与sealed dialogue/rain/no-music facts；native audio capability明确为`true`，但没有Provider-bound
request就没有accepted source type、SourceAudioPolicy或request binding，且没有使用default或inference。Provider preflight、durable intent、one-use permit、submit、
media、`video-analysis`、Manifest/Registry mutation与candidate activation均未发生。

Immutable blocked evidence：

- driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/provider_request_readiness_driver.py`，SHA-256 `9fd7aa85254ed46ff0543f06596ba0ac41545bea42a4f45a15a96266a9a66402`；
- evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-provider-profile-runtime-request-readiness-blocked-v1.json`，SHA-256 `f214645086e11c41d698190ac0ff4418278da9c02aae6ca1605b964d304b2cb1`；
- blocked envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v1.blocked.json`，SHA-256 `3e28032c7977579d2d53cf3650352c603547d219022429cdb5a886407c86bbcf`。

Current verification：

- immutable driver replay两次均保持evidence SHA-256 `f214645086e11c41d698190ac0ff4418278da9c02aae6ca1605b964d304b2cb1`；
- dirty-checkout与missing `sage_attention` launch-capability negative probes均fail closed为`MISMATCH`；
- focused requirement/H3/planner/readiness/Router/T8 family suite：`312 passed`；
- docs contract：PASS；Architecture Gate：PASS；
- native `reviewer_xhigh`初审指出SourceAudio inference与launch/dirty identity两个truth defects，修正后scoped re-review verdict：`accept`，无blocking或non-blocking concern；
- `distill-ai-video-learning` automatic evaluation：`no_candidate`。本记录为single pre-artifact architecture/readiness stop，保持`learning_eligibility: ineligible`，未创建Learning Claim placeholder。

Current boundary为：

- `M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`；
- `next_shot_submit_allowed=false`；
- remaining blocker：`FIXED_5S_REQUIREMENT_NOT_EXPRESSIBLE_BY_SELECTED_T8_PROFILE`；
- Provider/profile/workflow/runtime identity已显式检查；exact request preview因Router stop未创建，未persist或submit request，未进入per-Shot media Gate；
- 未产生M6-D PASS、P6、Final Acceptance或Commercial verdict inheritance。

## Versioned Timing Repair And Current Stop — 2026-08-30

Current user明确授权一个独立pre-media versioned timing repair。Accepted overlay：

- payload：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v2.proposed.json`；
- payload commit：`2661309dfa8e29896508fae0487a2b4fb2ce38c4`；
- payload SHA-256：`9e37a8a6c6e14f4c82c356294fbf781332324bacee693fcc768496d14582f56e`；
- acceptance envelope：`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v2.accepted.json`；
- acceptance envelope SHA-256：`b508cb375b6c326cbaaa5342d6aec051d20276f2d652e094f9cbca3a48efee10`。

Overlay只把Planner-owned `OutputNeed`从fixed `5.0s`变为exact `frame_count=124` / `fps=24`，并把
`GenerationIntent.pacing.shot_duration_seconds`设为`124/24 = 5.166666666666667`。Prompt中仅三个对应timing token
从`5.000s`更新为`5.167s`：lighting endpoint、terminal hold与duration。Dialogue text/timing、其余execution intent、
fixture、baseline、Story、Scene、Character、Shot semantic bytes、profile、workflow、binding与SourceAudioPolicy均未改变；
accepted SourceAudioPolicy仍显式为`null`。

Canonical Planner、Router与adapter seam重新生成并严格重开：

- request：`6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047`；
- generation-intent projection：`8ab9bc42ed01add3080a7a6550246d370109a4489275e3c6fac35b557ca3922b`；
- verified projection：`e201aebeb90a324549138163c0d0f4f93405ad7755f3645b1a9bd99c5413ea21`；
- requirement：`735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924`；
- prompt：`e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47`；
- Provider-bound request：`69b470cd4a188fc31a73b04d69c59bba9b0efe8ab1f1eb9bde994f7999e951aa`；
- compiled request：`56a6a21750a93ea392139a1e98a0558d9e7d5ae0576e1210f7b744e3118b7656`；
- request input：`de4b222eef59e867eaa30c591a10f98808558a19fa9b5d8973c7aece366b27d2`；
- resolved generation：`5a9ee2722103a6cee533b36cd5ca2d6254f3ca2bf4c7e0e22da752bd48fecc95`；
- preview：`4ba6861de793286c47215d480d94237ab7202c966f9c4836716144008d7ecb76`。

Router decision现为`selected`，exact output为`124` frames、`24fps`、`1344x768`、`video/mp4`、
`native_audio=true`，且无image/media bindings。Preview只在内存中创建；没有把`VideoGenerationRequest`写入Production
state，没有durable submit intent、permit或Provider effect。Prompt继续exactly three lines、exact dialogue once、
`<d>[Chinese]`与`non_diegetic_music: none`，且无raw JSON、Story/Scene/future bookkeeping、opaque identity、abstract
objective或`unspecified`。

Read-only runtime inspection观察到profile要求ComfyUI commit
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，current clean checkout为
`e01fb4c56b7a88149d469b99cbbfe3223d715054`。T8 `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` / `1.36.2`、
VideoHelperSuite `4ee72c065db22c9d96c2427954dc69e7b908444b`、SageAttention `2.2.0`与current
`sage_attention` launch capability匹配，但ComfyUI commit mismatch使overall runtime identity为`MISMATCH`。
Canonical Provider component/object-info preflight因此未调用；没有修改或重启ComfyUI。

Exact request要求native audio，但本slice未获授权选择SourceAudioPolicy，也没有从dialogue/rain/no-music facts推断
`GENERATED + KEEP`。因此submit readiness同时保留：

- `SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH`；
- `SOURCE_AUDIO_POLICY_NOT_SEALED_FOR_NATIVE_AUDIO_REQUEST`。

Immutable evidence：

- driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_timing_request_readiness_driver.py`，SHA-256 `668712bedae6419dac88669a8c1215d72c1b6d13b5c5a64990b196579671ee88`；
- candidate evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-timing-request-readiness-candidate-v1.json`，SHA-256 `63e81fbc65a121a6f13b07531f2d53a861bddd0c1a51afa95ab3b7fb44e236b7`；
- accepted evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-timing-request-readiness-accepted-v1.json`，SHA-256 `e3463ca9acc9ac381d0c2cc350f9b449214c588bcbade6f74fa7438c86b6f113`；
- blocked envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v2.blocked.json`，SHA-256 `5fde388ce6b46225ed68031d79edca79d83b988ef7a4b391e28c6be4eea82f5e`。

Focused Planner/requirement/Router/T8 suite为`276 passed`；native `reviewer_xhigh`对candidate commit
`2661309dfa8e29896508fae0487a2b4fb2ce38c4`的verdict为`accept`，无blocking或non-blocking concern。Current
boundary保持`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`、`next_shot_submit_allowed=false`；未产生M6-D PASS、
P6、Final Acceptance或Commercial verdict inheritance。`distill-ai-video-learning` automatic evaluation为
`no_candidate`：本记录保持`learning_eligibility: ineligible`，且当前single pre-artifact readiness stop不足以形成
跨实验Learning Claim；未创建candidate或placeholder。

## Explicit SourceAudioPolicy And Runtime-Only Stop — 2026-08-30

Current user通过`request_user_input`明确选择canonical Shot 01的`source_type=GENERATED`与`policy=KEEP`。该选择不是
从dialogue、rain ambience、`native_audio=true`或历史preview推断出的default。Versioned policy只绑定Shot
`drama.shot.waiting-room.001` revision `1`、content hash
`4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b`与既有exact request lineage，不修改Product
`VideoGenerationRequest` schema，也不改变fixture、baseline、Story、Scene、Character、Shot或execution-intent bytes。

两份被review拒绝的candidate保持不可覆盖：

- v1 payload commit `c3dd44940a251966790ea105d26e3c941879c3ac`，SHA-256
  `141cc81edd0557ed94bc867676817b1f482e9c9c4a28efc3b34d2f8138755b11`；evidence SHA-256
  `0ca93cee2c882c996513c33572e95e8c1fc35b9cf1fd94ace90679b7d693920c`；
- v2 payload commit `f230896ba7504e79f383c177bc8a3c3198b015ee`，SHA-256
  `5968e99d3a6f7bacc1bf812b607fdec55a3bdf69265a5d6b5ccae75057577cb3`；evidence SHA-256
  `c3ab3b9ba2a6d2ab60048021831cf88129a91b866610231b8dc582bcaa0df13e`。

Accepted v3 identity：

- proposed payload：`docs/superpowers/artifacts/drama/b-d0/source-audio-policy/key-at-the-waiting-room-shot-01-v3.proposed.json`；
- candidate commit：`9677aad1814ddbef7dc430f91902e08bc15bd6a3`；
- payload SHA-256：`302ee9dec106902bc7b870feda7993ca6c47bb4d8c6cf144896b402e99ec9587`；
- acceptance envelope：`docs/superpowers/artifacts/drama/b-d0/source-audio-policy/key-at-the-waiting-room-shot-01-v3.accepted.json`，
  SHA-256 `bd10225c06fc837fb4fcd118f62bbf3214cadd0abd08445f35323c14df9e3239`；
- driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_source_audio_policy_readiness_driver.py`，
  SHA-256 `1c81b4f2d81f545c13d6538bd1f735f1b54ea06de541daf0be4496085cac45f6`；
- candidate evidence SHA-256：`1d6b7a214946b93e817b5c78315f322dd2073360127a4dacdabf4195960acbc4`；
- accepted evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-source-audio-policy-readiness-accepted-v3.json`，
  SHA-256 `3fae21a8ccb6a40ef5a2c2e515b1c771e8b156d9533770196a8020e3486bb659`；
- current blocked envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v3.blocked.json`，
  SHA-256 `d121d63afe62149f851c4bbb9338911182201a97adb4fe95e6100259d14aebfb`。

Strict reopen再次得到request `6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047`、requirement
`735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924`、prompt
`e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47`与preview
`4ba6861de793286c47215d480d94237ab7202c966f9c4836716144008d7ecb76`。Request保持`native_audio=true`，exact dialogue
出现一次；required rain ambience与`music=none`一致。Raw-Shot audio PASS不会推导final-composition audio PASS，后者仍须
经canonical P4 composition后独立判定。

Native `reviewer_xhigh`对candidate commit `9677aad1814ddbef7dc430f91902e08bc15bd6a3`的verdict为
`accept with concerns`，无blocking issue。Non-blocking concern是少数non-operational nested metadata字段未逐字段进入
candidate validator；当前accepted bytes正确且由commit/blob/byte-size/SHA绑定，任何accepted-byte drift均fail closed。
Focused Planner/requirement/Router/T8 suite为`276 passed`，8个关键policy mutation probe全部fail closed。

Read-only runtime inspection仍观察到required ComfyUI commit
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`与current clean checkout
`e01fb4c56b7a88149d469b99cbbfe3223d715054`不匹配。因此SourceAudio blocker已解除，但唯一remaining blocker为
`SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH`。Current boundary仍为`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`、
`next_shot_submit_allowed=false`。Provider preflight、ComfyUI lifecycle change、request persistence、durable intent、permit、
submit、media、retry/repair、Manifest/Registry write、candidate activation与`video-analysis`均未发生。
`distill-ai-video-learning` automatic evaluation为`no_candidate`：该record保持
`learning_eligibility: ineligible`，当前单一pre-media readiness lineage不满足跨实验admission threshold，未创建Learning Claim。

## Post-Acceptance Runtime Identity Drift — 2026-08-30

Initial v3 accepted replay与exact-range Harness完成后，concurrent unrelated work改变了active ComfyUI supervisor
identity。旧 supervisor `ai-video-comfyui-4ec54ce8452c4b7383bed5a27d7ce414.service`不再是canonical discovery结果；
fresh read-only replay观察到active unit `ai-video-comfyui-1ae8d86d0a554e73a5dd7bb1aea5a7b3.service`、PID `747091`、
invocation `dc7e5c60bd584247ab09ec4f6744f75c`。本slice没有start、stop、restart或checkout操作。

Source、workflow、binding、accepted SourceAudioPolicy与exact request lineage均未漂移。Current checkout仍为clean
`e01fb4c56b7a88149d469b99cbbfe3223d715054`，selected profile仍要求
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；因此唯一blocker仍是
`SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH`。Immutable v3 evidence未覆盖；fresh sidecar与current envelope为：

- accepted readiness evidence v4：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-source-audio-policy-readiness-accepted-v4.json`，
  SHA-256 `55c217616b0967c95a240caf920a1cf7483b4837b59124ad0fda4ca86b6ed45b`；
- blocked envelope v4：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v4.blocked.json`，
  SHA-256 `2ffbb5de9291470ddbd8a7703523aa3bfe710e771ce6bc8f4e6d570998648b39`。

v4 replay的所有non-runtime fields与v3一致，Production tree前后仍为15个相同files；Provider preflight、request
persistence、permit、submit、media、repair、Manifest/Registry write、candidate activation与`video-analysis`均为零。
`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`、`next_shot_submit_allowed=false`保持不变。

## Authorized Runtime Switch And Request-Seam Drift Stop — 2026-08-30

Current user在比较“切换actual runtime”与“重新封存profile contract”后明确选择并授权前者。切换前，canonical
supervisor对应ComfyUI clean detached checkout `e01fb4c56b7a88149d469b99cbbfe3223d715054`。Readiness preflight发现
queue中已有一条unrelated H3 job；本slice没有取消、接管、重试或恢复该job，而是等它自然完成并确认queue为
`0 running / 0 pending`后才继续。

Canonical `scripts/comfyui_supervisor.py`随后完成stop，确认`127.0.0.1:8188` listener消失，再把
`/home/reggie/ComfyUI`切换为clean detached commit
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`并以`--lowvram --use-sage-attention`重新启动。Initial restart之后发生一次
concurrent supervisor replacement；first seal attempt因短暂`Connection refused` fail closed且未写evidence。Fresh canonical
discovery最终绑定active unit `ai-video-comfyui-614d031d49ab4d18aca515337362a0dd.service`、PID `1511754`、invocation
`e46d4c1a66b04470b6857740e9549813`，且loopback listener由该PID拥有。该live identity只对下方exact evidence时点有效，
未来effect边界仍须重新核对。

切换后的一次preliminary、尚未封存的strict reopen观察到以下request lineage不变：

- request：`6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047`；
- verified projection：`e201aebeb90a324549138163c0d0f4f93405ad7755f3645b1a9bd99c5413ea21`；
- requirement：`735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924`；
- prompt：`e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47`；
- resolved generation：`5a9ee2722103a6cee533b36cd5ca2d6254f3ca2bf4c7e0e22da752bd48fecc95`；
- preview：`4ba6861de793286c47215d480d94237ab7202c966f9c4836716144008d7ecb76`。

Current runtime与profile逐项匹配：ComfyUI `7cee3ceb...`、T8 `977df788...` / `1.36.2`、VideoHelperSuite
`4ee72c...`、SageAttention `2.2.0`与`sage_attention` launch capability；三个checkout均clean。Canonical
`ComfyUIT8VideoProvider.preflight()`对该exact resolved request验证sealed component size/SHA、required object-info nodes、
workflow-required inputs与T8 input-schema hash，结果为`PASS_READ_ONLY_COMPONENT_AND_OBJECT_INFO`。Queue在preflight前后均
为空，supervisor identity不变，Production tree前后均为15个相同files。但independent `reviewer_xhigh`指出该provisional
evidence只绑定top-level driver，没有在import前assert并记录它实际执行的timing/readiness/provider/transport bytes，故
verdict为`reject`。该provisional evidence与envelope未checkpoint并已移除，不能作为accepted preflight或future submit
prerequisite复用。

Parent修复provenance ordering后，readiness driver SHA-256为
`8c9ea10f23a65e8ec8b4062a79d002dda33b2762aa585d79ae9499e487247ed1`。其hash-before-import检查的first exact
observation发现以下working-tree bytes已偏离v4 accepted dependency identities：

- `src/ai_video/production/_shot_router_contracts.py`：accepted `d67d5a20...`，current `1e27bed5...`；
- `src/ai_video/production/_video_requirement_routing.py`：accepted `506bf639...`，current `962b3818...`；
- `src/ai_video/production/shot_router.py`：accepted `01101b1b...`，current `4e022cfb...`。

这些path均带uncommitted `M` status并属于unrelated concurrent work；本slice没有修改、reset、stage或接管它们。因为
current exact request必须执行这些bytes，driver在import前fail closed；current exact request reopen与canonical Provider
preflight均为`NOT_EVALUATED_DEPENDENCY_DRIFT`。Reviewer在concurrent write期间的broader focused run曾观察到4个
`continuity_transition_policy`同源failure；parent随后fresh运行本slice的170项focused suite与standalone
`tests/test_production_shot_router.py`均通过（`170 passed`、`64 passed`）。这说明当前working-tree behavior已继续收敛，但
仍不能把未提交且不在本checkpoint中的dependency bytes重封为durable replacement contract。

First observation封存后，independent re-review发现上述dependency又发生变化。Second exact observation再次看到三个
path全部变化，并在single capture内以before/after reread确认该次snapshot内部stable。两次observation间至少包括：

- `_shot_router_contracts.py`：`1e27bed5...` → `59b9a3f5...`；
- `_video_requirement_routing.py`：`962b3818...` → `b5e17c7f...`；
- `shot_router.py`：`4e022cfb...` → `e6489aaa...`。

Second evidence显式设置`current_exact_hash_claim=false`；这些值只是两个已绑定观察时点，不被描述成回复时仍current。
该two-snapshot change把current blocker收紧为`CANONICAL_REQUEST_SEAM_DEPENDENCY_IDENTITY_UNSTABLE`，exact reopen与
canonical preflight均为`NOT_EVALUATED_DEPENDENCY_UNSTABLE`。

Immutable blocker checkpoint：

- readiness driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_runtime_profile_exact_request_readiness_driver.py`，
  SHA-256 `8c9ea10f23a65e8ec8b4062a79d002dda33b2762aa585d79ae9499e487247ed1`；
- blocker driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_runtime_profile_exact_request_readiness_blocker_driver.py`，
  SHA-256 `e5e2eefc4176cd885a67bac778cfdb3089cf0110dab36c566908a17300ccf919`；
- blocker evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-runtime-profile-exact-request-readiness-blocked-v1.json`，
  SHA-256 `d8f73639958447b8d138995b7a8a234e6f5e344217b68417fea0cd9dac675d2f`；
- instability driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_runtime_profile_exact_request_instability_driver.py`，
  SHA-256 `3d228ac85256832a6501a6efb925a7b99bc79903879d1d0d800dc0f55916f5f2`；
- current blocker evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-runtime-profile-exact-request-readiness-blocked-v2.json`，
  SHA-256 `91545ca9b1281cf05c6f1624a7f63620ab4cfc5edc61a965a38813aa80c6627a`；
- blocked envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v5.blocked.json`，
  SHA-256 `febf132fd11284c471ee7ce4df82b9cd519484256e782ed40e44df7e016b02b1`。

Selected-profile preflight通过不等于整个ComfyUI installation无warning：startup log仍报告两个不属于该profile required
node集合的`comfy_extras` dependency warning，以及`comfyui-embedded-docs`版本warning。它们没有使current selected-profile
preflight失败，也不应被外推为其它ComfyUI capability已qualified。

本slice完成了authorized runtime switch，但没有接受
`provider_profile_runtime_identity_and_exact_request_pre_submit_prerequisite`。Blocker evidence中的current Provider preflight
count为0；request persistence、durable submit intent、permit、submit、media、`video-analysis`、Manifest/Registry write与
candidate activation也均为0。Current boundary保持`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`、
`next_shot_submit_allowed=false`。只有unrelated request-seam owner完成、稳定并提交其change后，后续窗口才能在不修改这些
source/tests的前提下重新核对new canonical hashes、focused tests与exact preflight；本checkpoint不能复用为effect
authorization。

`retrieve-ai-video-memory`的matching `experience` preflight因local index library version mismatch严格失败；按Skill contract
未重建、重试或降级检索，当前RAG freshness保持未知。`distill-ai-video-learning` automatic evaluation为
`no_candidate`：本记录保持`learning_eligibility: ineligible`，该single operational runtime/request-seam blocker不满足两次
independent attempt、controlled multi-arm或existing-claim material update threshold；未创建Learning Claim或placeholder。

## Committed Source Reopen And Read-Only Preflight — 2026-09-05

本次从clean `3bd41443ab295289fe61a26846bfaab1a327622b`续接。之前三个Router source files已由其owner正式提交；
`video_planner.py`也有已提交变化。新driver在Product首次import前对289个source/workflow/canonical-run files核对该
commit的Git blobs，strict重开accepted overlay、timing repair、SourceAudioPolicy、Project/Registry、Shot与active graph，
之后再次核对source inventory和15-file Production tree。四个changed source hashes在evidence中独立保存，旧accepted
source identities没有被覆盖；所有exact request hashes与v4/v5 lineage一致。

初查supervisor inactive，故仅做offline reopen；随后外部工作启动canonical unit，第二次capture拒绝继续保存过时
inactive结论。本session没有start、stop或checkout操作。最终read-only preflight绑定unit
`ai-video-comfyui-688d00c86482418295fce737686eeb89.service`、PID `69226`、invocation
`18fc0acbe8a64dda9b32e777c9e2d57f`及该PID拥有的`127.0.0.1:8188` listener。
ComfyUI `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8 `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` /
`1.36.2`、VHS `4ee72c065db22c9d96c2427954dc69e7b908444b`、SageAttention `2.2.0`及`sage_attention`
launch capability全部匹配selected profile，三个checkout clean。

Provider仍是`comfy-local-h3-t8`，model/profile为`minimax-h3-t8-t2va-quality`，capability为
`minimax-h3-t8-t2va-quality-v1`，compiler version `3`。Canonical
`ComfyUIT8VideoProvider.preflight()`校验actual component bytes、required nodes、workflow inputs和input-schema；
真实transport只发生`GET /queue → GET /object_info → GET /queue`，三个HTTP 200，queue前后均为空，
supervisor identity前后稳定。Injected HTTP hook拒绝所有其它method/URL，socket guard限制到literal loopback:8188。

Timing-repaired prompt SHA-256仍为`e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47`，
严格三行、exact dialogue一次；原5.000s prompt `3676c999...750d`仍是未改动的historical parent。
SourceAudioPolicy通过原canonical loader显式重开，acceptance/payload/commit identity与v4完全相同，
`GENERATED + KEEP`、required dialogue/ambience/music和native-audio capability/request逐项一致。

Checkpoint artifacts：

- driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_committed_seam_readiness_v1.py`，
  SHA-256 `f4d2c29da3e550b6f8b95b612cc20b3d0e4ed7bbede8bbf85f91350670d0a847`；
- evidence：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-committed-seam-readiness-v2.json`，
  SHA-256 `c6529f5e43342e7f8ed00c1480939dba2a7b6c3f2260748b7b36f01480b3db7b`；
- envelope：`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v6.accepted.json`，
  SHA-256 `4db6a56bf8c043a308d989be38af726f2003e94686e75fbd88209c1692aa245f`。

Focused Planner/Router/adapter/T8/family suite：`240 passed`。Independent review和exact-range Harness结果以本次交付的
review verdict与`.agent/harness/runs/drama-m6d-shot01-committed-seam-20260905/receipt.json`为准；本段不以旧receipt
代替最终check。旧证据与accepted semantic bytes保持原样，没有修改runtime/code/tests来制造readiness。

`pre_submit_prerequisite_ready=true`只对应本次exact capture。Durable submit intent与one-use permit均未创建，
`submit_effect_allowed=false`；没有持久化VideoGenerationRequest、Provider submit、媒体、video-analysis或Production
mutation。当前为`M6-D=NOT_EVALUATED / STOP_BEFORE_SUBMIT`。下一独立阶段必须重新核对current identity并经既有
durable intent/permit owner处理submit前条件；不得把v6作为permit或M6-D/P6/Final Acceptance。

`retrieve-ai-video-memory --scope experience`正常返回matching history，但相关experience fragments标记`stale`；
CLI自行排队derived refresh，本session未手动重建或为freshness重试。`distill-ai-video-learning`评估为`no_candidate`：
这是同一pre-media prerequisite的source/runtime更新，没有新的独立媒体实验或可采纳的跨实验claim。
