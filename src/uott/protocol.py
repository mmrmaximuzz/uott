"""protocol - base definitions for uott protocol."""

from typing import Optional, Tuple

from .utils import split_at

MAGIC = b"UOTT"
TAG_BYTES = 2
LEN_BYTES = 2
BYTEORDER = "little"


def udp_dgram_to_tcp_msg(dgram: bytes, tag: int) -> bytes:
    """Convert UDP datagram to UOTT TCP message with given tag."""
    dlen = len(dgram)
    assert dlen <= 0xFFFF, f"oversized UDP datagram: {dlen} B"
    assert tag <= 0xFFFF, f"tag ID overflow: {tag}"

    parts = [
        MAGIC,
        tag.to_bytes(TAG_BYTES, BYTEORDER),
        dlen.to_bytes(LEN_BYTES, BYTEORDER),
        dgram,
    ]
    return b"".join(parts)


def tcp_msg_to_udp_dgram(msg: bytes) -> Optional[Tuple[bytes, bytes]]:
    """Convert UOTT TCP message to UDP datagram."""
    if len(msg) < len(MAGIC):
        # magic is not complete
        return None

    magic, msg = split_at(msg, len(MAGIC))
    assert magic == MAGIC, f"UOTT protocol is corrupted: wrong magic {magic}"

    if len(msg) < LEN_BYTES:
        # length is not complete
        return None

    udp_len_bytes, msg = split_at(msg, LEN_BYTES)
    udp_len = int.from_bytes(udp_len_bytes, BYTEORDER)
    if len(msg) < udp_len:
        # message is not complete
        return None

    return split_at(msg, udp_len)
