from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_video.config import load_project, load_shots, load_yaml
from ai_video.errors import AiVideoError
from ai_video.models import WorkflowBinding
from ai_video.pipeline import PipelineRunner
from ai_video.workflow_loader import load_workflow_template
from ai_video.workflow_renderer import render_workflow, validate_api_workflow


def _load_binding_and_template(project_path: str | Path, shots_path: str | Path):
    project = load_project(project_path)
    shots = load_shots(shots_path, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)
    validate_api_workflow(template)
    if shots:
        characters = {character.id: character for character in project.characters}
        character_image_names = {
            character.id: f"{character.id}.png" for character in project.characters
        }
        chain_image_name = shots[0].init_image.name if shots[0].init_image is not None else None
        render_workflow(
            template=template,
            binding=binding,
            shot=shots[0],
            defaults=project.defaults,
            characters=characters,
            shot_index=0,
            chain_image_name=chain_image_name,
            character_image_names=character_image_names,
            output_prefix="validate/output",
        )
    return project, shots, binding, template


def _cmd_validate(args: argparse.Namespace) -> int:
    _load_binding_and_template(args.project, args.shots)
    print("Project is valid.")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    project, shots, binding, template = _load_binding_and_template(args.project, args.shots)
    manifest = PipelineRunner(project, shots, binding, template, progress_callback=print).run(
        run_id=args.run_id,
        project_config_path=Path(args.project),
        shot_list_path=Path(args.shots),
    )
    print(f"Run succeeded: {manifest.final_output}")
    return 0


def _cmd_resume(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    from ai_video.manifest import load_manifest
    manifest = load_manifest(manifest_path)
    if not manifest.project_config_path or not manifest.shot_list_path:
        print("Cannot resume: manifest does not contain project config path.", file=sys.stderr)
        return 1
    project, shots, binding, template = _load_binding_and_template(
        manifest.project_config_path, manifest.shot_list_path
    )
    runner = PipelineRunner(project, shots, binding, template, progress_callback=print)
    result = runner.resume(manifest_path)
    print(f"Resume completed: {result.final_output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-video")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate")
    validate.add_argument("--project", required=True)
    validate.add_argument("--shots", required=True)
    validate.set_defaults(func=_cmd_validate)

    run = subcommands.add_parser("run")
    run.add_argument("--project", required=True)
    run.add_argument("--shots", required=True)
    run.add_argument("--run-id")
    run.set_defaults(func=_cmd_run)

    resume = subcommands.add_parser("resume")
    resume.add_argument("--manifest", required=True)
    resume.set_defaults(func=_cmd_resume)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except AiVideoError as exc:
        print(exc.user_message, file=sys.stderr)
        if exc.technical_detail:
            print(exc.technical_detail, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
