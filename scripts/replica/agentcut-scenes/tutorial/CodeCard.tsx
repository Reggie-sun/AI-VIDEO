import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW } from "./lib/theme";
import { GiftCard } from "./lib/GiftCard";

type Props = SceneProps & { arrowFrom: number; title?: string; target?: string; heading?: string; tail?: string };

// "一串兑换码" → App Store 日本 → 等值日元余额
export default function CodeCard({ arrowFrom, title = "一串兑换码", target = "App Store 日本", heading = "礼品卡 = ", tail = "等值账户余额", clip }: Props) {
  const f = useCurrentFrame();
  const a = sp(f, 0, SPRING.smooth);
  const full = "XXXX XXXX XXXX XXXX";
  const n = Math.max(0, Math.min(full.length, Math.floor((f - 10) / 2)));
  const code = full.slice(0, n).padEnd(full.length, "·");
  const ar = sp(f, arrowFrom, SPRING.smooth);
  const bal = sp(f, arrowFrom + 14, SPRING.pop);
  const yen = Math.round(1000 * Math.min(1, Math.max(0, (f - arrowFrom - 14) / 24)));
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 6)) / 6));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, opacity: 1 - out }}>
      <div style={{ position: "absolute", left: 130, top: 160, color: "#fff", fontSize: 64, fontWeight: 900, opacity: a }}>
        {heading}<span style={{ color: YELLOW }}>{title}</span>
      </div>
      <div style={{ position: "absolute", left: 130, top: 330, transform: `translateX(${mix(-80, 0, a)}px)`, opacity: a }}>
        <GiftCard w={620} code={code} />
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <path d={`M 800 525 L ${800 + 240 * ar} 525`} stroke={YELLOW} strokeWidth={10} strokeLinecap="round" />
        {ar > 0.9 && <path d="M 1030 495 L 1068 525 L 1030 555" fill="none" stroke={YELLOW} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      <div style={{ position: "absolute", left: 1120, top: 330, width: 640, height: 390, borderRadius: 36, background: "rgba(255,255,255,0.08)",
                    border: "2px solid rgba(255,255,255,0.18)", transform: `scale(${mix(0.85, 1, bal)})`, opacity: bal,
                    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#fff" }}>
        <div style={{ width: 120, height: 120, borderRadius: 28, background: "linear-gradient(160deg,#1fb6ff,#0a66ff)", display: "flex",
                      alignItems: "center", justifyContent: "center", fontSize: 76, fontWeight: 900 }}>A</div>
        <div style={{ fontSize: 40, fontWeight: 700, marginTop: 20 }}>{target}</div>
        <div style={{ fontSize: 86, fontWeight: 900, color: YELLOW, marginTop: 6 }}>¥{yen.toLocaleString("en-US")}</div>
        <div style={{ fontSize: 30, color: "#cfd0d6" }}>{tail}</div>
      </div>
    </AbsoluteFill>
  );
}
