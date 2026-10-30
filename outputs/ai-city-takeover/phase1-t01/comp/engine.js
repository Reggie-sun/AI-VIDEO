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
      const dt = t - e;
      return dt < 0 ? 0 : Math.exp(-dt / decay);
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
  function fbm1(x, seed = 0, oct = 3) {
    let v = 0, amp = 0.5, f = 1, norm = 0;
    for (let k = 0; k < oct; k++) {
      v += amp * noise1(x * f, seed + k * 17);
      norm += amp;
      amp *= 0.5;
      f *= 2.03;
    }
    return v / norm;
  }
  var clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  var lerp = (a, b, t) => a + (b - a) * t;
  var remap = (x, a, b, c = 0, d = 1) => lerp(c, d, clamp((x - a) / (b - a)));
  var easeOutCubic = (t) => 1 - Math.pow(1 - clamp(t), 3);
  var easeInOutCubic = (t) => {
    t = clamp(t);
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };
  var easeOutExpo = (t) => t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t));
  function squareToQuad(p) {
    const [x0, y0] = p[0], [x1, y1] = p[1], [x2, y2] = p[2], [x3, y3] = p[3];
    const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3;
    const dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
    const den = dx1 * dy2 - dx2 * dy1;
    const g = (dx3 * dy2 - dx2 * dy3) / den, h = (dx1 * dy3 - dx3 * dy1) / den;
    return [
      x1 - x0 + g * x1,
      x3 - x0 + h * x3,
      x0,
      y1 - y0 + g * y1,
      y3 - y0 + h * y3,
      y0,
      g,
      h,
      1
    ];
  }
  function invert3(m) {
    const [a, b, c, d, e, f, g, h, i] = m;
    const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
    const det = a * A + b * B + c * C;
    return [
      A / det,
      -(b * i - c * h) / det,
      (b * f - c * e) / det,
      B / det,
      (a * i - c * g) / det,
      -(a * f - c * d) / det,
      C / det,
      -(a * h - b * g) / det,
      (a * e - b * d) / det
    ];
  }

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
  function wipeOut(ctx, draw2, { t, t0, dur = 0.12, x0, y0, w, h }) {
    const k = clamp((t - t0) / dur);
    if (k >= 1) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(x0 + w * easeOutCubic(k), y0, w * (1 - easeOutCubic(k)), h);
    ctx.clip();
    draw2(ctx);
    ctx.restore();
  }
  function rollNumber(from, to, t, t0, t1, steps) {
    if (t <= t0) return from;
    if (t >= t1) return to;
    const s = Math.floor((t - t0) / (t1 - t0) * steps) / steps;
    return Math.round(lerp(from, to, easeOutCubic(s)));
  }
  var thousands = (n) => n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  function osd(ctx, x, y, lines, { size = 22, color = "rgba(236,241,244,0.86)", lead = 1.45 } = {}) {
    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.65)";
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 1;
    ctx.shadowOffsetY = 1;
    let yy = y;
    for (const line of lines) {
      runs(ctx, line.map((p) => ({ family: F.mono, size, tracking: 1.5, color, ...p })), x, yy, { gap: size * 0.6 });
      yy += size * lead;
    }
    ctx.restore();
  }
  function detector(ctx, box, { t, t0, frame, label, sub = null, subColor = "#E3342F", color = "rgba(240,244,246,0.92)", s0 = 1.6, lw = 2 }) {
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
    ctx.globalAlpha = Math.min(1, 0.3 + e);
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
    font(ctx, F.mono, 24, 0.5);
    const tw = ctx.measureText(label).width + 14;
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y - 36), Math.round(tw), 32);
    ctx.fillStyle = "rgba(8,10,12,0.95)";
    ctx.fillText(label, Math.round(x + 7), Math.round(y - 12));
    if (sub) {
      font(ctx, F.monoB, 24, 1);
      const sw = ctx.measureText(sub).width + 14;
      ctx.fillStyle = subColor;
      ctx.fillRect(Math.round(x + tw + 4), Math.round(y - 36), Math.round(sw), 32);
      ctx.fillStyle = subColor.startsWith("#") ? "rgba(250,250,250,0.98)" : "rgba(8,10,12,0.95)";
      ctx.fillText(sub, Math.round(x + tw + 11), Math.round(y - 12));
    }
    ctx.restore();
  }
  function chrome(ctx, w, h, { inset = 36, alpha = 0.5, mark = 26 } = {}) {
    ctx.save();
    ctx.strokeStyle = `rgba(236,241,244,${alpha})`;
    ctx.lineWidth = 1;
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
  function carDialog(ctx, W2, H2, { t, on, title, button, disabledAt, progress, frame }) {
    ctx.save();
    const g = ctx.createLinearGradient(0, 0, 0, H2);
    g.addColorStop(0, "#0a0f14");
    g.addColorStop(1, "#05080b");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W2, H2);
    const k = clamp((t - on) / 0.18);
    if (k <= 0) {
      ctx.restore();
      return;
    }
    ctx.globalAlpha = easeOutCubic(k);
    font(ctx, F.sansR, 30, 2);
    ctx.fillStyle = "rgba(160,176,190,0.9)";
    ctx.fillText("\u7CFB\u7EDF\u901A\u77E5", 72, 74);
    ctx.fillStyle = "rgba(160,176,190,0.5)";
    ctx.fillRect(72, 92, W2 - 144, 1);
    font(ctx, F.sans, 84, 4);
    ctx.fillStyle = "#f2f5f7";
    ctx.fillText(title, 72, 206);
    ctx.fillStyle = "rgba(242,245,247,0.16)";
    ctx.fillRect(72, 252, W2 - 144, 4);
    ctx.fillStyle = "rgba(242,245,247,0.95)";
    ctx.fillRect(72, 252, (W2 - 144) * clamp(progress), 4);
    const dis = clamp((t - disabledAt) / 0.08);
    const bw = 330, bh = 92, bx = W2 - 72 - bw, by = H2 - 40 - bh;
    ctx.lineWidth = 2;
    ctx.strokeStyle = `rgba(242,245,247,${lerp(0.9, 0.22, dis)})`;
    roundRect(ctx, bx, by, bw, bh, 14);
    ctx.stroke();
    font(ctx, F.sansR, 44, 3);
    ctx.fillStyle = `rgba(242,245,247,${lerp(0.95, 0.28, dis)})`;
    const tw = ctx.measureText(button).width;
    ctx.fillText(button, bx + (bw - tw) / 2, by + 62);
    if (dis > 0) {
      font(ctx, F.sansR, 30, 2);
      ctx.fillStyle = `rgba(227,52,47,${0.95 * dis})`;
      ctx.fillText("\u4E0D\u53EF\u7528", bx - 128, by + 58);
    }
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
    uGrain: 0.035,
    uGrainOverlay: 0.45,
    uVignette: 0.32,
    uCA: 0.25,
    uMisreg: 0,
    uFlash: 0,
    uFade: 0,
    uSat: 0.86,
    uRedKeep: 1.12,
    uWeave: [0, 0],
    uFeedGain: 0.92
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
    const ctx = { W: W2, H: H2, fps: cfg.fps, clock, data, size, layers, info };
    window.__mk = { info, scenes: Object.keys(cfg.scenes), music, ready: true };
    function renderFrame(t) {
      const frame = Math.round(t * cfg.fps);
      for (const l of Object.values(layers)) reset(l.ctx);
      const shot = cfg.pickShot(t, clock, data);
      const scene = cfg.scenes[shot.id];
      const p = scene(t, { ...ctx, frame, shot, t0: shot.t0, t1: shot.t1 });
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
    window.addEventListener("hf-seek", (e) => {
      const t = e.detail.time;
      e.detail.waitUntil(ready.then((r) => r.renderFrame(t)));
    });
    window.__mkRender = (t) => ready.then((r) => r.renderFrame(t));
    return ready;
  }

  // outputs/ai-city-takeover/phase1-t01/comp/src/main.js
  var W = 1920;
  var H = 1080;
  var FPS = 30;
  var DURATION = 10;
  var PW = 1672;
  var PH = 941;
  var FIT = W / PW;
  var RED = "#E3342F";
  function clampView(cx, cy, z) {
    const hx = W / 2 / (FIT * z), hy = H / 2 / (FIT * z);
    return [clamp(cx, hx, PW - hx), clamp(cy, hy, PH - hy), z, 0];
  }
  function cam(view, shake = [0, 0]) {
    const [cx, cy, z] = view, s = FIT * z;
    return { view, shake, s, out: ([x, y]) => [(x - cx) * s + W / 2 + shake[0], (y - cy) * s + H / 2 + shake[1]] };
  }
  var snap2 = (t, ts) => easeOutCubic(clamp((t - ts) / (2 / FPS)));
  var impactKick = (dt) => dt < 0 ? 0 : dt < 0.04 ? dt / 0.04 : Math.exp(-(dt - 0.04) / 0.03);
  function packLights(list) {
    const p = new Float32Array(32 * 4), c = new Float32Array(32 * 4);
    list.slice(0, 32).forEach((l, i) => {
      p.set([l.x, l.y, l.r, l.I], i * 4);
      c.set([...l.c, l.refl || 0], i * 4);
    });
    return { n: Math.min(32, list.length), p, c };
  }
  function packSegs(list, color) {
    const a = new Float32Array(64 * 4), w = new Float32Array(64 * 2);
    list.slice(0, 64).forEach((s, i) => {
      a.set([s.a[0], s.a[1], s.b[0], s.b[1]], i * 4);
      w.set([s.r, s.I], i * 2);
    });
    return { n: Math.min(64, list.length), a, w, color };
  }
  function packBodies(list) {
    const p = new Float32Array(12 * 4), a = new Float32Array(12);
    list.slice(0, 12).forEach((b, i) => {
      p.set([b.x, b.y, b.hw, b.hh], i * 4);
      a[i] = b.o;
    });
    return { n: Math.min(12, list.length), p, a };
  }
  var YH = 179;
  var KZ = 461;
  var xDivL = () => 1106;
  var xDivR = (y) => 1290 + 0.483 * (y - 560);
  var xEdgeL = (y) => 760 + 0.4167 * (900 - y);
  var xEdgeR = (y) => 1270 + 0.638 * (y - 230);
  var laneC = (lane, y) => lane === 0 ? (xEdgeL(y) + xDivL(y)) / 2 : lane === 1 ? (xDivL(y) + xDivR(y)) / 2 : (xDivR(y) + xEdgeR(y)) / 2;
  var depthW = (y) => 0.483 * (y - YH);
  function car(lane, z, lat = 0) {
    const y = YH + KZ / z, w = depthW(y);
    return { x: laneC(lane, y) + lat * w, y, sep: 0.42 * w, z };
  }
  var humanZ = (t) => 1.55 + 0.5 * t + 0.05 * fbm1(t * 0.8, 5);
  var humanLat = (t) => 0.07 * fbm1(t * 0.6, 9);
  var aiCars = (t) => [
    ...[0, 1, 2, 3, 4].map((i) => ({ lane: 0, z: 2.5 + 0.95 * i + 0.47 * t })),
    ...[0, 1, 2, 3].map((j) => ({ lane: 2, z: 2.9 + 0.95 * j + 0.47 * t }))
  ];
  function carLights(c, cm, { brake = 1, glow = true, ai = false }) {
    const att = Math.exp(-0.38 * (c.z - 1));
    if (att < 0.03) return { lights: [], body: null, att };
    const I = (ai ? 2.4 : 3.2) * att * brake;
    const col = brake > 1.05 ? [1, 0.075, 0.03] : [1, 0.045, 0.02];
    const yl = c.y - 0.4 * c.sep;
    const lights = [];
    for (const dx of [-0.5, 0.5]) {
      const [x, y] = cm.out([c.x + dx * c.sep, yl]);
      lights.push({ x, y, r: Math.max(0.9, 0.05 * c.sep * cm.s), I, c: col, refl: 0.75 * c.sep * cm.s });
    }
    if (glow) {
      const [gx, gy] = cm.out([c.x, yl - 1.9 * c.sep]);
      lights.push({ x: gx, y: gy, r: -(0.95 * c.sep * cm.s), I: (ai ? 0.035 : 0.05) * att, c: [0.55, 0.66, 0.82] });
    }
    const [bx, by] = cm.out([c.x, c.y - 0.18 * c.sep]);
    const body = { x: bx, y: by, hw: 0.62 * c.sep * cm.s, hh: 0.3 * c.sep * cm.s, o: 0.45 * Math.sqrt(att) };
    return { lights, body, att };
  }
  var ev = (k, id) => k.clock.at(...k.data.events.events[id].at);
  function S1(t, k) {
    const { clock, frame, layers } = k;
    const at = (b, be = 0, s = 0) => clock.at(b, be, s);
    const s1 = ev(k, "s1_ptz1"), s2 = ev(k, "s1_ptz2"), pushT0 = s2 + 2 / FPS, pushT1 = ev(k, "cut_s2");
    let z = 1 + 0.06 * snap2(t, s1) + 0.06 * snap2(t, s2);
    z *= 1 + 0.045 * easeInOutCubic(clamp((t - pushT0) / (pushT1 - pushT0)));
    if (t >= ev(k, "s1_census")) z *= 1 + 0.01 * clock.pulse("kick", t, 0.12);
    const cz = clamp((z - 1) / 0.17);
    const view = clampView(lerp(836, 1080, cz), lerp(470, 470, cz), z);
    const cm = cam(view);
    const lights = [], segs = [], bodies = [];
    const brakeAt = [1.55, 3.05];
    const brake = (tt) => 1 + 0.85 * brakeAt.reduce((m, b) => Math.max(m, tt >= b && tt < b + 0.22 ? 1 - (tt - b) / 0.22 * 0.3 : 0), 0);
    const human = (tt) => car(1, humanZ(tt), humanLat(tt));
    const add = (c, opts, trailFn) => {
      const r = carLights(c, cm, opts);
      lights.push(...r.lights);
      if (r.body) bodies.push(r.body);
      if (trailFn && r.att > 0.08) {
        for (const dx of [-0.5, 0.5]) {
          let prev = null;
          for (let j = 0; j <= 3; j++) {
            const cc = trailFn(t - j * 0.06);
            const p = cm.out([cc.x + dx * cc.sep, cc.y - 0.4 * cc.sep]);
            if (prev) segs.push({ a: prev, b: p, r: Math.max(0.7, 0.035 * cc.sep * cm.s), I: 0.45 * r.att * (1 - j / 4) });
            prev = p;
          }
        }
      }
    };
    for (const a of aiCars(t)) add(car(a.lane, a.z), { ai: true }, (tt) => car(a.lane, a.z - 0.47 * (t - tt)));
    const hc = human(t);
    add(hc, { brake: brake(t) }, human);
    const f = layers.feed.ctx;
    chrome(f, W, H, { inset: 36, alpha: 0.32 });
    const secs = 12 + Math.floor(t);
    const blink = clock.beat(t).frac < 0.5;
    osd(f, 72, 96, [
      [{ text: "CAM 07" }, { text: "\u73AF\u57CE\u9AD8\u67B6 \xB7 \u5317\u5411", family: F.sansR, size: 22 }],
      [{ text: `03:47:${String(secs).padStart(2, "0")}` }, { text: blink ? "\u25CF REC" : "  REC", color: blink ? "rgba(227,52,47,0.95)" : "rgba(236,241,244,0.86)" }]
    ]);
    const lag = human(t - 1.5 / FPS);
    const [bx, by] = cm.out([lag.x, lag.y - 0.2 * lag.sep]);
    const bw = Math.max(70, 1.55 * lag.sep * cm.s), bh = Math.max(46, 1 * lag.sep * cm.s);
    const conf = (0.95 + 0.04 * hash2(frame, 7)).toFixed(2);
    detector(f, [bx - bw / 2, by - bh / 2, bw, bh], {
      t,
      t0: 0,
      frame,
      label: `car ${conf}`,
      sub: t >= ev(k, "s1_census") ? "HUMAN" : null
    });
    const o = layers.overlay.ctx;
    const titleOn = ev(k, "s1_title"), titleOff = ev(k, "s1_census");
    const title = (c) => {
      c.fillStyle = "#F1F4F6";
      runs(c, [
        { text: "\u5982\u679C", family: F.serif, size: 104, tracking: 6 },
        { text: "AI", family: F.serif, size: 96, tracking: 4, gap: 26 },
        { text: "\u5728\u51CC\u6668", family: F.serif, size: 104, tracking: 6 }
      ], 120, 452, { gap: 22 });
      runs(c, [{ text: "\u63A5\u7BA1\u4E00\u5EA7\u57CE\u5E02", family: F.serif, size: 104, tracking: 6 }], 120, 588);
    };
    if (t < titleOff) slam(o, title, { t, t0: titleOn, dur: 0.06, s0: 1.08, ax: 120, ay: 520 });
    else wipeOut(o, title, { t, t0: titleOff, dur: 0.1, x0: 100, y0: 330, w: 760, h: 300 });
    const cardOn = ev(k, "s1_census");
    if (t >= cardOn) {
      const ai = rollNumber(1284180, 1284329, t, cardOn, at(1, 1), 8);
      slam(o, (c) => {
        font(c, F.mono, 18, 3);
        c.fillStyle = "rgba(236,241,244,0.55)";
        c.fillText("VEHICLE CENSUS \xB7 03:47", 120, 724);
        c.fillStyle = "rgba(236,241,244,0.35)";
        c.fillRect(120, 740, 640, 1);
        font(c, F.sansR, 46, 4);
        c.fillStyle = "#E9EEF1";
        c.fillText("\u81EA\u52A8\u9A7E\u9A76", 120, 806);
        font(c, F.mono, 54, 0);
        c.textAlign = "right";
        c.fillText(thousands(ai), 760, 806);
        c.textAlign = "left";
      }, { t, t0: cardOn, dur: 0.06, s0: 1.05, ax: 120, ay: 780 });
      slam(o, (c) => {
        font(c, F.sansR, 46, 4);
        c.fillStyle = "#E9EEF1";
        c.fillText("\u4EBA\u7C7B\u9A7E\u9A76", 120, 884);
        font(c, F.mono, 54, 0);
        c.fillStyle = RED;
        c.textAlign = "right";
        c.fillText("1", 760, 884);
        c.textAlign = "left";
        c.fillStyle = RED;
        c.fillRect(120, 902, 18, 4);
      }, { t, t0: ev(k, "s1_census2"), dur: 0.06, s0: 1.05, ax: 120, ay: 860 });
    }
    return {
      plate: "P1L",
      view,
      fit: FIT,
      fogA: [0.3, 45e-4, 9, -2.5],
      fogB: [0.22, 0.011, -14, 1.5],
      fogTint: [0.05, 0.068, 0.09],
      fogLift: 0.15,
      lights: packLights(lights),
      segs: packSegs(segs, [1, 0.05, 0.02]),
      bodies: packBodies(bodies),
      emitGain: 0,
      bloomThreshold: 1.1,
      feedGlow: 0.1,
      overlayGlow: 0.05,
      grade: { uHalation: 0.22, uWeave: [(hash2(frame, 11) - 0.5) * 0.5, (hash2(frame, 12) - 0.5) * 0.5] }
    };
  }
  var SCREEN = [[1028, 490], [1631, 519], [1626, 710], [1009, 667]];
  var VP2 = [1010, 330];
  function S2(t, k) {
    const { clock, layers, t0, t1 } = k;
    const at = (b2, be = 0, s = 0) => clock.at(b2, be, s);
    const u = clamp((t - t0) / (t1 - t0));
    const rz = clock.riser(t);
    let z = 1.06 * (1 + 0.03 * easeInOutCubic(u));
    const amp = 3.5 * rz * rz;
    const shake = [2.4 * noise1(t * 0.7, 21) + amp * noise1(t * 9, 22), 1.8 * noise1(t * 0.6, 23) + amp * noise1(t * 8, 24)];
    const view = clampView(960, 470, z);
    const cm = cam(view, shake);
    const b = clock.beat(t);
    const beatInBar = Math.min(3, Math.floor(clock.bar(t).frac * 4 + 1e-6));
    const sweepAge = beatInBar % 2 * b.len + b.frac * b.len;
    const sweepPos = lerp(-300, 1500, clamp(sweepAge / 0.42));
    const sweepGain = 0.85 * Math.exp(-sweepAge / 0.5);
    const ui = layers.ui;
    carDialog(ui.ctx, ui.c.width, ui.c.height, {
      t,
      on: t0,
      title: "\u7CFB\u7EDF\u5C06\u63A5\u7BA1\u9A7E\u9A76",
      button: "\u4FDD\u6301\u624B\u52A8",
      disabledAt: ev(k, "s2_disable"),
      progress: remap(t, t0 + 0.2, at(3, 0) - 0.05),
      frame: k.frame
    });
    const quad = SCREEN.map(cm.out);
    const Hm = invert3(squareToQuad(quad));
    const Hcol = [Hm[0], Hm[3], Hm[6], Hm[1], Hm[4], Hm[7], Hm[2], Hm[5], Hm[8]];
    const cx = quad.reduce((s, p) => s + p[0], 0) / 4, cy = quad.reduce((s, p) => s + p[1], 0) / 4;
    const pulse = 1 + 0.05 * clock.pulse("kick", t, 0.15);
    return {
      plate: "P2L",
      view,
      fit: FIT,
      shake,
      mask: "P2Lmask",
      flowVP: [VP2[0], VP2[1], 1 + 0.1 * u],
      sweep: [0.35, 0.94, sweepPos, 150],
      sweepGain,
      fogA: [0.1, 6e-3, 6, 0],
      fogB: [0.06, 0.013, -8, 1],
      fogTint: [0.05, 0.065, 0.085],
      fogLift: 0.1,
      screen: { H: Hcol, gain: 1.15 * pulse, spill: 0.55 * pulse, spillColor: [0.55, 0.7, 0.95], center: [cx, cy], radius: 520 },
      bloomThreshold: 0.8,
      feedGlow: 0,
      grade: { uExposure: 1.05, uHalation: 0.3, uVignette: 0.38 }
    };
  }
  function S3(t, k) {
    const { clock, frame, layers, data, t0 } = k;
    const at = (b2, be = 0, s = 0) => clock.at(b2, be, s);
    const dt = t - t0;
    let z = lerp(1.1, 1.03, easeInOutCubic(clamp(dt / (DURATION - t0))));
    z *= 1 + 0.06 * impactKick(dt);
    const view = clampView(836, 520, z);
    const cm = cam(view);
    const b = clock.beat(t);
    const beatPos = b.idx + easeOutCubic(clamp(b.frac / 0.35));
    const settleStart = t0 + 5 / FPS;
    const e = layers.emit.ctx;
    const LAMBDA = 110, DASH = 58;
    let hero = null;
    const bpRef = clock.beat(t0 + b.len).pos;
    data.paths.paths.forEach((path, i) => {
      const isHero = path.id === "f";
      const settle = (isHero ? 1 : 0.5) * b.len;
      const chaos = 1 - easeInOutCubic(clamp((t - settleStart) / settle));
      const pts = path.points, arc = path.arc, len = arc[arc.length - 1];
      const at_s = (s) => {
        let j = 1;
        while (j < arc.length - 1 && arc[j] < s) j++;
        const f2 = clamp((s - arc[j - 1]) / Math.max(1e-6, arc[j] - arc[j - 1]));
        return [lerp(pts[j - 1][0], pts[j][0], f2), lerp(pts[j - 1][1], pts[j][1], f2)];
      };
      const N = Math.ceil(len / LAMBDA) + 2;
      const kHero = (Math.round((120 + LAMBDA) / LAMBDA - bpRef) % N + N) % N;
      for (let kk = 0; kk < N; kk++) {
        const off = (hash2(i * 31 + 7, kk + 100) - 0.5) * 0.95 * chaos;
        const s = ((kk + beatPos + off) % N + N) % N * LAMBDA - LAMBDA;
        if (s < 0 || s > len) continue;
        const seg = [];
        for (let q = 0; q <= 6; q++) seg.push(cm.out(at_s(clamp(s - DASH + q / 6 * DASH, 0, len))));
        const bright = lerp(0.35 + 0.65 * hash2(i, kk + 7), 1, 1 - chaos);
        const heroPulse = isHero && kk === kHero;
        glowPath(e, seg, { core: heroPulse ? 3 : 2, halo: heroPulse ? 11 : 7, alpha: (heroPulse ? 1 : 0.8) * bright });
        if (heroPulse) hero = seg[seg.length - 1];
      }
    });
    const f = layers.feed.ctx;
    chrome(f, W, H, { inset: 36, alpha: 0.32 });
    osd(f, 72, 96, [
      [{ text: "AERIAL \xB7 CAM 01" }, { text: "\u73AF\u57CE\u7ACB\u4EA4", family: F.sansR, size: 22 }],
      [{ text: `03:48:${String(Math.max(0, Math.floor(dt))).padStart(2, "0")}` }]
    ]);
    if (hero && t >= t0 + b.len * 1) {
      const conf = (0.96 + 0.03 * hash2(frame, 9)).toFixed(2);
      detector(f, [hero[0] - 44, hero[1] - 30, 88, 60], { t, t0: t0 + b.len * 1, frame, label: `car ${conf}`, sub: "AI", subColor: "rgba(240,244,246,0.92)" });
    }
    const o = layers.overlay.ctx;
    slam(o, (c) => {
      font(c, F.sansR, 48, 6);
      c.fillStyle = "#E9EEF1";
      c.fillText("\u4EBA\u7C7B\u9A7E\u9A76", 124, 300);
      font(c, F.sans, 300, 0);
      c.fillStyle = "#F4F6F8";
      c.fillText("0", 108, 590);
    }, { t, t0, dur: 0.05, s0: 1.16, ax: 120, ay: 440, ghosts: 2 });
    const tc = clamp((t - ev(k, "s3_time")) / 0.25);
    if (tc > 0) {
      o.save();
      o.globalAlpha = tc;
      font(o, F.mono, 34, 4);
      o.fillStyle = "rgba(236,241,244,0.82)";
      o.fillText("03:48", 128, 652);
      o.restore();
    }
    const mis = 4 * Math.max(0, 1 - dt / (3 / FPS));
    return {
      plate: "P3L",
      view,
      fit: FIT,
      fogA: [0.16, 3e-3, 7, -1],
      fogB: [0.1, 8e-3, -10, 1],
      fogTint: [0.055, 0.07, 0.092],
      fogLift: 0.12,
      emitGain: 2 + 0.4 * clock.pulse("kick", t, 0.12),
      bloomThreshold: 1,
      feedGlow: 0.1,
      overlayGlow: 0.05,
      grade: {
        uMisreg: mis,
        uHalftone: 0.1 + 0.25 * Math.max(0, 1 - dt / (4 / FPS)),
        uFlash: frame === Math.ceil(t0 * FPS - 1e-6) ? 0.06 : 0,
        uWeave: [(hash2(frame, 13) - 0.5) * 0.5, (hash2(frame, 14) - 0.5) * 0.5]
      }
    };
  }
  var _events = null;
  var EVENTS = () => _events;
  function pickShot(t, clock, data) {
    _events = data.events.events;
    const f = Math.round(t * FPS);
    const cut = (x) => Math.ceil(x * FPS - 1e-6);
    const c1 = cut(clock.at(...EVENTS().cut_s2.at)), c2 = cut(clock.at(...EVENTS().cut_s3_drop.at));
    if (f < c1) return { id: "S1", t0: 0, t1: c1 / FPS };
    if (f < c2) return { id: "S2", t0: c1 / FPS, t1: c2 / FPS };
    return { id: "S3", t0: c2 / FPS, t1: DURATION };
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
    data: { paths: "data/P3L-paths.json", events: "data/events.json" },
    images: {
      P1L: { url: "plates/P1L.png" },
      P2L: { url: "plates/P2L.png" },
      P3L: { url: "plates/P3L.png" },
      P2Lmask: { url: "plates/P2L-interior.png", mipmap: false }
    },
    uiSize: [1268, 400],
    scenes: { S1, S2, S3 },
    pickShot
  });
})();
