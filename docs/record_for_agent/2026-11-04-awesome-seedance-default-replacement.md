---
record_kind: architecture_implementation
topic_id: awesome-seedance-default-creative-workflow
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Awesome Seedance Default Creative Workflow

## Decision

用户在两版《蒲公英邮差》观看后明确：“很明显别人的好,你直接替换”。据此直接替换默认视频创作方法，不再把awesome-seedance仅作为按需参考。此前“不默认安装/仅提取方法”的研究建议在本范围被该用户决策取代；历史媒体检查、失败点、成本与资格状态不修改。

这是用户的工作流选择，不是用两个非盲、不可控seed样本证明方法普遍优越，也不是自动经验提炼采纳。

## Implementation

- `AGENTS.md`及`.agent/context/control-plane-playbook.md`将默认创作路由切至awesome-seedance。
- `.agents/skills/open-video/SKILL.md`必须读取本地固定`references/awesome-seedance/UPSTREAM.md`，按上游brief、参考、镜头、prompt、生成交接、逐镜review和定点repair流程创作。旧导演/表演/节奏/音乐资料退出默认链，只供明确历史查询或具体问题参考。
- 保留`open-video`和`director_skill=open-video`作为已有契约入口，不增加Agent/Router/Manifest/Registry或状态机，不改Product源码。
- `seedance-authoring`、common及2.0/2.5 overlay收窄为版本能力、模式语法、素材职责与actual input核验，不自动二次创作或套本地repair配方改写上游prompt。保留上游原文与必要技术差异。
- vendored固定源`LearnPrompt/awesome-seedance@67df3707a4f25f860088790fb0a74d8f99a50cbb`，含SKILL、MIT许可和4份配套reference，来源及SHA在SOURCE.json。未安装依赖、未执行第三方脚本、未复制案例prompt或媒体，无自动更新。
- 上游plan/run-manifest映射到现有coverage、Manifest、Registry与receipts；上游validator映射现有验证器；评分不代替PASS/FAIL/NOT_EVALUATED。Preview、预算、egress、permit、UNKNOWN、逐镜Gate、HyperFrames、ResolvedTimeline及人工观感验收不变。
- Claude现有symlink指向同一Skill实体，Codex和Claude共同使用新默认入口。

## Verification

新增默认pin路由、逐文件hash/许可/无脚本、技术适配不二次创作回归，先RED后GREEN。定向执行`tests/test_open_video_skill.py tests/test_seedance_authoring_skill.py tests/test_runtime_skill_boundary.py`：62 passed（含入口防护新增回归）。原目录文件集合检查排除明确的`.omc`运行元数据，未删除或提交他人runtime文件。

精确staged快照的Harness证据写入`.agent/harness/runs/awesome-default-focused-20261104-v3/`和`.agent/harness/runs/awesome-default-related-20261104-v3/`；各receipt的实际状态、范围与级别为准，不能将定向或related通过称为full回归。独立review绑定同一staged tree，未额外生成付费媒体。

## Boundaries And Learning

未触碰已有dirty的`docs/agent-primary-contract-matrix.md`或其他工作，未把历史未验收影片当作已通过。本次替换只证明默认流程和兼容边界落地；后续视频仍须实际制作和用户观看。

`record-ai-video-session`记录后，`distill-ai-video-learning`评估为no_candidate：本次为用户明确授权的默认选择，没有新增可归因的跨实验质量证据。不产生待采纳经验、不暗改Provider/Policy/Gate。

首轮related在文档预算检查停止；精简本次规则说明后，AGENTS为15922 bytes、playbook为17938 bytes，保持原预算不变。首轮失败receipt保留在`awesome-default-related-20261104/`，不覆盖历史。

独立审查指出嵌套SKILL.md会成为可发现的第二入口。保留上游原始bytes/hash与upstream路径，仅本地改名UPSTREAM.md，并增加vendor无嵌套SKILL.md断言；本地wrapper仍是唯一入口。
