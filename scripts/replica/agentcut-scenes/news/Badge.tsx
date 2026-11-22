import { AbsoluteFill, useCurrentFrame } from "remotion";
import { SPRING, ease, mix, sp, type SceneProps } from "agentcut";

type Props = SceneProps & { title: string; tag: string };

// Column badge for the opening: bottom-left pill, slides in, eases out.
export default function Badge({ title, tag, clip }: Props) {
  const f = useCurrentFrame();
  const s = sp(f, 2, SPRING.snappy);
  const out = ease(f, clip.duration - 8, clip.duration);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 72,
          top: 720,
          display: "flex",
          alignItems: "center",
          gap: 14,
          transform: `translateX(${mix(-60, 0, s)}px)`,
          opacity: s * (1 - out),
        }}
      >
        <div
          style={{
            padding: "12px 26px",
            borderRadius: 999,
            background: "linear-gradient(90deg,#ff5a36,#ffb03a)",
            color: "#16110c",
            fontFamily: "Noto Sans SC",
            fontWeight: 900,
            fontSize: 46,
            letterSpacing: 2,
          }}
        >
          {title}
        </div>
        <div
          style={{
            padding: "10px 18px",
            borderRadius: 10,
            background: "rgba(10,10,14,0.75)",
            color: "#ffd7a8",
            fontFamily: "Noto Sans SC",
            fontWeight: 700,
            fontSize: 30,
          }}
        >
          {tag}
        </div>
      </div>
    </AbsoluteFill>
  );
}
