# Shot Performance And Prompt Fidelity Repair Implementation Plan

Date: 2026-10-21

## Goal And Authorization

用户本轮“修复”授权实施既有[规格](../specs/2026-10-21-shot-performance-and-prompt-fidelity-repair.md)，并明确要求共享能力，不能只修《界蚀》。本计划记录该后续授权，不改写 draft 的历史授权状态。实现与作者流程面向任意项目、cast、景别及 beat；不写作品、人名、人数或动作特例。

## Contract And Ownership

- `generation_input_control.py` / `requirement_semantics.py`：在现有 QA 表达中增加可选 `native_text_mapping`，形状为 `contract_version="native-text-mapping/1"`、`intent_sha256=canonical_sha256(generation_intent.model_dump(mode="json"))`、`bindings=({intent_path, fragment_indices}, ...)`。QA 作者封存 intent 指纹；intent 修订后必须重新审查并封存 QA，runtime 不代填或刷新。索引只引用同一条 selected QA 的 `native_text`；path 必须来自该条 `intent_paths`、存在于当前 canonical intent 且指向具体叶子。一个片段可对应多项明确列出的职责。缺省字段不序列化，保持旧 bytes/hash。
- `generation_recipe.py`：从 selected QA 核验映射及片段来源，保留 request/requirement/rubric identity 验证；只有存在于最终正文的有效片段才能表达相应路径。没有映射时保留既有无歧义的精确文字表达，不把父路径或 caller 自报 controls 当成逐人物证明。
- `seedance_native_prompt.py` / `seedance.py`：普通 authored binding 使用新 compiler v4，与 v3 preserved-source 独立。v4 只保留实际结构控制与最终正文的明确表达，不继承被替换 prose 的文字控制。目标 compiler/profile/stack 必须先封存；不在 compile 中偷偷升级 target 或改变 route。
- `_sequence_source.py` / `video_generation.py`：复用唯一 compile helper。fresh prepare 使用当前 adapter 的新建编译入口；pre-submit recompile 以已有 sealed request 为 replay evidence，必须完整相等，不用布尔值授予 replay authority。v1/v2/v3 历史正文、hash、effect identity、计数与合法恢复保持。
- `generation_execution.py`：fresh `create` 及当前项目 admission 检查新契约和最终表达，防止手工构造或重新封装旧 v2 compilation 进入新执行。只有 Manifest 中唯一匹配的 generation、binding pointer 与 canonical request receipt 的完整一致才作为历史恢复；历史 reader/model validation 本身不追加义务。
- `performance_authoring.py` / `video_reference_controls.py`：现有报告分别展示参数完整性、选定 QA 映射、最终正文及表达缺口、实际质量。精简映射不要求完整 renderer block；`actual_quality` 继续 `NOT_EVALUATED`。
- `docs/canvas-production-harness.md` / `.agents/skills/seedance-authoring/`：同步作者来源审查、避免无依据冻结、全场风格观察及 exact 正常速度声画审查；不增加第二意图、QA ledger 或自动审美判断。

`docs/agent-primary-contract-matrix.md` 已有他人 dirty changes，本轮不覆盖；共享 owner 保持不变，新增操作细节写入其已委托的 Canvas workflow。其他已暂存或未提交文件均不纳入本任务。

## Compatibility And Failure Boundaries

v4 只用于新普通 authored binding；无 binding 的自动 prose 继续 v1/v2，`source_preservation=true` 的既有 v2 和 Shot-level preserved-source v3 均保留。fresh v3 必须具有真实 preserved-source 并精确重编译，未知版本拒绝。旧普通 binding 的 v2 只能在既有请求的精确重编译边界执行；fresh prepare 不得选择它来省略检查。低层纯编译不产生执行权限，fresh execution binding 另复验。

映射缺失、陈旧、越界、无对应人物/beat 或缺 final fragment，返回现有 `PROMPT_EXPRESSION_UNSUPPORTED` / typed input failure，列明 requirement 和具体路径；start、Manifest 新 attempt、permit、POST 均不得发生。代码不做自然语言等义或矛盾识别，作者必须拒绝错误的心理/动作声明。

voice/continuity 保留既有 owner；新版本只在已验证的同等能力下加入 allowlist，不能支持时 typed 拒绝，不降级、静音或换参考。typed-hash continuity 的原 exact expression 限制不放宽。

## Major Milestones

### 1. Reproduce The Shared Coverage Failure

新增 `tests/test_seedance_prompt_fidelity.py`，经标准 projection/Resolver/prepare/compile seam 建立失败回归。至少覆盖不同 cast、景别、visible/offscreen 和 beat 组合；先证明删除必需片段或虚报父路径不能继续编译。Parent 为实现唯一 writer，一名 native bounded test writer 只拥有该测试文件；一名只读 mapper 已核对 fresh/replay 调用链。

验收：记录可信 RED，缺口绑定最终文字而非作品特例；不读取凭据、不发 Provider effect。

### 2. Bind Final Text And Preserve Versioned Replay

实施上述现有表达、compiler、fresh/replay seam 和 execution guard。选定 QA fragment 由 profile seal 提供，recipe 不能偷换。v4 精简正文逐字保留；普通新 binding 不接受 v2 route。新 optional 字段不影响旧序列化。voice 及 continuity 按真实能力校验。

验收：规格 E1–E9 对应 focused cases 通过；旧 v1/v2/v3、自动 prose、preserved-source 正向路径与失败边界继续成立，无新媒体 effect。

### 3. Report And Author Against Actual Inputs

改进既有表演预检报告，落实规格 B/C/D 的作者与审片步骤，增加相称的报告验证。分清原始约束、导演选择和 repair margin，不凭参数完整、人数或参考覆盖声明自然度/全场画风成立。

验收：规格 E10 可执行；通用指南覆盖静止、遮挡与背景角色，不强制微动作，不复制本案例故事。

### 4. Deliver Bounded Evidence

先运行修改范围内的 focused compiler/performance/input-control/replay/guard 验证；Risk Gate 依据实际剩余风险决定是否需要一名 native read-only reviewer。若测试新文件需要 Harness 路径登记，只补现有 suite 的 routing，不改变质量或安全规则。

真实试片沿规格上限：至多一条代表性短镜头、一次 POST、零重抽；执行前核对当前 outcome、sealed inputs、原已满足条件、来源、剩余计数/预算、exact preview 和 permit。Fast 的原 `EVIDENCE_GAP` 不伪造成关闭或质量失败；旧媒体不改写。存在不可执行前提时明确记录最小恢复条件，不能绕 guard。

先交真实试片审片；用户明确认可效果后才运行适用完整 Harness、按 owned paths commit/push 并核验远端 SHA。未获认可时保留工程与媒体证明边界及 publication 实况，不扩跑完整 suite。工程验证完成也不代表自然度、Shot 或 Final Acceptance 已成立。

## Verification And Self Review

Focused seam 包括新 fidelity cases、`tests/test_seedance_durable_fidelity.py` 的真实临时 Production begin/reopen cases，以及受影响的 `test_seedance_source_prompt.py`、`test_seedance_source_expression.py`、`test_production_seedance_mixed_reference.py`、`test_performance_authoring.py`、`test_generation_input_control.py` 与既有 execution guards；按实际改动选择 node IDs，不机械反复执行整组。原 `production_generation_execution_factory.activate_generated_video_shot(require_first_frame=False)` 错留空 first-frame role，现只在确有 first frame 时加该 role，使标准 fixture 可以合法建立 T2V 项目；不修改任何 runtime 验证约束。

Parent 自审已覆盖规格 A 的最终文字/映射/version/replay、B 的表演来源与区别、C 的审美边界、D 的 exact 声画与 STOP、E1–E10 和真实媒体/发布分离。未创建第二执行器、timeline、NLP scorer、人物库、QA 状态或 Provider fallback；约350.5秒历史读取延迟不在本轮修复范围。
