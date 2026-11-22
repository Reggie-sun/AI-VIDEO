import { AbsoluteFill, Img, useCurrentFrame } from "remotion";
import { asset, type SceneProps } from "agentcut";

type Props = SceneProps & { pages: string[]; pageW: number; pageH: number; speed: number };

// Pages of the real preprint stream past, tilted and full-bleed: a wall of equations, not text to read.
export default function PaperScroll({ pages, pageW, pageH, speed = 26, width, height, clip }: Props) {
  const f = useCurrentFrame();
  const h = height * 1.25;
  const w = (pageW / pageH) * h;
  const gap = 36;
  const row = pages.length * (w + gap);
  const shift = (f * speed) % row;
  const fade = Math.min(1, f / 6, (clip.duration - f) / 6);
  const tiles = [];
  for (let k = 0; k < 2; k++) {
    pages.forEach((p, i) => {
      const x = i * (w + gap) + k * row - shift;
      if (x > width * 1.4 || x + w < -width * 0.4) return;
      tiles.push(
        <Img
          key={`${k}-${i}`}
          src={asset(p)}
          style={{ position: "absolute", left: x, top: (height - h) / 2, width: w, height: h, boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}
        />,
      );
    });
  }
  return (
    <AbsoluteFill style={{ background: "#e9e6df", overflow: "hidden", opacity: fade }}>
      <AbsoluteFill style={{ transform: "rotate(-8deg) scale(1.25)" }}>{tiles}</AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(90deg,rgba(15,12,10,0.55),rgba(15,12,10,0) 25%,rgba(15,12,10,0) 75%,rgba(15,12,10,0.55))" }} />
    </AbsoluteFill>
  );
}
