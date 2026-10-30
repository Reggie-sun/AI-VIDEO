"""Exact source/output raster and audio checks; never human acceptance."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from PIL import Image
R=Path.cwd();H=Path(__file__).resolve().parents[1];Q=H/'qa'
receipt=json.loads((H/'render-receipt.json').read_text());out=R/receipt['output']
src=R/'runs/shizhen-macro-opening-20261027/MC03-descent-v1/state/video-generation/fetch/files/326e4fcb83b4bfcd232a3efefab44bd52f0caef6c7be2b3242a0042cca41e43e.mp4'
old=R/'outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-edit-v3/失帧-下楼到达-1080p-到达近景修订03.mp4'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(out.read_bytes())==receipt['sha256']
ff='/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg'
def audio(path):
 return subprocess.check_output([ff,'-v','error','-i',str(path),'-map','0:a:0','-vn','-ar','48000','-ac','2','-f','s16le','pipe:1'])
new_audio,old_audio=audio(out),audio(old)
assert new_audio==old_audio, 'Existing exact decoded audio observation can only be reused with identical PCM'
def tail(path):
 data=subprocess.check_output([ff,'-v','error','-i',str(path),'-vf',"select='between(n,144,191)',crop=760:244:1000:836",'-fps_mode','vfr','-pix_fmt','rgb24','-f','rawvideo','pipe:1'])
 return np.frombuffer(data,dtype=np.uint8).reshape(48,244,760,3)
raw=tail(src);patched=tail(out)
alpha=np.array(Image.open(H/'stair-lock-rgba.png'))[836:1080,1000:1760,3]
opaque=alpha==255
def variation(data):
 return float(data.astype(np.float32).std(axis=0)[opaque].mean())
metrics={'source_opaque_region_mean_temporal_std_rgb':variation(raw),'output_opaque_region_mean_temporal_std_rgb':variation(patched),'scope':'Decoded 6..8s opaque patch pixels only; compression residual is possible; not a perceptual acceptance score'}
assert metrics['output_opaque_region_mean_temporal_std_rgb']<metrics['source_opaque_region_mean_temporal_std_rgb'], 'Static patch must measurably reduce variation'
protected=np.array(Image.open(H/'stair-lock-rgba.png'))[835:899,1290:1581,3]
assert not protected.any()
report={'video_sha256':receipt['sha256'],'source_sha256':sha(src.read_bytes()),'patch_sha256':sha((H/'stair-lock-rgba.png').read_bytes()),'frame_count':192,'first_patch_frame':144,'alpha_zero_in_protected_foot_envelope':True,'metrics':metrics,'decoded_audio_sha256':sha(new_audio),'audio_decoded_bytes':len(new_audio),'audio_identical_to_previous_exact_mp4_sha256':sha(old.read_bytes()),'audio_evidence_reuse':'../MC03-descent-edit-v3/qa/native-audio-result.json; observation belongs to old MP4 and identical decoded audio, not new human listening','new_remote_audio_calls':0,'new_paid_generation_calls':0,'human_acceptance':'NOT_EVALUATED'}
(Q/'patch-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
