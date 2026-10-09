# Canvas Sequence Preparation Plan

## Scope

按[spec](../specs/2026-10-10-canvas-sequence-preparation.md)在当前main串行实现；不修改旧run或媒体。
新增脚本/测试，补既有Harness canvas category路由、使用说明和runtime/matrix链接。

## Milestones

1. 用失败测试固定两套源结构、顺序、reference identity、typed continuity缺口与480p默认。
2. 实现纯离线source→连续准备包；保留逐段原文、共享资产与原timeline编辑数据，拒绝隐式推断。
3. 两份真实捕获件离线验证；更新共用制作流程与既有owner交接说明，运行focused tests和staged Harness。
4. Parent裁决risk/review、记录真实结果，commit/push并核验SHA。

## Verification

`PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_canvas_sequence_packet.py tests/test_canvas_reference_packet.py -q`

只验证输入与准备行为，不调用Provider、视频分析或媒体生成，不宣称自动连续制作/听看通过。
