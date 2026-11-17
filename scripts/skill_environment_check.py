"""Read-only checkout/MCP prerequisite diagnostics; never launches configured commands."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib


def diagnose(root: Path, *, host: bool = True) -> dict:
    findings = []

    def add(code: str, path: str, status: str, detail: str) -> None:
        findings.append(dict(code=code, path=path, status=status, detail=detail))

    canonical = root / '.agents/skills'
    aliases = root / '.claude/skills'
    names = {p.name for p in canonical.iterdir() if (p / 'SKILL.md').is_file()}
    for name in sorted(names):
        alias = aliases / name
        target = canonical / name
        good = alias.is_symlink() and alias.resolve() == target.resolve()
        add('skill_symlink', str(alias.relative_to(root)), 'PASS' if good else 'FAIL',
            'Canonical target resolved' if good else
            'Missing, flattened, or wrong symlink. On Windows enable Developer Mode/Git core.symlinks and re-checkout this path; do not copy Skill bodies.')
    for alias in sorted(aliases.iterdir()):
        if not alias.name.startswith('.') and alias.name not in names:
            add('extra_alias', str(alias.relative_to(root)), 'FAIL', 'No canonical Skill')
    configs = [('.mcp.json', 'mcpServers', json.loads),
               ('.codex/config.toml', 'mcp_servers', tomllib.loads)]
    for filename, key, parser in configs:
        config = parser((root / filename).read_text())
        for name, server in config.get(key, {}).items():
            if server.get('enabled') is False:
                continue
            command = server.get('command')
            if not command:
                continue
            refs = [('command', command)]
            if server.get('cwd'):
                refs.append(('cwd', server['cwd']))
            for arg in server.get('args', []):
                value = arg.removeprefix('--chdir=')
                if Path(value).is_absolute():
                    refs.append(('argument', value))
            for kind, value in refs:
                absolute = Path(value).is_absolute()
                label = f'{filename}:{name}:{kind}'
                if absolute:
                    add('machine_path', label, 'WARN', value)
                if not host:
                    continue
                path = Path(value) if absolute else root / value
                if kind == 'command':
                    exists = (path.is_file() and os.access(path, os.X_OK)) if absolute else shutil.which(value) is not None
                else:
                    exists = path.exists()
                add('host_prerequisite', label, 'PASS' if exists else 'WARN',
                    'Available' if exists else f'Missing prerequisite or runtime-created path: {value}')
    scripts = list(canonical.glob('*/scripts/*.py'))
    for script in sorted(scripts):
        try:
            compile(script.read_bytes(), str(script), 'exec')
        except (SyntaxError, OSError) as exc:
            add('python_script', str(script.relative_to(root)), 'FAIL', type(exc).__name__)
    add('python', 'interpreter', 'PASS' if sys.version_info >= (3, 11) else 'FAIL',
        '.'.join(map(str, sys.version_info[:3])))
    return {'status': 'FAIL' if any(x['status'] == 'FAIL' for x in findings) else 'PASS',
            'host_checked': host, 'scripts_checked': len(scripts), 'findings': findings,
            'mcp_runtime': 'NOT_EVALUATED', 'python_dependencies': 'NOT_EVALUATED',
            'note': 'Only config paths and Python syntax checked. No secrets read, commands executed, services started or dependencies imported. WARN needs operator review; PASS is not runtime readiness.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--checkout-only', action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose(args.root, host=not args.checkout_only)
    except (OSError, ValueError) as exc:
        report = {'status': 'FAIL', 'error': type(exc).__name__}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
