"""Credential-free HTTP(S) streaming for downloaded bytes."""

from __future__ import annotations

import http.client
import ipaddress
import math
import re
import socket
import ssl
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from urllib.parse import quote, unquote, urljoin, urlsplit

from ai_video.errors import AiVideoError, ErrorCode


_MAX_REDIRECTS = 10
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_REG_NAME = re.compile(r"[a-z0-9._~!$&'()*+,;=-]+\Z", re.IGNORECASE)


def _error() -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_ARTIFACT_INVALID,
        user_message="Video result requires a valid credential-free HTTP(S) download.",
    )


@dataclass(frozen=True)
class ViduResultLocator:
    hostname: str
    origin: str
    target: str = field(repr=False)
    host_header: str
    scheme: str = "https"
    port: int = 443


def parse_result_url(url: str) -> ViduResultLocator:
    """Parse a credential-free HTTP(S) locator and return its canonical origin."""
    try:
        if (
            not isinstance(url, str)
            or not url
            or any(ord(character) < 33 or ord(character) == 127 for character in url)
            or "\\" in url
        ):
            raise ValueError()
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError()
        if parsed.username is not None or parsed.password is not None or parsed.netloc.endswith(":"):
            raise ValueError()
        raw_host = parsed.hostname
        if not raw_host:
            raise ValueError()
        raw_host = unquote(raw_host, encoding="utf-8", errors="strict")
        is_ipv6 = False
        try:
            address = ipaddress.ip_address(raw_host)
        except ValueError:
            host = raw_host.encode("idna").decode("ascii").lower()
            if not host or not _REG_NAME.fullmatch(host):
                raise ValueError()
        else:
            host = address.compressed.lower()
            is_ipv6 = isinstance(address, ipaddress.IPv6Address)
        port = parsed.port if parsed.port is not None else (443 if scheme == "https" else 80)
        default_port = 443 if scheme == "https" else 80
        authority_host = f"[{host}]" if is_ipv6 else host
        authority = authority_host if port == default_port else f"{authority_host}:{port}"
        raw_target = parsed.path or "/"
        if "?" in url.split("#", 1)[0]:
            raw_target += "?" + parsed.query
        target = quote(raw_target, safe="/%?:@!$&'()*+,;=-._~")
        return ViduResultLocator(
            hostname=host,
            origin=f"{scheme}://{authority}",
            target=target,
            host_header=authority,
            scheme=scheme,
            port=port,
        )
    except (UnicodeError, ValueError, TypeError):
        raise _error() from None


def _resolver_records(locator: ViduResultLocator, resolver: Callable) -> list[tuple]:
    try:
        records = resolver(
            locator.hostname,
            locator.port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        if not records:
            raise ValueError()
        validated = []
        for record in records:
            if not isinstance(record, (tuple, list)) or len(record) != 5:
                raise ValueError()
            family, kind, protocol, canonical_name, sockaddr = record
            if (
                family not in {socket.AF_INET, socket.AF_INET6}
                or kind != socket.SOCK_STREAM
                or protocol not in {0, socket.IPPROTO_TCP}
                or not isinstance(canonical_name, str)
                or not isinstance(sockaddr, (tuple, list))
                or len(sockaddr) != (2 if family == socket.AF_INET else 4)
                or sockaddr[1] != locator.port
            ):
                raise ValueError()
            address = ipaddress.ip_address(sockaddr[0])
            if address.version != (4 if family == socket.AF_INET else 6):
                raise ValueError()
            validated.append((family, kind, protocol, tuple(sockaddr)))
        return validated
    except (OSError, UnicodeError, ValueError, TypeError, IndexError):
        raise _error() from None


def _connect_with_resolver(
    locator: ViduResultLocator,
    resolver: Callable,
    timeout: float,
    source_address: tuple[str, int] | None,
) -> socket.socket:
    records = _resolver_records(locator, resolver)
    last_error: OSError | None = None
    for family, kind, protocol, sockaddr in records:
        connection = socket.socket(family, kind, protocol)
        try:
            connection.settimeout(timeout)
            if source_address is not None:
                connection.bind(source_address)
            connection.connect(sockaddr)
            return connection
        except OSError as error:
            last_error = error
            connection.close()
    if last_error is not None:
        raise last_error
    raise OSError("resolver returned no usable address")


class _VideoResponse:
    def __init__(self, response: http.client.HTTPResponse):
        self._response = response
        self.status_code = response.status
        self.headers = dict(response.getheaders())

    def iter_bytes(self) -> Iterator[bytes]:
        while True:
            try:
                chunk = self._response.read(64 * 1024)
            except http.client.IncompleteRead as error:
                if error.partial:
                    yield bytes(error.partial)
                raise
            if not chunk:
                if self._response.length not in (None, 0):
                    raise http.client.IncompleteRead(b"", self._response.length)
                return
            yield chunk


@contextmanager
def stream_public_video(
    url: str, *, timeout_seconds: float, download_resolver: Callable | None = None
) -> Iterator[_VideoResponse]:
    """Stream HTTP(S) response bytes without forwarding credentials or cookies."""
    if (
        not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise _error()

    current_url = url
    redirects = 0
    while True:
        locator = parse_result_url(current_url)
        if locator.scheme == "https":
            # Avoid create_default_context's implicit SSLKEYLOGFILE handling.
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_default_certs()
            connection: http.client.HTTPConnection = http.client.HTTPSConnection(
                locator.hostname, locator.port, timeout=timeout_seconds, context=context
            )
        else:
            connection = http.client.HTTPConnection(
                locator.hostname, locator.port, timeout=timeout_seconds
            )
        connection.set_debuglevel(0)
        if download_resolver is not None:
            connection._create_connection = lambda _address, timeout, source_address=None: _connect_with_resolver(
                locator, download_resolver, timeout, source_address
            )
        response = None
        try:
            connection.request(
                "GET",
                locator.target,
                headers={
                    "Host": locator.host_header,
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            location = response.getheader("Location")
            if response.status in _REDIRECT_STATUSES and location is not None:
                if redirects >= _MAX_REDIRECTS:
                    raise _error()
                current_url = urljoin(current_url, location)
                parse_result_url(current_url)
                redirects += 1
                continue
            yield _VideoResponse(response)
            return
        except AiVideoError:
            raise
        except (OSError, http.client.HTTPException, UnicodeError, ValueError, TypeError):
            raise _error() from None
        finally:
            if response is not None:
                response.close()
            connection.close()
