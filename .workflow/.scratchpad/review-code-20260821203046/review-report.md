# Code Review Report

## 审查概览

| 项目 | 值 |
|------|------|
| 目标路径 | T8 H3 provider-family implementation/test diff |
| 文件数量 | 10 target files |
| 主要语言 | Python |
| 框架 | pytest, Pydantic |
| 审查 commit | `33beb13d5b8ae68ee109e41d2df7f186ea1f1b1b` |

审查范围仅包含 target implementation/test files。审查期间并发 dirty 的 `.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、superpowers docs 和 `src/ai_video/production/seedance_asset.py` 被排除且未修改。

## Verdict

**accept with concerns**。未发现 Critical 或 High 问题；当前实现的 exact-dispatch 测试通过，但在 reopened identity binding、真实 preflight lifecycle coverage 与 production assembly closure 上仍有需要明确处理的风险。

## 问题统计

| 严重程度 | 数量 |
|----------|------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 1 |
| Info | 1 |
| **总计** | **5** |

### 按维度统计

| 维度 | 问题数 |
|------|--------|
| Correctness | 1 |
| Security | 0 |
| Performance | 0 |
| Readability | 0 |
| Testing | 2 |
| Architecture | 2 |

## 主要发现

### Correctness

#### 🟡 [CORR-001] Reopened submission 未绑定 generation_id

- **文件**: `src/ai_video/production/local_h3_provider_family.py:231`
- **描述**: `get_local_status()` 与 `fetch_local()` 只比较 `resolved_generation_hash`，没有同时比较 `LocalVideoSubmission.generation_id`。一个保持 request hash、但带有不同 generation/provider request identity 的合法 sealed submission 仍可能进入 child adapter。
- **建议**: 两个 seam 都同时校验 `generation_id` 与 `resolved_generation_hash`，并增加 forged-but-valid cross-generation regression test。

### Testing

#### 🟡 [TEST-001] Restart test 未证明真实 preflight→permit→submit 链

- **文件**: `tests/test_production_local_video_state.py:347`
- **描述**: 测试使用 `LocalVideoProviderDouble` 的 no-op `preflight()`，且直接 `submit_local_once()`；真实 Comfy T8/Turbo adapter 要求 exact preflight marker，而 service 不会自动调用 preflight。
- **建议**: 使用会强制 preflight 的 child double/adapter seam，显式调用 `family.preflight()`，再验证 restart 不会重复 submit。

#### 🔵 [TEST-002] Family tests 绕过 typed seals

- **文件**: `tests/test_production_local_h3_provider_family.py:200`
- **描述**: 多数 dispatch tests 使用 `SimpleNamespace` 与宽松 duck-typed children，未覆盖生产 Pydantic request/submission/observation seals。
- **建议**: 保留 routing tests，并补充 typed fixtures 与 tampered-but-resealed negative cases。

### Architecture

#### 🟡 [ARCH-001] Production assembly caller 尚未出现

- **文件**: `src/ai_video/production/local_h3_provider_family.py:101`
- **描述**: family facade/registry type 已存在，但 `src/` 中没有 concrete caller 组装 `VideoProviderRegistry` 并注入 family；当前 assembly evidence 仅在 tests。
- **建议**: 另开 bounded integration/assembly slice；在该 caller 出现前，将 runtime closure 描述为 partial，不新增第二个 selector/lifecycle owner。

#### ⚪ [ARCH-002] T8 adapter oversized-module warning

- **文件**: `src/ai_video/production/comfy_t8_video.py`
- **描述**: architecture gate 报告该模块 808 LOC 的 oversized-module warning。这是结构债务信号，不是本次 family dispatch 的阻塞缺陷。
- **建议**: 单独跟踪拆分或 reviewed exception，不与本 slice 混做。

## 未发现问题的维度

本次未发现额外的 Security、Performance 或 Readability 问题。未发现 secret、注入、明显资源泄漏、额外 I/O fan-out 或不可读命名造成的阻塞风险。

## Verification

以下命令在 commit `33beb13` 与其余工作树只含已知 Seedance dirty change 的状态上实际运行：

```text
python -m pytest -p no:cacheprovider tests/test_production_comfy_t8_video.py tests/test_production_comfy_t8_turbo_video.py tests/test_production_local_h3_provider_family.py tests/test_production_local_video_state.py tests/test_production_comfy_video.py -q
74 passed in 6.13s

python -m pytest -p no:cacheprovider tests/test_production_provider_neutral_adapters.py tests/test_production_shot_router.py tests/test_production_video.py tests/test_production_video_state_recovery.py tests/test_production_video_fake.py -q
120 passed in 2.18s

python -m compileall -q <target production modules>
passed

git diff HEAD^ HEAD --check
passed

python -m scripts.architecture_gate check
Architecture gate: PASS (0 errors, 8 warnings, 3 info findings)
```

Architecture warnings include pre-existing oversized modules; only the `comfy_t8_video.py` warning is called out above as adjacent to this diff.

## Review boundary and workspace safety

本 review 没有修复代码、没有修改 tests、没有 stage 或 commit。现有 commit 与 `seedance_asset.py` dirty change 被保留；scratchpad 是本 review 的 untracked artifact，除非用户另行要求，不应纳入产品 commit。

## Recommended next step

先决定是否接受上述 three medium concerns；若不接受，优先补 `generation_id` fail-closed 校验与真实 preflight-enforced restart regression，再单独推进 concrete registry assembly slice。

*报告生成时间: 2026-08-21*
