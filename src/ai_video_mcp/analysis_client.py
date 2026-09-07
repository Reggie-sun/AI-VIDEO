"""Private stdio MCP client, run using the existing isolated analysis Python."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


async def analyze(video_path):
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server = StdioServerParameters(command=sys.executable, args=["-m", "ai_video_mcp"],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])})
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool("video_analyze", {
                "video_path": video_path, "extract_frames": True,
                "transcribe_audio": False, "detect_scenes": True,
            })
            return result.model_dump(mode="json")


if __name__ == "__main__":
    print(json.dumps(asyncio.run(analyze(sys.argv[1])), ensure_ascii=False))
