# Harness Latency Implementation Plan

**Goal:** 减少制作迭代的重复测试与失效等待，保持精确验证和真实验收。

**Spec:** `docs/superpowers/specs/2026-10-14-harness-latency.md`

**Contract Surfaces:** policy selection、exact-scope argv、sealed receipt、canonical Canvas read-only author/preflight。

**Invariants:** 保留 shared-state/broad fallback、no-network/no-Production-write、source identity、freshness、paid/unknown/per-shot/final acceptance。

**Compatibility:** policy version 与 receipt version 保持不变；缺省 `scope_paths=false`，历史 argv 重建不变。失败 drift receipt 不具 closure eligibility 的成功证据。

## Milestone 1: Stop Invalid Verification Early

**Files:** `scripts/agent_harness.py`、`tests/test_agent_harness_policy.py`。

在每项 check 前调用同一个 exact snapshot callback；drift 或读取错误停止剩余 checks，保留实际已执行证据与失败原因。最后一项结束后保留原最终核对。测试验证第二项未执行、首项前失效、最终失效、读取错误与稳定通过，不 mock 成功验收。

## Milestone 2: Separate Data And Runtime Checks

**Files:** 新增 `scripts/agent_harness_canvas_data.py`、`tests/test_agent_harness_canvas_data.py`；修改 `scripts/agent_harness_policy.py`、policy 与 Harness routing tests。

接收 exact changed paths，定位并去重受影响 `project.json`，用临时空 Production 目录调用既有 author seam，核验目录仍为空；拒绝无定义的遗留输入和 escaping/symlink paths。JSON/schema/identity 只由既有 owner 判断。README 只走 docs；其他项目文件均走离线检查。新增 CLI 的失败报告不输出原输入。

## Milestone 3: Factor Suites And Complete Evidence

**Files:** `.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md`、`.agent/context/control-plane-playbook.md`、`tests/test_agent_harness.py` 与上述 focused tests。

等待另一窗口提交后再获得 policy/matrix ownership。将 image 的完整共享基础套件拆为 reader/state/dependency 三个 `-k "image or p7"` focused checks，保留 image lifecycle/E2E 与 adapter 测试；对应完整 owner 同轮 PASS 后才覆盖其子集，broad Production/full pytest 也只按真实包含关系覆盖。reader/state/dependency 保留自己的完整职责，shared-owner 变化仍 broad。用实际 pytest collection 验证代表性历史 scope 的新旧选择，检查共享 owner 与未知路径未变弱。迭代和最终验证节奏写入现有 workflow context，不增加 approval gate。

最终运行 project-native tests 与 exact Harness，再判断 Risk Gate；managed Kimi 仅承担有界独立 coverage/read-only 复核，Parent 裁决。记录实际减少数量、receipt 与未验证范围；session record/no-candidate 评估后仅 commit/push owned paths。

只读 image reader/lineage 经源码与 CodeGraph 核对，映射完整 reader suite；runtime image contract/committer 保持上方 domain/boundary 与 shared-state 验证，不依据 Provider 名称剪裁。

## Self-Review

所有 spec AC 对应上述三项 milestone；无未决产品方向，不扩展 Provider 或制作能力。无 microstep artifacts、额外 worktree 或重复 reviewer。现有 pytest node selection/JUnit 已满足可追溯验证，无需引入测试调度框架。
