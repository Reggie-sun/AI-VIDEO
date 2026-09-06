"""Resume known FETCH with real public DNS, preserving canonical download guards."""
import hashlib
import ipaddress
import json
import socket
from datetime import UTC, datetime

import httpx

from live_i2v import ROOT, PREP, ATTEMPT, EXPECTED, credential, event
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.vidu import HttpxViduTransport, ViduVideoProvider
from ai_video.production.vidu_profile import ViduProviderProfile


HOST = "prod-ss-vidu.s3.oss-cn-beijing.aliyuncs.com"


def main():
    loaded = load_production_project(ROOT / "project.yaml")
    attempt, = (a for a in loaded.manifest.attempts if a.attempt_id == ATTEMPT)
    assert attempt.video_generation_state.phase.value == "fetch"
    writer = ProductionStateCommitter(ROOT)
    resolved = writer._reopen_video_request(attempt.video_generation_state.request)
    assert resolved.resolved_generation_hash == EXPECTED
    # The host resolver returns a Mihomo fake IP. Resolve only this public hostname
    # via authenticated HTTPS DNS; never pass signed URLs or Provider credentials.
    response = httpx.get("https://dns.alidns.com/resolve", params={"name": HOST, "type": "A"}, timeout=15, follow_redirects=False)
    response.raise_for_status()
    data = response.json()
    assert data["Status"] == 0
    addresses = tuple(a["data"] for a in data.get("Answer", ()) if a["type"] == 1)
    assert addresses
    for address in addresses:
        ip = ipaddress.ip_address(address)
        assert ip.version == 4 and ip.is_global and not ip.is_multicast and not ip.is_reserved
    report = {"at": datetime.now(UTC).isoformat(), "hostname": HOST, "addresses": addresses,
              "dns_response_sha256": hashlib.sha256(response.content).hexdigest(),
              "scope": "this single fetch process only", "new_submit_count": 0}
    with (PREP / "fetch-dns-evidence.json").open("x") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    system_getaddrinfo = socket.getaddrinfo

    def exact_public_getaddrinfo(host, port, *args, **kwargs):
        if host != HOST:
            return system_getaddrinfo(host, port, *args, **kwargs)
        assert port == 443
        return [row for ip in addresses for row in system_getaddrinfo(ip, port, *args, **kwargs)]

    class FetchTransport(HttpxViduTransport):
        def request(self, request):
            assert request.method == "GET", "Fetch recovery cannot submit"
            return super().request(request)

    transport = FetchTransport(timeout_seconds=45)
    try:
        profile = ViduProviderProfile.model_validate_json((PREP / "provider-profile.json").read_bytes())
        provider = ViduVideoProvider(profile=profile, transport=transport, credential=credential)
        service = VideoGenerationService(committer=writer, provider=provider)
        assert service.resume_next_action(attempt_id=ATTEMPT) == "fetch"
        socket.getaddrinfo = exact_public_getaddrinfo
        fetched = service.fetch_once(attempt_id=ATTEMPT)
        path = ROOT / fetched.relative_path
        event("fetched_unactivated", path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              size_bytes=path.stat().st_size, next_action="exact MP4 project-local video-analysis Gate")
    finally:
        socket.getaddrinfo = system_getaddrinfo
        transport.close()


if __name__ == "__main__":
    main()
