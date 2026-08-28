from __future__ import annotations

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT / "src" / "ai_video"
FORBIDDEN_PATH_FRAGMENTS = (
    ".agents/skills",
    ".codex/skills",
    "skill.md",
)
FORBIDDEN_SKILL_IDENTITIES = (
    "ecommerce-ad-workflow",
    "ecommerce_ad_workflow",
    "hell-grind-aigc-skill",
    "hell_grind_aigc_skill",
    "higgsfield-seedance",
    "higgsfield_seedance",
    "higgsfield-troubleshoot",
    "higgsfield_troubleshoot",
    "open-video",
    "open_video",
    "seedance-authoring",
    "seedance_authoring",
    "video-shotcraft",
    "video_shotcraft",
)


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", identifier)
    return tuple(
        token.casefold() for token in re.split(r"[^A-Za-z0-9]+", camel_split) if token
    )


def test_skill_identifier_guard_covers_snake_case_and_camel_case() -> None:
    for identifier in (
        "skill_loader",
        "load_skill",
        "SkillRegistry",
        "AgentSkillLoader",
        "invokeSkill",
    ):
        assert {"skill", "skills"}.intersection(_identifier_tokens(identifier))


def test_product_runtime_has_no_agent_skill_dependency_or_invocation_path() -> None:
    for source_path in PRODUCT_ROOT.rglob("*.py"):
        source = source_path.read_text(encoding="utf-8")
        normalized_source = source.casefold().replace("\\", "/")

        for fragment in FORBIDDEN_PATH_FRAGMENTS:
            assert fragment.casefold() not in normalized_source, (
                f"{source_path} contains forbidden Agent Skill dependency {fragment!r}"
            )
        for identity in FORBIDDEN_SKILL_IDENTITIES:
            assert re.search(
                rf"(?<![a-z0-9]){re.escape(identity.casefold())}(?![a-z0-9])",
                normalized_source,
            ) is None, (
                f"{source_path} contains forbidden Agent Skill identity {identity!r}"
            )

        tree = ast.parse(source, filename=str(source_path))
        for node in ast.walk(tree):
            modules: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                modules = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = (node.module,)
            for module in modules:
                assert not {"skill", "skills"}.intersection(
                    _identifier_tokens(module)
                ), f"{source_path}:{node.lineno} imports Agent Skill module {module!r}"

            identifier: str | None = None
            if isinstance(node, ast.Name):
                identifier = node.id
            elif isinstance(node, ast.Attribute):
                identifier = node.attr
            if identifier is not None:
                assert not {"skill", "skills"}.intersection(
                    _identifier_tokens(identifier)
                ), (
                    f"{source_path}:{node.lineno} exposes Agent Skill runtime identifier "
                    f"{identifier!r}"
                )
