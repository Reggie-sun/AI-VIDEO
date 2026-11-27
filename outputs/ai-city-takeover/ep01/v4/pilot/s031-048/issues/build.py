#!/usr/bin/env python3
"""Build pilot/s031-048/issues/index.html: the pre-submit continuity gaps for s031-s048 and their fixes (2026-11-24).

  /home/reggie/miniconda3/bin/python outputs/ai-city-takeover/ep01/v4/pilot/s031-048/issues/build.py

Reads the prompt drafts before / after (excerpt/flash/s031-048-seedance.md[.before-continuity-2026-11-24]), the old and
new first frames and the CONT1124 design candidates; writes side-by-side JPEGs next to this file and the page.
No Provider, no approval, no board write.
"""
import difflib
import hashlib
import html
import re
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
V4 = HERE.parents[2]
D = V4 / "excerpt/flash/design/S31-48"
C = D / "CONT1124"
PL = V4 / "board/plates"
MD = V4 / "excerpt/flash/s031-048-seedance.md"
E = html.escape


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 + 9 * len(text), 22], fill=(0, 0, 0))
    d.text((5, 5), text, fill=(255, 220, 120))
    return im


def row(name, tiles, h=420):
    """tiles: [(path, box or None, label)] scaled to height h, side by side."""
    ims = []
    for path, box, lab in tiles:
        im = Image.open(path).convert("RGB")
        if box:
            im = im.crop(box)
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        ims.append(label(im, lab))
    out = Image.new("RGB", (sum(i.width for i in ims) + 8 * (len(ims) - 1), h), (12, 12, 12))
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width + 8
    out.save(HERE / name, quality=88)
    return name


def blocks(text):
    return dict(re.findall(r"^## s\d{3} · (\w+) · .*?\n\n```prompt\n(.*?)\n```", text, re.S | re.M))


def diff_html(a, b):
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(E(a[i1:i2]))
        if op in ("delete", "replace"):
            out.append(f"<del>{E(a[i1:i2])}</del>")
        if op in ("insert", "replace"):
            out.append(f"<ins>{E(b[j1:j2])}</ins>")
    return "".join(out)


old = blocks(Path(str(MD) + ".before-continuity-2026-11-24").read_text(encoding="utf-8"))
new = blocks(MD.read_text(encoding="utf-8"))

# ---------------------------------------------------------------- pictures
img = {
    "boots42": row("boots-sg19.jpg", [(PL / "p042-w1.png", None, "BEFORE p042-w1 (over-knee)"),
                                      (PL / "p042-w2.png", None, "AFTER p042-w2 (knee-high)")], 470),
    "boots42z": row("boots-sg19-zoom.jpg", [(PL / "p042-w1.png", (600, 700, 1400, 941), "before"),
                                            (PL / "p042-w2.png", (600, 700, 1400, 941), "after")], 260),
    "mo15": row("mo15.jpg", [(PL / "p046-w1.png", None, "BEFORE p046-w1"), (PL / "p046-w2.png", None, "AFTER p046-w2")], 470),
    "mo15z": row("mo15-zoom.jpg", [(PL / "p046-w1.png", (1000, 100, 1672, 941), "before: rail full to the partition"),
                                   (PL / "p046-w2.png", (1000, 100, 1672, 941), "after: bunched at her end, bare rail")], 420),
    "mw": row("microwave.jpg", [(D / "S037A/a.png", None, "s037a still S037A"), (PL / "p037-c1.png", None, "BEFORE p037-c1"),
                                (PL / "p037-c2.png", None, "AFTER p037-c2")], 330),
    "mwz": row("microwave-zoom.jpg", [(D / "S037A/a.png", (600, 330, 1200, 640), "S037A"),
                                      (PL / "p037-c1.png", (300, 250, 1000, 700), "before"),
                                      (PL / "p037-c2.png", (300, 250, 1000, 700), "after")], 300),
    "ins37": row("ins37.jpg", [(D / "S037A/a.png", None, "S037A: phone in RIGHT hand"),
                               (PL / "p037-ins37.png", None, "BEFORE: right hand from right"),
                               (PL / "p037-ins37b.png", None, "AFTER: mirrored, left hand from left")], 330),
    "p047": row("p047.jpg", [(D / "P047/a.png", None, "BEFORE P047/a: partition LEFT"),
                             (C / "p047-rb-b.png", None, "AFTER rb-b: partition RIGHT")], 470),
    "axis": row("p047-axis.jpg", [(D / "P045/c-2944.png", None, "s045"), (PL / "p046-w2.png", None, "s046 (MO15)"),
                                  (C / "p047-rb-b.png", None, "s047 new"), (PL / "p048-w1.png", None, "s048 (SG20)")], 250),
    "p047alt": row("p047-alts.jpg", [(C / "p047-rb-a.png", None, "rb-a"), (C / "p047-ra-a.png", None, "ra-a (edit of p048)"),
                                     (C / "p047-ra-b.png", None, "ra-b (edit of p048)")], 300),
    "p047z": row("p047-zoom.jpg", [(C / "p047-rb-b.png", (1220, 820, 1560, 920), "paper: dots/dashes only"),
                                   (C / "p047-rb-b.png", (600, 100, 920, 400), "face + left-ear lamp"),
                                   (V4 / "excerpt/flash/design/S15-30/refs/face-P016b.png", None, "opening face ref"),
                                   (V4 / "excerpt/flash/design/S15-30/refs/face-F1a.png", None, "F1a ref")], 260),
    "p047s": row("p047-240.jpg", [(C / "p047-rb-b.png", None, "240 px")], 135),
}
# 240 px view of every new first frame
small = [Image.open(p).convert("RGB").resize((240, 135), Image.BOX) for p in
         (PL / "p037-c2.png", PL / "p037-ins37b.png", PL / "p042-w2.png", PL / "p046-w2.png", C / "p047-rb-b.png")]
s = Image.new("RGB", (5 * 248, 135), (12, 12, 12))
for i, im in enumerate(small):
    s.paste(im, (i * 248, 0))
s.save(HERE / "all-240.jpg", quality=90)

files = {k: (p, sha(p)) for k, p in {
    "p037-c2": PL / "p037-c2.png", "p037-ins37b": PL / "p037-ins37b.png", "p042-w2": PL / "p042-w2.png",
    "p046-w2": PL / "p046-w2.png", "P047 rb-b": C / "p047-rb-b.png", "P047 rb-b-2944": C / "p047-rb-b-2944.png"}.items()}


def fsha(k):
    p, h = files[k]
    return f'<span class="d">{E(str(p.relative_to(V4)))} · sha256 {h}</span>'


def pdiff(unit):
    return f'<div class="pr">{diff_html(old[unit], new[unit])}</div>'


# ---------------------------------------------------------------- page
P = []
P.append("""<!doctype html><html lang="zh"><meta charset="utf-8"><title>s031–s048 提交前连续性问题与修正</title>
<style>body{background:#111;color:#ddd;font:15px/1.65 sans-serif;max-width:1500px;margin:24px auto;padding:0 16px}
img{max-width:100%;display:block;margin:6px 0}h2{color:#f3d9a8;margin-top:34px;border-top:1px solid #333;padding-top:14px}
.pr{background:#1c1c1c;padding:10px 12px;border-radius:6px;white-space:pre-wrap}del{background:#5a1f1f;color:#f0b0b0}
ins{background:#1f4a2a;color:#b8f0c0;text-decoration:none}.d{color:#8a96a3;font-size:13px}.rec{color:#9fe0a8}
.dec{background:#1d2430;border:1px solid #3a4a60;padding:10px 16px;border-radius:6px}.warn{color:#ffb4a8}</style>
<h1>IRIS EP01 s031–s048 · 提交前连续性检查：问题与修正（待你重新认可）</h1>
<p class="d">2026-11-24。场记（continuity-supervisor）提交前报告的缺口已逐条改好。没有提交任何即梦 / Seedance，没有付费调用，没有写 approval，没有 commit。
新图都是新文件（旧首帧、旧设计件一个没覆盖）；SG16 / SG19 / MO15 的新首帧是“本地有界合成”：Codex 只改了要改的那一块，贴回原图，
<b>她的脸和其余像素与你认可过的首帧逐像素相同</b>。提交前预览包已按新首帧和新 prompt 重建（秒数、积分不变：65 s，预计 10,400，上限 11,200）。</p>
<div class="dec"><h3 style="margin:4px 0">需要你定的（4 项）</h3><ol>
<li><b>及膝靴 + MO15 衣架</b>：SG19 首帧 p042-w2、MO15 首帧 p046-w2（靴子改及膝；MO15 衣架堆在她这一头、靠隔板那段杆空出来）。推荐：用。</li>
<li><b>茶水间微波炉</b>：SG16 首帧 p037-c2 加上 S037A 那台微波炉，并在 SG16 里让它在“十二点三十四分停掉”那句熄灯；INS37 首帧左右镜像（左手、插座在左）。
推荐：用；镜像后微波炉按键面板在左边（S037A/SG16 里在右边），1.37 s 特写里算次要。</li>
<li><b>P047 重做</b>：隔板改到画面右边（和 s045、s046、s048 同一条轴线），纸条从隔板下滑到她左手指尖，纸上只有点和短划。推荐：用 rb-b。</li>
<li><b>SG19 落布改写</b>：布从腰后慢慢往下滑，唱完这一句之后才落到脚边，185.585 剪切点（片内约 0.92 s）布还在往下落。推荐：按此改。</li>
</ol><p class="d">其余是 prompt 字面修正（SG12、SG16、SG18、INS33、INS37、MO15），按你和场记给的写法改，一并在下面列出。</p></div>
<p><img src="all-240.jpg" alt="240 px"><span class="d">五张新图的 240 px 观看尺寸：p037-c2 · p037-ins37b · p042-w2 · p046-w2 · P047 rb-b</span></p>
""")

P.append(f"""<h2>1. 靴子：W1 是及膝长靴，SG19 / MO15 首帧是过膝靴</h2>
<p><b>问题</b>：W1 造型定义（gen/unit.py 第 97 行）是“黑色及膝长靴”，s045、s047、s048 也都是及膝靴；但 p042-w1（SG19）和 p046-w1（MO15）画面下沿露出的是过膝靴的靴筒。</p>
<img src="{img['boots42']}"><img src="{img['boots42z']}">
<p>SG19：{fsha('p042-w2')}<br><span class="d">做法：codex_plate.py --edit-base p042-w1（两抽 a/b，取 b），只把腿部一块（x780–1300, y800–941，内侧 24 px 羽化）贴回原图；块外像素与 p042-w1 逐像素相同（脚本核验），所以脸、耳挂、衣服不变。及膝靴的靴口在画面下边以外，画面里露出的是大腿。红色：只有耳挂小红灯（19 px）；无字。</span></p>
<p class="rec"><b>建议</b>：用 p042-w2 / p046-w2。SG19 prompt 同时写明“黑色及膝长靴”。</p>""")

P.append(f"""<h2>2. MO15 首帧：衣架已经挤满靠隔板那头，没地方“推到隔板那头”</h2>
<p><b>问题</b>：p046-w1 里衣架一直排到隔板，prompt 要她“一把把所有衣架推到隔板那头”，推不动。</p>
<img src="{img['mo15']}"><img src="{img['mo15z']}">
<p>{fsha('p046-w2')}<br><span class="d">做法：同一次 Codex 编辑里改靴子 + 衣架（两抽，取 b），贴回右侧挂衣杆一块（x1220–1672, y132–941）和腿部一块；块外逐像素相同。左手仍搭在衣架堆最右边，隔板上方副本的手和空白秒表不变（那一块没贴）。她的左耳在头的另一侧看不到；无红；衣服无吊牌无字。</span></p>
<p>prompt 同步（首帧状态 + 左耳一句；左耳是被头挡住，不是被头发挡住，所以按实际写）：</p>{pdiff('MO15')}
<p class="rec"><b>建议</b>：用 p046-w2。</p>""")

P.append(f"""<h2>3. s037 微波炉：S037A 里有，SG16 首帧里台面是空的</h2>
<p><b>问题</b>：s037a 静图 S037A 里微波炉在咖啡机和她之间的台面上；s037b/d 的 SG16 首帧 p037-c1 同一处什么也没有，两刀接不上。</p>
<img src="{img['mw']}"><img src="{img['mwz']}">
<p>{fsha('p037-c2')}<br><span class="d">做法：--edit-base p037-c1 --ref S037A/a（两抽，取 b），只贴回台面那一块（x330–925, y285–650）；她的姿势、闭着的嘴、脸、工程师都逐像素不变。微波炉在转（暖黄灯、白马克杯），门在左、按键面板在右（同 S037A），显示屏黑、按键无字、无红。</span></p>
<p class="warn">连带：s037b 微波炉在转 → INS37 拔插头 → s037d 必须是灭的。所以 SG16 prompt 让它在“十二点三十四分停掉”（Killed at twelve thirty-four）那句熄灯，和放碗同一句（也是你要的放碗时机）。风险：模型不熄灯，s037d 就接不上（Gate 时查；不行就后期压暗炉窗）。</p>
{pdiff('SG16')}
<p class="rec"><b>建议</b>：用 p037-c2 和上面的 SG16 prompt。</p>""")

P.append(f"""<h2>4. INS37：工程师右手拿着手机，按键的应该是另一只手</h2>
<p><b>问题</b>：S037A 里他右手拿手机贴右耳；INS37 首帧是一只右手从画面右边伸进来按键。</p>
<img src="{img['ins37']}">
<p>{fsha('p037-ins37b')}<br><span class="d">做法：INS37/b 左右镜像（PNG 无损，逐像素等于原图翻转；画面无脸无字）。镜像后是一只左手从画面左边伸进来，插座在左边墙上。</span></p>
<p class="warn">镜像露馅检查：① 微波炉按键面板到了左边，门把手在右（S037A 和新 p037-c2 里面板在右）——最明显的一处；② 墙上美式插座两孔宽窄左右互换，看不出；③ 马克杯把手换边，转盘在转，看不出；④ 牛仔袖口的扣子换边，看不出。①在 1.37 s 的特写里一般不会被注意，但严格说和 S037A 不一致。</p>
{pdiff('INS37')}
<p class="rec"><b>建议</b>：用镜像版。若要面板也在右边，只能重做一张“左手越过炉门去按右边面板”的新首帧（构图会被手臂挡住炉窗），不推荐。交接里的“右手”已改。</p>""")

P.append(f"""<h2>5. P047（s047 静图）越轴</h2>
<p><b>问题</b>：P047/a 隔板在画面左边，她朝左伸手；s045、s046、s048 隔板都在她右边（画面右侧）。直接镜像她会把耳挂红灯换到右耳，不行。</p>
<img src="{img['p047']}"><img src="{img['axis']}">
<p>推荐 rb-b：{fsha('P047 rb-b')}<br>2944 宽：{fsha('P047 rb-b-2944')}<br>
<span class="d">做法：codex_plate.py 新生成（参考 p048-w1 的试衣间与造型、P047/a 的纸条与姿势、开场脸两张），没有镜像：隔板在右，下沿离地一掌高，纸条从缝里滑出来碰到她左手指尖；她单膝跪、低头看缝，耳挂和小红灯在她左耳（画面右侧），看得见。
纸条上只有一行点和短划，没有字母数字（下图放大）。红色：只有耳挂灯，另两个小点是嘴唇和指甲的肤色像素。脸对照开场脸：同一个人（雀斑、银白眉、冰灰眼、下颌）。2944 版用 tools/upscale_lanczos.py。</span></p>
<img src="{img['p047z']}"><img src="{img['p047s']}">
<p>其余候选：rb-a（同一提示另一抽，脸更侧）、ra-a / ra-b（以 p048-w1 为底图改，和 s048 同机位同构图，接 s048 像跳切；ra-a 脸被头发挡住大半）。</p>
<img src="{img['p047alt']}">
<p class="d">s047 → s048 衔接：s047 她低头、左手按着纸条在隔板脚下；s048 她已经抬头对镜头念白，手在画外，纸条留给剪辑（s048 首帧不用改）。外套左臂：同 s048 首帧（外套从左肩滑下挂在左臂上），与已认可的 p048-w1 一致。</p>
<p class="rec"><b>建议</b>：s047 用 rb-b（2944 版）；预览包里 s047 静图已换成它。</p>""")

P.append(f"""<h2>6. SG19 落布时机（你定的“185.585 重音上…布正落下”）</h2>
<p><b>问题</b>：原 prompt 一开头就写“防尘布落到她脚边”，模型多半第一秒就落完；剪辑入点 185.585 在片内约 0.92 s，那时布已经不动了。</p>
{pdiff('SG19')}
<p class="d">首帧里布已经离肩、堆在腰后（P042/a），所以按首帧状态写“从腰后慢慢往下滑”，而不是“从肩上滑下”。</p>
<p class="rec"><b>建议</b>：按此改。</p>""")

P.append(f"""<h2>7. prompt 字面修正（按你和场记给的写法）</h2>
<p class="d">prompt 只能是中文（项目规则 + 测试 prompt_language_ok 会拒绝英文字母），所以英文词写成中文意思：No luck → “运气不好”，Killed at twelve thirty-four → “十二点三十四分停掉”，October → “十月”。</p>
<h3>SG12（s031）：纸币素色；收腰带绑第一个词；塞纸币 + 眼睛左瞟绑 No luck；去掉“最后”</h3>{pdiff('SG12')}
<h3>SG18（s041）：抓布边绑在最后一个词 October 刚开口；只露手</h3>{pdiff('SG18')}
<h3>INS33（s033b）：结尾接 P034</h3>{pdiff('INS33')}
<p class="rec"><b>建议</b>：全部按此。</p>""")

P.append("""<h2>文件与验证</h2><ul>
<li>候选与提示词：excerpt/flash/design/S31-48/CONT1124/（prompt.md、runs.md、comp.py、check/ 审看表、sha256.txt）。</li>
<li>改动的文字/JSON 都留了 *.before-continuity-2026-11-24 备份：s031-048-seedance.md、gen/unit.py、gen/test_unit_lanes.py、submit/build.py、submit/preview-inputs.json、submit/index.html、board/shots.json、director-coverage.json、11 个 approval 模板、交接文件。</li>
<li>board/shots.json：s037/s042/s046 与 SG16/INS37/SG19/MO15 改指新首帧，INS37 insert 文字改“左手、左边插座”；BOARD_SHA256 加历史注释；director-coverage.json 重建（53 单元）。</li>
<li>uv run pytest -q outputs/ai-city-takeover/ep01/v4/gen/test_unit_lanes.py → 112 passed。</li>
</ul>""")

(HERE / "index.html").write_text("\n".join(P) + "\n", encoding="utf-8")
print(HERE / "index.html", sha(HERE / "index.html"))
