// Graphic name -> handler(k, t, u, cm) for every component family in shots-map.json's `graphic` field ('+' joins
// several on one unit): exact names first, then a family prefix whose rest is the argument (flipclock_0346_0347 ->
// 0346_0347). A name with no handler draws nothing and is reported by build.py. Handlers return scene overrides
// (plateGain, emitGain, grade, osdAlpha) merged by main.js.
import { smoothstep } from '../../../../../../motion-kit/src/math.js';
import { BOARDS } from './boards.js';
import { CHARTS } from './charts.js';
import { LABELS } from './labels.js';
import { LIGHTS } from './lights.js';
import { LYRIC_STYLES } from './lyric.js';
import { OSD, monitorFrame, monitorWall } from './osd.js';

const EXACT = {
  ...OSD, ...LIGHTS, ...CHARTS,
  photo_flip_cached: (k, t, u) => BOARDS.photo_flip_cached(k, t, u),
  tag_cached_timestamps: (k, t, u, cm) => LABELS.tag_cached_timestamps(k, t, u, cm),
  label_redteam: (k, t, u) => LABELS.label_redteam(k, t, u),
  label_card: (k, t, u) => LABELS.label_card(k, t, u),
  invert_white_panel_words: (k, t, u) => LABELS.white_panel(k, t, u),
  monitor_wall: (k, t, u) => monitorWall(k, t, u),
  monitor_frame: (k, t, u, cm) => { monitorFrame(k, t, 1); return LIGHTS.breathe_red(k, t, u, cm); },
  // the city's camera: the same bezel fading in over the unit's first beats, labelled with graphic_text (CITY CAM)
  monitor_frame_city: (k, t, u) => { monitorFrame(k, t, smoothstep(k.t0, k.t0 + 0.4, t), u.text || undefined); return {}; },
  black: () => ({ plateGain: 0, emitGain: 0 }),
  ...Object.fromEntries(LYRIC_STYLES.map(n => [n, () => ({})])),        // the lyric layer (lyric.js) draws these
};
const PREFIX = [
  ['flipclock_', (k, t, u, cm, a) => BOARDS.flipclock(k, t, u, a)], ['flipdate_', (k, t, u, cm, a) => BOARDS.flipdate(k, t, u, a)],
  ['calendar_', (k, t, u, cm, a) => BOARDS.calendar(k, t, u, a)], ['flipwall_', (k, t, u, cm, a) => BOARDS.flipwall(k, t, u, a)],
  ['look_label_', (k, t, u, cm, a) => LABELS.look_label(k, t, u, a, cm)], ['date_tag_', (k, t, u, cm, a) => LABELS.date_tag(k, t, u, a, cm)],
  ['tag_', (k, t, u, cm, a) => LABELS.tag(k, t, u, a, cm)], ['stamp_', (k, t, u, cm, a) => LABELS.stamp(k, t, u, a, cm)],
  ['invert_flash_', (k, t, u, cm, a) => LABELS.invert_flash(k, t, u, a)], ['corner_', () => ({})],
];
export function handlerOf(name) {
  if (EXACT[name]) return (k, t, u, cm) => EXACT[name](k, t, u, cm);
  const hit = PREFIX.find(([p]) => name.startsWith(p));
  return hit ? (k, t, u, cm) => hit[1](k, t, u, cm, name.slice(hit[0].length)) : null;
}
