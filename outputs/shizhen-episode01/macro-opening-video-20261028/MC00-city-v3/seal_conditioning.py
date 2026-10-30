"""Seal prospective review over current exact inputs, not over the rejected proxy."""
import hashlib
import json
from pathlib import Path

from ai_video.production.video_requirement import (
    GenerationIntent, ScaleTransitionEvidence, scale_transition_camera_intent_hash,
)

ROOT=Path.cwd();D=Path(__file__).resolve().parent
row=json.loads((D/'row.json').read_text());data=json.loads((D/'data.json').read_text())
prior=json.loads((D.with_name('MC00-city-v2')/'conditioning-review.json').read_text())['evidence']['scale_transition']
intent=GenerationIntent.model_validate(row['generation']['generation_intent'])
specs=[('first-anchor','anchor_geometry_review',D/'first-frame-1920x1080.png'),
       ('last-anchor','anchor_geometry_review',ROOT/'referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png'),
       ('anchor-review','anchor_geometry_review',D/'pre-generation-feasibility.md'),
       ('raster-normalization','anchor_geometry_review',D/'input-raster-normalization.json'),
       ('route','trajectory',D/'prospective-trajectory.json'),
       ('city-map','trajectory',ROOT/'referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/city-map.svg')]
sources=[{'source_id':key,'kind':kind,'evidence_ref':str(path.relative_to(ROOT)),
          'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for key,kind,path in specs]
findings=prior['findings']
for f in findings:
    if f['finding_id']=='anchor_correspondence':
        f['source_ids'].append('raster-normalization')
        f['rationale']+=' 实际首帧为原屋檐图的纯尺寸适配副本，无重画、裁切或内容添加；源与derivative身份分别保留。'
extension=ScaleTransitionEvidence.create(first_anchor_id=data['images'][0]['asset_id'],
    first_anchor_sha256=sources[0]['sha256'],last_anchor_id=data['images'][1]['asset_id'],
    last_anchor_sha256=sources[1]['sha256'],camera_intent_hash=scale_transition_camera_intent_hash(intent),
    available_duration_seconds=20,sources=sources,findings=findings)
compat=row['generation']['conditioning_compatibility']
compat.update(same_subject_scale=False,composition_compatible=True,screen_order_compatible=True,
    axis_compatible=True,camera_path_reachable=True,character_prop_state_reachable=True,
    action_endpoint_reachable=True,scale_transition=extension.model_dump(mode='json'))
(D/'row.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
(D/'conditioning-review.json').write_text(json.dumps({'scope':'PRE_GENERATION_AUTHORED_FEASIBILITY_ONLY',
    'evidence':compat,'actual_motion_and_sound':'NOT_EVALUATED','human_acceptance':'NOT_EVALUATED'},ensure_ascii=False,indent=2)+'\n')
pending=json.loads((D/'conditioning-review-pending.json').read_text())
pending.update(previous_status=pending['status'],status='REPLACED_BY_EXACT_TYPED_PROSPECTIVE_REVIEW',
               current_review='conditioning-review.json')
(D/'conditioning-review-pending.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'scale_transition_hash':extension.content_hash,'same_subject_scale':False,
                  'first_sha256':sources[0]['sha256'],'six_other_conditions':True}))
