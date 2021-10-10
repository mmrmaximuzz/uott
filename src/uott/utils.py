"""Simple utils for UOTT."""

from typing import Tuple


def split_at(bs: bytes, idx: int) -> Tuple[bytes, bytes]:
    """Split the bytestring by given index."""
    return bs[:idx], bs[idx:]


def parse_endpoint(line: str) -> Tuple[str, int]:
    """Parse the endpoint string to a `bind`able tuple."""
    addr, port = line.split(":")
    return addr, int(port)
