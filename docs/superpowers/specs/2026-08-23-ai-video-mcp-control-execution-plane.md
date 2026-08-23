# AI-VIDEO MCP Control And Execution Plane Specification

## Status

Accepted architecture，documentation-only。用户已接受本文的核心方向：Comfy MCP只进入
Development / Experiment Control Plane；AI-VIDEO Product Runtime继续通过direct、sealed Provider
adapters执行Local ComfyUI与Seedance。

本次只授权创建本spec与配套plan，不授权安装或启动Comfy MCP、修改Codex host配置、运行ComfyUI、
提交任何workflow、调用本地或远程Provider、读取credential、产生付费行为、修改Product Runtime、
激活candidate、push或release。

## Goal

让Codex在开发和实验阶段通过Agent-friendly MCP surface完成ComfyUI discovery与受边界约束的本地实验，
同时保持AI-VIDEO对以下Production semantics的唯一ownership：

- semantic request与resolved capability；
- exact execution-stack、workflow/profile/compiler/model identity；
- durable intent、one-use permit与submit effect boundary；
- provenance、status/fetch receipts与artifact identity；
- lifecycle、unknown-outcome handling、explicit recovery与exact replay；
- candidate、activation、QA、P6与Final Acceptance。

目标不是以MCP替换所有Provider adapters，而是把Agent control ergonomics与Product execution correctness分开。

## Governing Decision

采用Split Control / Execution Plane：

```text
Development / Experiment Control Plane

Codex / Agent
    -> Comfy MCP
    -> local ComfyUI discovery or bounded development experiment
    -> non-authoritative development evidence


AI-VIDEO Product Runtime

VideoGenerationRequest
    -> Router + exact capability/profile
    -> VideoGenerationService
    -> ProductionStateCommitter intent/permit/receipts
    -> sealed direct ComfyUI or Ark adapter
    -> candidate/activation/recovery/replay
    -> P6 / human acceptance
```

Seedance Production execution继续使用direct Ark API。当前不得增加third-party Seedance MCP、
ComfyUI Partner-node Seedance或Provider-native MCP作为Production transport。

## Problem Boundary

当前Local Comfy lane已经拥有完整的Production boundary：

- `VideoGenerationService`编排request、intent、permit、submit/status/fetch、candidate与activation；
- `ProductionStateCommitter`是唯一durable lifecycle、activation与recovery writer；
- `ComfyUIVideoProvider`及T8/H3 child adapters拥有deterministic workflow rendering、exact profile
  preflight与ComfyUI native transport mapping；
- `LocalVideoTransport`只抽象`get_object_info`、`upload_image`、`submit_prompt`、`poll_job`与
  `fetch_artifact_bytes`五类I/O primitive；
- exact replay在调用Provider transport前由canonical lifecycle short-circuit；
- submit结果不明时fail closed为`OUTCOME_UNKNOWN`，不得blind retry。

当前Seedance lane已经拥有exact model/profile、pricing upper bound、Cloud Egress、Paid Provider Gate、
materialization、one-use permit、native task ID、submit/status/fetch、response model identity、unknown-outcome
recovery、activation与replay。

因此MCP带来的主要价值是Agent discovery与实验效率，不是删除Production semantics。当前审计估算：
MCP最多委托Local Comfy execution的五项底层I/O职责；Production responsibility complexity约减少
`5-8%`，扣除MCP bridge/version/error/state handling后tracked-code净减少约`0-3%`。

## Scope

### In Scope

1. 为Codex提供host-local、project-scoped的Comfy MCP discovery surface。
2. 查询当前ComfyUI server identity、installed nodes、node schemas、model filenames与available
   workflows/templates。
3. 在另行明确授权后，运行与Production state隔离的loopback-only development experiment。
4. 为development experiment保留minimum sanitized evidence与明确的non-authoritative标记。
5. 固定MCP、`comfy-cli`与ComfyUI target identity，避免工具在多个server之间静默分流。
6. 定义从development experiment升级为AI-VIDEO Production attempt前必须经过的STOP boundary。
7. 定义未来评估MCP-backed local transport时的hard eligibility gates；本spec不批准该transport。

### Out Of Scope

- 修改`src/ai_video/production/**`、Legacy pipeline或现有Provider adapters；
- 把Codex、MCP、`.agent/`、`.codex/`或Agent Memory变成Product Runtime dependency；
- 新Manifest、Registry、attempt、receipt、schema、artifact layout或lifecycle owner；
- MCP自动选择Provider、model、profile、workflow或quality winner；
- MCP自动retry、fallback、recovery、candidate activation、QA acceptance或delivery；
- direct MCP output自动注册为Production asset或candidate；
- remote ComfyUI、Comfy Cloud、Partner nodes、Seedance、Hailuo或任何paid/cloud workflow；
- 安装custom nodes、models、workflows、MCP/plugin/dependency或修改ComfyUI；
- 将MCP run成功、output可播放或hash存在解释为Production/P6/Final Acceptance。

## Canonical Ownership

| Concern | Canonical owner | MCP role |
| --- | --- | --- |
| semantic `VideoGenerationRequest` | AI-VIDEO Planner/request model | none |
| selected Provider/capability/profile | AI-VIDEO Router + Provider resolver | discovery only |
| `execution_stack_hash` | AI-VIDEO | report pinned tool versions only |
| workflow/profile/compiler/model hashes | AI-VIDEO sealed profile/compiler | pass through experimental workflow; never certify Production seal |
| native payload | selected AI-VIDEO adapter | experiment-only invocation outside Production path |
| durable intent/one-use permit/effect token | `ProductionStateCommitter` | none |
| Comfy prompt ID / Provider task ID | external system, durably recorded by AI-VIDEO for Production | return observation unchanged |
| status and Provider error | external system observation; AI-VIDEO receipt for Production | return sanitized development observation |
| fetched bytes and SHA-256 | AI-VIDEO sink/receipt for Production | fetch experiment bytes; caller computes hash |
| candidate/activation | `ProductionStateCommitter` | forbidden |
| provenance | AI-VIDEO exact request/stack/output evidence | supply non-authoritative tool/run facts |
| recovery/exact replay/unknown outcome | `ProductionStateCommitter` | no automatic action |
| QA/P6/Final Acceptance | AI-VIDEO Review/P6/human | forbidden |

MCP不得成为second Manifest、Registry、lifecycle、recovery、retry、Provider router或quality owner。

## Development Modes

### Discovery Mode

Discovery Mode是默认允许的MCP mode，只执行不会submit workflow或改变ComfyUI state的查询：

- server/system information；
- installed nodes与node schemas；
- model filenames与categories；
- workflow/template catalog与metadata；
- queue/history的只读观察，前提是不触发cancel/delete/clear。

Discovery结果只证明当前live ComfyUI inventory。model filename不等于registered bytes、SHA-256、license或
Production readiness；node存在不等于selected sealed workflow能够通过AI-VIDEO preflight。

### Development Experiment Mode

Development Experiment Mode必须由当前task明确授权，且同时满足：

- exact target是`http://127.0.0.1:<port>`或`http://localhost:<port>`；
- `COMFYUI_URL`、`COMFY_LOCAL_URL`及任何comfy-cli target解析为同一个loopback endpoint；
- workflow来自明确的experimental copy或已知exact file，调用前计算SHA-256；
- 不修改sealed Production workflow/profile/binding；
- 不使用remote/partner/paid nodes，不读取Provider credential；
- 一个experiment identity最多一次submit；timeout/unknown outcome不自动retry；
- output写入temporary/non-Production location，不写`runs/**`、Project、Registry或Manifest；
- 记录prompt ID（若返回）、status、workflow hash、target identity、MCP/comfy-cli version、output path/hash与
  known error boundary。

MCP run默认是`development_experiment`，不是Production attempt、candidate、activated asset或QA evidence。

### Production Attempt Boundary

以下任一条件成立时，不得由Agent直接调用MCP run，必须进入现有AI-VIDEO Product Runtime：

- 使用canonical Project/Shot/request/attempt identity；
- 使用sealed Production workflow/profile/binding或registered input；
- output准备写入Registry、Manifest、candidate、continuity或activation path；
- 需要exact replay、explicit recovery、P5/P6 evidence或Final Acceptance；
- workflow包含remote、Partner、paid、credential-bearing或cloud-egress node；
- result将被描述为Production、live-ready、quality accepted或delivery output。

Production attempt必须由`VideoGenerationService`和`ProductionStateCommitter`签发durable intent与Local/Paid
Permit，并通过selected sealed adapter执行。Agent不得通过MCP绕过该boundary。

## Workflow And Asset Rules

- MCP不得修改sealed Production workflow、profile、binding或materialized execution stack。
- Agent可以在temporary experimental directory创建或修改experimental workflow，但该workflow不得静默覆盖
  repository workflow，也不得因一次成功run升级为Production artifact。
- reference upload只负责传输bytes；AI-VIDEO继续拥有input path containment、registered bytes、SHA-256、role
  binding与provenance。
- MCP model discovery只返回inventory hint；Production preflight继续读取并验证exact model/checkpoint bytes、
  component sizes/hashes、ComfyUI commit与installed node schemas。
- output fetch只负责搬运bytes；AI-VIDEO继续负责container probe、bounds、content SHA、candidate validation、
  activation与reopen。

## Evidence Boundary

Development experiment minimum evidence包含：

- `authority = development_experiment`；
- exact MCP repository commit/version与`comfy-cli` version；
- exact loopback endpoint及ComfyUI server identity；
- workflow source path、pre-run SHA-256与是否为experimental copy；
- relevant node/model filenames，明确注明未证明model bytes/hash/license；
- prompt ID（若成功获得）、terminal status、output filename/bytes/SHA-256；
- timeout、normalized error与unknown-outcome limitation；
- `production_attempt_id = null`、`candidate_id = null`、`activation = false`、`p6_verdict = null`。

这些字段可以写入sanitized session/report artifact，但不能写入或替代Production Manifest/Registry receipts。
若未来需要把development output正式导入Product Runtime，必须另行定义并批准strict import/materialization
contract；本spec不创建该旁路。

## Retry, Replay And Recovery Contract

### Development Experiment

- MCP/comfy-cli的实际retry policy必须在启用前静态审计并记录。
- Agent policy固定为no automatic retry。一次submit timeout或未返回prompt ID时标记
  `development_outcome_unknown`并停止。
- 用户若明确要求新的实验，必须使用新的experiment identity；不得把它描述为原run的exact replay。

### Production Runtime

Production exact replay必须在任何MCP/Provider call之前由AI-VIDEO canonical state命中：

```text
same desired exact replay
    -> zero MCP invocation
    -> zero ComfyUI submit
    -> zero Provider/fetch/activation effect
```

当前Comfy MCP没有caller-supplied effect token、request idempotency或按该token查回唯一prompt ID的contract。
如果MCP request已发送但response/prompt ID丢失，不能canonical reconcile，只能fail closed并可能留下orphan
Comfy job。因此当前MCP不得进入Production execution path。

## Tool And Host Boundary

- Comfy MCP安装在host-local isolated environment，不加入AI-VIDEO runtime dependencies。
- project `.codex/config.toml`只负责Development Governance routing；Product Runtime不得读取该文件。
- server command使用explicit pinned executable path，不使用unpinned `uvx ...@latest`或network-on-start launcher。
- target必须显式固定为同一loopback endpoint；禁止remote fallback与多个environment keys指向不同server。
- 初始adoption只启用/调用read-only discovery tools。run、workflow mutation、install/update/restart、queue
  mutation、cancel/delete与Partner tools保持inactive，直到对应阶段获得明确授权。
- secrets不得进入config、environment、prompt、command argument、log、receipt或report。

## Seedance Boundary

Seedance Production继续使用current direct Ark adapter，保留：

- exact API model/profile与native request；
- native task ID、status、response model与Provider error；
- pricing/budget/Cloud Egress/Paid Provider Gate；
- `SeedanceAssetMaterializationReceipt`与remote asset lifecycle；
- one-use permit、unknown-outcome recovery、activation与exact replay。

Third-party Seedance MCP、ComfyUI Partner-node Seedance或未来Provider-native MCP只能作为另行授权的
experiment control surface；不能因“能生成视频”进入Production lane。

## Future MCP-Backed Local Executor Eligibility

只有新的独立spec同时证明以下全部条件，才可重新讨论
`AI-VIDEO Runtime -> MCP transport -> ComfyUI`：

1. pinned compatible license、MCP、comfy-cli与ComfyUI versions；
2. enforced loopback-only与single exact target；
3. exact workflow/request bytes或caller-computed hash被原样回显；
4. no workflow mutation、Provider routing、fallback或implicit retry；
5. structured prompt ID、raw status/error与exact output metadata；
6. caller-owned durable effect token/idempotency identity；
7. crash after request send before response可按effect token查回canonical prompt ID；
8. MCP/comfy-cli state不成为canonical lifecycle；
9. tests证明same-desired exact replay为zero MCP run、zero Comfy submit；
10. `ProductionStateCommitter`继续独占permit、receipts、recovery、activation与P6 boundary。

当前审计的Comfy MCP不满足第4、5、6、7项，因此default decision是保持Agent-only。

## Compatibility And Rollback

- Legacy `0.1.x` CLI、Manifest、workflow binding与Comfy transport保持不变。
- v0.2 request/resolved/Manifest/Registry/Dependency Graph/ResolvedTimeline/P6 contracts保持不变。
- Local H3/T8/Turbo/native-Turbo与Seedance adapters保持不变。
- 删除project MCP routing并移除host-local isolated environment即可回滚Agent adoption；回滚不触碰Product
  state、runs、workflows、models或Provider artifacts。

## Acceptance Criteria

1. Codex可以通过pinned Comfy MCP列出同一loopback ComfyUI的server、nodes与model filenames。
2. Discovery不会submit workflow、upload asset、修改queue/workflow、写Product state或读取secret。
3. Product Runtime没有新增MCP/Codex/.agent/.codex import或runtime dependency。
4. 未经单独授权不能执行development run；未经AI-VIDEO permit不能产生Production attempt。
5. 一个另行授权的development experiment可以返回prompt ID/status/output，并被诚实标记为non-Production。
6. timeout/unknown outcome停止且不automatic retry。
7. MCP output不能直接activation，也不能产生P6或Final Acceptance claim。
8. Seedance Production仍只走direct Ark adapter。
9. exact rollback不修改任何Production state或generated media。
10. policy-routed documentation verification对exact snapshot通过。

## Verification

Spec/plan阶段只允许offline documentation verification：

```bash
git diff --check -- \
  docs/superpowers/specs/2026-08-23-ai-video-mcp-control-execution-plane.md \
  docs/superpowers/plans/2026-08-23-ai-video-mcp-control-execution-plane.md
python -m scripts.docs_contract_gate check
```

完成artifact后按`.agent/harness/policy.yaml`对non-empty exact staged snapshot运行Harness。不得为了文档
verification安装/启动MCP、启动ComfyUI、运行Provider或生成媒体。

## External Evidence Snapshot

本contract基于2026-08-23只读审计：

- Comfy MCP pinned source：
  `https://github.com/Comfy-Org/comfy-mcp/tree/b3766a0baa456deda5944b9e3f549228eecf7985`
- Comfy MCP在该snapshot仍为Agent-friendly wrapper，通过`comfy-cli`调用ComfyUI；支持discovery、workflow
  run、prompt ID、status与output fetch，但没有AI-VIDEO要求的durable effect token和crash reconciliation。
- Third-party Seedance reference：
  `https://github.com/AceDataCloud/SeedanceMCP/tree/0e54bb1c28e90a7c30520922a4c1adae14630c3b`
  使用broker API，不是AI-VIDEO direct Ark Production transport。

外部工具后续版本可能变化；implementation开始前必须重新审计current pinned source，不能从本日期snapshot
推断未来compatibility。
