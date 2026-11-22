import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW } from "./lib/theme";

type Step = { n: string; t: string; s: string };
type Props = SceneProps & { byeFrom: number; title?: string; steps?: Step[] };

// 全流程回顾：买卡 → 兑换 → 消费
export default function Recap({ byeFrom, title, steps: given, clip }: Props) {
  const f = useCurrentFrame();
  const steps: Step[] = given ?? [
    { n: "1", t: "日卡通买卡", s: "微信付款 · 拿到卡密" },
    { n: "2", t: "App Store 兑换", s: "使用礼品卡或代码" },
    { n: "3", t: "余额消费", s: "订阅 ChatGPT Go" },
  ];
  const bye = sp(f, byeFrom, SPRING.pop);
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 10)) / 10));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, opacity: 1 - out }}>
      <div style={{ position: "absolute", top: 150, width: "100%", textAlign: "center", color: "#fff", fontSize: 66, fontWeight: 900, opacity: sp(f, 0, SPRING.smooth) }}>
        {title ? title : <>日区礼品卡 <span style={{ color: YELLOW }}>全流程</span></>}
      </div>
      <div style={{ position: "absolute", top: 330, width: "100%", display: "flex", justifyContent: "center", alignItems: "center", gap: 30 }}>
        {steps.map((s, i) => {
          const a = sp(f, 10 + i * 16, SPRING.pop);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 30 }}>
              <div style={{ width: 440, height: 300, borderRadius: 36, background: "rgba(255,255,255,0.09)", border: "2px solid rgba(255,255,255,0.2)",
                            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16,
                            transform: `translateY(${mix(60, 0, a)}px)`, opacity: a }}>
                <div style={{ width: 80, height: 80, borderRadius: 40, background: "#ff3b30", color: "#fff", fontSize: 46, fontWeight: 900,
                              display: "flex", alignItems: "center", justifyContent: "center" }}>{s.n}</div>
                <div style={{ color: "#fff", fontSize: 52, fontWeight: 900 }}>{s.t}</div>
                <div style={{ color: "#cfd0d6", fontSize: 32 }}>{s.s}</div>
              </div>
              {i < steps.length - 1 && <div style={{ color: YELLOW, fontSize: 70, fontWeight: 900, opacity: a }}>→</div>}
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", top: 730, width: "100%", textAlign: "center", color: YELLOW, fontSize: 72, fontWeight: 900,
                    opacity: f >= byeFrom ? bye : 0, transform: `scale(${mix(0.7, 1, bye)})` }}>谢谢观看</div>
    </AbsoluteFill>
  );
}
