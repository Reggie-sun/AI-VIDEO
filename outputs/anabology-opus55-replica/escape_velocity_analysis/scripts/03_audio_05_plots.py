#!/usr/bin/env python
"""Spectrogram/waveform overview PNGs. Usage: 03_audio_05_plots.py <analysis_root>
Writes audio/audio_overview.png and audio/spec_seg_0..7.png (~40 s each). Draws beats (thin), downbeats (bold),
sections (labelled, if audio_timeline.json exists) and events."""
import sys, os, json
import numpy as np, soundfile as sf, librosa
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
root = sys.argv[1]; A = os.path.join(root, "audio"); TMP = os.path.join(root, "work", "audio_tmp")
F = np.load(os.path.join(root, "work", "feat.npz")); bj = json.load(open(f"{A}/beats.json")); hits = json.load(open(f"{A}/hits.json"))["hits"]
tl = json.load(open(os.path.join(root, "audio_timeline.json"))) if os.path.exists(os.path.join(root, "audio_timeline.json")) else None
y, sr = sf.read(f"{TMP}/mix.wav", dtype="float32"); mono = y.mean(1); dur = len(mono) / sr
S = librosa.feature.melspectrogram(y=mono, sr=sr, n_fft=2048, hop_length=441, n_mels=128, fmax=16000); Sdb = librosa.power_to_db(S, ref=S.max(), top_db=80)
T100 = F["T100"]; mel_f = librosa.mel_frequencies(n_mels=128, fmax=16000)
beats = np.array(bj["beats_s"]); dbs = np.array(bj["downbeats_s"])
ev = tl["events"] if tl else []
cols = {"kick": "#ff5555", "snare_body": "#ffaa00", "snare_crack": "#ffee00", "hat": "#55ddff", "clap_mid": "#cc77ff"}
def panel(ax_s, ax_e, ax_h, t0, t1):
    i0, i1 = int(t0 * 100), int(t1 * 100)
    ax_s.imshow(Sdb[:, i0:i1], origin="lower", aspect="auto", extent=[t0, min(t1, dur), 0, 128], cmap="magma", vmin=-80, vmax=0)
    ax_s.set_yticks([0, 32, 64, 96, 127]); ax_s.set_yticklabels(["0", f"{mel_f[32]:.0f}", f"{mel_f[64]:.0f}", f"{mel_f[96]:.0f}", "16k"]); ax_s.set_ylabel("mel Hz")
    for b in beats[(beats >= t0) & (beats <= t1)]: ax_s.axvline(b, color="w", lw=0.3, alpha=0.35)
    for b in dbs[(dbs >= t0) & (dbs <= t1)]: ax_s.axvline(b, color="cyan", lw=1.0, alpha=0.9)
    if tl:
        for s in tl["sections"]:
            if t0 <= s["start_s"] <= t1:
                for a in (ax_s, ax_e): a.axvline(s["start_s"], color="lime", lw=2)
                ax_s.text(s["start_s"] + 0.1, 122, f'{s["section_id"]} {s["label"]}', color="lime", fontsize=7, va="top")
        for e in ev:
            if t0 <= e["start_s"] <= t1 and e["type"] in ("drop", "impact", "riser", "downlifter", "silence", "breakdown", "fill", "stutter", "glitch", "whoosh", "reverse", "speech_sample", "sfx"):
                ax_s.plot([e["start_s"]], [4], marker="v", color="white", ms=5); ax_s.text(e["start_s"], 8 + (hash(e["event_id"]) % 4) * 7, e["type"][:6], color="white", fontsize=5)
    xs = np.arange(i0, min(i1, len(T100)))
    for nm, c in [("Ldr", "r"), ("Lbass", "orange"), ("Lot", "g"), ("Lvoc", "c")]:
        ax_e.plot(T100[xs], np.convolve(F[nm], np.ones(10) / 10, "same")[xs], color=c, lw=0.8, label=nm[1:])
    ax_e.set_ylim(-80, 0); ax_e.set_ylabel("stem dB"); ax_e.legend(fontsize=6, ncol=4, loc="lower right")
    for k, c in cols.items():
        yk = list(cols).index(k)
        hh = [h["t"] for h in hits if h["band"] == k and t0 <= h["t"] <= t1]
        ax_h.vlines(hh, yk, yk + 0.9, color=c, lw=0.8)
    ax_h.set_yticks(np.arange(len(cols)) + 0.45); ax_h.set_yticklabels(list(cols), fontsize=6); ax_h.set_xlabel("s")
    for a in (ax_s, ax_e, ax_h): a.set_xlim(t0, t1)
for k in range(8):
    t0, t1 = k * 40.0, min(dur, (k + 1) * 40.0)
    fig, ax = plt.subplots(3, 1, figsize=(24, 9), gridspec_kw={"height_ratios": [4, 1.5, 1.2]}, sharex=True)
    panel(*ax, t0, t1); fig.suptitle(f"ESCAPE VELOCITY audio {t0:.0f}-{t1:.0f}s  (cyan=downbeat, white=beat, green=section)"); fig.tight_layout()
    fig.savefig(f"{A}/spec_seg_{k}.png", dpi=70); plt.close(fig)
# overview
fig, ax = plt.subplots(4, 1, figsize=(26, 12), sharex=True, gridspec_kw={"height_ratios": [1.6, 1.6, 1.4, 1.2]})
t = np.arange(len(mono)) / sr; st = 200
ax[0].plot(t[::st], mono[::st], color="#444", lw=0.3); ax[0].set_ylabel("waveform")
env = json.load(open(f"{A}/envelopes_24fps.json"))["arrays"]; tf = np.arange(len(env["rms_db"])) / 24
ax[1].plot(tf, env["rms_db"], color="k", lw=0.7, label="mix rms dB"); ax[1].plot(tf, env["vocal_rms_db"], color="c", lw=0.5, label="vocal stem rms dB"); ax[1].set_ylim(-70, -5); ax[1].legend(fontsize=7, loc="lower right"); ax[1].set_ylabel("dB")
ax[2].plot(tf, env["low"], color="r", lw=0.6, label="low"); ax[2].plot(tf, env["mid"], color="g", lw=0.6, label="mid"); ax[2].plot(tf, env["high"], color="b", lw=0.6, label="high"); ax[2].legend(fontsize=7, ncol=3); ax[2].set_ylabel("band 0-1")
ax[3].imshow(Sdb, origin="lower", aspect="auto", extent=[0, dur, 0, 128], cmap="magma", vmin=-80, vmax=0)
if tl:
    for s in tl["sections"]:
        for a in ax: a.axvline(s["start_s"], color="lime", lw=1)
        ax[0].text(s["start_s"] + 0.3, 0.9, f'{s["section_id"]}\n{s["label"]}', fontsize=6, color="darkgreen", va="top", transform=ax[0].get_xaxis_transform())
    for e in ev:
        if e["type"] in ("drop", "impact", "riser", "downlifter", "silence", "breakdown"):
            ax[3].plot([e["start_s"]], [6], marker="v", color="w", ms=4)
ax[3].set_xlabel("s"); ax[3].set_xlim(0, dur); fig.tight_layout(); fig.savefig(f"{A}/audio_overview.png", dpi=60); plt.close(fig)
print("plots done")
