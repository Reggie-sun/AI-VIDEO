#!/usr/bin/env python3
"""Build pilot/s031-048/preview/index.html (first-frame / still candidates for IRIS EP01 s031–s048)."""
import hashlib
import html
import shutil
from pathlib import Path

V4 = Path("/home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v4")
D = "excerpt/flash/design/S31-48/"
OUT = V4 / "pilot/s031-048/preview"
REL = "../../../"
FACE = "excerpt/flash/design/S15-30/refs/face-P016b.png"


def sha(p):
    return hashlib.sha256((V4 / p).read_bytes()).hexdigest()


E = html.escape

# shot: (title, plan line, old plate or None, [(file, label, verdict)], rec file, changed, reason, issues)
SHOTS = [
    ("s031a / s031c · SG12 念白首帧（视频）", "她站在售货机旁正对镜头，左手收腰带，念白，最后眼睛往左一瞟；s031b 售货机静图盖中段。",
     "board/plates/p031.png",
     [("P031/a.png", "a：以 p031 编辑", "✓ 全项通过"), ("P031/b.png", "b：同 a 另一抽", "✓ 纸币上有不可读的淡纹")],
     "P031/a.png", "开场脸；闭嘴；不再塞币→正对镜头、折起的纸币垂在腰前；左手挨着腰带；售货机屏黑、商品素色无字无价签；走廊无出口灯。",
     "a 的纸币只有素边框、完全没有纹样；左手就在腰带上，方便视频第一拍收腰带。", []),
    ("s031b · 售货机静图（新做）", "她看到的：三台旧售货机，她在右缘侧身入画；图形在黑屏上砸名字和错误码。",
     None,
     [("S031B/a.png", "a：她在右缘半身入画", "✓"), ("S031B/b.png", "b：她全身站在走廊里", "✓ 不是“右缘入画”")],
     "S031B/a-2944.png", "新做：同一条走廊，三台机器各一块黑屏，商品素色；她 LC、侧脸朝机器，左耳红灯朝镜头。",
     "a 符合方案“右缘侧身入画”，三块黑屏都完整可做图形锚点。已 Lanczos 放大到 2944 宽。", ["侧脸，脸的比对只能看侧面轮廓与雀斑。"]),
    ("s032 · 闸机静图（拉焦）", "前景保安掌心（虚）→ 141.758 焦点拉到她脸；她停在闸机前一步、两手插兜看镜头。",
     "board/plates/p032.png",
     [("P032/a.png", "a：脸实", "✗ 远处拱门上方有一块红绿色出口牌 → 本地去色得 a-fix"),
      ("P032/b.png", "b：同 a 另一抽", "✗ 同一块出口牌"),
      ("P032/a-fix.png", "a-fix：a 去掉出口牌颜色（本地，只动 20×20 px）", "✓"),
      ("P032/a-palm.png", "a-palm：以 a-fix 编辑成掌心实、人虚", "✓ 拉焦另一端")],
     "P032/a-fix-2944.png", "开场脸；停步、两手插兜看镜头；闸机/保安台/袖子无字无臂章；另出掌心实版本供拉焦。",
     "a-fix（脸实）+ a-palm（掌心实）一对，后期在两张之间做焦点拉动；两张都已 Lanczos 放大到 2944 宽（a-palm-2944.png）。",
     ["她站在闸机列之间的空当里（不是闸机外一步），方案“停在闸机前一步”的意思仍成立，后期不动。"]),
    ("s033a · 档案通道远景（新做）", "两排报纸合订本的长通道，她小小站在尽头黄铜管站旁。",
     None,
     [("S033A/a.png", "a：她约占画高 1/5", "✓"), ("S033A/b.png", "b：她约占画高 1/3", "✓")],
     "S033A/a-2944.png", "新做：书脊素色无字；黄铜管站与接收篮在尽头；她 LC、正对镜头。",
     "a 的尺度最像方案“小小地站在尽头”，三条路线图有足够空墙面。", ["a 的脸只有十几像素高，远景里无法逐项比对脸（b 能看清，若你想远景也认得出脸就选 b）。"]),
    ("s033b · INS33 插镜首帧（视频）", "她的右手把黄铜筒推进管口、松手、盖子合上。",
     None,
     [("INS33/a.png", "a", "✓"), ("INS33/b.png", "b", "✓")],
     "INS33/b.png", "新做：黄铜管口特写、盖子开着，银灰风衣袖口的手握着素面铜筒停在管口外。",
     "b 的铜筒正对管口、手指五根清楚，推进动作的起始状态最明确；黄铜无刻字。", []),
    ("s034 · 手按黄铜盖静图", "重音冲击：她手掌平按黄铜盖、看镜头；管内铜筒层向上拖影（后期）。",
     "board/plates/p034.png",
     [("P034/a.png", "a：保留铰链盖", "✓"), ("P034/b.png", "b：盖子变成圆顶", "✓ 但读起来不像盖子")],
     "P034/a-2944.png", "开场脸；看镜头；闭嘴；黄铜盖无刻度刻字。",
     "a 的盖子有铰链，和 INS33 的开合盖是同一种东西。拖影用的铜筒层见 s035b 的 canister-2（单独元素）。",
     ["“另抠一层铜筒”没有从这张图里抠：盖子是合着的，看不见筒；改为单独出一张和 INS33 一样的铜筒元素（S035B/canister-2）。"]),
    ("s035a · 她 + 接收篮静图（新做）", "她站在黄铜接收篮旁抬眼看管口，篮子空。",
     None,
     [("S035A/a.png", "a", "✓"), ("S035A/b.png", "b", "✓")],
     "S035A/a-2944.png", "新做（p035 不用）：中景，她 LC、闭嘴、仰头看上方管子，篮子空。",
     "两张几乎一样，a 的脸更清楚。", ["她看的是篮子上方的竖管，不是正上方的出口嘴；时间戳图形不受影响。"]),
    ("s035b · 接收篮特写 + 铜筒元素（新做）", "铜筒层从画外落进篮子，155.26 落地冲一下（2.5D）。",
     None,
     [("S035B/a.png", "a：空篮特写", "✓"),
      ("S035B/canister.png", "canister：第一版铜筒元素", "✗ 有铰链和铆钉，和 INS33 手里的素面筒不一致"),
      ("S035B/canister-2.png", "canister-2：照 INS33/b 的筒重出", "✓ 浅灰平底，供抠层")],
     "S035B/a-2944.png", "新做：黄铜网篮特写（空）；另出一张素色背景上的铜筒元素，s035b 落入、s034 拖影共用。",
     "篮子与 s035a 同一种；canister-2 和 INS33 推荐件同一只筒。两张都已放大到 2944 宽。",
     ["铜筒还没抠成透明层（背景是平的浅灰，剪辑时抠）。"]),
    ("s036a / s036c · SG15 念白首帧（视频）", "阅览室过道：她站着、寻呼机攥在腰前；读者把椅子横在她前面，最后一句时让路。",
     "board/plates/p036.png",
     [("P036/a.png", "a", "✗ 风衣立领内侧一道粉红细线（像旧 L1 红线）；读者是深色卷发，容易被看成开场工程师"),
      ("P036/b.png", "b", "✗ 同一道粉红立领线"),
      ("P036/x.png", "x：以 b 编辑，只去掉立领粉线", "✓")],
     "P036/x.png", "开场脸；闭嘴；站定不走向镜头；右手攥寻呼机在腰前、液晶空白灰绿；读者横椅坐着抬头看她；书脊无字。",
     "x 去掉了粉红立领线，读者是灰发中年人（不会被认成工程师）。", ["读者的椅子只是侧坐在过道边上，没有完全横在她正前方；让路动作仍可写成“把椅子往桌子里拉”。"]),
    ("s037a · 工程师静图（新做）", "开场工程师在微波炉前举着手机僵住，她在后面料理台上（虚）。",
     None,
     [("S037A/a.png", "a", "✓"), ("S037A/b.png", "b", "✓")],
     "S037A/a-2944.png", "新做：开场工程师（深色卷发、胡茬、深蓝牛仔夹克）、微波炉内灯亮、显示屏黑、手机素背；她 LC 坐在料理台上。",
     "a 的工程师占画面更大、“僵住”的眼神更清楚。", ["她在背景里并不够虚（方案写“虚焦”），剪辑时按 B 类模糊加景深。"]),
    ("s037b / s037d · SG16 念白首帧（视频）", "她坐在料理台上、碗在腿上一直看镜头念白；画面左缘只有工程师的肩和举手机的手；微波炉出画。",
     "board/plates/p037.png",
     [("P037/a.png", "a：以 p037 编辑推近", "✗ 输出 1312×1199，不是 16:9"),
      ("P037/b.png", "b：同 a 另一抽", "✗ 同上"),
      ("P037/c.png", "c：按参考重新构图（中景）", "✓"),
      ("P037/d.png", "d：同 c 另一抽（人更近）", "✓")],
     "P037/d.png", "开场脸；闭嘴；碗在腿上；工程师换开场那位，只露肩、后脑和举手机的手；微波炉不在画面里；罐子无标签。",
     "d 的脸更大，念白口型更容易验收；工程师手和牛仔袖都在左缘。", []),
    ("s037c · INS37 插镜首帧（视频）", "他连按两下停止键，拔插头，灯灭转盘停。",
     None,
     [("INS37/a.png", "a", "✓"), ("INS37/b.png", "b", "✓")],
     "INS37/b.png", "新做：微波炉暖光、素色马克杯、黑显示屏、无字按键面板；牛仔袖口的手指按在最下一格；墙上插座和插头在画内。",
     "b 的插座和电线更清楚，拔插头这一下有落点。", ["插座是美式三孔（素色，无字）。"]),
    ("s038a / s038c · 楼梯静图", "她坐在台阶上，膝上两张空白半页纸并排，看镜头；s038c 裁紧 ≤1.1×。",
     "board/plates/p038.png",
     [("P038/a.png", "a", "✓"), ("P038/b.png", "b", "✓")],
     "P038/a-2944.png", "开场脸；闭嘴；两张空白半页纸；打开的空铜筒放在身边台阶上。",
     "a 更正面看镜头。已放大到 2944 宽，裁 1.1× 后仍高于 1920。", []),
    ("s038b · 半页纸插镜（新做）", "膝上两张半页纸微距特写，K 复印抖动。",
     None,
     [("S038B/a.png", "a", "✓"), ("S038B/b.png", "b", "✓")],
     "S038B/b-2944.png", "新做：两张空白撕开的半页纸，银灰风衣下摆、黑裤，浅景深。",
     "b 两张纸居中、撕口对着，手在角上不抢画面。", []),
    ("s039 · SG17 念白首帧（视频）", "低机位：她蹲在关着的门前，门缝下一线红光在指尖前；gap 上把手掌按进光里。",
     "board/plates/p039.png",
     [("P039/a.png", "a", "✓"), ("P039/b.png", "b", "✓")],
     "P039/b.png", "开场脸；闭嘴；看镜头；门无牌无字；红色只剩耳挂和门缝一线光。",
     "b 的眼神正对镜头。", ["两张的指尖都几乎贴着红线（提示词要求差一指宽）；视频里“按进光里”仍成立。"]),
    ("s040a · 保安亭静图", "越过研究员的肩：她已把他的马克杯拿在手里，他的手还停在半空。",
     "board/plates/p040.png",
     [("P040/a.png", "a", "✓"), ("P040/b.png", "b", "✓")],
     "P040/a-2944.png", "开场脸；闭嘴；杯子在她手里、他手空停半空；研究员改直发、眼镜、灰连帽衫、背对；监控画面无字。",
     "两张几乎一样；a 他的手离杯子更近，“刚被拿走”更好读。", []),
    ("s040b · 监控屏特写（新做，两个机位都要）", "176.518 换一个走廊机位，Eleven 上屏幕暗下去。",
     None,
     [("S040B/a.png", "a：第一版机位一", "✗ 显像管厚边屏，和 s040a 的平板屏不一致"),
      ("S040B/b.png", "b：第一版机位二", "✗ 同上"),
      ("S040B/a2.png", "a2：照 P040/a 的平板屏重出，机位一", "✗ 书架上方小牌子有伪文字划痕 → 本地模糊成空白牌得 a2-fix"),
      ("S040B/a2-fix.png", "a2-fix", "✓"),
      ("S040B/b2.png", "b2：机位二（十字路口 + 推车）", "✓")],
     "S040B/a2-fix-2944.png", "新做：s040a 那台细边框平板屏，黑白监控画面，空无一人，无时间码。",
     "a2-fix（176.518 前）+ b2（176.518 后）两张都用，均已放大到 2944 宽（b2-2944.png）。", []),
    ("s041a / s041c · SG18 唱段首帧（视频）", "夜里橱窗：她从肩到脚裹在防尘布里，只露脸；轻声唱。",
     "board/plates/p041.png",
     [("P041/c.png", "c：改写提示词后重出", "✓"), ("P041/d.png", "d：同 c 另一抽", "✓")],
     "P041/c.png", "开场脸；闭嘴；本白粗亚麻布像高领斗篷从下巴罩到脚，看不见任何衣服；人台都盖布无脸；玻璃无倒影。",
     "c、d 几乎一样，c 的布在胸前合拢的缝更清楚，方便 Octo- 时手从布里抓布边。",
     ["第一轮 a、b 两抽都被 image_gen 输出审核拦截（moderation_blocked，没有文件）；改写成“厚实不透明的高领斗篷”后通过。"]),
    ("s041b · INS41 插镜首帧（视频）", "两只黑袖子的手把防尘布从人台头顶拉下来，布落在 181.104 重音上。",
     None,
     [("INS41/a.png", "a", "✓"), ("INS41/b.png", "b", "✓")],
     "INS41/b.png", "新做：无五官素色人台，两只黑袖子的手把撑开的防尘布举在它头顶，后面人台已盖布。",
     "b 的布离头更近、两边垂得更低，落下更快能落在重音上。", ["人台是裸胸像（无五官、无乳头细节），和旧板子一致。"]),
    ("s042 · SG19 唱段首帧（视频）", "砰的灯全亮：她已是 W1，防尘布正从背上滑到脚边，站直唱。",
     "board/plates/p042.png",
     [("P042/a.png", "a：头到大腿", "✓ W1 全件入画"), ("P042/b.png", "b：头到腰", "✓ 脸更大"),
      ("P042/c.png", "c：试拉成中景", "✗ 输出竖图 1086×1448"), ("P042/d.png", "d：同 c", "✗ 输出竖图 1024×1536")],
     "P042/a.png", "开场脸；闭嘴；L1 → W1（灰不对称外套露左肩、右臂长袖、斜挎带右肩→左胯、腰链挂寻呼机和空白工牌、迷你裙、长靴）；布已离肩往下滑；射灯全亮。",
     "a 能同时看到 W1 每一件和正在落的布，换装这一刀最好读；b 的脸更大、口型更好验收（见上方决定 1）。", []),
    ("s043 · 橱窗远景静图（换气）", "清晨 Union Square 一排橱窗，她停在最后一扇前不动，标签按拍出现。",
     "board/plates/p043.png",
     [("P043/a.png", "a", "✓"), ("P043/b.png", "b", "✓")],
     "P043/a-2944.png", "开场脸（远景）；L1 → W1；站定不走；人台已揭布、无工人；店面无招牌字。",
     "a 腰链上的寻呼机和工牌更清楚。", ["檐口有装饰浮雕（不是文字）；远景脸约 25 px 高，只能看轮廓和发型。"]),
    ("s044 · 试衣间入口静图", "店员递来服装袋和活页夹，她翻页。",
     "board/plates/p044.png",
     [("P044/a.png", "a", "✓"), ("P044/b.png", "b", "✓")],
     "P044/a-2944.png", "开场脸；闭嘴；L1 → W1；活页夹纸页空白；服装袋无标志。",
     "两张几乎一样，a 手指更自然。", ["整张偏暖（底图就是暖光），指尖皮肤被红色检测标出，目检是肤色不是红色。"]),
    ("s045 · 两个隔间俯拍静图", "左格她（灯亮），右格副本（灯灭），副本只露头顶和手。",
     "board/plates/p045.png",
     [("P045/a.png", "a：保持底图斜俯拍", "✓"), ("P045/b.png", "b：同 a", "✓"),
      ("P045/c.png", "c：改正上方俯拍", "✓"), ("P045/d.png", "d：同 c", "✓ 她的耳挂灯看不清")],
     "P045/c-2944.png", "她：开场脸、W1、去立领红线、看镜头；副本：同发型与 W1，埋头抱膝，只露头顶、头发和手，耳挂不亮；右格灯灭。",
     "c 是方案写的“正上方俯拍”，两格就是示意图本身，最适合 AGENT A / AGENT B 框（见上方决定 2）。", ["副本的脸在四张里都完全看不到。"]),
    ("s046a / s046b · MO15 动作首帧（视频）", "她推衣架、隔板上方副本的手按秒表；s046b 从 4K 裁秒表。",
     "board/plates/p046.png",
     [("P046/a.png", "a", "✗ 她朝右侧身，看得见的是右耳，耳挂和红灯却戴在右耳；伸向衣架的左臂穿着袖子（W1 左臂应裸）"),
      ("P046/b.png", "b", "✗ 同 a"),
      ("P046/x.png", "x：以 a 编辑修这两处", "✓ 右耳无耳挂；左臂裸露")],
     "P046/x.png", "开场脸；L1 → W1；侧身面向挂衣杆；衣服无吊牌；隔板上方只有一只灰长袖的手和表盘空白的秒表。",
     "x 修好了耳挂边和左臂，其余与 a 一致。", ["搭在衣架上的是她的左手（方案 prompt 写“右手”）：拍之前 MO15 prompt 要改成“左手”。"]),
    ("s047 · 隔板缝静图", "她单膝跪在隔板下，从缝看过去，一张白纸条滑到手边。",
     "board/plates/p047.png",
     [("P047/a.png", "a", "✓"), ("P047/b.png", "b", "✓")],
     "P047/a-2944.png", "开场脸；L1 → W1；深蹲改单膝跪；纸条空白；闭嘴。",
     "a 单膝着地更明确。", []),
    ("s048 · SG20 念白首帧（视频）", "特写：她跪在隔板旁看镜头，轻声说完后静止闭嘴。",
     "board/plates/p048.png",
     [("P048/a.png", "a", "✓"), ("P048/b.png", "b", "✓")],
     "P048/b.png", "开场脸；闭嘴；L1 → W1；单膝跪；看镜头；双手和纸条都在画外。",
     "b 的耳挂灯清楚、着地的膝更明确。", ["景别是中近景（头到膝），不是大特写；需要更紧时从 4K 成片裁。"]),
]

DECISIONS = [
    "s042（SG19）首帧：<b>A 头到大腿（P042/a，推荐）</b>——W1 每一件和正在落下的布都在画里；B 头到腰（P042/b）——脸更大、口型好验收，但布和腰链以下看不到。",
    "s045 机位：<b>A 正上方俯拍（P045/c，推荐，方案写法）</b>；B 保持旧底图的斜俯拍（P045/a），两人的姿态更好读。",
    "s037b/d（SG16）首帧：<b>A 人更近（P037/d，推荐）</b>；B 中景、看得到更多茶水间（P037/c）。",
    "s033a 远景尺度：<b>A 她很小（S033A/a，推荐，方案写法）</b>；B 她大一点、远景里也认得出脸（S033A/b）。",
]


def fig(path, label, verdict, rec=False):
    s = sha(path)
    cls = " class=rec" if rec else ""
    bad = verdict.startswith("✗")
    return (f'<figure{cls}><a href="{REL}{path}" target="_blank"><img loading="lazy" src="{REL}{path}"></a>'
            f'<figcaption>{"<b>推荐</b> · " if rec else ""}{E(label)}<br><span class={"bad" if bad else "ok"}>{E(verdict)}</span>'
            f'<br><code>{E(path)}</code><br><small>sha256 {s[:16]}…</small></figcaption></figure>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evidence").mkdir(exist_ok=True)
    shutil.copyfile("/tmp/s031pv/rev/z-up.jpg", OUT / "evidence/esrgan-vs-native.jpg")
    p = []
    p.append('<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>IRIS EP01 s031–s048 首帧/静图预览</title><style>'
             'body{background:#111;color:#ddd;font:14px/1.55 sans-serif;margin:20px;max-width:1800px}img{width:100%;display:block}'
             '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:14px}figure{margin:0}figure.rec{outline:3px solid #6c6}'
             'figure.ref img{max-height:260px;object-fit:contain;background:#000}h2{margin-top:36px;border-top:1px solid #444;padding-top:14px}'
             'code{color:#9cf;font-size:11px}.act{color:#fc6}.bad{color:#f88}.ok{color:#8d8}.iss{color:#f99}.box{border:1px solid #6c6;padding:10px 14px;background:#182018}'
             'table{border-collapse:collapse}td,th{border:1px solid #555;padding:3px 6px;font-size:12px;vertical-align:top}</style></head><body>')
    p.append('<h1>IRIS EP01 s031–s048 首帧与静图候选（只有静图，没有提交任何视频生成）</h1>')
    p.append('<p>按已认可的导演方案（<a href="../plan/index.html">plan</a>；logs/decisions.md 2026-11-24「按方案做首帧预览」及三处分叉 A）制作。旧底图 <code>board/plates/</code> 一张没改；候选在 <code>excerpt/flash/design/S31-48/&lt;镜&gt;/</code>，每个文件夹有 <code>prompt.md</code>（原样送给 image_gen 的提示词）、<code>runs.md</code>（每次调用的参考图 sha、输出 sha）、<code>sha256.txt</code>。'
             '工具：<code>motion-kit/tools/codex_plate.py</code>（--edit-base 旧底图 + --ref）；脸参考与 s015–s030 相同：<code>S15-30/refs/face-P016b.png</code>、<code>face-F1a.png</code>；W1 参考 <code>board/plates/p011-w1c.png</code>、<code>S15-30/refs/w1-close-p012w1.png</code>；工程师 <code>S15-30/refs/engineer-p012w1.png</code>；LC 风衣参考从 p031 裁出、不含脸（<code>S31-48/refs/lc-coat-p031.png</code>）。绿框 = 推荐。</p>')
    p.append('<div class=box><h3 style="margin-top:0">要你决定的（4 项，其余都按推荐）</h3><ol>' + "".join(f"<li>{d}</li>" for d in DECISIONS) + '</ol></div>')
    p.append('<p>自检（每张都做）：1400 宽全图目检 + 240 宽缩略看整体；脸用 haar 检测裁出后和开场脸（P016/b、F1a）并排；红色用像素检测（R 主导且 G&lt;0.5R、B&lt;0.55R，或色相在红 ±15° 且饱和度、亮度 &gt;0.35）定位再目检——粉红色的细线检测不到，所以风衣立领另做了一张放大并排逐张看；文字、手指、服装、嘴、耳挂在哪只耳朵逐张放大看。'
             '视频首帧保持 image_gen 原图 1672×941（和 s015–s030 的首帧一样）；静图推荐件另存 <code>*-2944.png</code>，用 Lanczos 放大到 2944 宽。'
             'Real-ESRGAN（本机 realesr-general-x4v3）先试过，弃用：它把她的雀斑抹掉（脸变了），还把书脊锐化出像字的笔画，见 <a href="evidence/esrgan-vs-native.jpg">对比图</a>（左原图 / 右 ESRGAN）。观感好坏由你判，下面只是我的核对。</p>')
    p.append('<p>新图数量：方案表里新做是 10 行（s031b、s033a、INS33、s035a、s035b、s037a、INS37、s038b、s040b、INS41），比交代的 “9 张” 多 1 张；全部做了。另外 s040b 要两个机位、s032 要掌心实的拉焦版、s035b 加了一张单独的铜筒元素。旧底图 p033、p035 方案里不用，没有改。</p>')
    for title, plan, old, cands, rec, changed, reason, issues in SHOTS:
        p.append(f'<h2>{E(title)}</h2><p class=act>方案：{E(plan)}</p><div class=g>')
        if old:
            p.append(f'<figure><a href="{REL}{old}" target="_blank"><img loading="lazy" src="{REL}{old}"></a><figcaption>旧底图（未改）<br><code>{E(old)}</code><br><small>sha256 {sha(old)[:16]}…</small></figcaption></figure>')
        recbase = rec.replace("-2944", "")
        for f, label, verdict in cands:
            p.append(fig(D + f, label, verdict, rec=(f == recbase)))
        p.append(f'<figure class=ref><a href="{REL}{FACE}" target="_blank"><img loading="lazy" src="{REL}{FACE}"></a><figcaption>开场脸（对照）<br><code>{FACE}</code></figcaption></figure>')
        p.append('</div>')
        p.append(f'<p><b>改了什么：</b>{E(changed)}</p>')
        recpath = D + rec
        p.append(f'<p><b>推荐：</b><code>{E(recpath)}</code>（sha256 <code>{sha(recpath)}</code>）。{E(reason)}</p>')
        for i in issues:
            p.append(f'<p class=iss>待处理：{E(i)}</p>')
    p.append('<h2>没做 / 做不到的</h2><ul>'
             '<li>没有提交任何即梦或 Seedance 视频，没有付费调用；没有改 board/、没有改旧底图、没有 commit。</li>'
             '<li>“另抠一层铜筒”只给了平底元素图（canister-2），透明层留给剪辑抠。</li>'
             '<li>MO15 的 prompt 还写着“右手”，首帧里是左手搭衣架，拍之前要改。</li></ul>')
    p.append('</body></html>')
    (OUT / "index.html").write_text("\n".join(p), encoding="utf-8")
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
