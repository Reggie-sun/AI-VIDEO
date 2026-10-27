# Jimeng Chinese Native Prompt

## Current Unknown Stop

引用归属恢复已应用到真实Project7，81精准/72关联与native工程round6（remaining findings为空）完成。006实际进入submit_once后返回UNKNOWN；没有sealed Jimeng dispatch/resource可查，canonical query-only recovery一次仍KEEP_UNKNOWN且Manifest未变。当前video24次尝试=23known+1UNKNOWN、S05六次；quote1280credits、扣费/是否产生新视频未确认，reservation保留。没有新MP4或媒体PASS，S06未submit；停止新付费尝试，不重发/remint/补造dispatch/新root归零。事实与恢复边界归S05 primary record最新段及 `S05-repair-006/attempt-outcome-receipt.json`。下方旧引用阻断和用户暂停均是历史状态。

## Current Admission Block

用户已解除暂停。固定林序/骑手参考已导入S05 Project6，1007字纯中文准备稿、9图与一个空节点已备；历史video23/S05五次，新有限单元24/六次尚未提交或消费permit。当前normal prepare因旧动作参考丢失Character归属而被拦截，不能覆盖封存Project6或绕过exact /5 target。必须先通过committer保留历史的未提交归属恢复；该恢复尚未实现，当前停止paid attempt，S06不提交。实证与剩余工作归S05 primary record最新段及 `S05-repair-006/reference-owner-blocker.json`。下方旧用户暂停是历史状态，不应重新索要“继续”。

## Current Hold

用户最新明确“先别生成了,主人公的referces都没有固定我发现...”。所有图像/视频生成暂停；累计video23、S05五次，006仅离线准备且未进入canonical state/预算/permit。S06继续阻断。先完成林序共同身份锚点及派生参考的核对，不按下方历史“下一步生成”自动执行；审计归 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/identity-reference-audit/README.md`，当前状态归S05 primary record。

## Goal And Evidence

用户在S05字幕失败后明确“prompt就用纯中文,写入规则”“继续”。规则已以 `3e0ae8e` push main；新任务是让封存的精简中文正文实际进入Jimeng请求，而非只保存中文草稿。当前005实际5734字符混合模板且原片仍烧入字幕，804字稿尚未提交；不能宣称改中文已证明去字幕。

## Scope And Owners

沿既有Shot、QA `native_text/native_text_mapping`、recipe、Jimeng compiler、committer与submit owner，不新建prompt库、执行链、旁路transport或接受器。Jimeng当前不消费Seedance精简最终文本入口，默认共享模板会展开英文标签。新增明确由QA映射选择的Shot最终正文路径，复用既有final-text标量映射/人物表演/共同compiler验证；无映射的历史行为和旧序列化hash不变，有映射但缺失表达时拒绝，不能退回旧长文冒充成功。

主要文件：`jimeng_prompt.py`只管既有模式/材料装配与新入口分派；新 `jimeng_authored_prompt.py`作为无副作用叶模块，复用 `seedance_native_prompt` 的既有final-text校验而不复制权威；`generation_authoring_revision.py`仅在显式列出的既有raw QA IDs上允许更新封存native文本映射，保持observable/证明身份及完整Goal，不扩大模型/refs/output/count/UNKNOWN。测试归新 `tests/test_jimeng_authored_prompt.py` 及既有authoring/Jimeng/Seedance契约用例。其他窗口dirty source与AGENTS拼接规则不动。

## Acceptance And Verification

1. 先写失败测试，经标准resolver/compiler seam证明精简中文原文无英文模板进入请求、参考marker只绑定对应素材、默认历史输出不变；缺片段/错误intent hash/未映射人物/未绑定引用必须失败。
2. 最小实现和精准测试，继而关联Jimeng、Seedance表达与authoring修订契约回归。新声明不改变raw QA proof/stage/IDs/owner，也不靠扩大硬限制隐藏失败。
3. 当前S05真实资料沿既有canonical authoring构造prospective candidate，逐项核对原文→QA→最终native。纯中文检测只允许实际必要技术标识/素材语法，禁止英文自然语言标签；长度和匹配只证明输入，非媒体验收。
4. Risk Gate为NATIVE_REVIEW_REQUIRED：映射参与新paid准入，独立验证有实质收益。旧工程review已3轮、remaining findings为空；本次因用户新明确语言/实际输入要求引入新语义，最多追加2轮native xhigh只读审查（总上限5），不是重试旧finding或重置历史。影视review已有2轮单独保留，不能代替工程复核。
5. 必要准入/审查通过后才决定新的有限实测单元；历史video23、S05own5、两次audioUNKNOWN保留，不能复用permit、改旧文本或未封存发包。当前不授权无限重抽。任何新MP4仍需逐Shot MCP和原速声画审看；未认可不S06、拼接、后期字幕或发布。

## Known Verification Limits

AGENTS基线在本任务前HEAD即14185bytes，超过registry14000；当前另有其他窗口同文件hunk。规则测试33passed/1因该基线失败，staged Harness因保留的非本任务unstaged AGENTS hunk拒绝运行。此问题不伪报PASS、不提高阈值隐藏，也不夹带他人hunk提交。媒体改动仍按用户认可后的完整验证再owned commit/push。

## Unsubmitted Reference Ownership Recovery

用户再次要求继续，Parent修复Project6登记失误。新增一个既有committer下的未提交恢复：仅允许封存/5 target无任何后继视频request时，对其Project追加一次纯人物reference ownership修订；保持Shot、Registry、完整intent/QA/goal、所有输入bytes、model/output/profile、预算/计数/UNKNOWN不变。旧Project6与receipt保留，以existing previous_supersession连结一次新receipt和exact Project7，原direct /5仍严格source+1；amended /5只有locked owner实际重开该一跳来源后可验新Project。reader也须核验相同metadata delta，拒绝改脸/减少reference/改其他creative字段、任意跳版本、重复链或后继request。preflight只是候选识别，不拥有放行，committer锁下校验不可省略。修改前先TDD，零Provider副作用的当前root克隆验证后才应用到真实root。

source、paid准入及recovery的跨模块改变触发NATIVE_REVIEW_REQUIRED。原3轮和中文正文2轮（total5）保留；本次新出现的未提交metadata恢复语义最多再2轮native xhigh（total7），不扩付费生成额度、不重置finding/UNKNOWN。若required review仍不闭合或canonical proof不足，不submit。媒体仍须逐Shot exact MCP/原速声画/human分开，不因软件修好签PASS。
