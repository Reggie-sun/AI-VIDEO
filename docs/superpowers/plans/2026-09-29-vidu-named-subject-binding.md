# Vidu Named Subject Binding Implementation Plan

## Goal And Scope

实施 [spec](../specs/2026-09-29-vidu-named-subject-binding.md) 的 canonical subjects 接入与声线拒绝路径，随后继续已授权媒体前置核验。Native Codex Parent 串行写入当前 main，不创建 worktree，保留 `.codex/config.toml`。Owner mapping 使用独立只读 native `code_mapper`；工程 final candidate 使用受管 Kimi。

## Contract Surfaces And Invariants

Canonical Character / Scene / Shot voice requirement → owner-bound Router inputs → native prompt projection → sole request compiler → request/resolved/activation seals → existing generation seam。Typed subject 字段不拥有 authoring、Registry、state 或 acceptance。旧 empty field bytes/hash/replay 保持。Q3 `voice_id` 控制缺乏可靠支持，当前 capability 必须拒绝；不能为了完成调用降低原声线 criterion。

## Milestone 1: Sealed Subject Contracts

Create `src/ai_video/production/video_subjects.py` 与 `_vidu_subjects.py`；modify `video.py`、`video_compiler.py`、`video_contracts.py`、`generation_execution.py`。通用 shape 验证 canonical order、完整且唯一 image partition、owner/artifact lineage、voice reference pairs；canonical derivation 复核选中 Character / Scene 的 ID/hash/ref membership。Populate 新 version hashes，empty field省略。执行 reopen/tamper 与旧 request/hash golden 验证。

同步 `shot_router.py` 的 compiler / named capability 配对，防止旧 route 出现候选歧义；execution binding 对 named projection 和 exact prompt 重算，不能只验新 request hash。

既有 request fingerprint 投影移至 `video_request_models.py`，public 调用和历史 bytes 保持；减小 oversized `video.py`，不通过 baseline 更新隐藏增长。

## Milestone 2: Versioned Adapter And Behavioral Tests

Modify `vidu.py`、`vidu_profile.py`、`_vidu_prompt.py`；create `tests/test_production_vidu_subjects.py`。新增 explicit named R2V capability 和 compiler v4，从现有 complete native intent机械增加角色/场景 reference职责及唯一 speaker `@name`。原 flat 路径保持。校验 exact images 后 only-subjects payload；typed voice投影可表示但当前 resolve/compiler拒绝其 control。RED → GREEN 包括标准 compile seam、reference identity换位、篡改/遗漏/重复图片、voice/no-audio、计数、旧replay。同步 provider docs、contract matrix、baseline 与新文件的 policy routing。

## Milestone 3: Exact Verification And Review

运行 focused suite 并检查 staged task-only diff。按 policy inspect执行所有 selected native checks，保存命令、出口、日志、owned source/staged hashes与时间；不创建 worktree，不伪造 isolated Harness receipt。Stable candidate之后按spec risk gate派发受管 Kimi read-only审查，绑定 exact tree、source hashes、spec/plan和verification evidence。Parent裁决并修复有据 blockers，semantic fix重验和适用re-review；提交 task-owned paths。

## Milestone 4: Media Prerequisites And Truthful Stop

重开原 registered 三图与原 COCO 音频，记录 exact bytes。当前有界账号 GET 已验证 credential 和空主体库；若有 canonical clone/source receipt再核对归属与有效性，不能把同名当原声线证明。仅在原声线与有效 Q3 control齐备后冻结分Shot因果链/对白归属、封存最小新 submit/repair/clone quota，保留 predecessor与旧8次physical消费，然后标准生成/逐Shot MCP/合成/观看。当前不足10秒且模型control缺口阻断，保留 known conditions，不调用无意义付费sample或其他Provider。稳定record后执行learning评估，交付准确remaining work。

## Acceptance And Self Review

四个milestones覆盖schema、ownership、protocol、compatibility、verification、review与真实媒体边界；无第二writer/clone/QA owner。工程证据不等于用户复现完成；缺关键control或input时只报告真实blocker。Spec/plan由当前授权与Parent self-review定稿，无新增用户批准步骤。
