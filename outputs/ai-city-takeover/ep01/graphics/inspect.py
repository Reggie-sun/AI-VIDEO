#!/usr/bin/env python3
"""Probe exact source MP4 and extract first/middle/last contact sheets; no acceptance signature."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['dns', 'pause', 'web-cache', 'cpu-cache'])
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    video = root / 'renders' / f'{args.kind}.mp4'
    out = root / 'qa' / args.kind
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    streams = meta['streams']
    v = next(s for s in streams if s['codec_type'] == 'video')
    checks = {'size': [v['width'], v['height']] == [1920,1080], 'fps': v['r_frame_rate'] == '30/1',
              'frames': int(v['nb_frames']) == 120, 'silent': not any(s['codec_type'] == 'audio' for s in streams),
              'duration': abs(float(v['duration']) - 4) < .001}
    frames = []
    for n in (0, 60, 119):
        p = out / f'frame-{n:03}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', '-q:v', '2', str(p)], check=True)
        frames.append((n, Image.open(p).convert('RGB')))
    for width, name in [(640, 'contact-sheet.jpg'), (390, 'legibility-390.jpg')]:
        h = round(width * 1080 / 1920)
        sheet = Image.new('RGB', (width * 3, h + 28), '#f4f4f4')
        d = ImageDraw.Draw(sheet)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        for i, (n, im) in enumerate(frames):
            sheet.paste(im.resize((width,h), Image.Resampling.LANCZOS), (i * width, 28))
            d.text((i * width + 8, 5), f'{args.kind} / f{n:03} / {n/30:.3f}s', font=font, fill='#151515')
        sheet.save(out / name, quality=94)
    result = {'scope':'development_source_asset', 'video':str(video), 'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
              'metadata':meta, 'checks':checks, 'human_acceptance':'NOT_EVALUATED'}
    (out / 'probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'kind':args.kind,'sha256':result['sha256'],'checks':checks}))
    raise SystemExit(0 if all(checks.values()) else 2)


if __name__ == '__main__':
    main()
