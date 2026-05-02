from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence
from uuid import uuid4

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.config import ensure_min_free_space, sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.manifest import RunManifest, ShotRecord, atomic_write_manifest, load_manifest, successful_shot_is_valid
from ai_video.models import ProjectConfig, ShotSpec, WorkflowBinding
from ai_video import ffmpeg_tools
from ai_video.workflow_renderer import collect_clip_artifact, render_workflow


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


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
            record, previous_frame = self._run_shot(
                run_root=run_root,
                actual_run_id=actual_run_id,
                shot=shot,
                shot_index=index,
                characters=characters,
                character_image_names=character_image_names,
                previous_frame=previous_frame,
                previous_frame_hash=previous_frame_hash,
            )
            manifest.shots.append(record)
            previous_frame_hash = record.last_frame_hash
            atomic_write_manifest(manifest_path, manifest)

        normalized_paths = []
        for shot_record in manifest.shots:
            source = Path(shot_record.clip_path or "")
            target = run_root / "normalized" / f"{shot_record.shot_id}.mp4"
            self.ffmpeg.normalize_clip(
                source,
                target,
                width=self.project.defaults.width,
                height=self.project.defaults.height,
                fps=self.project.defaults.fps,
                encoder="libx264",
            )
            shot_record.normalized_clip_path = str(target)
            shot_record.normalized_clip_hash = sha256_file(target)
            normalized_paths.append(target)

        final_output = run_root / "final" / "final.mp4"
        self.ffmpeg.stitch_clips(normalized_paths, final_output)
        manifest.final_output = str(final_output)
        manifest.status = "succeeded"
        atomic_write_manifest(manifest_path, manifest)
        self.progress(f"Final video: {final_output}")
        return manifest

    def resume(self, manifest_path: Path) -> RunManifest:
        manifest = load_manifest(manifest_path)
        if manifest.status == "succeeded":
            all_valid = all(successful_shot_is_valid(r) for r in manifest.shots)
            if all_valid:
                return manifest

        run_root = manifest_path.parent
        characters = {character.id: character for character in self.project.characters}
        character_image_names = self._prepare_character_images()
        previous_frame: Path | None = None
        previous_frame_hash: str | None = None

        for index, shot in enumerate(self.shots):
            existing = None
            for record in manifest.shots:
                if record.shot_id == shot.id:
                    existing = record
                    break

            if existing and existing.status == "succeeded" and successful_shot_is_valid(existing):
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

            record, previous_frame = self._run_shot(
                run_root=run_root,
                actual_run_id=manifest.run_id,
                shot=shot,
                shot_index=index,
                characters=characters,
                character_image_names=character_image_names,
                previous_frame=previous_frame,
                previous_frame_hash=previous_frame_hash,
            )
            if existing:
                idx = manifest.shots.index(existing)
                manifest.shots[idx] = record
            else:
                manifest.shots.append(record)
            previous_frame_hash = record.last_frame_hash
            atomic_write_manifest(manifest_path, manifest)

        normalized_paths = []
        for shot_record in manifest.shots:
            source = Path(shot_record.clip_path or "")
            target = run_root / "normalized" / f"{shot_record.shot_id}.mp4"
            self.ffmpeg.normalize_clip(
                source, target,
                width=self.project.defaults.width,
                height=self.project.defaults.height,
                fps=self.project.defaults.fps,
                encoder="libx264",
            )
            shot_record.normalized_clip_path = str(target)
            shot_record.normalized_clip_hash = sha256_file(target)
            normalized_paths.append(target)

        final_output = run_root / "final" / "final.mp4"
        self.ffmpeg.stitch_clips(normalized_paths, final_output)
        manifest.final_output = str(final_output)
        manifest.status = "succeeded"
        atomic_write_manifest(manifest_path, manifest)
        return manifest

    def _prepare_character_images(self) -> dict[str, str]:
        names = {}
        for character in self.project.characters:
            if character.reference_images:
                names[character.id] = self.comfy.prepare_image(character.reference_images[0])
        return names

    def _run_shot(
        self,
        *,
        run_root: Path,
        actual_run_id: str,
        shot: ShotSpec,
        shot_index: int,
        characters: dict,
        character_image_names: dict[str, str],
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> tuple[ShotRecord, Path]:
        from ai_video.manifest import AttemptRecord, _now
        last_error: AiVideoError | None = None
        max_attempts = max(1, self.project.defaults.max_attempts)
        started_at = _now()
        attempts: list[AttemptRecord] = []
        for attempt in range(1, max_attempts + 1):
            attempt_record = AttemptRecord(attempt=attempt, status="running")
            try:
                record, last_frame = self._run_shot_attempt(
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
                attempt_record.status = "succeeded"
                attempt_record.comfy_prompt_id = record.comfy_prompt_id
                attempts.append(attempt_record)
                record.started_at = started_at
                record.attempts = attempts
                return record, last_frame
            except AiVideoError as exc:
                attempt_record.status = "failed"
                attempt_record.error = {"code": exc.code.value, "message": exc.user_message}
                attempts.append(attempt_record)
                last_error = exc
                if isinstance(self.comfy, ComfyClient) and "memory" in (exc.technical_detail or "").lower():
                    self.comfy.free_memory()
                if not exc.retryable or attempt == max_attempts:
                    raise
        raise last_error or AiVideoError(
            code=ErrorCode.COMFY_JOB_FAILED,
            user_message=f"Shot failed: {shot.id}",
            retryable=True,
        )

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
    ) -> tuple[ShotRecord, Path]:
        shot_dir = run_root / "shots" / shot.id
        attempt_dir = shot_dir / f"attempt_{attempt}"
        clip_path = shot_dir / "clip.mp4"
        last_frame_path = shot_dir / "last_frame.png"
        rendered_path = attempt_dir / "workflow.json"
        output_prefix = f"{self.project.project_name}/{actual_run_id}/{shot.id}/attempt_{attempt}"
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
        prompt_id = self._submit_and_collect_clip(rendered.workflow, clip_path)
        self.ffmpeg.extract_last_frame(clip_path, last_frame_path)
        record = ShotRecord.succeeded(
            shot_id=shot.id,
            seed=rendered.seed,
            clip_path=clip_path,
            last_frame_path=last_frame_path,
            chain_input_hash=previous_frame_hash,
            character_ref_hashes=self._character_ref_hashes(shot),
        )
        record.active_attempt = attempt
        record.rendered_workflow_path = str(rendered_path)
        record.rendered_workflow_hash = sha256_file(rendered_path)
        record.comfy_prompt_id = prompt_id
        return record, last_frame_path

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
