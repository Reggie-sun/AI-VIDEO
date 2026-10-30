"""Record deterministic FFmpeg input normalization; retain original model PNG."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

d=Path(__file__).resolve().parent
src=d.with_name('MC00-city-v2')
for name in ['native-prompt.zh.txt','profile.json','node-created.json','native-readonly.json',
             'operator-bound.json','historical-generation-audit.json','prospective_trajectory.py',
             'prospective-trajectory.json','pre-generation-feasibility.md']:
    shutil.copyfile(src/name,d/name)
raw=Path('referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/02-eave-start-v1.png')
out=d/'first-frame-1920x1080.png';payload=out.read_bytes();digest=hashlib.sha256(payload).hexdigest()
assert struct.unpack('>II',payload[16:24])==(1920,1080)
record={'kind':'technical-input-raster-normalization/1','source_path':str(raw),
    'source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'source_dimensions':[1672,940],
    'output_path':str(out.relative_to(Path.cwd())),'sha256':digest,'size_bytes':len(payload),
    'width':1920,'height':1080,'operation':'FFmpeg Lanczos scale only; no crop/repaint/content insertion',
    'generator':'FFmpeg input preprocessing; not a new built-in model image',
    'ffmpeg_executable':'/home/reggie/miniconda3/bin/ffmpeg',
    'original_builtin_generation_record':'referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/generation-intent.json',
    'original_preserved':True,'output_video_resolution_remains':'480p','not_1080p_video_quality_claim':True}
(d/'input-raster-normalization.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
script=(src/'prepare_local.py').read_text().replace('MC00-city-v2','MC00-city-v3')
script=script.replace('referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/02-eave-start-v1.png',record['output_path'])
script=script.replace('03e1386dad73448fea3fada774c810b3d8cb0d593f97f3f637e34e3bd5ee2e68',digest)
start=script.index('    if role == "first_frame":');end=script.index('    else:',start)
script=script[:start]+'''    if role == "first_frame":
        normalization = json.loads((HERE / "input-raster-normalization.json").read_text())
        assert normalization["sha256"] == expected
        assert sha(ROOT / normalization["source_path"]) == normalization["source_sha256"]
        record.update(generator="FFmpeg technical input-raster normalization", normalization=normalization,
            original_builtin_source="referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/generation-intent.json")
        tool = {"name": "ffmpeg-lanczos-input-normalization", "version": "configured-ffmpeg"}
''' + script[end:]
(d/'prepare_local.py').write_text(script)
for name in ['bootstrap.py','execute.py']:
    s=(src/name).read_text().replace('MC00-city-v2','MC00-city-v3').replace('-city-v2-20261028','-city-v3-20261028').replace('preview-v2','preview-v3')
    (d/name).write_text(s)
review=(d/'pre-generation-feasibility.md').read_text()
review=review.replace('首帧为 `MC00-reference-revision-20261028/02-eave-start-v1.png`，SHA `03e1386dad73448fea3fada774c810b3d8cb0d593f97f3f637e34e3bd5ee2e68`。',
    '原始屋檐图为 `MC00-reference-revision-20261028/02-eave-start-v1.png`，SHA `03e1386dad73448fea3fada774c810b3d8cb0d593f97f3f637e34e3bd5ee2e68`；实际首帧是纯尺寸适配副本 `first-frame-1920x1080.png`，SHA `'+digest+'`。原图保留，仅FFmpeg Lanczos尺寸转换，无裁切、重画或新增内容。')
(d/'pre-generation-feasibility.md').write_text(review)
(src/'prepare-failed-anchor-geometry.json').write_text(json.dumps({
    'status':'KNOWN_LOCAL_PREPARE_FAILURE_NO_EXTERNAL_EFFECT','diagnostic':'asset_evidence.anchor_geometry',
    'reason':'raw first1672x940 versus last1920x1080','video_attempts_started':0,'paid_submits':0,
    'next_root':'runs/shizhen-macro-opening-20261028/MC00-city-v3',
    'normalization_record':str((d/'input-raster-normalization.json').relative_to(Path.cwd())),
    'original_run_retained':True},indent=2)+'\n')
print(json.dumps({'normalized_first_sha256':digest,'dimensions':[1920,1080],'original_preserved':True}))
