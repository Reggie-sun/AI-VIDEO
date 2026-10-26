from pathlib import Path
from io import BytesIO
import json,hashlib,subprocess
from PIL import Image
from ai_video.production.image_import_video_frame import VideoFrameImageImportReferenceBinding,validate_video_frame_reference_bytes,_decode_selected_frame_rgb
D=Path(__file__).resolve().parent.parent;gate=json.loads((D/'qa/CO-A1-post-media-gate.json').read_text());assert gate['verdict']=='PASS' and all(x['verdict']=='PASS' for x in gate['required_findings'])
p=Path(gate['artifact_path']);raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha==gate['artifact_sha256'];idx=192;w,h,rgb=_decode_selected_frame_rgb(raw,idx);b=BytesIO();Image.frombytes('RGB',(w,h),rgb).save(b,format='PNG');png=b.getvalue();ps=hashlib.sha256(png).hexdigest();version=subprocess.run(['ffmpeg','-version'],capture_output=True,text=True,check=True).stdout.splitlines()[0].split()[2]
ref=VideoFrameImageImportReferenceBinding(role='video_frame',source_video_path=Path(f'evidence/video-frame-import/{sha}.mp4'),source_video_sha256=sha,source_video_size_bytes=len(raw),extracted_frame_path=Path(f'evidence/video-frame-import/{ps}.png'),extracted_frame_sha256=ps,extracted_frame_size_bytes=len(png),extracted_frame_width=w,extracted_frame_height=h,frame_index=idx,extraction_contract_version='video-frame-import-v1',extractor_name='ffmpeg',extractor_version=version)
validate_video_frame_reference_bytes(ref,source_video_bytes=raw,extracted_frame_bytes=png,verify_derivation=True)
out=D/'art/CO-A1-terminal-frame-192.png';assert not out.exists();out.write_bytes(png)
record={'schema_version':'exact-generated-video-frame-observation/1','sha256':ps,'size_bytes':len(png),'width':w,'height':h,'generator':'ffmpeg from exact fetched Seedance2.5 MP4; not a new imagegen call','video_frame_binding':ref.model_dump(mode='json'),'source_runtime_path':str(p),'raw_gate':gate,'production_activation':False,'actual_phone_hand':'LEFT but people currently fully occluded'}
(out.with_suffix('.png.record.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'source_frame':idx,'sha256':ps,'width':w,'height':h,'new_generation_calls':0}))
