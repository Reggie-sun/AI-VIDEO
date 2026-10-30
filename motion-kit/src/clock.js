// Beat clock. Every musical time goes through the beat map, never one BPM:
// generated songs drift like live music. Comp time t (seconds from frame 0) maps to
// song time s = t + offset. All functions are pure functions of t.

function search(arr, s) {
  // index of the last element <= s (-1 if s < arr[0])
  let lo = 0, hi = arr.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= s) { ans = mid; lo = mid + 1; } else hi = mid - 1;
  }
  return ans;
}

export class Clock {
  constructor(beatsDoc, hitsDoc = {}, { offset = 0, windowBar0 = 0, fps = 30 } = {}) {
    this.beats = beatsDoc.beats;
    this.downbeats = beatsDoc.downbeats;
    this.offset = offset;
    this.bar0 = windowBar0;
    this.fps = fps;
    this.hits = hitsDoc;
  }

  song(t) { return t + this.offset; }
  comp(s) { return s - this.offset; }

  _phase(arr, t) {
    const s = this.song(t);
    const i = search(arr, s);
    if (i < 0) {
      const len = arr[1] - arr[0];
      return { idx: -1, frac: (s - arr[0]) / len + 1, len, pos: (s - arr[0]) / len };
    }
    const next = i + 1 < arr.length ? arr[i + 1] : arr[i] + (arr[i] - arr[i - 1]);
    const len = next - arr[i];
    const frac = (s - arr[i]) / len;
    return { idx: i, frac, len, pos: i + frac };
  }

  beat(t) { return this._phase(this.beats, t); }
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
  frameOf(t) { return Math.ceil(t * this.fps - 1e-6); }
  quant(t) { return this.frameOf(t) / this.fps; }

  // most recent event (comp time) at or before t from a list of song-time seconds
  last(list, t) {
    if (!list || !list.length) return null;
    const i = search(list, this.song(t));
    return i < 0 ? null : this.comp(list[i]);
  }

  // exponential pulse from the most recent event of a kind (kick, snare, hat, hits...)
  pulse(kind, t, decay = 0.12) {
    const list = kind === 'impact' ? (this.hits.hits || []).map(h => h.t) : this.hits[kind];
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
}

// Synthetic grid for development before the song exists (never used for delivery).
export function syntheticGrid({ bpm = 120, from = -4, to = 40, riser = [4, 6], impact = 6 } = {}) {
  const spb = 60 / bpm;
  const beats = [], downbeats = [], kick = [], snare = [], hat = [];
  for (let s = from; s <= to + 1e-9; s += spb) {
    const b = Math.round((s - from) / spb);
    const t = +s.toFixed(6);
    beats.push(t); kick.push(t);
    if (b % 4 === 0) downbeats.push(t);
    if (b % 4 === 1 || b % 4 === 3) snare.push(t);
    hat.push(t, +(t + spb / 2).toFixed(6));
  }
  return {
    beats: { duration: to, beats, downbeats, tempo: [{ t: 0, bpm }], downbeat_phase: 0, downbeat_method: 'synthetic' },
    hits: { kick, snare, hat, hits: [{ t: impact, score: 1 }], risers: [{ t0: riser[0], t1: riser[1], land: riser[1] }], fills: [], vocal_entries: [], env24: {} },
  };
}
