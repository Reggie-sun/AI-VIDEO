"""Explicit ElevenLabs speech batch using sealed operator ceilings and P4 gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ai_video.errors import AiVideoError
from ai_video.production.elevenlabs import ElevenLabsTransportResponse
from ai_video.production.elevenlabs_batch import ElevenLabsSpeechTestBatch, run_elevenlabs_speech_batch
from ai_video.production.project import load_production_project
from scripts.minimax_speech_batch import _toolchain


class _SecretServiceCredential:
    def api_key(self):
        result = subprocess.run(
            ["secret-tool", "lookup", "application", "ai-video", "provider", "elevenlabs",
             "credential", "ELEVENLABS_API_KEY"], capture_output=True, timeout=15, check=False)
        if result.returncode or not result.stdout.strip():
            raise RuntimeError("ElevenLabs Secret Service lookup failed")
        return result.stdout.decode().strip()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _HttpTransport:
    def request(self, request):
        # Resolve the injected capability only at the actual wire boundary.
        headers = dict(request.headers)
        headers["xi-api-key"] = headers["xi-api-key"].api_key()
        wire = Request(request.url + "?" + urlencode(request.query), data=request.body,
                       headers=headers, method=request.method)
        try:
            response = build_opener(_NoRedirect()).open(wire, timeout=90)
        except HTTPError as error:
            response = error
        with response:
            return ElevenLabsTransportResponse(status_code=response.code,
                headers=dict(response.headers.items()), body=response.read(2 * 1024 * 1024 + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--text", action="append", required=True)
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--unit-price-microunits", type=int, required=True)
    parser.add_argument("--per-call-ceiling-microunits", type=int, required=True)
    parser.add_argument("--project-ceiling-microunits", type=int, required=True)
    args = parser.parse_args()
    source = load_production_project(args.source_project)
    source_sha = hashlib.sha256((source.root / "state/manifest.json").read_bytes()).hexdigest()
    batch = ElevenLabsSpeechTestBatch(batch_id=args.root.name, scripts=tuple(args.text),
        voice_id=args.voice_id, language=args.language,
        unit_price_microunits=args.unit_price_microunits,
        per_call_ceiling_microunits=args.per_call_ceiling_microunits,
        project_ceiling_microunits=args.project_ceiling_microunits,
        source_reference=f"{source.project.project_id}:manifest:{source_sha}")
    paths = run_elevenlabs_speech_batch(args.root, batch, transport=_HttpTransport(),
        credential=_SecretServiceCredential(), toolchain=_toolchain())
    print(json.dumps({"batch_id": batch.batch_id, "wav_files": [str(p) for p in paths],
        "actual_cost": "unknown unless provider reported", "quality_acceptance": "NOT_EVALUATED"},
        ensure_ascii=False))


def entrypoint():
    try:
        main()
    except AiVideoError as error:
        print(json.dumps({"status": "stopped", "error_type": type(error).__name__,
                          "code": error.code.value, "retryable": error.retryable}))
        raise SystemExit(1) from None
    except Exception as error:
        print(json.dumps({"status": "stopped", "error_type": type(error).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    entrypoint()
