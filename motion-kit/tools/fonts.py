#!/usr/bin/env python3
"""Extract OFL CJK faces from the system TTC collections (and, with --latin, OFL Latin display
faces) and subset them to the glyphs a composition actually uses.

The text set is every non-ASCII character found in the given source files (JS/JSON/HTML/MD)
plus printable ASCII and a few typographic marks, so a subset never silently drops a glyph
that the composition draws.  Output: OTF files + fonts.json (family, file, sha256, license).

With --grotesk it also subsets the URW base35 Nimbus Sans Bold (a Helvetica-like bold grotesque, motion-kit
lyrics.js headline style). It is not OFL: URW base35 is AGPL-3 with a font exception (the Debian copyright file is
copied next to it and the licence is recorded per face in fonts.json). A render carries only the rasterised glyphs.

Usage:
  uv run python motion-kit/tools/fonts.py --out <comp>/fonts --scan <dir-or-file> [...] [--latin] [--grotesk]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTCollection, TTFont

FACES = {
    # css family            (collection file,                                    name-table family, weight)
    "MK Sans SC": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "Noto Sans CJK SC", "Bold"),
    "MK Sans SC Regular": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "Noto Sans CJK SC", "Regular"),
    "MK Mono SC": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "Noto Sans Mono CJK SC", "Regular"),
    "MK Mono SC Bold": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "Noto Sans Mono CJK SC", "Bold"),
    "MK Serif SC": ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "Noto Serif CJK SC", "Bold"),
}
# Latin display faces for English lyric lines (single TTF files from fonts-noto-core)
LATIN_FACES = {
    "MK Display": "/usr/share/fonts/truetype/noto/NotoSansDisplay-Regular.ttf",
    "MK Display Italic": "/usr/share/fonts/truetype/noto/NotoSansDisplay-Italic.ttf",
    "MK Serif Display Italic": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf",
}
# Latin grotesque for the opt-in headline lyric style (--grotesk; fonts-urw-base35)
GROTESK_FACES = {
    "MK Grotesk Bold": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf",
}
GROTESK_LICENSE = "AGPL-3.0 with font exception (URW base35, (URW)++ 2013-2015; Debian fonts-urw-base35)"
GROTESK_LICENSE_SRC = Path("/usr/share/doc/fonts-urw-base35/copyright")
LICENSE_SRC = Path("/usr/share/doc/fonts-noto-cjk/copyright")
LATIN_LICENSE_SRC = Path("/usr/share/doc/fonts-noto-core/copyright")
EXTRA = "·•—–‒…“”‘’「」『』《》（）【】，。：；！？、％‰°±×÷→←↑↓▲▼■□●○◆◇★☆／＼｜＿　"


def family_name(font) -> str:
    name = font["name"]
    for nid in (16, 1):
        rec = name.getName(nid, 3, 1, 0x409) or name.getName(nid, 1, 0, 0)
        if rec:
            return str(rec)
    return ""


def pick(collection: str, family: str):
    coll = TTCollection(collection)
    for font in coll.fonts:
        if family_name(font) == family:
            return font
    raise SystemExit(f"{family} not in {collection}")


def collect_text(paths: list[Path]) -> str:
    chars: set[str] = set(chr(c) for c in range(0x20, 0x7F)) | set(EXTRA)
    for root in paths:
        files = [root] if root.is_file() else [p for p in root.rglob("*")
                                               if p.suffix in {".js", ".mjs", ".json", ".html", ".md"}]
        for f in files:
            if "node_modules" in f.parts or "fonts" in f.parts:
                continue
            chars |= {ch for ch in f.read_text(encoding="utf-8", errors="ignore") if ord(ch) > 0x7F}
    return "".join(sorted(chars))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--scan", type=Path, nargs="+", required=True)
    ap.add_argument("--latin", action="store_true", help="also subset the Latin display faces")
    ap.add_argument("--grotesk", action="store_true", help="also subset Nimbus Sans Bold (AGPL-3 + font exception)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    text = collect_text(args.scan)
    manifest = {"text_sha256": hashlib.sha256(text.encode()).hexdigest(), "chars": len(text), "faces": []}
    ofl = "SIL Open Font License 1.1"
    faces = [(css, pick(coll, fam), fam, weight, text, ofl) for css, (coll, fam, weight) in FACES.items()]
    latin = "".join(ch for ch in text if ord(ch) < 0x2E80)           # no CJK in a Latin face
    if args.latin:
        faces += [(css, TTFont(path), Path(path).stem, "Regular", latin, ofl) for css, path in LATIN_FACES.items()]
    if args.grotesk:
        faces += [(css, TTFont(path), Path(path).stem, "Bold", latin, GROTESK_LICENSE) for css, path in GROTESK_FACES.items()]
    for css, font, fam, weight, face_text, lic in faces:
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.hinting = False
        sub = subset.Subsetter(opts)
        sub.populate(text=face_text)
        sub.subset(font)
        fname = css.replace(" ", "-") + ".otf"
        path = args.out / fname
        font.save(path)
        cmap = font.getBestCmap()
        missing = [ch for ch in face_text if ord(ch) not in cmap and ch not in "　"
                   and (face_text is text or ch.isalnum() or ch in "'’—.,?!:;-")]
        data = path.read_bytes()
        manifest["faces"].append({"family": css, "source_family": fam, "weight": weight, "file": fname,
                                  "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                  "license": lic, "missing": "".join(missing)})
    shutil.copyfile(LICENSE_SRC, args.out / "LICENSE-noto-cjk.txt")
    if args.latin:
        shutil.copyfile(LATIN_LICENSE_SRC, args.out / "LICENSE-noto-core.txt")
    if args.grotesk:
        shutil.copyfile(GROTESK_LICENSE_SRC, args.out / "LICENSE-urw-base35.txt")
    (args.out / "fonts.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in manifest["faces"]:
        print(f"{f['family']:20s} {f['bytes']:>8d}  missing={f['missing']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
