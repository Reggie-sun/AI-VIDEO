import { AbsoluteFill, useCurrentFrame } from "remotion";
import { type SceneProps } from "agentcut";
import { FONT, RED } from "./lib/theme";

type Ch = { label: string; from: number };
type Props = SceneProps & { chapters: Ch[] };

// Bottom chapter strip like the reference's progress bar; the current chapter is lit.
export default function Chapters({ chapters, width, clip }: Props) {
  const f = useCurrentFrame();
  const total = clip.duration;
  let cur = 0;
  chapters.forEach((c, i) => { if (f >= c.from) cur = i; });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: 1030, width, height: 50, display: "flex", fontFamily: FONT, background: "rgba(0,0,0,0.55)" }}>
        {chapters.map((c, i) => {
          const end = i + 1 < chapters.length ? chapters[i + 1].from : total;
          const w = ((end - c.from) / total) * width;
          const p = Math.max(0, Math.min(1, (f - c.from) / (end - c.from)));
          return (
            <div key={i} style={{ position: "relative", width: w, height: 50, borderRight: "2px solid rgba(255,255,255,0.25)",
                                  display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${p * 100}%`, background: i === cur ? "rgba(255,59,48,0.85)" : "rgba(255,255,255,0.12)" }} />
              <div style={{ position: "relative", color: i === cur ? "#fff" : "rgba(255,255,255,0.7)", fontSize: 24, fontWeight: i === cur ? 900 : 500, whiteSpace: "nowrap" }}>
                {c.label}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}
