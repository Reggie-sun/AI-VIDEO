# AI-VIDEO Base AI Comic E2E Specification

Status: Approved prerequisite design for P8；Base AI Comic implementation 已获授权。本文不授权 P8、Paid Provider Gate、真实 Provider、push 或 release。

## 1. Goal

在不启用 Video Provider、不增加 production orchestrator 的前提下，用同一个 durable Production Project 证明：

```text
Story / two Shots
  -> reusable Character / Scene references
  -> P7 generated image assets
  -> P4 voice + CaptionTrack
  -> P3 ResolvedTimeline + HyperFrames render
  -> P6 strategy-aware failed review
  -> exact approved composition repair
  -> P5 selective invalidation
  -> rerender + fresh pass reviews
  -> repair outcome + final acceptance
  -> reopen exact final.mp4 and provenance
```

该 proof 是 P8 的 hard prerequisite，但不属于 Generated Video Provider implementation。

## 2. Repository Findings

### 2.1 Existing capabilities are individually accepted

- P7 已能以 deterministic injected Provider生成两个 Shot 的 PNG，复用 Character/Scene reference，并通过唯一 `ProductionStateCommitter` 原子激活 target Shot、Registry 与 P5 graph。
- P4 已能以 fake voice Provider生成 audio/CaptionTrack，并通过 injectable HyperFrames runner生成可 probe 的 MP4。
- P5 已能计算 precise desired/applied state、exact affected closure 与 render-node freshness。
- P6 已能持久化 Review、approved Repair、Repair Outcome 与 Final Acceptance receipts。

这些能力分别通过测试，但当前没有一条 acceptance path在同一 Project上组合它们。

### 2.2 Manifest 2.5 compatibility gap

`ProductionManifest` model、reader 与 P7 state已允许 Manifest 2.5组合 P6字段；但下列 mutation owners仍只把2.3/2.4视为 graph/review-aware：

- `_state_commit_dependency.py`：graph transition；
- `_state_commit_voice_intent.py`、`_state_commit_voice_activation.py`：P4 voice lifecycle；
- `hyperframes.py`、`_state_commit_render_lifecycle.py`：render transition、replay与review staleness；
- `_state_commit_review.py`、`_state_commit_repair.py`：P6 review/repair；
- `_state_commit_transaction.py`：generic approved repair commit。

因此 P7升级到 Manifest 2.5 后，现有 runtime无法诚实完成 voice、render、review、repair与final acceptance。该缺口是 version-aware compatibility glue，不需要新 schema。

### 2.3 Composition selection gap

P7 激活新 generated image时更新 active Shot的 exact asset role binding，但不会改写调用方之前持有的 `CompositionSpec`。Base E2E必须从当前 active Project/Shot重新解析 visual asset IDs并 seal新的 CompositionSpec；不得继续渲染旧 imported image IDs。

## 3. Architecture Decision

选择 standalone deterministic integration acceptance + existing-owner compatibility fixes。

- Codex继续是顶层 Production Agent；仓库不新增 `BaseComicService`、workflow engine或public orchestration API。
- Manifest继续使用2.5；不新增字段、pointer、layout或migration。
- 每项 mutation仍由原 owner执行；只扩展其 accepted-version条件与2.5 state-preservation tests。
- `ProductionStateCommitter`继续是唯一 writer/recovery owner。
- E2E orchestration只存在于 tests/support code，调用真实 production APIs与durable files。
- 所有 Provider、analyzer与renderer transport使用 deterministic fake/injected boundary；默认 no-network/no-secret/no-charge。

Rejected alternatives：

1. 先做 P4/P6 再做 P7以避开2.5：P7之后仍无法 rerender/review，且不能证明目标链路。
2. 把全流程塞进 P7 E2E：会把 renderer/review/repair错误归给 P7。
3. 新建 production coordinator：重复 Codex orchestration职责并扩大恢复与public API表面。

## 4. Compatibility Contract

### 4.1 Version semantics

对已有 P3-P6 mutation paths，Manifest 2.5必须保持与2.4相同的 P5 graph、P6 review和single-writer语义，同时原样保留全部 P7 image attempts/evidence。

要求：

- 2.0-2.4 reader/serialization行为不变；
- 2.5 operation不得删除、重排或重写历史 P7 evidence；
- P4 voice request/activation不得把2.5降级为2.2/2.4；
- render transition必须在2.5上原子推进 composition/timeline/source/render nodes；
- render activation必须 stale exact current P6 review/final state，不能 blanket stale无关 state；
- P6 review/repair/final acceptance在2.5上必须绑定 exact active Project/Registry/Graph/Render；
- generic repair commit必须把2.5视为 P5-aware，并保留 P7 attempt history；
- replay/recovery不得 schema downgrade或重放 Provider/renderer/analyzer。

### 4.2 No new owner

不得把 version compatibility抽到第二 writer或ad-hoc E2E mutation helper。测试 support可以构造 inputs/fakes，但所有 durable write必须通过现有 production API。

## 5. Acceptance Data Flow

### 5.1 Initial materialization

1. 建立 two-Shot Production Project、Character/Scene reference与 P5 graph。
2. 用 P7 deterministic Provider生成两个不同 PNG；两 Shot复用相同 Character/Scene reference。
3. 重新打开 active Project，确认 Shot role绑定 exact generated asset。
4. 用 P4 fake Provider生成 dialogue/narration所需 audio与 CaptionTrack，并保留现有 budget/egress fake receipts。
5. 从 active Shots、audio tracks、caption tracks与style reference构造并 seal当前 CompositionSpec。
6. `resolve_composition()`生成唯一 `ResolvedTimeline`。
7. injectable fake HyperFrames runner产出真实可 probe 的 `final.mp4`，并通过 existing render activation推进 exact P5 render closure。

### 5.2 Failed review and repair

1. 激活 deterministic QA policy。
2. durable ReviewRequest + fake analyzer产生一个可复现的 layout/composition FAIL evidence。
3. `ApprovedRepairReceipt`只授权同 node-ID graph shape内的 composition/layout change，target closure固定为：

```text
composition:main
  -> timeline:main
  -> renderer-source:main
  -> render:main
```

4. generic `StateCommitRequest(operation="repair")`提交新 sealed CompositionSpec/related exact candidate；不得修改 image、voice、caption asset identity。
5. 现有 P5 resolver证明只有 exact closure stale/blocked，无关 Shot/voice/caption节点保持fresh。

### 5.3 Rerender and acceptance

1. 从 repaired CompositionSpec解析新 ResolvedTimeline。
2. rerender产出不同、可 probe、content-addressed final MP4。
3. 对当前 graph/timeline/render重新记录 required PASS reviews。
4. `record_repair_outcome()`绑定 approval、actual invalidation、rerender与fresh receipts。
5. `record_final_acceptance()`只接受当前 exact graph/render/policy/pass receipts。
6. `load_production_project()`重新打开全部 selected evidence。

## 6. Repair Boundary

本 slice明确不使用 approved repair触发新的 P7 image generation。

原因：P6 approval根据 before graph计算 exact outgoing closure；新 P7 asset ID会引入 before graph中不存在的 node，不能安全伪装为原 closure内的普通 repair。若未来要求“P6 approved repair直接触发 P7 regeneration”，必须另行设计 future-node scope与approved P7 execution seam。

本 slice的 repair只改变 composition/layout artifact identity，保持 graph node IDs与所有 media asset IDs稳定。

## 7. Files and Ownership

Expected production compatibility files：

- `src/ai_video/production/_state_commit_dependency.py`
- `src/ai_video/production/_state_commit_voice_intent.py`
- `src/ai_video/production/_state_commit_voice_activation.py`
- `src/ai_video/production/hyperframes.py`
- `src/ai_video/production/_state_commit_render_lifecycle.py`
- `src/ai_video/production/_state_commit_review.py`
- `src/ai_video/production/_state_commit_repair.py`
- `src/ai_video/production/_state_commit_transaction.py`

Expected tests/support：

- create `tests/test_production_base_ai_comic_e2e.py`
- optionally create `tests/production_e2e_support.py`
- modify `tests/production_project_factory.py`
- modify focused `tests/test_production_state_commit.py`
- modify focused `tests/test_production_hyperframes.py`

`_state_commit_common._validated_transition()`已能保留2.5/P6 state，不应重写。`dependency.py` pure resolver、Production schemas、Asset Registry schemas与package root exports不需要改变。

## 8. Test Strategy

### 8.1 Focused compatibility tests

- voice request/submit/result/activation preserves Manifest 2.5 and P7 evidence；
- render begin/failure/activation/replay preserves Manifest 2.5 and exact graph transitions；
- review/repair/outcome/final acceptance accept current2.5 state and reject forged/stale identities；
- generic repair on2.5 uses P5-aware exact closure；
- recovery preserves2.5 attempts and never downgrades/remints/replays。

### 8.2 Full E2E assertions

- two generated images reuse Character/Scene but have distinct provenance；
- voice/caption/image provenance all reopen；
- initial and repaired MP4 both pass local probe/hash validation；
- first review deterministically fails for exact layout evidence；
- approved repair changes only composition closure；
- rerender and fresh reviews bind current identities；
- final acceptance is fresh and content-addressed；
- Shot 2、image assets、voice、caption identities remain unchanged by repair；
- replay counts：image Provider 0、voice Provider 0、analyzer 0、renderer 0、Manifest write 0；
- socket/secret access remains zero。

### 8.3 Verification

Focused：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py -q
```

Compatibility：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_image_e2e.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_state_recovery.py \
  tests/test_production_project.py -q
```

Final：

```bash
python -m pytest -p no:cacheprovider -q
python -m scripts.architecture_gate check
```

## 9. Scope and Non-Goals

Includes：Manifest 2.5 compatibility fixes、deterministic combined E2E、exact composition repair、rerender/final acceptance、runtime truth docs after verification。

Non-goals：

- P8 Generated Video implementation；
- Paid Provider Gate或任何 real/live Provider；
- P7 image regeneration from P6 approval；
- new CLI/API server/queue/workflow engine；
- schema/version/layout change；
- renderer/model/provider redesign；
- automatic recovery或blanket stale；
- push/release。

## 10. Rollback

本 slice没有 schema migration。Rollback可移除2.5 mutation compatibility与combined E2E，但必须保留 existing Manifest 2.5 reader/P7 state；不得 downgrade或删除已存在的2.5 Project evidence。由于该 slice不新增 durable fields，rollback不需要数据转换。

## 11. Acceptance Criteria

- Manifest 2.5可沿 existing owners完成 P7 images、P4 voice/captions、P3 render、P6 review/repair/final acceptance；
- no new production orchestrator、writer、schema、CLI、dependency或network path；
- one deterministic layout failure经过exact approved repair与rerender关闭；
- final `final.mp4`、graph、timeline、review、repair与acceptance evidence可由 reader exact reopen；
- unrelated identities remain stable and fresh；
- exact replay performs zero external-effect calls/writes；
- focused、compatibility、full pytest与Architecture Gate通过；
- independent review verdict为accept，无blocking issue。
