import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, type SceneProps } from "agentcut";
import { screenRect, RED } from "./lib/theme";

type Box = { x: number; y: number; w: number; h: number; from: number; to: number };
type Props = SceneProps & { sw: number; sh: number; boxes?: Box[] };

// Bezel over the native video clip (same rect), rounded screen corners, and red tap boxes.
// Box coordinates are source pixels; from/to are frames local to the clip.
export default function Phone({ sw, sh, boxes = [], width }: Props) {
  const f = useCurrentFrame();
  const r = screenRect(sw, sh, width);
  const B = 14; // bezel
  const R = 46; // screen corner radius
  const ox = r.x - B, oy = r.y - B, ow = r.w + 2 * B, oh = r.h + 2 * B;
  const inner = `M${r.x + R},${r.y} H${r.x + r.w - R} A${R},${R} 0 0 1 ${r.x + r.w},${r.y + R} V${r.y + r.h - R} A${R},${R} 0 0 1 ${r.x + r.w - R},${r.y + r.h} H${r.x + R} A${R},${R} 0 0 1 ${r.x},${r.y + r.h - R} V${r.y + R} A${R},${R} 0 0 1 ${r.x + R},${r.y} Z`;
  const RO = R + B;
  const outer = `M${ox + RO},${oy} H${ox + ow - RO} A${RO},${RO} 0 0 1 ${ox + ow},${oy + RO} V${oy + oh - RO} A${RO},${RO} 0 0 1 ${ox + ow - RO},${oy + oh} H${ox + RO} A${RO},${RO} 0 0 1 ${ox},${oy + oh - RO} V${oy + RO} A${RO},${RO} 0 0 1 ${ox + RO},${oy} Z`;
  return (
    <AbsoluteFill>
      <svg width={width} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <defs>
          <filter id="ps" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="18" stdDeviation="22" floodColor="#000" floodOpacity="0.55" />
          </filter>
        </defs>
        {/* screen-corner mask + bezel: outer rounded rect minus inner rounded rect, plus the square corners outside the inner rect */}
        <path d={`M0,0 H${width} V1080 H0 Z ${inner}`} fill="none" />
        <path d={`${outer} ${inner}`} fillRule="evenodd" fill="#0d0e11" filter="url(#ps)" />
        <path d={`${outer} ${inner}`} fillRule="evenodd" fill="none" stroke="#3a3d45" strokeWidth={2} />
        <path d={`M${r.x - 1},${r.y - 1} H${r.x + r.w + 1} V${r.y + r.h + 1} H${r.x - 1} Z ${inner}`} fillRule="evenodd" fill="#0d0e11" />
      </svg>
      {boxes.map((b, i) => {
        if (f < b.from || f >= b.to) return null;
        const s = sp(f, b.from, SPRING.pop);
        const pulse = 0.5 + 0.5 * Math.sin(((f - b.from) / 30) * Math.PI * 2);
        const pad = 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: r.x + b.x * r.s - pad,
              top: r.y + b.y * r.s - pad,
              width: b.w * r.s + 2 * pad,
              height: b.h * r.s + 2 * pad,
              border: `5px solid ${RED}`,
              borderRadius: 12,
              boxShadow: `0 0 ${10 + 10 * pulse}px rgba(255,59,48,0.75)`,
              transform: `scale(${1.25 - 0.25 * s})`,
              opacity: Math.min(1, s * 1.5),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
}
