import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW, RED } from "./lib/theme";

type Item = { text: string; from: number };
type Props = SceneProps & { section: string; captions: Item[]; steps: Item[] };

// Left: section name + the current action in big type. Right: the section's step list.
export default function Steps({ section, captions, steps, clip }: Props) {
  const f = useCurrentFrame();
  const inA = sp(f, 0, SPRING.smooth);
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 8)) / 8));
  let ci = -1;
  captions.forEach((c, i) => { if (f >= c.from) ci = i; });
  let si = -1;
  steps.forEach((s, i) => { if (f >= s.from) si = i; });
  const cap = ci >= 0 ? captions[ci] : null;
  const capS = cap ? sp(f, cap.from, SPRING.pop) : 0;
  return (
    <AbsoluteFill style={{ opacity: inA * (1 - out), fontFamily: FONT }}>
      <div style={{ position: "absolute", left: 90, top: 300, width: 560 }}>
        <div style={{ display: "inline-block", padding: "8px 22px", borderRadius: 40, background: "rgba(255,255,255,0.1)",
                      color: "#e8e9ee", fontSize: 30, fontWeight: 700, letterSpacing: 2, transform: `translateX(${mix(-40, 0, inA)}px)` }}>
          {section}
        </div>
        {cap && (
          <div key={ci} style={{ marginTop: 34, color: "#fff", fontSize: 64, fontWeight: 900, lineHeight: 1.22,
                                 textShadow: "0 6px 24px rgba(0,0,0,0.6)", transform: `translateY(${mix(26, 0, capS)}px)`, opacity: capS }}>
            {cap.text.split("|").map((part, i) => (
              <div key={i} style={{ color: i === 1 ? YELLOW : "#fff", whiteSpace: "nowrap",
                                    fontSize: Math.min(64, Math.floor(560 / Math.max(1, [...part].reduce((u, ch) => u + (/[\u3000-\u9fff\uff00-\uffef]/.test(ch) ? 1 : 0.56), 0)))) }}>{part}</div>
            ))}
          </div>
        )}
      </div>
      <div style={{ position: "absolute", left: 1290, top: 250, width: 520 }}>
        {steps.map((s, i) => {
          const done = i < si, cur = i === si;
          const a = sp(f, 4 + i * 4, SPRING.smooth);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 22, marginBottom: 26, opacity: a * (cur ? 1 : done ? 0.75 : 0.42),
                                  transform: `translateX(${mix(40, 0, a)}px)` }}>
              <div style={{ width: 54, height: 54, borderRadius: 27, display: "flex", alignItems: "center", justifyContent: "center",
                            background: cur ? RED : done ? "#2fbf71" : "rgba(255,255,255,0.12)", color: "#fff", fontSize: 28, fontWeight: 900,
                            boxShadow: cur ? "0 0 24px rgba(255,59,48,0.6)" : "none" }}>
                {done ? "✓" : i + 1}
              </div>
              <div style={{ color: "#fff", fontSize: cur ? 40 : 34, fontWeight: cur ? 900 : 700 }}>{s.text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}
