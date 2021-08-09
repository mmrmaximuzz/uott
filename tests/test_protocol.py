"""Testing suite for uott protocol module."""

from uott import protocol


def test_udp_to_tcp_empty():
    """UDP datagrams can be zero-sized."""
    udp_dgram = b""
    uott_msg = protocol.udp_dgram_to_tcp_msg(udp_dgram)
    assert uott_msg == protocol.MAGIC + (0).to_bytes(2, "little")


def test_udp_to_tcp_normal():
    """Test ordinary datagrams."""
    udp_dgram = b"0123456789abcdef"
    uott_msg = protocol.udp_dgram_to_tcp_msg(udp_dgram)
    assert uott_msg == protocol.MAGIC + (16).to_bytes(2, "little") + udp_dgram
