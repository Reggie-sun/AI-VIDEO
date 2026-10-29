---
record_kind: architecture_implementation
topic_id: h3-chinese-prompt-grammar
learning_eligibility: ineligible
evidence_index_version: "1"
---

# H3 Chinese Prompt Grammar Record

Date: 2026-10-28

## Purpose

`AGENTS.md` 要求实际提交的图像/视频提示词为纯中文，只保留必要技术标识与素材引用语法。
本次会话前，唯一 H3 编译器 `src/ai_video/production/_h3_prompt.py` 的连接词、标签和枚举值
全部为英文拼接（如 `action … -> …`、`locked-off camera`、`Speaker 1 (S1) says exactly`），
共用的 `performance_direction.py`、`_causal_state_expression.py` 也只输出英文。本记录说明
新增的 opt-in 中文 H3 语法、其回放边界和尚未验证的媒体质量。

## Current Runtime Truth

- 语言由 sealed provider profile 决定：共用 mixin `H3PromptLanguageProfile`
  （`src/ai_video/production/_h3_prompt_zh.py`）为 H3 profile 增加
  `prompt_language: "en" | "zh"`，默认 `en` 且为 `en` 时不进入序列化，因此全部既有 H3 profile
  的 `profile_content_hash` 不变。
- `zh` profile 编译 grammar `h3-three-field-zh-v1`；`en` 保持 `h3-three-field-v1` 字节不变
  （`tests/test_production_h3_prompt_zh.py` 以改动前编译器计算的 sha256 golden 固定）。
- 中文版只保留 H3 语法标识：三个字段头、`[Shot 1]`、`<d>[Language]…</d>`、`S1`、
  `<Picture N>` / `<Audio N>`；其余连接词、运镜枚举（方向/幅度/速度/起止状态/主体关系）、
  因果维度与表演阶段标签为中文；`unspecified` 占位被省略。
- 编译器只翻译自己的文字。Shot 中作者撰写的字段若为英文，提交文本仍会中英混杂。
- 中文 profile 为同一 capability 的独立 sealed profile 文件，共 8 个 `<lane>_zh.json`：
  Stock20 `minimax_h3_fl2va_quality`、T8 `t2va_quality`、T8 `t2va_turbo`，以及 T8-native
  turbo `t2va/i2va/fl2va/ref2va v2` 与 `ref2va_17s_v3`。普通 Stock20 `minimax_h3_fl2va.json`
  只有 legacy `/1` 路径、没有 H3 原生 prompt，因此没有 zh 版；zh profile 遇到 `/1` requirement
  时 typed 拒绝，不回退英文。
- `video_compiler.py` 按 native prompt 的 grammar label 决定重编译语言（`h3_prompt_language`），
  因果事实按同一语言核对；中英 label 对调会因重编译不一致而被拒。
- 中文保留词检查：转场类词（切到/转场/叠化等）一律拒绝；无对白镜头中的旁白/对白/台词等
  说话提示被拒，与英文规则对称。

## Session Work And Decisions

- 用户确认保留 H3 原生字段头等语法为必要技术标识，其余改中文；先只做 H3。
- 提交：`1f74383`（编译器、I2VA native zh profile、测试、Harness 映射、`h3-video` skill 说明）；
  后续提交将语言扩展到全部 H3 线路并加入本记录。
- 同日较早的 `3bf4f4d` 对齐项目 Skill 与仓库规则（`record-ai-video-session` push 规则、
  `ad-creative` 移出具体商品 brief、`seedance-authoring` 去重与720p例外、`h3-video` 去除
  上游 OpenVideo 产品内容、Blender 系列旧名与安装提示），与本主题独立。
- 本地 H3 中英对照实测已启动准备但按用户指令停止：用户先选择提交代码、实测后续，随后明确
  “別實際測試了,就改完就好”。

## Verification And Evidence

- 离线 related 测试：H3/编译器/各 H3 adapter 相关测试文件通过（见提交后的 Harness receipt）；
  `1f74383` 的 Harness related receipt 为
  `.agent/harness/runs/20261028T222944343234Z/receipt.json`（19 项 PASS，非 full）。
- 独立 reviewer 第一轮 REQUEST CHANGES：MAJOR 为运镜方向 `forward` 原样漏入中文 prompt，
  已改为中文方向映射并修正测试；MINOR 中的 zh 标签负向用例、`在画内/在画外`、golden sha
  等已补。修复后未再次请求 reviewer 复审。
- Architecture Gate：最终扩展后 0 warning（mixin 由 `_h3_prompt` 再导出，未增加已有债务模块的有效行数）。
- 没有任何 Provider 调用、ComfyUI 启动、媒体生成或付费行为。

## Assessment

中文 H3 编译的 deterministic 结构、回放兼容与校验路径已由离线测试证明；这不证明 H3 模型对
中文描述的遵循度、旁白/硬字幕泄漏风险或画质。历史记录
`2026-08-29-h3-t8-drama-preview-shot-gate-stop.md` 曾观察到传入 H3 的说明文字被念成中文旁白，
因此中文 prompt 的媒体质量为 `NOT_EVALUATED`，不得据离线 PASS 将 zh 设为默认或宣称质量等同。

## Remaining Risks Or Next Work

- 媒体 A/B 未执行。`runs/h3-zh-prompt-ab-20261028-001/` 保留实验设计（`experiment.json`）、
  中文翻译 intent、两组驱动脚本，以及 4 组未完成的本地 production scratch root
  （`production`、`production-r2`、`production-r3`、`production-r4`）；它们只含本地状态，未提交
  Provider，按规则保留、不删除、不进 Git。
- 9 月的 H3 驱动已与当前规范 seam 不兼容：路由现在要求 `DecisionInputs`、带验收表达式的
  `GenerationRecipe`（强制可控 seed）与激活的 QA 验收策略；`runs/jieshi-e01-i2v-20260906-attempt01`
  与 `runs/jieshi-s01-h3-horizontal-20260906-001` 的 production root 因历史 MP4 缺失而 fail closed。
  后续实测应走 `GenerationFeedbackOrchestrator`，两组固定同一 seed。
- 已同步 `docs/v0.2-runtime-baseline.md`（2026-10-28 条目）与
  `docs/agent-primary-contract-matrix.md` 的 Provider-Neutral Generation Requirement 行。

## Agent Guardrails

- 不要把 `h3-three-field-zh-v1` 的离线 PASS 当作媒体质量或默认切换依据。
- 选择中文 H3 时，同时把 Shot 作者字段写成中文；编译器不会翻译作者内容。
- 不要改写英文编译输出；任何字节变化都会破坏历史 exact replay，golden sha 测试会拦截。
- 不要给 legacy `/1` Stock20 线路制作 zh profile 来“满足纯中文”，它没有 H3 原生 prompt。
