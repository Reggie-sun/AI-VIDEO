import json
from pathlib import Path

from scripts.skill_environment_check import diagnose


def checkout(tmp_path):
    target = tmp_path / '.agents/skills/demo'
    target.mkdir(parents=True)
    (target / 'SKILL.md').write_text('demo')
    aliases = tmp_path / '.claude/skills'
    aliases.mkdir(parents=True)
    (aliases / 'demo').symlink_to('../../.agents/skills/demo')
    (tmp_path / '.mcp.json').write_text(json.dumps({'mcpServers': {}}))
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').write_text('')
    return tmp_path


def test_valid_checkout(tmp_path):
    report = diagnose(checkout(tmp_path), host=False)
    assert report['status'] == 'PASS'
    assert report['mcp_runtime'] == 'NOT_EVALUATED'


def test_flattened_windows_symlink_is_rejected(tmp_path):
    root = checkout(tmp_path)
    alias = root / '.claude/skills/demo'
    alias.unlink()
    alias.write_text('../../.agents/skills/demo')
    report = diagnose(root, host=False)
    assert report['status'] == 'FAIL'
    assert 'Windows' in report['findings'][0]['detail']


def test_missing_host_command_reported_without_execution(tmp_path):
    root = checkout(tmp_path)
    command = str(root / 'missing-python')
    (root / '.mcp.json').write_text(json.dumps({'mcpServers': {'test': {'command': command}}}))
    report = diagnose(root)
    assert any(x['code'] == 'host_prerequisite' and x['status'] == 'WARN' for x in report['findings'])
    assert not Path(command).exists()


def test_syntax_checked_without_importing_script(tmp_path):
    root = checkout(tmp_path)
    scripts = root / '.agents/skills/demo/scripts'
    scripts.mkdir()
    (scripts / 'bad.py').write_text('def broken(')
    assert diagnose(root, host=False)['status'] == 'FAIL'
