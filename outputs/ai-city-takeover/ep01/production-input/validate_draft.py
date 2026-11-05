"""Validate typed preparation; never bootstrap, submit, activate or compose."""
import argparse
import hashlib
import json
from pathlib import Path

from ai_video.production.models import ProductionBrief, Story, Character, Scene, Storyboard, Shot, SourceReference, DeliveryProfile, RendererPolicy
from ai_video.production.hashing import verify_artifact_hash

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def validate(folder):
    types={'brief.json':ProductionBrief,'story.json':Story,'character-iris.json':Character,
           'storyboard.json':Storyboard,'delivery-profile.json':DeliveryProfile,'renderer-policy.json':RendererPolicy}
    types.update({p.name:Scene for p in folder.glob('scene-*.json')})
    types.update({p.name:Shot for p in folder.glob('shot-*.json')})
    loaded={}
    for name,kind in types.items():
        value=kind.model_validate_json((folder/name).read_bytes())
        if hasattr(value,'content_hash') and not verify_artifact_hash(value):
            raise ValueError(f'Artifact content hash mismatch: {name}')
        loaded[name]=value
    refs=[SourceReference.model_validate(v) for v in json.loads((folder/'source-references.json').read_text())]
    for ref in refs:
        target=(REPO/ref.reference).resolve()
        if not target.is_relative_to(REPO):raise ValueError('Reference escapes repository')
        if hashlib.sha256(target.read_bytes()).hexdigest()!=ref.content_hash:raise ValueError(f'Reference bytes changed: {ref.reference}')
    shots={v.shot_id:v for v in loaded.values() if isinstance(v,Shot)}
    scenes={v.scene_id:v for v in loaded.values() if isinstance(v,Scene)}
    if len(shots)!=8 or len(scenes)!=2:raise ValueError('Expected eight narrative shots across four photographic setups and two scenes')
    for beat in loaded['storyboard.json'].beats:
        if beat.scene_id not in scenes or any(s not in shots for s in beat.shot_ids):raise ValueError('Storyboard reference missing')
    for shot in shots.values():
        if shot.shot_id in ('ep01-intro','ep01-dns'):
            if shot.duration_policy.seconds!=6:raise ValueError('A/C source generation windows must be six seconds')
        elif shot.duration_policy.seconds is not None:raise ValueError('Preparation must not fabricate exact song timing')
        if shot.scene_id not in scenes or any(c!='IRIS' for c in shot.character_ids):raise ValueError('Scene/cast mismatch')
    return {'typed_artifacts_validated':len(loaded),'reference_bytes_verified':len(refs),'final_compose_ready':False,
            'missing_prerequisites':['实际选定歌曲及完整演唱/逐字时间测量','最终Director coverage与镜长决定',
                '已认可参考包对应的exact runtime preview_approval','素材经Registry/committer登记并采用到primary_visual',
                '实际镜头逐镜媒体Gate与最终声画审看'],
            'state_mutations':0,'provider_calls':0,'proof':'development_preparation_only'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifacts',type=Path,default=HERE)
    ap.add_argument('--require-compose-ready',action='store_true',help='Fail closed: this preparation is not a complete Production project.')
    args=ap.parse_args()
    try:result=validate(args.artifacts)
    except (ValueError,OSError) as e:
        print(json.dumps({'status':'invalid','error':str(e)},ensure_ascii=False));return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if args.require_compose_ready else 0


if __name__=='__main__':raise SystemExit(main())
