"""Explicit ElevenLabs speech batch using sealed operator ceilings and P4 gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.elevenlabs import ElevenLabsTransportResponse
from ai_video.production.elevenlabs_batch import ElevenLabsSpeechTestBatch, run_elevenlabs_speech_batch
from ai_video.production.project import load_production_project
from scripts.minimax_speech_batch import _toolchain
from scripts.elevenlabs_performance_context import load_performance_context


class _SecretServiceCredential:
    def api_key(self):
        supplier_env = dict(os.environ)
        supplier_env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{os.getuid()}/bus")
        result = subprocess.run(
            ["secret-tool", "lookup", "application", "ai-video", "provider", "elevenlabs",
             "credential", "ELEVENLABS_API_KEY"], env=supplier_env, capture_output=True, timeout=15, check=False)
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
    parser.add_argument("--root", type=Path)
    parser.add_argument("--source-project", type=Path)
    parser.add_argument("--text", action="append")
    parser.add_argument("--voice-id")
    parser.add_argument("--performance-context", type=Path)
    parser.add_argument("--line-id")
    parser.add_argument("--preview-context", action="store_true")
    parser.add_argument("--audio-tag", action="append", default=[])
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--model-id", choices=("eleven_multilingual_v2", "eleven_v4"),
                        default=None)
    parser.add_argument("--unit-price-microunits", type=int)
    parser.add_argument("--per-call-ceiling-microunits", type=int)
    parser.add_argument("--project-ceiling-microunits", type=int)
    args = parser.parse_args()
    context = None
    if args.performance_context:
        if not args.line_id or args.text or args.audio_tag:
            parser.error("Context mode requires --line-id and excludes --text/--audio-tag")
        context = load_performance_context(args.performance_context, args.line_id)
        if args.model_id is not None and args.model_id != context['model_id']:
            parser.error("Explicit model does not match the context")
        if args.preview_context:
            print(json.dumps(context, ensure_ascii=False))
            return
        if context['authoring_blocked']:
            raise AiVideoError(ErrorCode.VOICE_REQUEST_INVALID,
                "Performance context has an unresolved authoring restriction; execution is blocked.",
                retryable=False)
        args.text = [context['script_text']]
        args.audio_tag = context['audio_tags']
        args.model_id = context['model_id']
    elif args.line_id or args.preview_context:
        parser.error("--line-id/--preview-context requires --performance-context")
    if not args.text:
        parser.error("Provide --text or a selected performance context line")
    for name in ('root', 'source_project', 'voice_id', 'unit_price_microunits',
                 'per_call_ceiling_microunits', 'project_ceiling_microunits'):
        if getattr(args, name) is None:
            parser.error("Execution requires --" + name.replace('_', '-'))
    args.model_id = args.model_id or "eleven_multilingual_v2"
    source = load_production_project(args.source_project)
    source_sha = hashlib.sha256((source.root / "state/manifest.json").read_bytes()).hexdigest()
    source_reference = f"{source.project.project_id}:manifest:{source_sha}"
    if context:
        source_reference += (f":performance-context:{context['context_package_sha256']}"
                             f":line:{args.line_id}")
    batch = ElevenLabsSpeechTestBatch(batch_id=args.root.name, scripts=tuple(args.text),
        voice_id=args.voice_id, language=args.language, model_id=args.model_id,
        unit_price_microunits=args.unit_price_microunits,
        per_call_ceiling_microunits=args.per_call_ceiling_microunits,
        project_ceiling_microunits=args.project_ceiling_microunits,
        source_reference=source_reference)
    if args.audio_tag:
        batch = ElevenLabsSpeechTestBatch.model_validate({
            **batch.model_dump(mode="json"),
            "parameters": {**batch.parameters.model_dump(mode="json"),
                           "audio_tags": args.audio_tag},
        })
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
