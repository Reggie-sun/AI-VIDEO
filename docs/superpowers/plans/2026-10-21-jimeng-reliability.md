# Jimeng Reliability And Qualification Plan

## Goal And Boundaries

加固现有 Jimeng Provider，完成免费工程与历史任务只读验证，给出有界 Production Qualification 判断。本轮禁止新的生成、充值和购买。Paid Owner、Manifest、ProductionStateCommitter、Registry 与标准 Reader 保持唯一权威，UNKNOWN 只查询，不重交、不重置预算。Provider 不负责创作验收。

## Ownership

Parent 串行负责 Browser Worker、Python transport、必要 Provider 修复及针对性测试；只读调查 Agent 负责恢复与素材契约取证；一名 native Reviewer 审查最终候选，不派生 Agent。现有 Jimeng dirty/staged 改动须确认接管后再写；其他工作保留。

## Milestones

1. 核对当前源码、工程记录与真实历史资源；冻结接管前 diff。检查 Fiber owner 唯一性、会话漂移、请求 fence 超时/清理、子进程协议和依赖配置。先复现具体缺陷，再做最小修复。
2. 检查 dispatch/recovery、并发、未知状态、素材顺序/hash/引用与输出归属。用现有服务和标准 Reader 做边界/故障验证，不引入第二生命周期。
3. 通过实际 Worker 的离线 Node/子进程测试与可用浏览器只读检查验证修复；历史回读与模拟分级记录，禁止将离线结果写成真实生产 PASS。执行相关 Provider 回归与 exact task snapshot Harness；单独保留历史 12 项基线失败，不改无关代码求全绿。
4. 冻结候选身份，调用一名 read-only native Reviewer；确认的 blocker 修复后回归并在既有有限轮次内复审。更新 Provider 文档和工程记录，提交 owned paths，push main 并核验远端 SHA。

## Acceptance

重复/延迟提交被阻断；失联及身份漂移保持 fail closed；未知状态、读回中断及重开不释放预留或重交；素材与任务身份可核对；无新增付费调用；必要独立审查闭环。受控资格与正式生产资格分别裁决，缺失的真实提交、浏览器重启、会话恢复及成功输出证据明确列出，不冒充 PASS。
