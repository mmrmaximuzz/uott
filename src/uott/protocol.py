"""protocol - base definitions for uott protocol."""

MAGIC = b"UOTT"
BYTEORDER = "little"


def udp_dgram_to_tcp_msg(dgram: bytes) -> bytes:
    """Convert UDP datagram to UOTT TCP message."""
    udp_len = len(dgram)
    assert udp_len <= 0xFFFF

    return MAGIC + udp_len.to_bytes(length=2, byteorder=BYTEORDER) + dgram


def tcp_msg_to_udp_dgram(msg: bytes) -> bytes:
    """Convert UOTT TCP message to UDP datagram."""

