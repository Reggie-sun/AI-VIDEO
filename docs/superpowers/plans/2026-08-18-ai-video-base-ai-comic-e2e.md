# AI-VIDEO Base AI Comic E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Before every write task, verify the current writer and worktree ownership required by `AGENTS.md`.

**Goal:** 在不启用 Video Provider、不增加 production orchestrator 的前提下，让同一个 Manifest 2.5 Production Project 完成 P7 images、P4 voice/captions、P3 render、P6 failed review、exact composition repair、rerender 与 final acceptance，并以 deterministic no-network E2E 证明 exact reopen 和 replay safety。

**Architecture:** 先把既有 P4/P5/P6 mutation owners 对 Manifest 2.5 的版本条件补齐，使它们保持 2.4 的 graph/review semantics 并原样保留 P7 evidence；再用 test-only support 串联现有 public production APIs。Durable mutation 仍只由 `ProductionStateCommitter` 完成，E2E 不引入 production coordinator、第二 writer 或 ad-hoc manifest rewrite。

**Tech Stack:** Python 3.11+、Pydantic v2 strict/frozen models、existing `ProductionStateCommitter`、P5 dependency resolver、P7 deterministic image provider、P4 fake voice/provider/HyperFrames runner、existing ffprobe/hash primitives、pytest。无新 runtime dependency、无 CLI、无 network、无 secret、无 paid/live Provider。

**Spec:** `docs/superpowers/specs/2026-08-18-ai-video-base-ai-comic-e2e.md`

## Global Constraints

- Planning base is clean local `main` at `07cd02f`; Task 0 must re-check the exact execution base because another writer advanced `main` during prerequisite discovery.
- Direct-on-`main` remains the repository default only while no other write-capable agent/session owns overlapping files. If another writer is active or unrelated dirty work appears, stop writes and isolate this slice in a feature branch/worktree.
- Manifest remains schema `2.5`; Asset Registry remains its accepted P7 schema. No schema, path layout, migration, package export, CLI, dependency, or error-code change is authorized.
- Versions `2.0` through `2.4` must keep their existing load, serialization, transition, replay, and recovery behavior.
- On `2.5`, every touched owner must preserve all P7 image attempts, pointers, results, receipts, and active Project/Registry/Graph evidence byte-for-byte unless that owner already owns the exact field being changed.
- `ProductionStateCommitter` remains the only durable writer, activator, and recovery owner. Tests may construct inputs and fakes but may not write Manifest/Project/Registry/Graph state directly.
- `dependency.py`, `models.py`, `registry.py`, `project.py`, `composition.py`, `review.py`, and `repair.py` remain unchanged unless a RED test proves the approved design cannot be met through the listed version-aware owners.
- The repair uses stable graph node IDs and changes only the composition/layout artifact identity. It must not call P7 image generation or create a new asset node.
- Default and focused tests must be deterministic, no-network, no-secret, no-charge, and must not require a local ComfyUI or live HyperFrames installation.
- Every behavior task follows RED → minimal GREEN → focused regression → commit. Do not combine unrelated cleanup or refactoring.

---

## File Map

### Production compatibility files

- `src/ai_video/production/_state_commit_dependency.py` — admit Manifest 2.5 to the existing P5 graph transition validator without changing graph semantics.
- `src/ai_video/production/_state_commit_voice_intent.py` — preserve graph-aware voice request/submit state on 2.5.
- `src/ai_video/production/_state_commit_voice_activation.py` — co-activate voice Registry/Graph state on 2.5 without dropping P7 evidence.
- `src/ai_video/production/hyperframes.py` — require and prepare the existing dependency transition for render on 2.5.
- `src/ai_video/production/_state_commit_render_lifecycle.py` — preserve 2.5 during render replay/activation and stale current review state on changed render identity.
- `src/ai_video/production/_state_commit_review.py` — activate policy, review, and final acceptance on 2.5 without downgrading to 2.4.
- `src/ai_video/production/_state_commit_repair.py` — accept exact approved repair/outcome against active 2.5 evidence.
- `src/ai_video/production/_state_commit_transaction.py` — treat 2.5 as graph-aware for generic approved repair commits and preserve active render/P7 evidence.

### Tests and support

- `tests/test_production_state_commit.py` — focused 2.5 voice/dependency/generic transaction regression tests.
- `tests/test_production_hyperframes.py` — focused 2.5 render/replay/review-staleness regression tests.
- `tests/test_production_review.py` — focused 2.5 policy/review/final acceptance state-preservation tests.
- `tests/test_production_repair.py` — focused 2.5 repair-scope and generic repair rejection assertions.
- `tests/production_project_factory.py` — create only reusable Base E2E inputs derived from accepted P7/P4 factories.
- `tests/production_e2e_support.py` — create bounded deterministic provider/renderer/analyzer helpers; no pytest test functions and no state writes.
- `tests/test_production_base_ai_comic_e2e.py` — create the single combined acceptance path and replay proof.

### Runtime-truth documentation after GREEN

- `AGENTS.md`
- `README.md`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`

### Explicitly unchanged

- `src/ai_video/production/models.py`
- `src/ai_video/production/dependency.py`
- `src/ai_video/production/state_commit.py`
- `src/ai_video/production/registry.py`
- `src/ai_video/production/project.py`
- `src/ai_video/production/composition.py`
- `src/ai_video/production/image.py`
- `src/ai_video/cli.py`, `src/ai_video/config.py`, Legacy `pipeline.py`/`manifest.py`
- `.workflow/**`, `runs/**`, live/generated external artifacts

---

### Task 0: Freeze the Execution Base and Prove the Existing Baseline

**Dependencies:** approved Base E2E spec and current user implementation authorization.

**Files:**

- Read: `AGENTS.md`
- Read: `.agent/context/session-handoff.md` if present
- Read: `docs/agent-primary-contract-matrix.md`
- Read: `docs/v0.2-runtime-baseline.md`
- Read: `docs/v0.2-agentic-production-roadmap.md`
- Read: this plan and its spec
- Modify: no runtime file

**Interfaces:**

- Consumes: accepted P3-P7 production APIs and current Git ownership state.
- Produces: an exact clean execution base and a named focused baseline result for later comparison.

- [ ] **Step 1: Re-check repository and writer ownership**

```bash
git status --short --branch
git log --oneline --decorate -12
git rev-list --left-right --count origin/main...HEAD
git worktree list --porcelain
```

Expected: current tree is clean and no live write-capable agent/session owns any file in the File Map. If either condition is false, do not edit this tree; create an isolated branch/worktree or wait for the owner according to `AGENTS.md`.

- [ ] **Step 2: Confirm exact version gates and approved APIs**

```bash
rg -n 'schema_version.*2\.[345]|\{"2\.3", "2\.4"\}|== "2\.4"|== "2\.3"' \
  src/ai_video/production/_state_commit_dependency.py \
  src/ai_video/production/_state_commit_voice_intent.py \
  src/ai_video/production/_state_commit_voice_activation.py \
  src/ai_video/production/hyperframes.py \
  src/ai_video/production/_state_commit_render_lifecycle.py \
  src/ai_video/production/_state_commit_review.py \
  src/ai_video/production/_state_commit_repair.py \
  src/ai_video/production/_state_commit_transaction.py
rg -n 'make_p7_reuse_runtime|make_voice_request|render_with_hyperframes|record_final_acceptance' src tests
```

Expected: the 2.5 gaps match the spec; no alternate writer/coordinator is discovered.

- [ ] **Step 3: Run the accepted focused baseline**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_validation.py \
  tests/test_production_project.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_review.py \
  tests/test_production_repair.py -q
```

Expected: same accepted baseline as discovery (`1128 passed`) unless intervening accepted commits intentionally changed collection; any difference must be explained before Task 1.

- [ ] **Step 4: Record the execution base in the implementation log**

Do not edit runtime code in this step. Record exact `HEAD`, clean/isolated tree decision, baseline count, and any accepted intervening commit in the task checkpoint message.

**Acceptance criteria:** exact clean/isolated base, no overlapping writer, and baseline GREEN before compatibility edits.

---

### Task 1: Make P5 and P4 Voice Mutations Preserve Manifest 2.5

**Dependencies:** Task 0.

**Files:**

- Modify: `src/ai_video/production/_state_commit_dependency.py`
- Modify: `src/ai_video/production/_state_commit_voice_intent.py`
- Modify: `src/ai_video/production/_state_commit_voice_activation.py`
- Modify: `tests/test_production_state_commit.py`

**Interfaces:**

- Consumes: `ProductionStateCommitter.begin_voice_generation()`, `record_voice_submit_intent()`, `activate_voice_assets()`, existing P5 `DependencyGraphTransition` validation, and a P7-active Manifest 2.5 fixture.
- Produces: the same public methods accepting 2.5 while preserving schema, P7 attempt history, active P7 pointers, and exact graph transition semantics. No new public symbol.

- [ ] **Step 1: Turn the existing documented 2.5 gap into a RED acceptance test**

Rename `test_dependency_result_preserves_manifest_25_and_generic_transition_rejects()` to `test_dependency_result_and_generic_transition_support_manifest_25()` and replace its terminal rejection assertion with:

```python
validated, reopened_graph = writer._validate_dependency_transition(
    applied,
    expected_manifest_revision=applied.manifest_revision,
    artifacts=(),
    transition=transition,
)

assert validated == transition
assert reopened_graph == graph
assert applied.schema_version == "2.5"
assert tuple(
    item for item in applied.attempts if item.operation == "image_generation"
) == tuple(
    item for item in image.attempts if item.operation == "image_generation"
)
assert (
    applied.active_project,
    applied.active_registry,
    applied.active_dependency_graph,
) == (
    image.active_project,
    image.active_registry,
    image.active_dependency_graph,
)
assert (
    applied.active_qa_policy,
    applied.active_review_receipts,
    applied.review_states,
    applied.active_approved_repair,
    applied.repair_outcome_receipts,
    applied.final_acceptance_state,
) == (
    p6.active_qa_policy,
    p6.active_review_receipts,
    p6.review_states,
    p6.active_approved_repair,
    p6.repair_outcome_receipts,
    p6.final_acceptance_state,
)
```

Keep the existing fixture construction and the existing `record_dependency_node_applied()` proof unchanged. Add only a private `_p7_attempts()` helper for the later voice assertions; do not add a production helper.

- [ ] **Step 2: Run the dependency test and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py::test_dependency_result_and_generic_transition_support_manifest_25 -q
```

Expected: FAIL because `_validate_dependency_transition()` rejects schema 2.5 or treats it as non-graph-aware.

- [ ] **Step 3: Add RED voice intent and activation regressions**

Add tests named:

```python
def test_manifest_25_voice_intent_and_submit_preserve_p7_state(tmp_path: Path) -> None:
    root, committer, before = _make_manifest_25_voice_base(tmp_path)
    request = make_voice_request(root)
    preview, authorization = make_voice_preview_and_authorization(request)

    intent = committer.begin_voice_generation(
        request,
        preview,
        authorization,
        dependency_transition_preparer_available=True,
    )
    permit = committer.record_voice_submit_intent(request, preview, authorization)
    submitted = load_production_project(root / "project.yaml").manifest

    assert intent.schema_version == submitted.schema_version == "2.5"
    assert _p7_attempts(submitted) == _p7_attempts(before)
    assert submitted.active_project == before.active_project
    assert permit is not None


def test_manifest_25_voice_activation_coactivates_exact_graph_and_preserves_p7_state(
    tmp_path: Path,
) -> None:
    root, committer, before, activation, audio_ids, caption_ids = (
        _make_manifest_25_voice_activation(tmp_path)
    )
    after = committer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=caption_ids,
    )

    assert after.schema_version == "2.5"
    assert _p7_attempts(after) == _p7_attempts(before)
    assert after.active_project == before.active_project
    assert after.active_registry != before.active_registry
    assert after.active_dependency_graph != before.active_dependency_graph
```

Define private `_make_manifest_25_voice_base()` and `_make_manifest_25_voice_activation()` helpers in `tests/test_production_state_commit.py`. They must build inputs through existing `make_voice_request()`, `make_voice_preview_and_authorization()`, `make_voice_provider_result()`, and accepted P7 runtime APIs; they must not edit Manifest JSON directly.

- [ ] **Step 4: Run the voice tests and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py::test_manifest_25_voice_intent_and_submit_preserve_p7_state \
  tests/test_production_state_commit.py::test_manifest_25_voice_activation_coactivates_exact_graph_and_preserves_p7_state -q
```

Expected: FAIL at the existing `{"2.3", "2.4"}` gates or by failing to co-activate the graph.

- [ ] **Step 5: Implement the minimal 2.5 compatibility**

In the three production files, extend only P5-aware existing version predicates from:

```python
manifest.schema_version in {"2.3", "2.4"}
```

to:

```python
manifest.schema_version in {"2.3", "2.4", "2.5"}
```

and the corresponding negative predicates. Do not change 2.0-2.2 upgrade logic, hashes, graph construction, state field ownership, or introduce a shared version framework.

- [ ] **Step 6: Run focused and compatibility tests**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_image_e2e.py -q
```

Expected: PASS; 2.3/2.4 tests remain unchanged and 2.5 preserves P7 evidence.

- [ ] **Step 7: Commit Task 1**

```bash
git add \
  src/ai_video/production/_state_commit_dependency.py \
  src/ai_video/production/_state_commit_voice_intent.py \
  src/ai_video/production/_state_commit_voice_activation.py \
  tests/test_production_state_commit.py
git commit -m "fix: compose manifest 25 voice state"
```

**Acceptance criteria:** a P7-active 2.5 Project can persist voice request/submit/activation with exact P5 graph transitions and no P7 state loss or schema downgrade.

---

### Task 2: Make Render Lifecycle and HyperFrames Orchestration Preserve Manifest 2.5

**Dependencies:** Task 1.

**Files:**

- Modify: `src/ai_video/production/hyperframes.py`
- Modify: `src/ai_video/production/_state_commit_render_lifecycle.py`
- Modify: `tests/test_production_hyperframes.py`

**Interfaces:**

- Consumes: existing `render_with_hyperframes()`, `dependency_transition_preparer`, `ProductionStateCommitter.activate_render_state()`, and Manifest 2.5 with P7/P4 state.
- Produces: render begin/activation/replay on 2.5 with an atomic composition/timeline/renderer-source/render transition and exact P6 review staleness. Test-only helpers `make_manifest_25_render_fixture()` and `make_manifest_25_reviewed_render_fixture()` stay inside `tests/test_production_hyperframes.py`; no new public API.

- [ ] **Step 1: Add a RED missing-preparer test for 2.5**

Add:

```python
def test_manifest_25_render_requires_dependency_transition_before_runner(tmp_path: Path) -> None:
    fixture = make_manifest_25_render_fixture(tmp_path)

    with pytest.raises(AiVideoError) as exc_info:
        render_with_hyperframes(
            fixture.attempt,
            committer=fixture.committer,
            runner=fixture.runner,
            dependency_transition_preparer=None,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert fixture.runner.calls == []
```

- [ ] **Step 2: Run it and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_hyperframes.py::test_manifest_25_render_requires_dependency_transition_before_runner -q
```

Expected: FAIL because current `hyperframes.py` only requires a preparer for schema 2.3.

- [ ] **Step 3: Add RED activation/replay/state-preservation tests**

Add:

```python
def test_manifest_25_render_activation_preserves_p7_and_stales_exact_reviews(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_reviewed_render_fixture(tmp_path)
    before = fixture.load_manifest()

    result = render_with_hyperframes(
        fixture.attempt,
        committer=fixture.committer,
        runner=fixture.runner,
        dependency_transition_preparer=fixture.prepare_transition,
    )
    after = fixture.load_manifest()

    assert after.schema_version == "2.5"
    assert tuple(
        item for item in after.attempts if item.operation == "image_generation"
    ) == tuple(
        item for item in before.attempts if item.operation == "image_generation"
    )
    assert after.active_project == before.active_project
    assert after.active_render_state == result.render_state
    if after.final_acceptance_state is not None:
        assert after.final_acceptance_state.lifecycle == "stale"
        assert after.final_acceptance_state.active_receipt is None
    assert set(fixture.changed_nodes) == {
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }


def test_manifest_25_render_exact_replay_has_zero_runner_and_manifest_writes(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_render_fixture(tmp_path)
    first = fixture.render()
    counts = fixture.call_counts()
    second = fixture.render()

    assert second == first
    assert fixture.call_counts() == counts
```

- [ ] **Step 4: Run the new tests and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_hyperframes.py::test_manifest_25_render_activation_preserves_p7_and_stales_exact_reviews \
  tests/test_production_hyperframes.py::test_manifest_25_render_exact_replay_has_zero_runner_and_manifest_writes -q
```

Expected: FAIL at 2.5 lifecycle/replay gates or because 2.5 review state is not stale after render identity changes.

- [ ] **Step 5: Implement minimal render compatibility**

Make these exact semantic changes:

```python
GRAPH_AWARE_INLINE_SET = {"2.3", "2.4", "2.5"}
REVIEW_AWARE_INLINE_SET = {"2.4", "2.5"}
```

The names above describe predicates, not new exported constants. Apply them inline in the two owner files:

- `hyperframes.py`: 2.5 requires `dependency_transition_preparer` before runner invocation and calls it before activation.
- `_state_commit_render_lifecycle.py`: 2.5 participates in graph-aware replay/activation and in existing P6 review/final staleness.
- Preserve the incoming schema version; never rewrite 2.5 to 2.3/2.4.

- [ ] **Step 6: Run focused render and cross-phase regression**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_review.py \
  tests/test_production_image_e2e.py -q
```

Expected: PASS with exact replay performing no runner/write work.

- [ ] **Step 7: Commit Task 2**

```bash
git add \
  src/ai_video/production/hyperframes.py \
  src/ai_video/production/_state_commit_render_lifecycle.py \
  tests/test_production_hyperframes.py
git commit -m "fix: compose manifest 25 render lifecycle"
```

**Acceptance criteria:** 2.5 uses the existing atomic P5 render transition, preserves P7 evidence, stales exact review/final state on new render identity, and exact replay is zero-effect.

---

### Task 3: Make Review, Repair, and Generic Repair Transactions Preserve Manifest 2.5

**Dependencies:** Task 2.

**Files:**

- Modify: `src/ai_video/production/_state_commit_review.py`
- Modify: `src/ai_video/production/_state_commit_repair.py`
- Modify: `src/ai_video/production/_state_commit_transaction.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_review.py`
- Modify: `tests/test_production_repair.py`

**Interfaces:**

- Consumes: `activate_qa_policy()`, `begin_review()`, `record_review_receipt()`, `record_approved_repair_receipt()`, generic `commit(StateCommitRequest(operation="repair"))`, `record_repair_outcome()`, and `record_final_acceptance()`.
- Produces: all existing P6 operations on Manifest 2.5 with exact graph/render/policy binding, stable node IDs, preserved P7 history, and no schema downgrade. Test-only fixtures `make_manifest_25_review_fixture()`, `make_manifest_25_passing_review_fixture()`, and `make_manifest_25_failed_layout_review_fixture()` remain in their owning test modules; no new public symbol.

- [ ] **Step 1: Add a RED QA policy preservation test**

```python
def test_manifest_25_qa_policy_activation_does_not_downgrade_or_drop_p7(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_review_fixture(tmp_path)
    before = fixture.load_manifest()
    after = fixture.committer.activate_qa_policy(
        fixture.policy,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="base-e2e-qa-policy",
    )

    assert after.schema_version == "2.5"
    assert _p7_attempts(after) == _p7_attempts(before)
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.active_qa_policy is not None
```

- [ ] **Step 2: Add RED review/final acceptance tests**

```python
def test_manifest_25_review_and_final_acceptance_bind_current_render_and_preserve_p7(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_passing_review_fixture(tmp_path)
    before = fixture.load_manifest()

    receipt = fixture.run_required_review()
    acceptance = fixture.acceptance(receipt)
    accepted = fixture.committer.record_final_acceptance(
        acceptance,
        expected_manifest_revision=fixture.load_manifest().manifest_revision,
        attempt_id="base-e2e-final-acceptance",
    )

    assert accepted.schema_version == "2.5"
    assert _p7_attempts(accepted) == _p7_attempts(before)
    assert accepted.final_acceptance_state is not None
    assert accepted.final_acceptance_state.active_receipt is not None
    final_receipt = load_final_acceptance_receipt(
        tmp_path, accepted.final_acceptance_state.active_receipt
    )
    assert final_receipt.render_state == accepted.active_render_state
```

- [ ] **Step 3: Add RED exact repair transaction test**

```python
def test_manifest_25_generic_repair_uses_exact_p5_closure_and_preserves_assets(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = fixture.load_manifest()
    approved_manifest = fixture.committer.record_approved_repair_receipt(
        fixture.repair_request,
        fixture.approval,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="base-e2e-repair-approval",
    )
    after = fixture.committer.commit(
        fixture.state_commit_request(approved_manifest.active_approved_repair)
    )

    assert after.schema_version == "2.5"
    assert _p7_attempts(after) == _p7_attempts(before)
    assert after.active_registry == before.active_registry
    assert set(fixture.actual_invalidated_nodes(after)) == {
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }
    assert fixture.unchanged_media_nodes(after) == fixture.unchanged_media_nodes(before)
```

Also assert a forged repair that adds an image asset node or uses a blanket node set fails before mutation.

- [ ] **Step 4: Run the new tests and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_review.py::test_manifest_25_qa_policy_activation_does_not_downgrade_or_drop_p7 \
  tests/test_production_review.py::test_manifest_25_review_and_final_acceptance_bind_current_render_and_preserve_p7 \
  tests/test_production_repair.py::test_manifest_25_generic_repair_uses_exact_p5_closure_and_preserves_assets -q
```

Expected: FAIL because review/repair owners currently require or emit 2.4 and the generic transaction does not treat 2.5 as graph-aware.

- [ ] **Step 5: Implement minimal 2.5 review/repair compatibility**

Apply these precise rules:

- `activate_qa_policy()`: 2.3 still upgrades to 2.4; 2.4 stays 2.4; 2.5 stays 2.5.
- review request/receipt/final acceptance gates accept `{"2.4", "2.5"}` and keep exact active policy/graph/render checks.
- approved repair and repair outcome gates accept `{"2.4", "2.5"}` without widening scope.
- generic transaction treats `{"2.3", "2.4", "2.5"}` as graph-aware for candidate verification, applied evidence, active render retention, and exact invalidation.
- Do not modify pure `review.py`, pure `repair.py`, P5 resolver, or model invariants.

- [ ] **Step 6: Run focused P5/P6/P7 regression**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_recovery.py \
  tests/test_production_image_e2e.py -q
```

Expected: PASS; 2.3 bootstrap behavior, 2.4 P6 behavior, and 2.5 P7 evidence all remain valid.

- [ ] **Step 7: Commit Task 3**

```bash
git add \
  src/ai_video/production/_state_commit_review.py \
  src/ai_video/production/_state_commit_repair.py \
  src/ai_video/production/_state_commit_transaction.py \
  tests/test_production_state_commit.py \
  tests/test_production_review.py \
  tests/test_production_repair.py
git commit -m "fix: compose manifest 25 review and repair"
```

**Acceptance criteria:** current 2.5 state can perform P6 policy/review/repair/outcome/final acceptance with exact identity binding, no schema downgrade, no new node scope, and no P7 history loss.

---

### Task 4: Create Deterministic Cross-Phase E2E Support

**Dependencies:** Task 3.

**Files:**

- Create: `tests/production_e2e_support.py`
- Modify: `tests/production_project_factory.py`
- Test: `tests/test_production_base_ai_comic_e2e.py`

**Interfaces:**

- Consumes: accepted P7 `make_p7_reuse_runtime()`, P4 voice factories, `resolve_composition()`, injectable HyperFrames runner contract, P6 review/repair request models, and existing video probe/hash helpers.
- Produces test-only:
  - `BaseAiComicE2ERuntime`
  - `BaseAiComicCallCounts`
  - `DeterministicVoiceProvider`
  - `DeterministicHyperFramesRunner`
  - `DeterministicReviewAnalyzer`
  - `require_audio_toolchain() -> AudioProbeToolchain`
  - `make_base_ai_comic_e2e_runtime(root: Path) -> BaseAiComicE2ERuntime`

- [ ] **Step 1: Add the initial RED support contract test**

Create `tests/test_production_base_ai_comic_e2e.py` with:

```python
def test_base_ai_comic_support_is_deterministic_and_has_no_direct_state_writer(
    tmp_path: Path,
) -> None:
    first = make_base_ai_comic_e2e_runtime(tmp_path / "first")
    second = make_base_ai_comic_e2e_runtime(tmp_path / "second")

    assert first.synthetic_inputs_hash == second.synthetic_inputs_hash
    assert first.call_counts == BaseAiComicCallCounts()
    assert not hasattr(first, "write_manifest")
    assert not hasattr(first, "activate_registry")
```

- [ ] **Step 2: Run it and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py::test_base_ai_comic_support_is_deterministic_and_has_no_direct_state_writer -q
```

Expected: FAIL because the support module/runtime does not exist.

- [ ] **Step 3: Implement bounded fakes and call counters**

`tests/production_e2e_support.py` must define immutable counters and deterministic transports only. The runner writes the same small, locally generated/probeable MP4 fixture bytes used by accepted P4 tests; it must implement the existing `RendererRunner` protocol and expose calls for `version`, `doctor`, and `run`. The analyzer returns one scripted layout FAIL for the initial render and PASS only for the exact repaired render identity.

```python
@dataclass(frozen=True)
class BaseAiComicCallCounts:
    image_submit: int = 0
    voice_submit: int = 0
    review_analyze: int = 0
    renderer_run: int = 0


class DeterministicReviewAnalyzer:
    def analyze(self, request: ReviewRequest) -> ReviewEvidence:
        self.calls += 1
        if request.render_state == self.initial_render_state:
            return self.failed_layout_evidence(request)
        return self.passing_layout_evidence(request)
```

Do not import private helpers from another `test_*.py` module. Copy only the minimal deterministic transport logic or move a genuinely shared helper while keeping the existing P4 tests green.

- [ ] **Step 4: Add the runtime factory through accepted APIs**

`tests/production_project_factory.py` constructs the runtime by composition:

```python
def make_base_ai_comic_e2e_runtime(root: Path) -> BaseAiComicE2ERuntime:
    image_runtime = make_p7_reuse_runtime(root)
    toolchain = require_audio_toolchain()
    return BaseAiComicE2ERuntime(
        root=root,
        image_runtime=image_runtime,
        voice_provider=DeterministicVoiceProvider(),
        renderer=DeterministicHyperFramesRunner(toolchain.ffmpeg_path),
        analyzer=DeterministicReviewAnalyzer(),
    )
```

The runtime may orchestrate calls for test readability, but every durable write delegates to existing `ProductionStateCommitter` public methods. It must rebuild the `CompositionSpec` from the reloaded active Project after P7 image activation.

- [ ] **Step 5: Run support plus source slice tests**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py::test_base_ai_comic_support_is_deterministic_and_has_no_direct_state_writer \
  tests/test_production_image_e2e.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_hyperframes.py -q
```

Expected: PASS and existing P4/P7 helpers retain behavior.

- [ ] **Step 6: Commit Task 4**

```bash
git add \
  tests/production_e2e_support.py \
  tests/production_project_factory.py \
  tests/test_production_base_ai_comic_e2e.py
git commit -m "test: add base ai comic e2e support"
```

**Acceptance criteria:** deterministic support exists entirely under tests, uses no direct durable writer, and exposes exact effect counters for the final replay gate.

---

### Task 5: Prove P7 Images, P4 Voice/Captions, P3 Timeline, and Initial MP4 Render

**Dependencies:** Task 4.

**Files:**

- Modify: `tests/test_production_base_ai_comic_e2e.py`
- Modify: `tests/production_project_factory.py`

**Interfaces:**

- Consumes: `make_base_ai_comic_e2e_runtime()`, accepted P7/P4/P3 public APIs, and existing probe/hash helpers.
- Produces: a durable initial-render checkpoint in the combined E2E, with exact P7 image, voice, caption, timeline, graph, and MP4 provenance.

- [ ] **Step 1: Write the RED materialization-to-render E2E**

```python
def test_base_ai_comic_materializes_and_renders_from_current_active_assets(
    tmp_path: Path,
) -> None:
    runtime = make_base_ai_comic_e2e_runtime(tmp_path)

    images = runtime.generate_two_shot_images()
    voice = runtime.generate_voice_and_captions()
    initial = runtime.render_current_composition(revision=1)
    loaded = load_production_project(tmp_path)

    assert images.shot_1.references == images.shot_2.references
    assert images.shot_1.asset_id != images.shot_2.asset_id
    assert loaded.manifest.schema_version == "2.5"
    assert loaded.shot("shot-1").required_asset_roles["visual"] == images.shot_1.asset_id
    assert loaded.shot("shot-2").required_asset_roles["visual"] == images.shot_2.asset_id
    assert voice.audio_asset_ids
    assert voice.caption_track_ids
    assert initial.timeline.composition == initial.composition.pointer
    assert initial.render_state == loaded.manifest.active_render_state
    assert initial.probe.duration_milliseconds > 0
    assert initial.probe.video_stream_count == 1
    assert initial.sha256 == sha256_path(initial.path)
```

- [ ] **Step 2: Run it and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py::test_base_ai_comic_materializes_and_renders_from_current_active_assets -q
```

Expected: FAIL at the first missing runtime orchestration method or current-asset CompositionSpec construction.

- [ ] **Step 3: Implement the smallest test-only orchestration**

Implement only these test runtime operations:

```python
runtime.generate_two_shot_images()
runtime.generate_voice_and_captions()
runtime.render_current_composition(revision=1)
```

`render_current_composition()` must reload the Production Project, derive each Shot's exact active visual asset binding, seal a fresh `CompositionSpec`, call `resolve_composition()`, then use `render_with_hyperframes()` with the Task 2 dependency transition seam. It must not reuse a CompositionSpec created before image activation.

- [ ] **Step 4: Run focused E2E and component regressions**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_image_e2e.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_hyperframes.py -q
```

Expected: PASS with a real probeable MP4 and no external network/provider.

- [ ] **Step 5: Commit Task 5**

```bash
git add tests/test_production_base_ai_comic_e2e.py tests/production_project_factory.py tests/production_e2e_support.py
git commit -m "test: render base ai comic from durable assets"
```

**Acceptance criteria:** one Project carries two distinct generated-image provenances, voice/captions, a sealed current CompositionSpec, ResolvedTimeline, graph-aware render state, and a validated MP4.

---

### Task 6: Prove Failed Review, Exact Composition Repair, Rerender, and Final Acceptance

**Dependencies:** Task 5.

**Files:**

- Modify: `tests/test_production_base_ai_comic_e2e.py`
- Modify: `tests/production_project_factory.py`
- Modify: `tests/production_e2e_support.py`

**Interfaces:**

- Consumes: Task 5 initial checkpoint and existing P6 review/repair/final acceptance APIs.
- Produces: a final accepted Manifest 2.5 with exact repaired composition closure, a second validated MP4, repair outcome, fresh PASS receipts, and durable final acceptance.

- [ ] **Step 1: Write the RED full repair/acceptance flow**

```python
def test_base_ai_comic_failed_layout_review_repairs_exact_closure_and_accepts(
    tmp_path: Path,
) -> None:
    runtime = make_base_ai_comic_e2e_runtime(tmp_path)
    initial = runtime.materialize_and_render_initial()
    stable_media = runtime.media_identity_snapshot()

    failed = runtime.review_initial_render()
    approval = runtime.approve_exact_layout_repair(failed)
    repaired_state = runtime.commit_layout_repair(approval)
    repaired = runtime.render_current_composition(revision=2)
    passing = runtime.review_repaired_render()
    outcome = runtime.record_repair_outcome(approval, repaired, passing)
    accepted = runtime.record_final_acceptance(passing)

    assert failed.verdict == "fail"
    assert failed.issue_ids == ("layout.safe-area",)
    assert set(repaired_state.invalidated_node_ids) == {
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }
    assert runtime.media_identity_snapshot() == stable_media
    assert repaired.sha256 != initial.sha256
    assert repaired.probe.duration_milliseconds > 0
    assert all(receipt.verdict == "pass" for receipt in passing)
    assert outcome.actual_invalidated_node_ids == repaired_state.invalidated_node_ids
    assert accepted.render_state == repaired.render_state
    assert accepted.lifecycle == "fresh"
```

- [ ] **Step 2: Run it and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py::test_base_ai_comic_failed_layout_review_repairs_exact_closure_and_accepts -q
```

Expected: FAIL at the first missing P6 orchestration helper or exact generic repair request.

- [ ] **Step 3: Implement exact layout repair orchestration**

The repair request must satisfy all of these concrete constraints:

```python
operation = "repair"
approved_node_ids = (
    "composition:main",
    "timeline:main",
    "renderer-source:main",
    "render:main",
)
```

- create a new sealed CompositionSpec revision with one deterministic layout transform change;
- keep both image asset IDs, audio asset IDs, caption track IDs, Character/Scene reference identities, and graph node IDs unchanged;
- use `record_approved_repair_receipt()` before the exact generic repair `StateCommitRequest` is passed to `commit()`;
- require P5 to calculate the same exact closure rather than passing a blanket stale set;
- rerender through the standard render lifecycle, then record fresh required PASS receipts, repair outcome, and final acceptance.

- [ ] **Step 4: Add forged-scope and stale-evidence negatives**

```python
@pytest.mark.parametrize("mutation", ["add_image_node", "blanket_all_nodes", "stale_render"])
def test_base_ai_comic_repair_rejects_scope_or_identity_drift_before_mutation(
    tmp_path: Path,
    mutation: str,
) -> None:
    runtime = make_base_ai_comic_e2e_runtime(tmp_path)
    before = runtime.materialize_review_and_approve()

    with pytest.raises(AiVideoError):
        runtime.commit_forged_repair(mutation)

    assert runtime.load_manifest() == before
```

- [ ] **Step 5: Run focused repair/review/E2E regression**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_recovery.py -q
```

Expected: PASS; only the four composition/render nodes transition, and stable media identities do not change.

- [ ] **Step 6: Commit Task 6**

```bash
git add tests/test_production_base_ai_comic_e2e.py tests/production_project_factory.py tests/production_e2e_support.py
git commit -m "test: accept repaired base ai comic"
```

**Acceptance criteria:** deterministic initial failure is closed by exact approved composition repair and rerender; current required reviews pass and final acceptance binds the exact repaired render.

---

### Task 7: Prove Exact Reopen, Recovery, and Zero-Effect Replay

**Dependencies:** Task 6.

**Files:**

- Modify: `tests/test_production_base_ai_comic_e2e.py`
- Modify: `tests/production_e2e_support.py`

**Interfaces:**

- Consumes: final accepted state from Task 6, `load_production_project()`, `recover_production_state()`, and all deterministic effect counters.
- Produces: the final Base AI Comic replay/recovery acceptance proof.

- [ ] **Step 1: Write the RED reopen/replay test**

```python
def test_base_ai_comic_final_state_reopens_and_exact_replay_has_zero_effects(
    tmp_path: Path,
) -> None:
    runtime = make_base_ai_comic_e2e_runtime(tmp_path)
    final = runtime.run_full_acceptance()
    before_manifest_bytes = runtime.manifest_bytes()
    before_counts = runtime.call_counts

    recovery = recover_production_state(tmp_path)
    replay = runtime.run_full_acceptance()
    reopened = load_production_project(tmp_path)

    assert recovery.manifest_revision_after == recovery.manifest_revision_before
    assert replay == final
    assert runtime.call_counts == before_counts
    assert runtime.manifest_bytes() == before_manifest_bytes
    assert reopened.manifest.final_acceptance_state is not None
    assert (
        reopened.manifest.final_acceptance_state.active_receipt
        == final.acceptance_pointer
    )
    assert reopened.manifest.active_render_state == final.render_state
    assert sha256_path(final.path) == final.sha256
```

The call-count snapshot must include image Provider, voice Provider, analyzer, renderer, and Manifest replace/write counters.

- [ ] **Step 2: Run it and verify RED**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py::test_base_ai_comic_final_state_reopens_and_exact_replay_has_zero_effects -q
```

Expected: FAIL if any orchestration helper reissues a provider/analyzer/renderer call or rewrites the Manifest on exact replay.

- [ ] **Step 3: Implement replay short-circuits only through existing durable evidence**

Test runtime methods must first reopen current committed state and call the existing production replay APIs. They may return already selected evidence when the exact desired identity is active; they must not maintain an in-memory-only success cache that would hide restart behavior.

- [ ] **Step 4: Add a fresh-process replay assertion**

Instantiate a second `BaseAiComicE2ERuntime` against the same root with fresh fake objects and assert it reopens the same final state without calling their side-effect methods.

- [ ] **Step 5: Run the complete Base E2E and recovery regression**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_state_recovery.py \
  tests/test_production_project.py -q
```

Expected: PASS with recovery unchanged and all second-runtime effect counters at zero.

- [ ] **Step 6: Commit Task 7**

```bash
git add tests/test_production_base_ai_comic_e2e.py tests/production_e2e_support.py
git commit -m "test: prove base ai comic replay safety"
```

**Acceptance criteria:** exact final MP4/provenance reopens after process restart; recovery is idempotent; replay performs zero external/provider/analyzer/renderer calls and zero Manifest writes.

---

### Task 8: Synchronize Runtime Truth and Close the Base E2E Gate

**Dependencies:** Task 7.

**Files:**

- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Verify: all files changed by Tasks 1-7

**Interfaces:**

- Consumes: actual final code, test evidence, and independent review findings.
- Produces: repository governance that describes Base AI Comic E2E as accepted runtime truth while keeping P8 and Paid Provider Gate unimplemented.

- [ ] **Step 1: Update docs from verified behavior only**

Record:

- Base AI Comic E2E is accepted and proves the P3-P7 combined no-Video-Provider production path.
- Manifest 2.5 now composes existing voice/render/review/repair owners without schema changes.
- P8 still cannot start until Paid Provider Gate is separately designed, planned, implemented, and accepted.
- No new public CLI, production coordinator, real Provider, schema, or asset layout was added.
- Replace stale statements that P7 is unmerged/unaccepted only where Git/test evidence now proves otherwise.

- [ ] **Step 2: Run focused acceptance**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py \
  tests/test_production_image_e2e.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_state_recovery.py \
  tests/test_production_project.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full suite and architecture gate**

```bash
python -m pytest -p no:cacheprovider -q
python -m scripts.architecture_gate check
```

Expected: all tests PASS and Architecture Gate PASS. Record exact counts/output; do not infer them from earlier runs.

- [ ] **Step 4: Inspect the complete diff and history**

```bash
git status --short
git diff --check
git diff 07cd02f...HEAD --stat
git diff 07cd02f...HEAD -- \
  src/ai_video/production \
  tests/test_production_base_ai_comic_e2e.py \
  tests/production_e2e_support.py \
  tests/production_project_factory.py \
  docs README.md AGENTS.md
```

Expected: every changed line traces to 2.5 compatibility, combined E2E, or verified runtime-truth docs; no secret, live artifact, `.workflow`, `runs`, CLI, schema, or unrelated refactor is present.

- [ ] **Step 5: Request independent architecture review**

Reviewer scope:

- verify no production orchestrator or second writer was introduced;
- verify 2.0-2.4 compatibility and 2.5 P7 evidence preservation;
- verify exact repair closure and no P7 regeneration from approval;
- verify replay proof is durable/restart-based rather than an in-memory fake shortcut;
- verify default suite cannot access network or paid providers.

Acceptance: reviewer verdict `accept` with no blocking issue. Parent verifies every blocking claim directly before changing code or declaring completion.

- [ ] **Step 6: Commit verified runtime-truth docs**

```bash
git add \
  AGENTS.md \
  README.md \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md
git commit -m "docs: accept base ai comic e2e"
```

If review requires a code/test correction, make that correction in a separate focused commit, rerun Steps 2-4, then commit docs last.

**Acceptance criteria:** focused/full tests and Architecture Gate are freshly GREEN, independent review has no blocker, docs match runtime truth, tree is clean, and Paid Provider Gate remains the only unresolved prerequisite before returning to P8 Task 0.

---

## E2E Acceptance Flow

```text
load two-Shot ProductionProject
  -> generate two P7 PNG assets with shared Character/Scene references
  -> reopen exact active Shot visual bindings
  -> generate P4 fake voice + CaptionTrack
  -> build and seal current CompositionSpec
  -> resolve ResolvedTimeline
  -> render probeable initial MP4 through injected HyperFrames runner
  -> activate QA policy
  -> persist deterministic layout FAIL review
  -> approve exact composition repair closure
  -> generic repair commit with stable graph node IDs
  -> prove only composition/timeline/source/render become stale
  -> rerender a different probeable MP4
  -> persist current PASS reviews
  -> persist RepairOutcome + FinalAcceptance
  -> restart and reopen exact Project/Registry/Graph/Render/Review/Repair evidence
  -> exact replay with zero image/voice/analyzer/renderer calls and zero Manifest writes
```

## Final Gate

Base AI Comic E2E is complete only when all of the following are true:

- Manifest 2.5 retains every P7 evidence field across voice, render, review, repair, recovery, and replay.
- The initial and repaired MP4s are both non-empty, locally probeable, and content-hashed; the repaired artifact identity differs.
- The repair changes exactly `composition:main`, `timeline:main`, `renderer-source:main`, and `render:main` desired/applied state.
- Image, Character/Scene reference, voice, and caption identities remain unchanged by repair.
- Final Acceptance binds current Project, Registry, Graph, Render, policy, and required PASS reviews.
- A fresh runtime instance reopens the accepted state and performs zero paid/external/material side effects on exact replay.
- Default `pytest` is deterministic, no-network, no-secret, no-charge.
- No schema, CLI, production orchestrator, dependency, P8 provider, or Paid Provider Gate implementation was added.
