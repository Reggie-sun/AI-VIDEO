"""Gift-card tutorial replica (2026-11-20): layers.json for the full cut and two split parts.

Usage: python examples/reference-replica/giftcard-jp/build_layers.py [parts] --projects-root <path>

Writes <projects-root>/giftcard-jp-replica/layers.json (and giftcard-jp-part1/-part2 with `parts`).
Shot lists are written on the v1 timeline (timeline-v1.json) and mapped onto timeline.json through
layers_kit.make_mapper; the g02 channel block was rewritten in round 2 and is laid out on the current timeline.
Copy this folder for a new tutorial replica and replace the data and shot lists.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]
from scripts.replica import layers_kit as K  # noqa: E402
from scripts.replica._local import cli, project_root  # noqa: E402

SCENES = REPO / "scripts" / "replica" / "agentcut-scenes" / "tutorial"
VOICE_LABEL = "刘飞口播"
FPS = K.FPS
END0 = 4625
SRC = {"A": ("assets/footage/A_red2.mp4", 448, 960, 158.36), "B": ("assets/footage/B_red2.mp4", 592, 1280, 87.0)}
MUSIC = {"name": "Soft Circuit Pulse", "src": "assets/music/soft-circuit-pulse.mp3", "trimStart": 0, "volume": 0.25,
         "fadeIn": 15, "fadeOut": 45, "role": "music", "note": "原片停顿处 RMS −28~−36 dB，全程有轻底乐；listen_rank z 2.88"}

TLD = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
TL0 = json.loads((HERE / "timeline-v1.json").read_text(encoding="utf-8"))
T = K.Timeline(TLD)
G, line, at = T.G, T.line, T.at
M, END = K.make_mapper(TL0, TLD, END0, rewritten={"g02": (792, 1155, G["g02"]["from"], G["g03"]["from"] - 20)})

# ---------- phone shots (v1 frames) ----------
PH0 = [
    # g03 购买：打开官网 → 选面额
    (1155, 1312, "A", 0.0, 0.85, []),
    (1312, 1420, "A", 4.45, 0.9, [(18, 150, 92, 232, 5.0, 7.7)]),
    (1420, 1605, "A", 7.69, 0.27, [(28, 470, 218, 622, 8.14, 9.36)]),
    # g04 注册登录
    (1605, 1709, "A", 9.36, 0.94, [(39, 580, 199, 618, 9.36, 9.8), (160, 325, 290, 360, 10.2, 11.6)]),
    (1709, 1765, "A", 12.6, 9.86, []),
    (1765, 1806, "A", 43.8, 4.2, []),
    (1806, 1909, "A", 50.3, 1.37, [(39, 414, 199, 450, 52.6, 53.8)]),
    # g05 确认订单 / 确认并支付 / 反诈
    (1909, 1980, "A", 55.0, 1.27, [(28, 200, 431, 448, 55.4, 58.0)]),
    (1980, 2051, "A", 58.0, 0.85, [(233, 754, 428, 802, 58.1, 60.0)]),
    (2051, 2207, "A", 60.0, 0.42, [(31, 633, 419, 672, 60.9, 62.2)]),
    # g06 收钱吧 → 微信
    (2207, 2293, "A", 62.2, 0.98, [(95, 570, 355, 612, 62.7, 64.2), (233, 739, 420, 781, 64.2, 65.0)]),
    (2293, 2336, "A", 67.2, 1.95, [(233, 782, 429, 831, 67.2, 68.6), (352, 470, 410, 498, 68.7, 70.0)]),
    (2336, 2371, "A", 77.0, 2.57, []),
    (2371, 2406, "A", 81.0, 3.0, []),
    (2406, 2442, "A", 92.2, 1.8, []),
    # g07 我的订单 → 查看卡密 → 提醒 → 复制
    (2442, 2523, "A", 104.5, 1.0, []),
    (2523, 2641, "A", 114.4, 1.58, [(244, 328, 315, 361, 114.8, 116.3), (39, 650, 151, 678, 116.8, 119.3)]),
    (2641, 2791, "A", 120.6, 0.76, [(40, 126, 432, 184, 120.8, 124.4)]),
    (2791, 2870, "A", 124.4, 1.2, [(350, 545, 405, 572, 124.6, 127.6)]),
    # g08 App Store 兑换
    (3020, 3073, "A", 128.4, 0.9, [(34, 535, 106, 610, 128.6, 130.0)]),
    (3073, 3119, "B", 59.6, 1.1, [(500, 60, 580, 140, 59.9, 61.3)]),
    (3119, 3189, "A", 131.0, 1.03, [(25, 610, 345, 655, 131.3, 133.4)]),
    (3189, 3256, "A", 135.6, 1.43, [(45, 851, 403, 907, 136.4, 138.8)]),
    (3256, 3329, "A", 139.0, 1.48, [(35, 255, 100, 295, 141.2, 142.2)]),
    (3329, 3357, "A", 143.6, 1.67, [(45, 759, 403, 826, 143.7, 145.0)]),
    (3357, 3481, "A", 146.7, 0.3, [(43, 190, 314, 263, 147.0, 148.0)]),
    # g09 ChatGPT Go
    (3481, 3536, "B", 0.0, 1.0, [(44, 866, 141, 947, 0.6, 1.9)]),
    (3536, 3600, "B", 1.9, 1.12, []),
    (3600, 3672, "B", 4.3, 1.06, []),
    (3672, 3730, "B", 7.45, 0.9, [(440, 400, 528, 456, 7.6, 8.75)]),
    (3730, 3812, "B", 9.2, 1.17, [(59, 474, 296, 518, 9.3, 10.8), (47, 1069, 542, 1147, 10.8, 12.5)]),
    (3812, 3842, "B", 14.6, 2.0, [(47, 1069, 542, 1147, 14.6, 16.6)]),
    (3842, 3908, "B", 19.6, 1.82, [(45, 860, 330, 915, 19.7, 21.5), (481, 454, 570, 518, 21.5, 23.6)]),
    (3908, 3969, "B", 27.8, 1.08, [(74, 570, 518, 755, 27.9, 30.0)]),
    # g10 购买记录
    (3969, 4039, "B", 66.5, 1.41, [(20, 615, 575, 680, 67.0, 68.75)]),
    (4039, 4142, "B", 72.0, 1.17, [(39, 467, 566, 678, 72.2, 76.1)]),
    (4142, 4191, "B", 82.2, 1.47, [(53, 237, 559, 566, 82.3, 84.6)]),
    (4191, 4261, "B", 12.8, 0.49, [(47, 1069, 542, 1147, 12.85, 14.0)]),
    (4261, 4330, "B", 59.8, 0.6, [(422, 740, 526, 784, 59.9, 61.2)]),
    (4330, 4408, "B", 45.5, 1.35, [(37, 207, 562, 252, 45.6, 48.9)]),
]
PH = K.remap_phone(PH0, M)

# g02 block on the current timeline: channel card, then 微信/支付宝, 拿到兑换码, price list
g2 = G["g02"]["lines"]
B2 = G["g03"]["from"] - 20
S2 = at("g02", 4, 12 / 23)  # “付完款” starts
L6 = g2[5]["from"]  # “它的价格也比某宝的要便宜”
PH += [
    (g2[4]["from"], S2, "A", 66.3, (68.3 - 66.3) * FPS / (S2 - g2[4]["from"]), [(233, 782, 429, 831, 66.4, 68.3)]),
    (S2, L6, "A", 119.0, 0.8, []),
    (L6, B2, "A", 7.0, 0.6 * FPS / (B2 - L6), [(30, 505, 200, 545, 7.0, 7.7)]),  # 价格列表：1000円（约¥46.53）
]
PH.sort(key=lambda x: x[0])

# ---------- full-frame graphics ----------
GR = [
    (0, M(183), "Intro", {"questionFrom": line("g01", 1)["from"]}),
    (M(183), M(380), "CodeCard", {"arrowFrom": 92}),
    (M(380), M(553), "Uses", "tiles"),
    (M(553), G["g02"]["from"] - 4, "PayMethods", {"chipsFrom": 22, "crossFrom": 96, "cardFrom": 118}),
    (G["g02"]["from"] - 4, g2[4]["from"], "Channel", {"waysFrom": g2[1]["from"] - G["g02"]["from"] + 4,
                                                       "pickFrom": g2[2]["from"] - G["g02"]["from"] + 4,
                                                       "tagsFrom": g2[3]["from"] - G["g02"]["from"] + 4}),
    (M(2870), M(3020), "CodeCard", {"arrowFrom": 60, "heading": "拿到", "title": "兑换码", "target": "App Store 日本", "tail": "兑换成账户余额"}),
    (M(4408), END, "Recap", {"byeFrom": line("g11", 1)["from"] - M(4408)}),
]


def resolve(a, name, props):
    if props != "tiles":
        return props
    return {"tiles": [
        {"label": "购买软件", "icon": "app", "from": at("g01", 3, 14 / 31) - a},
        {"label": "充值游戏", "icon": "game", "from": at("g01", 3, 18 / 31) - a},
        {"label": "订阅会员", "icon": "vip", "from": at("g01", 3, 22 / 31) - a}]}


# ---------- side panels (v1 frames; mapped) ----------
SIDE0 = [
    (1155, 2870, "第一步 · 日卡通买卡", [
        (1155, "打开日卡通官网|ri-card.cn"), (1312, "苹果日本礼品卡|选择面额"), (1420, "按需求|选择面额"),
        (1470, "1000日元|≈ ¥46.53"), (1605, "点击立即购买|注册登录"), (1709, "手机号 + 密码|+ 短信验证码"),
        (1806, "登录后|再点立即购买"), (1909, "确认|订单信息"), (1980, "点击|确认并支付"),
        (2051, "反诈提醒|点击我已确认"), (2207, "支持|微信/支付宝/云闪付"), (2293, "选择|微信"),
        (2336, "输入密码|付款成功"), (2442, "回到|我的订单"), (2523, "已发货 · 查看卡密|拿到兑换码"),
        (2641, "兑换时要录屏|20分钟内联系客服"), (2791, "复制|兑换码")],
     [(1312, "选择面额"), (1605, "注册登录"), (1909, "确认订单"), (2207, "微信付款"), (2442, "复制卡密")]),
    (3020, 3481, "第二步 · App Store 兑换", [
        (3020, "打开|App Store"), (3073, "点击|右上角头像"), (3119, "使用礼品卡|或代码"), (3189, "手动输入|兑换码"),
        (3256, "粘贴|兑换码"), (3329, "点击|兑换"), (3357, "成功添加|1000日元")],
     [(3020, "打开 App Store"), (3073, "点击头像"), (3119, "使用礼品卡或代码"), (3189, "手动输入兑换码"), (3256, "粘贴并兑换"), (3357, "到账")]),
    (3481, 4408, "第三步 · 余额订阅", [
        (3481, "用余额|付款"), (3536, "以 ChatGPT Go|为例"), (3600, "打开 ChatGPT|进入设置"), (3691, "点击|升级"),
        (3730, "选择 Go|每月1400日元"), (3812, "点击|升级"), (3842, "按两下侧边按钮|付款成功"),
        (3969, "App Store|购买记录"), (4039, "ChatGPT Go|扣款1400日元"), (4142, "付款|没有问题"),
        (4191, "Plus 升级 · 买游戏|同样适用"), (4330, "流程|一模一样")],
     [(3481, "打开 ChatGPT"), (3691, "点击升级"), (3730, "选择 Go"), (3842, "侧边按钮确认"), (3969, "查看购买记录")]),
]
SIDE = [(g2[4]["from"], B2, "日卡通", [(g2[4]["from"], "微信 · 支付宝|直接付款"), (S2, "付完款|就能拿到兑换码"), (L6, "价格|也比某宝便宜")], [])]
SIDE += [(M(a), M(b), sec, [(M(f), t) for f, t in caps], [(M(f), t) for f, t in steps]) for a, b, sec, caps, steps in SIDE0]

CHAPTERS = [("介绍", 0), ("日卡通买卡", M(1155)), ("App Store 兑换", M(2870)), ("余额消费", M(3481)), ("回顾", M(4408))]

SUB_EXTRA = {"首先，打开日卡通官网。": "首先，打开日卡通官网 ri-card.cn",
             "点击使用礼品卡或代码。": "点击使用礼品卡或代码（ギフトカードまたはコードを使う）"}


def sub_text(t):
    return SUB_EXTRA.get(t, t.rstrip("。，"))


def build_full(root):
    K.tile_check(PH, GR, END)
    video, overlay = K.phone_clips(PH, SRC, 0, END)
    subs, voice = K.voice_sub_clips(G, [g["id"] for g in TLD], sub_text)
    K.assemble(root / "giftcard-jp-replica", END, subs=subs, voice=voice, chapters=CHAPTERS, overlay=overlay,
               side=K.side_clips(SIDE, 0, END), graphics=K.graphic_clips(GR, 0, END, resolve), video=video,
               music=MUSIC, voice_label=VOICE_LABEL)


# ---------- split parts ----------
BYE_TRIM = line("g11", 1)["from"] - G["g11"]["from"] - 2   # frames into g11.wav where “谢谢大家” starts
BYE_DUR = G["g11"]["dur"] - BYE_TRIM
OUTRO = BYE_DUR + 24


def outro(at_frame, recap):
    gr = [{"id": "gr-outro", "name": "Recap", "from": at_frame, "duration": OUTRO, "scene": "Recap", "props": {**recap, "byeFrom": 0}}]
    sub = [{"id": "subs-bye", "name": "字幕 结尾", "from": at_frame, "duration": OUTRO, "scene": "Subs",
            "props": {"lines": [{"text": "谢谢大家，我们下期再见", "from": 0, "to": BYE_DUR}], "fontSize": 44}}]
    vo = [{"id": "vo-bye", "name": "口播 结尾（截自 g11）", "from": at_frame, "duration": BYE_DUR, "src": G["g11"]["src"],
           "trimStart": BYE_TRIM, "volume": 1, "role": "voice"}]
    return gr, sub, vo


def build_part(root, slug, lo, hi, gids, chapters, recap, rename=None):
    K.range_check(PH, GR, lo, hi)
    video, overlay = K.phone_clips(PH, SRC, lo, hi)
    subs, voice = K.voice_sub_clips(G, gids, sub_text)
    side, graphics = K.side_clips(SIDE, lo, hi, rename), K.graphic_clips(GR, lo, hi, resolve)
    for cl in (video, overlay, subs, voice, side, graphics):
        K.shift(cl, -lo)
    end = hi - lo + OUTRO
    gr, sub, vo = outro(hi - lo, recap)
    K.assemble(root / slug, end, subs=subs + sub, voice=voice, chapters=chapters, overlay=overlay, side=side,
               graphics=graphics + gr, video=video, music=MUSIC, extra_voice=vo, voice_label=VOICE_LABEL)


def build_parts(root):
    K.ensure_project(root, "giftcard-jp-part1", "日区苹果礼品卡 · 上：购买与兑换", "giftcard-jp-replica", SCENES)
    K.ensure_project(root, "giftcard-jp-part2", "日区苹果礼品卡 · 下：余额订阅 ChatGPT Go", "giftcard-jp-replica", SCENES)
    x1 = M(3481)  # end of App Store 兑换 block
    x2 = M(4408)  # end of 余额消费 block
    build_part(root, "giftcard-jp-part1", 0, x1, [f"g0{i}" for i in range(1, 9)],
               [("介绍", 0), ("日卡通买卡", M(1155)), ("App Store 兑换", M(2870)), ("回顾", x1)],
               {"title": "日区礼品卡 购买与兑换", "steps": [
                   {"n": "1", "t": "日卡通买卡", "s": "微信付款 · 拿到卡密"},
                   {"n": "2", "t": "App Store 兑换", "s": "到账账户余额"}]})
    build_part(root, "giftcard-jp-part2", x1, x2, ["g09", "g10"],
               [("订阅 ChatGPT Go", 0), ("查看购买记录", G["g10"]["from"] - x1), ("回顾", x2 - x1)],
               {"title": "用礼品卡余额 订阅 ChatGPT Go", "steps": [
                   {"n": "1", "t": "选择 Go", "s": "每月1400日元"},
                   {"n": "2", "t": "侧边按钮确认", "s": "余额直接付款"},
                   {"n": "3", "t": "查看购买记录", "s": "确认已扣款"}]},
               rename={"第三步 · 余额订阅": "礼品卡余额 · 订阅 ChatGPT Go"})


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", choices=("parts",))
    parser.add_argument("--projects-root", type=Path)
    args = parser.parse_args(argv)
    root = project_root(args.projects_root)
    build_full(root)
    if args.mode == "parts":
        build_parts(root)


if __name__ == "__main__":
    cli(main)
