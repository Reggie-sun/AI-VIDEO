import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW } from "./lib/theme";

type Props = SceneProps & { waysFrom: number; pickFrom: number; tagsFrom: number };

// 购买方式有很多种 → 这里用日卡通 → 专卖日本礼品卡
export default function Channel({ waysFrom, pickFrom, tagsFrom, clip }: Props) {
  const f = useCurrentFrame();
  const a = sp(f, 0, SPRING.pop), b = sp(f, 10, SPRING.smooth);
  const w = sp(f, waysFrom, SPRING.smooth), p = sp(f, pickFrom, SPRING.pop);
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 6)) / 6));
  const ways = ["苹果官网", "购物平台", "礼品卡商城"];
  const tags = ["苹果 Apple", "Google Play", "任天堂 Switch", "Steam"];
  return (
    <AbsoluteFill style={{ fontFamily: FONT, alignItems: "center", justifyContent: "center", opacity: 1 - out }}>
      <div style={{ display: "flex", alignItems: "center", gap: 20, height: 70, marginBottom: 20, opacity: f >= waysFrom ? w : 0 }}>
        <div style={{ color: "#cfd0d6", fontSize: 38, fontWeight: 700 }}>购买方式很多：</div>
        {ways.map((t, i) => (
          <div key={i} style={{ padding: "8px 24px", borderRadius: 14, background: "rgba(255,255,255,0.1)", color: "#e8e9ee", fontSize: 34, fontWeight: 700,
                                opacity: mix(1, 0.45, p), transform: `translateY(${mix(20, 0, sp(f, waysFrom + i * 5, SPRING.pop))}px)` }}>{t}</div>
        ))}
      </div>
      <div style={{ color: YELLOW, fontSize: 44, fontWeight: 900, opacity: f >= pickFrom ? p : 0, height: 60 }}>这里用的是</div>
      <div style={{ fontSize: 190, fontWeight: 900, letterSpacing: 10, transform: `scale(${mix(0.7, 1, a) * mix(1, 1.06, Math.sin(Math.min(1, Math.max(0, (f - pickFrom) / 12)) * Math.PI))})`, opacity: a,
                    background: "linear-gradient(90deg,#ff4d4d,#ffb03b)", WebkitBackgroundClip: "text", color: "transparent" }}>日卡通</div>
      <div style={{ marginTop: 10, padding: "14px 40px", borderRadius: 50, background: "rgba(255,255,255,0.12)", color: "#fff",
                    fontSize: 48, fontWeight: 700, letterSpacing: 2, opacity: b, transform: `translateY(${mix(30, 0, b)}px)` }}>ri-card.cn</div>
      <div style={{ display: "flex", gap: 24, marginTop: 44, height: 70, opacity: f >= tagsFrom ? 1 : 0 }}>
        {tags.map((t, i) => (
          <div key={i} style={{ padding: "12px 28px", borderRadius: 16, border: `2px solid ${YELLOW}`, color: YELLOW, fontSize: 34, fontWeight: 700,
                                opacity: sp(f, tagsFrom + i * 5, SPRING.pop), transform: `translateY(${mix(30, 0, sp(f, tagsFrom + i * 5, SPRING.pop))}px)` }}>{t}</div>
        ))}
      </div>
      <div style={{ color: "#cfd0d6", fontSize: 34, marginTop: 18, opacity: f >= tagsFrom ? sp(f, tagsFrom + 20, SPRING.smooth) : 0 }}>专卖日本礼品卡的线上商城</div>
    </AbsoluteFill>
  );
}
