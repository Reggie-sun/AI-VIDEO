from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence
from uuid import uuid4

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.config import ensure_min_free_space, sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.manifest import (
    AttemptRecord,
    RunManifest,
    ShotRecord,
    _now,
    atomic_write_manifest,
    load_manifest,
    mark_shots_stale,
    successful_shot_is_valid,
)
from ai_video.models import ProjectConfig, ShotSpec, WorkflowBinding
from ai_video import ffmpeg_tools
from ai_video.workflow_renderer import collect_clip_artifact, render_workflow


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _cleanup_artifact(
    path: Path,
    *,
    exc: BaseException | None = None,
    progress: Callable[[str], None] | None = None,
) -> bool:
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanup_error:
        message = f"Artifact cleanup failed for {path}: {cleanup_error}"
        if exc is not None:
            exc.add_note(message)
        elif progress is not None:
            try:
                progress(message)
            except Exception:
                pass
        return False
    return True


@dataclass
class _ArtifactPromotion:
    staged_clip_path: Path
    staged_last_frame_path: Path
    clip_path: Path
    last_frame_path: Path
    clip_backup: Path
    frame_backup: Path
    clip_existed: bool
    frame_existed: bool
    progress: Callable[[str], None]
    clip_promoted: bool = False
    frame_promoted: bool = False
    clip_backup_owned: bool = False
    frame_backup_owned: bool = False

    @staticmethod
    def _copy_backup_exclusive(source: Path, backup: Path) -> None:
        created = False
        try:
            with source.open("rb") as source_file, backup.open("xb") as backup_file:
                created = True
                shutil.copyfileobj(source_file, backup_file)
            shutil.copystat(source, backup)
        except BaseException as exc:
            if created:
                _cleanup_artifact(backup, exc=exc)
            raise

    @classmethod
    def _backup_artifact(cls, source: Path, backup: Path) -> None:
        try:
            os.link(source, backup)
        except FileExistsError:
            raise
        except OSError:
            cls._copy_backup_exclusive(source, backup)

    def _preflight_backups(self) -> None:
        existing = next(
            (path for path in (self.clip_backup, self.frame_backup) if path.exists()),
            None,
        )
        if existing is not None:
            raise FileExistsError(f"Recovery artifact backup already exists: {existing}")

    def promote(self) -> "_ArtifactPromotion":
        try:
            self._preflight_backups()
            if self.clip_existed:
                self._backup_artifact(self.clip_path, self.clip_backup)
                self.clip_backup_owned = True
            if self.frame_existed:
                self._backup_artifact(self.last_frame_path, self.frame_backup)
                self.frame_backup_owned = True

            self.staged_clip_path.replace(self.clip_path)
            self.clip_promoted = True
            self.staged_last_frame_path.replace(self.last_frame_path)
            self.frame_promoted = True
        except BaseException as exc:
            self.rollback(exc)
            raise
        return self

    @staticmethod
    def _restore_backup(backup: Path, canonical: Path, exc: BaseException) -> bool:
        try:
            backup.replace(canonical)
            return True
        except OSError as replace_error:
            exc.add_note(
                f"Artifact rollback replace failed for {canonical}: {replace_error}"
            )
        try:
            shutil.copy2(backup, canonical)
        except OSError as copy_error:
            exc.add_note(f"Artifact rollback copy failed for {canonical}: {copy_error}")
            return False
        _cleanup_artifact(backup, exc=exc)
        return True

    def rollback(self, exc: BaseException) -> None:
        rollback_failed: set[Path] = set()
        for promoted, existed, canonical, backup in (
            (self.clip_promoted, self.clip_existed, self.clip_path, self.clip_backup),
            (
                self.frame_promoted,
                self.frame_existed,
                self.last_frame_path,
                self.frame_backup,
            ),
        ):
            if not promoted:
                continue
            if existed:
                if not self._restore_backup(backup, canonical, exc):
                    rollback_failed.add(backup)
            elif not _cleanup_artifact(canonical, exc=exc):
                exc.add_note(f"Partial canonical artifact remains at {canonical}")

        _cleanup_artifact(self.staged_clip_path, exc=exc)
        _cleanup_artifact(self.staged_last_frame_path, exc=exc)
        if self.clip_backup_owned and self.clip_backup not in rollback_failed:
            _cleanup_artifact(self.clip_backup, exc=exc)
        if self.frame_backup_owned and self.frame_backup not in rollback_failed:
            _cleanup_artifact(self.frame_backup, exc=exc)

    def commit(self) -> None:
        paths = [self.staged_clip_path, self.staged_last_frame_path]
        if self.clip_backup_owned:
            paths.append(self.clip_backup)
        if self.frame_backup_owned:
            paths.append(self.frame_backup)
        for path in paths:
            _cleanup_artifact(path, progress=self.progress)


class PipelineRunner:
    def __init__(
        self,
        project: ProjectConfig,
        shots: Sequence[ShotSpec],
        binding: WorkflowBinding,
        template: dict[str, Any],
        *,
        comfy: Any | None = None,
        ffmpeg: Any | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.project = project
        self.shots = list(shots)
        self.binding = binding
        self.template = template
        self.comfy = comfy or ComfyClient(project.comfy.base_url)
        self.ffmpeg = ffmpeg or ffmpeg_tools
        self.progress = progress_callback or (lambda msg: None)

    def run(self, run_id: str | None = None, *, project_config_path: Path | None = None, shot_list_path: Path | None = None) -> RunManifest:
        ensure_min_free_space(self.project.output.root, self.project.output.min_free_gb)
        actual_run_id = run_id or f"run-{_now_id()}-{uuid4().hex[:8]}"
        run_root = self.project.output.root / actual_run_id
        manifest_path = run_root / "manifest.json"
        manifest = RunManifest(run_id=actual_run_id, status="running")
        manifest.project_config_path = str(project_config_path) if project_config_path else None
        manifest.shot_list_path = str(shot_list_path) if shot_list_path else None
        if project_config_path and Path(project_config_path).exists():
            manifest.project_config_hash = sha256_file(project_config_path)
        if self.project.workflow.template.exists():
            manifest.workflow_template_hash = sha256_file(self.project.workflow.template)
        if self.project.workflow.binding.exists():
            manifest.workflow_binding_hash = sha256_file(self.project.workflow.binding)
        atomic_write_manifest(manifest_path, manifest)
        self.progress(f"Starting run {actual_run_id} with {len(self.shots)} shots")

        characters = {character.id: character for character in self.project.characters}
        character_image_names = self._prepare_character_images()
        previous_frame: Path | None = None
        previous_frame_hash: str | None = None

        for index, shot in enumerate(self.shots):
            self.progress(f"Shot {shot.id} ({index + 1}/{len(self.shots)}): starting")
            record, previous_frame, promotion = self._run_shot(
                manifest=manifest,
                manifest_path=manifest_path,
                run_root=run_root,
                actual_run_id=actual_run_id,
                shot=shot,
                shot_index=index,
                characters=characters,
                character_image_names=character_image_names,
                previous_frame=previous_frame,
                previous_frame_hash=previous_frame_hash,
            )
            self._persist_successful_shot(
                manifest=manifest,
                manifest_path=manifest_path,
                record=record,
                promotion=promotion,
            )
            previous_frame_hash = record.last_frame_hash

        normalized_paths = self._normalize_shots(manifest, run_root)

        final_output = run_root / "final" / "final.mp4"
        self.ffmpeg.stitch_clips(normalized_paths, final_output)
        manifest.final_output = str(final_output)
        manifest.status = "succeeded"
        atomic_write_manifest(manifest_path, manifest)
        self.progress(f"Final video: {final_output}")
        return manifest

    def resume(self, manifest_path: Path) -> RunManifest:
        manifest = load_manifest(manifest_path)
        if manifest.status == "succeeded" and self._all_resume_shots_current(manifest):
            return manifest
        manifest.status = "running"
        atomic_write_manifest(manifest_path, manifest)

        run_root = manifest_path.parent
        characters = {character.id: character for character in self.project.characters}
        character_image_names = self._prepare_character_images()
        previous_frame: Path | None = None
        previous_frame_hash: str | None = None

        for index, shot in enumerate(self.shots):
            existing = self._find_shot_record(manifest, shot.id)

            if existing and self._shot_is_current(
                existing,
                shot,
                previous_frame,
                previous_frame_hash,
            ):
                last_frame_path = Path(existing.last_frame_path) if existing.last_frame_path else None
                if last_frame_path and not last_frame_path.exists():
                    clip_path = Path(existing.clip_path)
                    if clip_path.exists():
                        self.ffmpeg.extract_last_frame(clip_path, last_frame_path)
                        existing.last_frame_hash = sha256_file(last_frame_path)
                        atomic_write_manifest(manifest_path, manifest)
                previous_frame = last_frame_path
                previous_frame_hash = existing.last_frame_hash
                continue

            old_last_frame_hash = existing.last_frame_hash if existing else None
            record, previous_frame, promotion = self._run_shot(
                manifest=manifest,
                manifest_path=manifest_path,
                run_root=run_root,
                actual_run_id=manifest.run_id,
                shot=shot,
                shot_index=index,
                characters=characters,
                character_image_names=character_image_names,
                previous_frame=previous_frame,
                previous_frame_hash=previous_frame_hash,
            )

            def update_stale_dependency() -> None:
                if old_last_frame_hash == record.last_frame_hash or index + 1 >= len(self.shots):
                    return
                next_shot = self.shots[index + 1]
                next_record = self._find_shot_record(manifest, next_shot.id)
                if (
                    next_record is not None
                    and self._uses_previous_frame(next_shot, previous_frame)
                    and next_record.chain_input_hash != record.last_frame_hash
                ):
                    stale_manifest = mark_shots_stale(manifest, {next_shot.id})
                    manifest.shots = stale_manifest.shots
                    manifest.updated_at = stale_manifest.updated_at

            self._persist_successful_shot(
                manifest=manifest,
                manifest_path=manifest_path,
                record=record,
                promotion=promotion,
                update_manifest=update_stale_dependency,
            )
            previous_frame_hash = record.last_frame_hash

        normalized_paths = self._normalize_shots(manifest, run_root)

        final_output = run_root / "final" / "final.mp4"
        self.ffmpeg.stitch_clips(normalized_paths, final_output)
        manifest.final_output = str(final_output)
        manifest.status = "succeeded"
        atomic_write_manifest(manifest_path, manifest)
        return manifest

    def _normalize_shots(self, manifest: RunManifest, run_root: Path) -> list[Path]:
        delivery_fps = self.project.defaults.fps
        normalized_paths = []
        for shot_record in manifest.shots:
            source = Path(shot_record.clip_path or "")
            target = run_root / "normalized" / f"{shot_record.shot_id}.mp4"
            self.ffmpeg.normalize_clip(
                source,
                target,
                width=self.project.defaults.width,
                height=self.project.defaults.height,
                fps=delivery_fps,
                encoder="libx264",
            )
            shot_record.normalized_clip_path = str(target)
            shot_record.normalized_clip_hash = sha256_file(target)
            normalized_paths.append(target)
        return normalized_paths

    def _prepare_character_images(self) -> dict[str, str]:
        names = {}
        for character in self.project.characters:
            if character.reference_images:
                names[character.id] = self.comfy.prepare_image(character.reference_images[0])
        return names

    @staticmethod
    def _find_shot_record(manifest: RunManifest, shot_id: str) -> ShotRecord | None:
        return next((record for record in manifest.shots if record.shot_id == shot_id), None)

    @staticmethod
    def _upsert_shot_record(manifest: RunManifest, record: ShotRecord) -> None:
        existing = PipelineRunner._find_shot_record(manifest, record.shot_id)
        if existing is None:
            manifest.shots.append(record)
            return
        manifest.shots[manifest.shots.index(existing)] = record

    def _uses_previous_frame(self, shot: ShotSpec, previous_frame: Path | None) -> bool:
        return (
            self.binding.init_image is not None
            and shot.init_image is None
            and previous_frame is not None
        )

    def _effective_chain_input_hash(
        self,
        shot: ShotSpec,
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> str | None:
        if self._uses_previous_frame(shot, previous_frame):
            return previous_frame_hash
        return None

    def _shot_is_current(
        self,
        record: ShotRecord,
        shot: ShotSpec,
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> bool:
        if not successful_shot_is_valid(record):
            return False
        if not self._uses_previous_frame(shot, previous_frame):
            return True
        return record.chain_input_hash == previous_frame_hash

    def _all_resume_shots_current(self, manifest: RunManifest) -> bool:
        previous_frame: Path | None = None
        previous_frame_hash: str | None = None
        for shot in self.shots:
            record = self._find_shot_record(manifest, shot.id)
            if record is None or not self._shot_is_current(
                record,
                shot,
                previous_frame,
                previous_frame_hash,
            ):
                return False
            previous_frame = Path(record.last_frame_path) if record.last_frame_path else None
            previous_frame_hash = record.last_frame_hash
        return True

    @staticmethod
    def _error_record(exc: BaseException) -> dict[str, str]:
        if isinstance(exc, AiVideoError):
            return {"code": exc.code.value, "message": exc.user_message}
        return {"code": "unexpected_error", "message": "Unexpected internal error"}

    def _persist_terminal_failure(
        self,
        *,
        manifest: RunManifest,
        manifest_path: Path,
        shot: ShotSpec,
        attempts: list[AttemptRecord],
        started_at: str,
        exc: BaseException,
    ) -> None:
        failed = ShotRecord.failed(
            shot_id=shot.id,
            attempts=attempts,
            error=self._error_record(exc),
            started_at=started_at,
            previous=self._find_shot_record(manifest, shot.id),
        )
        self._upsert_shot_record(manifest, failed)
        manifest.status = "failed"
        atomic_write_manifest(manifest_path, manifest)

    def _persist_successful_shot(
        self,
        *,
        manifest: RunManifest,
        manifest_path: Path,
        record: ShotRecord,
        promotion: _ArtifactPromotion,
        update_manifest: Callable[[], None] | None = None,
    ) -> None:
        try:
            self._upsert_shot_record(manifest, record)
            if update_manifest is not None:
                update_manifest()
            atomic_write_manifest(manifest_path, manifest)
        except BaseException as exc:
            promotion.rollback(exc)
            raise
        promotion.commit()

    def _run_shot(
        self,
        *,
        manifest: RunManifest,
        manifest_path: Path,
        run_root: Path,
        actual_run_id: str,
        shot: ShotSpec,
        shot_index: int,
        characters: dict,
        character_image_names: dict[str, str],
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> tuple[ShotRecord, Path, _ArtifactPromotion]:
        max_attempts = max(1, self.project.defaults.max_attempts)
        started_at = _now()
        previous_record = self._find_shot_record(manifest, shot.id)
        attempts = list(previous_record.attempts) if previous_record else []
        attempt_offset = max((item.attempt for item in attempts), default=0)
        for retry_index in range(1, max_attempts + 1):
            attempt = attempt_offset + retry_index
            attempt_record = AttemptRecord(attempt=attempt, status="running")
            try:
                record, last_frame, promotion = self._run_shot_attempt(
                    run_root=run_root,
                    actual_run_id=actual_run_id,
                    shot=shot,
                    shot_index=shot_index,
                    attempt=attempt,
                    characters=characters,
                    character_image_names=character_image_names,
                    previous_frame=previous_frame,
                    previous_frame_hash=previous_frame_hash,
                )
            except AiVideoError as exc:
                attempt_record.status = "failed"
                attempt_record.error = self._error_record(exc)
                attempts.append(attempt_record)
                if isinstance(self.comfy, ComfyClient) and "memory" in (exc.technical_detail or "").lower():
                    self.comfy.free_memory()
                if exc.retryable and retry_index < max_attempts:
                    continue
                self._persist_terminal_failure(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    shot=shot,
                    attempts=attempts,
                    started_at=started_at,
                    exc=exc,
                )
                raise
            except Exception as exc:
                attempt_record.status = "failed"
                attempt_record.error = self._error_record(exc)
                attempts.append(attempt_record)
                self._persist_terminal_failure(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    shot=shot,
                    attempts=attempts,
                    started_at=started_at,
                    exc=exc,
                )
                raise

            attempt_record.status = "succeeded"
            attempt_record.comfy_prompt_id = record.comfy_prompt_id
            attempts.append(attempt_record)
            record.started_at = started_at
            record.attempts = attempts
            return record, last_frame, promotion

        raise AssertionError("Shot retry loop exhausted without returning or raising")

    def _run_shot_attempt(
        self,
        *,
        run_root: Path,
        actual_run_id: str,
        shot: ShotSpec,
        shot_index: int,
        attempt: int,
        characters: dict,
        character_image_names: dict[str, str],
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> tuple[ShotRecord, Path, _ArtifactPromotion]:
        shot_dir = run_root / "shots" / shot.id
        attempt_dir = shot_dir / f"attempt_{attempt}"
        clip_path = shot_dir / "clip.mp4"
        last_frame_path = shot_dir / "last_frame.png"
        staged_clip_path = shot_dir / f".attempt_{attempt}.clip.mp4"
        staged_last_frame_path = shot_dir / f".attempt_{attempt}.last_frame.png"
        rendered_path = attempt_dir / "workflow.json"
        output_prefix = f"{self.project.project_name}/{actual_run_id}/{shot.id}/attempt_{attempt}"
        try:
            chain_image_name = self._prepare_chain_image(shot, previous_frame)
            rendered = render_workflow(
                template=self.template,
                binding=self.binding,
                shot=shot,
                defaults=self.project.defaults,
                characters=characters,
                shot_index=shot_index,
                chain_image_name=chain_image_name,
                character_image_names=character_image_names,
                output_prefix=output_prefix,
            )
            attempt_dir.mkdir(parents=True, exist_ok=True)
            rendered_path.write_text(json.dumps(rendered.workflow, indent=2), encoding="utf-8")
            prompt_id = self._submit_and_collect_clip(rendered.workflow, staged_clip_path)
            self.ffmpeg.extract_last_frame(staged_clip_path, staged_last_frame_path)
            record = ShotRecord.succeeded(
                shot_id=shot.id,
                seed=rendered.seed,
                clip_path=staged_clip_path,
                last_frame_path=staged_last_frame_path,
                chain_input_hash=self._effective_chain_input_hash(
                    shot,
                    previous_frame,
                    previous_frame_hash,
                ),
                character_ref_hashes=self._character_ref_hashes(shot),
            )
            record.active_attempt = attempt
            record.rendered_workflow_path = str(rendered_path)
            record.rendered_workflow_hash = sha256_file(rendered_path)
            record.comfy_prompt_id = prompt_id
            promotion = self._promote_shot_artifacts(
                staged_clip_path=staged_clip_path,
                staged_last_frame_path=staged_last_frame_path,
                clip_path=clip_path,
                last_frame_path=last_frame_path,
            )
            record.clip_path = str(clip_path)
            record.last_frame_path = str(last_frame_path)
            return record, last_frame_path, promotion
        except BaseException as exc:
            _cleanup_artifact(staged_clip_path, exc=exc)
            _cleanup_artifact(staged_last_frame_path, exc=exc)
            raise

    def _promote_shot_artifacts(
        self,
        *,
        staged_clip_path: Path,
        staged_last_frame_path: Path,
        clip_path: Path,
        last_frame_path: Path,
    ) -> _ArtifactPromotion:
        clip_backup = staged_clip_path.with_suffix(staged_clip_path.suffix + ".backup")
        frame_backup = staged_last_frame_path.with_suffix(
            staged_last_frame_path.suffix + ".backup"
        )
        return _ArtifactPromotion(
            staged_clip_path=staged_clip_path,
            staged_last_frame_path=staged_last_frame_path,
            clip_path=clip_path,
            last_frame_path=last_frame_path,
            clip_backup=clip_backup,
            frame_backup=frame_backup,
            clip_existed=clip_path.exists(),
            frame_existed=last_frame_path.exists(),
            progress=self.progress,
        ).promote()

    def _submit_and_collect_clip(self, workflow: dict[str, Any], clip_path: Path) -> str:
        if not isinstance(self.comfy, ComfyClient):
            return self.comfy.submit_and_collect_clip(workflow, clip_path)

        prompt_id = self.comfy.submit_prompt(workflow)
        result = self.comfy.poll_job(
            prompt_id,
            poll_interval_seconds=self.project.defaults.poll_interval_seconds,
            timeout_seconds=self.project.defaults.job_timeout_seconds,
        )
        if result.status is not JobStatus.COMPLETED or result.history is None:
            raise result.error or AiVideoError(
                code=ErrorCode.COMFY_JOB_TIMEOUT,
                user_message=f"ComfyUI job did not complete: {prompt_id}",
                retryable=True,
            )
        artifact = collect_clip_artifact(result.history, self.binding.clip_output)
        self.comfy.download_artifact(
            filename=artifact.filename,
            subfolder=artifact.subfolder,
            type_=artifact.type,
            target=clip_path,
        )
        self.ffmpeg.validate_clip(clip_path)
        return prompt_id

    def _prepare_chain_image(self, shot: ShotSpec, previous_frame: Path | None) -> str | None:
        image = shot.init_image or previous_frame
        if image is None:
            return None
        return self.comfy.prepare_image(image)

    def _character_ref_hashes(self, shot: ShotSpec) -> dict[str, str]:
        characters = {character.id: character for character in self.project.characters}
        hashes = {}
        for character_id in shot.characters:
            character = characters.get(character_id)
            if character and character.reference_images:
                hashes[character_id] = sha256_file(character.reference_images[0])
        return hashes
