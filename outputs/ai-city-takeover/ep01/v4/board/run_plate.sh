#!/usr/bin/env bash
# one board plate via codex_plate.py; args: PLATE ref|noref
set -u
B=outputs/ai-city-takeover/ep01/v4/board
[ -s "$B/plates/$1.png" ] && { echo "$1 exists"; exit 0; }
REF=(); [ "$2" = ref ] && REF=(--ref outputs/ai-city-takeover/ep01/v4/face/IRIS-anchor-F1a.png)
python3 motion-kit/tools/codex_plate.py --book "$B/plates-book.md" --plate "$1" --size 1920x1080 "${REF[@]}" \
  --dest "$B/plates/$1.png" --runs outputs/ai-city-takeover/logs/runs.md > "$B/plates/logs/$1.log" 2>&1
tail -n1 "$B/plates/logs/$1.log" | grep -o '"status": "[^"]*"' | sed "s/^/$1 /"
