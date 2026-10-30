// GLSL ES 3.00 sources. Conventions:
//  - "px" = output pixel coordinates, origin top-left (converted from gl_FragCoord).
//  - Plate textures are uploaded without flip: v = 0 is the image's top row, so a plate is
//    sampled with platePx / plateSize directly.
//  - Render-target textures are sampled with vUv (origin bottom-left, same as gl_FragCoord).
//  - The overlay canvas texture (no flip, premultiplied) is sampled with (vUv.x, 1 - vUv.y).
//  - Scene passes work in linear light; the final pass tone-maps and encodes to sRGB.

export const COMMON = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 fragColor;
uniform vec2 uRes;
uniform float uTime;
uniform float uFrame;
vec2 pxCoord(){ return vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y); }
float luma(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 toLin(vec3 c){ return pow(max(c, 0.0), vec3(2.2)); }
vec3 toSrgb(vec3 c){ return pow(max(c, 0.0), vec3(1.0 / 2.2)); }
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash12(i), b = hash12(i + vec2(1.0, 0.0)), c = hash12(i + vec2(0.0, 1.0)), d = hash12(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
  for (int i = 0; i < 5; i++){ v += a * vnoise(p); p = m * p; a *= 0.5; }
  return v;
}
vec4 sampleCR(sampler2D tex, vec2 uv, vec2 texSize){
  vec2 sp = uv * texSize; vec2 t1 = floor(sp - 0.5) + 0.5; vec2 f = sp - t1;
  vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f)); vec2 w1 = 1.0 + f * f * (-2.5 + 1.5 * f);
  vec2 w2 = f * (0.5 + f * (2.0 - 1.5 * f)); vec2 w3 = f * f * (-0.5 + 0.5 * f);
  vec2 w12 = w1 + w2; vec2 t12 = (t1 + w2 / w12) / texSize; vec2 t0 = (t1 - 1.0) / texSize; vec2 t3 = (t1 + 2.0) / texSize;
  vec4 r = textureLod(tex, vec2(t0.x, t0.y), 0.0) * w0.x * w0.y + textureLod(tex, vec2(t12.x, t0.y), 0.0) * w12.x * w0.y
         + textureLod(tex, vec2(t3.x, t0.y), 0.0) * w3.x * w0.y + textureLod(tex, vec2(t0.x, t12.y), 0.0) * w0.x * w12.y
         + textureLod(tex, vec2(t12.x, t12.y), 0.0) * w12.x * w12.y + textureLod(tex, vec2(t3.x, t12.y), 0.0) * w3.x * w12.y
         + textureLod(tex, vec2(t0.x, t3.y), 0.0) * w0.x * w3.y + textureLod(tex, vec2(t12.x, t3.y), 0.0) * w12.x * w3.y
         + textureLod(tex, vec2(t3.x, t3.y), 0.0) * w3.x * w3.y;
  return max(r, 0.0);
}
`;

// Scene pass: plate through a camera, fog, lights, light-trail segments, and per-shot
// features switched by uniforms (screen UI via homography, interior sweeps, trail pulses).
export const SCENE = COMMON + `
uniform sampler2D uPlate; uniform vec2 uPlateSize;
uniform vec4 uView;      // plate cx, cy, zoom, rotation
uniform float uFit;      // output px per plate px at zoom 1
uniform vec2 uShake;     // output px offset
uniform float uPlateGain;
uniform vec3 uPlateTint;
// fog: two drifting layers lit by the blurred plate
uniform vec4 uFogA; uniform vec4 uFogB; // density, scale, driftX, driftY
uniform vec3 uFogTint; uniform float uFogLift;
// point lights in output px
#define MAXL 32
uniform int uLN; uniform vec4 uLP[MAXL]; uniform vec4 uLC[MAXL];
// light-trail capsule segments in output px
#define MAXS 64
uniform int uSN; uniform vec4 uSA[MAXS]; uniform vec2 uSW[MAXS]; uniform vec3 uSColor;
// screen (S2): output px -> screen uv
uniform float uScreenOn; uniform mat3 uScreenH; uniform sampler2D uUI; uniform float uScreenGain;
uniform vec3 uSpillColor; uniform float uSpill; uniform vec2 uScreenCenter; uniform float uScreenRadius;
// interior mask (S2): r = interior (1) vs exterior through glass (0); sampled in plate uv
uniform float uMaskOn; uniform sampler2D uMask;
uniform vec4 uSweep; uniform float uSweepGain; // dir.x, dir.y, position, width
uniform vec3 uFlowVP; // exterior forward flow: vp.x, vp.y (plate px), scale
// soft dark car bodies (output px): cx, cy, halfW, halfH ; opacity
#define MAXB 12
uniform int uBN; uniform vec4 uBP[MAXB]; uniform float uBA[MAXB];
// emissive canvas (premultiplied, top-left origin) added as HDR light
uniform sampler2D uEmit; uniform float uEmitGain;
// trail pulses (S3)
uniform float uTrailOn; uniform sampler2D uFlow; uniform float uBeatPos; uniform float uLambda;
uniform float uPulseGain; uniform float uFlashGain; uniform vec3 uTrailColor;

vec2 outToPlate(vec2 px){
  vec2 d = px - uRes * 0.5 - uShake;
  float c = cos(-uView.w), s = sin(-uView.w);
  d = mat2(c, s, -s, c) * d;
  return uView.xy + d / (uFit * uView.z);
}
float segDist(vec2 p, vec2 a, vec2 b){ vec2 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-4), 0.0, 1.0); return length(pa - ba * h); }

void main(){
  vec2 px = pxCoord();
  vec2 pp = outToPlate(px);
  float interior = 1.0;
  if (uMaskOn > 0.5) {
    interior = textureLod(uMask, pp / uPlateSize, 0.0).r;
    // exterior seen through the glass drifts forward around the vanishing point
    vec2 ppx = uFlowVP.xy + (pp - uFlowVP.xy) / uFlowVP.z;
    pp = mix(ppx, pp, interior);
  }
  vec2 uv = pp / uPlateSize;
  vec3 col = toLin(sampleCR(uPlate, uv, uPlateSize).rgb) * uPlateGain * uPlateTint;
  vec3 blurred = toLin(textureLod(uPlate, uv, 5.0).rgb);
  vec3 blurredWide = toLin(textureLod(uPlate, uv, 7.0).rgb);

  // interior light sweeps from passing street lamps relight existing surfaces
  if (uMaskOn > 0.5) {
    float band = exp(-pow((dot(px, uSweep.xy) - uSweep.z) / uSweep.w, 2.0));
    col *= 1.0 + band * uSweepGain * interior;
  }

  // screen UI (emissive) and its spill on nearby interior surfaces
  if (uScreenOn > 0.5) {
    vec3 q = uScreenH * vec3(px, 1.0); vec2 suv = q.xy / q.z;
    vec2 edge = min(suv, 1.0 - suv);
    float inside = smoothstep(-0.002, 0.004, min(edge.x, edge.y * 3.2));
    vec4 ui = texture(uUI, suv);
    vec3 uiLin = toLin(ui.rgb);
    col = mix(col, col * 0.18 + uiLin * uScreenGain, inside);
    float dist = length(px - uScreenCenter) / uScreenRadius;
    float spill = exp(-dist * dist * 1.6) * (1.0 - inside) * interior;
    col += uSpillColor * spill * uSpill * (0.35 + 2.0 * luma(col));
  }

  // trail pulses advected along the plate's own long-exposure light trails
  if (uTrailOn > 0.5) {
    vec4 fl = texture(uFlow, uv);
    vec2 dir = normalize(fl.rg * 2.0 - 1.0 + 1e-5);
    float m = fl.b;
    float ph = dot(pp, dir) / uLambda - uBeatPos;
    float f = fract(ph);
    float dash = smoothstep(0.0, 0.05, f) * (1.0 - smoothstep(0.05, 0.42, f));
    col += uTrailColor * m * (uPulseGain * dash + uFlashGain);
  }

  // dark car bodies veil what is behind them
  for (int i = 0; i < MAXB; i++) {
    if (i >= uBN) break;
    vec2 q = abs(px - uBP[i].xy) - uBP[i].zw;
    float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
    float soft = max(uBP[i].w * 0.35, 1.0);
    col *= 1.0 - uBA[i] * (1.0 - smoothstep(-soft, soft, sd));
  }
  // point lights (tail lights etc.) with fog scattering and wet-road reflections
  vec3 lights = vec3(0.0);
  for (int i = 0; i < MAXL; i++) {
    if (i >= uLN) break;
    vec2 d = px - uLP[i].xy; float I = uLP[i].w;
    if (uLP[i].z < 0.0) { float rr = -uLP[i].z; lights += uLC[i].rgb * I * exp(-dot(d, d) / (2.0 * rr * rr)); continue; }
    float r = max(uLP[i].z, 0.5);
    float d2 = dot(d, d); float dl = sqrt(d2);
    float core = exp(-d2 / (2.0 * r * r));
    float glow = exp(-dl / (r * 3.0)) * 0.07;
    float wide = exp(-dl / (r * 9.0)) * 0.012;
    float flare = exp(-abs(d.y) / (r * 0.30)) * exp(-abs(d.x) / (r * 7.0)) * 0.012;
    float refl = 0.0;
    if (uLC[i].a > 0.0 && d.y > r) {
      float k = (d.y - r) / uLC[i].a;
      float rip = 0.55 + 0.9 * vnoise(vec2(px.x * 0.09, px.y * 0.42 - uTime * 3.0));
      refl = exp(-k * k * 1.8) * exp(-abs(d.x) / (r * 0.9)) * 0.16 * rip;
    }
    lights += uLC[i].rgb * I * (core + glow + wide + flare + refl);
  }
  for (int i = 0; i < MAXS; i++) {
    if (i >= uSN) break;
    float dd = segDist(px, uSA[i].xy, uSA[i].zw); float r = max(uSW[i].x, 0.5);
    lights += uSColor * uSW[i].y * (exp(-dd * dd / (2.0 * r * r)) + 0.12 * exp(-dd / (r * 5.0)));
  }
  vec4 em = texture(uEmit, vec2(px.x, px.y) / uRes);
  lights += toLin(em.rgb) * uEmitGain;
  col += lights;

  // volumetric-looking fog: two drifting layers, lit by what is behind them
  vec2 fa = pp * uFogA.y + uFogA.zw * uTime;
  vec2 fb = pp * uFogB.y + uFogB.zw * uTime;
  float na = smoothstep(0.30, 0.85, fbm(fa));
  float nb = smoothstep(0.35, 0.90, fbm(fb + 13.7));
  vec3 fogLight = uFogTint * (uFogLift + 2.2 * luma(blurred) + 1.2 * luma(blurredWide)) + lights * 0.18;
  float fogAmt = clamp(uFogA.x * na + uFogB.x * nb, 0.0, 0.85) * mix(1.0, 0.15, interior * uMaskOn);
  col = mix(col, fogLight, fogAmt);

  fragColor = vec4(col, 1.0);
}
`;

// Bloom: bright pass (scene + overlay glow), 13-tap downsample, tent upsample.
export const BRIGHT = COMMON + `
uniform sampler2D uScene; uniform sampler2D uOverlay; uniform sampler2D uFeed;
uniform float uThreshold; uniform float uKnee; uniform float uOverlayGlow; uniform float uFeedGlow;
void main(){
  vec3 c = texture(uScene, vUv).rgb;
  float l = max(c.r, max(c.g, c.b));
  float soft = clamp(l - uThreshold + uKnee, 0.0, 2.0 * uKnee); soft = soft * soft / (4.0 * uKnee + 1e-4);
  float w = max(soft, l - uThreshold) / max(l, 1e-4);
  vec3 b = c * w;
  vec4 ov = texture(uOverlay, vec2(vUv.x, 1.0 - vUv.y));
  b += toLin(ov.rgb) * uOverlayGlow;
  b += toLin(texture(uFeed, vec2(vUv.x, 1.0 - vUv.y)).rgb) * uFeedGlow;
  fragColor = vec4(b, 1.0);
}
`;

export const DOWN = COMMON + `
uniform sampler2D uSrc; uniform vec2 uSrcTexel;
void main(){
  vec2 t = uSrcTexel; vec2 u = vUv;
  vec3 a = texture(uSrc, u + t * vec2(-2, -2)).rgb, b = texture(uSrc, u + t * vec2(0, -2)).rgb, c = texture(uSrc, u + t * vec2(2, -2)).rgb;
  vec3 d = texture(uSrc, u + t * vec2(-2, 0)).rgb, e = texture(uSrc, u).rgb, f = texture(uSrc, u + t * vec2(2, 0)).rgb;
  vec3 g = texture(uSrc, u + t * vec2(-2, 2)).rgb, h = texture(uSrc, u + t * vec2(0, 2)).rgb, i = texture(uSrc, u + t * vec2(2, 2)).rgb;
  vec3 j = texture(uSrc, u + t * vec2(-1, -1)).rgb, k = texture(uSrc, u + t * vec2(1, -1)).rgb;
  vec3 l = texture(uSrc, u + t * vec2(-1, 1)).rgb, m = texture(uSrc, u + t * vec2(1, 1)).rgb;
  vec3 o = e * 0.125 + (a + c + g + i) * 0.03125 + (b + d + f + h) * 0.0625 + (j + k + l + m) * 0.125;
  fragColor = vec4(o, 1.0);
}
`;

export const UP = COMMON + `
uniform sampler2D uSrc; uniform sampler2D uBase; uniform vec2 uSrcTexel; uniform float uRadius;
void main(){
  vec2 t = uSrcTexel * uRadius; vec2 u = vUv;
  vec3 s = texture(uSrc, u + t * vec2(-1, -1)).rgb + 2.0 * texture(uSrc, u + t * vec2(0, -1)).rgb + texture(uSrc, u + t * vec2(1, -1)).rgb
         + 2.0 * texture(uSrc, u + t * vec2(-1, 0)).rgb + 4.0 * texture(uSrc, u).rgb + 2.0 * texture(uSrc, u + t * vec2(1, 0)).rgb
         + texture(uSrc, u + t * vec2(-1, 1)).rgb + 2.0 * texture(uSrc, u + t * vec2(0, 1)).rgb + texture(uSrc, u + t * vec2(1, 1)).rgb;
  fragColor = vec4(texture(uBase, u).rgb + s / 16.0, 1.0);
}
`;

// Final: grade, halation, print texture, overlay, grain, misregistration, dither.
export const FINAL = COMMON + `
uniform sampler2D uScene; uniform sampler2D uBloom; uniform sampler2D uOverlay; uniform sampler2D uFeed;
uniform float uFeedGain;
uniform float uExposure; uniform float uBloomGain; uniform float uHalation;
uniform vec3 uLift; uniform float uLiftAmt;
uniform float uHalftone; uniform float uCell; uniform float uGrain; uniform float uGrainOverlay;
uniform float uVignette; uniform float uCA; uniform float uMisreg; uniform float uFlash; uniform float uFade;
uniform float uSat; uniform float uRedKeep; uniform vec2 uWeave;

vec3 aces(vec3 x){ return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
float screenDot(vec2 p, float ang, float cell, float v){
  float s = sin(ang), c = cos(ang);
  vec2 q = mat2(c, -s, s, c) * p / cell;
  vec2 f = fract(q) - 0.5;
  float r = sqrt(clamp(v, 0.0, 1.0)) * 0.7071;
  float d = length(f);
  float aa = 0.75 / cell;
  return 1.0 - smoothstep(r - aa, r + aa, d);
}
vec3 gradeAt(vec2 uvb){
  vec3 c = texture(uScene, uvb).rgb * uExposure;
  vec4 fd = texture(uFeed, vec2(uvb.x, 1.0 - uvb.y));       // in-image signal: OSD, detector boxes
  c = c * (1.0 - fd.a) + toLin(fd.rgb) * uFeedGain;
  vec3 bl = texture(uBloom, uvb).rgb;
  c += bl * uBloomGain;
  c += bl * vec3(1.0, 0.32, 0.16) * uHalation;           // film halation around hot reds/whites
  float L = luma(c);
  c = mix(c, c * vec3(0.90, 1.0, 1.14), smoothstep(0.30, 0.0, L) * 0.35);  // cool shadows
  float red = smoothstep(0.02, 0.25, c.r - max(c.g, c.b));
  c = mix(vec3(luma(c)), c, mix(uSat, uRedKeep, red));
  c = aces(c);
  c = c * (1.0 - uLiftAmt) + uLift * uLiftAmt;
  return toSrgb(c);
}
void main(){
  vec2 px = pxCoord();
  vec2 uvb = vUv + uWeave / uRes;                          // gate weave, sub-pixel
  vec2 cd = vUv - 0.5;
  float r2 = dot(cd, cd) * 4.0;
  float ca = uCA * r2 * r2;
  vec2 mis = vec2(uMisreg / uRes.x, 0.0);
  vec3 d;
  d.r = gradeAt(uvb + cd * ca / 100.0 + mis).r;
  d.g = gradeAt(uvb).g;
  d.b = gradeAt(uvb - cd * ca / 100.0 - mis).b;
  // additive colour halftone: light dots on dark, so a night scene keeps its colour
  vec3 ht = vec3(screenDot(px, 0.2618, uCell, d.r), screenDot(px, 1.309, uCell, d.g), screenDot(px, 0.7854, uCell, d.b));
  d = mix(d, ht * max(d * 1.35, vec3(0.0)) + d * 0.35, uHalftone);
  float v = length(cd * vec2(1.0, 0.62)) * 1.45;
  d *= 1.0 - uVignette * v * v;
  // overlay (premultiplied sRGB), shares the misregistration on hits
  vec2 ot = vec2(vUv.x, 1.0 - vUv.y);
  vec4 ov = texture(uOverlay, ot);
  float oR = texture(uOverlay, ot + vec2(mis.x * 1.4, 0.0)).r;
  float oB = texture(uOverlay, ot - vec2(mis.x * 1.4, 0.0)).b;
  ov.rgb = vec3(oR, ov.g, oB);
  d = d * (1.0 - ov.a) + ov.rgb;
  d += uFlash;
  // film grain: clumped, strongest in the mid tones, lighter on graphics
  float g = (vnoise(px / 1.35 + uFrame * vec2(37.1, 17.3)) - 0.5) * 1.6 + (hash12(px + uFrame * 7.7) - 0.5) * 0.7;
  float lm = luma(d);
  float amp = uGrain * (0.45 + 0.9 * (1.0 - abs(lm * 2.0 - 1.0))) * mix(1.0, uGrainOverlay, ov.a);
  d += g * amp;
  d *= 1.0 - uFade;
  d += (hash12(px + uFrame * 3.1) - 0.5) / 255.0;           // dither before 8-bit quantisation
  fragColor = vec4(clamp(d, 0.0, 1.0), 1.0);
}
`;
