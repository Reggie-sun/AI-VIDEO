"""Explicit live MiniMax Speech test entry; no monetary configuration or prompts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ai_video.production.audio import AudioProbeToolchain
from ai_video.production.minimax_speech import MiniMaxSpeechTransportResponse
from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, run_minimax_speech_batch
from ai_video.production.models import ToolIdentity
from ai_video.production.project import load_production_project


class _SecretServiceCredential:
    def __init__(self, reference_id):
        self._reference_id = reference_id

    def bearer_header(self):
        result = subprocess.run(
            ["secret-tool", "lookup", "application", "ai-video", "provider", "minimax-speech",
             "credential", self._reference_id], capture_output=True, timeout=15, check=False)
        if result.returncode or not result.stdout.strip():
            raise RuntimeError("MiniMax Speech Secret Service lookup failed")
        return "Bearer " + result.stdout.decode().strip()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _HttpTransport:
    def request(self, request):
        opener = build_opener(_NoRedirect())
        wire = Request(request.url, data=request.body, headers=dict(request.headers), method="POST")
        try:
            response = opener.open(wire, timeout=90)
        except HTTPError as error:
            response = error
        with response:
            return MiniMaxSpeechTransportResponse(
                status_code=response.code, headers=dict(response.headers.items()),
                body=response.read(6 * 1024 * 1024 + 1))


def _toolchain():
    values = {}
    for name in ("ffmpeg", "ffprobe"):
        found = shutil.which(name)
        if found is None:
            raise RuntimeError(f"Required audio tool is unavailable: {name}")
        path = Path(found).resolve(strict=True)
        version = subprocess.run([str(path), "-version"], capture_output=True,
                                 text=True, check=True).stdout.splitlines()[0]
        values[name + "_path"] = path
        values[name] = ToolIdentity(name=name, version=version)
    return AudioProbeToolchain(**values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--text", action="append", required=True,
                        help="Repeat for a finite ordered batch; stops on first error.")
    parser.add_argument("--voice-id", default="male-qn-jingying")
    parser.add_argument("--region", choices=("cn", "international"), default="cn",
                        help="cn uses the domestic API and a separate Secret Service credential.")
    args = parser.parse_args()
    source = load_production_project(args.source_project)
    source_sha = hashlib.sha256((source.root / "state/manifest.json").read_bytes()).hexdigest()
    batch = MiniMaxSpeechTestBatch(
        batch_id=args.root.name, scripts=tuple(args.text), voice_id=args.voice_id,
        region="cn" if args.region == "cn" else None,
        source_reference=f"{source.project.project_id}:manifest:{source_sha}")
    paths = run_minimax_speech_batch(args.root, batch, transport=_HttpTransport(),
                                    credential=_SecretServiceCredential(batch.credential_reference_id), toolchain=_toolchain())
    print(json.dumps({"batch_id": batch.batch_id, "wav_files": [str(p) for p in paths],
                      "actual_cost": "unknown unless provider reported",
                      "quality_acceptance": "NOT_EVALUATED"}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never print exception payloads from credential/transport/tool processes.
        print(json.dumps({"status": "stopped", "error_type": type(error).__name__}))
        raise SystemExit(1) from None
