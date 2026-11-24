#!/usr/bin/env bash
# Offline + no-cost prep for one approved Seedance unit: draft, add an empty canvas node, write profile/bound,
# materialize, prepare, start. Never submits. Usage: prep_unit.sh UNIT SECONDS MODE(first_frame|multimodal) CEILING
set -euo pipefail
U=$1; S=$2; M=$3; C=$4
export SD_TRIAL=${TRIAL_DIR:-outputs/ai-city-takeover/ep01/v4/pilot/sd-$U}
G=outputs/ai-city-takeover/ep01/v4/gen
q() { grep -v 'UserWarning\|validate_director_coverage' || true; }
uv run python $G/unit.py draft $U 2>&1 | q | tail -1
[ -f $SD_TRIAL/$U/node-created.json ] || node $G/addnode.cjs $SD_TRIAL/$U | tail -1
python3 - "$U" "$S" "$M" "$C" <<'PY'
import json,sys,datetime
U,S,M,C=sys.argv[1],int(sys.argv[2]),sys.argv[3],int(sys.argv[4])
import os; T=os.environ['SD_TRIAL']
node=json.load(open(f'{T}/{U}/node-created.json'))['node_id']
appr=json.load(open(f'{T}/preview-approval.json'))
json.dump({"model_id":"seedance_2.0_vip","input_mode":M,"account_sha256":"72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe","project_id":"829df260-5a63-4f0d-8265-8353dc693b3b","node_id":node,"duration_seconds":S,"resolution":"4k","aspect_ratio":"16:9","benefit_amount":S,"benefit_type":"seedance_20_pro_4k_output","credit_upper_bound":C},open(f'{T}/{U}/profile.json','w'),indent=1)
now=datetime.datetime.now(datetime.timezone.utc)
json.dump({"schema_version":"iris-v4-unit/1","unit":U,"task":f"IRIS EP01 v4 {U}; Seedance 2.0 VIP {M}, {S} s 4k 16:9","user_quote":appr["user_quote"],"preview_approval":f"{T}/preview-approval.json",
 **(appr.get("bound_ids") or {"attempt_id":f"iris-{U.lower()}-source-001","policy_id":f"iris-{U.lower()}-source-001","reservation_id":f"iris-{U.lower()}-reservation-001"}),"max_submit_count":1,"automatic_retries":0,"operator_currency":"CRD","operator_ceiling":C,
 "ledger":"ledger.json","cumulative_submit_ceiling":1,"cumulative_operator_credit_ceiling":C,"issued_at":now.isoformat(timespec='seconds'),"expires_at":(now+datetime.timedelta(hours=6)).isoformat(timespec='seconds'),"stop_on_unknown":True},open(f'{T}/{U}/operator-bound.json','w'),ensure_ascii=False,indent=1)
PY
uv run python $G/unit.py materialize $U --profile $SD_TRIAL/$U/profile.json 2>&1 | q | tail -1
uv run python $G/operator.py prepare $U 2>&1 | q | tail -1
uv run python $G/operator.py start $U 2>&1 | q | tail -1
