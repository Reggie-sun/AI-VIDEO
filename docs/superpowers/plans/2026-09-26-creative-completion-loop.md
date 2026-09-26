# Creative Completion Loop Plan

## Goal And Scope

执行 [spec](../specs/2026-09-26-creative-completion-loop.md)，在 existing development report 与 Agent 创作流程中保留完整目标。Native Codex 串行在当前 main 工作，保留 `.codex/config.toml`，不改 Product Runtime owners。

## Milestone 1: Complete Contract Report

Owner：`scripts/visual_quality_report.py`；tests：`tests/test_visual_quality_report.py`。

先添加广告/电视剧完整合同 round-trip、额外 FAIL/缺项阻断、视觉定义不匹配零副作用与 CLI 用例，确认 RED。再增可选 `final_output_contract`、packet `/2`、泛化 findings 展示和 CLI `--contract`；沿用原 adjudicator，保持 `/1` exact compatibility。GREEN 验证：`PYTHONPATH=src:. .venv/bin/pytest tests/test_visual_quality_report.py tests/test_production_visual_quality.py -q`。

## Milestone 2: Creative Execution Discipline

Owner：`.agents/skills/open-video/references/creative-completion.md`；入口：`.agents/skills/open-video/SKILL.md` 和 `.agent/context/control-plane-playbook.md`。更新 `docs/visual-quality-gate.md` 与 matrix/baseline 对该报告的准确范围描述。

明确复用素材仍需导演前置；创意目标、硬要求与偏好分开；广告/电视剧分别判断，不用固定镜头数或 CTA 替代导演判断；交付前独立复核，已知缺陷进入有限修复，诊断展示不是完成。现有 Director v4 与 Production FinalOutputContract 仍为原 owners。验证 existing Skill routing tests，文档不通过机械增加关键词测试冒充行为证据。

## Milestone 3: Exact Counterexample And Closure

用已生成青颜 MP4 的 exact bytes 创建完整合同开发报告，记录实际包装错误为 FAIL，未观察的音频/完整观看保持 NOT_EVALUATED；证明旧技术成功不能覆盖此 FAIL。不生成新片，不执行 Provider。更正旧 session record 的当前质量结论，保留技术与历史证据。

在稳定 snapshot 对真实 changed paths 运行 Harness，并验证 receipt integrity/freshness；独立 review 只评本次完整目标、兼容和 authority 边界，不能冒充人类审片。按 record skill 记录本轮及 learning evaluation，仅提交 task-owned paths，不 push。AOCI 已交付 33 个对象，但治理陈旧且 attestation 格式未通过，所有修改依据当前源码；不处理本任务以外的索引债务。

## Verification And Stop Conditions

Focused tests 如上，完整组合由 `.agent/harness/policy.yaml` 决定。验收以 spec 五项为准；如果实现证明现有 root cause 假设不成立，回到源头修订，禁止叠加第二 owner。Git 同文件冲突、实际 mandatory verification failure 或 required review 不可用须据实报告，不修改 baseline 隐藏。即使工程闭环通过，也只声明机制与反例验证完成，不声明后续广告/剧集质量已获保证。
