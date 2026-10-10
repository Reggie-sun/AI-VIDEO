# Canvas Sequence Preparation Plan

## Scope

按[spec](../specs/2026-10-10-canvas-sequence-preparation.md)在当前main串行实现；不修改旧run或媒体。
新增脚本/测试，补既有Harness canvas category路由、使用说明和runtime/matrix链接。

## Milestones

### Corrective Milestones — 2026-10-10

1. `scripts/canvas_sequence_packet.py`与对应tests修复来源混用、异常shape、引文连续性与输出resource身份；
   `production/video_transition.py`抽取共用authoring校验，不改变现有policy语义或生命周期。
2. `docs/canvas-sequences/*.json`保存两条真实链的有据边界分析，packet验证每条原句、缺口和冲突并阻断；
   原source与旧run不修改，新离线结果写新run。原文不完整则保留缺证，不硬填完整十维。
3. `scripts/canvas_sequence_handoff.py`实现source/selection→existing sequence adapter的只读handoff，
   由`tests/test_canvas_sequence_handoff.py`用真实Production fixture验证进入owner及错序/陈旧/缺证阻断。
   既有Storyboard顺序、Shot identity、accepted source和Planner仍各自唯一拥有事实；不调用Provider。
4. 更新制作说明/matrix/baseline和既有Harness category；focused tests、staged Harness后独立有界核对，Parent裁决并记录/发布。

Self-review：每个原目标均有证据与执行seam；不能将本次离线集成宣布为真实连续成片通过。

### Original Milestones

1. 用失败测试固定两套源结构、顺序、reference identity、typed continuity缺口与480p默认。
2. 实现纯离线source→连续准备包；保留逐段原文、共享资产与原timeline编辑数据，拒绝隐式推断。
3. 两份真实捕获件离线验证；更新共用制作流程与既有owner交接说明，运行focused tests和staged Harness。
4. Parent裁决risk/review、记录真实结果，commit/push并核验SHA。

## Verification

`PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_canvas_sequence_packet.py tests/test_canvas_reference_packet.py -q`

只验证输入与准备行为，不调用Provider、视频分析或媒体生成，不宣称自动连续制作/听看通过。
