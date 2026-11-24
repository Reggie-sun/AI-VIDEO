#!/usr/bin/env python3
"""Lyric scorer: scansion and assonance for a Suno lyric sheet, before any take is spent.

Method from the ESCAPE VELOCITY toolkit (claudia.gallery/wiki/toolkit, tool 2 "The lyric scorer:
scansion and assonance", and wiki/song "Verse lines that flow", "Sung hooks that fit their slot",
"Two numbers"); the code and its weights are original to this project and only approximate the
author's scorer. Scores are advice: the director's ear outranks them.

Run (the dictionary lives in its own venv, not in the project's lock):
  python3 -m venv ~/.local/share/ai-video/lyric-venv
  ~/.local/share/ai-video/lyric-venv/bin/pip install pronouncing pytest
  ~/.local/share/ai-video/lyric-venv/bin/python motion-kit/tools/lyric_score.py SHEET \
      [--bpm 128] [--seconds 200] [--json out.json] [--taboo words.txt] [--grid]

SHEET is plain text or Markdown. A ```lyrics fenced block is used if present; otherwise the fenced
block with the most section tags; otherwise the whole file. Each section starts with a tag line such
as `[Verse 1 - spoken, deadpan]`, `[Chorus - sung]`, `[Drop - chant]`; delivery is read from the tag
(spoken / sung / chant), falling back on the section name (Chorus/Hook -> sung, Drop -> chant).

Delivery model (tool 2):
- spoken: each line gets a two-bar slot; it enters on the "and" of beat 2 of bar 1 and its last
  word's stress lands on beat 4 of bar 2 (5.5 beats later). The natural rhythm is stretched to fit.
  NATURAL_SPOKEN_SYL_S is derived from the spec, not measured: a 11.5-syllable line (middle of the
  10-13 target) must come out at the median stretch 1.12 at 128 BPM.
- sung: a hook line is sung as one phrase of at most 1.5 bars (rest of the two-bar slot rested),
  one syllable per note; capacity = 2.9 syl/s x 1.5 bars, about 8 syllables at 128 BPM.
- chant: short clauses locked to the eighth-note pulse; capacity 3.0 syl/s x 2 bars.
Flow (spoken) = grid + stress spacing + stretch + line shape + couplet rhyme. Groove (sung/chant
only) = clause length + stress lock to the pulse + crush. Scansion = flow without rhyme, averaged
with groove where groove applies. Assonance = best line-end partner within four lines (rhyme, slant
rhyme, shared stressed vowels) plus internal stressed-vowel echo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import pronouncing
except ImportError:  # pragma: no cover - environment guard
    sys.exit("lyric_score.py needs `pronouncing`; run it with ~/.local/share/ai-video/lyric-venv/bin/python")

# ---------------------------------------------------------------- delivery constants (spec)
SLOT_BEATS = 8.0                 # two bars of 4/4
SPOKEN_ENTRY, SPOKEN_LAND = 1.5, 7.0   # "and" of beat 2 of bar 1 -> beat 4 of bar 2 (0-based beats)
RATE = {"spoken": 3.3, "sung": 2.9, "chant": 3.0}   # delivered syllables per second
SUNG_PHRASE_BARS = 1.5
SPOKEN_TARGET = (10, 13)
SUNG_HOOK_MAX = 8
MEDIAN_STRETCH = 1.12
NATURAL_SPOKEN_SYL_S = (11.5 - 1) * MEDIAN_STRETCH / ((SPOKEN_LAND - SPOKEN_ENTRY) * 60 / 128)
LYRICS_FIELD_MAX = 3000

# ---------------------------------------------------------------- weights (calibrated, see report)
FLOW_W = {"grid": 0.30, "spacing": 0.25, "stretch": 0.25, "shape": 0.20}   # scansion part of flow
FLOW_RHYME_W = 0.15                                                        # rhyme share of flow
ASSON_END_W, ASSON_ECHO_W = 0.8, 0.2

FUNCTION_WORDS = set("""a an the of to and or but nor is am are was were be been being in on at by for from
with into onto as if than that this these those it its it's i i'm i'd i'll you your you're you'll we we're
our us they they're their them he she him his her me my so do does did has have had will would can could
should shall may might must there there's who which what's let's 's""".split())
PREPOSITIONS = set("in on at by for from with into onto up out off over down to of".split())
SHORT_WORDS = set("""no go so yes oh we me us my up ok hey wow yeah yo is it in on at to do be he she his her
all and are but can did for get got had has him how its let man may new not now off old one our out own
run say see set she sit the too two use was way who why yet you big bad mad sad top hot cut fun win won
love back feel fast lock stop make take free gas fire burn fly high low""".split())
HOMOGRAPHS = set("""lead read live tear wind bass close wound bow row minute object present record content
desert refuse produce project permit subject contract conduct invalid does dove sow polish entrance separate
moderate estimate alternate deliberate graduate console resume sewer august buffet compact convict
digest excuse house lives number progress rebel recall wicked""".split())
LETTER_PHONES = {
    "A": "EY1", "B": "B IY1", "C": "S IY1", "D": "D IY1", "E": "IY1", "F": "EH1 F", "G": "JH IY1",
    "H": "EY1 CH", "I": "AY1", "J": "JH EY1", "K": "K EY1", "L": "EH1 L", "M": "EH1 M", "N": "EH1 N",
    "O": "OW1", "P": "P IY1", "Q": "K Y UW1", "R": "AA1 R", "S": "EH1 S", "T": "T IY1", "U": "Y UW1",
    "V": "V IY1", "W": "D AH1 B AH0 L Y UW0", "X": "EH1 K S", "Y": "W AY1", "Z": "Z IY1",
}
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
NEAR_VOWELS = [{"AA", "AO"}, {"UH", "UW"}, {"AH", "ER"}]
CONS_CLASS = {**{c: "stop" for c in "P B T D K G".split()}, **{c: "nasal" for c in "M N NG".split()},
              **{c: "fric" for c in "F V TH DH S Z SH ZH HH".split()}, "CH": "affr", "JH": "affr",
              "L": "liq", "R": "liq", "W": "glide", "Y": "glide"}

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
NUMBER_WORDS = set(ONES + TENS[2:] + ["hundred", "thousand", "million", "billion", "trillion", "point"])


def number_to_words(token: str) -> list[str]:
    def below_1000(n: int) -> list[str]:
        out: list[str] = []
        if n >= 100:
            out += [ONES[n // 100], "hundred"]
            n %= 100
            if n == 0:
                return out
        if n < 20:
            out.append(ONES[n])
        else:
            out.append(TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else ""))
        return out

    whole, _, frac = token.partition(".")
    n = int(whole)
    words: list[str] = []
    for value, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= value:
            words += below_1000(n // value) + [name]
            n %= value
    if n or not words:
        words += below_1000(n)
    if frac:
        words += ["point"] + [ONES[int(d)] for d in frac]
    return [p for w in words for p in w.split("-")]


# ---------------------------------------------------------------- pronunciation
_VOWEL_SPELL = [("igh", "AY"), ("eau", "OW"), ("ee", "IY"), ("ea", "IY"), ("ie", "IY"), ("ai", "EY"),
                ("ay", "EY"), ("ei", "EY"), ("ey", "EY"), ("oo", "UW"), ("ou", "AW"), ("ow", "OW"),
                ("oa", "OW"), ("oi", "OY"), ("oy", "OY"), ("au", "AO"), ("aw", "AO"), ("ue", "UW"),
                ("a", "AE"), ("e", "EH"), ("i", "IH"), ("o", "AA"), ("u", "AH"), ("y", "IH")]
_CONS_SPELL = [("tch", ["CH"]), ("ch", ["CH"]), ("sh", ["SH"]), ("th", ["TH"]), ("ng", ["NG"]), ("ph", ["F"]),
               ("ck", ["K"]), ("qu", ["K", "W"]), ("x", ["K", "S"]), ("c", ["K"]), ("j", ["JH"]), ("y", ["Y"])]


def fallback_phones(word: str) -> str:
    """Rough letter-to-sound for words CMUdict lacks: vowel groups are syllables, stress by suffix."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return ""
    if len(w) > 2 and w.endswith("e") and not w.endswith(("le", "ee", "ie", "ye")):
        w_core, silent_e = w[:-1], True
    else:
        w_core, silent_e = w, False
    phones: list[str] = []
    i = 0
    while i < len(w_core):
        for spell, ph in _VOWEL_SPELL:
            if w_core.startswith(spell, i) and not (spell == "y" and i == 0):
                v = ph
                if silent_e and spell in "aeiou" and i >= len(w_core) - 2:
                    v = {"a": "EY", "i": "AY", "o": "OW", "u": "UW", "e": "IY"}[spell]
                if spell == "y" and i == len(w_core) - 1:
                    v = "IY"
                if spell == "o" and i == len(w_core) - 1:
                    v = "OW"
                if spell == "a" and i == len(w_core) - 1:
                    v = "AH"
                phones.append(v + "0")
                i += len(spell)
                break
        else:
            for spell, ph in _CONS_SPELL:
                if w_core.startswith(spell, i):
                    phones += ph
                    i += len(spell)
                    break
            else:
                ch = w_core[i]
                phones.append({"s": "S", "z": "Z", "g": "G"}.get(ch, ch.upper()))
                i += 1
    vowel_idx = [k for k, p in enumerate(phones) if p[-1].isdigit()]
    if not vowel_idx:
        return " ".join(phones)
    n = len(vowel_idx)
    if n <= 2:
        stress = 0
    elif w.endswith(("ic", "tion", "sion", "ia", "io")):
        stress = n - 2
    else:
        stress = n - 3
    if n == 2 and w.endswith(("ic", "tion", "sion")):
        stress = 0
    k = vowel_idx[stress]
    phones[k] = phones[k][:-1] + "1"
    return " ".join(phones)


def lookup(word: str) -> tuple[list[str], str]:
    """All pronunciations for a lower-case word and their source."""
    found = pronouncing.phones_for_word(word)
    if found:
        return found, "cmudict"
    if word.endswith("'s") and pronouncing.phones_for_word(word[:-2]):
        return [p + " Z" for p in pronouncing.phones_for_word(word[:-2])], "cmudict"
    if word.endswith("s") and len(word) > 3 and pronouncing.phones_for_word(word[:-1]):
        return [p + " Z" for p in pronouncing.phones_for_word(word[:-1])], "cmudict"
    plain = re.sub(r"[^a-z]", "", word)
    for cut in range(3, len(plain) - 2):
        a, b = pronouncing.phones_for_word(plain[:cut]), pronouncing.phones_for_word(plain[cut:])
        if a and b:
            return [a[0] + " " + b[0].replace("1", "2")], "compound"
    return [fallback_phones(word)], "fallback"


@dataclass
class Word:
    text: str
    phones: list[str]                     # chosen pronunciation, phone list
    variants: list[str]
    source: str                           # cmudict / compound / fallback / letters / number
    function: bool = False
    caps: bool = False
    name: bool = False
    number: bool = False
    phrase_end: bool = False
    full_stop: bool = False
    pause: float = 0.0                    # pause after the word, in natural syllable units

    @property
    def stresses(self) -> list[int]:
        return [int(p[-1]) for p in self.phones if p[-1].isdigit()]

    @property
    def vowels(self) -> list[str]:
        return [p[:-1] for p in self.phones if p[-1].isdigit()]


@dataclass
class Syl:
    word: int
    vowel: str
    stress: int
    important: bool
    function: bool
    weight: float = 1.0
    pause: float = 0.0
    beat: float = 0.0                     # quantised position in the slot, in beats


TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|[A-Za-z]+(?:['’][A-Za-z]+)*|[.,!?;:…]+|[-–—]+")


def tokenize(line: str, lint: list[dict], where: str) -> list[Word]:
    raw = TOKEN_RE.findall(line.replace("’", "'"))
    alpha = [t for t in raw if t[0].isalpha()]
    shouting = bool(alpha) and sum(t.isupper() and len(t) > 1 for t in alpha) >= 0.5 * len(alpha)
    words: list[Word] = []
    sentence_start = True
    i = 0
    while i < len(raw):
        tok = raw[i]
        if not (tok[0].isalnum()):
            if words:
                strong = any(c in tok for c in ".!?;:…")
                words[-1].pause = max(words[-1].pause, 1.0 if strong else 0.6)
                words[-1].phrase_end = True
                words[-1].full_stop = words[-1].full_stop or strong
            sentence_start = sentence_start or any(c in tok for c in ".!?:")
            i += 1
            continue
        if tok[0].isdigit():
            lint.append({"where": where, "kind": "digits", "detail": f"'{tok}' - spell numbers out as sung"})
            for w in number_to_words(tok):
                ph, _ = lookup(w)
                words.append(Word(w, ph[0].split(), ph, "number", number=True))
            sentence_start = False
            i += 1
            continue
        # spaced acronym run: two or more single capital letters ("A G I")
        run = []
        j = i
        while j < len(raw) and len(raw[j]) == 1 and raw[j].isupper():
            run.append(raw[j])
            j += 1
        if len(run) >= 2 or (len(run) == 1 and run[0] not in "AI"):
            for k, letter in enumerate(run):
                ph = LETTER_PHONES[letter].replace("1", "1" if k == len(run) - 1 else "2")
                words.append(Word(letter, ph.split(), [ph], "letters", caps=True))
            sentence_start = False
            i = j
            continue
        low = tok.lower()
        is_acronym = (tok.isupper() and tok.isalpha() and 2 <= len(tok) <= 5 and not shouting and (
            not pronouncing.phones_for_word(low) or not re.search(r"[aeiou]", low)
            or (len(tok) <= 3 and low not in SHORT_WORDS)))
        if is_acronym:
            lint.append({"where": where, "kind": "unspaced acronym",
                         "detail": f"'{tok}' - write '{' '.join(tok)}' in the sheet; scored as letters"})
            for k, letter in enumerate(tok):
                ph = LETTER_PHONES[letter].replace("1", "1" if k == len(tok) - 1 else "2")
                words.append(Word(letter, ph.split(), [ph], "letters", caps=True))
            sentence_start = False
            i += 1
            continue
        if low in HOMOGRAPHS:
            lint.append({"where": where, "kind": "homograph", "detail": f"'{tok}' has two readings"})
        for part in low.split("-"):
            variants, source = lookup(part)
            w = Word(tok, variants[0].split(), variants, source)
            w.function = part in FUNCTION_WORDS
            w.caps = tok.isupper() and len(tok) > 1
            w.name = (tok[0].isupper() and not sentence_start and low != "i") or (tok[0].isupper() and source == "fallback")
            w.number = part in NUMBER_WORDS
            words.append(w)
        sentence_start = False
        i += 1
    if words:
        words[-1].phrase_end = True
    # a stranded preposition ending a phrase ("Lock in.") is stressed, not a function word
    for w in words:
        if w.phrase_end and w.function and w.text.lower() in PREPOSITIONS:
            w.function = False
    return words


def syllables(words: list[Word]) -> list[Syl]:
    """Syllables with the important ones marked: lexical stress, names, numbers, caps, phrase-final content."""
    syls: list[Syl] = []
    for wi, w in enumerate(words):
        st = w.stresses or [1]
        vw = w.vowels or ["AH"]
        primary = max(range(len(st)), key=lambda k: (st[k] == 1, st[k] == 2, -k)) if any(st) else 0
        for k, (s, v) in enumerate(zip(st, vw)):
            if w.function and not w.caps:
                important = False
            elif len(st) == 1:
                important = True
            else:
                important = k == primary or (s == 2 and len(st) >= 3 and abs(k - primary) >= 2)
            if w.source == "letters":
                important = True
            weight = 1.3 if important else (0.75 if w.function else 0.9)
            syls.append(Syl(wi, v, s, important, w.function and not w.caps, weight))
        syls[-1].pause = w.pause
    return syls


# ---------------------------------------------------------------- rhyme
def rhyme_tail(phones: list[str]) -> list[str]:
    """Phones from the last stressed vowel (primary or secondary) to the end."""
    idx = [k for k, p in enumerate(phones) if p[-1] in "12"]
    if not idx:
        idx = [k for k, p in enumerate(phones) if p[-1].isdigit()] or [0]
    return [p.rstrip("012") for p in phones[idx[-1]:]]


def end_unit(words: list[Word]) -> tuple[str, list[list[str]]]:
    """The line-end word (an acronym run counts as one unit) and its candidate pronunciations."""
    if not words:
        return "", [[]]
    if words[-1].source == "letters":
        k = len(words) - 1
        while k > 0 and words[k - 1].source == "letters":
            k -= 1
        run = words[k:]
        return " ".join(w.text for w in run), [sum((w.phones for w in run), [])]
    w = words[-1]
    return w.text.lower(), [v.split() for v in w.variants]


def _vowel_match(a: str, b: str) -> bool:
    return a == b or any(a in g and b in g for g in NEAR_VOWELS)


def _coda_close(ca: list[str], cb: list[str]) -> bool:
    """Slant-rhyme codas: same consonant class position by position, or one extra consonant (class/fast)."""
    if len(ca) == len(cb):
        return all(CONS_CLASS.get(x) == CONS_CLASS.get(y) for x, y in zip(ca, cb))
    short, long_ = sorted((ca, cb), key=len)
    return len(long_) - len(short) == 1 and bool(short) and (long_[:-1] == short or long_[1:] == short)


def pair_score(a: tuple[str, list[list[str]]], b: tuple[str, list[list[str]]]) -> tuple[float, str]:
    """1.0 rhyme, 0.8 slant, 0.6 assonance, 0.5 repeated word, 0.4 consonance, else shared stressed vowels."""
    if not a[0] or not b[0]:
        return 0.0, "none"
    if a[0] == b[0]:
        return 0.5, "repeat"
    best = (0.0, "none")
    for pa in a[1]:
        for pb in b[1]:
            ta, tb = rhyme_tail(pa), rhyme_tail(pb)
            if not ta or not tb:
                continue
            ca, cb = [p for p in ta[1:] if p not in VOWELS], [p for p in tb[1:] if p not in VOWELS]
            if ta == tb:
                cand = (1.0, "rhyme")
            elif _vowel_match(ta[0], tb[0]):
                if _coda_close(ca, cb):
                    cand = (0.8, "slant")
                else:
                    cand = (0.6, "assonance")
            elif ca and ca == cb:
                cand = (0.4, "consonance")
            else:
                va = [p.rstrip("012") for p in pa if p[-1] in "12"]
                vb = [p.rstrip("012") for p in pb if p[-1] in "12"]
                shared = len(set(va) & set(vb))
                cand = (min(0.3, 0.15 * shared), "shared vowels") if shared else (0.0, "none")
            best = max(best, cand)
    return best


# ---------------------------------------------------------------- per-line scoring
def ramp(x: float, lo0: float, lo1: float, hi1: float, hi0: float) -> float:
    """0 below lo0, 1 between lo1 and hi1, 0 above hi0, linear in between."""
    if x <= lo0 or x >= hi0:
        return 0.0
    if x < lo1:
        return (x - lo0) / (lo1 - lo0)
    if x > hi1:
        return (hi0 - x) / (hi0 - hi1)
    return 1.0


def place_spoken(syls: list[Syl], words: list[Word], bpm: float) -> float:
    """Place syllables in the two-bar slot; return the stretch factor."""
    beat_s = 60.0 / bpm
    unit = 1.0 / NATURAL_SPOKEN_SYL_S
    last_word = syls[-1].word
    anchor = max((k for k, s in enumerate(syls) if s.word == last_word and s.important),
                 default=len(syls) - 1)
    # Punctuation adds no natural time here: with it, EV's verses came out at median stretch 0.92
    # (132 BPM) against the measured 1.12; without it, 1.10 with 20 of 24 lines inside 0.8-1.5.
    onsets, t = [], 0.0
    for s in syls:
        onsets.append(t)
        t += s.weight * unit
    span_nat = onsets[anchor]
    span_slot = (SPOKEN_LAND - SPOKEN_ENTRY) * beat_s
    stretch = span_slot / span_nat if span_nat > 0 else 4.0
    for k, s in enumerate(syls):
        if k <= anchor and span_nat > 0:
            pos = SPOKEN_ENTRY + onsets[k] / span_nat * (SPOKEN_LAND - SPOKEN_ENTRY)
        else:
            pos = SPOKEN_LAND + (onsets[k] - span_nat) * stretch / beat_s
        s.beat = round(pos * 4) / 4
    return stretch


def place_pulse(syls: list[Syl], hold: bool = True) -> tuple[int, int]:
    """One syllable per eighth note from the first stress on a beat; with `hold`, a stress that would
    fall off the beat is held over to the next one. Returns (holds, weak syllables on a beat)."""
    first = next((k for k, s in enumerate(syls) if s.important), 0)
    pos = -0.5 * first
    holds = weak_on = 0
    for k, s in enumerate(syls):
        if k > 0:
            pos += 0.5 + (0.5 if syls[k - 1].pause >= 1.0 else 0.0)
        if hold and s.important and pos % 1:
            pos += 0.5
            holds += 1
        elif not s.important and not pos % 1 and k > 0:
            weak_on += 1
        s.beat = pos
    return holds, weak_on


def grid_score(syls: list[Syl]) -> float:
    imp = [s for s in syls if s.important]
    fn = [s for s in syls if s.function]
    def credit(b: float) -> float:
        f = b % 1
        return 1.0 if f == 0 else (0.5 if f == 0.5 else 0.15)
    g = sum(credit(s.beat) for s in imp) / len(imp) if imp else 0.0
    f = sum(0.0 if s.beat % 1 == 0 else 1.0 for s in fn) / len(fn) if fn else 1.0
    return 0.8 * g + 0.2 * f


def spacing_score(syls: list[Syl]) -> float:
    idx = [k for k, s in enumerate(syls) if s.important]
    if not idx:
        return 0.0
    gaps = [b - a - 1 for a, b in zip(idx, idx[1:])] + [idx[0]]
    value = {0: 0.55, 1: 1.0, 2: 1.0, 3: 0.75}
    return sum(value.get(g, 0.35) for g in gaps) / len(gaps)


def shape_score(words: list[Word]) -> tuple[float, list[str]]:
    """At most two phrases between full stops; no one-word sentence mid-line ("Ugh.")."""
    sentences: list[list[list[Word]]] = [[[]]]
    for w in words:
        sentences[-1][-1].append(w)
        if w.full_stop:
            sentences.append([[]])
        elif w.phrase_end:
            sentences[-1].append([])
    sentences = [[p for p in s if p] for s in sentences]
    sentences = [s for s in sentences if s]
    notes, score = [], 1.0
    for s in sentences:
        if len(s) > 2:
            score -= 0.2 * (len(s) - 2)
            notes.append(f"{len(s)} phrases in one sentence")
    for s in sentences[1:-1]:
        if len(s) == 1 and len({w.text for w in s[0]}) == 1:
            score -= 0.3
            notes.append(f"one-word fragment '{s[0][0].text}'")
    return max(score, 0.0), notes


def clause_groove(clause: list[Syl], delivery: str) -> float:
    n = len(clause)
    length = 1.0 if 2 <= n <= 6 else (0.85 if n in (1, 7) else (0.65 if n == 8 else 0.4))
    holds, weak_on = place_pulse(clause)
    imp = max(1, sum(s.important for s in clause))
    lock = max(0.0, 1.0 - 0.3 * holds / imp - 0.5 * weak_on / max(1, n - imp))
    return 0.4 * length + 0.6 * lock


@dataclass
class LineResult:
    section: str
    index: int
    delivery: str
    text: str
    syllables: int
    words: int
    stretch: float | None
    rate: float
    grid: float
    spacing: float
    stretch_score: float
    shape: float
    rhyme: float = 0.0
    flow: float = 0.0
    groove: float | None = None
    scansion: float = 0.0
    end_word: str = ""
    end_sound: str = ""
    partner: str = ""
    partner_kind: str = "none"
    end_score: float = 0.0
    echo: float = 0.0
    assonance: float = 0.0
    notes: list[str] = field(default_factory=list)
    grid_line: str = ""


def draw_grid(syls: list[Syl]) -> str:
    cells = ["." for _ in range(int(SLOT_BEATS * 4))]
    for s in syls:
        k = int(round(s.beat * 4))
        if 0 <= k < len(cells):
            cells[k] = "X" if s.important else "x"
    return "|".join("".join(cells[b * 4:(b + 1) * 4]) for b in range(int(SLOT_BEATS)))


def score_line(section: str, index: int, delivery: str, text: str, bpm: float,
               lint: list[dict]) -> tuple[LineResult, list[Word], list[Syl]]:
    where = f"{section} #{index + 1}"
    if re.search(r"[()\[\]{}<>/\\&%$#@*+=~_|^]", text):
        lint.append({"where": where, "kind": "symbols", "detail": "brackets or symbols in a lyric line (parentheses get sung)"})
    words = tokenize(text, lint, where)
    syls = syllables(words)
    n = len(syls)
    beat_s = 60.0 / bpm
    notes: list[str] = []
    if delivery == "spoken":
        stretch = place_spoken(syls, words, bpm)
        stretch_sc = ramp(stretch, 0.6, 0.95, 1.3, 2.4)
        if not SPOKEN_TARGET[0] - 1 <= n <= SPOKEN_TARGET[1]:
            notes.append(f"{n} syl (target 10-13)")
    else:
        capacity = RATE[delivery] * (SUNG_PHRASE_BARS * 4 if delivery == "sung" else SLOT_BEATS) * beat_s
        stretch = capacity / max(n, 1)
        stretch_sc = ramp(stretch, 0.6, 0.98, 3.0, 6.0)
        place_pulse(syls, hold=False)
        if delivery == "sung" and n > SUNG_HOOK_MAX:
            notes.append(f"crush risk: {n} syl sung (hook max {SUNG_HOOK_MAX})")
            lint.append({"where": where, "kind": "crushed hook",
                         "detail": f"sung line of {n} syllables > {SUNG_HOOK_MAX}; Suno will skip or crush syllables"})
    grid = grid_score(syls)
    spacing = spacing_score(syls)
    shape, shape_notes = shape_score(words)
    notes += shape_notes
    res = LineResult(section, index, delivery, text, n, len(text.split()),
                     round(stretch, 2) if delivery == "spoken" else None,
                     round(n / (SLOT_BEATS * beat_s), 2), grid, spacing, stretch_sc, shape, notes=notes)
    if delivery != "spoken":
        clauses: list[list[Syl]] = [[]]
        for s in syls:
            clauses[-1].append(s)
            if s.pause > 0:
                clauses.append([])
        clauses = [c for c in clauses if c]
        g = sum(clause_groove(c, delivery) * len(c) for c in clauses) / max(n, 1)
        if delivery == "sung" and n > SUNG_HOOK_MAX:
            g *= max(0.45, 1.0 - 0.12 * (n - SUNG_HOOK_MAX))
        res.groove = g
        place_pulse(syls)
    res.grid_line = draw_grid(syls)
    return res, words, syls


def finish_section(lines: list[tuple[LineResult, list[Word], list[Syl]]]) -> None:
    ends = [end_unit(words) for _, words, _ in lines]
    for i, (res, words, syls) in enumerate(lines):
        # couplet rhyme on the beat-4 word, for flow
        mate = i + 1 if i % 2 == 0 else i - 1
        if mate >= len(lines):
            mate = i - 1
        res.rhyme = pair_score(ends[i], ends[mate])[0] if 0 <= mate < len(lines) and mate != i else 0.0
        scan_part = sum(FLOW_W[k] * getattr(res, {"grid": "grid", "spacing": "spacing", "stretch": "stretch_score",
                                                     "shape": "shape"}[k]) for k in FLOW_W)
        res.flow = (1 - FLOW_RHYME_W) * scan_part + FLOW_RHYME_W * res.rhyme
        res.scansion = scan_part if res.groove is None else (scan_part + res.groove) / 2
        # assonance: best partner within four lines, plus stressed-vowel echo inside the line
        best, kind, partner = 0.0, "none", ""
        for j in range(max(0, i - 4), min(len(lines), i + 5)):
            if j == i:
                continue
            sc, kd = pair_score(ends[i], ends[j])
            if sc > best:
                best, kind, partner = sc, kd, f"#{j + 1} {ends[j][0]}"
        res.end_word = ends[i][0]
        res.end_sound = "-".join(rhyme_tail(ends[i][1][0])) if ends[i][0] else ""
        res.end_score, res.partner_kind, res.partner = best, kind, partner
        stressed = [s.vowel for s in syls if s.important]
        res.echo = (sum(stressed.count(v) > 1 for v in stressed) / len(stressed)) if len(stressed) > 1 else 0.0
        res.assonance = ASSON_END_W * best + ASSON_ECHO_W * res.echo


# ---------------------------------------------------------------- sheet parsing
TAG_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def extract_lyrics(text: str) -> str:
    fenced = re.findall(r"```(\w*)[^\n]*\n(.*?)```", text, flags=re.S)
    for lang, body in fenced:
        if lang.lower() == "lyrics":
            return body
    tagged = [(sum(bool(TAG_RE.match(row)) for row in body.splitlines()), body) for _, body in fenced]
    tagged = [t for t in tagged if t[0] > 0]
    if tagged:
        return max(tagged, key=lambda t: t[0])[1]
    return text


def delivery_of(tag: str) -> str:
    low = tag.lower()
    name, _, cues = low.partition(" - ")
    for key, words in (("chant", ("chant",)), ("sung", ("sung", "sing", "singing")), ("spoken", ("spoken", "speak", "rap"))):
        if any(re.search(rf"\b{w}", cues) for w in words):
            return key
    if re.search(r"chorus|hook", name):
        return "sung"
    if re.search(r"drop|chant", name):
        return "chant"
    return "spoken"


def parse_sheet(lyrics: str) -> list[tuple[str, str, list[str]]]:
    sections: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for raw in lyrics.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = TAG_RE.match(line)
        if m:
            tag = m.group(1).strip()
            current = (tag.split(" - ")[0].strip(), delivery_of(tag), [])
            sections.append(current)
            continue
        if current is None:
            current = ("Untagged", "spoken", [])
            sections.append(current)
        current[2].append(line)
    return [s for s in sections if s[2]]


# ---------------------------------------------------------------- song
def pct(x: float) -> int:
    return int(round(100 * x))


def score_sheet(text: str, bpm: float = 128.0, seconds: float | None = None,
                taboo: list[str] | None = None) -> dict:
    lyrics = extract_lyrics(text)
    lint: list[dict] = []
    field_chars = len(lyrics.strip())
    if field_chars > LYRICS_FIELD_MAX:
        lint.append({"where": "sheet", "kind": "length",
                     "detail": f"lyrics field {field_chars} chars > ~{LYRICS_FIELD_MAX}; Suno rushes or truncates silently"})
    sections_out, all_lines = [], []
    for name, delivery, lines in parse_sheet(lyrics):
        scored = [score_line(name, i, delivery, text, bpm, lint) for i, text in enumerate(lines)]
        finish_section(scored)
        results = [r for r, _, _ in scored]
        all_lines += results
        sections_out.append({"section": name, "delivery": delivery, "lines": len(results),
                             "scansion": pct(sum(r.scansion for r in results) / len(results)),
                             "assonance": pct(sum(r.assonance for r in results) / len(results)),
                             "flow": pct(sum(r.flow for r in results) / len(results)),
                             "groove": (pct(sum(r.groove for r in results) / len(results))
                                        if results[0].groove is not None else None)})
    for word in taboo or []:
        pat = re.compile(rf"\b{re.escape(word)}\b", re.I)
        for r in all_lines:
            if pat.search(r.text):
                lint.append({"where": f"{r.section} #{r.index + 1}", "kind": "taboo", "detail": f"'{word}'"})
    n_lines = max(1, len(all_lines))
    total_words = sum(r.words for r in all_lines)
    song = {"scansion": pct(sum(r.scansion for r in all_lines) / n_lines),
            "assonance": pct(sum(r.assonance for r in all_lines) / n_lines),
            "lines": len(all_lines), "words": total_words,
            "syllables": sum(r.syllables for r in all_lines), "lyrics_chars": field_chars, "bpm": bpm,
            "seconds": seconds,
            "words_per_minute": round(total_words / (seconds / 60), 1) if seconds else None}
    lines_out = []
    for r in all_lines:
        d = asdict(r)
        for k in ("grid", "spacing", "stretch_score", "shape", "rhyme", "flow", "scansion", "end_score",
                  "echo", "assonance"):
            d[k] = pct(d[k])
        d["groove"] = pct(r.groove) if r.groove is not None else None
        d["index"] = r.index + 1
        lines_out.append(d)
    return {"song": song, "sections": sections_out, "lines": lines_out, "lint": lint}


def to_markdown(report: dict, show_grid: bool = False) -> str:
    s = report["song"]
    out = [f"# Lyric score: scansion {s['scansion']} / assonance {s['assonance']}", "",
           f"{s['lines']} lines, {s['words']} words, {s['syllables']} syllables, lyrics field {s['lyrics_chars']} chars, "
           f"{s['bpm']:g} BPM" + (f", {s['words_per_minute']} words/min over {s['seconds']:g} s" if s["seconds"] else ""),
           "", "## Sections", "", "| Section | Delivery | Lines | Scansion | Assonance | Flow | Groove |",
           "|---|---|---|---|---|---|---|"]
    for sec in report["sections"]:
        out.append(f"| {sec['section']} | {sec['delivery']} | {sec['lines']} | {sec['scansion']} | {sec['assonance']} | "
                   f"{sec['flow']} | {'' if sec['groove'] is None else sec['groove']} |")
    out += ["", "## Lines", "", "| Section | # | Line | Syl | Stretch | Grid | Space | Shape | Flow | Groove | Scan | "
            "End sound | Partner | Kind | Asson | Notes |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for ln in report["lines"]:
        text = ln["text"].replace("|", "\\|")
        out.append(f"| {ln['section']} | {ln['index']} | {text} | {ln['syllables']} | "
                   f"{'' if ln['stretch'] is None else ln['stretch']} | {ln['grid']} | {ln['spacing']} | {ln['shape']} | "
                   f"{ln['flow']} | {'' if ln['groove'] is None else ln['groove']} | {ln['scansion']} | {ln['end_sound']} | "
                   f"{ln['partner']} | {ln['partner_kind']} | {ln['assonance']} | {'; '.join(ln['notes'])} |")
        if show_grid:
            out.append(f"| | | `{ln['grid_line']}` | | | | | | | | | | | | | |")
    out += ["", "## Lint", ""]
    out += [f"- **{x['kind']}** ({x['where']}): {x['detail']}" for x in report["lint"]] or ["- clean"]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sheet", type=Path)
    ap.add_argument("--bpm", type=float, default=128.0)
    ap.add_argument("--seconds", type=float, help="assumed song duration, for words per minute")
    ap.add_argument("--json", type=Path, help="write the full report as JSON here")
    ap.add_argument("--taboo", type=Path, help="word list, one word or phrase per line (# comments)")
    ap.add_argument("--grid", action="store_true", help="draw each line on the 16th-note grid")
    a = ap.parse_args(argv)
    taboo = None
    if a.taboo:
        taboo = [t.strip() for t in a.taboo.read_text(encoding="utf-8").splitlines()
                 if t.strip() and not t.lstrip().startswith("#")]
    report = score_sheet(a.sheet.read_text(encoding="utf-8"), a.bpm, a.seconds, taboo)
    sys.stdout.write(to_markdown(report, a.grid))
    if a.json:
        a.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
