# Lost Frames Cold Open — Music And Sound Direction

## Musical Identity

用户补充的《爱，死亡和机器人》是**高级、冷峻、带悬疑质感**的审美方向，不被当作统一曲风或具体作品可复制的谱面。此次原创方向是：**冷色电子室内乐，城市仍有规则，而乐句内部少了一次应答。** 不写传统恐怖短剧的“气氛垫＋突然重击”。

配器职责：窄而近的低音单簧管只吐出两个短音，第二音稍向下；带细微颗粒的模拟合成器延续余振，让音符之间的空气可听；极薄中提琴泛音提供冷硬边缘，不演尖叫。低频有形体但不成为持续轰鸣。声音空间深，攻击干净，尾音有距离。没有人声、哼唱、耳语、合唱、歌词、摇滚鼓、舞曲drop、反向尖叫和恐怖重击。

动机称为**“缺席的应答”**。最初只提出两音，第三个预期回应不出现；间隙是音乐结构，不与画面里的十一秒作精确节拍对应。可有缓慢、非舞曲的内在脉冲，先不锁BPM或调性。该两音下行是创作目标，Suno不保证按文字精确作曲；最终必须从实际音频辨认并记录采用的乐句，而不是把Prompt当谱面证据。

## Spotting By Event

| Event | Score | Foreground sound / dramatic reason |
| --- | --- | --- |
| CO01两人在雨站、CO02说“两位”与路滑 | **无新增配乐** | 雨打棚顶、远轮胎与普通人声建立可信关系。高级感来自取舍，不靠从首秒铺满电子氛围 |
| CO03货车遮挡、两人变一人 | **继续无配乐** | 正常货车通过声保持可识别。异常在其声尾中少掉一截反射与雨棚滴水节律，留一层远城底噪；不做全声场归零，不复制便利店扫码截断音 |
| 车尾退出后看清空位 | **先给环境声独自成立的空间** | 观众自己发现缺席；不提前让低音告诉他“这里要出事” |
| CO04司机问“一位”，罗敏回答“就我一个” | **话语余波后第一次进入** | 平静回答必须完整清晰；此后低音单簧管双音与细颗粒尾音才建立作品身份 |
| CO-TITLE | **同一cue、同一实际录音接续** | 第二次动机稍稀疏，留未解决尾音；不另起Logo音乐，不为“失帧”两字各打一下重击 |
| 片名末段至S01 | **音乐退尽，S01无新增配乐** | 本方案默认零重叠进入S01，保护自然对白和生活动作。若尾音与片名字长冲突，先选可完整收束的源区间，不剪掉S01开头迁就音乐 |
| 第一集最后身份／明日信息已成立 | **原结尾继续只留真实雨声** | 不替身份揭示加恐怖答案，不提前泄露人物关系 |
| 终场切黑之后 | **可选，复用片头同一已选录音的另一句** | 让城市主题回来，留更大的第三音空位；不是为反转现场加音乐。原剧本切黑片名保留为end slate，不再做一套片头动画 |

局部环境缺失是这一事件的声音剪辑表现，不宣称是每次异常都具有的固定规律。先检查生成原声中是否已含车流与雨，不叠两辆货车或两遍滴水。精确缺口、跨镜声桥、电话滤波和混音都归现有Composition／HyperFrames P4，不要求Suno生成雨、司机或时间码。

## Suno Preparation Through Existing Music Director

本包用现有`music_direction.SceneMusicBrief`与`MusicalDesign`表达音乐选择，经`direct_music()`输出，而非另建Music Director。三条brief为：

- `co-diegetic-only`：前半段`INTENTIONAL_SILENCE`，只表示不新增配乐，不创建静音音频、不消掉环境声。
- `co-missing-response`：一条真正需要Suno v6生成的纯器乐cue，为缺席后的余韵与片名供源；初次只需一对候选，不按镜头分别生成。暂不锁slides、Max Mode、时长或歌曲段式，不塞伪歌词。
- `co-s01-protect`：S01`INTENTIONAL_SILENCE`，保留其现有声音，禁止把“片头情绪统一”理解成重新配满S01。

`music/briefs.json`是现有schema的输入，`music/directions.json`是现有API的实际输出。`music/co-missing-response/style.txt`、`exclude.txt`和`dry-run.argv.json`均由该输出导出，没有第二套作曲编译器。离线`generate --dry-run`结果见同目录；其中`submitted=false`、`model_verified_live=false`不能证明v6账号权限或音乐效果。

当前没有可用的片头音乐源，不能给片尾伪造clip ID或`AssetRecord`。获得候选后先听两条，采用一条，记录SHA、clip ID、完整乐句与尾音区间；片头和片尾优先裁用这一条actual source，不通过再生成“same theme”冒充延续。独立CLI有其他命令不代表项目adapter已接通音频上传、stem、局部改写或extend，当前不绕过适配器来补这些能力。

## Current Suno Stop And Cost

本轮只作离线音乐准备，不运行generate live、不检查或更新凭据、不解验证码。当前同账号另一个执行窗口报告：两次已授权尝试均`auth_expired`、无clip，`doctor`显示captcha preflight required；项目`request-02`保存`PAID_PROVIDER_OUTCOME_UNKNOWN`、`new_submissions_allowed=false`。读取成功、认证刷新成功或库中暂时看不见clip都不足以重置UNKNOWN。

认证修复由该窗口独占，`suno_music.py`、其测试、旧ledger和STOP文件不归本任务写入。旧最多三次请求上限的历史消费不能因新cue或新目录归零；此次准备没有分配“可再试三次”。任何新live请求都要由原owner核对历史、outcome、剩余次数和当前授权／额度，按现有安全边界处理。本轮新增付费生成0次、无新增积分扣费事件；旧两次最终账单结算仍待其owner确认。

## Listening And Acceptance

干音乐先核对：没有人声／尖叫／突发重击，短动机可辨，发展不是流行主副歌，存在能自然剪辑的完整乐句和尾音。随后必须在exact开场＋片名＋S01上下文听：正常音量下电话与生活声是否可懂，缺席是否先于音乐被发现，音乐是否抢先解释异常，S01首字与动作声是否完整，片尾采用是否确为同源而非相似风格。

用手机扬声器补听，避免依赖听不到的超低频；耳机再查雨声高频疲劳和尾音接缝。响度、频谱、ASR与文件有效均不能代替该听感裁决。没有实际Suno音频和正常速度听看证据时，作曲质量、主题延续及最终混音均为`NOT_EVALUATED`。
