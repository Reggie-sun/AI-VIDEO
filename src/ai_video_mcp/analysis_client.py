"""Private stdio MCP client, run using the existing isolated analysis Python."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path


async def analyze(video_path, *, understand_audio=False, expected_sha256=None):
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    arguments = {"video_path": video_path, "extract_frames": True,
        "transcribe_audio": False, "detect_scenes": True}
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    if understand_audio:
        if (understand_audio is not True or not isinstance(expected_sha256, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
            raise ValueError("audio analysis requires an exact source SHA")
        arguments.update(understand_audio=True, expected_sha256=expected_sha256)
        for name in ("VIDEO_MCP_AUDIO_RUNTIME_FACTORY", "VIDEO_MCP_AUDIO_MEDIA_ROOT", "VIDEO_MCP_AUDIO_MODEL_ID"):
            if name in os.environ:
                env[name] = os.environ[name]
    server = StdioServerParameters(command=sys.executable, args=["-m", "ai_video_mcp"], env=env)
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool("video_analyze", arguments)
            return result.model_dump(mode="json")


if __name__ == "__main__":
    options = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if set(options) - {"understand_audio", "expected_sha256"}:
        raise ValueError("unsupported analysis options")
    print(json.dumps(asyncio.run(analyze(sys.argv[1], **options)), ensure_ascii=False))
