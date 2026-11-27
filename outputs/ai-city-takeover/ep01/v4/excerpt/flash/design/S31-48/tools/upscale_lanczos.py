#!/usr/bin/env python3
"""upscale_lanczos.py SRC DST [W=2944]: plain Lanczos resample to width W (no learned detail, keeps freckles/grain as-is).
Real-ESRGAN realesr-general-x4v3 was tried first and rejected: it erased her freckles (face drift) and sharpened
book spines into glyph-like marks."""
import hashlib, sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]; W = int(sys.argv[3]) if len(sys.argv) > 3 else 2944
im = Image.open(src).convert('RGB'); H = round(im.height * W / im.width)
im.resize((W, H), Image.LANCZOS).save(dst)
print(dst, W, H, hashlib.sha256(open(dst, 'rb').read()).hexdigest())
