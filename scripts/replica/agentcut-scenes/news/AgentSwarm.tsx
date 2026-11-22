import { AbsoluteFill, useCurrentFrame } from "remotion";
import { RadialGlow, SPRING, mix, sp, type SceneProps } from "agentcut";

type Props = SceneProps & { count: number; label: string; sub: string; accent: string };

// 1,000 agents as a full-bleed field of dots that light up in waves from the centre.
export default function AgentSwarm({ count = 1000, label, sub, accent = "#ff7a45", width, height }: Props) {
  const f = useCurrentFrame();
  const cols = 50;
  const rows = Math.ceil(count / cols);
  const gx = width / (cols + 1);
  const gy = height / (rows + 1);
  const cx = width / 2;
  const cy = height / 2;
  const maxD = Math.hypot(cx, cy);
  const dots = [];
  for (let i = 0; i < count; i++) {
    const c = i % cols;
    const r = Math.floor(i / cols);
    const x = (c + 1) * gx;
    const y = (r + 1) * gy;
    const d = Math.hypot(x - cx, y - cy) / maxD;
    const on = Math.min(1, Math.max(0, (f - 4 - d * 46) / 10));
    const pulse = 0.65 + 0.35 * Math.sin((f + i * 7) * 0.22);
    dots.push(
      <div
        key={i}
        style={{
          position: "absolute",
          left: x - 7,
          top: y - 7,
          width: 14,
          height: 14,
          borderRadius: 7,
          background: on > 0.5 ? accent : "rgba(255,255,255,0.16)",
          opacity: mix(0.4, pulse, on),
          transform: `scale(${mix(0.6, 1, on)})`,
        }}
      />,
    );
  }
  const s = sp(f, 18, SPRING.pop);
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg,#120d0b,#07070a)" }}>
      <RadialGlow x={0.5} y={0.48} radius={0.55} color={accent} opacity={0.22} />
      {dots}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            padding: "26px 56px",
            borderRadius: 26,
            background: "rgba(10,8,8,0.82)",
            border: `3px solid ${accent}`,
            textAlign: "center",
            opacity: s,
            transform: `translateY(${mix(-90, -60, s)}px) scale(${mix(0.9, 1, s)})`,
            fontFamily: "Noto Sans SC",
          }}
        >
          <div style={{ fontSize: 118, fontWeight: 900, color: "#fff", letterSpacing: 2 }}>{label}</div>
          <div style={{ fontSize: 38, fontWeight: 700, color: accent, marginTop: 4 }}>{sub}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}
