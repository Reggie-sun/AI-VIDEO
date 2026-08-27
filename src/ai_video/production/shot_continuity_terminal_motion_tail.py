"""Frame-exact terminal-window motion-tail materialization for M0."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_contracts import PreparedArtifact, StateCommitRequest
from ai_video.production._video_continuity import C4MotionTailEvidence, TerminalFrameEvidence
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    resolve_dependency_state,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
    canonical_motion_tail_window_analysis_receipt_path,
    canonical_terminal_motion_tail_receipt_path,
    canonical_video_asset_path,
)
from ai_video.production.shot_continuity_motion_analysis import (
    MotionTailWindowAnalysisReceipt,
    analyze_motion_tail_window,
)
from ai_video.production.shot_continuity_motion_tail import (
    _seal_registry,
    _source_lineage,
)
from ai_video.production.shot_continuity_source_runtime import build_source_closure


_SHA256 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SCHEMA = "ai-video-terminal-motion-tail/1"
_RULE = "terminal-window-frame-exact-v1"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _sha256_fd(descriptor: int) -> str:
    digest = hashlib.sha256()
    offset = 0
    while chunk := os.pread(descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    return digest.hexdigest()


class _TailStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class TerminalMotionTailReceipt(_TailStrictModel):
    schema_version: Literal["ai-video-terminal-motion-tail/1"] = _SCHEMA
    source_attempt_id: str = Field(pattern=_SAFE_ID)
    source_shot_id: str = Field(pattern=_SAFE_ID)
    source_shot_revision: int = Field(strict=True, ge=1)
    source_shot_content_hash: str = Field(pattern=_SHA256)
    source_video_asset_id: str = Field(pattern=_SAFE_ID)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_registry_revision_id: str = Field(pattern=_SHA256)
    source_generation_id: str = Field(pattern=_SAFE_ID)
    source_request_input_hash: str = Field(pattern=_SHA256)
    source_resolved_generation_hash: str = Field(pattern=_SHA256)
    source_provenance_receipt_id: str = Field(pattern=_SHA256)
    source_provenance_receipt_sha256: str = Field(pattern=_SHA256)
    source_p6_acceptance_evidence_id: str = Field(pattern=_SHA256)
    source_p6_acceptance_evidence_sha256: str = Field(pattern=_SHA256)
    source_p6_acceptance_receipt_id: str = Field(pattern=_SHA256)
    source_p6_acceptance_receipt_sha256: str = Field(pattern=_SHA256)
    tail_asset_id: str = Field(pattern=_SAFE_ID)
    extracted_sha256: str = Field(pattern=_SHA256)
    extracted_size_bytes: int = Field(strict=True, gt=0)
    extracted_codec_name: str = Field(min_length=1)
    extracted_width: int = Field(strict=True, gt=0)
    extracted_height: int = Field(strict=True, gt=0)
    extracted_fps_numerator: int = Field(strict=True, gt=0)
    extracted_fps_denominator: int = Field(strict=True, gt=0)
    extracted_duration_milliseconds: int = Field(strict=True, gt=0)
    extracted_frame_count: int = Field(strict=True, ge=3)
    selection_rule_version: Literal["terminal-window-frame-exact-v1"]
    start_timestamp_numerator: int = Field(strict=True, ge=0)
    start_timestamp_denominator: int = Field(strict=True, gt=0)
    end_timestamp_numerator: int = Field(strict=True, ge=0)
    end_timestamp_denominator: int = Field(strict=True, gt=0)
    start_frame_index: int = Field(strict=True, ge=0)
    end_frame_index: int = Field(strict=True, ge=0)
    source_fps_numerator: int = Field(strict=True, gt=0)
    source_fps_denominator: int = Field(strict=True, gt=0)
    source_frame_count: int = Field(strict=True, ge=3)
    source_duration_milliseconds: int = Field(strict=True, gt=0)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    provider_min_duration_milliseconds: int = Field(strict=True, gt=0)
    provider_max_duration_milliseconds: int = Field(strict=True, gt=0)
    terminal_frame_evidence: TerminalFrameEvidence
    motion_analysis_receipt_hash: str = Field(pattern=_SHA256)
    extractor: ToolIdentity
    extractor_executable_sha256: str = Field(pattern=_SHA256)
    probe: ToolIdentity
    probe_executable_sha256: str = Field(pattern=_SHA256)
    decoded_frame_sequence_sha256: str = Field(pattern=_SHA256)
    terminal_decoded_frame_sha256: str = Field(pattern=_SHA256)
    canonical_arguments: tuple[str, ...] = Field(min_length=1)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    continuity_constraint_snapshot_hash: str = Field(pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_tail(self) -> "TerminalMotionTailReceipt":
        terminal = self.terminal_frame_evidence
        expected_frames = self.end_frame_index - self.start_frame_index + 1
        if (
            self.tail_asset_id == self.source_video_asset_id
            or self.extracted_sha256 == self.source_video_sha256
            or self.source_p6_acceptance_evidence_id
            != self.source_p6_acceptance_evidence_sha256
            or self.source_p6_acceptance_receipt_id
            != self.source_p6_acceptance_receipt_sha256
            or self.source_provenance_receipt_id
            != self.source_provenance_receipt_sha256
            or self.source_shot_id != terminal.source_shot_id
            or self.source_shot_revision != terminal.source_shot_revision
            or self.source_shot_content_hash != terminal.source_shot_content_hash
            or self.end_frame_index != self.source_frame_count - 1
            or self.end_frame_index != terminal.frame_index
            or self.source_generation_id != terminal.source_generation_id
            or self.source_request_input_hash != terminal.source_request_input_hash
            or self.source_resolved_generation_hash
            != terminal.source_resolved_generation_hash
            or self.source_provenance_receipt_id
            != terminal.source_provenance_receipt_id
            or self.extracted_frame_count != expected_frames
            or self.extracted_codec_name != "h264"
            or self.extracted_width != self.source_width
            or self.extracted_height != self.source_height
            or self.extracted_fps_numerator != self.source_fps_numerator
            or self.extracted_fps_denominator != self.source_fps_denominator
            or not (
                self.provider_min_duration_milliseconds
                <= self.extracted_duration_milliseconds
                <= self.provider_max_duration_milliseconds
            )
            or self.source_video_sha256 != terminal.source_video_sha256
            or self.source_video_asset_id != terminal.source_video_asset_id
            or self.source_registry_revision_id != terminal.source_registry.revision_id
            or self.source_fps_numerator != terminal.source_fps_numerator
            or self.source_fps_denominator != terminal.source_fps_denominator
            or self.source_frame_count != terminal.source_frame_count
            or self.source_duration_milliseconds
            != terminal.source_duration_milliseconds
            or self.source_width != terminal.source_width
            or self.source_height != terminal.source_height
            or self.start_timestamp_numerator * self.source_fps_numerator
            != self.start_frame_index
            * self.source_fps_denominator
            * self.start_timestamp_denominator
            or self.end_timestamp_numerator * terminal.timestamp_denominator
            != terminal.timestamp_numerator * self.end_timestamp_denominator
            or self.extractor.name != "ffmpeg"
            or self.probe.name != "ffprobe"
            or self.canonical_arguments
            != _canonical_arguments(self.start_frame_index, self.end_frame_index)
        ):
            raise ValueError("terminal motion-tail contract is inconsistent")
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        if self.content_hash != _seal(payload):
            raise ValueError("terminal motion-tail receipt hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "TerminalMotionTailReceipt":
        candidate = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": _seal(
                    candidate.model_dump(
                        mode="json", exclude={"content_hash"}, warnings=False
                    )
                ),
            }
        )

    def to_c4_motion_tail_evidence(
        self, *, registry_revision_id: str, tail_asset: AssetRecord
    ) -> C4MotionTailEvidence:
        metadata = tail_asset.video_metadata
        if (
            tail_asset.asset_id != self.tail_asset_id
            or tail_asset.sha256 != self.extracted_sha256
            or tail_asset.source_kind is not AssetSourceKind.DERIVED
            or metadata is None
            or tail_asset.creation_receipt_id != self.content_hash
        ):
            raise _invalid("Terminal motion-tail registry asset is not exact.")
        return C4MotionTailEvidence.create(
            source_shot_id=self.source_shot_id,
            source_shot_revision=self.source_shot_revision,
            source_shot_content_hash=self.source_shot_content_hash,
            source_video_asset_id=self.source_video_asset_id,
            source_video_sha256=self.source_video_sha256,
            source_registry_revision_id=self.source_registry_revision_id,
            source_generation_id=self.source_generation_id,
            source_request_input_hash=self.source_request_input_hash,
            source_resolved_generation_hash=self.source_resolved_generation_hash,
            source_provenance_receipt_id=self.source_provenance_receipt_id,
            source_provenance_receipt_sha256=self.source_provenance_receipt_sha256,
            source_p6_acceptance_evidence_id=self.source_p6_acceptance_evidence_id,
            source_p6_acceptance_evidence_sha256=self.source_p6_acceptance_evidence_sha256,
            registry_revision_id=registry_revision_id,
            extraction_receipt_id=self.content_hash,
            extraction_receipt_sha256=self.content_hash,
            materialization_receipt_id=self.content_hash,
            materialization_receipt_sha256=self.content_hash,
            selection_rule_version=self.selection_rule_version,
            start_timestamp_numerator=self.start_timestamp_numerator,
            start_timestamp_denominator=self.start_timestamp_denominator,
            end_timestamp_numerator=self.end_timestamp_numerator,
            end_timestamp_denominator=self.end_timestamp_denominator,
            start_frame_index=self.start_frame_index,
            end_frame_index=self.end_frame_index,
            source_fps_numerator=self.source_fps_numerator,
            source_fps_denominator=self.source_fps_denominator,
            source_frame_count=self.source_frame_count,
            extracted_asset_id=tail_asset.asset_id,
            extracted_sha256=tail_asset.sha256,
            extracted_mime_type=tail_asset.mime_type,
            extracted_size_bytes=tail_asset.size_bytes,
            extracted_width=tail_asset.width,
            extracted_height=tail_asset.height,
            extracted_fps_numerator=metadata.fps_numerator,
            extracted_fps_denominator=metadata.fps_denominator,
            extracted_duration_milliseconds=metadata.duration_milliseconds,
            extracted_frame_count=metadata.frame_count,
            extractor_name=self.extractor.name,
            extractor_version=self.extractor.version,
            terminal_frame_evidence=self.terminal_frame_evidence,
            target_shot_id=self.target_shot_id,
            target_shot_revision=self.target_shot_revision,
            target_shot_content_hash=self.target_shot_content_hash,
            continuity_constraint_snapshot_hash=self.continuity_constraint_snapshot_hash,
        )


@dataclass(frozen=True)
class PreparedTerminalMotionTail:
    receipt: TerminalMotionTailReceipt
    tail_asset: AssetRecord
    commit_request: StateCommitRequest | None
    replayed: bool = False


def _seal(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _canonical_arguments(start: int, end: int) -> tuple[str, ...]:
    return (
        "-nostdin", "-hide_banner", "-loglevel", "error", "-i", "{SOURCE}",
        "-map", "0:v:0", "-vf", f"trim=start_frame={start}:end_frame={end + 1},setpts=PTS-STARTPTS",
        "-an", "-frames:v", str(end - start + 1), "-c:v", "libx264", "-qp", "0",
        "-pix_fmt", "yuv420p", "-threads", "1", "-movflags", "+faststart", "-y", "{TARGET}",
    )


def _decoded_frame_sha256(
    ffmpeg_descriptor: int, video_descriptor: int, frame_index: int
) -> str:
    try:
        result = subprocess.run(
            (
                f"/proc/self/fd/{ffmpeg_descriptor}", "-nostdin", "-v", "error",
                "-i", f"/proc/self/fd/{video_descriptor}", "-vf",
                f"select=eq(n\\,{frame_index})", "-frames:v", "1", "-f", "hash",
                "-hash", "sha256", "-",
            ),
            check=True, capture_output=True, text=True, timeout=120,
            pass_fds=(ffmpeg_descriptor, video_descriptor),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _invalid("Terminal motion-tail frame verification failed.", str(exc)) from exc
    value = result.stdout.strip()
    if not value.startswith("SHA256=") or len(value) != 71:
        raise _invalid("Terminal motion-tail frame hash is invalid.")
    return value.removeprefix("SHA256=").lower()


def _decoded_frame_sequence_sha256(
    ffmpeg_descriptor: int,
    video_descriptor: int,
    *,
    start_frame_index: int | None = None,
    end_frame_index: int | None = None,
) -> str:
    arguments = [
        f"/proc/self/fd/{ffmpeg_descriptor}", "-nostdin", "-v", "error",
        "-i", f"/proc/self/fd/{video_descriptor}",
    ]
    if start_frame_index is not None and end_frame_index is not None:
        arguments.extend(
            (
                "-vf",
                f"trim=start_frame={start_frame_index}:end_frame={end_frame_index + 1}",
            )
        )
    arguments.extend(("-map", "0:v:0", "-an", "-f", "framemd5", "-"))
    try:
        result = subprocess.run(
            tuple(arguments), check=True, capture_output=True, text=True,
            timeout=180, pass_fds=(ffmpeg_descriptor, video_descriptor),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _invalid("Terminal motion-tail sequence verification failed.", str(exc)) from exc
    hashes = tuple(
        line.rsplit(",", 1)[-1].strip().lower()
        for line in result.stdout.splitlines()
        if line and not line.startswith("#")
    )
    if not hashes or any(len(value) != 32 for value in hashes):
        raise _invalid("Terminal motion-tail decoded sequence is invalid.")
    return hashlib.sha256(("\n".join(hashes) + "\n").encode("ascii")).hexdigest()


def _identity_fd(descriptor: int, name: str) -> tuple[ToolIdentity, str]:
    digest = _sha256_fd(descriptor)
    try:
        result = subprocess.run(
            (f"/proc/self/fd/{descriptor}", "-version"), check=True,
            capture_output=True, text=True, timeout=10, pass_fds=(descriptor,),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _invalid(f"Terminal motion-tail {name} identity failed.", str(exc)) from exc
    line = result.stdout.splitlines()[0] if result.stdout else ""
    if not line.startswith(f"{name} version "):
        raise _invalid(f"Terminal motion-tail {name} identity is invalid.")
    return ToolIdentity(name=name, version=line.split()[2]), digest


def _materialize(
    root: Path, source_asset: AssetRecord, *, start: int, end: int
) -> tuple[bytes, dict[str, object]]:
    ffmpeg_candidate = shutil.which("ffmpeg")
    ffprobe_candidate = shutil.which("ffprobe")
    if ffmpeg_candidate is None or ffprobe_candidate is None:
        raise _invalid("Terminal motion-tail ffmpeg toolchain is unavailable.")
    ffmpeg_path = Path(ffmpeg_candidate).resolve(strict=True)
    ffprobe_path = Path(ffprobe_candidate).resolve(strict=True)
    source_path = root / source_asset.artifact_path
    with _open_regular_file_nofollow(
        source_path, contained_by=root / "assets"
    ) as (source_fd, opened), _open_regular_file_nofollow(
        ffmpeg_path, contained_by=ffmpeg_path.parent
    ) as (ffmpeg_fd, ffmpeg_opened), _open_regular_file_nofollow(
        ffprobe_path, contained_by=ffprobe_path.parent
    ) as (ffprobe_fd, ffprobe_opened), tempfile.TemporaryDirectory(
        prefix="ai-video-terminal-motion-tail-"
    ) as scratch:
        if _sha256_fd(source_fd) != source_asset.sha256 or opened.st_size != source_asset.size_bytes:
            raise _invalid("Terminal motion-tail source bytes are not exact.")
        ffmpeg, ffmpeg_sha = _identity_fd(ffmpeg_fd, "ffmpeg")
        ffprobe, ffprobe_sha = _identity_fd(ffprobe_fd, "ffprobe")
        target = Path(scratch) / "tail.mp4"
        canonical = _canonical_arguments(start, end)
        arguments = tuple(
            f"/proc/self/fd/{source_fd}" if value == "{SOURCE}" else str(target) if value == "{TARGET}" else value
            for value in canonical
        )
        try:
            subprocess.run(
                (f"/proc/self/fd/{ffmpeg_fd}", *arguments), check=True,
                capture_output=True, text=True, timeout=300,
                pass_fds=(source_fd, ffmpeg_fd),
            )
            payload = target.read_bytes()
            probe_result = subprocess.run(
                (f"/proc/self/fd/{ffprobe_fd}", "-v", "error", "-show_streams",
                 "-show_format", "-of", "json", str(target)),
                check=True, capture_output=True, text=True, timeout=60,
                pass_fds=(ffprobe_fd,),
            )
            raw = json.loads(probe_result.stdout)
            with _open_regular_file_nofollow(
                target, contained_by=Path(scratch)
            ) as (target_fd, _):
                source_sequence_hash = _decoded_frame_sequence_sha256(
                    ffmpeg_fd,
                    source_fd,
                    start_frame_index=start,
                    end_frame_index=end,
                )
                tail_sequence_hash = _decoded_frame_sequence_sha256(
                    ffmpeg_fd,
                    target_fd,
                )
                if source_sequence_hash != tail_sequence_hash:
                    raise _invalid(
                        "Terminal motion-tail does not preserve the selected frame sequence."
                    )
                source_terminal_hash = _decoded_frame_sha256(
                    ffmpeg_fd, source_fd, end
                )
                tail_terminal_hash = _decoded_frame_sha256(
                    ffmpeg_fd, target_fd, end - start
                )
                if source_terminal_hash != tail_terminal_hash:
                    raise _invalid(
                        "Terminal motion-tail does not preserve the terminal frame."
                    )
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            raise _invalid("Terminal motion-tail materialization failed.", str(exc)) from exc
        if (
            _sha256_fd(source_fd) != source_asset.sha256
            or _sha256_fd(ffmpeg_fd) != ffmpeg_sha
            or _sha256_fd(ffprobe_fd) != ffprobe_sha
            or os.fstat(ffmpeg_fd).st_size != ffmpeg_opened.st_size
            or os.fstat(ffprobe_fd).st_size != ffprobe_opened.st_size
            or target.read_bytes() != payload
        ):
            raise _invalid("Terminal motion-tail inputs changed during materialization.")
    try:
        videos = [item for item in raw["streams"] if item.get("codec_type") == "video"]
        audios = [item for item in raw["streams"] if item.get("codec_type") == "audio"]
        video = videos[0]
        fps = Fraction(str(video["avg_frame_rate"]))
        duration = Decimal(str(video.get("duration", raw["format"]["duration"])))
        measured = {
            "sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
            "codec_name": str(video["codec_name"]), "width": int(video["width"]),
            "height": int(video["height"]), "fps_numerator": fps.numerator,
            "fps_denominator": fps.denominator,
            "duration_milliseconds": int((duration * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "frame_count": int(video["nb_frames"]), "audio_stream_count": len(audios),
            "ffmpeg": ffmpeg, "ffmpeg_sha": ffmpeg_sha, "ffprobe": ffprobe,
            "ffprobe_sha": ffprobe_sha, "canonical_arguments": canonical,
            "decoded_frame_sequence_sha256": source_sequence_hash,
            "terminal_decoded_frame_sha256": source_terminal_hash,
        }
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise _invalid("Terminal motion-tail probe evidence is invalid.", str(exc)) from exc
    return payload, measured


def _tail_asset(source: AssetRecord, receipt: TerminalMotionTailReceipt) -> AssetRecord:
    metadata = VideoAssetMetadata(
        container_name="mp4", codec_name=receipt.extracted_codec_name,
        width=receipt.extracted_width, height=receipt.extracted_height,
        fps_numerator=receipt.extracted_fps_numerator,
        fps_denominator=receipt.extracted_fps_denominator,
        duration_milliseconds=receipt.extracted_duration_milliseconds,
        frame_count=receipt.extracted_frame_count, probe_receipt_id=receipt.content_hash,
        request_receipt_fingerprint=receipt.source_request_input_hash,
        resolved_generation_hash=receipt.source_resolved_generation_hash,
        provenance_receipt_id=receipt.source_provenance_receipt_id,
    )
    return AssetRecord(
        asset_id=receipt.tail_asset_id, asset_type=AssetType.VIDEO,
        artifact_path=canonical_video_asset_path(receipt.extracted_sha256),
        sha256=receipt.extracted_sha256, size_bytes=receipt.extracted_size_bytes,
        mime_type="video/mp4", duration_seconds=receipt.extracted_duration_milliseconds / 1000,
        width=receipt.extracted_width, height=receipt.extracted_height,
        source_kind=AssetSourceKind.DERIVED, tool=receipt.extractor,
        input_artifact_ids=(source.asset_id, receipt.terminal_frame_evidence.extracted_asset_id),
        input_fingerprint=receipt.content_hash, creation_receipt_id=receipt.content_hash,
        usage_license=source.usage_license, video_metadata=metadata,
    )


def prepare_terminal_motion_tail_commit(
    *, project_root: str | Path, committer, project: LoadedProductionProject,
    attempt_id: str, source_attempt_id: str, tail_asset_id: str,
    target_shot_id: str, target_shot_revision: int, target_shot_content_hash: str,
    continuity_constraint_snapshot_hash: str,
    provider_min_duration_milliseconds: int, provider_max_duration_milliseconds: int,
) -> PreparedTerminalMotionTail:
    root = Path(project_root).resolve(strict=True)
    if root != project.root.resolve(strict=True) or committer._read_manifest() != project.manifest:
        raise _invalid("Terminal motion-tail base project is stale.")
    existing = next((item for item in project.registry.assets if item.asset_id == tail_asset_id), None)
    if existing is not None:
        receipt = validate_terminal_motion_tail(root, project, existing)
        if (
            receipt.source_attempt_id != source_attempt_id
            or receipt.target_shot_id != target_shot_id
            or receipt.target_shot_revision != target_shot_revision
            or receipt.target_shot_content_hash != target_shot_content_hash
            or receipt.continuity_constraint_snapshot_hash
            != continuity_constraint_snapshot_hash
            or receipt.provider_min_duration_milliseconds
            != provider_min_duration_milliseconds
            or receipt.provider_max_duration_milliseconds
            != provider_max_duration_milliseconds
        ):
            raise _invalid("Existing terminal motion-tail does not match replay.")
        return PreparedTerminalMotionTail(receipt, existing, None, True)
    target = next((item for item in project.shots if item.shot_id == target_shot_id), None)
    if target is None or (target.revision, target.content_hash) != (target_shot_revision, target_shot_content_hash):
        raise _invalid("Terminal motion-tail target Shot is not exact.")
    request, source, terminal, evidence, p6_receipt, provenance = _source_lineage(root, project, source_attempt_id)
    metadata = source.video_metadata
    assert metadata is not None
    duration_denominator = 1000 * metadata.fps_denominator
    selected_frames = max(3, (provider_min_duration_milliseconds * metadata.fps_numerator + duration_denominator - 1) // duration_denominator)
    if selected_frames > metadata.frame_count:
        raise _invalid("Terminal motion-tail provider duration cannot fit the source.")
    start = metadata.frame_count - selected_frames
    end = metadata.frame_count - 1
    window_analysis = analyze_motion_tail_window(
        root,
        source,
        start_frame_index=start,
        end_frame_index=end,
    )
    payload, measured = _materialize(root, source, start=start, end=end)
    if (
        measured["frame_count"] != selected_frames
        or measured["width"] != metadata.width or measured["height"] != metadata.height
        or (measured["fps_numerator"], measured["fps_denominator"]) != (metadata.fps_numerator, metadata.fps_denominator)
        or measured["audio_stream_count"] != 0
        or not provider_min_duration_milliseconds <= measured["duration_milliseconds"] <= provider_max_duration_milliseconds
    ):
        raise _invalid("Terminal motion-tail measured output violates the exact window contract.")
    receipt = TerminalMotionTailReceipt.create(
        source_attempt_id=source_attempt_id, source_shot_id=terminal.source_shot_id,
        source_shot_revision=terminal.source_shot_revision, source_shot_content_hash=terminal.source_shot_content_hash,
        source_video_asset_id=source.asset_id, source_video_sha256=source.sha256,
        source_registry_revision_id=terminal.source_registry.revision_id,
        source_generation_id=request.generation_id, source_request_input_hash=request.request_input_hash,
        source_resolved_generation_hash=request.resolved_generation_hash,
        source_provenance_receipt_id=provenance.content_hash, source_provenance_receipt_sha256=provenance.content_hash,
        source_p6_acceptance_evidence_id=evidence.content_hash, source_p6_acceptance_evidence_sha256=evidence.content_hash,
        source_p6_acceptance_receipt_id=p6_receipt.content_hash, source_p6_acceptance_receipt_sha256=p6_receipt.content_hash,
        tail_asset_id=tail_asset_id, extracted_sha256=measured["sha256"], extracted_size_bytes=measured["size_bytes"],
        extracted_codec_name=measured["codec_name"], extracted_width=measured["width"], extracted_height=measured["height"],
        extracted_fps_numerator=measured["fps_numerator"], extracted_fps_denominator=measured["fps_denominator"],
        extracted_duration_milliseconds=measured["duration_milliseconds"], extracted_frame_count=measured["frame_count"],
        selection_rule_version=_RULE, start_timestamp_numerator=start * metadata.fps_denominator,
        start_timestamp_denominator=metadata.fps_numerator, end_timestamp_numerator=terminal.timestamp_numerator,
        end_timestamp_denominator=terminal.timestamp_denominator, start_frame_index=start, end_frame_index=end,
        source_fps_numerator=metadata.fps_numerator, source_fps_denominator=metadata.fps_denominator,
        source_frame_count=metadata.frame_count, source_duration_milliseconds=metadata.duration_milliseconds,
        source_width=metadata.width, source_height=metadata.height,
        provider_min_duration_milliseconds=provider_min_duration_milliseconds,
        provider_max_duration_milliseconds=provider_max_duration_milliseconds,
        terminal_frame_evidence=terminal, motion_analysis_receipt_hash=window_analysis.content_hash,
        extractor=measured["ffmpeg"], extractor_executable_sha256=measured["ffmpeg_sha"],
        probe=measured["ffprobe"], probe_executable_sha256=measured["ffprobe_sha"],
        decoded_frame_sequence_sha256=measured["decoded_frame_sequence_sha256"],
        terminal_decoded_frame_sha256=measured["terminal_decoded_frame_sha256"],
        canonical_arguments=measured["canonical_arguments"], target_shot_id=target_shot_id,
        target_shot_revision=target_shot_revision, target_shot_content_hash=target_shot_content_hash,
        continuity_constraint_snapshot_hash=continuity_constraint_snapshot_hash,
    )
    tail = _tail_asset(source, receipt)
    registry = _seal_registry(project.registry, project.registry.assets + (tail,))
    base = prepare_project_registry_commit(manifest=project.manifest, project=project.project, registry=registry, attempt_id=attempt_id)
    candidate_manifest = project.manifest.model_copy(update={"active_project": base.next_project, "active_registry": base.next_registry})
    candidate = project.model_copy(update={"manifest": candidate_manifest, "registry": registry, "asset_paths": {**project.asset_paths, tail.asset_id: root / tail.artifact_path}})
    closure = build_source_closure(candidate)
    states = resolve_dependency_state(closure.graph, build_applied_dependency_evidence(closure.inputs, None)).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=project.manifest.manifest_revision,
        base_dependency_graph=project.manifest.active_dependency_graph,
        candidate_graph=closure.graph, candidate_dependency_states=states,
        expected_desired_fingerprints=closure.desired_fingerprints,
    )
    receipt_payload = _canonical_json_bytes(receipt)
    analysis_payload = _canonical_json_bytes(window_analysis)
    graph_payload = _canonical_json_bytes(closure.graph)
    artifacts = base.artifacts + (
        PreparedArtifact(tail.artifact_path, payload, tail.sha256),
        PreparedArtifact(canonical_terminal_motion_tail_receipt_path(receipt.content_hash), receipt_payload, hashlib.sha256(receipt_payload).hexdigest()),
        PreparedArtifact(canonical_motion_tail_window_analysis_receipt_path(window_analysis.content_hash), analysis_payload, hashlib.sha256(analysis_payload).hexdigest()),
        PreparedArtifact(canonical_dependency_graph_snapshot_path(closure.graph.revision_id), graph_payload, hashlib.sha256(graph_payload).hexdigest()),
    )
    return PreparedTerminalMotionTail(receipt, tail, replace(base, artifacts=tuple(sorted(artifacts, key=lambda item: item.relative_path.as_posix())), dependency_graph_transition=transition))


def reopen_terminal_motion_tail_receipt(
    project_root: str | Path, receipt_or_asset: str | AssetRecord
) -> TerminalMotionTailReceipt:
    root = Path(project_root).resolve(strict=True)
    if isinstance(receipt_or_asset, AssetRecord):
        receipt_hash = receipt_or_asset.creation_receipt_id
    elif len(receipt_or_asset) == 64 and all(c in "0123456789abcdef" for c in receipt_or_asset):
        receipt_hash = receipt_or_asset
    else:
        from ai_video.production.project import load_production_project
        project = load_production_project(root / "project.yaml")
        asset = next((item for item in project.registry.assets if item.asset_id == receipt_or_asset), None)
        if asset is None:
            raise _invalid("Terminal motion-tail asset is not registered.")
        receipt_hash = asset.creation_receipt_id
    try:
        path = canonical_terminal_motion_tail_receipt_path(receipt_hash)
        raw = _read_regular_file_nofollow(root / path, contained_by=root / "state")
        receipt = TerminalMotionTailReceipt.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Could not reopen terminal motion-tail receipt.", str(exc)) from exc
    if receipt.content_hash != receipt_hash or raw.data != _canonical_json_bytes(receipt):
        raise _invalid("Terminal motion-tail receipt identity is invalid.")
    return receipt


def _reopen_window_analysis(
    project_root: Path, content_hash: str
) -> MotionTailWindowAnalysisReceipt:
    try:
        path = canonical_motion_tail_window_analysis_receipt_path(content_hash)
        raw = _read_regular_file_nofollow(
            project_root / path, contained_by=project_root / "state"
        )
        receipt = MotionTailWindowAnalysisReceipt.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Could not reopen motion-tail window analysis.", str(exc)) from exc
    if receipt.content_hash != content_hash or raw.data != _canonical_json_bytes(receipt):
        raise _invalid("Motion-tail window analysis identity is invalid.")
    return receipt


def validate_terminal_motion_tail(
    project_root: str | Path, project: LoadedProductionProject,
    receipt_or_asset: str | AssetRecord,
) -> TerminalMotionTailReceipt:
    root = Path(project_root).resolve(strict=True)
    if root != project.root.resolve(strict=True):
        raise _invalid("Terminal motion-tail project root is not exact.")
    receipt = reopen_terminal_motion_tail_receipt(root, receipt_or_asset)
    request, source, terminal, evidence, p6_receipt, provenance = _source_lineage(root, project, receipt.source_attempt_id)
    analysis = _reopen_window_analysis(root, receipt.motion_analysis_receipt_hash)
    tail = next((item for item in project.registry.assets if item.asset_id == receipt.tail_asset_id), None)
    if (
        request.output_asset_id != receipt.source_video_asset_id
        or source.sha256 != receipt.source_video_sha256 or terminal != receipt.terminal_frame_evidence
        or evidence.content_hash != receipt.source_p6_acceptance_evidence_sha256
        or p6_receipt.content_hash != receipt.source_p6_acceptance_receipt_sha256
        or provenance.content_hash != receipt.source_provenance_receipt_sha256
        or analyze_motion_tail_window(
            root,
            source,
            start_frame_index=receipt.start_frame_index,
            end_frame_index=receipt.end_frame_index,
        )
        != analysis
        or tail != _tail_asset(source, receipt)
    ):
        raise _invalid("Terminal motion-tail lineage drifted.")
    try:
        raw = _read_regular_file_nofollow(root / tail.artifact_path, contained_by=root / "assets")
    except (OSError, ValueError) as exc:
        raise _invalid("Terminal motion-tail bytes cannot be reopened.", str(exc)) from exc
    if raw.file_sha256 != tail.sha256 or raw.size_bytes != tail.size_bytes:
        raise _invalid("Terminal motion-tail bytes are not exact.")
    receipt.to_c4_motion_tail_evidence(registry_revision_id=project.registry.revision_id, tail_asset=tail)
    return receipt


__all__ = [
    "PreparedTerminalMotionTail", "TerminalMotionTailReceipt",
    "prepare_terminal_motion_tail_commit", "reopen_terminal_motion_tail_receipt",
    "validate_terminal_motion_tail",
]
