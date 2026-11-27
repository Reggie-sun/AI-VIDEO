#!/usr/bin/env bash
# run.sh PLATE DEST [edit-base] [ref ...]  (paths relative to ep01/v4; edit-base "-" = none). Repo root cwd.
set -u
V=outputs/ai-city-takeover/ep01/v4; D=$V/excerpt/flash/design/S31-48/CONT1124
plate=$1; dest=$2; base=$3; shift 3
argv=(python3 motion-kit/tools/codex_plate.py --book $D/prompt.md --plate "$plate" --dest "$D/$dest" --runs $D/runs.md --size 3840x2160)
[ "$base" != "-" ] && argv+=(--edit-base "$V/$base")
for r in "$@"; do argv+=(--ref "$V/$r"); done
"${argv[@]}" > "$D/log-${dest%.png}.txt" 2>&1; echo "[$?] $dest"
