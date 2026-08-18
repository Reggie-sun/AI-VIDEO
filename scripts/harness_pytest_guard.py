"""Pytest plugin that blocks non-loopback network access during Harness runs."""

from __future__ import annotations

import ipaddress
import os
import socket
from collections.abc import Callable
from typing import Any


_ENABLED_ENV = "AI_VIDEO_HARNESS_NO_NETWORK"
_ORIGINALS: dict[str, Callable[..., Any]] = {}


def network_guard_installed() -> bool:
    return bool(_ORIGINALS)


def is_loopback_host(host: object) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", "ignore")
    if not isinstance(host, str):
        return False
    normalized = host.rstrip(".").split("%", 1)[0]
    if normalized.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def require_loopback(address: object) -> None:
    if not isinstance(address, tuple) or not address:
        return
    if not is_loopback_host(address[0]):
        raise RuntimeError(
            f"Harness external network disabled; non-loopback address rejected: "
            f"{address[0]!r}"
        )


def _guarded_connect(sock: socket.socket, address: object) -> Any:
    if sock.family != socket.AF_UNIX:
        require_loopback(address)
    return _ORIGINALS["connect"](sock, address)


def _guarded_connect_ex(sock: socket.socket, address: object) -> int:
    if sock.family != socket.AF_UNIX:
        require_loopback(address)
    return _ORIGINALS["connect_ex"](sock, address)


def _guarded_create_connection(address: object, *args: Any, **kwargs: Any) -> Any:
    require_loopback(address)
    return _ORIGINALS["create_connection"](address, *args, **kwargs)


def _guarded_sendto(sock: socket.socket, data: bytes, *args: Any) -> int:
    if sock.family != socket.AF_UNIX and args:
        require_loopback(args[-1])
    return _ORIGINALS["sendto"](sock, data, *args)


def _guarded_sendmsg(
    sock: socket.socket,
    buffers: Any,
    ancdata: Any = (),
    flags: int = 0,
    address: object | None = None,
) -> int:
    if sock.family != socket.AF_UNIX and address is not None:
        require_loopback(address)
    if address is None:
        return _ORIGINALS["sendmsg"](sock, buffers, ancdata, flags)
    return _ORIGINALS["sendmsg"](sock, buffers, ancdata, flags, address)


def _guarded_getaddrinfo(host: object, *args: Any, **kwargs: Any) -> Any:
    if not is_loopback_host(host):
        raise RuntimeError(
            f"Harness external network disabled; DNS lookup rejected: {host!r}"
        )
    return _ORIGINALS["getaddrinfo"](host, *args, **kwargs)


def _guarded_host_lookup(host: object, *args: Any, **kwargs: Any) -> Any:
    if not is_loopback_host(host):
        raise RuntimeError(
            f"Harness external network disabled; DNS lookup rejected: {host!r}"
        )
    return _ORIGINALS["gethostbyname"](host, *args, **kwargs)


def _guarded_host_lookup_ex(host: object, *args: Any, **kwargs: Any) -> Any:
    if not is_loopback_host(host):
        raise RuntimeError(
            f"Harness external network disabled; DNS lookup rejected: {host!r}"
        )
    return _ORIGINALS["gethostbyname_ex"](host, *args, **kwargs)


def _guarded_host_reverse_lookup(host: object, *args: Any, **kwargs: Any) -> Any:
    if not is_loopback_host(host):
        raise RuntimeError(
            f"Harness external network disabled; DNS lookup rejected: {host!r}"
        )
    return _ORIGINALS["gethostbyaddr"](host, *args, **kwargs)


def _guarded_getnameinfo(address: object, *args: Any, **kwargs: Any) -> Any:
    require_loopback(address)
    return _ORIGINALS["getnameinfo"](address, *args, **kwargs)


def install_network_guard() -> None:
    if _ORIGINALS:
        return
    _ORIGINALS.update(
        {
            "connect": socket.socket.connect,
            "connect_ex": socket.socket.connect_ex,
            "create_connection": socket.create_connection,
            "getaddrinfo": socket.getaddrinfo,
            "gethostbyaddr": socket.gethostbyaddr,
            "gethostbyname": socket.gethostbyname,
            "gethostbyname_ex": socket.gethostbyname_ex,
            "getnameinfo": socket.getnameinfo,
            "sendto": socket.socket.sendto,
        }
    )
    socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
    socket.create_connection = _guarded_create_connection
    socket.getaddrinfo = _guarded_getaddrinfo
    socket.gethostbyaddr = _guarded_host_reverse_lookup
    socket.gethostbyname = _guarded_host_lookup
    socket.gethostbyname_ex = _guarded_host_lookup_ex
    socket.getnameinfo = _guarded_getnameinfo
    socket.socket.sendto = _guarded_sendto  # type: ignore[method-assign]
    if hasattr(socket.socket, "sendmsg"):
        _ORIGINALS["sendmsg"] = socket.socket.sendmsg
        socket.socket.sendmsg = _guarded_sendmsg  # type: ignore[method-assign]


def remove_network_guard() -> None:
    if not _ORIGINALS:
        return
    socket.socket.connect = _ORIGINALS["connect"]  # type: ignore[method-assign]
    socket.socket.connect_ex = _ORIGINALS["connect_ex"]  # type: ignore[method-assign]
    socket.create_connection = _ORIGINALS["create_connection"]
    socket.getaddrinfo = _ORIGINALS["getaddrinfo"]
    socket.gethostbyaddr = _ORIGINALS["gethostbyaddr"]
    socket.gethostbyname = _ORIGINALS["gethostbyname"]
    socket.gethostbyname_ex = _ORIGINALS["gethostbyname_ex"]
    socket.getnameinfo = _ORIGINALS["getnameinfo"]
    socket.socket.sendto = _ORIGINALS["sendto"]  # type: ignore[method-assign]
    if "sendmsg" in _ORIGINALS:
        socket.socket.sendmsg = _ORIGINALS["sendmsg"]  # type: ignore[method-assign]
    _ORIGINALS.clear()


def pytest_configure() -> None:
    if os.environ.get(_ENABLED_ENV) == "1":
        install_network_guard()


def pytest_unconfigure() -> None:
    remove_network_guard()
