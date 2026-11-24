(() => {
  // motion-kit/src/gl.js
  function createGL(canvas) {
    const gl = canvas.getContext("webgl2", {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: true,
      powerPreference: "high-performance"
    });
    if (!gl) throw new Error("WebGL2 unavailable");
    const floatRT = !!gl.getExtension("EXT_color_buffer_float");
    gl.getExtension("OES_texture_float_linear");
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    const info = {
      renderer: (() => {
        const ext = gl.getExtension("WEBGL_debug_renderer_info");
        return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      })(),
      floatRT
    };
    return { gl, vao, info };
  }
  var VS = `#version 300 es
layout(location=0) in vec2 aPos;
out vec2 vUv;
void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;
  function program(gl, fsSource, name = "program") {
    const compile = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        const log = gl.getShaderInfoLog(s);
        const numbered = src.split("\n").map((l, i) => `${i + 1}: ${l}`).join("\n");
        throw new Error(`${name} shader compile failed:
${log}
${numbered}`);
      }
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, compile(gl.VERTEX_SHADER, VS));
    gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fsSource));
    gl.bindAttribLocation(p, 0, "aPos");
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(`${name} link failed: ${gl.getProgramInfoLog(p)}`);
    const uniforms = {};
    const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) {
      const u = gl.getActiveUniform(p, i);
      const base = u.name.replace(/\[0\]$/, "");
      uniforms[base] = { loc: gl.getUniformLocation(p, u.name), type: u.type, size: u.size };
    }
    return { p, uniforms, name };
  }
  function use(gl, prog, values = {}, textures = {}) {
    gl.useProgram(prog.p);
    let unit = 0;
    for (const [k, tex] of Object.entries(textures)) {
      const u = prog.uniforms[k];
      if (!u) continue;
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.uniform1i(u.loc, unit);
      unit++;
    }
    for (const [k, v] of Object.entries(values)) {
      const u = prog.uniforms[k];
      if (!u) continue;
      const arr = typeof v === "number" ? [v] : v;
      switch (u.type) {
        case gl.FLOAT:
          gl.uniform1fv(u.loc, arr);
          break;
        case gl.FLOAT_VEC2:
          gl.uniform2fv(u.loc, arr);
          break;
        case gl.FLOAT_VEC3:
          gl.uniform3fv(u.loc, arr);
          break;
        case gl.FLOAT_VEC4:
          gl.uniform4fv(u.loc, arr);
          break;
        case gl.INT:
        case gl.BOOL:
          gl.uniform1iv(u.loc, arr.map((x) => x | 0));
          break;
        case gl.FLOAT_MAT3:
          gl.uniformMatrix3fv(u.loc, false, arr);
          break;
        default:
          throw new Error(`uniform ${k}: unsupported type ${u.type}`);
      }
    }
  }
  function texture(gl, source, { mipmap = false, linear = true, wrap = "clamp", flipY = false } = {}) {
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, flipY);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, source);
    const w = wrap === "repeat" ? gl.REPEAT : gl.CLAMP_TO_EDGE;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, w);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, w);
    if (mipmap) gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mipmap ? gl.LINEAR_MIPMAP_LINEAR : linear ? gl.LINEAR : gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, linear ? gl.LINEAR : gl.NEAREST);
    return t;
  }
  function updateTexture(gl, t, source) {
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, source);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  }
  function target(gl, w, h, { float = true } = {}) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    if (float) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    else gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) throw new Error(`framebuffer incomplete ${status}`);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { tex, fbo, w, h };
  }
  function draw(gl, rt) {
    if (rt) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, rt.fbo);
      gl.viewport(0, 0, rt.w, rt.h);
    } else {
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    }
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  // motion-kit/src/shaders.js
  var COMMON = `#version 300 es
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
  var SCENE = COMMON + `
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
uniform vec3 uFlowVP; // exterior forward flow: vp.x, vp.y (plate px), scale (legacy radial zoom)
uniform vec4 uRoad;    // ground-plane forward travel: vp.x, horizon y (plate px), speed (1/px per s), cycle (s)
uniform float uRoadOn;
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
// Sample the plate as if the camera travelled d forward over a ground (below the horizon) and a
// mirrored ceiling plane (lamps, fog above it): depth \u221D 1/(y - yh); travelling d samples farther points.
vec2 roadFlow(vec2 pp, float d){
  float dy = pp.y - uRoad.y;
  float s = sign(dy);
  if (s < 0.0) d *= 0.5;                                  // lamps and fog above the horizon travel less
  float a = max(abs(dy), 1.5);
  float a2 = 1.0 / (1.0 / a + d);
  return vec2(uRoad.x + (pp.x - uRoad.x) * (a2 / a), uRoad.y + s * a2);
}
vec3 exteriorTravel(vec2 pp){
  vec3 acc = vec3(0.0);
  for (int ph = 0; ph < 2; ph++) {
    float f = fract(uTime / uRoad.w + 0.5 * float(ph));
    float w = 1.0 - abs(2.0 * f - 1.0);                  // two phases always sum to 1
    float d = f * uRoad.z * uRoad.w;
    vec3 c = vec3(0.0);
    for (int k = 0; k < 4; k++) {                         // shutter blur along the flow
      float dk = d - float(k) * uRoad.z * 0.005;
      c += toLin(sampleCR(uPlate, roadFlow(pp, max(dk, 0.0)) / uPlateSize, uPlateSize).rgb);
    }
    acc += w * c * 0.25;
  }
  return acc;
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
  vec3 col = toLin(sampleCR(uPlate, uv, uPlateSize).rgb);
  if (uRoadOn > 0.5 && interior < 0.999) col = mix(exteriorTravel(outToPlate(px)), col, interior);
  col *= uPlateGain * uPlateTint;
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
  var BRIGHT = COMMON + `
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
  var DOWN = COMMON + `
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
  var UP = COMMON + `
uniform sampler2D uSrc; uniform sampler2D uBase; uniform vec2 uSrcTexel; uniform float uRadius;
void main(){
  vec2 t = uSrcTexel * uRadius; vec2 u = vUv;
  vec3 s = texture(uSrc, u + t * vec2(-1, -1)).rgb + 2.0 * texture(uSrc, u + t * vec2(0, -1)).rgb + texture(uSrc, u + t * vec2(1, -1)).rgb
         + 2.0 * texture(uSrc, u + t * vec2(-1, 0)).rgb + 4.0 * texture(uSrc, u).rgb + 2.0 * texture(uSrc, u + t * vec2(1, 0)).rgb
         + texture(uSrc, u + t * vec2(-1, 1)).rgb + 2.0 * texture(uSrc, u + t * vec2(0, 1)).rgb + texture(uSrc, u + t * vec2(1, 1)).rgb;
  fragColor = vec4(texture(uBase, u).rgb + s / 16.0, 1.0);
}
`;
  var FINAL = COMMON + `
uniform sampler2D uScene; uniform sampler2D uBloom; uniform sampler2D uOverlay; uniform sampler2D uFeed;
uniform float uFeedGain;
uniform float uExposure; uniform float uBloomGain; uniform float uHalation;
uniform vec3 uLift; uniform float uLiftAmt;
uniform float uHalftone; uniform float uCell; uniform float uGrain; uniform float uGrainOverlay;
uniform float uVignette; uniform float uCA; uniform float uMisreg; uniform float uFlash; uniform float uFade;
uniform float uSat; uniform float uRedKeep; uniform vec2 uWeave;
uniform float uInvert;

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
  float r2 = dot(cd, cd) * 2.0;                             // 0 centre .. 1 corner
  vec2 caOff = normalize(cd + 1e-6) * uCA * r2 / uRes;      // uCA px at the corners
  vec2 mis = vec2(uMisreg / uRes.x, 0.0);
  vec3 d;
  d.r = gradeAt(uvb + caOff + mis).r;
  d.g = gradeAt(uvb).g;
  d.b = gradeAt(uvb - caOff - mis).b;
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
  // luminance inversion (EV's white-ground turn): light becomes dark and back, hue kept; 0 = off
  d = mix(d, clamp(d + vec3(1.0 - 2.0 * luma(d)), 0.0, 1.0), uInvert);
  // film grain: clumped, strongest in the mid tones, lighter on graphics
  float g = (vnoise(px / 1.35 + uFrame * vec2(37.1, 17.3)) - 0.5) * 1.6 + (hash12(px + uFrame * 7.7) - 0.5) * 0.7;
  float lm = luma(d);
  float amp = uGrain * (0.45 + 0.9 * (1.0 - abs(lm * 2.0 - 1.0))) * mix(1.0, uGrainOverlay, ov.a);
  amp *= 0.45 + 0.55 * smoothstep(0.02, 0.20, lm);         // deep darks get less grain (survives platform transcodes)
  d += g * amp;
  d *= 1.0 - uFade;
  d += (hash12(px + uFrame * 3.1) - 0.5) / 255.0;           // dither before 8-bit quantisation
  fragColor = vec4(clamp(d, 0.0, 1.0), 1.0);
}
`;

  // motion-kit/src/math.js
  function hash1(n) {
    let x = (n | 0) ^ 2654435769;
    x = Math.imul(x ^ x >>> 16, 2246822507);
    x = Math.imul(x ^ x >>> 13, 3266489909);
    x ^= x >>> 16;
    return (x >>> 0) / 4294967296;
  }
  var hash2 = (a, b) => hash1(Math.imul(a | 0, 73856093) ^ Math.imul(b | 0, 19349663));
  function noise1(x, seed = 0) {
    const i = Math.floor(x), f = x - i;
    const u = f * f * (3 - 2 * f);
    const a = hash2(i, seed) * 2 - 1, b = hash2(i + 1, seed) * 2 - 1;
    return a + (b - a) * u;
  }
  var clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  var lerp = (a, b, t) => a + (b - a) * t;
  var easeOutCubic = (t) => 1 - Math.pow(1 - clamp(t), 3);
  var easeInOutCubic = (t) => {
    t = clamp(t);
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };

  // motion-kit/src/draw2d.js
  function canvas2d(w, h) {
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    const ctx = c.getContext("2d", { willReadFrequently: true, alpha: true });
    return { c, ctx };
  }
  function reset(ctx) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
    ctx.filter = "none";
    ctx.shadowBlur = 0;
    ctx.shadowColor = "transparent";
    ctx.letterSpacing = "0px";
    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "left";
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/type.js
  var FONT = { din: "XDIN", dinB: "XDINB", nim: "XNIM", nimR: "XNIMR", mono: "XMONO", monoR: "XMONOR", monoS: "XMONOS" };
  var INK = { warm: "#F3EEE4", paper: "#ECE8DE", dark: "#17191C", amber: "#F2B134", bone: "#E8E4DA", signal: "#D7263D" };
  function setFont(ctx, fam, size, track = 0) {
    ctx.font = `${size}px "${fam}"`;
    ctx.letterSpacing = `${track}px`;
  }
  var since = (k, ts) => k.f - k.fo(ts);
  var shown = (k, ts) => k.f >= k.fo(ts);
  function layoutWords(ctx, words, fam, size, track, space) {
    setFont(ctx, fam, size, track);
    const xs = [];
    let x = 0;
    for (const w of words) {
      xs.push(x);
      x += ctx.measureText(w.text).width + space;
    }
    return { xs, w: x - space };
  }
  function drawWords(k, ctx, words, x, y, fam, size, {
    track = 0,
    space = size * 0.28,
    color = INK.warm,
    shadow = null,
    align = "left",
    pop = true,
    upper = false,
    dim = null
  } = {}) {
    const ws = upper ? words.map((w) => ({ ...w, text: w.text.toUpperCase() })) : words;
    const L = layoutWords(ctx, ws, fam, size, track, space);
    const x0 = align === "center" ? x - L.w / 2 : align === "right" ? x - L.w : x;
    ctx.save();
    setFont(ctx, fam, size, track);
    if (shadow) {
      ctx.shadowColor = shadow.color;
      ctx.shadowBlur = shadow.blur;
      ctx.shadowOffsetY = shadow.dy || 0;
    }
    ws.forEach((w, i) => {
      const a = since(k, w.start);
      if (a < 0) {
        if (dim) {
          ctx.globalAlpha = dim;
          ctx.fillStyle = color;
          ctx.fillText(w.text, x0 + L.xs[i], y);
        }
        return;
      }
      const e = pop ? easeOutCubic(clamp((a + 1) / 3)) : 1;
      ctx.globalAlpha = pop ? clamp(0.55 + 0.45 * e) : 1;
      ctx.fillStyle = color;
      ctx.fillText(w.text, x0 + L.xs[i], y + (1 - e) * size * 0.08);
      k.mark(w.li, w.wi);
    });
    ctx.restore();
    return { x0, w: L.w, xs: L.xs.map((v) => v + x0) };
  }
  function slamWord(k, ctx, text, ts, x, y, size, {
    color = INK.warm,
    align = "left",
    track = -1,
    shadowA = 0.5,
    fam = FONT.din,
    marks = []
  } = {}) {
    const a = since(k, ts);
    if (a < 0) return null;
    setFont(ctx, fam, size, track);
    const w = ctx.measureText(text).width;
    const x0 = align === "center" ? x - w / 2 : align === "right" ? x - w : x;
    const s = a >= 3 ? 1 : [1.16, 1.06, 1.015][a];
    const cx = x0 + w / 2, cy = y - size * 0.35;
    ctx.save();
    if (a < 2) {
      ctx.save();
      ctx.globalAlpha = 0.18;
      ctx.translate(cx, cy);
      ctx.scale(s * 1.07, s * 1.07);
      ctx.translate(-cx, -cy);
      ctx.fillStyle = color;
      ctx.fillText(text, x0, y);
      ctx.restore();
    }
    ctx.translate(cx, cy);
    ctx.scale(s, s);
    ctx.translate(-cx, -cy);
    ctx.shadowColor = `rgba(0,0,0,${shadowA})`;
    ctx.shadowBlur = size * 0.11;
    ctx.shadowOffsetY = size * 0.035;
    ctx.fillStyle = color;
    ctx.fillText(text, x0, y);
    ctx.restore();
    for (const [li, wi] of marks) k.mark(li, wi);
    return { x0, w };
  }
  function micro(ctx, text, x, y, {
    size = 12,
    track = 2.2,
    color = "rgba(236,232,222,0.78)",
    align = "left",
    fam = FONT.mono
  } = {}) {
    ctx.save();
    setFont(ctx, fam, size, track);
    ctx.textAlign = align;
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    ctx.restore();
  }
  function typed(text, a, perTick = 2) {
    if (a < 0) return "";
    return text.slice(0, Math.min(text.length, (Math.floor(a / 2) + 1) * perTick));
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/devices.js
  var W = 1920;
  var H = 1080;
  var FLAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-";
  function flap(prev, next, a, f) {
    if (a < 0) return prev;
    const ticks = Math.floor(a / 2);
    const n = Math.max(prev.length, next.length);
    let out2 = "";
    for (let i = 0; i < n; i++) {
      const ch = next[i] || " ";
      const settle = 1 + i % 4;
      if (ticks >= settle || ch === " " || ch === (prev[i] || " ")) out2 += ch;
      else out2 += FLAP[Math.floor(hash2(i * 31 + ticks, f >> 1) * FLAP.length)];
    }
    return out2.replace(/\s+$/, "");
  }
  function hairline(ctx, x0, y0, x1, y1, color = "rgba(236,232,222,0.8)", w = 1) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
    ctx.restore();
  }
  function leader(ctx, a, b, age, { dur = 4, color = "rgba(236,232,222,0.85)", dot = true } = {}) {
    if (age < 0) return;
    const e = easeOutCubic(clamp((age + 1) / dur));
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e);
    ctx.stroke();
    if (dot) {
      ctx.beginPath();
      ctx.arc(a[0], a[1], 3, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
  function brackets(ctx, x0, y0, x1, y1, age, { color = "rgba(236,232,222,0.9)", arm = 14, w = 1.5 } = {}) {
    if (age < 0) return;
    const g = age < 2 ? 1.06 - 0.03 * age : 1;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const hx = (x1 - x0) / 2 * g, hy = (y1 - y0) / 2 * g;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
      const x = cx + sx * hx, y = cy + sy * hy;
      ctx.beginPath();
      ctx.moveTo(x - sx * arm, y);
      ctx.lineTo(x, y);
      ctx.lineTo(x, y - sy * arm);
      ctx.stroke();
    }
    ctx.restore();
  }
  function pagerIcon(ctx, x, y, s = 1, { body = "rgba(236,232,222,0.92)", lcd = "rgba(20,22,24,0.9)" } = {}) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = body;
    ctx.beginPath();
    ctx.roundRect(0, 0, 22, 14, 2.5);
    ctx.fill();
    ctx.fillStyle = lcd;
    ctx.fillRect(3, 3, 12, 6);
    ctx.fillRect(17, 4, 2.5, 6);
    ctx.restore();
  }
  var TICKET = [
    { at: 0, id: "INC-0804", sev: "SEV-MED", title: "BILLBOARD BEHIND A TREE", status: "PAGED" },
    { at: 32.934, id: "INC-0902", sev: "SEV-MED", title: "BUS STOP", status: "PAGED" },
    { at: 36.1999, id: "INC-0902", sev: "SEV-MED", title: "FREEWAY", status: "PAGED" },
    { at: 40.7859, id: "ALL HANDS", sev: "SEV-MED", title: "RUNWAY ONE", status: "PAGED" },
    { at: 42.769, id: "ALL HANDS", sev: "SEV-HIGH", title: "RUNWAY ONE", status: "PAGED" }
  ];
  function ticketCard(k, ctx, { accent = INK.amber, alpha = 1, narrow = false, icons = true } = {}) {
    const s = k.s;
    let i = 0;
    for (let j = 0; j < TICKET.length; j++) if (shown(k, TICKET[j].at) || TICKET[j].at === 0) i = j;
    const cur = TICKET[i], prev = TICKET[Math.max(0, i - 1)];
    const a = i === 0 ? 99 : since(k, cur.at);
    const white = shown(k, 39.897);
    const wa = since(k, 39.897);
    const x = 60, y = 56, w = narrow ? 268 : 382, h = narrow ? 82 : 104;
    ctx.save();
    ctx.globalAlpha = alpha;
    const paper = white ? INK.paper : "rgba(12,14,16,0.74)";
    const ink = white ? INK.dark : "rgba(240,236,228,0.95)";
    const sub = white ? "rgba(23,25,28,0.62)" : "rgba(240,236,228,0.6)";
    ctx.fillStyle = "rgba(12,14,16,0.74)";
    ctx.fillRect(x, y, w, h);
    if (white) {
      ctx.fillStyle = paper;
      ctx.fillRect(x, y, w, h * clamp((wa + 1) / 3));
    }
    ctx.strokeStyle = white ? "rgba(23,25,28,0.5)" : accent;
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    ctx.fillStyle = white ? INK.dark : accent;
    ctx.fillRect(x, y, 5, h);
    const id = flap(prev.id, cur.id, a, k.f), sev = flap(prev.sev, cur.sev, a, k.f), title = flap(prev.title, cur.title, a, k.f);
    setFont(ctx, FONT.monoS, 19, 1.5);
    ctx.fillStyle = ink;
    ctx.fillText(id, x + 20, y + 30);
    setFont(ctx, FONT.monoS, 13, 1.6);
    const sw = ctx.measureText(sev).width + 18;
    ctx.strokeStyle = ink;
    ctx.strokeRect(x + w - 16 - sw + 0.5, y + 13.5, sw, 22);
    ctx.fillText(sev, x + w - 16 - sw + 9, y + 29);
    micro(ctx, "SHOW SCALE", x + w - 16, y + 50, { size: 9, track: 1.8, color: sub, align: "right" });
    setFont(ctx, FONT.mono, narrow ? 12 : 15, 1.2);
    ctx.fillStyle = ink;
    ctx.fillText(title, x + 20, y + (narrow ? 54 : 60));
    micro(ctx, `STATUS \xB7 ${cur.status}`, x + 20, y + (narrow ? 72 : 88), { size: narrow ? 10 : 12, track: 2, color: sub });
    ctx.restore();
    const n = !icons ? 0 : 2 + k.snaresBetween(44.9422, Math.min(s, 50.933));
    for (let j = 0; j < n; j++) {
      const born = j < 2 ? -99 : k.snareTimes(44.9422, 50.933)[j - 2];
      const ag = born < 0 ? 99 : since(k, born);
      const sc = ag < 2 ? 1.25 - 0.12 * ag : 1;
      pagerIcon(ctx, x + j % 14 * 27, y + h + 12 + Math.floor(j / 14) * 20, sc * 0.9);
    }
    const st = since(k, 53.767);
    if (st >= 0) {
      const sc = st >= 3 ? 1 : [1.45, 1.12, 1.03][st];
      ctx.save();
      ctx.translate(x + w * 0.62, y + h * 0.58);
      ctx.rotate(-0.13);
      ctx.scale(sc, sc);
      ctx.globalAlpha = st < 1 ? 0.7 : 0.92;
      ctx.strokeStyle = INK.dark;
      ctx.lineWidth = 3;
      ctx.strokeRect(-104, -26, 208, 52);
      ctx.lineWidth = 1;
      ctx.strokeRect(-98, -20, 196, 40);
      setFont(ctx, FONT.din, 40, 1);
      ctx.fillStyle = INK.dark;
      ctx.textAlign = "center";
      ctx.fillText("ALL HANDS", 0, 14);
      ctx.globalCompositeOperation = "destination-out";
      for (let q = 0; q < 70; q++) {
        ctx.globalAlpha = 0.5 * hash2(q, 7);
        ctx.fillRect(-104 + hash2(q, 3) * 208, -26 + hash2(q, 5) * 52, 1 + hash2(q, 9) * 4, 1 + hash2(q, 11) * 2);
      }
      ctx.restore();
    }
  }
  var CHAPTERS = [{ at: 0, text: "02 STREET LOOKS" }, { at: 40.7859, text: "03 RUNWAY ONE \xB7 ALL HANDS" }];
  function frameChrome(k, ctx) {
    ctx.save();
    ctx.fillStyle = "rgba(236,232,222,0.7)";
    for (const [x, y2] of [[28, 28], [W - 28, 28], [28, H - 28], [W - 28, H - 28]]) {
      ctx.fillRect(x - 7, y2, 15, 1);
      ctx.fillRect(x, y2 - 7, 1, 15);
    }
    let i = 0;
    for (let j = 0; j < CHAPTERS.length; j++) if (shown(k, CHAPTERS[j].at) || j === 0) i = j;
    const a = i === 0 ? 99 : since(k, CHAPTERS[i].at);
    const txt = flap(CHAPTERS[Math.max(0, i - 1)].text, CHAPTERS[i].text, a, k.f);
    setFont(ctx, FONT.monoS, 15, 0);
    const cw = 15, gap = 2, x1 = W - 60, y = 54;
    const n = txt.length;
    for (let c = 0; c < n; c++) {
      const xx = x1 - (n - c) * (cw + gap);
      const ch = txt[c];
      if (ch === " ") continue;
      ctx.fillStyle = "rgba(14,16,18,0.78)";
      ctx.fillRect(xx, y, cw, 23);
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(xx, y + 11, cw, 1);
      ctx.fillStyle = "rgba(240,236,228,0.95)";
      ctx.textAlign = "center";
      ctx.fillText(ch, xx + cw / 2, y + 17);
    }
    ctx.textAlign = "left";
    micro(ctx, "IRIS \xB7 EP01 \xB7 ALL HANDS", x1, y - 10, { size: 10, track: 2.4, align: "right", color: "rgba(236,232,222,0.62)" });
    const sec = k.s;
    const mm = String(Math.floor(sec / 60)).padStart(2, "0"), ss = (sec % 60).toFixed(2).padStart(5, "0");
    hairline(ctx, W - 470, H - 50.5, W - 60, H - 50.5, "rgba(236,232,222,0.35)");
    micro(ctx, `INCIDENT WEEK \xB7 SONG ${mm}:${ss} \xB7 BAR ${k.barNo()}`, W - 60, H - 34, {
      size: 11,
      track: 2.2,
      align: "right",
      color: "rgba(236,232,222,0.7)"
    });
    ctx.restore();
  }
  function tagLabel(ctx, x, y, age, { tag, sub, source, rot = -0.06 }) {
    if (age < 0) return;
    const e = easeOutCubic(clamp((age + 1) / 4));
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot * e);
    ctx.translate(0, (1 - e) * -14);
    ctx.globalAlpha = clamp(0.3 + e);
    ctx.shadowColor = "rgba(0,0,0,0.45)";
    ctx.shadowBlur = 16;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = INK.paper;
    ctx.beginPath();
    ctx.roundRect(0, 0, 300, 150, 3);
    ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.fillStyle = "rgba(23,25,28,0.85)";
    ctx.beginPath();
    ctx.arc(150, 13, 4.5, 0, Math.PI * 2);
    ctx.fill();
    setFont(ctx, FONT.monoS, 29, 0);
    ctx.fillStyle = INK.dark;
    ctx.fillText(typed(tag, age, 3), 18, 62);
    micro(ctx, typed(sub, age - 4, 4), 18, 90, { size: 12, track: 1.6, color: INK.dark });
    ctx.fillStyle = INK.dark;
    let bx = 18;
    for (let q = 0; q < 46 && bx < 200; q++) {
      const bw = 1 + Math.floor(hash2(q, 41) * 3);
      if (hash2(q, 43) > 0.38) ctx.fillRect(bx, 104, bw, 22);
      bx += bw + 1;
    }
    micro(ctx, source, 18, 141, { size: 9, track: 1.2, color: "rgba(23,25,28,0.75)" });
    ctx.fillStyle = INK.amber;
    ctx.fillRect(282, 104, 6, 22);
    ctx.restore();
  }
  function classifier(k, ctx, x, y, rows, { title, source, width = 420, accent = INK.amber, dark = true } = {}) {
    const shownRows = rows.filter((r) => shown(k, r.at));
    if (!shownRows.length) return;
    const a0 = since(k, rows[0].at);
    const e = easeOutCubic(clamp((a0 + 1) / 3));
    const rh = 30, h = 46 + rows.length * rh + (source ? 22 : 0);
    ctx.save();
    ctx.globalAlpha = e;
    ctx.fillStyle = dark ? "rgba(10,12,14,0.62)" : "rgba(236,232,222,0.88)";
    ctx.fillRect(x, y, width, h * e);
    ctx.strokeStyle = "rgba(236,232,222,0.55)";
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, width - 1, h * e - 1);
    micro(ctx, title, x + 14, y + 22, { size: 11, track: 2.4, color: "rgba(236,232,222,0.7)" });
    hairline(ctx, x + 14, y + 32.5, x + width - 14, y + 32.5, "rgba(236,232,222,0.3)");
    rows.forEach((r, i) => {
      const a = since(k, r.at);
      if (a < 0) return;
      const yy = y + 58 + i * rh;
      setFont(ctx, FONT.mono, 16, 1.2);
      ctx.fillStyle = "rgba(240,236,228,0.95)";
      ctx.fillText(typed(r.k, a, 4), x + 14, yy);
      const v = a >= 2 ? r.v : "";
      setFont(ctx, FONT.monoS, 16, 1.4);
      ctx.fillStyle = r.hot ? accent : "rgba(240,236,228,0.95)";
      ctx.textAlign = "right";
      ctx.fillText(v, x + width - 14, yy);
      ctx.textAlign = "left";
      if (r.lyric) for (const [li, wi] of r.lyric) k.mark(li, wi);
    });
    if (source) micro(ctx, source, x + 14, y + h - 10, { size: 9, track: 1.2, color: "rgba(236,232,222,0.6)" });
    ctx.restore();
  }
  function hypnogram(k, ctx, x, y, { t0, drop, w = 360, h = 150 }) {
    const a0 = since(k, t0);
    if (a0 < 0) return;
    const e = easeOutCubic(clamp((a0 + 1) / 3));
    ctx.save();
    ctx.globalAlpha = e;
    ctx.fillStyle = "rgba(10,12,14,0.62)";
    ctx.fillRect(x, y, w, h + 50);
    ctx.strokeStyle = "rgba(236,232,222,0.5)";
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h + 49);
    micro(ctx, "SLEEP \xB7 LAST NIGHT", x + 14, y + 22, { size: 12, track: 2.4, color: "rgba(240,236,228,0.92)" });
    micro(ctx, "ILLUSTRATIVE CURVE", x + w - 14, y + 22, { size: 9, track: 1.6, align: "right", color: "rgba(236,232,222,0.55)" });
    const stages = ["AWAKE", "REM", "LIGHT", "DEEP"];
    const gx = x + 74, gw = w - 92, gy = y + 44, gh = h - 20;
    stages.forEach((s, i) => {
      const yy = gy + i * gh / 3;
      micro(ctx, s, x + 14, yy + 4, { size: 9, track: 1.2, color: s === "AWAKE" ? INK.bone : "rgba(236,232,222,0.55)" });
      hairline(ctx, gx, yy + 0.5, gx + gw, yy + 0.5, "rgba(236,232,222,0.14)");
    });
    const seq = [2, 3, 3, 2, 1, 2, 3, 3, 2, 2, 1, 2, 3, 2, 1, 1, 2];
    const n = Math.min(seq.length, Math.floor(a0 / 3) + 1);
    const dropped = shown(k, drop);
    ctx.strokeStyle = "rgba(240,236,228,0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    const step = gw / (seq.length + 2);
    for (let i = 0; i < n; i++) {
      const xx = gx + i * step, yy = gy + seq[i] * gh / 3;
      if (i === 0) ctx.moveTo(xx, yy);
      else ctx.lineTo(xx, yy);
      ctx.lineTo(xx + step, yy);
    }
    ctx.stroke();
    if (dropped) {
      const da = since(k, drop);
      const lastX = gx + n * step, lastY = gy + seq[n - 1] * gh / 3;
      const ey = lastY + (gy - lastY) * easeOutCubic(clamp((da + 1) / 2));
      ctx.strokeStyle = INK.bone;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(lastX, lastY);
      ctx.lineTo(lastX, ey);
      ctx.lineTo(gx + gw, ey);
      ctx.stroke();
      if (da >= 1) {
        setFont(ctx, FONT.din, 44, 0.5);
        ctx.fillStyle = INK.warm;
        ctx.textAlign = "right";
        ctx.fillText("AWAKE", x + w - 14, y + h + 38);
        ctx.textAlign = "left";
      }
    }
    ctx.restore();
  }
  function gauge(k, ctx, cx, cy, r, { at, full, label, from, to, fill }) {
    const a = since(k, at);
    if (a < 0) return;
    const e = easeOutCubic(clamp((a + 1) / 3));
    const p = clamp(k.sixteenthsBetween(at, Math.min(k.s, full)) / Math.max(1, k.sixteenthsBetween(at, full)));
    ctx.save();
    ctx.globalAlpha = e;
    ctx.lineCap = "butt";
    ctx.strokeStyle = "rgba(236,232,222,0.35)";
    ctx.lineWidth = r * 0.16;
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, 2 * Math.PI);
    ctx.stroke();
    ctx.strokeStyle = INK.warm;
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * p);
    ctx.stroke();
    for (let i = 0; i <= 8; i++) {
      const t = Math.PI + Math.PI * i / 8;
      hairline(
        ctx,
        cx + Math.cos(t) * r * 1.12,
        cy + Math.sin(t) * r * 1.12,
        cx + Math.cos(t) * r * 1.22,
        cy + Math.sin(t) * r * 1.22,
        "rgba(236,232,222,0.7)",
        1.2
      );
    }
    const nt = Math.PI + Math.PI * p;
    ctx.strokeStyle = INK.warm;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(nt) * r * 0.86, cy + Math.sin(nt) * r * 0.86);
    ctx.stroke();
    micro(ctx, from, cx - r * 1.2, cy + 22, { size: 12, track: 2, color: "rgba(240,236,228,0.85)", align: "center" });
    micro(ctx, to, cx + r * 1.2, cy + 22, { size: 12, track: 2, color: "rgba(240,236,228,0.85)", align: "center" });
    micro(ctx, label, cx, cy - r * 0.42, { size: 13, track: 2.6, color: "rgba(240,236,228,0.95)", align: "center", fam: FONT.monoS });
    if (p >= 1) {
      setFont(ctx, FONT.din, r * 0.42, 0.5);
      ctx.fillStyle = INK.warm;
      ctx.textAlign = "center";
      ctx.fillText(fill, cx, cy + r * 0.62);
    }
    ctx.restore();
  }
  function callScreen(k, ctx, x, y, { at, takeAt, flashAt, caller, label, decline }) {
    const a = since(k, at);
    if (a < 0) return;
    const e = easeOutCubic(clamp((a + 1) / 4));
    const w = 300, h = 520;
    ctx.save();
    ctx.translate(x, y + (1 - e) * 24);
    ctx.rotate(-0.05);
    ctx.globalAlpha = e;
    ctx.shadowColor = "rgba(0,0,0,0.5)";
    ctx.shadowBlur = 30;
    ctx.shadowOffsetY = 10;
    ctx.fillStyle = "rgba(16,18,21,0.9)";
    ctx.beginPath();
    ctx.roundRect(0, 0, w, h, 34);
    ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.strokeStyle = "rgba(236,232,222,0.35)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    const taken = shown(k, takeAt);
    micro(ctx, taken ? "ON CALL \xB7 00:00" : label, w / 2, 92, {
      size: 13,
      track: 2.2,
      align: "center",
      fam: FONT.monoS,
      color: taken ? INK.bone : "rgba(240,236,228,0.8)"
    });
    setFont(ctx, FONT.nim, 40, 0);
    ctx.fillStyle = INK.warm;
    ctx.textAlign = "center";
    ctx.fillText("Incident", w / 2, 150);
    ctx.fillText("Week", w / 2, 196);
    micro(ctx, caller, w / 2, 228, { size: 11, track: 2.4, align: "center", color: "rgba(236,232,222,0.55)" });
    const by = h - 110;
    ctx.fillStyle = "rgba(120,122,126,0.35)";
    ctx.beginPath();
    ctx.arc(78, by, 36, 0, Math.PI * 2);
    ctx.fill();
    hairline(ctx, 54, by + 24, 102, by - 24, "rgba(236,232,222,0.7)", 2);
    micro(ctx, decline, 78, by + 62, { size: 10, track: 1.8, align: "center", color: "rgba(236,232,222,0.7)" });
    const ta = since(k, takeAt);
    const press = ta >= 0 ? ta < 3 ? 0.9 + 0.033 * ta : 1 : 1;
    ctx.fillStyle = taken ? INK.warm : "rgba(236,232,222,0.85)";
    ctx.beginPath();
    ctx.arc(w - 78, by, 36 * press, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = INK.dark;
    ctx.font = `600 13px "${FONT.monoS}"`;
    ctx.letterSpacing = "1.5px";
    ctx.fillText(taken ? "TAKEN" : "ACCEPT", w - 78, by + 5);
    micro(ctx, "ANSWER", w - 78, by + 62, { size: 10, track: 1.8, align: "center", color: "rgba(236,232,222,0.7)" });
    const fa = since(k, flashAt);
    if (fa >= 0 && fa < 8) {
      ctx.globalAlpha = e * 0.5 * Math.exp(-fa / 2.2);
      ctx.fillStyle = "#FFFFFF";
      ctx.beginPath();
      ctx.roundRect(0, 0, w, h, 34);
      ctx.fill();
    }
    ctx.restore();
  }
  function pagerStack(k, ctx, x1, yBase, { from, to, label }) {
    const n = Math.min(40, k.sixteenthsBetween(from, Math.min(k.s, to)) + 1);
    if (!shown(k, from)) return;
    for (let j = 0; j < n; j++) {
      const col = j % 5, row = Math.floor(j / 5);
      const born = k.sixteenthAt(from, j);
      const ag = since(k, born);
      const sc = ag < 2 ? 1.3 - 0.15 * ag : 1;
      pagerIcon(ctx, x1 - (5 - col) * 28, yBase - row * 19, sc);
    }
    micro(ctx, label, x1, yBase + 34, { size: 12, track: 2.6, align: "right", fam: FONT.monoS, color: "rgba(240,236,228,0.9)" });
  }
  function lcdCard(k, ctx, x, y, { at, text, label, source }) {
    const a = since(k, at);
    if (a < 0) return;
    const e = easeOutCubic(clamp((a + 1) / 3));
    ctx.save();
    ctx.globalAlpha = e;
    ctx.shadowColor = "rgba(0,0,0,0.45)";
    ctx.shadowBlur = 20;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = "#20231F";
    ctx.beginPath();
    ctx.roundRect(x, y, 420, 150, 14);
    ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.fillStyle = "#A3AE93";
    ctx.fillRect(x + 18, y + 18, 384, 84);
    setFont(ctx, FONT.monoS, 62, 2);
    ctx.fillStyle = "#1C2219";
    ctx.fillText(typed(text, a, 3), x + 34, y + 82);
    setFont(ctx, FONT.monoS, 16, 2.4);
    ctx.fillStyle = INK.signal;
    ctx.fillText(label, x + 20, y + 130);
    ctx.restore();
    const parts = source.split(" \xB7 ");
    let l1 = source, l2 = "";
    if (source.length > 52) {
      const h = Math.ceil(parts.length / 2);
      l1 = parts.slice(0, h).join(" \xB7 ");
      l2 = parts.slice(h).join(" \xB7 ");
    }
    micro(ctx, l1, x, y + 176, { size: 10, track: 1.3, color: "rgba(236,232,222,0.75)" });
    if (l2) micro(ctx, l2, x, y + 192, { size: 10, track: 1.3, color: "rgba(236,232,222,0.75)" });
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shaders.js
  var SCENE2 = COMMON + `
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
  var BRIGHT2 = COMMON + `
uniform sampler2D uScene;
void main(){ fragColor = vec4(texture(uScene, vUv).rgb, 1.0); }
`;
  var FINAL2 = COMMON + `
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

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots.js
  var W2 = 1920;
  var H2 = 1080;
  var SHADOW = { color: "rgba(0,0,0,0.55)", blur: 18, dy: 2 };
  function fitOf(size) {
    return Math.max(W2 / size[0], H2 / size[1]);
  }
  function clampView(size, v) {
    const fit = fitOf(size), hw = W2 / 2 / (fit * v[2]), hh = H2 / 2 / (fit * v[2]);
    return [clamp(v[0], hw, size[0] - hw), clamp(v[1], hh, size[1] - hh), v[2], v[3]];
  }
  function fwd(size, v, x, y, shake = [0, 0]) {
    const k = fitOf(size) * v[2], c = Math.cos(v[3]), s = Math.sin(v[3]);
    const dx = (x - v[0]) * k, dy = (y - v[1]) * k;
    return [W2 / 2 + shake[0] + c * dx - s * dy, H2 / 2 + shake[1] + s * dx + c * dy];
  }
  function srcTransform(ctx, size, v, shake = [0, 0]) {
    const k = fitOf(size) * v[2], c = Math.cos(v[3]), s = Math.sin(v[3]);
    const [ex, ey] = fwd(size, v, 0, 0, shake);
    ctx.setTransform(k * c, k * s, -k * s, k * c, ex, ey);
  }
  function parallax(v, anchor, par, parZ = 0.6) {
    const z = Math.pow(v[2], 1 + parZ);
    return [anchor[0] + (v[0] - anchor[0]) * (1 + par), anchor[1] + (v[1] - anchor[1]) * (1 + par), z, v[3] * (1 + par * 0.5)];
  }
  function beatSteps(k, a, b, ease = 0.35) {
    const n = k.beatsBetween(a, b);
    if (n <= 0) return clamp((k.s - a) / (b - a));
    const bp = k.beatIndexFloat(k.s) - k.beatIndexFloat(a);
    const i = Math.floor(bp), f = bp - i;
    return clamp((Math.min(n, i) + (i < n ? easeOutCubic(f / ease) : 0)) / n);
  }
  var W_ = (k, li, idx = null) => {
    const ws = k.line(li);
    return idx ? idx.map((i) => ws[i]) : ws;
  };
  function monoLine(k, ctx, li, { from = -1e9, until = 1e9 } = {}) {
    if (k.s < from || k.s > until) return;
    drawWords(k, ctx, W_(k, li), 72, H2 - 46, FONT.mono, 21, {
      track: 7,
      space: 22,
      upper: true,
      color: "rgba(242,238,230,0.9)",
      shadow: { color: "rgba(0,0,0,0.6)", blur: 10 },
      pop: false
    });
  }
  function subtitle(k, ctx, li, until) {
    if (k.s > until) return;
    drawWords(k, ctx, W_(k, li), W2 / 2, H2 - 92, FONT.nim, 44, { align: "center", color: INK.warm, shadow: SHADOW, space: 12 });
  }
  function s007(k) {
    const v = [1152, 648, 1 + 0.02 * clamp((k.s - 26.0528) / 3.7), 0];
    const L = k.layers;
    const sf = L.surf.ctx;
    sf.save();
    sf.translate(96, 236);
    sf.rotate(0.118);
    sf.transform(1, 0, -0.06, 1, 0, 0);
    const l2 = W_(k, 2);
    drawWords(k, sf, l2.slice(0, 4), 0, 0, FONT.nim, 42, { color: INK.dark, space: 12 });
    drawWords(k, sf, l2.slice(4), 0, 54, FONT.nim, 42, { color: INK.dark, space: 12 });
    drawWords(k, sf, W_(k, 3), 0, 108, FONT.nim, 42, { color: INK.dark, space: 12 });
    sf.restore();
    const o = L.overlay.ctx;
    const a = since(k, 26.293);
    if (a >= 0) {
      o.save();
      o.strokeStyle = "rgba(236,232,222,0.8)";
      o.lineWidth = 1;
      o.beginPath();
      o.moveTo(1008, 196);
      o.lineTo(842, 332);
      o.stroke();
      o.restore();
      tagLabel(o, 690, 326, a, { tag: "$6,000 / MONTH", sub: "PARTIALLY OBSCURED BY A TREE", source: "SOURCE \xB7 SF STANDARD \xB7 AUG 4 2026", rot: 0.05 });
    }
    return { A: { tex: "seq", view: v, lod: 0 }, key: [0.55, 0.78] };
  }
  function s008(k) {
    const v = [1220, 640, 1.05, -0.012];
    const size = [2304, 1296];
    const tr = k.track("s008");
    const L = k.layers;
    if (tr) {
      const [x0, y0] = fwd(size, v, tr[0] * size[0], tr[1] * size[1]);
      const [x1, y1] = fwd(size, v, tr[2] * size[0], tr[3] * size[1]);
      const f = L.feed.ctx;
      f.save();
      f.translate(x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.66);
      f.rotate(-0.02);
      setFont(f, FONT.nim, 38, 0);
      f.fillStyle = "rgba(23,25,28,0.9)";
      f.textAlign = "center";
      f.fillText("A.I.", 0, 0);
      setFont(f, FONT.mono, 10, 1.6);
      f.fillText("AVERAGE INDIVIDUAL", 0, 20);
      f.restore();
      const o = L.overlay.ctx;
      brackets(o, x0 - 8, y0 - 8, x1 + 8, y1 + 8, since(k, 29.7448), { color: INK.amber });
      leader(o, [x0 + 40, y0 - 8], [1560, 820], since(k, 29.7448), { dot: false, color: "rgba(242,177,52,0.85)" });
      classifier(k, o, 1440, 672, [
        { k: "AI", v: "DETECTED", at: 29.7448, hot: false },
        { k: "AI = AVERAGE INDIVIDUAL", v: "MATCH", at: 30.238, hot: true }
      ], {
        title: "CLASSIFIER \xB7 NAME TAG",
        width: 420,
        source: "CHATTJB BILLBOARD \xB7 6TH & FOLSOM \xB7 SF STANDARD \xB7 AUG 4 2026"
      });
    }
    subtitle(k, L.overlay.ctx, 3, 99);
    return { A: { tex: "seq", view: v, lod: 0 } };
  }
  var SCRATCH = [[200, 300], [262, 318], [318, 333], [365, 345], [405, 358], [432, 370], [451, 382]];
  function s009(k) {
    const size = [1672, 941];
    const anchor = [1e3, 470];
    const rack = easeInOutCubic(clamp((k.s - 33.4367) / 0.35));
    const p = beatSteps(k, 33.4367, 36.1999);
    const z = lerp(1.14, 1.1, rack) + 0.05 * p;
    const v = clampView(size, [lerp(980, 700, rack) - 110 * p, lerp(430, 440, rack), z, lerp(0.012, -0.01, rack)]);
    const vb = parallax(v, anchor, 0.32, 0.5);
    const L = k.layers;
    const sf = L.surf.ctx;
    sf.save();
    srcTransform(sf, size, v);
    drawWords(k, sf, W_(k, 4, [0, 1]), 104, 214, FONT.nim, 34, { color: INK.dark, space: 10 });
    const big = W_(k, 4, [2, 3, 4, 5, 6]);
    const notA = since(k, 35.158);
    drawWords(k, sf, big.slice(0, 2), 104, 372, FONT.din, 104, { color: INK.dark, space: 22, upper: true, track: 1 });
    drawWords(k, sf, big.slice(2, 3), 104, 482, FONT.din, 104, { color: INK.dark, upper: true, track: 1 });
    drawWords(k, sf, big.slice(3), 104, 592, FONT.din, 104, { color: INK.dark, space: 22, upper: true, track: 1 });
    drawWords(k, sf, W_(k, 4, [7, 8]), 104, 668, FONT.nim, 32, { color: INK.dark, space: 9 });
    drawWords(k, sf, W_(k, 4, [9, 10]), 104, 708, FONT.nim, 32, { color: INK.dark, space: 9 });
    if (shown(k, 32.934)) {
      setFont(sf, FONT.mono, 12, 1.4);
      sf.fillStyle = "rgba(23,25,28,0.8)";
      sf.fillText("SOURCE \xB7 BUS-SHELTER AD \xB7 SF STANDARD \xB7 SEP 2 2026", 104, 880);
    }
    sf.restore();
    const e = L.emit.ctx;
    const run = clamp((k.s - 35.158) / (35.2827 - 35.158));
    if (notA >= 0) {
      e.save();
      srcTransform(e, size, v);
      const n = SCRATCH.length - 1, upto = run * n;
      e.lineCap = "round";
      for (const [wd, col] of [[9, "rgba(255,214,150,0.22)"], [3.2, "rgba(255,236,200,0.85)"], [1.2, "rgba(255,255,255,1)"]]) {
        e.strokeStyle = col;
        e.lineWidth = wd;
        e.beginPath();
        e.moveTo(...SCRATCH[0]);
        for (let i2 = 1; i2 <= Math.ceil(upto); i2++) {
          const f2 = Math.min(1, upto - (i2 - 1));
          e.lineTo(lerp(SCRATCH[i2 - 1][0], SCRATCH[i2][0], f2), lerp(SCRATCH[i2 - 1][1], SCRATCH[i2][1], f2));
        }
        e.stroke();
      }
      const fade = run >= 1 ? Math.exp(-Math.max(0, k.s - 35.2827) / 0.5) : 1;
      const i = Math.min(n - 1, Math.floor(upto)), f = upto - i;
      const hx = lerp(SCRATCH[i][0], SCRATCH[i + 1][0], Math.min(1, f)), hy = lerp(SCRATCH[i][1], SCRATCH[i + 1][1], Math.min(1, f));
      const g = e.createRadialGradient(hx, hy, 0, hx, hy, 34);
      g.addColorStop(0, `rgba(255,240,215,${0.9 * fade})`);
      g.addColorStop(1, "rgba(255,240,215,0)");
      e.fillStyle = g;
      e.beginPath();
      e.arc(hx, hy, 34, 0, Math.PI * 2);
      e.fill();
      e.restore();
    }
    const o = L.overlay.ctx;
    const ca = since(k, 32.007);
    if (ca >= 0 && k.s < 33.4367) {
      const [x0, y0] = fwd(size, vb, 930, 70), [x1, y1] = fwd(size, vb, 1190, 390);
      brackets(o, x0, y0, x1, y1, ca, { color: INK.amber, arm: 22 });
      micro(o, "AI = AVERAGE INDIVIDUAL", x0 - 16, y0 + 40, { size: 12, track: 2, color: "rgba(240,236,228,0.85)", align: "right" });
      const me = shown(k, 32.289);
      setFont(o, FONT.monoS, 18, 2);
      o.fillStyle = INK.amber;
      o.textAlign = "right";
      o.fillText(me ? "THAT'S ME \xB7 CONFIRMED" : "THAT'S", x0 - 16, y0 + 66);
      o.textAlign = "left";
      k.mark(3, 4);
      if (me) k.mark(3, 5);
    }
    subtitle(k, o, 3, 32.369 + 0.4);
    return {
      A: { tex: "p009-bg", view: v, lod: lerp(1.5, 0, rack) },
      B: { tex: "p009-fg", view: vb, lod: lerp(0, 0.9, rack) },
      key: [0.6, 0.8]
    };
  }
  function s010(k) {
    const kickA = k.s - 38.9399;
    const sh = kickA >= 0 && kickA < 0.3 ? [Math.sin(kickA * 90) * 7 * Math.exp(-kickA / 0.08), Math.cos(kickA * 70) * 4 * Math.exp(-kickA / 0.08)] : [0, 0];
    const v = [1152, 648, 1 + 0.025 * clamp((k.s - 36.1999) / 4.6), 0];
    const L = k.layers;
    const f = L.feed.ctx, o = L.overlay.ctx;
    const out2 = shown(k, 39.897);
    if (!out2) {
      const [bx, by] = fwd([2304, 1296], v, 0.19 * 2304, 0.36 * 1296, sh);
      drawWords(k, f, W_(k, 5, [0]), 500, 176, FONT.nim, 40, { color: INK.warm, shadow: SHADOW });
      const fa = since(k, 37.226);
      if (fa >= 0) {
        leader(o, [bx, by], [500, 282], fa, { color: "rgba(242,177,52,0.85)" });
        brackets(o, 0.105 * 1920 - 6, 0.355 * 1080, 0.195 * 1920 + 6, 0.445 * 1080, fa, { color: INK.amber, arm: 9 });
        const e = easeOutCubic(clamp((fa + 1) / 3));
        o.save();
        o.globalAlpha = e;
        o.fillStyle = "rgba(244,241,234,0.94)";
        o.beginPath();
        o.roundRect(500, 196, 620, 86, 6);
        o.fill();
        o.restore();
        const ws = W_(k, 5, [1, 2, 3, 4, 5, 6]);
        const toks = [{ w: [ws[0], ws[1]], t: "SF" }, { w: [ws[2]], t: "HATES" }, { w: [ws[3], ws[4]], t: "AI" }, { w: [ws[5]], t: "BILLBOARS!!!" }];
        setFont(o, FONT.nim, 44, 0.5);
        let x = 524;
        let sq = null;
        for (const tk of toks) {
          const vis = tk.w.filter((w) => shown(k, w.start));
          if (vis.length) {
            const txt = tk.t === "SF" && vis.length === 1 ? "S" : tk.t === "AI" && vis.length === 1 ? "A" : tk.t;
            o.fillStyle = INK.dark;
            o.fillText(txt, x, 256);
            vis.forEach((w) => k.mark(w.li, w.wi));
          }
          const tw = o.measureText(tk.t).width;
          if (tk.t.startsWith("BILL")) sq = [x, x + o.measureText("BILLBOARS").width];
          x += tw + 16;
        }
        if (sq && shown(k, 38.69)) {
          o.save();
          o.strokeStyle = INK.amber;
          o.lineWidth = 2.5;
          o.beginPath();
          for (let xx = sq[0]; xx <= sq[1]; xx += 2) o.lineTo(xx, 266 + Math.sin((xx - sq[0]) / 3.2) * 2.6);
          o.stroke();
          o.restore();
        }
        const pa = since(k, 38.751), ig = since(k, 39.674);
        if (pa >= 0 && ig < 3) {
          const e2 = easeOutCubic(clamp((pa + 1) / 3));
          const px = sq ? sq[0] : 700;
          o.save();
          o.globalAlpha = e2;
          o.shadowColor = "rgba(0,0,0,0.4)";
          o.shadowBlur = 18;
          o.shadowOffsetY = 6;
          o.fillStyle = "rgba(250,248,243,0.97)";
          o.beginPath();
          o.roundRect(px, 290, 290, 132, 6);
          o.fill();
          o.shadowColor = "transparent";
          setFont(o, FONT.nim, 30, 0);
          o.fillStyle = INK.dark;
          o.fillText("billboards?", px + 18, 332);
          hairline(o, px + 12, 348.5, px + 278, 348.5, "rgba(23,25,28,0.25)");
          if (ig >= 0) {
            o.fillStyle = "rgba(242,177,52,0.9)";
            o.fillRect(px + 6, 354, 278, 32);
          }
          setFont(o, FONT.monoS, 15, 2);
          o.fillStyle = INK.dark;
          o.fillText("IGNORE", px + 18, 376);
          setFont(o, FONT.mono, 13, 1.4);
          o.fillStyle = "rgba(23,25,28,0.6)";
          o.fillText("ADD TO DICTIONARY", px + 18, 408);
          o.restore();
        }
        micro(
          o,
          "GRAFFITI ON AN AI-RECEPTIONIST BILLBOARD \xB7 US-101 NEAR POTRERO HILL \xB7 SF STANDARD \xB7 SEP 2 2026",
          500,
          304,
          { size: 10, track: 1.3, color: "rgba(236,232,222,0.72)" }
        );
      }
    } else {
      micro(f, "RUNWAY ONE \xB7 LOOK 01 \xB7 SCULPTURAL WHITE", 116, 222, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, f, "ALL", 39.897, 108, 480, 340, { marks: [[6, 0]] });
      monoLine(k, o, 6);
    }
    if (k.s < 40.055 + 0.4) drawWords(k, f, W_(k, 5, [7, 8, 9]), 610, 470, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 14 });
    return { A: { tex: "seq", view: v, lod: 0 }, shake: sh };
  }
  function s011(k) {
    const size = [1672, 941];
    const anchor = [1060, 560];
    const p = beatSteps(k, 40.7859, 44.9422, 0.4);
    const v = clampView(size, [lerp(900, 990, p), lerp(470, 455, p), lerp(1, 1.08, p), 0]);
    const vb = parallax(v, anchor, 0.15, 1.1);
    const bp = k.beatIndexFloat(k.s) % 1;
    vb[1] += Math.abs(Math.sin(bp * Math.PI)) * 2.2 - 1.1;
    const six = k.sixteenthLen(40.7859);
    const gains = [0, 1, 2, 3].map((b) => shown(k, 40.7859 + b * six) ? 1 : 0);
    const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
    const L = k.layers;
    const fb = L.feedBack.ctx, o = L.overlay.ctx;
    micro(fb, "RUNWAY ONE \xB7 LOOK 01 \xB7 SCULPTURAL WHITE", 116, 222, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
    const words = [
      ["ALL", 39.897, [6, 0]],
      ["HANDS!", 40.861, [6, 1]],
      ["ALL", 42.247, [6, 2]],
      ["NIGHT!", 42.769, [6, 3]],
      ["EVERYBODY,", 44.077, [7, 0]]
    ];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur) {
      const size0 = cur[0] === "EVERYBODY," ? 236 : 340;
      slamWord(k, fb, cur[0], cur[1], 108, 480, size0, { marks: [cur[2]] });
    }
    monoLine(k, o, 6, { until: 44 });
    if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H2 - 46, FONT.mono, 21, {
      track: 7,
      upper: true,
      pop: false,
      color: "rgba(242,238,230,0.9)",
      shadow: { color: "rgba(0,0,0,0.6)", blur: 10 }
    });
    const f = L.feed.ctx;
    const [px, py] = fwd(size, v, 1466, 372);
    const [gx, gy] = fwd(size, v, 1330, 262);
    const ga = since(k, 42.247);
    if (ga >= 0) {
      const sc = fitOf(size) * v[2];
      f.save();
      f.globalAlpha = 0.85;
      setFont(f, FONT.din, 40 * sc, 0);
      f.fillStyle = "rgba(232,228,218,0.8)";
      f.textAlign = "center";
      f.fillText("B2", px, py);
      f.restore();
      leader(o, [px, py - 40 * sc], [gx + 40, gy + 46], ga, { color: "rgba(236,232,222,0.7)" });
      f.save();
      f.globalAlpha = easeOutCubic(clamp((ga + 1) / 3)) * 0.42;
      f.fillStyle = "#000";
      f.beginPath();
      f.arc(gx, gy, 132, 0, Math.PI * 2);
      f.filter = "blur(18px)";
      f.fill();
      f.restore();
    }
    gauge(k, f, gx, gy, 84, { at: 42.247, full: 43.854, label: "ON CALL", from: "DUSK", to: "DAWN", fill: "ALL NIGHT" });
    return {
      A: { tex: "p011-bg", view: v, lod: 0.15 },
      B: { tex: "p011-fg", view: vb, lod: 0 },
      rows: { gain: gains, ambient: amb, dark: 0.1 }
    };
  }
  function s012(k) {
    const push = easeInOutCubic(clamp((k.s - 48.1698) / 0.42));
    const v = [lerp(1152, 1300, push), lerp(648, 560, push), 1 + 0.04 * push, 0];
    const L = k.layers;
    const f = L.feed.ctx, o = L.overlay.ctx;
    if (k.s < 47.517 - 0.06) {
      drawWords(k, f, W_(k, 7, [0]), 480, 112, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, pop: false });
      drawWords(k, f, W_(k, 7, [1, 2]), 474, 246, FONT.din, 124, {
        upper: true,
        color: INK.warm,
        space: 30,
        shadow: { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 }
      });
      drawWords(k, f, W_(k, 7, [3]), 474, 364, FONT.din, 124, {
        upper: true,
        color: INK.warm,
        shadow: { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 }
      });
    } else {
      drawWords(k, f, W_(k, 8, [0, 1]), 480, 112, FONT.nim, 40, { color: INK.warm, shadow: SHADOW, space: 12 });
      drawWords(k, f, W_(k, 8, [2]), 474, 246, FONT.din, 112, { upper: true, color: INK.warm, shadow: { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 } });
      drawWords(k, f, W_(k, 8, [3, 4]), 474, 360, FONT.din, 112, {
        upper: true,
        color: INK.warm,
        space: 30,
        shadow: { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 }
      });
    }
    const lap = fwd([2304, 1296], v, 0.37 * 2304, 0.77 * 1296);
    if (k.s < 47.517) {
      const a = since(k, 45.625);
      brackets(o, ...fwd([2304, 1296], v, 0.02 * 2304, 0.5 * 1296), ...fwd([2304, 1296], v, 0.42 * 2304, 0.99 * 1296), a, { arm: 22 });
      leader(o, lap, [1170, 742], a, { color: "rgba(236,232,222,0.8)" });
      const six = k.sixteenthLen(45.625);
      classifier(k, o, 1170, 712, [
        { k: "HOLDING ON", v: "YES", at: 45.625 },
        { k: "HOLDING ON", v: "YES", at: 45.625 + six },
        { k: "HOLDING ON", v: "WHITE-KNUCKLED", at: 45.625 + 2 * six, hot: true }
      ], { title: "FRONT ROW \xB7 CLASSIFIER", width: 440, accent: INK.bone });
    } else {
      leader(o, lap, [1170, 742], since(k, 47.517), { color: "rgba(236,232,222,0.8)" });
      hypnogram(k, o, 1170, 712, { t0: 47.517, drop: 49.307, w: 440, h: 150 });
    }
    return { A: { tex: "seq", view: v, lod: 0 } };
  }
  function s013(k) {
    const size = [1672, 941];
    const anchor = [900, 760];
    const p = beatSteps(k, 50.933, 55.0777, 0.4);
    const punch = easeOutCubic(clamp((k.s - 51.76) / 0.18));
    const z = 2 + 0.08 * punch + 0.05 * p;
    const v = clampView(size, [lerp(690, 760, p), 700, z, lerp(-0.03, 0.015, p)]);
    const vb = parallax(v, anchor, 0.22, 0.4);
    const L = k.layers;
    const f = L.feed.ctx, o = L.overlay.ctx;
    if (k.s < 54.187 + 0.35) {
      drawWords(k, f, W_(k, 9, [0, 1]), 80, 262, FONT.nim, 42, { color: INK.warm, shadow: SHADOW, space: 12 });
      drawWords(k, f, W_(k, 9, [2]), 74, 470, FONT.din, 210, { upper: true, color: INK.warm, shadow: { color: "rgba(0,0,0,0.5)", blur: 22, dy: 7 } });
      drawWords(k, f, W_(k, 9, [3, 4, 5, 6]), 78, 600, FONT.din, 120, {
        upper: true,
        color: INK.warm,
        space: 28,
        shadow: { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 }
      });
    }
    const mw = [["ALL", 53.767, [10, 0]], ["HANDS!", 54.59, [10, 1]]];
    let cur = null;
    for (const w of mw) if (shown(k, w[1])) cur = w;
    monoLine(k, o, 10, { from: 53.767 - 0.03 });
    if (cur) {
      micro(f, "RUNWAY ONE \xB7 LOOK 01 \xB7 SCULPTURAL WHITE", 84, 726, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, f, cur[0], cur[1], 74, 1e3, 300, { marks: [cur[2]] });
    }
    const ph = fwd(size, vb, 1030, 845);
    const ca = since(k, 51.76);
    leader(o, ph, [1420, 600], ca, { color: "rgba(236,232,222,0.8)" });
    callScreen(k, o, 1420, 250, {
      at: 51.76,
      takeAt: 53.645,
      flashAt: 53.708,
      caller: "INCOMING CALL",
      label: "INCOMING \xB7 SEV-HIGH",
      decline: "DECLINE \xB7 DISABLED"
    });
    const fl = since(k, 53.708);
    const e = L.emit.ctx;
    const glow = 0.35 + (fl >= 0 ? 1.4 * Math.exp(-fl / 3) : 0);
    const g = e.createRadialGradient(ph[0], ph[1], 0, ph[0], ph[1], 260);
    g.addColorStop(0, `rgba(200,220,255,${0.55 * glow})`);
    g.addColorStop(0.35, `rgba(170,195,240,${0.18 * glow})`);
    g.addColorStop(1, "rgba(160,190,240,0)");
    e.fillStyle = g;
    e.beginPath();
    e.arc(ph[0], ph[1], 260, 0, Math.PI * 2);
    e.fill();
    return {
      A: { tex: "p013-bg", view: v, lod: 0.9 },
      B: { tex: "p013-fg", view: vb, lod: 0.1 }
    };
  }
  var PAGER = [997, 435];
  function s014(k) {
    const size = [1672, 941];
    const anchor = [990, 470];
    const p = beatSteps(k, 55.0777, 58.726, 0.45);
    const tp = k.s - 55.542;
    const punch = tp >= 0 ? 0.05 * Math.exp(-tp / 0.12) * (tp < 0.05 ? tp / 0.05 : 1) : 0;
    const crash = easeInOutCubic(clamp((k.s - 58.726) / 0.21));
    let v = [lerp(1060, 880, p), lerp(470, 480, p), 1.06 + punch + 0.03 * p, lerp(0.02, -0.015, p)];
    v = [lerp(v[0], PAGER[0] + 60, crash), lerp(v[1], PAGER[1] - 20, crash), lerp(v[2], 1.85, crash), lerp(v[3], -0.03, crash)];
    v = clampView(size, v);
    const vb = parallax(v, anchor, -0.18, 0.25);
    const L = k.layers;
    const fb = L.feedBack.ctx, f = L.feed.ctx, o = L.overlay.ctx;
    const mw = [["ALL", 55.152, [10, 2]], ["NIGHT!", 55.513, [10, 3]]];
    let cur = null;
    for (const w of mw) if (shown(k, w[1])) cur = w;
    if (k.s < 55.152) cur = ["HANDS!", 54.59, [10, 1]];
    if (cur && k.s < 58.6) {
      micro(fb, "RUNWAY ONE \xB7 LOOK 01 \xB7 SCULPTURAL WHITE", 116, 222, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, fb, cur[0], cur[1], 108, 480, 340, { marks: [cur[2]] });
    }
    monoLine(k, o, 10, { until: 58.6 });
    pagerStack(k, o, W2 - 60, 300, { from: 55.0777, to: 58.726, label: "PAGED" });
    if (shown(k, 58.726)) {
      drawWords(k, f, W_(k, 11), 80, 440, FONT.din, 200, {
        upper: true,
        color: INK.warm,
        space: 40,
        shadow: { color: "rgba(0,0,0,0.55)", blur: 22, dy: 7 }
      });
      const [lx, ly] = fwd(size, vb, PAGER[0], PAGER[1]);
      const sc = fitOf(size) * vb[2];
      f.save();
      f.translate(lx, ly);
      f.rotate(vb[3] - 0.02);
      setFont(f, FONT.monoS, 8.5 * sc, 0.3 * sc);
      f.fillStyle = "rgba(28,34,25,0.92)";
      f.textAlign = "center";
      f.fillText("10:02", 0, 3.2 * sc);
      f.restore();
      const e = L.emit.ctx;
      const g = e.createRadialGradient(lx, ly, 0, lx, ly, 22 * sc);
      g.addColorStop(0, "rgba(170,190,150,0.35)");
      g.addColorStop(1, "rgba(170,190,150,0)");
      e.fillStyle = g;
      e.beginPath();
      e.arc(lx, ly, 22 * sc, 0, Math.PI * 2);
      e.fill();
      leader(o, [lx + 22 * sc, ly], [1380, 640], since(k, 58.726));
      lcdCard(k, o, 1380, 560, {
        at: 58.726,
        text: "10:02:11",
        label: "P0 ALERT RAISED",
        source: "SOURCE \xB7 OPENAI ALIGNMENT REPORT \xB7 SEP 20 2026 (UPDATED SEP 25) \xB7 NO TIME ZONE GIVEN"
      });
    }
    return {
      A: { tex: "p014-bg", view: v, lod: 0.35 },
      B: { tex: "p014-fg", view: vb, lod: 0 }
    };
  }
  var SHOT_FN = { s007, s008, s009, s010, s011, s012, s013, s014 };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots2.js
  var W3 = 1920;
  var H3 = 1080;
  var SZ = [1672, 941];
  var SHADOW2 = { color: "rgba(0,0,0,0.55)", blur: 18, dy: 2 };
  var BIG_SH = { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 };
  var GEO = {
    2: {
      look: "RUNWAY ONE \xB7 LOOK 01 \xB7 SCULPTURAL WHITE",
      s007: { crops: [[26.0528, 836, 470, 1, 0], [27.8872, 720, 360, 1.15, -8e-3]], text: [120, 290, -0.2, 34, 46], branch: [1300, 140], key: [0.72, 0.86] },
      s008: { crops: [[29.7448, 836, 470, 1, 0], [30.662, 1e3, 560, 1.22, 0.012]], tag: [1137, 756, 1388, 874], ai: [1262, 828, 46], panel: [1480, 400], lead: [1500, 560] },
      s009: {
        crops: [[31.1263, 836, 470, 1, 0], [33.4367, 1029, 380, 1.3, -0.01], [35.2827, 836, 470, 1, 0.01], [35.7355, 700, 400, 1.18, -6e-3]],
        busStop: [1456, 120, 28],
        X0: 1452,
        rows: [210, 320, 420, 520, 620],
        size: 84,
        tail: [690, 722, 25],
        source: [880, 896],
        scratchA: [[1572, 234], [1530, 270], [1490, 303], [1452, 334], [1421, 360]],
        scratchB: [[67, 151], [140, 237], [215, 325], [290, 413], [360, 496]],
        not: [96, 380, 150],
        face: [690, 90, 960, 430],
        key: [0.6, 0.78]
      },
      s010: {
        crops: [[36.1999, 836, 470, 1, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01], [39.8454, 836, 470, 1, 0]],
        bill: [209, 286, 502, 487],
        freeway: [80, 220],
        field: [80, 240],
        popup: [696, 240],
        forgot: [680, 424],
        micro: [80, 348]
      },
      s011: { crops: [[40.7859, 836, 470, 1, 0], [42.6318, 836, 430, 1.12, -8e-3], [44.0134, 635, 294, 1.5, 0.01]], gauge: [1330, 210], size: 250, rows: "X11a-rows" },
      s012: {
        crops: [[44.9422, 836, 470, 1, 0], [46.3238, 836, 430, 1.1, -0.01], [48.1698, 900, 470, 1, 0], [50.0158, 900, 380, 1.14, 0.01]],
        massX: 1414,
        lap: [560, 540],
        b: [68, 262, 392, 514]
      },
      s013: {
        crops: [[50.933, 836, 470, 1, 0], [51.8502, 850, 400, 1.3, 0.01], [53.7078, 836, 470, 1.06, -5e-3]],
        mass: [1244, 140, 330, 440],
        phone: [860, 525],
        card: [1500, 540]
      },
      s014: {
        crops: [[55.0777, 836, 470, 1, 0], [55.5421, 836, 440, 1.1, 0.01], [57.3765, 880, 380, 1.28, -0.01], [58.7697, 886, 380, 2.1, -0.02]],
        lcd: [886, 336, 0.1],
        night: [106, 236, 450, 230],
        ten: 360
      }
    },
    3: {
      look: "RUNWAY ONE \xB7 LOOK W1 \xB7 ON-CALL HOODIE COUTURE",
      // X07a: the billboard is smaller (x 0-550, its lower edge rising 12 deg to the right); the branch at (1270, 150)
      s007: { crops: [[26.0528, 836, 470, 1, 0], [27.8872, 700, 360, 1.15, -8e-3]], text: [60, 230, -0.21, 30, 40], branch: [1300, 170], key: [0.72, 0.86] },
      // X08a: the blank name badge on her chest (1102-1210, 572-636), under her thumb; the dark city top right
      s008: { crops: [[29.7448, 836, 470, 1, 0], [30.662, 1150, 500, 1.22, 0.012]], tag: [1102, 572, 1210, 636], ai: [1170, 618, 32], panel: [1480, 120], lead: [1520, 250] },
      // X09a: the scratch from (1590, 150) to her nail at (1386, 289); glass from x 1300; X09b: scratch (20, 460) -> nail (395, 610)
      s009: {
        crops: [[31.1263, 836, 470, 1, 0], [33.4367, 1029, 362, 1.3, -0.01], [35.2827, 836, 470, 1, 0.01], [35.7355, 708, 470, 1.18, -6e-3]],
        busStop: [1346, 140, 21],
        X0: 1440,
        rows: [140, 235, 335, 430, 525],
        size: 84,
        tail: [600, 632, 25],
        source: [880, 896],
        scratchA: [[1590, 150], [1543, 156], [1507, 179], [1450, 214], [1386, 289]],
        scratchB: [[20, 460], [115, 498], [210, 536], [305, 574], [395, 610]],
        not: [56, 560, 150],
        face: [640, 20, 940, 300],
        key: [0.6, 0.78]
      },
      // X10a: the graffiti billboard at (50-326, 318-485), her head at (736-1037, 100-335)
      s010: {
        crops: [[36.1999, 836, 470, 1, 0], [37.0939, 643, 400, 1.3, 0.012], [38.9399, 760, 420, 1.12, -0.01], [39.8454, 836, 470, 1, 0]],
        bill: [50, 318, 326, 485],
        freeway: [80, 232],
        field: [80, 246],
        popup: [500, 342],
        forgot: [500, 520],
        micro: [80, 352]
      },
      s011: { crops: [[40.7859, 836, 470, 1, 0], [42.6318, 836, 430, 1.12, -8e-3], [44.0134, 635, 294, 1.5, 0.01]], gauge: [1330, 230], size: 230, rows: "X11a-w1-rows" },
      s012: {
        crops: [[44.9422, 836, 470, 1, 0], [46.3238, 836, 430, 1.1, -0.01], [48.1698, 900, 470, 1, 0], [50.0158, 900, 380, 1.14, 0.01]],
        massX: 1520,
        lap: [450, 540],
        b: [68, 262, 392, 514]
      },
      s013: {
        crops: [[50.933, 836, 470, 1, 0], [51.8502, 800, 400, 1.3, 0.01], [53.7078, 836, 470, 1.06, -5e-3]],
        mass: [1244, 120, 300, 400],
        phone: [720, 500],
        card: [1500, 540]
      },
      s014: {
        crops: [[55.0777, 836, 470, 1, 0], [55.5421, 836, 440, 1.1, 0.01], [57.3765, 880, 380, 1.28, -0.01], [58.7697, 902, 470, 2.1, -0.02]],
        lcd: [902, 498, -0.08],
        night: [470, 196, 380, 230],
        ten: 360
      }
    }
  };
  var G = (k) => GEO[k.version >= 3 ? 3 : k.version] || GEO[2];
  function frameOf(k, plan, seed) {
    let still3 = k.shot.stills[0][0];
    for (const [key, at] of k.shot.stills) if (shown(k, at)) still3 = key;
    let c = plan[0];
    for (const p of plan) if (shown(k, p[0])) c = p;
    const v = clampView(SZ, [c[1], c[2], c[3], c[4]]);
    const t = k.s;
    const shake = [noise1(t * 0.9, seed) * 2.2, noise1(t * 0.8, seed + 7) * 1.6];
    v[3] += noise1(t * 0.6, seed + 13) * 12e-4;
    return { still: still3, v, shake };
  }
  var P = (fr, x, y) => fwd(SZ, fr.v, x, y, fr.shake);
  var plateCtx = (ctx, fr) => srcTransform(ctx, SZ, fr.v, fr.shake);
  var out = (fr, extra = {}) => ({ A: { tex: fr.still, view: fr.v, lod: 0 }, shake: fr.shake, ...extra });
  function s0072(k) {
    const g = G(k).s007;
    const fr = frameOf(k, g.crops, 1);
    const L = k.layers;
    const sf = L.surf.ctx;
    const [tx0, ty0, rot, fs, lh] = g.text;
    sf.save();
    plateCtx(sf, fr);
    sf.translate(tx0, ty0);
    sf.rotate(rot);
    const l2 = W_(k, 2), l3 = W_(k, 3);
    drawWords(k, sf, l2.slice(0, 4), 0, 0, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
    drawWords(k, sf, l2.slice(4), 0, lh, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
    drawWords(k, sf, l3.slice(0, 4), 0, 2 * lh, FONT.nim, fs, { color: INK.dark, space: fs * 0.3 });
    sf.restore();
    const o = L.overlay.ctx;
    const a = since(k, 26.293);
    if (a >= 0) {
      const [bx, by] = P(fr, g.branch[0], g.branch[1]);
      const tx = Math.min(W3 - 340, bx + 50), ty = by + 110;
      o.save();
      o.strokeStyle = "rgba(236,232,222,0.8)";
      o.lineWidth = 1;
      o.beginPath();
      o.moveTo(bx, by);
      o.lineTo(tx + 150, ty + 12);
      o.stroke();
      o.restore();
      tagLabel(o, tx, ty, a, { tag: "$6,000 / MONTH", sub: "PARTIALLY OBSCURED BY A TREE", source: "SOURCE \xB7 SF STANDARD \xB7 AUG 4 2026", rot: 0.04 });
    }
    return out(fr, { key: g.key });
  }
  function s0082(k) {
    const g = G(k).s008;
    const fr = frameOf(k, g.crops, 2);
    const L = k.layers;
    const f = L.feed.ctx;
    f.save();
    plateCtx(f, fr);
    f.translate(g.ai[0], g.ai[1]);
    f.rotate(-0.03);
    setFont(f, FONT.nim, g.ai[2], 0);
    f.fillStyle = "rgba(23,25,28,0.9)";
    f.textAlign = "center";
    f.fillText("A.I.", 0, 0);
    setFont(f, FONT.mono, g.ai[2] * 0.24, 1.4);
    f.fillText("AVERAGE INDIVIDUAL", 0, g.ai[2] * 0.48);
    f.restore();
    const o = L.overlay.ctx;
    const [x0, y0] = P(fr, g.tag[0], g.tag[1]), [x1, y1] = P(fr, g.tag[2], g.tag[3]);
    brackets(o, x0 - 6, y0 - 6, x1 + 6, y1 + 6, since(k, 29.7448), { color: INK.amber });
    leader(o, [x1 + 6, y0 - 6], g.lead, since(k, 29.7448), { dot: false, color: "rgba(242,177,52,0.85)" });
    classifier(k, o, g.panel[0], g.panel[1], [
      { k: "AI", v: "DETECTED", at: 29.7448 },
      { k: "AI = AVERAGE INDIVIDUAL", v: "MATCH", at: 30.238, hot: true }
    ], { title: "CLASSIFIER \xB7 NAME TAG", width: 400, source: "CHATTJB BILLBOARD \xB7 6TH & FOLSOM \xB7 SF STANDARD \xB7 AUG 4 2026" });
    subtitle(k, o, 3, 99);
    return out(fr);
  }
  function strokePath(e, pts, upto, widths) {
    const n = pts.length - 1, u = upto * n;
    for (const [wd, col] of widths) {
      e.strokeStyle = col;
      e.lineWidth = wd;
      e.lineCap = "round";
      e.beginPath();
      e.moveTo(...pts[0]);
      for (let i = 1; i <= Math.ceil(u); i++) {
        const q = Math.min(1, u - (i - 1));
        e.lineTo(lerp(pts[i - 1][0], pts[i][0], q), lerp(pts[i - 1][1], pts[i][1], q));
      }
      e.stroke();
    }
  }
  function s0092(k) {
    const g = G(k).s009;
    const fr = frameOf(k, g.crops, 3);
    const L = k.layers, o = L.overlay.ctx;
    if (fr.still === "X09a") {
      const sf = L.surf.ctx;
      sf.save();
      plateCtx(sf, fr);
      const [bsx, bsy, bss] = g.busStop, X0 = g.X0, R = g.rows, S = g.size;
      drawWords(k, sf, W_(k, 4, [0, 1]), bsx, bsy, FONT.nim, bss, { color: INK.dark, space: 8 });
      [2, 3, 4, 5, 6].forEach((wi, i) => drawWords(k, sf, W_(k, 4, [wi]), X0, R[i], FONT.din, S, { color: INK.dark, upper: true, track: 1 }));
      drawWords(k, sf, W_(k, 4, [7, 8]), X0 + 2, g.tail[0], FONT.nim, g.tail[2], { color: INK.dark, space: 7 });
      drawWords(k, sf, W_(k, 4, [9, 10]), X0 + 2, g.tail[1], FONT.nim, g.tail[2], { color: INK.dark, space: 7 });
      if (shown(k, 32.934)) {
        setFont(sf, FONT.mono, 10, 1.2);
        sf.fillStyle = "rgba(23,25,28,0.8)";
        sf.fillText("SOURCE \xB7 BUS-SHELTER AD", X0 + 2, g.source[0]);
        sf.fillText("SF STANDARD \xB7 SEP 2 2026", X0 + 2, g.source[1]);
      }
      sf.restore();
      if (shown(k, 35.158)) {
        const e = L.emit.ctx;
        e.save();
        plateCtx(e, fr);
        strokePath(
          e,
          g.scratchA,
          clamp((k.s - 35.158) / (35.2827 - 35.158)),
          [[8, "rgba(255,214,150,0.25)"], [3, "rgba(255,236,200,0.85)"], [1.1, "rgba(255,255,255,1)"]]
        );
        e.restore();
      }
      const ca = since(k, 32.007);
      if (ca >= 0 && k.s < 33.4367) {
        const [bx0, by0] = P(fr, g.face[0], g.face[1]), [bx1, by1] = P(fr, g.face[2], g.face[3]);
        brackets(o, bx0, by0, bx1, by1, ca, { color: INK.amber, arm: 20 });
        const me = shown(k, 32.289);
        micro(o, "AI = AVERAGE INDIVIDUAL", bx0 - 16, by0 + 40, { size: 12, track: 2, color: "rgba(240,236,228,0.85)", align: "right" });
        setFont(o, FONT.monoS, 18, 2);
        o.fillStyle = INK.amber;
        o.textAlign = "right";
        o.fillText(me ? "THAT'S ME \xB7 CONFIRMED" : "THAT'S", bx0 - 16, by0 + 66);
        o.textAlign = "left";
        k.mark(3, 4);
        if (me) k.mark(3, 5);
      }
      subtitle(k, o, 3, 32.369 + 0.4);
    } else {
      const f = L.feed.ctx;
      f.save();
      plateCtx(f, fr);
      setFont(f, FONT.din, g.not[2], 2);
      f.fillStyle = "rgba(20,22,25,0.86)";
      f.fillText("NOT", g.not[0], g.not[1]);
      f.restore();
      const e = L.emit.ctx;
      e.save();
      plateCtx(e, fr);
      const fade = 0.45 + 0.55 * Math.exp(-Math.max(0, k.s - 35.2827) / 0.35);
      strokePath(e, g.scratchB, 1, [[10, `rgba(255,214,150,${0.25 * fade})`], [3.4, `rgba(255,236,200,${0.85 * fade})`], [1.2, `rgba(255,255,255,${fade})`]]);
      e.restore();
      drawWords(k, o, W_(k, 4, [7, 8, 9, 10]), 72, H3 - 92, FONT.nim, 44, { color: INK.warm, shadow: SHADOW2, space: 12 });
      micro(o, "SOURCE \xB7 BUS-SHELTER AD \xB7 SF STANDARD \xB7 SEP 2 2026", 74, H3 - 56, { size: 11, track: 1.6 });
    }
    return out(fr, { key: g.key });
  }
  function s0102(k) {
    const g = G(k).s010;
    const fr = frameOf(k, g.crops, 4);
    const kickA = k.s - 38.9399;
    if (kickA >= 0 && kickA < 0.3) {
      fr.shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08);
      fr.shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08);
    }
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    const [fx, fy] = g.field, [px, py] = g.popup;
    if (fr.still === "X10a") {
      drawWords(k, f, W_(k, 5, [0]), g.freeway[0], g.freeway[1], FONT.nim, 40, { color: INK.warm, shadow: SHADOW2 });
      const fa = since(k, 37.226);
      if (fa >= 0) {
        const [b0x, b0y] = P(fr, g.bill[0], g.bill[1]), [b1x, b1y] = P(fr, g.bill[2], g.bill[3]);
        brackets(o, b0x, b0y, b1x, b1y, fa, { color: INK.amber, arm: 10 });
        leader(o, [(b0x + b1x) / 2, b0y], [fx + 220, fy + 86], fa, { color: "rgba(242,177,52,0.85)" });
        const e = easeOutCubic(clamp((fa + 1) / 3));
        o.save();
        o.globalAlpha = e;
        o.fillStyle = "rgba(244,241,234,0.94)";
        o.beginPath();
        o.roundRect(fx, fy, 600, 86, 6);
        o.fill();
        o.restore();
        const ws = W_(k, 5, [1, 2, 3, 4, 5, 6]);
        const toks = [{ w: [ws[0], ws[1]], t: "SF" }, { w: [ws[2]], t: "HATES" }, { w: [ws[3], ws[4]], t: "AI" }, { w: [ws[5]], t: "BILLBOARS!!!" }];
        setFont(o, FONT.nim, 40, 0.5);
        let x = fx + 18, sq = null;
        for (const tk of toks) {
          const vis = tk.w.filter((w) => shown(k, w.start));
          if (vis.length) {
            const txt = tk.t === "SF" && vis.length === 1 ? "S" : tk.t === "AI" && vis.length === 1 ? "A" : tk.t;
            o.fillStyle = INK.dark;
            o.fillText(txt, x, fy + 59);
            vis.forEach((w) => k.mark(w.li, w.wi));
          }
          if (tk.t.startsWith("BILL")) sq = [x, x + o.measureText("BILLBOARS").width];
          x += o.measureText(tk.t).width + 15;
        }
        if (sq && shown(k, 38.69)) {
          o.save();
          o.strokeStyle = INK.amber;
          o.lineWidth = 2.5;
          o.beginPath();
          for (let xx = sq[0]; xx <= sq[1]; xx += 2) o.lineTo(xx, fy + 69 + Math.sin((xx - sq[0]) / 3.2) * 2.6);
          o.stroke();
          o.restore();
        }
        const pa = since(k, 38.751), ig = since(k, 39.674);
        if (pa >= 0 && ig < 3) {
          const e2 = easeOutCubic(clamp((pa + 1) / 3));
          o.save();
          o.globalAlpha = e2;
          o.shadowColor = "rgba(0,0,0,0.4)";
          o.shadowBlur = 18;
          o.shadowOffsetY = 6;
          o.fillStyle = "rgba(250,248,243,0.97)";
          o.beginPath();
          o.roundRect(px, py, 270, 128, 6);
          o.fill();
          o.shadowColor = "transparent";
          setFont(o, FONT.nim, 28, 0);
          o.fillStyle = INK.dark;
          o.fillText("billboards?", px + 16, py + 40);
          hairline(o, px + 10, py + 55.5, px + 260, py + 55.5, "rgba(23,25,28,0.25)");
          if (ig >= 0) {
            o.fillStyle = "rgba(242,177,52,0.9)";
            o.fillRect(px + 6, py + 61, 258, 30);
          }
          setFont(o, FONT.monoS, 14, 2);
          o.fillStyle = INK.dark;
          o.fillText("IGNORE", px + 16, py + 82);
          setFont(o, FONT.mono, 12, 1.4);
          o.fillStyle = "rgba(23,25,28,0.6)";
          o.fillText("ADD TO DICTIONARY", px + 16, py + 112);
          o.restore();
        }
        micro(
          o,
          "GRAFFITI ON AN AI-RECEPTIONIST BILLBOARD \xB7 US-101 NEAR POTRERO HILL \xB7 SF STANDARD \xB7 SEP 2 2026",
          g.micro[0],
          g.micro[1],
          { size: 9, track: 1.1, color: "rgba(236,232,222,0.72)" }
        );
      }
    } else {
      micro(f, G(k).look, 106, 236, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, f, "ALL", 39.897, 100, 470, G(k).s011.size, { marks: [[6, 0]] });
      monoLine(k, o, 6);
    }
    if (k.s < 40.055 + 0.4) drawWords(k, f, W_(k, 5, [7, 8, 9]), g.forgot[0], g.forgot[1], FONT.nim, 38, { color: INK.warm, shadow: SHADOW2, space: 13 });
    return out(fr);
  }
  function s0112(k) {
    const g = G(k).s011;
    const fr = frameOf(k, g.crops, 5);
    const six = k.sixteenthLen(40.7859);
    const gains = [0, 1, 2, 3].map((b) => shown(k, 40.7859 + b * six) ? 1 : 0);
    const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    micro(f, G(k).look, 106, 236, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
    const words = [["ALL", 39.897, [6, 0]], ["HANDS!", 40.861, [6, 1]], ["ALL", 42.247, [6, 2]], ["NIGHT!", 42.769, [6, 3]], ["EVERYBODY,", 44.077, [7, 0]]];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur) slamWord(k, f, cur[0], cur[1], 100, 470, cur[0] === "EVERYBODY," ? 200 : g.size, { marks: [cur[2]] });
    monoLine(k, o, 6, { until: 44 });
    if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H3 - 46, FONT.mono, 21, {
      track: 7,
      upper: true,
      pop: false,
      color: "rgba(242,238,230,0.9)",
      shadow: { color: "rgba(0,0,0,0.6)", blur: 10 }
    });
    const ga = since(k, 42.247);
    if (ga >= 0 && k.s < 44.0134) {
      const [gx, gy] = P(fr, g.gauge[0], g.gauge[1]);
      gauge(k, f, gx, gy, 80, { at: 42.247, full: 43.854, label: "B2 \xB7 ON CALL", from: "DUSK", to: "DAWN", fill: "ALL NIGHT" });
    }
    return out(fr, { rows: { tex: g.rows, gain: gains, ambient: amb, dark: 0.12 } });
  }
  function s0122(k) {
    const g = G(k).s012;
    const fr = frameOf(k, g.crops, 6);
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    const MX = g.massX;
    if (fr.still === "X12a") {
      if (k.s < 47.517 - 0.06) {
        drawWords(k, f, W_(k, 7, [0]), MX + 6, 128, FONT.nim, 38, { color: INK.warm, shadow: SHADOW2, pop: false });
        drawWords(k, f, W_(k, 7, [1, 2]), MX, 252, FONT.din, 116, { upper: true, color: INK.warm, space: 26, shadow: BIG_SH });
        drawWords(k, f, W_(k, 7, [3]), MX, 366, FONT.din, 116, { upper: true, color: INK.warm, shadow: BIG_SH });
      } else {
        drawWords(k, f, W_(k, 8, [0, 1]), MX + 6, 128, FONT.nim, 38, { color: INK.warm, shadow: SHADOW2, space: 11 });
      }
      const lap = P(fr, g.lap[0], g.lap[1]);
      if (k.s < 47.517) {
        const a = since(k, 45.625);
        leader(o, lap, [460, 790], a, { color: "rgba(236,232,222,0.8)" });
        const six = k.sixteenthLen(45.625);
        classifier(k, o, 60, 770, [
          { k: "HOLDING ON", v: "YES", at: 45.625 },
          { k: "HOLDING ON", v: "YES", at: 45.625 + six },
          { k: "HOLDING ON", v: "WHITE-KNUCKLED", at: 45.625 + 2 * six, hot: true }
        ], { title: "FRONT ROW \xB7 CLASSIFIER", width: 400, accent: INK.bone });
      } else {
        leader(o, lap, [420, 790], since(k, 47.517), { color: "rgba(236,232,222,0.8)" });
        hypnogram(k, o, 60, 770, { t0: 47.517, drop: 49.307, w: 360, h: 120 });
      }
    } else {
      const [bx, b1, b2, b3] = g.b;
      drawWords(k, f, W_(k, 8, [0, 1]), bx, b1, FONT.nim, 40, { color: INK.warm, shadow: SHADOW2, space: 12, pop: false });
      drawWords(k, f, W_(k, 8, [2]), bx - 6, b2, FONT.din, 124, { upper: true, color: INK.warm, shadow: BIG_SH });
      drawWords(k, f, W_(k, 8, [3, 4]), bx - 6, b3, FONT.din, 124, { upper: true, color: INK.warm, space: 26, shadow: BIG_SH });
      hypnogram(k, o, 60, 770, { t0: 47.517, drop: 49.307, w: 360, h: 120 });
    }
    return out(fr);
  }
  function s0132(k) {
    const g = G(k).s013;
    const fr = frameOf(k, g.crops, 7);
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    const [mx, m1, m2, m3] = g.mass;
    if (k.s < 54.187 + 0.35) {
      drawWords(k, f, W_(k, 9, [0, 1]), mx, m1, FONT.nim, 40, { color: INK.warm, shadow: SHADOW2, space: 12 });
      drawWords(k, f, W_(k, 9, [2]), mx - 6, m2, FONT.din, 190, { upper: true, color: INK.warm, shadow: BIG_SH });
      drawWords(k, f, W_(k, 9, [3, 4, 5, 6]), mx - 2, m3, FONT.din, 92, { upper: true, color: INK.warm, space: 22, shadow: BIG_SH });
    }
    const mw = [["ALL", 53.767, [10, 0]], ["HANDS!", 54.59, [10, 1]]];
    let cur = null;
    for (const w of mw) if (shown(k, w[1])) cur = w;
    monoLine(k, o, 10, { from: 53.767 - 0.03 });
    if (cur) {
      micro(f, G(k).look, 70, 790, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, f, cur[0], cur[1], 64, 1e3, 240, { marks: [cur[2]] });
    }
    const ph = P(fr, g.phone[0], g.phone[1]);
    const ca = since(k, 51.76);
    leader(o, ph, [g.card[0], g.card[1] + 160], ca, { color: "rgba(236,232,222,0.8)" });
    o.save();
    o.translate(g.card[0], g.card[1]);
    o.scale(0.7, 0.7);
    callScreen(k, o, 0, 0, {
      at: 51.76,
      takeAt: 53.645,
      flashAt: 53.708,
      caller: "INCOMING CALL",
      label: "INCOMING \xB7 SEV-HIGH",
      decline: "DECLINE \xB7 DISABLED"
    });
    o.restore();
    const fl = since(k, 53.708);
    const e = L.emit.ctx;
    const glow = 0.25 + (fl >= 0 ? 1.3 * Math.exp(-fl / 3) : 0);
    const gr = e.createRadialGradient(ph[0], ph[1], 0, ph[0], ph[1], 240);
    gr.addColorStop(0, `rgba(200,220,255,${0.5 * glow})`);
    gr.addColorStop(0.35, `rgba(170,195,240,${0.16 * glow})`);
    gr.addColorStop(1, "rgba(160,190,240,0)");
    e.fillStyle = gr;
    e.beginPath();
    e.arc(ph[0], ph[1], 240, 0, Math.PI * 2);
    e.fill();
    return out(fr);
  }
  function s0142(k) {
    const g = G(k).s014;
    const fr = frameOf(k, g.crops, 8);
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    const mw = [["ALL", 55.152, [10, 2]], ["NIGHT!", 55.513, [10, 3]]];
    let cur = k.s < 55.152 ? ["HANDS!", 54.59, [10, 1]] : null;
    for (const w of mw) if (shown(k, w[1])) cur = w;
    const [nmx, nmy, nby, nsz] = g.night;
    if (cur && k.s < 58.6) {
      micro(f, G(k).look, nmx, nmy, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
      slamWord(k, f, cur[0], cur[1], 100, nby, nsz, { marks: [cur[2]] });
    }
    monoLine(k, o, 10, { until: 58.6 });
    pagerStack(k, o, W3 - 60, 300, { from: 55.0777, to: 58.726, label: "PAGED" });
    if (shown(k, 58.726)) {
      drawWords(k, f, W_(k, 11), 80, g.ten, FONT.din, 170, { upper: true, color: INK.warm, space: 34, shadow: { color: "rgba(0,0,0,0.55)", blur: 22, dy: 7 } });
      const [lx, ly] = P(fr, g.lcd[0], g.lcd[1]);
      const sc = 1.148 * fr.v[2];
      f.save();
      f.translate(lx, ly);
      f.rotate(fr.v[3] + g.lcd[2]);
      setFont(f, FONT.monoS, 9 * sc, 0.3 * sc);
      f.fillStyle = "rgba(28,34,25,0.92)";
      f.textAlign = "center";
      f.fillText("10:02", 0, 3.2 * sc);
      f.restore();
      const e = L.emit.ctx;
      const gr = e.createRadialGradient(lx, ly, 0, lx, ly, 22 * sc);
      gr.addColorStop(0, "rgba(170,190,150,0.35)");
      gr.addColorStop(1, "rgba(170,190,150,0)");
      e.fillStyle = gr;
      e.beginPath();
      e.arc(lx, ly, 22 * sc, 0, Math.PI * 2);
      e.fill();
      leader(o, [lx + 20 * sc, ly], [1300, 680], since(k, 58.726));
      lcdCard(k, o, 1300, 600, {
        at: 58.726,
        text: "10:02:11",
        label: "P0 ALERT RAISED",
        source: "SOURCE \xB7 OPENAI ALIGNMENT REPORT \xB7 SEP 20 2026 (UPDATED SEP 25) \xB7 NO TIME ZONE GIVEN"
      });
    }
    return out(fr);
  }
  var SHOT_FN_V2 = { s007: s0072, s008: s0082, s009: s0092, s010: s0102, s011: s0112, s012: s0122, s013: s0132, s014: s0142 };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots4.js
  var H4 = 1080;
  var SEQ = [2304, 1296];
  var PLATE = [1672, 941];
  var SHADOW3 = { color: "rgba(0,0,0,0.55)", blur: 18, dy: 2 };
  var BIG_SH2 = { color: "rgba(0,0,0,0.5)", blur: 16, dy: 5 };
  var LOOK = "RUNWAY ONE \xB7 LOOK W1 \xB7 ON-CALL HOODIE COUTURE";
  function pick(k, plan) {
    let c = plan[0];
    for (const p of plan) if (shown(k, p[0])) c = p;
    return c;
  }
  function s0113(k) {
    const v = [1152, 648, 1, 0];
    const six = k.sixteenthLen(40.7859);
    const gains = [0, 1, 2, 3].map((b) => shown(k, 40.7859 + b * six) ? 1 : 0);
    const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    micro(f, LOOK, 106, 236, { size: 13, track: 3, color: "rgba(242,238,230,0.85)" });
    const words = [["ALL", 39.897, [6, 0]], ["HANDS!", 40.861, [6, 1]], ["ALL", 42.247, [6, 2]], ["NIGHT!", 42.769, [6, 3]], ["EVERYBODY,", 44.077, [7, 0]]];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur) slamWord(k, f, cur[0], cur[1], 100, 470, cur[0] === "EVERYBODY," ? 200 : 230, { marks: [cur[2]] });
    monoLine(k, o, 6, { until: 44 });
    if (shown(k, 44.077)) drawWords(k, o, W_(k, 7, [0]), 72, H4 - 46, FONT.mono, 21, {
      track: 7,
      upper: true,
      pop: false,
      color: "rgba(242,238,230,0.9)",
      shadow: { color: "rgba(0,0,0,0.6)", blur: 10 }
    });
    return { A: { tex: "seq", view: v, lod: 0 }, rows: { procedural: true, gain: gains, ambient: amb, dark: 0.08, ambDark: 0.55 } };
  }
  function s012a(k) {
    let still3 = k.shot.stills[0][0];
    for (const [key, at] of k.shot.stills) if (shown(k, at)) still3 = key;
    const hand = still3 === "p012w1-hand";
    const c = hand ? [775, 692, 3.2, 0] : [380, 420, 2.2, 0];
    const v = clampView(PLATE, c);
    const t = k.s;
    const shake = [noise1(t * 0.9, 41) * 1.6, noise1(t * 0.8, 47) * 1.2];
    const P2 = (x, y) => fwd(PLATE, v, x, y, shake);
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx, e = L.emit.ctx;
    const bp = k.beatIndexFloat(k.s) % 1;
    const pulse = 0.55 + 0.45 * Math.exp(-bp * 3.2);
    const [gx, gy] = hand ? P2(560, 690) : P2(400, 600);
    const gr = e.createRadialGradient(gx, gy, 0, gx, gy, hand ? 520 : 600);
    gr.addColorStop(0, `rgba(150,185,255,${0.22 * pulse})`);
    gr.addColorStop(1, "rgba(150,185,255,0)");
    e.fillStyle = gr;
    e.beginPath();
    e.arc(gx, gy, hand ? 520 : 600, 0, Math.PI * 2);
    e.fill();
    if (hand) {
      const ha = since(k, 45.625);
      const [x0, y0] = P2(682, 604), [x1, y1] = P2(826, 690);
      brackets(o, x0, Math.max(30, y0), x1, y1, ha, { color: INK.amber, arm: 22 });
      if (ha >= 0) {
        setFont(o, FONT.monoS, 20, 2.4);
        o.fillStyle = INK.amber;
        o.fillText("GRIP \xB7 WHITE-KNUCKLED", x0, y1 + 40);
        micro(o, "FRONT ROW \xB7 CLASSIFIER", x0, y1 + 64, { size: 12, track: 2.4 });
      }
      drawWords(k, f, W_(k, 7, [1]), 1240, 900, FONT.din, 210, { upper: true, color: INK.warm, shadow: BIG_SH2 });
    } else {
      drawWords(k, f, W_(k, 7, [1, 2]), 1250, 430, FONT.din, 170, { upper: true, color: INK.warm, space: 36, shadow: BIG_SH2, pop: false });
      drawWords(k, f, W_(k, 7, [3]), 1250, 620, FONT.din, 170, { upper: true, color: INK.warm, shadow: BIG_SH2 });
    }
    drawWords(k, o, W_(k, 7), 72, H4 - 46, FONT.mono, 21, {
      track: 7,
      upper: true,
      pop: false,
      color: "rgba(242,238,230,0.9)",
      shadow: { color: "rgba(0,0,0,0.6)", blur: 10 }
    });
    return { A: { tex: still3, view: v, lod: 0 }, shake };
  }
  function s012b(k) {
    const c = pick(k, [[46.7882, 1152, 648, 1, 0], [48.1698, 1290, 560, 1.04, 0]]);
    const v = clampView(SEQ, [c[1], c[2], c[3], c[4]]);
    const L = k.layers, f = L.feed.ctx, o = L.overlay.ctx;
    drawWords(k, f, W_(k, 8, [0, 1]), 474, 116, FONT.nim, 36, { color: INK.warm, shadow: SHADOW3, space: 11 });
    drawWords(k, f, W_(k, 8, [2]), 468, 222, FONT.din, 96, { upper: true, color: INK.warm, shadow: BIG_SH2 });
    drawWords(k, f, W_(k, 8, [3, 4]), 468, 318, FONT.din, 80, { upper: true, color: INK.warm, space: 20, shadow: BIG_SH2 });
    const lap = fwd(SEQ, v, 0.3 * 2304, 0.86 * 1296);
    leader(o, lap, [400, 828], since(k, 47.517), { color: "rgba(236,232,222,0.75)" });
    hypnogram(k, o, 60, 810, { t0: 47.517, drop: 49.307, w: 340, h: 100 });
    return { A: { tex: "seq", view: v, lod: 0 } };
  }
  var SHOT_FN_V4 = { s011: s0113, s012a, s012b };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/console2.js
  var W4 = 1920;
  var H5 = 1080;
  var AMBER = "#F2B134";
  var INKW = "rgba(240,236,228,0.92)";
  var INKD = "rgba(240,236,228,0.58)";
  var RULE = "rgba(240,236,228,0.42)";
  var INKD5 = "rgba(240,236,228,0.84)";
  function mono(ctx, text, x, y, { size = 13, track = 2.6, color = INKW, align = "left", fam = FONT.mono } = {}) {
    ctx.save();
    setFont(ctx, fam, size, track);
    ctx.textAlign = align;
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    const w = ctx.measureText(text).width;
    ctx.restore();
    return w;
  }
  function rule(ctx, x0, y, x1, color = RULE) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.fillRect(Math.min(x0, x1), Math.round(y), Math.abs(x1 - x0), 1);
    ctx.restore();
  }
  function ticketAt(s) {
    if (s < 32.934) return { id: "INC-0804", title: "BILLBOARD BEHIND A TREE", sev: "MED" };
    if (s < 36.1999) return { id: "INC-0902", title: "BUS STOP", sev: "MED" };
    if (s < 40.7859) return { id: "INC-0902", title: "FREEWAY", sev: "MED" };
    return { id: "ALL HANDS", title: "RUNWAY ONE", sev: s < 42.769 ? "MED" : "HIGH" };
  }
  function tiles(ctx, text, x, y, { accentFrom = 99, tw = 17, th = 23, gap = 2 } = {}) {
    ctx.save();
    setFont(ctx, FONT.monoS, 14, 0);
    ctx.textAlign = "center";
    let cx = x;
    [...text].forEach((ch, i) => {
      if (ch === " ") {
        cx += tw * 0.6;
        return;
      }
      ctx.fillStyle = "rgba(34,36,40,0.62)";
      ctx.fillRect(cx, y, tw, th);
      ctx.fillStyle = "rgba(0,0,0,0.45)";
      ctx.fillRect(cx, y + th / 2, tw, 1);
      ctx.fillStyle = i >= accentFrom ? AMBER : INKW;
      ctx.fillText(ch, cx + tw / 2, y + th - 6);
      cx += tw + gap;
    });
    ctx.restore();
    return cx - x;
  }
  function pagerGlyph(ctx, x, y, s, { lit = 0, bright = false } = {}) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.lineWidth = 1 / s;
    ctx.strokeStyle = lit > 0 ? "rgba(240,236,228,0.9)" : "rgba(240,236,228,0.42)";
    ctx.strokeRect(0.5, 0.5, 20, 13);
    if (lit > 0) {
      ctx.fillStyle = bright ? "#FFD27A" : AMBER;
      ctx.globalAlpha = 0.35 + 0.65 * lit;
      ctx.fillRect(3, 3, 11, 5);
    } else {
      ctx.strokeRect(3.5, 3.5, 10, 4);
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = ctx.strokeStyle;
    ctx.fillRect(16, 4, 1.5, 5);
    ctx.restore();
  }
  function bracket(ctx, x0, y0, x1, y1, arm = 5) {
    ctx.save();
    ctx.strokeStyle = INKW;
    ctx.lineWidth = 1;
    for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x1, y1, -1, -1], [x0, y1, 1, -1]]) {
      ctx.beginPath();
      ctx.moveTo(x + 0.5, y + sy * arm);
      ctx.lineTo(x + 0.5, y + 0.5);
      ctx.lineTo(x + sx * arm, y + 0.5);
      ctx.stroke();
    }
    ctx.restore();
  }
  function roster(ctx, { mode, lit, selected = [0, 1], sel = true, x = 72, y, v5 = false }) {
    const MS = v5 ? 11 : 9, MC = v5 ? INKD5 : INKD;
    const per = 8;
    if (mode === "thin") {
      mono(ctx, "FRONT ROW \xB7 ON CALL", x, y + 8, { size: MS, track: 2, color: MC });
      for (let r = 0; r < 2; r++) for (let i = 0; i < per; i++) {
        const sx = x + i * 22, sy = y + 18 + r * 16;
        pagerGlyph(ctx, sx, sy, 0.78, { lit: i / per < lit / 4 ? 1 : 0 });
        if (sel && r === selected[0] && i === selected[1]) bracket(ctx, sx - 4, sy - 4, sx + 20, sy + 14, 4);
      }
      return;
    }
    const pw = 340, ph = 214, vx = x + pw / 2, vy = y + 34;
    ctx.save();
    ctx.fillStyle = "rgba(10,11,13,0.30)";
    ctx.fillRect(x, y, pw, ph);
    rule(ctx, x, y, x + pw, "rgba(240,236,228,0.55)");
    mono(ctx, "FIG. 01 \xB7 FRONT ROW \xB7 ON CALL", x + 10, y + 18, { size: 10, track: 2 });
    mono(ctx, "ALL HANDS", x + pw - 10, y + 18, { size: 10, track: 2, color: AMBER, align: "right" });
    for (const sgn of [-1, 1]) {
      ctx.strokeStyle = "rgba(240,236,228,0.28)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(vx, vy);
      ctx.lineTo(vx + sgn * 36, y + ph - 4);
      ctx.stroke();
    }
    for (let r = 0; r < 2; r++) {
      const sgn = r === 0 ? -1 : 1;
      for (let i = 0; i < per; i++) {
        const d = Math.pow(i / (per - 1), 1.35);
        const sx = vx + sgn * (40 + 96 * d), sy = vy + 12 + (ph - 56) * d;
        const sc = 0.42 + 0.7 * d;
        const order = Math.floor(i / 2);
        const f = clamp(lit - order);
        pagerGlyph(ctx, sx - 10.5 * sc, sy - 7 * sc, sc, { lit: f, bright: f > 0 && f < 1 });
        if (sel && r === selected[0] && i === per - 1 - selected[1]) bracket(ctx, sx - 15 * sc, sy - 11 * sc, sx + 15 * sc, sy + 11 * sc, 4);
      }
    }
    ctx.restore();
  }
  function console2(k, ctx, { narrow = false, mode = "thin", lit = 0, burn = [], sel = true, v5 = false } = {}) {
    const MS = v5 ? 11 : 8.5, MC = v5 ? INKD5 : INKD;
    const s = k.s, t = ticketAt(s);
    for (const [bx, by, br, ba] of burn) {
      const g = ctx.createRadialGradient(bx, by, 0, bx, by, br);
      g.addColorStop(0, `rgba(8,9,11,${ba})`);
      g.addColorStop(0.55, `rgba(8,9,11,${ba * 0.6})`);
      g.addColorStop(1, "rgba(8,9,11,0)");
      ctx.fillStyle = g;
      ctx.fillRect(bx - br, by - br, 2 * br, 2 * br);
    }
    ctx.save();
    ctx.fillStyle = "rgba(240,236,228,0.62)";
    for (const [x2, y] of [[24, 24], [W4 - 24, 24], [24, H5 - 24], [W4 - 24, H5 - 24]]) {
      ctx.fillRect(x2 - 11, y, 23, 1);
      ctx.fillRect(x2, y - 11, 1, 23);
    }
    ctx.restore();
    const x = 72;
    const head = narrow ? `${t.id} \xB7 ${t.title}` : `${t.id} \xB7 ${t.title}`;
    const hw = mono(ctx, head, x, 61, { size: 13, track: 2.6 });
    const tw = tiles(ctx, `SEV ${t.sev}`, x, 74, { accentFrom: 4 });
    const ruleW = narrow ? Math.max(hw, tw) : Math.max(300, hw, tw);
    rule(ctx, x, 106, x + ruleW);
    if (!narrow) mono(ctx, "SHOW SCALE \xB7 LOW / MED / HIGH / CRIT", x, v5 ? 124 : 120, { size: MS, track: 1.8, color: MC });
    mono(ctx, "STATUS \xB7 PAGED", x, narrow ? 120 : v5 ? 141 : 133, { size: MS, track: 1.8, color: MC });
    roster(ctx, { mode, lit, sel, v5, y: narrow ? 138 : v5 ? 162 : 152 });
    mono(ctx, "IRIS \xB7 ALL HANDS \xB7 EP01", W4 - 72, 61, { size: 13, track: 2.6, align: "right" });
    let wave = [];
    if (k.data.wave_db) {
      const i = Math.floor((s - k.data.wave_t0) / k.data.wave_step);
      wave = k.data.wave_db.slice(Math.max(0, i - 55), i + 1);
    } else if (k.data.frame_song) wave = k.data.wave[k.data.frame_song.indexOf(s)] || [];
    const n = wave.length, bw = 2, bg = 1.4;
    const lo = Math.min(...wave), hi = Math.max(...wave);
    ctx.save();
    wave.forEach((db, i) => {
      const h = 2 + 16 * Math.pow(clamp((db - lo) / Math.max(hi - lo, 1e-3)), 1.6);
      ctx.fillStyle = i === n - 1 ? AMBER : "rgba(240,236,228,0.72)";
      ctx.fillRect(W4 - 72 - (n - i) * (bw + bg), 108 - h, bw, h);
    });
    ctx.restore();
    const ch = s < 40.7859 ? "CH 02 \xB7 STREET LOOKS" : "CH 03 \xB7 RUNWAY ONE";
    mono(ctx, ch, W4 - 72, v5 ? 128 : 126, { size: v5 ? 11 : 9, track: 2, color: MC, align: "right" });
    const mm = String(Math.floor(s / 60)).padStart(2, "0"), ss = (s % 60).toFixed(2).padStart(5, "0");
    mono(ctx, `SONG ${mm}:${ss} \xB7 BAR ${k.barNo()}`, W4 - 72, H5 - 76, { size: 13, track: 2.6, align: "right" });
    if (v5) {
      ticker(k, ctx);
      ruler(k, ctx);
    }
  }
  function ticker(k, ctx) {
    const items = (k.data.ticker || []).map((i) => i.text);
    if (!items.length) return;
    const y0 = H5 - 48, y1 = H5 - 14;
    ctx.fillStyle = "rgba(8,9,11,0.38)";
    ctx.fillRect(0, y0, W4, y1 - y0);
    rule(ctx, 0, y0, W4, "rgba(240,236,228,0.5)");
    rule(ctx, 0, y1, W4, "rgba(240,236,228,0.5)");
    ctx.save();
    setFont(ctx, FONT.mono, 13, 0);
    const adv = ctx.measureText("M").width + 2.4;
    const sep = "   *   ";
    const line = items.join(sep) + sep;
    const lw = line.length * adv;
    const x0 = -(k.s * 80 % lw);
    ctx.fillStyle = "rgba(240,236,228,0.9)";
    for (let rep = 0; x0 + rep * lw < W4; rep++) {
      for (let i = 0; i < line.length; i++) {
        const x = x0 + rep * lw + i * adv;
        if (x < -adv || x > W4 || line[i] === " ") continue;
        ctx.fillText(line[i], x, H5 - 25);
      }
    }
    ctx.restore();
  }
  function ruler(k, ctx) {
    const db = k.data.downbeats || [];
    let i = 0;
    while (i + 1 < db.length && db[i + 1] <= k.s) i++;
    const frac = db[i + 1] ? (k.s - db[i]) / (db[i + 1] - db[i]) : 0;
    const pos = i + frac;
    const PX = 88, cy = H5 / 2, x = 34;
    ctx.save();
    for (let b = Math.floor(pos) - 6; b <= Math.floor(pos) + 7; b++) {
      for (let q = 0; q < 4; q++) {
        const yy = cy + (b + q / 4 - pos) * PX;
        if (yy < 220 || yy > H5 - 80) continue;
        ctx.fillStyle = "rgba(240,236,228,0.4)";
        ctx.fillRect(x, Math.round(yy), q === 0 ? 9 : 5, 1);
        if (q === 0 && b >= 0) mono(ctx, String(b + 1).padStart(3, "0"), x + 14, yy + 3, { size: 9, track: 1.2, color: "rgba(240,236,228,0.5)" });
      }
    }
    ctx.fillStyle = AMBER;
    ctx.fillRect(x - 6, cy, 14, 1.5);
    ctx.restore();
  }
  function lyricMono(k, ctx, words, drawWords2, { index, x = 72, y = H5 - 82 } = {}) {
    mono(ctx, index, x, y - 30, { size: 11, track: 2, color: INKD5 });
    drawWords2(k, ctx, words, x, y, FONT.mono, 20, {
      track: 4.5,
      space: 18,
      upper: true,
      pop: false,
      color: "rgba(242,238,230,0.94)",
      shadow: { color: "rgba(0,0,0,0.55)", blur: 10 }
    });
  }
  function lyricLow(k, ctx, words, drawWords2, { index, x = 72, y = H5 - 92 } = {}) {
    mono(ctx, index, x, y - 50, { size: 9, track: 2, color: INKD });
    drawWords2(k, ctx, words, x, y, FONT.nim, 42, {
      color: "rgba(240,234,224,0.95)",
      shadow: { color: "rgba(0,0,0,0.45)", blur: 16, dy: 2 },
      space: 12,
      pop: false
    });
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/design.js
  var W5 = 1920;
  var H6 = 1080;
  var AMBER2 = "#F2B134";
  var COLD = "rgba(232,240,250,0.95)";
  var SHADOW4 = { color: "rgba(0,0,0,0.6)", blur: 20, dy: 2 };
  function meter(k, o) {
    const lv = (k.data.meter || [])[k.data.frame_song.indexOf(k.s)] || [-60, -60];
    const x0 = W5 - 470, y0 = H6 - 72;
    micro(o, "MASTER", x0, y0 + 9, { size: 9, track: 2, color: "rgba(236,232,222,0.6)" });
    lv.forEach((db, row) => {
      const n = Math.round(clamp((db + 48) / 48) * 24);
      for (let i = 0; i < 24; i++) {
        o.fillStyle = i < n ? i >= 20 ? AMBER2 : "rgba(236,232,222,0.85)" : "rgba(236,232,222,0.16)";
        o.fillRect(x0 + 52 + i * 6, y0 + row * 6, 4, 4);
      }
    });
  }
  function roster2(o, { mode, lit = 0, selected = [0, 1], x = 60, y = 176 }) {
    const rows = 2, per = 8;
    if (mode === "thin") {
      micro(o, "FRONT ROW \xB7 ON CALL", x, y + 8, { size: 9, track: 2, color: "rgba(236,232,222,0.6)" });
      for (let r = 0; r < rows; r++) for (let i = 0; i < per; i++) {
        const sx = x + i * 21, sy = y + 18 + r * 15;
        const on = i / per < lit / 4;
        const sel = r === selected[0] && i === selected[1];
        pagerIcon(o, sx, sy, 0.72, { body: on ? AMBER2 : "rgba(236,232,222,0.28)", lcd: "rgba(14,15,17,0.9)" });
        if (sel) {
          o.strokeStyle = AMBER2;
          o.lineWidth = 1.5;
          o.strokeRect(sx - 3.5, sy - 3.5, 22, 17);
        }
      }
      return;
    }
    const pw = 340, ph = 220, vx = x + pw / 2, vy = y + 24;
    o.save();
    o.fillStyle = "rgba(10,11,13,0.55)";
    o.fillRect(x, y, pw, ph);
    o.strokeStyle = "rgba(236,232,222,0.25)";
    o.lineWidth = 1;
    o.strokeRect(x + 0.5, y + 0.5, pw - 1, ph - 1);
    micro(o, "FRONT ROW \xB7 ON CALL", x + 12, y + 18, { size: 10, track: 2.2, color: "rgba(236,232,222,0.75)" });
    micro(o, "ALL HANDS", x + pw - 12, y + 18, { size: 10, track: 2.2, color: AMBER2, align: "right", fam: FONT.monoS });
    for (const sgn of [-1, 1]) hairline(o, vx, vy + 6, vx + sgn * 40, y + ph - 6, "rgba(236,232,222,0.35)");
    for (let r = 0; r < rows; r++) {
      const sgn = r === 0 ? -1 : 1;
      for (let i = 0; i < per; i++) {
        const u = i / (per - 1);
        const d = Math.pow(u, 1.35);
        const sx = vx + sgn * (44 + 100 * d), sy = vy + 18 + (ph - 60) * d;
        const sc = 0.42 + 0.72 * d;
        const group = 3 - Math.floor(i / 2);
        const order = 3 - group;
        const f = clamp(lit - order);
        const lighting = f > 0 && f < 1;
        o.save();
        if (f > 0) {
          o.shadowColor = `rgba(242,177,52,${lighting ? 0.95 : 0.6})`;
          o.shadowBlur = lighting ? 18 : 8;
        }
        pagerIcon(o, sx - 11 * sc, sy - 7 * sc, sc, { body: f > 0 ? lighting ? "#FFD27A" : AMBER2 : "rgba(236,232,222,0.22)", lcd: "rgba(14,15,17,0.9)" });
        o.restore();
        if (r === selected[0] && i === per - 1 - selected[1]) {
          o.strokeStyle = AMBER2;
          o.lineWidth = 1.5;
          o.strokeRect(sx - 15 * sc, sy - 11 * sc, 30 * sc, 22 * sc);
        }
      }
    }
    o.restore();
  }
  var V2 = (k) => k.data.style === 2;
  var PRINT = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  function fin(k, ret) {
    return V2(k) ? { ...ret, underPrint: true, grade: { ...ret.grade || {}, ...PRINT } } : ret;
  }
  function chrome(k, o, { narrow = false, mode = "thin", lit = 0, burn = [] } = {}) {
    if (V2(k)) {
      console2(k, o, { narrow, mode, lit, burn });
      return;
    }
    ticketCard(k, o, { accent: k.s >= 40.7859 ? "#E8E4DA" : AMBER2, narrow, icons: false });
    frameChrome(k, o);
    meter(k, o);
    roster2(o, { mode, lit, y: narrow ? 154 : 176 });
  }
  var stillView = (size, c) => clampView(size, c);
  function d1(k) {
    const size = [1672, 941];
    const v = stillView(size, [836, 470, 1, 0]);
    const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx;
    chrome(k, o, { mode: "thin", lit: 4 });
    const [lx, ly] = fwd(size, v, 492, 806);
    const steps = [
      [lx, ly],
      [lx + 60, ly],
      [lx + 60, ly + 26],
      [lx + 230, ly + 26],
      [lx + 230, ly + 8],
      [lx + 420, ly + 8],
      [lx + 420, ly + 30],
      [lx + 640, ly + 30],
      [lx + 640, ly + 4],
      [lx + 780, ly + 4]
    ];
    const leapX = lx + 780, top = ly - 330;
    if (V2(k)) {
      o.save();
      o.strokeStyle = "rgba(236,242,250,0.9)";
      o.lineWidth = 1.25;
      o.lineJoin = "miter";
      o.beginPath();
      o.moveTo(...steps[0]);
      for (const p of steps.slice(1)) o.lineTo(...p);
      o.lineTo(leapX, top);
      o.lineTo(leapX + 260, top);
      o.stroke();
      o.setLineDash([2, 4]);
      o.strokeStyle = "rgba(236,242,250,0.4)";
      o.beginPath();
      o.moveTo(lx, top);
      o.lineTo(leapX, top);
      o.stroke();
      o.restore();
      o.fillStyle = "rgba(236,242,250,0.9)";
      o.fillRect(leapX - 2, top - 2, 5, 5);
      mono(o, "SLEEP \xB7 LAST NIGHT", lx + 8, ly + 40, { size: 10, track: 2 });
      mono(o, "HIS LAPTOP \xB7 ILLUSTRATIVE CURVE", lx + 8, ly + 55, { size: 8, track: 1.6, color: "rgba(240,236,228,0.55)" });
      mono(o, "AWAKE", leapX + 14, top - 12, { size: 16, track: 4, color: "#F2B134", fam: FONT.monoS });
      mono(o, "DEEP \u2192 AWAKE \xB7 49.31", leapX + 14, top + 22, { size: 8, track: 1.6, color: "rgba(240,236,228,0.55)" });
      lyricLow(k, o, W_(k, 8), drawWords, { index: "L08 \xB7 CHORUS", x: 1150, y: 330 });
      return fin(k, { A: { tex: "D1-b", view: v, lod: 0 }, chrome: false, emitGain: 1.4 });
    }
    e.save();
    e.lineJoin = "round";
    for (const [wd, col] of [[10, "rgba(200,225,255,0.18)"], [3.2, "rgba(225,238,255,0.85)"], [1.3, "rgba(255,255,255,1)"]]) {
      e.strokeStyle = col;
      e.lineWidth = wd;
      e.beginPath();
      e.moveTo(...steps[0]);
      for (const p of steps.slice(1)) e.lineTo(...p);
      e.lineTo(leapX, top);
      e.lineTo(leapX + 300, top);
      e.stroke();
    }
    const g = e.createRadialGradient(leapX, top, 0, leapX, top, 70);
    g.addColorStop(0, "rgba(235,245,255,0.7)");
    g.addColorStop(1, "rgba(235,245,255,0)");
    e.fillStyle = g;
    e.beginPath();
    e.arc(leapX, top, 70, 0, Math.PI * 2);
    e.fill();
    e.restore();
    micro(o, "SLEEP \xB7 LAST NIGHT", lx + 8, ly + 58, { size: 11, track: 2.2, color: "rgba(225,235,248,0.8)" });
    micro(o, "ILLUSTRATIVE CURVE", lx + 8, ly + 74, { size: 9, track: 1.6, color: "rgba(225,235,248,0.5)" });
    setFont(o, FONT.monoS, 24, 3);
    o.fillStyle = COLD;
    o.fillText("AWAKE", leapX + 18, top - 14);
    drawWords(k, o, W_(k, 8), 1150, 300, FONT.nim, 46, { color: INK.warm, shadow: SHADOW4, space: 13, pop: false });
    return { A: { tex: "D1-b", view: v, lod: 0 }, chrome: false, emitGain: 1.4 };
  }
  function d2(k) {
    const size = [2304, 1296];
    const v = stillView(size, [1152, 648, 1, 0]);
    const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx, f = L.feed.ctx;
    chrome(k, o, { mode: "expanded", lit: 3.45 });
    e.save();
    e.filter = "blur(14px)";
    for (const [x, y0, len, a] of [
      [250, 840, 200, 0.26],
      [470, 790, 140, 0.2],
      [640, 760, 90, 0.16],
      [1290, 760, 90, 0.16],
      [1450, 790, 140, 0.2],
      [1660, 840, 200, 0.26]
    ]) {
      const g = e.createLinearGradient(x, y0, x, y0 + len);
      g.addColorStop(0, `rgba(242,177,52,${a})`);
      g.addColorStop(1, "rgba(242,177,52,0)");
      e.fillStyle = g;
      e.beginPath();
      e.ellipse(x, y0 + len / 2, 46, len / 2, 0, 0, Math.PI * 2);
      e.fill();
    }
    e.restore();
    if (V2(k)) {
      mono(o, "LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 846, { size: 10, track: 2.2, color: "rgba(240,236,228,0.6)" });
      o.save();
      setFont(o, FONT.din, 112, 1);
      o.shadowColor = "rgba(0,0,0,0.38)";
      o.shadowBlur = 22;
      o.shadowOffsetY = 3;
      o.fillStyle = "rgba(236,230,220,0.86)";
      o.fillText("NIGHT!", 70, 950);
      o.restore();
      k.mark(6, 3);
      mono(o, "L06 \xB7 ALL HANDS! ALL NIGHT!", 74, 990, { size: 11, track: 3.2, color: "rgba(240,236,228,0.78)" });
      return fin(k, { A: { tex: "walk", view: v, lod: 0 }, chrome: false, emitGain: 1.3 });
    }
    micro(f, "RUNWAY ONE \xB7 LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 862, { size: 12, track: 3, color: "rgba(242,238,230,0.8)" });
    setFont(f, FONT.din, 120, 0);
    f.save();
    f.shadowColor = "rgba(0,0,0,0.5)";
    f.shadowBlur = 14;
    f.shadowOffsetY = 4;
    f.fillStyle = INK.warm;
    f.fillText("NIGHT!", 70, 970);
    f.restore();
    monoLine(k, o, 6);
    return { A: { tex: "walk", view: v, lod: 0 }, chrome: false, emitGain: 1.3 };
  }
  var SCRATCH2 = [[20, 460], [115, 498], [210, 536], [305, 574], [395, 610]];
  function d3(k) {
    const size = [1672, 941];
    const v = stillView(size, [836, 470, 1, 0.01]);
    const L = k.layers, o = L.overlay.ctx, e = L.emit.ctx, f = L.feed.ctx;
    chrome(k, o, { narrow: true, mode: "thin", lit: 0, burn: [[170, 120, 390, 0.86], [330, 1015, 540, 0.82]] });
    const P2 = (x, y) => fwd(size, v, x, y);
    f.save();
    const [nx, ny] = P2(56, 560);
    const sc = 1.148 * v[2];
    f.translate(nx, ny);
    f.rotate(v[3]);
    f.scale(sc, sc);
    setFont(f, FONT.din, 150, 2);
    f.fillStyle = "rgba(20,22,25,0.86)";
    f.fillText("NOT", 0, 0);
    f.restore();
    e.save();
    e.lineCap = "round";
    const pts = SCRATCH2.map(([x, y]) => P2(x, y));
    const g = e.createLinearGradient(...pts[0], ...pts[pts.length - 1]);
    g.addColorStop(0, "rgba(242,177,52,0.0)");
    g.addColorStop(0.45, "rgba(255,196,96,0.95)");
    g.addColorStop(0.7, "rgba(242,177,52,0.5)");
    g.addColorStop(1, "rgba(242,177,52,0.15)");
    for (const [wd, a] of [[12, 0.25], [4, 0.8], [1.6, 1]]) {
      e.globalAlpha = a;
      e.strokeStyle = g;
      e.lineWidth = wd;
      e.beginPath();
      e.moveTo(...pts[0]);
      for (const p of pts.slice(1)) e.lineTo(...p);
      e.stroke();
    }
    const [gx, gy] = P2(170, 518);
    const rg = e.createRadialGradient(gx, gy, 0, gx, gy, 90);
    rg.addColorStop(0, "rgba(255,190,90,0.55)");
    rg.addColorStop(1, "rgba(255,190,90,0)");
    e.globalAlpha = 1;
    e.fillStyle = rg;
    e.beginPath();
    e.arc(gx, gy, 90, 0, Math.PI * 2);
    e.fill();
    e.restore();
    if (V2(k)) {
      lyricLow(k, o, W_(k, 4, [7, 8, 9, 10]), drawWords, { index: "L04 \xB7 VERSE 1", y: H6 - 96 });
      mono(o, "SOURCE \xB7 BUS-SHELTER AD \xB7 SF STANDARD \xB7 SEP 2 2026", 74, H6 - 60, { size: 9, track: 1.8, color: "rgba(240,236,228,0.6)" });
      return fin(k, { A: { tex: "X09b", view: v, lod: 0 }, chrome: false, emitGain: 1.3, tint: [0.97, 1, 1.035] });
    }
    drawWords(k, o, W_(k, 4, [7, 8, 9, 10]), 72, H6 - 92, FONT.nim, 44, { color: INK.warm, shadow: SHADOW4, space: 12, pop: false });
    micro(o, "SOURCE \xB7 BUS-SHELTER AD \xB7 SF STANDARD \xB7 SEP 2 2026", 74, H6 - 56, { size: 11, track: 1.6 });
    return { A: { tex: "X09b", view: v, lod: 0 }, chrome: false, emitGain: 1.3, tint: [0.97, 1, 1.035] };
  }
  var SHOT_FN_DESIGN = { d1, d2, d3 };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots5.js
  var W6 = 1920;
  var H7 = 1080;
  var PLATE2 = [1672, 941];
  var SEQ2 = [2304, 1296];
  var INKD2 = "rgba(240,236,228,0.58)";
  var PRINT2 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  var fin2 = (ret) => ({ ...ret, chrome: false, underPrint: true, grade: { ...PRINT2, ...ret.grade || {} } });
  function still(k) {
    let key = k.shot.stills[0][0];
    for (const [kk, at] of k.shot.stills) if (shown(k, at)) key = kk;
    return key;
  }
  function crop(k, plan, seed, size = PLATE2) {
    let c = plan[0];
    for (const p of plan) if (shown(k, p[0])) c = p;
    const v = clampView(size, [c[1], c[2], c[3], c[4]]);
    const shake = [noise1(k.s * 0.9, seed) * 2, noise1(k.s * 0.8, seed + 7) * 1.5];
    return { v, shake };
  }
  function bigWord(k, ctx, text, ts, mark, { x = 70, y = 900, size = 112 } = {}) {
    const a = since(k, ts);
    if (a < 0) return;
    const sc = a >= 3 ? 1 : [1.12, 1.04, 1.01][a];
    ctx.save();
    setFont(ctx, FONT.din, size, 1);
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    ctx.shadowColor = "rgba(0,0,0,0.38)";
    ctx.shadowBlur = 22;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = "rgba(236,230,220,0.86)";
    ctx.fillText(text, 0, 0);
    ctx.restore();
    k.mark(...mark);
  }
  var lyric = (k, o, li, idx, opts = {}) => lyricLow(k, o, W_(k, li), drawWords, { index: idx, y: H7 - 96, ...opts });
  var BILL = [50, 318, 326, 485];
  function s0103(k) {
    const key = still(k);
    const { v, shake } = crop(k, [
      [36.1999, 836, 470, 1, 0],
      [37.0939, 643, 400, 1.3, 0.012],
      [38.9399, 760, 420, 1.12, -0.01],
      [39.8454, 836, 470, 1, 0]
    ], 4);
    const kickA = k.s - 38.9399;
    if (kickA >= 0 && kickA < 0.3) {
      shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08);
      shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08);
    }
    const o = k.layers.overlay.ctx;
    console2(k, o, { mode: "thin", lit: 0, sel: false });
    if (key === "X10a") {
      const a = since(k, 37.226);
      if (a >= 0) {
        const [x0, y0] = fwd(PLATE2, v, BILL[0], BILL[1], shake), [x1, y1] = fwd(PLATE2, v, BILL[2], BILL[3], shake);
        o.save();
        o.strokeStyle = "rgba(240,236,228,0.85)";
        o.lineWidth = 1;
        for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x1, y1, -1, -1], [x0, y1, 1, -1]]) {
          o.beginPath();
          o.moveTo(x, y + sy * 10);
          o.lineTo(x, y);
          o.lineTo(x + sx * 10, y);
          o.stroke();
        }
        const lx = x0, ly = y0 - 64;
        o.fillStyle = "rgba(240,236,228,0.5)";
        o.fillRect(lx, ly + 12, Math.max(320, x1 - x0), 1);
        o.restore();
        mono(o, "GRAFFITI \xB7 AI-RECEPTIONIST BILLBOARD \xB7 US-101", lx, ly - 4, { size: 9, track: 1.8, color: INKD2 });
        const txt = "SF HATES AI BILLBOARS!!!";
        const n = clamp(Math.floor((k.s - 37.226) / (38.69 - 37.226) * txt.length) + 1, 1, txt.length);
        const w = mono(o, txt.slice(0, n), lx, ly + 34, { size: 17, track: 2.4 });
        if (shown(k, 38.69)) {
          o.save();
          setFont(o, FONT.mono, 17, 2.4);
          const pre = o.measureText("SF HATES AI ").width, bw = o.measureText("BILLBOARS").width;
          o.strokeStyle = AMBER;
          o.lineWidth = 1.2;
          o.beginPath();
          for (let xx = 0; xx <= bw; xx += 2) o.lineTo(lx + pre + xx, ly + 42 + Math.sin(xx / 3) * 1.6);
          o.stroke();
          o.restore();
        }
        if (shown(k, 38.751)) mono(o, "SUGGEST \xB7 BILLBOARDS", lx, ly + 60, { size: 9, track: 1.8, color: INKD2 });
        if (shown(k, 39.674)) mono(o, "IGNORED", lx + 190, ly + 60, { size: 9, track: 1.8, color: AMBER, fam: FONT.monoS });
        mono(o, "SOURCE \xB7 SF STANDARD \xB7 SEP 2 2026", lx, ly + 76, { size: 8, track: 1.6, color: "rgba(240,236,228,0.42)" });
        void w;
      }
    } else {
      mono(o, "LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 790, { size: 10, track: 2.2, color: INKD2 });
      bigWord(k, o, "ALL", 39.897, [6, 0]);
    }
    if (k.s < 40.055 + 0.4) lyric(k, o, 5, "L05 \xB7 VERSE 1");
    else lyric(k, o, 6, "L06 \xB7 CHORUS");
    return fin2({ A: { tex: key, view: v, lod: 0 }, shake });
  }
  function s0114(k) {
    const six = k.sixteenthLen(40.7859);
    const gains = [0, 1, 2, 3].map((b) => shown(k, 40.7859 + b * six) ? 1 : 0);
    const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
    const o = k.layers.overlay.ctx;
    const lit = clamp((k.s - 40.7859) / six + 0, 0, 4);
    console2(k, o, { mode: "expanded", lit, sel: shown(k, 44.077) });
    mono(o, "LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 790, { size: 10, track: 2.2, color: INKD2 });
    const words = [["ALL", 39.897, [6, 0]], ["HANDS!", 40.861, [6, 1]], ["ALL", 42.247, [6, 2]], ["NIGHT!", 42.769, [6, 3]], ["EVERYBODY,", 44.077, [7, 0]]];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur) bigWord(k, o, cur[0], cur[1], cur[2]);
    if (k.s < 44.077 - 0.04) lyric(k, o, 6, "L06 \xB7 CHORUS");
    else lyric(k, o, 7, "L07 \xB7 CHORUS");
    return fin2({ A: { tex: "seq", view: [1152, 648, 1, 0], lod: 0 }, rows: { procedural: true, gain: gains, ambient: amb, dark: 0.08, ambDark: 0.55 } });
  }
  function s012a2(k) {
    const key = still(k);
    const hand = key === "p012w1-hand";
    const v = clampView(PLATE2, hand ? [775, 692, 3.2, 0] : [380, 420, 2.2, 0]);
    const shake = [noise1(k.s * 0.9, 41) * 1.6, noise1(k.s * 0.8, 47) * 1.2];
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
    console2(k, o, { mode: "expanded", lit: 4, sel: true });
    const bp = k.beatIndexFloat(k.s) % 1;
    const pulse = 0.55 + 0.45 * Math.exp(-bp * 3.2);
    const [gx, gy] = fwd(PLATE2, v, hand ? 560 : 400, hand ? 690 : 600, shake);
    const gr = e.createRadialGradient(gx, gy, 0, gx, gy, hand ? 520 : 600);
    gr.addColorStop(0, `rgba(150,185,255,${0.22 * pulse})`);
    gr.addColorStop(1, "rgba(150,185,255,0)");
    e.fillStyle = gr;
    e.beginPath();
    e.arc(gx, gy, hand ? 520 : 600, 0, Math.PI * 2);
    e.fill();
    lyric(k, o, 7, "L07 \xB7 CHORUS");
    return fin2({ A: { tex: key, view: v, lod: 0 }, shake });
  }
  function sleepLine(k, o, x0, y0, len, { leapX, top }) {
    const steps = [[0, 0], [60, 0], [60, 26], [230, 26], [230, 8], [420, 8], [420, 30], [640, 30], [640, 4], [len, 4]];
    const grow = clamp((k.s - 47.517) / (49.307 - 47.517));
    const reach = 0.12 + 0.88 * grow;
    o.save();
    o.strokeStyle = "rgba(236,242,250,0.9)";
    o.lineWidth = 1.25;
    o.beginPath();
    o.moveTo(x0, y0);
    for (const [dx, dy] of steps.slice(1)) {
      if (dx / len > reach) {
        o.lineTo(x0 + len * reach, y0 + dy);
        break;
      }
      o.lineTo(x0 + dx, y0 + dy);
    }
    const la = since(k, 49.307);
    if (la >= 0) {
      const e = easeOutCubic(clamp((la + 1) / 3));
      o.lineTo(leapX, y0 + 4 + (top - y0 - 4) * e);
      if (e >= 1) o.lineTo(leapX + 240, top);
    }
    o.stroke();
    if (la >= 0) {
      o.setLineDash([2, 4]);
      o.strokeStyle = "rgba(236,242,250,0.4)";
      o.beginPath();
      o.moveTo(x0, top);
      o.lineTo(leapX, top);
      o.stroke();
    }
    o.restore();
    mono(o, "SLEEP \xB7 LAST NIGHT", x0 + 8, y0 + 40, { size: 10, track: 2 });
    mono(o, "HIS LAPTOP \xB7 ILLUSTRATIVE CURVE", x0 + 8, y0 + 55, { size: 8, track: 1.6, color: INKD2 });
    if (shown(k, 49.89)) {
      mono(o, "AWAKE", leapX + 14, top - 12, { size: 16, track: 4, color: AMBER, fam: FONT.monoS });
      mono(o, "DEEP \u2192 AWAKE \xB7 49.31", leapX + 14, top + 22, { size: 8, track: 1.6, color: INKD2 });
    }
  }
  function s012b2(k) {
    const v = clampView(SEQ2, [1152, 648, 1, 0]);
    const o = k.layers.overlay.ctx;
    console2(k, o, { mode: "thin", lit: 4, sel: true });
    if (shown(k, 47.517)) {
      const [lx, ly] = fwd(SEQ2, v, 0.2 * 2304, 0.75 * 1296);
      sleepLine(k, o, lx, ly, 900, { leapX: lx + 900, top: ly - 300 });
    }
    lyric(k, o, 8, "L08 \xB7 CHORUS");
    return fin2({ A: { tex: "seq", view: v, lod: 0 } });
  }
  function s012c(k) {
    const v = clampView(PLATE2, [836, 470, 1, 0]);
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
    console2(k, o, { mode: "thin", lit: 4, sel: true });
    const bp = k.beatIndexFloat(k.s) % 1;
    const pulse = 0.6 + 0.4 * Math.exp(-bp * 3);
    const [gx, gy] = fwd(PLATE2, v, 420, 880);
    const gr = e.createRadialGradient(gx, gy, 0, gx, gy, 700);
    gr.addColorStop(0, `rgba(170,200,255,${0.2 * pulse})`);
    gr.addColorStop(1, "rgba(170,200,255,0)");
    e.fillStyle = gr;
    e.beginPath();
    e.arc(gx, gy, 700, 0, Math.PI * 2);
    e.fill();
    const [lx, ly] = fwd(PLATE2, v, 492, 806);
    sleepLine(k, o, lx, ly, 780, { leapX: lx + 780, top: ly - 330 });
    lyric(k, o, 8, "L08 \xB7 CHORUS", { x: 1150, y: 330 });
    mono(o, "PLACEHOLDER STILL \xB7 CLOSE-UP CLIP TO COME", W6 - 72, H7 - 112, { size: 9, track: 2, color: "rgba(240,236,228,0.5)", align: "right" });
    return fin2({ A: { tex: "D1-b", view: v, lod: 0 } });
  }
  var SHOT_FN_V5 = { s010: s0103, s011: s0114, s012a: s012a2, s012b: s012b2, s012c };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots6.js
  var PLATE3 = [1672, 941];
  var SEQ3 = [2304, 1296];
  var INKD3 = "rgba(240,236,228,0.58)";
  var PRINT3 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  var fin3 = (ret) => ({ ...ret, chrome: false, underPrint: true, grade: { ...PRINT3, ...ret.grade || {} } });
  function still2(k) {
    let key = k.shot.stills[0][0];
    for (const [kk, at] of k.shot.stills) if (shown(k, at)) key = kk;
    return key;
  }
  function crop2(k, plan, seed, size = PLATE3) {
    let c = plan[0];
    for (const p of plan) if (shown(k, p[0])) c = p;
    const v = clampView(size, [c[1], c[2], c[3], c[4]]);
    const shake = [noise1(k.s * 0.9, seed) * 2, noise1(k.s * 0.8, seed + 7) * 1.5];
    return { v, shake };
  }
  function bigWord2(k, ctx, text, ts, mark, { x = 70, y = 900, size = 112 } = {}) {
    const a = since(k, ts);
    if (a < 0) return;
    const sc = a >= 3 ? 1 : [1.12, 1.04, 1.01][a];
    ctx.save();
    setFont(ctx, FONT.din, size, 1);
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    ctx.shadowColor = "rgba(0,0,0,0.38)";
    ctx.shadowBlur = 22;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = "rgba(236,230,220,0.86)";
    ctx.fillText(text, 0, 0);
    ctx.restore();
    k.mark(...mark);
  }
  var lyric2 = (k, o, li, idx, opts = {}) => lyricMono(k, o, W_(k, li), drawWords, { index: idx, ...opts });
  var BILL2 = [50, 318, 326, 485];
  function s0104(k) {
    const key = still2(k);
    const { v, shake } = crop2(k, [
      [36.1999, 836, 470, 1, 0],
      [37.0939, 643, 400, 1.3, 0.012],
      [38.9399, 760, 420, 1.12, -0.01],
      [39.8454, 836, 470, 1, 0]
    ], 4);
    const kickA = k.s - 38.9399;
    if (kickA >= 0 && kickA < 0.3) {
      shake[0] += Math.sin(kickA * 90) * 6 * Math.exp(-kickA / 0.08);
      shake[1] += Math.cos(kickA * 70) * 3.5 * Math.exp(-kickA / 0.08);
    }
    const o = k.layers.overlay.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 0, sel: false });
    if (key === "X10a") {
      const a = since(k, 37.226);
      if (a >= 0) {
        const [x0, y0] = fwd(PLATE3, v, BILL2[0], BILL2[1], shake), [x1, y1] = fwd(PLATE3, v, BILL2[2], BILL2[3], shake);
        o.save();
        o.strokeStyle = "rgba(240,236,228,0.85)";
        o.lineWidth = 1;
        for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x1, y1, -1, -1], [x0, y1, 1, -1]]) {
          o.beginPath();
          o.moveTo(x, y + sy * 10);
          o.lineTo(x, y);
          o.lineTo(x + sx * 10, y);
          o.stroke();
        }
        const lx = Math.max(x0, 84), ly = y0 - 64;
        o.fillStyle = "rgba(240,236,228,0.5)";
        o.fillRect(lx, ly + 12, Math.max(320, x1 - x0), 1);
        o.restore();
        mono(o, "GRAFFITI \xB7 AI-RECEPTIONIST BILLBOARD \xB7 US-101", lx, ly - 4, { size: 9, track: 1.8, color: INKD3 });
        const txt = "SF HATES AI BILLBOARS!!!";
        const n = clamp(Math.floor((k.s - 37.226) / (38.69 - 37.226) * txt.length) + 1, 1, txt.length);
        const w = mono(o, txt.slice(0, n), lx, ly + 34, { size: 17, track: 2.4 });
        if (shown(k, 38.69)) {
          o.save();
          setFont(o, FONT.mono, 17, 2.4);
          const pre = o.measureText("SF HATES AI ").width, bw = o.measureText("BILLBOARS").width;
          o.strokeStyle = AMBER;
          o.lineWidth = 1.2;
          o.beginPath();
          for (let xx = 0; xx <= bw; xx += 2) o.lineTo(lx + pre + xx, ly + 42 + Math.sin(xx / 3) * 1.6);
          o.stroke();
          o.restore();
        }
        if (shown(k, 38.751)) mono(o, "SUGGEST \xB7 BILLBOARDS", lx, ly + 60, { size: 9, track: 1.8, color: INKD3 });
        if (shown(k, 39.674)) mono(o, "IGNORED", lx + 190, ly + 60, { size: 9, track: 1.8, color: AMBER, fam: FONT.monoS });
        mono(o, "SOURCE \xB7 SF STANDARD \xB7 SEP 2 2026", lx, ly + 76, { size: 8, track: 1.6, color: "rgba(240,236,228,0.42)" });
        void w;
      }
    } else {
      mono(o, "LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 790, { size: 10, track: 2.2, color: INKD3 });
      bigWord2(k, o, "ALL", 39.897, [6, 0]);
    }
    if (k.s < 40.055 + 0.4) lyric2(k, o, 5, "L05 \xB7 VERSE 1");
    else lyric2(k, o, 6, "L06 \xB7 CHORUS");
    return fin3({ A: { tex: key, view: v, lod: 0 }, shake });
  }
  function s0115(k) {
    const six = k.sixteenthLen(40.7859);
    const gains = [0, 1, 2, 3].map((b) => shown(k, 40.7859 + b * six) ? 1 : 0);
    const amb = [0, 1, 2, 3].reduce((acc, b) => acc + clamp((since(k, 40.7859 + b * six) + 1) / 3), 0) / 4;
    const o = k.layers.overlay.ctx;
    const lit = clamp((k.s - 40.7859) / six + 0, 0, 4);
    console2(k, o, { v5: true, mode: "expanded", lit, sel: shown(k, 44.077) });
    mono(o, "LOOK W1 \xB7 ON-CALL HOODIE COUTURE", 74, 790, { size: 10, track: 2.2, color: INKD3 });
    const words = [["ALL", 39.897, [6, 0]], ["HANDS!", 40.861, [6, 1]], ["ALL", 42.247, [6, 2]], ["NIGHT!", 42.769, [6, 3]]];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur && !shown(k, 44.077)) bigWord2(k, o, cur[0], cur[1], cur[2]);
    if (k.s < 44.077 - 0.04) lyric2(k, o, 6, "L06 \xB7 CHORUS \xB7 ALL HANDS");
    else lyric2(k, o, 7, "L07 \xB7 CHORUS");
    return fin3({ A: { tex: "seq", view: [1152, 648, 1, 0], lod: 0 }, rows: { procedural: true, gain: gains, ambient: amb, dark: 0.08, ambDark: 0.55 } });
  }
  function s012a3(k) {
    const key = still2(k);
    const hand = key === "p012w1-hand";
    const v = clampView(PLATE3, hand ? [775, 692, 3.2, 0] : [380, 420, 2.2, 0]);
    const shake = [noise1(k.s * 0.9, 41) * 1.6, noise1(k.s * 0.8, 47) * 1.2];
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
    console2(k, o, { v5: true, mode: "expanded", lit: 4, sel: true });
    const bp = k.beatIndexFloat(k.s) % 1;
    const pulse = 0.55 + 0.45 * Math.exp(-bp * 3.2);
    const [gx, gy] = fwd(PLATE3, v, hand ? 560 : 400, hand ? 690 : 600, shake);
    const gr = e.createRadialGradient(gx, gy, 0, gx, gy, hand ? 520 : 600);
    gr.addColorStop(0, `rgba(150,185,255,${0.22 * pulse})`);
    gr.addColorStop(1, "rgba(150,185,255,0)");
    e.fillStyle = gr;
    e.beginPath();
    e.arc(gx, gy, hand ? 520 : 600, 0, Math.PI * 2);
    e.fill();
    lyric2(k, o, 7, "L07 \xB7 CHORUS");
    return fin3({ A: { tex: key, view: v, lod: 0 }, shake });
  }
  function s012b3(k) {
    const punched = shown(k, k.shot.punch);
    const v = clampView(SEQ3, punched ? [790, 905, 1.8, 0] : [1152, 648, 1, 0]);
    const o = k.layers.overlay.ctx, e = k.layers.emit.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    const S = 1.2;
    const [ax, ay] = fwd(SEQ3, v, 520 * S, 868 * S), [bx, by] = fwd(SEQ3, v, 828 * S, 782 * S);
    const grow = clamp((k.s - 47.517) / (50.32 - 47.517));
    if (shown(k, 47.517)) {
      o.save();
      o.strokeStyle = "rgba(236,242,250,0.9)";
      o.lineWidth = punched ? 1.6 : 1.2;
      const n = 9, pts = [];
      for (let i = 0; i <= n; i++) {
        const u = i / n, dy = [0, 10, 10, 4, 4, 12, 12, 2, 2, 0][i] * (punched ? 1.8 : 1);
        pts.push([ax + (bx - ax) * u, ay + (by - ay) * u - 14 * (punched ? 1.8 : 1) - dy]);
      }
      const upto = punched ? n : Math.max(1, Math.round(grow * n));
      o.beginPath();
      o.moveTo(...pts[0]);
      for (let i = 1; i <= upto; i++) o.lineTo(...pts[i]);
      o.stroke();
      const la = since(k, k.shot.punch);
      if (la >= 0) {
        const eu = easeOutCubic(clamp((la + 1) / 3));
        const top = 300;
        const [px_, py_] = pts[n];
        o.beginPath();
        o.moveTo(px_, py_);
        o.lineTo(px_, py_ + (top - py_) * eu);
        if (eu >= 1) o.lineTo(px_ + 60, top);
        o.stroke();
        o.setLineDash([2, 4]);
        o.strokeStyle = "rgba(236,242,250,0.4)";
        o.beginPath();
        o.moveTo(pts[0][0], top);
        o.lineTo(px_, top);
        o.stroke();
        o.restore();
        mono(o, "SLEEP \xB7 LAST NIGHT", pts[0][0], py_ + 70, { size: 11, track: 2 });
        mono(o, "HIS LAPTOP \xB7 ILLUSTRATIVE CURVE", pts[0][0], py_ + 88, { size: 10, track: 1.6, color: "rgba(240,236,228,0.8)" });
        if (eu >= 1) {
          o.fillStyle = AMBER;
          o.fillRect(px_ - 3, top - 3, 7, 7);
          bigWord2(k, o, "AWAKE", k.shot.punch + 2 / 24, [8, 4], { x: px_ + 76, y: top + 40, size: 120 });
        }
      } else o.restore();
    }
    lyric2(k, o, 8, "L08 \xB7 CHORUS");
    return fin3({ A: { tex: "seq", view: v, lod: 0 } });
  }
  var SHOT_FN_V6 = { s010: s0104, s011: s0115, s012a: s012a3, s012b: s012b3 };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots7.js
  var SEQ4 = [2304, 1296];
  var PRINT4 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  function s012c2(k) {
    const o = k.layers.overlay.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    lyricMono(k, o, W_(k, 8), drawWords, { index: "L08 \xB7 CHORUS" });
    return { A: { tex: "seq", view: clampView(SEQ4, [1152, 648, 1, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT4 } };
  }
  var s012d = (k) => SHOT_FN_V6.s012b(k);
  var SHOT_FN_V7 = { ...SHOT_FN_V6, s012c: s012c2, s012d };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/shots8.js
  var H8 = 1080;
  var PLATE4 = [1672, 941];
  var SEQ5 = [2304, 1296];
  var PRINT5 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  var fin4 = (ret) => ({ ...ret, chrome: false, underPrint: true, grade: { ...PRINT5, ...ret.grade || {} } });
  function bigWord3(k, ctx, text, ts, mark, { x = 70, y = 900, size = 112 } = {}) {
    const a = since(k, ts);
    if (a < 0) return;
    const sc = a >= 3 ? 1 : [1.12, 1.04, 1.01][a];
    ctx.save();
    setFont(ctx, FONT.din, size, 1);
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    ctx.shadowColor = "rgba(0,0,0,0.38)";
    ctx.shadowBlur = 22;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = "rgba(236,230,220,0.86)";
    ctx.fillText(text, 0, 0);
    ctx.restore();
    k.mark(...mark);
  }
  function masthead(k, o, pos, until = 58.6) {
    const words = [["ALL", 53.767, [10, 0]], ["HANDS!", 54.59, [10, 1]], ["ALL", 55.152, [10, 2]], ["NIGHT!", 55.513, [10, 3]]];
    let cur = null;
    for (const w of words) if (shown(k, w[1])) cur = w;
    if (cur && k.s < until) bigWord3(k, o, cur[0], cur[1], cur[2], pos);
  }
  var IDX = { 8: "L08 \xB7 CHORUS", 9: "L09 \xB7 CHORUS", 10: "L10 \xB7 CHORUS \xB7 ALL HANDS", 11: "L11 \xB7 POST-CHORUS" };
  function lyrics(k, o) {
    const act = [];
    for (const li of [8, 9, 10, 11]) {
      const ws = W_(k, li);
      if (!ws.length) continue;
      if (k.s >= ws[0].start - 0.05 && k.s <= ws[ws.length - 1].end + 0.4) act.push(li);
    }
    act.slice(-2).reverse().forEach((li, i) => lyricMono(k, o, W_(k, li), drawWords, { index: IDX[li], y: H8 - 82 - i * 64 }));
  }
  var SCR = { tl: [905, 358], tr: [1090, 394], bl: [753, 631], w: 188, h: 312 };
  function s013a(k) {
    const u = clamp((k.s - 50.933) / (52.3146 - 50.933));
    const v = clampView(PLATE4, [900 + 20 * u, 560 - 20 * u, 1.55 + 0.35 * u, 0]);
    const shake = [noise1(k.s * 0.9, 61) * 1.6, noise1(k.s * 0.8, 67) * 1.2];
    const o = k.layers.overlay.ctx, f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    const P2 = (x, y) => fwd(PLATE4, v, x, y, shake);
    const [tlx, tly] = P2(...SCR.tl), [trx, try_] = P2(...SCR.tr), [blx, bly] = P2(...SCR.bl);
    f.save();
    f.setTransform((trx - tlx) / SCR.w, (try_ - tly) / SCR.w, (blx - tlx) / SCR.h, (bly - tly) / SCR.h, tlx, tly);
    const a = since(k, 51.76);
    const lit = a < 0 ? 0 : a === 0 ? 0.55 : 1;
    f.beginPath();
    f.roundRect(4, 4, SCR.w - 8, SCR.h - 8, 18);
    f.fillStyle = `rgba(${Math.round(14 + 214 * lit)},${Math.round(16 + 220 * lit)},${Math.round(20 + 226 * lit)},0.97)`;
    f.fill();
    if (lit > 0) {
      f.globalAlpha = lit;
      setFont(f, FONT.monoS, 10, 1.6);
      f.fillStyle = "rgba(20,22,26,0.75)";
      f.textAlign = "center";
      f.fillText("INCOMING \xB7 SEV-HIGH", SCR.w / 2, 46);
      f.fillStyle = "rgba(20,22,26,0.3)";
      f.fillRect(24, 58, SCR.w - 48, 1);
      setFont(f, FONT.din, 40, 0.5);
      f.fillStyle = "rgba(16,18,22,0.92)";
      f.fillText("INCIDENT", SCR.w / 2, 112);
      f.fillText("WEEK", SCR.w / 2, 152);
      f.lineWidth = 1.2;
      f.strokeStyle = "rgba(20,22,26,0.35)";
      f.beginPath();
      f.arc(52, 248, 20, 0, Math.PI * 2);
      f.stroke();
      f.beginPath();
      f.moveTo(38, 262);
      f.lineTo(66, 234);
      f.stroke();
      f.strokeStyle = "rgba(20,22,26,0.85)";
      f.beginPath();
      f.arc(SCR.w - 52, 248, 20, 0, Math.PI * 2);
      f.stroke();
      setFont(f, FONT.mono, 8, 1.2);
      f.fillStyle = "rgba(20,22,26,0.6)";
      f.fillText("DECLINE \xB7 DISABLED", 52, 286);
      f.globalAlpha = 1;
    }
    f.restore();
    if (lit > 0) {
      const cx = (tlx + trx + blx + (trx + blx - tlx)) / 4, cy = (tly + try_ + bly + (try_ + bly - tly)) / 4;
      const g = e.createRadialGradient(cx, cy, 0, cx, cy, 520);
      g.addColorStop(0, `rgba(200,220,250,${0.22 * lit})`);
      g.addColorStop(1, "rgba(200,220,250,0)");
      e.fillStyle = g;
      e.beginPath();
      e.arc(cx, cy, 520, 0, Math.PI * 2);
      e.fill();
    }
    lyrics(k, o);
    return fin4({ A: { tex: "INS13-a", view: v, lod: 0 }, shake });
  }
  function s013b(k) {
    const o = k.layers.overlay.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    masthead(k, o, { x: 1300, y: 640 });
    lyrics(k, o);
    return fin4({ A: { tex: "seq", view: clampView(SEQ5, [1152, 648, 1, 0]), lod: 0 } });
  }
  function s0143(k) {
    const o = k.layers.overlay.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    masthead(k, o, { x: 70, y: 860 });
    lyrics(k, o);
    return fin4({ A: { tex: "seq", view: clampView(SEQ5, [1152, 648, 1, 0]), lod: 0 } });
  }
  function s014p(k) {
    const o = k.layers.overlay.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    masthead(k, o, { x: 70, y: 860 });
    lyrics(k, o);
    const K = k.shot.punch.keys;
    let j = 0;
    while (j < K.length - 2 && k.f >= K[j + 1].f) j++;
    const a = K[j], b = K[Math.min(j + 1, K.length - 1)];
    const u = b.f > a.f ? clamp((k.f - a.f) / (b.f - a.f)) : 0;
    const L = (p, q) => p + (q - p) * u;
    return fin4({ A: { tex: "seq", view: clampView(SEQ5, [L(a.cx, b.cx), L(a.cy, b.cy), L(a.z, b.z), 0]), lod: 0 } });
  }
  var LCD = { x0: 756, y0: 453, x1: 894, y1: 509 };
  function s014c(k) {
    const u = clamp((k.s - 58.7697) / (59.2341 - 58.7697));
    const v = clampView(PLATE4, [835, 480, 1.25 + 0.1 * u, 0]);
    const shake = [noise1(k.s * 0.9, 71) * 1.4, noise1(k.s * 0.8, 73) * 1];
    const o = k.layers.overlay.ctx, f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    console2(k, o, { v5: true, mode: "thin", lit: 4, sel: true });
    f.save();
    srcTransform(f, PLATE4, v, shake);
    const w = LCD.x1 - LCD.x0, h = LCD.y1 - LCD.y0;
    const g = f.createLinearGradient(LCD.x0, LCD.y0, LCD.x0, LCD.y1);
    g.addColorStop(0, "#E9A62C");
    g.addColorStop(0.5, AMBER);
    g.addColorStop(1, "#D9971F");
    f.fillStyle = g;
    f.beginPath();
    f.roundRect(LCD.x0 + 3, LCD.y0 + 3, w - 6, h - 6, 4);
    f.fill();
    setFont(f, FONT.monoS, 34, 3);
    f.fillStyle = "rgba(46,30,6,0.9)";
    f.textAlign = "center";
    f.fillText("10:02", (LCD.x0 + LCD.x1) / 2, LCD.y1 - 14);
    f.restore();
    const [cx, cy] = fwd(PLATE4, v, (LCD.x0 + LCD.x1) / 2, (LCD.y0 + LCD.y1) / 2, shake);
    const gl = e.createRadialGradient(cx, cy, 0, cx, cy, 240);
    gl.addColorStop(0, "rgba(242,177,52,0.28)");
    gl.addColorStop(1, "rgba(242,177,52,0)");
    e.fillStyle = gl;
    e.beginPath();
    e.arc(cx, cy, 240, 0, Math.PI * 2);
    e.fill();
    lyrics(k, o);
    return fin4({ A: { tex: "INS14-b", view: v, lod: 0 }, shake });
  }
  var SHOT_FN_V8 = { ...SHOT_FN_V7, s013a, s013b, s014a: s0143, s014b: s0143, s014p, s014c };

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/bake.js
  var W7 = 1920;
  var H9 = 1080;
  var PRINT6 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  function bakeShot(k) {
    const m = k.shot.move, lf = k.f - k.shot.f0;
    const t = Math.min(1, Math.max(0, (lf - m.push.from) / Math.max(1, m.push.to - m.push.from)));
    const push = 1 + (m.push.scale - 1) * t;
    let cut = null;
    for (const c of m.cuts) if (c.at <= lf) cut = c;
    const tex = cut && cut.kind === "pixel" && lf === cut.at && m.mosaic ? m.mosaic : m.src;
    const cs = cut ? cut.scale : 1, co = cut ? [cut.ox, cut.oy] : [0, 0];
    const z = push * cs;
    const b = [push * (co[0] - cs * co[0] - m.push.ox) + m.push.ox, push * (co[1] - cs * co[1] - m.push.oy) + m.push.oy];
    const size = m.size, fit = fitOf(size);
    const off = [(W7 - size[0] * fit) / 2, (H9 - size[1] * fit) / 2];
    const view = [((W7 / 2 - b[0]) / z - off[0]) / fit, ((H9 / 2 - b[1]) / z - off[1]) / fit, z, 0];
    return { A: { tex, view, lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT6 } };
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/opening.js
  var SEQ6 = [2304, 1296];
  var PRINT7 = { uHalftone: 0.085, uCell: 3, uGrain: 0.034 };
  function openingShot() {
    return { A: { tex: "seq", view: clampView(SEQ6, [1152, 648, 1, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT7 } };
  }
  function openingShotV2(k) {
    const sh = k.shot, st = sh.still;
    let z = 1, cx = 1152, cy = 648;
    if (st) {
      const u = (k.f - sh.f0) / Math.max(1, sh.f1 - 1 - sh.f0);
      z = st.zoom[0] + (st.zoom[1] - st.zoom[0]) * u;
      [cx, cy] = st.center;
    }
    for (const e of sh.fx || []) if (k.f >= e.f0 && k.f < e.f1 && e.zoom) z *= e.zoom;
    return { A: { tex: "seq", view: clampView(SEQ6, [cx, cy, z, 0]), lod: 0 }, chrome: false, underPrint: true, grade: { ...PRINT7 } };
  }

  // outputs/ai-city-takeover/ep01/v4/excerpt/src/main.js
  var W8 = 1920;
  var H10 = 1080;
  var OFFSET_DATA = Number(document.getElementById("root")?.dataset?.exOffset || 0);
  var EDL = document.getElementById("root")?.dataset?.exEdl || "data/edl.json";
  var GRADE = {
    uExposure: 1,
    uMist: 0.16,
    uBloomGain: 0.34,
    uBloomKnee: 0.32,
    uHalation: 0.16,
    uBloomNorm: 0.1667,
    uLift: [0.105, 0.112, 0.118],
    uLiftAmt: 0.085,
    uSat: 0.86,
    uRedKeep: 1.15,
    uContrast: 0.96,
    uWarm: 0.35,
    uHalftone: 0.055,
    uCell: 3.2,
    uGrain: 0.036,
    uGrainOverlay: 0.5,
    uVignette: 0.26,
    uCA: 0.7,
    uOvAlpha: 1,
    uFade: 0,
    uCoolShadow: 0.5
  };
  var GRADE_V2 = {
    uMist: 0.09,
    uLiftAmt: 0.06,
    uBloomGain: 0.26,
    uBloomKnee: 0.4,
    uHalation: 0.1,
    uSat: 0.93,
    uContrast: 1,
    uWarm: 0.25,
    uHalftone: 0.045,
    uGrain: 0.032
  };
  var GRADE_TRIM_V2 = {};
  var GRADE_V4R3 = {
    uSoft: 1.5,
    uLine: 0.3,
    uLinePitch: 4,
    uLineAng: -0.3159,
    uMisregPx: 0.5,
    uHalftone: 0,
    uSat: 2,
    uWarmBal: 0.22,
    uGrain: 0.04,
    uRedKeep: 0.85,
    uPinkGuard: 1
  };
  var GRADE_V4R4 = {
    uSoft: 0,
    uSoftMix: 1,
    uSoftQ: 0.45,
    uOvInPrint: 1,
    uOvAlpha: 0,
    uLine: 0,
    uLineAM: 0.3,
    uLinePitch: 4,
    uLineAng: -0.3159,
    uMisregPx: 0.6,
    uHalftone: 0,
    uSat: 1.85,
    uWarmBal: 0.14,
    uWarm: 0.55,
    uCoolShadow: 0,
    uSoftE: 0,
    uShadowTint: [1.1, 0.98, 0.84],
    uLift: [0.16, 0.11, 0.075],
    uLiftAmt: 0.075,
    uColdGuard: 1,
    uRedCap: 0.62,
    uRedKeep: 1.5,
    uPinkGuard: 0,
    uGrain: 0.035,
    uGrainOverlay: 1
  };
  var GRADE_V4R8 = {
    uMist: 0.38,
    uMistLocal: 0.25,
    uBloomGain: 0.6,
    uBloomKnee: 0.22,
    uHalation: 0.34,
    uSoftQ: 0.85,
    uSat: 1.85,
    uWarmBal: 0.21
  };
  var GRADE_V4R9 = { uSoftQ: 1, uMist: 0.62, uMistLocal: 0.1, uSoftE: 0, uVignette: 0.45 };
  var GRADE_V4R10 = {
    uToneOn: 1,
    uToneBP: 0.016,
    uToneWP: 0.69,
    uToneG: 1.3,
    uMistLocal: 0.6,
    uMist: 0.75,
    uWarmBal: 0.13,
    uWarm: 0.45,
    uSoftE: 0.25,
    uSat: 1.75
  };
  var GRADE_V4R11 = {
    uSoftMix: 1,
    uSoftQ: 0.4,
    uSoftE: 0,
    uMist: 0.07,
    uMistLocal: 1,
    uBloomGain: 0.3,
    uBloomKnee: 0.35,
    uHalation: 0.14
  };
  var GRADE_V4R11_SHOT = { s012c: { uToneBP: -0.012, uToneWP: 1.2 } };
  var GRADE_DESIGN = {
    uMist: 0.07,
    uMistLocal: 1,
    uLiftAmt: 0.035,
    uLift: [0.06, 0.065, 0.075],
    uBloomGain: 0.3,
    uBloomKnee: 0.35,
    uHalation: 0.14,
    uSat: 1.04,
    uRedKeep: 1.1,
    uContrast: 1.05,
    uWarm: 0.3,
    uHalftone: 0.04,
    uGrain: 0.03
  };
  var GRADE_TRIM = {
    s007: { uExposure: 0.95 },
    s008: { uExposure: 1 },
    s009: { uExposure: 0.95 },
    s010: { uExposure: 1.12 },
    s011: { uExposure: 1.05 },
    s012: { uExposure: 1.06 },
    s013: { uExposure: 1 },
    s014: { uExposure: 1.02 }
  };
  async function loadImage(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
    return createImageBitmap(await res.blob(), { colorSpaceConversion: "none", premultiplyAlpha: "none" });
  }
  async function loadFonts(manifestUrl) {
    const m = await (await fetch(manifestUrl)).json();
    for (const f of m.faces) {
      const face = new FontFace(f.family, `url(fonts/${f.file})`);
      await face.load();
      document.fonts.add(face);
    }
    await document.fonts.ready;
  }
  var search = (arr, s) => {
    let lo = 0, hi = arr.length - 1, ans = -1;
    while (lo <= hi) {
      const m = lo + hi >> 1;
      if (arr[m] <= s) {
        ans = m;
        lo = m + 1;
      } else hi = m - 1;
    }
    return ans;
  };
  async function boot() {
    const canvas = document.getElementById("stage");
    const { gl, info } = createGL(canvas);
    const D = await (await fetch(EDL)).json();
    const FNS = D.opening_v2 ? Object.fromEntries(D.shots.map((x) => [x.id, openingShotV2])) : D.opening ? Object.fromEntries(D.shots.map((x) => [x.id, openingShot])) : D.bake ? Object.fromEntries(D.shots.map((x) => [x.id, bakeShot])) : D.version === "design" ? SHOT_FN_DESIGN : D.version >= 10 ? SHOT_FN_V8 : D.version >= 9 ? SHOT_FN_V7 : D.version >= 8 ? SHOT_FN_V6 : D.version >= 5 ? SHOT_FN_V5 : D.version >= 4 ? { ...SHOT_FN_V2, ...SHOT_FN_V4 } : D.version >= 2 ? SHOT_FN_V2 : SHOT_FN;
    await loadFonts("fonts/fonts.json");
    const FPS = D.fps, OFF = D.offset;
    const tex = {}, size = {};
    for (const [k, url] of Object.entries(D.images)) {
      const img = await loadImage(url);
      tex[k] = texture(gl, img, { mipmap: true });
      size[k] = [img.width, img.height];
      img.close();
    }
    const seqShot = D.shots.find((s) => s.seq);
    if (seqShot) {
      const seq0 = await loadImage(`${seqShot.seq.dir}/0000.jpg`);
      tex.seq = texture(gl, seq0, { mipmap: true });
      size.seq = [seq0.width, seq0.height];
      seq0.close();
    }
    let shownSeq = null;
    let seqSize = size.seq;
    async function showSeq(shot, i) {
      const key = `${shot.id}/${i}`;
      if (shownSeq === key) return;
      const img = await loadImage(`${shot.seq.dir}/${String(i).padStart(4, "0")}.jpg`);
      gl.bindTexture(gl.TEXTURE_2D, tex.seq);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D);
      if (D.version >= 16) seqSize = [img.width, img.height];
      img.close();
      shownSeq = key;
    }
    const layers = { overlay: canvas2d(W8, H10), feed: canvas2d(W8, H10), feedBack: canvas2d(W8, H10), surf: canvas2d(W8, H10), emit: canvas2d(W8, H10) };
    const ltex = {};
    for (const [k, l] of Object.entries(layers)) ltex[k] = texture(gl, l.c, { mipmap: false });
    const prog = {
      scene: program(gl, SCENE2, "scene"),
      bright: program(gl, BRIGHT2, "bright"),
      down: program(gl, DOWN, "down"),
      up: program(gl, UP, "up"),
      final: program(gl, FINAL2, "final")
    };
    const rt = { scene: target(gl, W8, H10, { float: info.floatRT }) };
    const chain = [];
    let w = W8 >> 1, h = H10 >> 1;
    for (let i = 0; i < 6; i++) {
      chain.push(target(gl, Math.max(w, 8), Math.max(h, 8), { float: info.floatRT }));
      w >>= 1;
      h >>= 1;
    }
    const ups = chain.map((c) => target(gl, c.w, c.h, { float: info.floatRT }));
    const lines = {};
    for (const l of D.lines) lines[l.id] = l.words.map((w2, i) => ({ ...w2, li: l.id, wi: i }));
    const beats = D.beats, snares = D.snare, downbeats = D.downbeats;
    const fo = (ts) => Math.round((ts - OFF) * FPS);
    const beatIndexFloat = (s) => {
      const i = search(beats, s);
      if (i < 0) return (s - beats[0]) / (beats[1] - beats[0]);
      const nx = i + 1 < beats.length ? beats[i + 1] : beats[i] + (beats[i] - beats[i - 1]);
      return i + (s - beats[i]) / (nx - beats[i]);
    };
    const beatLen = (s) => {
      const i = Math.max(0, search(beats, s));
      return beats[i + 1] - beats[i];
    };
    let marks = [];
    async function renderFrame(t) {
      const fr = Math.round((t + OFFSET_DATA) * FPS);
      const s = D.frame_song ? D.frame_song[fr] : OFF + fr / FPS;
      const f = D.frame_song ? fo(s) : fr;
      for (const l of Object.values(layers)) reset(l.ctx);
      marks = [];
      const shot = D.shots.find((x) => fr >= x.f0 && fr < x.f1) || D.shots[D.shots.length - 1];
      const sixteenthLen = (ts) => beatLen(ts) / 4;
      const k = {
        f,
        s,
        fo,
        layers,
        shot,
        version: D.version || 1,
        data: D,
        mark: (li, wi) => marks.push(`${li}:${wi}`),
        line: (li) => lines[li] || [],
        track: (id) => D.tracks[id] ? D.tracks[id][Math.min(D.tracks[id].length - 1, f - shot.f0)] : null,
        beatIndexFloat,
        beatsBetween: (a, b) => Math.round(beatIndexFloat(b) - beatIndexFloat(a)),
        sixteenthLen,
        sixteenthsBetween: (a, b) => Math.max(0, Math.floor((beatIndexFloat(b) - beatIndexFloat(a)) * 4 + 1e-6)),
        sixteenthAt: (a, j) => {
          let ts = a;
          for (let q = 0; q < j; q++) ts += sixteenthLen(ts);
          return ts;
        },
        snareTimes: (a, b) => snares.filter((x) => x >= a - 1e-6 && x < b),
        snaresBetween: (a, b) => snares.filter((x) => x >= a - 1e-6 && x < b && fo(x) <= f).length,
        barNo: () => 1 + search(downbeats, s + 1e-6)
      };
      const p = FNS[shot.id](k);
      const o = layers.overlay.ctx;
      if (p.chrome !== false) {
        ticketCard(k, o, { accent: shot.chapter === "c3" ? "#E8E4DA" : "#F2B134" });
        frameChrome(k, o);
      }
      if (D.picture_only) reset(o);
      const seqIdx = shot.hold && f >= shot.hold.f ? shot.hold.idx : shot.seq?.fixed ?? (shot.freeze_f ? Math.min(f, shot.freeze_f) : f) - shot.f0;
      if (p.A.tex === "seq") await showSeq(shot, seqIdx);
      if (p.underPrint && D.version < 7) {
        layers.feed.ctx.save();
        layers.feed.ctx.setTransform(1, 0, 0, 1, 0, 0);
        layers.feed.ctx.drawImage(layers.overlay.c, 0, 0);
        layers.feed.ctx.restore();
        reset(layers.overlay.ctx);
      }
      for (const [kk, l] of Object.entries(layers)) updateTexture(gl, ltex[kk], l.c);
      const A = p.A, B = p.B;
      const rows = p.rows;
      let aSize = size[A.tex], aView = A.view;
      if (D.version >= 16 && A.tex === "seq" && seqSize[0] !== size.seq[0]) {
        const r = seqSize[0] / size.seq[0];
        aSize = seqSize;
        aView = [A.view[0] * r, A.view[1] * r, A.view[2], A.view[3]];
      }
      use(gl, prog.scene, {
        uRes: [W8, H10],
        uTime: t,
        uFrame: f,
        uASize: aSize,
        uViewA: aView,
        uFitA: fitOf(aSize),
        uLodA: A.lod || 0,
        uGainA: A.gain ?? 1,
        uBSize: B ? size[B.tex] : [1, 1],
        uViewB: B ? B.view : [0, 0, 1, 0],
        uFitB: B ? fitOf(size[B.tex]) : 1,
        uLodB: B?.lod || 0,
        uBOn: B ? 1 : 0,
        uGainB: B?.gain ?? 1,
        uShake: p.shake || [0, 0],
        uRowsOn: rows ? rows.procedural ? 2 : 1 : 0,
        uRowGain: rows ? rows.gain : [1, 1, 1, 1],
        uAmbient: rows ? rows.ambient : 1,
        uDark: rows ? rows.dark : 1,
        uAmbDark: rows?.ambDark ?? (rows ? rows.dark : 1),
        uLevels: (D.levels || {})[A.tex === "seq" ? shot.id : A.tex] || [0, 1, 0],
        uKey: p.key || [0.6, 0.8],
        uEmitGain: p.emitGain ?? 1.6,
        uTint: p.tint || [1, 1, 1]
      }, {
        uA: tex[A.tex],
        uB: B ? tex[B.tex] : tex[A.tex],
        uRows: rows && tex[rows.tex || "p011-rows"] || tex[A.tex],
        uFeedBack: ltex.feedBack,
        uFeed: ltex.feed,
        uSurf: ltex.surf,
        uEmit: ltex.emit
      });
      draw(gl, rt.scene);
      use(gl, prog.bright, { uRes: [chain[0].w, chain[0].h] }, { uScene: rt.scene.tex });
      draw(gl, chain[0]);
      for (let i = 1; i < chain.length; i++) {
        use(gl, prog.down, { uRes: [chain[i].w, chain[i].h], uSrcTexel: [1 / chain[i - 1].w, 1 / chain[i - 1].h] }, { uSrc: chain[i - 1].tex });
        draw(gl, chain[i]);
      }
      let src = chain[chain.length - 1];
      for (let i = chain.length - 2; i >= 0; i--) {
        use(gl, prog.up, { uRes: [ups[i].w, ups[i].h], uSrcTexel: [1 / src.w, 1 / src.h], uRadius: 1 }, { uSrc: src.tex, uBase: chain[i].tex });
        draw(gl, ups[i]);
        src = ups[i];
      }
      const grade = D.version >= 7 ? { ...GRADE, ...GRADE_DESIGN, ...p.grade || {}, ...GRADE_V4R4, ...D.version >= 11 ? GRADE_V4R8 : {}, ...D.version >= 12 ? GRADE_V4R9 : {}, ...D.version >= 13 ? GRADE_V4R10 : {}, ...D.version >= 14 ? { uRedCapPost: 0.42 } : {}, ...D.version >= 15 && shot.id === "s013a" ? { uRedCapPost: 0.3 } : {}, ...D.version >= 16 ? { ...GRADE_V4R11, ...GRADE_V4R11_SHOT[shot.id] || {} } : {}, ...p.grade7 || {} } : D.version >= 6 ? { ...GRADE, ...GRADE_DESIGN, ...p.grade || {}, ...GRADE_V4R3, ...p.grade6 || {} } : D.version === "design" || D.version >= 5 ? { ...GRADE, ...GRADE_DESIGN, ...p.grade || {} } : D.version >= 2 ? { ...GRADE, ...GRADE_V2, ...GRADE_TRIM_V2[shot.id] || {}, ...p.grade || {} } : { ...GRADE, ...GRADE_TRIM[shot.id] || {}, ...p.grade || {} };
      if (shot.blur?.grade) Object.assign(grade, shot.blur.grade);
      if (shot.screen) Object.assign(grade, shot.screen);
      for (const e of shot.fx || []) if (f >= e.f0 && f < e.f1 && e.grade) Object.assign(grade, e.grade);
      use(gl, prog.final, { uRes: [W8, H10], uTime: t, uFrame: f, uDotAM: 0, uMosaic: 0, uDither: 0, uBlack: 0, ...grade }, { uScene: rt.scene.tex, uBloom: ups[0].tex, uOverlay: ltex.overlay, uHalf: chain[0].tex, uQuarter: chain[1].tex, uEighth: chain[2].tex });
      draw(gl, null);
      gl.finish();
      window.__exMarks = {
        f,
        s,
        shot: shot.id,
        words: [...new Set(marks)],
        still: A.tex,
        view: aView,
        shake: p.shake || [0, 0],
        src: A.tex === "seq" ? `${shot.seq.dir}/${String(seqIdx).padStart(4, "0")}.jpg` : D.images[A.tex],
        size: aSize
      };
    }
    window.__ex = { ready: true, info };
    return { renderFrame };
  }
  var ready = boot().catch((err) => {
    window.__exError = String(err && err.stack || err);
    document.title = "EX-ERROR";
    throw err;
  });
  var queue = ready;
  var render = (t) => {
    const run = queue.then((r) => r.renderFrame(t));
    queue = run.then(() => ready, () => ready);
    return run;
  };
  window.addEventListener("hf-seek", (e) => {
    e.detail.waitUntil(render(e.detail.time));
  });
  window.__exRender = render;
})();
