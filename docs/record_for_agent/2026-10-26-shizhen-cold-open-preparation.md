# Lost Frames Cold Open — Director Preparation

Date: 2026-10-26

## Current Revision — Rhythm 02

用户保留核心创意、人物关系、规则、音乐及S01衔接，要求更快建立兴趣，并明确本轮不付费生成。当前创作入口改为`cold-open-preparation/rhythm-revision-02/director-revision.md`及同目录coverage；下方37秒方案／旧回执属于Revision 01历史，相关实测事实不回写。

推荐22秒预算、20–28秒弹性。一个固定构图并入“两位”、同伴关心与遮挡后空位；约第7–9秒揭示是待实片检验的导演偏好，不是QA硬deadline。第二构图听见“就我一个”，再用片名交接翌夜S01。取消重复转告司机、擦镜片／举手机等入口动作及为消失重新建立机位，保留辨认空位和日常回答的时间；不靠改速、截对白或快切增密。

实际重读：原coverage与31条shot cards均276秒，S02准备版coverage为278秒（S02从6到8秒）；加22秒分别298／300秒，仅是规划账，S01实际16.065秒与最终timeline readback不能四舍五入冒充已成片。未削减或重生成正片，未改已认可S02及字幕。

失踪路线由“优先单次生成”改为“优先准备前后动态状态＋完整车身遮挡硬切”，原生连续生成保留为有界备选。依据是决定性事件控制风险与当前Composition仅接受零时长CUT的真实边界；不声称已测试胜率、成本或自然度，也不假设已有动态mask能力。不新建组件执行器，不把摄影镜头与生成组件强行一一对应。

沿用既有Music Director的“缺席的应答”音乐输入与生成identity，只调整事件锚点和短版可用余量；不重新提交、dry-run、读取认证或签发permit。原Suno UNKNOWN历史不变，其他音乐窗口后续执行状态由其owner独占，不将其候选自动认作片头cue。

本轮验证以revision-02的`verification.json`及最终消息所列exact staged Harness为准，区分文本／结构验证与未执行的媒体验收。源哈希、原创角色关系和S01保护重验；旧37秒文件保持不变，父README仅追加当前revision入口。Risk Gate为Parent自审、无高后果运行行为变更，无需额外reviewer。record更新，learning评估`no_candidate`：没有新的真实媒体实验可用于学习claim。

## Scope And Current Truth

用户要求先审查《失帧》第一集，再完成冷开场完整导演方案、音乐、镜头编排、S01衔接及可执行素材准备；后续明确音乐偏高级冷峻的影视悬疑质感，并指定即梦`seedance_2.5`。本次是设计及离线准备checkpoint，不是已生成的新开场。

新增包为`docs/superpowers/artifacts/drama/shizhen-episode-01/cold-open-preparation/`。原剧本、原coverage、ProductionProject、Registry、Manifest、S01版本索引、S02准备稿、旧Suno请求与累计计数保持原位，不改写旧版本来假称新方案已经落地。

## Creative Decision

暂名《两位》：前一夜两名夜班同事在雨站接车，配送货车短暂遮挡后只剩罗敏；她将此前“两位”自然答成“就我一个”。观众记得同伴，世界继续生活；片名后转“翌夜”完整进入S01。约37秒为本版预算，可按表演修订，不为逐句对白分配时间戳。

没有第二个保留记忆并查监控的目击者，不提前出现妹妹、走廊、未来日期、林序身份线索或异常组织。雨与货车只是表现条件，不是新触发机制。原结尾的反转及真实雨声保留。

Music Director沿现有`SceneMusicBrief.musical_design`表达冷色电子室内乐及“缺席的应答”动机；前半段主动无新增配乐，罗敏回答后进入，片名接续，S01前退尽。片尾只在反转后的黑场考虑复用同一actual录音乐句，不以新生成相似曲冒充主题连续。

## Verified Evidence And Boundaries

S01 HD-005原片实际SHA-256为`15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，51,142,682 bytes，1920×1080，16.065秒、385帧、44.1kHz双声道AAC。ffprobe显示nominal `60/1`、average `23100/961`，不能宣称CFR60。版本索引的原片用户`APPROVED`、字幕`PENDING`、历史媒体Gate `NOT_EVALUATED`分别保留。

本轮显式调用project-local `video_analyze`，只请求metadata与抽帧；实际返回0/5/10/15秒帧，已查看首帧与末段样本，并另查看D选型原图。没有请求新的付费听音、ASR或重试旧audio UNKNOWN；不能据此声明连续表演、音画同步与音乐听感通过。

两张S01样本JPEG与原文件身份／metadata进入准备包；仅用于本地美术及衔接核对，不是新视频、已注册参考或Production qualification。片名字形由实际`Noto Sans CJK SC Regular`轮廓导出透明SVG，Chrome实际栅格化检查静态可读性；没有制作或验收P4动态片名。

本包调用现有Music Director输出三条direction，其中两条为`INTENTIONAL_SILENCE`，一条为器乐cue。现有Suno adapter实际构造`--dry-run` argv并由安装的CLI离线执行，`submitted=false`、`model_verified_live=false`、v6映射`chirp-hawk`、器乐标志为真；结果只保存allowlisted离线字段，不持久化session metadata或live next action。未新增执行器、provider、依赖或Music Director模块。

验证详情与每个准备文件SHA见`cold-open-preparation/verification/preparation-receipt.json`；Director v4验证仅证明声明结构／来源锚定与绑定，不替QA author裁定hard requirements。相邻固定机位的提示保留：固定机位服务缺席对照，不能为了消除warning改成运镜。

初次focused Harness通过。related Harness被既有`AGENTS.md`预算阻断：当前14,235 bytes，上限14,000，文件与HEAD逐字一致，本任务没有修改它。独立执行剩余检查又发现policy audit已有8个未映射路径、4个未引用测试；这些路径和policy同样不是本任务改动。`tests/test_runtime_skill_boundary.py`实际2 passed。具体基线identity见准备包`verification/existing-engineering-blockers.json`。保留失败，不改规则／映射来凑绿，不将focused或文档检查称为related全通过；最终exact-snapshot回执以交付消息所列路径为准。

## Suno Ownership And Stop

另一窗口负责Suno认证／预检修复，明确占有`src/ai_video/production/suno_music.py`、`tests/test_suno_music.py`及旧pilot执行材料。本窗口已通过原生线程工具确认只作新包离线准备、不写其文件、不生成或解验证码。

本次实际读取`STOP-request-02.json`仍为`PAID_PROVIDER_OUTCOME_UNKNOWN`且`new_submissions_allowed=false`；该窗口报告两次尝试`auth_expired`、无clip及captcha preflight required。旧未知结果与历史次数不因新cue或新目录重置。本轮新增付费生成0次；旧两次最终结算由其owner报告，不能把本轮dry-run当作第三次live授权。

## Review And Completion Boundary

Parent自审此设计与素材包。Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`：未修改共享运行行为／凭据／Production持久化，没有独立审查能补足的高后果运行缺口；本包没有冒签媒体验收。项目要求的文档级验证与exact staged Harness按最终receipt报告，不用全仓测试冒充电影完成。

当前缺少新角色／站棚美术、exact native profile／mode／附件、QA-owned新Shot allocation、冷开场MP4、可听Suno音频及exact混音。下一制作阶段沿原owner补齐，逐Shot media Gate，最终审看“冷开场＋片名＋完整S01”；本轮未创建Production revision、activation、P6、Final Acceptance或public publication。

`record-ai-video-session`评估为recorded；`distill-ai-video-learning`评估为`no_candidate`：这次是单一未实测创作方案与离线准备，不符合跨实验学习claim门槛，不修改Skill／Policy／Gate。保留其他窗口dirty工作；提交／推送结果由本轮最终消息及实际Git核验报告。
