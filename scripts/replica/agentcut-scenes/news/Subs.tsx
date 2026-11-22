import { AbsoluteFill, useCurrentFrame } from "remotion";
import { type SceneProps } from "agentcut";

type Line = { text: string; from: number; to: number };
type Props = SceneProps & { lines: Line[]; fontSize?: number };

// One subtitle line at a time, white on a dark plate, centred in the y≈925–980 band.
// A line stays up until the next line starts (or the clip ends).
export default function Subs({ lines, fontSize = 50, width, clip }: Props) {
  const f = useCurrentFrame();
  let current: Line | null = null;
  lines.forEach((line, i) => {
    const end = i + 1 < lines.length ? lines[i + 1].from : clip.duration;
    if (f >= line.from && f < end) current = line;
  });
  if (!current) return null;
  const text = (current as Line).text;
  // Rough width: CJK ≈ 1em, Latin/digits ≈ 0.56em. Shrink long lines to fit one row.
  let units = 0;
  for (const ch of text) units += /[　-鿿＀-￯「」]/.test(ch) ? 1 : 0.56;
  const size = Math.min(fontSize, Math.floor((width * 0.86) / Math.max(1, units)));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
      <div
        style={{
          marginBottom: 1080 - 985,
          padding: "8px 26px 10px",
          borderRadius: 10,
          background: "rgba(10,10,14,0.72)",
          color: "#ffffff",
          fontFamily: "Noto Sans SC",
          fontWeight: 700,
          fontSize: size,
          lineHeight: 1.25,
          letterSpacing: 1,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
}
