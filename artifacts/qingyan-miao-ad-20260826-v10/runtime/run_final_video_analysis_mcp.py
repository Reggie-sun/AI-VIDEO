from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
VIDEO = REPO / "artifacts/qingyan-miao-ad-20260826-v10/final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4"
OUTPUT = REPO / "artifacts/qingyan-miao-ad-20260826-v10/review/final/video-analysis-mcp-receipt.json"
PYTHON = Path("/home/reggie/.local/share/ai-video/video-analysis-mcp/bin/python")


def dump(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


async def main() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    server = StdioServerParameters(
        command=str(PYTHON),
        args=["-m", "ai_video_mcp"],
        cwd=REPO,
        env=env,
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialize = await session.initialize()
            tools = await session.list_tools()
            analyze = await session.call_tool(
                "video_analyze",
                {
                    "video_path": str(VIDEO),
                    "extract_frames": True,
                    "frame_interval": 1.5,
                    "max_frames": 20,
                    "transcribe_audio": True,
                    "whisper_model": "base",
                    "detect_scenes": True,
                    "scene_threshold": 0.35,
                },
            )
            review = await session.call_tool(
                "video_review",
                {
                    "video_path": str(VIDEO),
                    "frame_interval": 1.5,
                    "max_frames": 20,
                    "scene_threshold": 0.35,
                    "transcribe_audio": True,
                },
            )
            transcribe = await session.call_tool(
                "video_transcribe",
                {
                    "video_path": str(VIDEO),
                    "model": "base",
                    "language": "zh",
                    "word_timestamps": True,
                },
            )
    receipt = {
        "video_path": str(VIDEO),
        "initialize": dump(initialize),
        "tools": dump(tools),
        "video_analyze": dump(analyze),
        "video_review": dump(review),
        "video_transcribe": dump(transcribe),
    }
    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
