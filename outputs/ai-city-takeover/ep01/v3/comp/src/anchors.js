// Plate anchors in plate px (the stills are 1672 x 941), read off gridded sheets of the board-v2 stills on 2026-11-04.
// Keyed by the still's file stem: a regenerated variant (-b, -c) needs its own entry; an unknown still falls back to
// the centre and to each component's generic default. A unit's `target` / `targets` in shots-map.json override the
// matching anchor (osd boxes, red dots, the door gap).
//   focus: what the camera centres on; figure / face / body: [x, y, w, h]; collar: her red collar line (two points,
//   top first); led: the red light on her ear device; slit: the door gap as a top / bottom pair; other keys per graphic
export const ANCHORS = {
  // the hall from the CCTV mount: a perspective lattice of copies (head heights per row, vanishing point at the door,
  // front-row spacing); `her` is the copy the board follows (the shots map's target for this still)
  'P-hall-cctv-a': {
    focus: [836, 470], door: [840, 150], her: [936, 489],
    lattice: { vx: 816, vy: 141, y0: 545, spacing: 97, rows: [545, 480, 433, 392, 360, 333, 309, 290, 272, 256, 243], cols: [-9, 8] },
  },
  'P-dark-hall-b': { focus: [836, 560], her: [1205, 560], led: [1250, 683], collar: [[1242, 655], [1267, 728]], figure: [1150, 500, 117, 230] },
  'P-row-lit-a': { focus: [1000, 420], dir: 1, collar: [[1154, 376], [1104, 438]], led: [1150, 254] },
  'P-eyes-closed-a': { focus: [840, 430] },
  'P-headturn-b': { focus: [840, 430], face: [600, 180, 520, 560] },
  'P-step-out-a': { focus: [836, 380] },
  'P-catwalk-b': { focus: [836, 400], side: [1010, 330], figure: [700, 30, 275, 880], face: [760, 20, 135, 160] },
  'P-rack-miswire-a': { focus: [1000, 360], led: [1048, 314] },
  'P-aisle-door-a': { focus: [836, 470], slit: [[842, 385], [842, 590]], floor: [842, 590] },
  'P-door-face-a': { focus: [880, 400], slit: [[392, 0], [392, 941]], collar: [[1263, 635], [1162, 811]], led: [1207, 371], face: [552, 100, 602, 602] },
  'P-city-aerial-a': {
    focus: [836, 430],
    highway: [[0, 620], [200, 575], [400, 510], [600, 450], [800, 400], [960, 350], [1060, 305], [1110, 265], [1125, 220]],
  },
  'P-city-gap-a': { focus: [850, 470] },
  'P-gap-face-a': { focus: [880, 420], slit: [[1358, 0], [1358, 941]], collar: [[1179, 707], [1079, 883]], led: [1179, 381], face: [602, 130, 602, 585] },
  'P-gap-wide-a': { focus: [836, 470], figure: [720, 90, 150, 740], slit: [[468, 0], [468, 790]] },
  'P-eval-screens-a': {
    focus: [836, 380],
    screens: [[10, 225, 317, 265], [355, 225, 290, 265], [676, 240, 233, 240], [931, 240, 224, 235], [1173, 250, 145, 225],
      [1336, 255, 146, 215], [1495, 260, 150, 205]],
  },
  'P-speak-aisle-b': { focus: [836, 330], face: [702, 50, 210, 226], body: [569, 0, 518, 941], tag: [330, 200] },
  'P-offline-a': { focus: [853, 420], sheets: [[250, 40], [1170, 70], [1450, 90], [40, 470], [1260, 345]] },
  // the white red-team room: two faceless terminals back to back, one per glass booth; the shared wall between them
  'P-lab-terminals-a': { focus: [836, 470], terminals: [[642, 367, 158, 375], [867, 367, 167, 375]], screens: [[692, 417, 66, 116], [913, 417, 70, 116]], wall: 833 },
  'P-dark-cu-a': { focus: [900, 420], slit: [[181, 268], [181, 470]], collar: [[1288, 702], [1212, 861]], led: [1246, 385] },
  'P-floor-line-b': { focus: [836, 420], figure: [700, 15, 275, 885] },
  // face boxes of the monitor wall's stills (a2 U073; read off gridded sheets on 2026-11-04)
  'P-door-latch-a': { face: [730, 10, 340, 350] },
  'P-spotlight-low-a': { face: [590, 160, 540, 560] },
  'P-hairflip-a': { face: [690, 220, 500, 420] },
  'P-gaze-b': { focus: [850, 450], collar: [[1137, 686], [1037, 853]], led: [1137, 372], face: [602, 167, 502, 569] },
  'P-hand-lens-a': { focus: [800, 470], dot: [1067, 580] },
  'P-behind-glass-a': { focus: [836, 430], face: [560, 100, 560, 700], collar: [[1204, 666], [1087, 875]], led: [1204, 390] },
  // the fingertip on the glass and the skyline outline it traces, leftwards from the tip
  'P-trace-profile-a': {
    focus: [760, 470], tip: [381, 512], collar: [[1321, 599], [1304, 783]], led: [1251, 331],
    skyline: [[381, 512], [334, 502], [301, 532], [251, 448], [217, 465], [184, 406], [159, 398], [142, 331], [125, 264],
      [110, 381], [84, 448], [50, 465], [5, 431]],
  },
  'P-glass-profile-a': { focus: [760, 470], fog: [440, 560], collar: [[1145, 677], [1065, 886]], led: [1050, 390] },
  'P-spotlight-wide-a': { focus: [836, 470], figure: [735, 330, 195, 455] },
  'P-backlit-b': { focus: [836, 420], collar: [[1137, 702], [1037, 870]] },
  'P-gap-close-a': { focus: [800, 470], slit: [[671, 0], [671, 650]], pool: [[600, 650], [1500, 941]] },
};
