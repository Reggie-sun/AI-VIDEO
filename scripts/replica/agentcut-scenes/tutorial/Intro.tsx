import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW } from "./lib/theme";
import { GiftCard } from "./lib/GiftCard";

type Props = SceneProps & { questionFrom: number };

// L1 title + L2 "什么是礼品卡？"
export default function Intro({ questionFrom, clip }: Props) {
  const f = useCurrentFrame();
  const a = sp(f, 0, SPRING.smooth), b = sp(f, 8, SPRING.pop), q = sp(f, questionFrom, SPRING.pop);
  const fl = Math.sin(f / 22) * 10;
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 6)) / 6));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, opacity: 1 - out }}>
      <div style={{ position: "absolute", left: 140, top: 270, color: "#fff" }}>
        <div style={{ fontSize: 120, fontWeight: 900, lineHeight: 1.1, transform: `translateX(${mix(-60, 0, a)}px)`, opacity: a,
                      textShadow: "0 8px 30px rgba(0,0,0,0.6)" }}>日区<span style={{ color: YELLOW }}>苹果礼品卡</span></div>
        <div style={{ fontSize: 64, fontWeight: 700, marginTop: 26, color: "#e9e9ee", transform: `translateX(${mix(-60, 0, b)}px)`, opacity: b }}>
          购买 · 兑换 · 使用 全流程
        </div>
        <div style={{ marginTop: 60, fontSize: 72, fontWeight: 900, color: YELLOW, transform: `scale(${mix(0.6, 1, q)})`, transformOrigin: "left center",
                      opacity: f >= questionFrom ? q : 0 }}>什么是礼品卡？</div>
      </div>
      <div style={{ position: "absolute", left: 1150, top: 250, transform: `translateY(${mix(120, fl, b)}px) rotate(${mix(14, -6, b)}deg)`, opacity: b }}>
        <GiftCard w={600} />
      </div>
    </AbsoluteFill>
  );
}
