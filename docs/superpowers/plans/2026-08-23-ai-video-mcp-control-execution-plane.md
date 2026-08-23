# AI-VIDEO MCP Control And Execution Plane Implementation Plan

## Status

Deferred；当前明确结论是`DO NOT START NOW`。现有direct/sealed adapters已经满足Production execution，
当前没有证据证明ComfyUI discovery或临时HTTP/Python实验摩擦正在阻塞后续工作。本文保留event-driven start
gate，只有下文条件全部满足时才进入Milestone 0。

本文是durable execution plan；spec/plan及本status更新都不授权安装/启动Comfy MCP、修改host/project config、
运行ComfyUI、submit workflow、调用Provider、读取credential、生成媒体、付费、push或release。

## Goal

把pinned Comfy MCP接入Codex的Development / Experiment Control Plane，先完成loopback-only discovery，
再在单独授权下验证一次non-Production local experiment；AI-VIDEO Product Runtime继续使用现有direct、sealed
ComfyUI与Ark adapters。

## Scope

包括host-local isolated installation、project MCP routing、Development Governance guardrails、read-only
discovery verification、可选的单次development experiment与最终Agent-only/MCP-transport decision closure。

## Contract Surfaces

- Governing spec：
  `docs/superpowers/specs/2026-08-23-ai-video-mcp-control-execution-plane.md`
- Development routing：`.codex/config.toml`
- Agent operating boundary：`.agent/context/control-plane-playbook.md`
- Product isolation：`AGENTS.md`、`docs/agent-primary-contract-matrix.md`、
  `docs/v0.2-runtime-baseline.md`与architecture checks。
- External pinned source：Comfy MCP commit
  `b3766a0baa456deda5944b9e3f549228eecf7985`。

## Invariants

- `ProductionStateCommitter`继续是唯一durable lifecycle、activation与recovery writer。
- Product Runtime不得import、启动或依赖Comfy MCP、Codex或`.codex/config.toml`。
- Local H3/T8/Turbo/native-Turbo与Seedance Production adapters保持direct/sealed。
- Seedance Production保持direct Ark API；不得增加third-party/Partner MCP path。
- discovery default-on；run/mutation/install/update/restart/cancel/delete/Partner tools default-off。
- development experiment不写`runs/**`、Project、Registry、Manifest、candidate或P6 evidence。
- unknown outcome不automatic retry；exact replay只能由AI-VIDEO canonical state拥有。

## Current / Target Behavior

### Current

Codex需要通过已有AI-VIDEO scripts/adapters或临时HTTP/Python方式检查ComfyUI inventory与实验output。
Production path已经完整，不需要MCP补充lifecycle semantics。

### Target

Codex可以通过project-scoped Comfy MCP查询single loopback ComfyUI；只有在另行授权的development task中才
运行一次sandbox experiment。任何Production candidate仍必须回到`VideoGenerationService`、Local Permit、
sealed adapter和`ProductionStateCommitter`。

## Compatibility

本计划不迁移public API/CLI/schema/Manifest/artifact layout，不修改runtime dependency，不改变local-first、
renderer、timeline、Provider selection、activation、recovery或P6 contracts。回滚仅移除Development Governance
routing与host-local environment。

## Out Of Scope

- MCP-backed Product Runtime executor；
- Product evidence import/schema；
- Seedance MCP；
- remote/partner/paid workflow；
- ComfyUI/custom-node/model/workflow upgrade；
- Provider benchmark、quality acceptance、Pilot或release。

## Execution Start Gate

### Current Answer

当前不应开始实施。Spec、plan和architecture record已经足以保存决策；在没有真实重复摩擦前安装MCP只会增加
host dependency、license/version维护和新的tool/retry/state surface，不会改善Production correctness。

### Required Start Conditions

只有以下条件全部满足，才可以开始Milestone 0；任何一项不满足都继续`DEFERRED`：

1. 用户在新的current task中明确授权“开始实现Comfy MCP Agent control plane”，而不只是要求查看、讨论、
   更新spec/plan或询问必要性。
2. 已出现以下任一可验证需求信号：
   - 两个独立、已授权的Local Comfy开发任务都需要重复手工查询live server/nodes/models/workflows、临时写
     HTTP/Python或手工定位output；或
   - 一个当前Local Comfy开发任务因缺少Agent-readable discovery/tool surface而真实blocked，且现有
     AI-VIDEO adapter/CLI不能提供同等低成本的只读信息。
3. 目标收益明确是Development discovery/experiment ergonomics，不是减少Production adapter代码、修复
   Production replay/recovery或替换Seedance direct Ark path。
4. Local ComfyUI与现有AI-VIDEO direct path已经独立可用；不得用安装MCP同时诊断或修复ComfyUI、custom node、
   model、workflow或Provider问题。
5. 当前没有更高优先级的continuity、quality、Provider lifecycle或Pilot acceptance工作因本adoption被延迟；
   MCP若不是其直接blocker，就不得插队实施。
6. `.codex/config.toml`与`.agent/context/control-plane-playbook.md`没有same-file live writer或uncommitted ownership
   conflict；unrelated dirty files本身不阻塞，但必须保持不动。
7. Milestone 0重新确认pinned source、entrypoint、license、`comfy-cli` compatibility、tool categories、retry行为与
   single-loopback configuration仍与governing spec一致。
8. implementation scope仍能停在Milestone 0-2，不需要Product Runtime、Seedance、remote/Partner、paid、schema、
   Manifest或artifact-layout change。

当第2项首次满足时，执行Agent必须在过程更新中列出构成trigger的exact tasks/blocker；不得只写“以后可能方便”。

### Do Not Start Conditions

以下情况即使用户正在使用ComfyUI，也不构成启动理由：

- 偶尔运行一个已经sealed并可由现有adapter执行的workflow；
- 仅希望删除`ComfyUIVideoProvider`、`LocalVideoTransport`或`comfy_client.py`代码；
- 需要Production one-use permit、exact replay、unknown-outcome recovery、activation或P6；
- 需要Seedance、Comfy Partner node、remote ComfyUI、paid workflow或Provider credential；
- 只是因为MCP“更先进”、plan已经存在或host支持MCP；
- external version/license/entrypoint发生drift，但尚未完成重新审计；
- same-file writer conflict尚未由用户决定ownership或执行顺序。

## Completion And Stop Gates

### Minimal Adoption Complete

本plan的推荐最小完成点是Milestone 0-2全部通过，不要求运行generation。只有同时满足以下条件才可声明
`Comfy MCP Agent discovery adopted`：

1. exact external commit、resolved package versions、license与entrypoint已记录；
2. isolated host environment与project `.codex/config.toml` routing已完成，single target严格解析为同一loopback
   ComfyUI；
3. Codex完成真实MCP initialize/list-tools handshake；
4. read-only server/node/schema/model/workflow metadata discovery成功；
5. mutating、submit、install/update/restart、cancel/delete、Partner/paid tools均未调用；
6. 调用前后证据证明zero Comfy submit/upload/queue mutation、zero `runs/**`/Product state writes；
7. Product Runtime没有新增MCP/Codex/.codex dependency，existing direct adapters保持可用；
8. task-owned config/docs delta通过exact staged与commit-range Harness并形成fresh receipt；
9. local commit与origin publication分别报告，未push时不得声称published。

达到该点后应停止并交付，不得仅为“把plan全部跑完”自动进入Milestone 3。

### Optional Experiment Complete

Milestone 3不是minimal adoption的完成条件。只有新的current task明确授权一次local development experiment时才
执行；完成定义是exactly one submit、prompt ID/status/output identity可复核、unknown outcome no retry、zero
Product writes以及明确的`development_experiment`标记。成功生成媒体仍不构成Production、quality、P6或Final
Acceptance。

### Plan Closure Complete

Milestone 4在以下任一结果下都可以关闭本plan：

- `Agent-only retained`：Milestone 0-2通过，MCP作为Development discovery tool稳定使用；
- `Adoption rejected/rolled back`：license、version、security、target isolation或operational cost不合适，routing和
  host environment按Rollback清理；
- `Experiment not needed`：read-only discovery已经解决真实摩擦，Milestone 3明确标记`not_evaluated`；
- `Future executor gate failed`：缺caller effect token、crash reconciliation、raw error或strict zero retry，继续
  direct Production adapters。

“MCP-backed Product executor完成”与“Seedance MCP完成”不是本plan的closure条件；若未来十项eligibility gates
全部成立，必须另写spec/plan并获得新的implementation authorization。

### Immediate Stop Conditions

implementation期间命中以下任一项必须停止，不得自动扩大scope或换路线：

- target解析为非loopback、多个environment keys指向不同ComfyUI或出现remote fallback；
- installer/server需要network-on-start、unbounded latest或未审计dependency；
- license或`comfy-cli` compatibility无法确定；
- read-only discovery触发upload、submit、queue mutation、workflow modification或credential lookup；
- error/timeout触发隐式submit retry，或无法区分是否已经产生external effect；
- 需要修改`src/ai_video/production/**`、workflow/profile/binding、Manifest/Registry/schema或Seedance lane；
- target-file ownership与其它writer发生same-file overlap；
- 无法证明rollback不会删除ComfyUI、models、workflows、runs或Production state。

## Acceptance Criteria

- Codex host可以列出pinned Comfy MCP tools，且target解析为唯一loopback endpoint。
- read-only discovery返回server/nodes/model filenames，不产生submit/upload/queue mutation。
- Product Runtime source、dependencies和canonical owners没有变化。
- 可选experiment严格标记为`development_experiment`，一次submit、no automatic retry、zero Product writes。
- unknown outcome被诚实保留，output不能直接activation或声明P6/Final Acceptance。
- removal test证明禁用MCP routing不影响Legacy或Production Runtime。

## Verification Strategy

每个milestone先执行不启动Provider的offline/static checks；live discovery与development experiment是后续独立
authorization gates。任何Harness receipt只证明exact code/control-plane snapshot，不证明ComfyUI live、media
quality或Production acceptance。

## Change Surface

### Phase 0 Repository Files

- Modify: `.codex/config.toml` — 增加project-scoped pinned Comfy MCP launch与single loopback target。
- Modify: `.agent/context/control-plane-playbook.md` — 增加Agent-only discovery/experiment、Production STOP、
  retry/unknown-outcome与evidence guardrails。
- Modify only if current Harness inspection requires exact routing ownership:
  `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`。
- Modify only if dynamic implementation truth changed after successful adoption:
  `docs/v0.2-runtime-baseline.md`。它只能记录Development Governance availability，不得声明Product Runtime
  dependency或Production acceptance。

### Host-Local State

- Create isolated environment under
  `/home/reggie/.local/share/ai-video/comfy-mcp-0.10.0/`。
- Install audited source commit
  `b3766a0baa456deda5944b9e3f549228eecf7985` and its compatible `comfy-cli` into that environment。
- Record resolved package versions and license snapshot in a sanitized implementation receipt；不得写credential或
  private environment dump。

### Must Not Modify

- `src/ai_video/production/**`、`src/ai_video/comfy_client.py`、Legacy pipeline；
- `workflows/**`、models、custom nodes、`runs/**`；
- Project、Registry、Manifest、Dependency Graph、ResolvedTimeline、P6 state；
- Seedance profiles/adapters/materialization/paid-provider code；
- unrelated dirty/staged files。

## Major Milestones

### Milestone 0: Reconfirm Boundary And Freeze External Identity

**Files:**

- Read: governing spec、`AGENTS.md`、contract matrix、Harness policy、playbook、runtime baseline。
- Read: pinned Comfy MCP source/license and compatible `comfy-cli` metadata。

**Owner / Dependencies:** Main Agent；no implementation writer until exact target-file ownership is clear。

**Contract:** 重新确认external source仍提供预期entrypoint与tools；识别所有submit、retry、workflow mutation、
install/update/restart、queue mutation与Partner paths。外部source若与审计snapshot不一致，停止并更新spec/plan，
不得自动跟随latest。

**Acceptance:** 形成exact version/license/entrypoint/tool classification；Product Runtime target files为空。

**Verification:**

```bash
git status --short --branch
git rev-parse HEAD
```

只读检查pinned source；不安装、不启动server、不访问ComfyUI。

### Milestone 1: Provision Isolated Host Runtime

**Files:**

- Create outside repository:
  `/home/reggie/.local/share/ai-video/comfy-mcp-0.10.0/`
- Modify: `.codex/config.toml`
- Modify: `.agent/context/control-plane-playbook.md`

**Owner / Dependencies:** 用户单独授权host installation后由一个bounded writer执行；不得与其它writer修改同一
config/playbook file。

**Contract:**

- 使用isolated environment，不加入`pyproject.toml`或Product Runtime dependencies；
- command绑定explicit executable path，不使用unpinned network-on-start launcher；
- `COMFYUI_URL`与`COMFY_LOCAL_URL`固定为同一`http://127.0.0.1:8188`；
- 不配置remote fallback、credential或Partner account；
- playbook明确MCP属于Development Governance、default discovery-only、Production STOP与no automatic retry。

**Acceptance:** Codex strict config能够解析新server；禁用该server后AI-VIDEO imports/tests/runtime行为不变。

**Verification:**

```bash
/home/reggie/.local/share/ai-video/comfy-mcp-0.10.0/bin/python -m pip show comfy-mcp comfy-cli
codex --strict-config doctor --json
python -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('.codex/config.toml').read_text())"
git diff --check -- .codex/config.toml .agent/context/control-plane-playbook.md
```

本milestone不启动Comfy MCP或ComfyUI，不调用任何MCP tool。

### Milestone 2: Verify MCP Handshake And Read-Only Discovery

**Files:**

- Modify only if verified truth warrants:
  `docs/v0.2-runtime-baseline.md`
- Optional sanitized record after stable completion:
  `docs/record_for_agent/2026-08-23-comfy-mcp-agent-control-plane.md`

**Owner / Dependencies:** 需要Milestone 1完成及用户允许连接已运行的loopback ComfyUI；不授权generation。

**Contract:**

- 完成真实MCP initialize/list-tools handshake；
- 将tools分类为read-only、submit、workflow mutation、runtime mutation与paid/Partner；
- 只调用server info、installed nodes/schema、model filename与workflow/template metadata查询；
- 调用前后比较Comfy queue/history、repository status与`runs/**`，证明zero submit/upload/queue mutation和zero
  Product writes；
- discovery findings只报告inventory，不升级model hash、workflow readiness或Production capability。

**Acceptance:** Codex可以稳定读取single loopback server inventory；所有mutating tool仍未调用；错误中不包含
secret、absolute private asset path或raw environment dump。

**Verification:**

```bash
git status --short
git diff --check
```

并保存sanitized MCP handshake/tool inventory与zero-mutation comparison。不得为此启动generation或运行Provider。

### Milestone 3: Optional Bounded Development Experiment

**Files:**

- Temporary only: `mktemp -d`下的experimental workflow copy与fetched output。
- Optional sanitized record only after stable result:
  `docs/record_for_agent/2026-08-23-comfy-mcp-agent-control-plane.md`

**Owner / Dependencies:** 必须由新task明确授权local experiment；Milestone 2通过；确认workflow没有remote、Partner、
paid、credential-bearing或state-mutating nodes。

**Contract:**

- experiment authority固定为`development_experiment`；
- 调用前记录workflow SHA-256、single loopback target、MCP/comfy-cli/ComfyUI identity；
- exactly one submit；取得prompt ID后只poll该identity并fetch其exact output；
- timeout或prompt ID丢失标记`development_outcome_unknown`并停止，不retry、不猜测queue job；
- output留在temporary/non-Production location，计算bytes/SHA-256与minimum media probe；
- 不调用`VideoGenerationService`、不签发Local Permit、不写Manifest，因为该run明确不是Production attempt；
- 不把成功output导入Registry、candidate、P6或Final Acceptance。

**Acceptance:** 一次独立experiment能够被exact identity和output hash描述；Product state与repository workflow保持
不变；失败时同样保持no retry与zero Product writes。

**Verification:**

```bash
git status --short
git diff -- runs workflows src/ai_video/production
```

使用`ffprobe`只验证fetched development bytes的基本容器事实；不得由此声称quality PASS。

### Milestone 4: Close Agent-Only Adoption Decision

**Files:**

- Modify: `docs/v0.2-runtime-baseline.md` only if Development Governance availability became current truth。
- Create/update one `docs/record_for_agent/**` record only if the session-record skill boundary is met。

**Owner / Dependencies:** Milestone 2必须完成；Milestone 3可以未执行并明确标记not evaluated。

**Contract:** 默认结论保持Agent-only。逐项评估pinned implementation是否满足governing spec的十项future
MCP-backed local executor eligibility gates。缺caller effect token、crash reconciliation、raw error或strict zero
retry任一项，即不得创建Product executor plan。

Seedance direct Ark path不参与该decision；不得以Comfy/third-party MCP run替代current Paid Provider evidence。

**Acceptance:** durable truth明确区分：installed、handshake、read-only live、development experiment、Production
transport、quality/P6分别是什么状态；没有从前一层外推后一层。

**Verification:** 对exact task-owned staged snapshot运行Harness；文档/control-plane category必须包含
`docs_contract_check`。若包含executable config/tooling change，按policy运行额外selected checks。

### Milestone 5: Exact Snapshot Verification And Local Commit

**Files:** 只包含本implementation实际拥有的Development Governance/config/docs files。

**Owner / Dependencies:** 所有已授权milestones完成；再次检查live writer target-file overlap。

**Contract:** 保留unrelated dirty/index work；使用`git add <specific-files>`；不得stage host environment、temporary
experiment output、`runs/**`或其它writer changes。

**Acceptance:** exact staged snapshot与commit range均可解释；fresh receipt只覆盖task-owned delta；local commit不被
描述为push/release或Product acceptance。

**Verification:**

```bash
python -m scripts.agent_harness inspect --staged
python -m scripts.agent_harness run --staged
git diff --cached --check
```

commit后按当前Harness CLI对exact commit range生成fresh receipt。不得运行live Provider、media generation或额外
paid smoke来关闭Harness。

## Future MCP-Backed Executor Decision Gate

本计划不包含MCP-backed executor。只有Milestone 4证明governing spec全部eligibility gates后，用户才可另行授权
新spec；该新spec至少必须定义：

- AI-owned caller effect token与MCP request binding；
- crash after request send before response的prompt-ID reconciliation；
- zero hidden retry/fallback/workflow mutation；
- raw status/error/output identity；
- MCP/comfy-cli version进入`execution_stack_hash`；
- same-desired exact replay的zero MCP/zero Comfy submit tests；
- `ProductionStateCommitter`唯一lifecycle/recovery/activation ownership。

未满足时，不得把“Agent实验好用”转换成“Product Runtime应依赖MCP”。

## Rollback

1. 从`.codex/config.toml`移除Comfy MCP server routing。
2. 恢复playbook中仅与该routing相关的task-owned段落。
3. 删除host-local isolated environment
   `/home/reggie/.local/share/ai-video/comfy-mcp-0.10.0/`，但只在精确确认target且用户授权destructive
   host cleanup后执行。
4. 不修改或删除ComfyUI、models、custom nodes、workflows、`runs/**`、Production state或Harness history。
5. 运行Codex strict-config验证与policy-selected exact snapshot checks，证明AI-VIDEO direct Runtime不受影响。

## Self-Review Checklist

- Spec coverage：Agent-only discovery、optional experiment、Production STOP、Seedance direct、retry/recovery、
  provenance、evidence与future executor gate均有milestone owner。
- Placeholder scan：无`TBD`、`TODO`或由executor重新选择的architecture decision。
- Type/identity consistency：全plan使用`development_experiment`、`development_outcome_unknown`、
  `ProductionStateCommitter`与single loopback target等同一术语。
- Verification boundary：offline/Harness、live discovery、development generation、Production/P6被分别报告。
