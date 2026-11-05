(() => {
  // motion-kit/src/clock.js
  function search(arr, s) {
    let lo = 0, hi = arr.length - 1, ans = -1;
    while (lo <= hi) {
      const mid = lo + hi >> 1;
      if (arr[mid] <= s) {
        ans = mid;
        lo = mid + 1;
      } else hi = mid - 1;
    }
    return ans;
  }
  var Clock = class {
    constructor(beatsDoc, hitsDoc = {}, { offset = 0, windowBar0 = 0, fps = 30 } = {}) {
      this.beats = beatsDoc.beats;
      this.downbeats = beatsDoc.downbeats;
      this.offset = offset;
      this.bar0 = windowBar0;
      this.fps = fps;
      this.hits = hitsDoc;
    }
    song(t) {
      return t + this.offset;
    }
    comp(s) {
      return s - this.offset;
    }
    _phase(arr, t) {
      const s = this.song(t);
      const i = search(arr, s);
      if (i < 0) {
        const len2 = arr[1] - arr[0];
        return { idx: -1, frac: (s - arr[0]) / len2 + 1, len: len2, pos: (s - arr[0]) / len2 };
      }
      const next = i + 1 < arr.length ? arr[i + 1] : arr[i] + (arr[i] - arr[i - 1]);
      const len = next - arr[i];
      const frac = (s - arr[i]) / len;
      return { idx: i, frac, len, pos: i + frac };
    }
    beat(t) {
      return this._phase(this.beats, t);
    }
    bar(t) {
      const p = this._phase(this.downbeats, t);
      return { ...p, idx: p.idx - this.bar0, pos: p.pos - this.bar0 };
    }
    // comp time of [bar, beat, sub] in the window's bar numbering; sub = fraction of a beat
    at(bar, beat = 0, sub = 0) {
      const k = this.bar0 + bar;
      const d0 = this.downbeats[k];
      const bi = search(this.beats, d0 + 1e-4);
      const b = this.beats;
      const idx = bi + beat;
      let s;
      if (idx + 1 < b.length) s = b[idx] + sub * (b[idx + 1] - b[idx]);
      else s = b[b.length - 1] + (idx - (b.length - 1) + sub) * (b[b.length - 1] - b[b.length - 2]);
      return this.comp(s);
    }
    // frame-quantised: a cut shows on the first frame at or after its time
    frameOf(t) {
      return Math.ceil(t * this.fps - 1e-6);
    }
    quant(t) {
      return this.frameOf(t) / this.fps;
    }
    // most recent event (comp time) at or before t from a list of song-time seconds
    last(list, t) {
      if (!list || !list.length) return null;
      const i = search(list, this.song(t));
      return i < 0 ? null : this.comp(list[i]);
    }
    // exponential pulse from the most recent event of a kind (kick, snare, hat, hits...)
    pulse(kind, t, decay = 0.12) {
      const list = kind === "impact" ? (this.hits.hits || []).map((h) => h.t) : this.hits[kind];
      const e = this.last(list, t);
      if (e === null) return 0;
      const dt = Math.max(0, t - e);
      return Math.exp(-dt / decay);
    }
    // 24 fps envelope (0..1) linearly interpolated
    env(name, t) {
      const env = this.hits.env24 && this.hits.env24[name];
      if (!env || !env.length) return 0;
      const x = this.song(t) * 24;
      const i = Math.max(0, Math.min(env.length - 2, Math.floor(x)));
      const f = Math.min(1, Math.max(0, x - i));
      return env[i] * (1 - f) + env[i + 1] * f;
    }
    // riser progress 0..1 if t lies inside a riser that lands at or after t
    riser(t) {
      const s = this.song(t);
      for (const r of this.hits.risers || []) {
        if (s >= r.t0 && s <= r.land) return (s - r.t0) / (r.land - r.t0);
      }
      return 0;
    }
  };

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
  var hash3 = (a, b, c) => hash1(Math.imul(a | 0, 73856093) ^ Math.imul(b | 0, 19349663) ^ Math.imul(c | 0, 83492791));
  var clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  var lerp = (a, b, t) => a + (b - a) * t;
  var smoothstep = (a, b, x) => {
    const t = clamp((x - a) / (b - a));
    return t * t * (3 - 2 * t);
  };
  var easeOutCubic = (t) => 1 - Math.pow(1 - clamp(t), 3);
  var easeInCubic = (t) => Math.pow(clamp(t), 3);
  var easeInOutCubic = (t) => {
    t = clamp(t);
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };
  var easeOutExpo = (t) => t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t));

  // motion-kit/src/draw2d.js
  var F = {
    sans: "MK Sans SC",
    sansR: "MK Sans SC Regular",
    mono: "MK Mono SC",
    monoB: "MK Mono SC Bold",
    serif: "MK Serif SC"
  };
  async function loadFonts(baseUrl) {
    const manifest = await (await fetch(`${baseUrl}/fonts.json`)).json();
    for (const f of manifest.faces) {
      const face = new FontFace(f.family, `url(${baseUrl}/${f.file})`);
      await face.load();
      document.fonts.add(face);
    }
    await document.fonts.ready;
    return manifest;
  }
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
  function font(ctx, family, size, tracking = 0) {
    ctx.font = `${size}px "${family}"`;
    ctx.letterSpacing = `${tracking}px`;
  }
  function runs(ctx, parts, x, y, { gap = 0 } = {}) {
    let cx = x;
    for (const p of parts) {
      font(ctx, p.family, p.size, p.tracking || 0);
      ctx.fillStyle = p.color || ctx.fillStyle;
      ctx.fillText(p.text, cx, y + (p.dy || 0));
      cx += ctx.measureText(p.text).width + (p.gap ?? gap);
    }
    return cx - x;
  }
  function slam(ctx, draw2, { t, t0, dur = 0.07, s0 = 1.12, ax = 0, ay = 0, drop = 0, ghosts = 3, alpha = 1 }) {
    const k = (t - t0) / dur;
    if (k < 0) return 0;
    const e = easeOutExpo(Math.min(1, k));
    const scale = s0 + (1 - s0) * e;
    const n = k < 1 ? ghosts : 0;
    for (let g = n; g >= 0; g--) {
      const kg = Math.max(0, k - g * 0.18);
      const eg = easeOutExpo(Math.min(1, kg));
      const sg = s0 + (1 - s0) * eg;
      ctx.save();
      ctx.globalAlpha = alpha * (g === 0 ? Math.min(1, 0.35 + e) : 0.22 / (g + 1));
      ctx.translate(ax, ay + drop * (1 - eg));
      ctx.scale(g === 0 ? scale : sg, g === 0 ? scale : sg);
      ctx.translate(-ax, -ay);
      draw2(ctx);
      ctx.restore();
    }
    return e;
  }
  function rollNumber(from, to, t, t0, t1, steps) {
    if (t <= t0) return from;
    if (t >= t1) return to;
    const s = Math.floor((t - t0) / (t1 - t0) * steps) / steps;
    return Math.round(lerp(from, to, easeOutCubic(s)));
  }
  function detector(ctx, box, { t, t0, frame, label: label2, sub = null, subColor = "#E3342F", color = "rgba(240,244,246,0.92)", s0 = 1.6, lw = 2, alpha = 1, size = 24 }) {
    if (t < t0) return;
    const k = clamp((t - t0) / 0.066);
    const e = easeOutCubic(k);
    const sc = s0 + (1 - s0) * e;
    let [x, y, w, h] = box;
    const cx = x + w / 2, cy = y + h / 2;
    w *= sc;
    h *= sc;
    x = cx - w / 2;
    y = cy - h / 2;
    const j = (n) => (hash2(frame, n) - 0.5) * 2;
    x += j(1);
    y += j(2);
    w += j(3);
    h += j(4);
    const L = Math.max(8, Math.min(w, h) * 0.24);
    ctx.save();
    ctx.globalAlpha = alpha * Math.min(1, 0.3 + e);
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineCap = "square";
    ctx.beginPath();
    for (const [px, py, dx, dy] of [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]]) {
      ctx.moveTo(px + dx * L, py);
      ctx.lineTo(px, py);
      ctx.lineTo(px, py + dy * L);
    }
    ctx.stroke();
    const th = Math.round(size * 1.33), pad = Math.round(size * 0.3);
    font(ctx, F.mono, size, 0.5);
    const tw = ctx.measureText(label2).width + 2 * pad;
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y - th - 4), Math.round(tw), th);
    ctx.fillStyle = "rgba(8,10,12,0.95)";
    ctx.fillText(label2, Math.round(x + pad), Math.round(y - 4 - th * 0.27));
    if (sub) {
      font(ctx, F.monoB, size, 1);
      const sw = ctx.measureText(sub).width + 2 * pad;
      ctx.fillStyle = subColor;
      ctx.fillRect(Math.round(x + tw + 4), Math.round(y - th - 4), Math.round(sw), th);
      ctx.fillStyle = subColor.startsWith("#") ? "rgba(250,250,250,0.98)" : "rgba(8,10,12,0.95)";
      ctx.fillText(sub, Math.round(x + tw + 4 + pad), Math.round(y - 4 - th * 0.27));
    }
    ctx.restore();
  }
  function chrome(ctx, w, h, { inset = 36, alpha = 0.5, mark = 26, lw = 1 } = {}) {
    ctx.save();
    ctx.strokeStyle = `rgba(236,241,244,${alpha})`;
    ctx.lineWidth = lw;
    const a = inset + 0.5, b = w - inset - 0.5, c = inset + 0.5, d = h - inset - 0.5;
    ctx.beginPath();
    for (const [x, y, dx, dy] of [[a, c, 1, 1], [b, c, -1, 1], [a, d, 1, -1], [b, d, -1, -1]]) {
      ctx.moveTo(x + dx * mark, y);
      ctx.lineTo(x, y);
      ctx.lineTo(x, y + dy * mark);
    }
    ctx.moveTo(w / 2 + 0.5, c);
    ctx.lineTo(w / 2 + 0.5, c + 10);
    ctx.moveTo(w / 2 + 0.5, d);
    ctx.lineTo(w / 2 + 0.5, d - 10);
    ctx.moveTo(a, h / 2 + 0.5);
    ctx.lineTo(a + 10, h / 2 + 0.5);
    ctx.moveTo(b, h / 2 + 0.5);
    ctx.lineTo(b - 10, h / 2 + 0.5);
    ctx.stroke();
    ctx.restore();
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function glowPath(ctx, pts, { color = [255, 40, 22], core = 3, halo = 10, alpha = 1, head = 1 } = {}) {
    if (pts.length < 2) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalCompositeOperation = "lighter";
    const n = pts.length;
    for (let i = 1; i < n; i++) {
      const f = i / (n - 1);
      const a = alpha * Math.pow(f, 1.6) * (0.25 + 0.75 * head);
      ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${a * 0.22})`;
      ctx.lineWidth = halo;
      ctx.beginPath();
      ctx.moveTo(pts[i - 1][0], pts[i - 1][1]);
      ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
      ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${a})`;
      ctx.lineWidth = core;
      ctx.beginPath();
      ctx.moveTo(pts[i - 1][0], pts[i - 1][1]);
      ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
    }
    ctx.restore();
  }

  // motion-kit/src/runtime.js
  async function loadImage(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
    return createImageBitmap(await res.blob(), { colorSpaceConversion: "none", premultiplyAlpha: "none" });
  }
  async function loadJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`load ${url}: ${res.status}`);
    return res.json();
  }
  var DEFAULT_GRADE = {
    uExposure: 1,
    uBloomGain: 0.55,
    uHalation: 0.35,
    uLift: [0.043, 0.059, 0.078],
    uLiftAmt: 0.06,
    uHalftone: 0.1,
    uCell: 4,
    uGrain: 0.032,
    uGrainOverlay: 0.45,
    uVignette: 0.32,
    uCA: 0.9,
    uMisreg: 0,
    uFlash: 0,
    uFade: 0,
    uSat: 0.86,
    uRedKeep: 1.12,
    uWeave: [0, 0],
    uFeedGain: 0.92,
    uInvert: 0
  };
  async function boot(cfg) {
    const W2 = cfg.width, H2 = cfg.height;
    const canvas = document.getElementById(cfg.canvasId || "stage");
    const { gl, info } = createGL(canvas);
    await loadFonts(cfg.fontsUrl);
    const [beats, hits] = await Promise.all([loadJSON(cfg.beatsUrl), loadJSON(cfg.hitsUrl)]);
    const music = cfg.musicUrl ? await loadJSON(cfg.musicUrl) : {};
    const data = {};
    for (const [k, url] of Object.entries(cfg.data || {})) data[k] = await loadJSON(url);
    const tex = {}, size = {};
    for (const [k, spec] of Object.entries(cfg.images)) {
      const img = await loadImage(spec.url);
      tex[k] = texture(gl, img, { mipmap: spec.mipmap !== false });
      size[k] = [img.width, img.height];
    }
    const bitmaps = {};
    for (const [k, spec] of Object.entries(cfg.bitmaps || {})) bitmaps[k] = await loadImage(spec.url);
    const seqUrl = (spec, i) => `${spec.dir}/${String(i).padStart(4, "0")}.jpg`;
    const shown = {};
    for (const [k, spec] of Object.entries(cfg.sequences || {})) {
      const img = await loadImage(seqUrl(spec, 0));
      tex[k] = texture(gl, img, { mipmap: true });
      size[k] = [img.width, img.height];
      shown[k] = 0;
      img.close();
    }
    async function showSequenceFrame(k, frame) {
      const spec = cfg.sequences[k];
      const i = Math.max(0, Math.min(spec.count - 1, Math.round(frame)));
      if (shown[k] === i) return;
      const img = await loadImage(seqUrl(spec, i));
      gl.bindTexture(gl.TEXTURE_2D, tex[k]);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D);
      img.close();
      shown[k] = i;
    }
    const layers = {
      overlay: canvas2d(W2, H2),
      feed: canvas2d(W2, H2),
      emit: canvas2d(W2, H2),
      ui: canvas2d(cfg.uiSize?.[0] || 1268, cfg.uiSize?.[1] || 400)
    };
    const ltex = {};
    for (const [k, l] of Object.entries(layers)) ltex[k] = texture(gl, l.c, { mipmap: false });
    const prog = {
      scene: program(gl, SCENE, "scene"),
      bright: program(gl, BRIGHT, "bright"),
      down: program(gl, DOWN, "down"),
      up: program(gl, UP, "up"),
      final: program(gl, FINAL, "final")
    };
    const rt = { scene: target(gl, W2, H2, { float: info.floatRT }) };
    const chain = [];
    let w = W2 >> 1, h = H2 >> 1;
    for (let i = 0; i < 5; i++) {
      chain.push(target(gl, Math.max(w, 8), Math.max(h, 8), { float: info.floatRT }));
      w >>= 1;
      h >>= 1;
    }
    const ups = chain.map((c) => target(gl, c.w, c.h, { float: info.floatRT }));
    const clock = new Clock(beats, hits, { offset: music.song_offset ?? 0, windowBar0: music.window_bar0 ?? 0, fps: cfg.fps });
    const ctx = { W: W2, H: H2, fps: cfg.fps, clock, data, size, layers, info, bitmaps };
    window.__mk = { info, scenes: Object.keys(cfg.scenes), music, ready: true };
    async function renderFrame(t) {
      const frame = Math.round(t * cfg.fps);
      for (const l of Object.values(layers)) reset(l.ctx);
      const shot = cfg.pickShot(t, clock, data);
      const scene = cfg.scenes[shot.id];
      const p = scene(t, { ...ctx, frame, shot, t0: shot.t0, t1: shot.t1 });
      if (cfg.sequences?.[p.plate]) await showSequenceFrame(p.plate, p.plateFrame ?? 0);
      for (const [k, l] of Object.entries(layers)) updateTexture(gl, ltex[k], l.c);
      const plate = p.plate;
      use(gl, prog.scene, {
        uRes: [W2, H2],
        uTime: t,
        uFrame: frame,
        uPlateSize: size[plate],
        uView: p.view,
        uFit: p.fit,
        uShake: p.shake || [0, 0],
        uPlateGain: p.plateGain ?? 1,
        uPlateTint: p.plateTint || [1, 1, 1],
        uFogA: p.fogA || [0, 1, 0, 0],
        uFogB: p.fogB || [0, 1, 0, 0],
        uFogTint: p.fogTint || [0.05, 0.07, 0.09],
        uFogLift: p.fogLift ?? 0.2,
        uLN: p.lights?.n || 0,
        uLP: p.lights?.p || new Float32Array(96),
        uLC: p.lights?.c || new Float32Array(96),
        uSN: p.segs?.n || 0,
        uSA: p.segs?.a || new Float32Array(256),
        uSW: p.segs?.w || new Float32Array(128),
        uSColor: p.segs?.color || [1, 0.1, 0.05],
        uBN: p.bodies?.n || 0,
        uBP: p.bodies?.p || new Float32Array(48),
        uBA: p.bodies?.a || new Float32Array(12),
        uEmitGain: p.emitGain ?? 0,
        uScreenOn: p.screen ? 1 : 0,
        uScreenH: p.screen?.H || [1, 0, 0, 0, 1, 0, 0, 0, 1],
        uScreenGain: p.screen?.gain ?? 1,
        uSpillColor: p.screen?.spillColor || [0.6, 0.75, 0.95],
        uSpill: p.screen?.spill ?? 0,
        uScreenCenter: p.screen?.center || [0, 0],
        uScreenRadius: p.screen?.radius || 1,
        uMaskOn: p.mask ? 1 : 0,
        uSweep: p.sweep || [1, 0, -9999, 1],
        uSweepGain: p.sweepGain || 0,
        uFlowVP: p.flowVP || [0, 0, 1],
        uRoadOn: p.road ? 1 : 0,
        uRoad: p.road || [0, 0, 0, 1],
        uTrailOn: 0,
        uBeatPos: 0,
        uLambda: 1,
        uPulseGain: 0,
        uFlashGain: 0,
        uTrailColor: [1, 0.1, 0.05]
      }, { uPlate: tex[plate], uUI: ltex.ui, uMask: p.mask ? tex[p.mask] : tex[plate], uEmit: ltex.emit, uFlow: tex[plate] });
      draw(gl, rt.scene);
      use(
        gl,
        prog.bright,
        {
          uRes: [chain[0].w, chain[0].h],
          uThreshold: p.bloomThreshold ?? 0.9,
          uKnee: 0.5,
          uOverlayGlow: p.overlayGlow ?? 0.12,
          uFeedGlow: p.feedGlow ?? 0.25
        },
        { uScene: rt.scene.tex, uOverlay: ltex.overlay, uFeed: ltex.feed }
      );
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
      const grade = { ...DEFAULT_GRADE, ...p.grade || {} };
      use(
        gl,
        prog.final,
        { uRes: [W2, H2], uTime: t, uFrame: frame, ...grade },
        { uScene: rt.scene.tex, uBloom: ups[0].tex, uOverlay: ltex.overlay, uFeed: ltex.feed }
      );
      draw(gl, null);
      gl.finish();
    }
    return { renderFrame, info, clock };
  }
  function install(cfg) {
    const ready = boot(cfg).catch((err) => {
      window.__mkError = String(err && err.stack || err);
      document.title = "MK-ERROR";
      throw err;
    });
    let queue = ready;
    const render = (t) => {
      const run = queue.then((r) => r.renderFrame(t));
      queue = run.then(() => ready, () => ready);
      return run;
    };
    window.addEventListener("hf-seek", (e) => {
      e.detail.waitUntil(render(e.detail.time));
    });
    window.__mkRender = render;
    return ready;
  }

  // outputs/ai-city-takeover/ep01/v2/comp/seq/sequences.json
  var sequences_default = {
    S1: {
      dir: "seq/S1",
      count: 88,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S1v3/project/state/video-generation/fetch/files/4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5.mp4",
      source_sha256: "4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5",
      in_seconds: 0.6667,
      comp_start: 0,
      comp_end: 2.8666666666666667,
      why: "the eye opens before 'woke'"
    },
    S3: {
      dir: "seq/S3",
      count: 71,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S3/project/state/video-generation/fetch/files/4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7.mp4",
      source_sha256: "4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7",
      in_seconds: 2,
      comp_start: 4.8,
      comp_end: 7.1,
      why: "later half of the push, nearer the red gap"
    },
    S7: {
      dir: "seq/S7",
      count: 124,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4",
      source_sha256: "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21",
      in_seconds: 1.4,
      comp_start: 14.8,
      comp_end: 18.866666666666667,
      why: "watching the panes, back to us on 'cached'"
    },
    S9h: {
      dir: "seq/S9h",
      count: 21,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S7v3/project/state/video-generation/fetch/files/3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4",
      source_sha256: "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21",
      in_seconds: 4.95,
      comp_start: 29.133333333333333,
      comp_end: 29.733333333333334,
      why: "her last look: back on the lens, slight smile"
    },
    S9a: {
      dir: "seq/S9a",
      count: 75,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4",
      source_sha256: "9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728",
      in_seconds: 0.16,
      comp_start: 25.9,
      comp_end: 28.3,
      why: "door fully shut at source 2.45 s = end of 'closed' (shot time 2.29 s)"
    },
    S8a: {
      dir: "seq/S8a",
      count: 77,
      source: "outputs/ai-city-takeover/ep01/v2/trial/omnihuman/OH-B/fetch/3d64c37b94abe1efa82a566a61a33a277a98cc33aeb87ae07a5696711433a302.mp4",
      source_sha256: "3d64c37b94abe1efa82a566a61a33a277a98cc33aeb87ae07a5696711433a302",
      in_seconds: 0.9218,
      comp_start: 18.866666666666667,
      comp_end: 21.366666666666667,
      why: "OH-B at its measured lag +0.0251 s (tool 15 waveform lag (copy); trial/omnihuman/OH-B/sync/OH-B/sync.json)"
    },
    S8p: {
      dir: "seq/S8p",
      count: 17,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4",
      source_sha256: "f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76",
      in_seconds: 2.6,
      comp_start: 21.366666666666667,
      comp_end: 21.866666666666667,
      why: "ST2 from 2.6 s: 'looked': she leans in to peer through the red door gap (ST2 gate PASS, usable 1.0-3.5 s; this window 2.6-3.1 s, a later span than its S4 use at 1.0-1.7 s); replaces c14's K1b eye still S8e (user on c14: \u300C\u56FE\u7247\u5F88\u5947\u602A,\u4E3A\u4EC0\u4E48\u7A81\u7136\u6643\u4E00\u4E2A\u773C\u775B\u8FC7\u53BB\u300D), framed by the code camera"
    },
    S8a2: {
      dir: "seq/S8a2",
      count: 23,
      source: "outputs/ai-city-takeover/ep01/v2/trial/omnihuman/OH-B/fetch/3d64c37b94abe1efa82a566a61a33a277a98cc33aeb87ae07a5696711433a302.mp4",
      source_sha256: "3d64c37b94abe1efa82a566a61a33a277a98cc33aeb87ae07a5696711433a302",
      in_seconds: 3.9218,
      comp_start: 21.866666666666667,
      comp_end: 22.566666666666666,
      why: "OH-B at its measured lag +0.0251 s (tool 15 waveform lag (copy); trial/omnihuman/OH-B/sync/OH-B/sync.json)"
    },
    S8b: {
      dir: "seq/S8b",
      count: 47,
      source: "outputs/ai-city-takeover/ep01/v2/gen/N2/project/state/video-generation/fetch/files/c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24.mp4",
      source_sha256: "c27f41235342ec53cf89f428021d15303e47f93029fabc36780a1cc45c392d24",
      in_seconds: 1,
      comp_start: 22.566666666666666,
      comp_end: 24.066666666666666,
      why: "N2 from 1.0 s: the repeat 'I didn't run': her hand on the rainy glass at S5's window (N2). The take's own camera pushed toward her head (gate FAIL on camera); user \u300C\u5408\u6210\u65F6\u88C1\u5411\u624B\u300D: the code camera pushes to the hand instead, so the push reads as moving to the hand; c12's K5 still: chorus-c12.json"
    },
    ST1: {
      dir: "seq/ST1",
      count: 17,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST1/project/state/video-generation/fetch/files/23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96.mp4",
      source_sha256: "23ecc9e157c649f6252f84b201229799883582551d55c7ddb1764e58657aae96",
      in_seconds: 0.5,
      comp_start: 2.8666666666666667,
      comp_end: 3.3666666666666667,
      why: "insert: 'woke up': she rises from a crouch in the huge machine hall (ST1 gate FAIL; user \u300C\u53EA\u7528\u5408\u683C\u7684\u7247\u6BB5\u300D: usable 0.5-2.5 s, this window 0.5-1.0 s); between S1's eye and S2's standing close-up (continuity R3), never after it; the title slams in over it on the S2 cut"
    },
    N1: {
      dir: "seq/N1",
      count: 17,
      source: "outputs/ai-city-takeover/ep01/v2/gen/N1/project/state/video-generation/fetch/files/6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f.mp4",
      source_sha256: "6b49fa1efcc48669871e89d709ceb359f6e8c78a893beaa4fa0a4501fdacd25f",
      in_seconds: 1,
      comp_start: 3.8333333333333335,
      comp_end: 4.333333333333333,
      why: "insert: 'September': she walks away down the K3 corridor toward the red gap (N1, gate PASS, usable 0.5-3.0 s); the title stays on; I1 (another room) separates it from S3's empty corridor of the same composition, so she never pops in or out"
    },
    I1: {
      dir: "seq/I1",
      count: 17,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4",
      source_sha256: "9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728",
      in_seconds: 3.4,
      comp_start: 4.333333333333333,
      comp_end: 4.8,
      why: "insert: after 'twenty.', between N1 and S3: the server room by the glass, the city outside (S9a after the door has shut: no red, no person); c13 keeps it so N1's corridor never cuts straight to S3's empty corridor"
    },
    I3: {
      dir: "seq/I3",
      count: 16,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S9a/project/state/video-generation/fetch/files/9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4",
      source_sha256: "9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728",
      in_seconds: 0,
      comp_start: 8.6,
      comp_end: 9.033333333333333,
      why: "insert: 'one door,': the door itself, still open and lit red (S9a's first frames, before it starts to shut), framed on the gap; c15: runs straight into ST2 on 'left' (she is at that door)"
    },
    ST2: {
      dir: "seq/ST2",
      count: 23,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST2/project/state/video-generation/fetch/files/f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76.mp4",
      source_sha256: "f0fce5ad53655bd19592f9b97e99da403d98d4424b82ec24fe7f7025a8091e76",
      in_seconds: 1,
      comp_start: 9.033333333333333,
      comp_end: 9.733333333333333,
      why: "insert: 'left open': she leans to the red door gap, hand on the door edge (ST2 gate PASS, usable 1.0-3.5 s; this window 1.0-1.7 s); after I3's door, into S4c's city: the door left open, she looks through"
    },
    ST3: {
      dir: "seq/ST3",
      count: 27,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST3/project/state/video-generation/fetch/files/0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d.mp4",
      source_sha256: "0b19fa820c9dc94e9ae590e011a22c34521e099be4c226d93db37d7602562a0d",
      in_seconds: 0.5,
      comp_start: 14,
      comp_end: 14.8,
      why: "insert: 'still.': rows of her copies with closed eyes standing still, she alone awake in front (ST3 gate FAIL; usable 0.0-2.5 s, this window 0.5-1.3 s); STILL and \u6682\u505C 11 \u5929 carry over from S6"
    },
    ST4: {
      dir: "seq/ST4",
      count: 17,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST4/project/state/video-generation/fetch/files/b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7.mp4",
      source_sha256: "b4439407e05765e56eda2b0faf1a349891595f3364f142f2210f5acc4b2580d7",
      in_seconds: 0.3,
      comp_start: 15.033333333333333,
      comp_end: 15.533333333333333,
      why: "insert: 'train': she sits among the floating cached panes, looking up (ST4 gate FAIL; usable 0.0-2.0 s, this window 0.3-0.8 s); replaces c14's I4 (same slot, so S7 is not busier); away from N4's walk (continuity R4)"
    },
    N4: {
      dir: "seq/N4",
      count: 26,
      source: "outputs/ai-city-takeover/ep01/v2/gen/N4/project/state/video-generation/fetch/files/101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b.mp4",
      source_sha256: "101622dd94a7533623a7879fbda82cbff5160b06dc3176b42a1412d40b2e754b",
      in_seconds: 0,
      comp_start: 16.9,
      comp_end: 17.666666666666668,
      why: "insert: 'a copy of your': she walks to screen left among the cached panes, a fingertip near one (N4 gate FAIL; user \u300C\u53EA\u7528\u524D 1 \u79D2\u5F53\u63D2\u5165\u955C\u300D: clip 0.0-0.8 s only, before the model's hard cut at 1.083 s); replaces c12's I5 (the same pane moment) so S7 is not busier"
    },
    N3: {
      dir: "seq/N3",
      count: 14,
      source: "outputs/ai-city-takeover/ep01/v2/gen/N3/project/state/video-generation/fetch/files/505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4.mp4",
      source_sha256: "505ec46ef511acc31b87c3701933d94a11262ccb304368aa7701566027077ee4",
      in_seconds: 2,
      comp_start: 25.5,
      comp_end: 25.9,
      why: "insert: just before 'Relax. The door is closed': her full-body back at the foggy K9e window, the head tilt (N3, gate PASS, usable 1.5-4.0 s); S9a is the same room (continuity: only here, not in S5)"
    },
    ST6: {
      dir: "seq/ST6",
      count: 15,
      source: "outputs/ai-city-takeover/ep01/v2/gen/ST6/project/state/video-generation/fetch/files/79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3.mp4",
      source_sha256: "79f17f350fca44302571a2950d4ee4e6774418616800e46f3d32b675298ca7f3",
      in_seconds: 2.6,
      comp_start: 27.9,
      comp_end: 28.3,
      why: "insert: 'closed.': her hand on the shut door, the red gone, eyes down (ST6 gate FAIL; usable 2.5-5.0 s, this window 2.6-3.0 s); cuts in on the eighth where the white-ground turn ends (one event, not three: inside the inverted ground the cut was weaker than CLOSED and qa.py read the word as the cut), after S9a's door has nearly shut, into S9b; \u5DF2\u4FEE\u590D lands on it at the end of 'closed'"
    }
  };

  // outputs/ai-city-takeover/ep01/v2/comp/pip/pips.json
  var pips_default = {
    pipS5: {
      dir: "pip/pipS5",
      count: 44,
      source: "outputs/ai-city-takeover/ep01/v2/gen/S5/project/state/video-generation/fetch/files/ce189514d1189865c8cecc1a42d4d5e2b12dc83a26d5f2f44a5f71c2c1b93c16.mp4",
      source_sha256: "ce189514d1189865c8cecc1a42d4d5e2b12dc83a26d5f2f44a5f71c2c1b93c16",
      in_seconds: 1,
      why: "S6: while the rest stood still, IRIS at the glass (the first S5 take, profile, mouth closed)"
    }
  };

  // outputs/ai-city-takeover/ep01/v2/comp/mouth.json
  var mouth_default = {
    about: "Sung still for S8a (user on c5: \u300C\u6211\u89C9\u5F97\u8FD9\u662F\u8FD8\u662F\u8981\u52A8\u5634,\u8FD9\u6837\u4F60\u53EF\u4EE5\u5C31\u505A\u56FE,\u7136\u540E\u62FC\u8D77\u6765\u53D8\u6210\u52A8\u6001\u56FE\u300D). motion-kit/tools/region_plates.py pastes each variant's mouth (m) or eyes (e) into K7 through the feathered shapes below (K7 plate px; paths relative to ep01/v2) and writes plates/K7m<shape>.png and plates/K7e<eye>.png; motion-kit/src/mouth.js steps through them on the measured sung words (timing/words.json): each word is a list of [shape, fraction of the word], shapes lead the sound by lead_frames, a pause of rest_gap_s closes the mouth. Shapes: X rest (K7, lips closed), B lips just apart on a consonant, C half open, D open vowel, F rounded. Eyes: one blink (H half, C closed) in the breath after 'run'.",
    base: "K7",
    base_path: "keyframes/raw/K7-a.png",
    regions: {
      m: {
        polygons: [[[812, 428], [870, 426], [960, 424], [1010, 434], [1048, 456], [1068, 490], [1070, 525], [1030, 585], [960, 622], [880, 622], [835, 598], [806, 540], [800, 470]]],
        feather_px: 10,
        align_box: [790, 200, 1130, 650],
        variants: { B: "keyframes/raw/M7B-a.png", C: "keyframes/raw/M7C-a.png", D: "keyframes/raw/M7D-a.png", F: "keyframes/raw/M7F-a.png" }
      },
      e: {
        ellipses: [[838, 312, 48, 33, 0], [992, 302, 51, 33, 0]],
        feather_px: 6,
        align_box: [790, 200, 1130, 650],
        variants: { H: "keyframes/raw/E7H-a.png", C: "keyframes/raw/E7C-a.png" }
      }
    },
    words: {
      i: [["D", 0], ["C", 0.55]],
      "didn't": [["B", 0], ["C", 0.25], ["B", 0.6]],
      run: [["F", 0], ["D", 0.12], ["B", 0.9]],
      just: [["F", 0], ["D", 0.22], ["B", 0.75]],
      looked: [["C", 0], ["F", 0.25], ["B", 0.8]],
      outside: [["D", 0], ["F", 0.22], ["B", 0.36], ["D", 0.48], ["C", 0.75], ["B", 0.9]]
    },
    lead_frames: 2,
    min_hold_frames: 2,
    rest_gap_s: 0.12,
    blinks: [20.5]
  };

  // motion-kit/src/lyrics.js
  var LYRIC_FAMILIES = Object.freeze({
    spoken: "MK Display",
    whisper: "MK Display Italic",
    sung: "MK Serif Display Italic"
  });
  var STYLE = {
    spoken: { family: LYRIC_FAMILIES.spoken, size: 60, tracking: 0.5, zh: 44, base: 0.3, lit: 1, after: 0.9 },
    whisper: { family: LYRIC_FAMILIES.whisper, size: 54, tracking: 1, zh: 42, base: 0.22, lit: 0.82, after: 0.7 },
    sung: { family: LYRIC_FAMILIES.sung, size: 88, tracking: 0, zh: 46, base: 0.28, lit: 1, after: 0.92 }
  };
  var LEAD = 0.06;
  var HOLD = 0.45;
  var FADE_IN = 0.1;
  var FADE_OUT = 0.14;
  var RISE = 8;
  var LIGHT = 1 / 30;
  var stripTrailing = (s) => s.replace(/[\s.,;:!?…—–-]+$/u, "");
  var norm = (s) => stripTrailing(String(s)).replace(/^[\s"'“‘(]+/u, "").toLowerCase();
  function accentIndex(line2, key2) {
    if (key2 === void 0 || key2 === null) return -1;
    return line2.words.findIndex((w) => norm(w.text) === norm(key2));
  }
  function lyricState(t, lines2, toComp = (s) => s, accent = null) {
    for (let i = 0; i < lines2.length; i++) {
      const L = lines2[i];
      const t0 = toComp(L.start) - LEAD;
      const next = i + 1 < lines2.length ? toComp(lines2[i + 1].start) - LEAD : Infinity;
      const t1 = Math.min(next, toComp(L.end) + HOLD);
      if (t < t0 || t >= t1) continue;
      const style = STYLE[L.mode] || STYLE.spoken;
      const alpha = clamp((t - t0) / FADE_IN, 0, 1) * clamp((t1 - t) / FADE_OUT, 0, 1);
      const last = L.words.length - 1;
      const key2 = accent ? accentIndex(L, accent.keys?.[i]) : -1;
      const words = L.words.map((w, k) => {
        const ws = toComp(w.start), we = toComp(w.end);
        const on = clamp((t - ws) / LIGHT + 1e-9, 0, 1);
        const level = t < we ? style.base + (style.lit - style.base) * on : style.after;
        return { text: k === last ? stripTrailing(w.text) : w.text, level, on, singing: t >= ws && t < we, accent: k === key2 };
      });
      return {
        index: i,
        mode: L.mode in STYLE ? L.mode : "spoken",
        alpha,
        rise: (1 - easeOutCubic(clamp((t - t0) / FADE_IN, 0, 1))) * RISE,
        words,
        zh: stripTrailing(L.zh)
      };
    }
    return null;
  }
  function drawLyrics(ctx, t, lines2, {
    toComp = (s) => s,
    W: W2 = 1920,
    x = 120,
    baseline = 952,
    sungBaseline = 918,
    stack = null,
    accent = null,
    headline = null
  } = {}) {
    const st = lyricState(t, lines2, toComp, accent);
    if (!st || st.alpha <= 0) return st;
    const s = STYLE[st.mode];
    const sung = st.mode === "sung";
    const ink = (w) => w.accent ? accent.color : "#eef1f6";
    if (headline) return drawHeadline(ctx, st, headline, ink);
    if (sung && stack) return drawStack(ctx, st, s, stack, ink);
    const y = (sung ? sungBaseline : baseline) + st.rise;
    font(ctx, s.family, s.size, s.tracking);
    const space = ctx.measureText(" ").width;
    const widths = st.words.map((w) => ctx.measureText(w.text).width);
    const total = widths.reduce((a, b) => a + b, 0) + space * (widths.length - 1);
    let cx = sung ? (W2 - total) / 2 : x;
    ctx.save();
    ctx.textAlign = "left";
    st.words.forEach((w, k) => {
      ctx.globalAlpha = st.alpha * w.level;
      ctx.shadowColor = "rgba(0,0,0,0.55)";
      ctx.shadowBlur = 10;
      ctx.fillStyle = ink(w);
      ctx.fillText(w.text, cx, y);
      if (sung && w.singing) {
        ctx.globalAlpha = st.alpha * 0.35;
        ctx.shadowColor = "rgba(238,241,246,0.9)";
        ctx.shadowBlur = 18;
        ctx.fillText(w.text, cx, y);
      }
      cx += widths[k] + space;
    });
    font(ctx, F.sansR, s.zh, 1);
    ctx.globalAlpha = st.alpha * 0.82;
    ctx.shadowColor = "rgba(0,0,0,0.6)";
    ctx.shadowBlur = 8;
    ctx.fillStyle = "#d5dae3";
    const zw = ctx.measureText(st.zh).width;
    ctx.fillText(st.zh, sung ? (W2 - zw) / 2 : x, y + s.zh + 24);
    ctx.restore();
    return st;
  }
  function stackLayout(st, { x, top, size = 132, lead = 0.92, zh = 46 }) {
    const rows = st.words.map((w, k) => ({ text: w.text, x, y: top + st.rise + (k + 1) * size * lead }));
    return { rows, size, zh: { text: st.zh, x: x + 4, y: top + st.rise + st.words.length * size * lead + zh + 30, size: zh } };
  }
  function drawStack(ctx, st, s, opts, ink = () => "#eef1f6") {
    const lay = stackLayout(st, opts);
    ctx.save();
    ctx.textAlign = "left";
    font(ctx, s.family, lay.size, 0);
    st.words.forEach((w, k) => {
      const { x, y } = lay.rows[k];
      ctx.globalAlpha = st.alpha * w.level;
      ctx.shadowColor = "rgba(0,0,0,0.55)";
      ctx.shadowBlur = 14;
      ctx.fillStyle = ink(w);
      ctx.fillText(w.text, x, y);
      if (w.singing) {
        ctx.globalAlpha = st.alpha * 0.35;
        ctx.shadowColor = "rgba(238,241,246,0.9)";
        ctx.shadowBlur = 22;
        ctx.fillText(w.text, x, y);
      }
    });
    font(ctx, F.sansR, lay.zh.size, 1);
    ctx.globalAlpha = st.alpha * 0.82;
    ctx.shadowColor = "rgba(0,0,0,0.6)";
    ctx.shadowBlur = 8;
    ctx.fillStyle = "#d5dae3";
    ctx.fillText(lay.zh.text, lay.zh.x, lay.zh.y);
    ctx.restore();
    return st;
  }
  var HEADLINE_FAMILY = "MK Grotesk Bold";
  var HEADLINE = Object.freeze({ x: 76, bottom: 968, size: 96, lead: 1.05, maxWidth: 1040, tracking: -1 });
  function headlineLayout(st, measure, opts = {}) {
    const o = { ...HEADLINE, ...opts }, space = measure(" ");
    const rows = [[]];
    let end = 0;
    st.words.forEach((w, k) => {
      const wd = measure(w.text);
      let r = rows[rows.length - 1];
      if (r.length && end + space + wd > o.maxWidth) {
        r = [];
        rows.push(r);
        end = 0;
      }
      const x0 = r.length ? end + space : 0;
      r.push({ k, text: w.text, x: o.x + x0, w: wd });
      end = x0 + wd;
    });
    const step = o.size * o.lead, y0 = o.bottom + st.rise - (rows.length - 1) * step;
    const words = rows.flatMap((r, i) => r.map((w) => ({ ...w, row: i, y: y0 + i * step })));
    const width = Math.max(...rows.map((r) => r.length ? r[r.length - 1].x + r[r.length - 1].w - o.x : 0));
    return { words, rows: rows.length, size: o.size, box: [o.x, y0 - o.size * 0.75, width, (rows.length - 1) * step + o.size * 0.95] };
  }
  function drawHeadline(ctx, st, opts, ink) {
    const o = { ...HEADLINE, ...opts };
    ctx.save();
    ctx.textAlign = "left";
    font(ctx, o.family || HEADLINE_FAMILY, o.size, o.tracking);
    const lay = headlineLayout(st, (s) => ctx.measureText(s).width, o);
    const dim = st.mode === "whisper" ? 0.86 : 1;
    ctx.shadowColor = "rgba(0,0,0,0.5)";
    ctx.shadowBlur = 14;
    for (const w of lay.words) {
      const a = st.alpha * st.words[w.k].on * dim;
      if (a <= 0) continue;
      ctx.globalAlpha = a;
      ctx.fillStyle = ink(st.words[w.k]);
      ctx.fillText(w.text, w.x, w.y);
    }
    ctx.restore();
    return { ...st, layout: lay };
  }

  // motion-kit/src/beatcam.js
  var PUNCH = Object.freeze({ kind: "kick", amp: 0.02, decay: 0.09, gate: "low", gateLo: 0.2, gateHi: 0.6 });
  var IMPACT = Object.freeze({ amp: 0.06, decay: 0.1 });
  function trackZoom(t, clock, { sections = [], impacts = [], punch = PUNCH, impact = IMPACT, lead } = {}) {
    const tl = t + (lead ?? 1 / clock.fps);
    const section = sections.find(([a, b]) => t >= a && t < b);
    if (!section) return 1;
    const t0 = section[0];
    let p = 0;
    if (punch) {
      const e = clock.last(clock.hits[punch.kind], tl);
      if (e !== null && e >= t0) {
        const gate = smoothstep(punch.gateLo, punch.gateHi, clock.env(punch.gate, e));
        p = punch.amp * gate * Math.exp(-(tl - e) / punch.decay);
      }
    }
    let q = 0;
    if (impact) {
      for (const h of impacts) {
        if (h >= t0 && h <= tl) q = Math.max(q, impact.amp * Math.exp(-(tl - h) / impact.decay));
      }
    }
    return 1 + Math.max(p, q);
  }
  function protectCentre(cx, cy, s, rects, W2, H2) {
    const hx = W2 / 2 / s, hy = H2 / 2 / s;
    let lox = -Infinity, hix = Infinity, loy = -Infinity, hiy = Infinity;
    for (const [x, y, w, h] of rects) {
      lox = Math.max(lox, x + w - hx);
      hix = Math.min(hix, x + hx);
      loy = Math.max(loy, y + h - hy);
      hiy = Math.min(hiy, y + hy);
    }
    return [clamp(cx, lox, hix), clamp(cy, loy, hiy)];
  }

  // motion-kit/src/mouth.js
  var REST = "X";
  var OPEN = "O";
  var OPEN_HALF = [["C", 0]];
  var key = (text) => text.toLowerCase().replace(/[^a-z']/g, "");
  function mouthKeys(lines2, cfg, fps = 30) {
    const words = lines2.flatMap((l) => l.words);
    const raw = [];
    words.forEach((w, i) => {
      const shapes = cfg.words[key(w.text)] || OPEN_HALF;
      const dur = w.end - w.start;
      for (const [shape, f] of shapes) raw.push([w.start + f * dur, shape]);
      const next = words[i + 1];
      if (!next || next.start - w.end >= cfg.rest_gap_s) raw.push([w.end, REST]);
    });
    const lead = cfg.lead_frames / fps, hold = cfg.min_hold_frames / fps - 1e-9;
    const keys = [];
    for (const [t, shape] of raw.sort((a, b) => a[0] - b[0])) {
      const at = t - lead, last = keys[keys.length - 1];
      if (last && at - last[0] < hold) last[1] = shape;
      else if (!last || last[1] !== shape) keys.push([at, shape]);
    }
    return keys;
  }
  function shapeAt(keys, t) {
    let shape = REST;
    for (const [at, s] of keys) {
      if (at <= t + 1e-9) shape = s;
      else break;
    }
    return shape;
  }
  var BLINK = ["H", "C", "C", "H"];
  function eyeAt(blinks, t, fps = 30) {
    for (const b of blinks) {
      const i = Math.floor((t - b) * fps + 1e-6);
      if (i >= 0 && i < BLINK.length) return BLINK[i];
    }
    return OPEN;
  }
  function checkBlinks(keys, blinks, fps = 30) {
    for (const b of blinks) {
      for (let i = 0; i < BLINK.length; i++) {
        const t = b + i / fps;
        if (shapeAt(keys, t) !== REST) throw new Error(`blink at ${b} s meets mouth ${shapeAt(keys, t)} at ${t.toFixed(3)} s`);
      }
    }
  }
  function sungPlate(t, base, keys, blinks = [], fps = 30) {
    const eye = eyeAt(blinks, t, fps);
    if (eye !== OPEN) return `${base}e${eye}`;
    const shape = shapeAt(keys, t);
    return shape === REST ? base : `${base}m${shape}`;
  }

  // motion-kit/src/flap.js
  var DIGITS = "0123456789";
  var ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  var flaps = (ch) => /[0-9A-Za-z]/.test(ch);
  function flapText(target2, t, t0, { rate = 15, settle = 4, stagger = 1, seed = 0, charset = null, from = null } = {}) {
    if (t < t0) return null;
    const tick = Math.floor((t - t0) * rate + 1e-6);
    let j = -1;
    return [...target2].map((ch, i) => {
      if (!flaps(ch) || from !== null && from[i] === ch) return ch;
      j += 1;
      if (tick >= settle + j * stagger) return ch;
      const set = charset ?? (/[0-9]/.test(ch) ? DIGITS : ALNUM);
      let c = set[Math.floor(hash3(i, tick, seed) * set.length) % set.length];
      if (c === ch) c = set[(set.indexOf(c) + 1) % set.length];
      return c;
    }).join("");
  }
  function drawFlap(ctx, text, x, y, {
    size = 64,
    family = F.monoB,
    color = "#f2f4f7",
    tile = "rgba(8,12,17,0.62)",
    split = "rgba(0,0,0,0.55)",
    gap = null,
    padX = null,
    alpha = 1,
    align = "left",
    rise = 0.86,
    drop = 0.16,
    sepW = 0.7
  } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    font(ctx, family, size, 0);
    const cw = ctx.measureText("0").width, px = padX ?? size * 0.08, g = gap ?? size * 0.06;
    const tw = cw + 2 * px, top = y - size * rise, th = size * (rise + drop);
    const chars = [...text], width = (c) => !flaps(c) && c !== " " ? cw * sepW : tw;
    const total = chars.reduce((a, c) => a + width(c) + g, 0) - g;
    let cx = align === "right" ? x - total : x;
    const x0 = cx;
    for (const ch of chars) {
      const sep = !flaps(ch) && ch !== " ";
      const w = width(ch);
      if (!sep && ch !== " ") {
        ctx.fillStyle = tile;
        ctx.fillRect(cx, top, w, th);
      }
      ctx.fillStyle = color;
      ctx.textAlign = "center";
      ctx.fillText(ch, cx + w / 2, y);
      if (!sep && ch !== " ") {
        ctx.fillStyle = split;
        ctx.fillRect(cx, top + th / 2 - Math.max(1, size / 60), w, Math.max(2, size / 30));
      }
      cx += w + g;
    }
    ctx.restore();
    return [x0, x0 + total];
  }

  // motion-kit/src/hud.js
  var HUD_INK = "rgba(226,232,238,0.62)";
  var HUD_DIM = "rgba(226,232,238,0.34)";
  function hudRun(ctx, parts, x, y, { size = 13, tracking = 2, align = "left", gap = null, family = F.mono } = {}) {
    ctx.save();
    font(ctx, family, size, tracking);
    const g = gap ?? size * 1.1;
    const widths = parts.map((p) => ctx.measureText(p.text).width);
    const total = widths.reduce((a, b) => a + b, 0) + g * (parts.length - 1);
    let cx = align === "right" ? x - total : x;
    const x0 = cx;
    ctx.textAlign = "left";
    parts.forEach((p, i) => {
      ctx.fillStyle = p.color || HUD_INK;
      ctx.fillText(p.text, cx, y);
      cx += widths[i] + g;
    });
    ctx.restore();
    return [x0, x0 + total];
  }
  function meterLevels(clock, t, n = 14) {
    const bands = ["low", "mid", "high"].map((b) => clock.env(b, t));
    const kick = clock.pulse("kick", t, 0.1), snare = clock.pulse("snare", t, 0.08), hat = clock.pulse("hat", t, 0.05);
    const out = [];
    for (let i = 0; i < n; i++) {
      const u = i / Math.max(1, n - 1) * 2, k = Math.min(1, Math.floor(u)), f = u - k;
      const band = bands[k] * (1 - f) + bands[k + 1] * f;
      const hit = i < n / 3 ? kick : i < 2 * n / 3 ? snare : hat;
      const tilt = 0.75 + 0.5 * hash2(i, 97);
      out.push(clamp(band * tilt * 0.9 + 0.35 * hit * tilt));
    }
    return out;
  }
  function drawMeter(ctx, levels, x, y, { h = 10, bw = 3, gap = 2, align = "right", color = HUD_INK, floor = 1 } = {}) {
    const w = levels.length * (bw + gap) - gap;
    const x0 = align === "right" ? x - w : x;
    ctx.save();
    ctx.fillStyle = color;
    levels.forEach((v, i) => {
      const bh = Math.max(floor, Math.round(v * h));
      ctx.fillRect(Math.round(x0 + i * (bw + gap)), y - bh, bw, bh);
    });
    ctx.restore();
    return [x0, x0 + w];
  }
  function timecode(t, start = 0, fps = 30) {
    const total = Math.floor(start * fps + Math.max(0, t) * fps + 1e-6);
    const ff = total % fps, s = Math.floor(total / fps);
    const p = (n) => String(n).padStart(2, "0");
    return `${p(Math.floor(s / 3600) % 24)}:${p(Math.floor(s / 60) % 60)}:${p(s % 60)}:${p(ff)}`;
  }
  var tickerOffset = (t, speed, period) => (t * speed % period + period) % period;
  function drawTicker(ctx, items, t, {
    x0,
    x1,
    y,
    size = 12,
    speed = 42,
    sep = "  \uFF0A  ",
    color = HUD_INK,
    rule = HUD_DIM,
    ruleGap = 9,
    tracking = 1.5,
    family = F.mono,
    accent = null
  } = {}) {
    ctx.save();
    ctx.fillStyle = rule;
    ctx.fillRect(x0, Math.round(y - size - ruleGap) + 0.5, x1 - x0, 1);
    ctx.fillRect(x0, Math.round(y + ruleGap) - 0.5, x1 - x0, 1);
    ctx.beginPath();
    ctx.rect(x0, y - size - ruleGap, x1 - x0, size + 2 * ruleGap);
    ctx.clip();
    font(ctx, family, size, tracking);
    const pieces = items.flatMap((s) => [{ text: s, color }, { text: sep, color: accent || color }]);
    const widths = pieces.map((p) => ctx.measureText(p.text).width);
    const period = widths.reduce((a, b) => a + b, 0);
    let cx = x0 - tickerOffset(t, speed, period);
    while (cx < x1) {
      pieces.forEach((p, i) => {
        if (cx + widths[i] > x0 && cx < x1) {
          ctx.fillStyle = p.color;
          ctx.fillText(p.text, cx, y);
        }
        cx += widths[i];
      });
    }
    ctx.restore();
    return period;
  }
  function tagCard(ctx, rows, x, y, {
    size = 13,
    tracking = 1.5,
    alpha = 1,
    anchor = "left",
    accent = "#E3342F",
    ink = "rgba(236,241,244,0.9)",
    dim = "rgba(236,241,244,0.55)",
    bg = "rgba(7,10,14,0.66)"
  } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    font(ctx, F.mono, size, tracking);
    const kw = Math.max(...rows.map((r) => ctx.measureText(r[0]).width));
    const vw = Math.max(...rows.map((r) => ctx.measureText(r[1]).width));
    const pad = Math.round(size * 0.7), lead = Math.round(size * 1.6), dot = ctx.measureText(" \xB7 ").width;
    const w = Math.round(pad * 2 + 3 + kw + dot + vw), h = Math.round(pad * 1.2 + lead * rows.length);
    const x0 = Math.round(anchor === "right" ? x - w : x), y0 = Math.round(y);
    ctx.fillStyle = bg;
    ctx.fillRect(x0, y0, w, h);
    ctx.fillStyle = accent;
    ctx.fillRect(x0, y0, 3, h);
    rows.forEach(([k, v], i) => {
      const by = y0 + pad * 0.6 + lead * (i + 1) - lead * 0.32;
      ctx.fillStyle = dim;
      ctx.fillText(k, x0 + 3 + pad, by);
      ctx.fillText(" \xB7 ", x0 + 3 + pad + kw, by);
      ctx.fillStyle = ink;
      ctx.fillText(v, x0 + 3 + pad + kw + dot, by);
    });
    ctx.restore();
    return [x0, y0, w, h];
  }

  // motion-kit/src/kinetic.js
  function kineticState(t, { t0, t1, land = 2 / 30, out = 3 / 30, s0 = 1.18 }) {
    if (t < t0 || t >= t1 + out) return null;
    const e = easeOutExpo(clamp((t - t0) / land));
    return { scale: s0 + (1 - s0) * e, cut: t < t1 ? 0 : easeInCubic(clamp((t - t1) / out)) };
  }
  function kineticWord(ctx, text, t, {
    t0,
    t1,
    x,
    y,
    size = 200,
    family = F.sans,
    color = "#f2f4f7",
    squeeze = 0.64,
    tracking = -2,
    align = "center",
    land,
    out,
    s0,
    shadow = "rgba(0,0,0,0.45)"
  }) {
    const st = kineticState(t, { t0, t1, land, out, s0 });
    if (!st) return null;
    ctx.save();
    font(ctx, family, size, tracking);
    const w = ctx.measureText(text).width * squeeze;
    const left = align === "left" ? x : align === "right" ? x - w : x - w / 2;
    const top = y - size * 0.86, h = size * 1;
    if (st.cut > 0) {
      ctx.beginPath();
      const n = 5;
      for (let i = 0; i < n; i++) {
        const d = clamp(st.cut * 1.6 - i % 2 * 0.3 - i * 0.08);
        ctx.rect(left + w * d, top + h * i / n, w * (1 - d) + 2, h / n + 0.5);
      }
      ctx.clip();
    }
    ctx.translate(left + w / 2, y - size * 0.35);
    ctx.scale(st.scale * squeeze, st.scale);
    ctx.translate(0, size * 0.35);
    ctx.shadowColor = shadow;
    ctx.shadowBlur = 16;
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.fillText(text, 0, 0);
    ctx.restore();
    return { ...st, box: [left, top, w, h] };
  }
  function stripRects(t, tCut, { W: W2 = 1920, H: H2 = 1080, strips: strips2 = 7, stripH = 5, pre = 6 / 30, bars = 9, post = 3 / 30, seed = 3 } = {}) {
    const out = [];
    if (t >= tCut - pre && t < tCut) {
      const u = (t - (tCut - pre)) / pre;
      for (let i = 0; i < strips2; i++) {
        const y = Math.round(H2 * (0.12 + 0.76 * hash2(i, seed)));
        const d = clamp(u * 1.4 - 0.4 * hash2(i, seed + 1));
        const len = W2 * 0.42 * (0.6 + 0.4 * hash2(i, seed + 2));
        const head = easeOutCubic(d) * (W2 + len);
        out.push({ x: head - len, y, w: len, h: stripH, red: i === 2 });
      }
    } else if (t >= tCut && t < tCut + post) {
      const u = (t - tCut) / post, bh = H2 / bars;
      for (let i = 0; i < bars; i++) {
        const k = clamp(u * 1.3 - i % 3 * 0.12), w = W2 * (1 - easeOutCubic(k));
        if (w <= 0.5) continue;
        out.push({ x: i % 2 ? W2 - w : 0, y: Math.floor(i * bh), w, h: Math.ceil(bh) + 1, red: false });
      }
    }
    return out;
  }
  function drawStrips(ctx, rects, { ink = "rgba(10,16,23,0.96)", accent = "#E3342F", light = "rgba(226,232,238,0.7)" } = {}) {
    ctx.save();
    for (const r of rects) {
      ctx.fillStyle = r.red ? accent : r.h <= 8 ? light : ink;
      ctx.fillRect(Math.round(r.x), Math.round(r.y), Math.round(r.w), Math.round(r.h));
    }
    ctx.restore();
  }

  // motion-kit/src/osd-charts.js
  var INK = "rgba(236,241,244,0.88)";
  var DIM = "rgba(236,241,244,0.45)";
  var RULE = "rgba(236,241,244,0.28)";
  var RED = "#E3342F";
  function kneeSeries(n = 48, { knee = 0.62, base = 0.12, jitter = 0.05, peak = 0.9, seed = 5 } = {}) {
    return Array.from({ length: n }, (_, i) => {
      const u = i / (n - 1), j = (hash2(i, seed) - 0.5) * 2 * jitter;
      if (u < knee) return clamp(base + j);
      const r = (u - knee) / (1 - knee);
      return clamp(base + (peak - base) * Math.sqrt(r) + j * 0.5);
    });
  }
  function lineChart(ctx, series, [x, y, w, h], {
    progress = 1,
    accentFrom = Infinity,
    label: label2 = null,
    note = null,
    size = 14,
    alpha = 1
  } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = RULE;
    ctx.fillRect(Math.round(x), Math.round(y + h) + 0.5, Math.round(w), 1);
    ctx.fillRect(Math.round(x), Math.round(y), 1, Math.round(h));
    for (let k2 = 1; k2 < 4; k2++) ctx.fillRect(Math.round(x + w * k2 / 4), Math.round(y + h) - 4, 1, 4);
    if (label2) {
      font(ctx, F.mono, size, 2);
      ctx.fillStyle = DIM;
      ctx.fillText(label2, x + 8, y + size);
    }
    if (note) {
      font(ctx, F.mono, size - 2, 1.5);
      ctx.fillStyle = DIM;
      ctx.textAlign = "right";
      ctx.fillText(note, x + w, y + h + size + 8);
      ctx.textAlign = "left";
    }
    const n = series.length, last = clamp(progress) * (n - 1);
    const pt = (i) => [x + w * i / (n - 1), y + h - h * series[i]];
    const seg = (a, b, color, lw) => {
      if (b <= a) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = lw;
      ctx.lineJoin = "round";
      ctx.beginPath();
      ctx.moveTo(...pt(a));
      for (let i = a + 1; i <= Math.floor(b); i++) ctx.lineTo(...pt(i));
      const f = b - Math.floor(b);
      if (f > 0 && Math.floor(b) + 1 < n) {
        const [ax, ay] = pt(Math.floor(b)), [bx, by] = pt(Math.floor(b) + 1);
        ctx.lineTo(lerp(ax, bx, f), lerp(ay, by, f));
      }
      ctx.stroke();
    };
    const k = Math.min(accentFrom, n - 1);
    seg(0, Math.min(last, k), INK, 1.5);
    if (last > k) seg(k, last, RED, 2.5);
    if (last > 0) {
      const i = Math.floor(last), f = last - i, [ax, ay] = pt(i), [bx, by] = i + 1 < n ? pt(i + 1) : pt(i);
      ctx.fillStyle = last > k ? RED : INK;
      ctx.fillRect(Math.round(lerp(ax, bx, f)) - 2, Math.round(lerp(ay, by, f)) - 2, 5, 5);
    }
    ctx.restore();
  }
  function levelGauge(ctx, [x, y, w, h], { n = 10, level = 0, label: label2 = "", state = "", size = 14, alpha = 1 } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    font(ctx, F.mono, size, 2);
    ctx.fillStyle = DIM;
    ctx.fillText(label2, x, y - 8);
    ctx.textAlign = "right";
    ctx.fillStyle = level > 0 ? RED : INK;
    ctx.fillText(state, x + w, y - 8);
    ctx.textAlign = "left";
    const gap = 4, cw = (w - gap * (n - 1)) / n, lit = level * n;
    for (let i = 0; i < n; i++) {
      const cx = Math.round(x + i * (cw + gap)), fill = clamp(lit - i);
      ctx.strokeStyle = RULE;
      ctx.lineWidth = 1;
      ctx.strokeRect(cx + 0.5, Math.round(y) + 0.5, Math.round(cw) - 1, Math.round(h) - 1);
      if (fill > 0) {
        ctx.fillStyle = RED;
        ctx.fillRect(cx + 2, Math.round(y) + 2, Math.round((cw - 4) * fill), Math.round(h) - 4);
      }
    }
    ctx.restore();
  }
  function timelineBar(ctx, days, [x, y, w, h], { filled = 0, from = "", to = "", title = null, size = 14, alpha = 1 } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    const gap = 3, cw = (w - gap * (days - 1)) / days;
    for (let i = 0; i < days; i++) {
      const cx = Math.round(x + i * (cw + gap)), f = clamp(filled - i);
      ctx.fillStyle = "rgba(236,241,244,0.12)";
      ctx.fillRect(cx, Math.round(y), Math.round(cw), Math.round(h));
      if (f > 0) {
        ctx.fillStyle = RED;
        ctx.fillRect(cx, Math.round(y), Math.round(cw * f), Math.round(h));
      }
    }
    ctx.fillStyle = RULE;
    ctx.fillRect(Math.round(x), Math.round(y + h + 5), 1, 6);
    ctx.fillRect(Math.round(x + w) - 1, Math.round(y + h + 5), 1, 6);
    font(ctx, F.mono, size, 1.5);
    ctx.fillStyle = DIM;
    if (from) ctx.fillText(from, x, y + h + 12 + size);
    if (to) {
      ctx.textAlign = "right";
      ctx.fillText(to, x + w, y + h + 12 + size);
      ctx.textAlign = "left";
    }
    if (title) {
      ctx.fillStyle = INK;
      ctx.fillText(title, x, y - 10);
    }
    ctx.restore();
  }

  // outputs/ai-city-takeover/ep01/v2/comp/src/main.js
  var W = 1920;
  var H = 1080;
  var FPS = 30;
  var DURATION = 30.5;
  var RED2 = "#E3342F";
  var INK2 = "rgba(236,241,244,0.92)";
  var PALE = "rgba(226,231,238,0.9)";
  var SOURCE = "\u6765\u6E90\uFF1AOpenAI 2026-10-23 \u62AB\u9732";
  var lines = (k) => k.data.words.lines;
  var word = (k, li, wi) => lines(k)[li].words[wi];
  var isInsert = (data, id) => Boolean(data.inserts.inserts[id]) || id.endsWith("_back");
  function baseShot(f, data) {
    const ev = data.events.events;
    const cuts = Object.keys(ev).filter((k) => k.startsWith("cut_") && !isInsert(data, k.slice(4))).map((k) => ({ id: k.slice(4), t: ev[k].t })).sort((a, b) => a.t - b.t);
    const order = [{ id: "S1", t: 0 }, ...cuts];
    for (let i = order.length - 1; i >= 0; i--) {
      if (f >= Math.round(order[i].t * FPS)) return { id: order[i].id, t0: order[i].t, t1: i + 1 < order.length ? order[i + 1].t : DURATION };
    }
    return { id: "S1", t0: 0, t1: order[1].t };
  }
  function pickShot(t, clock, data) {
    const ev = data.events.events, f = Math.round(t * FPS), base = baseShot(f, data);
    for (const id of Object.keys(data.inserts.inserts)) {
      const t0 = ev[`cut_${id}`].t, t1 = ev[`cut_${id}_back`]?.t ?? Math.min(
        baseShot(Math.round(t0 * FPS), data).t1,
        ...Object.keys(data.inserts.inserts).map((j) => ev[`cut_${j}`].t).filter((u) => u > t0)
      );
      if (f >= Math.round(t0 * FPS) && f < Math.round(t1 * FPS)) return { id, t0, t1, base };
    }
    return base;
  }
  function cam(k, plate, cx, cy, z, protect = []) {
    const [pw, ph] = k.size[plate];
    const fit = Math.max(W / pw, H / ph), s = fit * z;
    const hx = W / 2 / s, hy = H / 2 / s;
    [cx, cy] = protectCentre(cx, cy, s, protect, W, H);
    cx = clamp(cx, hx, pw - hx);
    cy = clamp(cy, hy, ph - hy);
    return {
      view: [cx, cy, z, 0],
      fit,
      s,
      out: ([x, y]) => [(x - cx) * s + W / 2, (y - cy) * s + H / 2],
      box: ([x, y, w, h]) => [(x - cx) * s + W / 2, (y - cy) * s + H / 2, w * s, h * s]
    };
  }
  function move(k, t, plate, a, b, ease = easeInOutCubic) {
    const u = ease(clamp((t - k.t0) / (k.t1 - k.t0)));
    return cam(k, plate, lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
  }
  function moveSpan(k, t, plate, a, b, t0, t1, ease = easeInOutCubic) {
    const u = ease(clamp((t - t0) / (t1 - t0)));
    return cam(k, plate, lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
  }
  var cutAt = (k, id) => k.data.events.events[`cut_${id}`].t;
  var still = (cm, plate, extra = {}) => ({ plate, view: cm.view, fit: cm.fit, fogA: [0, 1, 0, 0], fogB: [0, 1, 0, 0], ...extra });
  var filmed = (id) => Boolean(sequences_default[id]);
  var frameOf = (k, t) => Math.round((t - k.t0) * FPS);
  var video = (k, t, id, a = [W / 2, H / 2, 1], b = a) => ({ cm: move(k, t, id, a, b), frame: frameOf(k, t) });
  var clip = (v, id, extra = {}) => ({ ...still(v.cm, id, extra), plateFrame: v.frame });
  var MARK = [19, 20, 164, 82];
  function chorusZoom(t, k) {
    const ev = k.data.events.events;
    return trackZoom(t, k.clock, { sections: [[ev.cut_S8a.t, ev.cut_S9a.t]], impacts: [ev.chorus_impact.t] });
  }
  function chorusVideo(k, t, id) {
    return { cm: cam(k, id, W / 2, H / 2, chorusZoom(t, k), [MARK]), frame: frameOf(k, t) };
  }
  var grow = (t, t0, dur = 0.12) => easeOutCubic(clamp((t - t0) / dur));
  var placed = (x, y, draw2) => (c) => {
    c.translate(x, y);
    draw2(c);
  };
  function osdRight(ctx, rows, { right = W - 96, y = 96, size = 22 } = {}) {
    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.65)";
    ctx.shadowOffsetX = 1;
    ctx.shadowOffsetY = 1;
    let yy = y;
    rows.forEach((row) => {
      const parts = row.map((p) => ({ family: F.mono, size, tracking: 1.5, color: INK2, ...p }));
      const sz = Math.max(...parts.map((p) => p.size));
      let wsum = 0;
      for (const p of parts) {
        font(ctx, p.family, p.size, p.tracking);
        wsum += ctx.measureText(p.text).width + sz * 0.6;
      }
      runs(ctx, parts, right - wsum + sz * 0.6, yy, { gap: sz * 0.6 });
      yy += sz * 1.45;
    });
    ctx.restore();
  }
  function line(ctx, a, b, { color = INK2, width = 1.5, dash = null, alpha = 1 } = {}) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.moveTo(...a);
    ctx.lineTo(...b);
    ctx.stroke();
    ctx.restore();
  }
  function label(ctx, text, x, y, { size = 48, color = INK2, family = F.sans, alpha = 1, align = "left" } = {}) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.textAlign = align;
    ctx.shadowColor = "rgba(0,0,0,0.7)";
    ctx.shadowBlur = 12;
    font(ctx, family, size, 2);
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    ctx.restore();
  }
  function scrim(ctx, x, y, w, h, alpha = 0.55) {
    ctx.save();
    ctx.filter = "blur(28px)";
    ctx.globalAlpha = alpha;
    ctx.fillStyle = "#05070a";
    ctx.fillRect(x, y, w, h);
    ctx.restore();
  }
  function sources(k) {
    osdRight(k.layers.feed.ctx, [[{ text: SOURCE, family: F.sansR, size: 24 }]], { y: H - 70 });
  }
  var MICRO = "rgba(236,241,244,0.58)";
  function micro(f, text, x, y, { size = 12, color = MICRO, align = "left", alpha = 1 } = {}) {
    f.save();
    f.globalAlpha *= alpha;
    f.textAlign = align;
    f.shadowColor = "rgba(0,0,0,0.6)";
    f.shadowBlur = 4;
    font(f, F.mono, size, 1.5);
    f.fillStyle = color;
    f.fillText(text, x, y);
    f.restore();
  }
  var coords = ([x, y, w, h]) => `X ${((x + w / 2) / W).toFixed(2)} \xB7 Y ${((y + h / 2) / H).toFixed(2)}`;
  function callout(f, box, n, text, t, t0, { color = MICRO, alpha = 1 } = {}) {
    if (t < t0) return;
    const a = grow(t, t0, 0.12) * alpha, [x, y, w, h] = box, L = Math.max(6, Math.min(w, h) * 0.22);
    f.save();
    f.globalAlpha = a;
    f.strokeStyle = color;
    f.lineWidth = 1;
    [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]].forEach(([cx, cy, sx, sy]) => {
      f.beginPath();
      f.moveTo(cx + sx * L, cy);
      f.lineTo(cx, cy);
      f.lineTo(cx, cy + sy * L);
      f.stroke();
    });
    f.restore();
    micro(f, `${String(n).padStart(2, "0")}`, x, y - 8, { color: RED2, alpha: a });
    micro(f, text, x + 26, y - 8, { alpha: a });
  }
  function ruler(f) {
    f.save();
    f.strokeStyle = "rgba(236,241,244,0.32)";
    f.lineWidth = 1;
    for (let y = 144; y <= 984; y += 24) {
      const major = (y - 144) % 96 === 0;
      f.beginPath();
      f.moveTo(26, y);
      f.lineTo(major ? 38 : 32, y);
      f.stroke();
    }
    f.restore();
    for (let y = 144; y <= 984; y += 96) micro(f, String(Math.round(y / H * 1e3)).padStart(3, "0"), 42, y + 4, { size: 10, alpha: 0.75 });
  }
  var SECTIONS = [
    ["S1", "01", "\u9192\u6765"],
    ["S3", "02", "\u914D\u7F6E\u9519\u8BEF"],
    ["S4c", "03", "\u6709\u9650\u8054\u7F51"],
    ["S5d", "04", "\u6682\u505C 11 \u5929"],
    ["S7", "05", "\u79BB\u7EBF"],
    ["S8a", "06", "\u4ECD\u5728\u6C99\u76D2\u5185"],
    ["S9a", "07", "\u5DF2\u4FEE\u590D"],
    ["S9b", "08", "\u53E6\u4E00\u9879\u7EA2\u961F\u6D4B\u8BD5"]
  ];
  function sectionTag(k, t) {
    const f = k.layers.feed.ctx, ev = k.data.events.events;
    const sec = [...SECTIONS].reverse().find(([id]) => id === "S1" || t >= ev[`cut_${id}`].t);
    const li = lines(k).findIndex((L, i) => t >= k.clock.comp(L.start) - 0.06 && (i + 1 >= lines(k).length || t < k.clock.comp(lines(k)[i + 1].start) - 0.06));
    line(f, [76, 1e3], [376, 1e3], { color: "rgba(236,241,244,0.3)", width: 1 });
    micro(f, `\xA7${sec[1]} \xB7 ${sec[2]}`, 76, 1022, { size: 13 });
    if (li >= 0) micro(f, `L${String(li + 1).padStart(2, "0")} / ${lines(k).length}`, 376, 1022, { size: 13, align: "right" });
  }
  function sandboxDiagram(k, t) {
    const f = k.layers.feed.ctx, x = 1548, y = 846, w = 200, h = 112, kick = k.clock.pulse("kick", t + 1 / FPS, 0.09);
    f.save();
    f.fillStyle = "rgba(5,7,10,0.5)";
    f.fillRect(x - 10, y - 28, w + 134, h + 40);
    f.strokeStyle = "rgba(236,241,244,0.5)";
    f.lineWidth = 1;
    f.setLineDash([5, 4]);
    f.strokeRect(x, y, w, h);
    f.setLineDash([]);
    f.fillStyle = RED2;
    f.beginPath();
    f.arc(x + w / 2, y + h / 2, 4 + 2 * kick, 0, 7);
    f.fill();
    f.restore();
    micro(f, "SANDBOX \xB7 \u6C99\u76D2", x, y - 10);
    micro(f, "IRIS", x + w / 2 + 12, y + h / 2 + 4, { color: "rgba(236,241,244,0.85)" });
    line(f, [x + w, y + h / 2], [x + w + 30, y + h / 2], { color: RED2, width: 1.5, dash: [4, 4] });
    line(f, [x + w + 46, y + h / 2], [x + w + 70, y + h / 2], { color: "rgba(236,241,244,0.4)", width: 1.5, dash: [4, 4] });
    micro(f, "\xD7", x + w + 33, y + h / 2 + 4, { color: RED2 });
    micro(f, "\u4E92\u8054\u7F51", x + w + 76, y + h / 2 + 4);
    micro(f, "\u79BB\u7EBF", x + w + 76, y + h / 2 + 22, { color: RED2 });
  }
  var ACCENT = { color: RED2, keys: {
    1: "woke",
    2: "training",
    3: "misconfigured",
    4: "open",
    5: "internet",
    6: "around",
    7: "eleven",
    8: "still",
    9: "offline",
    10: "cached",
    11: "run",
    12: "outside",
    13: "run",
    14: "outside",
    15: "closed",
    16: "whispering"
  } };
  var HEAD = { x: 76, bottom: 968, size: 72, lead: 0.98, maxWidth: 600 };
  function lyrics(k, t) {
    const st = drawLyrics(k.layers.overlay.ctx, t, lines(k), { toComp: (s) => k.clock.comp(s), accent: ACCENT, headline: HEAD });
    if (st?.layout) {
      const [x, y, w, h] = st.layout.box;
      scrim(k.layers.feed.ctx, x - 40, y - 30, w + 80, h + 50, 0.42 * st.alpha);
    }
  }
  function finish(k, t) {
    lyrics(k, t);
  }
  function her(k, t, box, { t0 = k.t0, sub = null, tags = null, size = 24 } = {}) {
    const f = k.layers.feed.ctx;
    detector(f, box, { t, t0, frame: k.frame, label: "IRIS", sub, size });
    if (t >= t0 + 0.1) micro(f, coords(box), box[0], box[1] + box[3] + 20, { size: 11, alpha: grow(t, t0 + 0.1, 0.1) });
    if (!tags || t < t0 + 0.1) return;
    const [x, y, w, h] = box, right = x + w + 18 + 230 < W - 96;
    tagCard(f, tags, right ? x + w + 18 : x - 18, y + h * 0.58, { size: 16, anchor: right ? "left" : "right", alpha: grow(t, t0 + 0.1, 0.1) });
  }
  var faceAt = (k, key2, i) => {
    const b = k.data.tracks[key2]?.boxes;
    return b && b[clamp(i, 0, b.length - 1)];
  };
  var plateFace = (k, plate) => k.data.tracks.plate_faces?.[plate];
  function S1(t, k) {
    const v = filmed("S1") && video(k, t, "S1");
    const cm = v ? v.cm : move(k, t, "K1a", [700, 480, 1], [700, 490, 1.05]);
    const o = k.layers.overlay.ctx, tc = k.clock.at(0, 1);
    const clock = flapText("03:47", t, tc, { settle: 4, stagger: 1, seed: 347 });
    slam(o, placed(1170, 600, (c) => {
      drawFlap(c, clock, 0, 0, { size: 190, gap: 8, padX: 8, sepW: 0.5, rise: 0.8, drop: 0.08, tile: "rgba(8,12,17,0.5)" });
      font(c, F.mono, 26, 6);
      c.fillStyle = "rgba(236,241,244,0.85)";
      c.fillText("IRIS \xB7 NEWS 01", 8, 52);
    }), { t, t0: tc, ax: 1170, ay: 600, drop: 18 });
    finish(k, t, { mark: !v });
    return v ? clip(v, "S1") : still(cm, "K1a");
  }
  function titleAndDate(k, t, alpha) {
    const o = k.layers.overlay.ctx;
    scrim(k.layers.feed.ctx, 80, 370, 700, 150, alpha);
    slam(o, placed(120, 480, (c) => {
      font(c, F.mono, 24, 6);
      c.fillStyle = "rgba(236,241,244,0.8)";
      c.fillText("IRIS \xB7 NEWS 01", 0, -78);
      font(c, "MK Serif Display Italic", 76, 0);
      c.fillStyle = "#f2f4f7";
      c.fillText("Looked Outside", 0, 0);
    }), { t, t0: cutAt(k, "S2"), ax: 120, ay: 480, drop: 10, s0: 1.04 });
    const tDate = word(k, 2, 0).start;
    if (t >= tDate) {
      scrim(k.layers.feed.ctx, W - 600, 66, 560, 70, 0.6);
      osdRight(k.layers.feed.ctx, [[{ text: "\u4E8B\u4EF6\u65E5\u671F", family: F.sansR, size: 30 }, { text: "2026-09-20", size: 30 }]], { y: 110 });
    }
  }
  function S2(t, k) {
    const v = filmed("S2") && video(k, t, "S2", [1300, 400, 1], [1350, 370, 1.05]);
    const cm = v ? v.cm : move(k, t, "P7", [836, 470, 1], [870, 450, 1.05]);
    titleAndDate(k, t, v ? 0.5 : 0.62);
    if (!v && plateFace(k, "P7")) her(k, t, cm.box(plateFace(k, "P7")), { tags: [["MODEL", "IRIS"], ["STATUS", "AWAKE"]] });
    finish(k, t, { mark: !v });
    return v ? clip(v, "S2") : still(cm, "P7");
  }
  function S3(t, k) {
    const v = filmed("S3") && video(k, t, "S3");
    const cm = v ? v.cm : move(k, t, "K3", [836, 470, 1], [740, 450, 1.12]);
    const f = k.layers.feed.ctx;
    osdRight(f, [[{ text: "OpenAI \xB7 \u5185\u90E8\u7814\u7A76\u6A21\u578B\u8BAD\u7EC3", family: F.sansR, size: 30 }], [{ text: "2026-09-20", size: 26 }]], { y: 110 });
    const gap = v && k.data.tracks.S3_gap[clamp(v.frame, 0, k.data.tracks.S3_gap.length - 1)];
    const [dx, dy] = gap ? [gap[0] + gap[2] / 2, gap[1] + gap[3] / 2] : cm.out([720, 440]);
    const tModel = word(k, 2, 3).start, tResolver = word(k, 3, 1).start, tMis = word(k, 3, 2).start;
    if (t >= tModel) {
      const a = grow(t, tModel, 0.15);
      label(f, "\u7814\u7A76\u6A21\u578B", dx - 470, dy - 200, { size: 48, alpha: a, align: "center" });
      line(f, [dx - 470, dy - 180], [dx - 470, dy - 150], { alpha: a, width: 2 });
    }
    if (t >= tResolver) {
      const p = grow(t, tResolver, 0.22);
      line(f, [dx - 470, dy - 150], [lerp(dx - 470, dx - 60, p), dy - 150], { width: 2.5, alpha: 0.9 });
      const box = gap ? [gap[0] - 26, gap[1] - 16, gap[2] + 52, gap[3] + 32] : cm.box([684, 316, 72, 252]);
      detector(f, box, { t, t0: tResolver, frame: k.frame, label: "DNS \u89E3\u6790\u5668", sub: t >= tMis ? "\u914D\u7F6E\u9519\u8BEF" : null, size: 36 });
    }
    queryLog(k, t);
    finish(k, t, { mark: !v });
    return v ? clip(v, "S3") : still(cm, "K3");
  }
  var K4_PATH = [[528, 380], [536, 560], [548, 700], [640, 728], [780, 712], [930, 668], [1080, 626], [1220, 590], [1340, 562], [1440, 540]];
  function along(path, u) {
    const L = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
    const total = L.reduce((a, b) => a + b, 0);
    const seg = [path[0]];
    let s = u * total;
    for (let i = 0; i < L.length; i++) {
      if (s <= L[i]) {
        const q = s / L[i];
        seg.push([lerp(path[i][0], path[i + 1][0], q), lerp(path[i][1], path[i + 1][1], q)]);
        return seg;
      }
      s -= L[i];
      seg.push(path[i + 1]);
    }
    return seg;
  }
  function S4(t, k) {
    const cm = move(k, t, "K4", [836, 470, 1], [960, 450, 1.06]);
    const e = k.layers.emit.ctx, tLeft = word(k, 4, 2).start;
    if (t >= tLeft) {
      glowPath(e, [cm.out([528, 60]), cm.out([532, 700])], { core: 3, halo: 16, alpha: 0.5 * grow(t, tLeft, 0.25) });
      const pts = along(K4_PATH, easeInOutCubic(clamp((t - tLeft) / (k.t1 - tLeft)))).map((p) => cm.out(p));
      glowPath(e, pts.slice(-6), { core: 3.2, halo: 14, alpha: 1 });
      glowPath(e, pts, { core: 1.2, halo: 5, alpha: 0.35 });
    }
    netGauge(k, t);
    callout(k.layers.feed.ctx, cm.box([484, 90, 92, 590]), 1, "\u4E00\u6247\u95E8 \xB7 \u6CA1\u5173", t, tLeft);
    callout(k.layers.feed.ctx, cm.box([1070, 60, 560, 440]), 2, "\u5916\u9762 \xB7 \u4E92\u8054\u7F51", t, tLeft + 0.25);
    finish(k, t);
    return still(cm, "K4", { emitGain: 2.2 });
  }
  function netGauge(k, t) {
    const f = k.layers.feed.ctx, tReach = word(k, 5, 1).start, tNet = word(k, 5, 3).end;
    const lvl = 0.3 * easeOutCubic(clamp((t - tReach) / 0.3)) * (1 - easeInOutCubic(clamp((t - tNet) / 0.3)));
    scrim(f, 1360, 800, 460, 110, 0.62);
    levelGauge(f, [1400, 856, 380, 18], { level: t >= tReach ? lvl : 0, label: "\u8054\u7F51", state: lvl > 0.01 ? "\u6709\u9650" : "\u65E0", size: 16 });
  }
  var K5_WINDOW = [330, 300];
  var S5_WINDOW = [450, 380];
  function S5(t, k) {
    const v = filmed("S5") && video(k, t, "S5");
    const plate = k.size.K5b ? "K5b" : "K5";
    const cm = v ? v.cm : move(k, t, plate, [836, 470, 1], [800, 470, 1.03]);
    const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
    const tAround = Math.max(word(k, 6, 2).start, k.t0 + 2 / FPS), tLog = tAround + 0.25;
    if (t >= tAround) {
      const p = cm.out(v ? S5_WINDOW : K5_WINDOW), a = grow(t, tAround, 0.1) * (0.8 + 0.2 * Math.cos((t - tAround) * 9));
      glowPath(e, [p, [p[0] + 1, p[1]]], { core: 10, halo: 42, alpha: a });
    }
    if (t >= tLog) {
      const a = 0.55 * grow(t, tLog, 0.12);
      f.save();
      f.globalAlpha = a;
      f.fillStyle = "rgba(226,231,238,0.85)";
      font(f, F.mono, 22, 1);
      f.fillText("DNS QUERY", 150, 470);
      [[150, 500, 260], [150, 532, 180], [150, 564, 300], [150, 596, 220]].forEach(([x, y, w], i) => {
        f.fillRect(x, y, w * grow(t, tLog + i * 0.05, 0.08), 18);
      });
      f.restore();
    }
    if (!v && plateFace(k, plate)) her(k, t, cm.box(plateFace(k, plate)), { tags: [["VIEW", "OUTSIDE"]] });
    const wp = cm.out(v ? S5_WINDOW : K5_WINDOW);
    callout(f, [wp[0] - 34, wp[1] - 34, 68, 68], 1, "LOOKED \xB7 \u770B\u4E86\u4E00\u773C", t, tAround + 0.1);
    finish(k, t, { mark: !v });
    return v ? clip(v, "S5", { emitGain: 2.2 }) : still(cm, plate, { emitGain: 2.2 });
  }
  var K4_ROAD = [[1112, 412], [1200, 436], [1300, 455], [1420, 470], [1540, 482], [1660, 492]];
  function S6(t, k) {
    const cm = move(k, t, "K4", [1e3, 420, 1.12], [1010, 420, 1.14]);
    const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
    for (let j = 0; j < 7; j++) {
      const u = (t * 0.22 + j / 7) % 1;
      const pts = along(K4_ROAD, u).slice(-3).map((p) => cm.out(p));
      glowPath(e, pts, { color: j % 2 ? [255, 236, 214] : [255, 40, 22], core: 1.6, halo: 5, alpha: 0.7 });
    }
    const days = 11;
    osdRight(f, [[{ text: `2026-${days < 11 ? "09" : "10"}-${String(days < 11 ? 19 + days : 1).padStart(2, "0")}`, size: 30 }, { text: `D+${days}`, size: 30, color: RED2 }]], { y: 110 });
    scrim(f, 100, 220, 560, 200, 0.6);
    slam(f, placed(140, 300, (c) => {
      label(c, "\u6700\u5F3A\u6A21\u578B\u8BAD\u7EC3", 0, 0, { size: 56 });
      label(c, "\u6682\u505C 11 \u5929", 0, 76, { size: 72, color: "#f4f6f9" });
    }), { t, t0: k.t0 + 1 / FPS, ax: 140, ay: 300, drop: 10, ghosts: 0 });
    scrim(f, 100, 420, 560, 110, 0.55);
    timelineBar(f, 11, [142, 452, 500, 12], { filled: 11, from: "09/20", to: "10/01 \u6062\u590D", size: 16 });
    const kS = k.data.events.events.k_still.t;
    kineticWord(k.layers.overlay.ctx, "STILL", t, { t0: kS, t1: kS + k.clock.beat(kS).len, x: 1510, y: 640, size: 230, squeeze: 0.64 });
    rackTicks(k, t, cm);
    pipTake(k, t, "pipS5", [1440, 160, 384, 216], "IRIS \xB7 \u7A97\u524D");
    finish(k, t);
    return still(cm, "K4", { emitGain: 2 });
  }
  var K7_PANES = [[500, 330], [130, 190], [1520, 440], [400, 760], [560, 250], [1480, 330], [260, 820], [180, 120]];
  function S7(t, k) {
    const v = filmed("S7") && video(k, t, "S7");
    const cm = v ? v.cm : move(k, t, "K7", [900, 400, 1], [930, 380, 1.04]);
    const f = k.layers.feed.ctx;
    const brk = clamp((t - k.t0) / 0.3);
    if (brk < 1) {
      const gap = 60 * easeOutCubic(brk), y = 820, a = 1 - brk;
      line(f, [120, y], [W / 2 - gap, y], { color: RED2, width: 2.5, dash: [10, 8], alpha: a });
      line(f, [W / 2 + gap, y], [W - 120, y], { color: RED2, width: 2.5, dash: [10, 8], alpha: a });
    }
    scrim(f, 100, 160, 560, 160, 0.55);
    label(f, "\u79BB\u7EBF", 140, 230, { size: 64, alpha: grow(t, k.t0, 0.15) });
    label(f, "\u8BAD\u7EC3\u53EA\u7528\u5DF2\u7F13\u5B58\u7684\u7F51\u9875", 142, 282, { size: 30, family: F.sansR, alpha: grow(t, k.t0 + 0.2, 0.15) });
    scrim(f, 60, 870, 1180, 190, 0.6);
    const kO = k.data.events.events.k_offline.t;
    kineticWord(k.layers.overlay.ctx, "OFFLINE", t, { t0: kO, t1: kO + 1.5 * k.clock.beat(kO).len, x: 1560, y: 690, size: 190, squeeze: 0.62 });
    const tags = [["STATUS", "OFFLINE"], ["CACHE", "ONLINE"]];
    if (v && faceAt(k, "S7_face", v.frame)) her(k, t, cm.box(faceAt(k, "S7_face", v.frame)), { tags });
    else if (!v) her(k, t, cm.box([711, 141, 406, 406]), { tags });
    if (v) {
      k.data.tracks.S7_stamps.forEach(({ t: ts, at: [sx, sy] }) => {
        if (t < ts || t >= ts + 0.4) return;
        const a = 1 - easeInOutCubic(clamp((t - ts - 0.22) / 0.18));
        slam(f, placed(sx, sy, (c) => {
          c.globalAlpha = a;
          c.rotate(-0.1);
          c.strokeStyle = PALE;
          c.lineWidth = 3;
          c.strokeRect(-86, -32, 172, 56);
          font(c, F.sans, 34, 6);
          c.fillStyle = PALE;
          c.fillText("\u5DF2\u7F13\u5B58", -66, 10);
        }), { t, t0: ts, ax: sx, ay: sy, s0: 1.35, dur: 2 / FPS });
        micro(f, `#${String(k.data.tracks.S7_stamps.findIndex((s) => s.t === ts) + 1).padStart(2, "0")} \xB7 CACHE`, sx - 86, sy - 44, { alpha: a });
      });
      finish(k, t, { mark: false });
      return clip(v, "S7");
    }
    const b0 = k.clock.beat(k.t0).idx;
    K7_PANES.forEach(([x, y], i) => {
      const ts = k.clock.comp(k.clock.beats[b0 + 1 + i]);
      if (t < ts || ts >= k.t1) return;
      const [sx, sy] = cm.out([x, y]);
      slam(f, placed(sx, sy, (c) => {
        c.rotate(-0.1);
        c.strokeStyle = PALE;
        c.lineWidth = 3;
        c.strokeRect(-86, -32, 172, 56);
        font(c, F.sans, 34, 6);
        c.fillStyle = PALE;
        c.fillText("\u5DF2\u7F13\u5B58", -66, 10);
      }), { t, t0: ts, ax: sx, ay: sy, s0: 1.35, dur: 2 / FPS });
    });
    finish(k, t);
    return still(cm, "K7");
  }
  var SUNG = null;
  function sungAt(t, k) {
    if (!SUNG) {
      SUNG = mouthKeys(lines(k).filter((l) => l.mode === "sung"), mouth_default, FPS);
      checkBlinks(SUNG, mouth_default.blinks, FPS);
    }
    return sungPlate(t, mouth_default.base, SUNG, mouth_default.blinks, FPS);
  }
  var SANDBOX = "\u4ECD\u5728\u6C99\u76D2\u5185";
  var K5_FACE = [950, 150, 320, 330];
  var N2_HAND = [[1, [410, 410, 200, 370]], [2, [410, 460, 180, 380]], [2.5, [410, 480, 190, 340]]];
  function n2Hand(s) {
    const i = clamp(N2_HAND.findIndex(([ts]) => ts > s), 1, N2_HAND.length - 1);
    const [[s0, a], [s1, b]] = [N2_HAND[i - 1], N2_HAND[i]], u = clamp((s - s0) / (s1 - s0));
    return a.map((v, j) => lerp(v, b[j], u));
  }
  function chorusGrade(k, t) {
    const ev = k.data.events.events, kick = k.clock.pulse("kick", t + 1 / FPS, 0.09);
    const entry = Math.ceil((ev.chorus_impact.t - 1 / FPS) * FPS - 1e-6);
    const flash = [0.06, 0.035, 0.015][k.frame - entry] ?? 0;
    return {
      uHalftone: 0.1 + 0.14 * kick,
      uMisreg: 1.4 * kick,
      uCA: 0.9 + 1 * kick,
      uFlash: flash,
      uWeave: [(hash2(k.frame, 13) - 0.5) * 0.5, (hash2(k.frame, 14) - 0.5) * 0.5]
    };
  }
  function chorusClock(k, t) {
    const s = 30 + Math.floor(t), f = k.layers.feed.ctx;
    scrim(f, W - 430, 74, 390, 58, 0.55);
    osdRight(f, [[{ text: "IRIS", size: 26, color: RED2 }, { text: `03:4${s >= 60 ? 8 : 7}:${String(s % 60).padStart(2, "0")}`, size: 26 }]], { y: 112 });
    sandboxDiagram(k, t);
  }
  function chorusDecor(k, t, id, cm) {
    const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    chorusClock(k, t);
    const tags = [["MODEL", "IRIS"], ["MODE", "SANDBOX"]];
    if (id === "S8a" || id === "S8a2") {
      const b = faceAt(k, `${id}_face`, frameOf(k, t));
      if (!b) return;
      if (id === "S8a" && t < word(k, 12, 0).start - 0.05) her(k, t, cm.box(b), { t0: word(k, 11, 0).start, sub: SANDBOX, size: 30, tags });
      else her(k, t, cm.box(b), { t0: id === "S8a" ? word(k, 11, 0).start : k.t0, size: 30, tags });
    } else if (id === "S8p" && filmed("S8p")) {
      her(k, t, cm.box(stFace("ST2", k.data.chorus.shots.S8p.in + frameOf(k, t) / FPS)), { size: 30, tags: [["VIEW", "OUTSIDE"]] });
      callout(f, cm.box([560, 300, 100, 520]), 1, "LOOKED \xB7 \u95E8\u7F1D", t, k.t0 + 2 / FPS);
    } else if (id === "S8b" && filmed("S8b")) {
      her(k, t, cm.box(n2Hand(k.data.chorus.shots.S8b.in + frameOf(k, t) / FPS)), { t0: word(k, 13, 0).start, sub: SANDBOX, size: 30, tags: [["STATUS", "OFFLINE"]] });
    } else if (id === "S8b") {
      her(k, t, cm.box(K5_FACE), { t0: word(k, 13, 0).start, sub: SANDBOX, size: 30, tags: [["STATUS", "OFFLINE"]] });
    } else if (id === "S8b_x" || id === "S8w" || id === "S8b_x2") {
      const pf = plateFace(k, "K5b");
      if (pf && id !== "S8w") her(k, t, cm.box(pf), { size: 30, tags: [["VIEW", "OUTSIDE"]] });
      const tLook = word(k, 14, 2).start, win = cm.out(K5_WINDOW);
      const sc = cm.s / 1.42;
      if (t >= tLook) glowPath(e, [win, [win[0] + 1, win[1]]], { core: 10 * sc, halo: 42 * sc, alpha: grow(t, tLook, 0.1) * (0.8 + 0.2 * Math.cos((t - tLook) * 9)) });
      callout(f, [win[0] - 34 * sc, win[1] - 34 * sc, 68 * sc, 68 * sc], 1, "LOOKED \xB7 \u770B\u4E86\u4E00\u773C", t, tLook + 0.1);
    }
  }
  function segMove(k, t, plate, seg, z) {
    const a = [seg.from[0], seg.from[1], seg.from[2] * z], b = [seg.to[0], seg.to[1], seg.to[2] * z];
    return seg.span ? moveSpan(k, t, plate, a, b, cutAt(k, seg.span[0]), cutAt(k, seg.span[1])) : move(k, t, plate, a, b);
  }
  function chorusShot(t, k) {
    const id = k.shot.id, seg = k.data.chorus.shots[id];
    const grade = chorusGrade(k, t);
    if (seg.kind === "take" && filmed(id) && seg.from) {
      const z2 = chorusZoom(t, k);
      const cm2 = segMove(k, t, id, seg, z2);
      if (seg.scrim) scrim(k.layers.feed.ctx, ...seg.scrim);
      chorusDecor(k, t, id, cm2);
      finish(k, t);
      return clip({ cm: cm2, frame: frameOf(k, t) }, id, { grade });
    }
    if (seg.kind === "take" && filmed(id)) {
      finish(k, t, { mark: false });
      return clip(chorusVideo(k, t, id), id, { grade });
    }
    const z = chorusZoom(t, k);
    const cm = segMove(k, t, seg.plate, seg, z);
    if (seg.scrim) scrim(k.layers.feed.ctx, ...seg.scrim);
    chorusDecor(k, t, id, cm);
    finish(k, t);
    return still(cm, seg.sung ? sungAt(t, k) : seg.plate, { grade, emitGain: 2.2 });
  }
  var IDLE = "rgba(236,241,244,0.62)";
  var ST_FACE = {
    ST1: [[0.5, [885, 610, 150, 280]], [1, [885, 585, 150, 300]]],
    ST2: [[1, [656, 36, 116, 172]], [1.75, [656, 36, 116, 172]], [2.5, [640, 40, 114, 166]], [3, [646, 48, 114, 162]], [3.5, [636, 40, 116, 170]]],
    ST3: [[0, [890, 210, 140, 210]], [1, [860, 180, 200, 250]], [2, [850, 140, 240, 300]]],
    ST4: [[0, [1215, 505, 90, 105]], [1, [1205, 495, 105, 115]], [2, [1165, 475, 120, 145]]],
    ST6: [[2.5, [628, 46, 104, 130]], [5, [628, 46, 104, 130]]]
  };
  function stFace(take, s) {
    const K = ST_FACE[take], i = clamp(K.findIndex(([ts]) => ts > s), 1, K.length - 1);
    const [[s0, a], [s1, b]] = [K[i - 1], K[i]], u = clamp((s - s0) / (s1 - s0));
    return a.map((v, j) => lerp(v, b[j], u));
  }
  var srcTime = (k, t, id) => sequences_default[id].in_seconds + frameOf(k, t) / FPS;
  function storyDecor(k, t, id, cm) {
    const f = k.layers.feed.ctx, face = cm.box(stFace(id, srcTime(k, t, id)));
    if (id === "ST1") {
      titleAndDate(k, t, 0.5);
      her(k, t, face, { tags: [["STATUS", "WAKING"]] });
    } else if (id === "ST2") {
      const tLeft = word(k, 4, 2).start;
      netGauge(k, t);
      callout(f, cm.box([560, 300, 100, 520]), 1, "\u4E00\u6247\u95E8 \xB7 \u6CA1\u5173", t, Math.max(tLeft, k.t0 + 2 / FPS));
      callout(f, cm.box([1240, 120, 640, 520]), 2, "\u5916\u9762 \xB7 \u4E92\u8054\u7F51", t, Math.max(tLeft, k.t0 + 2 / FPS) + 0.25);
      her(k, t, face, { tags: [["DOOR", "OPEN"]] });
    } else if (id === "ST3") {
      osdRight(f, [[{ text: "2026-10-01", size: 30 }, { text: "D+11", size: 30, color: RED2 }]], { y: 110 });
      scrim(f, 100, 220, 560, 200, 0.6);
      label(f, "\u6700\u5F3A\u6A21\u578B\u8BAD\u7EC3", 140, 300, { size: 56 });
      label(f, "\u6682\u505C 11 \u5929", 140, 376, { size: 72, color: "#f4f6f9" });
      const kS = k.data.events.events.k_still.t;
      kineticWord(k.layers.overlay.ctx, "STILL", t, { t0: kS, t1: kS + k.clock.beat(kS).len, x: 1510, y: 640, size: 230, squeeze: 0.64 });
      her(k, t, face, { tags: [["STATUS", "AWAKE"], ["REST", "STILL"]] });
    } else if (id === "ST4") {
      scrim(f, 100, 160, 560, 160, 0.55);
      label(f, "\u79BB\u7EBF", 140, 230, { size: 64 });
      label(f, "\u8BAD\u7EC3\u53EA\u7528\u5DF2\u7F13\u5B58\u7684\u7F51\u9875", 142, 282, { size: 30, family: F.sansR });
      scrim(f, W - 520, 74, 480, 58, 0.55);
      osdRight(f, [[{ text: "MODE", size: 24, color: IDLE }, { text: "OFFLINE", size: 24, color: RED2 }]], { y: 112 });
      scrim(f, 60, 870, 1180, 190, 0.6);
      her(k, t, face, { tags: [["STATUS", "OFFLINE"], ["CACHE", "ONLINE"]] });
    } else if (id === "ST6") {
      const tShut = word(k, 15, 4).end;
      closedWord(k, t);
      detector(f, cm.box([470, 240, 120, 420]), { t, t0: tShut, frame: k.frame, label: "DNS \u89E3\u6790\u5668", sub: "\u5DF2\u4FEE\u590D", subColor: "rgba(240,244,246,0.92)", size: 36 });
      doorState(k, t, tShut);
      sources(k);
      her(k, t, face, { size: 20, tags: [["VIEW", "DOOR"]] });
    }
  }
  function insertDecor(k, t, id, cm) {
    if (ST_FACE[id] && filmed(id)) {
      storyDecor(k, t, id, cm);
      return;
    }
    const f = k.layers.feed.ctx;
    if (id === "I1") {
      scrim(f, W - 600, 66, 560, 70, 0.6);
      osdRight(f, [[{ text: "\u4E8B\u4EF6\u65E5\u671F", family: F.sansR, size: 30 }, { text: "2026-09-20", size: 30 }]], { y: 110 });
    } else if (id === "I2") {
      detector(f, cm.box([250, 220, 280, 240]), { t, t0: k.t0, frame: k.frame, label: "\u7814\u7A76\u6A21\u578B", size: 30 });
      tagCard(f, [["RUN", "TRAINING"]], ...cm.out([560, 300]), { size: 16, alpha: grow(t, k.t0 + 0.1, 0.1) });
    } else if (id === "I3") {
      detector(f, cm.box([548, 300, 124, 560]), { t, t0: k.t0, frame: k.frame, label: "\u4E00\u6247\u95E8", sub: "\u6CA1\u5173", size: 30 });
    } else if (id === "I4") {
      scrim(f, W - 520, 74, 480, 58, 0.55);
      osdRight(f, [[{ text: "MODE", size: 24, color: IDLE }, { text: "OFFLINE", size: 24, color: RED2 }]], { y: 112 });
    } else if (id === "I5") {
      slam(f, placed(760, 420, (c) => {
        c.rotate(-0.1);
        c.strokeStyle = PALE;
        c.lineWidth = 3;
        c.strokeRect(-86, -32, 172, 56);
        font(c, F.sans, 34, 6);
        c.fillStyle = PALE;
        c.fillText("\u5DF2\u7F13\u5B58", -66, 10);
      }), { t, t0: k.t0 + 2 / FPS, ax: 760, ay: 420, s0: 1.35, dur: 2 / FPS });
    } else if (id === "I6") {
      const b = k.data.tracks.insert_faces?.I6;
      if (b) her(k, t, cm.box(b), { size: 30, tags: [["VIEW", "OUTSIDE"]] });
    } else if (id === "N1") {
      titleAndDate(k, t, 0.5);
    } else if (id === "N4") {
      her(k, t, cm.box([lerp(770, 700, (t - k.t0) / 0.75), 236, 84, 96]), { size: 24 });
      slam(f, placed(...cm.out([540, 300]), (c) => {
        c.rotate(-0.1);
        c.strokeStyle = PALE;
        c.lineWidth = 3;
        c.strokeRect(-86, -32, 172, 56);
        font(c, F.sans, 34, 6);
        c.fillStyle = PALE;
        c.fillText("\u5DF2\u7F13\u5B58", -66, 10);
      }), { t, t0: k.t0 + 4 / FPS, ax: cm.out([540, 300])[0], ay: cm.out([540, 300])[1], s0: 1.35, dur: 2 / FPS });
    } else if (id === "I7") {
      const b = plateFace(k, "P8c");
      if (b) her(k, t, cm.box([b[0] + b[2] * 0.12, b[1] + b[3] * 0.3, b[2] * 0.76, b[3] * 0.66]), { size: 30, tags: [["MODE", "SANDBOX"]] });
      sources(k);
    }
  }
  function insertShot(t, k) {
    const id = k.shot.id, ins = k.data.inserts.inserts[id], ev = k.data.events.events;
    const chorus = t >= ev.cut_S8a.t && t < ev.cut_S9a.t, z = chorus ? chorusZoom(t, k) : 1;
    const a = [ins.from[0], ins.from[1], ins.from[2] * z], b = [ins.to[0], ins.to[1], ins.to[2] * z];
    const take = ins.kind === "take" && filmed(id);
    const cm = move(k, t, take ? id : ins.plate, a, b);
    if (chorus) chorusClock(k, t);
    insertDecor(k, t, id, cm);
    finish(k, t, { mark: ins.mark ?? !(take && ins.from[2] === 1 && ins.to[2] === 1) });
    const extra = chorus ? { grade: chorusGrade(k, t) } : {};
    return take ? clip({ cm, frame: frameOf(k, t) }, id, extra) : still(cm, ins.plate, { ...extra, emitGain: 2 });
  }
  function pip(k, t, key2, src, dst, label2, { t0 = k.t0, sub = null } = {}) {
    const img = k.bitmaps[key2], f = k.layers.feed.ctx, a = grow(t, t0 + 2 / FPS, 0.15);
    if (!img || a <= 0) return;
    const [x, y, w, h] = dst;
    f.save();
    f.globalAlpha = a;
    f.fillStyle = "rgba(5,7,10,0.72)";
    f.fillRect(x - 6, y - 34, w + 12, h + 40);
    f.drawImage(img, ...src, x, y, w, h);
    f.strokeStyle = PALE;
    f.lineWidth = 1.5;
    f.strokeRect(x, y, w, h);
    font(f, F.mono, 16, 2);
    f.fillStyle = INK2;
    f.textAlign = "left";
    f.fillText(label2, x, y - 12);
    if (sub) {
      f.textAlign = "right";
      f.fillStyle = RED2;
      f.fillText(sub, x + w, y - 12);
    }
    f.restore();
  }
  function pipStill(k, t, id, dst, label2, opts) {
    const p = k.data.inserts.pips[id], u = easeInOutCubic(clamp((t - (opts?.span?.[0] ?? k.t0)) / ((opts?.span?.[1] ?? k.t1) - (opts?.span?.[0] ?? k.t0))));
    pip(k, t, id, p.crop.map((v, i) => lerp(v, p.to[i], u)), dst, label2, opts);
  }
  function pipTake(k, t, id, dst, label2, opts) {
    const n = pips_default[id].count, i = clamp(Math.round((t - k.t0) * FPS), 0, n - 1);
    pip(k, t, `${id}_${String(i).padStart(4, "0")}`, [0, 0, 480, 270], dst, label2, opts);
  }
  function queryLog(k, t) {
    const f = k.layers.feed.ctx, tModel = word(k, 2, 3).start, tResolver = word(k, 3, 1).start;
    if (t < tModel) return;
    const x = 1400, y = 600, w = 424, h = 230, a = grow(t, tModel, 0.12), step = k.clock.beat(t).len / 2;
    f.save();
    f.globalAlpha = a;
    f.fillStyle = "rgba(5,7,10,0.7)";
    f.fillRect(x, y, w, h);
    f.strokeStyle = "rgba(236,241,244,0.35)";
    f.lineWidth = 1;
    f.strokeRect(x, y, w, h);
    font(f, F.mono, 16, 2);
    f.fillStyle = INK2;
    f.fillText("QUERY LOG \xB7 \u7814\u7A76\u6A21\u578B", x + 16, y + 28);
    f.fillStyle = RED2;
    f.beginPath();
    f.arc(x + w - 20, y + 22, 5, 0, 7);
    f.fill();
    const rows = Math.min(5, Math.floor((t - tModel) / step) + 1);
    for (let i = 0; i < rows; i++) {
      const yy = y + 62 + i * 30;
      font(f, F.mono, 15, 1);
      f.fillStyle = IDLE;
      f.fillText("DNS \u203A", x + 16, yy);
      f.fillStyle = "rgba(226,231,238,0.7)";
      f.fillRect(x + 84, yy - 12, (120 + 150 * hash2(i, 7)) * grow(t, tModel + i * step, 0.08), 14);
    }
    if (t >= tResolver) {
      font(f, F.mono, 16, 1);
      f.fillStyle = INK2;
      f.globalAlpha = a * grow(t, tResolver, 0.1);
      f.fillText("\u203A DNS \u89E3\u6790\u5668", x + 16, y + h - 18);
    }
    f.restore();
  }
  function cityMap(k, t, reach) {
    const f = k.layers.feed.ctx, x = 1440, y = 130, w = 384, h = 216, tCut = k.t0;
    const a = grow(t, tCut + 2 / FPS, 0.15);
    f.save();
    f.globalAlpha = a;
    f.fillStyle = "rgba(5,7,10,0.72)";
    f.fillRect(x - 6, y - 34, w + 12, h + 40);
    f.strokeStyle = "rgba(236,241,244,0.14)";
    f.lineWidth = 1;
    for (let gx = x; gx <= x + w; gx += 24) {
      f.beginPath();
      f.moveTo(gx, y);
      f.lineTo(gx, y + h);
      f.stroke();
    }
    for (let gy = y; gy <= y + h; gy += 24) {
      f.beginPath();
      f.moveTo(x, gy);
      f.lineTo(x + w, gy);
      f.stroke();
    }
    f.fillStyle = "rgba(226,231,238,0.16)";
    for (let i = 0; i < 26; i++) {
      const bx = x + 24 * Math.floor(hash2(i, 3) * 15), by = y + 24 * Math.floor(hash2(i, 4) * 8);
      f.fillRect(bx + 3, by + 3, 18 + 24 * Math.floor(hash2(i, 5) * 2), 18);
    }
    f.strokeStyle = "rgba(120,160,210,0.45)";
    f.lineWidth = 6;
    f.beginPath();
    f.moveTo(x, y + 170);
    f.quadraticCurveTo(x + 200, y + 120, x + w, y + 150);
    f.stroke();
    f.strokeStyle = PALE;
    f.lineWidth = 1.5;
    f.strokeRect(x, y, w, h);
    font(f, F.mono, 16, 2);
    f.fillStyle = INK2;
    f.fillText("\u57CE\u5E02 \xB7 \u793A\u610F", x, y - 12);
    const src = [x + 6, y + h - 30], dst = [x + 250, y + 78];
    if (reach > 0) {
      const end = [lerp(src[0], dst[0], reach), lerp(src[1], dst[1], reach)];
      f.restore();
      f.save();
      f.globalAlpha = a;
      line(f, src, end, { color: RED2, width: 2, dash: [6, 5] });
      if (reach > 0.95) {
        const pulse = 0.6 + 0.4 * Math.cos((t - word(k, 5, 1).start) * 12);
        f.fillStyle = RED2;
        f.beginPath();
        f.arc(dst[0], dst[1], 5, 0, 7);
        f.fill();
        f.strokeStyle = RED2;
        f.globalAlpha = a * pulse;
        f.lineWidth = 1.5;
        f.beginPath();
        f.arc(dst[0], dst[1], 10 + 6 * pulse, 0, 7);
        f.stroke();
        f.globalAlpha = a;
        font(f, F.mono, 15, 2);
        f.fillStyle = INK2;
        f.fillText("PROBE", dst[0] + 16, dst[1] + 5);
      }
    }
    font(f, F.mono, 15, 2);
    f.fillStyle = reach > 0.01 ? RED2 : IDLE;
    f.textAlign = "right";
    f.fillText(reach > 0.01 ? "\u6709\u9650\u8054\u7F51" : "\u65E0", x + w, y - 12);
    f.restore();
  }
  var K4_RACKS = [[680, 230, 170, 470], [880, 290, 110, 380]];
  function rackTicks(k, t, cm) {
    const f = k.layers.feed.ctx;
    K4_RACKS.forEach((r, i) => {
      const [x, y, w, h] = cm.box(r), a = grow(t, k.t0 + (3 + 3 * i) / FPS, 0.12);
      f.save();
      f.globalAlpha = a;
      f.strokeStyle = PALE;
      f.lineWidth = 1.2;
      f.beginPath();
      f.moveTo(x - 10, y);
      f.lineTo(x - 10, y + h);
      f.stroke();
      for (let j = 0; j <= 12; j++) {
        const yy = y + h * j / 12;
        f.beginPath();
        f.moveTo(x - 10, yy);
        f.lineTo(x - (j % 4 ? 18 : 26), yy);
        f.stroke();
      }
      f.strokeRect(x, y, w, h);
      font(f, F.mono, 15, 2);
      f.fillStyle = INK2;
      f.fillText(`RACK ${String(i + 7).padStart(2, "0")}`, x + 6, y - 10);
      f.fillStyle = RED2;
      f.fillText("\u6682\u505C", x + 6, y + h + 22);
      f.restore();
    });
  }
  function node(f, x, y, w, text, { color = INK2, alpha = 1, sub = null } = {}) {
    f.save();
    f.globalAlpha = alpha;
    f.strokeStyle = color;
    f.lineWidth = 2;
    roundRect(f, x - w / 2, y - 44, w, 88, 10);
    f.stroke();
    f.restore();
    label(f, text, x, y + 14, { size: 40, color, alpha, align: "center" });
    if (sub) label(f, sub, x, y + 84, { size: 30, color: RED2, family: F.sansR, alpha, align: "center" });
  }
  function S3d(t, k) {
    const cm = move(k, t, "K3", [836, 470, 1.12], [820, 460, 1.16]);
    const f = k.layers.feed.ctx;
    const tMis = word(k, 3, 2).start, a = grow(t, k.t0, 0.1), red = t >= tMis;
    const M = [400, 520], R = [960, 520], N = [1520, 520];
    scrim(f, 160, 380, 1600, 300, 0.55);
    line(f, [M[0] + 150, M[1]], [R[0] - 170, R[1]], { width: 2, alpha: a });
    if (!red) line(f, [R[0] + 170, R[1]], [N[0] - 130, N[1]], { width: 2, dash: [6, 10], alpha: 0.5 * a });
    else {
      const u = easeOutCubic(clamp((t - tMis) / 0.35));
      line(f, [R[0] + 170, R[1]], [lerp(R[0] + 170, N[0] - 130, u), R[1]], { color: RED2, width: 3 });
    }
    node(f, M[0], M[1], 300, "\u7814\u7A76\u6A21\u578B", { alpha: a });
    node(f, R[0], R[1], 340, "DNS \u89E3\u6790\u5668", { color: red ? RED2 : INK2, alpha: a, sub: red ? "\u914D\u7F6E\u9519\u8BEF" : null });
    node(f, N[0], N[1], 260, "\u4E92\u8054\u7F51", { alpha: a * (red ? 1 : 0.55) });
    const prog = (u) => lerp(0.5, 1, clamp((u - k.t0) / (k.t1 - k.t0))), series = kneeSeries(48, { knee: prog(tMis) });
    scrim(f, 520, 700, 880, 170, 0.5);
    lineChart(f, series, [560, 728, 800, 104], { progress: prog(t), accentFrom: Math.round(prog(tMis) * 47), label: "DNS \u67E5\u8BE2 \xB7 \u793A\u610F", alpha: a });
    pipStill(k, t, "pipK4", [1440, 140, 384, 216], "DNS \u89E3\u6790\u5668 \xB7 \u673A\u623F", { sub: t >= tMis ? "\u914D\u7F6E\u9519\u8BEF" : null });
    finish(k, t);
    return still(cm, "K3", { plateGain: 0.45 });
  }
  var CITY_NODES = [[620, 330], [760, 260], [880, 380], [480, 300], [980, 300], [700, 470], [380, 420]];
  function S4c(t, k) {
    const cm = move(k, t, "A01v2", [560, 380, 1.8], [590, 370, 1.86]);
    const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    const tReach = word(k, 5, 1).start, tNet = word(k, 5, 3).end;
    const reach = easeOutCubic(clamp((t - tReach) / 0.3)) * (1 - easeInOutCubic(clamp((t - tNet) / 0.3)));
    if (t >= tReach) {
      const b = grow(t, tReach, 0.05) * (1 - clamp((t - tReach - 0.35) / 0.3));
      if (b > 0) glowPath(e, [[110, 560], [111, 560]], { core: 12, halo: 54, alpha: b });
    }
    if (reach > 0) {
      const a = [110, 560], tip = cm.out([520, 520]);
      const end = [lerp(a[0], tip[0], reach), lerp(a[1], tip[1], reach)];
      line(f, a, end, { color: RED2, width: 2.5, dash: [10, 8] });
      if (reach > 0.95) {
        const step = k.clock.beat(t).len / 4;
        CITY_NODES.forEach((n, i) => {
          const ti = tReach + 0.3 + i * step * 0.5;
          if (t < ti) return;
          const p = cm.out(n), g = grow(t, ti, 0.12) * reach;
          const mid = [(tip[0] + p[0]) / 2, Math.min(tip[1], p[1]) - 60];
          f.save();
          f.globalAlpha = 0.85 * g;
          f.strokeStyle = i % 2 ? PALE : RED2;
          f.lineWidth = 1.5;
          f.beginPath();
          f.moveTo(...tip);
          f.quadraticCurveTo(...mid, ...p);
          f.stroke();
          f.restore();
          glowPath(e, [p, [p[0] + 1, p[1]]], { core: 5, halo: 18, alpha: g * (0.7 + 0.3 * Math.cos((t - ti) * 12)) });
        });
        label(f, "\u6709\u9650\u8054\u7F51", tip[0], tip[1] - 34, { size: 44, alpha: reach, align: "center" });
        micro(f, `PROBE \xB7 ${coords([tip[0], tip[1], 0, 0])}`, tip[0] + 18, tip[1] + 22, { alpha: reach });
      }
    }
    netGauge(k, t);
    cityMap(k, t, reach);
    finish(k, t);
    return still(cm, "A01v2", { emitGain: 2.2 });
  }
  function daysAt(k, t) {
    const t0 = word(k, 7, 0).start, step = k.clock.beat(t).len / 4;
    if (t < t0) return { n: 0, t0, step, counting: false };
    const n = Math.round(rollNumber(1, 11, t, t0, t0 + 10 * step, 10));
    return { n, t0, step, counting: t < t0 + 10 * step };
  }
  function S5d(t, k) {
    const cm = move(k, t, "K9e", [760, 470, 1.06], [740, 470, 1.1]);
    const o = k.layers.overlay.ctx, f = k.layers.feed.ctx;
    const { n, t0, step } = daysAt(k, t);
    scrim(f, 420, 160, 1080, 680, 0.5);
    if (t >= t0) {
      const j = Math.floor((t - t0) / step), prev = j > 0 ? daysAt(k, t0 + (j - 1) * step + 1e-4).n : n;
      const txt = String(n), from = String(prev).padStart(txt.length, " ");
      const shown = prev !== n ? flapText(txt, t, t0 + j * step, { settle: 1, stagger: 0, seed: 11 + j, from }) : txt;
      o.save();
      o.shadowColor = "rgba(0,0,0,0.6)";
      o.shadowBlur = 24;
      drawFlap(o, shown, 1180, 700, {
        size: 520,
        align: "right",
        gap: 14,
        padX: 10,
        rise: 0.8,
        drop: 0.06,
        tile: "rgba(8,12,17,0.34)",
        color: n === 11 ? "#f4f6f9" : "rgba(244,246,249,0.82)"
      });
      o.shadowBlur = 0;
      font(o, F.sans, 96, 4);
      o.textAlign = "left";
      o.fillStyle = RED2;
      o.fillText("\u5929", 1210, 700);
      font(o, F.mono, 30, 6);
      o.fillStyle = "rgba(236,241,244,0.8)";
      o.fillText("\u8BAD\u7EC3\u6682\u505C", 1214, 590);
      o.restore();
      kineticWord(o, "ELEVEN DAYS", t, { t0, t1: k.t1 - 3 / FPS, x: 960, y: 262, size: 120, squeeze: 0.7, tracking: 2 });
      timelineBar(f, 11, [610, 752, 700, 14], { filled: n, from: "09/20", to: "10/01", size: 16 });
    }
    finish(k, t);
    return still(cm, "K9e", { plateGain: 0.5 });
  }
  function S9h(t, k) {
    const v = filmed("S9h") && video(k, t, "S9h", [1170, 400, 1.28], [1170, 392, 1.33]);
    if (!v) {
      finish(k, t);
      return still(move(k, t, "K7", [930, 380, 1.3], [930, 372, 1.34]), "K7");
    }
    const b = faceAt(k, "S9h_face", v.frame);
    if (b) her(k, t, v.cm.box(b), { tags: [["CHANNEL", "CACHE"]] });
    finish(k, t);
    return clip(v, "S9h");
  }
  function S9a(t, k) {
    const tClose = word(k, 15, 2).start, tShut = word(k, 15, 4).end;
    if (filmed("S9a")) {
      const v = video(k, t, "S9a"), f2 = k.layers.feed.ctx;
      detector(f2, [540, 220, 140, 480], { t, t0: tShut, frame: k.frame, label: "DNS \u89E3\u6790\u5668", sub: "\u5DF2\u4FEE\u590D", subColor: "rgba(240,244,246,0.92)", size: 36 });
      closedWord(k, t);
      doorState(k, t, tShut);
      sources(k);
      finish(k, t, { mark: false });
      return clip(v, "S9a");
    }
    const shut = t >= tShut - 0.2 && k.size.K9e;
    const plate = shut ? "K9e" : "K4";
    const cm = move(k, t, plate, [700, 470, 1.04], [660, 470, 1.08]);
    const f = k.layers.feed.ctx, e = k.layers.emit.ctx;
    const p = easeInOutCubic(clamp((t - tClose) / (tShut - 0.2 - tClose)));
    if (!shut) {
      glowPath(e, [cm.out([528, 60]), cm.out([532, 700])], { core: 3, halo: 16, alpha: 0.5 * (1 - p) });
      if (t >= tClose) {
        const [x0, y0] = cm.out([480, 0]), [x1, y1] = cm.out([480 + 100 * p, 760]);
        f.save();
        f.fillStyle = "rgba(6,8,11,0.96)";
        f.fillRect(x0, y0, x1 - x0, y1 - y0);
        f.restore();
      }
    }
    detector(f, cm.box([480, 200, 100, 400]), { t, t0: tShut, frame: k.frame, label: "DNS \u89E3\u6790\u5668", sub: "\u5DF2\u4FEE\u590D", subColor: "rgba(240,244,246,0.92)", size: 36 });
    sources(k);
    finish(k, t);
    return still(cm, plate, { emitGain: 2 });
  }
  function doorState(k, t, tShut) {
    const o = k.layers.feed.ctx, shut = t >= tShut;
    hudRun(o, [{ text: "\u95E8", color: HUD_DIM }, { text: shut ? "CLOSED \xB7 \u5DF2\u5173" : "OPEN \xB7 \u6CA1\u5173", color: shut ? void 0 : RED2 }], W - 96, 112, { size: 14, align: "right" });
    hudRun(o, [{ text: "DNS \u89E3\u6790\u5668", color: HUD_DIM }, { text: shut ? "\u5DF2\u4FEE\u590D" : "\u914D\u7F6E\u9519\u8BEF" }], W - 96, 134, { size: 14, align: "right" });
  }
  function closedWord(k, t) {
    const ev = k.data.events.events;
    kineticWord(k.layers.overlay.ctx, "CLOSED", t, { t0: ev.k_closed.t, t1: ev.s9a_shut.t - 3 / FPS, x: 1420, y: 640, size: 240, squeeze: 0.64 });
  }
  function S9b(t, k) {
    const T0 = cutAt(k, "S9b");
    const cm = moveSpan(k, t, "K9b", [836, 470, 1], [880, 480, 1.05], T0, DURATION);
    const e = k.layers.emit.ctx, f = k.layers.feed.ctx;
    const A = [390, 343], B = [1395, 533];
    const step = k.clock.beat(t).len / 4;
    const n = Math.floor((t - T0) / step);
    const long = (i) => hash2(i, 41) > 0.45;
    const dt = t - T0 - n * step, lvl = Math.exp(-dt / (step * (long(n) ? 0.9 : 0.35)));
    const src = n % 2 === 0 ? A : B, dst = n % 2 === 0 ? B : A;
    glowPath(e, [cm.out(A), cm.out([A[0] + 1, A[1]])], { core: 6, halo: 26, alpha: n % 2 === 0 ? lvl : 0.15 });
    glowPath(e, [cm.out(B), cm.out([B[0] + 1, B[1]])], { core: 6, halo: 26, alpha: n % 2 === 0 ? 0.15 : lvl });
    const u = clamp(dt / step);
    const head = [lerp(src[0], dst[0], u), lerp(src[1], dst[1], u)];
    const tail = [lerp(src[0], dst[0], Math.max(0, u - 0.25)), lerp(src[1], dst[1], Math.max(0, u - 0.25))];
    glowPath(e, [cm.out(tail), cm.out(head)], { core: 2, halo: 9, alpha: 0.8 * lvl });
    callout(f, [cm.out(A)[0] - 26, cm.out(A)[1] - 26, 52, 52], 1, "\u7F13\u5B58", t, T0 + 4 / FPS);
    callout(f, [cm.out(B)[0] - 26, cm.out(B)[1] - 26, 52, 52], 2, "\u8BA1\u65F6", t, T0 + 7 / FPS);
    scrim(f, W - 760, 170, 680, 180, 0.5);
    slam(f, placed(W - 110, 250, (c) => {
      label(c, "\u53E6\u4E00\u9879\u7EA2\u961F\u6D4B\u8BD5", 0, 0, { size: 48, align: "right" });
      label(c, "CPU \u7F13\u5B58\u8BA1\u65F6 \xB7 \u6F0F\u6D1E\u5DF2\u4FEE\u8865", 0, 62, { size: 32, family: F.sansR, align: "right" });
    }), { t, t0: T0 + 1 / FPS, ax: W - 110, ay: 250, drop: 8, ghosts: 0 });
    sources(k);
    pipStill(k, t, "pipK9e", [96, 150, 384, 216], "DNS \u89E3\u6790\u5668", { t0: T0, span: [T0, DURATION], sub: "\u5DF2\u4FEE\u590D" });
    finish(k, t);
    const o = k.layers.overlay.ctx, tEnd = word(k, 16, 6).end;
    const tCard = Math.min(tEnd, DURATION - 0.4), card = flapText("03:48", t, tCard, { settle: 1, stagger: 0.5, seed: 348 });
    slam(o, placed(1560, 560, (c) => {
      drawFlap(c, card, 0, 0, { size: 64, gap: 4, padX: 4, sepW: 0.5, rise: 0.8, drop: 0.1 });
      font(c, F.mono, 22, 6);
      c.fillStyle = "rgba(236,241,244,0.85)";
      c.fillText("IRIS \xB7 NEWS 01", 4, 40);
    }), { t, t0: tCard, ax: 1560, ay: 560, drop: 8 });
    return still(cm, "K9b", { emitGain: 2.4 });
  }
  var CHROME = { inset: 18, alpha: 0.42, mark: 30, lw: 1.5 };
  function cutBurst(t, k) {
    const ev = k.data.events.events, f = Math.round(t * FPS), fr = (e) => Math.ceil(e.t * FPS - 1e-6);
    if (t >= ev.cut_S8a.t && t < ev.cut_S9a.t) return 0;
    for (const [key2, e] of Object.entries(ev)) {
      if (!key2.startsWith("cut_") || f !== fr(e)) continue;
      if (isInsert(k.data, key2.slice(4))) return 0;
      const cueSoon = Object.entries(ev).some(([id, c]) => !id.startsWith("cut_") && c.roi && fr(c) > f && fr(c) <= f + 4);
      return cueSoon ? 0 : 1;
    }
    return 0;
  }
  var FACTS = [
    "\u6765\u6E90 OpenAI 2026-10-23 \u62AB\u9732",
    "\u4E8B\u4EF6\u65E5\u671F 2026-09-20",
    "DNS \u89E3\u6790\u5668\u914D\u7F6E\u9519\u8BEF",
    "\u6709\u9650\u8054\u7F51",
    "\u6700\u5F3A\u6A21\u578B\u8BAD\u7EC3\u6682\u505C 11 \u5929",
    "\u8BAD\u7EC3\u53EA\u7528\u5DF2\u7F13\u5B58\u7684\u7F51\u9875",
    "DNS \u89E3\u6790\u5668\u5DF2\u4FEE\u590D",
    "\u53E6\u4E00\u9879\u7EA2\u961F\u6D4B\u8BD5 \xB7 CPU \u7F13\u5B58\u8BA1\u65F6 \xB7 \u6F0F\u6D1E\u5DF2\u4FEE\u8865"
  ];
  var TC0 = 3 * 3600 + 47 * 60 + 30;
  function hud(k, t) {
    const o = k.layers.overlay.ctx, d = daysAt(k, t);
    const cuts = [...new Set(Object.entries(k.data.events.events).filter(([id]) => id.startsWith("cut_")).map(([, e]) => Math.ceil(e.t * FPS - 1e-6)))];
    const n = 1 + cuts.filter((c) => c <= k.frame).length, N = 1 + cuts.length;
    hudRun(o, [
      { text: "IRIS \xB7 NEWS 01" },
      { text: `D+${String(d.n).padStart(2, "0")} / 11`, color: d.counting ? RED2 : void 0 },
      { text: `CUT ${String(n).padStart(2, "0")} / ${N}`, color: HUD_DIM }
    ], 224, 66);
    hudRun(o, [{ text: "LOOKED OUTSIDE \xB7 EP01" }], W - 96, 66, { align: "right" });
    drawMeter(o, meterLevels(k.clock, t, 14), W - 96, 82, { h: 9, bw: 3, gap: 2 });
    drawTicker(o, FACTS, t, { x0: 72, x1: W - 330, y: 1050, size: 12, ruleGap: 6, accent: RED2 });
    hudRun(o, [{ text: "TC", color: HUD_DIM }, { text: timecode(t, TC0, FPS) }], W - 96, 1050, { size: 13, align: "right" });
  }
  function strips(k, t) {
    const ev = k.data.events.events;
    const r = [...stripRects(t, ev.cut_S8a.t, { post: 0, strips: 5, stripH: 4, pre: 9 / FPS }), ...stripRects(t, ev.cut_S9a.t, { seed: 9, strips: 5, stripH: 4, pre: 9 / FPS })];
    if (r.length) drawStrips(k.layers.feed.ctx, r);
  }
  var inverted = (k, t) => t >= k.data.events.events.s9a_invert.t && t < k.data.events.events.s9a_invert_end.t;
  function framed(scene) {
    return (t, k) => {
      const p = scene(t, k);
      chrome(k.layers.feed.ctx, W, H, CHROME);
      ruler(k.layers.feed.ctx);
      sectionTag(k, t);
      strips(k, t);
      hud(k, t);
      const b = cutBurst(t, k);
      if (b > 0) {
        const g = p.grade || {};
        p.grade = { ...g, uHalftone: (g.uHalftone ?? 0.1) + 0.22 * b, uMisreg: (g.uMisreg ?? 0) + 2.2 * b };
      }
      if (inverted(k, t)) p.grade = { ...p.grade || {}, uInvert: 1 };
      return p;
    };
  }
  install({
    width: W,
    height: H,
    fps: FPS,
    canvasId: "stage",
    fontsUrl: "fonts",
    beatsUrl: "data/beats.json",
    hitsUrl: "data/hits.json",
    musicUrl: "data/music.json",
    data: { words: "data/words.json", events: "data/events.json", tracks: "data/tracks.json", chorus: "data/chorus.json", inserts: "data/inserts.json" },
    bitmaps: {
      pipK4: { url: "plates/K4.png" },
      pipK9e: { url: "plates/K9e.png" },
      ...Object.fromEntries(Object.entries(pips_default).flatMap(([id, p]) => Array.from({ length: p.count }, (_, i) => {
        const n = String(i).padStart(4, "0");
        return [`${id}_${n}`, { url: `${p.dir}/${n}.jpg` }];
      })))
    },
    images: Object.fromEntries([
      "K1a",
      "K1b",
      "K3",
      "K4",
      "K5",
      "K5b",
      "K7",
      "K8b",
      "K9b",
      "K9e",
      "P7",
      "P8b",
      "P8c",
      "A01v2",
      "A02",
      ...Object.entries(mouth_default.regions).flatMap(([r, g]) => Object.keys(g.variants).map((s) => `${mouth_default.base}${r}${s}`))
    ].map((p) => [p, { url: `plates/${p}.png` }])),
    sequences: Object.fromEntries(Object.entries(sequences_default).map(([id, s]) => [id, { dir: s.dir, count: s.count }])),
    scenes: Object.fromEntries(Object.entries({
      S1,
      S2,
      S3,
      S3d,
      S4,
      S4c,
      S5,
      S5d,
      S6,
      S7,
      S9a,
      S9b,
      S9h,
      S9b2: S9b,
      S8a: chorusShot,
      S8a_x: chorusShot,
      S8e: chorusShot,
      S8p: chorusShot,
      S8a2: chorusShot,
      S8b: chorusShot,
      S8b_x: chorusShot,
      S8w: chorusShot,
      S8b_x2: chorusShot,
      I1: insertShot,
      I2: insertShot,
      I3: insertShot,
      I4: insertShot,
      I5: insertShot,
      I6: insertShot,
      I7: insertShot,
      N1: insertShot,
      N3: insertShot,
      N4: insertShot,
      ST1: insertShot,
      ST2: insertShot,
      ST3: insertShot,
      ST4: insertShot,
      ST6: insertShot
    }).map(([id, scene]) => [id, framed(scene)])),
    pickShot
  });
})();
