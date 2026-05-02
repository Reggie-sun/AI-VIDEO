import httpx
import pytest

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.errors import AiVideoError, ErrorCode


def test_submit_rejects_node_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad prompt", "node_errors": {"6": "bad"}})

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(AiVideoError) as exc:
        client.submit_prompt({"6": {"inputs": {}, "class_type": "Test"}})
    assert exc.value.code is ErrorCode.COMFY_SUBMISSION_FAILED
    assert exc.value.retryable is False


def test_poll_completed_history_collects_status():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": [], "queue_pending": []})
        if request.url.path == "/history/prompt-1":
            return httpx.Response(
                200,
                json={
                    "prompt-1": {
                        "outputs": {
                            "42": {
                                "gifs": [
                                    {"filename": "clip.mp4", "subfolder": "", "type": "output"}
                                ]
                            }
                        }
                    }
                },
            )
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.poll_job("prompt-1", poll_interval_seconds=0, timeout_seconds=1)
    assert result.status is JobStatus.COMPLETED
    assert result.history["outputs"]["42"]["gifs"][0]["filename"] == "clip.mp4"


def test_poll_error_history_wins_over_empty_outputs():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": [], "queue_pending": []})
        if request.url.path == "/history/prompt-oom":
            return httpx.Response(
                200,
                json={
                    "prompt-oom": {
                        "outputs": {},
                        "status": {
                            "status_str": "error",
                            "messages": [
                                [
                                    "execution_error",
                                    {
                                        "exception_message": "Allocation on device",
                                        "exception_type": "torch.OutOfMemoryError",
                                    },
                                ]
                            ],
                        },
                    }
                },
            )
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.poll_job("prompt-oom", poll_interval_seconds=0, timeout_seconds=1)
    assert result.status is JobStatus.FAILED
    assert result.error is not None
    assert result.error.code is ErrorCode.COMFY_JOB_FAILED
    assert "OutOfMemoryError" in (result.error.technical_detail or "")


def test_collect_output_downloads_view(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/view":
            return httpx.Response(200, content=b"video")
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    target = tmp_path / "clip.mp4"
    client.download_artifact(filename="clip.mp4", subfolder="", type_="output", target=target)
    assert target.read_bytes() == b"video"
