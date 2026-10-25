---
record_kind: recovery_incident
topic_id: paid-history-read-reuse
learning_eligibility: ineligible
---

# Paid History Read Reuse Repair

Date: 2026-10-21

## Follow-up Runtime Boundary — 2026-10-21

最新媒体状态已由[Seedance 2.0/Fast对照](2026-10-21-jieshi-seedance-20-fast-comparison.md)取代，下段METASO/402描述为历史。两条Seedance原始MP4均已下载，但尚未全项验收。Fast从authorization issued到实际POST仍耗本地约350.5秒；下文39.207秒是Manifest206标准reader的独立只读测量，不能推出完整start/quota/submit已经足够快。既有局部解析复用和focused tests仍只证明其原范围，整条重复历史读取的耗时未解决；本次先完成交片，没有再扩大缓存工程或整组回归。

当前媒体状态已由用户显式切换METASO的新单元取代：已真实生成新MP4，但0–3秒内出现手部倒影，未通过媒体Gate。见[METASO实际结果](2026-10-20-jieshi-3d-anime-minimax-test.md#metaso-s01-actual-result--2026-10-21)。下文官方MiniMax的402仍是该历史单元事实，不再作为METASO当前blocker。

## Symptom And Cause

用户要求修复《界蚀》单条 MiniMax 生成前耗时过长的本地核验。当前实际调用栈为 `extend_paid_provider_submit_quota` → `retained_submit_quota_allows` → `_reopen_paid_budget` → quota ancestry → `load_generation_execution_binding` → 历史质量诊断和内容哈希；这不是 Provider 生成耗时，也不是正在跑完整回归套件。

此前 budget DAG traversal 已避免同一预算节点的重复历史递归，但多个历史快照仍重复完整解析相同 execution binding；调用方在遍历历史 attempt 时又重复打开同一本完整预算账本。本次最小回归在两个不同 binding 上分别观察到两次完整解析，预期均为一次。

## Change And Boundaries

`_paid_provider_project_reader.py` 的单次 traversal 保存已经完整解析的 binding；复用仍由 `_generation_feedback_reader.py` 的私有入口执行，每次访问仍 nofollow 读取当前 bytes、计算文件 SHA，并核对 pointer 的 file SHA、binding hash、request fingerprint。失败/未完成校验不进入复用表；public reader 每次创建新的表，不跨读取、项目或锁边界保存。

`paid_provider_submit_quota.py` 的当前额度扩展循环复用已经核验的 budget；`_state_commit_video.py` 的单次持锁限额核验按需读取一次 budget，供当前循环的 retained-quota predicate 使用。public predicate 仍 fresh reopen。没有修改历史计数、预算上界、未知结果处理、permit、Provider、生成输入或媒体质量要求。

## Verification

证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/uploaded-style-S01-20261021-regen-001/control-reader-repair/`。

- `candidate-hashes.json` 绑定四个源码文件与一个测试文件；`verification.json` 保存有限验证边界。
- binding 解析次数回归先 FAIL，修复后遍历和 quota 文件共 43 PASS / 114.49 秒；随后未提交关闭/继承及 generation execution 共 16 PASS / 41.87 秒。最后 budget 循环复用改动后补跑相关 inherited、未提交、reservation、expiry 六项，6 PASS / 16.80 秒，不把重复执行计为新增独立测试。
- 新测试保留同次 traversal 的 binding bytes 漂移拒绝、下一 public call fresh validation，以及三个 pointer identity 字段的错配拒绝；原有历史 base/derived snapshot/循环/篡改测试保留。
- 当前真实项目 strict standard reader 完成于 39.207 秒；Manifest206 前后 SHA 均为 `c6986bfa5eabe1efbe160d9d2fd65884997ab434103d4bbc88ce1f429f236bc0`。这是当前只读测量，没有受控的同快照旧版耗时对照，不宣称整体生成已达到某个加速倍数。
- 一名 native `reviewer_xhigh` 独立审查 round1 的 finding set 为空；Parent 核对当前 diff、候选哈希与测试结果。审查意见不代替实际运行。

## Recovery And Current Limits

旧本地进程中断前后均为 Manifest206、当前 attempt `canvas-6af3a215597bc51303c0df8836b84f2008b211df` 的 REQUEST；无 paid state、permit/submit receipt 或 wire log，已确认未发出视频 POST。退出旧 Python 后以新源码恢复同一已知未提交请求，没有创建新 attempt 或重置消费。后续视频真实提交/结果仅以同 run 下 actual receipt、wire、MP4 和逐镜媒体裁决为准。

新进程完成额度核验并在2026-10-20 19:30:02.510 UTC实际发出一次 MiniMax POST，19:30:03.401 UTC收到HTTP402。canonical Manifest209登记 failed / known_no_effect，未生成新视频、未重发。当前 blocker 是 Provider 的402响应，修复后的 end-to-end 成功出片耗时仍未验证；当前 full media state 见[同主题记录](2026-10-20-jieshi-3d-anime-minimax-test.md#regeneration-blocked-before-media--2026-10-21)。

本次没有运行完整工程 policy suite。当前 constitution 要求先交视频审片，用户认可效果后再做完整工程验证及 commit/push；本地修复与上述 focused verification 不冒称 full Harness PASS，publication 暂缓。相关 Harness inspect 有 17 项 engineering checks，明确 `media_submit_authority=false`。

`record-ai-video-session` 评估为 record，自动 `distill-ai-video-learning` 结果为 `no_candidate`：本次是实际故障及单次有界修复，没有可升级为跨实验制作规则的受控质量证据；不修改 Skill/Policy/Gate 或全局 memory。旧性能修复历史仍见 [2026-10-02 record](2026-09-28-reference-capabilities-and-local-canvas-method.md#bounded-reader-performance-repair--2026-10-02)，不将其旧 PASS 冒充本快照证据。
