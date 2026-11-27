#!/usr/bin/env python3
"""Run codex_plate.py jobs in parallel. argv: spec.json (list of {plate, shot, dest, base, refs})."""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = "/home/reggie/vscode_folder/AI-VIDEO"
V4 = "outputs/ai-city-takeover/ep01/v4/"
D = V4 + "excerpt/flash/design/S31-48/"
specs = json.load(open(sys.argv[1]))
par = int(sys.argv[2]) if len(sys.argv) > 2 else 6
def run(j):
    argv = ["python3", "motion-kit/tools/codex_plate.py", "--book", D + j["shot"] + "/prompt.md", "--plate", j["plate"],
            "--dest", D + j["shot"] + "/" + j["dest"], "--runs", D + j["shot"] + "/runs.md", "--size", "3840x2160"]
    if j.get("base"):
        argv += ["--edit-base", V4 + j["base"]]
    for r in j.get("refs", []):
        argv += ["--ref", V4 + r]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    tail = (p.stdout.strip().splitlines() or [""])[-1][:300]
    print(f"[{p.returncode}] {j['shot']}/{j['dest']} {tail if p.returncode else ''} {p.stderr[-300:] if p.returncode else ''}", flush=True)
with ThreadPoolExecutor(par) as ex:
    list(ex.map(run, specs))
print("ALL DONE", flush=True)
