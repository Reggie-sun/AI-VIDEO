export const FONT = "Noto Sans SC";
export const RED = "#ff3b30";
export const YELLOW = "#ffd23f";
export const BG = "#1b1d22";
// Phone screen layout on the 1920x1080 frame: fixed height, width from the source aspect.
export const SCREEN_TOP = 16;
export const SCREEN_H = 896;
export function screenRect(sw: number, sh: number, W = 1920) {
  const h = SCREEN_H;
  const w = (h * sw) / sh;
  return { x: (W - w) / 2, y: SCREEN_TOP, w, h, s: h / sh };
}
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
