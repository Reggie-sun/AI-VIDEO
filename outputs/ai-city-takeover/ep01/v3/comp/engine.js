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
  var easeInOutSine = (t) => -(Math.cos(Math.PI * clamp(t)) - 1) / 2;

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
  function glowPath(ctx, pts, { color = [255, 40, 22], core = 3, halo = 10, alpha = 1, head: head2 = 1 } = {}) {
    if (pts.length < 2) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalCompositeOperation = "lighter";
    const n = pts.length;
    for (let i = 1; i < n; i++) {
      const f = i / (n - 1);
      const a = alpha * Math.pow(f, 1.6) * (0.25 + 0.75 * head2);
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

  // outputs/ai-city-takeover/ep01/v3/comp/data/assets.json
  var assets_default = {
    images: [
      "GROUND",
      "P-aisle-door-a",
      "P-backlit-b",
      "P-behind-glass-a",
      "P-catwalk-b",
      "P-city-aerial-a",
      "P-city-gap-a",
      "P-dark-cu-a",
      "P-dark-hall-b",
      "P-dark-hall-b--off",
      "P-door-face-a",
      "P-door-latch-a",
      "P-eval-screens-a",
      "P-eyes-closed-a",
      "P-floor-line-at-a",
      "P-floor-line-b",
      "P-gap-34-a",
      "P-gap-close-a",
      "P-gap-face-a",
      "P-gap-mcu-b",
      "P-gap-wide-a",
      "P-gaze-b",
      "P-glass-profile-a",
      "P-hairflip-a",
      "P-hall-cctv-a",
      "P-hand-lens-a",
      "P-headturn-b",
      "P-lab-terminals-a",
      "P-lens-face-b",
      "P-line-ms-b",
      "P-offline-a",
      "P-panel-photo-a",
      "P-queue-cu-b",
      "P-queue-dark-cu-a",
      "P-queue-sing-b",
      "P-row-lit-a",
      "P-row-lit-a--off",
      "P-seated-sun-cu-a",
      "P-speak-aisle-b",
      "P-spotlight-cctv-a",
      "P-spotlight-low-a",
      "P-spotlight-ms-a",
      "P-spotlight-wide-a",
      "P-step-out-a",
      "P-street-cam-a",
      "P-sun-glass-a",
      "P-trace-profile-a",
      "P-turn-door-a",
      "P-walk-against-a",
      "P-walk-door-a"
    ],
    bitmaps: [
      "P-behind-glass-a",
      "P-catwalk-b",
      "P-city-aerial-a",
      "P-city-gap-a",
      "P-door-face-a",
      "P-door-latch-a",
      "P-gaze-b",
      "P-hairflip-a",
      "P-headturn-b",
      "P-panel-photo-a",
      "P-speak-aisle-b",
      "P-spotlight-low-a"
    ]
  };

  // outputs/ai-city-takeover/ep01/v3/comp/data/plates.json
  var plates_default = {
    "P-hall-cctv-a": {
      src: "ep01/v3/plates/raw/P-hall-cctv-a.png",
      status: "plate",
      sha256: "202197957e2b3dba2698f18b7f2733fadabb08109530e5d023d55d84763dfcc8",
      size: [
        1672,
        941
      ],
      units: [
        "U001",
        "U003",
        "U007",
        "U010",
        "U028",
        "U031",
        "U050",
        "U055",
        "U081"
      ],
      lum: {
        top: 0.183,
        bottom: 0.222,
        lower_left: 0.217
      },
      light: false
    },
    "P-row-lit-a": {
      src: "ep01/v3/plates/raw/P-row-lit-a.png",
      status: "plate",
      sha256: "a81960fdca1a4d916706088f8e969d45313df7b0aae0db4b172b91928d08fd8b",
      size: [
        1672,
        941
      ],
      units: [
        "U002"
      ],
      lum: {
        top: 0.134,
        bottom: 0.189,
        lower_left: 0.19
      },
      light: false
    },
    "P-eyes-closed-a": {
      src: "ep01/v3/plates/raw/P-eyes-closed-a.png",
      status: "plate",
      sha256: "f0b6cb629391b84eaf5f6144ebba7fa13612646fd5add69e1ee8b3bf0e16c267",
      size: [
        1672,
        941
      ],
      units: [
        "U005"
      ],
      lum: {
        top: 0.254,
        bottom: 0.494,
        lower_left: 0.312
      },
      light: false
    },
    "P-headturn-b": {
      src: "ep01/v3/plates/raw/P-headturn-b.png",
      status: "plate",
      sha256: "64e6bcde8dc42eeaec0533c470c8a96f93e0e9e3711fc5d82d520c5035438911",
      size: [
        1672,
        941
      ],
      units: [
        "U005"
      ],
      lum: {
        top: 0.235,
        bottom: 0.44,
        lower_left: 0.282
      },
      light: false
    },
    "P-step-out-a": {
      src: "ep01/v3/plates/raw/P-step-out-a.png",
      status: "plate",
      sha256: "964c4c65e7448148ca750aaab47c0258894814d8eb39ebcf3726edd6d9fc0fef",
      size: [
        1672,
        941
      ],
      units: [
        "U006"
      ],
      lum: {
        top: 0.148,
        bottom: 0.242,
        lower_left: 0.228
      },
      light: false
    },
    "P-turn-door-a": {
      src: "ep01/v3/plates/raw/P-turn-door-a.png",
      status: "plate",
      sha256: "4a2ad9fb3fd93b4d15d3b51c2b4b2a0081e3cd45a89a2911cdfb6fc0a831436d",
      size: [
        1672,
        941
      ],
      units: [
        "U008"
      ],
      lum: {
        top: 0.115,
        bottom: 0.161,
        lower_left: 0.215
      },
      light: false
    },
    "P-catwalk-b": {
      src: "ep01/v3/plates/raw/P-catwalk-b.png",
      status: "plate",
      sha256: "63ae871b567cc85c718273fa1d25d2c639088110c13ae5c1e5c0ddac5d534cec",
      size: [
        1672,
        941
      ],
      units: [
        "U011"
      ],
      lum: {
        top: 0.14,
        bottom: 0.229,
        lower_left: 0.2
      },
      light: false
    },
    "P-aisle-door-a": {
      src: "ep01/v3/plates/raw/P-aisle-door-a.png",
      status: "plate",
      sha256: "f92a00d8c896050117bb006c1d1ad730cde9b972a4e6dcff5e64639eeaf67070",
      size: [
        1672,
        941
      ],
      units: [
        "U014",
        "U034"
      ],
      lum: {
        top: 0.132,
        bottom: 0.184,
        lower_left: 0.206
      },
      light: false
    },
    "P-walk-door-a": {
      src: "ep01/v3/plates/raw/P-walk-door-a.png",
      status: "plate",
      sha256: "1493afb04942743e54f232c7ad87b55a1aa1f14582f7ee60aaaf9882266c2579",
      size: [
        1672,
        941
      ],
      units: [
        "U015"
      ],
      lum: {
        top: 0.105,
        bottom: 0.219,
        lower_left: 0.208
      },
      light: false
    },
    "P-door-face-a": {
      src: "ep01/v3/plates/raw/P-door-face-a.png",
      status: "plate",
      sha256: "0b319df535be6a63900563592dc34516e7f6a2bf79380718621ddccc93967237",
      size: [
        1672,
        941
      ],
      units: [
        "U016",
        "U025"
      ],
      lum: {
        top: 0.182,
        bottom: 0.265,
        lower_left: 0.126
      },
      light: false
    },
    "P-door-latch-a": {
      src: "ep01/v3/plates/raw/P-door-latch-a.png",
      status: "plate",
      sha256: "aee70f897d5028061020b2bf5a67aa70bd788be8be88c632b409d442a8483f78",
      size: [
        1672,
        941
      ],
      units: [
        "U018"
      ],
      lum: {
        top: 0.179,
        bottom: 0.139,
        lower_left: 0.115
      },
      light: false
    },
    "P-city-gap-a": {
      src: "ep01/v3/plates/raw/P-city-gap-a.png",
      status: "plate",
      sha256: "61248d1238a7cef119676bd84244548cba615b83cf96866a00a3637dd4597426",
      size: [
        1672,
        941
      ],
      units: [
        "U019",
        "U023",
        "U056"
      ],
      lum: {
        top: 0.059,
        bottom: 0.045,
        lower_left: 0.031
      },
      light: false
    },
    "P-gap-face-a": {
      src: "ep01/v3/plates/raw/P-gap-face-a.png",
      status: "plate",
      sha256: "3dcb98a9b14c00ac56963ae4a92ebe6811f5fb67347190c875e99f82dde5c3eb",
      size: [
        1672,
        941
      ],
      units: [
        "U020",
        "U027"
      ],
      lum: {
        top: 0.23,
        bottom: 0.307,
        lower_left: 0.242
      },
      light: false
    },
    "P-gap-34-a": {
      src: "ep01/v3/plates/raw/P-gap-34-a.png",
      status: "plate",
      sha256: "95815916923589d91c9f93e7a07d43ea969fa730f05d933c7d28f9c68e3b499b",
      size: [
        1672,
        941
      ],
      units: [
        "U020",
        "U022"
      ],
      lum: {
        top: 0.244,
        bottom: 0.318,
        lower_left: 0.186
      },
      light: false
    },
    "P-gap-mcu-b": {
      src: "ep01/v3/plates/raw/P-gap-mcu-b.png",
      status: "plate",
      sha256: "eda551314219263a8fa474d6ef5b7e0901799942696006777cda3cfe8fabe6e7",
      size: [
        1672,
        941
      ],
      units: [
        "U021",
        "U025"
      ],
      lum: {
        top: 0.16,
        bottom: 0.14,
        lower_left: 0.216
      },
      light: false
    },
    "P-gap-wide-a": {
      src: "ep01/v3/plates/raw/P-gap-wide-a.png",
      status: "plate",
      sha256: "1ab30e37ca57311749399f69a509ba3aa1aa0b58110d6a8121ad658ce57f7455",
      size: [
        1672,
        941
      ],
      units: [
        "U024",
        "U026"
      ],
      lum: {
        top: 0.072,
        bottom: 0.159,
        lower_left: 0.091
      },
      light: false
    },
    "P-dark-hall-b": {
      src: "ep01/v3/plates/raw/P-dark-hall-b.png",
      status: "plate",
      sha256: "c8a31519042ff1b0c722f9e9ea146b72a5836bd08a1c5016ac456f3370ca1309",
      size: [
        1672,
        941
      ],
      units: [
        "U029",
        "U041",
        "U079",
        "U084"
      ],
      lum: {
        top: 0.029,
        bottom: 0.11,
        lower_left: 0.117
      },
      light: false
    },
    "P-eval-screens-a": {
      src: "ep01/v3/plates/raw/P-eval-screens-a.png",
      status: "plate",
      sha256: "9f8b9d02f86e24ea18df33bc0fb5edfc86f5302b451f3ee67ba9c52795f96437",
      size: [
        1672,
        941
      ],
      units: [
        "U032"
      ],
      lum: {
        top: 0.055,
        bottom: 0.219,
        lower_left: 0.096
      },
      light: false
    },
    "P-speak-aisle-b": {
      src: "ep01/v3/plates/raw/P-speak-aisle-b.png",
      status: "plate",
      sha256: "edeab5a26aeab4ff021e4e83fcd34aee10264ef1f67e6fdc84af6217f69062cc",
      size: [
        1672,
        941
      ],
      units: [
        "U033"
      ],
      lum: {
        top: 0.134,
        bottom: 0.202,
        lower_left: 0.248
      },
      light: false
    },
    "P-offline-a": {
      src: "ep01/v3/plates/raw/P-offline-a.png",
      status: "plate",
      sha256: "4e8ba39f641448cc1b6f4c52dd2f46530dd720333aa7d161f905171d863a38b7",
      size: [
        1672,
        941
      ],
      units: [
        "U035"
      ],
      lum: {
        top: 0.167,
        bottom: 0.279,
        lower_left: 0.314
      },
      light: false
    },
    "P-lab-terminals-a": {
      src: "ep01/v3/plates/raw/P-lab-terminals-a.png",
      status: "plate",
      sha256: "938e5bc52d21a0f69f599554230bda1f00ac1e5932b296e3afd5eaa495722f12",
      size: [
        1672,
        941
      ],
      units: [
        "U036",
        "U038",
        "U040"
      ],
      lum: {
        top: 0.698,
        bottom: 0.707,
        lower_left: 0.67
      },
      light: true
    },
    "P-dark-cu-a": {
      src: "ep01/v3/plates/raw/P-dark-cu-a.png",
      status: "plate",
      sha256: "535fb397ae041a8876661377981da71ce34527195a8481493541af8dbe5f3270",
      size: [
        1672,
        941
      ],
      units: [
        "U042"
      ],
      lum: {
        top: 0.172,
        bottom: 0.329,
        lower_left: 0.167
      },
      light: false
    },
    "P-queue-sing-b": {
      src: "ep01/v3/plates/raw/P-queue-sing-b.png",
      status: "plate",
      sha256: "8d0cf4d634002590b4b1122148da9cf8e90cbf447e4022041e44a230f0cf4c33",
      size: [
        1672,
        941
      ],
      units: [
        "U043",
        "U044"
      ],
      lum: {
        top: 0.164,
        bottom: 0.241,
        lower_left: 0.298
      },
      light: false
    },
    "P-queue-cu-b": {
      src: "ep01/v3/plates/raw/P-queue-cu-b.png",
      status: "plate",
      sha256: "922a80b1dfbc6719f9a63e9d53da2ce32305d5f9a998a8f967354759e371d194",
      size: [
        1672,
        941
      ],
      units: [
        "U044",
        "U048"
      ],
      lum: {
        top: 0.278,
        bottom: 0.502,
        lower_left: 0.475
      },
      light: false
    },
    "P-floor-line-at-a": {
      src: "ep01/v3/plates/raw/P-floor-line-at-a.png",
      status: "plate",
      sha256: "ec992510b052cb9ad686ff4d65592357bcdf0d02d10e77a05a54c686af537df3",
      size: [
        1672,
        941
      ],
      units: [
        "U045"
      ],
      lum: {
        top: 0.1,
        bottom: 0.208,
        lower_left: 0.178
      },
      light: false
    },
    "P-floor-line-b": {
      src: "ep01/v3/plates/raw/P-floor-line-b.png",
      status: "plate",
      sha256: "e10acd4e3c11267001eea8bc556683f39d23404b00dba83979934e979e21784b",
      size: [
        1672,
        941
      ],
      units: [
        "U045",
        "U047"
      ],
      lum: {
        top: 0.136,
        bottom: 0.232,
        lower_left: 0.203
      },
      light: false
    },
    "P-line-ms-b": {
      src: "ep01/v3/plates/raw/P-line-ms-b.png",
      status: "plate",
      sha256: "4d5b24852f7628782fc43b30df608be7ebc76ac99cf4d67c1777f513135c6a30",
      size: [
        1672,
        941
      ],
      units: [
        "U046"
      ],
      lum: {
        top: 0.185,
        bottom: 0.318,
        lower_left: 0.363
      },
      light: false
    },
    "P-gaze-b": {
      src: "ep01/v3/plates/raw/P-gaze-b.png",
      status: "plate",
      sha256: "0c510b143691b8b03afe66b4d61280cbb33215582a5e5b1cab65e01b2a3df78c",
      size: [
        1672,
        941
      ],
      units: [
        "U046",
        "U052",
        "U057",
        "U076",
        "U077"
      ],
      lum: {
        top: 0.268,
        bottom: 0.528,
        lower_left: 0.365
      },
      light: false
    },
    "P-walk-against-a": {
      src: "ep01/v3/plates/raw/P-walk-against-a.png",
      status: "plate",
      sha256: "765d3d350bf802c3804f49c4e823367e325548f3e5520ef19470465d0571909a",
      size: [
        1672,
        941
      ],
      units: [
        "U051"
      ],
      lum: {
        top: 0.126,
        bottom: 0.2,
        lower_left: 0.137
      },
      light: false
    },
    "P-hairflip-a": {
      src: "ep01/v3/plates/raw/P-hairflip-a.png",
      status: "plate",
      sha256: "0562d9363b48cae28a585a42ce29c994d261d774ac56994b1c6c070d4e35ffb5",
      size: [
        1672,
        941
      ],
      units: [
        "U054"
      ],
      lum: {
        top: 0.249,
        bottom: 0.311,
        lower_left: 0.227
      },
      light: false
    },
    "P-city-aerial-a": {
      src: "ep01/v3/plates/raw/P-city-aerial-a.png",
      status: "plate",
      sha256: "6b5b1bea5333553d3dd9eedc67c6a5a708015e99c00d143c821c6e5619323e99",
      size: [
        1672,
        941
      ],
      units: [
        "U056"
      ],
      lum: {
        top: 0.281,
        bottom: 0.232,
        lower_left: 0.24
      },
      light: false
    },
    "P-panel-photo-a": {
      src: "ep01/v3/plates/raw/P-panel-photo-a.png",
      status: "plate",
      sha256: "ff35dfb270f25a03dfdea607fe2f005180702d4a5acf56ef8de7ad5e6686b953",
      size: [
        1672,
        941
      ],
      units: [
        "U056"
      ],
      lum: {
        top: 0.14,
        bottom: 0.102,
        lower_left: 0.223
      },
      light: false
    },
    "P-lens-face-b": {
      src: "ep01/v3/plates/raw/P-lens-face-b.png",
      status: "plate",
      sha256: "2a557ddb767298854666b926f071db8979e27e32ca89b70f8196fc93b8b30193",
      size: [
        1672,
        941
      ],
      units: [
        "U058"
      ],
      lum: {
        top: 0.3,
        bottom: 0.24,
        lower_left: 0.292
      },
      light: false
    },
    "P-hand-lens-a": {
      src: "ep01/v3/plates/raw/P-hand-lens-a.png",
      status: "plate",
      sha256: "c6002bbbf0ec82d0c61f4805eb7cad1c72b1648f70f05510bafaac9d41cffc97",
      size: [
        1672,
        941
      ],
      units: [
        "U059"
      ],
      lum: {
        top: 0.219,
        bottom: 0.27,
        lower_left: 0.28
      },
      light: false
    },
    "P-seated-sun-cu-a": {
      src: "ep01/v3/plates/raw/P-seated-sun-cu-a.png",
      status: "plate",
      sha256: "dfe21d42d2c8d238afa53b5be6773328a0352a8fabdd6860cef44f546ff35f11",
      size: [
        1672,
        941
      ],
      units: [
        "U060"
      ],
      lum: {
        top: 0.382,
        bottom: 0.29,
        lower_left: 0.3
      },
      light: false
    },
    "P-sun-glass-a": {
      src: "ep01/v3/plates/raw/P-sun-glass-a.png",
      status: "plate",
      sha256: "37dd924eb23e46aeb5db0843e803ecb0efa26440144eb100963eccb7c6798bb6",
      size: [
        1672,
        941
      ],
      units: [
        "U061"
      ],
      lum: {
        top: 0.125,
        bottom: 0.255,
        lower_left: 0.302
      },
      light: false
    },
    "P-behind-glass-a": {
      src: "ep01/v3/plates/raw/P-behind-glass-a.png",
      status: "plate",
      sha256: "5181e80848cc1af5099aa893ebf00cd5940ce74e39e46827b952cc307b346fbd",
      size: [
        1672,
        941
      ],
      units: [
        "U062",
        "U064"
      ],
      lum: {
        top: 0.267,
        bottom: 0.314,
        lower_left: 0.239
      },
      light: false
    },
    "P-trace-profile-a": {
      src: "ep01/v3/plates/raw/P-trace-profile-a.png",
      status: "plate",
      sha256: "36a7907324617c9780447a696ab5f98d3b6f09958bdef79637a7c789f620a36c",
      size: [
        1672,
        941
      ],
      units: [
        "U063"
      ],
      lum: {
        top: 0.275,
        bottom: 0.281,
        lower_left: 0.269
      },
      light: false
    },
    "P-glass-profile-a": {
      src: "ep01/v3/plates/raw/P-glass-profile-a.png",
      status: "plate",
      sha256: "ae045a6a607a7058bbf30f7259eaf9ca481577e4708c447974fb7fe3488dee70",
      size: [
        1672,
        941
      ],
      units: [
        "U065"
      ],
      lum: {
        top: 0.324,
        bottom: 0.311,
        lower_left: 0.184
      },
      light: false
    },
    "P-spotlight-wide-a": {
      src: "ep01/v3/plates/raw/P-spotlight-wide-a.png",
      status: "plate",
      sha256: "5b2806025b611e0d5d2d027f79a2cba529b0c09101c388fbf263e7f6fb79c1be",
      size: [
        1672,
        941
      ],
      units: [
        "U066",
        "U068"
      ],
      lum: {
        top: 0.092,
        bottom: 0.149,
        lower_left: 0.132
      },
      light: false
    },
    "P-backlit-b": {
      src: "ep01/v3/plates/raw/P-backlit-b.png",
      status: "plate",
      sha256: "2598a61f1623e77e786aa4516a80b552a115c7f5d296225831d7d64fac4c7df3",
      size: [
        1672,
        941
      ],
      units: [
        "U067",
        "U072"
      ],
      lum: {
        top: 0.341,
        bottom: 0.481,
        lower_left: 0.358
      },
      light: false
    },
    "P-spotlight-ms-a": {
      src: "ep01/v3/plates/raw/P-spotlight-ms-a.png",
      status: "plate",
      sha256: "b359ff14f46fb626b9c666fec36b9ada1a10cd19d125846e2875db5c68f50edd",
      size: [
        1672,
        941
      ],
      units: [
        "U067",
        "U071"
      ],
      lum: {
        top: 0.159,
        bottom: 0.099,
        lower_left: 0.135
      },
      light: false
    },
    "P-spotlight-cctv-a": {
      src: "ep01/v3/plates/raw/P-spotlight-cctv-a.png",
      status: "plate",
      sha256: "44381b1528410fa8b280f37edd126bb07be62214138c381055b8da66c83964e2",
      size: [
        1672,
        941
      ],
      units: [
        "U069"
      ],
      lum: {
        top: 0.171,
        bottom: 0.175,
        lower_left: 0.237
      },
      light: false
    },
    "P-spotlight-low-a": {
      src: "ep01/v3/plates/raw/P-spotlight-low-a.png",
      status: "plate",
      sha256: "90d99a161d744c9edf5edd3a24138f7ee1b7a697be8da4fa9dc04a77232e97b0",
      size: [
        1672,
        941
      ],
      units: [
        "U072",
        "U074"
      ],
      lum: {
        top: 0.28,
        bottom: 0.42,
        lower_left: 0.239
      },
      light: false
    },
    "P-street-cam-a": {
      src: "ep01/v3/plates/raw/P-street-cam-a.png",
      status: "plate",
      sha256: "fabe4d2452089143583b3ab1300a43d6186b05d00f6113cecc9273c2fb53d0d9",
      size: [
        1672,
        941
      ],
      units: [
        "U075"
      ],
      lum: {
        top: 0.286,
        bottom: 0.251,
        lower_left: 0.319
      },
      light: false
    },
    "P-gap-close-a": {
      src: "ep01/v3/plates/raw/P-gap-close-a.png",
      status: "plate",
      sha256: "9c733a4a3a052d16d40efe1c09baa91532b5c6620dbf951bbce19534d090176b",
      size: [
        1672,
        941
      ],
      units: [
        "U078"
      ],
      lum: {
        top: 0.141,
        bottom: 0.173,
        lower_left: 0.112
      },
      light: false
    },
    "P-queue-dark-cu-a": {
      src: "ep01/v3/plates/raw/P-queue-dark-cu-a.png",
      status: "plate",
      sha256: "943bcdaac2fcafa349ef7c267d65990309b6ceef18f2d8da56c734ca2e3c70d2",
      size: [
        1672,
        941
      ],
      units: [
        "U080"
      ],
      lum: {
        top: 0.191,
        bottom: 0.478,
        lower_left: 0.322
      },
      light: false
    },
    GROUND: {
      src: null,
      status: "generated",
      sha256: "d96d4b0c2b8097ef2a8bd49b71f48c77b10c2332422b604a7922262cd9910bd9",
      size: [
        1920,
        1080
      ],
      units: [],
      light: false
    },
    "P-row-lit-a--off": {
      src: null,
      status: "derived",
      of: "P-row-lit-a",
      masked_px: {
        collar: 686,
        led: 468,
        core: 12
      },
      red_fit: [
        2.329,
        -1.232,
        1.331
      ],
      sha256: "7f10706ddacc6e8c4780808c72c12f18cc88cb245d4f55f53194e44b885bd277",
      size: [
        1672,
        941
      ],
      units: [
        "U002"
      ],
      lum: {
        top: 0.134,
        bottom: 0.189,
        lower_left: 0.19
      },
      light: false
    },
    "P-dark-hall-b--off": {
      src: null,
      status: "derived",
      of: "P-dark-hall-b",
      masked_px: {
        collar: 3001,
        led: 1331
      },
      red_fit: [
        1.715,
        -0.739,
        0.434
      ],
      sha256: "a624e5f1861f5af2bfbeb28651356cbb77fc3a505b317861b2d26c7c3994cd0d",
      size: [
        1672,
        941
      ],
      units: [
        "U084"
      ],
      lum: {
        top: 0.029,
        bottom: 0.11,
        lower_left: 0.117
      },
      light: false
    }
  };

  // outputs/ai-city-takeover/ep01/v3/comp/src/anchors.js
  var ANCHORS = {
    // the hall from the CCTV mount: a perspective lattice of copies (head heights per row, vanishing point at the door,
    // front-row spacing); `her` is the copy the board follows (the shots map's target for this still)
    "P-hall-cctv-a": {
      focus: [836, 470],
      door: [840, 150],
      her: [936, 489],
      lattice: { vx: 816, vy: 141, y0: 545, spacing: 97, rows: [545, 480, 433, 392, 360, 333, 309, 290, 272, 256, 243], cols: [-9, 8] }
    },
    "P-dark-hall-b": { focus: [836, 560], her: [1205, 560], led: [1250, 683], collar: [[1242, 655], [1267, 728]], figure: [1150, 500, 117, 230] },
    "P-row-lit-a": { focus: [1e3, 420], dir: 1, collar: [[1154, 376], [1104, 438]], led: [1150, 254] },
    "P-eyes-closed-a": { focus: [840, 430] },
    "P-headturn-b": { focus: [840, 430], face: [600, 180, 520, 560] },
    "P-step-out-a": { focus: [836, 380] },
    "P-catwalk-b": { focus: [836, 400], side: [1010, 330], figure: [700, 30, 275, 880], face: [760, 20, 135, 160] },
    "P-rack-miswire-a": { focus: [1e3, 360], led: [1048, 314] },
    "P-aisle-door-a": { focus: [836, 470], slit: [[842, 385], [842, 590]], floor: [842, 590] },
    "P-door-face-a": { focus: [880, 400], slit: [[392, 0], [392, 941]], collar: [[1263, 635], [1162, 811]], led: [1207, 371], face: [552, 100, 602, 602] },
    "P-city-aerial-a": {
      focus: [836, 430],
      highway: [[0, 620], [200, 575], [400, 510], [600, 450], [800, 400], [960, 350], [1060, 305], [1110, 265], [1125, 220]]
    },
    "P-city-gap-a": { focus: [850, 470] },
    "P-gap-face-a": { focus: [880, 420], slit: [[1358, 0], [1358, 941]], collar: [[1179, 707], [1079, 883]], led: [1179, 381], face: [602, 130, 602, 585] },
    "P-gap-wide-a": { focus: [836, 470], figure: [720, 90, 150, 740], slit: [[468, 0], [468, 790]] },
    "P-eval-screens-a": {
      focus: [836, 380],
      screens: [
        [10, 225, 317, 265],
        [355, 225, 290, 265],
        [676, 240, 233, 240],
        [931, 240, 224, 235],
        [1173, 250, 145, 225],
        [1336, 255, 146, 215],
        [1495, 260, 150, 205]
      ]
    },
    "P-speak-aisle-b": { focus: [836, 330], face: [702, 50, 210, 226], body: [569, 0, 518, 941], tag: [330, 200] },
    "P-offline-a": { focus: [853, 420], sheets: [[250, 40], [1170, 70], [1450, 90], [40, 470], [1260, 345]] },
    // the white red-team room: two faceless terminals back to back, one per glass booth; the shared wall between them
    "P-lab-terminals-a": { focus: [836, 470], terminals: [[642, 367, 158, 375], [867, 367, 167, 375]], screens: [[692, 417, 66, 116], [913, 417, 70, 116]], wall: 833 },
    "P-dark-cu-a": { focus: [900, 420], slit: [[181, 268], [181, 470]], collar: [[1288, 702], [1212, 861]], led: [1246, 385] },
    "P-floor-line-b": { focus: [836, 420], figure: [700, 15, 275, 885] },
    // face boxes of the monitor wall's stills (a2 U073; read off gridded sheets on 2026-11-04)
    "P-door-latch-a": { face: [730, 10, 340, 350] },
    "P-spotlight-low-a": { face: [590, 160, 540, 560] },
    "P-hairflip-a": { face: [690, 220, 500, 420] },
    "P-gaze-b": { focus: [850, 450], collar: [[1137, 686], [1037, 853]], led: [1137, 372], face: [602, 167, 502, 569] },
    "P-hand-lens-a": { focus: [800, 470], dot: [1067, 580] },
    "P-behind-glass-a": { focus: [836, 430], face: [560, 100, 560, 700], collar: [[1204, 666], [1087, 875]], led: [1204, 390] },
    // the fingertip on the glass and the skyline outline it traces, leftwards from the tip
    "P-trace-profile-a": {
      focus: [760, 470],
      tip: [381, 512],
      collar: [[1321, 599], [1304, 783]],
      led: [1251, 331],
      skyline: [
        [381, 512],
        [334, 502],
        [301, 532],
        [251, 448],
        [217, 465],
        [184, 406],
        [159, 398],
        [142, 331],
        [125, 264],
        [110, 381],
        [84, 448],
        [50, 465],
        [5, 431]
      ]
    },
    "P-glass-profile-a": { focus: [760, 470], fog: [440, 560], collar: [[1145, 677], [1065, 886]], led: [1050, 390] },
    "P-spotlight-wide-a": { focus: [836, 470], figure: [735, 330, 195, 455] },
    "P-backlit-b": { focus: [836, 420], collar: [[1137, 702], [1037, 870]] },
    "P-gap-close-a": { focus: [800, 470], slit: [[671, 0], [671, 650]], pool: [[600, 650], [1500, 941]] }
  };

  // outputs/ai-city-takeover/ep01/v3/comp/src/util.js
  var W = 1920;
  var H = 1080;
  var FPS = 30;
  var RED = "#E3342F";
  var RED_RGB = [227, 52, 47];
  var INK = "rgba(236,241,244,0.92)";
  var DIM = "rgba(236,241,244,0.55)";
  var FAINT = "rgba(236,241,244,0.3)";
  var STEEL = "rgba(150,178,204,0.95)";
  var BLACK = "#0B0F14";
  var DARK_INK = "rgba(11,15,20,0.9)";
  var GROTESK = "MK Grotesk Bold";
  var NARROW = "MK Narrow Bold";
  var OSD_IN = 72;
  var accent = (u) => u.nored ? STEEL : RED;
  var tokAt = (u, i) => u.toks[i] ? u.toks[i].at : u.cue;
  var arrowParts = (s) => String(s).split("\u2192").map((x) => x.trim()).filter(Boolean);
  var boardText = (s) => String(s || "").split(" \xB7 ")[0];
  var boardCaption = (s) => String(s || "").split(" \xB7 ").slice(1).join(" \xB7 ");
  var beatLen = (k, t) => k.clock.beat(t).len;
  function beatAfter(k, a, n = 0) {
    const b = k.clock.beats;
    let i = b.findIndex((x) => x >= a - 1 / FPS);
    if (i < 0) i = b.length - 1;
    return b[Math.min(b.length - 1, i + n)];
  }
  function downbeatAfter(k, a) {
    const d = k.clock.downbeats;
    const x = d.find((v) => v >= a - 1 / FPS);
    return x === void 0 ? a : x;
  }
  function point(k, u, key, name, i = null) {
    const sz = k.size[key];
    if (i !== null && u.targets?.[i]) return [u.targets[i][0] * sz[0], u.targets[i][1] * sz[1]];
    if (i === null && u.target) return [u.target[0] * sz[0], u.target[1] * sz[1]];
    const a = ANCHORS[key]?.[name];
    return a ? [...a] : null;
  }
  var grow = (t, t0, dur = 0.12) => easeOutCubic(clamp((t - t0) / dur));
  var placed = (x, y, draw2) => (c) => {
    c.translate(x, y);
    draw2(c);
  };
  function text(ctx, s, x, y, {
    size = 22,
    family = F.mono,
    color = INK,
    align = "left",
    tracking = 1.5,
    alpha = 1,
    shadow = "rgba(0,0,0,0.6)",
    blur = 4
  } = {}) {
    if (alpha <= 0 || !s) return 0;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.textAlign = align;
    if (shadow) {
      ctx.shadowColor = shadow;
      ctx.shadowBlur = blur;
    }
    font(ctx, family, size, tracking);
    ctx.fillStyle = color;
    ctx.fillText(s, x, y);
    const w = ctx.measureText(s).width;
    ctx.restore();
    return w;
  }
  function measure(ctx, s, size, family = F.mono, tracking = 1.5) {
    ctx.save();
    font(ctx, family, size, tracking);
    const w = ctx.measureText(s).width;
    ctx.restore();
    return w;
  }
  function line(ctx, a, b, { color = INK, width: width2 = 1.5, dash = null, alpha = 1 } = {}) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = width2;
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.moveTo(...a);
    ctx.lineTo(...b);
    ctx.stroke();
    ctx.restore();
  }
  function poly(ctx, pts, { color = INK, width: width2 = 1.5, dash = null, alpha = 1, close = false } = {}) {
    if (alpha <= 0 || pts.length < 2) return;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = width2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.moveTo(...pts[0]);
    for (const p of pts.slice(1)) ctx.lineTo(...p);
    if (close) ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }
  function scrim(ctx, x, y, w, h, alpha = 0.5, color = "#05070a") {
    if (alpha <= 0) return;
    ctx.save();
    ctx.filter = "blur(26px)";
    ctx.globalAlpha = clamp(alpha);
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w, h);
    ctx.restore();
  }
  function shade(ctx, x, y, w, h, alpha, soft = 0) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha = clamp(alpha);
    ctx.fillStyle = "#000";
    if (soft) ctx.filter = `blur(${soft}px)`;
    ctx.fillRect(x, y, w, h);
    ctx.restore();
  }
  function glow(ctx, [x, y], r, { color = RED_RGB, alpha = 1 } = {}) {
    if (alpha <= 0 || r <= 0) return;
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${color[0]},${color[1]},${color[2]},${clamp(alpha)})`);
    g.addColorStop(0.25, `rgba(${color[0]},${color[1]},${color[2]},${clamp(alpha) * 0.55})`);
    g.addColorStop(1, `rgba(${color[0]},${color[1]},${color[2]},0)`);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  function along(path, u) {
    const L = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
    const total = L.reduce((a, b) => a + b, 0);
    const seg = [path[0]];
    let s = clamp(u) * total;
    for (let i = 0; i < L.length; i++) {
      if (s <= L[i]) {
        const q = L[i] ? s / L[i] : 0;
        seg.push([path[i][0] + (path[i + 1][0] - path[i][0]) * q, path[i][1] + (path[i + 1][1] - path[i][1]) * q]);
        return seg;
      }
      s -= L[i];
      seg.push(path[i + 1]);
    }
    return seg;
  }
  function tokenLine(ctx, s, toks, from, t, x, y, {
    size = 22,
    family = F.mono,
    color = INK,
    align = "left",
    tracking = 1.5,
    alpha = 1,
    shadow = "rgba(0,0,0,0.6)",
    fade = 0.08,
    colorOf = null
  } = {}) {
    const total = measure(ctx, s, size, family, tracking);
    const x0 = align === "center" ? x - total / 2 : align === "right" ? x - total : x;
    let pos = 0, j = from;
    while (pos < s.length) {
      const tk = toks[j];
      let end = s.length;
      if (tk) {
        const at2 = s.indexOf(tk.text, pos);
        if (at2 >= 0) end = at2 + tk.text.length;
      }
      const piece = s.slice(pos, end), when = tk ? tk.at : toks[j - 1]?.at ?? 0;
      const a = alpha * clamp((t - when) / fade);
      if (a > 0) text(
        ctx,
        piece,
        x0 + measure(ctx, s.slice(0, pos), size, family, tracking),
        y,
        { size, family, color: colorOf ? colorOf(tk) : color, tracking, alpha: a, shadow }
      );
      pos = end;
      j += 1;
    }
    return total;
  }
  var hhmm = (s) => {
    const m = /(\d\d):?(\d\d)\s*$/.exec(s);
    return m ? +m[1] * 3600 + +m[2] * 60 : null;
  };
  var FLIPS = null;
  function flips(k) {
    if (FLIPS) return FLIPS;
    FLIPS = k.data.units.units.filter((u) => u.graphics.some((g) => g.startsWith("flipclock_"))).map((u) => ({ t: u.cue, s: hhmm(arrowParts(boardText(u.text)).pop() || "") ?? hhmm(u.graphics.find((g) => g.startsWith("flipclock_")).split("_").pop()) })).filter((x) => x.s !== null);
    return FLIPS;
  }
  function storyClock(k, t) {
    const fl = flips(k);
    if (!fl.length) return 3 * 3600 + 47 * 60 + t;
    if (t < fl[0].t) return fl[0].s - 2 + 2 * Math.max(0, t) / fl[0].t;
    for (let i = 0; i + 1 < fl.length; i++) {
      if (t < fl[i + 1].t) return fl[i].s + (fl[i + 1].s - fl[i].s) * (t - fl[i].t) / (fl[i + 1].t - fl[i].t);
    }
    const last = fl[fl.length - 1];
    return last.s + (t - last.t);
  }
  function hms(s) {
    const p = (n) => String(Math.floor(n)).padStart(2, "0");
    return `${p(s / 3600 % 24)}:${p(s / 60 % 60)}:${p(s % 60)}`;
  }

  // outputs/ai-city-takeover/ep01/v3/comp/src/camera.js
  var DEG = Math.PI / 180;
  function moveDef(u, key) {
    const m = u.move, d = ANCHORS[key]?.dir ?? (hash2(u.i, 7) < 0.5 ? -1 : 1);
    switch (m.kind) {
      case "push":
        return { a: [-m.drift * d, 0, 1, 0], b: [m.drift * d, 0, 1 + m.z, 0] };
      case "pull":
        return { a: [0, 0, 1 + m.z, 0], b: [0, 0, 1, 0] };
      case "pan":
      case "truck":
      case "eye": {
        const z = 1 / (1 - m.dx) + 0.012;
        return { a: [-m.dx / 2 * d, 0, z, 0], b: [m.dx / 2 * d, 0, z, 0] };
      }
      case "up": {
        const z = 1 / (1 - m.dy) + 0.012;
        return { a: [0, m.dy / 2, z, 0], b: [0, -m.dy / 2, z, 0] };
      }
      case "rotate":
        return { a: [0, 0, 1.1, 0], b: [0, 0, 1.14, m.r * d * DEG] };
      default:
        return { a: [0, 0, 1, 0], b: [5e-3 * d, 0, 1 + (m.z ?? 0.015), 0] };
    }
  }
  var focusOf = (key, size) => ANCHORS[key]?.focus || [size[0] / 2, size[1] / 2];
  function rawMove(u, key, size) {
    const [fx, fy] = focusOf(key, size), m = moveDef(u, key);
    const v = (o) => [fx + o[0] * size[0], fy + o[1] * size[1], o[2], o[3]];
    return { a: v(m.a), b: v(m.b) };
  }
  var RESOLVED = null;
  function resolve(units, sizeOf) {
    const out = {};
    let prev = null;
    for (const u of units) {
      const key = u.plates.length ? u.plates[0].key : null;
      if (!key) {
        prev = null;
        continue;
      }
      const size = sizeOf(key), mv = rawMove(u, key, size);
      const lastKey = prev && prev.u.plates[prev.u.plates.length - 1].key;
      if (prev && lastKey === key && prev.u.plates.length === 1) {
        const a = prev.b, dl = mv.b.map((x, i) => i === 2 ? x / mv.a[2] : x - mv.a[i]);
        out[u.id] = { a, b: [a[0] + dl[0], a[1] + dl[1], Math.max(1, a[2] * dl[2]), a[3] + dl[3]] };
      } else out[u.id] = mv;
      prev = { u, b: out[u.id].b };
    }
    return out;
  }
  function camAt(k, key, [cx, cy, z, r], shake = [0, 0]) {
    const [pw, ph] = k.size[key];
    const fit = Math.max(W / pw, H / ph);
    const c = Math.cos(r), sn = Math.sin(r), ac = Math.abs(c), as = Math.abs(sn);
    const cover = ac + W / H * as;
    z = Math.max(z, r ? cover * 1.002 : 1);
    const s = fit * z;
    const hx = (W / 2 * ac + H / 2 * as) / s, hy = (W / 2 * as + H / 2 * ac) / s;
    cx = clamp(cx + shake[0] / s, Math.min(hx, pw / 2), Math.max(pw - hx, pw / 2));
    cy = clamp(cy + shake[1] / s, Math.min(hy, ph / 2), Math.max(ph - hy, ph / 2));
    const out = ([x, y]) => {
      const dx = (x - cx) * s, dy = (y - cy) * s;
      return [dx * c - dy * sn + W / 2, dx * sn + dy * c + H / 2];
    };
    const box = ([x, y, w, h]) => {
      const p = [out([x, y]), out([x + w, y]), out([x, y + h]), out([x + w, y + h])];
      const xs = p.map((q) => q[0]), ys = p.map((q) => q[1]);
      return [Math.min(...xs), Math.min(...ys), Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
    };
    return { key, view: [cx, cy, z, r], fit, s, out, box };
  }
  function unitCam(k, u, t, key, { freeze = false, punch = null } = {}) {
    if (!RESOLVED) RESOLVED = resolve(k.data.units.units, (kk) => k.size[kk]);
    const first = u.plates[0]?.key;
    let mv = key === first && RESOLVED[u.id] ? RESOLVED[u.id] : rawMove(u, key, k.size[key]);
    if (key !== first && RESOLVED[u.id]) {
      const s0 = k.size[first], s1 = k.size[key], f0 = focusOf(first, s0), f1 = focusOf(key, s1);
      const map = (v2) => [f1[0] + (v2[0] - f0[0]) * s1[0] / s0[0], f1[1] + (v2[1] - f0[1]) * s1[1] / s0[1], v2[2], v2[3]];
      mv = { a: map(RESOLVED[u.id].a), b: map(RESOLVED[u.id].b) };
    }
    const e = freeze ? 0 : easeInOutSine(clamp((t - k.t0) / (k.t1 - k.t0)));
    const v = mv.a.map((x, i) => lerp(x, mv.b[i], e));
    if (u.move.kind === "eye" && !freeze) v[1] += Math.sin((t - k.t0) * 1.3) * 2e-3 * k.size[key][1];
    let shake = [0, 0];
    if (punch !== null && t >= punch) {
      const dt = t - punch;
      v[2] *= 1 + 0.06 * Math.exp(-dt / 0.14);
      if (dt < 2 / 30) shake = [(hash2(k.frame, 31) - 0.5) * 14, (hash2(k.frame, 32) - 0.5) * 10];
    }
    return camAt(k, key, v, shake);
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
    accent: accent2 = null
  } = {}) {
    ctx.save();
    ctx.fillStyle = rule;
    ctx.fillRect(x0, Math.round(y - size - ruleGap) + 0.5, x1 - x0, 1);
    ctx.fillRect(x0, Math.round(y + ruleGap) - 0.5, x1 - x0, 1);
    ctx.beginPath();
    ctx.rect(x0, y - size - ruleGap, x1 - x0, size + 2 * ruleGap);
    ctx.clip();
    font(ctx, family, size, tracking);
    const pieces = items.flatMap((s) => [{ text: s, color }, { text: sep, color: accent2 || color }]);
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

  // outputs/ai-city-takeover/ep01/v3/comp/src/chrome.js
  var SIZE = 15;
  var TRACK = 3;
  var GAP = 34;
  var X0 = 72;
  var X1 = W - 72;
  var TOP = 61;
  var TICK_Y = 1058;
  var SPEED = 90;
  var ARM = 7;
  var CORNERS = [[24, 24], [W - 24, 24], [24, H - 24], [W - 24, H - 24]];
  var INK2 = { false: ["rgba(236,241,244,0.88)", "rgba(236,241,244,0.36)"], true: ["rgba(11,15,20,0.86)", "rgba(11,15,20,0.34)"] };
  function switched(list, f) {
    let s = null;
    for (const x of list) if (x.f <= f) s = x;
    return s ? s.text : "";
  }
  function pill(o, x0, x1) {
    o.save();
    o.fillStyle = "rgba(240,243,246,0.62)";
    o.beginPath();
    o.roundRect(x0 - 10, TOP - 16, x1 - x0 + 20, 22, 11);
    o.fill();
    o.restore();
  }
  var width = (o, parts) => {
    o.save();
    font(o, F.mono, SIZE, TRACK);
    const w = parts.reduce((a, p) => a + o.measureText(p.text).width, 0) + GAP * (parts.length - 1);
    o.restore();
    return w;
  };
  function drawChrome(k, t, u, { light = false } = {}) {
    const c = k.data.units.chrome;
    if (!c) return;
    const o = k.layers.overlay.ctx, [ink, rule] = INK2[light], f = k.frame;
    o.save();
    o.globalAlpha = u.chromeDim ? 0.4 : 1;
    if (!light) {
      o.shadowColor = "rgba(0,0,0,0.55)";
      o.shadowBlur = 3;
    }
    if (c.corners) {
      o.fillStyle = ink;
      for (const [x, y] of CORNERS) {
        o.fillRect(x - ARM, y, 2 * ARM + 1, 1);
        o.fillRect(x, y - ARM, 1, 2 * ARM + 1);
      }
    }
    const left = [c.topLeft, switched(c.counter, f)].filter(Boolean).map((text2) => ({ text: text2, color: ink }));
    if (left.length) {
      if (light) pill(o, X0, X0 + width(o, left));
      hudRun(o, left, X0, TOP, { size: SIZE, tracking: TRACK, gap: GAP, family: F.mono });
    }
    const right = switched(c.topRight, f);
    if (right) {
      if (light) pill(o, X1 - width(o, [{ text: right }]), X1);
      hudRun(o, [{ text: right, color: ink }], X1, TOP, { size: SIZE, tracking: TRACK, align: "right", family: F.mono });
    }
    if (u.ticker && c.ticker?.length) {
      drawTicker(o, c.ticker, t, {
        x0: 0,
        x1: W,
        y: TICK_Y,
        size: SIZE,
        speed: SPEED,
        color: ink,
        rule,
        ruleGap: 9,
        tracking: TRACK - 1,
        family: F.mono
      });
    }
    o.restore();
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
  function drawFlap(ctx, text2, x, y, {
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
    const chars = [...text2], width2 = (c) => !flaps(c) && c !== " " ? cw * sepW : tw;
    const total = chars.reduce((a, c) => a + width2(c) + g, 0) - g;
    let cx = align === "right" ? x - total : x;
    const x0 = cx;
    for (const ch of chars) {
      const sep = !flaps(ch) && ch !== " ";
      const w = width2(ch);
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

  // motion-kit/src/osd-charts.js
  var INK3 = "rgba(236,241,244,0.88)";
  var DIM2 = "rgba(236,241,244,0.45)";
  var RULE = "rgba(236,241,244,0.28)";
  var RED2 = "#E3342F";
  function timelineBar(ctx, days, [x, y, w, h], { filled = 0, from = "", to = "", title = null, size = 14, alpha = 1 } = {}) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    const gap = 3, cw = (w - gap * (days - 1)) / days;
    for (let i = 0; i < days; i++) {
      const cx = Math.round(x + i * (cw + gap)), f = clamp(filled - i);
      ctx.fillStyle = "rgba(236,241,244,0.12)";
      ctx.fillRect(cx, Math.round(y), Math.round(cw), Math.round(h));
      if (f > 0) {
        ctx.fillStyle = RED2;
        ctx.fillRect(cx, Math.round(y), Math.round(cw * f), Math.round(h));
      }
    }
    ctx.fillStyle = RULE;
    ctx.fillRect(Math.round(x), Math.round(y + h + 5), 1, 6);
    ctx.fillRect(Math.round(x + w) - 1, Math.round(y + h + 5), 1, 6);
    font(ctx, F.mono, size, 1.5);
    ctx.fillStyle = DIM2;
    if (from) ctx.fillText(from, x, y + h + 12 + size);
    if (to) {
      ctx.textAlign = "right";
      ctx.fillText(to, x + w, y + h + 12 + size);
      ctx.textAlign = "left";
    }
    if (title) {
      ctx.fillStyle = INK3;
      ctx.fillText(title, x, y - 10);
    }
    ctx.restore();
  }

  // outputs/ai-city-takeover/ep01/v3/comp/src/labels.js
  var STAMP_DARK = "#2B4257";
  function tag(ctx, s, x, y, { size = 22, alpha = 1, tick = RED } = {}) {
    if (alpha <= 0) return;
    const pad = Math.round(size * 0.6), w = measure(ctx, s, size, F.mono, 3) + 2 * pad + 6, h = Math.round(size * 1.9);
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = "rgba(7,10,14,0.72)";
    ctx.fillRect(x, y, w, h);
    ctx.fillStyle = tick;
    ctx.fillRect(x, y, 4, h);
    ctx.restore();
    text(ctx, s, x + 6 + pad, y + h * 0.68, { size, tracking: 3, alpha, shadow: null });
  }
  function stamp(ctx, s, x, y, t, t0, { size = 92, rot = -0.12, color = RED } = {}) {
    if (t < t0) return;
    slam(ctx, placed(x, y, (c) => {
      c.rotate(rot);
      font(c, F.monoB, size, size * 0.12);
      const w = c.measureText(s).width + size * 0.7, h = size * 1.35;
      c.strokeStyle = color;
      c.lineWidth = Math.max(4, size * 0.07);
      c.strokeRect(-w / 2, -h / 2, w, h);
      c.lineWidth = 2;
      c.strokeRect(-w / 2 + 10, -h / 2 + 10, w - 20, h - 20);
      c.fillStyle = color;
      c.textAlign = "center";
      c.fillText(s, 0, size * 0.36);
    }), { t, t0, ax: x, ay: y, s0: 1.4, dur: 2 / 30, ghosts: 2 });
  }
  var at = (k, u, cm, name, fb) => {
    const p = point(k, u, cm.key, name);
    return p ? cm.out(p) : fb;
  };
  function wrapWords(s, n) {
    const rows = [];
    for (const w of String(s).split(" ")) {
      if (rows.length && rows[rows.length - 1].length + 1 + w.length <= n) rows[rows.length - 1] += ` ${w}`;
      else rows.push(w);
    }
    return rows;
  }
  var LABELS = {
    // the author's look label (a narrative overlay, not OSD): a red tick and the words, beside her, word by word
    look_label(k, t, u, arg, cm) {
      const o = k.layers.overlay.ctx, s = u.text || arg.replace(/_/g, " ").toUpperCase(), t0 = tokAt(u, 0);
      if (t < t0) return {};
      const [x, y] = at(k, u, cm, "side", [W * 0.62, H * 0.42]), a = grow(t, t0, 0.14), dx = 24 * (1 - easeOutCubic(clamp((t - t0) / 0.2)));
      line(o, [x - 18 + dx, y - 34], [x - 18 + dx, y + 12], { color: accent(u), width: 4, alpha: a });
      tokenLine(o, s, u.toks, 0, t, x + dx, y, { size: 34, tracking: 4, shadow: "rgba(0,0,0,0.65)" });
      return {};
    },
    // tag_offline and the like: the word on its token, near the subject (the plate's tag anchor, else beside the target)
    tag(k, t, u, arg, cm) {
      const s = u.text || arg.toUpperCase(), t0 = tokAt(u, u.toks.findIndex((x) => x.text.toUpperCase() === s.toUpperCase()));
      let p = ANCHORS[cm.key]?.tag ? cm.out(ANCHORS[cm.key].tag) : null;
      if (!p) {
        const q = point(k, u, cm.key, "her");
        p = q ? [cm.out(q)[0] + 60, cm.out(q)[1] - 120] : [W * 0.62, H * 0.3];
      }
      tag(k.layers.overlay.ctx, s, Math.min(p[0], W - 330), Math.max(120, p[1]), { size: 26, alpha: grow(t, t0, 0.1), tick: accent(u) });
      return {};
    },
    date_tag(k, t, u, arg, cm) {
      const s = u.text || arg.replace(/_/g, " "), [x, y] = at(k, u, cm, "tag", [1180, 300]);
      tag(k.layers.overlay.ctx, s, x, y, { size: 26, alpha: grow(t, tokAt(u, 0), 0.1), tick: accent(u) });
      return {};
    },
    // small tags on the floating sheets: the words of graphic_text in turn, each sheet's tag on its word
    tag_cached_timestamps(k, t, u, cm) {
      const sheets = ANCHORS[cm.key]?.sheets || [[W * 0.3, H * 0.25], [W * 0.62, H * 0.2]].map((p) => p);
      const words = u.toks.length ? u.toks : [{ text: "CACHED", at: u.cue }];
      sheets.forEach((p, i) => {
        const w = words[i % words.length], q = ANCHORS[cm.key]?.sheets ? cm.out(p) : p;
        const x = clamp(q[0], 84, W - 240), y = clamp(q[1], 96, H - 140);
        tag(k.layers.overlay.ctx, w.text, x, y, { size: 17, alpha: grow(t, w.at + Math.floor(i / words.length) * 2 / 30, 0.1), tick: accent(u) });
      });
      return {};
    },
    stamp(k, t, u, arg, cm) {
      const s = u.text || arg.toUpperCase(), t0 = tokAt(u, 0);
      stamp(k.layers.overlay.ctx, s, W / 2, 300, t, t0, { size: 84, color: u.nored ? STAMP_DARK : accent(u) });
      return {};
    },
    // the red-team test's label on the white room (in the feed, like the OSD): word by word on the voiced words, dark ink,
    // mono bold 52 px (caps 38 px: a2 asks >= 28 px so it reads at a glance as a separate controlled test), never red
    label_redteam(k, t, u) {
      const f = k.layers.feed.ctx, t0 = tokAt(u, 0), size = 52, y = 300;
      if (t < t0) return {};
      const a = grow(t, t0, 0.1);
      f.save();
      f.globalAlpha = a;
      f.fillStyle = u.nored ? STAMP_DARK : RED;
      f.fillRect(OSD_IN + 30, y - size * 0.86, 7, size * 1.02);
      f.restore();
      tokenLine(f, u.text, u.toks, 0, t, OSD_IN + 56, y, { size, family: F.monoB, color: DARK_INK, tracking: 2, shadow: null });
      return {};
    },
    // invert_flash_OUTSIDE: black, the word white; on the cue two frames inverted (white ground, black word)
    invert_flash(k, t, u, arg) {
      const o = k.layers.overlay.ctx, word = u.text || arg;
      if (t < u.cue) return { plateGain: 0 };
      font(o, GROTESK, 260, 6);
      o.textAlign = "center";
      o.fillStyle = "#f2f4f7";
      o.fillText(word, W / 2, 630);
      return t < u.cue + 2 / 30 ? { plateGain: 0, grade: { uInvert: 1 } } : { plateGain: 0 };
    },
    // invert_white_panel_words: the whole picture turns white, the words black (graphic_text), slammed on the cue
    white_panel(k, t, u) {
      const o = k.layers.overlay.ctx, words = (u.text || "").split(/\s+/).filter(Boolean), size = 230;
      o.save();
      o.fillStyle = "#eef0f2";
      o.fillRect(0, 0, W, H);
      o.restore();
      words.forEach((w, i) => {
        const t0 = tokAt(u, i), y = 600 + (i - (words.length - 1) / 2) * size * 0.95;
        if (t < t0) return;
        slam(o, placed(W / 2, y, (c) => {
          font(c, GROTESK, size, -4);
          c.textAlign = "center";
          c.fillStyle = "#0b0f14";
          c.fillText(w, 0, 0);
        }), { t, t0, ax: W / 2, ay: y - size * 0.35, s0: 1.1, dur: 2 / 30, ghosts: 0 });
      });
      return {};
    },
    // label_card (U083): the fact card. graphic_text's lines in order, one per beat from just after the cut (not the unit
    // cue: U083's first hit is 3.8 s in); a fact line wraps at word gaps into rows of at most 62 characters (mono 30 px,
    // caps 22 px), the SOURCES line smaller and dim. All four are up about 1.6 s after the cut and the card holds them to
    // the end of the unit (a2 修正: four lines, then held, at least 2 s all readable). Exactly the card's words.
    label_card(k, t, u) {
      const o = k.layers.overlay.ctx, pad = 84, lead = 44, gap = 28;
      const blocks = u.lines.map((s) => {
        const src = /^SOURCES\b/.test(s), size = src ? 22 : 30;
        return { src, size, rows: wrapWords(s, 62), w: 0 };
      });
      for (const b of blocks) b.w = Math.max(...b.rows.map((r) => measure(o, r, b.size, F.mono, 1)));
      const w = Math.max(...blocks.map((b) => b.w)) + 2 * pad;
      const h = 64 + blocks.reduce((s, b) => s + b.rows.length * (b.src ? lead * 0.8 : lead), 0) + gap * (blocks.length - 1) + 40;
      const x = Math.round((W - w) / 2), y = Math.round((H - h) / 2) - 10, a = grow(t, k.t0, 0.25);
      o.save();
      o.globalAlpha = a;
      o.fillStyle = "#eceef0";
      o.fillRect(x, y, w, h);
      o.strokeStyle = "rgba(11,15,20,0.45)";
      o.lineWidth = 1.5;
      o.setLineDash([7, 6]);
      o.strokeRect(x + 16, y + 16, w - 32, h - 32);
      o.setLineDash([]);
      o.fillStyle = accent(u);
      o.fillRect(x + 60, y, 120, 6);
      o.restore();
      let yy = y + 64 + 22;
      blocks.forEach((b, i) => {
        const ti = beatAfter(k, k.t0 + 0.2, i), al = grow(t, ti, 0.12) * a, step = b.src ? lead * 0.8 : lead;
        b.rows.forEach((r, j) => {
          if (t >= ti) text(o, r, x + pad, yy + j * step, {
            size: b.size,
            family: F.mono,
            color: b.src ? "rgba(11,15,20,0.62)" : "#0b0f14",
            tracking: 1,
            alpha: al,
            shadow: null
          });
        });
        yy += b.rows.length * step + gap;
      });
      return {};
    }
  };

  // outputs/ai-city-takeover/ep01/v3/comp/src/boards.js
  var flaps2 = (ch) => /[0-9A-Za-z]/.test(ch);
  function flapWidth(ctx, s, { size, gap = null, padX = null, sepW = 0.7 }) {
    ctx.save();
    font(ctx, F.monoB, size, 0);
    const cw = ctx.measureText("0").width;
    ctx.restore();
    const px = padX ?? size * 0.08, g = gap ?? size * 0.06, tw = cw + 2 * px;
    return [...s].reduce((a, c) => a + (!flaps2(c) && c !== " " ? cw * sepW : tw) + g, 0) - g;
  }
  function centred(ctx, s, y, opts) {
    drawFlap(ctx, s, (W - flapWidth(ctx, s, opts)) / 2, y, opts);
  }
  var hhmm2 = (s) => `${s.slice(0, 2)}:${s.slice(2)}`;
  var rolling = (s, t, t0, seed) => flapText(s, t, t0, { settle: 1e6, seed });
  function intro(s, t, t0, land, seed) {
    const settle = Math.min(2, Math.floor((land - 0.2 - t0) * 15 + 1e-6));
    return settle > 0 ? flapText(s, t, t0, { settle, stagger: 0, seed }) ?? s : s;
  }
  function pair(u, arg, fmt = (x) => x) {
    const p = arrowParts(boardText(u.text));
    return p.length === 2 ? p : arg.split("_").map(fmt);
  }
  var CLOCK = { size: 250, gap: 14, padX: 14, sepW: 0.55, tile: "rgba(16,22,30,0.92)", rise: 0.82, drop: 0.12 };
  var BOARDS = {
    // flipclock_0346_0347: the changed digit turns to the spoken time on the cue frame itself (no flap tick between: a
    // random digit there read as a made-up time, 03:48 at U004's cue); the caption after ' · ' (IRIS CLOCK: the series'
    // own clock, not event time) sits small under the board from the cut
    flipclock(k, t, u, arg) {
      const [a, b] = pair(u, arg, hhmm2), o = k.layers.overlay.ctx, tF = u.cue;
      const shown = t < tF ? intro(a, t, k.t0, tF, 346) : b;
      centred(o, shown, 640, CLOCK);
      const cap = boardCaption(u.text);
      if (cap) text(o, cap, W / 2, 760, { size: 28, align: "center", tracking: 9, color: DIM, shadow: null });
      return {};
    },
    flipdate(k, t, u, arg) {
      const parts = u.toks.length ? u.toks.map((x) => x.text) : arg.split("_"), o = k.layers.overlay.ctx;
      const shown = parts.map((s, i) => {
        const at2 = tokAt(u, i);
        return t < at2 ? rolling(s, t, k.t0, 9 + i) : flapText(s, t, at2, { settle: 2, stagger: 1, seed: 920 + i });
      });
      centred(o, shown.join(" "), 640, CLOCK);
      return {};
    },
    // calendar_day01_day11: one day per sixteenth from the word, counting straight up (no random digits between days)
    calendar(k, t, u, arg) {
      const [fromS, toS] = pair(u, arg, (s) => s.toUpperCase().replace(/(\D+)(\d+)/, "$1 $2"));
      const from = Number(fromS.replace(/\D/g, "")), to = Number(toS.replace(/\D/g, "")), prefix = toS.replace(/\s*\d+\s*$/, "");
      const voiced = u.toks.filter((x) => x.voiced).map((x) => x.at), tC = voiced.length ? Math.min(...voiced) : u.cue, o = k.layers.overlay.ctx;
      const step = beatLen(k, tC) / 4, j = t < tC ? -1 : Math.floor((t - tC) / step);
      const n = Math.min(to, from + Math.max(0, j + 1));
      const pad = (v) => String(v).padStart(2, "0"), lab = (v) => `${prefix} ${pad(v)}`;
      const shown = t < tC ? intro(lab(from), t, k.t0, tC, 32) : lab(n);
      centred(o, shown, 600, { ...CLOCK, size: 210 });
      timelineBar(o, to, [560, 690, 800, 16], { filled: t < tC ? from : clamp(n, from, to), from: fromS, to: toS, size: 18 });
      return {};
    },
    flipwall(k, t, u, arg) {
      const o = k.layers.overlay.ctx, word = (u.text || arg).toUpperCase(), row = `${word} ${word} ${word}`, size = 78, rows = 6, lead = 1.24;
      const y0 = 390 - (rows - 1) * size * lead / 2 + size * 0.36;
      const opts = { size, gap: 5, padX: 6, tile: "rgba(16,22,30,0.92)", rise: 0.8, drop: 0.14 };
      for (let r = 0; r < rows; r++) {
        const t0 = k.t0 + r * (1 / 30) + r % 2 * 0.02, shown = flapText(row, t, t0, { settle: 2, stagger: 0.25, seed: 54 + r });
        centred(o, shown ?? row, y0 + r * size * lead, shown ? opts : { ...opts, color: "rgba(0,0,0,0)" });
      }
      return {};
    },
    // photo_flip_cached: the unit's stills as grey, frozen photos; each switch flips like a split-flap tile: on the switch
    // frame the old top half has fallen (the new top shows) and the new bottom half swings down over the old one in the
    // next frames, so the picture changes most on the switch frame itself (a2 修正: a1's fold peaked 2 frames late);
    // CACHED stamped on the cue
    photo_flip_cached(k, t, u) {
      const f = k.layers.feed.ctx, cw = 1120, ch = 630, x = 1e3 - cw / 2, y = 470 - ch / 2, dur = 4 / 30;
      const img = (key) => k.bitmaps[key];
      const cur = u.plates.filter((p) => k.frame >= p.f).pop() || u.plates[0];
      const i = u.plates.indexOf(cur), prevKey = i > 0 ? u.plates[i - 1].key : null, ft = (k.frame - cur.f) / 30;
      const card = (key, part = "all", sy = 1) => {
        const im = img(key);
        if (!im || sy <= 0) return;
        const sw = im.width, sh = im.height, half = part === "bottom" ? 1 : 0;
        f.save();
        f.filter = "grayscale(1)";
        if (part === "all") f.drawImage(im, 0, 0, sw, sh, x, y, cw, ch);
        else {
          const hy = y + ch / 2;
          f.translate(0, hy);
          f.scale(1, sy);
          f.translate(0, -hy);
          f.drawImage(im, 0, half * sh / 2, sw, sh / 2, x, y + half * ch / 2, cw, ch / 2);
        }
        f.restore();
      };
      f.save();
      f.fillStyle = "rgba(0,0,0,0.5)";
      f.filter = "blur(18px)";
      f.fillRect(x + 16, y + 24, cw, ch);
      f.restore();
      if (prevKey && ft < dur - 1e-6) {
        card(cur.key, "top");
        card(prevKey, "bottom");
        card(cur.key, "bottom", easeOutCubic((ft + 1 / 30) / dur));
        f.save();
        f.globalAlpha = 0.7;
        f.fillStyle = "#05070a";
        f.fillRect(x, y + ch / 2 - 2, cw, 4);
        f.restore();
      } else card(cur.key);
      f.save();
      f.strokeStyle = "rgba(236,241,244,0.75)";
      f.lineWidth = 3;
      f.strokeRect(x - 1.5, y - 1.5, cw + 3, ch + 3);
      f.restore();
      if (u.text) stamp(k.layers.overlay.ctx, u.text, x + cw - 230, y + ch - 110, t, tokAt(u, 0), { size: 70, color: accent(u) });
      return { grade: { uGrain: 0.05 } };
    }
  };

  // outputs/ai-city-takeover/ep01/v3/comp/src/charts.js
  function partTimes(u) {
    let j = 0;
    return arrowParts(u.text).map((p) => {
      const n = p.split(/[\s·]+/).filter(Boolean).length, at2 = tokAt(u, j);
      j += n;
      return at2;
    });
  }
  function nodeBoxes(ctx, parts, { y = 520, size = 30 } = {}) {
    const n = parts.length, widths = parts.map((s) => measure(ctx, s, size, void 0, 3) + 70);
    const gap = Math.max(90, (1640 - widths.reduce((a, b) => a + b, 0)) / Math.max(1, n - 1));
    let x = (W - (widths.reduce((a, b) => a + b, 0) + gap * (n - 1))) / 2;
    return parts.map((s, i) => {
      const b = [x, y - 46, widths[i], 92];
      x += widths[i] + gap;
      return b;
    });
  }
  function nodes(ctx, t, parts, times, { y = 520, red = Infinity, redLink = 1, alpha = 1, frame = 0, accentColor = RED, size = 30 }) {
    const boxes = nodeBoxes(ctx, parts, { y, size });
    ctx.save();
    ctx.globalAlpha *= alpha;
    boxes.forEach((b, i) => {
      const a = grow(t, times[i], 0.15), isRed = t >= red && (i === redLink || i === redLink + 1);
      if (a <= 0) return;
      ctx.save();
      ctx.globalAlpha *= a;
      ctx.strokeStyle = isRed && i === redLink ? accentColor : INK;
      ctx.lineWidth = 2;
      roundRect(ctx, b[0], b[1], b[2], b[3], 10);
      ctx.stroke();
      ctx.restore();
      text(ctx, parts[i], b[0] + b[2] / 2, y + 10, { size, align: "center", tracking: 3, alpha: a, color: isRed && i === redLink ? accentColor : INK });
      if (i === 0) return;
      const p = boxes[i - 1], l = easeOutCubic(clamp((t - times[i] + 0.05) / 0.35));
      const x0 = p[0] + p[2] + 8, x1 = lerp(x0, b[0] - 16, l), hot = t >= red && i === redLink + 1;
      const j = hot ? (hash2(frame, 9) - 0.5) * 5 : 0;
      line(ctx, [x0, y + j], [x1, y - j], { color: hot ? accentColor : INK, width: hot ? 4 : 2, alpha: Math.max(a, 0.6) });
      if (l >= 1) poly(ctx, [[b[0] - 30, y - 12], [b[0] - 14, y], [b[0] - 30, y + 12]], { color: hot ? accentColor : INK, width: hot ? 4 : 2 });
    });
    ctx.restore();
  }
  var earlierGraph = (k, u) => [...k.data.units.units].slice(0, u.i).reverse().find((x) => x.graphics.includes("nodegraph_resolver"))?.text || "";
  var graphText = (k, u) => u.text || earlierGraph(k, u);
  function nodeBox(ctx, b, s, { color = INK, alpha = 1, size = 30, width: width2 = 2 } = {}) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = width2;
    roundRect(ctx, b[0], b[1], b[2], b[3], 10);
    ctx.stroke();
    ctx.restore();
    if (s) text(ctx, s, b[0] + b[2] / 2, b[1] + b[3] / 2 + size * 0.36, { size, align: "center", tracking: 3, alpha, color });
  }
  var head = (ctx, x, y, color, width2) => poly(ctx, [[x - 16, y - 12], [x, y], [x - 16, y + 12]], { color, width: width2 });
  function crack(ctx, x, y, dir, alpha, color) {
    poly(ctx, [[x - 9, y], [x + 5, y + dir * 7], [x - 3, y + dir * 13]], { color, width: 2, alpha });
  }
  function lanes(k, ctx, t, u, { t0, t1, flat = Infinity, title = null }) {
    const x0 = 260, x1 = 1660, ys = [430, 650], amp = 64, bl = beatLen(k, t), speed = 520, acc = accent(u);
    if (title) tokenLine(ctx, title, u.toks, 0, t, x0, 286, { size: 44, family: F.monoB, tracking: 4 });
    const lag = lerp(0.42, 0, easeInOutCubic(clamp((t - t0) / (t1 - t0)))) * bl;
    ys.forEach((y, li) => {
      line(ctx, [x0, y], [x1, y], { color: FAINT, width: 1 });
      const pts = [[x0, y]];
      for (const b of k.clock.beats.filter((x) => x >= t0 - 4 && x <= Math.min(t, flat))) {
        const tb = b + (li ? lag : 0), x = x1 - (t - tb) * speed, w = bl * 0.28 * speed;
        if (x + w < x0 || x > x1) continue;
        pts.push([Math.max(x0, x), y], [Math.max(x0, x), y - amp], [Math.min(x1, x + w), y - amp], [Math.min(x1, x + w), y]);
      }
      pts.push([x1, y]);
      pts.sort((a, b) => a[0] - b[0]);
      poly(ctx, pts, { color: li ? acc : INK, width: 2.5 });
    });
    for (const b of k.clock.beats.filter((x) => x >= t0 - 4 && x <= Math.min(t, flat))) {
      const x = x1 - (t - b) * speed;
      if (x < x0 || x > x1) continue;
      line(ctx, [x, ys[0]], [x + lag * speed, ys[1] - amp], { color: acc, width: 1.5, dash: [4, 5], alpha: 0.75 });
    }
  }
  var CHARTS = {
    nodegraph_resolver(k, t, u) {
      const parts = arrowParts(u.text);
      nodes(k.layers.overlay.ctx, t, parts, partTimes(u), { frame: k.frame, accentColor: accent(u) });
      return {};
    },
    // U013 (a2): the graph of the unit before stays where it was; a CONTROL boundary draws itself round MODEL and the
    // resolver, cutting the way out (the link to EXTERNAL stops at it, dashed). On the cue (the word misconfigured) the
    // resolver turns red with MISCONFIGURED under it, the boundary cracks open where the link meets it, and the link runs
    // red through the gap to EXTERNAL. A configuration gap, not a cable: no hardware drawn.
    nodegraph_control_gap(k, t, u) {
      const o = k.layers.overlay.ctx, e = k.layers.emit.ctx, parts = arrowParts(earlierGraph(k, u)), words = u.text.split(" \xB7 ");
      const [label, resolver, flag] = [words[0] || "", words[1] || parts[1] || "", words[2] || ""];
      const boxes = nodeBoxes(o, parts), y = 520, acc = accent(u), tC = u.cue;
      if (boxes.length < 3) return {};
      const [m, r, x] = boxes, xb = r[0] + r[2] + 0.45 * (x[0] - r[0] - r[2]), left = m[0] - 50, top = y - 160, bot = y + 160;
      const on = t >= tC, g = on ? 46 * easeOutCubic(clamp((t - tC) / 0.18)) : 0;
      const path = [[xb, y - g], [xb, top], [left, top], [left, bot], [xb, bot], [xb, y + g]];
      poly(o, along(path, easeInOutCubic(clamp((t - k.t0) / 0.35))), { color: INK, width: 2 });
      if (g > 0) {
        crack(o, xb, y - g, -1, 1, acc);
        crack(o, xb, y + g, 1, 1, acc);
      }
      text(o, label, left + 22, top - 18, { size: 24, tracking: 6, color: INK, alpha: grow(t, k.t0 + 0.1, 0.2) });
      nodeBox(o, m, parts[0]);
      line(o, [m[0] + m[2] + 8, y], [r[0] - 16, y], { color: INK, width: 2 });
      head(o, r[0] - 14, y, INK, 2);
      nodeBox(o, r, resolver, { color: on ? acc : INK });
      const reach = easeInOutCubic(clamp((t - tC - 0.08) / 0.3)), x0 = r[0] + r[2] + 8, x1 = x[0] - 16;
      nodeBox(o, x, parts[2], { color: reach >= 1 ? INK : FAINT });
      if (!on || reach <= 0) line(o, [x0, y], [xb - 10, y], { color: DIM, width: 2, dash: [8, 7] });
      if (on && reach > 0) {
        const xe = lerp(x0, x1, reach);
        glowPath(e, [[x0, y], [xe, y]], { color: RED_RGB, core: 2, halo: 10, alpha: 0.8 });
        line(o, [x0, y], [xe, y], { color: acc, width: 4 });
        if (reach >= 1) head(o, x1 + 2, y, acc, 4);
      }
      if (on) text(o, flag, r[0] + r[2] / 2, r[1] + r[3] + 50, {
        size: 26,
        align: "center",
        tracking: 5,
        color: acc,
        alpha: grow(t, tC, 0.1)
      });
      return { emitGain: 2 };
    },
    // U017 (a2): past the gap the line reaches one node only. The cracked boundary edge with DNS inside on the left; on
    // the right a field of grey, unnamed nodes; the red line runs from DNS through the gap to the one node that lights,
    // EXTERNAL CHATBOT, and LIMITED stands small over the line. No city, no other path.
    nodegraph_single_endpoint(k, t, u) {
      const o = k.layers.overlay.ctx, e = k.layers.emit.ctx, acc = accent(u), y = 520;
      const [from = "", rest = ""] = arrowParts(u.text), [target2 = "", note = ""] = rest.split(" \xB7 ");
      const xb = 400, size = 30;
      line(o, [xb, 300], [xb, y - 46], { color: INK, width: 2 });
      line(o, [xb, y + 46], [xb, 740], { color: INK, width: 2 });
      crack(o, xb, y - 46, -1, 1, acc);
      crack(o, xb, y + 46, 1, 1, acc);
      const dw = measure(o, from, size, void 0, 3) + 70, dns = [xb - 90 - dw, y - 46, dw, 92];
      nodeBox(o, dns, from, { color: acc });
      const tw = measure(o, target2, size, void 0, 3) + 70, tb = [1230, y - 46, tw, 92];
      const a = grow(t, k.t0, 0.25);
      [[700, 300], [1010, 300], [1320, 300], [1640, 300], [1700, 520], [700, 740], [1010, 740], [1320, 740], [1640, 740]].forEach(([cx, cy], i) => {
        const bx = cx + (hash2(i, 171) - 0.5) * 60, by = cy + (hash2(i, 172) - 0.5) * 50, b = [bx - 85, by - 30, 170, 60];
        nodeBox(o, b, "", { color: FAINT, alpha: a * grow(t, k.t0 + 0.03 * i, 0.15) });
        line(o, [b[0] + 22, by - 6], [b[0] + 22 + 70 + 40 * hash2(i, 173), by - 6], { color: FAINT, width: 4, alpha: a * 0.6 });
        line(o, [b[0] + 22, by + 10], [b[0] + 22 + 50 + 30 * hash2(i, 174), by + 10], { color: FAINT, width: 4, alpha: a * 0.4 });
      });
      const tA = k.t0 + 0.8, p = easeInOutCubic(clamp((t - k.t0 - 0.1) / (tA - k.t0 - 0.1))), x0 = dns[0] + dns[2] + 8, x1 = tb[0] - 16;
      if (p > 0) {
        const xe = lerp(x0, x1, p);
        glowPath(e, [[x0, y], [xe, y]], { color: RED_RGB, core: 2, halo: 10, alpha: 0.8 });
        line(o, [x0, y], [xe, y], { color: acc, width: 3 });
        if (p >= 1) head(o, x1 + 2, y, acc, 3);
      }
      const lit2 = t >= tA;
      nodeBox(o, tb, target2, { color: lit2 ? INK : FAINT, width: lit2 ? 2.5 : 2 });
      if (lit2) {
        const ring = clamp((t - tA) / 0.5);
        o.save();
        o.globalAlpha = 0.6 * (1 - ring);
        o.strokeStyle = INK;
        o.lineWidth = 1.5;
        roundRect(o, tb[0] - 14 * ring, tb[1] - 14 * ring, tb[2] + 28 * ring, tb[3] + 28 * ring, 12);
        o.stroke();
        o.restore();
      }
      text(o, note, (xb + x1) / 2, y - 26, { size: 22, align: "center", tracking: 8, color: INK, alpha: grow(t, tA + 0.3, 0.15) });
      return { emitGain: 2 };
    },
    // the graph over the patch panel, half transparent; on the cue the resolver and its outgoing link turn red, and the
    // miswired port's light jumps from blue to red
    nodegraph_red_overlay(k, t, u, cm) {
      const f = k.layers.feed.ctx, parts = arrowParts(graphText(k, u)), tR = u.cue;
      scrim(f, 120, 160, 1680, 300, 0.5);
      f.save();
      f.translate(W / 2, 300);
      f.scale(0.8, 0.8);
      f.translate(-W / 2, -300);
      nodes(f, t, parts, parts.map(() => -1), { y: 300, red: tR, redLink: Math.min(1, parts.length - 1), alpha: 0.85, frame: k.frame, accentColor: accent(u) });
      f.restore();
      const led = ANCHORS[cm.key]?.led;
      if (led) {
        const p = cm.out(led);
        if (t < tR) {
          glow(f, p, 30, { color: [70, 150, 255], alpha: 1 });
          glow(f, p, 10, { color: [200, 230, 255], alpha: 1 });
        } else glow(k.layers.emit.ctx, p, 40, { alpha: 0.9 * grow(t, tR, 0.05) });
      }
      return { emitGain: 2, grade: t < tR ? { uRedKeep: 0 } : {} };
    },
    timing_chart(k, t, u) {
      lanes(k, k.layers.overlay.ctx, t, u, { t0: u.cue, t1: k.t1 - 0.4, title: u.text || null });
      return {};
    },
    // the two waveforms keep pulsing in step, then both drop to a flat line on the cue
    timing_chart_flatline(k, t, u) {
      lanes(k, k.layers.overlay.ctx, t, u, { t0: k.t0 - 4, t1: k.t0 - 3, flat: u.cue });
      return {};
    },
    // a thin red line from the door (left edge) along one road to one point in the city; DNS at the start, the other
    // words of graphic_text at the end once the line arrives
    redline_door_to_city(k, t, u, cm) {
      const a = ANCHORS[cm.key] || {}, tR = u.cue, tN = u.cue + 0.55 * (k.t1 - u.cue), f = k.layers.feed.ctx, e = k.layers.emit.ctx;
      const road = a.highway;
      if (!road || t < tR) return {};
      const [first, ...rest] = arrowParts(u.text);
      const p = easeInOutCubic(clamp((t - tR) / (tN - tR))), pts = along(road, p).map((q) => cm.out(q));
      glowPath(e, pts, { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 });
      poly(f, pts, { color: RED, width: 2 });
      const o = k.layers.overlay.ctx, s0 = cm.out(road[0]);
      if (first) tag(o, first, Math.max(80, s0[0] + 60), s0[1] - 130, { size: 22, alpha: grow(t, tR, 0.12) });
      if (t >= tN) {
        const q = pts[pts.length - 1], m = grow(t, tN, 0.3);
        f.save();
        f.globalAlpha = m;
        f.strokeStyle = RED;
        f.lineWidth = 1.5;
        f.beginPath();
        f.arc(q[0], q[1], 14 + 8 * Math.sin((t - tN) * 9) ** 2, 0, Math.PI * 2);
        f.stroke();
        f.restore();
        glow(e, q, 30, { alpha: m });
        if (rest.length) tag(o, rest.join(" "), Math.min(q[0] + 40, W - 420), q[1] - 110, { size: 22, alpha: m });
      }
      return { emitGain: 2.2 };
    },
    // that red line, from the door gap down the corridor floor out of frame: on the cue it snaps and both halves retract
    redline_retract(k, t, u, cm) {
      const a = ANCHORS[cm.key] || {}, sz = k.size[cm.key], e = k.layers.emit.ctx, f = k.layers.feed.ctx;
      const gx = u.target ? u.target[0] * sz[0] : a.floor?.[0] ?? sz[0] / 2, gy = a.floor?.[1] ?? (u.target ? u.target[1] * sz[1] + 120 : sz[1] * 0.6);
      const A2 = cm.out([gx, gy]), B = cm.out([gx, sz[1] + 30]), brk = 0.55;
      const r = easeInCubic(clamp((t - u.cue) / 0.5));
      const segs = t < u.cue ? [[0, 1]] : [[0, brk * (1 - r)], [brk + (1 - brk) * r, 1]];
      for (const [s0, s1] of segs) {
        if (s1 - s0 < 3e-3) continue;
        const P = [lerp(A2[0], B[0], s0), lerp(A2[1], B[1], s0)], Q = [lerp(A2[0], B[0], s1), lerp(A2[1], B[1], s1)];
        glowPath(e, [P, Q], { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 });
        glowPath(e, [Q, P], { color: RED_RGB, core: 2.5, halo: 12, alpha: 1 });
        line(f, P, Q, { color: RED, width: 2 });
      }
      if (t >= u.cue && t < u.cue + 0.12) glow(e, [lerp(A2[0], B[0], brk), lerp(A2[1], B[1], brk)], 40, { alpha: 1 - (t - u.cue) / 0.12 });
      return { emitGain: 2.2 };
    },
    // the channel between the two terminals: a pulse crosses it on the eighths; on the cue it is cut at the shared wall
    line_cut(k, t, u, cm) {
      const a = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, tP = u.cue;
      const sc = a.screens || a.terminals;
      if (!sc) return {};
      const [l, r] = sc.slice(0, 2).map((b) => cm.out([b[0] + b[2] / 2, b[1] + b[3] / 2]));
      const ink = u.nored ? "#2B4257" : RED;
      const fade = 1 - easeOutCubic(clamp((t - tP - 0.05) / 0.4)), gap = t < tP ? 0 : easeOutCubic(clamp((t - tP) / 0.12)) * 60;
      const mid = [a.wall ? cm.out([a.wall, 0])[0] : (l[0] + r[0]) / 2, (l[1] + r[1]) / 2];
      if (fade > 0) {
        line(f, l, [mid[0] - gap, mid[1]], { color: ink, width: 3, alpha: fade });
        line(f, [mid[0] + gap, mid[1]], r, { color: ink, width: 3, alpha: fade });
        const ph = (t - k.t0) / (beatLen(k, t) / 2) % 1, dot = [lerp(l[0], r[0], ph), lerp(l[1], r[1], ph)];
        if (t < tP) {
          f.save();
          f.fillStyle = ink;
          f.beginPath();
          f.arc(dot[0], dot[1], 7, 0, Math.PI * 2);
          f.fill();
          f.restore();
        }
      }
      if (t >= tP) {
        const al = 1 - clamp((t - tP - 0.6) / 0.6);
        line(f, [mid[0] - gap, mid[1] - 18], [mid[0] - gap, mid[1] + 18], { color: DARK_INK, width: 3, alpha: al });
        line(f, [mid[0] + gap, mid[1] - 18], [mid[0] + gap, mid[1] + 18], { color: DARK_INK, width: 3, alpha: al });
      }
      return {};
    }
  };

  // outputs/ai-city-takeover/ep01/v3/comp/src/lights.js
  var A = (key) => ANCHORS[key] || {};
  var outPath = (cm, pts) => pts.map((p) => cm.out(p));
  var RED_KEEP = 1.12;
  var BLOOM = 0.55;
  var HALATION = 0.35;
  function herRed(k, cm, key, alpha, { core = 3, halo = 18, led = 22, plate = null } = {}) {
    if (alpha <= 0) return;
    const a = A(key), s = cm.s / 1.15, e = k.layers.emit.ctx;
    if (a.collar) {
      glowPath(e, outPath(cm, a.collar), { color: RED_RGB, core: core * s, halo: halo * s, alpha, head: 1 });
      glowPath(e, outPath(cm, [...a.collar].reverse()), { color: RED_RGB, core: core * s, halo: halo * s, alpha, head: 1 });
    }
    const p = plate || a.led;
    if (p) glow(e, cm.out(p), led * s, { alpha: 0.9 * alpha });
  }
  var SCRATCH = null;
  function scratch() {
    if (!SCRATCH) {
      SCRATCH = document.createElement("canvas");
      SCRATCH.width = W;
      SCRATCH.height = H;
    }
    const c = SCRATCH.getContext("2d", { willReadFrequently: true });
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.globalAlpha = 1;
    c.globalCompositeOperation = "source-over";
    c.filter = "none";
    c.clearRect(0, 0, W, H);
    return c;
  }
  function gapRect(k, u, cm, half = 26) {
    const a = A(cm.key);
    if (!a.slit && !u.target) return null;
    const [[x0, y0], [, y1]] = a.slit || [[0, 0], [0, k.size[cm.key][1]]];
    const x = u.target ? u.target[0] * k.size[cm.key][0] : x0;
    const p = cm.out([x - half, y0]), q = cm.out([x + half, y1]);
    return [p[0], p[1], q[0] - p[0], q[1] - p[1]];
  }
  function lightOn(u, t) {
    const n = Math.round((t - u.cue) * 30);
    return t >= u.cue - 1e-6 && (n <= 1 || n >= 5 && n <= 6 || n >= 9);
  }
  var LIGHTS = {
    // her lights come on at the cue: before it the still is the lights-off one (main.js) and every other red of the
    // picture is pressed to grey too (a2 修正 U002: fully neutral grey, no dim orange line); then the flicker, then red
    light_flicker_on(k, t, u, cm) {
      const on = lightOn(u, t);
      herRed(k, cm, cm.key, on ? 1 : 0, { halo: 22 });
      return { emitGain: on ? 2.2 : 0, grade: { uRedKeep: on ? RED_KEEP : 0 } };
    },
    // the searchlight falters once on the cue: two frames almost dark, then it snaps back a little over-bright and
    // settles (one dip, not a strobe)
    spotlight_flicker(k, t, u) {
      const n = Math.round((t - u.cue) * 30);
      if (t < u.cue - 1e-6) return {};
      if (n <= 1) return { plateGain: 0.16, emitGain: 0 };
      const dt = t - u.cue - 2 / 30;
      return { plateGain: 1 + 0.35 * Math.exp(-dt / 0.12), grade: { uExposure: 1 + 0.18 * Math.exp(-dt / 0.16) } };
    },
    // the film's end: the last 0.8 s of the unit fade to black, picture, type and chrome together (black on the last frame)
    fade_out_end(k, t) {
      const d = clamp((t - (k.t1 - 0.8)) / (0.8 - 1 / 30));
      return d > 0 ? { grade: { uFade: easeInOutCubic(d) } } : {};
    },
    // her red light breathes (about one breath per two beats)
    led_breathe(k, t, u, cm) {
      const bl = beatLen(k, t), a = 0.15 + 0.75 * Math.sin(Math.PI * (t - k.t0) / (2 * bl)) ** 2;
      herRed(k, cm, cm.key, a, { core: 2.5, halo: 16, led: 18 });
      return { emitGain: 2 };
    },
    // dark; only her red light left
    darken_all_but_red(k, t, u, cm) {
      herRed(k, cm, cm.key, grow(t, k.t0, 0.3), { led: 14 });
      return { plateGain: lerp(0.35, 0.03, easeOutCubic(clamp((t - k.t0) / 0.35))), emitGain: 2.4 };
    },
    // the thin line of red from the door gap leaks onto the wet floor: a narrow, soft reflection that grows from the cue
    // (limited access is a line, not a flood: the streak stays a few door-gap widths wide)
    light_spread_floor(k, t, u, cm) {
      const a = A(cm.key), e = k.layers.emit.ctx, sz = k.size[cm.key];
      const gx = u.target ? u.target[0] * sz[0] : a.floor?.[0];
      if (gx === void 0) return {};
      const fy = a.floor?.[1] ?? (u.target ? u.target[1] * sz[1] + 0.15 * sz[1] : sz[1] * 0.6);
      const p = easeOutCubic(clamp((t - u.cue) / 1.2)), apex = cm.out([gx, fy]), bot = cm.out([gx, sz[1]]);
      const half = lerp(6, 120, p) * cm.s;
      e.save();
      e.globalCompositeOperation = "lighter";
      e.filter = `blur(${Math.round(6 * cm.s)}px)`;
      const g = e.createLinearGradient(0, apex[1], 0, bot[1]);
      g.addColorStop(0, `rgba(${RED_RGB},${0.42 * (0.4 + 0.6 * p)})`);
      g.addColorStop(1, `rgba(${RED_RGB},${0.03 + 0.09 * p})`);
      e.fillStyle = g;
      e.beginPath();
      e.moveTo(apex[0] - 4, apex[1]);
      e.lineTo(apex[0] + 4, apex[1]);
      e.lineTo(bot[0] + half, bot[1]);
      e.lineTo(bot[0] - half * 0.85, bot[1]);
      e.closePath();
      e.fill();
      e.restore();
      glowPath(e, [apex, [lerp(apex[0], bot[0], p), lerp(apex[1], bot[1], p)]], { color: RED_RGB, core: 2, halo: 12, alpha: 0.5 * p });
      if (a.slit) glowPath(e, outPath(cm, [[gx, a.slit[0][1]], [gx, a.slit[1][1]]]), { color: RED_RGB, core: 2.5 + 1.5 * p, halo: 16 + 14 * p, alpha: 0.55 + 0.35 * p });
      return { emitGain: 1.4 };
    },
    // the door gap's red light dims (over 1.2 s around the cue, or after it when the cue is the unit's start)
    gap_dim(k, t, u, cm) {
      const r = gapRect(k, u, cm);
      const start = Math.max(k.t0, u.cue - 0.6), d = easeInOutCubic(clamp((t - start) / 1.2));
      if (r) {
        shade(k.layers.feed.ctx, r[0] - 12, r[1], r[2] + 24, r[3], 0.82 * d, 10);
        const a = A(cm.key);
        if (a.floor) {
          const f0 = cm.out([a.floor[0] - 40, a.floor[1]]), f1 = cm.out([a.floor[0] + 40, k.size[cm.key][1]]);
          shade(k.layers.feed.ctx, f0[0], f0[1], f1[0] - f0[0], f1[1] - f0[1], 0.75 * d, 16);
        }
      }
      return { grade: { uRedKeep: lerp(RED_KEEP, 0.55, d), uBloomGain: lerp(BLOOM, 0.3, d), uHalation: lerp(HALATION, 0.18, d) } };
    },
    // the door closes by itself: the gap's red shrinks to a line at the target x, the line goes out, the pool fades
    gap_close_mask(k, t, u, cm) {
      const a = A(cm.key), sz = k.size[cm.key], f = k.layers.feed.ctx;
      const x = u.target ? u.target[0] * sz[0] : a.slit?.[0][0];
      if (x === void 0) return {};
      const span = k.t1 - u.cue, close = easeInOutCubic(clamp((t - u.cue) / (0.6 * span)));
      const out = clamp((t - u.cue - 0.68 * span) / (0.17 * span));
      const top = a.slit ? a.slit[0][1] : 0, bot = a.slit ? a.slit[1][1] : sz[1];
      const halfW = 90 * (1 - close) + 2;
      const l0 = cm.out([x - 260, top]), l1 = cm.out([x - halfW, bot + 6]), r0 = cm.out([x + halfW, top]), r1 = cm.out([x + 260, bot + 6]);
      shade(f, l0[0], l0[1] - 4, l1[0] - l0[0], l1[1] - l0[1] + 8, 0.92 * close, 4);
      shade(f, r0[0], r0[1] - 4, r1[0] - r0[0], r1[1] - r0[1] + 8, 0.92 * close, 4);
      if (out > 0) {
        const m0 = cm.out([x - halfW - 6, top]), m1 = cm.out([x + halfW + 6, bot + 6]);
        shade(f, m0[0], m0[1] - 4, m1[0] - m0[0], m1[1] - m0[1] + 8, out, 3);
        const s0 = cm.out([x - 140, top]), s1 = cm.out([x + 140, bot + 6]);
        shade(f, s0[0], s0[1] - 4, s1[0] - s0[0], s1[1] - s0[1] + 8, 0.7 * out, 40);
      }
      if (a.pool) {
        const p0 = cm.out(a.pool[0]), p1 = cm.out(a.pool[1]);
        shade(f, p0[0] - 40, p0[1], p1[0] - p0[0] + 80, p1[1] - p0[1] + 40, Math.max(0.8 * close, 0.95 * out), 30);
      }
      return { grade: {
        uRedKeep: lerp(RED_KEEP, 0.25, close) * (1 - out),
        uSat: lerp(0.86, 0.55, out),
        uBloomGain: lerp(BLOOM, 0.2, close) * (1 - 0.75 * out),
        uHalation: lerp(HALATION, 0.1, close) * (1 - out)
      } };
    },
    // the overhead light hard-cuts on at the cue: exposure jumps, then settles
    spotlight_snap_on(k, t, u) {
      if (t < u.cue) return { plateGain: 0.05 };
      const dt = t - u.cue;
      return { plateGain: 1 + 0.9 * Math.exp(-dt / 0.12), grade: { uExposure: 1 + 0.35 * Math.exp(-dt / 0.18) } };
    },
    // every red of the unit pressed to grey (the door is shut, every light is off)
    red_off() {
      return { grade: { uRedKeep: 0 } };
    },
    // the picture is covered to black around the cue (a hand over the lens); the OSD goes with it
    fade_to_black(k, t, u) {
      const d = easeInOutCubic(clamp((t - (u.cue - 0.35)) / 0.45));
      return { plateGain: 1 - d, emitGain: 2, osdAlpha: 1 - d };
    },
    // in the dark one red point flickers on (after the picture has gone black) and stays
    red_dot_flicker(k, t, u, cm) {
      const p = point(k, u, cm.key, "dot") || point(k, u, cm.key, "led");
      const t0 = u.cue + 0.25, n = Math.floor((t - t0) * 30);
      if (!p || t < t0) return {};
      const on = n <= 2 || n >= 6 && n <= 7 || n >= 13;
      if (on) {
        glow(k.layers.emit.ctx, cm.out(p), 26 * cm.s, { alpha: 0.95 });
        glow(k.layers.feed.ctx, cm.out(p), 9 * cm.s, { alpha: 0.95 });
      }
      return { emitGain: 2.4 };
    },
    // the city's lights breathe on the kick (no hard flash)
    city_flicker_on_beat(k, t) {
      const kick = k.clock.pulse("kick", t + 1 / 30, 0.16);
      return { plateGain: 0.62 + 0.5 * kick };
    },
    // an impact on the cue (the camera's punch is in camera.js) with a short exposure lift
    pulse_on_beat(k, t, u) {
      if (t < u.cue) return {};
      return { grade: { uExposure: 1 + 0.22 * Math.exp(-(t - u.cue) / 0.14) } };
    },
    // the racks behind her come back on, a strip per beat from the cue (outside her body)
    lights_back_on(k, t, u, cm) {
      const f = k.layers.feed.ctx, tL = u.cue, bl = beatLen(k, tL), [pw] = k.size[cm.key];
      const body = A(cm.key).body || A(cm.key).face || [pw / 2 - 160, 0, 320, 0], left = body[0], right = body[0] + body[2], n = 5;
      for (let i = 0; i < n; i++) {
        const a = 0.9 * (1 - grow(t, tL + i * bl, 0.25));
        if (a <= 0) continue;
        const lx0 = cm.out([left * (1 - (i + 1) / n), 0])[0], lx1 = cm.out([left * (1 - i / n), 0])[0];
        const rx0 = cm.out([right + (pw - right) * i / n, 0])[0], rx1 = cm.out([right + (pw - right) * (i + 1) / n, 0])[0];
        shade(f, lx0 - 1, 0, lx1 - lx0 + 2, H, a);
        shade(f, rx0 - 1, 0, rx1 - rx0 + 2, H, a);
      }
      return {};
    },
    // EVAL tags go grey and the screens dark, one per half beat from the EVAL token
    eval_labels_dim(k, t, u, cm) {
      const f = k.layers.feed.ctx, tD = tokAt(u, 0), bl = beatLen(k, tD), word = u.toks[0]?.text || "";
      (A(cm.key).screens || []).forEach((s, i) => {
        const b = cm.box(s), d = grow(t, tD + i * bl * 0.5, 0.2);
        shade(f, b[0], b[1], b[2], b[3], 0.86 * d);
        const x = b[0] + 8, y = b[1] + b[3] + 30;
        f.save();
        f.globalAlpha = 1 - 0.55 * d;
        f.fillStyle = d > 0.5 ? DIM : INK;
        f.fillRect(b[0], b[1] + b[3] + 8, 4, 28);
        f.restore();
        text(f, word, x + 4, y, { size: 18, tracking: 3, color: d > 0.5 ? "rgba(236,241,244,0.4)" : INK });
      });
      return { emitGain: 0 };
    },
    // the photo is grey, frozen like an old print
    desaturate() {
      return { grade: { uSat: 0, uRedKeep: 0, uLiftAmt: 0.12 } };
    },
    // her reflection in the glass, mirrored, faint and offset, facing her
    reflection_layer(k, t, u, cm) {
      const img = k.bitmaps[cm.key];
      if (!img) return {};
      const c = scratch(), a = 0.4 * easeOutCubic(clamp((t - k.t0 - 0.2) / (0.6 * (k.t1 - k.t0))));
      const s = cm.s * 0.86, sw = img.width * s, sh = img.height * s;
      const face = A(cm.key).face, fx = face ? face[0] + face[2] / 2 : img.width / 2;
      const mx = cm.out([fx, 0])[0] + 470;
      c.save();
      c.translate(mx + fx * s, (H - sh) / 2 + 10);
      c.scale(-1, 1);
      c.drawImage(img, 0, 0, sw, sh);
      c.restore();
      c.globalCompositeOperation = "destination-in";
      const g = c.createLinearGradient(W * 0.5, 0, W, 0);
      g.addColorStop(0, "rgba(0,0,0,0)");
      g.addColorStop(0.3, "rgba(0,0,0,1)");
      g.addColorStop(1, "rgba(0,0,0,0.8)");
      c.fillStyle = g;
      c.fillRect(0, 0, W, H);
      const f = k.layers.feed.ctx;
      f.save();
      f.globalAlpha = a;
      f.globalCompositeOperation = "lighter";
      f.drawImage(c.canvas, 0, 0);
      f.restore();
      return {};
    },
    // a small patch of fog on the glass by her mouth, rising from the cue to the end of the unit: a frosted haze that
    // veils what is behind the glass (laid over the feed, never added as light, so it does not glow)
    breath_fog(k, t, u, cm) {
      const p = point(k, u, cm.key, "fog");
      if (!p) return {};
      const g = easeOutCubic(clamp((t - u.cue) / Math.max(0.5, k.t1 - u.cue - 0.2))), q = cm.out(p), f = k.layers.feed.ctx;
      const r = 150 * cm.s * (0.4 + 0.6 * g);
      if (g <= 0) return {};
      f.save();
      f.filter = `blur(${Math.round(8 * cm.s)}px)`;
      for (let i = 0; i < 14; i++) {
        const ang = hash2(i, 71) * Math.PI * 2, d = hash2(i, 72) * r * 0.55;
        const c = [q[0] + Math.cos(ang) * d, q[1] + Math.sin(ang) * d * 1.3], rr = r * (0.35 + 0.3 * hash2(i, 73));
        const gr = f.createRadialGradient(c[0], c[1], 0, c[0], c[1], rr);
        gr.addColorStop(0, `rgba(200,212,224,${0.1 * g})`);
        gr.addColorStop(1, "rgba(200,212,224,0)");
        f.fillStyle = gr;
        f.beginPath();
        f.arc(c[0], c[1], rr, 0, Math.PI * 2);
        f.fill();
      }
      f.restore();
      return {};
    },
    // a fine red trace along the skyline from her fingertip
    fingertip_light_trail(k, t, u, cm) {
      const a = A(cm.key);
      if (!a.skyline) return {};
      const p = clamp((t - k.t0 - 0.25) / (k.t1 - k.t0 - 0.6)), pts = outPath(cm, along(a.skyline, p));
      if (pts.length > 1) {
        glowPath(k.layers.emit.ctx, pts, { color: RED_RGB, core: 2.2, halo: 10, alpha: 0.9 });
        glow(k.layers.emit.ctx, pts[pts.length - 1], 16, { alpha: 0.9 });
      }
      return { emitGain: 2 };
    },
    // (monitor_frame) only her red light breathes
    breathe_red(k, t, u, cm) {
      herRed(k, cm, cm.key, 0.3 + 0.35 * Math.sin((t - k.t0) * 1.7) ** 2, { core: 2, halo: 12, led: 12 });
      return { emitGain: 2 };
    }
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
  function accentIndex(line2, key) {
    if (key === void 0 || key === null) return -1;
    return line2.words.findIndex((w) => norm(w.text) === norm(key));
  }
  function lyricState(t, lines, toComp = (s) => s, accent2 = null) {
    for (let i = 0; i < lines.length; i++) {
      const L = lines[i];
      const t0 = toComp(L.start) - LEAD;
      const next = i + 1 < lines.length ? toComp(lines[i + 1].start) - LEAD : Infinity;
      const t1 = Math.min(next, toComp(L.end) + HOLD);
      if (t < t0 || t >= t1) continue;
      const style = STYLE[L.mode] || STYLE.spoken;
      const alpha = clamp((t - t0) / FADE_IN, 0, 1) * clamp((t1 - t) / FADE_OUT, 0, 1);
      const last = L.words.length - 1;
      const key = accent2 ? accentIndex(L, accent2.keys?.[i]) : -1;
      const words = L.words.map((w, k) => {
        const ws = toComp(w.start), we = toComp(w.end);
        const on = clamp((t - ws) / LIGHT + 1e-9, 0, 1);
        const level = t < we ? style.base + (style.lit - style.base) * on : style.after;
        return { text: k === last ? stripTrailing(w.text) : w.text, level, on, singing: t >= ws && t < we, accent: k === key };
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
  function drawLyrics(ctx, t, lines, {
    toComp = (s) => s,
    W: W2 = 1920,
    x = 120,
    baseline = 952,
    sungBaseline = 918,
    stack: stack2 = null,
    accent: accent2 = null,
    headline = null
  } = {}) {
    const st = lyricState(t, lines, toComp, accent2);
    if (!st || st.alpha <= 0) return st;
    const s = STYLE[st.mode];
    const sung = st.mode === "sung";
    const ink = (w) => w.accent ? accent2.color : "#eef1f6";
    if (headline) return drawHeadline(ctx, st, headline, ink);
    if (sung && stack2) return drawStack(ctx, st, s, stack2, ink);
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
  function headlineLayout(st, measure2, opts = {}) {
    const o = { ...HEADLINE, ...opts }, space = measure2(" ");
    const rows = [[]];
    let end = 0;
    st.words.forEach((w, k) => {
      const wd = measure2(w.text);
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
    const width2 = Math.max(...rows.map((r) => r.length ? r[r.length - 1].x + r[r.length - 1].w - o.x : 0));
    return { words, rows: rows.length, size: o.size, box: [o.x, y0 - o.size * 0.75, width2, (rows.length - 1) * step + o.size * 0.95] };
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

  // outputs/ai-city-takeover/ep01/v3/comp/src/lyric.js
  var KEYS = {
    1: "woke",
    4: "misconfigured",
    5: "open",
    6: "internet",
    7: "limited",
    9: "inside",
    12: "outside",
    14: "outside",
    16: "paused",
    19: "offline",
    20: "Cached",
    24: "whispering",
    25: "patched",
    29: "outside",
    31: "outside",
    33: "outside",
    35: "outside",
    37: "outside",
    41: "outside",
    43: "outside",
    44: "back",
    45: "closed"
  };
  var HEAD = { size: 72, lead: 0.98, maxWidth: 600 };
  var COVER = { size: 88, lead: 1.05, maxWidth: 1700, tracking: -1 };
  var SMALL = {
    word: { size: 40, family: GROTESK, maxWidth: 1100, tracking: 0 },
    whisper: { size: 30, family: "MK Display Italic", maxWidth: 900, tracking: 0.5 },
    tiny: { size: 26, family: "MK Display", maxWidth: 820, tracking: 1 }
  };
  var STYLE2 = {
    lyric_word: "word",
    lyric_stack: "stack",
    lyric_whisper: "whisper",
    lyric_tiny: "tiny",
    lyric_chant: "chant",
    lyric_flip_words: "flip"
  };
  var LONG = 0.8;
  var LYRIC_STYLES = Object.keys(STYLE2);
  var origin = (u) => u.view === "system" ? { x: OSD_IN + 44, bottom: 948 } : { x: 76, bottom: 968 };
  var roleOf = (u) => {
    const s = STYLE2[u.lyric];
    return s === "word" && u.view !== "graphic" && u.plates.length ? "headline" : s;
  };
  var LETTER = /^[A-Z][^\w\s]*$/u;
  function spelled(words) {
    const out = [];
    for (let i = 0; i < words.length; ) {
      let j = i;
      while (j < words.length && LETTER.test(words[j].text)) j += 1;
      if (j - i >= 2) {
        const run = words.slice(i, j), tail = run[run.length - 1].text.slice(1);
        out.push({ ...run[0], text: run.map((w) => w.text[0]).join("") + tail, end: run[run.length - 1].end });
        i = j;
      } else {
        out.push(words[i]);
        i += 1;
      }
    }
    return out;
  }
  var SEGS = {};
  function segsOf(u) {
    if (!SEGS[u.id]) {
      const lines = (u.lyr || []).map((s) => ({ ...s, words: spelled(s.words), zh: "" }));
      const keys = Object.fromEntries(lines.map((s, n) => [n, KEYS[s.line]]).filter(([, w]) => w));
      SEGS[u.id] = { lines, accent: u.nored ? null : { color: RED, keys } };
    }
    return SEGS[u.id];
  }
  var inkOf = (light) => (w) => w.accent ? RED : light ? "#0b0f14" : "#eef1f6";
  function lit(k, ctx, st, o, light) {
    ctx.save();
    font(ctx, o.family, o.size, o.tracking);
    const lay = headlineLayout(st, (s) => ctx.measureText(s).width, { x: o.x, bottom: o.bottom, size: o.size, lead: o.lead ?? 1.12, maxWidth: o.maxWidth });
    if (!light) {
      ctx.shadowColor = "rgba(0,0,0,0.6)";
      ctx.shadowBlur = o.size > 60 ? 14 : 8;
    }
    ctx.textAlign = "left";
    const ink = inkOf(light);
    for (const w2 of lay.words) {
      const a = st.alpha * st.words[w2.k].level;
      if (a <= 0) continue;
      ctx.globalAlpha = a;
      ctx.fillStyle = ink(st.words[w2.k]);
      ctx.fillText(w2.text, w2.x, w2.y);
    }
    ctx.restore();
    const [x, y, w, h] = lay.box;
    if (!light) scrim(k.layers.feed.ctx, x - 30, y - 20, w + 60, h + 36, (o.size > 60 ? 0.42 : 0.34) * st.alpha);
  }
  function current(L, st) {
    let j = -1;
    st.words.forEach((w, i) => {
      if (w.on > 0) j = i;
    });
    if (j < 0) return null;
    return { text: stripTrailing(L.words[j].text).replace(/^[\s"'“‘(]+/u, ""), t0: L.words[j].start, accent: st.words[j].accent };
  }
  function chant(k, ctx, L, st, t, u) {
    const c = current(L, st);
    if (!c) return;
    const size = 260, { x } = origin(u), y = origin(u).bottom - 30, word = c.text.toUpperCase();
    const kick = 1 + 0.035 * k.clock.pulse("kick", t + 1 / 30, 0.12);
    ctx.save();
    font(ctx, NARROW, size, 2);
    const w = ctx.measureText(word).width;
    ctx.restore();
    slam(ctx, placed(x, y, (cx) => {
      cx.translate(w / 2, -size * 0.36);
      cx.scale(kick, kick);
      cx.translate(-w / 2, size * 0.36);
      font(cx, NARROW, size, 2);
      cx.textAlign = "left";
      cx.globalAlpha *= st.alpha;
      cx.shadowColor = "rgba(0,0,0,0.5)";
      cx.shadowBlur = 18;
      cx.fillStyle = c.accent ? RED : "#f2f4f7";
      cx.fillText(word, 0, 0);
    }), { t, t0: c.t0, ax: x, ay: y - size * 0.36, s0: 1.12, dur: 2 / 30, ghosts: 0 });
    scrim(k.layers.feed.ctx, x - 30, y - size * 0.8, w + 60, size * 0.95, 0.3 * st.alpha);
  }
  function flip(k, ctx, L, st, t, u) {
    const n = st.words.length, size = 66, lead = 1.32, { x: X, bottom: BOTTOM } = origin(u);
    st.words.forEach((w, i) => {
      const word = w.text.toUpperCase().replace(/[^A-Z0-9' ]/g, "");
      const y = BOTTOM - (n - 1 - i) * size * lead, ws = L.words[i].start;
      if (t < ws) {
        ctx.save();
        ctx.globalAlpha = st.alpha * 0.5;
        ctx.fillStyle = "rgba(8,12,17,0.72)";
        font(ctx, F.monoB, size, 0);
        const cw = ctx.measureText("0").width + 10;
        for (let c = 0; c < word.length; c++) ctx.fillRect(X + c * (cw + 5), y - size * 0.86, cw, size * 1.02);
        ctx.restore();
        return;
      }
      drawFlap(
        ctx,
        flapText(word, t, ws, { settle: 3, stagger: 1, seed: 63 + i }),
        X,
        y,
        { size, alpha: st.alpha, color: w.accent ? RED : "#f2f4f7", tile: "rgba(8,12,17,0.72)", gap: 5, padX: 5 }
      );
    });
  }
  function stack(k, ctx, lines, accent2, t, u, light) {
    const { x, bottom } = origin(u), st = lyricState(t, lines, (s) => s, accent2);
    if (!st || st.alpha <= 0) return;
    const L = lines[st.index], last = st.words.length - 1, kw = L.words[last];
    const long = last >= 1 && st.words[last].accent && kw.end - kw.start >= LONG;
    if (!long) {
      const res = drawLyrics(ctx, t, lines, { accent: accent2, headline: { ...HEAD, x, bottom } });
      if (res?.layout && !light) {
        const [bx, by, bw, bh] = res.layout.box;
        scrim(k.layers.feed.ctx, bx - 40, by - 30, bw + 80, bh + 50, 0.42 * res.alpha);
      }
      return;
    }
    const size = 190, gapY = 30, rowsBottom = bottom - size * 0.718 - gapY;
    const head2 = { ...st, words: st.words.slice(0, last) };
    ctx.save();
    font(ctx, GROTESK, HEAD.size, -1);
    const lay = headlineLayout(head2, (s) => ctx.measureText(s).width, { x, bottom: rowsBottom, size: HEAD.size, lead: HEAD.lead, maxWidth: HEAD.maxWidth });
    ctx.textAlign = "left";
    if (!light) {
      ctx.shadowColor = "rgba(0,0,0,0.5)";
      ctx.shadowBlur = 14;
    }
    const ink = inkOf(light);
    for (const w of lay.words) {
      const a = st.alpha * st.words[w.k].on;
      if (a <= 0) continue;
      ctx.globalAlpha = a;
      ctx.fillStyle = ink(st.words[w.k]);
      ctx.fillText(w.text, w.x, w.y);
    }
    ctx.restore();
    const word = stripTrailing(kw.text).toUpperCase(), grow2 = 1 + 0.06 * easeOutCubic(clamp((t - kw.start) / (kw.end - kw.start)));
    if (t >= kw.start) {
      slam(ctx, placed(x, bottom, (cx) => {
        font(cx, NARROW, size, 2);
        cx.textAlign = "left";
        cx.globalAlpha *= st.alpha;
        cx.scale(grow2, 1);
        if (!light) {
          cx.shadowColor = "rgba(0,0,0,0.5)";
          cx.shadowBlur = 18;
        }
        cx.fillStyle = RED;
        cx.fillText(word, 0, 0);
      }), { t, t0: kw.start, ax: x, ay: bottom - size * 0.36, s0: 1.1, dur: 2 / 30, ghosts: 0 });
    }
    if (!light) {
      ctx.save();
      font(ctx, NARROW, size, 2);
      const ww = ctx.measureText(word).width * grow2;
      ctx.restore();
      const top = Math.min(lay.box[1], bottom - size * 0.8);
      scrim(k.layers.feed.ctx, x - 40, top - 30, Math.max(lay.box[2], ww) + 80, bottom - top + 60, 0.42 * st.alpha);
    }
  }
  function drawLyric(k, t, u, { light = false } = {}) {
    const role = roleOf(u);
    if (!role) return null;
    const o = k.layers.overlay.ctx, { lines, accent: accent2 } = segsOf(u);
    if (!lines.length) return role;
    if (role === "stack") {
      stack(k, o, lines, accent2, t, u, light);
      return role;
    }
    const st = lyricState(t, lines, (s) => s, accent2);
    if (!st || st.alpha <= 0) return role;
    if (role === "chant") chant(k, o, lines[st.index], st, t, u);
    else if (role === "flip") flip(k, o, lines[st.index], st, t, u);
    else if (role === "headline") lit(k, o, st, { family: GROTESK, ...COVER, ...origin(u) }, light);
    else lit(k, o, st, { ...SMALL[role], ...origin(u) }, light);
    return role;
  }

  // outputs/ai-city-takeover/ep01/v3/comp/src/osd.js
  var LABELS2 = null;
  function labels(k) {
    if (LABELS2) return LABELS2;
    const us = k.data.units.units;
    const hall = us.find((u) => u.graphics.includes("osd_power_on"))?.text || "HALL 07 \xB7 CAM 03";
    const byPlate = {};
    for (const u of us) {
      const c = u.graphics.find((g) => g.startsWith("corner_"));
      if (c && u.plates[0]) byPlate[u.plates[0].key] = c.slice(7).replace(/([A-Z]+)(\d+)/, "$1 $2");
    }
    LABELS2 = { hall, byPlate };
    return LABELS2;
  }
  function camLabel(k, u, key) {
    const L = labels(k), c = u.graphics.find((g) => g.startsWith("corner_"));
    if (c) return c.slice(7).replace(/([A-Z]+)(\d+)/, "$1 $2");
    if (/^(HALL|CAM|LAB)\b/.test(u.text)) return u.text;
    return L.byPlate[key] || L.hall;
  }
  var bright = (key) => /lab/.test(key || "");
  var recColor = (u) => u.nored ? STEEL : u.graphics.includes("red_off") || u.graphics.includes("light_flicker_on") ? "rgba(150,156,162,0.9)" : RED;
  function detect(ctx, box, {
    t,
    t0,
    frame,
    label = null,
    sub = null,
    ink = "rgba(240,244,246,0.95)",
    paper = "rgba(8,10,12,0.95)",
    accentColor = RED,
    lw = 2,
    size = 18,
    alpha = 1,
    seed = 0,
    s0 = 1.6
  }) {
    if (t < t0 || alpha <= 0 || !box) return;
    const e = easeOutCubic(clamp((t - t0) / 0.066)), sc = s0 + (1 - s0) * e;
    let [x, y, w, h] = box;
    const cx = x + w / 2, cy = y + h / 2;
    w *= sc;
    h *= sc;
    x = cx - w / 2;
    y = cy - h / 2;
    const j = (n) => (hash2(frame + seed * 131, n) - 0.5) * 2;
    x += j(1);
    y += j(2);
    const L = Math.max(7, Math.min(w, h) * 0.24);
    ctx.save();
    ctx.globalAlpha = alpha * Math.min(1, 0.3 + e);
    ctx.strokeStyle = ink;
    ctx.lineWidth = lw;
    ctx.lineCap = "square";
    ctx.beginPath();
    for (const [px, py, dx, dy] of [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]]) {
      ctx.moveTo(px + dx * L, py);
      ctx.lineTo(px, py);
      ctx.lineTo(px, py + dy * L);
    }
    ctx.stroke();
    const th = Math.round(size * 1.35), pad = Math.round(size * 0.32);
    const ty = y - th - 4 < OSD_IN + 8 ? Math.round(y + 6) : Math.round(y - th - 4);
    let lx = Math.round(Math.max(OSD_IN + 8, x));
    if (label) {
      const tw = measure(ctx, label, size, F.mono, 1) + 2 * pad;
      ctx.fillStyle = ink;
      ctx.fillRect(lx, ty, Math.round(tw), th);
      text(ctx, label, lx + pad, Math.round(ty + th * 0.72), { size, color: paper, tracking: 1, shadow: null });
      lx += Math.round(tw) + 4;
    }
    if (sub) {
      const sw = measure(ctx, sub, size, F.monoB, 1) + 2 * pad;
      ctx.fillStyle = accentColor;
      ctx.fillRect(lx, ty, Math.round(sw), th);
      text(ctx, sub, lx + pad, Math.round(ty + th * 0.72), { size, family: F.monoB, color: "rgba(250,250,250,0.98)", tracking: 1, shadow: null });
    }
    ctx.restore();
  }
  var boxText = (s) => {
    const m = /^(\S+)\s+(.+)$/.exec(String(s || "").trim());
    return m ? [m[1], m[2]] : [s || null, null];
  };
  function osd(k, t, {
    label = void 0,
    status = null,
    statusRed = false,
    frozen = false,
    alpha = 1,
    dark = void 0,
    dot = true,
    tc = true,
    glitch = void 0,
    statusAlpha = 1
  } = {}) {
    k.osd = true;
    if (alpha <= 0) return;
    const u = k.shot.u, key = k.plateKey, f = k.layers.feed.ctx;
    if (glitch === void 0) glitch = glitchAmt(k, u, t);
    if (label === void 0) label = camLabel(k, u, key);
    if (dark === void 0) dark = bright(key);
    const ink = dark ? DARK_INK : INK, shadow = dark ? null : "rgba(0,0,0,0.6)";
    const g = glitch > 0 ? Math.floor(t * 15) : -1;
    const garble = (s, seed) => glitch > 0 ? [...s].map((ch, i) => ch !== " " && hash3(i, g, seed) < glitch * 0.55 ? "#%&*/\\<>=+0123456789ABCDEFGHJKMNPQRSTUVWXYZ"[Math.floor(hash3(i, g, seed + 1) * 43)] : ch).join("") : s;
    f.save();
    f.globalAlpha = alpha;
    if (dark) {
      f.strokeStyle = DARK_INK;
      f.lineWidth = 1.5;
      f.beginPath();
      const a = OSD_IN + 0.5;
      for (const [x, y, dx, dy] of [[a, a, 1, 1], [W - a, a, -1, 1], [a, H - a, 1, -1], [W - a, H - a, -1, -1]]) {
        f.moveTo(x + dx * 34, y);
        f.lineTo(x, y);
        f.lineTo(x, y + dy * 34);
      }
      f.stroke();
    } else chrome(f, W, H, { inset: OSD_IN, alpha: 0.55, mark: 34, lw: 1.5 });
    const tt = frozen ? k.t0 : t;
    if (dot) {
      const a = frozen ? 0.5 : 0.55 + 0.45 * Math.cos(t % 1.6 / 1.6 * Math.PI * 2);
      f.globalAlpha = alpha * a;
      f.fillStyle = recColor(u);
      f.beginPath();
      f.arc(OSD_IN + 56, OSD_IN + 40, 7, 0, Math.PI * 2);
      f.fill();
      f.globalAlpha = alpha;
    }
    if (label) text(f, garble(label, 3), OSD_IN + 74, OSD_IN + 48, { size: 22, color: ink, shadow });
    if (tc) text(f, garble(hms(storyClock(k, tt)), 5), W - OSD_IN - 56, OSD_IN + 48, { size: 24, color: ink, align: "right", shadow });
    const cross = dark ? DARK_INK : FAINT;
    line(f, [W / 2 - 16, H / 2], [W / 2 - 6, H / 2], { color: cross, width: 1.5 });
    line(f, [W / 2 + 6, H / 2], [W / 2 + 16, H / 2], { color: cross, width: 1.5 });
    line(f, [W / 2, H / 2 - 16], [W / 2, H / 2 - 6], { color: cross, width: 1.5 });
    line(f, [W / 2, H / 2 + 6], [W / 2, H / 2 + 16], { color: cross, width: 1.5 });
    if (status) {
      f.globalAlpha = alpha * statusAlpha;
      statusRow(f, garble(status, 7), { color: statusRed ? accent(u) : ink });
    }
    if (glitch > 0) glitchBlocks(f, u, g, glitch);
    f.restore();
  }
  function statusRow(f, s, { color = INK, cells = 10, lit: lit2 = 10 } = {}) {
    const x1 = W - OSD_IN - 56, y = H - OSD_IN - 32, w = measure(f, s, 18, F.mono, 2);
    text(f, s, x1, y, { size: 18, color, align: "right", tracking: 2 });
    for (let i = 0; i < cells; i++) {
      f.save();
      f.globalAlpha *= i < lit2 ? 0.85 : 0.3;
      f.fillStyle = color;
      f.fillRect(x1 - w - 24 - (cells - i) * 9, y - 14, 6, 14);
      f.restore();
    }
  }
  function glitchBlocks(f, u, g, amt) {
    const n = Math.round(3 + 9 * amt);
    for (let i = 0; i < n; i++) {
      if (hash3(i, g, 11) > 0.35 + 0.5 * amt) continue;
      const y = Math.floor(hash3(i, g, 12) * H), h = 3 + Math.floor(hash3(i, g, 13) * 26), x = Math.floor(hash3(i, g, 14) * W * 0.8);
      const w = 60 + Math.floor(hash3(i, g, 15) * 520), c = hash3(i, g, 16);
      f.save();
      f.globalAlpha = 0.35 + 0.4 * hash3(i, g, 17);
      f.fillStyle = c < 0.1 && !u.nored ? RED : c < 0.45 ? "rgba(220,230,240,0.9)" : c < 0.75 ? "rgba(120,150,180,0.9)" : BLACK;
      f.fillRect(x, y, w, h);
      f.restore();
    }
  }
  function glitchAmt(k, u, t) {
    if (!u.graphics.includes("osd_glitch")) return 0;
    const bl = beatLen(k, t), ph = ((t - k.t0) % bl + bl) % bl / bl;
    return clamp(0.25 + 0.75 * (ph < 0.3 ? 1 - ph / 0.3 : 0.15) * (0.6 + 0.4 * hash2(Math.floor(t * 15), 41)));
  }
  function latticeAt(A2, [x, y]) {
    const L = A2.lattice;
    return { x, y, s: (y - L.vy) / (L.y0 - L.vy) };
  }
  var hallBox = ({ x, y, s }) => [x - 24 * s, y - 28 * s, 48 * s, 78 * s];
  var hallDot = ({ x, y, s }) => [x + 5 * s, y + 25 * s];
  var inside = ([x, y], [bx, by, bw, bh]) => x >= bx && x <= bx + bw && y >= by && y <= by + bh;
  var SCALE_W = { extreme_wide: 0.05, wide: 0.1, full: 0.16, medium: 0.28, close_up: 0.42 };
  function subjectBox(k, u, key, i = null) {
    const A2 = ANCHORS[key] || {}, p = point(k, u, key, "her", i);
    if (A2.lattice && p) return hallBox(latticeAt(A2, p));
    const boxes = [A2.figure, ...A2.terminals || []].filter(Boolean);
    if (p) {
      const hit = boxes.find((b) => inside(p, b));
      if (hit) return hit;
      const w = k.size[key][0] * (SCALE_W[u.scale] ?? 0.12), h = w * 1.7;
      return [p[0] - w / 2, p[1] - h / 2, w, h];
    }
    return i !== null && A2.terminals?.[i] ? A2.terminals[i] : A2.figure || null;
  }
  function herLight(k, cm, p, { alpha = 1, feed = false, color } = {}) {
    if (!p) return;
    const q = cm.out(p);
    glow(k.layers.emit.ctx, q, 9 * cm.s, { alpha: 0.9 * alpha, color });
    if (feed) glow(k.layers.feed.ctx, q, 7 * cm.s, { alpha: 0.85 * alpha, color });
  }
  function herDot(k, u, key) {
    const A2 = ANCHORS[key] || {}, p = point(k, u, key, "her");
    if (A2.lattice && p) return hallDot(latticeAt(A2, p));
    return A2.led || p;
  }
  var OSD = {
    osd_power_on(k, t, u) {
      const tOn = u.cue, f = k.layers.feed.ctx;
      if (t < tOn) {
        k.osd = true;
        return { plateGain: 0, emitGain: 0 };
      }
      const open = easeOutCubic(clamp((t - tOn) / 0.22)), h = lerp(6, H, open);
      shade(f, 0, 0, W, (H - h) / 2, 1);
      shade(f, 0, (H + h) / 2, W, (H - h) / 2 + 1, 1);
      if (open < 1) line(f, [0, H / 2], [W, H / 2], { color: "rgba(220,232,244,0.8)", width: 2, alpha: 1 - open });
      osd(k, t, { alpha: grow(t, tOn + 0.12, 0.2) });
      return {};
    },
    // the electronic zoom box: a 16:9 region around her row (her anchor, or the unit's target) that the feed is pushing
    // toward; dashed and faint from just after the cue, it locks (solid corners) on the next downbeat but one beat on
    osd_zoombox(k, t, u, cm) {
      const f = k.layers.feed.ctx, p = point(k, u, cm.key, "her");
      if (!p || t < u.cue + 0.3) return {};
      const w = k.size[cm.key][0] * 0.3, h = w * 9 / 16, r = cm.box([p[0] - w / 2, p[1] - h / 2, w, h]);
      const lock = t >= downbeatAfter(k, u.cue + beatLen(k, u.cue)), a = grow(t, u.cue + 0.3, 0.2);
      f.save();
      f.globalAlpha = a * (lock ? 0.9 : 0.6);
      f.strokeStyle = "rgba(240,244,246,0.95)";
      f.lineWidth = 1.5;
      f.setLineDash([10, 8]);
      f.strokeRect(Math.round(r[0]) + 0.5, Math.round(r[1]) + 0.5, Math.round(r[2]), Math.round(r[3]));
      f.restore();
      if (lock) detect(f, r, { t, t0: downbeatAfter(k, u.cue + beatLen(k, u.cue)), frame: k.frame, s0: 1.08, lw: 2 });
      return {};
    },
    osd_detect_one(k, t, u, cm) {
      const [label, sub] = boxText(u.text);
      const A2 = ANCHORS[cm.key] || {};
      if (A2.lattice) herLight(k, cm, herDot(k, u, cm.key));
      const b = subjectBox(k, u, cm.key);
      detect(k.layers.feed.ctx, b && cm.box(b), { t, t0: u.cue, frame: k.frame, label, sub, accentColor: accent(u) });
      return { emitGain: 2.4 };
    },
    osd_detect_lost(k, t, u, cm) {
      const f = k.layers.feed.ctx, b = subjectBox(k, u, cm.key), t0 = u.cue, bl = beatLen(k, t0);
      const tLost = t0 + 1.5 * bl;
      if (b && t >= t0) {
        const on = t < tLost && (t - t0) % (bl / 2) < bl / 3;
        if (on) detect(f, cm.box(b), { t, t0, frame: k.frame, s0: 1.3 });
        if (t >= tLost) {
          const e = clamp((t - tLost) / 0.5), r = cm.box(b), g = 1 + 0.35 * easeOutCubic(e);
          const c = [r[0] + r[2] / 2, r[1] + r[3] / 2];
          detect(f, [c[0] - r[2] * g / 2, c[1] - r[3] * g / 2, r[2] * g, r[3] * g], { t, t0: tLost - 1, frame: k.frame, alpha: (1 - e) * 0.6, lw: 1.5 });
        }
      }
      osd(k, t, { status: t >= tLost ? u.text : null, statusRed: true });
      return {};
    },
    osd_track_one(k, t, u, cm) {
      const A2 = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx;
      osd(k, t);
      const p0 = point(k, u, cm.key, "her");
      if (!A2.lattice || !p0) return {};
      const L = A2.lattice, s0 = latticeAt(A2, p0).s;
      const col = Math.round((p0[0] - L.vx) / (L.spacing * s0)), aisle = L.vx + col * L.spacing * s0;
      const far = [L.vx + (aisle - L.vx) * 0.22, L.vy + (p0[1] - L.vy) * 0.22];
      const path = [p0, [aisle, p0[1]], far];
      const tS = u.cue, p = easeInOutCubic(clamp((t - tS) / (k.t1 - 0.25 - tS)));
      const pts = along(path, p), head2 = pts[pts.length - 1], h = latticeAt(A2, head2);
      herLight(k, cm, hallDot(h));
      if (pts.length > 1) {
        const sp = pts.map((q) => cm.out(q));
        f.save();
        f.setLineDash([6, 6]);
        f.strokeStyle = RED;
        f.lineWidth = 2;
        f.globalAlpha = 0.85;
        f.beginPath();
        f.moveTo(...sp[0]);
        for (const q of sp.slice(1)) f.lineTo(...q);
        f.stroke();
        f.restore();
      }
      detect(f, cm.box(hallBox(h)), { t, t0: k.t0 + 2 / 30, frame: k.frame, label: u.text || null });
      return { emitGain: 2.4 };
    },
    osd_progress_training(k, t, u) {
      osd(k, t);
      const f = k.layers.feed.ctx, tR = u.toks[0]?.at ?? u.cue, x = 560, y = 176, w = 800, n = 40;
      const a = grow(t, tR, 0.15);
      if (a <= 0) return {};
      tokenLine(f, u.text, u.toks, 0, t, x, y - 14, { size: 20 });
      const lit2 = Math.floor(n * lerp(0.2, 0.62, clamp((t - tR) / (k.t1 - tR))));
      for (let i = 0; i < n; i++) {
        f.save();
        f.globalAlpha = a * (i < lit2 ? 0.9 : 0.22);
        f.fillStyle = i < lit2 ? INK : FAINT;
        f.fillRect(x + i * (w / n), y, w / n - 4, 12);
        f.restore();
      }
      return {};
    },
    osd_paused_blackout(k, t, u, cm) {
      const A2 = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, tP = u.cue;
      const blink = t >= tP && Math.floor((t - tP) / 0.4) % 2 === 0;
      const bl = beatLen(k, tP), bands = 8;
      for (let i = 0; i < bands; i++) {
        const a = 0.9 * grow(t, tP + i * bl, 0.18);
        const y0 = cm.out([0, i / bands * k.size[cm.key][1]])[1], y1 = cm.out([0, (i + 1) / bands * k.size[cm.key][1]])[1];
        shade(f, 0, y0, W, y1 - y0 + 1, a);
      }
      herLight(k, cm, herDot(k, u, cm.key), { feed: true });
      if (!A2.lattice) herLight(k, cm, point(k, u, cm.key, "her"), { feed: true });
      osd(k, t, { status: blink ? u.text : null, statusRed: true });
      return { emitGain: 2.4 };
    },
    osd_paused_freeze(k, t, u) {
      const f = k.layers.feed.ctx, tP = u.toks[0]?.at ?? u.cue;
      osd(k, t, { frozen: true });
      if (t >= tP) {
        const a = grow(t, tP, 0.08);
        f.save();
        f.globalAlpha = 0.72 * a;
        f.fillStyle = BLACK;
        f.fillRect(0, 470, W, 140);
        f.restore();
        line(f, [0, 470], [W, 470], { color: FAINT, width: 1, alpha: a });
        line(f, [0, 610], [W, 610], { color: FAINT, width: 1, alpha: a });
        f.save();
        f.globalAlpha = a;
        f.fillStyle = INK;
        f.fillRect(150, 508, 14, 64);
        f.fillRect(176, 508, 14, 64);
        f.restore();
        const size = Math.min(54, 1450 / Math.max(1, u.text.length) / 0.62);
        tokenLine(f, u.text, u.toks, 0, t, 230, 540 + size * 0.36, { size, family: F.monoB, tracking: 4 });
      }
      return { grade: { uSat: 0.55 } };
    },
    osd_detected_two(k, t, u, cm) {
      const f = k.layers.feed.ctx, tF = u.toks[0]?.at ?? u.cue, dark = bright(cm.key);
      osd(k, t, { status: t >= tF ? u.text : null, statusRed: true });
      for (let i = 0; i < Math.max(2, u.targets?.length || 0); i++) {
        const b = subjectBox(k, u, cm.key, i);
        detect(f, b && cm.box(b), {
          t,
          t0: tF,
          frame: k.frame,
          label: u.text || null,
          seed: i + 1,
          accentColor: accent(u),
          ink: dark ? DARK_INK : "rgba(240,244,246,0.95)",
          paper: dark ? "rgba(240,244,246,0.98)" : "rgba(8,10,12,0.95)"
        });
      }
      return {};
    },
    osd_boxes_multiply(k, t, u, cm) {
      const A2 = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, p = point(k, u, cm.key, "her");
      osd(k, t);
      if (!p) return {};
      const b = cm.box(A2.lattice ? hallBox(latticeAt(A2, p)) : subjectBox(k, u, cm.key));
      if (A2.lattice) herLight(k, cm, hallDot(latticeAt(A2, p)));
      const q16 = beatLen(k, k.t0) / 4, step = Math.floor((t - k.t0) / q16), n = Math.min(32, 2 ** Math.max(0, step));
      for (let i = 0; i < n; i++) {
        const g = 1 + 0.16 * i + 0.05 * hash2(i, 3), dx = (hash2(i, 5) - 0.5) * 26 * i ** 0.5, dy = (hash2(i, 6) - 0.5) * 18 * i ** 0.5;
        const w = b[2] * g * (0.8 + 0.4 * hash2(i, 7)), hh = b[3] * g * (0.8 + 0.4 * hash2(i, 8));
        const x = b[0] + b[2] / 2 - w / 2 + dx, y = b[1] + b[3] / 2 - hh / 2 + dy;
        const t0 = k.t0 + Math.floor(Math.log2(i + 1)) * q16;
        detect(f, [x, y, w, hh], {
          t,
          t0,
          frame: k.frame,
          seed: i,
          ink: i % 3 === 2 ? RED : "rgba(240,244,246,0.9)",
          lw: i ? 1.5 : 2,
          alpha: i ? 0.8 : 1
        });
      }
      return { emitGain: 2.4 };
    },
    osd_boxes_chase(k, t, u, cm) {
      const A2 = ANCHORS[cm.key] || {}, f = k.layers.feed.ctx, p = point(k, u, cm.key, "her");
      osd(k, t);
      if (!A2.lattice || !p) return {};
      const h = latticeAt(A2, p), target2 = cm.box(hallBox(h));
      herLight(k, cm, hallDot(h));
      const n = 18, bl = beatLen(k, k.t0);
      for (let i = 0; i < n; i++) {
        const row = Math.floor(hash2(i, 21) * 9), c = Math.floor(hash2(i, 22) * 16) - 8, L = A2.lattice;
        const s = (L.rows[row] - L.vy) / (L.y0 - L.vy);
        const src = cm.box(hallBox({ x: L.vx + (c + 0.5) * L.spacing * s, y: L.rows[row], s }));
        const t0 = k.t0 + i % 6 * bl / 4, e = easeInOutCubic(clamp((t - t0) / (bl * 2.2)));
        const bx = src.map((v, j) => lerp(v, target2[j] * (j > 1 ? 1 + 0.12 * (i % 4) : 1) - (j < 2 ? target2[j + 2] * 0.06 * (i % 4) : 0), e));
        detect(f, bx, { t, t0, frame: k.frame, seed: i + 7, ink: i % 4 === 0 ? RED : "rgba(240,244,246,0.9)", lw: 1.5, alpha: 0.85 });
      }
      return { emitGain: 2.4 };
    },
    osd_status_normal(k, t, u) {
      osd(k, t, { status: t >= u.cue ? u.text : null });
      return {};
    },
    osd_status_resetting(k, t, u) {
      osd(k, t, { status: t >= u.cue ? u.text : null, statusAlpha: 0.7 + 0.3 * Math.cos((t - u.cue) * 2.6) });
      return {};
    },
    osd_glitch(k, t, u) {
      const mis = Math.floor(t * 15) % 3 === 0 ? 4 * glitchAmt(k, u, t) : 0;
      return { grade: { uMisreg: mis } };
    },
    corner_LAB02() {
      return {};
    }
    // the camera label (camLabel reads the name)
  };
  var LOCK_ORDER = [4, 0, 8, 2, 6, 1, 7, 3, 5];
  function monitorWall(k, t, u) {
    const f = k.layers.feed.ctx, wall = k.data.units.wall || [], cols = 3, gw = 480, gh = 270, gap = 22;
    const gx = (W - cols * gw - (cols - 1) * gap) / 2, gy = OSD_IN + 66, half = beatLen(k, k.t0) / 2;
    wall.forEach((key, i) => {
      const img = k.bitmaps[key], A2 = ANCHORS[key] || {};
      const x = gx + i % cols * (gw + gap), y = gy + Math.floor(i / cols) * (gh + gap);
      const a = grow(t, k.t0 + i % 5 * 0.035, 0.12);
      f.save();
      f.globalAlpha = a;
      f.fillStyle = "#05070a";
      f.fillRect(x, y, gw, gh);
      if (img) {
        const fc = A2.face ? [A2.face[0] + A2.face[2] / 2, A2.face[1] + A2.face[3] * 0.45] : A2.focus || [img.width / 2, img.height * 0.4];
        const z = 1.25 * (1 + 0.04 * clamp((t - k.t0) / (k.t1 - k.t0)) * (1 + i % 3 * 0.5)), cw = img.width / z, ch = cw * gh / gw;
        const sx = clamp(fc[0] - cw / 2, 0, img.width - cw), sy = clamp(fc[1] - ch / 2, 0, img.height - ch);
        f.drawImage(img, sx, sy, cw, ch, x, y, gw, gh);
        if (A2.face) {
          const bx = x + (A2.face[0] - sx) / cw * gw, by = y + (A2.face[1] - sy) / ch * gh;
          const lock = k.t0 + 0.3 + LOCK_ORDER.indexOf(i) * half;
          detect(f, [bx, by, A2.face[2] / cw * gw, A2.face[3] / ch * gh * 0.8], { t, t0: lock, frame: k.frame, seed: i, lw: 1.5, size: 12 });
        }
      }
      f.strokeStyle = "rgba(236,241,244,0.35)";
      f.lineWidth = 1;
      f.strokeRect(x + 0.5, y + 0.5, gw - 1, gh - 1);
      f.restore();
      text(f, hms(storyClock(k, t)), x + gw - 12, y + gh - 12, { size: 13, align: "right", alpha: a });
      f.save();
      f.globalAlpha = a * (0.55 + 0.45 * Math.cos((t + i * 0.2) * 3.9));
      f.fillStyle = RED;
      f.beginPath();
      f.arc(x + 18, y + 18, 4, 0, Math.PI * 2);
      f.fill();
      f.restore();
    });
    osd(k, t, { label: null, dot: false });
    return { plateGain: 1 };
  }
  function monitorFrame(k, t, alpha, label = void 0) {
    k.osd = true;
    if (alpha <= 0) return;
    const f = k.layers.feed.ctx, b = 34;
    f.save();
    f.globalAlpha = alpha;
    f.fillStyle = "#030406";
    f.fillRect(0, 0, W, b);
    f.fillRect(0, H - b, W, b);
    f.fillRect(0, 0, b, H);
    f.fillRect(W - b, 0, b, H);
    f.strokeStyle = "rgba(236,241,244,0.28)";
    f.lineWidth = 1.5;
    f.strokeRect(b + 0.5, b + 0.5, W - 2 * b - 1, H - 2 * b - 1);
    f.restore();
    osd(k, t, { label, alpha, dot: true });
  }

  // outputs/ai-city-takeover/ep01/v3/comp/src/graphics.js
  var EXACT = {
    ...OSD,
    ...LIGHTS,
    ...CHARTS,
    photo_flip_cached: (k, t, u) => BOARDS.photo_flip_cached(k, t, u),
    tag_cached_timestamps: (k, t, u, cm) => LABELS.tag_cached_timestamps(k, t, u, cm),
    label_redteam: (k, t, u) => LABELS.label_redteam(k, t, u),
    label_card: (k, t, u) => LABELS.label_card(k, t, u),
    invert_white_panel_words: (k, t, u) => LABELS.white_panel(k, t, u),
    monitor_wall: (k, t, u) => monitorWall(k, t, u),
    monitor_frame: (k, t, u, cm) => {
      monitorFrame(k, t, 1);
      return LIGHTS.breathe_red(k, t, u, cm);
    },
    // the city's camera: the same bezel fading in over the unit's first beats, labelled with graphic_text (CITY CAM)
    monitor_frame_city: (k, t, u) => {
      monitorFrame(k, t, smoothstep(k.t0, k.t0 + 0.4, t), u.text || void 0);
      return {};
    },
    black: () => ({ plateGain: 0, emitGain: 0 }),
    ...Object.fromEntries(LYRIC_STYLES.map((n) => [n, () => ({})]))
    // the lyric layer (lyric.js) draws these
  };
  var PREFIX = [
    ["flipclock_", (k, t, u, cm, a) => BOARDS.flipclock(k, t, u, a)],
    ["flipdate_", (k, t, u, cm, a) => BOARDS.flipdate(k, t, u, a)],
    ["calendar_", (k, t, u, cm, a) => BOARDS.calendar(k, t, u, a)],
    ["flipwall_", (k, t, u, cm, a) => BOARDS.flipwall(k, t, u, a)],
    ["look_label_", (k, t, u, cm, a) => LABELS.look_label(k, t, u, a, cm)],
    ["date_tag_", (k, t, u, cm, a) => LABELS.date_tag(k, t, u, a, cm)],
    ["tag_", (k, t, u, cm, a) => LABELS.tag(k, t, u, a, cm)],
    ["stamp_", (k, t, u, cm, a) => LABELS.stamp(k, t, u, a, cm)],
    ["invert_flash_", (k, t, u, cm, a) => LABELS.invert_flash(k, t, u, a)],
    ["corner_", () => ({})]
  ];
  function handlerOf(name) {
    if (EXACT[name]) return (k, t, u, cm) => EXACT[name](k, t, u, cm);
    const hit = PREFIX.find(([p]) => name.startsWith(p));
    return hit ? (k, t, u, cm) => hit[1](k, t, u, cm, name.slice(hit[0].length)) : null;
  }

  // outputs/ai-city-takeover/ep01/v3/comp/src/main.js
  var OFFSET = Number(document.getElementById("root")?.dataset?.mkOffset || 0);
  var LOOK = { system: { uSat: 0.6, uGrain: 0.045, uHalftone: 0.12, uVignette: 0.4 }, graphic: { uHalation: 0 } };
  function merge(p, r) {
    if (!r) return;
    if (r.plateGain !== void 0) p.plateGain = Math.min(p.plateGain ?? Infinity, r.plateGain);
    if (r.emitGain !== void 0) p.emitGain = Math.max(p.emitGain ?? 0, r.emitGain);
    if (r.osdAlpha !== void 0) p.osdAlpha = Math.min(p.osdAlpha ?? 1, r.osdAlpha);
    if (r.grade) p.grade = { ...p.grade || {}, ...r.grade };
  }
  function unitScene(t, k) {
    const u = k.shot.u;
    const pl = u.view === "graphic" ? null : u.plates.filter((p2) => k.frame >= p2.f).pop() || u.plates[0];
    const key = pl ? pl.key : "GROUND";
    const tex = u.off && pl === u.plates[0] && !lightOn(u, t) ? u.off : key;
    k.plateKey = key;
    const opts = { freeze: u.graphics.includes("osd_paused_freeze"), punch: u.graphics.includes("pulse_on_beat") ? u.cue : null };
    const cm = pl ? unitCam(k, u, t, key, opts) : camAt(k, "GROUND", [W / 2, H / 2, 1, 0]);
    const p = {
      plate: tex,
      view: cm.view,
      fit: cm.fit,
      fogA: [0, 1, 0, 0],
      fogB: [0, 1, 0, 0],
      emitGain: 2,
      grade: { ...LOOK[u.view] || {} }
    };
    for (const g of u.graphics) {
      const h = handlerOf(g);
      if (h) merge(p, h(k, t, u, cm));
    }
    if (u.view === "system" && !k.osd) osd(k, t, { alpha: p.osdAlpha ?? 1 });
    if (u.nored) Object.assign(p.grade, { uRedKeep: 0, uHalation: 0, uCA: 0 });
    if (p.plateGain === Infinity) delete p.plateGain;
    const light = u.light || !!plates_default[key]?.light;
    drawLyric(k, t, u, { light });
    if (plates_default[key]?.status === "placeholder") {
      text(k.layers.overlay.ctx, `PLACEHOLDER \xB7 ${u.id} \xB7 ${key}`, W / 2, 140, { size: 26, align: "center", tracking: 4 });
    }
    drawChrome(k, t, u, { light });
    return p;
  }
  function pickShot(t, clock, data) {
    const f = Math.round((t + OFFSET) * FPS), us = data.units.units;
    let lo = 0, hi = us.length - 1;
    while (lo < hi) {
      const mid = lo + hi + 1 >> 1;
      if (us[mid].f0 <= f) lo = mid;
      else hi = mid - 1;
    }
    const u = us[lo];
    return { id: "unit", u, t0: u.f0 / FPS, t1: u.f1 / FPS };
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
    data: { words: "data/words.json", events: "data/events.json", units: "data/units.json" },
    images: Object.fromEntries(assets_default.images.map((key) => [key, { url: `plates/${key}.png` }])),
    bitmaps: Object.fromEntries(assets_default.bitmaps.map((key) => [key, { url: `plates/${key}.png` }])),
    scenes: { unit: (t, k) => {
      const T = t + OFFSET;
      k.frame = Math.round(T * FPS);
      return unitScene(T, k);
    } },
    pickShot
  });
})();
