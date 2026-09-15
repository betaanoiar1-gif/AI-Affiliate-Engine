from __future__ import annotations
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURL(ValueError):
    pass


def validate_public_url(url: str, *, allow_http: bool = False) -> str:
    parsed = urlparse(url)
    allowed = {"https"} | ({"http"} if allow_http else set())
    if parsed.scheme.lower() not in allowed or not parsed.hostname:
        raise UnsafeURL("only public HTTPS URLs are allowed")
    host = parsed.hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise UnsafeURL("local hosts are not allowed")
    try:
        addresses = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise UnsafeURL("hostname cannot be resolved") from exc
    for item in addresses:
        ip = ipaddress.ip_address(item[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise UnsafeURL("private or special-use addresses are not allowed")
    return parsed.geturl()


def redact_secret(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * max(4, len(value) - keep)
