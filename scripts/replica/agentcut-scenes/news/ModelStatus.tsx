import { AbsoluteFill, Img, useCurrentFrame } from "remotion";
import { SPRING, asset, mix, sp, type SceneProps } from "agentcut";

type Card = { org: string; name: string; status: string; note: string; tone: "green" | "amber"; at: number; focus?: boolean };
type Props = SceneProps & { bgSrc: string; cards: Card[] };

const TONE = { green: "#2fd47a", amber: "#ffb340" };

// Status cards (released vs. in testing) over the real AA index chart, dimmed.
export default function ModelStatus({ bgSrc, cards, width, height }: Props) {
  const f = useCurrentFrame();
  const n = cards.length;
  const cw = n === 1 ? 900 : 800;
  const gap = 48;
  const total = n * cw + (n - 1) * gap;
  return (
    <AbsoluteFill style={{ background: "#0b0b0f", overflow: "hidden" }}>
      <Img
        src={asset(bgSrc)}
        style={{ position: "absolute", left: -120, top: -260, width: width + 240, opacity: 0.32, filter: "blur(6px) saturate(0.8)" }}
      />
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(8,8,12,0.55),rgba(8,8,12,0.85))" }} />
      {cards.map((c, i) => {
        const s = sp(f, c.at, SPRING.pop);
        const left = (width - total) / 2 + i * (cw + gap);
        const dim = cards.some((x) => x.focus) && !c.focus ? 0.55 : 1;
        const color = TONE[c.tone];
        return (
          <div
            key={c.name}
            style={{
              position: "absolute",
              left,
              top: height * 0.2,
              width: cw,
              height: 470,
              borderRadius: 28,
              background: "rgba(20,20,26,0.92)",
              border: `3px solid ${c.focus ? color : "rgba(255,255,255,0.14)"}`,
              boxShadow: c.focus ? `0 0 46px ${color}55` : "none",
              padding: "46px 52px",
              opacity: s * dim,
              transform: `translateY(${mix(50, 0, s)}px) scale(${mix(0.94, 1, s)})`,
              fontFamily: "Noto Sans SC",
              color: "#fff",
            }}
          >
            <div style={{ fontSize: 34, fontWeight: 500, color: "rgba(255,255,255,0.62)" }}>{c.org}</div>
            <div style={{ fontSize: n === 1 ? 92 : 76, fontWeight: 900, marginTop: 10, letterSpacing: 0.5, whiteSpace: "nowrap" }}>{c.name}</div>
            <div
              style={{
                display: "inline-block",
                marginTop: 52,
                padding: "12px 30px",
                borderRadius: 999,
                background: `${color}22`,
                border: `3px solid ${color}`,
                color,
                fontSize: 52,
                fontWeight: 900,
              }}
            >
              {c.status}
            </div>
            <div style={{ fontSize: 34, fontWeight: 500, marginTop: 34, color: "rgba(255,255,255,0.78)" }}>{c.note}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
}
