import os
from pathlib import Path
import stat
import subprocess

import pytest

from ai_video.production import dotenv_source
from ai_video.production.dotenv_source import DotenvSourceError, read_dotenv_value
from ai_video_mcp.audio_understanding import AudioUnderstandingError

SECRET = "DOTENV-PRIVATE-VALUE-123"


@pytest.fixture
def dotenv_path(tmp_path, monkeypatch):
    previous = os.umask(0o077)  # the source rejects group/world-writable files
    path = tmp_path / "repo" / ".env"
    path.parent.mkdir()
    monkeypatch.setattr(dotenv_source, "REPOSITORY_DOTENV", path)
    yield path
    os.umask(previous)


@pytest.fixture
def secret_lookups(monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, b"SECRET-SERVICE-VALUE\n", b"")
    monkeypatch.setattr(subprocess, "run", run)
    return calls


@pytest.fixture
def user_bus(monkeypatch):
    from ai_video_mcp import audio_operator
    bus = Path(f"/run/user/{os.getuid()}/bus")
    real_lstat = audio_operator.os.lstat
    monkeypatch.setattr(audio_operator.os, "lstat", lambda path: (
        type("BusStat", (), {"st_mode": stat.S_IFSOCK, "st_uid": os.getuid()})()
        if Path(path) == bus else real_lstat(path)))


def test_default_path_is_fixed_repository_root_not_cwd(tmp_path, monkeypatch):
    import runpy
    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(dotenv_source.__file__)
    assert namespace["REPOSITORY_DOTENV"] == Path(__file__).resolve().parents[1] / ".env"


def test_parses_simple_lines_quotes_export_and_comments(dotenv_path):
    dotenv_path.write_text(
        "# comment\n\nOTHER=x\nexport ELEVENLABS_API_KEY=\"" + SECRET + "\"\n"
        "MINIMAX_API_KEY='single-quoted'\nGOOGLE_API_KEY = $HOME\n", encoding="utf-8")
    assert read_dotenv_value("ELEVENLABS_API_KEY") == SECRET
    assert read_dotenv_value("MINIMAX_API_KEY") == "single-quoted"
    assert read_dotenv_value("GOOGLE_API_KEY") == "$HOME"  # never expanded
    assert read_dotenv_value("MISSING_KEY") is None


def test_missing_file_and_empty_value_return_none(dotenv_path):
    assert read_dotenv_value("ELEVENLABS_API_KEY") is None
    dotenv_path.write_text("ELEVENLABS_API_KEY=\nMINIMAX_API_KEY=\"\"\n", encoding="utf-8")
    assert read_dotenv_value("ELEVENLABS_API_KEY") is None
    assert read_dotenv_value("MINIMAX_API_KEY") is None


@pytest.mark.parametrize("content", [
    f"ELEVENLABS_API_KEY={SECRET}\nELEVENLABS_API_KEY={SECRET}x\n",
    f"ELEVENLABS_API_KEY={SECRET} trailing\n",
    "ELEVENLABS_API_KEY=" + "A" * 5000 + "\n",
])
def test_invalid_content_fails_closed_without_value(dotenv_path, content):
    dotenv_path.write_text(content, encoding="utf-8")
    with pytest.raises(DotenvSourceError) as caught:
        read_dotenv_value("ELEVENLABS_API_KEY")
    assert SECRET not in str(caught.value) and SECRET not in repr(caught.value)
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_symlink_oversized_non_regular_and_non_utf8_are_rejected(dotenv_path, tmp_path):
    real = tmp_path / "real.env"
    real.write_text(f"ELEVENLABS_API_KEY={SECRET}\n", encoding="utf-8")
    dotenv_path.symlink_to(real)
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")
    dotenv_path.unlink()
    dotenv_path.write_bytes(b"ELEVENLABS_API_KEY=" + SECRET.encode() + b"\n" + b"#" * (64 * 1024))
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")
    dotenv_path.unlink()
    os.mkfifo(dotenv_path)
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")
    dotenv_path.unlink()
    dotenv_path.write_bytes(b"ELEVENLABS_API_KEY=\xff\n")
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")


def test_elevenlabs_supplier_prefers_dotenv_then_secret_service(dotenv_path, secret_lookups):
    from scripts import elevenlabs_speech_batch as cli
    dotenv_path.write_text(f"ELEVENLABS_API_KEY={SECRET}\n", encoding="utf-8")
    assert cli._SecretServiceCredential().api_key() == SECRET
    assert secret_lookups == []
    dotenv_path.write_text("OTHER=1\n", encoding="utf-8")
    assert cli._SecretServiceCredential().api_key() == "SECRET-SERVICE-VALUE"
    dotenv_path.unlink()
    assert cli._SecretServiceCredential().api_key() == "SECRET-SERVICE-VALUE"
    assert [argv[-1] for argv in secret_lookups] == ["ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY"]


def test_elevenlabs_supplier_fails_closed_when_both_missing_or_dotenv_invalid(dotenv_path, monkeypatch):
    from scripts import elevenlabs_speech_batch as cli
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda argv, **kwargs: (
        calls.append(argv) or subprocess.CompletedProcess(argv, 1, b"", b"")))
    with pytest.raises(RuntimeError, match="Secret Service lookup failed"):
        cli._SecretServiceCredential().api_key()
    dotenv_path.write_text(f"ELEVENLABS_API_KEY={SECRET}\nELEVENLABS_API_KEY={SECRET}\n", encoding="utf-8")
    with pytest.raises(RuntimeError) as caught:
        cli._SecretServiceCredential().api_key()
    assert SECRET not in str(caught.value) and caught.value.__cause__ is None
    assert len(calls) == 1  # invalid .env never falls back


def test_minimax_cn_uses_dotenv_and_international_never_reads_it(dotenv_path, secret_lookups, monkeypatch):
    from scripts import minimax_speech_batch as cli
    dotenv_path.write_text(
        f"MINIMAX_API_KEY={SECRET}\nMINIMAX_SPEECH_API_KEY=wrong\nMINIMAX_SPEECH_CN_API_KEY=wrong\n",
        encoding="utf-8")
    assert cli._SecretServiceCredential("MINIMAX_SPEECH_CN_API_KEY").bearer_header() == "Bearer " + SECRET
    assert secret_lookups == []
    reads = []
    monkeypatch.setattr(cli, "read_dotenv_value", lambda name: reads.append(name))
    assert cli._SecretServiceCredential("MINIMAX_SPEECH_API_KEY").bearer_header() == "Bearer SECRET-SERVICE-VALUE"
    assert reads == []
    assert secret_lookups == [["secret-tool", "lookup", "application", "ai-video", "provider",
                               "minimax-speech", "credential", "MINIMAX_SPEECH_API_KEY"]]


def test_minimax_cn_falls_back_and_fails_closed(dotenv_path, monkeypatch):
    from scripts import minimax_speech_batch as cli
    results = iter([0, 1])
    calls = []
    def run(argv, **kwargs):
        calls.append(argv[-1])
        return (subprocess.CompletedProcess(argv, 0, b"CN-SECRET", b"") if next(results) == 0
                else subprocess.CompletedProcess(argv, 1, b"", b""))
    monkeypatch.setattr(subprocess, "run", run)
    assert cli._SecretServiceCredential("MINIMAX_SPEECH_CN_API_KEY").bearer_header() == "Bearer CN-SECRET"
    with pytest.raises(RuntimeError, match="Secret Service lookup failed"):
        cli._SecretServiceCredential("MINIMAX_SPEECH_CN_API_KEY").bearer_header()
    assert calls == ["MINIMAX_SPEECH_CN_API_KEY", "MINIMAX_SPEECH_CN_API_KEY"]
    dotenv_path.symlink_to(dotenv_path.parent / "elsewhere")
    with pytest.raises(RuntimeError, match=r"\.env credential source is invalid"):
        cli._SecretServiceCredential("MINIMAX_SPEECH_CN_API_KEY").bearer_header()
    assert len(calls) == 2


def test_gemini_supplier_prefers_google_api_key_then_secret_service(dotenv_path, secret_lookups, user_bus):
    from ai_video_mcp import audio_operator
    dotenv_path.write_text(f"GEMINI_API_KEY=wrong\nGOOGLE_API_KEY={SECRET}\n", encoding="utf-8")
    assert audio_operator._secret_service_credential() == SECRET
    assert secret_lookups == []
    dotenv_path.unlink()
    assert audio_operator._secret_service_credential() == "SECRET-SERVICE-VALUE"
    assert secret_lookups[0][-1] == "GEMINI_API_KEY"


def test_gemini_supplier_fails_closed_without_value_in_error(dotenv_path, monkeypatch, user_bus):
    from ai_video_mcp import audio_operator
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda argv, **kwargs: (
        calls.append(argv) or subprocess.CompletedProcess(argv, 1, b"", b"")))
    with pytest.raises(AudioUnderstandingError):
        audio_operator._secret_service_credential()
    dotenv_path.write_text(f"GOOGLE_API_KEY={SECRET}\nGOOGLE_API_KEY={SECRET}\n", encoding="utf-8")
    with pytest.raises(AudioUnderstandingError) as caught:
        audio_operator._secret_service_credential()
    assert SECRET not in str(caught.value) and SECRET not in repr(caught.value)
    assert caught.value.__cause__ is None
    assert len(calls) == 1


def test_bom_first_line_is_still_read(dotenv_path):
    dotenv_path.write_bytes(b"\xef\xbb\xbfELEVENLABS_API_KEY=" + SECRET.encode() + b"\n")
    assert read_dotenv_value("ELEVENLABS_API_KEY") == SECRET


@pytest.mark.parametrize("line", ["ELEVENLABS_API_KEY: abc", 'ELEVENLABS_API_KEY="abc',
                                  "ELEVENLABS_API_KEY=abc'", 'ELEVENLABS_API_KEY="abc\ndef"'])
def test_malformed_target_line_fails_closed(dotenv_path, line):
    dotenv_path.write_text(line + "\n")
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")


def test_malformed_other_line_is_ignored(dotenv_path):
    dotenv_path.write_text("OTHER: x\nELEVENLABS_API_KEY=" + SECRET + "\n")
    assert read_dotenv_value("ELEVENLABS_API_KEY") == SECRET


def test_group_or_world_writable_file_is_rejected(dotenv_path):
    dotenv_path.write_text("ELEVENLABS_API_KEY=" + SECRET + "\n")
    dotenv_path.chmod(0o620)
    with pytest.raises(DotenvSourceError):
        read_dotenv_value("ELEVENLABS_API_KEY")
