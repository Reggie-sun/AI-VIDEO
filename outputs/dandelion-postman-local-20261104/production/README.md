# Local System Postman Preparation

## Scope

当前用户要求用现有体系制作一个对照。使用 open-video 的事件先后/动作连续性与 seedance-authoring common、2.0 overlay；不使用外部 Skill 新编排。保留已认可的同图、故事、12秒、2.0VIP、1080p与原生音频要求。原版也通过同一项目执行链，本次区别在创作表达，不是两套生成引擎对比。

当前版本已见上一条的动作/声音结果，因此不是盲实验，也不是可以归因整个Skill优劣的受控对照；prompt多处精简及步伐表达变化、模型随机性均是限制。没有改变原片。

## Ready Evidence

`coverage-validation.json`、`prompt-lint.json`通过；`prepare-result.json`返回 GENERATE_ONCE/executable。新root为 `runs/dandelion-postman-local-20261104`，离线bootstrap时Manifest revision5，未调用外部或创建视频attempt。父会话拥有live提交。

唯一输入仍是已认可蒲公英邮差新图 SHA8125187d8eba4f1b9d13262ade2301c81391ccb756c32237b9b1ffebca68cd48。不是新图假认可。`preview-approval.json`使用当前用户指令并保留`approval-context.json`指出原图认可。

## Preflight

连续单镜：机器人左/蒲公英右；12秒中景微距正侧前方微推，不越轴。先双脚各前移落地一次、双脚站定，再有风吹种子，机器人因看见种子而抬头；种子沿可见轨迹落头并停顿。保留右胯邮袋。独立单镜无前镜handoff，不借用旧视频末帧；参考为soft reference非硬首帧，种子落点和精确步数仍须实际检查。

QA保留identity/action/camera/performance/space/sound/art七维。每组只映射相关原生文本片段，没有把完整prompt塞给全部路径。模型输出仍NOT_EVALUATED；不要重跑build/bootstrap覆盖已封存root。没有业务代码、Skill或Gate改动，没有commit/push。
