"""protocol - base definitions for uott protocol."""

from typing import Optional, Tuple

MAGIC = b"UOTT"
LEN_BYTES = 2
BYTEORDER = "little"


def udp_dgram_to_tcp_msg(dgram: bytes) -> bytes:
    """Convert UDP datagram to UOTT TCP message."""
    udp_len = len(dgram)
    assert udp_len <= 0xFFFF, f"oversized UDP datagram: {udp_len} B"

    return MAGIC + udp_len.to_bytes(LEN_BYTES, BYTEORDER) + dgram


def _split_at(bs: bytes, idx: int) -> Tuple[bytes, bytes]:
    """Split the bytestring by given index."""
    return bs[:idx], bs[idx:]


def tcp_msg_to_udp_dgram(msg: bytes) -> Optional[Tuple[bytes, bytes]]:
    """Convert UOTT TCP message to UDP datagram."""
    if len(msg) < len(MAGIC):
        # magic is not complete
        return None

    magic, msg = _split_at(msg, len(MAGIC))
    assert magic == MAGIC, f"UOTT protocol is corrupted: wrong magic {magic}"

    if len(msg) < LEN_BYTES:
        # length is not complete
        return None

    udp_len_bytes, msg = _split_at(msg, LEN_BYTES)
    udp_len = int.from_bytes(udp_len_bytes, BYTEORDER)
    if len(msg) < udp_len:
        # message is not complete
        return None

    return _split_at(msg, udp_len)
