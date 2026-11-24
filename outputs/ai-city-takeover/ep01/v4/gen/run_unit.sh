#!/usr/bin/env bash
# One paid Seedance unit after its continuity report is on disk: lint -> exact balance -> ONE submit -> balance ->
# poll until terminal -> fetch -> gate evidence (frames at 4 fps with source sha; sync_check for sung units).
# VOCAL=<key> overrides the vocal file (pilot/audio/<key>.wav) when a spec uses vocal= (e.g. SG05m); 2026-11-22 fix.
# Stops on any failure or a non-succeeded state (no retry). Usage: run_unit.sh UNIT [SONG_T0 for sung units]
set -uo pipefail
U=$1; T0=${2:-}
export SD_TRIAL=${TRIAL_DIR:-outputs/ai-city-takeover/ep01/v4/pilot/sd-$U}
G=outputs/ai-city-takeover/ep01/v4/gen
q() { grep -v 'UserWarning\|validate_director_coverage' || true; }
L=$(uv run python $G/lint.py $U 2>&1 | q | tail -1); echo "lint $L"
echo "$L" | grep -q '"pass": true' || { echo "STOP lint"; exit 2; }
B0=$(node $G/balance.cjs | python3 -c "import json,sys;print(json.load(sys.stdin)['observed_balance'])"); echo "balance_before $B0"
[ -n "$B0" ] || { echo "STOP no balance"; exit 2; }
S=$(uv run python $G/operator.py submit $U 2>&1 | q | tail -1); echo "submit $S"
sleep 5; B1=$(node $G/balance.cjs | python3 -c "import json,sys;print(json.load(sys.stdin)['observed_balance'])"); echo "balance_after $B1 spent $((B0-B1))"
echo "{\"unit\":\"$U\",\"balance_before\":$B0,\"balance_after\":$B1,\"spent\":$((B0-B1)),\"submit\":$S}" > $SD_TRIAL/$U/spend.json
echo "$S" | grep -q '"submitted": true' || { echo "STOP submit not confirmed"; exit 3; }
for i in $(seq 1 80); do P=$(uv run python $G/operator.py poll $U 2>&1 | q | tail -1)
  echo "$P" | grep -q '"running"\|"queued"\|"pending"' || break; sleep 20; done
echo "poll $P"; echo "$P" | grep -q '"succeeded"' || { echo "STOP state"; exit 4; }
F=$(uv run python $G/operator.py fetch $U 2>&1 | q | tail -1); echo "fetch $F"
M=$SD_TRIAL/$U/project/$(echo "$F" | python3 -c "import json,sys;print(json.load(sys.stdin)['artifact_path'])")
O=$SD_TRIAL/$U/gate/frames; mkdir -p $O; sha256sum "$M" | cut -c1-64 > $O/source.sha256
ffmpeg -v error -y -i "$M" -vf "fps=4,scale=1920:-2" $O/f%02d.jpg
echo "media $M"; echo "frames $(ls $O/f*.jpg | wc -l)"
if [ -n "$T0" ]; then uv run python motion-kit/tools/sync_check.py --take "$M" --window outputs/ai-city-takeover/ep01/v4/pilot/audio/${VOCAL:-$U}.wav \
  --song-t0 $T0 --out $SD_TRIAL/$U/gate --name $U-sd --song outputs/ai-city-takeover/ep01/v4/song/master/all-hands-r4-edc6c6bf.wav --review \
  --words outputs/ai-city-takeover/ep01/v4/song/timing/words.json 2>&1 | tail -1 | cut -c1-400; fi
