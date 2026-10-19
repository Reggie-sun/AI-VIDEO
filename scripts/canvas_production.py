"""Reusable data-driven operator entry over CanvasProductionService.

Runtime bindings are installed once by the operator, shared across stories.
Inspection needs no runtime binding; other operations can use a shared binding.
"""
import argparse
from dataclasses import asdict, is_dataclass
import importlib
import json
from pathlib import Path

from ai_video.canvas_project_data import open_canvas_project
from ai_video.canvas_preflight import canvas_reference_preflight
from ai_video.errors import AiVideoError
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_production_source import inspect_canvas_source


def _json(path, root):
    return json.loads(_read_regular_file_nofollow(path, contained_by=root).data)


def _approved_preflight_shots(loaded, authored_shots):
    """Use retained production owners for approved Shots replaced by components."""
    from ai_video.production.production_strategy_reader import production_parent_context

    active = {shot.shot_id: shot for shot in loaded.shots}
    family_parents = {shot.production_lineage.parent_shot_id for shot in loaded.shots
        if shot.production_lineage is not None}
    resolved = []
    for authored in authored_shots:
        current = active.get(authored.shot_id)
        if current is not None and current.production_intent is not None:
            resolved.append(current)
        elif ((current is not None and current.production_lineage is not None)
                or authored.shot_id in family_parents):
            parent, _, _, _ = production_parent_context(loaded, authored.shot_id)
            resolved.append(parent)
        else:
            resolved.append(authored)
    return tuple(resolved)


def run(*, data_path, project_root, action, runtime_factory=None, arguments=None,
       ffprobe_executable=None, ffmpeg_executable=None):
    data_path = Path(data_path).absolute()
    root = data_path.parent.resolve(strict=True)
    definition = _json(data_path, root)
    source = _json(root / definition["source"], root)
    inspection = inspect_canvas_source(source, definition["selection"])
    if action == "inspect":
        return inspection
    if runtime_factory is not None and action not in {"preflight", "prepare_image_workflow", "bootstrap_video_cleanup"}:
        module, name = runtime_factory.split(":", 1)
        runtime = getattr(importlib.import_module(module), name)(project_root=Path(project_root))
    else:
        runtime = {"committer": ProductionStateCommitter(project_root)}
    committer = runtime.pop("committer")
    operator_arguments = runtime.pop("action_arguments", lambda action, service, arguments: arguments)
    service, registry, artifacts = open_canvas_project(inspection=inspection, definition=definition,
        data_root=root, committer=committer, resume=action not in {"author", "approve", "revise", "bootstrap_video_cleanup"},
        ffprobe_executable=ffprobe_executable, **runtime)
    arguments = {} if arguments is None else arguments
    if action == "bootstrap_video_cleanup":
        if ffmpeg_executable is None or ffprobe_executable is None:
            raise ValueError("Video cleanup requires explicit local FFmpeg and ffprobe executables")
        bundle = service.author(registry=registry, asset_artifacts=artifacts)
        arguments = dict(arguments)
        if isinstance(arguments.get("cleanup_plan"), str):
            arguments["cleanup_plan"] = _json(root / arguments["cleanup_plan"], root)
        return service.bootstrap_video_cleanup(bundle=bundle, ffmpeg_executable=ffmpeg_executable,
            ffprobe_executable=ffprobe_executable, **arguments)
    if action in {"author", "approve", "preflight"}:
        bundle = service.author(registry=registry, asset_artifacts=artifacts)
        if action in {"author", "preflight"}:
            from ai_video.production.models import QaPolicy, Shot

            selected = arguments.get("qa_policy")
            qa_policy, qa_authority = None, "NOT_EVALUATED"
            selected_project = None
            if selected is not None:
                qa_policy = selected if isinstance(selected, QaPolicy) else QaPolicy.model_validate(
                    _json(root / selected, root))
                qa_authority = "candidate_not_approved"
            elif action == "preflight" and (Path(project_root) / "project.yaml").exists():
                selected_project = service._load()
                qa_policy = selected_project.qa_policy
                qa_authority = "selected_policy"
            authored_shots = tuple(m for m in bundle.creative_artifacts if isinstance(m, Shot))
            if selected_project is not None and qa_policy is not None:
                authored_shots = _approved_preflight_shots(selected_project, authored_shots)
            preflight = canvas_reference_preflight(packet=service.packet,
                direction=service.direction, registry=bundle.registry, qa_policy=qa_policy,
                qa_authority=qa_authority,
                authored_shots=authored_shots)
            if action == "preflight":
                preflight["position"] = asdict(service.position()) if (
                    Path(project_root) / "project.yaml").exists() else None
                return preflight
            return {"project": bundle.project.model_dump(mode="json"), "adaptations": bundle.adaptations,
                    "preflight": preflight,
                    "production_acceptance": "NOT_EVALUATED"}
        from ai_video.production.models import QaPolicy
        arguments = operator_arguments(action, service, arguments)
        selected = arguments.pop("qa_policy")
        policy = selected if isinstance(selected, QaPolicy) else QaPolicy.model_validate(_json(root / selected, root))
        return service.approve_authoring(bundle=bundle, qa_policy=policy, **arguments)
    if action == "revise":
        return service.revise_authoring(registry=registry, asset_artifacts=artifacts, **arguments)
    if action == "status":
        return service.position()
    if action == "prepare_image_workflow":
        return service.prepare_image_workflow(**arguments)
    arguments = operator_arguments(action, service, arguments)
    if action in {"compose", "compose_production"}:
        spec, timeline = getattr(service, action)(**arguments)
        return {"spec": spec.model_dump(mode="json"), "timeline": timeline.model_dump(mode="json")}
    if action == "deliver":
        loaded, timeline = service.deliver()
        return {"output": loaded.render_state.output.model_dump(mode="json"),
                "timeline_fingerprint": timeline.composition_fingerprint,
                "final_acceptance": loaded.manifest.final_acceptance_state.model_dump(mode="json")
                    if loaded.manifest.final_acceptance_state else "NOT_EVALUATED"}
    return getattr(service, action)(**arguments)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inspect", "preflight", "author", "approve", "revise", "status", "prepare", "start",
        "prepare_repair", "start_repair", "prepare_production", "materialize_production", "compose_production",
        "generate_voice", "prepare_image_workflow", "bootstrap_video_cleanup",
        "execute", "evaluate", "handoff_reference", "register_native_audio", "compose", "render", "cut_packet",
        "review_delivery", "deliver"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--runtime", help="Trusted shared operator module:function; never a story executor")
    parser.add_argument("--arguments", type=Path, help="Ordinary action arguments JSON; credentials are forbidden")
    parser.add_argument("--ffprobe", type=Path, help="Absolute ffprobe executable for first-time local MP4 imports")
    parser.add_argument("--ffmpeg", type=Path, help="Absolute local FFmpeg executable for non-generative cleanup")
    args = parser.parse_args(argv)
    try:
        arguments = _json(args.arguments.absolute(), args.arguments.absolute().parent) if args.arguments else {}
        result = run(data_path=args.data, project_root=args.project_root, action=args.action,
            runtime_factory=args.runtime, arguments=arguments, ffprobe_executable=args.ffprobe,
            ffmpeg_executable=args.ffmpeg)
        import inspect
        if inspect.isawaitable(result):
            import asyncio
            result = asyncio.run(result)
        def encode(value):
            if hasattr(value, "model_dump"):
                return value.model_dump(mode="json")
            from ai_video.production.generation_feedback import PreparedGeneration
            if isinstance(value, PreparedGeneration):
                from ai_video.production.video_reference_controls import prepared_generation_report
                return prepared_generation_report(value)
            if is_dataclass(value):
                return asdict(value)
            if isinstance(value, Path):
                return str(value)
            raise TypeError("Operator result is not serializable")
        print(json.dumps(result, default=encode, ensure_ascii=False, indent=2))
        return 0
    except (AiVideoError, ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        message = error.user_message if isinstance(error, AiVideoError) else f"Canvas operator input failed ({type(error).__name__})"
        print(json.dumps({"error": message, "stage": args.action,
                          "production_acceptance": "NOT_EVALUATED"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
