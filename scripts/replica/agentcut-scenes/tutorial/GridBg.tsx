import { AbsoluteFill } from "remotion";
import { type SceneProps } from "agentcut";

// Dark studio floor with a faint grid, like the reference's backdrop.
export default function GridBg(_: SceneProps) {
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 38%, #2b2e35 0%, #1b1d22 55%, #121317 100%)" }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.09) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
          backgroundPosition: "0 0, 0 0",
          maskImage: "radial-gradient(ellipse at 50% 45%, black 30%, transparent 85%)",
          WebkitMaskImage: "radial-gradient(ellipse at 50% 45%, black 30%, transparent 85%)",
        }}
      />
    </AbsoluteFill>
  );
}
