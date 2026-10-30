"""Read-only binding of advisory acting context to an exact source dialogue line."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.elevenlabs_performance import compile_synthesis_text
from ai_video.production.voice_parameters import VoiceProviderParameters

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_CONTEXT_BYTES = 128 * 1024


def _invalid() -> AiVideoError:
    return AiVideoError(ErrorCode.VOICE_REQUEST_INVALID,
                        "Performance context is invalid or no longer matches its source.",
                        retryable=False)


def _read_json(path: Path) -> tuple[dict, bytes]:
    """Walk with directory fds so symlink parents cannot redirect the read."""
    absolute = Path(os.path.abspath(path))
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in absolute.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CONTEXT_BYTES:
                raise _invalid()
            raw = stream.read(MAX_CONTEXT_BYTES + 1)
            if len(raw) > MAX_CONTEXT_BYTES:
                raise _invalid()
    finally:
        os.close(directory)

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _invalid()
            result[key] = value
        return result

    data = json.loads(raw, object_pairs_hook=object_pairs)
    if not isinstance(data, dict):
        raise _invalid()
    return data, raw


def _line_map(rows: object) -> dict:
    if not isinstance(rows, list) or not rows:
        raise _invalid()
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise _invalid()
        if not row['id'] or row['id'] in result:
            raise _invalid()
        result[row['id']] = row
    return result


def load_performance_context(path: Path, line_id: str) -> dict:
    """Return offline context; no package status grants execution authorization."""
    try:
        package, raw = _read_json(path)
        reference = package['source_plan']
        if not isinstance(reference, str):
            raise _invalid()
        relative = Path(reference)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise _invalid()
        source, source_bytes = _read_json(REPO_ROOT / relative)
        source_sha = hashlib.sha256(source_bytes).hexdigest()
        if source_sha != package['source_plan_sha256']:
            raise _invalid()
        rows = _line_map(package['rows'])
        sources = _line_map(source['lines'])
        line = rows[line_id]
        exact = sources[line_id]
        for key in ('id', 'text', 'role', 'unit', 'shot_s'):
            if type(line[key]) is not type(exact[key]) or line[key] != exact[key]:
                raise _invalid()
        if not isinstance(line['text'], str) or not line['text']:
            raise _invalid()
        if not isinstance(line['audio_tags'], list):
            raise _invalid()
        parameters = VoiceProviderParameters(audio_tags=line['audio_tags'])
        model = line['model_candidate']
        parameters.validate_route('elevenlabs', model)
        if model not in {'eleven_v4', 'eleven_multilingual_v2'}:
            raise _invalid()
        if not isinstance(package['shared_scene'], str):
            raise _invalid()
        context = line['performance_context']
        for key in ('trigger', 'listener', 'objective', 'subtext', 'delivery', 'after', 'knowledge'):
            if not isinstance(context[key], str) or not context[key]:
                raise _invalid()
        status = package.get('submit_status')
        # Missing/unknown status cannot be interpreted as a clear authoring restriction.
        blocked = (not isinstance(status, str) or status != 'READY_FOR_CANONICAL_PREFLIGHT'
                   or package.get('blocked_by_attempt') is not None
                   or line.get('blocked_by_attempt') is not None)
        synthesis = compile_synthesis_text(line['text'], parameters.audio_tags)
        return {
            'schema': 'elevenlabs-performance-context-preview/1',
            'context_package_sha256': hashlib.sha256(raw).hexdigest(),
            'source_plan': reference, 'source_plan_sha256': source_sha,
            'shared_scene': package['shared_scene'], 'line': line,
            'script_text': line['text'], 'audio_tags': list(parameters.audio_tags),
            'synthesis_text': synthesis,
            'synthesis_sha256': hashlib.sha256(synthesis.encode('utf-8')).hexdigest(),
            'model_id': model, 'authoring_blocked': blocked,
            'network_calls': 0, 'canonical_paid_preview': False,
            'authorization_granted': False,
        }
    except AiVideoError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise _invalid() from None
