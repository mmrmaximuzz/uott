"""Simple utils for UOTT."""

from typing import Tuple

EndPoint = Tuple[str, int]


def split_at(bstring: bytes, idx: int) -> Tuple[bytes, bytes]:
    """Split the bytestring by given index."""
    return bstring[:idx], bstring[idx:]


def parse_endpoint(line: str) -> EndPoint:
    """Parse the endpoint string to a `bind`able tuple."""
    addr, port = line.split(":")
    return addr, int(port)
