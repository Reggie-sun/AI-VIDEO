# Jimeng Pre-dispatch Gate Repair

## Runtime Recovery Completed

原006已canonical known-no-effect纠正，compiler2与首次恢复准入经round10空findings后，007实际submit/平台完成/fetch成功，证明本次修复已走通真实平台链路。媒体Gate仍NOT_EVALUATED，不代签质量。真实交付、当前28次尝试与声音观察归S05 primary record最新S05-007段；下方pre-submit/旧UNKNOWN是历史。新source改动按成片优先等待审片后完整验证及owned commit/push；旧Gate独立slice已push。

## Recovery Pre-submit Verification — Latest

2026-10-27最新完整关联回归202通过、2失败；两个失败分别为既有Seedance final-text QA fixture缺口与既有error-message匹配不一致，使用Git HEAD原`generation_execution`内存载入均复现同样失败，未修改工作树基线。新compiler/predicate定向75项通过，完整无付费clone grant→prepare→start→quota→strict reopen通过，真实Manifest仍82。

提交前stop fence发现其他窗口新增macro1080v3 accepted，strict reopen后累计27次（26 accepted/settled、1 known-no-effect，无video UNKNOWN），S05六次。旧26→27预备bound保留，新的有限单元为全片27→28、S05六→七、最多1次新video、retry0，9000CRD金额guard不增；旧音频/图像UNKNOWN不重试。`S05-repair-007`保存最终bound/inventory、clone、定向/关联日志及两个基线复现，round10独立审查未完成前不实际submit。学习评估no_candidate：此处为同一原attempt的运行故障证据与工程恢复，不把多个证据层计作独立媒体实验。

## Historical Attempt Recovery — Current Extension

用户再次“那你继续修复啊”后，新增真实证据改变了旧006的恢复条件：同一native历史登记保存的`o.params.video_params.prompt`为1006字符，SHA精确等于canonical请求1007字符仅移除末尾LF的结果；native `resolveSubmitContext`明确执行`trim()`，修复前Worker精确params guard在admission前必然拒绝。使用Git原Worker与同一canonical prompt已本地复现`native request changed`，原HTTP/dispatch均0；空resource查询只作旁证。原证据已由round9独立审查后经唯一committer追加纠正；当前Manifest82，006为known_no_effect、reservation释放且actual cost0，原UNKNOWN文件保留，不重发旧请求。

本扩展先只读复核上述原始请求证据，再通过现有reconciliation恢复006；随后修复compiler边界空白（显式新compiler版本，冻结version1历史bytes）并走现有no-effect runtime repair、新preview/预算/count/一次性permit。不得覆盖旧Project/Shot、降低QA/Goal、复用旧permit或重置历史。补查全部roots已纳入其他窗口两个macro调用：原R lineage24次，全片26次（25 accepted/settled+1 known-no-effect，无video UNKNOWN）。只封存一个最多1次video的后继有限单元：全片26→27、S05六→七，auto retry0，新image/audio生成0，原9000CRD内部guard利用已释放预留、不增额度；旧音频/图像UNKNOWN不动。先交S05原声单段，S06仍等前序真实Gate。

新发现属于实际付费UNKNOWN的证据裁决及确定性root-cause修复，独立于此前已完成的Gate错误分类单元。旧8轮审查保留，最多有据追加3轮至total11：一次原证据/纠正操作审查、一次新版本compiler实现审查、仅必要时一次复审；复用原一名native reviewer，不重置历史，不自动增加。Parent是唯一writer，runtime evidence与纠正脚本放`L/S05-repair-006`，后继准备仅用新`L/S05-repair-007`，canonical root继续`R/trial-S05-v1`。

## Compiler Recovery Contract

真实clone回放暴露既有qualification分支把首次runtime recovery限定在总attempt2至5，不能表达已有多次known-media修订后的首次运行故障。本次新增纯predicate，严格限定jimeng同model、compiler1→2、正文只变化为native trim、原recipe/Goal/output/references冻结、全部同task历史保留且unique paid attempt数=used、ceiling=used+1、仅一份未消费的canonical /3 paid-no-effect grant及零resample。相同request/media的重复评价去重计费但保留证据，冲突身份或任一UNKNOWN拒绝。已有committer完整history/grant/receipt/current-scope/quota/permit检查保持，旧2至5分支不改；不提高通用最大次数、不新建task清零。

Parent新增owner为`_qualification_compiler_repair.py`及对应测试，只接入既有`generation_execution`判定；compiler v2归`jimeng_prompt`，adapter显式消费contract版本。新007 caller采用独立lifecycle/output ID，防止同创意后继占用006旧generation身份；不修订旧Shot。clone验证必须覆盖正常grant→prepare→start→quota→strict reopen，真实paid前round10审查。

## Goal And Scope

修复已在本地请求校验拦截、且能证明没有进入发送阶段的请求仍误报UNKNOWN的问题；保留真正未知结果的阻断，避免下一次确定性拒绝再次卡死制作。用户最新授权为“先修复gate”，本单元仅工程修复，不提交新视频，不将S05-006改签为无效果或媒体PASS。

## Evidence And Ownership

`jimeng_browser.cjs`在native调用前设置`nativeStarted`，即便HTTP wrapper在admission前抛错，main仍仅因该标志返回UNKNOWN。现有`jimeng_worker_faults.cjs`能执行真实Worker的请求变更、报价变更与迟到发送路径，但没有验证terminal错误协议的分类。Python transport已有只接受干净终止、尚未dispatch的`no_effect`协议；Provider与唯一committer已有known-no-effect路径，继续复用。

S05-006原始发送前错误证据未保存；2026-10-27只读取回预分配ID、精确查询为空，均不证明未发送/未扣费。此历史UNKNOWN及reservation不改写。

Parent唯一写入：`src/ai_video/production/jimeng_browser.cjs`、`tests/fixtures/generated_video/jimeng_worker_faults.cjs`、`tests/test_production_jimeng.py`、干净的`docs/jimeng-provider.md`、本计划与独立工程记录。保留所有并行dirty/staged内容、原同任务source修复与媒体记录，不stage它们。

## Contract

- 仅Worker自己在本次调用内观察到的、admission前本地guard拒绝可作为新增无效果证据；必须native已终止、lease已关闭、原HTTP未调用/未发送、host没有宣布或批准dispatch。
- proof缺失/陈旧、native仍pending、浏览器读取失败、未正常退出、已dispatch或response丢失均继续UNKNOWN；错误文本、空资源查询与节点failed状态不能代替proof。
- 正向proof保留关闭的页面发送锁及原HTTP/fetch guard，native终止后也不释放，防止脱离promise的迟到发送；后续新授权尝试前刷新页面并重新验证，不删除锁或复用permit。guard ownership变化不能给出正向proof。
- 不输出raw异常、cookie/session、signed URL或HTTP body。新增诊断只用静态枚举，不改变真实请求与quote，不增加retry。
- Python协议、selected adapter、ProductionStateCommitter、预算/count/permit、历史serialization与逐镜媒体验收不改。禁止runtime修改当前006或新付费调用。
- Worker故障测试执行真实JS且检查实际network call计数、dispatch事件及terminal协议；不是只测分类helper。

## Milestones

1. 扩充现有故障fixture：请求/报价在本地拒绝应返回可证明的no-effect，已dispatch、迟到pending、owner替换及缺证保持UNKNOWN；观察RED后才改生产代码。
2. 在现有本地guard和terminal清理边界保存本次有限proof，修复协议分类；不新增状态writer/恢复分支。精准测试、transport与canonical paid恢复关联回归。
3. 必要native独立审查、最终diff与证据核验，更新Provider说明和本记录，按owned paths提交推送。工程修复不等于S05-006已恢复，也不授权下一Shot。

## Verification And Review

精准：`tests/test_production_jimeng.py`的shipped-worker故障与browser协议测试，新增失败先RED。关联：完整Jimeng tests、paid no-effect reconciliation、qualification及paid状态/恢复测试；报告实际级别，不冒称full suite或真实Provider验收。

该改动可能将错误分类为无效果并影响预算释放，错误后果重大，浏览器异步清理语义存在离线验证缺口，触发`NATIVE_REVIEW_REQUIRED`，复用一名`reviewer_xhigh`。原同任务工程已6轮全部保留；用户新授权Gate修复且新增付费结果判定，有限扩展最多2轮至total8，停止条件为该范围findings清空或额度用尽，不重置旧历史。

## Status

已完成。先复现两种guard拒绝误报UNKNOWN；native round7发现实例方法覆盖漏判，Parent另复现实例覆盖及账号变化两个RED并修复，round8 finding set为空。最终定向33项、映射provider回归1286项（23个既有恶意构造模型序列化warning）、恢复回归44项及文档契约检查通过。隔离真实Chromium五场景均确认native调用恰好一次、原HTTP/平台请求0；一次早期探针未捕获场景的断言失配保留在运行证据中，不计PASS或泛化为完整runtime稳定性。

标准Harness入口会创建临时worktree，与用户限定冲突；本次直接执行其映射check argv并封存source hashes、日志和分级证据，不称为正式Harness回执或完整仓库回归。证据归`runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/S05-gate-repair/`，primary工程记录为`docs/record_for_agent/2026-10-27-jimeng-pre-dispatch-gate-repair.md`。本单元video/image/audio付费调用均0，S05-006原UNKNOWN和预算预留未变，S06未提交。
