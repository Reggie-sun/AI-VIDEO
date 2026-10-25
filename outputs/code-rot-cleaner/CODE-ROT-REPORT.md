# Code Rot Report

**REPORT READY** — 本轮识别出 **2 个函数级 REVIEW 候选，共 16 行、682 bytes**；SAFE TO REMOVE 为 **0 行、0 bytes**。尚未执行真实清理、临时副本测试或 Harness。只新增本目录中的报告与静态证据；本轮未修改任何原有源码、测试、配置或未提交文档。

## Scope And Snapshot

- 当前分支 `main`，HEAD `6ff8f4cf2c68154324fd820fd82c4f448377829b`。
- 源码范围：`src/`、`scripts/`、`tests/`、`provider-console/` 和根目录源码；755 个文件，361,734 个物理行，14,869,578 bytes。行数包含空行、注释和测试，不能当作有效代码量。
- 排除依赖、构建产物、缓存、媒体/历史 artifacts、runs、外部 Skills、symlink 和派生 CodeGraph `index.json`。文档与配置参与引用核查，但不作为本轮删除目标；`.codex/hooks.json` 与 `.claude/settings.json` 手工只读核查。
- 原始完整目录扫描因误纳大量运行产物而停止；有效扫描使用 Skill 原扫描器和仅限定范围/排除项的 adapter `run_scan.py`。未更改 Skill。

## Results By Status

| 状态 | 数量 | 行数 / bytes | 解释 |
| --- | ---: | ---: | --- |
| SAFE TO REMOVE | 0 | 0 / 0 | 尚无临时副本执行证明 |
| REVIEW | 2 | 16 / 682 | 函数块大小；不是整个文件大小 |
| KEEP | 323 | 120,333 / 5,085,941（保留量） | 所有原始扫描线索均有真实引用、入口或内部调用；这些数量不属于可删除代码 |

扫描器原报的 122,148 行 / 5,158,485 bytes 是误报文件总量，**不能作为清理收益**。本轮未发现可据当前证据直接删除的完整源码文件。

## Proposed Cleanup

| ID | 精确文件与函数 | 证据 | Proof | 风险 |
| --- | --- | --- | --- | --- |
| CRT-324 | `src/ai_video/production/dependency.py:838` 的 `_source_render_pairs`，仅定义块 838–851 行 | src-layout AST 与全仓文本核查未找到调用；CodeGraph 关系查询为空，仅作辅助 | REVIEW；拟议删除文本可被 AST 解析，未运行测试 | low；动态/仓库外调用未被执行验证排除 |
| CRT-325 | `src/ai_video/production/manifest_schema.py:110` 的 `is_supported_manifest_version`，仅定义块 110–111 行 | AST 与文本核查仅找到定义 | REVIEW；拟议删除文本可被 AST 解析，未运行测试 | medium；公开模块函数可能被仓库外消费者导入 |

可审阅的精确补丁：[proposed-cleanup.patch](proposed-cleanup.patch)。补丁仅移除上述函数块，不删文件、不改 import、manifest、lockfile、API 调用方或历史证据。第一批建议只验证 CRT-324：14 行、593 bytes；CRT-325 的 2 行、89 bytes 收益较小且具有公开导出风险。

## Rejected Findings

- Python 扫描器无法正确解析本项目 `src/` 绝对导入及 pytest 的 `tests/` import root。补充 AST 实际解析了 720 个 Python 文件，语法错误为 0；导入证据逐项记录在 `review.json` 和 `python-static.json`。
- `ai_video_mcp.analysis_client` 被 `generation_feedback.py:131` 通过 `python -m` 调用，不能删除。
- `ai_video_mcp.analysis_hook` 是 Codex/Claude hook 注册及 detached worker 入口；`tests/helpers/p2a_crash_worker.py` 被状态恢复测试按路径执行，均保留。
- `continuity-review-contract.js` 存在多行 import/re-export；`downloadHumanReviewDecision` 在同文件 submit handler 内调用；`preferredRunBinding` 在同文件显示逻辑内调用。未被其他文件导入不等于函数不执行。
- `_fixed_gain`、`_decoded_pcm16` 及 `validate_preserved_seedance_request` 暂不列入清理：前两者位于声明保留导入面的 HyperFrames 兼容层，后者明确标注 compatibility wrapper；项目要求维持兼容。底层音频函数通过 alias 导入，有实际调用。
- 当前解释器未安装 Vulture、Knip、deadcode、ts-prune、Pyflakes 或 Ruff；未安装任何新依赖。根 package 的 HyperFrames 有实际用途；本扫描器不完整分析 Python/嵌套 package 的依赖，不宣称所有依赖均已核清。

## Proposed Verification

**等待批准后**，只对 CRT-324 运行以下精确命令；先在未修改的临时副本建立基线，再在新的副本只移除 `_source_render_pairs` 后重跑。每条命令上限 300 秒，最多基线与一个变体两轮；预估数分钟，实际耗时尚未测量。测试覆盖依赖图和 selective rebuild 行为；Architecture Gate 检查模块约束。失败停止，不削弱检查，也不将基线失败记为可删除证据。

```bash
make harness-inspect
env -i PATH="$PATH" LANG=C.UTF-8 AI_VIDEO_HARNESS_NO_NETWORK=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_PLUGINS=scripts.harness_pytest_guard python -m pytest -p no:cacheprovider tests/test_production_dependency.py -q
env -i PATH="$PATH" LANG=C.UTF-8 python -m scripts.architecture_gate check
```

这三条命令都执行仓库代码，当前未获 Skill 要求的命令批准，故未运行。临时副本不带真实媒体、runs、凭据或用户工作区身份，测试依赖沿当前解释器且不自动安装。`make harness-inspect` 仅检查配置；不冒充 exact staged-snapshot Harness receipt。原生 `prove_candidates.py` 只支持整文件删除，不适用于这两个仍在使用的模块，因此本轮不会让它删除整个文件。

CRT-325 若要继续，需要另行确认外部兼容边界及 focused proof 范围；当前不在上述验证批次内。副本验证通过后会再次呈现精确 ID、文件、补丁与最终验证范围，取得第二次逐项批准才修改真实源码。真实实施后仍须执行项目要求的 exact-snapshot Harness、按 owned paths commit、push 并核验远端 SHA。

## Evidence And Limits

扫描期间另一个会话修改了 `tests/test_repair_input_admission.py`。本轮未触碰该改动；保留 `python-static-initial.json` 的初始 hashes，并重跑 AST/引用检查。候选所在文件的 hashes 未变；上方扫描总行数为原始扫描时点统计，不能作为全仓冻结快照。随后又观察到 `src/ai_video/production/_composition_visual.py` 与 `src/ai_video/production/repair_input_admission.py` 的并行修改；工作区仍在变化，完整当前快照一致性标为 NOT_EVALUATED。静态线索对应 `python-static.json` 的已记录 bytes，执行证明前必须重新冻结和核查。

- [cleanup-plan.csv](cleanup-plan.csv)：325 个 ID 的最终逐项状态。
- [SCANNER-DETAILS.md](SCANNER-DETAILS.md)：Skill 原生生成的完整证据明细，英文机器字段保留原貌。
- `analysis.json` / `scanner-analysis.json`：补充后的结果与原始有效扫描；`review.json`：逐条人工裁决。
- `python-static.json`：静态导入图、源文件 SHA-256；`inspection-receipt.json`：本轮静态证据身份，**不是 Harness receipt**。
- 全程未 import 项目模块，未执行项目测试/build/lint/package 命令、Provider/media 操作或 Production state mutation；AST 解析和缺少引用都不能证明真实执行安全。
- Record 评估：`no_record`。当前仅为待验证的代码扫描，报告本身已保存证据，未产生实现或媒体结论，不另建重复 session record；learning `not_applicable`。
- Publication：仅本地报告，未 stage/commit/push。项目完成检查含仓库命令，需先获得本 Skill 要求的批准；本轮不宣称清理完成或已发布。
