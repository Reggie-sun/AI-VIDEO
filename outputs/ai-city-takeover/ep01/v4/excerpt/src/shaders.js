// GLSL for the excerpt. Scene: a clip picture or a 2.5D plate (background layer + matted foreground layer, each under
// its own camera and focus), the fluorescent rows of s011, type tucked behind her (feedBack), type pressed in front of
// her (feed), ink keyed onto bright surfaces (surf: the billboard, the lightbox; the ink only takes where the surface is
// lit, so leaves and her finger cover it) and light (emit). Final: the gauze (mist veil and bloom from a blur of the
// whole frame, warm halation round the highlights, milky lifted blacks, soft shoulder), a light print screen, grain;
// then the crisp overlay. Conventions follow motion-kit/src/shaders.js (px origin top-left, textures uploaded unflipped,
// 2D canvases premultiplied).
import { COMMON } from '../../../../../../motion-kit/src/shaders.js';

export const SCENE = COMMON + `
uniform sampler2D uA; uniform vec2 uASize; uniform vec4 uViewA; uniform float uFitA; uniform float uLodA;
uniform sampler2D uB; uniform vec2 uBSize; uniform vec4 uViewB; uniform float uFitB; uniform float uLodB; uniform float uBOn;
uniform vec2 uShake;
uniform sampler2D uRows; uniform float uRowsOn; uniform vec4 uRowGain; uniform float uAmbient; uniform float uDark;
uniform float uAmbDark; uniform vec3 uLevels;   // v4: procedural rows on footage (uRowsOn 2); per-shot levels: black, scale, floor (linear)
uniform sampler2D uFeedBack; uniform sampler2D uFeed; uniform sampler2D uSurf; uniform vec2 uKey;
uniform sampler2D uEmit; uniform float uEmitGain;
uniform float uGainA; uniform float uGainB; uniform vec3 uTint;

vec2 toSrc(vec2 px, vec4 view, float fit){
  vec2 d = px - uRes * 0.5 - uShake;
  float c = cos(-view.w), s = sin(-view.w);
  d = mat2(c, s, -s, c) * d;
  return view.xy + d / (fit * view.z);
}
vec4 samp(sampler2D t, vec2 uv, vec2 size, float lod){
  vec4 sharp = sampleCR(t, uv, size);
  if (lod <= 0.001) return sharp;
  return mix(sharp, textureLod(t, uv, lod), clamp(lod, 0.0, 1.0));
}
vec4 layer(sampler2D tex, vec2 px){ vec4 c = texture(tex, vec2(px.x, px.y) / uRes); return c; }
vec3 over(vec3 col, vec4 pm){ // premultiplied sRGB canvas over linear colour
  if (pm.a <= 0.0) return col;
  vec3 c = toLin(pm.rgb / pm.a);
  return col * (1.0 - pm.a) + c * pm.a;
}
void main(){
  vec2 px = pxCoord();
  vec2 pa = toSrc(px, uViewA, uFitA);
  vec2 uva = pa / uASize;
  vec3 col = toLin(samp(uA, uva, uASize, uLodA).rgb) * uGainA;
  col = max(col - uLevels.x, 0.0) * uLevels.y + uLevels.z;
  float lumA = luma(toSrgb(col));
  if (uRowsOn > 1.5) {
    // the tubes on moving footage: bright, near-neutral pixels in the upper part of the frame, in four bands by height
    // (far = lowest), each switching with its row gain; the rest of the room (and the flash-lit figure) dims less
    vec3 s = toSrgb(col);
    float tube = smoothstep(0.80, 0.94, luma(s)) * (1.0 - smoothstep(0.10, 0.22, max(s.r, max(s.g, s.b)) - min(s.r, min(s.g, s.b))))
      * (1.0 - smoothstep(0.50, 0.58, px.y / uRes.y));
    float band = clamp(floor((0.56 - px.y / uRes.y) / 0.14), 0.0, 3.0);
    float rg = band < 0.5 ? uRowGain.x : band < 1.5 ? uRowGain.y : band < 2.5 ? uRowGain.z : uRowGain.w;
    float g = mix(uAmbient, rg, tube);
    col *= mix(mix(uAmbDark, uDark, tube), 1.0, g);
  } else if (uRowsOn > 0.5) {
    vec4 rm = texture(uRows, uva);
    float tw = clamp(rm.r + rm.g + rm.b + rm.a, 0.0, 1.0);
    float rg = dot(rm, uRowGain) / max(rm.r + rm.g + rm.b + rm.a, 1e-3);
    float g = mix(uAmbient, rg, tw);
    col *= mix(uDark, 1.0, g);
  }
  col = over(col, layer(uFeedBack, px));
  if (uBOn > 0.5) {
    vec2 pb = toSrc(px, uViewB, uFitB);
    vec2 uvb = pb / uBSize;
    vec4 f = samp(uB, uvb, uBSize, uLodB);
    float inside = step(0.0, uvb.x) * step(uvb.x, 1.0) * step(0.0, uvb.y) * step(uvb.y, 1.0);
    float a = clamp(f.a, 0.0, 1.0) * inside;
    vec3 fc = toLin(f.rgb) * uGainB;
    if (uRowsOn > 0.5) fc *= mix(uDark, 1.0, uAmbient);
    col = mix(col, fc, a);
    lumA = mix(lumA, luma(toSrgb(fc)), a);
  }
  vec4 sf = layer(uSurf, px);
  if (sf.a > 0.0) {
    float key = smoothstep(uKey.x, uKey.y, lumA);
    col = mix(col, toLin(sf.rgb / sf.a), sf.a * key);
  }
  col = over(col, layer(uFeed, px));
  vec4 em = layer(uEmit, px);
  col += toLin(em.rgb) * uEmitGain;
  col *= uTint;
  fragColor = vec4(col, 1.0);
}
`;

// Bright pass of the blur chain: here the whole frame (threshold 0), so the chain is a wide blur of the picture that
// the final pass uses both as the mist veil and, keyed by its own brightness, as the highlight bloom.
export const BRIGHT = COMMON + `
uniform sampler2D uScene;
void main(){ fragColor = vec4(texture(uScene, vUv).rgb, 1.0); }
`;

export const FINAL = COMMON + `
uniform sampler2D uScene; uniform sampler2D uBloom; uniform sampler2D uOverlay;
uniform float uExposure; uniform float uMist; uniform float uBloomGain; uniform float uBloomKnee; uniform float uHalation;
uniform vec3 uLift; uniform float uLiftAmt; uniform float uSat; uniform float uRedKeep; uniform float uContrast;
uniform float uHalftone; uniform float uCell; uniform float uGrain; uniform float uGrainOverlay;
uniform float uVignette; uniform float uCA; uniform float uWarm; uniform float uOvAlpha; uniform float uFade;
uniform float uBloomNorm; uniform float uMistLocal;
// v4r3 print (measured against EV, qa/texture.py): a softened base (Gaussian, uSoft px), EV's line screen (pitch
// uLinePitch px, frequency direction uLineAng rad in image px, strength uLine, the three inks offset by uMisregPx along
// it), and a warm balance on the mid tones (uWarmBal)
uniform float uSoft; uniform float uLine; uniform float uLinePitch; uniform float uLineAng; uniform float uMisregPx;
uniform float uWarmBal; uniform float uPinkGuard;
// v4r4 (2026-11-19): the base softened like a low-res photo upscaled (the half / quarter resolution copies of the scene,
// mixed in by uSoftMix, uSoftQ the quarter's share); the interface composited after the grade but under the screen and
// the grain, unsoftened (uOvInPrint); shadows cool (uCoolShadow, 0.5 before) or warm brown; an AM line screen with
// hard-ish lines, strongest in the mid tones (uLineAM); cold bright screens and lit glass kept cold (uColdGuard); reds
// below signal saturation capped (uRedCap: linear chroma ceiling for red hues that were not already signal red)
uniform sampler2D uHalf; uniform sampler2D uQuarter; uniform sampler2D uEighth; uniform float uSoftE; uniform float uSoftMix; uniform float uSoftQ; uniform float uOvInPrint;
uniform float uCoolShadow; uniform float uLineAM;
// v4r10: a tone curve over the picture before the interface and the screen: black point uToneBP, white point uToneWP,
// gamma uToneG (sRGB), a soft shoulder above 0.7 so the stretch never clips the lights; 0 = off
uniform float uToneOn; uniform float uToneBP; uniform float uToneWP; uniform float uToneG;
// v4r10b: the red cap again after the curve (the curve's stretch pushed skin into signal-red saturation): a red hue may
// not exceed uRedCapPost saturation unless it was already signal red before the curve (her ear lamp)
uniform float uRedCapPost; uniform float uColdGuard; uniform float uRedCap; uniform vec3 uShadowTint;
// s015-030 v1 (2026-11-23; 0 = off, so earlier EDLs render as before): the two red caps applied with a continuous hue
// weight (uCapSoft 1) instead of the hard redHue > 0.5 gate, whose on/off edge drew rust contours across smooth, warm
// defocused backgrounds (s022's panelling). Every pixel the hard gate capped is still capped in full; the band just
// past the old edge is capped partly, so no pixel gets redder than before.
uniform float uCapSoft;
// v2 (2026-11-21, texture_study/REPORT.md; 0 = off, so earlier versions are unchanged): an AM dot screen (uDotAM,
// pitch uDotPitch px, grid angle uDotAng rad; the three inks offset by uMisregPx along the grid's diagonal), a mosaic
// of the picture in uMosaic px blocks, a near-binary photocopy dither (uDither), a black frame (uBlack)
uniform float uDotAM; uniform float uDotPitch; uniform float uDotAng; uniform float uMosaic; uniform float uDither; uniform float uBlack;
vec3 sceneAt(vec2 uv){
  if (uSoftMix > 0.0) {
    vec3 half_ = texture(uHalf, uv).rgb, quart = texture(uQuarter, uv).rgb, full = texture(uScene, uv).rgb;
    vec3 soft = mix(full, mix(half_, quart, uSoftQ), uSoftMix);
    soft = mix(soft, texture(uEighth, uv).rgb, uSoftE);           // v4r9: a uniform diffusion at the viewing scale
    // her ear lamp is a few pixels: the softening must not average its red away
    float lamp = smoothstep(0.5, 0.7, (full.r - max(full.g, full.b)) / max(full.r, 1e-4)) * smoothstep(0.03, 0.08, full.r);
    return mix(soft, full, lamp);
  }
  if (uSoft <= 0.01) return texture(uScene, uv).rgb;
  vec2 px1 = 1.0 / uRes;
  vec3 acc = texture(uScene, uv).rgb * 0.2;
  float wsum = 0.2;
  for (int i = 0; i < 8; i++) {
    float a = float(i) * 0.7853982 + 0.3927;
    vec2 d = vec2(cos(a), sin(a));
    acc += texture(uScene, uv + d * px1 * uSoft * 0.75).rgb * 0.14; wsum += 0.14;
    acc += texture(uScene, uv + d.yx * vec2(1.0, -1.0) * px1 * uSoft * 1.7).rgb * 0.06; wsum += 0.06;
  }
  return acc / wsum;
}
float lineScreen(vec2 px, float v, float shift){
  vec2 f = vec2(cos(uLineAng), sin(uLineAng)) / uLinePitch;
  float s = 0.5 + 0.5 * cos(6.2831853 * (dot(px, f) + shift / uLinePitch));
  float aa = 0.12;
  return smoothstep(1.0 - clamp(v, 0.0, 1.0) - aa, 1.0 - clamp(v, 0.0, 1.0) + aa, s);
}

float screenDot(vec2 p, float ang, float cell, float v){
  float s = sin(ang), c = cos(ang);
  vec2 q = mat2(c, -s, s, c) * p / cell;
  vec2 f = fract(q) - 0.5;
  float r = sqrt(clamp(v, 0.0, 1.0)) * 0.7071;
  float aa = 0.75 / cell;
  return 1.0 - smoothstep(r - aa, r + aa, length(f));
}
vec3 tone(vec3 x){ // soft filmic shoulder, gentle toe (keeps the milky blacks milky, the whites creamy)
  x = max(x, 0.0);
  vec3 a = x * (1.0 + x / 6.0) / (1.0 + x);
  return a;
}
vec3 gradeAt(vec2 uv){
  vec3 c = sceneAt(uv) * uExposure;
  vec3 bl = texture(uBloom, uv).rgb * uBloomNorm * uExposure;
  float bL = luma(bl);
  c = mix(c, bl, uMist * mix(1.0, smoothstep(0.06, 0.45, bL), uMistLocal)); // the veil (design: only round light)
  vec3 glow = bl * smoothstep(uBloomKnee, uBloomKnee + 0.9, bL);
  c += glow * uBloomGain;                                            // pro-mist bloom on the highlights
  c += glow * vec3(1.0, 0.42, 0.22) * uHalation;                     // warm halation round them
  float L = luma(c);
  vec3 c0 = c;
  float cold = uColdGuard * smoothstep(0.02, 0.10, c.b - c.r) * smoothstep(0.25, 0.8, L);   // a lit screen keeps cold
  c = mix(c, c * vec3(0.93, 1.0, 1.06), smoothstep(0.25, 0.0, L) * uCoolShadow);   // cool shadows
  c = mix(c, c * uShadowTint, smoothstep(0.30, 0.02, L) * (1.0 - cold) * step(0.001, dot(uShadowTint, vec3(1.0))));
  c = mix(c, c * vec3(1.05, 1.0, 0.93), smoothstep(0.35, 1.2, L) * uWarm); // creamy highlights
  // warm toward amber (not toward red: pinks and lips must not turn signal red), held off what is already red-dominant
  float redDom = smoothstep(0.03, 0.15, c.r - max(c.g * 1.25, c.b));
  float wb = uWarmBal * (1.0 - redDom) * (1.0 - cold);
  c *= vec3(1.0 + wb, 1.0 + wb * 0.3, 1.0 - wb * 0.7) * (1.0 - smoothstep(0.6, 1.4, L)) + smoothstep(0.6, 1.4, L);
  float red = smoothstep(0.02, 0.2, c.r - max(c.g, c.b));
  red = max(red, smoothstep(0.0, 0.06, c.r - max(c.g * 1.15, c.b)) * uPinkGuard);   // v4r3: pinks and lips keep their chroma
  c = mix(vec3(luma(c)), c, mix(mix(uSat, 1.0, cold * 0.6), uRedKeep, red));
  if (uRedCap > 0.0) {
    // a red hue (R the largest, G and B close) may not reach signal saturation unless it already was signal red (the lamp)
    float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
    float redHue = step(max(c.g, c.b), c.r) * (1.0 - smoothstep(0.25, 0.45, (c.g - c.b) / max(c.r - c.b, 1e-4)));
    float s0 = (max(c0.r, max(c0.g, c0.b)) - min(c0.r, min(c0.g, c0.b))) / max(max(c0.r, max(c0.g, c0.b)), 1e-4);
    float sat = (mx - mn) / max(mx, 1e-4);
    float cap = mix(uRedCap, 1.0, smoothstep(0.82, 0.92, s0));
    if (uCapSoft > 0.5) {
      float wCap = step(max(c.g, c.b), c.r) * (1.0 - smoothstep(0.35, 0.65, (c.g - c.b) / max(c.r - c.b, 1e-4)));
      if (sat > cap) c = mix(c, vec3(mx) - (vec3(mx) - c) * (cap / sat), wCap);
    } else if (redHue > 0.5 && sat > cap) c = vec3(mx) - (vec3(mx) - c) * (cap / sat);
  }
  c = tone(c);
  c = toSrgb(c);
  c = (c - 0.5) * uContrast + 0.5;
  c = c * (1.0 - uLiftAmt) + uLift * uLiftAmt;                       // milky blacks
  return c;
}
void main(){
  vec2 px = pxCoord();
  if (uBlack > 0.5) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
  vec2 cd = vUv - 0.5;
  float r2 = dot(cd, cd) * 2.0;
  vec2 caOff = normalize(cd + 1e-6) * uCA * r2 / uRes;
  vec2 uv0 = vUv;
  if (uMosaic > 0.0) uv0 = (floor(vUv * uRes / uMosaic) + 0.5) * uMosaic / uRes;
  vec3 d;
  d.r = gradeAt(uv0 + caOff).r;
  d.g = gradeAt(uv0).g;
  d.b = gradeAt(uv0 - caOff).b;
  vec3 dPre = d;
  if (uToneOn > 0.5) {
    vec3 tv = pow(clamp((d - uToneBP) / (uToneWP - uToneBP), 0.0, 4.0), vec3(uToneG));
    vec3 sh = 0.7 + 0.3 * (1.0 - exp(-(tv - 0.7) / 0.3));
    d = mix(tv, sh, step(0.7, tv));
  }
  if (uRedCapPost > 0.0) {
    float mx = max(d.r, max(d.g, d.b)), mn = min(d.r, min(d.g, d.b));
    float redHue = step(max(d.g, d.b), d.r) * (1.0 - smoothstep(0.3, 0.5, (d.g - d.b) / max(d.r - d.b, 1e-4)));
    float s0 = (max(dPre.r, max(dPre.g, dPre.b)) - min(dPre.r, min(dPre.g, dPre.b))) / max(max(dPre.r, max(dPre.g, dPre.b)), 1e-4);
    float sat = (mx - mn) / max(mx, 1e-4);
    float cap = mix(uRedCapPost, 1.0, smoothstep(0.80, 0.90, s0));
    if (uCapSoft > 0.5) {
      float wCap = step(max(d.g, d.b), d.r) * (1.0 - smoothstep(0.40, 0.70, (d.g - d.b) / max(d.r - d.b, 1e-4)));
      if (sat > cap) d = mix(d, vec3(mx) - (vec3(mx) - d) * (cap / sat), wCap);
    } else if (redHue > 0.5 && sat > cap) d = vec3(mx) - (vec3(mx) - d) * (cap / sat);
  }
  vec4 ovp = texture(uOverlay, vec2(vUv.x, 1.0 - vUv.y));
  if (uOvInPrint > 0.5) d = d * (1.0 - ovp.a) + ovp.rgb;           // the interface under the print, unsoftened
  vec3 ht = vec3(screenDot(px, 0.2618, uCell, d.r), screenDot(px, 1.309, uCell, d.g), screenDot(px, 0.7854, uCell, d.b));
  d = mix(d, ht * max(d * 1.35, vec3(0.0)) + d * 0.35, uHalftone);
  if (uDotAM > 0.0) {
    // AM dot screen: two crossed cosines (peaks on the grid's two axes), clipped hard into dots, deepest in the mid tones
    float ca = cos(uDotAng), sa = sin(uDotAng);
    vec2 q = mat2(ca, sa, -sa, ca) * px / uDotPitch;
    q += vec2(vnoise(px / 37.0) - 0.5, vnoise(px / 37.0 + 5.3) - 0.5) * 0.6;   // a print's wobble
    float m = uMisregPx / uDotPitch;
    vec3 sq = 0.5 * vec3(cos(6.2831853 * (q.x + m)) + cos(6.2831853 * (q.y + m)), cos(6.2831853 * q.x) + cos(6.2831853 * q.y),
      cos(6.2831853 * (q.x - m)) + cos(6.2831853 * (q.y - m)));
    sq = clamp(sq * 1.8, -1.0, 1.0);
    vec3 wv = mix(vec3(0.35), vec3(1.0), 4.0 * d * (1.0 - d));
    d = d * (1.0 + uDotAM * wv * sq);
  }
  if (uDither > 0.0) {
    // photocopy: the tone thresholded against white noise per pixel, contrast pushed, a warm paper white
    float lmD = clamp((luma(d) - 0.5) * 1.6 + 0.5, 0.0, 1.0);
    vec3 bin = step(hash12(floor(px) + uFrame * 13.7), lmD) * vec3(0.96, 0.94, 0.89) + vec3(0.03);
    d = mix(d, bin, uDither);
  }
  if (uLineAM > 0.0) {
    // AM line screen: the tone modulated by a hard-edged line pattern, deepest in the mid tones, the three inks offset
    vec2 fv = vec2(cos(uLineAng), sin(uLineAng)) / uLinePitch;
    float ph = dot(px, fv) + (vnoise(px / 37.0) - 0.5) * 0.9 + (vnoise(px / 9.0 + 11.3) - 0.5) * 0.25;   // a print's wobble
    vec3 sq = vec3(cos(6.2831853 * (ph + uMisregPx / uLinePitch)), cos(6.2831853 * ph), cos(6.2831853 * (ph - uMisregPx / uLinePitch)));
    sq = clamp(sq * 1.6, -1.0, 1.0);
    vec3 wv = mix(vec3(0.35), vec3(1.0), 4.0 * d * (1.0 - d));
    d = d * (1.0 + uLineAM * wv * sq);
  } else if (uLine > 0.0) {
    vec3 ls = vec3(lineScreen(px, d.r, uMisregPx), lineScreen(px, d.g, 0.0), lineScreen(px, d.b, -uMisregPx));
    d = mix(d, ls * max(d * 1.25, vec3(0.0)) + d * 0.4, uLine);
  }
  float v = length(cd * vec2(1.0, 0.62)) * 1.45;
  d *= 1.0 - uVignette * v * v;
  vec4 ov = texture(uOverlay, vec2(vUv.x, 1.0 - vUv.y)) * uOvAlpha;
  d = d * (1.0 - ov.a) + ov.rgb;
  float g = (vnoise(px / 1.25 + uFrame * vec2(37.1, 17.3)) - 0.5) * 1.5 + (hash12(px + uFrame * 7.7) - 0.5) * 0.8;
  float lm = luma(d);
  float amp = uGrain * (0.55 + 0.8 * (1.0 - abs(lm * 2.0 - 1.0))) * mix(1.0, uGrainOverlay, ov.a);
  d += g * amp;
  d *= 1.0 - uFade;
  d += (hash12(px + uFrame * 3.1) - 0.5) / 255.0;
  fragColor = vec4(clamp(d, 0.0, 1.0), 1.0);
}
`;
