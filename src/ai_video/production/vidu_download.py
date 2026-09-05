"""Credential-free Vidu result GET with validated, pinned public addresses."""

from __future__ import annotations

import http.client
import ipaddress
import math
import re
import socket
import ssl
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from ai_video.errors import AiVideoError, ErrorCode


def _error() -> AiVideoError:
    return AiVideoError(code=ErrorCode.VIDEO_ARTIFACT_INVALID,
                        user_message="Vidu result requires direct public HTTPS without redirects.")


def _public_address(value: str):
    if "%" in value:
        raise ValueError("scoped address")
    address = ipaddress.ip_address(value)
    if (not address.is_global or address.is_multicast or address.is_reserved
            or address.is_unspecified or address.is_loopback or address.is_link_local):
        raise ValueError("non-public address")
    if isinstance(address, ipaddress.IPv6Address) and (
        address not in ipaddress.ip_network("2000::/3")
        or address.ipv4_mapped is not None or address.sixtofour is not None
        or address.teredo is not None
    ):
        raise ValueError("non-native global IPv6 address")
    return address


@dataclass(frozen=True)
class ViduResultLocator:
    hostname: str
    origin: str
    target: str = field(repr=False)
    host_header: str


def parse_result_url(url: str) -> ViduResultLocator:
    try:
        if not url or any(ord(c) < 33 or ord(c) > 126 for c in url) or "\\" in url or "#" in url:
            raise ValueError()
        parsed = urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.port not in (None, 443)
                or parsed.username is not None or parsed.password is not None
                or not parsed.path or parsed.path.startswith("//") or "%" in host or host.endswith(".")):
            raise ValueError()
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if len(host) > 253 or "." not in host or any(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) is None
                for label in host.split(".")
            ):
                raise ValueError()
        else:
            _public_address(host)
        authority = f"[{host}]" if ":" in host else host
        if parsed.netloc.lower() not in (authority, authority + ":443"):
            raise ValueError()
        return ViduResultLocator(host, f"https://{authority}",
                                 parsed.path + ("?" + parsed.query if "?" in url else ""), authority)
    except (ValueError, TypeError):
        raise _error() from None


def _resolve(locator: ViduResultLocator):
    try:
        records = socket.getaddrinfo(locator.hostname, 443, type=socket.SOCK_STREAM,
                                     proto=socket.IPPROTO_TCP)
        if not records:
            raise ValueError()
        for family, kind, protocol, _, sockaddr in records:
            address = _public_address(sockaddr[0])
            expected_family = socket.AF_INET if address.version == 4 else socket.AF_INET6
            if (family != expected_family or kind != socket.SOCK_STREAM or protocol != socket.IPPROTO_TCP
                    or sockaddr[1] != 443 or (family == socket.AF_INET6 and sockaddr[3] != 0)):
                raise ValueError()
        family, _, _, _, sockaddr = records[0]
        return family, sockaddr
    except (OSError, ValueError):
        raise _error() from None


class _VideoResponse:
    def __init__(self, response: http.client.HTTPResponse):
        self._response = response
        self.status_code = response.status
        self.headers = dict(response.getheaders())

    def iter_bytes(self) -> Iterator[bytes]:
        while chunk := self._response.read(64 * 1024):
            yield chunk


@contextmanager
def stream_public_video(url: str, *, timeout_seconds: float) -> Iterator[_VideoResponse]:
    if not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise _error()
    locator = parse_result_url(url)
    family, sockaddr = _resolve(locator)
    # Explicit context avoids create_default_context's SSLKEYLOGFILE side effect.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_default_certs()
    connection = http.client.HTTPConnection(locator.hostname, 443, timeout=timeout_seconds)
    connection.set_debuglevel(0)
    raw = socket.socket(family, socket.SOCK_STREAM)
    response = None
    try:
        raw.settimeout(timeout_seconds)
        raw.connect(sockaddr)
        # Connect the validated numeric address; certificate and SNI use the original host.
        connection.sock = context.wrap_socket(raw, server_hostname=locator.hostname)
        connection.request("GET", locator.target, headers={
            "Host": locator.host_header, "Accept": "video/mp4",
            "Accept-Encoding": "identity", "Connection": "close",
        })
        response = connection.getresponse()
        if 300 <= response.status < 400 or response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise _error()
        yield _VideoResponse(response)
    except (OSError, http.client.HTTPException):
        raise _error() from None
    finally:
        if response is not None:
            response.close()
        connection.close()
        raw.close()
