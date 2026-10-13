# Harness Latency Specification

## Goal And Authorization

用户要求修改近期审计发现的过宽验证与重复流程。减少确定性工程等待，让制作迭代更快回到原剧本的实际声画问题；不改变真实媒体验收。Parent 已按当前源码、receipt 与测试完成 scope self-review，任务内实现授权成立。

## Current And Target Behavior

- 最终 Harness 目前跑完所有 checks 才检测 source drift；改为每项检查前核对 exact scope，发现变化或无法读取立即停止剩余 checks，保留已有日志并输出 failed receipt，最后仍核对快照。
- `docs/canvas-projects/**` 当前触发完整 Canvas workflow；README 只走文档检查，其他项目输入走 strict read-only author/preflight。runtime 源码仍走完整 workflow。
- image 套件复制完整 reader/dependency/state/recovery；共享基础测试归原 owner，image 保留本域 E2E 和这些基础文件中 `image or p7` 的 focused boundary tests，包括 permit、activation、unknown、process-crash recovery。完整 owner 同轮通过才 skip 对应子集。共享 schema/committer 改动仍触发 broad Production checks，未知路径仍 full fallback。
- `_image_project_reader.py` 与只被该 reader 调用的 `_image_video_lineage.py` 属 read-only reopen 边界，走完整 reader suite，保留其他 category 的 independently selected checks，不触发 image generation/crash suite。
- 迭代使用 focused tests；所有修复完成后稳定 task-owned bytes，再执行一次最终 exact Harness。不得把自编技术样例称作用户原剧本验收。

## Contracts And Invariants

沿用 policy 为唯一 changed-path/check owner，argv 由 Harness 与 receipt proof 同一 builder 重建。新增 `scope_paths` boolean 只将 exact scope 的 changed paths 作为独立 argv 传入离线数据检查，不自行推导第二套 Git scope。

数据检查委托现有 `scripts.canvas_production.run(action="author")` 的 inspection、source preservation、identity、schema 与 preflight；不接 runtime factory，不 approve，不调用 Provider，不写 Production。受影响项目去重；缺失定义、无效来源与路径逃逸 fail closed。完整删除的项目允许删除，遗留输入无定义拒绝。

不改变 receipt freshness/integrity、unknown fail-closed、付费 guard、per-shot `video-analysis`、前镜 accepted state 或最终 1.0x 声画验收。不复用旧 receipt 作为新候选证据，不改历史规则或记录。

## Acceptance And Evidence

1. drift 与读取失败不会启动后续昂贵 check；failed receipt 的完整性可核验。
2. README 不选择 runtime workflow，JSON/图片等项目输入选择离线检查，runtime/recovery 修改仍选择完整相关验证。
3. 真实有效项目只读检查通过；扩写原 source、缺 source、缺定义、symlink/路径逃逸失败；Production 输出目录为空。
4. image 专属测试与共享 owner 的选择有 executable evidence；代表性旧/新 scope 的 pytest collection 比较保留于记录，报告实际用例数量，不推算未经实测的墙钟加速比。
5. exact task-owned snapshot 的全部 policy checks、fresh receipt 与 Parent diff review 完成后 commit/push。

## Ownership And Exclusions

遵从用户 A：等待另一窗口提交 `policy.yaml` 与 matrix 后再修改。其余 dirty files 不属于本任务。主实现为 clean Harness scripts/tests、new spec/plan、workflow context；不新增依赖，不生成媒体，不修改全局 Kimi maximum policy 或安装的 external-subagent Skill。
