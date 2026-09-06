---
record_kind: architecture_implementation
topic_id: jieshi-s01-first-last-frame-preparation
learning_eligibility: ineligible
---

# S01 First/Last Frame Preparation

Date: 2026-09-06

## Outcome

用户要求继续《界蚀》S01直至成功。本轮完成首尾帧 canonical 接入的有界代码修复、新末帧候选和独立 attempt05 bootstrap；没有新视频 POST、MP4、逐镜 PASS 或 S02 submit。上一条 attempt04 视频仍为 Gate FAIL，不能充当 accepted continuity source。

## Evidence

- 新图 `runs/jieshi-e01-i2v-20260906-attempt05/shot-01-last-frame-v1.png` 由 `codex_imagegen_tool` 编辑已登记首帧生成，SHA256 `059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330`，941×1672，1,998,073 bytes。
- Agent 观察：左手手背朝镜头、掌心朝玻璃，右手手机留在腿上，原七人倒影构图保留。仅为 still candidate 观察，不是 human input-use approval，也不证明动态倒影或广播正确。
- 已向用户展示新图并请求 exact input-use approval；本检查点尚无回复、无新 `HumanImageImportReceipt`，不得伪造 human actor attestation。
- `production-s01-v5` 经唯一 `ProductionStateCommitter.bootstrap_initial_state()` 创建并 strict reopen。新 `last_frame` 角色暂绑定原已注册首帧；`planning()` 对新末帧 SHA 的检查阻断该占位输入进入生成。
- 前三次 offline bootstrap 探索分别发现重复旧 Shot artifact、空末帧形成第二 pending role、validator 禁止末帧的问题；这些都发生于成功 bootstrap 前，没有 Provider effect 或 unknown submit。成功后不重复 bootstrap。

## Implementation

`video_planner.py` 与 `_asset_readiness.py` 是模式建议与素材 readiness 的既有 owner：非商业、无前镜、AUTO、明确 first/last role 的请求在两张图都 exact ready 时提出 `FIRST_LAST_FRAME_VIDEO`；末帧必须绑定当前 Shot owner/hash/role/唯一 IMAGE。保留 first-only I2V、其他 R2V、显式 T2V 和连续性契约。

`validation.py` 保留唯一 pending VIDEO output，仅允许已绑定的单图 `first_frame` 和可选单图 `last_frame`；缺首帧、多 IDs、非 IMAGE 或其他附属 role 仍拒绝。没有增加 writer、Router 旁路或 Provider selection path。

attempt05 的六份脚本分别准备 bootstrap、canonical import、Planner/Router/compiler 请求、单次提交和显式 GET recovery。`live_i2v.py` 的 `EXPECTED` 仍为 `PENDING_CANONICAL_PREPARATION`，不可提交。`request-draft.json` 已纠正复制来的旧 attempt03 描述，本次实验是给 attempt04 增加真实末帧，不是 prompt-only reroll。

## Verification

- `PYTHONPATH=. pytest -q tests/test_planning_video_planner.py tests/test_production_validation.py tests/test_production_image_import.py tests/test_production_shot_router.py tests/test_production_vidu.py`：386 passed。
- `PYTHONPATH=. python -m pytest -p no:cacheprovider tests/test_runtime_skill_boundary.py tests/test_production_models.py tests/test_production_registry.py tests/test_production_project.py tests/test_config.py tests/test_cli.py tests/test_errors.py tests/test_production_video_requirement.py tests/test_production_video_intent_validation.py tests/test_production_video_fake.py tests/test_production_provider_neutral_adapters.py tests/test_production_video.py tests/test_shot_readiness_gate.py tests/test_production_video_transition.py -q`：711 passed。
- 六个 attempt05 Python 脚本 AST parse、`git diff --check`：PASS；canonical bootstrap/strict reopen：PASS。
- Native `reviewer_xhigh`：`accept with concerns`，无 core blocking defect；旧 draft 描述已修正，canonical docs 同文件并发占用仍未解决。
- Harness inspect 已识别 `production_reader`、`video_planning`、`shot_readiness_gate`，无 fallback path。没有执行 isolated Harness：用户禁止 worktree。以上是当前 working-tree tests，不是 fresh isolated receipt 或完整 Harness acceptance。

## Remaining Boundaries

1. 等待新末帧 exact input-use approval 后才能创建真实 receipt、canonical import 和封存新请求；当前没有新 profile、preview、intent 或 permit。
2. `docs/agent-primary-contract-matrix.md` 和 `docs/v0.2-runtime-baseline.md` 同时存在另一会话的 H3 changes；遵守 same-file ownership 规则，未写入它们。本次文档同步仍待 ownership 解决，不能声称完整交付。
3. 继续使用已授权 Vidu Q3 Pro、4秒1080p、native audio、`is_rec=false`；以有限 submit ceiling、新 identity/intent/permit 执行。未知结果停止，不能把“直到成功”解释为无限重试。
4. 每个新 exact MP4 先调用 project-local `video-analysis` 并给出全部 required findings；全 PASS 前不得 S02。

## Learning Evaluation

已执行 `distill-ai-video-learning` 的候选评估：`no_candidate`。本轮没有新的动态媒体结果或可隔离跨实验比较，不足以证明首尾帧修复有效；既有烧字 pending candidate 保持未采纳，不将测试或 still 观察计作额外独立支持。未重建 RAG index。

## Workspace Preservation

保留原有七个 staged run files 和另一会话的 H3 code/tests/docs changes。未创建 worktree、未 push、未改写历史 attempt 或导入回执。
