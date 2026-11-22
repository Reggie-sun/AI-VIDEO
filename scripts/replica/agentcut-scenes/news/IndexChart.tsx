import { AbsoluteFill, useCurrentFrame } from "remotion";
import { RadialGlow, SPRING, mix, sp, type SceneProps } from "agentcut";

type Bar = { name: string; org: string; value: number; color: string };
type Props = SceneProps & { title: string; source: string; bars: Bar[]; focus: number[]; grow: boolean };

// Whole leaderboard at a glance: bars rise, the focused models glow. No zooming into numbers.
export default function IndexChart({ title, source, bars, focus, grow, width, height }: Props) {
  const f = useCurrentFrame();
  const max = Math.max(...bars.map((b) => b.value));
  const left = 140;
  const right = width - 140;
  const base = height - 310;
  const top = 330;
  const slot = (right - left) / bars.length;
  const bw = slot * 0.62;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(170deg,#141018,#08080b)", fontFamily: "Noto Sans SC" }}>
      <RadialGlow x={0.3} y={0.45} radius={0.6} color="#d97757" opacity={0.14} />
      <div style={{ position: "absolute", left, top: 80, color: "#fff", fontSize: 64, fontWeight: 900, opacity: sp(f, 0, SPRING.snappy) }}>
        {title}
      </div>
      <div style={{ position: "absolute", left, top: 168, color: "rgba(255,255,255,0.55)", fontSize: 32, fontWeight: 500 }}>{source}</div>
      {bars.map((b, i) => {
        const g = grow ? sp(f, 4 + i * 3, SPRING.land) : 1;
        const h = ((base - top) * b.value) / max;
        const on = focus.includes(i);
        const x = left + i * slot + (slot - bw) / 2;
        const glow = on ? sp(f, grow ? 22 : 2, SPRING.pop) : 0;
        return (
          <div key={b.name}>
            <div
              style={{
                position: "absolute",
                left: x,
                top: base - h * g,
                width: bw,
                height: h * g,
                borderRadius: "14px 14px 4px 4px",
                background: b.color,
                opacity: focus.length && !on ? 0.38 : 1,
                boxShadow: on ? `0 0 ${mix(0, 46, glow)}px ${b.color}` : "none",
                transform: `scale(${on ? mix(1, 1.04, glow) : 1})`,
                transformOrigin: "bottom center",
              }}
            />
            <div
              style={{
                position: "absolute",
                left: x - 20,
                width: bw + 40,
                top: base - h * g - 74,
                textAlign: "center",
                color: "#fff",
                fontSize: on ? 58 : 44,
                fontWeight: 900,
                opacity: g * (focus.length && !on ? 0.5 : 1),
              }}
            >
              {b.value}
            </div>
            <div
              style={{
                position: "absolute",
                left: x - 30,
                width: bw + 60,
                top: base + 18,
                textAlign: "center",
                color: on ? "#fff" : "rgba(255,255,255,0.55)",
                fontSize: on ? 36 : 30,
                fontWeight: on ? 900 : 700,
                lineHeight: 1.15,
              }}
            >
              {b.name}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
}
