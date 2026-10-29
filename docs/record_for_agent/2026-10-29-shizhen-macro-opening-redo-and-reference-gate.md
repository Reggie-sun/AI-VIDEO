---
record_kind: session_summary
topic_id: shizhen-macro-opening-redo-and-reference-gate
learning_eligibility: ineligible
---

# Shizhen Macro Opening Redo And Reference Planning Gate Record

Date: 2026-10-29

## Purpose

记录 2026-10-28～29 一个会话内的三段工作：MC00 城市长镜头按诊断重做（v4）仍未被接受；宏观开场改为“先出事、再拉开城市、调度对讲报异常”的 CITY-RISE 试片被用户评价为“太无厘头”；以及据此按用户提出的分工原则（Skill 负责专业判断，程序负责执行和强制校验，规则不重复实现）落地的新生成参考规划门禁。前两段是单次媒体尝试，不构成可泛化的模型结论；第三段是已提交、已推送的工程变更。

## Current Runtime Truth

- 提交 `d5c0718`（已推送 `origin/main` 并核对 SHA）引入 `src/ai_video/production/reference_authoring.py`：每次新生成在 `GenerationDecisionExecutionBinding.create` 处（排在既有表演／commercial／Seedance 表达检查之后）要求 `generation_intent.reference_planning`；`primary_camera_motion` 非 `locked` 时至少一个 `composition` event，且既有编译器规则会强制其 `visual_state/purpose` 进入实际 native prompt。历史读取、replay 和缺省序列化哈希不变。
- 导演证据按领域分开：剧情绑定 `reference_planning.director_coverage={coverage_hash, unit_id}`，当前 Project 供给时须是 Project／Shot provenance 中封存的 content-addressed authoring input 并通过结构校验；电商（`commercial_execution_class` 或 compiled `commercial_binding`）以 `ad_creative_plan_hash` 绑定 AdCreativePlan，禁止携带剧情 coverage。
- Director coverage 结构校验只有一份实现：`src/ai_video/production/director_coverage.py`；`.agents/skills/open-video/scripts/validate_director_coverage.py` 只薄封装并加 open-video 作者检查（Runtime 不认 Skill 身份）。
- Canvas `direction.director_coverages` 在 authoring 时封存 coverage；`docs/canvas-projects/subject-reference/project.json` 已按新规则补齐。`seedance-authoring` 不再维护第二份参考职责表；`open-video` 增加“画外声须有画面对应、配音先给用户试听”的规则。
- 运镜判断（提交 `3e2d5f2` 更新）：有结构化 `primary_camera_motion` 时以其非 locked 判断；v1–v3 requirement 不能携带该字段，此时 `camera_intent.movement` 除精确 `unspecified`／`locked`／`locked-off` 外均按运动处理，须声明 composition event。首版曾要求所有运镜文字都声明结构化字段，独立审查发现会阻断 H3 T2VA v1 与 Vidu legacy 的 `locked`，已改为上述规则。提交前不再复核该门禁，与表演门禁先例一致；M0／source qualification 资格试验链不经过它，其产物不得交付属 advisory、暂无 Harness 检查。

## Session Work And Decisions

1. **MC00 v4 重做。** 依据此前分析（首帧城市已展开、首尾帧几何跨度过大、末段空停），用 Codex CLI 内置 `image_gen` 生成被墙遮挡的新首帧（两次调用，v1 因主路外露被弃），Seedance 2.5 首尾帧 16s 480p，attempt `shizhen-macro-MC00-city-redo-008`。逐镜 Gate `FAIL`：action PASS；camera FAIL（末段仍约 1px/帧漂移，接固定机位市政片会骤停；10–12s 偏快）。用户反馈“运镜太平缓，想不出这个镜头怎么吸引人”。
2. **宏观开场改结构。** 用户判断宏观开场内容本身要改，并要求“同时要有声音和字幕介绍异常”。改为市政原片 → CITY-RISE（急速拉升、横掠、俯冲刹停到 B6 第 0 帧）＋调度对讲字幕 → B6 原片。attempt `shizhen-macro-CITY-RISE-preview-009`，20s 480p；对讲用本地 Kokoro-82M-v1.1-zh 盲选三声线、1.25 倍速、ffmpeg 对讲滤波，字幕经 libass 烧录到审看片（非 HyperFrames）。Gate：camera/action PASS，其余 `NOT_EVALUATED`，总结论 `NOT_EVALUATED`。用户评价“太无厘头”。
3. **根因（主会话自查）。** 两条试片都绕过了 `open-video` 的导演覆盖与独立 Concept Check、`seedance-authoring` 必读要求；镜头只是从 A 点到 B 点的转场，运动无动机；对讲内容与画面不对应；TTS 声线未经试听。Skill 文本本已禁止这些做法，缺口在于程序不要求导演层存在。
4. **分工落地。** 用户确认“全部新生成”范围，并要求电商与剧情导演层分开；据此实现上述门禁。夹具迁移由多个 executor/general-purpose 子代理按文件并行完成，主会话负责共享构建器、集成和裁决。
5. **环境发现。** ccam 账号目录（`groups/default`）未启用 `oh-my-claudecode@omc`，在 ccam 账号下运行时 OMC 子代理与 Skill 不加载（仅 OMC 的 `CLAUDE.md` 文本被复制）；未改该配置，待用户决定。VS Code `workbench.externalBrowser` 改为 `~/.local/bin/open-in-reggie-sun42`（Chrome profile group `cp-e7be810d639e` / Profile 1），备份在 `~/.config/Code/User/settings.json.bak-before-externalBrowser-20261028`。

## Verification And Evidence

| 项 | 证据 | 层级 |
| --- | --- | --- |
| MC00 v4 试片 | `outputs/shizhen-episode01/macro-opening-video-20261028/MC00-city-v4/`，SHA `de0608983dd5b6722a6ef14b086c2a41494693fd97af7019de2e297553f990cf`，16.065s，385 帧，854×480；Gate `qa/post-media-gate.json` FAIL | analyzer + Agent 采样；human 否定 |
| CITY-RISE 试片 | `outputs/shizhen-episode01/macro-opening-video-20261028/CITY-RISE-v1/`，SHA `8a787dfcec864bc8d8b5f58755e18f1d77b99d051e661d5cd79abc2a9ac9215e`，20.065s，481 帧；审看拼接 `assembly/` SHA 前缀 `6c5c1167b6486ded`（1080p，含对讲与字幕） | analyzer + Agent 采样；human 否定 |
| 付费调用 | 宏观累计由 7 增至 9（本会话 2 次，无重试）；平台只读报价 192 与 240 CRD，实际结算未暴露，待确认 | Provider receipt |
| 工程门禁 | Harness focused `.agent/harness/runs/20261029T045646273057Z/receipt.json`、related `.agent/harness/runs/20261029T053004662371Z/receipt.json`、full `.agent/harness/runs/20261029T061022816059Z/receipt.json`（8336 passed, 43 skipped），均在 staged tree `57e0e0c` | execution/structure |
| 独立审查 | 只读 general-purpose reviewer：首轮 REQUEST_CHANGES（漏迁移的冻结哈希测试 `tests/test_generation_no_regression.py`），修复后对 `57e0e0c` APPROVE | review |

两条试片的生成目录、`runs/` 状态与审看片均为本地未跟踪产物，未提交。

## Assessment

- “技术上停稳、有运动、无切点”不等于镜头成立：v4 与 CITY-RISE 的运镜项按帧差判 PASS，但用户分别判为平缓无趣、无厘头。Agent 无法原速观看与听音，数值不能代替“是否有戏”的判断。
- 冻结哈希测试必须继续使用历史形态输入（`setup_decision(legacy_intent=True)`）；只有“新鲜生成后投影”的夹具允许按新声明更新指纹，并须注明原因。
- 新门禁只证明导演声明存在且证据一致，不证明创作质量；镜头是否有动机仍归 `open-video` 与独立 Concept Check。

## Remaining Risks Or Next Work

- 宏观开场创作方向未定：用户否定 CITY-RISE 后，主会话提出“对讲每报一起、画面落到对应现场”的多镜方案，尚未获确认，也未按新门禁走 `open-video` 覆盖设计。
- 已解决：自由文本运镜的 composition 义务（`3e2d5f2`，full receipt `.agent/harness/runs/20261029T201639076941Z/receipt.json`，8341 passed）。仍未纳入：资格试验链；Canvas preflight 报告尚不投影门禁问题，作者要到执行绑定创建时才发现缺项。
- 是否在 ccam 共用配置启用 oh-my-claudecode 待用户决定。
- RAG／检索索引未刷新。

## Agent Guardrails

- 新创作视频提交前先走 `open-video` 覆盖设计与 Concept Check，再写结构化 `reference_planning`；不要先写 prompt 再补声明。
- 画外声／对讲要和画面同时设计；配音先出声线候选交用户试听，盲选 TTS 或 ffmpeg 混入的审看片只能标未验证草稿。
- 两帧锚点之间的运动必须有可说明的戏剧目的，不把“从 A 到 B”当成镜头。

> 本记录更新了 [2026-10-28 MC00 过程记录](2026-10-28-shizhen-mc00-process-and-user-feedback.md) 的当前状态：v3 之后的重做与结构调整见此。
