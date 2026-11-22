import { AbsoluteFill, Easing, Img, interpolate, useCurrentFrame } from "remotion";
import { asset, type SceneProps } from "agentcut";

type Rect = { x: number; y: number; w: number; h: number };
type Props = SceneProps & {
  src: string;
  iw: number;
  ih: number;
  from: Rect;
  to: Rect;
  bg?: string;
  mark?: Rect | null;
  markAt?: number;
  markColor?: string;
  clampEdges?: boolean;
  contain?: boolean;
  wipe?: { from: number; to: number } | null;
};

// Pans and zooms one screenshot from rect `from` to rect `to` (fractions of the image).
// The image always covers the whole frame: no dead bands around a small picture.
export default function Still({ src, iw, ih, from, to, bg = "#0b0b0f", mark, markAt = 10, markColor = "#ff6a3d", clampEdges = true, contain = false, wipe = null, width, height, clip }: Props) {
  const f = useCurrentFrame();
  const t = interpolate(f, [0, Math.max(1, clip.duration - 1)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const r = {
    x: from.x + (to.x - from.x) * t,
    y: from.y + (to.y - from.y) * t,
    w: from.w + (to.w - from.w) * t,
    h: from.h + (to.h - from.h) * t,
  };
  const fit = Math.min(width / (r.w * iw), height / (r.h * ih));
  const cover = Math.max(width / iw, height / ih);
  const s = contain ? fit : Math.max(fit, cover);
  const cx = (r.x + r.w / 2) * iw;
  const cy = (r.y + r.h / 2) * ih;
  // clampEdges=false lets the rect sit centred past the image edge; bg should match the page colour then.
  const left = clampEdges ? Math.min(0, Math.max(width - iw * s, width / 2 - cx * s)) : width / 2 - cx * s;
  const top = clampEdges ? Math.min(0, Math.max(height - ih * s, height / 2 - cy * s)) : height / 2 - cy * s;
  const m = mark ? interpolate(f, [markAt, markAt + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ background: bg, overflow: "hidden" }}>
      <Img src={asset(src)} style={{ position: "absolute", left, top, width: iw * s, height: ih * s }} />
      {wipe ? (
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            right: 0,
            left: left + iw * s * (wipe.from + (wipe.to - wipe.from) * Math.min(1, f / Math.max(1, clip.duration * 0.8))),
            background: bg,
          }}
        />
      ) : null}
      {mark ? (
        <div
          style={{
            position: "absolute",
            left: left + mark.x * iw * s - 8,
            top: top + mark.y * ih * s - 8,
            width: mark.w * iw * s + 16,
            height: mark.h * ih * s + 16,
            border: `6px solid ${markColor}`,
            borderRadius: 14,
            opacity: m,
            transform: `scale(${1.08 - 0.08 * m})`,
            boxShadow: `0 0 28px ${markColor}`,
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
}
