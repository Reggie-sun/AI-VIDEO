"""Development-only durable one-use operator for exact Gemini audio requests."""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from ai_video.production.paths import _read_regular_file_nofollow
from ai_video_mcp.audio_understanding import (
    AudioUnderstandingError, GeminiAudioAnalyzer, PreparedAudioRequest, _verify_prepared_request,
)
from ai_video_mcp.tools.audio_understand import AudioUnderstandingRuntime


_MODEL = "gemini-3.8-flash"
_ORIGIN = "https://generativelanguage.googleapis.com"
_ENDPOINT = f"{_ORIGIN}/v1beta/models/{_MODEL}:generateContent"
_AUTH_REF = re.compile(r"user-[A-Za-z0-9][A-Za-z0-9_.:-]{0,122}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_WINDOW = timedelta(minutes=30)
_LIMIT = 50_000
_INTENT, _RESERVATION, _LOCK, _CONSUME, _OUTCOME = (
    "intent.json", "reservation.json", ".operator.lock", "consume.json", "outcome.json",
)


def _error(code: str, outcome: str, message: str) -> AudioUnderstandingError:
    return AudioUnderstandingError(code, outcome, message)


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8") + b"\n"


def _decode(data: bytes) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result
    value = json.loads(data, object_pairs_hook=pairs,
                       parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    if not isinstance(value, dict) or _json(value) != data:
        raise ValueError
    return value


def _time(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _current(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _error("operator_clock_invalid", "REJECTED", "The audio operator clock is invalid.")
    return value.astimezone(timezone.utc)


def _unit_fd(unit: Path) -> int:
    try:
        if not unit.is_absolute() or unit.resolve(strict=True) != unit:
            raise ValueError
        fd = os.open(unit, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        if not stat.S_ISDIR(os.fstat(fd).st_mode) or os.fstat(fd).st_uid != os.getuid():
            os.close(fd)
            raise ValueError
        return fd
    except (OSError, ValueError):
        raise _error("operator_unit_invalid", "REJECTED", "The audio operator unit is unsafe or unavailable.") from None


def _read(fd: int, name: str) -> bytes:
    handle = None
    try:
        handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        info = os.fstat(handle)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 2_000_000:
            raise ValueError
        chunks = []
        while chunk := os.read(handle, 256 * 1024):
            chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) != os.fstat(handle).st_size:
            raise ValueError
        return data
    except (OSError, ValueError):
        raise _error("operator_unit_invalid", "REJECTED", "The audio operator unit evidence is unsafe.") from None
    finally:
        if handle is not None:
            os.close(handle)


def _write(fd: int, name: str, data: bytes) -> None:
    handle = None
    try:
        handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=fd)
        os.fchmod(handle, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(handle, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        os.fsync(handle)
    finally:
        if handle is not None:
            os.close(handle)


def _exists(fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        raise _error("operator_unit_invalid", "REJECTED", "The audio operator unit state is unsafe.") from None


def _lock(fd: int) -> int:
    try:
        handle = os.open(_LOCK, os.O_RDWR | os.O_NOFOLLOW, dir_fd=fd)
        if not stat.S_ISREG(os.fstat(handle).st_mode) or os.fstat(handle).st_uid != os.getuid():
            os.close(handle)
            raise ValueError
        fcntl.flock(handle, fcntl.LOCK_EX)
        return handle
    except (OSError, ValueError):
        raise _error("operator_lock_unknown", "UNKNOWN", "The audio operator lock could not be acquired.") from None


def _unlock(handle: int | None) -> None:
    if handle is not None:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            os.close(handle)


def _media(path: Path):
    try:
        if not path.is_absolute() or path.resolve(strict=True) != path:
            raise ValueError
        source = _read_regular_file_nofollow(path, contained_by=path.parent.resolve(strict=True))
        if source.size_bytes <= 0 or source.size_bytes > 128 * 1024 * 1024:
            raise ValueError
        return {"path": str(path), "sha256": source.file_sha256, "size_bytes": source.size_bytes}, source.data
    except (OSError, ValueError):
        raise _error("operator_source_invalid", "REJECTED", "The exact audio source is unsafe or unavailable.") from None


def _binding(prepared: PreparedAudioRequest) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        _verify_prepared_request(prepared)
        if prepared.model_id != _MODEL or prepared.endpoint != _ENDPOINT:
            raise ValueError
        payload = json.loads(prepared._payload)
        parts = payload["contents"][0]["parts"]
        preview = prepared.preview()
        wire_hash = hashlib.sha256(prepared._payload).hexdigest()
        request = {"preview": preview, "wire_sha256": wire_hash}
        egress = {
            "method": "POST", "origin": _ORIGIN, "endpoint": _ENDPOINT,
            "content_type": "application/json", "audio_sha256": prepared.audio_sha256,
            "audio_size_bytes": prepared.audio_size_bytes, "request_fingerprint": prepared.request_fingerprint,
            "wire_sha256": wire_hash,
            "prompt_sha256": hashlib.sha256(parts[0]["text"].encode("utf-8")).hexdigest(),
            "schema_sha256": hashlib.sha256(_json(payload["generationConfig"]["responseSchema"])).hexdigest(),
        }
        return request, egress
    except Exception:
        raise _error("prepared_request_invalid", "REJECTED", "The prepared audio request is not the fixed Gemini request.") from None


def prepare_operator_unit(
    unit_dir: Path, *, media_path: Path, prepared: PreparedAudioRequest,
    authorization_reference: str, issued_at: datetime, expires_at: datetime,
    upper_bound_microunits: int = 50_000,
) -> dict[str, str | int]:
    """Persist a fresh immutable development intent and its one-call reservation."""
    if not isinstance(authorization_reference, str) or not _AUTH_REF.fullmatch(authorization_reference):
        raise _error("authorization_reference_invalid", "REJECTED", "A user authorization reference is required.")
    if type(upper_bound_microunits) is not int or upper_bound_microunits != _LIMIT:
        raise _error("operator_budget_invalid", "REJECTED", "The authorized audio upper bound is fixed for this unit.")
    try:
        issued, expires, now = datetime.fromisoformat(_time(issued_at)), datetime.fromisoformat(_time(expires_at)), datetime.now(timezone.utc)
        if not issued <= now < expires or expires - issued > _MAX_WINDOW:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        raise _error("operator_window_invalid", "REJECTED", "The audio window must be current and at most 30 minutes.") from None
    source, source_data = _media(Path(media_path))
    request, egress = _binding(prepared)
    if source["sha256"] != prepared.source_sha256 or source["size_bytes"] != prepared.source_size_bytes:
        raise _error("operator_source_mismatch", "REJECTED", "The source file differs from the prepared audio request.")
    if Path(source["path"]).suffix.lower() == ".wav":
        try:
            audio = base64.b64decode(json.loads(prepared._payload)["contents"][0]["parts"][1]["inline_data"]["data"], validate=True)
        except Exception:
            raise _error("prepared_request_invalid", "REJECTED", "The prepared WAV request is invalid.") from None
        if audio != source_data:
            raise _error("operator_audio_source_mismatch", "REJECTED", "The prepared WAV differs from the exact source bytes.")

    intent = {
        "schema_version": "audio-development-intent/1", "scope": "DEVELOPMENT_ONLY",
        "operation": "audio_understand", "authorization": {"source": "user", "reference": authorization_reference},
        "issued_at": _time(issued), "expires_at": _time(expires), "provider": "gemini",
        "model_id": _MODEL, "origin": _ORIGIN, "endpoint": _ENDPOINT, "source": source,
        "request": request, "egress": egress,
        "budget": {"source": "operator_internal_upper_bound", "currency": "USD",
                   "unit": "microdollars", "upper_bound_microunits": _LIMIT},
        "submit_count": 1,
    }
    intent_bytes = _json(intent)
    intent_hash = hashlib.sha256(intent_bytes).hexdigest()
    reservation_bytes = _json({
        "schema_version": "audio-development-reservation/1", "scope": "DEVELOPMENT_ONLY",
        "operation": "audio_understand", "intent_sha256": intent_hash, "currency": "USD",
        "unit": "microdollars", "reserved_microunits": _LIMIT, "submit_count": 1,
    })
    unit = Path(unit_dir)
    try:
        if not unit.is_absolute():
            raise ValueError
        unit.parent.mkdir(parents=True, exist_ok=True)
        unit.mkdir(mode=0o700, exist_ok=False)
        fd = _unit_fd(unit)
    except (OSError, ValueError):
        raise _error("operator_unit_exists", "REJECTED", "The audio operator unit must be a new directory.") from None
    try:
        _write(fd, _INTENT, intent_bytes)
        _write(fd, _RESERVATION, reservation_bytes)
        _write(fd, _LOCK, b"")
        os.fsync(fd)
        if _read(fd, _INTENT) != intent_bytes or _read(fd, _RESERVATION) != reservation_bytes:
            raise OSError
    except Exception:
        os.close(fd)
        raise _error("operator_seal_failed", "UNKNOWN", "The audio intent or reservation could not be durably sealed.") from None
    os.close(fd)
    return {
        "unit_dir": str(unit), "intent_path": str(unit / _INTENT), "intent_sha256": intent_hash,
        "reservation_path": str(unit / _RESERVATION),
        "reservation_sha256": hashlib.sha256(reservation_bytes).hexdigest(),
        "source_sha256": source["sha256"], "source_size_bytes": source["size_bytes"],
        "submit_count": 1, "upper_bound_microunits": _LIMIT,
    }


def _validate(intent, reservation, intent_hash, clock):
    try:
        preview, source, egress = intent["request"]["preview"], intent["source"], intent["egress"]
        issued, expires = datetime.fromisoformat(intent["issued_at"]), datetime.fromisoformat(intent["expires_at"])
        now = _current(clock)
        if (set(intent) != {"schema_version", "scope", "operation", "authorization", "issued_at", "expires_at",
                            "provider", "model_id", "origin", "endpoint", "source", "request", "egress", "budget", "submit_count"}
                or intent["schema_version"] != "audio-development-intent/1" or intent["scope"] != "DEVELOPMENT_ONLY"
                or intent["operation"] != "audio_understand" or intent["authorization"]["source"] != "user"
                or not _AUTH_REF.fullmatch(intent["authorization"]["reference"])
                or intent["provider"] != "gemini" or intent["model_id"] != _MODEL
                or intent["origin"] != _ORIGIN or intent["endpoint"] != _ENDPOINT or intent["submit_count"] != 1
                or intent["budget"] != {"source": "operator_internal_upper_bound", "currency": "USD",
                                         "unit": "microdollars", "upper_bound_microunits": _LIMIT}
                or set(source) != {"path", "sha256", "size_bytes"}
                or source["sha256"] != preview["source_sha256"] or source["size_bytes"] != preview["source_size_bytes"]
                or preview["operation"] != "audio_understand" or preview["provider"] != "gemini"
                or preview["model_id"] != _MODEL or preview["endpoint"] != _ENDPOINT
                or not _SHA256.fullmatch(preview["audio_sha256"])
                or not _SHA256.fullmatch(preview["request_fingerprint"])
                or not _SHA256.fullmatch(intent["request"]["wire_sha256"])
                or set(egress) != {"method", "origin", "endpoint", "content_type", "audio_sha256", "audio_size_bytes",
                                   "request_fingerprint", "wire_sha256", "prompt_sha256", "schema_sha256"}
                or egress != {"method": "POST", "origin": _ORIGIN, "endpoint": _ENDPOINT,
                              "content_type": "application/json", "audio_sha256": preview["audio_sha256"],
                              "audio_size_bytes": preview["audio_size_bytes"],
                              "request_fingerprint": preview["request_fingerprint"],
                              "wire_sha256": intent["request"]["wire_sha256"],
                              "prompt_sha256": egress["prompt_sha256"], "schema_sha256": egress["schema_sha256"]}
                or not all(_SHA256.fullmatch(egress[key]) for key in ("prompt_sha256", "schema_sha256"))
                or reservation != {"schema_version": "audio-development-reservation/1", "scope": "DEVELOPMENT_ONLY",
                                   "operation": "audio_understand", "intent_sha256": intent_hash, "currency": "USD",
                                   "unit": "microdollars", "reserved_microunits": _LIMIT, "submit_count": 1}
                or expires <= issued or expires - issued > _MAX_WINDOW or now < issued or now >= expires):
            raise ValueError
    except Exception:
        raise _error("operator_seal_invalid", "REJECTED", "The audio intent, reservation, request, or window is invalid.") from None
    current_source, _data = _media(Path(source["path"]))
    if current_source != source:
        raise _error("operator_source_changed", "REJECTED", "The exact audio source no longer matches its intent.")


def _load_unit(fd, intent_hash, clock):
    raw = _read(fd, _INTENT)
    if hashlib.sha256(raw).hexdigest() != intent_hash:
        raise _error("operator_intent_hash_mismatch", "REJECTED", "The sealed audio intent hash differs from the expected value.")
    try:
        intent, reservation = _decode(raw), _decode(_read(fd, _RESERVATION))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise _error("operator_seal_invalid", "REJECTED", "The sealed audio operator files are invalid.") from None
    _validate(intent, reservation, intent_hash, clock)
    return intent


def _outcome(unit, intent_hash, clock, *, status, code, result=None, permit=None):
    if permit is not None and not permit.recordable:
        return
    fd = permit.fd if permit is not None else _unit_fd(unit)
    own_fd = permit is None
    lock = permit.lock_fd if permit is not None else None
    own_lock = lock is None
    try:
        if own_lock:
            lock = _lock(fd)
        if _exists(fd, _OUTCOME):
            return
        consumed = _exists(fd, _CONSUME)
        if permit is not None and consumed and not permit.consumed:
            return
        receipt = {
            "schema_version": "audio-development-outcome/1", "intent_sha256": intent_hash,
            "recorded_at": _time(_current(clock)), "status": status, "code": code,
            "outcome": "OBSERVATION_AVAILABLE" if status == "SUCCEEDED" else ("UNKNOWN" if status == "UNKNOWN" else "REJECTED"),
            "consumed": consumed, "evidence": result or {},
            "qa_acceptance": "NOT_EVALUATED", "human_acceptance": "NOT_EVALUATED",
        }
        _write(fd, _OUTCOME, _json(receipt))
        os.fsync(fd)
    except AudioUnderstandingError:
        raise
    except Exception:
        raise _error("operator_receipt_unknown", "UNKNOWN", "The audio outcome receipt could not be durably sealed.") from None
    finally:
        if own_lock:
            _unlock(lock)
        if own_fd:
            os.close(fd)


class _Permit:
    def __init__(self, unit, intent, intent_hash, clock):
        self.unit, self.intent, self.intent_hash, self.clock = unit, intent, intent_hash, clock
        self.fd = _unit_fd(unit)
        self.lock_fd = None
        self.recordable = False
        self.consumed = False

    def _release(self):
        _unlock(self.lock_fd)
        self.lock_fd = None

    def close(self):
        self._release()
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def claim(self):
        self.lock_fd = _lock(self.fd)
        if _exists(self.fd, _CONSUME) or _exists(self.fd, _OUTCOME):
            self._release()
            return
        self.recordable = True
        try:
            _load_unit(self.fd, self.intent_hash, self.clock)
        except AudioUnderstandingError as error:
            _outcome(self.unit, self.intent_hash, self.clock, status="REJECTED", code=error.code, permit=self)
            self._release()
            raise

    def validate(self, preview):
        if not self.recordable:
            return False
        try:
            _load_unit(self.fd, self.intent_hash, self.clock)
            if type(preview) is not dict or _json(preview) != _json(self.intent["request"]["preview"]):
                raise _error("operator_preview_mismatch", "REJECTED", "The request preview differs from the sealed intent.")
            return True
        except AudioUnderstandingError as error:
            _outcome(self.unit, self.intent_hash, self.clock, status="REJECTED", code=error.code, permit=self)
            self._release()
            return False

    def consume(self, preview):
        if not self.recordable or self.lock_fd is None:
            return False
        try:
            _load_unit(self.fd, self.intent_hash, self.clock)
            if type(preview) is not dict or _json(preview) != _json(self.intent["request"]["preview"]):
                raise _error("operator_preview_mismatch", "REJECTED", "The request preview differs from the sealed intent.")
            marker = {"schema_version": "audio-development-consumption/1", "intent_sha256": self.intent_hash,
                      "request_fingerprint": preview["request_fingerprint"], "consumed_at": _time(_current(self.clock)),
                      "submit_count": 1}
            try:
                _write(self.fd, _CONSUME, _json(marker))
                os.fsync(self.fd)
            except Exception:
                self.consumed = _exists(self.fd, _CONSUME)
                raise _error("operator_consume_unknown", "UNKNOWN", "The durable audio permit outcome is unknown.") from None
            self.consumed = True
            self._release()
            return True
        except AudioUnderstandingError as error:
            if error.code != "operator_consume_unknown":
                _outcome(self.unit, self.intent_hash, self.clock, status="REJECTED", code=error.code, permit=self)
                self._release()
                return False
            self._release()
            raise


class _Analyzer(GeminiAudioAnalyzer):
    def __init__(self, credential_supplier, transport, unit, intent_hash, clock):
        super().__init__(credential_supplier, transport=transport)
        self.unit, self.intent_hash, self.clock = unit, intent_hash, clock

    def analyze(self, prepared: PreparedAudioRequest, *, permit: Any) -> dict[str, Any]:
        selected = permit if isinstance(permit, _Permit) else None
        try:
            result = super().analyze(prepared, permit=permit)
            _outcome(self.unit, self.intent_hash, self.clock, status="SUCCEEDED", code="audio_observation_recorded",
                     result=result, permit=selected)
            return result
        except AudioUnderstandingError as error:
            try:
                _outcome(self.unit, self.intent_hash, self.clock,
                         status="UNKNOWN" if error.outcome == "UNKNOWN" else "REJECTED",
                         code=error.code, permit=selected)
            except AudioUnderstandingError:
                raise _error("operator_receipt_unknown", "UNKNOWN", "The audio outcome receipt could not be sealed.") from None
            raise
        finally:
            if selected is not None:
                selected.close()


def runtime_for_unit(unit_dir: Path, expected_intent_sha256: str, *, credential_supplier: Callable[[], str],
                     transport: Any = None, clock: Callable[[], datetime] | None = None) -> AudioUnderstandingRuntime:
    """Reopen a sealed unit through the existing audio MCP runtime contract."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    if not callable(credential_supplier) or not isinstance(expected_intent_sha256, str) or not _SHA256.fullmatch(expected_intent_sha256):
        raise _error("operator_binding_invalid", "REJECTED", "The exact audio operator binding is invalid.")
    unit = Path(unit_dir)
    fd = _unit_fd(unit)
    try:
        if _exists(fd, _CONSUME) or _exists(fd, _OUTCOME):
            raise _error("operator_unit_already_used", "REJECTED", "The audio operator unit is already consumed or closed.")
        intent = _load_unit(fd, expected_intent_sha256, clock)
    finally:
        os.close(fd)

    def permits(_preview):
        permit = _Permit(unit, intent, expected_intent_sha256, clock)
        try:
            permit.claim()
        except AudioUnderstandingError:
            permit.close()
            raise
        try:
            matches = type(_preview) is dict and _json(_preview) == _json(intent["request"]["preview"])
        except Exception:
            matches = False
        if not permit.recordable or not matches:
            if permit.recordable:
                _outcome(unit, expected_intent_sha256, clock, status="REJECTED",
                         code="operator_preview_mismatch", permit=permit)
            permit.close()
            raise _error("operator_preview_mismatch", "REJECTED", "The request preview differs from the sealed intent.")
        return permit

    analyzer = _Analyzer(credential_supplier, transport, unit, expected_intent_sha256, clock)
    return AudioUnderstandingRuntime(analyzer=analyzer, permit_supplier=permits)


def _secret_service_credential() -> str:
    uid = os.getuid()
    bus = Path(f"/run/user/{uid}/bus")
    try:
        info = os.lstat(bus)
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid:
            raise ValueError
        result = subprocess.run(
            ["secret-tool", "lookup", "application", "ai-video", "provider", "gemini-audio",
             "credential", "GEMINI_API_KEY"], capture_output=True, timeout=10, check=False,
            close_fds=True, env={"DBUS_SESSION_BUS_ADDRESS": f"unix:path={bus}", "PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        output = result.stdout.encode() if isinstance(result.stdout, str) else result.stdout
        if result.returncode != 0 or not isinstance(output, bytes) or not 0 < len(output) <= 4096:
            raise ValueError
        credential = output.decode("ascii").rstrip("\r\n")
        if not credential or any(not 0x21 <= ord(char) <= 0x7E for char in credential):
            raise ValueError
        return credential
    except Exception:
        raise _error("credential_unavailable", "REJECTED", "The configured audio credential is unavailable.") from None


def build_runtime() -> AudioUnderstandingRuntime:
    """Read only the explicit unit bindings; never inspect dotenv or ambient credentials."""
    try:
        unit = Path(os.environ["VIDEO_MCP_AUDIO_OPERATOR_UNIT"])
        intent_hash = os.environ["VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256"]
    except Exception:
        raise _error("operator_binding_missing", "REJECTED", "The exact audio operator unit binding is unavailable.") from None
    return runtime_for_unit(unit, intent_hash, credential_supplier=_secret_service_credential)
