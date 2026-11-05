#!/usr/bin/env python3
"""Build four editable, silent 4s development source assets, not an episode timeline."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
KINDS = ('dns', 'pause', 'web-cache', 'cpu-cache')


def main():
    fonts = ROOT / 'fonts'
    subprocess.run([sys.executable, str(REPO / 'motion-kit/tools/fonts.py'), '--out', str(fonts),
                    '--scan', str(REPO / 'motion-kit/src/news-graphics.js')], check=True)
    manifest = json.loads((fonts / 'fonts.json').read_text())
    if any(face['missing'] for face in manifest['faces']):
        raise SystemExit('Missing glyphs: refusing to build source assets')
    subprocess.run([str(REPO / 'node_modules/.bin/esbuild'), str(ROOT / 'src/main.js'), '--bundle',
                    '--format=iife', '--target=chrome120', f'--outfile={ROOT / "engine.js"}', '--log-level=warning'], check=True)
    for kind in KINDS:
        comp = ROOT / kind
        comp.mkdir(exist_ok=True)
        shutil.copytree(fonts, comp / 'fonts', dirs_exist_ok=True)
        shutil.copyfile(ROOT / 'engine.js', comp / 'engine.js')
        (comp / 'config.json').write_text(json.dumps({'kind': kind, 'scope': 'development_source_asset',
                                                     'duration': 4, 'fps': 30}, indent=2) + '\n')
        (comp / 'index.html').write_text(f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>IRIS explanation source: {kind}</title>
<style>html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#0b0f14}}canvas{{display:block}}</style>
</head><body><div data-composition-id="root" data-width="1920" data-height="1080" data-start="0" data-duration="4" data-no-timeline>
<canvas id="stage" class="clip" width="1920" height="1080" data-start="0" data-duration="4" data-track-index="0"></canvas>
</div><script src="engine.js"></script></body></html>\n''')
    print(json.dumps({'scope': 'development_source_asset', 'compositions': list(KINDS), 'duration': 4, 'fps': 30}))


if __name__ == '__main__':
    main()
