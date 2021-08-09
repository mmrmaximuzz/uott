"""protocol - base definitions for uott protocol."""

MAGIC = b"UOTT"
LEN_BYTES = 2
BYTEORDER = "little"


def udp_dgram_to_tcp_msg(dgram: bytes) -> bytes:
    """Convert UDP datagram to UOTT TCP message."""
    udp_len = len(dgram)
    assert udp_len <= 0xFFFF

    return MAGIC + udp_len.to_bytes(LEN_BYTES, BYTEORDER) + dgram


def tcp_msg_to_udp_dgram(msg: bytes) -> bytes:
    """Convert UOTT TCP message to UDP datagram."""
    msg_len = len(msg)
    assert msg_len >= len(MAGIC) + 2

    magic, udp_len, dgram = msg[:4], msg[4:6], msg[6:]
    assert magic == MAGIC
    assert int.from_bytes(udp_len, BYTEORDER) == len(dgram)

    return dgram
