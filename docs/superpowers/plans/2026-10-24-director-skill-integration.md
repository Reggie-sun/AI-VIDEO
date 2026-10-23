# Director Skill Integration Implementation Plan

## Goal And Scope

执行用户已接受的[五库职责方案](../../research/2026-10-24-five-drama-skills-role-design.md)，并接入用户补充的 `coreyhaines31/marketingskills` 中 `ad-creative`。交付可发现、可按需读取的 Agent-side 创作技能和本地方法；不安装上游执行器、不新增 Runtime schema 或媒体生成任务。

当前只有分工文档，目标是普通剧情、广告及选定 Seedance 2.5 的创作请求能够沿现有入口读到具体方法，输出同一剧情/镜头方案。完整来源、许可、限制与本地改写边界必须可追溯。

## Invariants

- Native Codex + `open-video` 统筹镜头，accepted Drama contract 拥有剧情语义，`ecommerce-ad-workflow` 拥有 Product Truth 和广告 authoring contract，selected authoring/adapter 拥有模型表达。
- `runtime_skill_calls = 0`；不引入第二项目、站位、表演或剪辑状态，不自行 submit、发布广告或签验收。
- 连续性包含人物知识/动机/情绪和动作/空间/声音；同场/换景均可。没有明确 reset 时继承真实已接受前镜状态。
- 用户夸张强度与批准台词保持；不套统一微表演、快切或环境特效配方。原声与后期配音合并规划，不默认静音/删除。
- 2.5 专属知识只从已选 2.5 overlay 读取；2.0 不加载。上游参数、排名与效果断言不成为当前能力/验收事实。
- 保留未知及他人的 dirty/index 工作；共享 dirty 文件先保存 exact baseline，Parent 只拥有新增集成 hunks，提交不夹带 baseline。

## File Ownership And Milestones

1. **Drama specialist — bounded worker**：仅新建 `.agents/skills/drama-authoring/**`。以 Zenstory 的剧本方法和 Shuohao 的制作设定分为按需 references，连接 accepted Drama contract 与 Director；输出既有 Story/Scene/Character/Shot 语义，不建立平行 schema。保留源许可声明和改写说明。
2. **Advertising specialist — bounded worker**：仅新建 `.agents/skills/ad-creative/**`。核对 `marketingskills` exact commit 与许可，将策略、Hook、创意形式和变体方法适配为现有广告 owner 的 advisory 专项；移除默认静音、强制裁切/快切和上游投放执行路径，不虚构来源与效果。
3. **Integration — Parent**：修改 `.agents/skills/open-video/SKILL.md`，新建其 `references/professional-specialists.md`，补 Kangarooking 表演/动作与 DirectorSKILL 调度交接；修改 clean `seedance-authoring/references/seedance-2.5.md`，按需接 Liyue 方法；更新 `.agent/context/control-plane-playbook.md` 的窄触发和职责入口。必要的 matrix 注册及 ecommerce Skill 引用仅增加 owned hunks，保留已有变更。Harness policy 已有 `.agents/skills/**` 路由，不默认增加规则。
4. **Verification — Parent and native forward tester**：运行 Skill quick validation、相对链接/源许可完整性核对、受影响现有 skill/runtime-boundary 测试；以无生成的真实文本任务检查剧情跨场衔接、夸张局部修复、冷启动广告和 2.0 版本隔离。行为检查给真实输出与边界，不把静态/文本证据当成成片验收。

## Acceptance And Completion

用户执行中补充允许删除不合理、冲突和重复内容。Parent 同时拥有 ecommerce Skill 内本任务相关的旧句替换，以及 `references/ad-qc.md` / `ad-beat-sequences.md` 的对应清理：删除错误的未实现状态、按题材关键词拒绝剧情广告、固定 30 秒竖屏假设与专业知识读取冲突；专业参考的通用空间/节奏/音频/故障归因重复段归回既有 `creative-completion.md`。既有 schema、facts、blocker 条件、Runtime gates 与无关 baseline 不变。

两个入口和五源专责均在本地有实质方法与可达链接；广告创意返回现有 G0–G7 owner，剧情回既有语义与镜头 owner。没有为了每次用齐五库而强制加载，也没有新控制面。对 shared baseline 和 index 做差异核验，按 owned paths/hunks commit、push `main` 并核验 SHA。

本轮是 Skills/authoring 集成，非视频交片，不因工程验证触发 paid media。先完成局部验证，再按实际影响决定 Harness；共享 Runtime 契约没有改变时不扩大为整库回归。Skill 行为复杂且已获子代理授权，使用原生只读 forward test；风险 Gate 另判，不把 forward tester 冒作工程 reviewer。稳定后记录并评估学习；没有独立媒体实验时不制造 Learning Claim。

## Self Review

方案与当前源码/owner 已核对。任务只改变 Markdown 知识与路由，无 Product Python/JS 调用链变更；结构引用由当前 Skill/reference 直接确认，AOCI/CodeGraph 不为文档注册机械调用。未解决项由实际验证暴露后处理；不预先承诺真实画面质量或广告表现。
