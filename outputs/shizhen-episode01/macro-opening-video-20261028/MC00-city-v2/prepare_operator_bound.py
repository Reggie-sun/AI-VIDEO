"""New one-call task bound; reopen six known macro outcomes without changing them."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path

from ai_video.production.project import load_production_project

V = Path(__file__).resolve().parent
prior = Path('outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-v1/operator-bound.json')
old = json.loads(prior.read_text())
roots = [x['root'] for x in old['ancestors']] + ['runs/shizhen-macro-opening-20261027/MC03-descent-v1']
items = []
for root in roots:
    loaded = load_production_project(Path(root)/'project.yaml')
    attempts = [a for a in loaded.manifest.attempts if a.operation == 'video_generation']
    assert len(attempts) == 1
    a = attempts[0]; receipt = a.video_generation_state.fetch_receipt
    assert receipt is not None and a.status.value not in {'outcome_unknown', 'interrupted'}
    assert a.paid_provider_state and a.paid_provider_state.phase.value not in {'outcome_unknown', 'submit_intent'}
    items.append({'root': root, 'attempt_id': a.attempt_id, 'known_fetched': True,
        'artifact_sha256': receipt.artifact_sha256,
        'manifest_sha256': hashlib.sha256((Path(root)/'state/manifest.json').read_bytes()).hexdigest()})
assert len(items) == 6
(V/'historical-generation-audit.json').write_text(json.dumps({
    'scope': 'Six macro submits only; old downstairs/door paired unit and unrelated UNKNOWN unchanged',
    'unique_macro_attempts': 6, 'items': items,
    'unknown_other_history_preserved': old['historical_unknown_attempts_preserved'],
    'new_macro_submissions': 0}, ensure_ascii=False, indent=2)+'\n')
source = Path('outputs/shizhen-episode01/cold-open-execution-20261026/video/CO-A1-profile.json')
assert json.loads(source.read_text())['credit_upper_bound'] == 1500
now = datetime.now(timezone.utc)
bound = {
    'authority': 'current-user-task-bounded-operator', 'authorization_quote': '生成视频我看看',
    'provider': 'jimeng', 'model_id': 'seedance_2.5',
    'scope': 'One MC00 continuous20s480p first-last-frame native-audio qualification preview; no MC03+ continuation or activation',
    'preconfigured_bound_source': str(source),
    'preconfigured_bound_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'preconfigured_per_call_credit_upper_bound': 1500,
    'per_call_credit_upper_bound': 1500, 'project_credit_upper_bound': 1500, 'currency': 'CRD',
    'issued_at': now.isoformat(), 'expires_at': (now+timedelta(hours=2)).isoformat(),
    'max_submit_count': 1, 'automatic_retries': 0,
    'macro_paid_submits_before': 6, 'macro_cumulative_ceiling_after_authorized_unit': 7,
    'old_downstairs_door_unit_not_reallocated': True, 'paired_unit_cumulative_ceiling_unchanged': 7,
    'ancestors': items, 'historical_unknown_attempts_preserved': old['historical_unknown_attempts_preserved'],
    'market_quote_claim': False, 'current_quote_credits': 240, 'quote_evidence': 'native-readonly.json',
    'resolution': '480p', 'production_activation': False, 'no_historical_count_reset_or_refund': True,
}
with (V/'operator-bound.json').open('x') as handle:
    json.dump(bound, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps({'known_prior_macro_calls': len(items), 'new_submit_ceiling': 1, 'old_pair_not_reallocated': True}))
