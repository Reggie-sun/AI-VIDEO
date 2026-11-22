import { AbsoluteFill, Img, useCurrentFrame } from "remotion";
import { RadialGlow, SPRING, asset, mix, sp, type SceneProps } from "agentcut";

type Props = SceneProps & { covers: string[]; accent: string };

// Official ACE v1 sample covers at their native size, each with a live waveform: songs, not a page of text.
export default function MusicCards({ covers, accent = "#ff6a2b", width, height }: Props) {
  const f = useCurrentFrame();
  const size = 300;
  const gap = 40;
  const total = covers.length * size + (covers.length - 1) * gap;
  const x0 = (width - total) / 2;
  const y0 = height * 0.2;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg,#1a0d08,#060506)", overflow: "hidden" }}>
      <RadialGlow x={0.5} y={0.4} radius={0.7} color={accent} opacity={0.22} />
      {covers.map((c, i) => {
        const s = sp(f, 2 + i * 4, SPRING.pop);
        const active = Math.floor(f / 12) % covers.length === i;
        const bars = [];
        for (let k = 0; k < 18; k++) {
          const amp = active ? 0.35 + 0.65 * Math.abs(Math.sin((f + k * 5 + i * 11) * 0.35)) : 0.18 + 0.1 * Math.abs(Math.sin(k + i));
          bars.push(
            <div key={k} style={{ width: 9, height: 70 * amp, borderRadius: 5, background: active ? accent : "rgba(255,255,255,0.3)" }} />,
          );
        }
        return (
          <div key={c} style={{ position: "absolute", left: x0 + i * (size + gap), top: y0, width: size, opacity: s, transform: `translateY(${mix(60, 0, s)}px) scale(${active ? 1.06 : 1})` }}>
            <Img
              src={asset(c)}
              style={{ width: size, height: size, borderRadius: 22, boxShadow: active ? `0 0 50px ${accent}aa` : "0 18px 40px rgba(0,0,0,0.5)" }}
            />
            <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "center", height: 90, marginTop: 18 }}>{bars}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
}
