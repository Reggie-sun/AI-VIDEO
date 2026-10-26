"""Prepare an isolated development composition through the existing committer."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import subprocess

from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact, canonical_sha256
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes
from ai_video.production.qualification_preview_input import prepare_qualification_preview_input
from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
from ai_video.production.video import ResolvedVideoGenerationRequest, VideoFetchReceipt
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.audio import AudioImportRequest, AudioProbeToolchain
from authoring import UNITS, write

REPO=Path.cwd(); HERE=Path(__file__).resolve().parent
TARGET=REPO/'runs/shizhen-opening-reconstruction-20261026/project-r2'
TOOLS=Path('/home/reggie/.config/jianji/tools/ffmpeg/bin')
OLD=REPO/'outputs/shizhen-episode01/cold-open-execution-20261026/composition/input-receipt.json'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    if (TARGET/'project.yaml').exists():
        raise FileExistsError('Prepared development project already exists; do not rewrite it')
    TARGET.mkdir(parents=True,exist_ok=True,mode=0o700)
    inp=json.loads(OLD.read_text()); old=load_production_project(Path(inp['project'])/'project.yaml')
    protected=[REPO/'docs/superpowers/artifacts/drama/shizhen-episode-01/screenplay.md',
        REPO/'docs/superpowers/artifacts/drama/shizhen-episode-01/production-design.md',
        REPO/'outputs/shizhen-episode01/cinematic-language-lab-20261026/C-refined/失帧-视觉方向-C-概念片.mp4',
        REPO/'outputs/shizhen-episode01/cinematic-language-lab-20261026/C-refined/poster.png',
        old.root/'state/manifest.json',*old.asset_paths.values()]
    protection={str(p.relative_to(REPO)):sha(p.read_bytes()) for p in protected}
    evidence=dict(kind='opening-reconstruction-development/1',
        user_input=(HERE/'creative-input.txt').read_text(),
        scope='New visual opening previs only; not complete dialogue cold-open, not live-action final, no Production/P6 activation',
        prior_art='C-refined exact original retained; its rain/station footage reused without old silhouette overlay',
        audio='Native dialogue explicitly muted in this visual opening; original B recording plus separately licensed rain',
        qualification='Old A3 whole-source FAIL remains; only post-event wide/closeup selected for new visual use',
        new_video_generation_calls=0, source_identity=protection)
    ref=authoring_input_reference(evidence)
    provenance=(*old.project.source_provenance,ref)
    def seal(cls,key,**kw):return seal_artifact(cls(artifact_id='opening-rebuild-'+key,revision=1,
        content_hash='0'*64,creation_receipt_id='opening-reconstruction-authored',source_provenance=provenance,**kw))
    brief=seal(ProductionBrief,'brief',title='失帧 开场重构动态预演',
        objective='从正常的城市秩序收束到两人关系的缺席；让观众比较前后空间而非只观看设计',
        audience='原创都市悬疑观众',format='1920x1080 24fps development previs',language='zh',
        constraints=('No paid video generation','Original B music recording at original speed',
                     'No sister/future date/Linxu reveal','Stock and old CG clearly identified as previs'))
    story=seal(Story,'story',language='zh',logline='城市继续运行，一段关系却被现实删去',
        synopsis='真实动态城市与道路收束到普通候车者；遮挡后只剩一人，空位持续，人物仍如常生活，片名在最后进入玻璃负空间。',
        beats=tuple(StoryBeat(beat_id=u['unit_id'],summary=u['objective']) for u in UNITS))
    shots=[]; old_shots={s.shot_id:s for s in old.shots}
    for u in UNITS:
        seconds=u['duration_seconds']-0.00000001
        if u['unit_id'].startswith('CO-'):
            s=old_shots[u['unit_id']].model_copy(update=dict(artifact_id='opening-rebuild-shot-'+u['unit_id'],
                content_hash='0'*64,revision=1,source_provenance=provenance,
                intent=u['objective']+'；本次视觉片头显式静音原对白，不能当作完整对白场景',
                dialogue='',narration='',storyboard_beat_id=u['unit_id'],
                duration_policy=DurationPolicy(mode='fixed',seconds=seconds)))
            shots.append(seal_artifact(s))
        else:
            asset='stock-'+u['unit_id'].lower()
            shots.append(seal(Shot,'shot-'+u['unit_id'],shot_id=u['unit_id'],scene_id=old.scenes[0].scene_id,
                storyboard_beat_id=u['unit_id'],intent=u['objective']+'；temporary stock，不是同街正式摄影',
                duration_policy=DurationPolicy(mode='fixed',seconds=seconds),character_ids=(),visual_strategy='existing_video',
                required_asset_roles=(AssetRoleRequirement(role='primary_visual',asset_ids=(asset,),allowed_asset_types=(AssetType.VIDEO,)),)))
    board=seal(Storyboard,'board',beats=tuple(StoryboardBeat(beat_id=s.shot_id,scene_id=s.scene_id,
        shot_ids=(s.shot_id,),narrative_intent=s.intent) for s in shots))
    models=[(brief,'creative/brief.yaml'),(story,'creative/story.yaml'),(board,'creative/storyboard.yaml'),
        *((c,'creative/characters/'+c.character_id+'.yaml') for c in old.characters),
        *((s,'creative/scenes/'+s.scene_id+'.yaml') for s in old.scenes),
        *((s,'creative/shots/'+s.shot_id+'.yaml') for s in shots)]
    def ar(m):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,
        path=Path(next(path for obj,path in models if obj==m)))
    project=seal_artifact(ProductionProject(artifact_id='opening-rebuild-project',revision=1,content_hash='0'*64,
        creation_receipt_id='opening-reconstruction-bootstrap',source_provenance=provenance,
        project_id='shizhen-opening-reconstruction-development-20261026',title='失帧 开场重构动态预演',default_language='zh',
        delivery_profile=DeliveryProfile(width=1920,height=1080,fps=24),renderer_policy=RendererPolicy(),
        artifacts=ProjectArtifactRefs(brief=ar(brief),story=ar(story),storyboard=ar(board),
            characters=tuple(ar(c) for c in old.characters),scenes=tuple(ar(s) for s in old.scenes),shots=tuple(ar(s) for s in shots))))
    artifacts={}
    def add(path,raw):
        path=Path(path)
        if path in artifacts:assert artifacts[path].payload==raw,'Conflicting source bytes'
        else:artifacts[path]=PreparedArtifact(path,raw,sha(raw))
    records=[]
    for a in old.registry.assets:
        if a.asset_type in {AssetType.IMAGE,AssetType.MUSIC}:
            records.append(a);add(a.artifact_path,old.asset_paths[a.asset_id].read_bytes())
    for r in old.project.source_provenance:
        if r.reference.startswith('evidence/authoring-input/'):
            add(r.reference,(old.root/r.reference).read_bytes())
    ffversion=subprocess.run([str(TOOLS/'ffmpeg'),'-version'],capture_output=True,text=True,check=True).stdout.split()[2]
    tool=ToolIdentity(name='ffmpeg',version=ffversion)
    chain=AudioProbeToolchain(ffmpeg_path=TOOLS/'ffmpeg',ffprobe_path=TOOLS/'ffprobe',ffmpeg=tool,ffprobe=ToolIdentity(name='ffprobe',version=ffversion))
    origin=dict(source='https://commons.wikimedia.org/wiki/File:Rain_(1).ogg',author='ezwa',license='Public domain',
        source_sha256=sha((HERE/'assets/rain-ezwa-original.ogg').read_bytes()),operation='Decode 45s original to stereo PCM16 48k; no loop/stretch or generated noise')
    fingerprint=canonical_sha256(origin)
    request=AudioImportRequest(asset_id='rain-public-domain',audio_kind='ambience',mime_type='audio/wav',
        source=AudioSource(kind='derived',provider_or_tool=tool,input_artifact_ids=(),input_fingerprint=fingerprint,
            original_reference=origin['source']),provenance_receipt_id=fingerprint,creation_receipt_id='rain-ezwa-decode-48k',
        usage_license='Public domain by ezwa, PDSounds via Wikimedia Commons; decoded stereo48k derivative')
    with (HERE/'assets/rain-ezwa-48k.wav').open('rb') as f:audio=request.prepare(f.fileno(),toolchain=chain)
    records.append(audio.asset_record);add(audio.asset_record.artifact_path,audio.payload)
    truck_source=old.asset_paths['CO-A2-original-mix']
    truck_hash=sha(truck_source.read_bytes())
    truck_request=AudioImportRequest(asset_id='original-truck-pass',audio_kind='sfx',mime_type='audio/wav',
        source=AudioSource(kind='derived',provider_or_tool=tool,input_artifact_ids=('opening-CO-A2',),
            input_fingerprint=truck_hash,original_reference='Original CO-A2 full4s non-dialogue truck/rain mix'),
        provenance_receipt_id=truck_hash,creation_receipt_id='opening-truck-original-sfx',
        usage_license='Exact task-owned CO-A2 original effect mix; no generated new sound or voice')
    with truck_source.open('rb') as f:truck_audio=truck_request.prepare(f.fileno(),toolchain=chain)
    records.append(truck_audio.asset_record);add(truck_audio.asset_record.artifact_path,truck_audio.payload)
    stock=[]
    for label,id,author,page in [('city','5907129','陈权威','https://www.pexels.com/video/city-at-night-5907129/'),
        ('road','36407440','LayG Traveller','https://www.pexels.com/video/night-view-of-urban-traffic-in-china-36407440/')]:
        path=HERE/('assets/'+label+'-24fps.mp4');raw=path.read_bytes();digest=sha(raw)
        with path.open('rb') as f:probe=probe_clip_fd_with_executable(f.fileno(),TOOLS/'ffprobe')
        v=next(s for s in probe['streams'] if s['codec_type']=='video');fps=Fraction(v['avg_frame_rate'])
        capture=dict(kind='stock-video-import-development/1',author=author,page=page,license='https://www.pexels.com/license/',
            source_sha256=sha((HERE/f'assets/pexels-{id}-original.mp4').read_bytes()),derivative_sha256=digest,
            processing='Normal-speed 24fps frame selection, H264, no interpolation; road scaled4K to1080',
            metadata_field_semantics='Legacy VideoAssetMetadata fingerprint fields identify this import operation, not a video generation request',
            measured_probe=probe,usage='temporary dynamic previs; no claim of same physical city/street or final shot')
        fprint=canonical_sha256(capture);ms=int((Decimal(v['duration'])*1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        a=AssetRecord(asset_id='stock-'+label,asset_type=AssetType.VIDEO,artifact_path=Path('assets/files/'+digest+'.mp4'),
            sha256=digest,size_bytes=len(raw),mime_type='video/mp4',duration_seconds=ms/1000,width=v['width'],height=v['height'],
            source_kind=AssetSourceKind.IMPORTED,tool=tool,input_fingerprint=fprint,creation_receipt_id=fprint,
            usage_license='Pexels License free edited previs; '+author+'; '+page,
            video_metadata=VideoAssetMetadata(container_name='mp4',codec_name=v['codec_name'],width=v['width'],height=v['height'],
                fps_numerator=fps.numerator,fps_denominator=fps.denominator,duration_milliseconds=ms,frame_count=int(v['nb_frames']),
                probe_receipt_id='measured-stock-import-'+fprint,request_receipt_fingerprint=fprint,
                resolved_generation_hash=fprint,provenance_receipt_id=fprint))
        records.append(a);add(a.artifact_path,raw)
        stock.append(capture)
    registry=AssetRegistrySnapshot(schema_version='2.2',revision_id='0'*64,content_hash='0'*64,assets=tuple(records))
    h=registry_semantic_sha256(registry);registry=registry.model_copy(update=dict(revision_id=h,content_hash=h))
    rows=[]
    windows={'CO-A1':(8,184),'CO-A2':(0,96),'CO-A3':(336,144)}
    for entry in inp['sources']:
        sid=entry['shot_id']
        if sid not in windows:continue
        start,n=windows[sid];root=Path(entry['raw_root']);source=load_production_project(root/'project.yaml')
        state=next(a.video_generation_state for a in source.manifest.attempts if a.attempt_id==entry['attempt_id'])
        capture=next(a for a in old.registry.assets if a.asset_id==entry['asset_id'])
        from ai_video.production.repair_input_admission import verify_repair_input
        admitted=verify_repair_input(capture,old.root)
        transform=entry['transform']
        use=dict(shot_id=sid,asset_role='primary_visual',trim_start_frame=start,trim_duration_frames=n,
            source_time_map=dict(contract_version='video-time-map/1',audio_policy='mute',
                points=[dict(source_frame=0,output_frame=0),dict(source_frame=n,output_frame=n)]),
            transform=transform,scope='replacement_audio_preview')
        registry,new=prepare_qualification_preview_input(target_root=TARGET,project=project,registry=registry,
            source_root=root,source_attempt_id=entry['attempt_id'],source_sha256=entry['sha256'],
            asset_id='opening-'+sid,usage_license='Task-owned exact original generated source; new development visual use only; historical acceptance unchanged',
            preview_use=use,preview_probe=admitted.preview_probe)
        for item in new:add(item.relative_path,item.payload)
        rows.append(dict(shot_id=sid,asset_id='opening-'+sid,start=start,frames=n,transform=transform,
                         source_sha256=entry['sha256'],source_manifest_sha256=sha((root/'state/manifest.json').read_bytes())))
    for obj,path in models:add(path,_canonical_yaml_bytes(obj))
    add(ref.reference,authoring_input_payload(evidence))
    ProductionStateCommitter(TARGET).bootstrap_initial_state(attempt_id='opening-reconstruction-bootstrap',
        project=project,registry=registry,artifacts=tuple(artifacts[p] for p in sorted(artifacts)))
    reopened=load_production_project(TARGET/'project.yaml')
    assert reopened.project==project
    assert all(sha((REPO/p).read_bytes())==h for p,h in protection.items())
    write('qa/protected-inputs.json',protection)
    write('assets/licenses-and-derivatives.json',dict(stock=stock,rain=origin,
        rejected=['pexels-3130284-original.mp4: actual graphics rather than city; not used; source page not confirmed'],
        reference_footage_in_final=False))
    write('input-receipt.json',dict(project=str(TARGET),rows=rows,music_asset_id=inp['music_asset_id'],
        source_music_sha256=inp['music_source_sha256'],order=[u['unit_id'] for u in UNITS],new_paid_video_calls=0,
        production_activation=False,publication='NOT_PUBLISHED',scope='development_audio_preview'))
    print(json.dumps(dict(project=str(TARGET),assets=len(registry.assets),source_protected=True)))


if __name__=='__main__':main()
