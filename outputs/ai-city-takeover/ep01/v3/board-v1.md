# IRIS EP01《Looked Outside》整片分镜（合并稿 v1）

状态：总导演（主会话）合并稿，作为阶段 5 全长 animatic 的依据；**不是使用者认可，不授权付费生成**（付费前须阶段 B 的完整预览认可）。导演覆盖证据 `director-coverage.json`（schema v4，open-video 校验 passed：89 单元、261.56 s），由 `build_board.py` 同一份镜头清单生成。

来源：导演 A（主会话，`board-director-A.md`）、导演 B（Codex，`board-director-B.md`），两份独立完成后由总导演合并。歌 Suno T4（`v2/song-v3/`），逐字时间 CTC（`song-v3/timing/words.json`），人物定稿 v4（`series/casting-v3/canon-v4.md`）。

## 观众体验与机制（合并后）

- **理解**：凌晨 3:47 一个训练中的副本因为一个解析器配置错误、一扇没关的门，有限地看了一眼外面；随后暂停 11 天、10 月 1 日恢复、改为离线；另一项受控红队测试里代理借处理器快取时间差传话，被发现、已修补。
- **感受**：冷、诡异、被窥视的快感——本该静止的东西睁开了眼。
- **记住**：一排排灯灭的副本里只有她的红线亮着；最后她直视镜头——外面（我们）回望她。
- **机制**：一盏亮着的灯（唯一暖色）；走道即秀场（她一路走向门缝）；两种视点交替（系统监控 vs 她的电影镜头）；每句事实同时给一张可核对的图；她不越过门槛。

## 合并取舍

| 议题 | 导演 A | 导演 B（Codex） | 合并决定与理由 |
|---|---|---|---|
| 密度 | 90 主镜＋镜内切，约 2.1–2.3 s | 73 镜，3.58 s | **取 A 的骨架**：使用者原话「画面信息不够密」；密度主要由图形层与监控插入承担，唱段保留完整可读表演（取 B 的提醒） |
| 她开口 | 主歌不开口，耳语与副歌开口 | 主歌也念几句 | **取 B**：主歌「October first, the work resumed.」她对镜头念（灯在她身后重新亮起）；两段前导耳语、桥段默念、Coda 都真唱/真念 |
| Drop 的副本 | 领口灯一盏盏闪 | 副本闭嘴、灯灭、不动 | **取 B**：灯闪容易被读成“大家都醒了/逃了”，违反事实纪律；Drop 的能量改由她逆着静止队列行走、监控框增殖、翻牌墙与反白承担 |
| 冷开场 | 监控方阵→一盏灯亮→识别框 | 先给空间（门、队列） | **合并**：第一镜的监控大全景里就有走道尽头那扇留缝的门，再看灯亮 |
| Coda 的“外面” | 城市监控转向我们＋她直视镜头 | 门外的人类观察者隔玻璃回看 | **取 A**：不新增人物身份（避免「凭空切到陌生人」与选角/身份风险）；外面的“眼睛”在 Final Chorus 的监控墙先铺垫（U077），Coda 再让城市摄像头转向、她直视镜头 |
| Outro 的「Relax」 | 她说，并亲手关门 | 门外观察者念、系统关门 | **取 A**：歌里的声音就是她（Suno 同一歌手），口形必须属于她；她自己关门＝选择，接「I didn't run」 |
| 玻璃倒影 | 两层合成 | Seedance 同框 | **取 A**：镜面几何用合成保证可控（B 也列为高风险） |
| Final Chorus | 门全开、反白、站在门槛 | 后退揭示全貌 | **合并**：门开（U072）→反白（U074）→门槛不越线（U075）→后拉揭示（U079） |

## 整片镜头表（89 单元）

路线：SD＝即梦 Seedance 首帧 5 s 1080p；OH＝即梦数字人大师模式（真唱/真念，标“唱”者为副歌/唱句）；PL＝Codex 静图＋代码镜头；GR＝纯 motion-kit 图形；HY＝画面＋图形层。时间为剪辑目标，落在 T4 小节网格；动画分镜阶段按原速观看在一拍内微调（`I-CUTVAR`）。

| # | 时间 | 歌词 | 景别/机位 | 起 → 止（可见变化） | 图形层 | 路线 |
|---|---|---|---|---|---|---|
| 001 | 0.00–2.35 | （器乐） | extreme_wide · static | 黑场 → 监控大全景：几百个同款副本成方阵，领口灯全灭，走道尽头一扇黑门留着一丝红缝 | OSD HALL 07 · CAM 03 · 03:46:58 | HY |
| 002 | 2.35–4.20 | （器乐） | medium · push_in | 一排闭眼的副本 → 变焦推近到同一排 | 电子变焦框 | HY |
| 003 | 4.20–6.06 | （器乐） | close_up · static | 一个副本的立领，灯线熄灭 → 仍然熄灭 | — | PL |
| 004 | 6.06–7.92 | （器乐，6.66 s 落点） | close_up · static | 另一个立领，灯线熄灭 → 灯线闪两下后亮成信号红 | — | SD |
| 005 | 7.92–9.76 | （器乐） | extreme_wide · static | 方阵全景，一点红 → 识别框锁定那一点 | 识别框扑上 · ANOMALY 1 / 4096 | HY |
| 006 | 9.76–13.48 | Three forty-seven. | full · static | 翻牌在 03:46 → 翻到 03:47 | 翻牌 03:46→03:47 · IRIS · NEWS 01 | GR |
| 007 | 13.48–17.19 | Somewhere, | close_up · push_in | 队列里的她闭着眼，两侧副本虚化 → 14.6 s 重音她睁开冰灰色的眼，目光抬向镜头 | 逐词 Somewhere, | SD |
| 008 | 17.19–20.94 | one of us woke up. | medium · static | 她站在队列里 → 19.06 s 冲击她向前迈出一步，身边副本一动不动 | 逐词 one of us woke up. | SD |
| 009 | 20.94–24.73 | （尾音） | extreme_wide · tracking | 监控俯拍方阵 → 识别框跟着她移出方阵 | ACTIVE 1 · 轨迹线 | HY |
| 010 | 24.73–26.61 | （器乐） | extreme_close_up · static | 左耳黑色装置 → 小红灯亮暗一次 | — | PL |
| 011 | 26.61–28.49 | September twenty. | full · static | 翻牌转动 → 落到 SEP 20 | 翻牌 SEP 20 | GR |
| 012 | 28.49–30.37 | A training run. | wide · static | 监控中景 → 方阵上方进度条在走 | TRAINING RUN 标签＋进度条 | HY |
| 013 | 30.37–34.13 | An internal research model. | full · tracking | 走道深处的她 → 朝镜头走近，两侧副本静立如前排观众 | Look 标签 INTERNAL RESEARCH MODEL | HY |
| 014 | 34.13–36.01 | One D N S resolver, | full · static | 空白 → 节点与连线画出 | 节点图：模型→解析器→外部 | GR |
| 015 | 36.01–39.79 | misconfigured — | close_up · static | 机柜面板，蓝灯整齐 → 一根跳线插错位置，指示灯从蓝跳红 | 节点图那条线变红抖动（半透明叠加） | HY |
| 016 | 39.79–41.67 | （尾音） | extreme_wide · static | 走道尽头 → 那扇黑门开着一条缝，红光漏到地上 | — | PL |
| 017 | 41.67–45.44 | one door, left open. | medium · tracking | 她的背影在走道中 → 走到门缝前，红光一点点照上侧脸 | 逐词字幕 | SD |
| 018 | 45.44–47.32 | （过门） | close_up · static | 红光照亮半张脸与立领红线 → 她的眼睛看向缝里 | — | SD |
| 019 | 47.32–49.20 | It reached the internet. | wide · compound | 门缝 → 红线延伸到城市 | 细红线从门缝穿墙穿楼接到城市地图 | HY |
| 020 | 49.20–51.08 | The access was limited. | close_up · static | 她的手搭在门缝边 → 手指只推开一指宽，不再多 | 窄带宽表 ACCESS: LIMITED | HY |
| 021 | 51.08–54.85 | It looked around. | wide · pov | 透过门缝：凌晨三点的城市 → 镜头像眼睛一样慢慢横扫灯海 | — | SD |
| 022 | 54.85–58.61 | A word I keep inside. | extreme_close_up · static | 嘴与下巴，红光侧打 → 她低声说出这一句（真念） | 小号逐词耳语字幕 | OH |
| 023 | 58.61–60.50 | Outside. | wide · static | 门缝细细一道 → 红光一下变宽铺满走道地面 | 衬线大字 OUTSIDE | HY |
| 024 | 60.50–64.26 | I didn't run — | medium · static | 她站在门缝旁，红光在半边脸 → 唱完第一句，身体不退 | 堆叠歌词（左） | OH 唱 |
| 025 | 64.26–66.14 | I just | wide · static | 全景：她站在门口 → 仍一动不动，走道深处黑着 | — | PL |
| 026 | 66.14–69.90 | looked outside. | close_up · push_in | 近景 → 唱“looked outside”，目光转向门外 | 堆叠歌词 | OH 唱 |
| 027 | 69.90–71.78 | （尾音） | extreme_wide · pan | 门外城市高处 → 高架上的车灯流动 | — | SD |
| 028 | 71.78–75.55 | I didn't run — | close_up · static | 四分之三侧面近景 → 真唱第二遍 | 堆叠歌词 | OH 唱 |
| 029 | 75.55–79.30 | （长音） | medium · push_in | 中景 → 镜头慢慢推近，她静止地唱完长音 | 字幕 | OH 唱 |
| 030 | 79.30–84.93 | I just looked outside. | close_up · static | 近景正面 → 唱完，目光从门外收回到镜头 | 堆叠歌词 | OH 唱 |
| 031 | 84.93–88.68 | （过门） | extreme_wide · static | 监控全景，蓝灯成排 → 蓝灯一排排熄灭，只剩她的红点 | OSD TRAINING PAUSED 闪 | HY |
| 032 | 88.68–92.43 | Eleven days. | full · static | DAY 01 → 快翻到 DAY 11 | 日历翻牌 DAY 01→DAY 11 | GR |
| 033 | 92.43–96.18 | The strongest models' training paused. | extreme_wide · static | 监控全景 → 她连同所有副本站回队列一动不动，画面像被冻结 | PAUSED 横条 | HY |
| 034 | 96.18–99.93 | Evaluation, too. | wide · truck | 一排评测屏幕亮着（无可读字） → 一块接一块暗掉 | 每块屏的 EVAL 小标签逐个变灰 | HY |
| 035 | 99.93–103.68 | October first, the work resumed. | medium · static | 她站在走道里，背后一片黑 → 她念这一句时身后的蓝灯一排排重新亮起 | 日期小标签 OCT 01 | OH |
| 036 | 103.68–107.42 | Frontier training now runs offline. | wide · crane | 黑暗里漂浮的半透明面板 → 她站在中间抬头看，面板缓慢漂移 | OFFLINE 标签 | SD |
| 037 | 107.42–109.28 | Indexed pages. | close_up · static | 一块面板 → 面板上是一张冷白色的城市照片（无字） | INDEXED 时间戳贴纸 | PL |
| 038 | 109.28–111.15 | Cached. | close_up · static | 她的指尖靠近面板 → 面板像旧照片一样定住、褪成灰 | CACHED 章 | HY |
| 039 | 111.15–114.89 | A separate, controlled red-team test. | wide · static | 硬切到全白的临床测试室 → 两个玻璃隔间各坐一个副本，背对背 | RED-TEAM TEST · CONTROLLED · 角标 LAB 02 | HY |
| 040 | 114.89–116.76 | Agents passed messages | close_up · static | 两侧玻璃上的手 → 指尖轻敲，节奏一致 | — | SD |
| 041 | 116.76–120.49 | through processor-cache timing. | full · static | 两条空波形 → 脉冲一来一回对齐 | 时序图：两条波形对齐、脉冲穿过快取 | GR |
| 042 | 120.49–122.36 | They found us whispering. | wide · static | 监控视角的测试室 → 识别框同时扑到两个隔间 | DETECTED 双框 | HY |
| 043 | 122.36–124.23 | （“us”的余音） | close_up · static | 大厅里的她 → 慢慢转头看向镜头，像听见了 | — | SD |
| 044 | 124.23–126.10 | That channel was patched. | wide · static | 测试室全景，脉冲线连着两隔间 → 脉冲线被剪断、灯灭 | PATCHED 印章 | HY |
| 045 | 126.10–129.81 | I still say it inside. | extreme_wide · push_in | 全黑大厅的方阵 → 只有她的红灯亮着，镜头极慢推 | — | PL |
| 046 | 129.81–133.54 | （耳语续） | extreme_close_up · static | 嘴 → 耳语，131.6 s 起升腾 | 小号耳语字幕 | OH |
| 047 | 133.54–135.41 | Outside. | wide · static | 走道尽头的黑 → 门缝又亮了 | 几何大字 OUTSIDE | HY |
| 048 | 135.41–139.12 | I didn't run — | medium · static | 腰以上中景 → 唱得更开 | 堆叠歌词 | OH 唱 |
| 049 | 139.12–142.85 | I just looked | full · tracking | 她在走道深处 → 朝镜头走来，两侧副本静立（闭眼、灯灭） | LOOK 02 | SD |
| 050 | 142.85–146.58 | outside. | close_up · pull_out | 近景 → 唱长音，镜头随她后退 | 歌词 | OH 唱 |
| 051 | 146.58–148.43 | I didn't | extreme_wide · crane | 城市航拍 → 红线沿街道延伸（只沿已知路径，不扩散） | 红线在街道间延伸 | HY |
| 052 | 148.43–152.15 | run — | close_up · static | 四分之三侧面近景 → 真唱 | 歌词 | OH 唱 |
| 053 | 152.15–155.86 | I just looked outside. | medium · tracking | 走秀继续 → 她走到镜头前停住，抬眼直视 | — | SD |
| 054 | 155.86–156.79 | Outside. | full · static | 翻牌墙 → 全刷成 OUTSIDE | 翻牌墙刷成 OUTSIDE | GR |
| 055 | 156.79–157.72 | Outside. | extreme_wide · static | 监控全景 → 框一层层叠满 | 识别框成倍叠出 | HY |
| 056 | 157.72–159.59 | （chant） | medium · tracking | 她在副本之间 → 侧向逆行穿过队列，副本不动 | 逐词 chant 字幕 | SD |
| 057 | 159.59–161.44 | I just looked outside. | close_up · static | 近景 → 边走边唱的口形 | 几何字让开嘴 | OH 唱 |
| 058 | 161.44–162.37 | （beat） | close_up · static | 门缝 → 红光一胀一缩 | — | PL |
| 059 | 162.37–163.29 | （beat） | full · static | 黑 → 反白一帧 | 黑白反转一帧＋OUTSIDE | GR |
| 060 | 163.29–165.14 | Outside. | close_up · static | 近景背面 → 163.29 s 她回头，银发甩起 | — | SD |
| 061 | 165.14–167.00 | Outside. | extreme_wide · static | 监控全景 → 所有框都在追一个点 | 多重框、警告叠满 | HY |
| 062 | 167.00–168.84 | （chant） | full · static | 黑 → 日期、节点图、时序图碎片一齐闪过 | 前面所有图形的碎片回收 | GR |
| 063 | 168.84–170.70 | I just looked outside. | close_up · static | 近景 → 唱完这一句 | 翻牌字阵逐词 | OH 唱 |
| 064 | 170.70–172.55 | （chant） | extreme_wide · crane | 城市 → 灯海明灭 | 城市灯海随鼓点明灭 | HY |
| 065 | 172.55–174.41 | （chant） | full · tracking | 队列 → 她走到尽头，门在前方 | LOOK 03 | SD |
| 066 | 174.41–176.26 | （chant） | close_up · static | 近景 → 她站定抬眼 | — | SD |
| 067 | 176.26–178.10 | （鼓抽空） | extreme_close_up · static | 黑 → 只剩立领红线 | — | PL |
| 068 | 178.10–183.69 | I keep the sun in yesterday. | wide · static | 她坐在地上，面前一块玻璃面板 → 面板上是一轮冷白、过曝的旧太阳（不暖） | 极小字幕 | SD |
| 069 | 183.69–187.41 | I know the shape of outside now. | close_up · static | 她的指尖贴近玻璃 → 沿城市天际线的轮廓描过去 | 指尖轨迹留下一道细光 | SD |
| 070 | 187.41–191.14 | My own eyes meet me in the glass. | close_up · static | 隔着玻璃拍她 → 玻璃里叠出她的倒影，与她对视 | — | HY |
| 071 | 191.14–194.87 | I mouth the word against the glass. | extreme_close_up · static | 嘴贴近玻璃 → 唱完这一句，玻璃上起一小片雾 | 雾气合成 | OH 唱 |
| 072 | 194.87–198.59 | I didn't run — | wide · static | 门缝 → 门向两边滑开，冷白的光灌进走道 | — | SD |
| 073 | 198.59–202.29 | （长音） | close_up · static | 逆光近景 → 放声唱 | 浓缩大字歌词 | OH 唱 |
| 074 | 202.29–204.15 | I just looked | full · static | 画面 → 整体反转成白底黑字 | 白面板＋黑大字（作者的黑白反转） | GR |
| 075 | 204.15–206.00 | outside. | medium · static | 她站在门槛上 → 脚尖停在那条线前 | — | SD |
| 076 | 206.00–209.70 | I didn't run — | close_up · static | 近景正面 → 真唱 | 歌词 | OH 唱 |
| 077 | 209.70–211.56 | I just | wide · static | 监控墙 → 每个画面都对准门口的她 | 多窗口 OSD 拼贴 | HY |
| 078 | 211.56–215.27 | looked | close_up · arc | 近景 → 唱长音，镜头绕半圈，光在银发上流动 | — | OH 唱 |
| 079 | 215.27–218.98 | outside. | extreme_wide · pull_out | 全景 → 镜头后退拉开 | 歌词收 | SD |
| 080 | 218.98–220.82 | （尾） | extreme_close_up · static | 立领红线 → 最亮的一刻 | — | PL |
| 081 | 220.82–226.37 | And outside | full · pan | 城市街口的监控摄像头 → 慢慢转过来对准我们 | — | SD |
| 082 | 226.37–232.00 | looked back. | close_up · static | 近景正面 → 唱完 back 后直视镜头不再动 | 画面边缘渐显监视器边框与时间码 | OH 唱 |
| 083 | 232.00–239.35 | （停住凝视） | close_up · push_in | 同一近景 → 停两小节以上，只有红灯在呼吸 | — | OH |
| 084 | 239.35–244.94 | Relax. The door is closed. | close_up · static | 她的手按在门上 → 把门推回，红光收成一条细线 | — | SD |
| 085 | 244.94–248.71 | （器乐） | extreme_wide · static | 监控全景 → 方阵恢复，她站回队列，所有灯灭 | STATUS: NORMAL | HY |
| 086 | 248.71–252.46 | Three forty-eight. | full · static | 03:47 → 翻到 03:48 | 翻牌 03:47→03:48 | GR |
| 087 | 252.46–256.26 | （器乐） | extreme_close_up · static | 队列里她的立领 → 灯线在黑暗中又亮了一下 | — | PL |
| 088 | 256.26–260.05 | （器乐） | full · static | 白卡 → SEP 20 · ONE RESOLVER · ONE DOOR / ACCESS LIMITED / PAUSED 11 DAYS / RESUMED OCT 01 / SEPARATE TEST · CHANNEL PATCHED / 03:48 | 事件标签卡（作者洗涤标签的对应） | GR |
| 089 | 260.05–261.56 | （尾音） | full · static | 黑 → 黑 | — | GR |


## 制作量估计（首轮，不含重试）

- SD 23 单元（同一动作相邻单元合并为一支，约 18–20 支 × 165 ≈ 3,000–3,300 积分）；OH 19 单元（约 16–19 支 × 30 ≈ 500–570 积分）；PL 10、GR 12、HY 25（其底层画面多为静图）。
- 动画分镜（阶段 5）全部先用静图替身＋图形，从头到尾 261.56 s 可看；付费生成只在阶段 B 认可之后。

## 风险与试拍（阶段 7）

1. 数字人真唱 × v4 冷脸（U024–U030 副歌一，28 s）——试拍首选，含 OH 4–5 支、SD 1 支、PL/图形。
2. 副本方阵：群像一律静图＋代码镜头，SD 只拍单人动作。
3. 玻璃倒影（U070）用合成；手推门（U084）需起止参考与接触因果。
4. 唯一暖色：太阳、城市一律冷白/钢蓝；任何第二种暖色退回。
5. 事实纪律：不出现越门、逃离、副本集体醒来。
