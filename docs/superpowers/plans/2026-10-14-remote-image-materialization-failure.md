# Remote Image Materialization Failure Plan

## Goal And Contract

按[Spec](../specs/2026-10-14-remote-image-materialization-failure.md)解除已知返回且被拒绝图片的local阻断，再完成有界原S01图像准备。Native Codex串行实现；受管Kimi只读mapping不代验收。Parent使用writing-plans组织契约与依赖，不增加用户批准步骤。

## Milestone 1: Precise Frontier And Explicit Closure

新增 `production/image_candidate_frontier.py` 做同一P5 baseline comparison，接入 `image.py`；新增 `production/image_materialization_failure.py` 独占typed closure及strict retained result joins。`_state_commit_remote_image.py`提供显式closure；`models.py`只接可选pointer及状态校验，`_image_project_reader.py`重验closure。不新增Provider、重放POST、修改旧paid receipt或已接受结果。

测试 `tests/test_image_candidate_frontier.py` 与 `tests/test_remote_image_materialization.py` 经既有public Canvas/committer seam：bootstrap边界、unchanged与changed无关frontier、known-result close/replay/recovery retention、unknown/tamper/stale/mixed拒绝，旧None serialization不变。先red，后实现/green；policy沿既有image/Seedream checks注册新leaf/test，matrix只补owner和normal caller。

## Milestone 2: Verified Runtime And Image Repair

focused suites、exact staged Harness、Risk Gate与必要review完成后，用strict loader重开实际旧attempt；显式封存失败并核验old/new状态、同bytes原图及reserved upper bound，零POST。基于原文字准备修正侧窗及左右手的exact新输入、profile/window、预算/egress、durable intent及one-use permit。第一张返回后实际看图全项QA，PASS才准备同源单PNG edit及actual bbox；任一FAIL/NOT_EVALUATED/unknown停止，保留证据，不重抽。

## Milestone 3: Evidence And Publication

record-ai-video-session更新同一原S01/S02记录，分别列出shared engineering、image QA、未生成的raw视频和human1.0x；自动distillation按独立attempt而非proof层计数。只commit/push owned paths，核验main SHA，保留foreign dirty。停止仅因真实Gate/预算/能力缺口，不能在单一工程checkpoint请求“继续”。

## Self-Review

所有Spec要求均归上述milestones。关闭已知retained-result失败与真正paid unknown严格分开；pipeline不得把Registry activation当accepted S01。writer文件与foreign dirty不相交，实际paid执行在工程验证之后，金额/次数历史不重置。
