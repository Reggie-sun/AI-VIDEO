"""One exact development audio observation through a fresh project-local MCP.

Usage: python review_audio.py <SHOT> <media.mp4>. Writes qa/<SHOT>/audio-* evidence; one operator unit per media.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import asyncio, hashlib, json, os, stat, sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.tools.audio_understand import _read_source, _audio_bytes, audio_understand
from ai_video_mcp.audio_understanding import prepare_audio_request
from ai_video_mcp.audio_operator import prepare_operator_unit
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    shot, media = sys.argv[1], Path(sys.argv[2]).resolve()
    out = HERE / "qa" / shot
    out.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(media.read_bytes()).hexdigest()
    cfg = ServerConfig(audio_media_root=str(REPO))
    preview = audio_understand(str(media), cfg, expected_sha256=digest, execute=False)
    (out / "audio-preview.json").write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n")
    source = _read_source(media, REPO, digest)
    audio, offset = _audio_bytes(source, media.suffix)
    prepared = prepare_audio_request(audio_bytes=audio, source_sha256=digest, source_size_bytes=len(source.data),
                                     model_id=cfg.audio_model_id, audio_start_seconds=offset)
    now = datetime.now(timezone.utc)
    unit = out / "audio-operator"
    receipt = prepare_operator_unit(unit, media_path=media, prepared=prepared,
                                    authorization_reference="user-shizhen-dispatch-picture-first-20261030",
                                    issued_at=now, expires_at=now + timedelta(minutes=25))
    (out / "audio-operator-preparation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    socket = Path(f"/run/user/{os.getuid()}/bus")
    if socket.stat().st_uid != os.getuid() or not stat.S_ISSOCK(socket.stat().st_mode):
        raise ValueError("current-user D-Bus unavailable")
    env = dict(os.environ)
    env.update(PYTHONPATH=str(REPO / "src"), DBUS_SESSION_BUS_ADDRESS=f"unix:path={socket}",
               VIDEO_MCP_AUDIO_MEDIA_ROOT=str(REPO), VIDEO_MCP_AUDIO_RUNTIME_FACTORY="ai_video_mcp.audio_operator:build_runtime",
               VIDEO_MCP_AUDIO_OPERATOR_UNIT=str(unit), VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256=receipt["intent_sha256"])
    params = StdioServerParameters(command="/home/reggie/.local/share/video-mcp/venv/bin/python",
                                   args=["-m", "ai_video_mcp"], env=env, cwd=str(REPO))
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            result = await client.call_tool("audio_understand", {"media_path": str(media), "expected_sha256": digest,
                                                                 "execute": True})
            value = result.model_dump(mode="json")
            (out / "audio-understanding.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({"shot": shot, "isError": result.isError, "source_sha256": digest}))


if __name__ == "__main__":
    asyncio.run(main())
