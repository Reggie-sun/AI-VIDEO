"""One canonical P4 timeline, existing HyperFrames renderer, no direct mux."""
from pathlib import Path
import json,hashlib,base64,io,os,sys
from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.composition import resolve_composition
from ai_video.production.project import load_production_project
from ai_video.production.commercial_graphics import GraphicTreatment,GraphicRole
from ai_video.production.text_design import TextDesign,TextVisualNode,TextRun,MotionPose
from ai_video.production.text_fonts import EmbeddedFont
from ai_video.production.hyperframes import HyperFramesAdapter,HyperFramesRenderAttempt,_NetworkIsolatedHyperFramesRunner,decoded_audio_sha256_fd_with_executable,probe_clip_fd_with_executable
V=Path(__file__).resolve().parent;REPO=Path.cwd();TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin');BROWSER=Path('/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome')
def font(path,text,face=0,family=None):
 from fontTools import subset
 from fontTools.ttLib import TTFont
 f=TTFont(path,fontNumber=face,recalcTimestamp=False);o=subset.Options();o.name_IDs=[0,1,2,3,4,5,6,13,14,16,17];s=subset.Subsetter(options=o);s.populate(text=text);s.subset(f);family=family or sorted({n.toUnicode() for n in f['name'].names if n.nameID in {1,16}})[0];b=io.BytesIO();f.save(b);raw=b.getvalue();return EmbeddedFont(family=family,sha256=hashlib.sha256(raw).hexdigest(),data_base64=base64.b64encode(raw).decode(),license='Noto CJK SIL OFL1.1 / DejaVu Bitstream Vera and public domain additions; system distribution font, subset only')
def title_graphic():
 serif=font('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc','失帧',2,'Noto Serif CJK SC');sans=font('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','翌夜',2,'Noto Sans CJK SC')
 nodes=(TextVisualNode(node_id='black-field',purpose='A continuous near-black title field, no underlying source image leaks',x_px=0,y_px=0,width_px=1920,height_px=1080,path='M0 0 L1920 0 L1920 1080 L0 1080 Z',fill='#080E13'),TextVisualNode(node_id='film-title',purpose='Restrained original Chinese film title',x_px=864,y_px=475,width_px=300,height_px=140,runs=(TextRun(text='失帧',font_family=serif.family,font_size_px=86,tracking_px=20,color='#DCE3E8'),),motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=8),MotionPose(frame=52),MotionPose(frame=62,opacity_milli=0))),TextVisualNode(node_id='next-night',purpose='Previous-night incident flows into the original next-night S01',x_px=929,y_px=579,width_px=130,height_px=60,runs=(TextRun(text='翌夜',font_family=sans.family,font_size_px=24,tracking_px=6,color='#AEBCC8'),),motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=60,opacity_milli=0),MotionPose(frame=66),MotionPose(frame=83))))
 design=TextDesign(intent='A cool, quiet film title after the ordinary answer; no glitch logo, jump scare or rule explanation.',hierarchy='失帧 then 翌夜, with a clear cut into the existing convenience-store film.',reference_width_px=1920,reference_height_px=1080,fonts=(serif,sans),nodes=nodes)
 return GraphicTreatment(graphic_id='shizhen-title-and-night',role=GraphicRole.HEADLINE,text=design.text,shot_id='TITLE',start_frame_offset=0,duration_frames=84,x_milli=0,y_milli=0,width_milli=1000,font_size_px=86,font_weight=400,text_color='#DCE3E8',z_index=100,text_design=design)
def clock_graphics():
 mono=font('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf','0123456789: ',family='DejaVu Sans Mono')
 result=[]
 def add(identity,text,shot,start,frames):
  node=TextVisualNode(node_id=identity,purpose='Exact diegetic clock on the existing blank shelter panel',x_px=0,y_px=0,width_px=230,height_px=60,runs=(TextRun(text=text,font_family=mono.family,font_size_px=30,color='#AEBCC8'),))
  design=TextDesign(intent='Accurate clock glyphs added in post; stop before truck occludes the panel, never float text on its side.',hierarchy='A small physical clue, no explanatory system graphics.',reference_width_px=230,reference_height_px=60,fonts=(mono,),nodes=(node,))
  result.append(GraphicTreatment(graphic_id=identity,role=GraphicRole.HEADLINE,text=text,shot_id=shot,start_frame_offset=start,duration_frames=frames,x_milli=860,y_milli=16,width_milli=120,font_size_px=30,font_weight=400,text_color='#AEBCC8',z_index=20,text_design=design))
 for k in range(7):add('clock-before-'+str(k),f'03:16:{53+k:02d}','CO-A1',k*24,24 if k<6 else 18)
 add('clock-after','03:17:11','CO-A2',84,12)
 return tuple(result)
def main():
 os.environ['PATH']=str(TOOLS)+os.pathsep+os.environ.get('PATH',os.defpath);inputs=json.loads((V/'input-receipt.json').read_bytes());p=load_production_project(Path(inputs['project'])/'project.yaml');rows=inputs['sources'];style=CaptionStyleReference.model_validate(inputs['style']);layers=[];audio=[]
 for row in rows:
  layers.append(CompositionLayerSpec(layer_id='original-visual-'+row['shot_id'],shot_id=row['shot_id'],asset_role='primary_visual',asset_id=row['asset_id'],trim_start_frame=row['start'],trim_duration_frames=row['frames'],source_audio_policy='KEEP',transform=FixedTransform.model_validate(row['transform'])))
  audio.append(AudioTrackSpec(track_id='original-mix-'+row['shot_id'],audio_kind='dialogue',asset_id=row['audio_id'],shot_id=row['shot_id'],trim_start_sample=row['start']*2000,trim_duration_samples=row['frames']*2000))
 layers.insert(3,CompositionLayerSpec(layer_id='title-base',shot_id='TITLE',asset_role='primary_visual',asset_id='co-before-image'))
 audio.append(AudioTrackSpec(track_id='missing-response-title',audio_kind='bgm',asset_id=inputs['music_asset_id'],start_sample=400*2000,trim_duration_samples=84*2000,gain_millidb=-8500,fade_in_samples=8000,fade_out_samples=16000))
 spec=seal_artifact(CompositionSpec(artifact_id='two-passengers-final-review-composition',schema_version='2.3',revision=1,content_hash='0'*64,creation_receipt_id='two-passengers-editorial-repair',source_provenance=p.project.source_provenance,composition_id='two-passengers-plus-S01-v1',shot_ids=tuple(inputs['order']),layers=tuple(layers),transitions=tuple(TransitionSpec(from_shot_id=a,to_shot_id=b,kind='cut',duration_frames=0) for a,b in zip(inputs['order'],inputs['order'][1:])),delivery_profile=p.project.delivery_profile,sample_rate=48000,requested_renderer='hyperframes',audio_tracks=tuple(audio),caption_tracks=(CaptionTrackBinding(binding_id='protected-S01-bilingual',caption_asset_id=inputs['caption_id'],source_audio_track_id='original-mix-S01',shot_id='S01',style_reference=style),),text_layers=(*clock_graphics(),title_graphic())))
 timeline=resolve_composition(p,spec,renderer_version='0.7.103');assert (timeline.total_frames,timeline.total_samples)==(868,1736000);assert timeline.usage_scope=='development_audio_preview';music=next(x for x in timeline.audio_spans if x.track_id=='missing-response-title');s01=next(x for x in timeline.audio_spans if x.track_id=='original-mix-S01');assert music.start_sample+music.duration_samples==s01.start_sample
 (V/'composition-spec.json').write_text(spec.model_dump_json(indent=2));(V/'resolved-timeline.json').write_text(timeline.model_dump_json(indent=2));print(json.dumps({'resolved':True,'frames':timeline.total_frames,'cold_open_seconds':484/24,'no_music_over_S01':True}),flush=True)
 if sys.argv[1:]==['--resolve-only']:return
 stage=REPO/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-composition-v1/render-001';stage.mkdir(mode=0o700,exist_ok=True);os.chmod(stage,0o700);ip=Path('/usr/sbin/ip').resolve(strict=True)
 class Runner(_NetworkIsolatedHyperFramesRunner):
  def run(self,command,args,**kw):
   r=super().run(command,args,**kw);(stage/(command+'-diagnostic.json')).write_text(json.dumps({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2));return r
 runner=Runner(project_root=REPO,binary=REPO/'node_modules/.bin/hyperframes',browser_path=BROWSER,ip_path=ip,unshare_path=Path('/usr/bin/unshare'),bash_path=Path('/usr/bin/bash'))
 adapter=HyperFramesAdapter(runner=runner,expected_version='0.7.103',browser_path=BROWSER,ip_path=ip,decoded_audio=lambda fd,rate,channels:decoded_audio_sha256_fd_with_executable(fd,rate,channels,TOOLS/'ffmpeg'),probe=lambda fd:probe_clip_fd_with_executable(fd,TOOLS/'ffprobe'))
 selection=RendererSelectionReceipt(receipt_id='two-passengers-S01-render-v1',attempt_id='two-passengers-S01-render-v1',requested_kind='hyperframes',selected_kinds=('hyperframes',),renderer_version='0.7.103',timeline_fingerprint=timeline.composition_fingerprint,current_project=p.manifest.active_project,current_registry=p.manifest.active_registry)
 assets={span.asset_id:p.asset_paths[span.asset_id] for span in (*timeline.visual_spans,*timeline.audio_spans)};assets.update({cue.caption_asset_id:p.asset_paths[cue.caption_asset_id] for cue in timeline.caption_cues});assets[style.artifact_id]=p.root/style.path;before=(p.root/'state/manifest.json').read_bytes()
 r=adapter.render(HyperFramesRenderAttempt(attempt_id=selection.attempt_id,selection=selection,timeline=timeline,asset_sources=assets,allowed_asset_root=p.root,staging_root=stage/'source',allowed_staging_parent=stage,output_path=stage/'output/失帧-两位冷开场加S01-1080p审看版.mp4',verification_snapshot_path=stage/'verified.mp4'))
 assert before==(p.root/'state/manifest.json').read_bytes();assert all(c.error_count==0 and c.exit_code==0 for c in r.checks)
 report={'output':str(r.output.untrusted_staged_path),'sha256':r.output.output_sha256,'bytes':r.output.output_size_bytes,'measured':r.output.measured.model_dump(mode='json'),'checks':[c.model_dump(mode='json') for c in r.checks],'timeline_fingerprint':timeline.composition_fingerprint,'usage_scope':timeline.usage_scope,'production_activation':False,'publication_state':'NOT_PUBLISHED','human_review':'PENDING','new_paid_calls':0};(V/'render-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
