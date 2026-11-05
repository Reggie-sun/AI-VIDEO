#!/usr/bin/env python
"""Frame-level features, loudness, band onsets/hits, beat/downbeat/tempo. Usage: 03_audio_03_features.py <analysis_root>
Needs work/audio_tmp/mix.wav + stems (03_audio_00_stems.py). Writes work/feat.npz, audio/hits.json, audio/beats.json,
audio/envelopes_24fps.json, audio/loudness.json. Python: /home/reggie/miniconda3/bin/python -I"""
import sys, os, json, subprocess, re
import numpy as np, soundfile as sf, scipy.signal as ss, librosa
root = sys.argv[1]; A = os.path.join(root, "audio"); W = os.path.join(root, "work"); TMP = os.path.join(W, "audio_tmp")
FPS = 24; NF = 7353; SR = 44100; HOP = 441; NFFT = 2048   # analysis grid: 100 frames/s
def load(p): x, sr = sf.read(p, dtype="float32"); assert sr == SR; return x
mix = load(f"{TMP}/mix.wav"); mono = mix.mean(1)
stem = {k: load(f"{TMP}/stems/{k}.wav").mean(1) for k in ["vocals", "drums", "bass", "other"]}
dur = len(mono) / SR
def stft_db(x):
    S = np.abs(librosa.stft(x, n_fft=NFFT, hop_length=HOP, center=True)) ** 2
    return S
freqs = librosa.fft_frequencies(sr=SR, n_fft=NFFT)
def band(S, lo, hi): return S[(freqs >= lo) & (freqs < hi)].sum(0)
def todb(p): return 10 * np.log10(p + 1e-12)
Sm = stft_db(mono); T100 = np.arange(Sm.shape[1]) * HOP / SR
# ---------------- loudness (BS.1770-4, ffmpeg ebur128 cross-check)
def kweight(x48):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1, -1.69065929318241, 0.73248077421585]
    b2 = [1, -2, 1]; a2 = [1, -1.99004745483398, 0.99007225036621]
    return ss.lfilter(b2, a2, ss.lfilter(b1, a1, x48))
x48 = librosa.resample(mix.T, orig_sr=SR, target_sr=48000)
kw = np.stack([kweight(c) for c in x48])
def block_lufs(kw, win, hop):
    n = (kw.shape[1] - win) // hop + 1
    ms = np.array([np.sum(np.mean(kw[:, i*hop:i*hop+win] ** 2, axis=1)) for i in range(n)])
    return -0.691 + 10 * np.log10(ms + 1e-14), ms
l400, ms400 = block_lufs(kw, int(0.4 * 48000), int(0.1 * 48000))
g1 = ms400[l400 > -70]; rel = -0.691 + 10 * np.log10(g1.mean()) - 10
integrated = -0.691 + 10 * np.log10(ms400[l400 > rel].mean())
l3s, _ = block_lufs(kw, 3 * 48000, int(0.1 * 48000)); g = l3s[l3s > -70]
relg = -0.691 + 10 * np.log10((10 ** ((g + 0.691) / 10)).mean()) - 20; g = g[g > relg]
lra = float(np.percentile(g, 95) - np.percentile(g, 10))
tp = max(np.abs(ss.resample_poly(mix[:, c], 4, 1)).max() for c in range(2)); tp_db = 20 * np.log10(tp)
ff = subprocess.run(["ffmpeg", "-nostats", "-i", f"{TMP}/mix.wav", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
def grab(k): m = re.findall(k + r":\s+(-?[\d.]+)", ff); return float(m[-1]) if m else None
loud = {"integrated_lufs": round(float(integrated), 2), "true_peak_dbfs": round(float(tp_db), 2), "lra": round(lra, 2),
        "ffmpeg_ebur128": {"I": grab("I"), "LRA": grab("LRA"), "true_peak": grab("Peak")},
        "momentary_lufs_100ms_series_file": "audio/loudness.json"}
loud["momentary_lufs_100ms"] = [round(float(v), 2) for v in l400[::10]]  # 1 value per second (400ms block @ every 1 s)
json.dump(loud, open(f"{A}/loudness.json", "w"))
print("loudness", {k: v for k, v in loud.items() if k != "momentary_lufs_100ms"})
# ---------------- band flux onsets from stems
B = {"kick": (30, 150), "snare_body": (150, 400), "snare_crack": (2000, 5000), "hat": (8000, 16000), "clap_mid": (900, 2000)}
Sd = stft_db(stem["drums"])
def flux(S, lo, hi):
    L = todb(band(S, lo, hi)); d = np.maximum(0, np.diff(L, prepend=L[0]))
    return d
def pick(env, min_dist_s, k_thr=2.5, win_s=1.0, abs_floor=None):
    med = ss.medfilt(env, 2 * int(win_s * 100 / 2) + 1)
    mad = ss.medfilt(np.abs(env - med), 2 * int(win_s * 100 / 2) + 1) + 1e-6
    pk, pr = ss.find_peaks(env, distance=int(min_dist_s * 100), height=med + k_thr * 1.4826 * mad + (abs_floor or 0))
    return pk, env[pk]
def refine(sig, lo, hi, times, half=0.035):
    """sub-frame onset time: max positive slope of the band-passed, rectified, 3 ms-smoothed stem envelope within +/-35 ms of the STFT-flux peak"""
    sos = ss.butter(4, [lo, min(hi, 20000)], btype="band", fs=SR, output="sos"); e = np.abs(ss.sosfiltfilt(sos, sig))
    e = np.convolve(e, np.ones(int(0.003 * SR)) / int(0.003 * SR), "same"); de = np.diff(e, prepend=e[0]); out = []
    for t in times:
        a = max(0, int((t - half) * SR)); b = min(len(de), int((t + half) * SR)); out.append((a + int(np.argmax(de[a:b]))) / SR)
    return np.array(out)
hits = []; fx = {}
for name, (lo, hi) in B.items():
    env = flux(Sd, lo, hi); env = ss.convolve(env, np.ones(3) / 3, mode="same"); fx[name] = env
    absf = {"kick": 6, "snare_body": 5, "snare_crack": 4, "hat": 3, "clap_mid": 5}[name]
    pk, val = pick(env, 0.12 if name != "hat" else 0.05, 2.0, 1.0, absf)
    # level gate: band energy at the peak must be within 35 dB of the stem's band max
    Lb = todb(band(Sd, lo, hi)); keep = Lb[pk] > Lb.max() - 40
    pk, val = pk[keep], val[keep]
    sc = np.clip(val / np.percentile(val, 95), 0, 1) if len(val) else val
    tt = refine(stem["drums"], lo, hi, T100[pk])
    for p, tr, s in zip(pk, tt, sc): hits.append({"t": round(float(tr), 4), "band": name, "strength": round(float(s), 3)})
hits.sort(key=lambda h: (h["t"], h["band"]))
for i, h in enumerate(hits): h["hit_id"] = f"H{i+1:05d}"; h["frame"] = int(round(h["t"] * FPS))
hits = [{"hit_id": h["hit_id"], "t": h["t"], "frame": h["frame"], "band": h["band"], "strength": h["strength"]} for h in hits]
json.dump({"band_hz": B, "source": "htdemucs drums stem, positive spectral flux (dB) per band, adaptive median+MAD peak picking", "hits": hits},
          open(f"{A}/hits.json", "w"))
print("hits", {b: sum(1 for h in hits if h["band"] == b) for b in B})
# ---------------- beat tracking
kick_t = np.array([h["t"] for h in hits if h["band"] == "kick"])
# note: STFT-flux peaks refined to waveform-envelope slope; librosa beat grid below is on a 10 ms grid and is snapped to these
oenv = librosa.onset.onset_strength(y=stem["drums"], sr=SR, hop_length=HOP, aggregate=np.median, fmax=300) \
     + 0.5 * librosa.onset.onset_strength(y=mono, sr=SR, hop_length=HOP)
tempo0, bt = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP, start_bpm=132, tightness=300, trim=False)
beats = librosa.frames_to_time(bt, sr=SR, hop_length=HOP)
print("initial tempo", float(np.atleast_1d(tempo0)[0]), "beats", len(beats))
# snap to kick onsets within 40 ms, then smooth
snapped = beats.copy(); resid = []
for i, b in enumerate(beats):
    j = np.argmin(np.abs(kick_t - b)) if len(kick_t) else None
    if j is not None and abs(kick_t[j] - b) < 0.04: snapped[i] = kick_t[j]; resid.append(kick_t[j] - b)
# robust smoothing of beat times: fit local linear within +/-8 beats, keep snapped only if residual to fit < 25 ms
n = len(snapped); fit = snapped.copy()
for i in range(n):
    a, c = max(0, i - 8), min(n, i + 9); idx = np.arange(a, c)
    co = np.polyfit(idx, snapped[a:c], 1); fit[i] = np.polyval(co, i)
final = np.where(np.abs(snapped - fit) < 0.025, snapped, fit)
# regularise: make final monotone with enforced local periodicity
ibi = np.diff(final); print("IBI s min/med/max", ibi.min(), np.median(ibi), ibi.max())
# extend grid back to t=0 and forward to the end (extrapolate with edge IBI)
while final[0] - np.median(ibi[:8]) > -0.01: final = np.insert(final, 0, final[0] - np.median(ibi[:8]))
while final[-1] + np.median(ibi[-8:]) < dur: final = np.append(final, final[-1] + np.median(ibi[-8:]))
final = final[final >= 0]
# kick-alignment confidence per beat: 1 if a kick within 30 ms
kc = np.array([np.min(np.abs(kick_t - b)) < 0.03 for b in final]) if len(kick_t) else np.zeros(len(final), bool)
# ---------------- downbeat phase from novelty peaks (section-level structure changes land on bar 1)
Lf = np.stack([todb(band(Sm, lo, hi)) for lo, hi in [(30, 150), (150, 400), (400, 2000), (2000, 5000), (5000, 16000)]])
Lvoc = todb(band(stft_db(stem["vocals"]), 100, 8000)); Ldr = todb(band(Sd, 30, 16000)); Lbass = todb(band(stft_db(stem["bass"]), 30, 300))
Lot = todb(band(stft_db(stem["other"]), 100, 10000))
def smooth(x, s=0.5): return ss.convolve(x, np.ones(int(s * 100)) / int(s * 100), mode="same")
st = np.stack([smooth(np.maximum(Ldr, -80)), smooth(np.maximum(Lbass, -80)), smooth(np.maximum(Lot, -80))])
nov = np.zeros(st.shape[1]); w = 200   # +/-2 s window difference of means
for i in range(w, st.shape[1] - w):
    nov[i] = np.abs(st[:, i:i + w].mean(1) - st[:, i - w:i].mean(1)).sum()
npk, _ = ss.find_peaks(nov, distance=300, height=np.percentile(nov, 80))
phase_votes = np.zeros(4); bi = np.arange(len(final))
for p in npk:
    j = int(np.argmin(np.abs(final - T100[p]))); phase_votes[j % 4] += nov[p]
    # also vote using the drum-resumption edge: first beat after
phase = int(np.argmax(phase_votes)); dconf = float(phase_votes[phase] / phase_votes.sum())
# second, independent vote: beat-synchronous chroma change (bass+other stems) on kick-supported beats, mod 4
chx = librosa.feature.chroma_cqt(y=stem["bass"] + stem["other"], sr=SR, hop_length=HOP); fr_b = librosa.time_to_frames(final, sr=SR, hop_length=HOP)
cs = np.array([chx[:, fr_b[i] + 5:max(fr_b[i] + 6, fr_b[i + 1] - 2)].mean(1) for i in range(len(fr_b) - 1)]); cs /= np.linalg.norm(cs, axis=1, keepdims=True) + 1e-9
dch = 1 - np.sum(cs[1:] * cs[:-1], axis=1); hv = np.zeros(4)
for i, v in zip(np.arange(1, len(cs)), dch):
    if kc[i]: hv[i % 4] += v
hphase = int(np.argmax(hv)); hshare = float(hv[hphase] / hv.sum())
print("harmonic-change vote", (hv / hv.sum()).round(3), "phase", hphase)
if hphase != phase and hshare > 0.6: phase = hphase; dconf = hshare   # chroma vote is the stronger evidence
downbeats = final[phase::4]
print("phase votes", phase_votes.round(0), "downbeat phase", phase, "conf", round(dconf, 2), "first downbeat", downbeats[0])
# local tempo curve
ibi = np.diff(final); bpm_beat = 60 / ibi
segs = []; win = 32  # 8 bars
for i in range(0, len(final) - 1, win):
    j = min(len(final) - 1, i + win)
    if j - i < 8: break
    co = np.polyfit(np.arange(i, j + 1), final[i:j + 1], 1); res = final[i:j + 1] - np.polyval(co, np.arange(i, j + 1))
    segs.append({"start_s": round(float(final[i]), 3), "end_s": round(float(final[j]), 3), "bpm": round(60 / co[0], 2),
                 "confidence": round(float(np.clip(1 - np.std(res) / 0.03, 0, 1) * (0.5 + 0.5 * kc[i:j + 1].mean())), 2)})
gco = np.polyfit(np.arange(len(final)), final, 1)
beats_json = {"beats_s": [round(float(b), 4) for b in final], "downbeats_s": [round(float(b), 4) for b in downbeats],
    "beat_is_kick_supported": [bool(k) for k in kc], "first_downbeat_s": round(float(downbeats[0]), 4), "groove_grid_valid_from_s": round(float(final[kc][0]), 3), "groove_grid_valid_to_s": round(float(final[kc][-1]), 3),
    "note": "beats before groove_grid_valid_from_s (intro, no steady pulse) and after groove_grid_valid_to_s are extrapolated at the edge tempo and carry no rhythmic evidence", "time_signature_assumed": "4/4",
    "global_bpm_linear_fit": round(60 / gco[0], 3), "global_bpm_median_ibi": round(float(60 / np.median(ibi)), 3),
    "downbeat_confidence": round(dconf, 2), "downbeat_harmonic_change_vote": [round(float(v / hv.sum()), 3) for v in hv], "downbeat_phase_votes": [round(float(v), 1) for v in phase_votes],
    "confidence": {"beat_kick_supported_fraction": round(float(kc.mean()), 3), "median_snap_residual_ms": round(float(np.median(np.abs(resid)) * 1000), 1) if resid else None},
    "method": "librosa DP beat tracker on drum-stem(<300Hz)+mix onset envelope, snapped to htdemucs kick onsets (<=40ms), local linear smoothing, downbeat phase by vote of structural novelty peaks on beat index mod 4",
    "tempo_segments": segs}
json.dump(beats_json, open(f"{A}/beats.json", "w"))
print("global bpm", beats_json["global_bpm_linear_fit"], beats_json["global_bpm_median_ibi"], "segments", [(s["start_s"], s["bpm"], s["confidence"]) for s in segs])
# ---------------- per-24fps-frame envelopes
tf = np.arange(NF) / FPS
def frame_agg(x, fn):
    out = np.zeros(NF)
    for f in range(NF):
        a = int(round(f / FPS * 100)); b = max(a + 1, int(round((f + 1) / FPS * 100))); out[f] = fn(x[a:min(b, len(x))]) if a < len(x) else x[-1]
    return out
rms_db = np.zeros(NF); 
for f in range(NF):
    a = int(f / FPS * SR); b = int((f + 1) / FPS * SR); seg = mono[a:b]
    rms_db[f] = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-7) if len(seg) else -120
def norm01(db, lo_p=2, hi_p=99.5):
    lo, hi = np.percentile(db, lo_p), np.percentile(db, hi_p); return np.clip((db - lo) / (hi - lo), 0, 1)
low = norm01(frame_agg(todb(band(Sm, 20, 150)), np.mean)); mid = norm01(frame_agg(todb(band(Sm, 150, 4000)), np.mean))
high = norm01(frame_agg(todb(band(Sm, 4000, 16000)), np.mean))
oe = librosa.onset.onset_strength(y=mono, sr=SR, hop_length=HOP); oe = oe / np.percentile(oe, 99)
onset = np.clip(frame_agg(oe, np.max), 0, 1.5)
vrms = np.zeros(NF)
for f in range(NF):
    a = int(f / FPS * SR); b = int((f + 1) / FPS * SR); seg = stem["vocals"][a:b]
    vrms[f] = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-7) if len(seg) else -120
env = {"fps": FPS, "n_frames": NF, "frame_window": "[f/24,(f+1)/24)", "arrays": {
    "rms_db": np.round(rms_db, 2).tolist(), "low": np.round(low, 3).tolist(), "mid": np.round(mid, 3).tolist(), "high": np.round(high, 3).tolist(),
    "onset_strength": np.round(onset, 3).tolist(), "vocal_rms_db": np.round(vrms, 2).tolist(),
    "vocal_energy": np.round(norm01(np.maximum(vrms, -70), 2, 99.5), 3).tolist()},
    "notes": ["low=20-150Hz, mid=150-4000Hz, high=4-16kHz mix band energy in dB mapped by 2nd..99.5th percentile to 0-1",
              "onset_strength = librosa onset_strength (mix) /p99, max within frame window", "vocal_* from htdemucs vocals stem (bleed of drums/FX possible)"]}
json.dump(env, open(f"{A}/envelopes_24fps.json", "w"))
np.savez_compressed(f"{W}/feat.npz", T100=T100, Lf=Lf, Lvoc=Lvoc, Ldr=Ldr, Lbass=Lbass, Lot=Lot, nov=nov, beats=final, downbeats=downbeats,
                    **{f"fx_{k}": v for k, v in fx.items()})
print("done")
