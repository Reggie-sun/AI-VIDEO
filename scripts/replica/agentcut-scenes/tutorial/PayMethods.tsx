import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW, RED } from "./lib/theme";
import { GiftCard } from "./lib/GiftCard";

type Props = SceneProps & { chipsFrom: number; crossFrom: number; cardFrom: number };

// 日区本地付款方式（需要日本本地账户）都没有 → 礼品卡最省事
export default function PayMethods({ chipsFrom, crossFrom, cardFrom, clip }: Props) {
  const f = useCurrentFrame();
  const chips = ["日本信用卡", "PayPay", "运营商代扣"];
  const x = sp(f, crossFrom, SPRING.smooth);
  const c = sp(f, cardFrom, SPRING.pop);
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 6)) / 6));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, opacity: 1 - out }}>
      <div style={{ position: "absolute", left: 130, top: 190, color: "#fff", fontSize: 54, fontWeight: 900, opacity: sp(f, 0, SPRING.smooth) }}>日区本地付款方式</div>
      <div style={{ position: "absolute", left: 130, top: 300, display: "flex", flexDirection: "column", gap: 34 }}>
        {chips.map((t, i) => {
          const s = sp(f, chipsFrom + i * 8, SPRING.pop);
          return (
            <div key={i} style={{ position: "relative", width: 560, height: 120, borderRadius: 24, background: "rgba(255,255,255,0.1)",
                                  border: "2px solid rgba(255,255,255,0.2)", display: "flex", alignItems: "center", paddingLeft: 40,
                                  color: "#fff", fontSize: 50, fontWeight: 700, opacity: s * mix(1, 0.4, x), transform: `translateX(${mix(-60, 0, s)}px)` }}>
              {t}
              <div style={{ position: "absolute", right: 40, color: RED, fontSize: 64, fontWeight: 900, opacity: x, transform: `scale(${mix(2, 1, x)})` }}>✕</div>
            </div>
          );
        })}
        <div style={{ color: "#cfd0d6", fontSize: 34, opacity: x, marginTop: 4 }}>都需要日本本地的卡或账户</div>
      </div>
      <div style={{ position: "absolute", left: 1030, top: 260, opacity: c, transform: `scale(${mix(0.7, 1, c)}) rotate(${mix(8, -4, c)}deg)` }}>
        <GiftCard w={680} />
      </div>
      <div style={{ position: "absolute", left: 1080, top: 730, color: YELLOW, fontSize: 80, fontWeight: 900, opacity: c,
                    textShadow: "0 6px 24px rgba(0,0,0,0.6)" }}>✓ 礼品卡最省事</div>
    </AbsoluteFill>
  );
}
