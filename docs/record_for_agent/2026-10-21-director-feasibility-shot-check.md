---
record_kind: session_summary
topic_id: director-feasibility-shot-check
learning_eligibility: ineligible
---

# Director Feasibility And One-Shot Check

Date: 2026-10-21

## Scope

用户指出方案选择时缺制作可行性判断、主Skill仍混入H3执行指令，要求停止扩建工程，只做一个有明确变化的短镜头对照及最小验证。本轮补充advisory实践、迁出旧H3文字，并选一个护腰贴开场单元回放已有exact媒体；无新schema、字段、评分器、Policy、Harness规则、生成、付费理解或Production提交。

源码与gate未改，已有Production Strategy继续拥有可执行分工和选路。本机默认`127.0.0.1:8188`的system_stats/queue只读请求均未成功，因此未将local generation视为已就绪，也未启动、安装模型或替换Provider。已有素材足以对部分动作可行性取证，未因此另开生成实验。

## Skill Changes

`.agents/skills/open-video/SKILL.md`保留Director任务分类、创作判断、coverage和语义交接；新增方案选择时与制作owner核对关键事件及能力证据。H3三字段语法、固定时长、参数、ComfyUI、自动Judge、上游Stitch及backend开发说明全部移入`references/legacy-h3-upstream.md`，归档原文可追溯但不作为日常Director流程或当前执行入口。H3/Seedance等具体表达归选定模型Skill；项目逐镜媒体Gate、HyperFrames和唯一ResolvedTimeline保持。

`references/creative-completion.md`新增Production Feasibility：区分自然表演、多人接触、反射几何、道具状态变化等风险；比较原生生成、参考约束、已有素材与分层合成的相称证据。用户给出的路线只作讨论起点，不自动按题材选路，不把支持模式、白模或静帧当作连续动作能力证明。

## One Case And Comparable Proposals

共同创作目标是下班客厅里从忙碌转向主动休息与伴侣照顾，保留真实商品身份，不编造功效。这里只研究一个开场单元，不用它替代完整广告。

| Variant | Directorial intent and production hypothesis |
| --- | --- |
| Q，历史实际发送方案，约7秒 | 长纸卷占沙发，女子前倾站稳、看纸后看伴侣，男子微笑，缓推；忙碌占据休息空间的隐喻，清纸/商品在后段。假设原生生成同时完成纸的连续物理运动与双人反应 |
| L，本轮采用新版方法整理的8秒回放方案 | 女子已坐并持一部手机，男子在右侧空位旁递一个盒；她放手机到近桌并释放、双手接盒，他等握稳再撤手并坐下，最后目光回应。制作选择是完整采用既有普通时序真人镜头，先验证手机释放/停留、支撑交接和落座，不依赖新生成或补造动作 |

Q固定为历史actual native，并非原coverage的最佳意图：原coverage另有“想坐又停”，该动作在作者交接中弱化。因此不能从L相对Q更清楚，推导原始创意天然没有动作。两案时长、动作、参考、商品出现时机均不同，不是控制变量的A/B。

尤其明确：L的动作机制已由另一窗口的`source-product.json`及SP1生成实现。本轮知道这些来源后才整理方案与取证，属于有既有素材的回溯可行性检查，不是先封存新版方案再前瞻生成，不能归因于本轮Skill升级或称为本轮原创生成成果。

一个fresh-context native `conceptual_planning_agent`，task `single_shot_feasibility_compare`，先只收到共同brief和匿名L/Q方案，未收到实际文件、作者diagnosis或优劣标签。其概念比较认为L的“腾手回应”更具体，但放手机不充分证明休息；Q的异常纸卷可能有钩子，但待办意义、占座及目光因果需实片证明。两案均有可证伪观察，不以镜头数或总分判优。随后才给它exact媒体作同一单元检验，无nested delegation。

## Exact Media And Observations

媒体均在`runs/hotpatch-dayoff-20261020-001/production/state/video-generation/fetch/files/`：

| Variant | Filename / SHA-256 | Current probe |
| --- | --- | --- |
| L / SP1 | `55857f1ae02d2e2be8d00a3c46030cfa2b14d35f029ade93afead44ab6c440ea.mp4` | 6,146,483 bytes；8.000秒、192帧、24fps、768×1344；含AAC |
| Q / 原S01 | `2df69a622b9cf0e869e028b5cf4882ce5539915f22e6bb9b1bfc95904516a10f.mp4` | 本轮probe container 7.300秒；沿原完整源检查，不混入2.25秒/加速预览 |

Parent显式调用project-local `video-analysis.video_analyze`，关闭转写、scene与audio understanding；实际查看L的0–7.5秒每0.5秒16帧，以及Q的0/1/3/5/7秒5帧。时间只表示所看样帧，不是精确接触帧或正常速度视听。

| Observation | Supported result / limit |
| --- | --- |
| L，0–1.5秒 | 女子持手机、男子持盒；两人开场已经微笑，未显示明显从紧张到放松的表情转变 |
| L，2–3秒 | 手机接触桌面，随后离手并留在桌面；支持腾手的状态变化，不证明主动停止工作；未签原native的face-down细节 |
| L，3.5–4秒 | 女子双手接盒，男子支撑手随后撤回；样帧支持先接稳后释放，仍不能由离散帧排除所有中间接触瑕疵 |
| L，5–7.5秒 | 男子坐至右侧，女子持盒，两人后段对视；共同坐下可见，不等于情绪自然或观众愿意看 |
| Q，0–3秒 | 长纸形成强前景，女子主要看纸，旁边仍有可用座位；“忙碌不让她休息”的空间原因不充分 |
| Q，5–7秒 | 女子转向男子，关系回应延后；不能仅据长度称失败，纸卷本身是否更吸引仍待观众判断 |

商品在L中直接成为互动对象，优于仅假设后镜建立关系的可见程度；但也可能是普通接礼物/摆拍，未证明护腰贴与休息结合更自然、产品独特性或事实细字正确。没有使用字幕、裁切、加速或修掉关键物理反例来提高通过率。

独立context随后实际调用本地MCP probe/extract，查看L16帧与Q8帧，共24帧，未读其他窗口的作者diagnosis。它支持上述关键状态次序，但指出L开场并无明确忙碌/疲惫、包装持续朝镜头、未看见明确生活笑点；Q的超长勾选清单仍可能成立为事务侵占休息的隐喻，旁边有空座只否定“物理上无处可坐”的强解释。Parent采纳这一收窄，不因Q没有在首镜引入商品而判其失败，也不将L动作更多当作吸引力胜出。

## Assessment And Boundary

实际证据支持这个既有8秒镜头里有可执行的放物—接物—落座状态变化；它补充了纯纸面复核，但不证明新版Director升级成功、H3一般能完成复杂接触、动作自然度更好或观看吸引力提高。模型/Agent抽帧观察不填成human，也不签Production质量或改旧诊断。

### User Feedback And Result

本窗口提供上列L exact MP4链接，说明原声不在本轮评估内，请用户静音、正常速度看一次，再反馈第一感觉。用户实际选择：“动作能读懂，但仍像摆拍或缺少吸引力”。该原话直接支持本镜动作可读，同时指出其创作观感不足；不将这项反馈扩成声音验收、正式human播放证明或盲测受众结果。用户已看过本窗口解释，也未被要求对Q作同等观看评价，不能据此统计比较两案胜负。

本次结果应保留为：**动作链有实片与用户理解支持；摆拍感和吸引力未过关，未证明导演升级成功。** Parent已观察到开场持续微笑和包装长期朝镜头，它们是下一次取舍可调查的具体线索，不据单例断言必然根因。L也可能只读成腾手接礼物，忙碌到休息的变化仍弱。

后续若继续创作，需要重新选择人物真正改变的时刻与商品进入的动机，并由相称实际表演验证；不能只把同一递盒过程加更多微表情、切镜或字段。当前用户只要求一个验证单元，本轮到此封存负面观感反馈，不自动追加生成或扩建工程。

## Verification And Completion

Parent唯一writer拥有两个现有Skill文件、新归档reference和本记录；foreign dirty/index保持。现有Skill格式及local links/anchors检查通过；58项相关现有测试通过，无新措辞匹配测试；归档正文与迁出前H3原文逐字核对。首轮最终Harness已通过，但之后收到用户观感反馈，补入记录后该旧snapshot收据不用于新bytes。最终按现有policy验证exact staged snapshot，receipt为`.agent/harness/runs/director-feasibility-shot-check-20261021-r2/receipt.json`，实际结果和publication在交付另报。

Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`：局部可回滚advisory文档/归档调整，不改变权限、持久化或验收；独立比较属于内容取证，不冒充代码或human审查。`record-ai-video-session`以本文件记录；`distill-ai-video-learning`: `no_candidate`，既有两次不同设计生成与本轮多层复核不构成受控改善或新的独立生成尝试，不创建Claim或ADOPTED状态。
